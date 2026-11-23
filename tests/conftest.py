"""Общие фикстуры тестов."""

import pytest

from core import fallback_loader


@pytest.fixture(autouse=True)
def reset_fallback_cache() -> None:
    """Сбрасывает кэш fallback перед каждым тестом."""
    fallback_loader._CACHE = None
