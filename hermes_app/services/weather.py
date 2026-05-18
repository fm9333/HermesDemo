from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Callable, Protocol
from uuid import uuid4

from hermes_app.core.database import Database


class UrlOpen(Protocol):
    def __call__(self, url: str, timeout: float = 8.0): ...


WEATHER_CODE_TEXT = {
    0: "晴",
    1: "大部晴朗",
    2: "局部多云",
    3: "阴",
    45: "雾",
    48: "雾凇",
    51: "小毛毛雨",
    53: "中等毛毛雨",
    55: "大毛毛雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    80: "小阵雨",
    81: "中等阵雨",
    82: "强阵雨",
    95: "雷暴",
}


class WeatherService:
    provider = "open-meteo"

    def __init__(self, db: Database, urlopen: Callable = urllib.request.urlopen):
        self.db = db
        self.urlopen = urlopen

    def lookup(self, location: str) -> dict:
        location = location.strip()
        if not location:
            return {"status": "needs_location", "message": "需要提供城市或地点。"}

        try:
            place = self._geocode(location)
            if not place:
                result = {"status": "not_found", "location": location, "message": "没有找到匹配地点。"}
            else:
                forecast = self._forecast(place["latitude"], place["longitude"])
                result = self._format_result(location, place, forecast)
        except Exception as exc:  # noqa: BLE001 - provider errors should not crash Hermes
            result = {
                "status": "provider_error",
                "location": location,
                "provider": self.provider,
                "message": str(exc),
            }

        self._cache(location, result)
        return result

    def list_cache(self) -> list[dict]:
        rows = self.db.query("SELECT * FROM weather_cache ORDER BY created_at DESC LIMIT 50")
        for row in rows:
            row["payload"] = json.loads(row.pop("payload_json"))
        return rows

    def _geocode(self, location: str) -> dict | None:
        query = urllib.parse.urlencode({"name": location, "count": 1, "language": "zh", "format": "json"})
        data = self._fetch_json(f"https://geocoding-api.open-meteo.com/v1/search?{query}")
        results = data.get("results") or []
        return results[0] if results else None

    def _forecast(self, latitude: float, longitude: float) -> dict:
        query = urllib.parse.urlencode(
            {
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,weather_code,wind_speed_10m,precipitation",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "forecast_days": 3,
                "timezone": "auto",
            }
        )
        return self._fetch_json(f"https://api.open-meteo.com/v1/forecast?{query}")

    def _fetch_json(self, url: str) -> dict:
        with self.urlopen(url, timeout=8.0) as response:
            return json.loads(response.read().decode("utf-8"))

    def _format_result(self, requested_location: str, place: dict, forecast: dict) -> dict:
        current = forecast.get("current") or {}
        daily = forecast.get("daily") or {}
        weather_code = current.get("weather_code")
        summary = WEATHER_CODE_TEXT.get(weather_code, f"天气代码 {weather_code}")
        days = []
        for index, day in enumerate(daily.get("time", [])):
            days.append(
                {
                    "date": day,
                    "temperature_max": _safe_index(daily.get("temperature_2m_max"), index),
                    "temperature_min": _safe_index(daily.get("temperature_2m_min"), index),
                    "precipitation_probability_max": _safe_index(
                        daily.get("precipitation_probability_max"), index
                    ),
                }
            )

        return {
            "status": "ok",
            "provider": self.provider,
            "requested_location": requested_location,
            "resolved_location": {
                "name": place.get("name"),
                "country": place.get("country"),
                "admin1": place.get("admin1"),
                "latitude": place.get("latitude"),
                "longitude": place.get("longitude"),
                "timezone": place.get("timezone"),
            },
            "current": {
                "temperature": current.get("temperature_2m"),
                "precipitation": current.get("precipitation"),
                "wind_speed": current.get("wind_speed_10m"),
                "weather_code": weather_code,
                "summary": summary,
                "time": current.get("time"),
            },
            "daily": days,
            "summary": self._build_summary(place, current, days, summary),
        }

    def _build_summary(self, place: dict, current: dict, days: list[dict], summary: str) -> str:
        name = place.get("name") or "该地点"
        temperature = current.get("temperature_2m")
        if temperature is None:
            return f"{name} 当前天气：{summary}。"

        rain_hint = ""
        if days:
            probability = days[0].get("precipitation_probability_max")
            if probability is not None and probability >= 50:
                rain_hint = f" 今日最高降雨概率 {probability}%，建议关注出行提醒。"
        return f"{name} 当前 {temperature}°C，{summary}。{rain_hint}".strip()

    def _cache(self, location: str, payload: dict) -> None:
        self.db.execute(
            """
            INSERT INTO weather_cache (id, location, provider, status, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid4()),
                location,
                self.provider,
                payload.get("status", "unknown"),
                json.dumps(payload, ensure_ascii=False),
                datetime.now(timezone.utc).isoformat(),
            ),
        )


def _safe_index(values: list | None, index: int):
    if not values or index >= len(values):
        return None
    return values[index]

