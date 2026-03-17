import logging
from contextlib import asynccontextmanager
import aiohttp
from fastapi import FastAPI, HTTPException, Request
from sqlalchemy import text
from app.database import AsyncSessionLocal
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config import settings
from app.logger import setup_logging
from app.routers.weather import router as weather_router
from app.tasks.scheduler import scheduler, fetch_all_cities_task

limiter = Limiter(key_func=get_remote_address)

setup_logging()
logger = logging.getLogger("weather_app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    app.state.http_client = aiohttp.ClientSession()
    scheduler.add_job(
        fetch_all_cities_task,
        "interval",
        minutes=settings.SCHEDULER_INTERVAL_MINUTES,
        args=[app.state.http_client, settings],
    )
    scheduler.start()
    yield
    logger.info("Shutting down...")
    scheduler.shutdown()
    await app.state.http_client.close()


app = FastAPI(title="Weather API", version="1.0.0", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "x-internal-token"],
)

UNPROTECTED_PATHS = {"/health"}


@app.middleware("http")
async def verify_internal_token(request: Request, call_next):
    if request.url.path not in UNPROTECTED_PATHS:
        token = request.headers.get("x-internal-token", "")
        if token != settings.INTERNAL_API_TOKEN:
            logger.warning(f"Unauthorized request to {request.url.path} from {request.client.host}")
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    return await call_next(request)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} -> {response.status_code}")
    return response


app.include_router(weather_router, prefix="/api/v1")


@app.get("/health")
async def health():
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}
    except Exception as e:
        logger.error(f"Health check DB failed: {e}")
        raise HTTPException(status_code=503, detail={"status": "degraded", "db": "unavailable"})
