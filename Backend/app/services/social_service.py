import logging
import re
from typing import Any, Dict, List, Optional

from app.database.mongodb import get_database
from app.database.neo4j import execute_query

logger = logging.getLogger("campusconnect.social_service")

# Strongest interaction first, used to collapse duplicate edges per event.
_ACTION_PRIORITY = ["REGISTERED", "SHARED", "LIKED", "VIEWED"]


def _public_user(u: Dict[str, Any], **extra: Any) -> Dict[str, Any]:
    return {
        "user_id": u["user_id"],
        "name": u.get("name", ""),
        "year": u.get("year"),
        "department": u.get("department"),
        "profile_picture": u.get("profile_picture"),
        **extra,
    }


class SocialService:
    # ------------------------------------------------------------------ helpers
    @staticmethod
    async def get_following_ids(user_id: str) -> set:
        records = await execute_query(
            "MATCH (:User {user_id: $user_id})-[:FOLLOWS]->(f:User) RETURN f.user_id AS user_id",
            {"user_id": user_id},
            required=False,
        )
        return {r["user_id"] for r in records}

    @staticmethod
    async def _hydrate_users(
        user_ids: List[str], viewer_id: Optional[str] = None, mutual_counts: Optional[Dict[str, int]] = None
    ) -> List[Dict[str, Any]]:
        """Mongo is the source of truth for profile data. Preserves id order."""
        if not user_ids:
            return []
        db = get_database()
        docs = await db.users.find(
            {"user_id": {"$in": user_ids}, "profile_completed": True}
        ).to_list(length=len(user_ids))
        by_id = {u["user_id"]: u for u in docs}
        following = await SocialService.get_following_ids(viewer_id) if viewer_id else set()
        result = []
        for uid in user_ids:
            u = by_id.get(uid)
            if not u:
                continue
            extra: Dict[str, Any] = {}
            if viewer_id:
                extra["is_following"] = uid in following
            if mutual_counts is not None:
                extra["mutual_count"] = mutual_counts.get(uid, 0)
            result.append(_public_user(u, **extra))
        return result

    # ------------------------------------------------------------------ follow
    @staticmethod
    async def follow_user(follower_id: str, target_id: str) -> bool:
        if follower_id == target_id:
            raise ValueError("You cannot follow yourself")

        db = get_database()
        target_user = await db.users.find_one({"user_id": target_id, "profile_completed": True})
        if not target_user:
            raise ValueError("Target user does not exist")

        follower_user = await db.users.find_one({"user_id": follower_id})
        if not follower_user:
            raise ValueError("Follower user does not exist")

        await execute_query(
            """
            MERGE (a:User {user_id: $follower_id})
            ON CREATE SET a.name = $follower_name
            MERGE (b:User {user_id: $target_id})
            ON CREATE SET b.name = $target_name
            MERGE (a)-[r:FOLLOWS]->(b)
            RETURN r
            """,
            {
                "follower_id": follower_id,
                "follower_name": follower_user.get("name", ""),
                "target_id": target_id,
                "target_name": target_user.get("name", ""),
            },
        )
        return True

    @staticmethod
    async def unfollow_user(follower_id: str, target_id: str) -> bool:
        await execute_query(
            """
            MATCH (a:User {user_id: $follower_id})-[r:FOLLOWS]->(b:User {user_id: $target_id})
            DELETE r
            """,
            {"follower_id": follower_id, "target_id": target_id},
        )
        return True

    @staticmethod
    async def get_follow_status(follower_id: str, target_id: str) -> bool:
        records = await execute_query(
            """
            OPTIONAL MATCH (a:User {user_id: $follower_id})-[r:FOLLOWS]->(b:User {user_id: $target_id})
            RETURN count(r) > 0 AS is_following
            """,
            {"follower_id": follower_id, "target_id": target_id},
            required=False,
        )
        return bool(records[0]["is_following"]) if records else False

    @staticmethod
    async def get_followers(user_id: str, viewer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        records = await execute_query(
            "MATCH (f:User)-[:FOLLOWS]->(:User {user_id: $user_id}) RETURN f.user_id AS user_id",
            {"user_id": user_id},
            required=False,
        )
        return await SocialService._hydrate_users([r["user_id"] for r in records], viewer_id)

    @staticmethod
    async def get_following(user_id: str, viewer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        records = await execute_query(
            "MATCH (:User {user_id: $user_id})-[:FOLLOWS]->(f:User) RETURN f.user_id AS user_id",
            {"user_id": user_id},
            required=False,
        )
        return await SocialService._hydrate_users([r["user_id"] for r in records], viewer_id)

    # ------------------------------------------------------------------ graph insight
    @staticmethod
    async def get_mutuals(user_id: str, target_id: str) -> List[Dict[str, Any]]:
        """People both users follow."""
        records = await execute_query(
            """
            MATCH (:User {user_id: $user_id})-[:FOLLOWS]->(m:User)<-[:FOLLOWS]-(:User {user_id: $target_id})
            RETURN DISTINCT m.user_id AS user_id
            """,
            {"user_id": user_id, "target_id": target_id},
            required=False,
        )
        return await SocialService._hydrate_users([r["user_id"] for r in records], user_id)

    @staticmethod
    async def get_common_interests(user_id: str, target_id: str) -> List[Dict[str, Any]]:
        """Events both users interacted with; one row per event."""
        records = await execute_query(
            """
            MATCH (:User {user_id: $user_id})-[r1:LIKED|REGISTERED|SHARED|VIEWED]->(e:Event)
                  <-[r2:LIKED|REGISTERED|SHARED|VIEWED]-(:User {user_id: $target_id})
            RETURN e.event_id AS event_id, collect(DISTINCT type(r1)) AS my_actions,
                   collect(DISTINCT type(r2)) AS target_actions
            """,
            {"user_id": user_id, "target_id": target_id},
            required=False,
        )
        event_ids = [r["event_id"] for r in records]
        if not event_ids:
            return []

        db = get_database()
        events = await db.events.find(
            {"event_id": {"$in": event_ids}, "status": "approved"}
        ).to_list(length=len(event_ids))
        events_map = {e["event_id"]: e for e in events}

        def strongest(actions: List[str]) -> str:
            for a in _ACTION_PRIORITY:
                if a in actions:
                    return a.lower()
            return actions[0].lower() if actions else "interacted"

        result = []
        for r in records:
            event = events_map.get(r["event_id"])
            if not event:
                continue
            result.append({
                "event_id": r["event_id"],
                "title": event["title"],
                "category": event["category"],
                "interaction_type": f"You {strongest(r['my_actions'])}, they {strongest(r['target_actions'])}",
            })
        return result

    @staticmethod
    async def get_suggestions(user_id: str, limit: int = 12) -> List[Dict[str, Any]]:
        """People you may know.

        1. Graph: friends-of-friends ranked by number of mutual connections.
        2. Fallback (and fill): same department, most recent first.
        """
        records = await execute_query(
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
        ids = [r["user_id"] for r in records]
        mutual_counts = {r["user_id"]: r["mutual_count"] for r in records}

        db = get_database()
        me = await db.users.find_one({"user_id": user_id})
        following = await SocialService.get_following_ids(user_id)

        if len(ids) < limit and me and me.get("department"):
            exclude = list(following | set(ids) | {user_id})
            same_dept = await db.users.find({
                "department": me["department"],
                "profile_completed": True,
                "user_id": {"$nin": exclude},
            }).sort("created_at", -1).limit(limit - len(ids)).to_list(length=limit)
            for u in same_dept:
                ids.append(u["user_id"])
                mutual_counts.setdefault(u["user_id"], 0)

        return await SocialService._hydrate_users(ids, user_id, mutual_counts)

    # ------------------------------------------------------------------ directory
    @staticmethod
    async def list_people(
        viewer_id: str,
        q: Optional[str] = None,
        department: Optional[str] = None,
        year: Optional[int] = None,
        page: int = 1,
        limit: int = 24,
    ) -> List[Dict[str, Any]]:
        db = get_database()
        query: Dict[str, Any] = {"profile_completed": True, "user_id": {"$ne": viewer_id}}
        if department:
            query["department"] = department
        if year:
            query["year"] = year
        if q:
            pattern = re.compile(re.escape(q.strip()), re.IGNORECASE)
            # Email is intentionally NOT searchable: it is not shown publicly.
            query["$or"] = [{"name": pattern}, {"department": pattern}]
        users = await (
            db.users.find(query).sort("name", 1).skip((page - 1) * limit).limit(limit).to_list(length=limit)
        )
        following = await SocialService.get_following_ids(viewer_id)
        return [_public_user(u, is_following=u["user_id"] in following) for u in users]

    @staticmethod
    async def list_departments() -> List[str]:
        db = get_database()
        values = await db.users.distinct("department", {"profile_completed": True})
        return sorted(v for v in values if v)
