from abc import ABCMeta, abstractmethod
from pathlib import Path

from sqlalchemy import create_engine

from we_wish_the_perfect_weather.model import Base


class DBControllerBase(metaclass=ABCMeta):
    def __init__(self, db_fullpath="PW_DB.db"):
        self.dbname = db_fullpath
        self.engine = create_engine(f"sqlite:///{self.dbname}", echo=False)
        Base.metadata.create_all(self.engine)

    @abstractmethod
    def upsert(self, params: dict) -> None:
        """DBにUPSERTする

        Notes:
            一致しているかの判定は
            record_type, target_date の両方が一致している場合、とする

        Args:
            params (dict): 以下のキーを持つ辞書
                params = {
                    "target_date": (str: "%Y-%m-%d %H:%M:%S"),
                    "record_type": (str),
                    "is_perfect": (bool),
                    "maximum_temperature": (float),
                    "minimum_temperature": (float),
                    "maximum_humidity": (int),
                    "minimum_humidity": (int),
                    "maximum_precipitation_probability": (int),
                    "maximum_precipitation": (float),
                    "maximum_wind_speed": (float),
                    "registered_at": (str: "%Y-%m-%d %H:%M:%S"),
                }
        """
        pass

    @abstractmethod
    def select(self, limit=300) -> list[dict]:
        """DBからSELECTする

        Note:
            f"select * from Weather order by id desc limit {limit}"

        Args:
            limit (int): 取得レコード数上限

        Returns:
            list[dict]: SELECTしたレコードの辞書リスト
        """
        return []

    @abstractmethod
    def is_perfect(self, record_type: str, target_date: str) -> bool:
        """特定の日付の結果or予測が "完璧な気候" かを取得する

        Note:
            f"select * from Weather where record_type={record_type} and target_date={target_date}"
        """
        pass


if __name__ == "__main__":
    import orjson

    from we_wish_the_perfect_weather.weather_db_controller import WeatherDBController

    config = orjson.loads(Path("./config/config.json").read_bytes())

    db_fullpath = Path(config["db"]["save_path"]) / config["db"]["save_file_name"]
    db_cont = WeatherDBController(db_fullpath=str(db_fullpath))
