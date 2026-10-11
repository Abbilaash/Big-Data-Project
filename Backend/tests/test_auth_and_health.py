from urllib.parse import parse_qs, urlparse

import pytest

from app.config import Settings
from app.utils.security import create_oauth_state, create_access_token


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


def test_dev_login_never_enabled_in_production():
    s = Settings(ENVIRONMENT="production", ENABLE_DEV_LOGIN=True)
    assert s.dev_login_enabled is False


# ----------------------------------------------------------------- dev login
async def test_dev_login_creates_incomplete_user_then_completes_profile(client):
    r = await client.post("/api/auth/dev-login", json={"email": "ada@campus.test", "name": "Ada"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["profile_completed"] is False
    assert data["role"] == "USER"
    headers = {"Authorization": f"Bearer {data['access_token']}"}

    # Incomplete profiles are blocked from app endpoints.
    assert (await client.get("/api/users/me", headers=headers)).status_code == 403

    r = await client.post(
        "/api/auth/complete-profile", headers=headers,
        json={"name": "Ada L", "year": 2, "department": "CSE"},
    )
    assert r.status_code == 200
    assert r.json()["data"]["profile_completed"] is True
    headers = {"Authorization": f"Bearer {r.json()['data']['access_token']}"}
    me = (await client.get("/api/users/me", headers=headers)).json()["data"]
    assert me["name"] == "Ada L" and me["department"] == "CSE"


async def test_session_endpoint_works_before_profile_completion(client):
    r = await client.post("/api/auth/dev-login", json={"email": "s@campus.test", "name": "Sam Doe"})
    headers = {"Authorization": f"Bearer {r.json()['data']['access_token']}"}
    r = await client.get("/api/auth/session", headers=headers)
    assert r.status_code == 200
    body = r.json()["data"]
    assert body["name"] == "Sam Doe" and body["profile_completed"] is False
    assert (await client.get("/api/auth/session")).status_code == 401


async def test_dev_login_admin_email_gets_admin_role(client):
    r = await client.post("/api/auth/dev-login", json={"email": "ADMIN@campus.test", "name": "Admin"})
    assert r.json()["data"]["role"] == "ADMIN"


async def test_dev_login_disabled_returns_404(client, monkeypatch):
    from app.config import get_settings
    monkeypatch.setattr(get_settings(), "ENABLE_DEV_LOGIN", False)
    r = await client.post("/api/auth/dev-login", json={"email": "x@campus.test", "name": "X"})
    assert r.status_code == 404


async def test_complete_profile_succeeds_while_graph_down(client, graph):
    """Onboarding must not depend on the graph (nodes are created lazily)."""
    r = await client.post("/api/auth/dev-login", json={"email": "g@campus.test", "name": "G"})
    headers = {"Authorization": f"Bearer {r.json()['data']['access_token']}"}
    graph.available = False
    r = await client.post("/api/auth/complete-profile", headers=headers,
                          json={"name": "G", "year": 1, "department": "IT"})
    assert r.status_code == 200


# ----------------------------------------------------------------- oauth
async def test_login_url_contains_signed_state(client):
    r = await client.get("/api/auth/google/login", params={"redirect": "false"})
    url = r.json()["data"]["authorization_url"]
    state = parse_qs(urlparse(url).query)["state"][0]
    from app.utils.security import verify_oauth_state
    assert verify_oauth_state(state)


async def test_callback_rejects_missing_or_forged_state(client):
    """Regression: state used to be ignored, giving no CSRF protection."""
    for params in ({"code": "abc"}, {"code": "abc", "state": "default_state"}):
        r = await client.get("/api/auth/google/callback", params=params, follow_redirects=False)
        assert r.status_code == 302
        assert r.headers["location"].startswith("http://localhost:3000/login#error=")


async def test_callback_rejects_access_token_used_as_state(client):
    token = create_access_token({"user_id": "USR_X"})
    r = await client.get("/api/auth/google/callback", params={"code": "abc", "state": token},
                         follow_redirects=False)
    assert "/login#error=" in r.headers["location"]


async def test_callback_success_puts_token_in_fragment_not_query(client, monkeypatch):
    from app.services.auth_service import AuthService

    async def fake_exchange(code):
        return {"id": "google-123", "email": "new@campus.test", "name": "New", "picture": ""}

    monkeypatch.setattr(AuthService, "exchange_google_code", staticmethod(fake_exchange))
    r = await client.get(
        "/api/auth/google/callback",
        params={"code": "abc", "state": create_oauth_state()},
        follow_redirects=False,
    )
    assert r.status_code == 302
    loc = urlparse(r.headers["location"])
    assert loc.path == "/auth/callback"
    assert loc.query == ""                       # token never in the query string
    frag = parse_qs(loc.fragment)
    assert frag["profile_completed"] == ["false"]
    assert frag["token"][0].count(".") == 2     # JWT


async def test_callback_does_not_leak_exception_text(client, monkeypatch):
    from app.services.auth_service import AuthService

    async def boom(code):
        raise RuntimeError("secret internal detail 10.0.0.5")

    monkeypatch.setattr(AuthService, "exchange_google_code", staticmethod(boom))
    r = await client.get("/api/auth/google/callback",
                         params={"code": "abc", "state": create_oauth_state()}, follow_redirects=False)
    assert "secret" not in r.headers["location"]
    assert "10.0.0.5" not in r.headers["location"]


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
