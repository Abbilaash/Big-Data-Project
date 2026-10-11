# CampusConnect — Full Project Documentation

> **Historical document.** This is the analysis of the repository *before* the
> implementation work of 2026-10-11 (frontend was a static prototype; the
> defects in §10 have since been fixed). For the current system see
> [ARCHITECTURE.md](ARCHITECTURE.md), [API.md](API.md), [SETUP.md](SETUP.md) and
> [IMPLEMENTATION_LOG.md](IMPLEMENTATION_LOG.md).

> A detailed walkthrough of every part of the **Big-Data-Project** repository: what it does, how it is built, how the pieces fit together, and what is still missing.

---

## Table of Contents

1. [What the project is](#1-what-the-project-is)
2. [Repository layout](#2-repository-layout)
3. [Tech stack](#3-tech-stack)
4. [High-level architecture](#4-high-level-architecture)
5. [Backend in detail](#5-backend-in-detail)
   - 5.1 [Entry points & startup](#51-entry-points--startup)
   - 5.2 [Configuration](#52-configuration-appconfigpy)
   - 5.3 [Database layer](#53-database-layer-appdatabase)
   - 5.4 [Authentication & authorization](#54-authentication--authorization)
   - 5.5 [Data models (MongoDB documents)](#55-data-models-mongodb-documents)
   - 5.6 [Neo4j graph model](#56-neo4j-graph-model)
   - 5.7 [Schemas (API request/response shapes)](#57-schemas-api-requestresponse-shapes)
   - 5.8 [Routes (every API endpoint)](#58-routes-every-api-endpoint)
   - 5.9 [Services (business logic)](#59-services-business-logic)
   - 5.10 [Utilities](#510-utilities)
6. [Frontend in detail](#6-frontend-in-detail)
   - 6.1 [Configuration files](#61-configuration-files)
   - 6.2 [Pages (routes)](#62-pages-routes)
   - 6.3 [Feature components](#63-feature-components)
   - 6.4 [UI primitives](#64-ui-primitives-componentsui)
   - 6.5 [Mock data](#65-mock-data-libdatats)
   - 6.6 [Styling](#66-styling)
7. [End-to-end flows](#7-end-to-end-flows)
8. [Running the project locally](#8-running-the-project-locally)
9. [Frontend ↔ Backend gap analysis](#9-frontend--backend-gap-analysis)
10. [Known bugs & issues found during review](#10-known-bugs--issues-found-during-review)
11. [Suggested next steps](#11-suggested-next-steps)
12. [Git history](#12-git-history)

---

## 1. What the project is

**CampusConnect** is a social-media-style **college event discovery and student networking platform** (the FastAPI app's description names *PSG Tech* as the target campus). Students can:

- Sign in with **Google**, then complete a profile (name, year, department).
- **Submit events** they are hosting. Events go into a **moderation queue** and only become public once an **admin approves** them.
- **Browse, search and filter** approved events.
- **Like, register for, view and share** events.
- **Follow** other students, see mutual connections and shared event interests.
- Get a **personalized feed** ranked by what the people they follow are doing ("Priya registered for this event").
- **Comment** on events.

Admins can moderate events and see analytics computed from both databases.

The "Big Data" angle of the project is its **hybrid / polyglot persistence** design: **MongoDB** (document store) holds rich content, and **Neo4j** (graph database) holds the social graph and interaction edges. Several endpoints query both and merge the results.

---

## 2. Repository layout

```
Big-Data-Project/
├── README.md                      # One-line title only
├── Backend/                       # Python / FastAPI API server
│   ├── .env.example               # Template for environment variables
│   ├── .gitignore
│   ├── README.md                  # Backend-specific docs (architecture, endpoints, setup)
│   ├── requirements.txt           # Python dependencies
│   ├── run.py                     # Starts uvicorn on 0.0.0.0:8000 with reload
│   └── app/
│       ├── main.py                # FastAPI app, lifespan, CORS, error handler, routers
│       ├── config.py              # Pydantic settings loaded from .env
│       ├── dependencies.py        # Auth dependencies (current user / active user / admin)
│       ├── database/
│       │   ├── mongodb.py         # Motor async client
│       │   ├── neo4j.py           # Neo4j async driver + execute_query helper
│       │   └── init_db.py         # Indexes (Mongo) + uniqueness constraints (Neo4j)
│       ├── models/                # Pydantic models describing stored Mongo documents
│       │   ├── user.py
│       │   ├── event.py
│       │   └── comment.py
│       ├── schemas/               # Pydantic request/response models for the API
│       │   ├── common.py          # ApiResponse[T] envelope, ErrorResponse
│       │   ├── auth.py, user.py, event.py, social.py, comment.py, admin.py
│       ├── routes/                # HTTP layer (APIRouters)
│       │   ├── auth.py, users.py, events.py, social.py, feed.py, admin.py, comments.py
│       ├── services/              # Business logic, DB queries
│       │   ├── auth_service.py, user_service.py, event_service.py,
│       │   ├── social_service.py, feed_service.py, admin_service.py, comment_service.py
│       └── utils/
│           ├── helpers.py         # ID generators, UTC time helpers
│           └── security.py        # JWT create / decode
└── frontend/                      # Next.js 16 / React 19 UI (currently mock data only)
    ├── package.json, pnpm-lock.yaml, pnpm-workspace.yaml
    ├── next.config.mjs, tsconfig.json, postcss.config.mjs, components.json
    ├── app/                       # App Router pages
    │   ├── layout.tsx, page.tsx, globals.css
    │   ├── events/page.tsx, events/[id]/page.tsx
    │   ├── students/page.tsx, students/[id]/page.tsx
    │   ├── teammates/page.tsx
    │   └── profile/page.tsx
    ├── components/                # Feature components + shadcn/ui primitives
    ├── lib/data.ts                # Static sample data
    ├── lib/utils.ts               # cn() class-name helper
    └── public/                    # Icons and placeholder images
```

---

## 3. Tech stack

### Backend
| Concern | Library | Notes |
|---|---|---|
| Web framework | **FastAPI** ≥ 0.100 | Async, auto Swagger at `/docs`, ReDoc at `/redoc` |
| ASGI server | **uvicorn[standard]** | Started by `run.py` |
| Validation / settings | **pydantic v2**, **pydantic-settings** | |
| MongoDB driver | **motor** (async) + **pymongo** | |
| Graph DB driver | **neo4j** ≥ 5.12 (async driver) | |
| HTTP client | **httpx** | Used for Google OAuth token exchange |
| Auth tokens | **PyJWT** | HS256 by default |
| Other | `authlib`, `python-dotenv` | Listed but not imported in the code (OAuth is done by hand with httpx) |

### Frontend
| Concern | Library |
|---|---|
| Framework | **Next.js 16.3** (App Router), **React 19** |
| Language | TypeScript 5.7 |
| Styling | **Tailwind CSS v4** (via `@tailwindcss/postcss`), `tw-animate-css` |
| Components | **shadcn/ui** in the `base-nova` style, built on **@base-ui/react** |
| Icons | `lucide-react` |
| Utilities | `clsx`, `tailwind-merge`, `class-variance-authority` |
| Analytics | `@vercel/analytics` (only rendered in production) |
| Package manager | **pnpm** |

The frontend was scaffolded with **v0.app** (Vercel's generator) — see `generator: 'v0.app'` in `layout.tsx` and the v0 entries in `frontend/.gitignore`.

---

## 4. High-level architecture

```
┌──────────────────────────┐        (not wired yet)        ┌──────────────────────────────┐
│   Next.js frontend       │  - - - - - HTTP / JSON - - -> │   FastAPI backend (port 8000)│
│   (mock data in lib/)    │                               │                              │
└──────────────────────────┘                               │  routes → services → DBs     │
                                                           └──────┬───────────────┬───────┘
                                                                  │               │
                                                     MongoDB (documents)    Neo4j (graph)
                                                     ┌──────────────────┐  ┌───────────────────────┐
                                                     │ users            │  │ (:User) (:Event)      │
                                                     │ events           │  │ FOLLOWS, HOSTED,      │
                                                     │ comments         │  │ LIKED, REGISTERED,    │
                                                     │ aggregations     │  │ VIEWED, SHARED        │
                                                     └──────────────────┘  └───────────────────────┘
                                                                  ▲
                                                     Google OAuth 2.0 (login)
```

**Division of responsibility**

- **MongoDB is the source of truth for content**: user profiles, full event documents (title, description, venue, status…), and comments. It also powers admin analytics through **aggregation pipelines**.
- **Neo4j is the source of truth for relationships**: who follows whom, who hosted / liked / registered / viewed / shared which event. Neo4j nodes are deliberately thin (`User {user_id, name, email}`, `Event {event_id}`), so the two databases are joined in application code using shared IDs (`USR_xxxxxxxx`, `EV_xxxxxxxx`).

**Typical "hybrid" query pattern** used throughout the services:

1. Run a Cypher query in Neo4j to get a list of IDs (e.g. people I follow, events my friends liked).
2. Batch-fetch the full documents from MongoDB with `{"<id_field>": {"$in": ids}}`.
3. Merge the two in Python and return.

**Layering inside the backend**

```
routes/      → HTTP concerns: path, query params, auth dependency, status codes, response envelope
services/    → business rules + all DB access (static methods on *Service classes)
database/    → connection management, query helper
schemas/     → what goes over the wire
models/      → what is stored in Mongo (documentation only; not used for reads/writes)
```

---

## 5. Backend in detail

### 5.1 Entry points & startup

**`Backend/run.py`** — runs `uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)`.

**`Backend/app/main.py`**

- Configures logging (`%(asctime)s [%(levelname)s] %(name)s: %(message)s`, INFO level). All modules log under the `campusconnect.*` namespace.
- Defines a **lifespan** context manager. On startup it:
  1. `connect_to_mongo()` — creates the Motor client and pings the server. **Fails hard** (raises) if MongoDB is unreachable.
  2. `connect_to_neo4j()` — creates the driver and calls `verify_connectivity()`. **Fails soft**: on error it logs a warning and continues, so the app runs with "degraded" social features.
  3. `initialize_databases()` — creates indexes and constraints (see 5.3).
  
  On shutdown it closes both connections.
- Creates the `FastAPI` app: title *CampusConnect API*, version 1.0.0.
- **CORS**: allowed origins come from `FRONTEND_URL`, split on commas (so several origins can be configured). Credentials, all methods and all headers are allowed.
- **Global exception handler**: any unhandled exception becomes HTTP 500 with `{"success": false, "message": "An internal server error occurred", "errors": "<exception text>"}`.
- **`GET /health`**: reports `mongodb` / `neo4j` as `connected` or `disconnected` and overall `ok` / `degraded`.
- Registers routers: `auth`, `users`, `events`, `social`, `feed`, `admin`, `comments`.

### 5.2 Configuration (`app/config.py`)

A `pydantic_settings.BaseSettings` class reads `Backend/.env` (path resolved relative to the file, so it works no matter where you launch from). Unknown keys are ignored. `get_settings()` is wrapped in `@lru_cache` so settings are built once.

| Variable | Default | Used for |
|---|---|---|
| `MONGO_URI` | `mongodb://localhost:27017` | Motor client |
| `MONGO_DB_NAME` | `campusconnect` | Database name |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j driver |
| `NEO4J_USERNAME` / `NEO4J_PASSWORD` | `neo4j` / `change_me` | Neo4j auth |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | placeholders | OAuth |
| `GOOGLE_REDIRECT_URI` | `http://localhost:8000/api/auth/google/callback` | OAuth callback |
| `JWT_SECRET_KEY` | placeholder | Signing JWTs |
| `JWT_ALGORITHM` | `HS256` | |
| `JWT_EXPIRE_MINUTES` | `1440` (24 h) | Token lifetime |
| `FRONTEND_URL` | `http://localhost:5173` | CORS + post-login redirects (comma-separated allowed for CORS) |
| `ADMIN_EMAIL` | `admin@example.com` | The Google account whose email matches becomes `ADMIN` |

### 5.3 Database layer (`app/database/`)

**`mongodb.py`**
- A module-level `MongoDBManager` singleton holds `client` and `db`.
- `get_database()` returns the `AsyncIOMotorDatabase` or raises `RuntimeError` if not connected. Services call it at the start of every method.

**`neo4j.py`**
- A module-level `Neo4jManager` singleton holds the `AsyncDriver`.
- `execute_query(query, parameters)` opens a session, runs the Cypher, and returns `await result.data()` (a list of dicts). **Any exception is logged and an empty list is returned** — this is why the app keeps working when Neo4j is down, but it also means graph write failures are silent.

**`init_db.py`** — run at startup; errors are logged as warnings, not raised.

MongoDB indexes:
| Collection | Index | Options |
|---|---|---|
| `users` | `user_id` | unique |
| `users` | `email` | unique |
| `users` | `google_id` | unique, sparse |
| `events` | `event_id` | unique |
| `events` | `status`, `category`, `date`, `host_id` | non-unique (for filtering) |
| `comments` | `comment_id` | unique |
| `comments` | `event_id` | non-unique |

Neo4j constraints:
- `user_id_unique` — `(:User).user_id` is unique.
- `event_id_unique` — `(:Event).event_id` is unique.

### 5.4 Authentication & authorization

**Login is Google-only (OAuth 2.0 authorization-code flow), and the app issues its own JWT.**

1. `GET /api/auth/google/login` builds the Google consent URL (scope `openid email profile`, `access_type=offline`, `prompt=consent`) and either redirects (default) or, with `?redirect=false`, returns the URL in JSON.
2. Google redirects back to `GET /api/auth/google/callback?code=...`.
3. `AuthService.exchange_google_code` POSTs the code to `https://oauth2.googleapis.com/token`, then GETs `https://www.googleapis.com/oauth2/v2/userinfo`.
4. `AuthService.process_google_user`:
   - Looks for an existing user by `google_id` **or** `email`.
   - Computes the role: `ADMIN` if the email equals `ADMIN_EMAIL` (case-insensitive), otherwise `USER`. **The role is recomputed on every login**, so changing `ADMIN_EMAIL` demotes/promotes users at their next login.
   - Existing user → updates `updated_at`, role if changed, back-fills `google_id` and `profile_picture` if missing.
   - New user → inserts a document with `profile_completed: False`, `year`/`department` null.
   - Creates a JWT with claims `sub`, `user_id`, `email`, `role`, `profile_completed`, `exp`, `iat`.
5. The callback **redirects to the frontend with the token in the query string**:
   - profile complete → `{FRONTEND_URL}/auth/callback?token=...`
   - profile incomplete → `{FRONTEND_URL}/complete-profile?token=...`
6. The frontend then calls `POST /api/auth/complete-profile` (with `Authorization: Bearer <token>`) sending `name`, `year` (1–6), `department`, optional `profile_picture`. This:
   - updates Mongo and sets `profile_completed: True`,
   - **creates/updates the `(:User)` node in Neo4j** (`MERGE … SET u.name, u.email`),
   - returns a **fresh JWT** with `profile_completed: True`.

**Dependency chain (`app/dependencies.py`)** — used via FastAPI `Depends`:

| Dependency | What it checks | Failure |
|---|---|---|
| `get_current_user_token_payload` | `Authorization: Bearer` header present, JWT valid, has `user_id` | 401 |
| `get_current_user` | user with that `user_id` exists in Mongo (fresh DB read on every request) | 401 |
| `get_current_active_user` | `profile_completed` is true | 403 "Profile registration incomplete" |
| `get_current_admin` | `role == "ADMIN"` | 403 "Admin privileges required" |

Because the user is re-read from MongoDB each request, role and profile changes take effect immediately even if the JWT claims are stale.

### 5.5 Data models (MongoDB documents)

These Pydantic classes in `app/models/` document the shape of stored documents; services actually work with plain dicts.

**`users`** (`UserModel`)
| Field | Type | Notes |
|---|---|---|
| `user_id` | str | `USR_` + 8 hex chars |
| `google_id` | str? | |
| `email` | email | unique |
| `name` | str | |
| `year` | int? | 1–6 |
| `department` | str? | |
| `profile_picture` | str? | Google avatar URL by default |
| `role` | `"USER"` \| `"ADMIN"` | |
| `profile_completed` | bool | |
| `created_at`, `updated_at` | datetime (UTC) | |

**`events`** (`EventModel`)
| Field | Type | Notes |
|---|---|---|
| `event_id` | str | `EV_` + 8 hex |
| `title`, `description`, `category` | str | |
| `host_id` | str | the submitting user |
| `date` | str `YYYY-MM-DD` | stored as string so lexical comparison = date comparison |
| `start_time`, `end_time` | str `HH:MM` | |
| `venue` | str | |
| `registration_url`, `poster_url` | str? | |
| `tags` | list[str] | |
| `status` | `pending` → `approved` / `rejected` | |
| `created_at`, `updated_at` | datetime | |
| `approved_at`, `approved_by` | set on approval | |
| `rejected_at`, `rejected_by`, `rejection_reason` | set on rejection | |

**`comments`** (`CommentModel`)
| Field | Type |
|---|---|
| `comment_id` | `CM_` + 8 hex |
| `event_id`, `user_id` | str |
| `content` | str (1–1000 chars) |
| `created_at` | datetime |

### 5.6 Neo4j graph model

```
(:User {user_id, name, email})
(:Event {event_id})

(:User)-[:FOLLOWS]->(:User)
(:User)-[:HOSTED]->(:Event)                 created when an admin approves the event
(:User)-[:LIKED]->(:Event)
(:User)-[:REGISTERED]->(:Event)
(:User)-[:VIEWED {first_viewed_at, last_viewed_at, count}]->(:Event)
(:User)-[:SHARED]->(:Event)
```

- All writes use `MERGE`, so repeating an action (like twice, follow twice) is idempotent. `VIEWED` is the only edge with state: repeated views increment `count` and update `last_viewed_at`.
- User nodes are created at profile completion, or lazily (`MERGE … ON CREATE SET u.name`) the first time the user follows / likes / registers / views / shares.
- Event nodes are created on approval (with `HOSTED`) or lazily on first interaction.

### 5.7 Schemas (API request/response shapes)

**Response envelope (`schemas/common.py`)** — every endpoint returns:
```json
{ "success": true, "message": "…", "data": <payload> }
```
`ApiResponse[T]` is a generic Pydantic model, so Swagger shows the exact payload type per endpoint. Errors raised with `HTTPException` use FastAPI's default `{"detail": "..."}` shape; only unhandled exceptions use the `ErrorResponse` shape.

| File | Models |
|---|---|
| `auth.py` | `ProfileCompletionRequest` (name 1–100, year 1–6, department 1–100, picture?), `AuthTokenResponse`, `GoogleAuthInitResponse` |
| `user.py` | `UserProfileResponse` (private, includes email/role), `UserProfileUpdateRequest` (all optional), `PublicUserResponse` (adds `followers_count`, `following_count`) |
| `event.py` | `EventCreateRequest` (regex-validated date `YYYY-MM-DD` and times `HH:MM`, title 3–200, description ≥ 10…), `EventResponse`, `EventDetailResponse` (adds like/registration/view/share counts and `is_liked_by_me`, `is_registered_by_me`) |
| `social.py` | `FollowStatusResponse`, `SocialUserResponse`, `FeedUserAction`, `SocialContext {reason, users[]}`, `FeedItemResponse`, `CommonInterestResponse` |
| `comment.py` | `CommentCreateRequest`, `CommentResponse` (hydrated with `user_name`, `user_picture`) |
| `admin.py` | `EventRejectionRequest`, `EventAnalyticsResponse`, `NetworkAnalyticsResponse` |

### 5.8 Routes (every API endpoint)

Legend for **Auth**: — = public · **U** = logged in (profile may be incomplete) · **A** = active user (profile complete) · **Adm** = admin.

#### Auth — `routes/auth.py`, prefix `/api/auth`
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/google/login?state=&redirect=` | — | Redirect to Google, or return the URL when `redirect=false` |
| GET | `/google/callback?code=` | — | Exchange code, upsert user, redirect to frontend with JWT |
| POST | `/complete-profile` | U | Finish onboarding, sync user to Neo4j, return new JWT |

#### Users — `routes/users.py`, prefix `/api/users`
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/me` | A | Own full profile |
| PATCH | `/me` | A | Partial update (name/year/department/picture); name change synced to Neo4j; 400 if body empty |
| GET | `/search?q=` | A | Case-insensitive regex over name, email, department (max 20, completed profiles only) |
| GET | `/{user_id}` | A | Public profile + follower/following counts from Neo4j |
| GET | `/{user_id}/followers` | A | Followers of any user |
| GET | `/{user_id}/following` | A | Who any user follows |

> Note: `/search` and `/me` are declared before `/{user_id}`, so they are matched first — the ordering matters.

#### Events — `routes/events.py`, prefix `/api/events`
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `` | A | Submit event → `status: pending` (201) |
| GET | `?category=&date=&search=&page=&limit=` | — | Approved events, newest first; search matches title/description/tags; limit ≤ 100 |
| GET | `/upcoming?limit=` | — | Approved events with `date >= today`, soonest first |
| GET | `/my-hosted` | A | Everything I submitted (any status) |
| GET | `/{event_id}` | A | Mongo details + Neo4j counts + "did I like/register". Non-approved events only visible to host or admin (403 otherwise) |
| POST / DELETE | `/{event_id}/like` | A | Like / unlike |
| POST / DELETE | `/{event_id}/register` | A | Register / unregister |
| POST | `/{event_id}/view` | A | Record view (increments counter) |
| POST | `/{event_id}/share` | A | Record share |

`format_event_response()` in this file converts a Mongo dict to `EventResponse` (turning `created_at` into an ISO string) and is reused by the admin router.

#### Comments — `routes/comments.py`, prefix `/api/events`
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/{event_id}/comments` | A | Add comment (event must be approved) |
| GET | `/{event_id}/comments` | A | Oldest-first, up to 200, with author name/picture |

#### Social — `routes/social.py`, prefix `/api/social`
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/follow/{user_id}` | A | Follow (can't follow yourself; both users must exist in Mongo) |
| DELETE | `/follow/{user_id}` | A | Unfollow |
| GET | `/status/{user_id}` | A | Am I following them? |
| GET | `/followers` | A | My followers |
| GET | `/following` | A | Who I follow |
| GET | `/mutuals/{user_id}` | A | People both of us follow (see bug #1 in section 10) |
| GET | `/common-interests/{user_id}` | A | Events we've both interacted with, e.g. "You LIKED, they REGISTERED" |

#### Feed — `routes/feed.py`, prefix `/api/feed`
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `?limit=` | A | Personalized feed (≤ 50), see 5.9 |

#### Admin — `routes/admin.py`, prefix `/api/admin`
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/events/pending` | Adm | Moderation queue (newest first, max 100) |
| GET | `/events/{event_id}` | Adm | Inspect any event |
| POST | `/events/{event_id}/approve` | Adm | Approve + create `HOSTED` edge in Neo4j |
| POST | `/events/{event_id}/reject` | Adm | Reject with optional `rejection_reason` |
| GET | `/analytics/events` | Adm | MongoDB aggregation analytics |
| GET | `/analytics/network` | Adm | Neo4j graph analytics |

#### Misc
| Method | Path | Description |
|---|---|---|
| GET | `/health` | DB connection status |
| GET | `/docs`, `/redoc` | Interactive API docs |

### 5.9 Services (business logic)

All services are classes with `@staticmethod async` methods.

#### `AuthService`
Covered in 5.4: `get_google_login_url`, `exchange_google_code`, `process_google_user`, `complete_profile`.

#### `UserService`
- `get_user_by_id` — plain Mongo lookup.
- `get_public_profile` — only for users with `profile_completed: True`; adds follower/following counts via one Cypher query with two `OPTIONAL MATCH` + `count(DISTINCT …)`.
- `update_profile` — strips `None` values, `$set`s the rest, re-reads the doc, and if `name` changed updates the Neo4j node too.
- `search_users` — escapes the query with `re.escape` (safe against regex injection) and does a case-insensitive `$or` over name/email/department.

#### `EventService`
- `create_event` — builds the document with a new `EV_` id, status `pending`.
- `get_approved_events` — filter by status/category/date, optional escaped regex search over title/description/tags, sort by `created_at` desc, skip/limit pagination, then **batch-hydrate host names** with one `$in` query.
- `get_upcoming_events` — `date >= today` (string comparison works because of `YYYY-MM-DD`), ascending.
- `get_hosted_by_user`, `get_event_by_id` — simple lookups.
- `get_event_detail` — Mongo doc + host name + one Cypher query returning `like_count`, `registration_count`, `view_count`, `share_count`, `is_liked_by_me`, `is_registered_by_me`. Falls back to zeros if the event has no graph node.
- `like_event`, `register_event`, `record_view`, `record_share` — verify the event exists **and is approved** in Mongo, then `MERGE` the user, event and edge in Neo4j.
- `unlike_event`, `unregister_event` — `MATCH … DELETE r` (no existence check needed).

#### `SocialService`
- `follow_user` — validates both users in Mongo, then `MERGE`s nodes (setting `name` on create) and the `FOLLOWS` edge.
- `unfollow_user`, `get_follow_status` — direct Cypher.
- `get_followers`, `get_following` — Cypher for IDs → Mongo `$in` for name/department/picture (hybrid pattern).
- `get_mutuals` — intended: `(me)-[:FOLLOWS]->(m)<-[:FOLLOWS]-(them)`.
- `get_common_interests` — `(me)-[r1:LIKED|REGISTERED|SHARED|VIEWED]->(e)<-[r2:…]-(them)`, hydrated with event title/category from Mongo, only approved events. One row per pair of edges, so an event can appear multiple times.

#### `FeedService` — the core "big data" feature
`get_personalized_feed(user_id, limit)`:

1. **Neo4j**: find every interaction by people I follow:
   ```cypher
   MATCH (me:User {user_id: $user_id})-[:FOLLOWS]->(friend:User)
         -[r:LIKED|REGISTERED|SHARED|VIEWED]->(e:Event)
   RETURN e.event_id, friend.user_id, friend.name, type(r)
   ```
2. **Score** each event by summing action weights:

   | Action | Weight |
   |---|---|
   | REGISTERED | 4 |
   | SHARED | 3 |
   | LIKED | 2 |
   | VIEWED | 1 |

   So an event that 2 friends registered for (8) outranks one that 3 friends viewed (3).
3. **MongoDB**: fetch all scored events in one `$in` query, keeping only `approved` ones.
4. **Social context**: for each event, de-duplicate friends (keeping each friend's highest-weight action) and build a reason string:
   - one friend → `"Priya registered for this event"`
   - several → `"Priya and 2 other connections interacted with this event"`
5. **Fallback / cold start**: if fewer than `limit` items, fill with other approved events sorted by date ascending, `social_context: null`.

#### `CommentService`
- `add_comment` — event must be approved; inserts, then attaches the author's name & picture.
- `get_event_comments` — up to 200 oldest-first; authors batch-hydrated with one `$in` query.

#### `AdminService`
- `get_pending_events`, `approve_event` (Mongo `$set` + Neo4j `HOSTED` edge), `reject_event`.
- `get_event_analytics` — three **MongoDB aggregation pipelines**:
  1. `$group` by status → total / approved / pending / rejected counts.
  2. `$match approved` → `$group` by category → `$sort` desc.
  3. `$group` by `host_id` → `$sort` → `$limit 10`, then host names joined from `users`.
- `get_network_analytics` — four **Cypher** queries: total users, total `FOLLOWS` edges, top-5 most-followed users, top-5 most-interacted events (titles then hydrated from Mongo).

### 5.10 Utilities

**`utils/helpers.py`**
- `generate_user_id()` → `USR_1A2B3C4D`, `generate_event_id()` → `EV_…`, `generate_comment_id()` → `CM_…` (first 8 hex chars of a UUID4, upper-cased).
- `utc_now()` → timezone-aware `datetime`; `utc_now_iso()` → ISO string (used for `VIEWED` timestamps in Neo4j).

**`utils/security.py`**
- `create_access_token(data, expires_delta=None)` — copies the claims, adds `exp` and `iat`, signs with `JWT_SECRET_KEY`/`JWT_ALGORITHM`.
- `decode_access_token(token)` — returns the payload or `None` on any `PyJWTError` (expired, bad signature, malformed).

---

## 6. Frontend in detail

> **Important:** the frontend is currently a **static UI prototype**. `lib/data.ts` literally says *"No backend, database, or API calls — everything here is local sample data."* None of the pages call the FastAPI backend yet.

### 6.1 Configuration files

| File | Purpose |
|---|---|
| `package.json` | Scripts `dev` / `build` / `start`; dependencies listed in section 3 |
| `next.config.mjs` | `typescript.ignoreBuildErrors: true` (type errors won't fail the build) and `images.unoptimized: true` |
| `tsconfig.json` | Strict TS, bundler module resolution, path alias `@/*` → project root |
| `components.json` | shadcn/ui config: style `base-nova`, RSC enabled, neutral base colour, CSS variables, aliases (`@/components`, `@/components/ui`, `@/lib`, `@/hooks`), lucide icons |
| `postcss.config.mjs` | Loads the Tailwind v4 PostCSS plugin |
| `pnpm-workspace.yaml` | pnpm settings (`minimumReleaseAgeExclude` for Next packages) |
| `next-env.d.ts` | Next.js type references |
| `.gitignore` | v0 sandbox files, `.env*.local`, `node_modules`, `.next/` |

### 6.2 Pages (routes)

| Route | File | Type | What it shows |
|---|---|---|---|
| `/` | `app/page.tsx` | Server component | **Dashboard**: welcome card ("Welcome back, Arun!"), 4 stat cards (Events Registered, Events Attended, Skills, Connections), 3 *Upcoming Events*, 3 *Recommended Events*, 3 *Recommended Teammates* — each section has a "View all" link |
| `/events` | `app/events/page.tsx` | Client component | **Event list** with a text search (by name) and a category dropdown (All, Hackathon, Workshop, Bootcamp, Seminar, Contest, Meetup); empty-state message |
| `/events/[id]` | `app/events/[id]/page.tsx` | Async server component | **Event details**: category badge, date, time, location, organizer, participants, description, "Required Skills" badges, Register button; 404 via `notFound()` if the id doesn't exist |
| `/students` | `app/students/page.tsx` | Client component | **Student directory** with name search and department filter (CSE, IT, AI&DS, ECE) |
| `/students/[id]` | `app/students/[id]/page.tsx` | Async server component | **Another student's profile** (via `ProfileView`) + Connect button |
| `/teammates` | `app/teammates/page.tsx` | Client component | **Find teammates**: name search + toggleable skill chips (a student must have *all* selected skills); cards show "Common skills" with the current user |
| `/profile` | `app/profile/page.tsx` | Server component | **My profile** (`ProfileView` of `currentUser`) + Edit Profile button |

`app/layout.tsx` sets metadata (title *"CampusConnect — Student Events & Networking"*, light/dark favicons, Apple icon), forces a light colour scheme, renders the `Navbar` and wraps pages in `<main className="mx-auto max-w-6xl px-4 py-8">`. Vercel Analytics is included only when `NODE_ENV === 'production'`.

Buttons such as **Register**, **Connect** and **Edit Profile** are visual only — they have no handlers yet.

### 6.3 Feature components

| Component | Description |
|---|---|
| `navbar.tsx` | Sticky header with logo (graduation-cap icon), desktop links (Dashboard, Events, Find Teammates, Students, Profile) with active-link highlighting, user avatar initials, and a slide-in `Sheet` menu on mobile |
| `event-card.tsx` | Card with category badge, name, description, date/location/organizer/participants, "View Details" link and "Register" button |
| `student-card.tsx` | Avatar initials, name, department · year, skill badges; with `showConnect` it also shows "Common skills" and a Connect button |
| `profile-view.tsx` | Large header (avatar, name, department/year, email), Skills and Interests tag cards, and three list cards: Events, Projects, Clubs |
| `stat-card.tsx` | Icon + big number + label |
| `search-bar.tsx` | Controlled input with a search icon |
| `page-header.tsx` | Page title + optional description |

### 6.4 UI primitives (`components/ui/`)

Generated by shadcn/ui (`base-nova` style), wrapping **@base-ui/react** headless components and styled with Tailwind + `class-variance-authority`:
`avatar`, `badge`, `button`, `card`, `dialog`, `input`, `label`, `select`, `sheet`, `textarea`.

Base UI uses a `render` prop instead of Radix's `asChild` — which is why links-as-buttons are written as
`<Button nativeButton={false} render={<Link href="…" />}>`.
`dialog`, `label` and `textarea` are currently unused (likely added for future forms).

`lib/utils.ts` exports `cn(...)` = `twMerge(clsx(...))` for merging Tailwind classes.

### 6.5 Mock data (`lib/data.ts`)

- **Types**: `EventItem {id, name, date, time, location, organizer, participants, category, description, skills[]}` and `Student {id, name, department, year, email, skills[], interests[], events[], projects[], clubs[]}`.
- `currentUser` — "Arun Nair", CSE 3rd year.
- `stats` — 4 dashboard numbers.
- `events` — 6 sample events (AI Hackathon, Web Dev Workshop, Cloud Bootcamp, ML Seminar, Coding Contest, Robotics Meetup), dated Oct–Nov 2026.
- `students` — 6 sample students across CSE, IT, AI&DS, ECE.
- Helpers: `commonSkills(student)`, `departments`, `categories`, `allSkills` (unique sorted skills across students), `getInitials(name)`.

### 6.6 Styling

`app/globals.css` imports Tailwind, `tw-animate-css` and `shadcn/tailwind.css`, maps design tokens to Tailwind colours in `@theme inline`, and defines a light theme on `:root` using **OKLCH** colours (primary is a blue/indigo, `oklch(0.52 0.2 264)`). A `.dark` variant exists via `@custom-variant`, but the layout pins the colour scheme to light.

---

## 7. End-to-end flows

### First-time login
```
Browser → GET /api/auth/google/login → 302 Google consent
Google  → GET /api/auth/google/callback?code=…
Backend → Google token + userinfo → insert user (profile_completed=false) → JWT
Backend → 302 {FRONTEND_URL}/complete-profile?token=JWT
Frontend→ POST /api/auth/complete-profile {name, year, department}   (Bearer JWT)
Backend → Mongo update + Neo4j MERGE (:User) → new JWT
```

### Event lifecycle
```
Student  POST /api/events                    → Mongo: status=pending
Admin    GET  /api/admin/events/pending
Admin    POST /api/admin/events/{id}/approve → Mongo: status=approved
                                             → Neo4j: (host)-[:HOSTED]->(event)
Anyone   GET  /api/events                    → now listed
Students POST /api/events/{id}/like|register|view|share → Neo4j edges
Students POST /api/events/{id}/comments      → Mongo comments
```

### Feed generation
```
GET /api/feed
  1. Neo4j: friends' interactions          → [(event_id, friend, action), …]
  2. Python: weight & rank events
  3. Mongo: $in fetch approved event docs
  4. Python: attach "X registered for this event"
  5. Mongo: pad with other approved events if needed
```

---

## 8. Running the project locally

### Prerequisites
- Python 3.10+
- A MongoDB instance (local or Atlas)
- A Neo4j 5 instance (Desktop, Docker or Aura)
- A Google Cloud OAuth 2.0 Web client (redirect URI `http://localhost:8000/api/auth/google/callback`)
- Node.js 20+ and pnpm (for the frontend)

### Backend
```bash
cd Backend
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux:        source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # then fill in DB URIs, Google credentials, JWT secret, ADMIN_EMAIL
python run.py             # or: uvicorn app.main:app --reload --port 8000
```
Open http://localhost:8000/docs for Swagger. To call protected endpoints, log in through `/api/auth/google/login`, copy the `token` from the redirect URL, and click **Authorize** in Swagger.

Quick DB start with Docker (optional):
```bash
docker run -d -p 27017:27017 --name mongo mongo:7
docker run -d -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/change_me --name neo4j neo4j:5
```

### Frontend
```bash
cd frontend
pnpm install
pnpm dev                  # http://localhost:3000
```

> The backend's default `FRONTEND_URL` is `http://localhost:5173` (a Vite port), but Next.js runs on **3000**. Set `FRONTEND_URL=http://localhost:3000` in `Backend/.env` once the two are connected.

---

## 9. Frontend ↔ Backend gap analysis

The two halves were built separately (backend in PR #1, frontend in PR #2) and don't line up yet.

| Area | Backend | Frontend | Gap |
|---|---|---|---|
| Data source | MongoDB + Neo4j | Hard-coded `lib/data.ts` | No API client / fetch calls |
| Auth | Google OAuth + JWT; redirects to `/auth/callback` and `/complete-profile` | No login, no token storage; those two routes don't exist | Need login button, callback page, profile-completion page, token storage |
| Event fields | `title`, `venue`, `date` + `start_time`/`end_time`, `host_id`/`host_name`, `tags`, `status`, counts | `name`, `location`, `date` + `time`, `organizer`, `participants`, `skills` | Field names need mapping; `participants` ≈ `registration_count`; `skills` ≈ `tags` |
| User fields | `name`, `email`, `year` (int), `department`, `profile_picture`, `role` | adds `skills`, `interests`, `projects`, `clubs`; `year` is a string ("3rd Year") | Backend has no skills/interests/projects/clubs |
| Teammates | Not implemented | Skill-based teammate finder | Needs backend skills + matching (a good Neo4j use case) |
| Connect button | `POST /api/social/follow/{id}` | No handler | Wire up |
| Register button | `POST /api/events/{id}/register` | No handler | Wire up |
| Feed | `GET /api/feed` with social context | Dashboard just slices the mock list | Use feed for "Recommended Events" |
| Event submission | `POST /api/events` | No form | Add a "Host an event" page (unused `dialog`/`textarea`/`label` are ready) |
| Comments, likes, shares | Implemented | No UI | Add to event details page |
| Admin moderation & analytics | Implemented | No UI | Add admin pages |
| Followers/following/mutuals | Implemented | No UI | Add to profile pages |

---

## 10. Known bugs & issues found during review

### Correctness bugs
1. **Mutual connections always empty** — `social_service.py` `get_mutuals` matches `(u2:User {target_id: $target_id})`. User nodes have no `target_id` property; it should be `{user_id: $target_id}`.
2. **Feed fallback isn't "upcoming"** — `feed_service.py` computes `today` but never uses it, so past approved events can fill the feed. Add `"date": {"$gte": today}` to the fallback query.
3. **Feed reason grammar** — for a single friend it builds `"<name> <action> for this event"`, producing "Priya liked for this event" / "Priya viewed for this event" / "Priya shared for this event". Only "registered for" reads correctly.
4. **Health check over-reports Neo4j** — `connect_to_neo4j` keeps the driver even when connectivity fails, and `/health` only checks `driver is not None`, so it says `connected` while Neo4j is down.
5. **Silent graph failures** — `execute_query` swallows every exception and returns `[]`. A failed `FOLLOWS`/`LIKED` write still returns "success" to the client.
6. **Possible double-counting in common interests** — each pair of edges produces a row, so an event both users liked *and* viewed appears multiple times.
7. **Comments on non-approved events can be read** — `get_event_comments` doesn't check event status (adding does).

### Security concerns
1. **OAuth `state` is not verified** — `/google/login` defaults `state` to `"default_state"` and the callback ignores it, so the flow has no CSRF protection.
2. **JWT in the redirect URL** — tokens in query strings end up in browser history, server logs and `Referer` headers. Prefer an HttpOnly cookie or a short-lived one-time code exchanged by the frontend.
3. **Error details leaked** — the global handler returns `str(exc)` to clients, and the OAuth callback includes the raw exception text.
4. **Weak defaults** — `JWT_SECRET_KEY` and `NEO4J_PASSWORD` have placeholder defaults; the app will start with them if `.env` is missing. Consider failing fast when they are unchanged.
5. **No rate limiting** on view/share/like endpoints, so counts can be inflated trivially.

### Frontend issues
1. `next.config.mjs` sets `ignoreBuildErrors: true`, hiding TypeScript errors in production builds.
2. All action buttons are non-functional placeholders.
3. `package.json` name is still the scaffold default (`my-project`).

### Housekeeping
1. Root `README.md` contains only the title.
2. `authlib` and `python-dotenv` are in `requirements.txt` but never imported.
3. `app/models/*` are not used at runtime (services use raw dicts) — fine as documentation, but they can drift from reality.
4. No tests, no CI, no Dockerfile / docker-compose.
5. No seed script — a fresh install has no events/users to demo with.

---

## 11. Suggested next steps

1. Fix the `get_mutuals` Cypher bug and the feed fallback date filter (small, high-value).
2. Add an API client in the frontend (`lib/api.ts`) with the JWT in an `Authorization` header, and replace `lib/data.ts` page by page, starting with `/events` and `/events/[id]`.
3. Build the auth pages: `/login`, `/auth/callback`, `/complete-profile`.
4. Decide on the user model: either add `skills`, `interests`, `clubs`, `projects` to the backend (and model skills as `(:User)-[:HAS_SKILL]->(:Skill)` in Neo4j for teammate matching), or drop them from the UI.
5. Add admin pages (moderation queue + analytics charts).
6. Add a `docker-compose.yml` with MongoDB, Neo4j, backend and frontend, plus a seed script.
7. Add OAuth `state` validation and move the token out of the URL.
8. Add pytest tests for the services (with mongomock / a test Neo4j) and a GitHub Actions workflow.

---

## 12. Git history

| Commit | Description |
|---|---|
| `95a313a` | Initial commit (README) |
| `db30c5b` | Basic Backend route with FastAPI for Campus Connect |
| `018f744` | Merge PR #1 from Abbilaash/main (backend) |
| `056265c` | Added basic frontend |
| `4fd8bce` | Merge PR #2 from Nivashini2505/add-frontend (frontend) |
