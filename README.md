# Weather App

## Architecture Overview

A fullstack weather application with a Next.js 14 frontend (App Router, Zustand, Zod, react-hook-form)
acting as a BFF, proxying requests to a FastAPI backend that stores weather data in PostgreSQL via
SQLAlchemy async. Background refresh is handled by Celery Beat workers backed by Redis.

### Core data flow

```
                                              ┌─ record fresh (<30 min) ──► return from DB
Browser → Next.js BFF → FastAPI POST /fetch ──┤
                                              └─ record stale / missing
                                                    │
                                                    ├─ OWM reachable ──► OpenWeatherMap API
                                                    │                          │
                                                    │                    PostgreSQL (upsert)
                                                    │                          │
                                                    └─ OWM unreachable ──► PostgreSQL (read)
                                                                         [X-Cache-Fallback: true]

Celery Beat (every 10 min) ──┬── refresh_popular_cities ──► OWM for top-10 ──► PostgreSQL (upsert)
                             └── refresh_sliding_window ──► OWM for records 30–60 min old ──► PostgreSQL (upsert)
```

**Fresh cache hit**: record exists and `last_updated < 30 min` → returned from DB, no OWM call.

**Stale/missing**: record is older than 30 min or doesn't exist → OWM API called, result upserted and returned.

**OWM error fallback**: OWM is unreachable → last known DB record returned with `X-Cache-Fallback: true`.
Client receives `200` with stale data instead of an error, as long as any prior record exists.

**Sliding window**: Celery Beat proactively refreshes records in the 30–60 min staleness window every
10 minutes. This pre-warms the cache for recently-searched cities so the next search is likely a
fresh cache hit rather than an on-demand OWM call.

**Popular cities**: a hardcoded list of 10 cities is always kept fresh by a dedicated Celery Beat
task (every 10 min). The frontend home page fetches these directly from DB via `GET /popular`.

### Frontend data flow

```
Home page load ──► GET /api/weather/popular ──► DB read ──► render top-10 grid

User searches city ──► POST /api/weather/fetch ──► backend (fresh check → OWM if needed)
                                                         │
                                              stored in Zustand (sessionStorage)
                                              displayed above top-10 as "Recent searches"

User edits card ──► PUT /api/weather/{id} ──► DB update
                                                  │
                                      local state updated (popular array + Zustand)
```

User-searched cities live in Zustand sessionStorage — visible only to that user, only while the
tab is open. They are deduplicated by city+country and capped at 5 recent entries.

---

## Prerequisites

- Docker & Docker Compose
- Node.js 24 (for local frontend development only)
- Python 3.12 (for local backend development only)
- OpenWeatherMap API key (free tier: https://openweathermap.org/api)

> New OWM free-tier keys can take 10–30 minutes to activate after creation.

---

## Quick Start

```bash
cp .env.example backend/.env
# Edit backend/.env: set OPENWEATHER_API_KEY and INTERNAL_API_TOKEN
docker compose up --build
```

On first start, the backend seeds all 10 popular cities from OWM before accepting requests.

---

## Run Tests

Backend tests run against a real PostgreSQL instance (`weather_test` database).
The test fixture creates this database automatically on first run.

```bash
# Start the database (if not already running)
docker compose up -d db

# Backend — repository, route, and service tests
docker compose exec backend pytest

# Frontend — BFF route and API client tests (Docker)
docker build --target test -t frontend-test ./frontend && docker run --rm frontend-test

# Frontend — local
cd frontend && npm test
```

---

## API Endpoints

| Method | Path | Rate limit | Description |
|--------|------|------------|-------------|
| GET | /api/v1/weather | 20/min | List all cached weather records |
| GET | /api/v1/weather/popular | 60/min | Top-10 popular cities (DB read only) |
| GET | /api/v1/weather/{id} | 20/min | Get record by UUID |
| POST | /api/v1/weather | 5/min | Create bare record (no OWM fetch) |
| PUT | /api/v1/weather/{id} | 5/min | Update record fields manually |
| DELETE | /api/v1/weather/{id} | 5/min | Delete record, returns 204 |
| POST | /api/v1/weather/fetch | 5/min | Fetch weather (cache-first, OWM on miss) |
| GET | /health | — | Health check (tests DB connection) |

Rate limits are per IP. Exceeded limits return `429 Too Many Requests`.

All endpoints (except `/health`) require the `x-internal-token` header matching `INTERNAL_API_TOKEN` from `.env`.

Interactive docs: `http://localhost:8000/docs` — click **Authorize** and enter the token once.

---

## Design Decisions & Trade-offs

### Cache-first search with 30-minute TTL

**Problem**: every user search hit the OWM API directly. This burned quota on duplicate searches,
returned no result when OWM was down, and overwrote manual user edits immediately.

**Solution**: `POST /fetch` first checks the DB. If the record exists and `last_updated < 30 min`,
it's returned without calling OWM. Only stale or missing records trigger an OWM call.

**Trade-off**: a user searching a city may get data up to 30 minutes old. Acceptable for weather,
where significant changes within 30 minutes are uncommon and the sliding window keeps active cities fresh.

### Sliding window background refresh

**Problem**: proactively refreshing every record in the DB (original APScheduler approach) was
wasteful — most records are cold and won't be searched again soon.

**Solution**: Celery Beat runs `refresh_sliding_window` every 10 minutes. It queries records where
`30 min ≤ last_updated ≤ 60 min` — recently active but about to go stale. These are refreshed
proactively so the next search hits the cache. Records older than 60 minutes are skipped; if someone
searches them, they trigger an on-demand OWM call.

**Trade-off**: a city searched once and then not searched for over an hour will be refreshed
on-demand, adding ~200–800ms latency to that request. This is the right trade-off: OWM quota is
finite, and pre-refreshing cold data wastes it.

### Manual edits vs. background refresh conflict

**Known limitation**: when a user manually edits a weather record, `last_updated` is set to now.
For the next 30 minutes, searches return the edited data from DB. After 30 minutes, the sliding
window or an on-demand search will overwrite the edit with fresh OWM data.

A proper fix would require an `is_manually_edited` flag (or separate `edited_at` column) so the
refresh logic can skip manually-edited records. This is left as a known trade-off pending a decision
on edit history semantics.

### APScheduler → Celery + Redis

APScheduler ran inside the FastAPI process. This works for a single instance but breaks under
horizontal scaling — every instance runs its own scheduler, leading to duplicate OWM calls and
race conditions on upserts.

Celery Beat is a separate process with a single scheduler. Workers are independently scalable.
Redis acts as the message broker and result backend. The cost is two extra containers (`celery-worker`,
`celery-beat`) and a Redis instance — justified even at this scale because it correctly models
the architecture.

### Node.js 20 → 24

Node 20 reaches EOL April 2026. Node 24 is the current Active LTS.
(Node 25 is an odd-numbered "Current" release — not LTS, not suitable for production.)

### Rate limiting — shared Limiter instance

The original scaffold created a `Limiter` in both `main.py` and `routers/weather.py`. Two
independent instances meant counters were never shared — limits were silently broken. Fixed by
extracting a single shared instance to `app/limiter.py`.

### Differentiated rate limits

- **GET /popular: 60/min** — pure DB read, no external calls, cheap
- **GET endpoints: 20/min** — DB reads, reasonable headroom
- **POST/PUT/DELETE: 5/min** — write operations; `POST /fetch` calls OWM

OWM free tier allows 60 calls/minute across all IPs. 5/min per IP gives headroom for concurrent users.

### Security hardening

- **Timing-safe token comparison**: `secrets.compare_digest()` instead of `==`. String equality
  short-circuits on the first mismatched byte, leaking token information through response time.
- **Required secrets at startup**: `Field(...)` in pydantic settings causes the app to crash
  immediately if `OPENWEATHER_API_KEY` or `INTERNAL_API_TOKEN` are missing. Eliminates the
  "silently running with placeholder credentials" failure mode.
- **UUID validation in BFF**: the `[id]` route validates UUID format before forwarding to the backend.
- **Zod bounds on edit form**: temperature (−100..60°C), humidity (0..100%), pressure (870..1084 hPa).
  City/country/coordinates excluded from the edit schema — no reason for a user to change them.

### /health endpoint

Original returned `{"status": "ok"}` statically — meaningless for real health monitoring.
Updated to run `SELECT 1` with a 3-second timeout:
- `200 {"status": "ok", "db": "ok"}` — fully operational
- `503` — DB unreachable

Useful for load balancers, uptime monitors, and k8s readiness probes.

---

## Intentionally Omitted

Production concerns explicitly left out of scope:

- **Authentication/Authorization** — `x-internal-token` is a shared secret between BFF and backend, not per-user auth. No JWT, no sessions.
- **Circuit breaker for OWM** — after N consecutive OWM failures, a circuit breaker would stop calling OWM entirely and serve cached data. Currently every stale request still attempts OWM.
- **Retry with exponential backoff** — transient OWM errors (502/503/timeout) return immediately to the client without retry.
- **Edit history / conflict resolution** — manual edits are overwritten by background refresh after 30 min. Requires `is_manually_edited` flag or a separate edits table.
- **Pagination on GET /weather** — returns all records unbounded.
- **Structured logging / tracing** — no request IDs, no correlation across BFF → backend → OWM hops.

---

## Project Structure

```
weather-app/
├── backend/
│   ├── app/
│   │   ├── main.py           # App entry, lifespan (seed), middleware, health check
│   │   ├── config.py         # Pydantic settings (required fields, extra=ignore)
│   │   ├── constants.py      # POPULAR_CITIES list, cache TTL, window bounds
│   │   ├── limiter.py        # Shared slowapi Limiter instance
│   │   ├── database.py       # Async SQLAlchemy engine, session factory, get_db DI
│   │   ├── logger.py         # Logging setup
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic v2 schemas
│   │   ├── repositories/     # Abstract base + SQLAlchemy async impl (upsert, sliding window)
│   │   ├── services/         # WeatherFetcherService (freshness check, OWM, cache fallback)
│   │   ├── routers/          # FastAPI route handlers with per-endpoint rate limits
│   │   └── tasks/
│   │       ├── celery_app.py      # Celery app + beat schedule
│   │       └── weather_tasks.py   # refresh_popular_cities + refresh_sliding_window
│   ├── migrations/           # Alembic async migrations
│   ├── tests/                # pytest-asyncio: repository, routes, service unit tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── page.tsx                      # Home: popular grid + recent searches + search form
│       │   ├── result/page.tsx               # Full weather result page
│       │   └── api/weather/
│       │       ├── route.ts                  # BFF: POST /fetch, GET all
│       │       ├── popular/route.ts          # BFF: GET popular cities
│       │       └── [id]/route.ts             # BFF: PUT update, DELETE
│       ├── components/
│       │   ├── WeatherForm.tsx       # react-hook-form + Zod, city/coords toggle
│       │   ├── WeatherResult.tsx     # Full result with temperature color coding
│       │   ├── CityCard.tsx          # Compact card for grids, optional edit button
│       │   ├── EditWeatherModal.tsx  # Modal form for manual weather edits
│       │   ├── Notification.tsx      # react-hot-toast wrapper
│       │   └── ErrorBoundary.tsx     # Class-based error boundary
│       ├── store/weatherStore.ts     # Zustand + sessionStorage (recent searches, current result)
│       ├── lib/
│       │   ├── api/weatherClient.ts  # All fetch calls (never from components directly)
│       │   └── validations/          # Zod schemas (search + edit forms)
│       └── types/weather.ts          # TypeScript interfaces matching backend response
├── docker-compose.yml         # db + redis + backend + celery-worker + celery-beat + frontend
├── .env.example
└── README.md
```
