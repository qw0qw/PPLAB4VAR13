"""Обработчики команд и callback-запросов Telegram-бота."""

import asyncio
import logging
import random

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.keyboards import get_themes_keyboard
from config.settings import (
    CATEGORY_LABELS,
    MAX_FAV_CATEGORIES,
    MIN_FAV_CATEGORIES,
)
from core.fact_provider import get_fact
from database.db import get_favorite_themes, set_favorite_themes
from exceptions import AppError

logger = logging.getLogger(__name__)
router = Router()
temp_selections: dict[int, list[str]] = {}


async def get_fact_text(category: str) -> str:
    """Получает факт в отдельном потоке, не блокируя event loop."""
    try:
        return await asyncio.to_thread(get_fact, category)
    except AppError as exc:
        logger.exception("Could not get fact for category %s", category)
        return exc.user_message


@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    """Показывает приветствие и список команд."""
    text = (
        "Hello! I am a random facts bot.\n\n"
        "Available commands:\n"
        "/fact — get a random fact\n"
        "/theme_fact — get a fact by category\n"
        "/fav — manage favorite categories\n"
        "/fav_fact — get a fact from your favorites"
    )
    await message.answer(text)


@router.message(Command("fact"))
async def fact_handler(message: Message) -> None:
    """Отправляет случайный факт общей категории."""
    await message.answer(await get_fact_text("trivia"))


@router.message(Command("theme_fact"))
async def theme_fact_handler(message: Message) -> None:
    """Предлагает пользователю выбрать категорию факта."""
    await message.answer(
        "Choose a category:",
        reply_markup=get_themes_keyboard("theme"),
    )


@router.callback_query(
    lambda callback: bool(callback.data)
    and callback.data.startswith("theme_")
)
async def theme_callback_handler(callback: CallbackQuery) -> None:
    """Обрабатывает выбор категории факта."""
    category = callback.data.removeprefix("theme_")
    if category not in CATEGORY_LABELS:
        await callback.answer("Unknown category.", show_alert=True)
        return

    fact = await get_fact_text(category)
    if callback.message:
        await callback.message.edit_text(fact)
    await callback.answer()


@router.message(Command("fav"))
async def favorite_handler(message: Message) -> None:
    """Открывает меню выбора избранных категорий."""
    user_id = message.from_user.id
    try:
        current = await asyncio.to_thread(get_favorite_themes, user_id)
        temp_selections[user_id] = current.copy()
        await message.answer(
            "Choose from 1 to 3 favorite categories:",
            reply_markup=get_themes_keyboard("fav", current),
        )
    except AppError as exc:
        logger.exception("Could not load favorite categories")
        await message.answer(exc.user_message)
    except Exception:
        logger.exception("Unexpected error loading favorite categories")
        await message.answer("Could not open favorite settings.")


@router.callback_query(
    lambda callback: bool(callback.data)
    and callback.data.startswith("fav_")
    and callback.data != "fav_save"
)
async def favorite_theme_callback_handler(callback: CallbackQuery) -> None:
    """Изменяет временный список избранных категорий."""
    user_id = callback.from_user.id
    category = callback.data.removeprefix("fav_")

    if category not in CATEGORY_LABELS:
        await callback.answer("Unknown category.", show_alert=True)
        return

    selected = temp_selections.setdefault(user_id, ["trivia"])
    if category in selected:
        if len(selected) <= MIN_FAV_CATEGORIES:
            await callback.answer("You must keep at least one category.")
            return
        selected.remove(category)
    else:
        if len(selected) >= MAX_FAV_CATEGORIES:
            await callback.answer("You can select no more than three categories.")
            return
        selected.append(category)

    if callback.message:
        await callback.message.edit_reply_markup(
            reply_markup=get_themes_keyboard("fav", selected)
        )
    await callback.answer()


@router.callback_query(lambda callback: callback.data == "fav_save")
async def favorite_save_callback_handler(callback: CallbackQuery) -> None:
    """Сохраняет выбранные категории в SQLite."""
    user_id = callback.from_user.id
    selected = temp_selections.get(user_id, ["trivia"])
    try:
        await asyncio.to_thread(set_favorite_themes, user_id, selected)
        temp_selections.pop(user_id, None)
        if callback.message:
            await callback.message.edit_text("Favorite categories saved.")
        await callback.answer("Saved.")
    except AppError as exc:
        logger.exception("Could not save favorite categories")
        await callback.answer(exc.user_message, show_alert=True)
    except Exception:
        logger.exception("Unexpected error saving favorite categories")
        await callback.answer("Could not save your selection.", show_alert=True)


@router.message(Command("fav_fact"))
async def favorite_fact_handler(message: Message) -> None:
    """Выбирает случайную избранную категорию и отправляет факт."""
    try:
        themes = await asyncio.to_thread(
            get_favorite_themes,
            message.from_user.id,
        )
        themes = [theme for theme in themes if theme in CATEGORY_LABELS]
        if not themes:
            themes = ["trivia"]
        category = random.choice(themes)
        await message.answer(await get_fact_text(category))
    except AppError as exc:
        logger.exception("Could not get a fact from favorites")
        await message.answer(exc.user_message)
    except Exception:
        logger.exception("Unexpected error getting a fact from favorites")
        await message.answer("Could not get a fact. Please try again later.")
