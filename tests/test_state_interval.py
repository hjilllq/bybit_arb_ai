import os, importlib, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import config


def test_state_interval_env(monkeypatch):
    monkeypatch.setenv("STATE_SAVE_SEC", "3")
    cfg = importlib.reload(config)
    assert cfg.STATE_SAVE_SEC == 3
    monkeypatch.delenv("STATE_SAVE_SEC", raising=False)
    importlib.reload(config)


def test_state_interval_default(monkeypatch):
    monkeypatch.delenv("STATE_SAVE_SEC", raising=False)
    cfg = importlib.reload(config)
    assert cfg.STATE_SAVE_SEC == 5
