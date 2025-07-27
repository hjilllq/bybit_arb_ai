import csv
from decimal import Decimal
from pathlib import Path
import tempfile
import sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pnl_logger import PNLLogger


def test_pnl_logger_writes_row():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "pnl.csv"
        logger = PNLLogger(path)
        logger.log("BTCUSDT", Decimal("1"), Decimal("0.5"), Decimal("10000"))
        with path.open() as f:
            rows = list(csv.reader(f))
    assert rows[0] == ["timestamp", "symbol", "real", "unreal", "equity"]
    assert rows[1][1:4] == ["BTCUSDT", "1", "0.5"]
