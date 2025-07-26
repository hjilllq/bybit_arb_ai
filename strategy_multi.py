from __future__ import annotations
import logging
from decimal import Decimal
from typing import Tuple
import config

logger = logging.getLogger(__name__)

class ArbitrageStrategyMulti:
    """Simplified strategy without external ML dependencies."""

    def __init__(self, client: "APIClient") -> None:  # noqa: F821
        self.client = client

    async def analyze(self, sym: str) -> Tuple[str, Decimal]:
        bid, ask = await self.client.get_best(sym)
        edge = (bid - ask) / ask - config.SPOT_FEE_RATE - config.FUTURES_FEE_TAKER
        if edge > Decimal("0"):
            action = "buy_spot"
        elif edge < Decimal("0"):
            action = "sell_spot"
        else:
            action = "hold"
        return action, edge
