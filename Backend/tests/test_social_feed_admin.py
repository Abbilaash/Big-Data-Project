"""Social graph, personalised feed, comments and admin moderation/analytics."""


async def follow(client, make, a, b):
    r = await client.post(f"/api/social/follow/{b['user_id']}", headers=make.headers(a))
    assert r.status_code == 200, r.text


# ------------------------------------------------------------------ social
async def test_follow_unfollow_and_status(client, make):
    a = await make.user("Asha")
    b = await make.user("Bala")
    await follow(client, make, a, b)
    st = (await client.get(f"/api/social/status/{b['user_id']}", headers=make.headers(a))).json()["data"]
    assert st["is_following"] is True
    # directionality
    st = (await client.get(f"/api/social/status/{a['user_id']}", headers=make.headers(b))).json()["data"]
    assert st["is_following"] is False

    following = (await client.get("/api/social/following", headers=make.headers(a))).json()["data"]
    assert [u["user_id"] for u in following] == [b["user_id"]]
    followers = (await client.get("/api/social/followers", headers=make.headers(b))).json()["data"]
    assert [u["user_id"] for u in followers] == [a["user_id"]]

    await client.delete(f"/api/social/follow/{b['user_id']}", headers=make.headers(a))
    st = (await client.get(f"/api/social/status/{b['user_id']}", headers=make.headers(a))).json()["data"]
    assert st["is_following"] is False


async def test_cannot_follow_self_or_unknown_or_incomplete_user(client, make):
    a = await make.user("Asha")
    ghost = await make.user("Ghost", completed=False)
    r = await client.post(f"/api/social/follow/{a['user_id']}", headers=make.headers(a))
    assert r.status_code == 400
    r = await client.post("/api/social/follow/USR_NOPE", headers=make.headers(a))
    assert r.status_code == 400
    r = await client.post(f"/api/social/follow/{ghost['user_id']}", headers=make.headers(a))
    assert r.status_code == 400


async def test_follow_is_idempotent(client, make, graph):
    a = await make.user()
    b = await make.user()
    await follow(client, make, a, b)
    await follow(client, make, a, b)
    assert len([e for e in graph.edges if e[1] == "FOLLOWS"]) == 1


async def test_mutual_connections_regression(client, make):
    """Regression: get_mutuals matched on a non-existent `target_id` property and was always empty."""
    me, them, m1, m2, only_mine = [await make.user(n) for n in ("Me", "Them", "M1", "M2", "Mine")]
    for m in (m1, m2, only_mine):
        await follow(client, make, me, m)
    for m in (m1, m2):
        await follow(client, make, them, m)
    r = await client.get(f"/api/social/mutuals/{them['user_id']}", headers=make.headers(me))
    assert {u["name"] for u in r.json()["data"]} == {"M1", "M2"}


async def test_common_interests_one_row_per_event(client, make):
    """Regression: an event both users liked AND viewed used to appear several times."""
    host = await make.user()
    me = await make.user("Me")
    them = await make.user("Them")
    ev = await make.event(host, title="Shared Interest")
    eid = ev["event_id"]
    for user in (me, them):
        await client.post(f"/api/events/{eid}/like", headers=make.headers(user))
        await client.post(f"/api/events/{eid}/view", headers=make.headers(user))
    await client.post(f"/api/events/{eid}/register", headers=make.headers(them))

    rows = (await client.get(f"/api/social/common-interests/{them['user_id']}", headers=make.headers(me))).json()["data"]
    assert len(rows) == 1
    assert rows[0]["title"] == "Shared Interest"
    assert rows[0]["interaction_type"] == "You liked, they registered"


async def test_suggestions_rank_friends_of_friends_then_department(client, make):
    me = await make.user("Me", department="CSE")
    friend = await make.user("Friend", department="ECE")
    fof = await make.user("FriendOfFriend", department="ECE")
    same_dept = await make.user("SameDept", department="CSE")
    await make.user("Unrelated", department="MECH")
    await follow(client, make, me, friend)
    await follow(client, make, friend, fof)

    data = (await client.get("/api/users/suggestions", headers=make.headers(me))).json()["data"]
    names = [u["name"] for u in data]
    assert names[0] == "FriendOfFriend"
    assert data[0]["mutual_count"] == 1
    assert "SameDept" in names
    assert "Friend" not in names           # already followed
    assert "Me" not in names


async def test_directory_search_filters_and_hides_email(client, make):
    me = await make.user("Me", department="CSE")
    await make.user("Priya Raman", department="IT", year=2, email="secretmail@campus.edu")
    await make.user("Arun Nair", department="CSE", year=3)
    await make.user("Pending Person", completed=False)

    r = await client.get("/api/users", headers=make.headers(me))
    names = {u["name"] for u in r.json()["data"]}
    assert names == {"Priya Raman", "Arun Nair"}       # excludes self and incomplete profiles
    assert "email" not in r.text

    r = await client.get("/api/users", params={"department": "IT"}, headers=make.headers(me))
    assert [u["name"] for u in r.json()["data"]] == ["Priya Raman"]
    r = await client.get("/api/users", params={"q": "secretmail"}, headers=make.headers(me))
    assert r.json()["data"] == []                       # email is not searchable
    r = await client.get("/api/users/departments", headers=make.headers(me))
    assert set(r.json()["data"]) == {"CSE", "IT"}


async def test_profile_update_and_public_profile_counts(client, make):
    a = await make.user("Asha")
    b = await make.user("Bala")
    await follow(client, make, b, a)
    r = await client.patch("/api/users/me", json={"name": "Asha K", "year": 4}, headers=make.headers(a))
    assert r.status_code == 200 and r.json()["data"]["name"] == "Asha K"
    pub = (await client.get(f"/api/users/{a['user_id']}", headers=make.headers(b))).json()["data"]
    assert pub["followers_count"] == 1 and pub["following_count"] == 0
    assert "email" not in pub
    assert (await client.patch("/api/users/me", json={}, headers=make.headers(a))).status_code == 400
    bad = await client.patch("/api/users/me", json={"profile_picture": "javascript:alert(1)"}, headers=make.headers(a))
    assert bad.status_code == 422


# ------------------------------------------------------------------ feed
async def test_feed_ranks_by_action_weight_and_explains_why(client, make):
    host = await make.user("Host")
    me = await make.user("Me")
    f1 = await make.user("Priya")
    f2 = await make.user("Ravi")
    f3 = await make.user("Sam")
    for f in (f1, f2, f3):
        await follow(client, make, me, f)

    registered = await make.event(host, title="Registered by Priya")        # score 4
    viewed = await make.event(host, title="Viewed by all three")             # score 3 (1+1+1)
    liked = await make.event(host, title="Liked by Ravi")                    # score 2

    await client.post(f"/api/events/{registered['event_id']}/register", headers=make.headers(f1))
    for f in (f1, f2, f3):
        await client.post(f"/api/events/{viewed['event_id']}/view", headers=make.headers(f))
    await client.post(f"/api/events/{liked['event_id']}/like", headers=make.headers(f2))

    feed = (await client.get("/api/feed", headers=make.headers(me))).json()["data"]
    titles = [e["title"] for e in feed]
    assert titles[:3] == ["Registered by Priya", "Viewed by all three", "Liked by Ravi"]

    assert feed[0]["social_context"]["reason"] == "Priya registered for this event"
    assert feed[2]["social_context"]["reason"] == "Ravi liked this event"      # grammar regression
    assert feed[1]["social_context"]["reason"].endswith("2 other connections interacted with this event")


async def test_feed_reason_grammar_for_each_action(client, make):
    host = await make.user()
    me = await make.user()
    friend = await make.user("Fran")
    await follow(client, make, me, friend)
    cases = {}
    for action, phrase in (("share", "shared this event"), ("view", "viewed this event"),
                           ("like", "liked this event"), ("register", "registered for this event")):
        ev = await make.event(host, title=f"E-{action}")
        await client.post(f"/api/events/{ev['event_id']}/{action}", headers=make.headers(friend))
        cases[ev["title"]] = f"Fran {phrase}"
    feed = (await client.get("/api/feed", headers=make.headers(me))).json()["data"]
    got = {e["title"]: e["social_context"]["reason"] for e in feed if e["social_context"]}
    assert got == cases


async def test_feed_fallback_is_upcoming_only_and_unsocial(client, make):
    """Regression: fallback used to include past events."""
    host = await make.user()
    me = await make.user()
    await make.event(host, title="Past", days=-10)
    await make.event(host, title="Upcoming", days=5)
    feed = (await client.get("/api/feed", headers=make.headers(me))).json()["data"]
    assert [e["title"] for e in feed] == ["Upcoming"]
    assert feed[0]["social_context"] is None


async def test_feed_excludes_unapproved_and_past_social_events(client, make):
    host = await make.user()
    me = await make.user()
    friend = await make.user("Fran")
    await follow(client, make, me, friend)
    past = await make.event(host, title="Past", days=-2)
    ok = await make.event(host, title="OK")
    await client.post(f"/api/events/{ok['event_id']}/like", headers=make.headers(friend))
    await client.post(f"/api/events/{past['event_id']}/like", headers=make.headers(friend))
    feed = (await client.get("/api/feed", headers=make.headers(me))).json()["data"]
    assert [e["title"] for e in feed] == ["OK"]


async def test_feed_survives_graph_outage_with_fallback(client, make, graph):
    host = await make.user()
    me = await make.user()
    await make.event(host, title="Still Here")
    graph.available = False
    r = await client.get("/api/feed", headers=make.headers(me))
    assert r.status_code == 200
    assert [e["title"] for e in r.json()["data"]] == ["Still Here"]


# ------------------------------------------------------------------ comments
async def test_comment_lifecycle(client, make):
    host = await make.user("Host")
    me = await make.user("Me")
    other = await make.user("Other")
    admin = await make.user("Admin", role="ADMIN")
    ev = await make.event(host)
    base = f"/api/events/{ev['event_id']}/comments"

    r = await client.post(base, json={"content": "  Count me in!  "}, headers=make.headers(me))
    assert r.status_code == 201
    cid = r.json()["data"]["comment_id"]
    assert r.json()["data"]["content"] == "Count me in!"
    assert r.json()["data"]["user_name"] == "Me"

    assert (await client.post(base, json={"content": ""}, headers=make.headers(me))).status_code == 422
    assert (await client.post(base, json={"content": "x" * 1001}, headers=make.headers(me))).status_code == 422

    listed = (await client.get(base, headers=make.headers(other))).json()["data"]
    assert [c["content"] for c in listed] == ["Count me in!"]

    assert (await client.delete(f"{base}/{cid}", headers=make.headers(other))).status_code == 403
    assert (await client.delete(f"{base}/{cid}", headers=make.headers(me))).status_code == 200
    assert (await client.get(base, headers=make.headers(other))).json()["data"] == []

    r = await client.post(base, json={"content": "again"}, headers=make.headers(me))
    cid2 = r.json()["data"]["comment_id"]
    assert (await client.delete(f"{base}/{cid2}", headers=make.headers(admin))).status_code == 200


async def test_comments_on_unapproved_event_are_not_readable(client, make):
    """Regression: comments could be read for events that were not public."""
    host = await make.user()
    me = await make.user()
    ev = await make.event(host, status="pending")
    base = f"/api/events/{ev['event_id']}/comments"
    assert (await client.get(base, headers=make.headers(me))).status_code == 404
    assert (await client.post(base, json={"content": "hi there"}, headers=make.headers(me))).status_code == 404


# ------------------------------------------------------------------ admin
async def test_admin_endpoints_require_admin(client, make):
    user = await make.user()
    for path in ("/api/admin/events/pending", "/api/admin/analytics/events", "/api/admin/analytics/network"):
        assert (await client.get(path, headers=make.headers(user))).status_code == 403
        assert (await client.get(path)).status_code == 401
    ev = await make.event(user, status="pending")
    r = await client.post(f"/api/admin/events/{ev['event_id']}/approve", headers=make.headers(user))
    assert r.status_code == 403


async def test_moderation_lifecycle(client, make, graph):
    host = await make.user("Host")
    admin = await make.user("Admin", role="ADMIN")
    pend = await make.event(host, title="To Approve", status="pending")
    rej = await make.event(host, title="To Reject", status="pending")

    queue = (await client.get("/api/admin/events/pending", headers=make.headers(admin))).json()["data"]
    assert {e["title"] for e in queue} == {"To Approve", "To Reject"}
    assert queue[0]["host_name"] == "Host"

    r = await client.post(f"/api/admin/events/{pend['event_id']}/approve", headers=make.headers(admin))
    assert r.status_code == 200 and r.json()["data"]["status"] == "approved"
    assert (host["user_id"], "HOSTED", pend["event_id"]) in graph.edges

    r = await client.post(f"/api/admin/events/{rej['event_id']}/reject", headers=make.headers(admin),
                          json={"rejection_reason": "Duplicate of another event"})
    assert r.status_code == 200 and r.json()["data"]["status"] == "rejected"

    # host sees the reason on their own submission
    mine = (await client.get("/api/events/my-hosted", headers=make.headers(host))).json()["data"]
    reasons = {e["title"]: e["rejection_reason"] for e in mine}
    assert reasons["To Reject"] == "Duplicate of another event"

    # approved event is now public
    pub = [e["title"] for e in (await client.get("/api/events")).json()["data"]]
    assert pub == ["To Approve"]


async def test_moderation_state_transitions_are_enforced(client, make):
    """Regression: a rejected event could be approved (and vice versa) repeatedly."""
    host = await make.user()
    admin = await make.user(role="ADMIN")
    ev = await make.event(host, status="pending")
    eid = ev["event_id"]
    h = make.headers(admin)
    assert (await client.post(f"/api/admin/events/{eid}/approve", headers=h)).status_code == 200
    assert (await client.post(f"/api/admin/events/{eid}/approve", headers=h)).status_code == 409
    assert (await client.post(f"/api/admin/events/{eid}/reject", headers=h)).status_code == 409
    assert (await client.post("/api/admin/events/EV_NOPE/approve", headers=h)).status_code == 404


async def test_approve_when_graph_down_leaves_event_pending(client, make, graph):
    host = await make.user()
    admin = await make.user(role="ADMIN")
    ev = await make.event(host, status="pending")
    graph.available = False
    r = await client.post(f"/api/admin/events/{ev['event_id']}/approve", headers=make.headers(admin))
    assert r.status_code == 503
    graph.available = True
    queue = (await client.get("/api/admin/events/pending", headers=make.headers(admin))).json()["data"]
    assert [e["event_id"] for e in queue] == [ev["event_id"]]       # still retryable
    assert (await client.post(f"/api/admin/events/{ev['event_id']}/approve", headers=make.headers(admin))).status_code == 200


async def test_admin_lists_by_status(client, make):
    host = await make.user()
    admin = await make.user(role="ADMIN")
    await make.event(host, title="A", status="approved")
    await make.event(host, title="R", status="rejected")
    h = make.headers(admin)
    r = await client.get("/api/admin/events", params={"status": "rejected"}, headers=h)
    assert [e["title"] for e in r.json()["data"]] == ["R"]
    assert (await client.get("/api/admin/events", params={"status": "bogus"}, headers=h)).status_code == 422


async def test_analytics(client, make):
    host = await make.user("Host")
    admin = await make.user("Admin", role="ADMIN")
    u = await make.user("U")
    e1 = await make.event(host, category="Workshop")
    await make.event(host, category="Workshop")
    await make.event(host, category="Sports")
    await make.event(host, status="pending")
    await make.event(host, status="rejected")
    await follow(client, make, u, host)
    await follow(client, make, admin, host)
    await client.post(f"/api/events/{e1['event_id']}/like", headers=make.headers(u))

    ev = (await client.get("/api/admin/analytics/events", headers=make.headers(admin))).json()["data"]
    assert ev["total_events"] == 5 and ev["approved_events"] == 3
    assert ev["pending_events"] == 1 and ev["rejected_events"] == 1
    assert ev["by_category"] == {"Workshop": 2, "Sports": 1}
    assert ev["events_by_host"][0]["host_name"] == "Host"

    net = (await client.get("/api/admin/analytics/network", headers=make.headers(admin))).json()["data"]
    assert net["total_follows"] == 2
    assert net["most_followed_users"][0] == {"user_id": host["user_id"], "name": "Host", "follower_count": 2}
    assert net["most_interacted_events"][0]["event_id"] == e1["event_id"]


async def test_network_analytics_503_when_graph_down(client, make, graph):
    admin = await make.user(role="ADMIN")
    graph.available = False
    r = await client.get("/api/admin/analytics/network", headers=make.headers(admin))
    assert r.status_code == 503      # honest failure rather than silent zeros
