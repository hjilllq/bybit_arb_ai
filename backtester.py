from __future__ import annotations
import argparse, csv
from decimal import Decimal
from pathlib import Path
from typing import Iterable

import config
from strategy_multi import ArbitrageStrategyMulti
from api_client import APIClient

class CsvData:
    """Iterate over historical price data from CSV."""

    def __init__(self, path: Path):
        self.path = path

    def __iter__(self) -> Iterable[tuple[str, Decimal, Decimal]]:
        with self.path.open() as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield row["symbol"], Decimal(row["bid"]), Decimal(row["ask"])

async def backtest(data: CsvData):
    async with APIClient() as client:
        strat = ArbitrageStrategyMulti(client)
        pnl = {s: Decimal() for s in config.TRADE_PAIRS}
        for sym, bid, ask in data:
            client.ws.best[sym] = (bid, ask)
            action, edge = await strat.analyze(sym)
            if action == "buy_spot":
                pnl[sym] -= ask
            elif action == "sell_spot":
                pnl[sym] += bid
        for sym, p in pnl.items():
            print(sym, "PNL", p)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Offline backtesting")
    ap.add_argument("csv", type=Path, help="CSV with symbol,bid,ask")
    args = ap.parse_args()
    import asyncio
    asyncio.run(backtest(CsvData(args.csv)))

