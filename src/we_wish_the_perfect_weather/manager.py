from logging import INFO, getLogger
from pathlib import Path

import httpx
import orjson
from jinja2 import Template

from we_wish_the_perfect_weather.fetcher_base import FetcherBase
from we_wish_the_perfect_weather.open_meteo_fetcher import OpenMeteoFetcher
from we_wish_the_perfect_weather.pollen_count_fetcher import PollenCountFetcher
from we_wish_the_perfect_weather.util import Result, datetime_to_date, get_now, get_tomorrow, get_yesterday, is_morning
from we_wish_the_perfect_weather.weather_db_controller import WeatherDBController

logger = getLogger(__name__)
logger.setLevel(INFO)


class Manager:
    MSG_TEMPLATE_PATH = "./log/msg.html"
    CONFIG_PATH = "./config/config.json"
    PW_BASE = {
        "maximum_temperature": 28,
        "minimum_temperature": 18,
        "maximum_humidity": 70,
        "minimum_humidity": 40,
        "maximum_precipitation_probability": 10,
        "maximum_precipitation": 0,
        "maximum_wind_speed": 3,
        "maximum_pollen_count": 10,
    }

    def __init__(self) -> None:
        self.config: dict = orjson.loads(Path(Manager.CONFIG_PATH).read_bytes())
        self.fetcher_list: list[FetcherBase] = [OpenMeteoFetcher(self.config), PollenCountFetcher(self.config)]

        db_fullpath: Path = Path(self.config["db"]["save_path"]) / self.config["db"]["save_file_name"]
        self.weather_db: WeatherDBController = WeatherDBController(db_fullpath)

        msg_template_str: str = Path(Manager.MSG_TEMPLATE_PATH).read_text()
        self.msg_template: Template = Template(msg_template_str)

        self.registered_at: str = get_now()

    def check_perfection(self, info: dict) -> list[bool]:
        """気象情報を元に、"完璧な気候" かどうかを判定する

        Args:
            info (dict): 気象情報辞書

        Returns:
            list[bool]: 以下の定義のそれぞれの基準について、満たすかどうかの真偽値配列

        Notes:
            "完璧な気候" の定義
            ある一日を通して以下の各項目を常に満たしているとき「"完璧な気候" の一日だった」と呼ぶ
            ・気温18度以上28度以下、かつ湿度40%以上70%以下
                事務所衛生基準規則第5条より
                https://jsite.mhlw.go.jp/yamanashi-roudoukyoku/hourei_seido_tetsuzuki/anzen_eisei/hourei_seido/jimushosoku_kaisei_00001.html
                https://laws.e-gov.go.jp/law/347M50002000043/#Mp-Ch_5
            ・降水量が0または降水確率が10%以下=天気が雨または雪でない
                晴れか曇りかは問わない
            （・以下の注意報が出ていない
                ・雷、濃霧、乾燥、低温）
            ・風速3m/s以下（木の葉や細かい小枝が揺れる程度で、日常生活にはほとんど影響がない程度）
        """
        result = []
        match info:
            case {
                "record_type": record_type,
                "maximum_temperature": maximum_temperature,
                "minimum_temperature": minimum_temperature,
                "maximum_humidity": maximum_humidity,
                "minimum_humidity": minimum_humidity,
                "maximum_precipitation_probability": maximum_precipitation_probability,
                "maximum_precipitation": maximum_precipitation,
                "maximum_wind_speed": maximum_wind_speed,
                "maximum_pollen_count": maximum_pollen_count,
            }:
                pass
            case _:
                raise ValueError("info structure is invalid.")

        base = Manager.PW_BASE
        result.append(
            base["minimum_temperature"] <= maximum_temperature and maximum_temperature <= base["maximum_temperature"]
        )
        result.append(
            base["minimum_temperature"] <= minimum_temperature and minimum_temperature <= base["maximum_temperature"]
        )
        result.append(maximum_humidity <= base["maximum_humidity"])
        result.append(base["minimum_humidity"] <= minimum_humidity)
        result.append(maximum_precipitation_probability <= base["maximum_precipitation_probability"])
        result.append(maximum_precipitation <= base["maximum_precipitation"])
        result.append(maximum_wind_speed <= base["maximum_wind_speed"])
        result.append(maximum_pollen_count < base["maximum_pollen_count"])
        return result

    def post_discord_notify(self, message: str, is_embed: bool = False) -> Result:
        """Discord通知ポスト

        Args:
            message (str): Discordに通知する文字列
            is_embed (bool): 埋め込んで投稿するかどうか

        Returns:
            Result: 成功時Result.success
        """
        url = self.config["discord_webhook_url"]["webhook_url"]
        headers = {"Content-Type": "application/json"}

        payload = {}
        # if is_embed:
        #     description_msg = ""
        #     media_links = []
        #     lines = message.split("\n")
        #     for line in lines:
        #         line = line.strip()
        #         if line.startswith("http"):
        #             media_links.append(line)
        #         else:
        #             description_msg += line + "\n"
        #     embeds = []
        #     embeds.append({"description": description_msg})
        #     payload = {"embeds": embeds}

        if not payload:
            payload = {"content": "```" + message + "```"}

        response = httpx.post(url, headers=headers, data=orjson.dumps(payload).decode())
        response.raise_for_status()
        return Result.success

    def register(self, target_date: str, record_type: str) -> Result:
        record = {}
        for fetcher in self.fetcher_list:
            record = record | fetcher.interpret(target_date, record_type)

        check = self.check_perfection(record)
        record["is_perfect"] = all(check)
        record["registered_at"] = self.registered_at

        self.weather_db.upsert(record)

        is_post_discord = self.config["discord_webhook_url"]["is_post_discord_notify"]
        if record["is_perfect"]:
            logger.info(f"{target_date} {record_type} is perfect !!!")
            if self.config["notification"]["perfect"] and is_post_discord:
                line = "/" * 55 + "\n"
                msg = self.msg_template.render(record=record, base=Manager.PW_BASE, check=check)
                self.post_discord_notify(f"{line}{msg}{line}")
        else:
            logger.info(f"{target_date} {record_type} is imperfect ...")
            if self.config["notification"]["imperfect"] and is_post_discord:
                msg = self.msg_template.render(record=record, base=Manager.PW_BASE, check=check)
                self.post_discord_notify(msg)
        return Result.success

    def is_first_run_of_day(self, target_date1: str, target_date2: str) -> bool:
        t1 = self.weather_db.select_by_target_date(target_date1, "actual")
        t2 = self.weather_db.select_by_target_date(target_date2, "forecast")
        return not (t1 and t2)

    def run(self) -> Result:
        logger.info("Manager run -> start.")

        target_date_at_list = [
            get_yesterday(),
            get_now(),
            get_tomorrow(),
        ]
        target_date_list = [datetime_to_date(t) for t in target_date_at_list]
        target_date1, target_date2 = "", ""
        if is_morning():
            target_date1 = target_date_list[0]
            target_date2 = target_date_list[1]
            logger.info(f"Now is morning, checking [{target_date1}, {target_date2}].")
        else:
            target_date1 = target_date_list[1]
            target_date2 = target_date_list[2]
            logger.info(f"Now is afternoon, checking [{target_date1}, {target_date2}].")

        # 実行日の午前or午後それぞれで初回実行で無ければ
        if not self.is_first_run_of_day(target_date1, target_date2):
            logger.info(f"[{target_date1}, {target_date2}] target_date is already done.")
            logger.info("Manager run -> done.")
            return Result.success

        # 気象情報取得
        for fetcher in self.fetcher_list:
            fetcher.fetch()

        logger.info("Manager register -> start.")
        # 実測値格納
        self.register(target_date1, "actual")
        # 予報値格納
        self.register(target_date2, "forecast")
        logger.info("Manager register -> done.")

        logger.info("Manager run -> done.")
        return Result.success


if __name__ == "__main__":
    manager = Manager()
    manager.run()
