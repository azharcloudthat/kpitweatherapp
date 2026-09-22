from __future__ import annotations

from typing import Any

import requests


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT_SECONDS = 8


class WeatherServiceError(Exception):
    """Expected error while resolving a location or loading its weather."""


class LocationNotFoundError(WeatherServiceError):
    """Raised when Open-Meteo cannot find the requested city."""


WEATHER_CODES: dict[int, tuple[str, str, str]] = {
    0: ("Clear sky", "SUN", "clear"),
    1: ("Mainly clear", "SUN", "clear"),
    2: ("Partly cloudy", "CLOUD", "cloudy"),
    3: ("Overcast", "CLOUD", "cloudy"),
    45: ("Foggy", "FOG", "cloudy"),
    48: ("Rime fog", "FOG", "cloudy"),
    51: ("Light drizzle", "RAIN", "rain"),
    53: ("Drizzle", "RAIN", "rain"),
    55: ("Heavy drizzle", "RAIN", "rain"),
    56: ("Freezing drizzle", "SNOW", "snow"),
    57: ("Heavy freezing drizzle", "SNOW", "snow"),
    61: ("Light rain", "RAIN", "rain"),
    63: ("Rain", "RAIN", "rain"),
    65: ("Heavy rain", "RAIN", "rain"),
    66: ("Freezing rain", "SNOW", "snow"),
    67: ("Heavy freezing rain", "SNOW", "snow"),
    71: ("Light snow", "SNOW", "snow"),
    73: ("Snow", "SNOW", "snow"),
    75: ("Heavy snow", "SNOW", "snow"),
    77: ("Snow grains", "SNOW", "snow"),
    80: ("Light showers", "RAIN", "rain"),
    81: ("Rain showers", "RAIN", "rain"),
    82: ("Heavy showers", "RAIN", "rain"),
    85: ("Snow showers", "SNOW", "snow"),
    86: ("Heavy snow showers", "SNOW", "snow"),
    95: ("Thunderstorm", "STORM", "storm"),
    96: ("Thunderstorm with hail", "STORM", "storm"),
    99: ("Heavy thunderstorm with hail", "STORM", "storm"),
}


def describe_weather_code(code: int) -> tuple[str, str, str]:
    """Return a readable condition, display icon, and CSS theme for a WMO code."""
    return WEATHER_CODES.get(code, ("Unknown conditions", "?", "cloudy"))


def _get_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as error:
        raise WeatherServiceError("The weather provider is unavailable.") from error

    if not isinstance(payload, dict):
        raise WeatherServiceError("The weather provider returned an invalid response.")

    return payload


def _find_location(city: str) -> dict[str, Any]:
    payload = _get_json(
        GEOCODING_URL,
        {"name": city, "count": 1, "language": "en", "format": "json"},
    )
    locations = payload.get("results")

    if not isinstance(locations, list) or not locations:
        raise LocationNotFoundError(f'No location found for "{city}".')

    location = locations[0]
    if not isinstance(location, dict) or not all(
        isinstance(location.get(field), (int, float))
        for field in ("latitude", "longitude")
    ):
        raise WeatherServiceError("The geocoding response was incomplete.")

    return location


def _weather_description(code: Any) -> tuple[str, str, str]:
    if isinstance(code, bool):
        return describe_weather_code(-1)

    try:
        return describe_weather_code(int(code))
    except (TypeError, ValueError):
        return describe_weather_code(-1)


def get_weather(city: str) -> dict[str, Any]:
    """Resolve a city and return the normalized data consumed by the frontend."""
    location = _find_location(city)
    latitude = location["latitude"]
    longitude = location["longitude"]

    payload = _get_json(
        FORECAST_URL,
        {
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,relative_humidity_2m,apparent_temperature,"
                "precipitation,weather_code,wind_speed_10m"
            ),
            "daily": "weather_code,temperature_2m_max,temperature_2m_min",
            "forecast_days": 5,
            "timezone": "auto",
        },
    )

    current_data = payload.get("current")
    daily_data = payload.get("daily")
    required_daily_fields = (
        "time",
        "weather_code",
        "temperature_2m_max",
        "temperature_2m_min",
    )

    if not isinstance(current_data, dict) or not isinstance(daily_data, dict):
        raise WeatherServiceError("The forecast response was incomplete.")
    if not all(isinstance(daily_data.get(field), list) for field in required_daily_fields):
        raise WeatherServiceError("The forecast response was incomplete.")

    current_condition, current_icon, current_theme = _weather_description(
        current_data.get("weather_code")
    )
    daily_dates = daily_data["time"]
    daily_codes = daily_data["weather_code"]
    daily_max = daily_data["temperature_2m_max"]
    daily_min = daily_data["temperature_2m_min"]
    forecast = []

    for date, code, maximum, minimum in zip(
        daily_dates, daily_codes, daily_max, daily_min, strict=False
    ):
        condition, icon, theme = _weather_description(code)
        forecast.append(
            {
                "date": date,
                "condition": condition,
                "icon": icon,
                "theme": theme,
                "max_temperature": maximum,
                "min_temperature": minimum,
            }
        )

    if len(forecast) != 5:
        raise WeatherServiceError("The forecast response did not contain five days.")

    return {
        "location": {
            "name": location.get("name", city),
            "country": location.get("country", ""),
            "latitude": latitude,
            "longitude": longitude,
        },
        "current": {
            "temperature": current_data.get("temperature_2m"),
            "feels_like": current_data.get("apparent_temperature"),
            "humidity": current_data.get("relative_humidity_2m"),
            "wind_speed": current_data.get("wind_speed_10m"),
            "precipitation": current_data.get("precipitation"),
            "condition": current_condition,
            "icon": current_icon,
            "theme": current_theme,
        },
        "forecast": forecast,
        "updated_at": current_data.get("time"),
        "units": {
            "temperature": "°C",
            "wind_speed": "km/h",
            "precipitation": "mm",
        },
    }