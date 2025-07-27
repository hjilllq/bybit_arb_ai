from __future__ import annotations
import asyncio
import logging
import signal
import sys
from decimal import Decimal
from types import FrameType
import uvloop
import config
from logger import setup_logger
from monitoring import heartbeat, start_metrics_server
from trading_multi import TradingBotMulti
from risk_manager import RiskManager

uvloop.install()
setup_logger()
logger = logging.getLogger(__name__)

def _graceful(sig: int, _: FrameType | None):
    """Cancel all tasks on termination signals."""
    logger.info("Получен сигнал %s – завершаем…", signal.Signals(sig).name)
    for t in asyncio.all_tasks():
        t.cancel()

for s in (signal.SIGINT, signal.SIGTERM): signal.signal(s, _graceful)

async def main():
    """Run trading bot until cancelled."""
    asyncio.create_task(start_metrics_server())
    asyncio.create_task(heartbeat())
    bot = TradingBotMulti()
    risk = RiskManager(
        bot,
        high_water=bot.risk_state.get("high_water", Decimal()),
        sym_high_water=bot.risk_state.get("sym_high_water", {}),
    )
    bot.risk_manager = risk
    asyncio.create_task(risk.watch())
    try:
        await bot.run()
    except asyncio.CancelledError:
        pass
    finally:
        await bot.close()

if __name__ == "__main__":
    logger.info(
        "Бот стартует в режиме %s – пары: %s", config.TRADE_MODE, ", ".join(config.TRADE_PAIRS)
    )
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)


