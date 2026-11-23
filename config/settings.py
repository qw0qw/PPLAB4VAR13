"""Настройки приложения и их проверка."""

import os
from urllib.parse import urlsplit

from dotenv import load_dotenv

from config.urls import FACT_API_BASE_URL
from exceptions import ConfigError

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

CATEGORIES: tuple[str, ...] = ("math", "date", "year", "trivia")
CATEGORY_LABELS: dict[str, str] = {
    "math": "Math",
    "date": "Dates",
    "year": "Years",
    "trivia": "Random trivia",
}

API_CONNECT_TIMEOUT = 3.0
API_READ_TIMEOUT = 5.0
API_MAX_RETRIES = 2
API_MAX_RETRY_AFTER = 5.0
MAX_FAV_CATEGORIES = 3
MIN_FAV_CATEGORIES = 1


def _read_float(name: str, default: float) -> float:
    """Читает числовую настройку из окружения."""
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError as exc:
        raise ConfigError(f"Invalid {name} value.") from exc
    if value <= 0:
        raise ConfigError(f"{name} must be greater than zero.")
    return value


def _read_int(name: str, default: int) -> int:
    """Читает целочисленную настройку из окружения."""
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError as exc:
        raise ConfigError(f"Invalid {name} value.") from exc
    if value < 0:
        raise ConfigError(f"{name} cannot be negative.")
    return value


API_CONNECT_TIMEOUT = _read_float("API_CONNECT_TIMEOUT", API_CONNECT_TIMEOUT)
API_READ_TIMEOUT = _read_float("API_READ_TIMEOUT", API_READ_TIMEOUT)
API_MAX_RETRIES = _read_int("API_MAX_RETRIES", API_MAX_RETRIES)
API_MAX_RETRY_AFTER = _read_float(
    "API_MAX_RETRY_AFTER",
    API_MAX_RETRY_AFTER,
)


def validate_settings() -> None:
    """Проверяет обязательные настройки перед запуском бота."""
    if not BOT_TOKEN:
        raise ConfigError(
            "BOT_TOKEN was not found. Add it to the .env file."
        )
    if urlsplit(FACT_API_BASE_URL).scheme not in {"http", "https"}:
        raise ConfigError("FACT_API_BASE_URL must use HTTP or HTTPS.")
    if not CATEGORIES:
        raise ConfigError("At least one category must be configured.")
    if MIN_FAV_CATEGORIES > MAX_FAV_CATEGORIES:
        raise ConfigError("Invalid favorite category limits.")
