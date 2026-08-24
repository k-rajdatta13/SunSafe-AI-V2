"""Resilient Open-Meteo client with caching, retries and clean error boundaries."""
from __future__ import annotations

from typing import Any
import requests
from requests.exceptions import RequestException, HTTPError

from api.exceptions import CityNotFoundError, ExternalServiceError
from utils.cache import geocode_cache, weather_cache, forecast_cache
from utils.logging_config import get_logger, log_event
from utils.retry import with_retry

class RetryableHTTPError(RequestException):
    pass

class NonRetryableHTTPError(RequestException):
    pass

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
CURRENT_WEATHER_FIELDS = "temperature_2m,relative_humidity_2m,cloud_cover,wind_speed_10m,weather_code,uv_index"
logger = get_logger("sunsafe.weather")


def _request_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    def call() -> dict[str, Any]:
        response = requests.get(url, params=params, timeout=8)
        if response.status_code == 429 or response.status_code == 408 or response.status_code >= 500:
            raise RetryableHTTPError(f"transient HTTP {response.status_code}")
        if response.status_code >= 400:
            raise NonRetryableHTTPError(f"HTTP {response.status_code}")
        try:
            return response.json()
        except ValueError as exc:
            raise RetryableHTTPError("invalid JSON from weather service") from exc

    try:
        return with_retry(call, attempts=3, base_delay=0.35, retry_exceptions=(RetryableHTTPError, RequestException, ValueError))
    except (NonRetryableHTTPError, RetryableHTTPError, RequestException, ValueError) as exc:
        raise ExternalServiceError(f"Open-Meteo request failed: {exc}") from exc


def get_coordinates(city: str) -> dict[str, Any]:
    key = city.strip().lower()
    cached = geocode_cache.get(key)
    if cached is not None:
        log_event(logger, 20, "geocode_cache_hit", city=city)
        return cached
    data = _request_json(GEOCODING_URL, {"name": city, "count": 1, "format": "json"})
    results = data.get("results") or []
    if not results:
        raise CityNotFoundError(f"City '{city}' not found.")
    location = results[0]
    result = {
        "name": location["name"],
        "country": location["country"],
        "latitude": location["latitude"],
        "longitude": location["longitude"],
    }
    geocode_cache.set(key, result)
    return result


def get_weather(latitude: float, longitude: float) -> dict[str, Any]:
    key = f"{latitude:.4f}:{longitude:.4f}"
    cached = weather_cache.get(key)
    if cached is not None:
        log_event(logger, 20, "weather_cache_hit", cache_key=key)
        return cached
    data = _request_json(FORECAST_URL, {
        "latitude": latitude,
        "longitude": longitude,
        "current": CURRENT_WEATHER_FIELDS,
        "timezone": "auto",
    })
    try:
        current = data["current"]
        result = {
            "temperature": current["temperature_2m"],
            "relative_humidity": current["relative_humidity_2m"],
            "cloud_cover": current["cloud_cover"],
            "wind_speed": current["wind_speed_10m"],
            "weather_code": current["weather_code"],
            "uv_index": current["uv_index"],
        }
    except (KeyError, TypeError) as exc:
        raise ExternalServiceError("Open-Meteo returned an unexpected weather payload") from exc
    weather_cache.set(key, result)
    return result


def get_hourly_forecast(latitude: float, longitude: float) -> list[dict[str, Any]]:
    key = f"{latitude:.4f}:{longitude:.4f}"
    cached = forecast_cache.get(key)
    if cached is not None:
        log_event(logger, 20, "forecast_cache_hit", cache_key=key)
        return cached
    data = _request_json(FORECAST_URL, {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m,uv_index,cloud_cover",
        "forecast_days": 1,
        "timezone": "auto",
    })
    try:
        hourly = data["hourly"]
        forecast = [
            {"time": t, "temperature": temp, "uv_index": uv, "cloud_cover": cloud}
            for t, temp, uv, cloud in zip(
                hourly["time"], hourly["temperature_2m"], hourly["uv_index"], hourly["cloud_cover"]
            )
        ]
    except (KeyError, TypeError) as exc:
        raise ExternalServiceError("Open-Meteo returned an unexpected forecast payload") from exc
    forecast_cache.set(key, forecast)
    return forecast
