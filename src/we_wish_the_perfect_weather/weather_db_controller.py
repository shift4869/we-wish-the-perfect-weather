from pathlib import Path

from sqlalchemy import and_, desc
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import sessionmaker

from we_wish_the_perfect_weather.db_controller_base import DBControllerBase
from we_wish_the_perfect_weather.model import Weather


class WeatherDBController(DBControllerBase):
    def __init__(self, db_fullpath="PW_DB.db"):
        super().__init__(db_fullpath)

    def upsert(self, params: dict) -> None:
        """DBにUPSERTする

        Notes:
            一致しているかの判定は
            record_type, target_date の両方が一致している場合、とする

        Args:
            params (dict): 以下のキーを持つ辞書
                params = {
                    "target_date": (str: "%Y-%m-%d"),
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
        Session = sessionmaker(bind=self.engine)
        session = Session()

        records = [Weather.create(params)]
        for r in records:
            try:
                q = session.query(Weather).filter(
                    and_(
                        Weather.record_type == r.record_type,
                        Weather.target_date == r.target_date,
                    )
                )
                ex = q.one()
            except NoResultFound:
                # INSERT
                session.add(r)
            else:
                # UPDATE
                ex.target_date = r.target_date
                ex.record_type = r.record_type
                ex.is_perfect = r.is_perfect
                ex.maximum_temperature = r.maximum_temperature
                ex.minimum_temperature = r.minimum_temperature
                ex.maximum_humidity = r.maximum_humidity
                ex.minimum_humidity = r.minimum_humidity
                ex.maximum_precipitation_probability = r.maximum_precipitation_probability
                ex.maximum_precipitation = r.maximum_precipitation
                ex.maximum_wind_speed = r.maximum_wind_speed
                ex.registered_at = r.registered_at

        session.commit()
        session.close()

    def select(self, limit=300) -> list[dict]:
        """WeatherからSELECTする

        Note:
            f"select * from Weather order by id desc limit {limit}"

        Args:
            limit (int): 取得レコード数上限

        Returns:
            list[dict]: SELECTしたレコードの辞書リスト
        """
        Session = sessionmaker(bind=self.engine)
        session = Session()

        res = session.query(Weather).order_by(desc(Weather.id)).limit(limit).all()
        res_dict = [r.to_dict() for r in res]  # 辞書リストに変換

        session.close()
        return res_dict

    def is_perfect(self, record_type: str, target_date: str) -> bool:
        """特定の日付の結果or予測が "完璧な気候" かを取得する

        Note:
            f"select * from Weather where record_type={record_type} and target_date={target_date}"
        """
        result = False
        Session = sessionmaker(bind=self.engine)
        session = Session()

        records = (
            session.query(Weather)
            .filter(
                and_(
                    Weather.record_type == record_type,
                    Weather.target_date == target_date,
                )
            )
            .all()
        )

        if not records:
            return False
        if len(records) != 1:
            return False
        result = records[0].is_perfect

        session.commit()
        session.close()

        return result


if __name__ == "__main__":
    import orjson

    from we_wish_the_perfect_weather.weather_db_controller import WeatherDBController

    config = orjson.loads(Path("./config/config.json").read_bytes())

    db_fullpath = Path(config["db"]["save_path"]) / config["db"]["save_file_name"]
    db_cont = WeatherDBController(db_fullpath=str(db_fullpath))
