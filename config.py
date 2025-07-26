from __future__ import annotations
import os, json, time
from decimal import Decimal, getcontext
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(BASE_DIR / ".env")

USE_TESTNET = os.getenv("USE_TESTNET", "true").lower() in ("true", "1", "yes")
TRADE_MODE  = "TESTNET" if USE_TESTNET else "MAINNET"

API_KEY    = os.getenv("BYBIT_API_KEY_TESTNET") if USE_TESTNET else os.getenv("BYBIT_API_KEY_MAIN")
API_SECRET = os.getenv("BYBIT_API_SECRET_TESTNET") if USE_TESTNET else os.getenv("BYBIT_API_SECRET_MAIN")

if not API_KEY or not API_SECRET:
    raise EnvironmentError("API‑keys not set")

BYBIT_API_BASE_URL = (
    os.getenv("BYBIT_API_BASE_URL") or
    ("https://api-testnet.bybit.com" if USE_TESTNET else "https://api.bybit.com")
)

TRADE_PAIRS = [p.strip().upper() for p in os.getenv("TRADE_PAIRS", "BTCUSDT").split(",") if p.strip()]
CATEGORY_MAP = {s: "linear" for s in TRADE_PAIRS}

MARGIN_MODE            = os.getenv("MARGIN_MODE", "CROSS").upper()
LEVERAGE               = Decimal(os.getenv("LEVERAGE", "1"))
MAX_POSITION_PERCENT   = Decimal(os.getenv("MAX_POSITION_PERCENT", "0.10"))
MAX_POSITION_USD       = Decimal(os.getenv("MAX_POSITION_USD", "1000"))

INCLUDE_FEES           = os.getenv("INCLUDE_FEES", "false").lower() in ("true", "1", "yes")
SPOT_FEE_RATE          = Decimal(os.getenv("SPOT_FEE_RATE", "0.0010"))
FUTURES_FEE_TAKER      = Decimal(os.getenv("FUTURES_FEE_TAKER_RATE", "0.00055"))
FUTURES_FEE_MAKER      = Decimal(os.getenv("FUTURES_FEE_MAKER_RATE", "0.00020"))

FUNDING_INTERVAL_HOURS = int(os.getenv("FUNDING_INTERVAL_HOURS",  "8"))
MIN_FUNDING_THRESHOLD  = Decimal(os.getenv("MIN_FUNDING_THRESHOLD", "0.0001"))

# максимальный допустимый убыток в долларах, после которого бот остановится
MAX_DRAWDOWN_USD = Decimal(os.getenv("MAX_DRAWDOWN_USD", "100"))

USE_RL_MODEL  = os.getenv("USE_RL_MODEL", "true").lower() in ("true", "1", "yes")
RL_MODEL_PATH = Path(os.getenv("RL_MODEL_PATH", "./policies/ppo_latest.zip"))
RL_UPDATE_SEC = int(os.getenv("RL_UPDATE_SEC", "30"))
RL_MIN_ROLLOUT= int(os.getenv("RL_MIN_ROLLOUT", "512"))
RL_BUFFER_CAP = 2048

PROM_HOST = os.getenv("PROM_HOST", "0.0.0.0")
PROM_PORT = int(os.getenv("PROM_PORT", "9100"))

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE  = LOG_DIR / "bot.log"

EMAIL_ENABLED  = os.getenv("EMAIL_ENABLED", "0").lower() in ("1", "true", "yes")
EMAIL_SENDER   = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
ALERT_EMAILS   = os.getenv("ALERT_EMAILS", "")
TG_BOT_TOKEN   = os.getenv("TG_BOT_TOKEN", "")
TG_CHAT_ID     = os.getenv("TG_CHAT_ID", "")

def get_model_path(sym: str) -> Path:
    """Return RL model path for a trading pair."""
    p = RL_MODEL_PATH
    if "{sym}" in str(p):
        return Path(str(p).format(sym=sym))
    return p.with_name(f"{p.stem}_{sym}{p.suffix}")

getcontext().prec = 18

# файл для записи сделок
TRADE_LOG = LOG_DIR / "trades.csv"
