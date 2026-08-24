"""Resilient WeatherAPI.com client with caching, retries and clean error boundaries."""
from __future__ import annotations

import os
import time
from typing import Any

import requests
from requests.exceptions import RequestException

from api.exceptions import CityNotFoundError, ExternalServiceError
from utils.cache import geocode_cache, weather_cache, forecast_cache
from utils.logging_config import get_logger, log_event
from utils.retry import with_retry


class RetryableHTTPError(RequestException):
    pass


class NonRetryableHTTPError(RequestException):
    pass


WEATHERAPI_URL = "https://api.weatherapi.com/v1"
logger = get_logger("sunsafe.weather")


def _api_key() -> str:
    key = os.getenv("WEATHERAPI_KEY", "").strip()
    if not key:
        raise ExternalServiceError("WEATHERAPI_KEY is not configured.")
    return key


def _request_json(endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
    request_params = {
        "key": _api_key(),
        **params,
    }

    def call() -> dict[str, Any]:
        started = time.perf_counter()

        response = requests.get(
            f"{WEATHERAPI_URL}/{endpoint}",
            params=request_params,
            timeout=8,
        )

        log_event(
            logger,
            20,
            "weather_api_request_timing",
            endpoint=endpoint,
            status_code=response.status_code,
            latency_ms=round(
                (time.perf_counter() - started) * 1000,
                2,
            ),
        )

        if (
            response.status_code == 429
            or response.status_code == 408
            or response.status_code >= 500
        ):
            raise RetryableHTTPError(
                f"transient HTTP {response.status_code}"
            )

        if response.status_code >= 400:
            raise NonRetryableHTTPError(
                f"HTTP {response.status_code}"
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise RetryableHTTPError(
                "invalid JSON from weather service"
            ) from exc

        if isinstance(data, dict) and data.get("error"):
            error = data["error"]
            code = error.get("code", "unknown")
            message = error.get("message", "WeatherAPI error")
            raise NonRetryableHTTPError(
                f"WeatherAPI error {code}: {message}"
            )

        return data

    try:
        return with_retry(
            call,
            attempts=3,
            base_delay=0.35,
            retry_exceptions=(
                RetryableHTTPError,
                RequestException,
                ValueError,
            ),
        )
    except (
        NonRetryableHTTPError,
        RetryableHTTPError,
        RequestException,
        ValueError,
    ) as exc:
        raise ExternalServiceError(
            f"WeatherAPI request failed: {exc}"
        ) from exc


def get_coordinates(city: str) -> dict[str, Any]:
    key = city.strip().lower()
    cached = geocode_cache.get(key)

    if cached is not None:
        log_event(logger, 20, "geocode_cache_hit", city=city)
        return cached

    data = _request_json(
        "search.json",
        {"q": city},
    )

    results = data or []

    if not results:
        raise CityNotFoundError(
            f"City '{city}' not found."
        )

    location = results[0]

    result = {
        "name": location["name"],
        "country": location["country"],
        "latitude": location["lat"],
        "longitude": location["lon"],
    }

    geocode_cache.set(key, result)
    return result


def get_weather(
    latitude: float,
    longitude: float,
) -> dict[str, Any]:
    key = f"{latitude:.4f}:{longitude:.4f}"
    cached = weather_cache.get(key)

    if cached is not None:
        log_event(
            logger,
            20,
            "weather_cache_hit",
            cache_key=key,
        )
        return cached

    data = _request_json(
        "current.json",
        {"q": f"{latitude},{longitude}"},
    )

    try:
        current = data["current"]

        result = {
            "temperature": current["temp_c"],
            "relative_humidity": current["humidity"],
            "cloud_cover": current["cloud"],
            "wind_speed": current["wind_kph"],
            "weather_code": current["condition"]["code"],
            "uv_index": current["uv"],
        }

    except (KeyError, TypeError) as exc:
        raise ExternalServiceError(
            "WeatherAPI returned an unexpected weather payload"
        ) from exc

    weather_cache.set(key, result)
    return result


def get_hourly_forecast(
    latitude: float,
    longitude: float,
) -> list[dict[str, Any]]:
    key = f"{latitude:.4f}:{longitude:.4f}"
    cached = forecast_cache.get(key)

    if cached is not None:
        log_event(
            logger,
            20,
            "forecast_cache_hit",
            cache_key=key,
        )
        return cached

    data = _request_json(
        "forecast.json",
        {
            "q": f"{latitude},{longitude}",
            "days": 1,
        },
    )

    try:
        forecast_days = data["forecast"]["forecastday"]
        forecast = []

        for day in forecast_days:
            for hour in day["hour"]:
                forecast.append(
                    {
                        "time": hour["time"].replace(" ", "T"),
                        "temperature": hour["temp_c"],
                        "uv_index": hour["uv"],
                        "cloud_cover": hour["cloud"],
                    }
                )

    except (KeyError, TypeError) as exc:
        raise ExternalServiceError(
            "WeatherAPI returned an unexpected forecast payload"
        ) from exc

    forecast_cache.set(key, forecast)
    return forecast