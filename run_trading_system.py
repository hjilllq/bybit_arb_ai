from __future__ import annotations
import asyncio, logging, signal, sys
from types import FrameType
import config
from logger import setup_logger
from monitoring import heartbeat, start_metrics_server
from trading_multi import TradingBotMulti

try:
    import uvloop
    uvloop.install()
except Exception:
    pass
setup_logger()
logger = logging.getLogger(__name__)

def _graceful(sig: int, _: FrameType | None):
    logger.info("Получен сигнал %s – завершаем…", signal.Signals(sig).name)
    for t in asyncio.all_tasks(): t.cancel()

for s in (signal.SIGINT, signal.SIGTERM): signal.signal(s, _graceful)

async def main():
    asyncio.create_task(start_metrics_server())
    asyncio.create_task(heartbeat())
    bot = TradingBotMulti()
    try:    await bot.run()
    except asyncio.CancelledError:
        pass
    finally: await bot.close()

if __name__ == "__main__":
    logger.info("Бот стартует в режиме %s – пары: %s", config.TRADE_MODE, ", ".join(config.TRADE_PAIRS))
    try:    asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)