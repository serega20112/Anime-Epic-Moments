"""Запрос письма со ссылкой на восстановление пароля."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RequestPasswordResetCommand:
    """Команда запроса восстановления пароля.

    Attributes:
        email: Нормализованный адрес почты.
        base_url: Адрес сайта, из которого собирается ссылка в письме.
    """

    email: str
    base_url: str
