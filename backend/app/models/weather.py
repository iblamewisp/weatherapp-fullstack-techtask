import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Integer, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Weather(Base):
    __tablename__ = "weather"

    # Уникальный constraint на (city, country) — используется в upsert через ON CONFLICT.
    # Имя constraint должно совпадать с тем, что передаётся в on_conflict_do_update.
    __table_args__ = (UniqueConstraint("city", "country", name="uq_city_country"),)

    # UUID как PK — избегаем предсказуемых числовых ID в публичном API.
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
    weather_icon: Mapped[str] = mapped_column(String, nullable=True)   # код иконки OWM, напр. "04d"

    # Обновляется при каждом upsert — показывает когда данные последний раз синхронизировались с OWM.
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    # Устанавливается один раз при создании записи.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
