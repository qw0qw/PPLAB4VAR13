"""Исключения приложения."""


class AppError(Exception):
    """Базовое исключение приложения."""

    user_message: str = "Произошла ошибка. Попробуйте позже."


class FactAPIError(AppError):
    """Ошибка получения факта из внешнего API."""

    user_message = (
        "Сервис фактов временно недоступен. "
        "Пробуем резервный источник..."
    )

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class FactFallbackError(AppError):
    """Ошибка загрузки или использования локального набора фактов."""

    user_message = "Не удалось получить факт. Попробуйте позже."


class ConfigError(AppError):
    """Ошибка конфигурации приложения."""

    user_message = "Бот временно недоступен (ошибка конфигурации)."


class DatabaseError(AppError):
    """Ошибка работы с базой данных."""

    user_message = "Ошибка доступа к данным. Попробуйте позже."
