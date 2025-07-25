from __future__ import annotations
import asyncio, hashlib, hmac, json, logging, time, uuid
from decimal import Decimal
from typing import Any, Dict, Tuple
import aiohttp, config
from retry_utils import retry_async
from ws_manager import WSManager

logger = logging.getLogger(__name__)

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
    PUB = _Limiter(150)
    PRI = _Limiter(60)

    def __init__(self):
        self.base, self.key, self.sec = (
            config.BYBIT_API_BASE_URL, config.API_KEY, config.API_SECRET.encode())
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2.))
        self.ws = WSManager(self)

    # подпись
    def _sign(self, params: Dict[str, Any]) -> Dict[str, Any]:
        ts = str(int(time.time() * 1000))
        params.update({"api_key": self.key, "timestamp": ts})
        query = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        params["sign"] = hmac.new(self.sec, query.encode(), hashlib.sha256).hexdigest()
        return params

    async def _call(self, m: str, path: str, params=None, private=False):
        url = f"{self.base}{path}"; params = params or {}
        lim = self.PRI if private else self.PUB

        async def _do():
            await lim.wait()
            payload = self._sign(params.copy()) if private else params
            async with self.session.request(
                m, url,
                params=payload if m == "GET" else None,
                json=payload if m == "POST" else None,
                headers={"User-Agent": "BybitArbBot/3.0"},
            ) as r:
                data = await r.json(loads=json.loads)
                if data.get("retCode"):
                    raise RuntimeError(f"Bybit {data['retCode']}: {data.get('retMsg')}")
                return data["result"]

        return await retry_async(_do)

    # публичные обёртки
    async def get_server_time_ms(self) -> int:
        res = await self._call("GET", "/v5/public/time")
        return int(res["timeSecond"] * 1000)

    async def get_best(self, sym: str) -> Tuple[Decimal, Decimal]:
        bid, ask = await self.ws.get_best(sym)
        return Decimal(str(bid)), Decimal(str(ask))

    async def place_order(self, sym: str, side: str, qty: Decimal, order_type="Market"):
        body = {
            "category": "linear", "symbol": sym,
            "side": side, "orderType": order_type, "qty": str(qty),
            "orderLinkId": f"arb-{uuid.uuid4().hex[:18]}",
            "timeInForce": "GoodTillCancel",
            "marginMode": config.MARGIN_MODE.title(),
        }
        return await self._call("POST", "/v5/order/create", body, private=True)

    async def restore_positions(self):
        res = await self._call("GET", "/v5/position/list",
                               {"category": "linear"}, private=True)
        out: Dict[str, Decimal] = {}
        for p in res["list"]:
            qty = Decimal(p["size"])
            if qty != 0:
                out[p["symbol"]] = qty * (1 if p["side"] == "Buy" else -1)
        return out

    async def start(self):
        await self.ws.start()

    async def close(self):
        await self.ws.close(); await self.session.close()