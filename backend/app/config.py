from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://weather:weather@db:5432/weather"
    OPENWEATHER_API_KEY: str = Field(..., min_length=1)
    OPENWEATHER_BASE_URL: str = "https://api.openweathermap.org/data/2.5"
    REDIS_URL: str = "redis://redis:6379/0"
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    INTERNAL_API_TOKEN: str = Field(..., min_length=1)
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
