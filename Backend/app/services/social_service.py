import logging
from typing import Dict, Any, List
from app.database.mongodb import get_database
from app.database.neo4j import execute_query

logger = logging.getLogger("campusconnect.social_service")

class SocialService:
    @staticmethod
    async def follow_user(follower_id: str, target_id: str) -> bool:
        if follower_id == target_id:
            raise ValueError("You cannot follow yourself")

        db = get_database()
        target_user = await db.users.find_one({"user_id": target_id})
        if not target_user:
            raise ValueError("Target user does not exist")

        follower_user = await db.users.find_one({"user_id": follower_id})
        if not follower_user:
            raise ValueError("Follower user does not exist")

        # MERGE in Neo4j
        cypher = """
        MERGE (a:User {user_id: $follower_id})
        ON CREATE SET a.name = $follower_name
        MERGE (b:User {user_id: $target_id})
        ON CREATE SET b.name = $target_name
        MERGE (a)-[r:FOLLOWS]->(b)
        RETURN r
        """
        await execute_query(cypher, {
            "follower_id": follower_id,
            "follower_name": follower_user.get("name", ""),
            "target_id": target_id,
            "target_name": target_user.get("name", "")
        })
        return True

    @staticmethod
    async def unfollow_user(follower_id: str, target_id: str) -> bool:
        cypher = """
        MATCH (a:User {user_id: $follower_id})-[r:FOLLOWS]->(b:User {user_id: $target_id})
        DELETE r
        """
        await execute_query(cypher, {
            "follower_id": follower_id,
            "target_id": target_id
        })
        return True

    @staticmethod
    async def get_follow_status(follower_id: str, target_id: str) -> bool:
        cypher = """
        MATCH (a:User {user_id: $follower_id})-[r:FOLLOWS]->(b:User {user_id: $target_id})
        RETURN count(r) > 0 AS is_following
        """
        records = await execute_query(cypher, {
            "follower_id": follower_id,
            "target_id": target_id
        })
        return records[0]["is_following"] if records else False

    @staticmethod
    async def get_followers(user_id: str) -> List[Dict[str, Any]]:
        cypher = """
        MATCH (follower:User)-[:FOLLOWS]->(u:User {user_id: $user_id})
        RETURN follower.user_id AS user_id, follower.name AS name
        """
        records = await execute_query(cypher, {"user_id": user_id})
        follower_ids = [r["user_id"] for r in records]
        if not follower_ids:
            return []

        db = get_database()
        cursor = db.users.find({"user_id": {"$in": follower_ids}})
        users = await cursor.to_list(length=len(follower_ids))
        return [
            {
                "user_id": u["user_id"],
                "name": u["name"],
                "department": u.get("department"),
                "profile_picture": u.get("profile_picture")
            }
            for u in users
        ]

    @staticmethod
    async def get_following(user_id: str) -> List[Dict[str, Any]]:
        cypher = """
        MATCH (u:User {user_id: $user_id})-[:FOLLOWS]->(following:User)
        RETURN following.user_id AS user_id, following.name AS name
        """
        records = await execute_query(cypher, {"user_id": user_id})
        following_ids = [r["user_id"] for r in records]
        if not following_ids:
            return []

        db = get_database()
        cursor = db.users.find({"user_id": {"$in": following_ids}})
        users = await cursor.to_list(length=len(following_ids))
        return [
            {
                "user_id": u["user_id"],
                "name": u["name"],
                "department": u.get("department"),
                "profile_picture": u.get("profile_picture")
            }
            for u in users
        ]

    @staticmethod
    async def get_mutuals(user_id: str, target_id: str) -> List[Dict[str, Any]]:
        cypher = """
        MATCH (u1:User {user_id: $user_id})-[:FOLLOWS]->(m:User)<-[:FOLLOWS]-(u2:User {target_id: $target_id})
        RETURN m.user_id AS user_id, m.name AS name
        """
        records = await execute_query(cypher, {"user_id": user_id, "target_id": target_id})
        mutual_ids = [r["user_id"] for r in records]
        if not mutual_ids:
            return []

        db = get_database()
        cursor = db.users.find({"user_id": {"$in": mutual_ids}})
        users = await cursor.to_list(length=len(mutual_ids))
        return [
            {
                "user_id": u["user_id"],
                "name": u["name"],
                "department": u.get("department"),
                "profile_picture": u.get("profile_picture")
            }
            for u in users
        ]

    @staticmethod
    async def get_common_interests(user_id: str, target_id: str) -> List[Dict[str, Any]]:
        cypher = """
        MATCH (u1:User {user_id: $user_id})-[r1:LIKED|REGISTERED|SHARED|VIEWED]->(e:Event)<-[r2:LIKED|REGISTERED|SHARED|VIEWED]-(u2:User {user_id: $target_id})
        RETURN e.event_id AS event_id, type(r1) AS my_action, type(r2) AS target_action
        """
        records = await execute_query(cypher, {"user_id": user_id, "target_id": target_id})
        event_ids = [r["event_id"] for r in records]
        if not event_ids:
            return []

        db = get_database()
        cursor = db.events.find({"event_id": {"$in": event_ids}, "status": "approved"})
        events_map = {e["event_id"]: e for e in await cursor.to_list(length=len(event_ids))}

        result = []
        for r in records:
            eid = r["event_id"]
            if eid in events_map:
                event = events_map[eid]
                result.append({
                    "event_id": eid,
                    "title": event["title"],
                    "category": event["category"],
                    "interaction_type": f"You {r['my_action']}, they {r['target_action']}"
                })
        return result
