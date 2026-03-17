import asyncio
import json
import logging
import aiohttp
from fastapi import HTTPException
from app.config import Settings
from app.repositories.weather import SQLAlchemyWeatherRepository
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("weather_app.fetcher")

# Mapping of OWM HTTP status codes to (client-facing status, message).
# 401/403 are returned as 503 — these are operator configuration errors, not client errors.
# 429 is passed through so the caller knows to back off.
OWM_ERRORS = {
    401: (503, "Invalid or expired OpenWeatherMap API key"),
    403: (503, "OpenWeatherMap API key does not have access to this resource"),
    429: (429, "OpenWeatherMap rate limit exceeded"),
    500: (502, "OpenWeatherMap internal server error"),
    502: (502, "OpenWeatherMap is temporarily unavailable"),
    503: (502, "OpenWeatherMap is temporarily unavailable"),
}


# Stateless service — receives http_client and settings via constructor.
# http_client is a singleton aiohttp.ClientSession stored on app.state, initialized in lifespan.
class WeatherFetcherService:
    def __init__(self, http_client: aiohttp.ClientSession, settings: Settings):
        self.http_client = http_client
        self.settings = settings

    # Raises HTTPException with the appropriate status code based on OWM response status.
    # Called before reading the response body to fail fast on error responses.
    def _raise_for_owm_status(self, status: int, context: str) -> None:
        if status == 404:
            raise HTTPException(status_code=404, detail=context)
        if status in OWM_ERRORS:
            code, detail = OWM_ERRORS[status]
            logger.error(f"OWM returned {status}: {detail}")
            raise HTTPException(status_code=code, detail=detail)
        if status != 200:
            logger.error(f"OWM unexpected status {status}")
            raise HTTPException(status_code=502, detail=f"Unexpected response from OpenWeatherMap (status {status})")

    # content_type=None skips aiohttp's Content-Type check — OWM occasionally returns
    # text/html (e.g. during DDoS protection) instead of application/json.
    # Logs first 200 chars of raw body to aid debugging when JSON parsing fails.
    async def _parse_json(self, resp: aiohttp.ClientResponse) -> dict:
        try:
            return await resp.json(content_type=None)
        except (json.JSONDecodeError, aiohttp.ContentTypeError) as e:
            raw = await resp.text()
            logger.error(f"OWM returned invalid JSON: {raw[:200]}")
            raise HTTPException(status_code=502, detail="OpenWeatherMap returned an invalid response")

    # Fetches weather by city + country code from OWM /weather endpoint.
    # units=metric ensures temperature is returned in Celsius.
    # Timeout of 10s — OWM free tier can be slow under load.
    async def fetch_by_city(self, city: str, country: str) -> dict:
        url = f"{self.settings.OPENWEATHER_BASE_URL}/weather"
        params = {
            "q": f"{city},{country}",
            "appid": self.settings.OPENWEATHER_API_KEY,
            "units": "metric",
        }
        logger.info(f"Fetching weather for city={city}, country={country}")
        try:
            async with self.http_client.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                self._raise_for_owm_status(resp.status, f"City '{city},{country}' not found")
                return await self._parse_json(resp)
        except HTTPException:
            raise  # Re-raise without wrapping — already a proper HTTP error
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching weather for {city},{country}")
            raise HTTPException(status_code=504, detail="OpenWeatherMap request timed out")
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching weather: {e}")
            raise HTTPException(status_code=502, detail="Network error fetching weather data")

    # Fetches weather by coordinates — used when frontend sends lat/lon instead of city name.
    async def fetch_by_coords(self, lat: float, lon: float) -> dict:
        url = f"{self.settings.OPENWEATHER_BASE_URL}/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.settings.OPENWEATHER_API_KEY,
            "units": "metric",
        }
        logger.info(f"Fetching weather for lat={lat}, lon={lon}")
        try:
            async with self.http_client.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                self._raise_for_owm_status(resp.status, "No weather data for these coordinates")
                return await self._parse_json(resp)
        except HTTPException:
            raise
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching weather for lat={lat}, lon={lon}")
            raise HTTPException(status_code=504, detail="OpenWeatherMap request timed out")
        except aiohttp.ClientError as e:
            logger.error(f"Network error fetching weather: {e}")
            raise HTTPException(status_code=502, detail="Network error fetching weather data")

    # Maps raw OWM JSON response to a flat dict matching the Weather model fields.
    # OWM response structure: https://openweathermap.org/current#fields_json
    def _parse_owm_response(self, data: dict) -> dict:
        return {
            "city": data["name"],
            "country": data["sys"]["country"],
            "latitude": data["coord"]["lat"],
            "longitude": data["coord"]["lon"],
            "temperature": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "wind_speed": data["wind"]["speed"],
            "weather_description": data["weather"][0]["description"],
            "weather_icon": data["weather"][0]["icon"],
        }

    # Convenience method: fetch from OWM by city + upsert into DB in one call.
    # Used by POST /fetch and the background scheduler.
    async def fetch_and_upsert(self, city: str, country: str, db_session: AsyncSession) -> dict:
        raw = await self.fetch_by_city(city, country)
        parsed = self._parse_owm_response(raw)
        repo = SQLAlchemyWeatherRepository(db_session)
        weather = await repo.upsert(parsed)
        return weather
