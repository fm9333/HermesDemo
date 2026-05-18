import json

from hermes_app.core.database import Database
from hermes_app.services.weather import WeatherService


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_weather_service_looks_up_forecast_and_caches_result(tmp_path):
    db = Database(tmp_path / "weather.db")
    db.init()

    def fake_urlopen(url, timeout=8.0):
        if "geocoding-api.open-meteo.com" in url:
            return FakeResponse(
                {
                    "results": [
                        {
                            "name": "北京",
                            "country": "中国",
                            "admin1": "北京市",
                            "latitude": 39.9042,
                            "longitude": 116.4074,
                            "timezone": "Asia/Shanghai",
                        }
                    ]
                }
            )
        return FakeResponse(
            {
                "current": {
                    "time": "2026-05-18T12:00",
                    "temperature_2m": 22.5,
                    "weather_code": 61,
                    "wind_speed_10m": 8.1,
                    "precipitation": 0.2,
                },
                "daily": {
                    "time": ["2026-05-18", "2026-05-19", "2026-05-20"],
                    "temperature_2m_max": [24, 25, 26],
                    "temperature_2m_min": [18, 19, 20],
                    "precipitation_probability_max": [60, 20, 10],
                },
            }
        )

    service = WeatherService(db, urlopen=fake_urlopen)
    result = service.lookup("北京")

    assert result["status"] == "ok"
    assert result["current"]["summary"] == "小雨"
    assert "北京 当前 22.5°C" in result["summary"]
    assert result["daily"][0]["precipitation_probability_max"] == 60

    cache = service.list_cache()
    assert len(cache) == 1
    assert cache[0]["location"] == "北京"
    assert cache[0]["payload"]["status"] == "ok"

