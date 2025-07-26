import sys, pathlib, os
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from error_manager import ErrorManager


def test_error_manager_stops(monkeypatch):
    called = {}
    def fake_kill(pid, sig):
        called['sig'] = sig
    monkeypatch.setattr(os, 'kill', fake_kill)
    em = ErrorManager(window=1, limit=2)
    em.record(); em.record()
    assert called['sig']

