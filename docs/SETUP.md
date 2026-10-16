# Setup

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | 3.10+ (3.11 used for development) | backend |
| Node.js | 20+ | frontend |
| pnpm | 10+ (repo pins `pnpm@12.3.4`) | `npx pnpm@10 …` works without installing |
| MongoDB | 6+ (7 recommended) | local, Docker or Atlas |
| Neo4j | **5.x** | pattern comprehensions and `IF NOT EXISTS` constraints need 4.4+/5 |

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
| `ENVIRONMENT` | `development` | `production` refuses to start with placeholder secrets and drops the extra development CORS origins |
| `MONGO_URI` / `MONGO_DB_NAME` | `mongodb://localhost:27017` / `campusconnect` | MongoDB |
| `NEO4J_URI` / `NEO4J_USERNAME` / `NEO4J_PASSWORD` | `bolt://localhost:7687` / `neo4j` / `change_me` | Neo4j |
| `JWT_SECRET_KEY` | placeholder | **Set to ≥ 32 random chars**: `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `JWT_ALGORITHM` / `JWT_EXPIRE_MINUTES` | `HS256` / `1440` | token settings |
| `FRONTEND_URL` | `http://localhost:3000` | CORS origin(s), comma-separated. Outside production, `localhost`/`127.0.0.1` on ports 3000 and 5173 are also allowed |
| `ADMIN_EMAIL` | `admin@example.com` | registering (or signing in) with this email gives the `ADMIN` role |

In `production`, the API **refuses to start** if `JWT_SECRET_KEY` is the
placeholder or shorter than 32 characters, or if `NEO4J_PASSWORD` is the
placeholder.

### Signing in

Accounts use **email and password**. Open the app, choose **Register Now**, and
create an account (password at least 6 characters). Email addresses are
validated, so reserved domains such as `.test` and `.local` are rejected; use a
real-looking domain such as `college.edu`.

**Getting an admin account:** register using exactly the address set in
`ADMIN_EMAIL`. That account gets the `ADMIN` role and the Admin console. There
is no email verification, so on a real deployment set `ADMIN_EMAIL` to an
address you control and register it **first**, before anyone else can claim it.
If you change `ADMIN_EMAIL`, restart the backend; the role is applied when that
address registers or signs in.

### Demo data (optional)
With the API running:
```bash
python scripts/seed_demo.py --base-url http://localhost:8000 --admin-email <ADMIN_EMAIL>
```
Registers 5 students and the admin (all with the demo password
`DemoPass123!`; existing accounts are signed in instead), then creates 6 events
(5 approved, 1 pending), a follow graph and interactions through the public
API. **This writes real records** to whichever databases the API is using.

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
| Register says the email already exists | That address is already registered; sign in instead |
| API exits at start-up in production | placeholder secret detected (see above) |
