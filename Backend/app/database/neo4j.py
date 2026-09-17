import logging
from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from app.config import get_settings

logger = logging.getLogger("campusconnect.neo4j")

class Neo4jManager:
    driver: AsyncDriver = None

neo4j_manager = Neo4jManager()

async def connect_to_neo4j():
    settings = get_settings()
    logger.info(f"Connecting to Neo4j at {settings.NEO4J_URI}...")
    try:
        neo4j_manager.driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
        )
        await neo4j_manager.driver.verify_connectivity()
        logger.info("Successfully connected to Neo4j.")
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        logger.warning("WARNING: Neo4j is unreachable. Social graph features will be degraded. Check if your database instance is running/unpaused or update NEO4J_URI in .env.")
        # Keep driver set so app can attempt reconnection later if database resumes

async def close_neo4j_connection():
    if neo4j_manager.driver:
        logger.info("Closing Neo4j connection...")
        try:
            await neo4j_manager.driver.close()
        except Exception:
            pass
        logger.info("Neo4j connection closed.")

def get_neo4j_driver() -> AsyncDriver:
    if neo4j_manager.driver is None:
        raise RuntimeError("Neo4j database is unreachable or connection failed during startup.")
    return neo4j_manager.driver

async def execute_query(query: str, parameters: dict = None):
    """Utility helper to execute a Cypher query and return records as list of dicts."""
    try:
        driver = get_neo4j_driver()
        async with driver.session() as session:
            result = await session.run(query, parameters or {})
            records = await result.data()
            return records
    except Exception as e:
        logger.error(f"Cypher query execution error: {e}")
        return []

