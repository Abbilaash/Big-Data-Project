# Implementation Log

Chronological record of every meaningful change. Newest entries at the bottom.

---

## 2026-10-11 — Phase 1: Repository analysis (no code changes)

**Files added:** `docs/ASSUMPTIONS.md`, `docs/IMPLEMENTATION_LOG.md`.
**Files modified/deleted:** none.

**What was done**
- Read `docs/PROJECT_DOCUMENTATION.md` and the full backend source (config,
  database layer, dependencies, utils, schemas, services, routes) and the key
  frontend files (layout, navbar, cards, events page, globals.css, ui/button).
- Confirmed the frontend is a static prototype (`lib/data.ts`), with no API
  calls, no auth, and non-functional buttons.
- Confirmed the toolchain: Python 3.11.9, Node 20.12.1, npm 10.5.0, pnpm not
  installed. Docker CLI present but its daemon was not running; no local
  MongoDB or Neo4j.
- Confirmed by reading the code the defects listed in
  `PROJECT_DOCUMENTATION.md` §10, including: `get_mutuals` matches on
  `target_id` instead of `user_id`; feed fallback ignores `today`; singular feed
  reason grammar; `/health` reports Neo4j connected unconditionally;
  `execute_query` swallows errors; OAuth `state` unchecked; raw exception text
  returned to clients; comments readable on unapproved events.

**Verification:** read-only inspection plus the toolchain checks above. An
initial attempt to create the backend virtualenv and install the frontend
dependencies was interrupted before doing anything; confirmed afterwards that
neither `Backend/.venv` nor `frontend/node_modules` exists.

**Remaining concerns:** see `ASSUMPTIONS.md` A-08 — no live databases available.

**Next:** Phase 2 — backend fixes and the endpoints the UI needs.

---

## 2026-10-11 — Phase 2: Backend fixes, hardening and new endpoints

### Bugs fixed (each has a regression test in `Backend/tests/`)
| # | Defect | Fix | File(s) |
|---|---|---|---|
| 1 | `get_mutuals` matched `{target_id: …}` so it always returned `[]` | Match on `user_id`; DISTINCT | `services/social_service.py` |
| 2 | Feed fallback included past events (`today` computed, unused) | `date >= today` filter on both social and fallback paths | `services/feed_service.py` |
| 3 | Feed reason grammar ("Priya liked for this event") | Per-action phrases | `services/feed_service.py` |
| 4 | `/health` said Neo4j "connected" if a driver object existed | Live `verify_connectivity()` probe + Mongo ping | `main.py`, `database/neo4j.py` |
| 5 | `execute_query` swallowed all errors → writes reported success | `GraphUnavailableError` → HTTP 503 for writes; decorative reads opt in to `required=False` | `database/neo4j.py`, services |
| 6 | Common interests duplicated per edge pair | `collect(DISTINCT …)`, one row per event | `services/social_service.py` |
| 7 | Comments readable on unapproved events | 404 unless approved | `services/comment_service.py` |
| 8 | Rejected/approved events could be re-moderated | Atomic `find_one_and_update` on `status=pending`; 409 otherwise | `services/admin_service.py` |
| 9 | OAuth `state` ignored (no CSRF protection) | Signed 10-minute state JWT verified in callback | `utils/security.py`, `routes/auth.py` |
| 10 | Unhandled errors returned `str(exc)` to clients | Generic message; detail logged only | `main.py` |
| 11 | JWT delivered in query string | Delivered in URL fragment | `routes/auth.py` |
| 12 | `javascript:`/`data:` URLs accepted for registration/poster/profile picture | http(s)-only validator | `schemas/validators.py` |
| 13 | Nonsense events accepted (end before start, 31 Feb, 25:99) | Real date/time validation, canonical categories | `schemas/event.py` |
| 14 | First-login race could 500 on duplicate key | Handle `DuplicateKeyError` | `services/auth_service.py` |
| 15 | Placeholder `JWT_SECRET_KEY` accepted silently | Fail-fast when `ENVIRONMENT=production` | `config.py`, `main.py` |

### Added
- **Endpoints:** `GET /api/auth/config`, `POST /api/auth/dev-login` (gated),
  `GET /api/events/categories`, `GET /api/events/registered`,
  `GET /api/users` (directory), `GET /api/users/suggestions`,
  `GET /api/users/departments`, `GET /api/admin/events?status=`,
  `DELETE /api/events/{id}/comments/{comment_id}`.
- **Fields:** event responses now carry `like_count`, `registration_count`,
  `is_liked_by_me`, `is_registered_by_me`, `rejection_reason`; user lists carry
  `year`, `is_following`, `mutual_count`.
- **Behaviour:** event list/upcoming/feed hydrate counts with ONE batched Cypher
  query (previously none; naive per-event querying would be N+1). Event detail
  Cypher rewritten from a cartesian product of OPTIONAL MATCHes to pattern
  comprehensions. `upcoming_only` filter on `GET /api/events`.
- **New modules:** `routes/formatters.py`, `schemas/validators.py`,
  `utils/errors.py` (`NotFoundError`→404, `ConflictError`→409).
- **Tooling:** `requirements-dev.txt`, `pytest.ini`, `tests/` (61 tests).

### Changed behaviour worth knowing
- `GET /api/events/{id}` for someone else's unapproved event now returns **404**
  (was 403) so drafts are not disclosed.
- Interaction endpoints return **404** (was 400) for missing/unapproved events.
- User search no longer matches on email; the directory never exposes email.
- `FRONTEND_URL` default changed `5173` → `3000` (Next.js dev port).
- CORS methods/headers narrowed from `*`.
- `UserProfileResponse.email` is `str` (was `EmailStr`); output re-validation
  rejected reserved TLDs and added no safety.

### Removed
- `authlib` from `requirements.txt` (never imported).

### Verification (MOCKED)
- `pytest` → **61 passed**, using mongomock-motor and an in-memory Neo4j fake
  (`tests/fake_graph.py`). Real MongoDB/Neo4j were not available; see
  ASSUMPTIONS A-08. Cypher validity against a real Neo4j is **unverified**.

### Remaining concerns
- Cypher uses `size([(e)<-[:X]-() | 1])` pattern comprehensions: valid on
  Neo4j 4.x/5.x, but unexecuted against a server here.
- No rate limiting. Counts are per distinct user, so repeated requests cannot
  inflate them; request flooding itself is unaddressed.

---

## 2026-10-11 — Phase 3: Frontend implementation, integration, verification, docs

### Frontend — added
- **Foundations:** `lib/api.ts` (typed client, `ApiError` with field errors and
  friendly 0/401/422/503 handling), `lib/types.ts`, `lib/auth.tsx`
  (session state machine), `lib/format.ts` (timezone-safe date/time),
  `lib/use-async.ts`, `lib/use-event-interactions.ts` (optimistic with
  rollback), `lib/constants.ts`.
- **Components:** `auth-gate`, `toast`, `state-views` (loading/empty/error),
  `select-field`, `user-avatar`, `status-badge`, `follow-button`,
  `person-card`, `profile-header`, `ranked-bars`, `link-button`.
- **Pages:** `/login`, `/auth/callback`, `/complete-profile`, `/events/new`,
  `/my-events`, `/people`, `/people/[id]`, `/admin` (queue, history,
  analytics).
- **Rewritten against the real API:** `/` (feed dashboard), `/events`,
  `/events/[id]` (actions + comments), `/profile` (edit dialog,
  followers/following), `components/event-card.tsx`, `components/navbar.tsx`,
  `app/layout.tsx`.
- **Tooling/config:** `frontend/.env.example`, `typecheck` script,
  package name `my-project` → `campusconnect-frontend`.

### Frontend — removed (all recoverable from git history)
| Removed | Reason | Replacement |
|---|---|---|
| `app/students/page.tsx`, `app/students/[id]/page.tsx` | Mock directory/profile | `/people`, `/people/[id]` (+ permanent redirects) |
| `app/teammates/page.tsx` | Skills-based matching has no backend support (ASSUMPTIONS A-03) | `/people` |
| `lib/data.ts` | Hard-coded mock data | `lib/api.ts` |
| `components/student-card.tsx`, `components/profile-view.tsx` | Rendered mock-only fields (skills, projects, clubs) | `person-card.tsx`, `profile-header.tsx` |

### Frontend — changed configuration
- `next.config.mjs`: **removed `typescript.ignoreBuildErrors: true`** (type
  errors now fail the build); added permanent redirects for old routes.
- `app/layout.tsx`: wrapped in `AuthProvider`/`ToastProvider`/`AuthGate`, skip
  link added, `generator: 'v0.app'` metadata removed, Vercel Analytics only
  when `VERCEL=1`.

### Other additions
- `docker-compose.yml` (MongoDB 7 + Neo4j 5; **unverified**, Docker daemon was
  down), root `README.md`, `Backend/scripts/seed_demo.py` (verified against
  the in-memory harness), `Backend/tests/demo_server.py` (harness),
  `e2e/` (Playwright scenario), `GET /api/auth/session` (+test).
- Docs: `ARCHITECTURE.md`, `SETUP.md`, `API.md`, `TESTING.md`; ASSUMPTIONS
  A-09…A-17; pointer note added to `Backend/README.md`.

### Defects found only by running the system
1. `AuthGate` left users on `/login` after sign-in with an incomplete
   profile — fixed (see TESTING.md).
2. Links rendered as `role="button"` — replaced with `LinkButton`.
3. Identical "Follow" button names — now include the person.
4. Analytics script 404 on non-Vercel builds — gated.
5. Truncated feed reasons; raw ISO date in registrations; oversized empty
   poster block; cramped mobile menu — fixed.

### Verification (final code, mocked databases — see TESTING.md)
- `pytest`: 62 passed. `tsc --noEmit`: clean. `next build`: success.
- Browser E2E: 29/29 against the real built frontend and real backend code on
  in-memory MongoDB/Neo4j mocks.

### Remaining concerns / not verified
- Real Neo4j/MongoDB, Google OAuth, and `docker-compose.yml` were never
  exercised (no servers/credentials in this environment).
- Hosts cannot edit or withdraw a submitted event; moderation is one-way
  (A-13). No rate limiting. No automated accessibility audit.
- Nothing has been committed; the working tree contains all changes.
- PROJECT_DOCUMENTATION.md: added historical-document banner

---

## 2026-10-11 — Phase 4: Real databases connected; dark theme

### Real database connection (no code change)
- Created `Backend/.env` (git-ignored) with the Atlas MongoDB URI and Neo4j
  Aura details, a freshly generated `JWT_SECRET_KEY`, and `ENABLE_DEV_LOGIN=true`
  at the user's request to allow testing without Google credentials.
- **Finding:** the Aura instance rejects username `neo4j`; the instance ID is
  the username. Recorded here because it is easy to trip over.
- Verified against the real services: `/health` → both `connected`; MongoDB
  indexes and Neo4j uniqueness constraints created. **Not yet verified against
  real Neo4j:** the feed, follow, count and analytics Cypher (startup only runs
  the constraint statements).

### Dark theme
- **Modified:** `app/globals.css` (branded `.dark` palette), `app/layout.tsx`
  (`<html class="dark">`, `colorScheme: 'dark light'`), `components/navbar.tsx`
  (toggle), `components/status-badge.tsx`, `components/event-card.tsx`,
  `app/events/[id]/page.tsx`, `components/toast.tsx` (dark variants for
  hard-coded amber/red/rose/emerald), `components/ui/dialog.tsx`,
  `components/ui/sheet.tsx` (heavier overlay in dark).
- **Added:** `components/theme-toggle.tsx`.
- **Verification (mock harness on a separate port, nothing written to the real
  databases):** `tsc` clean, `next build` success; screenshots reviewed for
  login, dashboard, host form with errors, My Events, admin queue, reject
  dialog, analytics; toggle persists across reload. Decision: ASSUMPTIONS A-18.

---

## 2026-10-11 — Phase 5: TitanGate-inspired visual language

- **Added:** `components/brand.tsx` (Eyebrow, SectionHeading, StatBlock,
  StepCard, CompareCard, TerminalLine), `components/landing-sections.tsx`,
  `components/sign-in-card.tsx`.
- **Rewritten:** `app/login/page.tsx` (now a server component: hero, typed
  terminal line, sign-in card, how-it-works, feed signals, comparison, footer);
  `components/stat-card.tsx` (display numerals + mono caption).
- **Modified:** `app/globals.css` (light + dark tokens, `--signal`, radius,
  `.grid-bg`, `.poster-grid`, `.caret`), `components/navbar.tsx` (mono "CC"
  mark, section anchors when signed out), `components/state-views.tsx`
  ("Initialising…" loader), `components/event-card.tsx` (grid poster
  placeholder).
- **Reasoning/limits:** see ASSUMPTIONS A-19 — built from a text description of
  the reference site; exact brand values were not available.
- **Verification (mock backend on :8001, real databases untouched):** `tsc`
  clean; `next build` success; screenshots reviewed for landing (dark and
  light), dashboard; browser E2E **29/29** again. `e2e/run.mjs` gained
  `API_PORT_REWRITE` so it can be pointed at the mock backend safely.

---

## 2026-10-12 — Real-database check (read-only)

- Backend and frontend had stopped (machine slept, network dropped); restarted
  both. `/health`: mongodb + neo4j `connected`.
- MongoDB holds pre-existing hand-made records (5 users incl. `USR_ADMIN1`,
  3 events: 2 approved, 1 pending; 2 comments) that were inserted directly, not
  via the app. Neo4j was **empty** (no nodes or relationships): those records
  never went through the graph-writing paths. Not a defect; graph nodes are
  created lazily on first follow/like/register/approve.
- All 24 app Cypher statements validated on the real Aura instance (reads
  executed, writes `EXPLAIN` only). No data was written or deleted.
- Existing admin account email matches `ADMIN_EMAIL`, so it keeps ADMIN on login.
- Aura note: the database name equals the instance ID (`590f6d74`), as does the
  username; the default session reaches it without extra configuration.

---

## 2026-10-16 — Phase 6: Aligning with the team's email/password auth; test-safety incident

### What changed on the team's side (observed in git)
- `aeb11c6` (Abbilaash, 2026-10-12): Google OAuth replaced by email/password
  (`/api/auth/register`, `/login`), recommended events separated from general
  events on the dashboard, frontend API default changed to `127.0.0.1`.
- `5c302cc` (Nivashini, 2026-10-14): `Backend/scripts/populate_demo_integration.py`
  and graph demo data (players, countries, a tournament) added to Neo4j.
- The earlier hand-seeded Mongo users and admin are no longer present.

### Fixed by me
- **Backend tests:** the team's register test failed because test addresses
  used reserved domains (`.test`) that email validation rejects; changed test
  data to `@campus.edu`. One assertion expected "already registered" but the
  service says "already exists"; assertion corrected. Removed dead
  `ENABLE_DEV_LOGIN` settings from `tests/conftest.py` and `tests/demo_server.py`.
  Result: **56 passed**.
- **`Backend/scripts/seed_demo.py`:** now registers accounts (or signs in if
  they exist) instead of the removed dev login; demo password `DemoPass123!`.
  Verified against the in-memory backend.
- **`e2e/run.mjs`:** rewritten for register/sign-in; OAuth-fragment step removed;
  dashboard and outage assertions updated to the team's new wording. Result:
  **28/28** against the in-memory backend.
- **Docs:** `API.md`, `ARCHITECTURE.md`, `SETUP.md`, `TESTING.md`,
  `ASSUMPTIONS.md` (A-04…A-06 marked superseded, A-20 added), `e2e/README.md`.

### Incident (my error): browser test hit the real backend
- The redirect that sends browser API calls to the in-memory backend matched
  `localhost` only; the frontend now defaults to `127.0.0.1`, so one E2E run
  executed against the **real** backend and databases.
- **Left behind (found by read-only audit):** MongoDB — users `USR_E47B7093`
  (admin@campus.edu), `USR_CC534494` (asha@campus.edu), `USR_A821ECF9`
  (bala@campus.edu), event `EV_8BE354FE` ("AI Hackathon", pending). Neo4j —
  `FOLLOWS` Asha→Bala and Bala→Asha; Bala `REGISTERED` and `VIEWED`
  `EV_ROBOT2026` (an existing event; its registration count rose by one).
- **Not deleted.** Removing records from a shared database needs the owner's
  go-ahead; see TESTING.md for the summary and cleanup status.
- **Prevention:** redirect matches both hostnames; `e2e/run.mjs` refuses to run
  unless `API_PORT_REWRITE` or `E2E_BACKEND_IS_DISPOSABLE=1` is set; the fixed
  run was verified by the real backend's write-request count (12 before, 12
  after).

### Real Neo4j verification (side result of the incident)
- Through the app, follow, register and view relationships were written to the
  real Neo4j and read back by the audit, so the backend-to-Neo4j write path works
  with real data. (Not a planned test; recorded because it is the first
  observation of real graph writes.)

### Open
- No admin account exists in the real database (see ASSUMPTIONS A-20).
- Email verification, login rate limiting and stronger PBKDF2 settings are
  recommended, not implemented.

---

## 2026-10-16 — Neo4j cleanup (destructive, requested by the project owner)

- **Request:** remove every Neo4j node and relationship that is not part of the
  app's own model (labels `User`/`Event`; relationships FOLLOWS, HOSTED, LIKED,
  REGISTERED, VIEWED, SHARED).
- **Removed:** 17 nodes (9 unlabelled, 3 `player`, and one each of `student`,
  `Student`, `class`, `Country`, `Tornament`) and 11 relationships
  (`TOPSCORRER_OF`, `is_friend_of`, `WINNER_OF` ×2 each, and `is_student_of`,
  `CAPTAIN_OF`, `WINNERS_OF`, `TOP_SCORER_OF`, `HIGHEST_WICKET_TAKER_OF` ×1 each).
  This was the cricket/student demo data added around commit `5c302cc`.
- **Kept, verified unchanged:** 6 `User`, 1 `Event`, FOLLOWS ×4, REGISTERED ×1,
  VIEWED ×1. No relationship between system nodes was removed.
- **Backup:** the removed nodes and relationships were saved as JSON in the
  session scratch folder (`neo4j_non_system_backup.json`), outside the repo. No
  restore script exists.
- **Process note:** the first attempt was blocked by the permission classifier
  and was not retried by other means; it was re-run on the owner's explicit
  instruction.
- **Heads-up:** `Backend/scripts/populate_demo_integration.py` (the team's
  script) would recreate that demo data if run again.
