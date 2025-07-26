from __future__ import annotations
import os, json, time
from decimal import Decimal, getcontext
from pathlib import Path
try:
    from dotenv import load_dotenv
except Exception:  # noqa: S110
    def load_dotenv(*_args, **_kwargs):
        pass

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(BASE_DIR / ".env")

USE_TESTNET = os.getenv("USE_TESTNET", "true").lower() in ("true", "1", "yes")
TRADE_MODE  = "TESTNET" if USE_TESTNET else "MAINNET"

API_KEY    = os.getenv("BYBIT_API_KEY_TESTNET") if USE_TESTNET else os.getenv("BYBIT_API_KEY_MAIN")
API_SECRET = os.getenv("BYBIT_API_SECRET_TESTNET") if USE_TESTNET else os.getenv("BYBIT_API_SECRET_MAIN")

if not API_KEY or not API_SECRET:
    API_KEY = API_SECRET = "DUMMY"

BYBIT_API_BASE_URL = (
    os.getenv("BYBIT_API_BASE_URL") or
    ("https://api-testnet.bybit.com" if USE_TESTNET else "https://api.bybit.com")
)

TRADE_PAIRS = [p.strip().upper() for p in os.getenv("TRADE_PAIRS", "BTCUSDT").split(",") if p.strip()]
CATEGORY_MAP = {s: "linear" for s in TRADE_PAIRS}

MARGIN_MODE            = os.getenv("MARGIN_MODE", "CROSS").upper()
LEVERAGE               = Decimal(os.getenv("LEVERAGE", "1"))
MAX_POSITION_PERCENT   = Decimal(os.getenv("MAX_POSITION_PERCENT", "0.10"))

INCLUDE_FEES           = os.getenv("INCLUDE_FEES", "false").lower() in ("true", "1", "yes")
SPOT_FEE_RATE          = Decimal(os.getenv("SPOT_FEE_RATE", "0.0010"))
FUTURES_FEE_TAKER      = Decimal(os.getenv("FUTURES_FEE_TAKER_RATE", "0.00055"))
FUTURES_FEE_MAKER      = Decimal(os.getenv("FUTURES_FEE_MAKER_RATE", "0.00020"))

FUNDING_INTERVAL_HOURS = int(os.getenv("FUNDING_INTERVAL_HOURS",  "8"))
MIN_FUNDING_THRESHOLD  = Decimal(os.getenv("MIN_FUNDING_THRESHOLD", "0.0001"))

USE_RL_MODEL  = os.getenv("USE_RL_MODEL", "true").lower() in ("true", "1", "yes")
RL_MODEL_PATH = Path(os.getenv("RL_MODEL_PATH", "./policies/ppo_latest.zip"))
RL_UPDATE_SEC = int(os.getenv("RL_UPDATE_SEC", "30"))
RL_MIN_ROLLOUT= int(os.getenv("RL_MIN_ROLLOUT", "512"))
RL_BUFFER_CAP = 2048

PROM_HOST  = os.getenv("PROM_HOST", "0.0.0.0")
PROM_PORT  = int(os.getenv("PROM_PORT", "9100"))

LOG_LEVEL  = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE   = LOG_DIR / "bot.log"

getcontext().prec = 18