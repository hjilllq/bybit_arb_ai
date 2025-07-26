from __future__ import annotations
import asyncio, logging, time
from decimal import Decimal
from typing import Dict
import config
from api_client import APIClient
from position_sync import sync_positions
from alert_utils import ALERTS
from monitoring import (CYCLE_LATENCY_MS, ORDERS_ACTIVE, PNL_TOTAL, PNL_UNREAL,
                        POSITION_SIZE, TRADING_EDGE)
from rebalancer import smart_rebalance
from slippage_sim import SlippageSimulator
from strategy_multi import ArbitrageStrategyMulti
from trade_logger import TradeLogger
from capital_manager import CapitalManager
from state_persistence import load_state, save_state

logger = logging.getLogger(__name__)

class TradingBotMulti:
    SLIP_TOL = Decimal("0.60")
    def __init__(self, client: APIClient | None = None):
        if client is not None:
            self.client = client
        else:
            try:
                self.client = APIClient()
            except Exception:
                self.client = None
        self.sim = SlippageSimulator(self.client)
        self.strategy = ArbitrageStrategyMulti(self.client)
        self.tlog = TradeLogger()
        self.capital = CapitalManager(self)
        self.position: Dict[str, Decimal] = {s: Decimal() for s in config.TRADE_PAIRS}
        self.entry: Dict[str, Decimal | None] = {s: None for s in config.TRADE_PAIRS}
        self.real: Dict[str, Decimal] = {s: Decimal() for s in config.TRADE_PAIRS}
        self.unreal: Dict[str, Decimal] = {s: Decimal() for s in config.TRADE_PAIRS}
        self._last_persist = time.time()
        self._lock: Dict[str, asyncio.Lock] = {s: asyncio.Lock() for s in config.TRADE_PAIRS}
        self._last_trade: Dict[str, float] = {s: 0.0 for s in config.TRADE_PAIRS}
        self._load_state()

    async def run(self):
        await self.client.start()
        await sync_positions(self, self.client)
        asyncio.create_task(ALERTS.watch_errors())
        asyncio.create_task(ALERTS.watch_inactivity())
        asyncio.create_task(smart_rebalance(self.client, self))
        tasks = []
        for sym in config.TRADE_PAIRS:
            for _ in range(config.PARALLEL_TASKS):
                tasks.append(asyncio.create_task(self._loop(sym)))
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
        if action == "hold":
            return
        now = time.time()
        if now - self._last_trade[sym] < config.TRADE_COOLDOWN_SEC:
            logger.debug("Skip trade: %s cooldown", sym)
            return
        async with self._lock[sym]:
            bid, ask = await self.client.get_best(sym)
            price = ask if action == "buy_spot" else bid
            side  = "Buy" if action == "buy_spot" else "Sell"
            if abs(self.position[sym] * price) >= config.MAX_POSITION_USD:
                logger.debug("Skip trade: %s position limit", sym)
                return
            qty   = self._calc_qty(sym, price)
            worst = await self.sim.worst_price(sym, side, qty)
            slip  = abs((worst-price)/price)
            if slip > self.SLIP_TOL * edge: return  # проскальзывание велико
            await self.client.place_order(sym, side, qty)
            self._last_trade[sym] = now
            self.tlog.log(sym, side, qty, price, edge, slip)
            ORDERS_ACTIVE.labels(sym=sym).set(1)
            delta = qty if side == "Buy" else -qty
            prev = self.position[sym]
            new_pos = prev + delta
            if prev == 0:
                self.entry[sym] = price
            elif (prev > 0 and delta > 0) or (prev < 0 and delta < 0):
                tot = abs(prev) + abs(delta)
                self.entry[sym] = (
                    (self.entry[sym] or price) * abs(prev) + price * abs(delta)
                ) / tot
            else:
                close_qty = min(abs(prev), abs(delta))
                entry = self.entry[sym] or price
                pnl = (price - entry) * close_qty if prev > 0 else (entry - price) * close_qty
                self.real[sym] += pnl
                if abs(delta) > abs(prev):
                    self.entry[sym] = price
                elif abs(delta) == abs(prev):
                    self.entry[sym] = None
            self.position[sym] = new_pos
            POSITION_SIZE.labels(sym=sym).set(float(self.position[sym]))
            ALERTS.trade_executed()
            self._maybe_persist()

    def _calc_qty(self, sym: str, price: Decimal) -> Decimal:
        return self.capital.calc_order_qty(sym, price)

    async def _update_pnl(self, sym: str):
        async with self._lock[sym]:
            bid, ask = await self.client.get_best(sym)
            self.capital.record_price(sym, (bid + ask) / 2)
            mark = bid if self.position[sym] < 0 else ask
            if self.position[sym] and self.entry[sym]:
                unreal = (mark - self.entry[sym]) * self.position[sym]
                self.unreal[sym] = unreal
                PNL_UNREAL.labels(sym=sym).set(float(unreal))
            else:
                self.unreal[sym] = Decimal()
            PNL_TOTAL.labels(sym=sym).set(float(self.real[sym]))
            self.capital.update_equity()
            self._maybe_persist()

    async def close(self): await self.client.close()

    # --- persistence -----------------------------------------------------
    def _maybe_persist(self) -> None:
        if time.time() - self._last_persist > 5:
            self._persist_state()
            self._last_persist = time.time()

    def _persist_state(self) -> None:
        save_state(
            {
                "position": self.position,
                "entry": self.entry,
                "real": self.real,
                "unreal": self.unreal,
            }
        )

    def _load_state(self) -> None:
        data = load_state()
        if not data:
            return
        self.position.update(data.get("position", {}))
        self.entry.update(data.get("entry", {}))
        self.real.update(data.get("real", {}))
        self.unreal.update(data.get("unreal", {}))

