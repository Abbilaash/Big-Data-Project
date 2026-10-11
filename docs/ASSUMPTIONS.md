# Assumptions and Engineering Decisions

This file records decisions made independently during implementation, with the
reasoning behind them. Each entry separates what is **known** (verified from the
repository), what is **assumed**, and what is **unresolved**.

Status legend: `Decided` (implemented), `Provisional` (reversible, would like
confirmation), `Open` (unresolved question).

Last updated: 2026-10-11 (after implementation and verification).

---

## A-01 Product scope: what "the whole system" means

- **Ambiguity:** The request is "implement the whole system based on the idea".
  The root README contains only a title.
- **Known (verified):** `docs/PROJECT_DOCUMENTATION.md` and the backend README
  describe CampusConnect: a college event discovery and student networking
  platform with Google login, event submission with admin moderation, likes /
  registrations / views / shares, follows, a graph-ranked personalised feed,
  comments, and admin analytics. The FastAPI backend implements nearly all of
  this; the Next.js frontend is a static prototype backed by `lib/data.ts`.
- **Decision (Decided):** The product is the backend's feature set, delivered
  through a real frontend. Scope = wire the frontend to the existing backend,
  fix backend defects, and add only the backend endpoints the UI genuinely needs.
- **Alternatives considered:** Rebuilding the backend from scratch (rejected –
  it is largely sound and uses the intended MongoDB + Neo4j design); keeping the
  mock frontend features (rejected – see A-03).
- **Risk:** The original authors may have intended features beyond the backend
  (e.g. skills-based teammate matching). See A-03.

## A-02 Keep the existing technology stack

- **Known:** FastAPI + Motor + Neo4j async driver; Next.js 16 / React 19 /
  Tailwind v4 / shadcn (base-ui).
- **Decision (Decided):** No framework changes. Additions are limited to test
  tooling (pytest, pytest-asyncio, mongomock-motor).
- **Reason:** Hybrid MongoDB + Neo4j persistence is the project's central "big
  data" idea; the UI kit is already in place.

## A-03 Teammates / skills / projects / clubs mock features

- **Ambiguity:** The prototype UI shows skills, interests, projects, clubs and a
  "Find Teammates" page. The backend has none of these fields or endpoints.
- **Known:** The user model is `name, email, year, department, profile_picture,
  role`. `PROJECT_DOCUMENTATION.md` §9 lists this as an open gap and offers two
  options: add skills to the backend, or drop them from the UI.
- **Decision (Decided, implemented — still needs confirmation):** Do not
  invent unsupported product surface. `/teammates` and `/students` were replaced
  by one `/people` page driven by real data (search, department/year filters,
  friends-of-friends suggestions with mutual-connection counts). Mock skills,
  `projects`, `clubs`, `interests`, "Events Attended" are not displayed. Old
  URLs permanently redirect to `/people`.
- **Why:** Showing fabricated skills/projects would be misleading content in a
  production-facing flow, which the brief forbids.
- **Needs confirmation:** If skills-based matching is wanted, it is a clean
  follow-up: `skills: list[str]` on users plus `(:User)-[:HAS_SKILL]->(:Skill)`.
- **Impact:** The `/teammates` route and `lib/data.ts` mock module are removed or
  replaced (logged in IMPLEMENTATION_LOG.md).

## A-04 Authentication: Google OAuth only, plus a gated dev login

- **Known:** Login is Google OAuth 2.0 only. No Google credentials exist in the
  repository or environment, so the real flow cannot be exercised here.
- **Decision (Decided):** Keep Google OAuth as the production login. Add a
  development-only login endpoint, disabled unless `ENABLE_DEV_LOGIN=true`, so
  the application is demonstrable without Google credentials. It refuses to
  enable itself when `ENVIRONMENT=production`.
- **Alternatives:** Password auth (rejected – new credential storage surface,
  not part of the design); mocking Google (rejected – would fake an integration).
- **Risk:** A dev login is a bypass by design. Mitigations: off by default,
  hard-blocked in production, documented in SETUP.md, logged at startup.
- **Unverified:** The live Google flow remains unverified against Google itself.

## A-05 Token transport after OAuth callback

- **Known:** The callback redirects with `?token=<JWT>` in the query string,
  which leaks into history, logs and Referer headers (documented as a security
  concern).
- **Decision (Provisional):** Deliver the token in the URL **fragment**
  (`#token=…`) instead of the query string. Fragments are not sent to servers
  or in Referer headers. The frontend reads it once, stores it, and strips it
  from the address bar.
- **Alternative:** HttpOnly cookie – stronger against XSS, but needs
  same-site deployment or cross-site cookie config; deferred.
- **Residual risk:** Token is held in `localStorage` and is readable by XSS.

## A-06 OAuth `state` / CSRF protection

- **Decision (Decided):** The backend issues a signed, short-lived `state`
  (JWT) at `/google/login` and verifies it in the callback. A missing or invalid
  state rejects the callback.

## A-07 Graph write failures must not be silent

- **Known:** `execute_query` catches all errors and returns `[]`, so a failed
  write reports success.
- **Decision (Decided):** Writes raise a `GraphUnavailableError` mapped to HTTP
  503. Read paths that are decorative (counts, feed social context) degrade to
  empty results instead of failing the whole page.

## A-08 Verification environment limits

- **Verified fact:** At the time of analysis Docker Desktop's daemon was not
  running and no `mongod`/`neo4j` binaries exist on PATH.
- **Consequence:** Live MongoDB/Neo4j integration cannot be exercised in this
  environment. Backend tests use `mongomock-motor` and an in-memory graph
  fake. These are **mocked** verifications and are labelled as such in
  TESTING.md. Cypher query correctness against a real Neo4j is unverified.

## A-09 Event categories are a fixed set

- **Ambiguity:** The backend accepted any 2–50 char category; the prototype UI
  filtered on six fixed values.
- **Decision (Decided):** `Hackathon, Workshop, Bootcamp, Seminar, Contest,
  Meetup, Cultural, Sports, Other` (the six prototype values plus three common
  campus categories). Input is matched case-insensitively and stored in the
  canonical spelling; `GET /api/events/categories` serves the list.
- **Why:** Free text fragments filters and analytics ("hackathon" vs
  "Hackathon").
- **Risk:** Existing documents with other categories still list and filter but
  cannot be created anew. **Needs confirmation** that this set matches the
  campus's reality; it is a one-line change in `schemas/event.py`.

## A-10 Departments and years in the profile forms

- **Known:** Backend stores `department` as free text and `year` as 1–6. The
  prototype listed CSE, IT, AI&DS, ECE.
- **Decision (Provisional):** The frontend offers `CSE, IT, AI&DS, ECE, EEE,
  MECH, CIVIL, Other` (`frontend/lib/constants.ts`). The backend is unchanged
  and still accepts any string; the directory's department filter is built from
  the values actually stored. The extra codes are my assumption about a
  technical campus.
- **Needs confirmation:** the real department list (or a backend-managed one).

## A-11 Privacy: email is not public or searchable

- **Known:** The old user search matched on email, which let anyone confirm
  whether a given address had an account; public profiles did not show email.
- **Decision (Decided):** Removed email from search; the directory never returns
  it. Email is visible only on one's own profile.

## A-12 Draft events return 404, not 403, to non-owners

- **Decision (Decided):** A 403 confirms an event ID exists. Returning 404
  avoids disclosing other people's submissions. Changes documented status
  codes (API.md).

## A-13 Moderation is one-way

- **Ambiguity:** The original allowed approving a rejected event and
  re-rejecting an approved one, indefinitely.
- **Decision (Decided):** Only `pending` events can be moderated; others get
  409. No "un-publish" or "reconsider" exists.
- **Impact / limitation:** An admin who approves by mistake cannot undo it via
  the API. Hosts also cannot edit or withdraw a submission — a gap, not a
  deliberate product choice. **Needs confirmation** whether edit/withdraw and
  an admin "unpublish" are wanted.

## A-14 Graph writes fail loudly; some reads degrade silently

- **Decision (Decided):** Beyond A-07: counts, feed social context and
  suggestions return empty/zero when the graph is down so pages still render,
  but **admin network analytics return 503** because silent zeros would be
  misleading. Onboarding (`complete-profile`) and profile-name sync tolerate a
  graph outage because Mongo is the source of truth and nodes are created
  lazily.
- **Risk:** Users may briefly see "0 registrations" during an outage while
  their registration is intact in the graph.

## A-15 Token storage in `localStorage`

- **Decision (Provisional):** Keep the bearer token in `localStorage`
  (simple, works across the separate API origin). Risk: readable by XSS. The
  app renders user content only through React text nodes, has no
  `dangerouslySetInnerHTML`, restricts URLs to http(s), and sets `no-referrer`
  on external images — but an HttpOnly-cookie session would be stronger.
- **Needs confirmation** if the deployment can serve both apps same-site.

## A-16 In-memory harness is a test aid only

- **Decision (Decided):** `Backend/tests/demo_server.py` boots the real app on
  mocked databases solely so the frontend could be exercised end to end where no
  database servers exist. It is not documented as a way to run the product,
  and its results are labelled as mocked wherever they appear.

## A-17 Not built (explicitly out of scope)

Notifications and email, direct messaging, event edit/withdraw, calendar
export, image upload (posters are URLs), password/email sign-up, rate limiting,
i18n, app Dockerfiles. None were in the original backend; adding
them would be new product scope rather than completing the existing one.

## A-18 Dark theme is the default

- **Request:** "change ui to darker theme".
- **Decision (Decided):** Dark is the default; a Sun/Moon toggle in the navbar
  (and mobile menu) switches to the original light theme, persisted in
  `localStorage` (`cc_theme`). Default is server-rendered on `<html class="dark">`,
  so there is no inline script; a user who chose light sees a brief dark flash on
  load.
- **Palette:** an indigo-tinted dark scale rather than the neutral grey scaffold
  values. `--primary` is a *light* periwinkle with dark foreground text so it
  keeps contrast both as a button fill and as link/icon text.
- **Alternatives considered:** dark-only (rejected: removes a working theme at
  no benefit); follow OS setting (rejected: user asked for dark explicitly).
- **Risk:** The light theme is lightly re-verified (see TESTING.md).

## A-19 Visual language: "TitanGate Equity"-inspired

- **Request:** use the design of titangatequity.com with similar components.
- **What was known (verified):** a text extraction of the page: dark/technical
  tone, a loader ("Initialising…"), large display headings, small lowercase
  eyebrow labels, numbered process steps ("01 / 04"), large stat figures,
  "old world vs new" comparison cards, a typed terminal-style line, a logo wall,
  anchor navigation with a distinct login button.
- **What was NOT available:** the site's actual colours, fonts, radii and
  spacing. A request to render the page and read its computed styles was not
  carried out; I worked only from the text description.
- **Decision (Decided, approximate):** near-black neutral surfaces, monochrome
  text and white primary buttons, one mint "signal" accent
  (`--signal`) for numerals, eyebrows and the terminal line, 6 px base radius,
  system sans + monospace labels. Components added: `Eyebrow`, `SectionHeading`,
  `StatBlock`, `StepCard`, `CompareCard`, `TerminalLine`
  (`components/brand.tsx`). The app's sign-in page became a landing page using
  them; stat tiles, loaders, poster placeholders and the navbar were restyled.
- **Not copied:** logo, name, copy, imagery. All text is original; the "signal"
  numbers on the landing page are the real feed weights (4/3/2/1), not made-up
  statistics. No logo wall: there are no partner logos to show.
- **Needs confirmation:** exact palette/fonts. Screenshots of the reference
  site, or a one-line palette/typeface, would let me tighten the match; only
  `app/globals.css` tokens would change.
- **Supersedes:** the indigo dark palette from A-18. Light theme remains
  available via the toggle and was re-tinted to the same monochrome language.

## Open questions

1. Should skills / teammate matching be a real feature? (A-03)
2. Is the intended campus single-tenant PSG Tech, or should branding be generic?
   Assumed PSG Tech per the FastAPI description; UI copy stays generic.
3. Should events support an end-of-event "attended" state? Not in the backend;
   not added. (The prototype's "Events Attended" stat was dropped.)
4. Should hosts be able to edit or withdraw an event, and should admins be able
   to unpublish? (A-13)
5. What is the real department list, and is the category set right? (A-09, A-10)
