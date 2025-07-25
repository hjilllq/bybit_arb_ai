from __future__ import annotations
import asyncio, logging, smtplib, time
from collections import deque
from email.message import EmailMessage
from typing import Deque, Optional
import aiohttp, config

logger = logging.getLogger(__name__)

class AlertCenter:
    TIME_WINDOW_SEC = 60
    INACTIVITY_MIN  = 5

    def __init__(self):
        self._errors: Deque[float] = deque()
        self._last_trade = time.time()
        self._email_on   = config.EMAIL_ENABLED
        self._tg_token   = config.TG_BOT_TOKEN
        self._tg_chat    = config.TG_CHAT_ID

    def trade_executed(self):
        self._last_trade = time.time()

    def error(self, msg: str):
        logger.error(msg)
        self._errors.append(time.time())

    async def watch_errors(self):
        last = 0.0
        while True:
            await asyncio.sleep(10)
            now = time.time()
            self._errors = deque(t for t in self._errors if now - t < self.TIME_WINDOW_SEC)
            if len(self._errors) >= 5 and now - last > 60:
                await self._send_alert("❗ Частые ошибки", f"За минуту {len(self._errors)} ошибок.")
                self._errors.clear()
                last = now

    async def watch_inactivity(self):
        while True:
            await asyncio.sleep(30)
            mins = (time.time() - self._last_trade) / 60
            if mins > self.INACTIVITY_MIN:
                await self._send_alert("⚠️ Нет сделок", f"Бот бездействует {mins:.1f} мин.")
                self._last_trade = time.time()

    # — отправка —
    async def _send_alert(self, title: str, body: str):
        logger.warning("ALERT: %s – %s", title, body)
        if self._email_on:
            self._send_email(title, body)
        if self._tg_token and self._tg_chat:
            await self._send_tg(body)

    def _send_email(self, subj: str, body: str):
        try:
            msg = EmailMessage()
            msg["Subject"] = subj
            msg["From"] = config.ALERT_EMAILS
            msg["To"] = config.ALERT_EMAILS
            msg.set_content(body)
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as s:
                s.starttls()
                s.login(config.EMAIL_SENDER, config.EMAIL_PASSWORD)
                s.send_message(msg)
        except Exception as exc:
            logger.warning("Email alert error: %s", exc)

    async def _send_tg(self, text: str):
        try:
            async with aiohttp.ClientSession() as sess:
                await sess.post(
                    f"https://api.telegram.org/bot{self._tg_token}/sendMessage",
                    json={"chat_id": self._tg_chat, "text": text},
                    timeout=5,
                )
        except Exception as exc:
            logger.warning("Telegram alert error: %s", exc)

ALERTS = AlertCenter()