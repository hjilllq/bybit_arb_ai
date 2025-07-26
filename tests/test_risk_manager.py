from decimal import Decimal
import os
import signal
import sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest

from risk_manager import RiskManager

class DummyBot:
    def __init__(self, real, unreal=None):
        self.real = real
        self.unreal = unreal or {}

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
