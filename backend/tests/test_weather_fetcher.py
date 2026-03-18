import pytest
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from app.services.weather_fetcher import WeatherFetcherService, WeatherResult


OWM_RESPONSE = {
    "name": "London",
    "sys": {"country": "GB"},
    "coord": {"lat": 51.5074, "lon": -0.1278},
    "main": {"temp": 15.0, "feels_like": 13.0, "humidity": 80, "pressure": 1013},
    "wind": {"speed": 5.0},
    "weather": [{"description": "light rain", "icon": "10d"}],
}


@pytest.fixture
def fetcher():
    mock_settings = MagicMock()
    mock_settings.OPENWEATHER_API_KEY = "test-key"
    mock_settings.OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"
    mock_settings.CACHE_TTL_MINUTES = 30
    return WeatherFetcherService(http_client=MagicMock(), settings=mock_settings)


def make_weather_mock(fresh: bool = False):
    """fresh=True → last_updated 5 min ago. fresh=False → 60 min ago (stale)."""
    w = MagicMock()
    w.id = uuid.uuid4()
    w.city = "London"
    w.country = "GB"
    offset = timedelta(minutes=5) if fresh else timedelta(minutes=60)
    w.last_updated = datetime.now(timezone.utc) - offset
    return w


# ---------------------------------------------------------------------------
# fetch_and_upsert — city path
# ---------------------------------------------------------------------------

async def test_fetch_and_upsert_returns_live_data_when_no_cache(fetcher):
    """No cache in DB → OWM is called, result upserted and returned."""
    weather = make_weather_mock()
    with patch.object(fetcher, "fetch_by_city", new_callable=AsyncMock, return_value=OWM_RESPONSE), \
         patch("app.services.weather_fetcher.SQLAlchemyWeatherRepository") as MockRepo:
        MockRepo.return_value.get_by_city = AsyncMock(return_value=None)
        MockRepo.return_value.upsert = AsyncMock(return_value=weather)
        result = await fetcher.fetch_and_upsert("London", "GB", db_session=MagicMock())

    assert isinstance(result, WeatherResult)
    assert result.from_cache is False
    assert result.owm_error is False
    assert result.data is weather


async def test_fetch_and_upsert_returns_fresh_cache_without_calling_owm(fetcher):
    """Fresh record in DB (<30 min) → returned immediately, OWM never called."""
    cached = make_weather_mock(fresh=True)
    with patch.object(fetcher, "fetch_by_city", new_callable=AsyncMock) as mock_owm, \
         patch("app.services.weather_fetcher.SQLAlchemyWeatherRepository") as MockRepo:
        MockRepo.return_value.get_by_city = AsyncMock(return_value=cached)
        result = await fetcher.fetch_and_upsert("London", "GB", db_session=MagicMock())

    mock_owm.assert_not_called()
    assert result.from_cache is True
    assert result.owm_error is False
    assert result.data is cached


async def test_fetch_and_upsert_calls_owm_when_cache_is_stale(fetcher):
    """Stale record in DB (≥30 min) → OWM is called and result upserted."""
    stale = make_weather_mock(fresh=False)
    live = make_weather_mock()
    with patch.object(fetcher, "fetch_by_city", new_callable=AsyncMock, return_value=OWM_RESPONSE), \
         patch("app.services.weather_fetcher.SQLAlchemyWeatherRepository") as MockRepo:
        MockRepo.return_value.get_by_city = AsyncMock(return_value=stale)
        MockRepo.return_value.upsert = AsyncMock(return_value=live)
        result = await fetcher.fetch_and_upsert("London", "GB", db_session=MagicMock())

    assert result.from_cache is False
    assert result.owm_error is False


async def test_fetch_and_upsert_owm_fails_stale_cache_returned(fetcher):
    """OWM raises + stale cache exists → stale data returned with owm_error=True."""
    cached = make_weather_mock(fresh=False)
    with patch.object(fetcher, "fetch_by_city", new_callable=AsyncMock, side_effect=HTTPException(502, "down")), \
         patch("app.services.weather_fetcher.SQLAlchemyWeatherRepository") as MockRepo:
        MockRepo.return_value.get_by_city = AsyncMock(return_value=cached)
        result = await fetcher.fetch_and_upsert("London", "GB", db_session=MagicMock())

    assert result.from_cache is True
    assert result.owm_error is True
    assert result.data is cached


async def test_fetch_and_upsert_owm_fails_no_cache_raises(fetcher):
    """OWM raises and no cache exists → original HTTPException propagates."""
    with patch.object(fetcher, "fetch_by_city", new_callable=AsyncMock, side_effect=HTTPException(502, "down")), \
         patch("app.services.weather_fetcher.SQLAlchemyWeatherRepository") as MockRepo:
        MockRepo.return_value.get_by_city = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc_info:
            await fetcher.fetch_and_upsert("London", "GB", db_session=MagicMock())

    assert exc_info.value.status_code == 502


# ---------------------------------------------------------------------------
# fetch_and_upsert_by_coords — coords path
# ---------------------------------------------------------------------------

async def test_fetch_and_upsert_by_coords_returns_live_data(fetcher):
    weather = make_weather_mock()
    with patch.object(fetcher, "fetch_by_coords", new_callable=AsyncMock, return_value=OWM_RESPONSE), \
         patch("app.services.weather_fetcher.SQLAlchemyWeatherRepository") as MockRepo:
        MockRepo.return_value.get_by_coords = AsyncMock(return_value=None)
        MockRepo.return_value.upsert = AsyncMock(return_value=weather)
        result = await fetcher.fetch_and_upsert_by_coords(51.5, -0.12, db_session=MagicMock())

    assert result.from_cache is False
    assert result.owm_error is False
    assert result.data is weather


async def test_fetch_and_upsert_by_coords_returns_fresh_cache(fetcher):
    cached = make_weather_mock(fresh=True)
    with patch.object(fetcher, "fetch_by_coords", new_callable=AsyncMock) as mock_owm, \
         patch("app.services.weather_fetcher.SQLAlchemyWeatherRepository") as MockRepo:
        MockRepo.return_value.get_by_coords = AsyncMock(return_value=cached)
        result = await fetcher.fetch_and_upsert_by_coords(51.5, -0.12, db_session=MagicMock())

    mock_owm.assert_not_called()
    assert result.from_cache is True
    assert result.owm_error is False


async def test_fetch_and_upsert_by_coords_owm_fails_stale_cache_returned(fetcher):
    cached = make_weather_mock(fresh=False)
    with patch.object(fetcher, "fetch_by_coords", new_callable=AsyncMock, side_effect=HTTPException(504, "timeout")), \
         patch("app.services.weather_fetcher.SQLAlchemyWeatherRepository") as MockRepo:
        MockRepo.return_value.get_by_coords = AsyncMock(return_value=cached)
        result = await fetcher.fetch_and_upsert_by_coords(51.5, -0.12, db_session=MagicMock())

    assert result.from_cache is True
    assert result.owm_error is True
    assert result.data is cached


async def test_fetch_and_upsert_by_coords_owm_fails_no_cache_raises(fetcher):
    with patch.object(fetcher, "fetch_by_coords", new_callable=AsyncMock, side_effect=HTTPException(504, "timeout")), \
         patch("app.services.weather_fetcher.SQLAlchemyWeatherRepository") as MockRepo:
        MockRepo.return_value.get_by_coords = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc_info:
            await fetcher.fetch_and_upsert_by_coords(51.5, -0.12, db_session=MagicMock())

    assert exc_info.value.status_code == 504


# ---------------------------------------------------------------------------
# _parse_owm_response
# ---------------------------------------------------------------------------

def test_parse_owm_response_maps_fields(fetcher):
    parsed = fetcher._parse_owm_response(OWM_RESPONSE)
    assert parsed["city"] == "London"
    assert parsed["country"] == "GB"
    assert parsed["temperature"] == 15.0
    assert parsed["latitude"] == 51.5074
    assert parsed["weather_icon"] == "10d"
