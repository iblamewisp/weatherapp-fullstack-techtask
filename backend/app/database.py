from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from app.config import settings
from typing import AsyncGenerator

# NullPool отключает connection pooling — asyncpg создаёт новое соединение на каждый запрос.
# Это предотвращает проблемы со stale connections при использовании asyncpg + SQLAlchemy 2.0.
engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)

# async_sessionmaker — dedicated async factory (SQLAlchemy 2.0+).
# expire_on_commit=False: объекты остаются доступны после commit без повторного SELECT.
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


# Base — базовый класс для всех ORM моделей.
# Все модели должны наследоваться от него, чтобы Alembic видел их при autogenerate.
class Base(DeclarativeBase):
    pass


# FastAPI dependency injection — yields сессию на время запроса.
# commit происходит автоматически при успехе, rollback — при любом исключении.
# Используется через Depends(get_db) в роутерах.
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
