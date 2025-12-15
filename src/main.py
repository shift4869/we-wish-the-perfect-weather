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
    p = Path(PREVENT_MULTIPLE_RUN_PATH)
    try:
        if not p.exists():
            p.touch()
            manager = Manager()
            manager.run()
        else:
            logger.info("Multiple run -> abort.")
    except Exception as e:
        logger.exception(e)
    finally:
        p.unlink(missing_ok=True)
    logger.info("We wish the perfect weather run -> done.")
    logger.info(horizontal_line)
