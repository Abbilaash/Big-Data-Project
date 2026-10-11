import logging
from typing import Optional

from neo4j import AsyncGraphDatabase, AsyncDriver
from app.config import get_settings

logger = logging.getLogger("campusconnect.neo4j")


class GraphUnavailableError(RuntimeError):
    """Raised when a graph operation that must succeed cannot be executed."""


class Neo4jManager:
    driver: Optional[AsyncDriver] = None
    connected: bool = False


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
        neo4j_manager.connected = True
        logger.info("Successfully connected to Neo4j.")
    except Exception as e:
        neo4j_manager.connected = False
        logger.error(f"Failed to connect to Neo4j: {e}")
        logger.warning(
            "Neo4j is unreachable. Social graph features are degraded; graph writes "
            "will return 503 until it is available."
        )
        # The driver is kept so queries can succeed once the database comes back.


async def close_neo4j_connection():
    if neo4j_manager.driver:
        logger.info("Closing Neo4j connection...")
        try:
            await neo4j_manager.driver.close()
        except Exception:
            pass
        neo4j_manager.connected = False
        logger.info("Neo4j connection closed.")


def get_neo4j_driver() -> AsyncDriver:
    if neo4j_manager.driver is None:
        raise GraphUnavailableError("Graph database is not configured.")
    return neo4j_manager.driver


async def check_neo4j_health() -> bool:
    """Live connectivity probe used by /health."""
    if neo4j_manager.driver is None:
        return False
    try:
        await neo4j_manager.driver.verify_connectivity()
        neo4j_manager.connected = True
        return True
    except Exception:
        neo4j_manager.connected = False
        return False


async def execute_query(query: str, parameters: dict = None, *, required: bool = True):
    """Execute a Cypher query and return records as a list of dicts.

    required=True (default): failures raise GraphUnavailableError so writes can
    never report success when the graph was not updated.
    required=False: failures are logged and an empty list is returned. Use this
    only for decorative reads where a degraded page beats an error page.
    """
    try:
        driver = get_neo4j_driver()
        async with driver.session() as session:
            result = await session.run(query, parameters or {})
            return await result.data()
    except Exception as e:
        logger.error(f"Cypher query execution error: {e}")
        if required:
            raise GraphUnavailableError("Graph database is unavailable.") from e
        return []
