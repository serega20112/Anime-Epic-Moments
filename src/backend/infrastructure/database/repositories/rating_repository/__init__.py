"""Репозиторий оценок: пользовательские оценки аниме.

Реализация — в модуле пакета, названном по зоне данных; этот файл только
публикует класс репозитория.
"""

from __future__ import annotations

from .ratings import RatingRepository

__all__ = ["RatingRepository"]
