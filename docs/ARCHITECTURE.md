# Architecture

This describes the system **as implemented**. For the pre-existing analysis of
the original prototype see `PROJECT_DOCUMENTATION.md` (kept for history; where
it disagrees with this file, this file is current).

## Overview

```
Browser ── Next.js 16 app (frontend/, port 3000)
              │  fetch + Bearer JWT          lib/api.ts
              ▼
          FastAPI (Backend/, port 8000)
              routes → services → databases
              │                    │
        MongoDB (content)     Neo4j (graph)
              ▲
   Email + password sign-in (JWT)
```

| Concern | Store | Why |
|---|---|---|
| Users, events, comments | MongoDB | Rich documents, text search, aggregation pipelines |
| FOLLOWS, LIKED, REGISTERED, VIEWED, SHARED, HOSTED | Neo4j | Traversals (friends-of-friends, "what did my follows do") are the product's core queries |

The databases are joined **in application code** on shared IDs
(`USR_xxxxxxxx`, `EV_xxxxxxxx`). Neo4j nodes are deliberately thin
(`User{user_id,name,email}`, `Event{event_id}`); **MongoDB is the source of
truth for names and profile data** and is used to hydrate every response.

### The hybrid query pattern
1. Cypher returns IDs (and relationship types).
2. One batched `$in` query hydrates documents from MongoDB.
3. Python merges, ranks and shapes the response.

## Backend (`Backend/app`)

| Layer | Responsibility |
|---|---|
| `main.py` | App factory, lifespan (connect DBs, validate config, create indexes), CORS, exception handlers, `/health` |
| `config.py` | Typed settings from env / `.env`; production fail-fast validation |
| `routes/` | HTTP only: parse input, call a service, shape the `ApiResponse` envelope |
| `services/` | Business rules and all database access |
| `schemas/` | Request/response models and input validation |
| `database/` | Motor client, Neo4j driver, `execute_query`, index/constraint setup |
| `utils/` | JWT signing, PBKDF2 password hashing, ID helpers, domain errors |
| `dependencies.py` | Auth chain: token → user → active (profile complete) → admin; optional user for public endpoints |

### Error model
- Domain errors: `NotFoundError` → 404, `ConflictError` → 409 (global handlers).
- `GraphUnavailableError` → **503**. Graph **writes** (`required=True`) raise;
  decorative **reads** (counts, feed context, suggestions) pass
  `required=False` and degrade to empty results so a page still renders.
- Unhandled exceptions → generic 500; details only in server logs.

### Authentication
Email and password; the app issues its own HS256 JWT. (This replaced the
earlier Google OAuth flow in the team's commit `aeb11c6`, 2026-10-12.)
1. `POST /api/auth/register` creates the account (role = `ADMIN` iff the email
   equals `ADMIN_EMAIL`, otherwise `USER`) and returns a token.
2. `POST /api/auth/login` verifies the credentials and returns a token.
3. The browser keeps the token and sends it as a Bearer header.
4. The user row is re-read from MongoDB on every request, so role/profile
   changes apply immediately regardless of stale token claims.

### Event lifecycle (state machine)
```
pending ──approve──▶ approved
   └─────reject────▶ rejected          (terminal; no re-moderation)
```
Transitions are an atomic `find_one_and_update` filtered on `status=pending`,
so concurrent or repeated requests produce one winner and 409s. Approval
writes the `HOSTED` edge **first** (idempotent `MERGE`), so a graph outage
leaves the event pending and retryable rather than half-approved.

### Feed ranking (`services/feed_service.py`)
Events interacted with by people you follow, scored by summed action weight
(REGISTERED 4, SHARED 3, LIKED 2, VIEWED 1). Only approved, not-yet-past
events qualify. Each event carries a reason ("Priya registered for this
event"); friend names come from MongoDB. If fewer than `limit` items
qualify, the feed is padded with other upcoming approved events.

### Graph interaction counts
List endpoints attach `like_count`, `registration_count`, `is_liked_by_me`
and `is_registered_by_me` with **one batched Cypher query** per response
(`UNWIND $event_ids … size([(e)<-[:LIKED]-() | 1])`), not one query per event.
Counts are distinct users, so repeated requests cannot inflate them.

## Frontend (`frontend/`)

Next.js App Router, all pages client components talking to the API.

| Piece | Role |
|---|---|
| `lib/api.ts` | Typed client; bearer token from `localStorage`; normalises errors into `ApiError` (network / 401 / 422 field errors / 503) |
| `lib/auth.tsx` | `AuthProvider`: `loading → anonymous / needs-profile / ready / unavailable`; global 401 → sign-out |
| `components/auth-gate.tsx` | Central redirect rules; no protected content flashes |
| `lib/use-async.ts` | Loader hook that ignores stale responses |
| `lib/use-event-interactions.ts` | Optimistic like/register with rollback + toast |
| `components/link-button.tsx` | Real `<a>` styled as a button (Base UI's non-native Button renders `role="button"`) |
| `components/ranked-bars.tsx` | Single-series bar chart for admin analytics |

Routes: `/login`, `/auth/callback`, `/complete-profile`, `/` (feed
dashboard), `/events`, `/events/new`, `/events/[id]`, `/my-events`, `/people`,
`/people/[id]`, `/profile`, `/admin`. Old `/students*` and `/teammates`
permanently redirect to `/people`.

## Security posture

| Control | Where |
|---|---|
| Passwords hashed with salted PBKDF2-HMAC-SHA256 (100,000 iterations), constant-time compare, one generic error for unknown email or wrong password | `utils/security.py`, `services/auth_service.py` |
| http(s)-only URLs for poster/registration/avatar | `schemas/validators.py` |
| Server-side validation of all inputs (dates, times, lengths, categories) | `schemas/` |
| Escaped regex for all text search | `re.escape` in services |
| Draft events invisible to others (404, not 403) | `routes/events.py` |
| Email never exposed in public profiles or searchable | `services/social_service.py` |
| Narrow CORS (explicit methods/headers/origins) | `main.py` |
| Production refuses placeholder secrets | `config.validate_for_runtime` |
| No stack/exception text to clients | `main.py` |

Known gaps: **no email verification, so whoever registers the `ADMIN_EMAIL` address first becomes ADMIN** (register the real admin account immediately after deploying, and consider email verification); no login rate limiting or lockout; PBKDF2 at 100,000 iterations is below current OWASP guidance for SHA-256 (600,000); no rate limiting elsewhere; JWT in `localStorage` is readable by XSS (React
escapes output and no `dangerouslySetInnerHTML` is used); no token revocation
other than expiry (default 24 h).

## Deployment shape
Stateless API (scale horizontally behind a load balancer; set a shared
`JWT_SECRET_KEY`), MongoDB and Neo4j as managed or self-hosted services,
frontend built with `next build` and served by `next start` or any Node host.
No Dockerfiles for the apps are provided.
