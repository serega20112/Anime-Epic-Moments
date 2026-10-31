"""Репозиторий коллекций: сами коллекции и их элементы.

Реализация — в модуле пакета, названном по зоне данных; этот файл только
публикует класс репозитория.
"""

from __future__ import annotations

from .collections import CollectionRepository

__all__ = ["CollectionRepository"]
