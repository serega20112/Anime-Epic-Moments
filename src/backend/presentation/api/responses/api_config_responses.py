"""Модели ответов служебного JSON API."""

from __future__ import annotations

from pydantic import BaseModel


class ApiConfigResponse(BaseModel):
    """Конфигурация возможностей, доступных клиенту.

    Attributes:
        api_version: Версия JSON API, заявленная в префиксе путей.
        adult_sources_enabled: Разрешены ли источники для взрослой аудитории.
        manual_source_creation_enabled: Разрешено ли ручное добавление источников.
    """

    api_version: str
    adult_sources_enabled: bool
    manual_source_creation_enabled: bool
