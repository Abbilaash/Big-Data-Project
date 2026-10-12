import logging
from collections import defaultdict
from typing import Any, Dict, List

from app.database.mongodb import get_database
from app.database.neo4j import execute_query
from app.services.event_service import EventService
from app.utils.helpers import utc_now

logger = logging.getLogger("campusconnect.feed_service")

# Action weight for ranking
ACTION_WEIGHTS = {
    "REGISTERED": 4,
    "SHARED": 3,
    "LIKED": 2,
    "VIEWED": 1
}

# Past-tense phrasing used in the human-readable reason.
ACTION_PHRASES = {
    "REGISTERED": "registered for this event",
    "SHARED": "shared this event",
    "LIKED": "liked this event",
    "VIEWED": "viewed this event",
}


def build_reason(unique_users: List[Dict[str, Any]]) -> str:
    """Compose the 'why am I seeing this' line from de-duplicated friend actions."""
    top = unique_users[0]
    if len(unique_users) == 1:
        return f"{top['name']} {ACTION_PHRASES.get(top['action'], 'interacted with this event')}"
    others = len(unique_users) - 1
    noun = "connection" if others == 1 else "connections"
    return f"{top['name']} and {others} other {noun} interacted with this event"


class FeedService:
    @staticmethod
    async def get_personalized_feed(user_id: str, limit: int = 20, include_fallback: bool = True) -> List[Dict[str, Any]]:
        """
        1. Neo4j: events interacted with by people I follow.
        2. Rank by summed action weight.
        3. MongoDB: fetch approved, not-yet-past event documents in one $in query.
        4. Attach social context (friend names come from MongoDB).
        5. Fallback: pad with other upcoming approved events.
        """
        records = await execute_query(
            """
            MATCH (friend:User)-[:FOLLOWS]-(me:User {user_id: $user_id})
            WHERE friend.user_id <> $user_id
            MATCH (friend)-[r:LIKED|REGISTERED|SHARED|VIEWED]->(e:Event)
            RETURN DISTINCT e.event_id AS event_id, friend.user_id AS friend_id, type(r) AS interaction_type
            """,
            {"user_id": user_id},
            required=False,
        )

        db = get_database()
        today = utc_now().strftime("%Y-%m-%d")

        # Friend display names: MongoDB is the source of truth for profiles.
        friend_ids = list({r["friend_id"] for r in records})
        friends = (
            await db.users.find({"user_id": {"$in": friend_ids}}).to_list(length=len(friend_ids))
            if friend_ids else []
        )
        friend_names = {f["user_id"]: f.get("name") or "Someone" for f in friends}

        event_interactions: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        event_scores: Dict[str, int] = defaultdict(int)
        for rec in records:
            eid, action = rec["event_id"], rec["interaction_type"]
            event_interactions[eid].append({
                "user_id": rec["friend_id"],
                "name": friend_names.get(rec["friend_id"], "Someone"),
                "action": action,
            })
            event_scores[eid] += ACTION_WEIGHTS.get(action, 1)

        sorted_event_ids = sorted(event_scores, key=lambda k: event_scores[k], reverse=True)

        feed: List[Dict[str, Any]] = []
        if sorted_event_ids:
            mongo_events = await db.events.find({
                "event_id": {"$in": sorted_event_ids},
                "status": "approved",
                "date": {"$gte": today},
            }).to_list(length=len(sorted_event_ids))
            events_by_id = {e["event_id"]: e for e in mongo_events}

            for eid in sorted_event_ids:
                event = events_by_id.get(eid)
                if not event:
                    continue
                # One entry per friend, keeping their strongest action.
                best: Dict[str, Dict[str, Any]] = {}
                for item in event_interactions[eid]:
                    cur = best.get(item["user_id"])
                    if cur is None or ACTION_WEIGHTS.get(item["action"], 0) > ACTION_WEIGHTS.get(cur["action"], 0):
                        best[item["user_id"]] = item
                unique_users = sorted(
                    best.values(), key=lambda u: ACTION_WEIGHTS.get(u["action"], 0), reverse=True
                )
                event["social_context"] = {"reason": build_reason(unique_users), "users": unique_users}
                feed.append(event)

        feed = feed[:limit]

        if include_fallback and len(feed) < limit:
            exclude = [e["event_id"] for e in feed]
            fallback = await db.events.find({
                "status": "approved",
                "event_id": {"$nin": exclude},
                "date": {"$gte": today},
            }).sort([("date", 1), ("start_time", 1)]).limit(limit - len(feed)).to_list(length=limit)
            for event in fallback:
                event["social_context"] = None
                feed.append(event)

        await EventService._attach_host_names(feed)
        await EventService.attach_interaction_stats(feed, user_id)
        return feed
