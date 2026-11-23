"""Тесты работы с базой данных SQLite."""

import pytest

from database import db


@pytest.fixture
def isolated_database(tmp_path, monkeypatch):
    """Подменяет рабочую БД временной тестовой базой."""
    db.close_db()
    monkeypatch.setattr(db, "DB_NAME", str(tmp_path / "test.db"))

    yield

    db.close_db()


def test_init_db_creates_database(isolated_database):
    """Инициализация создаёт таблицу users."""
    db.init_db()

    connection = db.get_connection()
    result = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = 'users'
        """
    ).fetchone()

    assert result is not None
    assert result[0] == "users"


def test_get_favorite_themes_returns_default(isolated_database):
    """Для нового пользователя возвращается категория по умолчанию."""
    db.init_db()

    assert db.get_favorite_themes(12345) == ["trivia"]


def test_set_and_get_favorite_themes(isolated_database):
    """Избранные категории сохраняются и корректно читаются."""
    db.init_db()
    themes = ["math", "date", "year"]

    db.set_favorite_themes(12345, themes)

    assert db.get_favorite_themes(12345) == themes


def test_set_favorite_themes_updates_existing_user(
    isolated_database,
):
    """Повторное сохранение обновляет категории пользователя."""
    db.init_db()

    db.set_favorite_themes(12345, ["math"])
    db.set_favorite_themes(12345, ["date", "year"])

    assert db.get_favorite_themes(12345) == ["date", "year"]


def test_close_db_is_safe_to_call_twice(isolated_database):
    """Повторное закрытие соединения не вызывает ошибку."""
    db.init_db()

    db.close_db()
    db.close_db()

    assert db._CONNECTION is None