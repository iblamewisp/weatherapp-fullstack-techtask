import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Integer, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Weather(Base):
    __tablename__ = "weather"

    # Unique constraint on (city, country) — used in upsert via ON CONFLICT.
    # The constraint name must match what is passed to on_conflict_do_update.
    __table_args__ = (UniqueConstraint("city", "country", name="uq_city_country"),)

    # UUID as PK — avoids predictable numeric IDs in the public API.
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    city: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)  # ISO 3166-1 alpha-2
    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)
    temperature: Mapped[float] = mapped_column(Float, nullable=True)   # °C
    feels_like: Mapped[float] = mapped_column(Float, nullable=True)    # °C
    humidity: Mapped[int] = mapped_column(Integer, nullable=True)      # %
    pressure: Mapped[int] = mapped_column(Integer, nullable=True)      # hPa
    wind_speed: Mapped[float] = mapped_column(Float, nullable=True)    # m/s
    weather_description: Mapped[str] = mapped_column(String, nullable=True)
    weather_icon: Mapped[str] = mapped_column(String, nullable=True)   # OWM icon code, e.g. "04d"

    # Updated on every upsert — reflects when the record was last synced with OWM.
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    # Set once on record creation, never overwritten by upsert.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
