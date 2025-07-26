from __future__ import annotations
import logging
from decimal import Decimal
from typing import Literal
from retry_utils import retry_async

logger = logging.getLogger(__name__)

class SlippageSimulator:
    DEPTH = 25
    def __init__(self, client: "APIClient"):  # noqa: F821
        self.client = client
    async def worst_price(self, sym: str, side: Literal["Buy", "Sell"], qty: Decimal) -> Decimal:
        bid, ask = await self.client.get_best(sym)
        base = ask if side == "Buy" else bid
        slip = Decimal("0.01") * qty
        return (base + slip) if side == "Buy" else (base - slip)
