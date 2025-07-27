from __future__ import annotations
import asyncio
import json
import logging
import time
from decimal import Decimal
try:
    import websockets
except ImportError:  # pragma: no cover - optional dependency
    websockets = None
import config
from monitoring import WS_RECONNECTS

logger = logging.getLogger(__name__)

class WSManager:
    """Maintain WebSocket connection and stream best bid/ask quotes."""

    URL_MAIN = "wss://stream.bybit.com/v5/public/linear"
    URL_TEST = "wss://stream-testnet.bybit.com/v5/public/linear"
    RECONNECT_DELAY = 5
    LIVENESS_TIMEOUT = config.WS_LIVENESS_TIMEOUT

    def __init__(self, client: "APIClient") -> None:  # noqa: F821
        self.client = client
        self.conn: websockets.WebSocketClientProtocol | None = None
        self.best: dict[str, tuple[Decimal, Decimal]] = {
            s: (Decimal(), Decimal()) for s in config.TRADE_PAIRS
        }
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()
        self._watchdog: asyncio.Task | None = None
        self._last_msg = asyncio.get_event_loop().time()

    async def start(self) -> None:
        if not self._task:
            self._stop.clear()
            self._task = asyncio.create_task(self._run())
            self._watchdog = asyncio.create_task(self._watch())

    async def _run(self) -> None:
        url = self.URL_TEST if config.USE_TESTNET else self.URL_MAIN
        subs = [f"orderbook.1.{sym}" for sym in config.TRADE_PAIRS]
        while not self._stop.is_set():
            try:
                async with websockets.connect(url) as conn:
                    self.conn = conn
                    await conn.send(json.dumps({"op": "subscribe", "args": subs}))
                    logger.info("WS subscribed to %s", ", ".join(subs))
                    await self._listener(conn)
            except Exception as exc:
                WS_RECONNECTS.inc()
                logger.warning(
                    "WS reconnect in %s sec: %s", self.RECONNECT_DELAY, exc
                )
                await asyncio.sleep(self.RECONNECT_DELAY)

    async def _listener(self, conn: websockets.WebSocketClientProtocol) -> None:
        async for msg in conn:
            self._last_msg = time.monotonic()
            data = json.loads(msg)
            ob = data.get("data")
            if not ob:
                continue
            sym = ob.get("s")
            if sym and sym in self.best:
                bid = Decimal(str(ob["b"][0][0]))
                ask = Decimal(str(ob["a"][0][0]))
                self.best[sym] = (bid, ask)

    async def get_best(self, sym: str) -> tuple[Decimal, Decimal]:
        while True:
            bid, ask = self.best.get(sym, (Decimal(), Decimal()))
            if bid and ask:
                return bid, ask
            await asyncio.sleep(0.1)

    async def close(self) -> None:
        self._stop.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        if self._watchdog:
            self._watchdog.cancel()
            try:
                await self._watchdog
            except asyncio.CancelledError:
                pass
            self._watchdog = None
        if self.conn:
            await self.conn.close()

    async def _watch(self) -> None:
        while not self._stop.is_set():
            await asyncio.sleep(self.LIVENESS_TIMEOUT)
            if time.monotonic() - self._last_msg > self.LIVENESS_TIMEOUT:
                logger.warning("WS stale, reconnecting")
                if self.conn:
                    await self.conn.close()

