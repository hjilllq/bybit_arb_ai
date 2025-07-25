from __future__ import annotations
import json, logging, logging.handlers, sys
from datetime import datetime
from pathlib import Path
import config

LOG_PATH: Path = config.LOG_FILE
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "ts": datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
            "lvl": record.levelname.lower(),
            "msg": record.getMessage(),
            "mod": record.name,
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)

def setup_logger() -> logging.Logger:
    logger = logging.getLogger()
    if logger.handlers:
        return logger
    logger.setLevel(getattr(logging, config.LOG_LEVEL, logging.INFO))
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(JsonFormatter())
    fh = logging.handlers.TimedRotatingFileHandler(
        LOG_PATH, when="midnight", backupCount=14, encoding="utf-8"
    )
    fh.setFormatter(JsonFormatter())
    logger.addHandler(sh)
    logger.addHandler(fh)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    return logger

setup_logger()