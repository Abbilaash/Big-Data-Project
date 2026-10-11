import logging
import re
from typing import Any, Dict, List, Optional

from app.database.mongodb import get_database
from app.database.neo4j import execute_query
from app.utils.helpers import generate_event_id, utc_now, utc_now_iso

logger = logging.getLogger("campusconnect.event_service")


class EventService:
    # ------------------------------------------------------------------ helpers
    @staticmethod
    async def _attach_host_names(events: List[Dict[str, Any]]) -> None:
        if not events:
            return
        db = get_database()
        host_ids = list({e["host_id"] for e in events})
        hosts = await db.users.find({"user_id": {"$in": host_ids}}).to_list(length=len(host_ids))
        names = {h["user_id"]: h.get("name", "Unknown Host") for h in hosts}
        for e in events:
            e["host_name"] = names.get(e["host_id"], "Unknown Host")

    @staticmethod
    async def attach_interaction_stats(
        events: List[Dict[str, Any]], user_id: Optional[str] = None
    ) -> None:
        """Annotate events in place with like/registration counts and the
        caller's own like/registration state using ONE batched Cypher query.

        Counts are best-effort: if the graph is down the page still renders
        with zeros rather than failing.
        """
        for e in events:
            e.setdefault("like_count", 0)
            e.setdefault("registration_count", 0)
            e.setdefault("is_liked_by_me", False)
            e.setdefault("is_registered_by_me", False)
        if not events:
            return

        cypher = """
        UNWIND $event_ids AS eid
        OPTIONAL MATCH (e:Event {event_id: eid})
        RETURN eid AS event_id,
               size([(e)<-[:LIKED]-(:User) | 1]) AS like_count,
               size([(e)<-[:REGISTERED]-(:User) | 1]) AS registration_count,
               size([(e)<-[:LIKED]-(:User {user_id: $user_id}) | 1]) > 0 AS is_liked_by_me,
               size([(e)<-[:REGISTERED]-(:User {user_id: $user_id}) | 1]) > 0 AS is_registered_by_me
        """
        records = await execute_query(
            cypher,
            {"event_ids": [e["event_id"] for e in events], "user_id": user_id or ""},
            required=False,
        )
        by_id = {r["event_id"]: r for r in records}
        for e in events:
            r = by_id.get(e["event_id"])
            if r:
                e["like_count"] = r["like_count"]
                e["registration_count"] = r["registration_count"]
                e["is_liked_by_me"] = bool(r["is_liked_by_me"])
                e["is_registered_by_me"] = bool(r["is_registered_by_me"])

    @staticmethod
    async def _require_approved(event_id: str) -> Dict[str, Any]:
        event = await EventService.get_event_by_id(event_id)
        if not event or event.get("status") != "approved":
            raise ValueError("Event not found or not approved")
        return event

    # ------------------------------------------------------------------ reads
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
        upcoming_only: bool = False,
        page: int = 1,
        limit: int = 20,
        viewer_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        db = get_database()
        query: Dict[str, Any] = {"status": "approved"}

        if category:
            query["category"] = category
        if date:
            query["date"] = date
        elif upcoming_only:
            query["date"] = {"$gte": utc_now().strftime("%Y-%m-%d")}
        if search:
            pattern = re.compile(re.escape(search), re.IGNORECASE)
            query["$or"] = [{"title": pattern}, {"description": pattern}, {"tags": pattern}]

        skip = (page - 1) * limit
        # Soonest first when filtering to upcoming; otherwise newest submissions.
        sort = [("date", 1), ("start_time", 1)] if upcoming_only else [("created_at", -1)]
        events = await db.events.find(query).sort(sort).skip(skip).limit(limit).to_list(length=limit)

        await EventService._attach_host_names(events)
        await EventService.attach_interaction_stats(events, viewer_id)
        return events

    @staticmethod
    async def get_upcoming_events(limit: int = 10, viewer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        db = get_database()
        today = utc_now().strftime("%Y-%m-%d")
        events = await (
            db.events.find({"status": "approved", "date": {"$gte": today}})
            .sort([("date", 1), ("start_time", 1)])
            .limit(limit)
            .to_list(length=limit)
        )
        await EventService._attach_host_names(events)
        await EventService.attach_interaction_stats(events, viewer_id)
        return events

    @staticmethod
    async def get_hosted_by_user(user_id: str) -> List[Dict[str, Any]]:
        db = get_database()
        events = await db.events.find({"host_id": user_id}).sort("created_at", -1).to_list(length=100)
        await EventService._attach_host_names(events)
        await EventService.attach_interaction_stats(events, user_id)
        return events

    @staticmethod
    async def get_registered_by_user(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Events the user registered for: graph gives IDs, Mongo gives content."""
        records = await execute_query(
            "MATCH (:User {user_id: $user_id})-[:REGISTERED]->(e:Event) RETURN e.event_id AS event_id",
            {"user_id": user_id},
            required=False,
        )
        ids = [r["event_id"] for r in records]
        if not ids:
            return []
        db = get_database()
        events = await db.events.find(
            {"event_id": {"$in": ids}, "status": "approved"}
        ).sort([("date", 1), ("start_time", 1)]).limit(limit).to_list(length=limit)
        await EventService._attach_host_names(events)
        await EventService.attach_interaction_stats(events, user_id)
        return events

    @staticmethod
    async def get_event_by_id(event_id: str) -> Optional[Dict[str, Any]]:
        db = get_database()
        return await db.events.find_one({"event_id": event_id})

    @staticmethod
    async def get_event_detail(event_id: str, current_user_id: Optional[str] = None) -> Dict[str, Any]:
        event = await EventService.get_event_by_id(event_id)
        if not event:
            raise ValueError("Event not found")

        await EventService._attach_host_names([event])

        cypher = """
        OPTIONAL MATCH (e:Event {event_id: $event_id})
        RETURN size([(e)<-[:LIKED]-(:User) | 1]) AS like_count,
               size([(e)<-[:REGISTERED]-(:User) | 1]) AS registration_count,
               size([(e)<-[:VIEWED]-(:User) | 1]) AS view_count,
               size([(e)<-[:SHARED]-(:User) | 1]) AS share_count,
               size([(e)<-[:LIKED]-(:User {user_id: $user_id}) | 1]) > 0 AS is_liked_by_me,
               size([(e)<-[:REGISTERED]-(:User {user_id: $user_id}) | 1]) > 0 AS is_registered_by_me
        """
        records = await execute_query(
            cypher, {"event_id": event_id, "user_id": current_user_id or ""}, required=False
        )
        rec = records[0] if records else {}
        event["like_count"] = rec.get("like_count", 0)
        event["registration_count"] = rec.get("registration_count", 0)
        event["view_count"] = rec.get("view_count", 0)
        event["share_count"] = rec.get("share_count", 0)
        event["is_liked_by_me"] = bool(rec.get("is_liked_by_me", False))
        event["is_registered_by_me"] = bool(rec.get("is_registered_by_me", False))
        return event

    # ------------------------------------------------------------------ writes
    @staticmethod
    async def like_event(user_id: str, user_name: str, event_id: str) -> bool:
        await EventService._require_approved(event_id)
        await execute_query(
            """
            MERGE (u:User {user_id: $user_id})
            ON CREATE SET u.name = $user_name
            MERGE (e:Event {event_id: $event_id})
            MERGE (u)-[r:LIKED]->(e)
            RETURN r
            """,
            {"user_id": user_id, "user_name": user_name, "event_id": event_id},
        )
        return True

    @staticmethod
    async def unlike_event(user_id: str, event_id: str) -> bool:
        await execute_query(
            "MATCH (u:User {user_id: $user_id})-[r:LIKED]->(e:Event {event_id: $event_id}) DELETE r",
            {"user_id": user_id, "event_id": event_id},
        )
        return True

    @staticmethod
    async def register_event(user_id: str, user_name: str, event_id: str) -> bool:
        await EventService._require_approved(event_id)
        await execute_query(
            """
            MERGE (u:User {user_id: $user_id})
            ON CREATE SET u.name = $user_name
            MERGE (e:Event {event_id: $event_id})
            MERGE (u)-[r:REGISTERED]->(e)
            RETURN r
            """,
            {"user_id": user_id, "user_name": user_name, "event_id": event_id},
        )
        return True

    @staticmethod
    async def unregister_event(user_id: str, event_id: str) -> bool:
        await execute_query(
            "MATCH (u:User {user_id: $user_id})-[r:REGISTERED]->(e:Event {event_id: $event_id}) DELETE r",
            {"user_id": user_id, "event_id": event_id},
        )
        return True

    @staticmethod
    async def record_view(user_id: str, user_name: str, event_id: str) -> bool:
        await EventService._require_approved(event_id)
        now = utc_now_iso()
        await execute_query(
            """
            MERGE (u:User {user_id: $user_id})
            ON CREATE SET u.name = $user_name
            MERGE (e:Event {event_id: $event_id})
            MERGE (u)-[r:VIEWED]->(e)
            ON CREATE SET r.first_viewed_at = $now, r.last_viewed_at = $now, r.count = 1
            ON MATCH SET r.last_viewed_at = $now, r.count = coalesce(r.count, 0) + 1
            RETURN r
            """,
            {"user_id": user_id, "user_name": user_name, "event_id": event_id, "now": now},
        )
        return True

    @staticmethod
    async def record_share(user_id: str, user_name: str, event_id: str) -> bool:
        await EventService._require_approved(event_id)
        await execute_query(
            """
            MERGE (u:User {user_id: $user_id})
            ON CREATE SET u.name = $user_name
            MERGE (e:Event {event_id: $event_id})
            MERGE (u)-[r:SHARED]->(e)
            RETURN r
            """,
            {"user_id": user_id, "user_name": user_name, "event_id": event_id},
        )
        return True
