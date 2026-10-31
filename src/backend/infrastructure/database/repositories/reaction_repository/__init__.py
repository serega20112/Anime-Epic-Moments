"""Репозиторий реакций: реакции пользователя на конкретные моменты эпизода.

Реализация — в модуле пакета, названном по зоне данных; этот файл только
публикует класс репозитория.
"""

from __future__ import annotations

from .reactions import ReactionRepository

__all__ = ["ReactionRepository"]
