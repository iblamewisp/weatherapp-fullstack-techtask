import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from app.models.weather import Weather
from app.repositories.base import BaseWeatherRepository
from app.schemas.weather import WeatherCreate, WeatherUpdate


# Concrete SQLAlchemy implementation of the repository.
# Receives an AsyncSession via __init__ — session lifecycle is managed by get_db() dependency.
class SQLAlchemyWeatherRepository(BaseWeatherRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    # session.scalar() returns a single ORM object or None — SQLAlchemy 2.0 style.
    async def get_by_id(self, id: uuid.UUID) -> Optional[Weather]:
        return await self.session.scalar(select(Weather).where(Weather.id == id))

    async def get_by_city(self, city: str, country: str) -> Optional[Weather]:
        return await self.session.scalar(
            select(Weather).where(Weather.city == city, Weather.country == country.upper())
        )

    # Nearest-match lookup within a lat/lon bounding box.
    # OWM returns city-centre coordinates which rarely match the queried coords exactly,
    # so we find the closest stored record within `tolerance` degrees on each axis,
    # ordered by Manhattan distance to prefer the best available match.
    async def get_by_coords(self, lat: float, lon: float, tolerance: float = 0.5) -> Optional[Weather]:
        return await self.session.scalar(
            select(Weather)
            .where(
                Weather.latitude.between(lat - tolerance, lat + tolerance),
                Weather.longitude.between(lon - tolerance, lon + tolerance),
            )
            .order_by(
                func.abs(Weather.latitude - lat) + func.abs(Weather.longitude - lon)
            )
            .limit(1)
        )

    # session.scalars() returns all matching ORM objects as a sequence.
    async def get_all(self) -> List[Weather]:
        result = await self.session.scalars(select(Weather))
        return list(result.all())

    # Creates a bare record without weather data — used for manual POST /weather.
    # flush() writes to DB within the transaction without committing;
    # refresh() re-reads the row so generated fields (id, created_at) are populated.
    async def create(self, data: WeatherCreate) -> Weather:
        weather = Weather(
            city=data.city,
            country=data.country.upper(),
            latitude=data.latitude,
            longitude=data.longitude,
        )
        self.session.add(weather)
        await self.session.flush()
        await self.session.refresh(weather)
        return weather

    # Partial update — model_dump(exclude_unset=True) only touches fields sent in the request body.
    async def update(self, id: uuid.UUID, data: WeatherUpdate) -> Optional[Weather]:
        weather = await self.get_by_id(id)
        if not weather:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(weather, key, value)
        weather.last_updated = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(weather)
        return weather

    # Returns True if a row was actually deleted, False if the id didn't exist.
    async def delete(self, id: uuid.UUID) -> bool:
        result = await self.session.execute(delete(Weather).where(Weather.id == id))
        return result.rowcount > 0

    # Core method used by POST /fetch and the scheduler.
    # PostgreSQL INSERT ... ON CONFLICT DO UPDATE — atomic get-or-create with fresh data.
    # created_at is excluded from the update set to preserve the original creation timestamp.
    # id is excluded to avoid overwriting the existing PK on conflict.
    # After the upsert, re-fetches the row via get_by_city to return a fully populated ORM object.
    async def upsert(self, data: dict) -> Weather:
        now = datetime.now(timezone.utc)
        insert_data = {**data, "last_updated": now}
        if "created_at" not in insert_data:
            insert_data["created_at"] = now

        stmt = insert(Weather).values(**insert_data)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_city_country",
            set_={
                k: stmt.excluded[k]
                for k in insert_data
                if k not in ("id", "created_at")
            },
        )
        stmt = stmt.returning(Weather)
        result = await self.session.execute(
            stmt, execution_options={"populate_existing": True}
        )
        weather = result.scalars().first()
        await self.session.flush()
        return weather
