"""Модели ответов служебного JSON API."""

from __future__ import annotations

from pydantic import BaseModel


class ApiConfigResponse(BaseModel):
    """Конфигурация возможностей и релиза, доступных клиенту.

    Attributes:
        api_version: Версия JSON API, заявленная в префиксе путей.
        adult_sources_enabled: Разрешены ли источники для взрослой аудитории.
        manual_source_creation_enabled: Разрешено ли ручное добавление источников.
        latest_app_version: Последняя опубликованная версия приложения.
        min_app_version: Минимально допустимая версия приложения.
        apk_url: Ссылка на установочный пакет либо пустая строка.
        apk_sha256: Хеш пакета либо пустая строка.
        changelog_url: Ссылка на список изменений либо пустая строка.
        maintenance_mode: Включён ли режим обслуживания.
    """

    api_version: str
    adult_sources_enabled: bool
    manual_source_creation_enabled: bool
    latest_app_version: str = ""
    min_app_version: str = ""
    apk_url: str = ""
    apk_sha256: str = ""
    changelog_url: str = ""
    maintenance_mode: bool = False
