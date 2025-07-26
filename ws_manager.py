from __future__ import annotations
import asyncio, logging, random
from decimal import Decimal
from typing import Dict, Tuple
import config

logger = logging.getLogger(__name__)

class WSManager:
    """Simple in-memory price simulator replacing real WebSocket connection."""

    def __init__(self, client: "APIClient") -> None:  # noqa: F821
        self.client = client
        self._prices: Dict[str, Tuple[Decimal, Decimal]] = {
            sym: (Decimal("100"), Decimal("100.5")) for sym in config.TRADE_PAIRS
        }
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._simulate())

    async def _simulate(self) -> None:
        while self._running:
            for sym, (bid, ask) in self._prices.items():
                delta = Decimal(str(random.uniform(-0.5, 0.5)))
                bid = (bid + delta).quantize(Decimal("0.01"))
                ask = (bid + Decimal("0.5")).quantize(Decimal("0.01"))
                self._prices[sym] = (bid, ask)
            await asyncio.sleep(0.5)

    async def get_best(self, sym: str) -> Tuple[Decimal, Decimal]:
        return self._prices.get(sym, (Decimal("0"), Decimal("0")))

    async def close(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
