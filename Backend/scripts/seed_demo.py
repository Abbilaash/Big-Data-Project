"""Populate a running CampusConnect backend with demo data through its public API.

Accounts are created with POST /api/auth/register (or signed in with
POST /api/auth/login if they already exist), so every demo user can later sign in
with the password below. ADMIN_EMAIL on the server must equal --admin-email for
that account to receive the ADMIN role. Everything goes through the same HTTP
endpoints the frontend uses, so it works against real MongoDB/Neo4j.

    python scripts/seed_demo.py --base-url http://localhost:8000 --admin-email admin@campus.edu

Re-running is safe for users (dev login is idempotent) but will create duplicate
events, so run it once per database.
"""
import argparse
import sys
from datetime import date, timedelta

import httpx

DEMO_PASSWORD = "DemoPass123!"  # demo accounts only

PEOPLE = [
    ("Priya Raman", "priya@campus.edu", 3, "CSE"),
    ("Arun Nair", "arun@campus.edu", 3, "CSE"),
    ("Meera Iyer", "meera@campus.edu", 2, "IT"),
    ("Karthik S", "karthik@campus.edu", 4, "ECE"),
    ("Divya Menon", "divya@campus.edu", 1, "AI&DS"),
]

EVENTS = [
    # (host index, title, category, days from today, start, end, venue, description, tags)
    (0, "24-hour AI Hackathon", "Hackathon", 9, "09:00", "17:00", "Main Auditorium",
     "Build something with machine learning in a day. Teams of up to four; mentors on site.", ["ai", "ml"]),
    (1, "Web Development Workshop", "Workshop", 5, "10:00", "13:00", "Lab 3, CSE Block",
     "A hands-on introduction to building modern web apps with React and an API backend.", ["web", "react"]),
    (2, "Cloud Computing Bootcamp", "Bootcamp", 14, "09:30", "16:30", "Seminar Hall B",
     "Two practical sessions on deploying containers and managed databases in the cloud.", ["cloud", "devops"]),
    (3, "Embedded Systems Seminar", "Seminar", 7, "14:00", "15:30", "ECE Auditorium",
     "Industry speakers on real-time operating systems and low-power design.", ["embedded", "iot"]),
    (4, "Inter-department Coding Contest", "Contest", 11, "11:00", "14:00", "Computer Centre",
     "Individual competitive programming contest with problems for every skill level.", ["dsa", "contest"]),
    (0, "Open Source Meetup", "Meetup", 3, "17:00", "18:30", "Library Atrium",
     "Casual meetup to find projects, share contribution tips and pair on first issues.", ["oss", "git"]),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8000")
    ap.add_argument("--admin-email", default="admin@campus.edu")
    args = ap.parse_args()

    http = httpx.Client(base_url=args.base_url.rstrip("/"), timeout=15.0)

    def login(email: str, name: str, year: int = 4, department: str = "IT") -> dict:
        """Register the account, or sign in if it already exists."""
        r = http.post("/api/auth/register", json={
            "name": name, "email": email, "password": DEMO_PASSWORD,
            "year": year, "department": department,
        })
        if r.status_code == 400:  # already registered: sign in instead
            r = http.post("/api/auth/login", json={"email": email, "password": DEMO_PASSWORD})
            if r.status_code == 401:
                sys.exit(f"{email} exists with a different password; cannot seed as that user.")
        r.raise_for_status()
        data = r.json()["data"]
        return {"user_id": data["user_id"], "role": data["role"],
                "headers": {"Authorization": f"Bearer {data['access_token']}"}}

    def call(method: str, path: str, who: dict, **kw):
        r = http.request(method, path, headers=who["headers"], **kw)
        r.raise_for_status()
        return r.json()["data"]

    admin = login(args.admin_email, "Campus Admin")
    if admin["role"] != "ADMIN":
        sys.exit(f"{args.admin_email} did not receive the ADMIN role; check ADMIN_EMAIL on the server.")
    people = [login(email, name, year, dept) for name, email, year, dept in PEOPLE]
    print(f"Signed in {len(people)} students and 1 admin.")

    event_ids = []
    today = date.today()
    for host, title, cat, days, start, end, venue, desc, tags in EVENTS:
        created = call("POST", "/api/events", people[host], json={
            "title": title, "category": cat, "date": (today + timedelta(days=days)).isoformat(),
            "start_time": start, "end_time": end, "venue": venue, "description": desc, "tags": tags,
        })
        event_ids.append(created["event_id"])
    # Leave the last one pending so the moderation queue has something in it.
    for event_id in event_ids[:-1]:
        call("POST", f"/api/admin/events/{event_id}/approve", admin)
    print(f"Created {len(event_ids)} events ({len(event_ids) - 1} approved, 1 pending).")

    # A small follow graph: everyone follows the next two people.
    for i, who in enumerate(people):
        for offset in (1, 2):
            call("POST", f"/api/social/follow/{people[(i + offset) % len(people)]['user_id']}", who)

    # Interactions that give the feed something to rank.
    approved = event_ids[:-1]
    plan = {
        0: [(0, "register"), (1, "like"), (3, "view")],
        1: [(0, "like"), (2, "register"), (4, "share")],
        2: [(0, "register"), (1, "register"), (4, "like")],
        3: [(2, "like"), (3, "register")],
        4: [(0, "view"), (1, "like"), (4, "register")],
    }
    for person_idx, actions in plan.items():
        for event_idx, action in actions:
            call("POST", f"/api/events/{approved[event_idx]}/{action}", people[person_idx])
    call("POST", f"/api/events/{approved[0]}/comments", people[1], json={"content": "Count me in!"})
    print("Seeded follows, registrations, likes, shares and a comment.")
    print(f"Sign in with password {DEMO_PASSWORD!r} as {args.admin_email} (admin) or any of: " + ", ".join(e for _, e, _, _ in PEOPLE))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
