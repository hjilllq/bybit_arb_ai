from __future__ import annotations
import logging
from decimal import Decimal
import config
from retry_utils import retry_async
from error_manager import ERROR_TRACKER

logger = logging.getLogger(__name__)

async def sync_positions(bot: "TradingBotMulti", client: "APIClient") -> None:  # noqa: F821
    """Load positions from the exchange and apply them to the bot state."""
    try:
        positions = await retry_async(client.restore_positions)
    except Exception as exc:  # pragma: no cover - network issues
        logger.warning("Failed to sync positions: %s", exc)
        ERROR_TRACKER.record()
        return
    for sym in config.TRADE_PAIRS:
        qty = positions.get(sym, Decimal())
        bot.position[sym] = qty
        if qty == 0:
            bot.entry[sym] = None
        bot.real[sym] = Decimal()
        bot.unreal[sym] = Decimal()
