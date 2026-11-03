"""Узкие конфигурационные политики приложения.

Слои application и presentation не читают ``backend.config.Settings`` напрямую:
конкретные значения им передаёт composition root в виде маленьких неизменяемых
политик. Так видно, какие именно настройки нужны сценарию или роуту, а доступ ко
всей конфигурации остаётся явной зависимостью слоя сборки.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class PasswordResetPolicy:
    """Значения, нужные сценарию восстановления пароля.

    Attributes:
        base_url: Публичный адрес приложения для сборки ссылки из письма.
        expire_minutes: Время жизни токена сброса в минутах.
    """

    base_url: str
    expire_minutes: int


@dataclass(frozen=True, slots=True)
class CookiePolicy:
    """Параметры установки cookie авторизации.

    Attributes:
        secure: Флаг ``Secure`` у cookie.
        samesite: Значение ``SameSite``.
        domain: Домен cookie либо None для host-only.
        access_expire_minutes: Время жизни access-токена в минутах.
        refresh_expire_days: Время жизни refresh-токена в днях.
    """

    secure: bool
    samesite: str
    domain: str | None
    access_expire_minutes: int
    refresh_expire_days: int

    @property
    def access_max_age_seconds(self) -> int:
        """Возраст access-cookie в секундах.

        Returns:
            int: Минуты жизни access-токена, переведённые в секунды.
        """
        return self.access_expire_minutes * 60

    @property
    def refresh_max_age_seconds(self) -> int:
        """Возраст refresh-cookie в секундах.

        Returns:
            int: Дни жизни refresh-токена, переведённые в секунды.
        """
        return self.refresh_expire_days * 86400


@dataclass(frozen=True, slots=True)
class RequestPolicy:
    """Ограничения и адресация самого HTTP-запроса.

    Attributes:
        max_request_bytes: Максимальный размер тела запроса.
        base_url: Публичный origin приложения.
        allowed_origins: Дополнительно разрешённые origin.
        hsts_max_age: ``max-age`` заголовка Strict-Transport-Security.
        cookie_secure: Признак HTTPS — включает HSTS и secure-флаги.
    """

    max_request_bytes: int
    base_url: str
    allowed_origins: tuple[str, ...] = field(default_factory=tuple)
    hsts_max_age: int = 0
    cookie_secure: bool = False


@dataclass(frozen=True, slots=True)
class ProxyTrustPolicy:
    """Список прокси, чьему ``X-Forwarded-For`` можно верить.

    Attributes:
        trusted_proxies: Адреса или CIDR-сети доверенных прокси.
    """

    trusted_proxies: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class CatalogLimitsPolicy:
    """Лимиты разбора входных параметров каталога и поиска.

    Attributes:
        query_limit_max: Максимум тайтлов на страницу обычного поиска.
        autocomplete_limit_max: Максимум подсказок автодополнения.
        title_max_length: Предельная длина строки поиска по названию.
        description_max_length: Предельная длина описания для семантического
            поиска.
        genre_hint_max_length: Предельная длина подсказки жанра.
    """

    query_limit_max: int
    autocomplete_limit_max: int
    title_max_length: int
    description_max_length: int
    genre_hint_max_length: int


@dataclass(frozen=True, slots=True)
class ApiFeatureFlags:
    """Фиче-флаги, о которых должен знать клиент JSON API.

    Attributes:
        adult_sources_enabled: Разрешены ли источники для взрослой аудитории.
        manual_source_creation_enabled: Разрешено ли ручное добавление источников.
    """

    adult_sources_enabled: bool = False
    manual_source_creation_enabled: bool = False


@dataclass(frozen=True, slots=True)
class AppReleaseInfo:
    """Сведения о релизе мобильного приложения для контракта ``/config``.

    Клиент сверяет ``latest_app_version`` и ``min_app_version`` с локальной
    версией, чтобы показать баннер обновления или блокирующий экран, а
    ``maintenance_mode`` включает превью техобслуживания.

    Attributes:
        latest_app_version: Последняя опубликованная версия либо пустая строка.
        min_app_version: Минимальная рабочая версия либо пустая строка.
        apk_url: Ссылка на установочный пакет либо пустая строка.
        apk_sha256: Хеш пакета для проверки целостности либо пустая строка.
        changelog_url: Ссылка на список изменений либо пустая строка.
        maintenance_mode: Включён ли режим обслуживания.
    """

    latest_app_version: str = ""
    min_app_version: str = ""
    apk_url: str = ""
    apk_sha256: str = ""
    changelog_url: str = ""
    maintenance_mode: bool = False


__all__ = [
    "ApiFeatureFlags",
    "AppReleaseInfo",
    "CatalogLimitsPolicy",
    "CookiePolicy",
    "PasswordResetPolicy",
    "ProxyTrustPolicy",
    "RequestPolicy",
]
