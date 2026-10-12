from urllib.parse import parse_qs, urlparse

import pytest

from app.config import Settings
from app.utils.security import create_access_token


# ----------------------------------------------------------------- health
async def test_health_reports_ok_when_both_databases_up(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "mongodb": "connected", "neo4j": "connected"}


async def test_health_degraded_when_graph_down(client, graph):
    """Regression: /health used to say 'connected' whenever a driver object existed."""
    graph.available = False
    body = (await client.get("/health")).json()
    assert body["status"] == "degraded"
    assert body["neo4j"] == "disconnected"
    assert body["mongodb"] == "connected"


# ----------------------------------------------------------------- config
def test_production_rejects_placeholder_secrets():
    s = Settings(ENVIRONMENT="production", JWT_SECRET_KEY="change_this_to_a_long_random_secret",
                 NEO4J_PASSWORD="change_me")
    problems = s.validate_for_runtime()
    assert len(problems) == 2


def test_production_accepts_real_secrets():
    s = Settings(ENVIRONMENT="production", JWT_SECRET_KEY="x" * 40, NEO4J_PASSWORD="a-real-password")
    assert s.validate_for_runtime() == []


# ----------------------------------------------------------------- register & login
async def test_register_creates_user_and_returns_token(client):
    r = await client.post("/api/auth/register", json={
        "name": "Ada Lovelace",
        "email": "ada@campus.test",
        "password": "secretpassword123",
        "year": 2,
        "department": "CSE"
    })
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["profile_completed"] is True
    assert data["role"] == "USER"
    assert "access_token" in data
    headers = {"Authorization": f"Bearer {data['access_token']}"}

    me = (await client.get("/api/users/me", headers=headers)).json()["data"]
    assert me["name"] == "Ada Lovelace"
    assert me["department"] == "CSE"
    assert me["year"] == 2


async def test_register_duplicate_email_fails(client):
    payload = {
        "name": "First User",
        "email": "unique@campus.test",
        "password": "secretpassword123",
        "year": 1,
        "department": "ECE"
    }
    r = await client.post("/api/auth/register", json=payload)
    assert r.status_code == 200

    r2 = await client.post("/api/auth/register", json=payload)
    assert r2.status_code == 400
    assert "already registered" in r2.json()["detail"].lower()


async def test_login_success_and_wrong_password(client):
    # Register user first
    await client.post("/api/auth/register", json={
        "name": "Login Tester",
        "email": "tester@campus.test",
        "password": "correct_password_here",
        "year": 3,
        "department": "MECH"
    })

    # Wrong password
    bad_login = await client.post("/api/auth/login", json={
        "email": "tester@campus.test",
        "password": "wrong_password"
    })
    assert bad_login.status_code == 401

    # Correct password
    good_login = await client.post("/api/auth/login", json={
        "email": "tester@campus.test",
        "password": "correct_password_here"
    })
    assert good_login.status_code == 200
    assert "access_token" in good_login.json()["data"]


async def test_session_endpoint_works(client):
    r = await client.post("/api/auth/register", json={
        "name": "Sam Doe",
        "email": "sam@campus.test",
        "password": "passwordsam123",
        "year": 1,
        "department": "IT"
    })
    headers = {"Authorization": f"Bearer {r.json()['data']['access_token']}"}
    sess = await client.get("/api/auth/session", headers=headers)
    assert sess.status_code == 200
    body = sess.json()["data"]
    assert body["name"] == "Sam Doe" and body["profile_completed"] is True
    assert (await client.get("/api/auth/session")).status_code == 401


async def test_register_admin_email_gets_admin_role(client):
    r = await client.post("/api/auth/register", json={
        "name": "Admin User",
        "email": "ADMIN@campus.test",
        "password": "adminpassword123",
        "year": 4,
        "department": "CSE"
    })
    assert r.status_code == 200
    assert r.json()["data"]["role"] == "ADMIN"


# ----------------------------------------------------------------- auth guards
async def test_missing_and_bad_tokens_are_401(client):
    assert (await client.get("/api/users/me")).status_code == 401
    r = await client.get("/api/users/me", headers={"Authorization": "Bearer nonsense"})
    assert r.status_code == 401


async def test_unhandled_error_is_generic(client, monkeypatch, make):
    """Regression: str(exc) used to be returned to clients."""
    from app.services.user_service import UserService

    async def boom(*a, **k):
        raise RuntimeError("db password is hunter2")

    monkeypatch.setattr(UserService, "search_users", staticmethod(boom))
    user = await make.user()
    transport_client = client
    # raise_app_exceptions is False on httpx's ASGITransport only via the handler path
    r = await transport_client.get("/api/users/search", params={"q": "a"}, headers=make.headers(user))
    assert r.status_code == 500
    assert "hunter2" not in r.text
