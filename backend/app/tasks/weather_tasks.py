import asyncio
import logging
from datetime import datetime, timezone, timedelta
import aiohttp
from app.tasks.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.repositories.weather import SQLAlchemyWeatherRepository
from app.services.weather_fetcher import WeatherFetcherService
from app.config import settings

logger = logging.getLogger("weather_app.tasks")


@celery_app.task(name="app.tasks.weather_tasks.refresh_popular_cities")
def refresh_popular_cities():
    """Synchronous Celery task entry point — delegates to async implementation."""
    asyncio.run(_do_refresh())


async def _do_refresh():
    logger.info("Celery task: refreshing popular cities")
    async with aiohttp.ClientSession() as http_client:
        async with AsyncSessionLocal() as session:
            fetcher = WeatherFetcherService(http_client, settings)
            for city, country in settings.POPULAR_CITIES:
                try:
                    # Bypass freshness check — always fetch live data for popular cities.
                    raw = await fetcher.fetch_by_city(city, country)
                    parsed = fetcher._parse_owm_response(raw)
                    repo = SQLAlchemyWeatherRepository(session)
                    await repo.upsert(parsed)
                    logger.info(f"Refreshed {city}, {country}")
                except Exception as e:
                    logger.error(f"Failed to refresh {city}, {country}: {e}")
            await session.commit()
    logger.info("Celery task: popular cities refresh complete")


@celery_app.task(name="app.tasks.weather_tasks.refresh_sliding_window")
def refresh_sliding_window():
    """Proactively refreshes records in the stale-but-recent window to pre-warm the cache."""
    asyncio.run(_do_sliding_window())


async def _do_sliding_window():
    now = datetime.now(timezone.utc)
    older_than = now - timedelta(minutes=settings.STALE_MAX_MINUTES)
    newer_than = now - timedelta(minutes=settings.STALE_MIN_MINUTES)
    logger.info(f"Sliding window: refreshing records between {settings.STALE_MIN_MINUTES} and {settings.STALE_MAX_MINUTES} min old")
    async with aiohttp.ClientSession() as http_client:
        async with AsyncSessionLocal() as session:
            repo = SQLAlchemyWeatherRepository(session)
            records = await repo.get_stale_in_window(older_than, newer_than)
            logger.info(f"Sliding window: {len(records)} records to refresh")
            fetcher = WeatherFetcherService(http_client, settings)
            for record in records:
                try:
                    raw = await fetcher.fetch_by_city(record.city, record.country)
                    parsed = fetcher._parse_owm_response(raw)
                    await repo.upsert(parsed)
                    logger.info(f"Window refreshed {record.city}, {record.country}")
                except Exception as e:
                    logger.error(f"Window failed for {record.city}, {record.country}: {e}")
            await session.commit()
    logger.info("Sliding window refresh complete")
