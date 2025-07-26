import csv
from decimal import Decimal
from pathlib import Path
import tempfile
import sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from trade_logger import TradeLogger


def test_trade_logger_writes_row():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "trades.csv"
        logger = TradeLogger(path)
        logger.log("BTCUSDT", "Buy", Decimal("1"), Decimal("100"), Decimal("0.1"), Decimal("0"))
        with path.open() as f:
            rows = list(csv.reader(f))
    assert rows[0] == ["timestamp", "symbol", "side", "qty", "price", "edge", "slip"]
    assert rows[1][1:4] == ["BTCUSDT", "Buy", "1"]
