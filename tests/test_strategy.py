import asyncio
from decimal import Decimal
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from api_client import APIClient
from strategy_multi import ArbitrageStrategyMulti

def test_strategy_detects_buy_sell():
    async def _run():
        client = APIClient()
        await client.start()
        client.ws._prices["BTCUSDT"] = (Decimal("102"), Decimal("100"))
        strat = ArbitrageStrategyMulti(client)
        action, edge = await strat.analyze("BTCUSDT")
        assert action == "buy_spot"
        assert edge > 0
        client.ws._prices["BTCUSDT"] = (Decimal("100"), Decimal("102"))
        action, edge = await strat.analyze("BTCUSDT")
        assert action == "sell_spot"
        await client.close()

    asyncio.run(_run())
