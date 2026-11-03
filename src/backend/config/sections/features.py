"""Фиче-флаги поведения приложения для клиентов."""

import os


def feature_manual_source_creation() -> bool:
    """Вернуть, разрешено ли ручное добавление источников просмотра.

    Returns:
        bool: True, если клиент может прислать адрес потока вручную.
    """
    return os.getenv("FEATURE_MANUAL_SOURCE_CREATION", "0") == "1"


def mobile_latest_app_version() -> str:
    """Вернуть последнюю опубликованную версию мобильного приложения.

    Returns:
        str: Семантический номер последней сборки либо пустую строку.
    """
    return os.getenv("MOBILE_LATEST_APP_VERSION", "").strip()


def mobile_min_app_version() -> str:
    """Вернуть минимально допустимую версию мобильного приложения.

    Returns:
        str: Семантический номер минимальной рабочей сборки либо пустую строку.
    """
    return os.getenv("MOBILE_MIN_APP_VERSION", "").strip()


def mobile_apk_url() -> str:
    """Вернуть ссылку на установочный пакет приложения.

    Returns:
        str: Адрес APK либо пустая строка, если релиз ещё не выложен.
    """
    return os.getenv("MOBILE_APK_URL", "").strip()


def mobile_apk_sha256() -> str:
    """Вернуть SHA-256 установочного пакета для проверки целостности.

    Returns:
        str: Хеш APK либо пустая строка, если он не публикуется.
    """
    return os.getenv("MOBILE_APK_SHA256", "").strip()


def mobile_changelog_url() -> str:
    """Вернуть ссылку на список изменений последнего релиза.

    Returns:
        str: Адрес changelog либо пустая строка.
    """
    return os.getenv("MOBILE_CHANGELOG_URL", "").strip()


def mobile_maintenance_mode() -> bool:
    """Вернуть, включён ли режим обслуживания для мобильного клиента.

    Returns:
        bool: True, если клиенту следует показывать экран техобслуживания.
    """
    return os.getenv("MOBILE_MAINTENANCE_MODE", "0") == "1"
