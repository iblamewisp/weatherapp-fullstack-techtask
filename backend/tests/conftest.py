import os

# Must be set before any app module is imported so pydantic Settings picks them up.
os.environ.setdefault("OPENWEATHER_API_KEY", "test-key")
os.environ.setdefault("INTERNAL_API_TOKEN", "test-token")

import pytest
from unittest.mock import AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app

TEST_TOKEN = os.environ["INTERNAL_API_TOKEN"]


@pytest.fixture
async def client():
    """AsyncClient with the internal auth token pre-set.
    Sets app.state.http_client so routes that call get_fetcher() don't fail —
    lifespan doesn't run in tests, so the aiohttp session is never created.
    Resets the rate limiter storage so tests don't bleed into each other
    (all requests share the same 127.0.0.1 address)."""
    app.state.http_client = AsyncMock()
    from app.limiter import limiter
    limiter._storage.reset()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"x-internal-token": TEST_TOKEN},
    ) as c:
        yield c
