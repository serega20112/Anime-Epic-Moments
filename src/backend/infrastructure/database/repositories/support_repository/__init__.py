"""Репозиторий тикетов поддержки: доступ к таблице `support_tickets`.

Реализация — в модуле пакета, названном по зоне данных; этот файл только
публикует класс репозитория.
"""

from __future__ import annotations

from .support import SupportRepository

__all__ = ["SupportRepository"]
