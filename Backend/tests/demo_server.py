"""Run the REAL FastAPI app against in-memory MOCKS of MongoDB and Neo4j.

    python tests/demo_server.py            # serves on http://localhost:8000

Purpose: exercise the genuine backend code and the genuine frontend end to end
on a machine with no database servers. Data lives in memory and is lost on
exit. This is a verification harness, NOT a deployment mode:
  * MongoDB is `mongomock-motor`.
  * Neo4j is `tests/fake_graph.FakeGraph` (it recognises only the Cypher this
    codebase issues and does not prove Cypher validity against a real server).
  * Google OAuth is not available; dev login is enabled.
"""
import importlib
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("ENABLE_DEV_LOGIN", "true")
os.environ.setdefault("ADMIN_EMAIL", "admin@campus.local")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")

import uvicorn  # noqa: E402
from mongomock_motor import AsyncMongoMockClient  # noqa: E402

from fake_graph import FakeGraph  # noqa: E402

import app.main as main_module  # noqa: E402
from app.database import mongodb  # noqa: E402

graph = FakeGraph()
for name in (
    "app.services.admin_service",
    "app.services.auth_service",
    "app.services.event_service",
    "app.services.feed_service",
    "app.services.social_service",
    "app.services.user_service",
    "app.database.init_db",
):
    importlib.import_module(name).execute_query = graph.execute_query


async def _connect_mongo():
    client = AsyncMongoMockClient()
    mongodb.db_manager.client = client
    mongodb.db_manager.db = client["campusconnect_demo"]


async def _connect_graph():
    return None


async def _graph_healthy():
    return graph.available


main_module.connect_to_mongo = _connect_mongo
main_module.connect_to_neo4j = _connect_graph
main_module.close_neo4j_connection = _connect_graph
main_module.check_neo4j_health = _graph_healthy

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print(f"[demo] in-memory MOCK databases; http://localhost:{port}/docs", flush=True)
    uvicorn.run(main_module.app, host="127.0.0.1", port=port, log_level="info")
