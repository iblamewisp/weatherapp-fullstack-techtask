from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional
import uuid
from datetime import datetime


class WeatherCreate(BaseModel):
    city: str
    country: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @field_validator('country')
    @classmethod
    def country_must_be_alpha(cls, v: str) -> str:
        if not v.isalpha() or len(v) != 2:
            raise ValueError('country must be 2 alpha characters')
        return v.upper()


class WeatherUpdate(BaseModel):
    city: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    temperature: Optional[float] = None
    feels_like: Optional[float] = None
    humidity: Optional[int] = None
    pressure: Optional[int] = None
    wind_speed: Optional[float] = None
    weather_description: Optional[str] = None
    weather_icon: Optional[str] = None


class WeatherResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    city: str
    country: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    temperature: Optional[float] = None
    feels_like: Optional[float] = None
    humidity: Optional[int] = None
    pressure: Optional[int] = None
    wind_speed: Optional[float] = None
    weather_description: Optional[str] = None
    weather_icon: Optional[str] = None
    last_updated: datetime
    created_at: datetime


class CoordinatesQuery(BaseModel):
    latitude: float
    longitude: float

    @field_validator('latitude')
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if v < -90 or v > 90:
            raise ValueError('latitude must be between -90 and 90')
        return v

    @field_validator('longitude')
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if v < -180 or v > 180:
            raise ValueError('longitude must be between -180 and 180')
        return v


class CityQuery(BaseModel):
    city: str
    country: str

    @field_validator('city')
    @classmethod
    def validate_city(cls, v: str) -> str:
        if len(v) < 1 or len(v) > 100:
            raise ValueError('city must be between 1 and 100 characters')
        return v

    @field_validator('country')
    @classmethod
    def validate_country(cls, v: str) -> str:
        if not v.isalpha() or len(v) != 2:
            raise ValueError('country must be 2 alpha characters')
        return v.upper()
