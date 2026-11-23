"""Создание inline-клавиатур бота."""

import logging

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config.settings import CATEGORY_LABELS

logger = logging.getLogger(__name__)


def get_themes_keyboard(
    prefix: str,
    selected_themes: list[str] | None = None,
) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру выбора категории или избранного."""
    if prefix not in {"theme", "fav"}:
        raise ValueError("Unknown keyboard prefix.")

    selected = selected_themes or []
    unknown = set(selected) - CATEGORY_LABELS.keys()
    if unknown:
        raise ValueError(f"Unknown categories: {sorted(unknown)}")

    buttons: list[list[InlineKeyboardButton]] = []
    for theme_key, theme_name in CATEGORY_LABELS.items():
        mark = "✅ " if theme_key in selected else ""
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{mark}{theme_name}",
                    callback_data=f"{prefix}_{theme_key}",
                )
            ]
        )

    if prefix == "fav":
        buttons.append(
            [
                InlineKeyboardButton(
                    text="💾 Save selection",
                    callback_data="fav_save",
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)
