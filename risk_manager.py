from __future__ import annotations
import asyncio, logging, os, signal
from decimal import Decimal
from alert_utils import ALERTS
import config

logger = logging.getLogger(__name__)

class RiskManager:
    """Monitor PnL and stop trading if losses exceed configured limits."""
    CHECK_INTERVAL = 30  # seconds

    def __init__(self, bot: "TradingBotMulti", *, interval: float | None = None) -> None:  # noqa: F821
        self.bot = bot
        if interval is not None:
            self.CHECK_INTERVAL = interval

    async def watch(self) -> None:
        while True:
            await asyncio.sleep(self.CHECK_INTERVAL)
            self.evaluate()

    def evaluate(self) -> None:
        pnl = sum(self.bot.real.values())
        if pnl <= -config.MAX_DRAWDOWN_USD:
            ALERTS.error(
                f"Порог убытка {config.MAX_DRAWDOWN_USD}$ превышен ({pnl}$)"
            )
            logger.warning("Останавливаем бота из-за превышения убытков")
            os.kill(os.getpid(), signal.SIGTERM)

