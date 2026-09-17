import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import get_settings

logger = logging.getLogger("campusconnect.mongodb")

class MongoDBManager:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None

db_manager = MongoDBManager()

async def connect_to_mongo():
    settings = get_settings()
    logger.info(f"Connecting to MongoDB at {settings.MONGO_URI}...")
    try:
        db_manager.client = AsyncIOMotorClient(settings.MONGO_URI)
        db_manager.db = db_manager.client[settings.MONGO_DB_NAME]
        # Ping the server to verify connectivity
        await db_manager.client.admin.command('ping')
        logger.info(f"Successfully connected to MongoDB database: {settings.MONGO_DB_NAME}")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise e

async def close_mongo_connection():
    if db_manager.client:
        logger.info("Closing MongoDB connection...")
        db_manager.client.close()
        logger.info("MongoDB connection closed.")

def get_database() -> AsyncIOMotorDatabase:
    if db_manager.db is None:
        raise RuntimeError("MongoDB connection is not initialized.")
    return db_manager.db
