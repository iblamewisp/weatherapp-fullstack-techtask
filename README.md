# Weather App

## Architecture Overview

A fullstack weather application with a Next.js 14 frontend (App Router, Zustand, Zod, react-hook-form)
acting as a BFF, proxying requests to a FastAPI backend that fetches live weather data from OpenWeatherMap,
stores it in PostgreSQL via SQLAlchemy async, and refreshes data on a configurable schedule using APScheduler.

The core data flow for a weather lookup:

```
Browser → Next.js BFF (/api/weather) → FastAPI (/api/v1/weather/fetch) → OpenWeatherMap API
                                                        │
                                                        └─► PostgreSQL (upsert)
                                                              ▲
                                              APScheduler ────┘ (background refresh every N minutes)
```

`POST /fetch` is intentionally a POST, not a GET — it performs a write (upsert) on every call.
The semantics are get-or-create: fetch fresh data from OWM and insert/update in the DB atomically.
The DB acts as a cache and history store, not the source of truth.

---

## Prerequisites

- Docker & Docker Compose
- Node.js 24 (for local frontend development only — not required if using Docker)
- Python 3.12 (for local backend development only — not required if using Docker)
- OpenWeatherMap API key (free tier: https://openweathermap.org/api)

> New OWM free-tier keys can take 10–30 minutes to activate after creation.

---

## Quick Start

```bash
cp .env.example backend/.env
# Edit backend/.env and set OPENWEATHER_API_KEY=<your_key>
docker compose up --build
```

---

## Run Tests

```bash
# Backend
docker compose exec backend pytest

# Frontend (requires Node.js 24 installed locally)
cd frontend && npm test
```

---

## API Endpoints

| Method | Path | Rate limit | Description |
|--------|------|------------|-------------|
| GET | /api/v1/weather | 20/min | List all cached weather records |
| GET | /api/v1/weather/{id} | 20/min | Get record by UUID |
| POST | /api/v1/weather | 5/min | Create bare record (no OWM fetch) |
| PUT | /api/v1/weather/{id} | 5/min | Update record fields |
| DELETE | /api/v1/weather/{id} | 5/min | Delete record, returns 204 |
| POST | /api/v1/weather/fetch | 5/min | Fetch from OWM + upsert to DB |
| GET | /health | — | Health check (tests DB connection) |

Rate limits are per IP. Exceeded limits return `429 Too Many Requests`.

---

## Post-spec Changes & Design Decisions

The initial spec was a boilerplate scaffold. The following decisions were made during implementation
and are documented here with the reasoning behind each.

### Node.js 20 → 24

The spec stated Node 20. Changed to Node 24 (Active LTS) because:
- Node 20 reaches EOL April 2026
- Node 25 is an odd-numbered "Current" release — not LTS, short-lived, not suitable for production
- Even-numbered versions are LTS in Node.js; 24 is the current Active LTS

### Rate limiting (slowapi)

Not in the original spec. Added with differentiated limits:
- **GET endpoints: 20/min** — read-only, cheap queries, reasonable headroom
- **POST/PUT/DELETE: 5/min** — write operations, hit external API or modify DB state

The asymmetry is intentional. `POST /fetch` in particular calls OWM on every request.
OWM free tier allows 60 calls/minute — 5/min per IP gives headroom for multiple users
without risking quota exhaustion.

### OWM error handling

The original spec had a single catch-all `502` for all non-200 OWM responses.
Expanded to distinguish:

| OWM status | Returned to client | Reason |
|---|---|---|
| 401 | 503 | Invalid/expired API key — operator error, not client error |
| 403 | 503 | Resource requires paid plan |
| 404 | 404 | City not found — pass through |
| 429 | 429 | OWM rate limit hit — pass through so caller knows to back off |
| 500/502/503 | 502 | OWM is down |
| Timeout | 504 | OWM did not respond within 10s |

401/403 return 503 (not 401/403) because these are operator-side configuration errors,
not client authentication errors. The client did nothing wrong.

### Invalid JSON from OWM

`resp.json()` raises `aiohttp.ContentTypeError` or `json.JSONDecodeError` if OWM returns
malformed content (happens during their DDoS protection or maintenance windows, when they
serve HTML error pages instead of JSON). Without handling this, the error surfaces as
an unhandled 500. Fixed with a dedicated `_parse_json` method that:
- Uses `content_type=None` to not fail on wrong Content-Type headers
- Logs the first 200 chars of the raw response for debugging
- Returns a clean `502` to the client

### Docker healthcheck + depends_on condition

Original compose had `depends_on: [db]` which only waits for the container to start,
not for Postgres to be ready to accept connections. On slow machines or first boot,
the backend would start before Postgres finished initializing and crash.

Fixed:
- Added `healthcheck` on db using `pg_isready`
- Changed backend `depends_on` to `condition: service_healthy`

This guarantees the backend only starts after Postgres is accepting connections.

### /health endpoint

Original `/health` returned a static `{"status": "ok"}` — useless for real health monitoring
since it doesn't reflect whether the service can actually serve requests.

Updated to run `SELECT 1` against the DB on every call, wrapped in a 3-second timeout:
- `200 {"status": "ok", "db": "ok"}` — service is fully operational
- `503 "Service unavailable: database unreachable"` — DB unreachable or timed out

This makes `/health` meaningful for load balancers, uptime monitors, and k8s readiness probes.

### Security hardening

Several hardening measures applied after initial implementation:

- **Token comparison**: `x-internal-token` validation uses `secrets.compare_digest()` instead
  of `==` to prevent timing attacks. String equality short-circuits on the first mismatched
  byte, leaking information about token length and content through response time differences.

- **Required secrets**: `OPENWEATHER_API_KEY` and `INTERNAL_API_TOKEN` have no default values.
  Pydantic `Field(...)` causes the app to crash at startup if either is missing from the
  environment. Previously both had placeholder defaults (`"your_key_here"`, `"change_me_in_prod"`)
  meaning a missing `.env` file would silently start the app in an insecure state.

### Rate limiter

The original implementation created a `Limiter` instance in both `main.py` and `routers/weather.py`.
Two independent instances meant rate limit counters were never shared — limits were silently broken.

Fixed by extracting the single shared instance to `app/limiter.py`, imported by both modules.

---

## Intentionally Omitted from the Spec

These are production concerns that were left out of the boilerplate spec deliberately.
They would be added before a real production deployment:

- **Authentication/Authorization** — no JWT, no API keys on the backend. The `x-internal-token`
  header in the BFF is a placeholder, not real auth.
- **Circuit breaker for OWM** — if OWM is down, every request still tries to hit it and fails.
  A circuit breaker (e.g. with `aiobreaker`) would fail fast after N consecutive failures.
- **Retry with exponential backoff** — transient OWM errors (502/503/timeout) are not retried.
  A single failure returns an error to the client immediately.
- **DB connection health in lifespan** — startup does not verify DB connectivity. If the DB is
  misconfigured, the backend starts successfully and only fails on the first real request.
- **Structured logging / tracing** — logs are plaintext. No request IDs, no correlation between
  frontend → BFF → backend → OWM calls. Makes debugging distributed issues harder.
- **Frontend error boundaries** — ~~the React app has no error boundary components~~ Added: `ErrorBoundary`
  class component wraps all pages in the root layout. Unhandled render errors show a recoverable
  fallback with a "Try again" reset instead of a blank screen.
- **Pagination on GET /weather** — returns all records. Will degrade with large datasets.

---

## Project Structure

```
weather-app/
├── backend/
│   ├── app/
│   │   ├── main.py           # App entry, lifespan, middleware, health check
│   │   ├── config.py         # Pydantic settings (reads from .env, required fields fail fast)
│   │   ├── limiter.py        # Shared slowapi Limiter instance (imported by main + router)
│   │   ├── database.py       # Async SQLAlchemy engine, session factory, get_db DI
│   │   ├── logger.py         # Logging setup
│   │   ├── models/           # SQLAlchemy ORM models (Weather with unique constraint)
│   │   ├── schemas/          # Pydantic v2 schemas (WeatherCreate, WeatherResponse, etc.)
│   │   ├── repositories/     # Abstract base + SQLAlchemy async repository (upsert via ON CONFLICT)
│   │   ├── services/         # OWM fetcher (aiohttp, error handling, JSON validation)
│   │   ├── routers/          # FastAPI route handlers with per-endpoint rate limits
│   │   └── tasks/            # APScheduler background refresh job
│   ├── migrations/           # Alembic async migrations
│   ├── tests/                # pytest-asyncio test suite
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── page.tsx              # Search form page
│       │   ├── result/page.tsx       # Weather result page (temperature-based bg color)
│       │   └── api/weather/route.ts  # BFF route handler (proxies to FastAPI)
│       ├── components/
│       │   ├── WeatherForm.tsx       # react-hook-form + Zod, city/coords toggle
│       │   ├── WeatherResult.tsx     # Result display with temperature color coding
│       │   ├── Notification.tsx      # react-hot-toast wrapper
│       │   └── ErrorBoundary.tsx     # Class-based error boundary, wraps all pages
│       ├── store/weatherStore.ts     # Zustand + sessionStorage persist
│       ├── lib/
│       │   ├── api/weatherClient.ts  # All fetch calls (never from components directly)
│       │   └── validations/          # Zod discriminated union schema
│       └── types/weather.ts          # TypeScript interfaces matching backend response
├── docker-compose.yml                # db (healthcheck) + backend + frontend
├── .env.example
└── README.md
```
