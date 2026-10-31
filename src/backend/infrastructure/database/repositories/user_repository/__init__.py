"""Репозиторий пользователей: профиль, настройки видимости и подписки.

Реализация — в модуле пакета, названном по зоне данных; этот файл только
публикует класс репозитория.
"""

from __future__ import annotations

from .users import UserRepository

__all__ = ["UserRepository"]
