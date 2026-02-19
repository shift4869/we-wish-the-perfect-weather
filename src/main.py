import argparse
import logging.config
from logging import INFO, getLogger
from pathlib import Path

from we_wish_the_perfect_weather.manager import Manager

logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
for name in logging.root.manager.loggerDict:
    # 自分以外のすべてのライブラリのログ出力を抑制
    if "we_wish_the_perfect_weather" not in name:
        getLogger(name).disabled = True
logger = getLogger(__name__)
logger.setLevel(INFO)

PREVENT_MULTIPLE_RUN_PATH = "./prevent_multiple_run"


if __name__ == "__main__":
    horizontal_line = "-" * 100
    logger.info(horizontal_line)
    logger.info("We wish the perfect weather run -> start.")

    parser = argparse.ArgumentParser(description="we_wish_the_perfect_weather")
    parser.add_argument(
        "--force", action="store_true", help="1日1回の取得制限を無視して強制的に気象情報を取得する（手動実行用）"
    )
    args = parser.parse_args()
    is_force = False
    if args.force:
        is_force = True

    p = Path(PREVENT_MULTIPLE_RUN_PATH)
    try:
        if not p.exists():
            p.touch()
            manager = Manager(is_force)
            manager.run()
        else:
            logger.info("Multiple run -> abort.")
    except Exception as e:
        logger.exception(e)
    finally:
        p.unlink(missing_ok=True)
    logger.info("We wish the perfect weather run -> done.")
    logger.info(horizontal_line)
