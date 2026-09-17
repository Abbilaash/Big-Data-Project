import logging
import re
from typing import Dict, Any, List, Optional
from app.database.mongodb import get_database
from app.database.neo4j import execute_query
from app.utils.helpers import generate_event_id, utc_now, utc_now_iso

logger = logging.getLogger("campusconnect.event_service")

class EventService:
    @staticmethod
    async def create_event(event_data: Dict[str, Any], host_id: str) -> Dict[str, Any]:
        db = get_database()
        event_id = generate_event_id()
        now = utc_now()

        event = {
            "event_id": event_id,
            "title": event_data["title"],
            "description": event_data["description"],
            "category": event_data["category"],
            "host_id": host_id,
            "date": event_data["date"],
            "start_time": event_data["start_time"],
            "end_time": event_data["end_time"],
            "venue": event_data["venue"],
            "registration_url": event_data.get("registration_url"),
            "poster_url": event_data.get("poster_url"),
            "tags": event_data.get("tags", []),
            "status": "pending",
            "created_at": now,
            "updated_at": now
        }
        await db.events.insert_one(event)
        logger.info(f"Event submitted: {event_id} by host {host_id} (pending approval)")
        return event

    @staticmethod
    async def get_approved_events(
        category: Optional[str] = None,
        date: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        db = get_database()
        query: Dict[str, Any] = {"status": "approved"}

        if category:
            query["category"] = category
        if date:
            query["date"] = date
        if search:
            regex_pattern = re.compile(re.escape(search), re.IGNORECASE)
            query["$or"] = [
                {"title": regex_pattern},
                {"description": regex_pattern},
                {"tags": regex_pattern}
            ]

        skip = (page - 1) * limit
        cursor = db.events.find(query).sort("created_at", -1).skip(skip).limit(limit)
        events = await cursor.to_list(length=limit)

        # Batch fetch host names
        host_ids = list(set([e["host_id"] for e in events]))
        hosts_cursor = db.users.find({"user_id": {"$in": host_ids}})
        hosts_map = {h["user_id"]: h.get("name", "Unknown Host") for h in await hosts_cursor.to_list(length=len(host_ids))}

        for e in events:
            e["host_name"] = hosts_map.get(e["host_id"], "Unknown Host")

        return events

    @staticmethod
    async def get_upcoming_events(limit: int = 10) -> List[Dict[str, Any]]:
        db = get_database()
        today = utc_now().strftime("%Y-%m-%d")
        query = {
            "status": "approved",
            "date": {"$gte": today}
        }
        cursor = db.events.find(query).sort("date", 1).limit(limit)
        events = await cursor.to_list(length=limit)

        host_ids = list(set([e["host_id"] for e in events]))
        hosts_cursor = db.users.find({"user_id": {"$in": host_ids}})
        hosts_map = {h["user_id"]: h.get("name", "Unknown Host") for h in await hosts_cursor.to_list(length=len(host_ids))}

        for e in events:
            e["host_name"] = hosts_map.get(e["host_id"], "Unknown Host")

        return events

    @staticmethod
    async def get_hosted_by_user(user_id: str) -> List[Dict[str, Any]]:
        db = get_database()
        cursor = db.events.find({"host_id": user_id}).sort("created_at", -1)
        return await cursor.to_list(length=100)

    @staticmethod
    async def get_event_by_id(event_id: str) -> Optional[Dict[str, Any]]:
        db = get_database()
        return await db.events.find_one({"event_id": event_id})

    @staticmethod
    async def get_event_detail(event_id: str, current_user_id: Optional[str] = None) -> Dict[str, Any]:
        event = await EventService.get_event_by_id(event_id)
        if not event:
            raise ValueError("Event not found")

        # Fetch host name
        db = get_database()
        host = await db.users.find_one({"user_id": event["host_id"]})
        event["host_name"] = host.get("name", "Unknown Host") if host else "Unknown Host"

        # Query Neo4j for interaction statistics and user status
        cypher = """
        MATCH (e:Event {event_id: $event_id})
        OPTIONAL MATCH (u1:User)-[l:LIKED]->(e)
        OPTIONAL MATCH (u2:User)-[r:REGISTERED]->(e)
        OPTIONAL MATCH (u3:User)-[v:VIEWED]->(e)
        OPTIONAL MATCH (u4:User)-[s:SHARED]->(e)
        OPTIONAL MATCH (me:User {user_id: $user_id})-[my_l:LIKED]->(e)
        OPTIONAL MATCH (me:User {user_id: $user_id})-[my_r:REGISTERED]->(e)
        RETURN count(DISTINCT l) AS like_count,
               count(DISTINCT r) AS registration_count,
               count(DISTINCT v) AS view_count,
               count(DISTINCT s) AS share_count,
               count(DISTINCT my_l) > 0 AS is_liked_by_me,
               count(DISTINCT my_r) > 0 AS is_registered_by_me
        """
        records = await execute_query(cypher, {
            "event_id": event_id,
            "user_id": current_user_id or ""
        })

        if records:
            rec = records[0]
            event["like_count"] = rec["like_count"]
            event["registration_count"] = rec["registration_count"]
            event["view_count"] = rec["view_count"]
            event["share_count"] = rec["share_count"]
            event["is_liked_by_me"] = rec["is_liked_by_me"]
            event["is_registered_by_me"] = rec["is_registered_by_me"]
        else:
            event["like_count"] = 0
            event["registration_count"] = 0
            event["view_count"] = 0
            event["share_count"] = 0
            event["is_liked_by_me"] = False
            event["is_registered_by_me"] = False

        return event

    @staticmethod
    async def like_event(user_id: str, user_name: str, event_id: str) -> bool:
        event = await EventService.get_event_by_id(event_id)
        if not event or event.get("status") != "approved":
            raise ValueError("Event not found or not approved")

        cypher = """
        MERGE (u:User {user_id: $user_id})
        ON CREATE SET u.name = $user_name
        MERGE (e:Event {event_id: $event_id})
        MERGE (u)-[r:LIKED]->(e)
        RETURN r
        """
        await execute_query(cypher, {"user_id": user_id, "user_name": user_name, "event_id": event_id})
        return True

    @staticmethod
    async def unlike_event(user_id: str, event_id: str) -> bool:
        cypher = """
        MATCH (u:User {user_id: $user_id})-[r:LIKED]->(e:Event {event_id: $event_id})
        DELETE r
        """
        await execute_query(cypher, {"user_id": user_id, "event_id": event_id})
        return True

    @staticmethod
    async def register_event(user_id: str, user_name: str, event_id: str) -> bool:
        event = await EventService.get_event_by_id(event_id)
        if not event or event.get("status") != "approved":
            raise ValueError("Event not found or not approved")

        cypher = """
        MERGE (u:User {user_id: $user_id})
        ON CREATE SET u.name = $user_name
        MERGE (e:Event {event_id: $event_id})
        MERGE (u)-[r:REGISTERED]->(e)
        RETURN r
        """
        await execute_query(cypher, {"user_id": user_id, "user_name": user_name, "event_id": event_id})
        return True

    @staticmethod
    async def unregister_event(user_id: str, event_id: str) -> bool:
        cypher = """
        MATCH (u:User {user_id: $user_id})-[r:REGISTERED]->(e:Event {event_id: $event_id})
        DELETE r
        """
        await execute_query(cypher, {"user_id": user_id, "event_id": event_id})
        return True

    @staticmethod
    async def record_view(user_id: str, user_name: str, event_id: str) -> bool:
        event = await EventService.get_event_by_id(event_id)
        if not event or event.get("status") != "approved":
            raise ValueError("Event not found or not approved")

        now = utc_now_iso()
        cypher = """
        MERGE (u:User {user_id: $user_id})
        ON CREATE SET u.name = $user_name
        MERGE (e:Event {event_id: $event_id})
        MERGE (u)-[r:VIEWED]->(e)
        ON CREATE SET r.first_viewed_at = $now, r.last_viewed_at = $now, r.count = 1
        ON MATCH SET r.last_viewed_at = $now, r.count = coalesce(r.count, 0) + 1
        RETURN r
        """
        await execute_query(cypher, {"user_id": user_id, "user_name": user_name, "event_id": event_id, "now": now})
        return True

    @staticmethod
    async def record_share(user_id: str, user_name: str, event_id: str) -> bool:
        event = await EventService.get_event_by_id(event_id)
        if not event or event.get("status") != "approved":
            raise ValueError("Event not found or not approved")

        cypher = """
        MERGE (u:User {user_id: $user_id})
        ON CREATE SET u.name = $user_name
        MERGE (e:Event {event_id: $event_id})
        MERGE (u)-[r:SHARED]->(e)
        RETURN r
        """
        await execute_query(cypher, {"user_id": user_id, "user_name": user_name, "event_id": event_id})
        return True
