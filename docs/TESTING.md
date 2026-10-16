# Testing

> **Read this first.** Unless a result says otherwise, no MongoDB or Neo4j server
> were available in the environment where this work was verified (Docker
> Desktop's daemon was not running; no `mongod`/`neo4j` binaries). Every
> result below was obtained against **mocks**, and is labelled as such. What
> is and is not proven is spelled out in [Unverified](#unverified).

## Layers

| Layer | Tooling | What it exercises | Mocked? |
|---|---|---|---|
| Backend API tests | pytest, pytest-asyncio, httpx `ASGITransport` | Real FastAPI app, routes, services, auth, validation | MongoDB = `mongomock-motor`; Neo4j = `tests/fake_graph.py` |
| Type check | `tsc --noEmit` | Whole frontend | — |
| Production build | `next build` (type errors fail the build) | Compilation, static generation | — |
| Browser E2E | Playwright (`playwright-core` + Chrome) | Real built frontend ↔ real backend code over HTTP | Same MongoDB/Neo4j mocks via `tests/demo_server.py` |

### What the mocks are
- **`mongomock-motor`** — an in-memory MongoDB-compatible client. Faithful for
  the operators used here, but not a real server (no index enforcement
  semantics beyond what mongomock implements, no text search, no real
  concurrency).
- **`tests/fake_graph.py`** — an in-memory edge set that **recognises the
  specific Cypher statements this codebase issues** (by distinctive fragments)
  and applies equivalent semantics. It does **not** parse Cypher. A passing
  test therefore shows the *application logic* around each query is right
  given the query's intended meaning — not that the Cypher text is valid or
  returns that on a real Neo4j. An unrecognised query raises, so adding a new
  query without teaching the fake fails loudly.

## Commands and results

Executed on 2026-10-11 against the final code:

| Command | Result |
|---|---|
| `cd Backend && .venv/Scripts/python -m pytest -q` | **56 passed** (mocked) |
| `cd frontend && ./node_modules/.bin/tsc --noEmit` | exit 0, no errors |
| `cd frontend && ./node_modules/.bin/next build` | success; 12 routes generated |
| `e2e/run.mjs` against a fresh in-memory backend + the built frontend (2026-10-16) | **28/28 steps passed** (mocked databases) |

### Running them yourself
```bash
# backend tests
cd Backend && pip install -r requirements-dev.txt && python -m pytest -q

# frontend
cd frontend && pnpm install && pnpm exec tsc --noEmit && pnpm build

# browser E2E on a machine with no databases (mocks!)
cd Backend && python tests/demo_server.py          # :8000, in-memory
cd frontend && pnpm start                          # :3000 (after build)
cd e2e && npm install && npm test
```

## Backend test inventory (`Backend/tests/`)

| File | Covers |
|---|---|
| `test_auth_and_health.py` | Live health/degraded reporting; production config validation; register (profile saved, duplicate email rejected, `ADMIN_EMAIL` gets ADMIN); login (wrong password 401); session endpoint; missing/invalid token 401; no exception text leaks |
| `test_events.py` | Create + canonicalisation; 8 invalid-input cases (URL schemes, time order, impossible dates, bad category, blank title, tag count); pending hidden publicly; filters + literal regex search; upcoming excludes past; draft visibility (404 for others); like/register/unlike counts and per-user flags; counts in lists; interactions blocked on unapproved events; unique-viewer counting; registered/hosted lists; **graph outage ⇒ 503 on writes, 200 degraded on reads** |
| `test_social_feed_admin.py` | Follow/unfollow/status/idempotency; self/unknown/incomplete targets; **mutuals regression**; common-interest de-duplication; suggestions ranking; directory filters and email privacy; profile update + counts; **feed ranking, reason grammar, upcoming-only fallback, outage fallback**; comments lifecycle/permissions/visibility; admin authz; moderation lifecycle; **state-transition enforcement**; approve-while-graph-down stays pending; analytics values; analytics 503 |

Regression tests are named after the defect they pin (see
IMPLEMENTATION_LOG.md Phase 2 table).

## Browser scenario (`e2e/run.mjs`)

Three users in separate browser contexts (host, admin, attendee) plus a
390 px mobile context. Steps cover: unauthenticated redirect; login screen;
login screen and wrong-credentials error; legacy-route redirect; registration
and duplicate-email rejection; dashboard empty states; host-form client validation (including
`javascript:` URL rejection); submission → pending; invisibility of pending
events; admin sign-in via `ADMIN_EMAIL`; moderation approve; non-admin
blocked; list search/filter/clear; optimistic register/like that persists
across reload; detail page, comment add/delete; follow from directory and
profile; **the social feed showing "Bala Kumar registered for this event"**;
profile edit dialog; My Events; admin analytics; invalid-token recovery;
unknown event; simulated API outage (recoverable error state); mobile layout
with no horizontal overflow and a working menu.

## Defects found by running the system (not by reading it)
1. **`AuthGate` stranded users on `/login`** after sign-in with an incomplete
   profile (login treated as exempt from the onboarding redirect). Found by
   E2E; fixed (the onboarding redirect still exists for accounts with an
   incomplete profile).
2. **Navigation rendered as `<a role="button">`** (Base UI non-native
   `Button`), mislabelling links for assistive tech. Replaced with a real
   `LinkButton`.
3. **Follow buttons were indistinguishable to screen readers** ("Follow" ×N).
   They now carry the person's name.
4. **Vercel Analytics script requested on non-Vercel production builds**
   (console 404). Now only rendered when `VERCEL=1`.
5. Feed reason was truncated mid-sentence on cards; registrations showed a raw
   ISO date. Fixed.

## Unverified
| Area | Why | What would verify it |
|---|---|---|
| Cypher *behaviour with real data* on Neo4j | **Partly verified (2026-10-12):** all 24 statements were validated on the real Aura instance (15 read queries executed against the empty graph; 9 write queries only `EXPLAIN`ed, not executed). Results over populated data, and actual write effects, are not yet observed | Use the app (follow, like, register, approve) and re-run the read-only count check |
| Real MongoDB behaviours (unique indexes, concurrent first-login race, aggregation edge cases) | mongomock | Same as above; add a concurrency test |
| Email-verification / admin claim | There is no email verification: whoever registers the `ADMIN_EMAIL` address first becomes ADMIN. Not a test gap, a design gap | Add verification, or register the admin account first on deploy |
| `docker-compose.yml` | Docker daemon not running | `docker compose up -d` and `GET /health` |
| Cross-browser / real devices | Only desktop Chrome and a 390 px emulated viewport | Manual pass on Safari/Firefox/mobile |
| Accessibility beyond structure | No automated audit (axe) or screen-reader run | Run axe in the E2E; manual NVDA/VoiceOver pass |
| Load/performance | Not measured | Load-test list/feed endpoints with realistic data volume |
| Light theme after the dark-theme change | Dark is the default and was reviewed screen by screen; the light theme was re-checked only on the dashboard toggle round trip | Visual pass over every page in light mode |

## Known limitations affecting tests
- The E2E needs a fresh backend; it is not idempotent.
- The in-memory harness is a verification aid, not a deployment mode.

## Incident: browser test reached the real backend (2026-10-16)

While updating the browser scenario for the new email/password sign-in, the
test run was meant to be redirected to the in-memory backend but was not. The
frontend's default API address had been changed to `127.0.0.1`, and the
redirect only matched `localhost`, so one run executed against the **real**
backend and databases.

It left test data behind: 3 users (`admin@campus.edu`, `asha@campus.edu`,
`bala@campus.edu`, all plain USER), 1 pending event ("AI Hackathon"), follow
edges between Asha and Bala in Neo4j, and Bala's REGISTERED and VIEWED edges to
an existing event. Nothing was deleted or modified besides those additions
(Bala's registration raised that event's count by one). Cleanup is recorded in
IMPLEMENTATION_LOG.md.

Fixes: the redirect now matches both `localhost` and `127.0.0.1`, and
`e2e/run.mjs` **refuses to run** unless a disposable backend is declared
(`API_PORT_REWRITE` or `E2E_BACKEND_IS_DISPOSABLE=1`). The corrected run was
verified by comparing the real backend's write-request count before and after
(12 and 12), while the in-memory backend handled the writes.
