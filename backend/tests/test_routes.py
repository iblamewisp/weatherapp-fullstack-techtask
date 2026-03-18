import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from fastapi import HTTPException
from app.main import app
from app.services.weather_fetcher import WeatherResult
from tests.conftest import TEST_TOKEN
from datetime import datetime, timezone


def make_weather_obj(**overrides):
    defaults = {
        "id": uuid.uuid4(),
        "city": "London",
        "country": "GB",
        "latitude": 51.5,
        "longitude": -0.12,
        "temperature": 15.0,
        "feels_like": 13.0,
        "humidity": 80,
        "pressure": 1013,
        "wind_speed": 5.0,
        "weather_description": "light rain",
        "weather_icon": "10d",
        "last_updated": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
    }
    obj = MagicMock()
    for k, v in {**defaults, **overrides}.items():
        setattr(obj, k, v)
    return obj


# ---------------------------------------------------------------------------
# Auth middleware
# ---------------------------------------------------------------------------

async def test_unauthorized_missing_token():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.get("/api/v1/weather")
    assert resp.status_code == 401


async def test_unauthorized_wrong_token():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.get("/api/v1/weather", headers={"x-internal-token": "wrong"})
    assert resp.status_code == 401


async def test_health_is_unprotected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.get("/health")
    # DB is not running in tests — we just confirm auth is not required
    assert resp.status_code != 401


# ---------------------------------------------------------------------------
# GET /weather
# ---------------------------------------------------------------------------

async def test_list_weather(client):
    weather = make_weather_obj()
    with patch("app.routers.weather.SQLAlchemyWeatherRepository") as MockRepo:
        MockRepo.return_value.get_all = AsyncMock(return_value=[weather])
        resp = await client.get("/api/v1/weather")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) == 1


async def test_get_weather_not_found(client):
    with patch("app.routers.weather.SQLAlchemyWeatherRepository") as MockRepo:
        MockRepo.return_value.get_by_id = AsyncMock(return_value=None)
        resp = await client.get(f"/api/v1/weather/{uuid.uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /weather/{id}
# ---------------------------------------------------------------------------

async def test_delete_weather_not_found(client):
    with patch("app.routers.weather.SQLAlchemyWeatherRepository") as MockRepo:
        MockRepo.return_value.delete = AsyncMock(return_value=False)
        resp = await client.delete(f"/api/v1/weather/{uuid.uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /weather/fetch — happy path
# ---------------------------------------------------------------------------

async def test_fetch_by_city_returns_200(client):
    weather = make_weather_obj()
    with patch("app.routers.weather.WeatherFetcherService.fetch_and_upsert", new_callable=AsyncMock) as mock:
        mock.return_value = WeatherResult(data=weather, from_cache=False)
        resp = await client.post("/api/v1/weather/fetch", json={"city": "London", "country": "GB"})
    assert resp.status_code == 200
    assert "X-Cache-Fallback" not in resp.headers


async def test_fetch_by_coords_returns_200(client):
    weather = make_weather_obj()
    with patch("app.routers.weather.WeatherFetcherService.fetch_and_upsert_by_coords", new_callable=AsyncMock) as mock:
        mock.return_value = WeatherResult(data=weather, from_cache=False)
        resp = await client.post("/api/v1/weather/fetch", json={"latitude": 51.5, "longitude": -0.12})
    assert resp.status_code == 200
    assert "X-Cache-Fallback" not in resp.headers


# ---------------------------------------------------------------------------
# POST /weather/fetch — cache-aside fallback
# ---------------------------------------------------------------------------

async def test_fetch_city_owm_fails_returns_cache(client):
    """OWM is down but cached data exists — 200 with X-Cache-Fallback header."""
    cached = make_weather_obj()
    with patch("app.routers.weather.WeatherFetcherService.fetch_and_upsert", new_callable=AsyncMock) as mock:
        mock.return_value = WeatherResult(data=cached, from_cache=True, owm_error=True)
        resp = await client.post("/api/v1/weather/fetch", json={"city": "London", "country": "GB"})
    assert resp.status_code == 200
    assert resp.headers.get("X-Cache-Fallback") == "true"


async def test_fetch_city_fresh_cache_no_fallback_header(client):
    """Fresh DB cache hit — 200 but NO X-Cache-Fallback header (OWM was not involved)."""
    cached = make_weather_obj()
    with patch("app.routers.weather.WeatherFetcherService.fetch_and_upsert", new_callable=AsyncMock) as mock:
        mock.return_value = WeatherResult(data=cached, from_cache=True, owm_error=False)
        resp = await client.post("/api/v1/weather/fetch", json={"city": "London", "country": "GB"})
    assert resp.status_code == 200
    assert "X-Cache-Fallback" not in resp.headers


async def test_fetch_coords_owm_fails_returns_cache(client):
    """Coords path: OWM down, nearest cached record returned."""
    cached = make_weather_obj()
    with patch("app.routers.weather.WeatherFetcherService.fetch_and_upsert_by_coords", new_callable=AsyncMock) as mock:
        mock.return_value = WeatherResult(data=cached, from_cache=True, owm_error=True)
        resp = await client.post("/api/v1/weather/fetch", json={"latitude": 51.5, "longitude": -0.12})
    assert resp.status_code == 200
    assert resp.headers.get("X-Cache-Fallback") == "true"


async def test_fetch_city_owm_fails_no_cache_raises(client):
    """OWM down and nothing in cache — original error must propagate."""
    with patch("app.routers.weather.WeatherFetcherService.fetch_and_upsert", new_callable=AsyncMock) as mock:
        mock.side_effect = HTTPException(status_code=502, detail="OWM unavailable")
        resp = await client.post("/api/v1/weather/fetch", json={"city": "London", "country": "GB"})
    assert resp.status_code == 502


# ---------------------------------------------------------------------------
# GET /weather/popular
# ---------------------------------------------------------------------------

async def test_get_popular_weather(client):
    cities = [make_weather_obj(city="London", country="GB"), make_weather_obj(city="Tokyo", country="JP")]
    with patch("app.routers.weather.SQLAlchemyWeatherRepository") as MockRepo:
        MockRepo.return_value.get_top_cities = AsyncMock(return_value=cities)
        resp = await client.get("/api/v1/weather/popular")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

async def test_fetch_invalid_coords_rejected(client):
    resp = await client.post("/api/v1/weather/fetch", json={"latitude": 200.0, "longitude": 0.0})
    assert resp.status_code == 422


async def test_fetch_empty_city_rejected(client):
    resp = await client.post("/api/v1/weather/fetch", json={"city": "", "country": "GB"})
    assert resp.status_code == 422
