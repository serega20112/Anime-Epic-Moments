"""Хранилище ключ-значение для защищённого состояния (fail-closed).

Используется ограничением частоты, отзывом токенов, блокировкой аккаунта и
подтверждением почты. Если Redis настроен, любая ошибка ввода-вывода
пробрасывается вызывающей стороне, а не переводит процесс на локальную
память: иначе состояние разъедется между воркерами gunicorn. Память остаётся
рабочим режимом только при явно выключенном Redis (``REDIS_ENABLED=0``), что
и есть одно-процессный dev-режим.
"""

from __future__ import annotations

from backend.infrastructure.cache.key_value_store import KeyValueStore


class SecurityKeyValueStore(KeyValueStore):
    """Хранилище, которое падает при недоступности Redis, а не деградирует."""

    def __init__(
        self,
        redis_url: str | None = None,
        namespace: str = "anime_epic_moments",
    ):
        """Инициализирует хранилище в обязательном режиме.

        Args:
            redis_url: URL подключения к Redis; None — память процесса.
            namespace: Префикс пространства ключей.
        """
        super().__init__(redis_url=redis_url, namespace=namespace, required=True)
