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
        ob = await retry_async(
            lambda: self.client._call("GET", "/v5/market/orderbook",
                                      {"symbol": sym, "category": "linear", "limit": self.DEPTH})
        )
        ladder = ob["a"] if side == "Buy" else ob["b"]
        remain = qty; worst = Decimal(ladder[-1][0])
        for price_str, size_str in ladder:
            price, size = Decimal(price_str), Decimal(size_str)
            worst = price
            if remain <= size:
                break
            remain -= size
        return worst