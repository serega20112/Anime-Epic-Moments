"""Фиче-флаги поведения приложения для клиентов."""

import os


def feature_manual_source_creation() -> bool:
    """Вернуть, разрешено ли ручное добавление источников просмотра.

    Returns:
        bool: True, если клиент может прислать адрес потока вручную.
    """
    return os.getenv("FEATURE_MANUAL_SOURCE_CREATION", "0") == "1"
