import logging
from pymongo import ASCENDING, IndexModel
from app.database.mongodb import get_database
from app.database.neo4j import execute_query

logger = logging.getLogger("campusconnect.init_db")

async def initialize_databases():
    """Create indexes and constraints for MongoDB and Neo4j."""
    logger.info("Initializing database indexes and constraints...")
    
    # 1. MongoDB Indexes
    try:
        db = get_database()
        
        # User indexes
        await db.users.create_index([("user_id", ASCENDING)], unique=True)
        await db.users.create_index([("email", ASCENDING)], unique=True)
        await db.users.create_index([("google_id", ASCENDING)], unique=True, sparse=True)
        
        # Event indexes
        await db.events.create_index([("event_id", ASCENDING)], unique=True)
        await db.events.create_index([("status", ASCENDING)])
        await db.events.create_index([("category", ASCENDING)])
        await db.events.create_index([("date", ASCENDING)])
        await db.events.create_index([("host_id", ASCENDING)])
        
        # Comments indexes
        await db.comments.create_index([("comment_id", ASCENDING)], unique=True)
        await db.comments.create_index([("event_id", ASCENDING)])
        
        logger.info("MongoDB indexes created successfully.")
    except Exception as e:
        logger.warning(f"Error creating MongoDB indexes: {e}")

    # 2. Neo4j Constraints
    try:
        user_constraint_query = (
            "CREATE CONSTRAINT user_id_unique IF NOT EXISTS "
            "FOR (u:User) REQUIRE u.user_id IS UNIQUE"
        )
        event_constraint_query = (
            "CREATE CONSTRAINT event_id_unique IF NOT EXISTS "
            "FOR (e:Event) REQUIRE e.event_id IS UNIQUE"
        )
        
        await execute_query(user_constraint_query)
        await execute_query(event_constraint_query)
        logger.info("Neo4j constraints created successfully.")
    except Exception as e:
        logger.warning(f"Error creating Neo4j constraints: {e}")
