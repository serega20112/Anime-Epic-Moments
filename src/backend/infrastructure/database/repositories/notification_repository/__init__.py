"""Репозиторий уведомлений: доступ к таблице `notifications`.

Реализация — в модуле пакета, названном по зоне данных; этот файл только
публикует класс репозитория.
"""

from __future__ import annotations

from .notifications import NotificationRepository

__all__ = ["NotificationRepository"]
