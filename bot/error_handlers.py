"""Глобальная обработка необработанных ошибок aiogram."""

import logging
import sys

from aiogram import Router
from aiogram.exceptions import TelegramConflictError
from aiogram.types import ErrorEvent

from exceptions import AppError

logger = logging.getLogger(__name__)
router = Router()


@router.errors()
async def global_error_handler(event: ErrorEvent) -> bool:
    """Логирует ошибку и, если возможно, сообщает о ней пользователю."""
    error = event.exception
    try:
        raise error
    except TelegramConflictError:
        logger.exception("Another bot instance is already polling.")
        sys.exit(1)
    except AppError as exc:
        logger.exception("Application error: %s", exc)
        user_message = exc.user_message
    except Exception:
        logger.exception("Unhandled bot error.")
        user_message = AppError.user_message

    update = event.update
    message = update.message
    if message is None and update.callback_query is not None:
        message = update.callback_query.message

    if message is not None:
        try:
            await message.answer(user_message)
        except Exception:
            logger.exception("Could not send error message to the user.")
    return True
