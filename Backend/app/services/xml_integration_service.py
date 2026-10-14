"""
xml_integration_service.py

PURPOSE:
    Integrates Neo4j (graph/relationship data) with MongoDB (content/profile data)
    and serializes the combined result as XML.

HOW IT WORKS (the 3-step hybrid query pattern):
    1. Query Neo4j with Cypher → get relationship-based IDs
    2. Query MongoDB with those IDs → get full document data
    3. Merge in Python → build and return an XML string

The two databases are bridged by shared IDs:
    - user_id (e.g. USR_abc123)  — exists in BOTH MongoDB and Neo4j
    - event_id (e.g. EV_xyz789)  — exists in BOTH MongoDB and Neo4j

Neo4j stores THIN nodes: User(user_id, name) and Event(event_id)
MongoDB stores RICH documents: full profiles, full event details, comments

XML is built using Python's built-in xml.etree.ElementTree (no extra install needed).
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.database.mongodb import get_database
from app.database.neo4j import execute_query


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _prettify(element: ET.Element) -> str:
    """Convert an ElementTree element to a nicely indented XML string."""
    raw = ET.tostring(element, encoding="unicode")
    reparsed = minidom.parseString(raw)
    return reparsed.toprettyxml(indent="  ")


def _sub(parent: ET.Element, tag: str, text: Any) -> ET.Element:
    """Add a child XML element with text content. Converts None to empty string."""
    el = ET.SubElement(parent, tag)
    el.text = str(text) if text is not None else ""
    return el


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 1 — Personalized Feed (Neo4j graph + MongoDB content)
# ─────────────────────────────────────────────────────────────────────────────

# Action weights: how strongly each action implies interest
ACTION_WEIGHTS = {"REGISTERED": 4, "SHARED": 3, "LIKED": 2, "VIEWED": 1}


async def get_feed_as_xml(user_id: str, limit: int = 10) -> str:
    """
    Build a personalised event feed for a user and return it as XML.

    Integration pattern:
        Step 1 (Neo4j)   → Cypher finds events interacted with by this user's
                           connections, returning event_id + friend_id + action.
        Step 2 (MongoDB) → Batch-fetch full event documents and friend names
                           using the IDs returned by Neo4j.
        Step 3 (Python)  → Score events by summed action weight, de-duplicate
                           friend entries, attach "social context" reason text.
        Step 4 (XML)     → Serialise everything; each <Event> explicitly tags
                           which fields came from which database.

    Sample output
    -------------
    <Feed user_id="USR_123" source_databases="Neo4j + MongoDB" ...>
      <Event rank="1" score="7">
        <event_id>EV_abc</event_id>
        <title>AI Workshop</title>           <!-- from MongoDB -->
        <like_count>12</like_count>          <!-- from Neo4j  -->
        <SocialContext>
          <reason>Priya registered this event</reason>
          <Friends>
            <Friend>
              <name>Priya</name>
              <action>REGISTERED</action>
            </Friend>
          </Friends>
        </SocialContext>
      </Event>
      <total_results>1</total_results>
    </Feed>
    """

    # ── STEP 1: Neo4j ─────────────────────────────────────────────────────────
    # Cypher: for each connection (bidirectional FOLLOWS), find events they
    # interacted with and return the interaction type.
    neo4j_records = await execute_query(
        """
        MATCH (friend:User)-[:FOLLOWS]-(me:User {user_id: $user_id})
        WHERE friend.user_id <> $user_id
        MATCH (friend)-[r:LIKED|REGISTERED|SHARED|VIEWED]->(e:Event)
        RETURN DISTINCT e.event_id    AS event_id,
                        friend.user_id AS friend_id,
                        type(r)        AS interaction_type
        """,
        {"user_id": user_id},
        required=False,   # degrade gracefully if Neo4j is down
    )
    # Example result:
    # [{"event_id": "EV_abc", "friend_id": "USR_priya", "interaction_type": "REGISTERED"}, ...]

    db = get_database()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    event_ids = list({r["event_id"] for r in neo4j_records})
    friend_ids = list({r["friend_id"] for r in neo4j_records})

    # ── STEP 2a: MongoDB — fetch full event documents ──────────────────────────
    # Only approved, upcoming events qualify for the feed.
    mongo_events: List[Dict] = []
    if event_ids:
        mongo_events = await db.events.find({
            "event_id": {"$in": event_ids},
            "status": "approved",
            "date": {"$gte": today},
        }).to_list(length=len(event_ids))

    # ── STEP 2b: MongoDB — fetch friend display names ─────────────────────────
    # Neo4j nodes store only (user_id, name); MongoDB is source of truth.
    mongo_friends: List[Dict] = []
    if friend_ids:
        mongo_friends = await db.users.find(
            {"user_id": {"$in": friend_ids}}
        ).to_list(length=len(friend_ids))

    # ── STEP 2c: Neo4j — get interaction counts per event (one batched query) ──
    stats_records: List[Dict] = []
    if event_ids:
        stats_records = await execute_query(
            """
            UNWIND $event_ids AS eid
            OPTIONAL MATCH (e:Event {event_id: eid})
            RETURN eid AS event_id,
                   size([(e)<-[:LIKED]-(:User)      | 1]) AS like_count,
                   size([(e)<-[:REGISTERED]-(:User) | 1]) AS registration_count
            """,
            {"event_ids": event_ids},
            required=False,
        )

    # ── STEP 3: Merge in Python ────────────────────────────────────────────────
    friend_map: Dict[str, Dict] = {f["user_id"]: f for f in mongo_friends}
    events_map: Dict[str, Dict] = {e["event_id"]: e for e in mongo_events}
    stats_map:  Dict[str, Dict] = {s["event_id"]: s for s in stats_records}

    # Group Neo4j records by event, accumulate score
    event_interactions: Dict[str, List] = defaultdict(list)
    event_scores:       Dict[str, int]  = defaultdict(int)

    for rec in neo4j_records:
        eid    = rec["event_id"]
        action = rec["interaction_type"]
        friend = friend_map.get(rec["friend_id"], {})
        event_interactions[eid].append({
            "user_id": rec["friend_id"],
            "name":    friend.get("name", "Someone"),
            "action":  action,
        })
        event_scores[eid] += ACTION_WEIGHTS.get(action, 1)

    # Sort events by descending score
    ranked_ids = sorted(event_scores, key=lambda k: event_scores[k], reverse=True)

    # ── STEP 4: Build XML ──────────────────────────────────────────────────────
    root = ET.Element("Feed")
    root.set("user_id",          user_id)
    root.set("generated_at",     datetime.now(timezone.utc).isoformat())
    root.set("source_databases", "Neo4j + MongoDB")

    count = 0
    for rank, eid in enumerate(ranked_ids, start=1):
        if count >= limit:
            break
        event_doc = events_map.get(eid)
        if not event_doc:
            continue  # event not approved / already past

        count += 1
        stats = stats_map.get(eid, {})

        event_el = ET.SubElement(root, "Event")
        event_el.set("rank",  str(rank))
        event_el.set("score", str(event_scores[eid]))

        # ── Content fields (source: MongoDB) ──────────────────────────────────
        _sub(event_el, "event_id",    event_doc["event_id"])
        _sub(event_el, "title",       event_doc.get("title"))
        _sub(event_el, "description", event_doc.get("description"))
        _sub(event_el, "date",        event_doc.get("date"))
        _sub(event_el, "start_time",  event_doc.get("start_time"))
        _sub(event_el, "venue",       event_doc.get("venue"))
        _sub(event_el, "category",    event_doc.get("category"))
        _sub(event_el, "host_id",     event_doc.get("host_id"))

        # ── Interaction counts (source: Neo4j) ─────────────────────────────────
        counts_el = ET.SubElement(event_el, "InteractionCounts")
        counts_el.set("source", "Neo4j")
        _sub(counts_el, "like_count",         stats.get("like_count", 0))
        _sub(counts_el, "registration_count", stats.get("registration_count", 0))

        # ── Social context — why am I seeing this? ─────────────────────────────
        ctx_el = ET.SubElement(event_el, "SocialContext")
        friends_here = event_interactions.get(eid, [])

        if friends_here:
            top    = friends_here[0]
            others = len(friends_here) - 1
            reason = (
                f"{top['name']} {top['action'].lower()}d this event"
                if others == 0
                else f"{top['name']} and {others} other connection(s) interacted with this event"
            )
            _sub(ctx_el, "reason", reason)

            friends_el = ET.SubElement(ctx_el, "Friends")
            friends_el.set("source", "Neo4j (relationships) + MongoDB (names)")
            for f in friends_here:
                f_el = ET.SubElement(friends_el, "Friend")
                _sub(f_el, "user_id", f["user_id"])
                _sub(f_el, "name",    f["name"])
                _sub(f_el, "action",  f["action"])

    _sub(root, "total_results", str(count))
    return _prettify(root)


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 2 — Friend Suggestions (Neo4j graph + MongoDB profiles)
# ─────────────────────────────────────────────────────────────────────────────

async def get_suggestions_as_xml(user_id: str, limit: int = 10) -> str:
    """
    Generate friend/connection suggestions and return them as XML.

    Integration pattern:
        Step 1 (Neo4j)   → Friends-of-friends ranked by mutual connection count.
        Step 2 (MongoDB) → Same-department fallback when the graph is sparse;
                           then hydrate all candidate profiles.
        Step 3 (XML)     → Each <Person> is tagged with its source database.

    Sample output
    -------------
    <Suggestions user_id="USR_123" source_databases="Neo4j + MongoDB" ...>
      <Person rank="1" mutual_count="3" source="graph">
        <user_id>USR_456</user_id>
        <name>Ananya</name>              <!-- from MongoDB -->
        <department>CSE</department>     <!-- from MongoDB -->
        <mutual_connections>3</mutual_connections>  <!-- from Neo4j -->
      </Person>
      <Person rank="2" mutual_count="0" source="department_fallback">
        ...
      </Person>
      <total_results>2</total_results>
    </Suggestions>
    """

    # ── STEP 1: Neo4j — friends of friends ────────────────────────────────────
    neo4j_records = await execute_query(
        """
        MATCH (me:User {user_id: $user_id})-[:FOLLOWS]->(:User)-[:FOLLOWS]->(cand:User)
        WHERE cand.user_id <> $user_id AND NOT (me)-[:FOLLOWS]->(cand)
        RETURN cand.user_id AS user_id, count(*) AS mutual_count
        ORDER BY mutual_count DESC
        LIMIT $limit
        """,
        {"user_id": user_id, "limit": limit},
        required=False,
    )

    graph_ids      = [r["user_id"] for r in neo4j_records]
    mutual_counts  = {r["user_id"]: r["mutual_count"] for r in neo4j_records}
    source_map     = {uid: "graph" for uid in graph_ids}

    # ── STEP 2a: MongoDB — my profile (for department fallback) ───────────────
    db     = get_database()
    me_doc = await db.users.find_one({"user_id": user_id})

    # ── STEP 2b: Neo4j — who am I already following? ──────────────────────────
    following_records = await execute_query(
        "MATCH (:User {user_id: $uid})-[:FOLLOWS]->(f:User) RETURN f.user_id AS user_id",
        {"uid": user_id},
        required=False,
    )
    following_ids = {r["user_id"] for r in following_records}

    # ── STEP 2c: MongoDB — department fallback (fill when graph is sparse) ─────
    dept_ids: List[str] = []
    if len(graph_ids) < limit and me_doc and me_doc.get("department"):
        exclude = list(following_ids | set(graph_ids) | {user_id})
        dept_users = await db.users.find({
            "department":       me_doc["department"],
            "profile_completed": True,
            "user_id":          {"$nin": exclude},
        }).sort("created_at", -1).limit(limit - len(graph_ids)).to_list(length=limit)

        for u in dept_users:
            dept_ids.append(u["user_id"])
            source_map[u["user_id"]] = "department_fallback"
            mutual_counts.setdefault(u["user_id"], 0)

    all_ids = graph_ids + dept_ids

    # ── STEP 2d: MongoDB — hydrate full profiles ───────────────────────────────
    mongo_users = await db.users.find(
        {"user_id": {"$in": all_ids}, "profile_completed": True}
    ).to_list(length=len(all_ids))
    users_map = {u["user_id"]: u for u in mongo_users}

    # ── STEP 3: Build XML ──────────────────────────────────────────────────────
    root = ET.Element("Suggestions")
    root.set("user_id",          user_id)
    root.set("generated_at",     datetime.now(timezone.utc).isoformat())
    root.set("source_databases", "Neo4j + MongoDB")

    for rank, uid in enumerate(all_ids, start=1):
        profile = users_map.get(uid)
        if not profile:
            continue

        person_el = ET.SubElement(root, "Person")
        person_el.set("rank",         str(rank))
        person_el.set("mutual_count", str(mutual_counts.get(uid, 0)))
        person_el.set("source",       source_map.get(uid, "unknown"))

        # Profile data from MongoDB
        info_el = ET.SubElement(person_el, "ProfileInfo")
        info_el.set("source", "MongoDB")
        _sub(info_el, "user_id",    profile["user_id"])
        _sub(info_el, "name",       profile.get("name"))
        _sub(info_el, "department", profile.get("department"))
        _sub(info_el, "year",       profile.get("year"))

        # Relationship data from Neo4j
        graph_el = ET.SubElement(person_el, "GraphInfo")
        graph_el.set("source", "Neo4j")
        _sub(graph_el, "mutual_connections", mutual_counts.get(uid, 0))

    _sub(root, "total_results", str(len(all_ids)))
    return _prettify(root)


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 3 — User Profile (MongoDB content + Neo4j graph stats)
# ─────────────────────────────────────────────────────────────────────────────

async def get_user_profile_as_xml(
    user_id: str,
    viewer_id: Optional[str] = None,
) -> str:
    """
    Fetch a user's full profile combining both databases and return as XML.

    Integration pattern:
        MongoDB → name, email, department, year, profile_picture, role
        Neo4j   → follower count, following count, events registered/liked

    Sample output
    -------------
    <UserProfile user_id="USR_123" generated_at="...">
      <BasicInfo source="MongoDB">
        <name>Nivashini</name>
        <department>CSE</department>
        <year>3</year>
        <role>student</role>
      </BasicInfo>
      <GraphStats source="Neo4j">
        <followers_count>45</followers_count>
        <following_count>30</following_count>
        <events_registered>12</events_registered>
        <events_liked>8</events_liked>
      </GraphStats>
    </UserProfile>
    """

    # ── STEP 1: MongoDB — get full profile ────────────────────────────────────
    db       = get_database()
    user_doc = await db.users.find_one({"user_id": user_id})

    if not user_doc:
        root = ET.Element("Error")
        _sub(root, "message", f"User '{user_id}' not found in MongoDB")
        return _prettify(root)

    # ── STEP 2: Neo4j — get graph stats ───────────────────────────────────────
    stats_records = await execute_query(
        """
        MATCH (u:User {user_id: $user_id})
        OPTIONAL MATCH (u)<-[:FOLLOWS]-(follower)
        OPTIONAL MATCH (u)-[:FOLLOWS]->(following)
        OPTIONAL MATCH (u)-[:REGISTERED]->(reg_event:Event)
        OPTIONAL MATCH (u)-[:LIKED]->(liked_event:Event)
        RETURN
            count(DISTINCT follower)   AS followers_count,
            count(DISTINCT following)  AS following_count,
            count(DISTINCT reg_event)  AS events_registered,
            count(DISTINCT liked_event) AS events_liked
        """,
        {"user_id": user_id},
        required=False,
    )
    stats = stats_records[0] if stats_records else {}

    # ── STEP 3: Neo4j — is viewer following this user? ────────────────────────
    is_following = False
    if viewer_id and viewer_id != user_id:
        follow_check = await execute_query(
            """
            OPTIONAL MATCH (a:User {user_id: $viewer_id})-[r:FOLLOWS]->(b:User {user_id: $user_id})
            RETURN count(r) > 0 AS is_following
            """,
            {"viewer_id": viewer_id, "user_id": user_id},
            required=False,
        )
        is_following = bool(follow_check[0]["is_following"]) if follow_check else False

    # ── STEP 4: Build XML ──────────────────────────────────────────────────────
    root = ET.Element("UserProfile")
    root.set("user_id",      user_id)
    root.set("generated_at", datetime.now(timezone.utc).isoformat())

    # Section 1: Basic info from MongoDB
    basic = ET.SubElement(root, "BasicInfo")
    basic.set("source", "MongoDB")
    _sub(basic, "name",            user_doc.get("name"))
    _sub(basic, "department",      user_doc.get("department"))
    _sub(basic, "year",            user_doc.get("year"))
    _sub(basic, "profile_picture", user_doc.get("profile_picture"))
    _sub(basic, "role",            user_doc.get("role", "student"))

    if viewer_id:
        _sub(root, "is_following_this_user", str(is_following).lower())

    # Section 2: Graph stats from Neo4j
    graph = ET.SubElement(root, "GraphStats")
    graph.set("source", "Neo4j")
    _sub(graph, "followers_count",   stats.get("followers_count", 0))
    _sub(graph, "following_count",   stats.get("following_count", 0))
    _sub(graph, "events_registered", stats.get("events_registered", 0))
    _sub(graph, "events_liked",      stats.get("events_liked", 0))

    return _prettify(root)
