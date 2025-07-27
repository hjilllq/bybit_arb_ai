from decimal import Decimal
import os, asyncio
import signal
import sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest

import config
from risk_manager import RiskManager

class DummyBot:
    def __init__(self, real, unreal=None):
        self.real = real
        self.unreal = unreal or {}
    async def close_all_positions(self):
        pass
    async def shutdown(self, reason: str):
        await self.close_all_positions()

def test_risk_manager_triggers(monkeypatch):
    called = {}
    def fake_kill(pid, sig):
        called['pid'] = pid
        called['sig'] = sig
    monkeypatch.setattr(os, 'kill', fake_kill)
    bot = DummyBot({'BTCUSDT': -100})
    rm = RiskManager(bot, interval=0)
    rm.evaluate()
    assert called['sig'] == signal.SIGTERM

def test_risk_manager_includes_unreal(monkeypatch):
    called = {}
    def fake_kill(pid, sig):
        called['pid'] = pid
        called['sig'] = sig
    monkeypatch.setattr(os, 'kill', fake_kill)
    bot = DummyBot({'BTCUSDT': -50}, {'BTCUSDT': -60})
    rm = RiskManager(bot, interval=0)
    rm.evaluate()
    assert called['sig'] == signal.SIGTERM

def test_relative_drawdown(monkeypatch):
    called = {}
    def fake_kill(pid, sig):
        called['sig'] = sig
    monkeypatch.setattr(os, 'kill', fake_kill)
    monkeypatch.setattr(config, 'MAX_DRAWDOWN_USD', Decimal('1000'))
    monkeypatch.setattr(config, 'MAX_RELATIVE_DRAWDOWN_USD', Decimal('10'))
    bot = DummyBot({'BTCUSDT': 20})
    rm = RiskManager(bot, interval=0)
    rm.evaluate()  # establish high water at 20
    bot.real['BTCUSDT'] = 5
    rm.evaluate()
    assert called['sig'] == signal.SIGTERM

@pytest.mark.asyncio
async def test_profit_limit(monkeypatch, event_loop):
    called = {}
    async def dummy_close():
        called['closed'] = True
    monkeypatch.setattr(os, 'kill', lambda *_: called.setdefault('kill', True))
    monkeypatch.setattr(config, 'MAX_PROFIT_USD', Decimal('10'))
    bot = DummyBot({'BTCUSDT': Decimal('12')})
    bot.close_all_positions = dummy_close
    rm = RiskManager(bot, interval=0)
    rm.evaluate()
    await asyncio.sleep(0)
    assert called['kill'] and called['closed']

def test_symbol_drawdown(monkeypatch):
    called = {}
    def fake_kill(pid, sig):
        called['sig'] = sig
    monkeypatch.setattr(os, 'kill', fake_kill)
    monkeypatch.setattr(config, 'MAX_SYMBOL_DRAWDOWN_USD', Decimal('50'))
    bot = DummyBot({'ETHUSDT': Decimal('-60')})
    rm = RiskManager(bot, interval=0)
    rm.evaluate()
    assert called['sig'] == signal.SIGTERM
