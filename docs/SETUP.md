# Setup

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | 3.10+ (3.11 used for development) | backend |
| Node.js | 20+ | frontend |
| pnpm | 10+ (repo pins `pnpm@12.3.4`) | `npx pnpm@10 …` works without installing |
| MongoDB | 6+ (7 recommended) | local, Docker or Atlas |
| Neo4j | **5.x** | pattern comprehensions and `IF NOT EXISTS` constraints need 4.4+/5 |
| Google OAuth client | — | only for real Google sign-in |

## 1. Databases

```bash
docker compose up -d       # starts MongoDB :27017 and Neo4j :7474/:7687
```
`docker-compose.yml` sets the Neo4j password to `change_me` for **local use
only**. *(The compose file has not been exercised in this repo's verification
environment — Docker was not running there.)*

Indexes and constraints are created automatically on API start-up.

## 2. Backend

```bash
cd Backend
python -m venv .venv
. .venv/Scripts/activate            # Windows (Git Bash) — or: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                # then edit
python run.py                       # http://localhost:8000  (Swagger at /docs)
```

### Environment variables (`Backend/.env`)

| Variable | Default | Purpose |
|---|---|---|
| `ENVIRONMENT` | `development` | `production` enforces real secrets and disables dev login |
| `MONGO_URI` / `MONGO_DB_NAME` | `mongodb://localhost:27017` / `campusconnect` | MongoDB |
| `NEO4J_URI` / `NEO4J_USERNAME` / `NEO4J_PASSWORD` | `bolt://localhost:7687` / `neo4j` / `change_me` | Neo4j |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | placeholders | Google OAuth |
| `GOOGLE_REDIRECT_URI` | `http://localhost:8000/api/auth/google/callback` | must match the Google console |
| `JWT_SECRET_KEY` | placeholder | **Set to ≥ 32 random chars**: `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `JWT_ALGORITHM` / `JWT_EXPIRE_MINUTES` | `HS256` / `1440` | token settings |
| `FRONTEND_URL` | `http://localhost:3000` | CORS origin(s), comma-separated; first is the login redirect target |
| `ADMIN_EMAIL` | `admin@example.com` | the account with this email becomes `ADMIN` at sign-in |
| `ENABLE_DEV_LOGIN` | `false` | enables `POST /api/auth/dev-login` (never in production) |

In `production`, the API **refuses to start** if `JWT_SECRET_KEY` is the
placeholder or shorter than 32 characters, or if `NEO4J_PASSWORD` is the
placeholder.

### Signing in

*With Google:* create an OAuth 2.0 **Web application** client in Google Cloud
Console, add the redirect URI above, and put the client ID/secret in `.env`.

*Without Google (development only):* set `ENABLE_DEV_LOGIN=true`. The login
page then shows a "Developer sign-in" form. Use the `ADMIN_EMAIL` value to
get the admin console. **Do not enable this on a deployment real users reach.**

### Demo data (optional)
With dev login enabled and the API running:
```bash
python scripts/seed_demo.py --base-url http://localhost:8000
```
Creates 5 students, 6 events (5 approved, 1 pending), a follow graph and
interactions through the public API.

## 3. Frontend

```bash
cd frontend
cp .env.example .env.local          # NEXT_PUBLIC_API_URL=http://localhost:8000
pnpm install
pnpm dev                            # http://localhost:3000
```
Production: `pnpm build && pnpm start`. `NEXT_PUBLIC_API_URL` is inlined at
**build** time. The build runs the TypeScript check (it was previously
disabled); a type error fails the build.

## 4. Running the tests
See [TESTING.md](TESTING.md).

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Login page says server unreachable | API not running, wrong `NEXT_PUBLIC_API_URL`, or CORS: `FRONTEND_URL` must equal the exact browser origin |
| `/health` → `neo4j: disconnected` | Neo4j down or wrong credentials; reads degrade, writes return 503 |
| Google sign-in lands on `/login` with an error | OAuth `state` expired (10 min) or redirect URI mismatch |
| API exits at start-up in production | placeholder secret detected (see above) |
