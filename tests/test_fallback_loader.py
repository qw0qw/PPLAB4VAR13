"""Тесты загрузчика локальных фактов."""

import json

import pytest

from core import fallback_loader
from exceptions import FactFallbackError


def test_load_valid_fallback_json(tmp_path, monkeypatch) -> None:
    """Корректный JSON загружается и кэшируется."""
    path = tmp_path / "facts.json"
    path.write_text(json.dumps({"trivia": ["A fact"]}), encoding="utf-8")
    monkeypatch.setattr(fallback_loader, "FALLBACK_FILE", path)

    assert fallback_loader.load_fallback_facts() == {"trivia": ["A fact"]}
    assert fallback_loader.get_random_fallback("trivia") == "A fact"


def test_invalid_json_raises_fallback_error(tmp_path, monkeypatch) -> None:
    """Повреждённый JSON вызывает FactFallbackError."""
    path = tmp_path / "facts.json"
    path.write_text("{broken", encoding="utf-8")
    monkeypatch.setattr(fallback_loader, "FALLBACK_FILE", path)

    with pytest.raises(FactFallbackError):
        fallback_loader.load_fallback_facts()


def test_empty_category_raises_fallback_error(tmp_path, monkeypatch) -> None:
    """Пустая категория не принимается валидатором."""
    path = tmp_path / "facts.json"
    path.write_text(json.dumps({"trivia": []}), encoding="utf-8")
    monkeypatch.setattr(fallback_loader, "FALLBACK_FILE", path)

    with pytest.raises(FactFallbackError):
        fallback_loader.load_fallback_facts()
