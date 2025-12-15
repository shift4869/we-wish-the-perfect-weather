from datetime import datetime
from logging import INFO, getLogger
from pathlib import Path

from we_wish_the_perfect_weather.fetcher_base import FetcherBase
from we_wish_the_perfect_weather.util import to_builtin

logger = getLogger(__name__)
logger.setLevel(INFO)


class WeatherFetcher(FetcherBase):
    def __init__(self, config: dict):
        super().__init__(config)

    def fetch(self) -> dict:
        logger.info("Fetching -> start.")
        url = self.api_endpoint_url
        params = self.api_params

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
        logger.info("Fetching -> done.")
        return hourly_data


if __name__ == "__main__":
    import orjson

    config = orjson.loads(Path("./config/config.json").read_bytes())
    fetcher = WeatherFetcher(config)
    print(fetcher.fetch())
