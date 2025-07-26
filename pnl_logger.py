from __future__ import annotations
import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import config

class PNLLogger:
    """Append PnL snapshots to a CSV file."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or config.PNL_LOG
        if not self.path.exists():
            self.path.write_text("timestamp,symbol,real,unreal,equity\n")

    def log(self, sym: str, real: Decimal, unreal: Decimal, equity: Decimal) -> None:
        with self.path.open("a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.utcnow().isoformat(timespec="seconds"),
                sym,
                f"{real}",
                f"{unreal}",
                f"{equity}",
            ])

