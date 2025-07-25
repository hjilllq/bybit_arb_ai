from __future__ import annotations
import asyncio, logging, time
from http import HTTPStatus
from aiohttp import web
from prometheus_client import (
    CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest
)
import config

logger = logging.getLogger(__name__)

PNL_TOTAL        = Gauge("pnl_total",        "Realized PnL",              ["sym"])
PNL_UNREAL       = Gauge("pnl_unreal",       "Unrealized PnL",            ["sym"])
TRADING_EDGE     = Gauge("trading_edge",     "Edge before entry",         ["sym"])
CYCLE_LATENCY_MS = Gauge("cycle_latency_ms", "Loop latency ms",           ["sym"])
ORDERS_ACTIVE    = Gauge("orders_active",    "Active orders flag",        ["sym"])
POSITION_SIZE    = Gauge("position_size",    "Position size",             ["sym"])
ERROR_COUNTER    = Counter("error_total",    "Total errors",              ["type"])

async def metrics_handler(_: web.Request):
    return web.Response(body=generate_latest(), content_type=CONTENT_TYPE_LATEST)

async def health_handler(_: web.Request):
    return web.Response(status=HTTPStatus.OK, text="OK")

async def start_metrics_server():
    app = web.Application()
    app.add_routes([web.get("/metrics", metrics_handler), web.get("/health", health_handler)])
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, config.PROM_HOST, config.PROM_PORT).start()
    logger.info("Prometheus → http://%s:%s/metrics", config.PROM_HOST, config.PROM_PORT)

async def heartbeat():
    while True:
        POSITION_SIZE.labels(sym="heartbeat").set(time.time())
        await asyncio.sleep(15)