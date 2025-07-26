from __future__ import annotations
import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import config

class TradeLogger:
    """Append executed trades to a CSV file."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or config.TRADE_LOG
        if not self.path.exists():
            self.path.write_text("timestamp,symbol,side,qty,price,edge,slip\n")

    def log(self, sym: str, side: str, qty: Decimal, price: Decimal,
            edge: Decimal, slip: Decimal) -> None:
        with self.path.open("a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.utcnow().isoformat(timespec="seconds"),
                sym,
                side,
                f"{qty}",
                f"{price}",
                f"{edge}",
                f"{slip}",
            ])

