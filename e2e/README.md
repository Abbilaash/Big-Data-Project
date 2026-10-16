# End-to-end scenario

28 browser steps covering sign-in and registration, hosting, moderation,
registering, liking, commenting, following, the social feed, admin analytics,
session expiry, error states and a mobile viewport.

## ⚠ This test writes data

It registers users, creates events and follows people. **Never run it against a
real database.** The script refuses to start unless you declare a disposable
backend (see below).

## Run

Needs a **fresh** in-memory backend started with `ADMIN_EMAIL=admin@campus.edu`
(the harness sets this itself) and the built frontend on `BASE_URL`.

```bash
# terminal 1 — in-memory MOCK backend on port 8001 (no databases involved)
cd Backend && PORT=8001 python tests/demo_server.py
# terminal 2 — the built frontend (it talks to :8000 by default)
cd frontend && pnpm build && pnpm start
# terminal 3 — redirect the browser's API calls from :8000 to the mock on :8001
cd e2e && npm install && API_PORT_REWRITE=8000:8001 npm test
```

`API_PORT_REWRITE=from:to` matches both `localhost` and `127.0.0.1`. If your
frontend is already built against a throwaway backend, set
`E2E_BACKEND_IS_DISPOSABLE=1` instead.

Other settings: `BASE_URL` (default `http://localhost:3000`), `CHROME_PATH` (a
Chrome/Chromium binary; otherwise Playwright's `chrome` channel is used).
Screenshots go to `e2e/shots/` (git-ignored).

After a run you can confirm nothing reached a real backend: its request log
should show no new POST/DELETE/PATCH lines.
