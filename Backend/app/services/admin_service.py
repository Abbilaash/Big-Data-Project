import logging
from typing import Dict, Any, List, Optional
from app.database.mongodb import get_database
from app.database.neo4j import execute_query
from app.utils.helpers import utc_now

logger = logging.getLogger("campusconnect.admin_service")

class AdminService:
    @staticmethod
    async def get_pending_events() -> List[Dict[str, Any]]:
        db = get_database()
        cursor = db.events.find({"status": "pending"}).sort("created_at", -1)
        return await cursor.to_list(length=100)

    @staticmethod
    async def approve_event(event_id: str, admin_id: str) -> Dict[str, Any]:
        db = get_database()
        event = await db.events.find_one({"event_id": event_id})
        if not event:
            raise ValueError("Event not found")

        now = utc_now()
        await db.events.update_one(
            {"event_id": event_id},
            {
                "$set": {
                    "status": "approved",
                    "approved_at": now,
                    "approved_by": admin_id,
                    "updated_at": now
                }
            }
        )
        event["status"] = "approved"

        # Create Neo4j (:User {user_id: host_id})-[:HOSTED]->(:Event {event_id: event_id})
        host_id = event["host_id"]
        cypher = """
        MERGE (u:User {user_id: $host_id})
        MERGE (e:Event {event_id: $event_id})
        MERGE (u)-[r:HOSTED]->(e)
        RETURN r
        """
        await execute_query(cypher, {"host_id": host_id, "event_id": event_id})
        logger.info(f"Event {event_id} approved by admin {admin_id}. HOSTED relationship created in Neo4j.")
        return event

    @staticmethod
    async def reject_event(event_id: str, admin_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
        db = get_database()
        event = await db.events.find_one({"event_id": event_id})
        if not event:
            raise ValueError("Event not found")

        now = utc_now()
        await db.events.update_one(
            {"event_id": event_id},
            {
                "$set": {
                    "status": "rejected",
                    "rejected_at": now,
                    "rejected_by": admin_id,
                    "rejection_reason": reason,
                    "updated_at": now
                }
            }
        )
        event["status"] = "rejected"
        event["rejection_reason"] = reason
        logger.info(f"Event {event_id} rejected by admin {admin_id}.")
        return event

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

        return {
            "total_users": total_users,
            "total_follows": total_follows,
            "most_followed_users": mf_res,
            "most_interacted_events": most_interacted_events
        }
