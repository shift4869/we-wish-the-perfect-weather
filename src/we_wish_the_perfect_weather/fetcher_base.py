from abc import ABCMeta, abstractmethod
from pathlib import Path

import openmeteo_requests
import requests_cache
from retry_requests import retry


class FetcherBase(metaclass=ABCMeta):
    api_endpoint_base = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, config: dict):
        self.config = config
        self.latitude = config["open_meteo"]["latitude"]
        self.longitude = config["open_meteo"]["longitude"]
        cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        self.open_meteo = openmeteo_requests.Client(session=retry_session)

    @property
    def api_endpoint_url(self) -> str:
        url = FetcherBase.api_endpoint_base
        return url

    @property
    def api_params(self) -> dict:
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


if __name__ == "__main__":
    import orjson

    from we_wish_the_perfect_weather.weather_fetcher import WeatherFetcher

    config = orjson.loads(Path("./config/config.json").read_bytes())
    fetcher = WeatherFetcher(config)
    print(fetcher.fetch())
