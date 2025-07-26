from __future__ import annotations
import os, signal, time
from collections import deque
from decimal import Decimal
from typing import Dict
import numpy as np
import config
from alert_utils import ALERTS

class CapitalManager:
    """Advanced capital management with dynamic position sizing"""
    def __init__(self, bot: "TradingBotMulti") -> None:  # noqa: F821
        self.bot = bot
        self.start_equity = config.ACCOUNT_EQUITY_USD
        self.equity = self.start_equity
        self.daily_start = time.time()
        self.daily_loss = Decimal()
        self.consecutive_losses = 0
        self.history: Dict[str, deque[Decimal]] = {
            s: deque(maxlen=config.VOL_WINDOW) for s in config.TRADE_PAIRS
        }

    def record_price(self, sym: str, price: Decimal) -> None:
        self.history[sym].append(price)

    def _volatility(self, sym: str) -> Decimal:
        hist = self.history[sym]
        if len(hist) < 2:
            return Decimal("0")
        arr = np.array([float(x) for x in hist])
        rets = np.diff(arr) / arr[:-1]
        return Decimal(str(np.std(rets)))

    def calc_stop_distance(self, sym: str, price: Decimal) -> Decimal:
        vol = self._volatility(sym)
        if not vol:
            vol = Decimal("0.002")  # fallback 0.2%
        return price * vol * config.STOP_MULTIPLIER

    def calc_order_qty(self, sym: str, price: Decimal) -> Decimal:
        risk_cap = self.equity * config.RISK_PER_TRADE
        stop = self.calc_stop_distance(sym, price)
        if stop <= 0:
            return Decimal()
        qty = risk_cap / stop
        max_qty = config.MAX_POSITION_USD / price
        qty = min(qty, max_qty)
        return qty.quantize(Decimal("0.0001"))

    def update_equity(self) -> None:
        total = sum(self.bot.real.values()) + sum(self.bot.unreal.values())
        new_eq = self.start_equity + total
        change = new_eq - self.equity
        if change < 0:
            self.consecutive_losses += 1
            self.daily_loss -= change
        else:
            self.consecutive_losses = 0
        self.equity = new_eq
        self._check_day_reset()
        self._enforce_limits()

    def _check_day_reset(self) -> None:
        if time.time() - self.daily_start > 86400:
            self.daily_start = time.time()
            self.daily_loss = Decimal()
            self.consecutive_losses = 0

    def _enforce_limits(self) -> None:
        if (
            self.daily_loss >= config.DAILY_DRAWDOWN_USD
            or self.consecutive_losses >= config.MAX_CONSECUTIVE_LOSSES
        ):
            ALERTS.error("Capital limits reached, stopping bot")
            os.kill(os.getpid(), signal.SIGTERM)

