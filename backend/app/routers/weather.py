import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.database import get_db
from app.repositories.weather import SQLAlchemyWeatherRepository
from app.schemas.weather import WeatherCreate, WeatherUpdate, WeatherResponse, CityQuery, CoordinatesQuery
from app.services.weather_fetcher import WeatherFetcherService
from app.config import settings
from typing import List, Union

router = APIRouter(prefix="/weather", tags=["weather"])
logger = logging.getLogger("weather_app.router")
limiter = Limiter(key_func=get_remote_address)


def get_fetcher(request: Request) -> WeatherFetcherService:
    return WeatherFetcherService(request.app.state.http_client, settings)


@router.get("", response_model=List[WeatherResponse])
@limiter.limit("20/minute")
async def list_weather(request: Request, db: AsyncSession = Depends(get_db)):
    repo = SQLAlchemyWeatherRepository(db)
    return await repo.get_all()


@router.get("/{id}", response_model=WeatherResponse)
@limiter.limit("20/minute")
async def get_weather(request: Request, id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    repo = SQLAlchemyWeatherRepository(db)
    record = await repo.get_by_id(id)
    if not record:
        raise HTTPException(status_code=404, detail="Weather record not found")
    return record


@router.post("", response_model=WeatherResponse, status_code=201)
@limiter.limit("5/minute")
async def create_weather(request: Request, data: WeatherCreate, db: AsyncSession = Depends(get_db)):
    repo = SQLAlchemyWeatherRepository(db)
    return await repo.create(data)


@router.put("/{id}", response_model=WeatherResponse)
@limiter.limit("5/minute")
async def update_weather(request: Request, id: uuid.UUID, data: WeatherUpdate, db: AsyncSession = Depends(get_db)):
    repo = SQLAlchemyWeatherRepository(db)
    record = await repo.update(id, data)
    if not record:
        raise HTTPException(status_code=404, detail="Weather record not found")
    return record


@router.delete("/{id}", status_code=204)
@limiter.limit("5/minute")
async def delete_weather(request: Request, id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    repo = SQLAlchemyWeatherRepository(db)
    deleted = await repo.delete(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Weather record not found")
    return Response(status_code=204)


@router.post("/fetch", response_model=WeatherResponse)
@limiter.limit("5/minute")
async def fetch_weather(
    request: Request,
    body: Union[CityQuery, CoordinatesQuery],
    db: AsyncSession = Depends(get_db),
):
    fetcher = get_fetcher(request)
    if isinstance(body, CityQuery):
        weather = await fetcher.fetch_and_upsert(body.city, body.country, db)
    else:
        raw = await fetcher.fetch_by_coords(body.latitude, body.longitude)
        parsed = fetcher._parse_owm_response(raw)
        repo = SQLAlchemyWeatherRepository(db)
        weather = await repo.upsert(parsed)
    return weather
