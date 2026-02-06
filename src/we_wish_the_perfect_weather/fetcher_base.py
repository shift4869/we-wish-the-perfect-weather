from abc import ABCMeta, abstractmethod
from pathlib import Path

import openmeteo_requests
import requests_cache
from retry_requests import retry


class FetcherBase(metaclass=ABCMeta):
    API_OPEN_METEO = ""

    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def api_endpoint_url(self) -> str:
        raise NotImplementedError()

    @abstractmethod
    def api_params(self) -> dict:
        raise NotImplementedError()
        params = {
            "latitude": float(self.latitude),
            "longitude": float(self.longitude),
            "hourly": [
                "temperature_2m",
                "relative_humidity_2m",
                "precipitation",
                "precipitation_probability",
                "wind_speed_10m",
            ],
            "timezone": "Asia/Tokyo",
            "past_days": 1,
            "forecast_days": 2,
        }
        return params

    @abstractmethod
    def fetch(self) -> dict:
        raise NotImplementedError()

    @abstractmethod
    def interpret(self, target_date: str, record_type: str) -> dict:
        raise NotImplementedError()


if __name__ == "__main__":
    import orjson

    from we_wish_the_perfect_weather.open_meteo_fetcher import OpenMeteoFetcher

    config = orjson.loads(Path("./config/config.json").read_bytes())
    fetcher = OpenMeteoFetcher(config)
    print(fetcher.fetch())
