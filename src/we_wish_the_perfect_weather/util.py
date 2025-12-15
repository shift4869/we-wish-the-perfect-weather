import enum
from datetime import datetime, timedelta
from typing import Any


class Result(enum.Enum):
    success = enum.auto()
    failed = enum.auto()


class RecordType(enum.Enum):
    actual = "actual"
    forcast = "forcast"


def find_values(
    obj: Any,
    key: str,
    is_predict_one: bool = False,
    key_white_list: list[str] = None,
    key_black_list: list[str] = None,
) -> list | Any:
    if not key_white_list:
        key_white_list = []
    if not key_black_list:
        key_black_list = []

    def _inner_helper(inner_obj: Any, inner_key: str, inner_result: list) -> list:
        if isinstance(inner_obj, dict) and (inner_dict := inner_obj):
            for k, v in inner_dict.items():
                if k == inner_key:
                    inner_result.append(v)
                if key_white_list and (k not in key_white_list):
                    continue
                if k in key_black_list:
                    continue
                inner_result.extend(_inner_helper(v, inner_key, []))
        if isinstance(inner_obj, list) and (inner_list := inner_obj):
            for element in inner_list:
                inner_result.extend(_inner_helper(element, inner_key, []))
        return inner_result

    result = _inner_helper(obj, key, [])
    if not is_predict_one:
        return result

    if len(result) < 1:
        raise ValueError(f"Value of key='{key}' is not found.")
    if len(result) > 1:
        raise ValueError(f"Value of key='{key}' are multiple found.")
    return result[0]


def get_now() -> str:
    """現在日時を返す

    Returns:
        str: "%Y-%m-%d %H:%M:%S" 形式の現在日時
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_tomorrow() -> str:
    """1日後の日時を返す

    Returns:
        str: "%Y-%m-%d %H:%M:%S" 形式の1日後の日時
    """
    return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")


def get_yesterday() -> str:
    """1日前の日時を返す

    Returns:
        str: "%Y-%m-%d %H:%M:%S" 形式の1日前の日時
    """
    return (datetime.now() + timedelta(days=-1)).strftime("%Y-%m-%d %H:%M:%S")


def datetime_to_date(datetime_at: str) -> str:
    """日時文字列から年月日のみ取り出す

    Args:
        datetime_at (str): 対象の日時文字列

    Returns:
        str: 対象の日時文字列に含まれる年月日
    """
    # 変換テスト
    datetime.strptime(datetime_at, "%Y-%m-%d %H:%M:%S")
    return str(datetime_at[:10])


def is_morning() -> bool:
    """午前中かどうかを返す

    Returns:
        bool: 午前中ならばTrue, 午後ならばFalse
    """
    return datetime.now().hour < 12


def to_builtin(obj: Any) -> Any:
    """NumPy互換データを、Python標準の list / dict / int / float に変換する

    Args:
        obj (Any): 対象のNumpy互換オブジェクト

    Returns:
        Any: Python標準オブジェクト
    """
    # NumPyが無い環境でも安全に動くようにする
    try:
        import numpy as np

        numpy_types = (
            np.ndarray,
            np.generic,
        )
    except ImportError:
        numpy_types = ()

    # NumPy配列
    if numpy_types and isinstance(obj, numpy_types[0]):
        return obj.tolist()

    # NumPyスカラー
    if numpy_types and isinstance(obj, numpy_types[1]):
        return obj.item()

    # dict
    if isinstance(obj, dict):
        return {k: to_builtin(v) for k, v in obj.items()}

    # list / tuple / set
    if isinstance(obj, (list, tuple, set)):
        return [to_builtin(v) for v in obj]

    # その他（int, float, str, None など）
    return obj


if __name__ == "__main__":
    pass
