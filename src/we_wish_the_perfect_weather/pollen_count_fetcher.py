from logging import INFO, getLogger
from pathlib import Path

import httpx
from httpx_retries import RetryTransport

from we_wish_the_perfect_weather.fetcher_base import FetcherBase
from we_wish_the_perfect_weather.util import datetime_to_date, datetime_to_yyyymmdd, get_now, get_tomorrow
from we_wish_the_perfect_weather.util import get_yesterday, is_morning

logger = getLogger(__name__)
logger.setLevel(INFO)


class PollenCountFetcher(FetcherBase):
    API_POLLEN_COUNT = "https://wxtech.weathernews.com/opendata/v1/pollen"

    def __init__(self, config: dict):
        super().__init__(config)
        self.citycode = config["pollen_count"]["citycode"]

    def api_endpoint_url(self) -> str:
        return PollenCountFetcher.API_POLLEN_COUNT

    def api_params(self) -> dict:
        # 昨日と今日の分のみリクエスト
        return {
            "citycode": self.citycode,
            "start": datetime_to_yyyymmdd(get_yesterday()),
            "end": datetime_to_yyyymmdd(get_now()),
        }

    def fetch(self) -> dict:
        logger.info("Fetching pollen_count -> start.")
        # 花粉飛散数APIを使用
        # 1時間ごとに記録されたcsvカンマ区切り文字列が返ってくる
        try:
            with httpx.Client(transport=RetryTransport()) as client:
                response = client.get(self.api_endpoint_url(), params=self.api_params())
                response.raise_for_status()

                self.fetched_csv = response.text
        except Exception:
            logger.info("Fetching pollen_count failed.")
            self.fetched_csv = ""

        self.fetched_data = self.fetched_csv

        logger.info("Fetching pollen_count -> done.")
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
        if self.fetched_csv == "":
            # fetchが失敗している場合
            return {
                "target_date": target_date,
                "record_type": record_type,
                "maximum_pollen_count": -9999,
            }

        n, m = self.get_slice(target_date)
        if n == -1 or m == -1:
            # target_date が想定外の範囲
            return {
                "target_date": target_date,
                "record_type": record_type,
                "maximum_pollen_count": -9999,
            }

        if n == 48 and m == 72:
            # 明日の値を参照された場合、確定で値が存在しないので決め打ち
            return {
                "target_date": target_date,
                "record_type": record_type,
                "maximum_pollen_count": -9999,
            }

        def is_numeric(s: str) -> bool:
            try:
                float(s)
            except ValueError:
                return False
            else:
                return True

        # fetchしたcsvを分解
        pollen_count_list: list[int] = []
        lines = self.fetched_csv.split("\n")
        for line in lines:
            token = line.split(",")
            pollen = token[-1]
            if not is_numeric(pollen):
                continue
            pollen_count_list.append(int(pollen))

        # 花粉飛散量のmaxをとる
        pollen_count = max(pollen_count_list[n:m])

        return {
            "target_date": target_date,
            "record_type": record_type,
            "maximum_pollen_count": pollen_count,
        }


if __name__ == "__main__":
    import orjson

    config = orjson.loads(Path("./config/config.json").read_bytes())
    fetcher = PollenCountFetcher(config)
    print(fetcher.fetch())
    print(fetcher.interpret("2026-02-07", "forecast"))
