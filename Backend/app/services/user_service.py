import logging
import re
from typing import Dict, Any, List, Optional
from app.database.mongodb import get_database
from app.database.neo4j import execute_query
from app.utils.helpers import utc_now

logger = logging.getLogger("campusconnect.user_service")

class UserService:
    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        db = get_database()
        return await db.users.find_one({"user_id": user_id})

    @staticmethod
    async def get_public_profile(user_id: str) -> Optional[Dict[str, Any]]:
        db = get_database()
        user = await db.users.find_one({"user_id": user_id, "profile_completed": True})
        if not user:
            return None

        # Fetch follower & following counts from Neo4j
        cypher_counts = """
        MATCH (u:User {user_id: $user_id})
        OPTIONAL MATCH (follower:User)-[:FOLLOWS]->(u)
        OPTIONAL MATCH (u)-[:FOLLOWS]->(following:User)
        RETURN count(DISTINCT follower) AS followers_count, count(DISTINCT following) AS following_count
        """
        records = await execute_query(cypher_counts, {"user_id": user_id})
        followers_count = records[0]["followers_count"] if records else 0
        following_count = records[0]["following_count"] if records else 0

        return {
            "user_id": user["user_id"],
            "name": user["name"],
            "year": user.get("year"),
            "department": user.get("department"),
            "profile_picture": user.get("profile_picture"),
            "followers_count": followers_count,
            "following_count": following_count
        }

    @staticmethod
    async def update_profile(user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        db = get_database()
        updates["updated_at"] = utc_now()
        
        # Remove None values
        clean_updates = {k: v for k, v in updates.items() if v is not None}
        
        await db.users.update_one({"user_id": user_id}, {"$set": clean_updates})
        updated_user = await db.users.find_one({"user_id": user_id})

        # Sync name update to Neo4j if name changed
        if "name" in clean_updates:
            cypher_update = """
            MATCH (u:User {user_id: $user_id})
            SET u.name = $name
            """
            await execute_query(cypher_update, {"user_id": user_id, "name": clean_updates["name"]})

        return updated_user

    @staticmethod
    async def search_users(q: str, limit: int = 20) -> List[Dict[str, Any]]:
        db = get_database()
        regex_pattern = re.compile(re.escape(q), re.IGNORECASE)
        query = {
            "profile_completed": True,
            "$or": [
                {"name": regex_pattern},
                {"email": regex_pattern},
                {"department": regex_pattern}
            ]
        }
        cursor = db.users.find(query).limit(limit)
        users = await cursor.to_list(length=limit)
        return [
            {
                "user_id": u["user_id"],
                "name": u["name"],
                "department": u.get("department"),
                "profile_picture": u.get("profile_picture")
            }
            for u in users
        ]
