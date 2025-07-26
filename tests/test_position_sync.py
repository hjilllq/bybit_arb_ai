import sys, pathlib
from decimal import Decimal
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest
from position_sync import sync_positions

class DummyClient:
    async def restore_positions(self):
        return {"BTCUSDT": Decimal("1")}

class DummyBot:
    def __init__(self):
        self.position = {"BTCUSDT": Decimal()}
        self.entry = {"BTCUSDT": None}
        self.real = {"BTCUSDT": Decimal()}
        self.unreal = {"BTCUSDT": Decimal()}

@pytest.mark.asyncio
async def test_sync_positions_updates():
    bot = DummyBot()
    client = DummyClient()
    await sync_positions(bot, client)
    assert bot.position["BTCUSDT"] == Decimal("1")

