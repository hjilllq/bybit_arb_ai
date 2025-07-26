# Bybit Spot <-> Perp Arbitrage Bot

This project implements an automated arbitrage trading system for Bybit. It streams orderbook data via WebSockets, applies reinforcement learning to estimate profitable edges and executes trades with a REST API client.

## Requirements

```bash
pip install -r requirements.txt
```

## Usage

Edit `.env` with your API keys and run:

```bash
python run_trading_system.py
```

Prometheus metrics will be served on `PROM_HOST:PROM_PORT`.

Trained RL policies are saved in `policies/` and automatically reloaded on
startup. WebSocket reconnects are counted by a Prometheus metric
`ws_reconnect_total`.
The counter `risk_violation_total` increments whenever the risk manager stops
trading due to excessive losses.

Set `MAX_DRAWDOWN_USD` to stop the bot if cumulative realized and unrealized
losses exceed this threshold. Use `MAX_POSITION_USD` to limit the size of any
single position. Alerts will be sent via email or Telegram if configured.
`MAX_RELATIVE_DRAWDOWN_USD` stops trading once the total PnL drops this amount
from its peak value during the session.
`ACCOUNT_EQUITY_USD` defines starting capital, `RISK_PER_TRADE` controls
position size based on volatility, `DAILY_DRAWDOWN_USD` and
`MAX_CONSECUTIVE_LOSSES` provide additional capital protection.
`PARALLEL_TASKS` sets how many concurrent loops run for each trading pair
(defaults to 4).
`TRADE_COOLDOWN_SEC` enforces a minimum delay between trades in the same symbol
to prevent overtrading (defaults to 0.5 seconds).
`ERROR_LIMIT` sets how many errors may occur within a minute before the bot
terminates to protect capital (defaults to 5).
`MAX_DAILY_TRADES` limits how many trades can be executed per symbol each day
before further trading is paused (defaults to 200).

Executed trades are appended to `logs/trades.csv` for later analysis. Each
row records timestamp, symbol, side, quantity, executed price, edge and
slippage.

Bot state (positions, entry prices and PnL) is saved to `logs/state.json`
every few seconds so trading can resume from the last known state after
restart.
On startup the bot also queries the exchange to synchronise open positions
so local state reflects reality even after downtime.

### Offline Backtesting

Historical quotes in CSV format can be used to test strategies without
connecting to the exchange. Each row should contain `symbol`, `bid` and `ask`
columns.

```bash
python backtester.py data.csv
```

