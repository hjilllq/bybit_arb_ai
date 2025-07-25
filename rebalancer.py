from __future__ import annotations
import asyncio, logging
from decimal import Decimal
import config
from retry_utils import retry_async

logger = logging.getLogger(__name__)
MIN_IMBAL_QTY = Decimal("0.0001")

async def smart_rebalance(client: "APIClient", bot: "TradingBotMulti"):  # noqa: F821
    while True:
        await asyncio.sleep(2)
        try:
            on_chain = await retry_async(client.restore_positions)
            for sym in config.TRADE_PAIRS:
                diff = bot.position[sym] - on_chain.get(sym, Decimal())
                if abs(diff) < MIN_IMBAL_QTY:
                    continue
                side = "Buy" if diff < 0 else "Sell"
                qty  = abs(diff)
                await client.place_order(sym, side, qty)
                bot.position[sym] -= diff
                logger.info("Rebalance %s %s %.6f", sym, side, qty)
        except Exception as exc:
            logger.warning("Rebalance err: %s", exc)