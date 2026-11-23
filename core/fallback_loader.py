"""Загрузка и выбор локальных резервных фактов."""

import json
import logging
import random
from pathlib import Path

from config.settings import CATEGORIES
from exceptions import FactFallbackError

logger = logging.getLogger(__name__)
FALLBACK_FILE = Path(__file__).with_name("fallback_facts.json")
_CACHE: dict[str, list[str]] | None = None


def load_fallback_facts() -> dict[str, list[str]]:
    """Загружает, проверяет и кэширует локальные факты."""
    global _CACHE
    if _CACHE is not None:
        return _CACHE

    try:
        with FALLBACK_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        raise FactFallbackError("Could not load fallback facts.") from exc

    if not isinstance(data, dict):
        raise FactFallbackError("Fallback data must be a JSON object.")

    validated: dict[str, list[str]] = {}
    for category, facts in data.items():
        if category not in CATEGORIES:
            raise FactFallbackError(f"Unknown fallback category: {category}")
        if (
            not isinstance(facts, list)
            or not facts
            or any(not isinstance(fact, str) or not fact.strip() for fact in facts)
        ):
            raise FactFallbackError(
                f"Fallback category {category} must contain non-empty strings."
            )
        validated[category] = facts

    _CACHE = validated
    logger.info(
        "Loaded fallback facts: %s",
        {category: len(facts) for category, facts in validated.items()},
    )
    return _CACHE


def get_random_fallback(category: str) -> str:
    """Возвращает случайный локальный факт для категории."""
    facts = load_fallback_facts().get(category)
    if not facts:
        raise FactFallbackError(
            f"No fallback facts available for category: {category}"
        )
    return random.choice(facts)
