import os
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.database import Base
from app.repositories.weather import SQLAlchemyWeatherRepository
from app.schemas.weather import WeatherCreate, WeatherUpdate

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://weather:weather@db:5432/weather_test",
)


@pytest.fixture(scope="session")
async def engine():
    # Create weather_test database if it doesn't exist.
    # Connects to the main database with AUTOCOMMIT since CREATE DATABASE
    # cannot run inside a transaction.
    admin_url = TEST_DATABASE_URL.rsplit("/", 1)[0] + "/weather"
    admin_engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    async with admin_engine.connect() as conn:
        exists = await conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = 'weather_test'")
        )
        if not exists.fetchone():
            await conn.execute(text("CREATE DATABASE weather_test"))
    await admin_engine.dispose()

    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def session(engine):
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s
    async with factory() as cleanup:
        await cleanup.execute(text("TRUNCATE TABLE weather CASCADE"))
        await cleanup.commit()


# ---------------------------------------------------------------------------
# Basic CRUD
# ---------------------------------------------------------------------------

async def test_create_and_get_by_city(session):
    repo = SQLAlchemyWeatherRepository(session)
    data = WeatherCreate(city="Paris", country="FR", latitude=48.85, longitude=2.35)
    created = await repo.create(data)
    assert created.city == "Paris"
    found = await repo.get_by_city("Paris", "FR")
    assert found is not None
    assert found.city == "Paris"


async def test_get_all(session):
    repo = SQLAlchemyWeatherRepository(session)
    await repo.create(WeatherCreate(city="Berlin", country="DE"))
    await repo.create(WeatherCreate(city="Tokyo", country="JP"))
    all_records = await repo.get_all()
    assert len(all_records) == 2


async def test_update(session):
    repo = SQLAlchemyWeatherRepository(session)
    created = await repo.create(WeatherCreate(city="Rome", country="IT"))
    updated = await repo.update(created.id, WeatherUpdate(temperature=25.0))
    assert updated.temperature == 25.0


async def test_delete(session):
    repo = SQLAlchemyWeatherRepository(session)
    created = await repo.create(WeatherCreate(city="Madrid", country="ES"))
    assert await repo.delete(created.id) is True
    assert await repo.get_by_id(created.id) is None


async def test_delete_nonexistent_returns_false(session):
    import uuid
    repo = SQLAlchemyWeatherRepository(session)
    assert await repo.delete(uuid.uuid4()) is False


# ---------------------------------------------------------------------------
# Upsert (PostgreSQL ON CONFLICT — untestable with SQLite)
# ---------------------------------------------------------------------------

async def test_upsert_inserts_new_record(session):
    repo = SQLAlchemyWeatherRepository(session)
    data = {
        "city": "London", "country": "GB",
        "latitude": 51.5, "longitude": -0.12,
        "temperature": 15.0, "feels_like": 13.0,
        "humidity": 80, "pressure": 1013, "wind_speed": 5.0,
        "weather_description": "light rain", "weather_icon": "10d",
    }
    result = await repo.upsert(data)
    assert result.city == "London"
    assert result.temperature == 15.0


async def test_upsert_updates_existing_record(session):
    """Second upsert on same city/country should update, not insert a duplicate."""
    repo = SQLAlchemyWeatherRepository(session)
    base = {
        "city": "London", "country": "GB",
        "latitude": 51.5, "longitude": -0.12,
        "temperature": 15.0, "feels_like": 13.0,
        "humidity": 80, "pressure": 1013, "wind_speed": 5.0,
        "weather_description": "light rain", "weather_icon": "10d",
    }
    first = await repo.upsert(base)
    updated = await repo.upsert({**base, "temperature": 20.0})

    assert updated.id == first.id          # same row, not a new one
    assert updated.temperature == 20.0
    assert updated.created_at == first.created_at  # created_at preserved


async def test_upsert_preserves_created_at(session):
    """ON CONFLICT DO UPDATE must exclude created_at from the update set."""
    repo = SQLAlchemyWeatherRepository(session)
    data = {
        "city": "Berlin", "country": "DE",
        "latitude": 52.5, "longitude": 13.4,
        "temperature": 10.0, "feels_like": 8.0,
        "humidity": 70, "pressure": 1010, "wind_speed": 3.0,
        "weather_description": "cloudy", "weather_icon": "04d",
    }
    first = await repo.upsert(data)
    second = await repo.upsert({**data, "temperature": 12.0})
    assert second.created_at == first.created_at


# ---------------------------------------------------------------------------
# get_by_coords
# ---------------------------------------------------------------------------

async def test_get_by_coords_hit(session):
    repo = SQLAlchemyWeatherRepository(session)
    await repo.create(WeatherCreate(city="London", country="GB", latitude=51.5074, longitude=-0.1278))
    found = await repo.get_by_coords(51.5, -0.12)
    assert found is not None
    assert found.city == "London"


async def test_get_by_coords_outside_tolerance_returns_none(session):
    repo = SQLAlchemyWeatherRepository(session)
    await repo.create(WeatherCreate(city="London", country="GB", latitude=51.5074, longitude=-0.1278))
    assert await repo.get_by_coords(40.0, 10.0) is None


async def test_get_by_coords_returns_nearest(session):
    """When multiple records fall within tolerance, the closest one is returned."""
    repo = SQLAlchemyWeatherRepository(session)
    await repo.create(WeatherCreate(city="CityFar", country="GB", latitude=51.8, longitude=-0.5))
    await repo.create(WeatherCreate(city="CityNear", country="GB", latitude=51.51, longitude=-0.13))
    found = await repo.get_by_coords(51.5, -0.12)
    assert found.city == "CityNear"
