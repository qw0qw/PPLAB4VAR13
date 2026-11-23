"""Служебный скрипт для ручной проверки подключения к Telegram API. Не используется в рантайме бота."""

import asyncio
import logging

import aiohttp

from config.urls import TELEGRAM_API_BASE_URL

logger = logging.getLogger(__name__)


async def main() -> None:
    """Проверяет доступность Telegram API."""
    timeout = aiohttp.ClientTimeout(total=5)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(TELEGRAM_API_BASE_URL) as response:
            logger.info("Telegram API HTTP status: %s", response.status)


if __name__ == "__main__":
    asyncio.run(main())
