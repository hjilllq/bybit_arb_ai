import asyncio
import os
import sys
from decimal import Decimal
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from api_client import APIClient

def test_place_order_updates_position_and_history():
    async def _run():
        client = APIClient()
        await client.start()
        await client.place_order("BTCUSDT", "Buy", Decimal("1"))
        assert client.position["BTCUSDT"] == Decimal("1")
        assert len(client.orders) == 1
        await client.close()

    asyncio.run(_run())
