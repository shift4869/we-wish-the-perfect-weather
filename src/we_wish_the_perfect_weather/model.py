from typing import Self

from sqlalchemy import INTEGER, Boolean, Column, Float, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, deferred

Base = declarative_base()


class Weather(Base):
    """気象情報モデル

    [id] INTEGER NOT NULL UNIQUE,
    [target_date] TEXT NOT NULL,
    [record_type] TEXT NOT NULL,
    [is_perfect] Boolean NOT NULL,
    [maximum_temperature] Float NOT NULL,
    [minimum_temperature] Float NOT NULL,
    [maximum_humidity] Integer NOT NULL,
    [minimum_humidity] Integer NOT NULL,
    [maximum_precipitation_probability] Integer NOT NULL,
    [maximum_precipitation] Float NOT NULL,
    [maximum_wind_speed] Float NOT NULL,
    [registered_at] TEXT NOT NULL,
    PRIMARY KEY([id])
    """

    __tablename__ = "Weather"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_date = Column(String(32))
    record_type = Column(String(256), nullable=False)
    is_perfect = Column(Boolean(), nullable=False)
    maximum_temperature = Column(Float(precision=1), nullable=False)
    minimum_temperature = Column(Float(precision=1), nullable=False)
    maximum_humidity = Column(INTEGER(), nullable=False)
    minimum_humidity = Column(INTEGER(), nullable=False)
    maximum_precipitation_probability = Column(INTEGER(), nullable=False)
    maximum_precipitation = Column(Float(precision=1), nullable=False)
    maximum_wind_speed = Column(Float(precision=1), nullable=False)
    registered_at = Column(String(32))

    def __init__(
        self,
        target_date: str,
        record_type: str,
        is_perfect: bool,
        maximum_temperature: float,
        minimum_temperature: float,
        maximum_humidity: int,
        minimum_humidity: int,
        maximum_precipitation_probability: int,
        maximum_precipitation: float,
        maximum_wind_speed: float,
        registered_at: str,
    ) -> None:
        if not isinstance(target_date, str):
            raise TypeError("target_date must be str.")
        if not isinstance(record_type, str):
            raise TypeError("record_type must be str.")
        if not isinstance(is_perfect, bool):
            raise TypeError("is_perfect must be bool.")
        if not isinstance(maximum_temperature, float):
            raise TypeError("maximum_temperature must be float.")
        if not isinstance(minimum_temperature, float):
            raise TypeError("minimum_temperature must be float.")
        if not isinstance(maximum_humidity, int):
            raise TypeError("maximum_humidity must be int.")
        if not isinstance(minimum_humidity, int):
            raise TypeError("minimum_humidity must be int.")
        if not isinstance(maximum_precipitation_probability, int):
            raise TypeError("maximum_precipitation_probability must be int.")
        if not isinstance(maximum_precipitation, float):
            raise TypeError("maximum_precipitation must be float.")
        if not isinstance(maximum_wind_speed, float):
            raise TypeError("maximum_wind_speed must be float.")
        if not isinstance(registered_at, str):
            raise TypeError("registered_at must be str.")

        self.target_date = target_date
        self.record_type = record_type
        self.is_perfect = is_perfect
        self.maximum_temperature = maximum_temperature
        self.minimum_temperature = minimum_temperature
        self.maximum_humidity = maximum_humidity
        self.minimum_humidity = minimum_humidity
        self.maximum_precipitation_probability = maximum_precipitation_probability
        self.maximum_precipitation = maximum_precipitation
        self.maximum_wind_speed = maximum_wind_speed
        self.registered_at = registered_at

    def __repr__(self) -> str:
        columns = ", ".join([f"{k}={v}" for k, v in self.__dict__.items() if k[0] != "_"])
        return f"<{self.__class__.__name__}({columns})>"

    def __eq__(self, other: Self) -> bool:
        return (
            isinstance(other, Weather)
            and other.target_date == self.target_date
            and other.record_type == self.record_type
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "target_date": self.target_date,
            "record_type": self.record_type,
            "is_perfect": self.is_perfect,
            "maximum_temperature": self.maximum_temperature,
            "minimum_temperature": self.minimum_temperature,
            "maximum_humidity": self.maximum_humidity,
            "minimum_humidity": self.minimum_humidity,
            "maximum_precipitation_probability": self.maximum_precipitation_probability,
            "maximum_precipitation": self.maximum_precipitation,
            "maximum_wind_speed": self.maximum_wind_speed,
            "registered_at": self.registered_at,
        }

    @classmethod
    def create(cls, arg_dict: dict) -> Self:
        match arg_dict:
            case {
                "target_date": target_date,
                "record_type": record_type,
                "is_perfect": is_perfect,
                "maximum_temperature": maximum_temperature,
                "minimum_temperature": minimum_temperature,
                "maximum_humidity": maximum_humidity,
                "minimum_humidity": minimum_humidity,
                "maximum_precipitation_probability": maximum_precipitation_probability,
                "maximum_precipitation": maximum_precipitation,
                "maximum_wind_speed": maximum_wind_speed,
                "registered_at": registered_at,
            }:
                return cls(
                    target_date,
                    record_type,
                    is_perfect,
                    maximum_temperature,
                    minimum_temperature,
                    maximum_humidity,
                    minimum_humidity,
                    maximum_precipitation_probability,
                    maximum_precipitation,
                    maximum_wind_speed,
                    registered_at,
                )
            case _:
                raise ValueError("Weather create failed.")


if __name__ == "__main__":
    engine = create_engine("sqlite:///PW_DB.db", echo=True)
    Base.metadata.create_all(engine)

    session = Session(engine)

    result = session.query(Weather).all()[:10]
    for f in result:
        print(f)

    session.close()
