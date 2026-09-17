import logging
from typing import Dict, Any, List
from app.database.mongodb import get_database
from app.utils.helpers import generate_comment_id, utc_now

logger = logging.getLogger("campusconnect.comment_service")

class CommentService:
    @staticmethod
    async def add_comment(event_id: str, user_id: str, content: str) -> Dict[str, Any]:
        db = get_database()
        event = await db.events.find_one({"event_id": event_id, "status": "approved"})
        if not event:
            raise ValueError("Approved event not found")

        comment_id = generate_comment_id()
        now = utc_now()
        comment = {
            "comment_id": comment_id,
            "event_id": event_id,
            "user_id": user_id,
            "content": content,
            "created_at": now
        }
        await db.comments.insert_one(comment)
        
        # Hydrate user details
        user = await db.users.find_one({"user_id": user_id})
        comment["user_name"] = user.get("name", "Unknown User") if user else "Unknown User"
        comment["user_picture"] = user.get("profile_picture") if user else None
        return comment

    @staticmethod
    async def get_event_comments(event_id: str) -> List[Dict[str, Any]]:
        db = get_database()
        cursor = db.comments.find({"event_id": event_id}).sort("created_at", 1)
        comments = await cursor.to_list(length=200)

        # Batch hydrate users
        user_ids = list(set([c["user_id"] for c in comments]))
        if user_ids:
            users_cursor = db.users.find({"user_id": {"$in": user_ids}})
            users_map = {u["user_id"]: u for u in await users_cursor.to_list(length=len(user_ids))}
        else:
            users_map = {}

        result = []
        for c in comments:
            user = users_map.get(c["user_id"])
            c["user_name"] = user.get("name", "Unknown User") if user else "Unknown User"
            c["user_picture"] = user.get("profile_picture") if user else None
            result.append(c)
        return result
