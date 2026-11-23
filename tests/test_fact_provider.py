"""Тесты выбора источника фактов."""

from unittest.mock import Mock

import pytest

from core import fact_provider
from exceptions import FactAPIError, FactFallbackError


def test_provider_returns_api_fact(monkeypatch: pytest.MonkeyPatch) -> None:
    """Факт из API имеет приоритет над локальным источником."""
    monkeypatch.setattr(
        fact_provider.api_client,
        "fetch_fact",
        Mock(return_value={"text": "API fact"}),
    )
    monkeypatch.setattr(
        fact_provider.fallback_loader,
        "get_random_fallback",
        Mock(side_effect=AssertionError("Fallback must not be used")),
    )

    assert fact_provider.get_fact("trivia") == "API fact"


def test_provider_uses_fallback_when_api_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """При ошибке API возвращается локальный факт."""
    monkeypatch.setattr(
        fact_provider.api_client,
        "fetch_fact",
        Mock(side_effect=FactAPIError("offline")),
    )
    monkeypatch.setattr(
        fact_provider.fallback_loader,
        "get_random_fallback",
        Mock(return_value="Local fact"),
    )

    assert fact_provider.get_fact("trivia") == "Local fact"


def test_provider_uses_fallback_after_two_transient_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """HTTP-клиент с ретраями может восстановиться до возврата ответа."""
    calls = 0

    def fetch_with_retries(category: str) -> dict[str, str]:
        nonlocal calls
        for _ in range(3):
            calls += 1
            if calls == 3:
                return {"text": "Recovered API fact"}
        raise FactAPIError("retries exhausted")

    monkeypatch.setattr(
        fact_provider.api_client,
        "fetch_fact",
        fetch_with_retries,
    )
    assert fact_provider.get_fact("trivia") == "Recovered API fact"
    assert calls == 3


def test_provider_raises_when_both_sources_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ошибка локального источника не скрывается."""
    monkeypatch.setattr(
        fact_provider.api_client,
        "fetch_fact",
        Mock(side_effect=FactAPIError("offline")),
    )
    monkeypatch.setattr(
        fact_provider.fallback_loader,
        "get_random_fallback",
        Mock(side_effect=FactFallbackError("missing")),
    )

    with pytest.raises(FactFallbackError):
        fact_provider.get_fact("trivia")
