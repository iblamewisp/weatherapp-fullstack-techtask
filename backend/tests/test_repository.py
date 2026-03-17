import pytest
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from app.database import Base
from app.models.weather import Weather
from app.repositories.weather import SQLAlchemyWeatherRepository
from app.schemas.weather import WeatherCreate, WeatherUpdate


DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def session():
    engine = create_async_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Use simple metadata without postgresql-specific constraints for sqlite
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_and_get_by_city(session):
    repo = SQLAlchemyWeatherRepository(session)
    data = WeatherCreate(city="Paris", country="FR", latitude=48.85, longitude=2.35)
    created = await repo.create(data)
    assert created.city == "Paris"
    found = await repo.get_by_city("Paris", "FR")
    assert found is not None
    assert found.city == "Paris"


@pytest.mark.asyncio
async def test_get_all(session):
    repo = SQLAlchemyWeatherRepository(session)
    data1 = WeatherCreate(city="Berlin", country="DE")
    data2 = WeatherCreate(city="Tokyo", country="JP")
    await repo.create(data1)
    await repo.create(data2)
    all_records = await repo.get_all()
    assert len(all_records) == 2


@pytest.mark.asyncio
async def test_update(session):
    repo = SQLAlchemyWeatherRepository(session)
    data = WeatherCreate(city="Rome", country="IT")
    created = await repo.create(data)
    update = WeatherUpdate(temperature=25.0)
    updated = await repo.update(created.id, update)
    assert updated.temperature == 25.0


@pytest.mark.asyncio
async def test_delete(session):
    repo = SQLAlchemyWeatherRepository(session)
    data = WeatherCreate(city="Madrid", country="ES")
    created = await repo.create(data)
    deleted = await repo.delete(created.id)
    assert deleted is True
    found = await repo.get_by_id(created.id)
    assert found is None
