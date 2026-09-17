# CampusConnect Backend

CampusConnect is a social-media-style college event discovery platform powered by a hybrid database architecture combining **MongoDB** and **Neo4j**.

---

## 1. Project Overview

CampusConnect enables college students to:
- Discover events submitted by fellow students (hosts).
- Follow other students and view their event activities.
- Like, register for, view, and share events.
- Receive a personalized social feed driven by real-time graph interactions.
- Provide moderation controls for campus administrators to review and approve submitted events.

---

## 2. Hybrid Database Architecture

The backend leverages a hybrid database model:

```
                            ┌─────────────────────────────────┐
                            │      FastAPI App (Python)       │
                            └────────┬───────────────┬────────┘
                                     │               │
                     MongoDB (Document)             Neo4j (Graph)
              ┌────────────────────────┐         ┌───────────────────────┐
              │ • User Profiles        │         │ • User & Event Nodes  │
              │ • Event Content        │         │ • FOLLOWS             │
              │ • Event Comments       │         │ • HOSTED              │
              │ • Aggregations         │         │ • LIKED / REGISTERED  │
              └────────────────────────┘         │ • VIEWED / SHARED     │
                                                 └───────────────────────┘
```

- **MongoDB** is the source of truth for rich event documents, user profiles, and comments.
- **Neo4j** is the source of truth for social relationships and event interactions.

---

## 3. MongoDB Responsibilities

Collections:
- `users`: User profile documents (`user_id`, `google_id`, `email`, `name`, `year`, `department`, `role`, `profile_completed`, timestamps).
- `events`: Complete event metadata (`event_id`, `title`, `description`, `category`, `host_id`, `date`, `start_time`, `end_time`, `venue`, `status`, timestamps).
- `comments`: Event comments (`comment_id`, `event_id`, `user_id`, `content`, `created_at`).

---

## 4. Neo4j Responsibilities

Graph Schema:
- **Nodes**:
  - `(:User {user_id, name, email})`
  - `(:Event {event_id})`
- **Relationships**:
  - `(:User)-[:FOLLOWS]->(:User)`
  - `(:User)-[:HOSTED]->(:Event)`
  - `(:User)-[:LIKED]->(:Event)`
  - `(:User)-[:REGISTERED]->(:Event)`
  - `(:User)-[:VIEWED {first_viewed_at, last_viewed_at, count}]->(:Event)`
  - `(:User)-[:SHARED]->(:Event)`

---

## 5. Environment Variables (`.env`)

| Variable | Description | Default / Example |
|---|---|---|
| `MONGO_URI` | MongoDB connection string | `mongodb://localhost:27017` |
| `MONGO_DB_NAME` | Database name | `campusconnect` |
| `NEO4J_URI` | Neo4j Bolt URI | `bolt://localhost:7687` |
| `NEO4J_USERNAME` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | `change_me` |
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID | `your_google_client_id` |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret | `your_google_client_secret` |
| `GOOGLE_REDIRECT_URI` | Google OAuth Callback URL | `http://localhost:8000/api/auth/google/callback` |
| `JWT_SECRET_KEY` | Secret key for signing JWTs | `long_random_secret_string` |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `JWT_EXPIRE_MINUTES` | Token expiration time | `1440` |
| `FRONTEND_URL` | Frontend URL for CORS & redirects | `http://localhost:5173` |
| `ADMIN_EMAIL` | Google login email automatically assigned ADMIN role | `admin@example.com` |

---

## 6. Installation & Running Locally

### Step 1: Create a Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env` and fill in your database URIs and Google OAuth credentials:
```bash
cp .env.example .env
```

### Step 4: Run FastAPI Server
```bash
python run.py
```
Or directly using Uvicorn:
```bash
uvicorn app.main:app --reload --port 8000
```

Access automatic Swagger documentation at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## 7. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project and configure the OAuth consent screen.
3. Create Credentials -> OAuth 2.0 Client IDs (Web application).
4. Set Authorized redirect URIs: `http://localhost:8000/api/auth/google/callback`.
5. Copy `CLIENT_ID` and `CLIENT_SECRET` into `.env`.

---

## 8. Database Setup

### MongoDB Setup
Install MongoDB locally or use MongoDB Atlas. Ensure `MONGO_URI` points to your instance.

### Neo4j Setup
Install Neo4j Desktop / Enterprise or use Neo4j Aura. Ensure `NEO4J_URI`, `NEO4J_USERNAME`, and `NEO4J_PASSWORD` are configured.

---

## 9. API Endpoints Summary

### Auth
- `GET /api/auth/google/login` - Initiate Google OAuth login
- `GET /api/auth/google/callback` - OAuth callback handler
- `POST /api/auth/complete-profile` - Complete first-time user profile (`name`, `year`, `department`)

### Users
- `GET /api/users/me` - Get current user profile
- `PATCH /api/users/me` - Update current user profile
- `GET /api/users/search?q=` - Search users by name/email/department
- `GET /api/users/{user_id}` - Get public user profile
- `GET /api/users/{user_id}/followers` - Get followers list
- `GET /api/users/{user_id}/following` - Get following list

### Social Graph
- `POST /api/social/follow/{user_id}` - Follow a user
- `DELETE /api/social/follow/{user_id}` - Unfollow a user
- `GET /api/social/status/{user_id}` - Check follow status
- `GET /api/social/followers` - Get my followers
- `GET /api/social/following` - Get my following list
- `GET /api/social/mutuals/{user_id}` - Get mutual connections
- `GET /api/social/common-interests/{user_id}` - Get shared event interactions

### Events
- `POST /api/events` - Submit an event (status = `pending`)
- `GET /api/events` - List approved events (supports pagination, category filter, date, search)
- `GET /api/events/upcoming` - List upcoming approved events
- `GET /api/events/my-hosted` - List events submitted by current user
- `GET /api/events/{event_id}` - Get complete event details (Mongo content + Neo4j interaction metrics)
- `POST /api/events/{event_id}/like` - Like event
- `DELETE /api/events/{event_id}/like` - Unlike event
- `POST /api/events/{event_id}/register` - Register for event
- `DELETE /api/events/{event_id}/register` - Unregister from event
- `POST /api/events/{event_id}/view` - Record event view
- `POST /api/events/{event_id}/share` - Record event share

### Social Feed
- `GET /api/feed` - Get personalized hybrid feed

### Admin
- `GET /api/admin/events/pending` - List pending event submissions
- `GET /api/admin/events/{event_id}` - Inspect event submission
- `POST /api/admin/events/{event_id}/approve` - Approve event (creates `HOSTED` relationship in Neo4j)
- `POST /api/admin/events/{event_id}/reject` - Reject event
- `GET /api/admin/analytics/events` - MongoDB aggregation analytics
- `GET /api/admin/analytics/network` - Neo4j graph network analytics

### Comments
- `POST /api/events/{event_id}/comments` - Post comment on event
- `GET /api/events/{event_id}/comments` - Get comments for event

---

## 10. Social Feed Logic Explanation

When a user calls `GET /api/feed`:
1. **Neo4j** executes Cypher to find events interacted with by users followed by the current user:
   ```cypher
   MATCH (me:User {user_id: $user_id})-[:FOLLOWS]->(friend:User)-[r:LIKED|REGISTERED|SHARED|VIEWED]->(e:Event)
   RETURN e.event_id AS event_id, friend.user_id AS friend_id, friend.name AS friend_name, type(r) AS interaction_type
   ```
2. The engine scores and ranks the events (REGISTERED > SHARED > LIKED > VIEWED).
3. **MongoDB** batch queries complete event details for the top event IDs using `$in`:
   ```python
   events.find({"event_id": {"$in": event_ids}, "status": "approved"})
   ```
4. The service combines the event documents with social context (e.g. *"Priya registered for this event"*).
5. If the user follows few people or activity is sparse, upcoming approved events fill the remaining slots as a fallback.

---

## 11. Useful Database Queries for Demonstration

### Neo4j Cypher Queries

**Find followers of a user:**
```cypher
MATCH (follower:User)-[:FOLLOWS]->(u:User {user_id: "USR_12345678"})
RETURN follower.name, follower.user_id;
```

**Find social feed activity for a user:**
```cypher
MATCH (me:User {user_id: "USR_12345678"})-[:FOLLOWS]->(friend:User)-[r:REGISTERED|LIKED]->(e:Event)
RETURN friend.name, type(r) AS action, e.event_id;
```

### MongoDB Aggregation Queries

**Events breakdown by category:**
```javascript
db.events.aggregate([
  { $match: { status: "approved" } },
  { $group: { _id: "$category", count: { $sum: 1 } } },
  { $sort: { count: -1 } }
]);
```
