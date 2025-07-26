import sys, pathlib, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import asyncio
import pytest
import config
from ws_manager import WSManager

class DummyClient:
    pass

class DummyConn:
    def __init__(self):
        self.closed = False
    async def close(self):
        self.closed = True

@pytest.mark.asyncio
async def test_watchdog_closes_stale(monkeypatch):
    monkeypatch.setattr(config, 'WS_LIVENESS_TIMEOUT', 0.01)
    mgr = WSManager(DummyClient())
    mgr.LIVENESS_TIMEOUT = 0.01
    mgr.conn = DummyConn()
    mgr._last_msg = time.monotonic() - 1
    mgr._stop.clear()
    task = asyncio.create_task(mgr._watch())
    await asyncio.sleep(0.03)
    mgr._stop.set()
    await task
    assert mgr.conn.closed
