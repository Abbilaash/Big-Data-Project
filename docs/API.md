# API Reference

Interactive docs: `http://localhost:8000/docs` (Swagger) and `/redoc`.
The endpoint table below was generated from the app's OpenAPI schema.

## Conventions

**Auth:** `Authorization: Bearer <jwt>`.

| Tag | Meaning |
|---|---|
| — | public |
| **O** | optional: personalises the response if a valid token is sent |
| **S** | signed in; profile may be incomplete |
| **U** | signed in with a completed profile |
| **A** | admin (`role == ADMIN`) |

**Success envelope**
```json
{ "success": true, "message": "Approved events retrieved", "data": <payload> }
```

**Errors** — FastAPI shape `{ "detail": <string | list> }`:

| Status | When |
|---|---|
| 401 | Missing/invalid/expired token, or user no longer exists |
| 403 | Profile incomplete; not an admin |
| 404 | Missing resource. Also: someone else's unapproved event (existence not disclosed) |
| 409 | Invalid state transition (moderating a non-pending event) |
| 422 | Validation failure; `detail` is a list of `{loc, msg}` |
| 503 | Graph database unavailable for an operation that must write to it |
| 500 | Generic message only; details are logged server-side |

## Endpoints

### Health
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | — | Live probe of both databases: `{status: ok\|degraded, mongodb, neo4j}` |

### Auth — `/api/auth`
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/config` | — | `{dev_login_enabled}` for the login screen |
| GET | `/google/login?redirect=true` | — | Redirect to Google (or JSON `authorization_url` with `redirect=false`). Includes a signed `state` |
| GET | `/google/callback?code&state` | — | Verifies `state`, signs the user in, redirects to `FRONTEND_URL/auth/callback#token=…&profile_completed=…`. Failures redirect to `FRONTEND_URL/login#error=…` |
| POST | `/dev-login` | — | `{email, name}` → token. **404 unless `ENABLE_DEV_LOGIN=true` and not production** |
| GET | `/session` | S | Identity + `profile_completed`, usable before onboarding |
| POST | `/complete-profile` | S | `{name, year 1-6, department, profile_picture?}` → new token |

### Users — `/api/users`
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/me` | U | Own profile (includes email, role) |
| PATCH | `/me` | U | Partial update of `name`, `year`, `department`, `profile_picture`; 400 if empty |
| GET | `` | U | Directory: `q`, `department`, `year`, `page`, `limit≤50`. Excludes self and incomplete profiles; sorted by name; includes `is_following` |
| GET | `/departments` | U | Distinct departments in use |
| GET | `/suggestions?limit` | U | Friends-of-friends by mutual count (graph), padded with same-department students |
| GET | `/search?q` | U | Name/department search (email is not searchable) |
| GET | `/{user_id}` | U | Public profile + follower/following counts |
| GET | `/{user_id}/followers` · `/{user_id}/following` | U | Lists with `is_following` relative to the caller |

### Events — `/api/events`
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `` | U | Submit an event → `status: pending` (201) |
| GET | `` | O | Approved events. `category`, `search` (title/description/tags), `date`, `upcoming_only`, `page`, `limit≤100` |
| GET | `/categories` | — | Canonical category list |
| GET | `/upcoming?limit` | O | Approved events dated today or later, soonest first |
| GET | `/my-hosted` | U | Everything I submitted, any status, with `rejection_reason` |
| GET | `/registered` | U | Approved events I registered for |
| GET | `/{event_id}` | U | Detail with `view_count`, `share_count`; 404 for others' unapproved events |
| POST/DELETE | `/{event_id}/like` | U | Like / unlike (idempotent) |
| POST/DELETE | `/{event_id}/register` | U | Register / unregister (idempotent) |
| POST | `/{event_id}/view` | U | Record a view |
| POST | `/{event_id}/share` | U | Record a share |
| GET/POST | `/{event_id}/comments` | U | List (oldest first, ≤200) / add (1–1000 chars). Approved events only |
| DELETE | `/{event_id}/comments/{comment_id}` | U | Author or admin |

Interaction endpoints require the event to be **approved** (404 otherwise).

### Social — `/api/social`
| Method | Path | Auth | Description |
|---|---|---|---|
| POST/DELETE | `/follow/{user_id}` | U | Follow / unfollow. 400 for self, unknown, or incomplete target |
| GET | `/status/{user_id}` | U | `{target_user_id, is_following}` |
| GET | `/followers` · `/following` | U | My lists |
| GET | `/mutuals/{user_id}` | U | People both of us follow |
| GET | `/common-interests/{user_id}` | U | One row per shared event, e.g. `"You liked, they registered"` |

### Feed — `/api/feed`
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `?limit≤50` | U | Ranked upcoming events with `social_context: {reason, users[]}` or `null` for fill items |

### Admin — `/api/admin`
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/events?status=pending\|approved\|rejected` | A | Events by status (newest first, ≤100) |
| GET | `/events/pending` | A | Moderation queue |
| GET | `/events/{event_id}` | A | Inspect any event |
| POST | `/events/{event_id}/approve` | A | pending → approved; 409 if already moderated |
| POST | `/events/{event_id}/reject` | A | `{rejection_reason?≤500}`; pending → rejected; 409 otherwise |
| GET | `/analytics/events` | A | MongoDB aggregations: totals by status, approved by category, top hosts |
| GET | `/analytics/network` | A | Cypher: user/follow counts, most followed, most engaged events. **503 if the graph is down** (no silent zeros) |

## Key shapes

**Event** (list / create / admin)
```json
{
  "event_id": "EV_1A2B3C4D", "title": "AI Hackathon", "description": "…",
  "category": "Hackathon", "host_id": "USR_…", "host_name": "Asha Raman",
  "date": "2026-10-21", "start_time": "09:00", "end_time": "17:30",
  "venue": "Main Auditorium", "registration_url": null, "poster_url": null,
  "tags": ["ai", "python"], "status": "approved", "rejection_reason": null,
  "created_at": "2026-10-11T12:00:00+00:00",
  "like_count": 1, "registration_count": 1,
  "is_liked_by_me": true, "is_registered_by_me": true
}
```
Event **detail** adds `view_count` and `share_count`.

**Event create request validation:** title 3–200; description 10–5000;
`category` must be one of `Hackathon, Workshop, Bootcamp, Seminar, Contest,
Meetup, Cultural, Sports, Other` (case-insensitive, stored canonical); `date`
a real `YYYY-MM-DD`; times real `HH:MM`, `end_time > start_time`;
`registration_url`/`poster_url` http(s) only; ≤10 tags of ≤30 chars,
de-duplicated.

**Feed item** = Event + `social_context`:
```json
{ "reason": "Priya Raman registered for this event",
  "users": [{ "user_id": "USR_…", "name": "Priya Raman", "action": "REGISTERED" }] }
```

## Example
```bash
TOKEN=$(curl -s -X POST localhost:8000/api/auth/dev-login \
  -H 'Content-Type: application/json' \
  -d '{"email":"me@campus.local","name":"Me"}' | jq -r .data.access_token)

curl -s localhost:8000/api/feed -H "Authorization: Bearer $TOKEN"
```
