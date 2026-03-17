from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://weather:weather@db:5432/weather"
    OPENWEATHER_API_KEY: str = "your_key_here"
    OPENWEATHER_BASE_URL: str = "https://api.openweathermap.org/data/2.5"
    SCHEDULER_INTERVAL_MINUTES: int = 30
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    INTERNAL_API_TOKEN: str = "change_me_in_prod"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
