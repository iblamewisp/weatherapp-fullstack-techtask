from abc import ABC, abstractmethod
from typing import List, Optional
import uuid
from app.models.weather import Weather
from app.schemas.weather import WeatherCreate, WeatherUpdate


class BaseWeatherRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> Optional[Weather]:
        pass

    @abstractmethod
    async def get_by_city(self, city: str, country: str) -> Optional[Weather]:
        pass

    @abstractmethod
    async def get_by_coords(self, lat: float, lon: float, tolerance: float = 0.5) -> Optional[Weather]:
        pass

    @abstractmethod
    async def get_all(self) -> List[Weather]:
        pass

    @abstractmethod
    async def create(self, data: WeatherCreate) -> Weather:
        pass

    @abstractmethod
    async def update(self, id: uuid.UUID, data: WeatherUpdate) -> Optional[Weather]:
        pass

    @abstractmethod
    async def delete(self, id: uuid.UUID) -> bool:
        pass

    @abstractmethod
    async def upsert(self, data: dict) -> Weather:
        pass
