from __future__ import annotations
import os, json, time
from decimal import Decimal, getcontext
from pathlib import Path
try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    def load_dotenv(*_args, **_kwargs):
        """Fallback no-op if python-dotenv is missing."""
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
    # In test environments credentials may be absent
    API_KEY = API_KEY or "TEST_KEY"
    API_SECRET = API_SECRET or "TEST_SECRET"

BYBIT_API_BASE_URL = (
    os.getenv("BYBIT_API_BASE_URL") or
    ("https://api-testnet.bybit.com" if USE_TESTNET else "https://api.bybit.com")
)

TRADE_PAIRS = [p.strip().upper() for p in os.getenv("TRADE_PAIRS", "BTCUSDT").split(",") if p.strip()]
CATEGORY_MAP = {s: "linear" for s in TRADE_PAIRS}

# number of concurrent trading loops per pair (default 4)
PARALLEL_TASKS = int(os.getenv("PARALLEL_TASKS", "4"))

MARGIN_MODE            = os.getenv("MARGIN_MODE", "CROSS").upper()
LEVERAGE               = Decimal(os.getenv("LEVERAGE", "1"))
MAX_POSITION_PERCENT   = Decimal(os.getenv("MAX_POSITION_PERCENT", "0.10"))
MAX_POSITION_USD       = Decimal(os.getenv("MAX_POSITION_USD", "1000"))
# maximum total exposure across all symbols
MAX_EXPOSURE_USD       = Decimal(os.getenv("MAX_EXPOSURE_USD", "3000"))

INCLUDE_FEES           = os.getenv("INCLUDE_FEES", "false").lower() in ("true", "1", "yes")
SPOT_FEE_RATE          = Decimal(os.getenv("SPOT_FEE_RATE", "0.0010"))
FUTURES_FEE_TAKER      = Decimal(os.getenv("FUTURES_FEE_TAKER_RATE", "0.00055"))
FUTURES_FEE_MAKER      = Decimal(os.getenv("FUTURES_FEE_MAKER_RATE", "0.00020"))

FUNDING_INTERVAL_HOURS = int(os.getenv("FUNDING_INTERVAL_HOURS",  "8"))
MIN_FUNDING_THRESHOLD  = Decimal(os.getenv("MIN_FUNDING_THRESHOLD", "0.0001"))

# максимальный допустимый убыток в долларах, после которого бот остановится
MAX_DRAWDOWN_USD = Decimal(os.getenv("MAX_DRAWDOWN_USD", "100"))
# maximum drop from peak PnL after start before the bot stops. 0 disables.
MAX_RELATIVE_DRAWDOWN_USD = Decimal(os.getenv("MAX_RELATIVE_DRAWDOWN_USD", "0"))
# per-symbol loss limit (0 disables)
MAX_SYMBOL_DRAWDOWN_USD = Decimal(os.getenv("MAX_SYMBOL_DRAWDOWN_USD", "0"))

# capital management parameters
ACCOUNT_EQUITY_USD      = Decimal(os.getenv("ACCOUNT_EQUITY_USD", "10000"))
RISK_PER_TRADE          = Decimal(os.getenv("RISK_PER_TRADE", "0.01"))  # 1% risk
DAILY_DRAWDOWN_USD      = Decimal(os.getenv("DAILY_DRAWDOWN_USD", "500"))
MAX_CONSECUTIVE_LOSSES  = int(os.getenv("MAX_CONSECUTIVE_LOSSES", "3"))
VOL_WINDOW              = int(os.getenv("VOL_WINDOW", "50"))
STOP_MULTIPLIER         = Decimal(os.getenv("STOP_MULTIPLIER", "2"))

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

# file for persisting bot state between restarts
STATE_FILE = LOG_DIR / "state.json"
# backup file to restore state if the main file is corrupted
STATE_BACKUP_FILE = LOG_DIR / "state.bak.json"

# interval between automatic state saves
STATE_SAVE_SEC = float(os.getenv("STATE_SAVE_SEC", "5"))

# minimal delay between trades for the same symbol
TRADE_COOLDOWN_SEC = float(os.getenv("TRADE_COOLDOWN_SEC", "0.5"))

# stop the bot if too many errors occur within a minute
ERROR_LIMIT = int(os.getenv("ERROR_LIMIT", "5"))

# maximum number of trades allowed per day before no further trades are placed
MAX_DAILY_TRADES = int(os.getenv("MAX_DAILY_TRADES", "200"))

# stop trading once profit reaches this amount (0 disables)
MAX_PROFIT_USD = Decimal(os.getenv("MAX_PROFIT_USD", "0"))

# file for logging profit and loss periodically
PNL_LOG = LOG_DIR / "pnl.csv"

# timeout before WS connection is considered stale
WS_LIVENESS_TIMEOUT = float(os.getenv("WS_LIVENESS_TIMEOUT", "30"))
