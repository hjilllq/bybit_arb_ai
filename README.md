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
If no quotes are received for `LIVENESS_TIMEOUT` seconds the WebSocket
connection is restarted automatically.
The counter `risk_violation_total` increments whenever the risk manager stops
trading due to excessive losses.

Set `MAX_DRAWDOWN_USD` to stop the bot if cumulative realized and unrealized
losses exceed this threshold. Use `MAX_POSITION_USD` to limit the size of any
single position. `MAX_EXPOSURE_USD` caps the sum of all open positions across
symbols. Alerts will be sent via email or Telegram if configured.
`MAX_RELATIVE_DRAWDOWN_USD` stops trading once the total PnL drops this amount
from its peak value during the session. The bot persists this peak across
restarts so relative drawdown protection remains effective after a crash or
manual stop.
`MAX_SYMBOL_DRAWDOWN_USD` limits the loss allowed per individual symbol. When
realized plus unrealized PnL for any trading pair falls below the negative
threshold the bot shuts down to avoid overexposure to a single market.
`MAX_SYMBOL_REL_DRAWDOWN_USD` sets a trailing loss limit per symbol. If the
unrealized plus realized PnL drops this amount from the peak for any instrument,
trading stops to protect profits.
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
`MAX_PROFIT_USD` stops trading once total profit exceeds this amount for the
current session (set to 0 to disable).
`STATE_FILE` defines where bot state is saved and `STATE_BACKUP_FILE` holds the
previous snapshot used for recovery if the main file gets corrupted.
`STATE_SAVE_SEC` controls how often the state file is updated (defaults to 5
seconds).
`PNL_LOG` specifies the CSV file used to track ongoing profit and loss.
`WS_LIVENESS_TIMEOUT` defines how long the bot waits for WebSocket updates
before forcing a reconnect (defaults to 30 seconds).

Executed trades are appended to `logs/trades.csv` for later analysis. Each
row records timestamp, symbol, side, quantity, executed price, edge and
slippage.

Periodically the bot also records current profit and loss to `logs/pnl.csv`
with columns `timestamp`, `symbol`, `real`, `unreal` and `equity` so you can
track performance over time.

Bot state (positions, entry prices and PnL) is saved to `logs/state.json`
every few seconds so trading can resume from the last known state after
restart. If this file becomes corrupted the bot automatically loads the
backup `logs/state.bak.json` with the previous snapshot.
On startup the bot also queries the exchange to synchronise open positions
so local state reflects reality even after downtime.
If risk limits trigger, the bot gracefully closes positions before shutting down.

### Offline Backtesting

Historical quotes in CSV format can be used to test strategies without
connecting to the exchange. Each row should contain `symbol`, `bid` and `ask`
columns.

```bash
python backtester.py data.csv
```

