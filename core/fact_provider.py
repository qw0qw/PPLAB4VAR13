"""Выбор источника факта: внешний API или локальный резерв."""

import logging
from typing import Any

from config.settings import CATEGORIES
from core import api_client, fallback_loader
from exceptions import FactAPIError, FactFallbackError

logger = logging.getLogger(__name__)


def _extract_text(payload: dict[str, Any]) -> str | None:
    """Извлекает непустой текст факта из JSON-ответа."""
    fact = payload.get("text")
    if isinstance(fact, str) and fact.strip():
        return fact.strip()
    return None


def get_fact(category: str) -> str:
    """Возвращает факт из API или локального резервного файла."""
    if category not in CATEGORIES:
        raise ValueError(f"Unknown fact category: {category}")

    try:
        payload = api_client.fetch_fact(category)
        fact = _extract_text(payload)
        if fact:
            return fact
        logger.warning("API returned an empty fact for category %s", category)
    except FactAPIError as exc:
        logger.warning("API unavailable for category %s: %s", category, exc)

    try:
        return fallback_loader.get_random_fallback(category)
    except FactFallbackError:
        logger.exception("Fallback source failed for category %s", category)
        raise
