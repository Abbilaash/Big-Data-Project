"""Shared fixtures.

Verification here is MOCKED: MongoDB is `mongomock-motor` and Neo4j is the
in-memory `FakeGraph`. No real database or Google service is contacted.
"""
import os
import sys
from datetime import timedelta
from pathlib import Path

import pytest
import pytest_asyncio

# Make `app` importable and keep tests hermetic regardless of any local .env.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ["ENVIRONMENT"] = "development"
os.environ["ADMIN_EMAIL"] = "admin@campus.edu"
os.environ["FRONTEND_URL"] = "http://localhost:3000"

import httpx  # noqa: E402
from mongomock_motor import AsyncMongoMockClient  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.utils.helpers import utc_now  # noqa: E402
from app.utils.security import create_access_token  # noqa: E402
from fake_graph import FakeGraph  # noqa: E402

get_settings.cache_clear()

GRAPH_CONSUMERS = [
    "app.services.admin_service",
    "app.services.auth_service",
    "app.services.event_service",
    "app.services.feed_service",
    "app.services.social_service",
    "app.services.user_service",
    "app.database.init_db",
]


@pytest.fixture
def graph(monkeypatch) -> FakeGraph:
    fake = FakeGraph()
    import importlib
    for name in GRAPH_CONSUMERS:
        module = importlib.import_module(name)
        monkeypatch.setattr(module, "execute_query", fake.execute_query)
    return fake


@pytest_asyncio.fixture
async def db(monkeypatch):
    from app.database import mongodb
    client = AsyncMongoMockClient()
    database = client["campusconnect_test"]
    monkeypatch.setattr(mongodb.db_manager, "client", client)
    monkeypatch.setattr(mongodb.db_manager, "db", database)
    yield database
    client.close()


@pytest_asyncio.fixture
async def client(db, graph, monkeypatch):
    import app.main as main_module

    async def healthy():
        return graph.available

    monkeypatch.setattr(main_module, "check_neo4j_health", healthy)
    transport = httpx.ASGITransport(app=main_module.app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class Factory:
    """Create users/events directly in the mock DB and mint tokens for them."""

    def __init__(self, db):
        self.db = db
        self._n = 0

    async def user(self, name="Student", *, role="USER", department="CSE", year=3,
                   completed=True, email=None):
        self._n += 1
        uid = f"USR_{self._n:08d}"
        doc = {
            "user_id": uid,
            "google_id": f"g{self._n}",
            "email": email or f"user{self._n}@campus.edu",
            "name": name,
            "year": year if completed else None,
            "department": department if completed else None,
            "profile_picture": None,
            "role": role,
            "profile_completed": completed,
            "created_at": utc_now(),
            "updated_at": utc_now(),
        }
        await self.db.users.insert_one(doc)
        return doc

    def headers(self, user):
        token = create_access_token({
            "sub": user["user_id"], "user_id": user["user_id"], "email": user["email"],
            "role": user["role"], "profile_completed": user["profile_completed"],
        })
        return {"Authorization": f"Bearer {token}"}

    async def event(self, host, *, title="Hack Night", status="approved", days=7,
                    category="Hackathon", **over):
        self._n += 1
        eid = f"EV_{self._n:08d}"
        date = (utc_now() + timedelta(days=days)).strftime("%Y-%m-%d")
        doc = {
            "event_id": eid, "title": title, "description": "A great campus event for everyone.",
            "category": category, "host_id": host["user_id"], "date": date,
            "start_time": "10:00", "end_time": "12:00", "venue": "Main Hall",
            "registration_url": None, "poster_url": None, "tags": ["ai"],
            "status": status, "created_at": utc_now(), "updated_at": utc_now(),
        }
        doc.update(over)
        await self.db.events.insert_one(doc)
        return doc


@pytest_asyncio.fixture
async def make(db):
    return Factory(db)
