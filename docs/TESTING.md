# Testing

> **Read this first.** No MongoDB or Neo4j server and no Google credentials
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
| `cd Backend && .venv/Scripts/python -m pytest -q` | **62 passed** (mocked) |
| `cd frontend && ./node_modules/.bin/tsc --noEmit` | exit 0, no errors |
| `cd frontend && ./node_modules/.bin/next build` | success; 12 routes generated |
| `cd e2e && node run.mjs` (fresh in-memory backend + built frontend) | **29/29 steps passed** (mocked databases) |

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
| `test_auth_and_health.py` | Live health/degraded reporting; production config validation; dev-login gating; onboarding flow; signed OAuth state (missing, forged, wrong-type token); token in fragment not query; no exception text leaks; 401 handling |
| `test_events.py` | Create + canonicalisation; 8 invalid-input cases (URL schemes, time order, impossible dates, bad category, blank title, tag count); pending hidden publicly; filters + literal regex search; upcoming excludes past; draft visibility (404 for others); like/register/unlike counts and per-user flags; counts in lists; interactions blocked on unapproved events; unique-viewer counting; registered/hosted lists; **graph outage ⇒ 503 on writes, 200 degraded on reads** |
| `test_social_feed_admin.py` | Follow/unfollow/status/idempotency; self/unknown/incomplete targets; **mutuals regression**; common-interest de-duplication; suggestions ranking; directory filters and email privacy; profile update + counts; **feed ranking, reason grammar, upcoming-only fallback, outage fallback**; comments lifecycle/permissions/visibility; admin authz; moderation lifecycle; **state-transition enforcement**; approve-while-graph-down stays pending; analytics values; analytics 503 |

Regression tests are named after the defect they pin (see
IMPLEMENTATION_LOG.md Phase 2 table).

## Browser scenario (`e2e/run.mjs`)

Three users in separate browser contexts (host, admin, attendee) plus a
390 px mobile context. Steps cover: unauthenticated redirect; login screen;
OAuth error fragment; legacy-route redirect; forced onboarding and its
validation; dashboard empty state; host-form client validation (including
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
   E2E; fixed; covered by the "forced onboarding" step.
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
| Cypher validity and semantics on real Neo4j 5 | Only a pattern-matching fake was available | Run `pytest` + `seed_demo.py` + the E2E against `docker compose up` databases |
| Real MongoDB behaviours (unique indexes, concurrent first-login race, aggregation edge cases) | mongomock | Same as above; add a concurrency test |
| Google OAuth round trip | No credentials | Sign in once with a real client ID; check the fragment redirect and `state` expiry |
| `docker-compose.yml` | Docker daemon not running | `docker compose up -d` and `GET /health` |
| Cross-browser / real devices | Only desktop Chrome and a 390 px emulated viewport | Manual pass on Safari/Firefox/mobile |
| Accessibility beyond structure | No automated audit (axe) or screen-reader run | Run axe in the E2E; manual NVDA/VoiceOver pass |
| Load/performance | Not measured | Load-test list/feed endpoints with realistic data volume |
| Light theme after the dark-theme change | Dark is the default and was reviewed screen by screen; the light theme was re-checked only on the dashboard toggle round trip | Visual pass over every page in light mode |

## Known limitations affecting tests
- The E2E needs a fresh backend; it is not idempotent.
- The in-memory harness is a verification aid, not a deployment mode.
