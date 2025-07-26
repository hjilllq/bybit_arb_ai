import os, importlib, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import config


def test_parallel_tasks_env(monkeypatch):
    monkeypatch.setenv("PARALLEL_TASKS", "3")
    cfg = importlib.reload(config)
    assert cfg.PARALLEL_TASKS == 3
    monkeypatch.delenv("PARALLEL_TASKS", raising=False)
    importlib.reload(config)

