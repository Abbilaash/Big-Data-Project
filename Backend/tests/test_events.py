import pytest

VALID = {
    "title": "AI Hackathon",
    "description": "Build something with machine learning in 24 hours.",
    "category": "hackathon",
    "date": "2030-01-15",
    "start_time": "09:00",
    "end_time": "17:30",
    "venue": "Main Auditorium",
    "tags": ["AI", "ml", "ai"],
}


async def test_create_event_is_pending_and_canonicalised(client, make):
    host = await make.user("Host")
    r = await client.post("/api/events", json=VALID, headers=make.headers(host))
    assert r.status_code == 201
    ev = r.json()["data"]
    assert ev["status"] == "pending"
    assert ev["category"] == "Hackathon"           # canonical spelling
    assert ev["tags"] == ["AI", "ml"]               # de-duplicated case-insensitively
    assert ev["host_name"] == "Host"


@pytest.mark.parametrize("patch,field", [
    ({"registration_url": "javascript:alert(1)"}, "registration_url"),
    ({"poster_url": "data:text/html;base64,AAAA"}, "poster_url"),
    ({"end_time": "08:00"}, "end_time"),
    ({"date": "2030-02-31"}, "date"),
    ({"start_time": "25:99"}, "start_time"),
    ({"category": "Underwater Basket Weaving"}, "category"),
    ({"title": "  "}, "title"),
    ({"tags": ["x"] * 11}, "tags"),
])
async def test_create_event_rejects_invalid_input(client, make, patch, field):
    host = await make.user()
    r = await client.post("/api/events", json={**VALID, **patch}, headers=make.headers(host))
    assert r.status_code == 422, r.text
    assert field in r.text


async def test_create_event_requires_login(client):
    assert (await client.post("/api/events", json=VALID)).status_code == 401


async def test_pending_events_are_not_public(client, make):
    host = await make.user()
    await make.event(host, title="Draft", status="pending")
    await make.event(host, title="Live", status="approved")
    titles = [e["title"] for e in (await client.get("/api/events")).json()["data"]]
    assert titles == ["Live"]


async def test_public_list_works_without_auth_and_filters(client, make):
    host = await make.user()
    await make.event(host, title="Python Workshop", category="Workshop")
    await make.event(host, title="Cricket Contest", category="Sports", tags=["bat"])
    r = await client.get("/api/events", params={"category": "Workshop"})
    assert [e["title"] for e in r.json()["data"]] == ["Python Workshop"]
    r = await client.get("/api/events", params={"search": "cricket"})
    assert [e["title"] for e in r.json()["data"]] == ["Cricket Contest"]
    # regex metacharacters are treated literally
    r = await client.get("/api/events", params={"search": ".*"})
    assert r.json()["data"] == []


async def test_upcoming_excludes_past_events(client, make):
    host = await make.user()
    await make.event(host, title="Past", days=-3)
    await make.event(host, title="Soon", days=2)
    await make.event(host, title="Later", days=20)
    titles = [e["title"] for e in (await client.get("/api/events/upcoming")).json()["data"]]
    assert titles == ["Soon", "Later"]


async def test_categories_endpoint(client):
    cats = (await client.get("/api/events/categories")).json()["data"]["categories"]
    assert "Hackathon" in cats and "Other" in cats


# ------------------------------------------------------------- visibility
async def test_unapproved_event_hidden_from_others_visible_to_host_and_admin(client, make):
    host = await make.user("Host")
    other = await make.user("Other")
    admin = await make.user("Admin", role="ADMIN")
    ev = await make.event(host, status="pending")
    url = f"/api/events/{ev['event_id']}"
    assert (await client.get(url, headers=make.headers(other))).status_code == 404
    assert (await client.get(url, headers=make.headers(host))).status_code == 200
    assert (await client.get(url, headers=make.headers(admin))).status_code == 200


async def test_missing_event_is_404(client, make):
    u = await make.user()
    assert (await client.get("/api/events/EV_NOPE", headers=make.headers(u))).status_code == 404


# ------------------------------------------------------------- interactions
async def test_like_register_flow_updates_counts_and_flags(client, make):
    host = await make.user("Host")
    a = await make.user("Asha")
    b = await make.user("Bala")
    ev = await make.event(host)
    eid = ev["event_id"]

    for who in (a, b):
        assert (await client.post(f"/api/events/{eid}/like", headers=make.headers(who))).status_code == 200
    assert (await client.post(f"/api/events/{eid}/register", headers=make.headers(a))).status_code == 200
    # idempotent
    await client.post(f"/api/events/{eid}/like", headers=make.headers(a))

    d = (await client.get(f"/api/events/{eid}", headers=make.headers(a))).json()["data"]
    assert d["like_count"] == 2
    assert d["registration_count"] == 1
    assert d["is_liked_by_me"] and d["is_registered_by_me"]

    d = (await client.get(f"/api/events/{eid}", headers=make.headers(b))).json()["data"]
    assert d["is_liked_by_me"] and not d["is_registered_by_me"]

    await client.delete(f"/api/events/{eid}/like", headers=make.headers(a))
    await client.delete(f"/api/events/{eid}/register", headers=make.headers(a))
    d = (await client.get(f"/api/events/{eid}", headers=make.headers(a))).json()["data"]
    assert d["like_count"] == 1 and d["registration_count"] == 0
    assert not d["is_liked_by_me"] and not d["is_registered_by_me"]


async def test_list_includes_counts_for_signed_in_viewer(client, make):
    host = await make.user()
    me = await make.user("Me")
    ev = await make.event(host)
    await client.post(f"/api/events/{ev['event_id']}/register", headers=make.headers(me))
    row = (await client.get("/api/events", headers=make.headers(me))).json()["data"][0]
    assert row["registration_count"] == 1 and row["is_registered_by_me"] is True
    anon = (await client.get("/api/events")).json()["data"][0]
    assert anon["registration_count"] == 1 and anon["is_registered_by_me"] is False


async def test_cannot_interact_with_unapproved_event(client, make):
    host = await make.user()
    me = await make.user()
    ev = await make.event(host, status="pending")
    for action in ("like", "register", "view", "share"):
        r = await client.post(f"/api/events/{ev['event_id']}/{action}", headers=make.headers(me))
        assert r.status_code == 404, action


async def test_view_and_share_are_counted_once_per_user(client, make):
    host = await make.user()
    me = await make.user()
    ev = await make.event(host)
    eid = ev["event_id"]
    for _ in range(3):
        await client.post(f"/api/events/{eid}/view", headers=make.headers(me))
    await client.post(f"/api/events/{eid}/share", headers=make.headers(me))
    d = (await client.get(f"/api/events/{eid}", headers=make.headers(me))).json()["data"]
    assert d["view_count"] == 1          # unique viewers, not raw hits
    assert d["share_count"] == 1


async def test_my_registered_and_my_hosted(client, make):
    host = await make.user("Host")
    me = await make.user("Me")
    live = await make.event(host, title="Live")
    pending = await make.event(me, title="Mine pending", status="pending")
    await client.post(f"/api/events/{live['event_id']}/register", headers=make.headers(me))

    reg = (await client.get("/api/events/registered", headers=make.headers(me))).json()["data"]
    assert [e["title"] for e in reg] == ["Live"]
    mine = (await client.get("/api/events/my-hosted", headers=make.headers(me))).json()["data"]
    assert [e["event_id"] for e in mine] == [pending["event_id"]]


# ------------------------------------------------------------- graph outage
async def test_graph_write_failure_returns_503_not_false_success(client, make, graph):
    """Regression: failed graph writes used to report success."""
    host = await make.user()
    me = await make.user()
    ev = await make.event(host)
    graph.available = False
    r = await client.post(f"/api/events/{ev['event_id']}/like", headers=make.headers(me))
    assert r.status_code == 503
    graph.available = True
    d = (await client.get(f"/api/events/{ev['event_id']}", headers=make.headers(me))).json()["data"]
    assert d["like_count"] == 0


async def test_reads_degrade_gracefully_when_graph_down(client, make, graph):
    host = await make.user()
    me = await make.user()
    ev = await make.event(host)
    graph.available = False
    assert (await client.get("/api/events")).status_code == 200
    r = await client.get(f"/api/events/{ev['event_id']}", headers=make.headers(me))
    assert r.status_code == 200
    assert r.json()["data"]["like_count"] == 0
