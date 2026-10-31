"""Репозиторий избранного: доступ к таблице `favorites` с локальным snapshot'ом карточки.

Реализация — в модуле пакета, названном по зоне данных; этот файл только
публикует класс репозитория.
"""

from __future__ import annotations

from .favorites import FavoriteRepository

__all__ = ["FavoriteRepository"]
