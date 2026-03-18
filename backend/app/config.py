from typing import ClassVar, List, Tuple
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://weather:weather@db:5432/weather"
    OPENWEATHER_API_KEY: str = Field(..., min_length=1)
    OPENWEATHER_BASE_URL: str = "https://api.openweathermap.org/data/2.5"
    REDIS_URL: str = "redis://redis:6379/0"
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    INTERNAL_API_TOKEN: str = Field(..., min_length=1)
    LOG_LEVEL: str = "INFO"

    # Tunable via env — useful for adjusting cache behaviour without code changes.
    CACHE_TTL_MINUTES: int = 30
    STALE_MIN_MINUTES: int = 30
    STALE_MAX_MINUTES: int = 60

    # ClassVar: not a model field, never read from env, never validated.
    # Used as a fixed application constant accessible via settings.POPULAR_CITIES.
    POPULAR_CITIES: ClassVar[List[Tuple[str, str]]] = [
        ("London", "GB"),
        ("New York", "US"),
        ("Tokyo", "JP"),
        ("Paris", "FR"),
        ("Berlin", "DE"),
        ("Dubai", "AE"),
        ("Sydney", "AU"),
        ("Toronto", "CA"),
        ("Singapore", "SG"),
        ("Moscow", "RU"),
    ]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
