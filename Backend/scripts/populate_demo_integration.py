import asyncio
import datetime
from app.database.mongodb import get_database, connect_to_mongo
from app.database.neo4j import execute_query, connect_to_neo4j

async def populate():
    await connect_to_mongo()
    await connect_to_neo4j()
    db = get_database()
    future = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    
    # 1. Insert approved event in Mongo
    ev = {
        "event_id": "EV_AI_HACK",
        "title": "PSG Big Data & AI Hackathon",
        "description": "A 24-hour hackathon exploring MongoDB, Neo4j, and XML data pipelines.",
        "category": "Hackathon",
        "venue": "CSE Seminar Hall, PSG Tech",
        "date": future,
        "start_time": "09:00",
        "end_time": "17:00",
        "host_id": "USR_9175919E",
        "status": "approved",
        "tags": ["bigdata", "nosql", "ai"],
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    await db.events.update_one({"event_id": "EV_AI_HACK"}, {"$set": ev}, upsert=True)
    
    # 2. Sync node and relationships in Neo4j
    await execute_query("MERGE (e:Event {event_id: 'EV_AI_HACK'}) SET e.title = $title", {"title": ev["title"]})
    await execute_query("MATCH (u:User {user_id: 'USR_9175919E'}), (e:Event {event_id: 'EV_AI_HACK'}) MERGE (u)-[:HOSTED]->(e)")
    await execute_query("MATCH (u:User {user_id: 'USR_B926ACAD'}), (e:Event {event_id: 'EV_AI_HACK'}) MERGE (u)-[:REGISTERED]->(e) MERGE (u)-[:LIKED]->(e)")
    print("Demo event and Neo4j graph relationships created successfully!")

if __name__ == "__main__":
    asyncio.run(populate())
