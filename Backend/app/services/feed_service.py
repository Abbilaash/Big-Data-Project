import logging
from typing import Dict, Any, List
from collections import defaultdict

from app.database.mongodb import get_database
from app.database.neo4j import execute_query
from app.utils.helpers import utc_now

logger = logging.getLogger("campusconnect.feed_service")

# Action weight for ranking
ACTION_WEIGHTS = {
    "REGISTERED": 4,
    "SHARED": 3,
    "LIKED": 2,
    "VIEWED": 1
}

class FeedService:
    @staticmethod
    async def get_personalized_feed(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        1. Neo4j Query: Find events interacted with by followed users.
        2. Rank events based on interaction weight & frequency.
        3. MongoDB Query: Fetch complete event documents in batch ($in).
        4. Combine event data with social context.
        5. Fallback: Fill remaining slots with upcoming approved events.
        """
        cypher_query = """
        MATCH (me:User {user_id: $user_id})-[:FOLLOWS]->(friend:User)-[r:LIKED|REGISTERED|SHARED|VIEWED]->(e:Event)
        RETURN e.event_id AS event_id,
               friend.user_id AS friend_id,
               friend.name AS friend_name,
               type(r) AS interaction_type
        """
        records = await execute_query(cypher_query, {"user_id": user_id})

        # Group interactions by event_id
        event_interactions = defaultdict(list)
        event_scores = defaultdict(int)

        for rec in records:
            eid = rec["event_id"]
            action = rec["interaction_type"]
            friend_id = rec["friend_id"]
            friend_name = rec["friend_name"] or "Someone"

            event_interactions[eid].append({
                "user_id": friend_id,
                "name": friend_name,
                "action": action
            })
            event_scores[eid] += ACTION_WEIGHTS.get(action, 1)

        # Sort event IDs by social score descending
        sorted_event_ids = sorted(event_scores.keys(), key=lambda k: event_scores[k], reverse=True)

        social_feed_items = []
        db = get_database()

        if sorted_event_ids:
            # Batch fetch from MongoDB
            cursor = db.events.find({
                "event_id": {"$in": sorted_event_ids},
                "status": "approved"
            })
            mongo_events = await cursor.to_list(length=len(sorted_event_ids))
            events_by_id = {e["event_id"]: e for e in mongo_events}

            # Assemble feed items in sorted order
            for eid in sorted_event_ids:
                if eid in events_by_id:
                    event = events_by_id[eid]
                    users_list = event_interactions[eid]

                    # Deduplicate user actions (keep highest priority action per user if needed)
                    user_action_map = {}
                    for u in users_list:
                        uid = u["user_id"]
                        if uid not in user_action_map or ACTION_WEIGHTS.get(u["action"], 0) > ACTION_WEIGHTS.get(user_action_map[uid]["action"], 0):
                            user_action_map[uid] = u
                    
                    unique_users = list(user_action_map.values())
                    top_user = unique_users[0]
                    
                    if len(unique_users) == 1:
                        action_verb = top_user["action"].lower()
                        reason = f"{top_user['name']} {action_verb} for this event"
                    else:
                        reason = f"{top_user['name']} and {len(unique_users) - 1} other connection{'s' if len(unique_users) > 2 else ''} interacted with this event"

                    event["social_context"] = {
                        "reason": reason,
                        "users": unique_users
                    }
                    social_feed_items.append(event)

        # Fallback section: If social feed items < limit, add upcoming approved events
        existing_eids = {item["event_id"] for item in social_feed_items}
        if len(social_feed_items) < limit:
            remaining_limit = limit - len(social_feed_items)
            today = utc_now().strftime("%Y-%m-%d")
            
            fallback_cursor = db.events.find({
                "status": "approved",
                "event_id": {"$nin": list(existing_eids)}
            }).sort("date", 1).limit(remaining_limit)
            
            fallback_events = await fallback_cursor.to_list(length=remaining_limit)
            for fe in fallback_events:
                fe["social_context"] = None
                social_feed_items.append(fe)

        return social_feed_items[:limit]
