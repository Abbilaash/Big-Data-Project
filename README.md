# CampusConnect

A campus event discovery and student networking platform built on a
**polyglot persistence** design: MongoDB holds content (users, events,
comments); Neo4j holds the social graph (follows and event interactions) and
powers the personalised feed, suggestions and network analytics.

- **Backend:** FastAPI (`Backend/`)
- **Frontend:** Next.js 16 + React 19 + Tailwind v4 (`frontend/`)
- **Docs:** [`docs/`](docs/) — start with [SETUP](docs/SETUP.md),
  [ARCHITECTURE](docs/ARCHITECTURE.md), [API](docs/API.md),
  [TESTING](docs/TESTING.md); decisions are in [ASSUMPTIONS](docs/ASSUMPTIONS.md)
  and history in [IMPLEMENTATION_LOG](docs/IMPLEMENTATION_LOG.md).

## What it does

- Register & Sign in with email and password.
- Browse, search and filter approved events; like, register, share, comment.
- Submit events; admins approve or reject them in a review queue.
- Follow classmates; your feed ranks events by what your connections
  registered for, shared, liked or viewed — and says why.
- Admin analytics from MongoDB aggregations and graph queries.

## Quick start

```bash
docker compose up -d                       # MongoDB + Neo4j (needs Docker)
cd Backend && python -m venv .venv && .venv/Scripts/activate   # or source .venv/bin/activate
pip install -r requirements.txt && cp .env.example .env        # edit secrets
python run.py                              # http://localhost:8000/docs
cd ../frontend && pnpm install && pnpm dev # http://localhost:3000
```

