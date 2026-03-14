from logging import INFO, getLogger
from pathlib import Path

import httpx
from httpx_retries import RetryTransport

from we_wish_the_perfect_weather.fetcher_base import FetcherBase
from we_wish_the_perfect_weather.util import datetime_to_date, datetime_to_yyyymmdd, get_now, get_yesterday

logger = getLogger(__name__)
logger.setLevel(INFO)


class PollenCountFetcher(FetcherBase):
    API_POLLEN_COUNT = "https://wxtech.weathernews.com/opendata/v1/pollen"
    INVALID_VALUE = -9999

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
        # 対象は昨日の実測値と、今日の予報値
        target_date_at_list = [
            get_yesterday(),
            get_now(),
        ]
        target_date_list = [datetime_to_date(t) for t in target_date_at_list]
        if target_date == target_date_list[0]:
            return (0, 24)  # 昨日の値が含まれるスライス範囲
        elif target_date == target_date_list[1]:
            return (24, 48)  # 今日の値が含まれるスライス範囲
        else:
            return (-1, -1)

    def get_forcast_max_pollon_count(self, pollen_count_list: list[int]) -> int:
        # 値として有効なものを集めた配列
        valid_pollen_count_list = [v for v in pollen_count_list if v != PollenCountFetcher.INVALID_VALUE]
        # 実測値としての現在の最大値
        max_rawdata_pollen_count = max(valid_pollen_count_list)

        n = len(valid_pollen_count_list)  # 有効な値が入っている個数
        m = len(pollen_count_list) - n  # 無効な値が入っている個数
        a = -1  # 傾き（仮置き）

        if n < 2:
            # 予測に必要な要素が足りない（少なくとも2つの要素が必要）ならば
            # 単純にmaxを返して終了
            return max_rawdata_pollen_count

        if m == 0:
            # すべて有効な実測値ならば
            # 予測する意味がないのでmaxを返して終了
            return max_rawdata_pollen_count

        # 増加量取得
        increases = [
            valid_pollen_count_list[i] - valid_pollen_count_list[i - 1]
            for i in range(1, n)
            # if valid_pollen_count_list[i] - valid_pollen_count_list[i - 1] > 0
        ]
        if not increases:
            a = 0
        else:
            # 傾きを取得
            a = sum(increases) / len(increases)

        # 予測値を取得
        max_forcast_pollen_count = int(max_rawdata_pollen_count + a * m)
        return max([max_forcast_pollen_count, max_rawdata_pollen_count])

    def interpret(self, target_date: str, record_type: str) -> dict:
        error_value_default = {
            "target_date": target_date,
            "record_type": record_type,
            "maximum_pollen_count": PollenCountFetcher.INVALID_VALUE,
        }
        if self.fetched_csv == "":
            # fetchが失敗している場合
            return error_value_default

        n, m = self.get_slice(target_date)
        if n == -1 or m == -1:
            # target_date が想定外の範囲
            return error_value_default

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

        # 花粉飛散量の実測値のmaxをとる
        max_rawdata_pollen_count = max(pollen_count_list[n:m])

        # target_dateが今日の予報ならば花粉飛散量のmaxの予測値を取得する
        max_forcast_pollen_count = (
            self.get_forcast_max_pollon_count(pollen_count_list)
            if target_date == datetime_to_date(get_now())
            else max_rawdata_pollen_count
        )

        # 花粉飛散量のmaxをとる
        pollen_count = max([max_forcast_pollen_count, max_rawdata_pollen_count])

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
    print(fetcher.interpret(datetime_to_date(get_now()), "forecast"))
