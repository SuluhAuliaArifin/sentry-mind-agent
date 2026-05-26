"""Telegram alert sender. No-op when token/chat not configured."""
from __future__ import annotations
import logging
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def send_alert(text: str) -> tuple[bool, str]:
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return False, "telegram not configured"
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(url, json={
                "chat_id": settings.telegram_chat_id,
                "text": text[:3500],
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            })
            if r.status_code == 200:
                return True, "sent"
            return False, f"http_{r.status_code}: {r.text[:200]}"
    except httpx.HTTPError as e:
        logger.warning("telegram error: %s", e)
        return False, str(e)
