"""Точка входа Telegram-бота."""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramConflictError

from bot.error_handlers import router as error_router
from bot.handlers import router as handlers_router
from config.settings import BOT_TOKEN, validate_settings
from database.db import close_db, init_db
from exceptions import AppError

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    """Настраивает формат и уровень журналирования."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


async def main() -> None:
    """Проверяет настройки и запускает polling Telegram-бота."""
    configure_logging()
    try:
        validate_settings()
        init_db()
    except AppError:
        logger.exception("Application startup failed.")
        raise SystemExit(1)

    bot = Bot(token=BOT_TOKEN)
    dispatcher = Dispatcher()
    dispatcher.include_router(handlers_router)
    dispatcher.include_router(error_router)

    try:
        await dispatcher.start_polling(bot)
    except TelegramConflictError:
        logger.exception("Bot is already running in another instance.")
        raise SystemExit(1)
    finally:
        await bot.session.close()
        close_db()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    configure_logging()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopped by user")
        sys.exit(0)
