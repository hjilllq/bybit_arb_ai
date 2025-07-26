import asyncio
from decimal import Decimal
import sys, pathlib
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import config
from trading_multi import TradingBotMulti

class DummyClient:
    async def get_best(self, sym):
        return Decimal('100'), Decimal('101')
    async def place_order(self, sym, side, qty):
        raise AssertionError('Order should not be placed')

class DummySim:
    async def worst_price(self, sym, side, qty):
        return Decimal('101')

@pytest.mark.asyncio
async def test_position_limit(monkeypatch):
    bot = TradingBotMulti()
    bot.client = DummyClient()
    bot.sim = DummySim()
    bot._calc_qty = lambda sym, price: Decimal('0.01')
    bot.position['BTCUSDT'] = Decimal('0.05')
    monkeypatch.setattr(config, 'MAX_POSITION_USD', Decimal('5'))
    await bot._trade('BTCUSDT', 'buy_spot', Decimal('0.2'))
    assert bot.position['BTCUSDT'] == Decimal('0.05')

