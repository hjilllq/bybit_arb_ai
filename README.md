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

Set `MAX_DRAWDOWN_USD` to stop the bot if cumulative realized and unrealized
losses exceed this threshold. Use `MAX_POSITION_USD` to limit the size of any
single position. Alerts will be sent via email or Telegram if configured.

Executed trades are appended to `logs/trades.csv` for later analysis. Each
row records timestamp, symbol, side, quantity, executed price, edge and
slippage.

### Offline Backtesting

Historical quotes in CSV format can be used to test strategies without
connecting to the exchange. Each row should contain `symbol`, `bid` and `ask`
columns.

```bash
python backtester.py data.csv
```

