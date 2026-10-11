# End-to-end scenario

29 browser steps covering sign-in, onboarding, hosting, moderation, registering,
liking, commenting, following, the social feed, admin analytics, session expiry,
error states and a mobile viewport.

## Run

Needs a **fresh** backend with `ENABLE_DEV_LOGIN=true` and
`ADMIN_EMAIL=admin@campus.local`, and the frontend on `BASE_URL`.

Without database servers, use the in-memory harness (mocks, see docs/TESTING.md):

```bash
# terminal 1
cd Backend && python tests/demo_server.py
# terminal 2
cd frontend && pnpm build && pnpm start
# terminal 3
cd e2e && npm install && npm test
```

Environment: `BASE_URL` (default `http://localhost:3000`), `CHROME_PATH` (path to
a Chrome/Chromium binary; otherwise Playwright's `chrome` channel is used).
Screenshots are written to `e2e/shots/` (git-ignored).

## Pointing the UI at a different backend

If the built frontend targets a backend you must not write test data to (for
example your real databases on `:8000`), run the mock harness on another port
and rewrite the browser's API calls:

```bash
PORT=8001 python Backend/tests/demo_server.py
API_PORT_REWRITE=8000:8001 npm test
```
