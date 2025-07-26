from __future__ import annotations
import asyncio, logging, time, uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Tuple
import config
from ws_manager import WSManager

logger = logging.getLogger(__name__)


@dataclass
class Order:
    id: str
    symbol: str
    side: str
    qty: Decimal
    price: Decimal
    ts: float

class _Limiter:
    def __init__(self, rps: int = 60) -> None:
        self.rps = rps; self.calls: list[float] = []

    async def wait(self):
        now = time.perf_counter()
        self.calls = [t for t in self.calls if now - t < 1]
        if len(self.calls) >= self.rps:
            await asyncio.sleep(1 - (now - self.calls[0]))
        self.calls.append(time.perf_counter())

class APIClient:
    """Минимальный клиент Bybit для офлайн-демо."""

    PUB = _Limiter(150)
    PRI = _Limiter(60)

    def __init__(self) -> None:
        self.ws = WSManager(self)
        self.position: Dict[str, Decimal] = {s: Decimal() for s in config.TRADE_PAIRS}
        self.orders: List[Order] = []

    async def _call(self, m: str, path: str, params=None, private=False):
        logger.debug("API call %s %s %s", m, path, params)
        await asyncio.sleep(0)  # simulate latency
        return {}

    # публичные обёртки
    async def get_server_time_ms(self) -> int:
        return int(time.time() * 1000)

    async def get_best(self, sym: str) -> Tuple[Decimal, Decimal]:
        bid, ask = await self.ws.get_best(sym)
        return Decimal(str(bid)), Decimal(str(ask))

    async def place_order(self, sym: str, side: str, qty: Decimal, order_type="Market"):
        bid, ask = await self.get_best(sym)
        price = ask if side == "Buy" else bid
        delta = qty if side == "Buy" else -qty
        self.position[sym] += delta
        order = Order(str(uuid.uuid4()), sym, side, qty, price, time.time())
        self.orders.append(order)
        logger.info("Executed %s %s %.6f at %s", sym, side, qty, price)
        await self._call("POST", "/v5/order/create", {})
        return {"status": "ok", "price": price}

    async def restore_positions(self):
        return self.position.copy()

    def get_orders(self) -> List[Order]:
        return list(self.orders)

    def clear_orders(self) -> None:
        self.orders.clear()

    async def start(self):
        await self.ws.start()

    async def close(self):
        await self.ws.close()
