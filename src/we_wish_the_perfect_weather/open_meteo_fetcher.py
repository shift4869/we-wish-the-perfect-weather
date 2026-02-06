from datetime import datetime
from logging import INFO, getLogger
from pathlib import Path

import openmeteo_requests
import requests_cache
from retry_requests import retry

from we_wish_the_perfect_weather.fetcher_base import FetcherBase
from we_wish_the_perfect_weather.util import datetime_to_date, get_now, get_tomorrow, get_yesterday, is_morning
from we_wish_the_perfect_weather.util import to_builtin

logger = getLogger(__name__)
logger.setLevel(INFO)


class OpenMeteoFetcher(FetcherBase):
    API_OPEN_METEO = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, config: dict):
        super().__init__(config)
        self.latitude = config["open_meteo"]["latitude"]
        self.longitude = config["open_meteo"]["longitude"]
        cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        self.open_meteo = openmeteo_requests.Client(session=retry_session)

    def api_endpoint_url(self) -> str:
        return OpenMeteoFetcher.API_OPEN_METEO

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

    def fetch(self) -> dict:
        logger.info("Fetching open_meteo -> start.")
        url = self.api_endpoint_url()
        params = self.api_params()

        responses = self.open_meteo.weather_api(url, params=params)
        response = responses[0]

        hourly = response.Hourly()
        hourly_temperature_2m = to_builtin(hourly.Variables(0).ValuesAsNumpy())
        hourly_relative_humidity_2m = to_builtin(hourly.Variables(1).ValuesAsNumpy())
        hourly_precipitation = to_builtin(hourly.Variables(2).ValuesAsNumpy())
        hourly_precipitation_probability = to_builtin(hourly.Variables(3).ValuesAsNumpy())
        hourly_wind_speed_10m = to_builtin(hourly.Variables(4).ValuesAsNumpy())
        start = hourly.Time()
        end = hourly.TimeEnd()
        freq = hourly.Interval()
        hourly_unixtime = list(range(start, end, freq))
        hourly_date_time = [datetime.fromtimestamp(x).strftime("%Y-%m-%d %H:%M:%S") for x in hourly_unixtime]

        hourly_data = {"date_list": hourly_date_time}
        hourly_data["temperature_2m"] = hourly_temperature_2m
        hourly_data["relative_humidity_2m"] = hourly_relative_humidity_2m
        hourly_data["precipitation"] = hourly_precipitation
        hourly_data["precipitation_probability"] = hourly_precipitation_probability
        hourly_data["wind_speed_10m"] = hourly_wind_speed_10m
        # print(hourly_data)
        self.fetched_data = hourly_data
        logger.info("Fetching open_meteo -> done.")
        return self.fetched_data

    def get_slice(self, target_date: str) -> tuple[int, int]:
        target_date_at_list = [
            get_yesterday(),
            get_now(),
            get_tomorrow(),
        ]
        target_date_list = [datetime_to_date(t) for t in target_date_at_list]
        if is_morning():
            if target_date == target_date_list[0]:
                return (0, 24)  # 昨日の値が含まれるスライス範囲
            elif target_date == target_date_list[1]:
                return (24, 48)  # 今日の値が含まれるスライス範囲
            else:
                return (-1, -1)
        else:
            if target_date == target_date_list[1]:
                return (24, 48)  # 今日の値が含まれるスライス範囲
            elif target_date == target_date_list[2]:
                return (48, 72)  # 明日の値が含まれるスライス範囲
            else:
                return (-1, -1)

    def interpret(self, target_date: str, record_type: str) -> dict:
        n, m = self.get_slice(target_date)
        if n == -1 or m == -1:
            return {}

        maximum_temperature = max(self.fetched_data["temperature_2m"][n:m])
        minimum_temperature = min(self.fetched_data["temperature_2m"][n:m])
        maximum_humidity = int(max(self.fetched_data["relative_humidity_2m"][n:m]))
        minimum_humidity = int(min(self.fetched_data["relative_humidity_2m"][n:m]))
        maximum_precipitation_probability = int(max(self.fetched_data["precipitation_probability"][n:m]))
        maximum_precipitation = max(self.fetched_data["precipitation"][n:m])
        maximum_wind_speed = max(self.fetched_data["wind_speed_10m"][n:m]) / 3.6  # [km/h]から[m/s]に変換

        return {
            "target_date": target_date,
            "record_type": record_type,
            "maximum_temperature": maximum_temperature,
            "minimum_temperature": minimum_temperature,
            "maximum_humidity": maximum_humidity,
            "minimum_humidity": minimum_humidity,
            "maximum_precipitation_probability": maximum_precipitation_probability,
            "maximum_precipitation": maximum_precipitation,
            "maximum_wind_speed": maximum_wind_speed,
        }


if __name__ == "__main__":
    import orjson

    config = orjson.loads(Path("./config/config.json").read_bytes())
    fetcher = OpenMeteoFetcher(config)
    print(fetcher.fetch())
