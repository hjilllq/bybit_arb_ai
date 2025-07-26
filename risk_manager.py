from __future__ import annotations
import asyncio, logging, os, signal
from decimal import Decimal
from alert_utils import ALERTS
import config
from monitoring import RISK_VIOLATIONS

logger = logging.getLogger(__name__)

class RiskManager:
    """Monitor PnL and stop trading if losses exceed configured limits."""
    CHECK_INTERVAL = 30  # seconds

    def __init__(self, bot: "TradingBotMulti", *, interval: float | None = None) -> None:  # noqa: F821
        self.bot = bot
        if interval is not None:
            self.CHECK_INTERVAL = interval
        self.high_water = Decimal()

    async def watch(self) -> None:
        while True:
            await asyncio.sleep(self.CHECK_INTERVAL)
            self.evaluate()

    def evaluate(self) -> None:
        pnl = sum(self.bot.real.values()) + sum(self.bot.unreal.values())
        if pnl > self.high_water:
            self.high_water = pnl
        if pnl <= -config.MAX_DRAWDOWN_USD:
            ALERTS.error(
                f"Порог убытка {config.MAX_DRAWDOWN_USD}$ превышен ({pnl}$)"
            )
            RISK_VIOLATIONS.labels(type="absolute").inc()
            logger.warning("Останавливаем бота из-за превышения убытков")
            os.kill(os.getpid(), signal.SIGTERM)
            return
        rel_limit = config.MAX_RELATIVE_DRAWDOWN_USD
        if rel_limit > 0 and self.high_water - pnl >= rel_limit:
            ALERTS.error(
                f"Потеря {self.high_water - pnl}$ от пика превышает лимит"
            )
            RISK_VIOLATIONS.labels(type="relative").inc()
            logger.warning("Останавливаем бота из-за относительной просадки")
            os.kill(os.getpid(), signal.SIGTERM)

