from celery import Celery
from app.config import settings

celery_app = Celery(
    "weather_app",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.weather_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        # Top-10 popular cities: always fresh, refresh every 10 minutes.
        "refresh-popular-cities": {
            "task": "app.tasks.weather_tasks.refresh_popular_cities",
            "schedule": 600.0,
        },
        # Sliding window: proactively refresh records that are 30-60 min old.
        # Reduces on-demand OWM calls for recently-searched cities.
        "refresh-sliding-window": {
            "task": "app.tasks.weather_tasks.refresh_sliding_window",
            "schedule": 600.0,
        },
    },
)
