import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import AsyncSessionLocal
from app.repositories.weather import SQLAlchemyWeatherRepository

logger = logging.getLogger("weather_app.scheduler")

# Module-level scheduler instance — started and stopped inside lifespan() in main.py.
# Using AsyncIOScheduler to run async jobs on the existing event loop.
# APScheduler 3.x is pinned (<4.0) — version 4.x has a completely different API.
scheduler = AsyncIOScheduler()


# Background task: re-fetches fresh weather data from OWM for every city stored in the DB.
# Runs on a configurable interval (SCHEDULER_INTERVAL_MINUTES in settings).
# Uses its own AsyncSession — independent from request-scoped sessions.
# Per-city errors are caught and logged individually so one failed city doesn't abort the rest.
async def fetch_all_cities_task(http_client, settings):
    logger.info("Scheduler task started: refreshing all cities")
    async with AsyncSessionLocal() as session:
        repo = SQLAlchemyWeatherRepository(session)
        records = await repo.get_all()
        for record in records:
            try:
                # Import inside the loop to avoid circular imports at module load time.
                from app.services.weather_fetcher import WeatherFetcherService
                fetcher = WeatherFetcherService(http_client, settings)
                await fetcher.fetch_and_upsert(record.city, record.country, session)
                logger.info(f"Updated weather for {record.city},{record.country}")
            except Exception as e:
                logger.error(f"Failed to update {record.city},{record.country}: {e}")
        await session.commit()
    logger.info("Scheduler task complete")
