import os
import signal
from decimal import Decimal
import sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import config
from capital_manager import CapitalManager

class DummyBot:
    def __init__(self):
        self.real = {s: Decimal() for s in config.TRADE_PAIRS}
        self.unreal = {s: Decimal() for s in config.TRADE_PAIRS}


def test_calc_order_qty_respects_limits(monkeypatch):
    bot = DummyBot()
    cm = CapitalManager(bot)
    monkeypatch.setattr(config, "RISK_PER_TRADE", Decimal("0.02"))
    monkeypatch.setattr(config, "MAX_POSITION_USD", Decimal("100"))
    qty = cm.calc_order_qty(config.TRADE_PAIRS[0], Decimal("50"))
    assert qty <= Decimal("2")  # 100 USD limit


def test_consecutive_loss_trigger(monkeypatch):
    bot = DummyBot()
    cm = CapitalManager(bot)
    monkeypatch.setattr(config, "MAX_CONSECUTIVE_LOSSES", 1)
    called = {}
    def fake_kill(pid, sig):
        called['sig'] = sig
    monkeypatch.setattr(os, 'kill', fake_kill)
    bot.real[config.TRADE_PAIRS[0]] = Decimal("-10")
    cm.update_equity()
    assert called['sig'] == signal.SIGTERM
