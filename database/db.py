"""Работа с базой данных SQLite."""

import logging
import sqlite3
from threading import RLock

from exceptions import DatabaseError

logger = logging.getLogger(__name__)
DB_NAME = "bot_data.db"
_CONNECTION: sqlite3.Connection | None = None
_LOCK = RLock()


def get_connection() -> sqlite3.Connection:
    """Возвращает общее соединение с базой данных."""
    global _CONNECTION
    with _LOCK:
        if _CONNECTION is None:
            try:
                _CONNECTION = sqlite3.connect(DB_NAME, check_same_thread=False)
            except sqlite3.Error as exc:
                raise DatabaseError("Could not connect to the database.") from exc
        return _CONNECTION


def init_db() -> None:
    """Создаёт таблицы и включает журналирование SQLite WAL."""
    try:
        with _LOCK:
            connection = get_connection()
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    favorite_themes TEXT NOT NULL DEFAULT 'trivia'
                )
                """
            )
            connection.commit()
        logger.info("Database initialized")
    except sqlite3.Error as exc:
        raise DatabaseError("Could not initialize the database.") from exc


def get_favorite_themes(user_id: int) -> list[str]:
    """Возвращает избранные категории пользователя."""
    try:
        with _LOCK:
            result = get_connection().execute(
                "SELECT favorite_themes FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        if not result or not result[0]:
            return ["trivia"]
        return result[0].split(",")
    except sqlite3.Error as exc:
        raise DatabaseError("Could not read favorite categories.") from exc


def set_favorite_themes(user_id: int, themes: list[str]) -> None:
    """Сохраняет избранные категории пользователя."""
    saved_themes = ",".join(themes)
    try:
        with _LOCK:
            connection = get_connection()
            connection.execute(
                """
                INSERT OR REPLACE INTO users (user_id, favorite_themes)
                VALUES (?, ?)
                """,
                (user_id, saved_themes),
            )
            connection.commit()
    except sqlite3.Error as exc:
        raise DatabaseError("Could not save favorite categories.") from exc


def close_db() -> None:
    """Закрывает соединение с БД; повторный вызов безопасен."""
    global _CONNECTION
    with _LOCK:
        if _CONNECTION is not None:
            try:
                _CONNECTION.close()
            except sqlite3.Error as exc:
                logger.warning("Could not close database connection: %s", exc)
            finally:
                _CONNECTION = None
