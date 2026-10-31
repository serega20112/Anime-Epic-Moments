"""Базовая иерархия доменных исключений приложения."""

from __future__ import annotations


class DomainError(Exception):
    """Базовое исключение доменных ошибок."""


class NotFoundError(DomainError):
    """Запрошенный объект не найден."""


class ValidationError(DomainError):
    """Входные данные не прошли проверку."""


class AuthenticationError(DomainError):
    """Не удалось подтвердить личность пользователя."""


class AuthorizationError(DomainError):
    """У пользователя нет прав на это действие."""


class InvalidTokenError(AuthenticationError):
    """Токен недействителен, истёк либо имеет другой служебный тип.

    Исключение объявлено в домене, чтобы сценарии и представление ловили
    отказ разбора токена, не зная библиотеки, которая этот токен кодирует.
    """


class DuplicateError(DomainError):
    """Объект с такими данными уже существует."""


class ExternalServiceError(DomainError):
    """Внешний сервис или API вернул ошибку."""
