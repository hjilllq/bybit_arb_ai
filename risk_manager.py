from __future__ import annotations
import asyncio, logging, os, signal
from decimal import Decimal
from alert_utils import ALERTS
import config

logger = logging.getLogger(__name__)

class RiskManager:
    """Monitor PnL and stop trading if losses exceed configured limits."""
    CHECK_INTERVAL = 30  # seconds

    def __init__(self, bot: "TradingBotMulti") -> None:  # noqa: F821
        self.bot = bot

    async def watch(self) -> None:
        while True:
            await asyncio.sleep(self.CHECK_INTERVAL)
            pnl = sum(self.bot.real.values())
            if pnl <= -config.MAX_DRAWDOWN_USD:
                ALERTS.error(
                    f"Порог убытка {config.MAX_DRAWDOWN_USD}$ превышен ({pnl}$)"
                )
                logger.warning("Останавливаем бота из-за превышения убытков")
                os.kill(os.getpid(), signal.SIGTERM)

