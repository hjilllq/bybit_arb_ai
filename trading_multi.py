from __future__ import annotations
import asyncio, logging, time
from decimal import Decimal
from typing import Dict
import config
from api_client import APIClient
from alert_utils import ALERTS
from monitoring import (CYCLE_LATENCY_MS, ORDERS_ACTIVE, PNL_TOTAL, PNL_UNREAL,
                        POSITION_SIZE, TRADING_EDGE)
from rebalancer import smart_rebalance
from slippage_sim import SlippageSimulator
from strategy_multi import ArbitrageStrategyMulti

logger = logging.getLogger(__name__)

class TradingBotMulti:
    SLIP_TOL = Decimal("0.60")
    def __init__(self):
        self.client = APIClient()
        self.sim = SlippageSimulator(self.client)
        self.strategy = ArbitrageStrategyMulti(self.client)
        self.position: Dict[str, Decimal] = {s: Decimal() for s in config.TRADE_PAIRS}
        self.entry: Dict[str, Decimal | None] = {s: None for s in config.TRADE_PAIRS}
        self.real: Dict[str, Decimal] = {s: Decimal() for s in config.TRADE_PAIRS}

    async def run(self):
        await self.client.start()
        asyncio.create_task(ALERTS.watch_errors())
        asyncio.create_task(ALERTS.watch_inactivity())
        asyncio.create_task(smart_rebalance(self.client, self))
        tasks = [asyncio.create_task(self._loop(s)) for s in config.TRADE_PAIRS]
        await asyncio.gather(*tasks)

    async def _loop(self, sym: str):
        while True:
            t0 = time.perf_counter()
            action, edge = await self.strategy.analyze(sym)
            TRADING_EDGE.labels(sym=sym).set(float(edge))
            if edge >= config.MIN_FUNDING_THRESHOLD:
                await self._trade(sym, action, edge)
            await self._update_pnl(sym)
            latency = (time.perf_counter() - t0)*1000
            CYCLE_LATENCY_MS.labels(sym=sym).set(latency)
            await asyncio.sleep(max(0, 0.05 - latency/1000))  # 50 мс такт

    async def _trade(self, sym: str, action: str, edge: Decimal):
        if action == "hold": return
        bid, ask = await self.client.get_best(sym)
        price = ask if action == "buy_spot" else bid
        side  = "Buy" if action == "buy_spot" else "Sell"
        qty   = self._calc_qty(price)
        worst = await self.sim.worst_price(sym, side, qty)
        slip  = abs((worst-price)/price)
        if slip > self.SLIP_TOL * edge: return  # проскальзывание велико
        await self.client.place_order(sym, side, qty)
        ORDERS_ACTIVE.labels(sym=sym).set(1)
        delta = qty if side == "Buy" else -qty
        if not self.entry[sym]: self.entry[sym] = price
        self.position[sym] += delta
        POSITION_SIZE.labels(sym=sym).set(float(self.position[sym]))
        ALERTS.trade_executed()

    def _calc_qty(self, price: Decimal) -> Decimal:
        trade_val = Decimal("1")*config.MAX_POSITION_PERCENT*config.LEVERAGE
        return (trade_val/price).quantize(Decimal("0.0001"))

    async def _update_pnl(self, sym: str):
        bid, ask = await self.client.get_best(sym)
        mark = bid if self.position[sym] < 0 else ask
        if self.position[sym] and self.entry[sym]:
            unreal = (mark - self.entry[sym]) * self.position[sym]
            PNL_UNREAL.labels(sym=sym).set(float(unreal))
        PNL_TOTAL.labels(sym=sym).set(float(self.real[sym]))

    async def close(self): await self.client.close()