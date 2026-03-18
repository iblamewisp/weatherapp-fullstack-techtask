import asyncio
import logging
import secrets
from contextlib import asynccontextmanager
import aiohttp
from fastapi import FastAPI, HTTPException, Request
from sqlalchemy import text
from app.database import AsyncSessionLocal
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.limiter import limiter
from app.config import settings
from app.logger import setup_logging
from app.routers.weather import router as weather_router
from app.repositories.weather import SQLAlchemyWeatherRepository
from app.services.weather_fetcher import WeatherFetcherService

setup_logging()
logger = logging.getLogger("weather_app")


async def _seed_popular_cities(http_client: aiohttp.ClientSession) -> None:
    """On cold start, fetch any popular cities not yet in the DB so the home page isn't empty."""
    async with AsyncSessionLocal() as session:
        repo = SQLAlchemyWeatherRepository(session)
        fetcher = WeatherFetcherService(http_client, settings)
        for city, country in settings.POPULAR_CITIES:
            existing = await repo.get_by_city(city, country)
            if not existing:
                try:
                    await fetcher.fetch_and_upsert(city, country, session)
                    logger.info(f"Seeded {city}, {country}")
                except Exception as e:
                    logger.warning(f"Seed failed for {city}, {country}: {e}")
        await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    app.state.http_client = aiohttp.ClientSession()
    await _seed_popular_cities(app.state.http_client)
    yield
    logger.info("Shutting down...")
    await app.state.http_client.close()


app = FastAPI(title="Weather API", version="1.0.0", lifespan=lifespan)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    from fastapi.openapi.utils import get_openapi
    schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
    schema.setdefault("components", {})["securitySchemes"] = {
        "InternalToken": {"type": "apiKey", "in": "header", "name": "x-internal-token"}
    }
    schema["security"] = [{"InternalToken": []}]
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "x-internal-token"],
)

UNPROTECTED_PATHS = {"/health", "/docs", "/redoc", "/openapi.json"}


@app.middleware("http")
async def verify_internal_token(request: Request, call_next):
    if request.url.path not in UNPROTECTED_PATHS:
        token = request.headers.get("x-internal-token", "")
        if not secrets.compare_digest(token, settings.INTERNAL_API_TOKEN):
            logger.warning(f"Unauthorized request to {request.url.path} from {request.client.host}")
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    return await call_next(request)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    try:
        response = await call_next(request)
        logger.info(f"{request.method} {request.url.path} -> {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"{request.method} {request.url.path} -> unhandled error: {e}")
        raise


app.include_router(weather_router, prefix="/api/v1")


@app.get("/health")
async def health():
    try:
        async with AsyncSessionLocal() as session:
            await asyncio.wait_for(session.execute(text("SELECT 1")), timeout=3.0)
        return {"status": "ok", "db": "ok"}
    except (asyncio.TimeoutError, Exception) as e:
        logger.error(f"Health check DB failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable: database unreachable")
