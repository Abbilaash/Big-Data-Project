import logging
from typing import Dict, Any, List, Optional
from pymongo import ReturnDocument
from app.database.mongodb import get_database
from app.database.neo4j import execute_query
from app.services.event_service import EventService
from app.utils.errors import NotFoundError, ConflictError
from app.utils.helpers import utc_now

logger = logging.getLogger("campusconnect.admin_service")

class AdminService:
    @staticmethod
    async def get_events_by_status(status: str, limit: int = 100) -> List[Dict[str, Any]]:
        db = get_database()
        events = await db.events.find({"status": status}).sort("created_at", -1).to_list(length=limit)
        await EventService._attach_host_names(events)
        return events

    @staticmethod
    async def get_pending_events() -> List[Dict[str, Any]]:
        return await AdminService.get_events_by_status("pending")

    @staticmethod
    async def _transition(event_id: str, new_status: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Atomically move a PENDING event to a new status.

        The filter on status=pending makes concurrent or repeated moderation
        requests safe: only one can win, the rest get a 409.
        """
        db = get_database()
        now = utc_now()
        updated = await db.events.find_one_and_update(
            {"event_id": event_id, "status": "pending"},
            {"$set": {"status": new_status, "updated_at": now, **fields}},
            return_document=ReturnDocument.AFTER,
        )
        if updated is None:
            existing = await db.events.find_one({"event_id": event_id}, {"status": 1})
            if existing is None:
                raise NotFoundError("Event not found")
            raise ConflictError(f"Event is already {existing.get('status')} and cannot be moderated again")
        return updated

    @staticmethod
    async def approve_event(event_id: str, admin_id: str) -> Dict[str, Any]:
        db = get_database()
        event = await db.events.find_one({"event_id": event_id})
        if not event:
            raise NotFoundError("Event not found")
        if event.get("status") != "pending":
            raise ConflictError(f"Event is already {event.get('status')} and cannot be moderated again")

        # Graph first: MERGE is idempotent, and if the graph is down nothing has
        # changed yet, so the admin can simply retry (HTTP 503).
        await execute_query(
            """
            MERGE (u:User {user_id: $host_id})
            MERGE (e:Event {event_id: $event_id})
            MERGE (u)-[r:HOSTED]->(e)
            RETURN r
            """,
            {"host_id": event["host_id"], "event_id": event_id},
        )
        approved = await AdminService._transition(
            event_id, "approved", {"approved_at": utc_now(), "approved_by": admin_id}
        )
        await EventService._attach_host_names([approved])
        logger.info(f"Event {event_id} approved by admin {admin_id}.")
        return approved

    @staticmethod
    async def reject_event(event_id: str, admin_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
        rejected = await AdminService._transition(
            event_id,
            "rejected",
            {"rejected_at": utc_now(), "rejected_by": admin_id, "rejection_reason": reason},
        )
        await EventService._attach_host_names([rejected])
        logger.info(f"Event {event_id} rejected by admin {admin_id}.")
        return rejected

    @staticmethod
    async def get_event_analytics() -> Dict[str, Any]:
        """MongoDB Aggregation Pipeline for event analytics."""
        db = get_database()

        # Pipeline for status counts
        status_pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        status_results = await db.events.aggregate(status_pipeline).to_list(length=10)
        status_map = {r["_id"]: r["count"] for r in status_results}

        total_events = sum(status_map.values())
        approved_events = status_map.get("approved", 0)
        pending_events = status_map.get("pending", 0)
        rejected_events = status_map.get("rejected", 0)

        # Pipeline for categories
        category_pipeline = [
            {"$match": {"status": "approved"}},
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        category_results = await db.events.aggregate(category_pipeline).to_list(length=20)
        by_category = {r["_id"]: r["count"] for r in category_results}

        # Pipeline for events by host
        host_pipeline = [
            {"$group": {"_id": "$host_id", "total_submitted": {"$sum": 1}}},
            {"$sort": {"total_submitted": -1}},
            {"$limit": 10}
        ]
        host_results = await db.events.aggregate(host_pipeline).to_list(length=10)
        
        # Populate host names
        host_ids = [r["_id"] for r in host_results]
        users_cursor = db.users.find({"user_id": {"$in": host_ids}})
        users_map = {u["user_id"]: u.get("name", "Unknown") for u in await users_cursor.to_list(length=len(host_ids))}

        events_by_host = [
            {
                "host_id": r["_id"],
                "host_name": users_map.get(r["_id"], "Unknown"),
                "total_submitted": r["total_submitted"]
            }
            for r in host_results
        ]

        return {
            "total_events": total_events,
            "approved_events": approved_events,
            "pending_events": pending_events,
            "rejected_events": rejected_events,
            "by_category": by_category,
            "events_by_host": events_by_host
        }

    @staticmethod
    async def get_network_analytics() -> Dict[str, Any]:
        """Neo4j Graph Analytics for social network metrics."""
        users_query = "MATCH (u:User) RETURN count(u) AS total_users"
        follows_query = "MATCH ()-[r:FOLLOWS]->() RETURN count(r) AS total_follows"
        
        most_followed_query = """
        MATCH (u:User)<-[r:FOLLOWS]-(:User)
        RETURN u.user_id AS user_id, u.name AS name, count(r) AS follower_count
        ORDER BY follower_count DESC
        LIMIT 5
        """

        most_interacted_query = """
        MATCH (e:Event)<-[r:LIKED|REGISTERED|SHARED|VIEWED]-(:User)
        RETURN e.event_id AS event_id, count(r) AS interaction_count
        ORDER BY interaction_count DESC
        LIMIT 5
        """

        u_res = await execute_query(users_query)
        f_res = await execute_query(follows_query)
        mf_res = await execute_query(most_followed_query)
        mi_res = await execute_query(most_interacted_query)

        total_users = u_res[0]["total_users"] if u_res else 0
        total_follows = f_res[0]["total_follows"] if f_res else 0

        # Hydrate event titles from MongoDB for most interacted events
        event_ids = [r["event_id"] for r in mi_res]
        db = get_database()
        cursor = db.events.find({"event_id": {"$in": event_ids}})
        events_map = {e["event_id"]: e.get("title", "Unknown Event") for e in await cursor.to_list(length=len(event_ids))}

        most_interacted_events = [
            {
                "event_id": r["event_id"],
                "title": events_map.get(r["event_id"], "Unknown Event"),
                "interaction_count": r["interaction_count"]
            }
            for r in mi_res
        ]

        # Names from MongoDB (source of truth); graph copies can be stale.
        mf_ids = [r["user_id"] for r in mf_res]
        mf_docs = await db.users.find({"user_id": {"$in": mf_ids}}).to_list(length=len(mf_ids)) if mf_ids else []
        mf_names = {u["user_id"]: u.get("name") for u in mf_docs}
        most_followed_users = [
            {
                "user_id": r["user_id"],
                "name": mf_names.get(r["user_id"]) or r.get("name") or "Unknown",
                "follower_count": r["follower_count"],
            }
            for r in mf_res
        ]

        return {
            "total_users": total_users,
            "total_follows": total_follows,
            "most_followed_users": most_followed_users,
            "most_interacted_events": most_interacted_events
        }
