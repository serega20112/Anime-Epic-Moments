"""Хранилище ключ-значение поверх Redis с явной политикой фолбэка.

Доменные dataclass'ы пишутся в JSON по меткам типов (см. :mod:`codec`).
Когда Redis обязателен (``required=True``), любая ошибка бэкенда пробрасывается
вызывающей стороне вместо тихого перехода на память процесса: иначе состояние
разъедется между воркерами. Хранилище с таким режимом для защищённых данных
живёт в :mod:`security_store`.
"""

from __future__ import annotations

import logging
from threading import RLock
from time import monotonic
from typing import Any

from backend.infrastructure.cache.codec import deserialize, serialize

logger = logging.getLogger("anime_epic_moments")

_INCR_TTL_SCRIPT = """
local value = redis.call('INCRBY', KEYS[1], ARGV[1])
if redis.call('TTL', KEYS[1]) < 0 then
    redis.call('EXPIRE', KEYS[1], ARGV[2])
end
return value
"""


class KeyValueStore:
    """Хранит произвольные JSON-совместимые значения в Redis или в памяти.

    Доменные dataclass'ы хранятся с явными метками типов, поэтому формат
    остаётся обычным JSON без pickle.
    """

    def __init__(
        self,
        redis_url: str | None = None,
        namespace: str = "anime_epic_moments",
        required: bool = False,
    ):
        """Инициализирует хранилище.

        Args:
            redis_url: URL подключения к Redis; None — только память.
            namespace: Префикс пространства ключей.
            required: Когда True, ошибки Redis пробрасываются наружу вместо
                перехода на память процесса.
        """
        self.namespace = str(namespace or "anime_epic_moments").strip(":")
        self.required = bool(required)
        self._redis_configured = bool(redis_url)
        self._redis = self._build_redis(redis_url=redis_url, required=required)
        self._items: dict[str, tuple[float | None, Any]] = {}
        self._lock = RLock()

    @property
    def uses_redis(self) -> bool:
        """Работает ли хранилище сейчас через Redis.

        Returns:
            bool: True, если клиент Redis создан и ещё не деградировал.
        """
        return self._redis is not None

    @property
    def redis_configured(self) -> bool:
        """Был ли Redis настроен при создании хранилища.

        Returns:
            bool: True, если URL Redis передан в конструктор.
        """
        return self._redis_configured

    def _handle_backend_error(self, operation: str, error: Exception) -> None:
        """Реагирует на ошибку ввода-вывода Redis по настроенной политике.

        При ``required=True`` ошибка пробрасывается: чувствительные к
        безопасности сценарии должны падать, а не разъезжаться по памяти
        процессов. Иначе клиент сбрасывается, и дальше работает фолбэк.

        Args:
            operation: Имя упавшей операции для лога.
            error: Исходное исключение.

        Raises:
            Exception: Всегда, когда хранилище объявлено обязательным.
        """
        if self.required:
            logger.error(
                "redis_operation_failed operation=%s namespace=%s error=%s: %s",
                operation,
                self.namespace,
                error.__class__.__name__,
                error,
            )
            raise error
        logger.warning(
            "redis_degraded_to_memory operation=%s namespace=%s error=%s: %s",
            operation,
            self.namespace,
            error.__class__.__name__,
            error,
        )
        self._redis = None

    async def ping(self) -> bool:
        """Проверяет доступность Redis.

        Returns:
            bool: True, если Redis отвечает; False, если он настроен, но
            недоступен.

        Raises:
            Exception: Когда Redis обязателен и недоступен.
        """
        if not self._redis_configured:
            return True
        if self._redis is None:
            return False
        try:
            return bool(await self._redis.ping())
        except Exception as error:
            self._handle_backend_error("ping", error)
            return False

    def _build_redis(self, redis_url: str | None, required: bool):
        """Создаёт клиент Redis, если задан URL.

        Args:
            redis_url: URL подключения к Redis.
            required: Пробрасывать ли ошибку создания клиента.

        Returns:
            object | None: Асинхронный клиент Redis или None.

        Raises:
            Exception: Ошибка создания клиента при ``required=True``.
        """
        if not redis_url:
            return None
        try:
            from redis.asyncio import Redis

            return Redis.from_url(
                redis_url,
                decode_responses=False,
                socket_connect_timeout=1,
                socket_timeout=1,
            )
        except Exception:
            if required:
                raise
            return None

    def _normalize_key(self, key: str) -> str:
        """Добавляет к ключу префикс пространства имён.

        Args:
            key: Исходный ключ.

        Returns:
            str: Ключ с префиксом хранилища.
        """
        normalized = str(key or "").strip()
        return f"{self.namespace}:{normalized}" if self.namespace else normalized

    def _normalize_ttl(self, ttl_seconds: float | int | None) -> int | None:
        """Приводит TTL к целым секундам.

        Args:
            ttl_seconds: TTL в секундах или None.

        Returns:
            int | None: Неотрицательный TTL либо None.
        """
        if ttl_seconds is None:
            return None
        return max(int(ttl_seconds), 0)

    async def _get_memory_item(self, key: str) -> tuple[bool, Any]:
        """Читает запись из памяти, отбрасывая просроченные.

        Args:
            key: Ключ с префиксом пространства имён.

        Returns:
            tuple[bool, Any]: Признак наличия и само значение.
        """
        await self._prune_memory()
        item = self._items.get(key)
        if item is None:
            return False, None
        expires_at, value = item
        if expires_at is not None and expires_at <= monotonic():
            self._items.pop(key, None)
            return False, None
        return True, value

    async def _prune_memory(self) -> None:
        """Удаляет из памяти записи с истёкшим TTL."""
        now = monotonic()
        expired_keys = [
            key
            for key, (expires_at, _value) in self._items.items()
            if expires_at is not None and expires_at <= now
        ]
        for key in expired_keys:
            self._items.pop(key, None)

    async def contains(self, key: str) -> bool:
        """Проверяет наличие ключа.

        Args:
            key: Проверяемый ключ.

        Returns:
            bool: True, если ключ существует.
        """
        normalized_key = self._normalize_key(key)
        if self._redis is not None:
            try:
                return bool(await self._redis.exists(normalized_key))
            except Exception as error:
                self._handle_backend_error("contains", error)

        with self._lock:
            found, _value = await self._get_memory_item(normalized_key)
            return found

    async def get(self, key: str, default: Any = None) -> Any:
        """Читает значение по ключу.

        Args:
            key: Ключ чтения.
            default: Значение на случай отсутствия ключа.

        Returns:
            Any: Сохранённое значение или ``default``.
        """
        normalized_key = self._normalize_key(key)
        if self._redis is not None:
            try:
                raw_value = await self._redis.get(normalized_key)
                if raw_value is None:
                    return default
                raw_text = raw_value.decode("utf-8") if isinstance(raw_value, bytes) else raw_value
                return deserialize(raw_text, default)
            except Exception as error:
                self._handle_backend_error("get", error)

        with self._lock:
            found, value = await self._get_memory_item(normalized_key)
            return value if found else default

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: float | int | None = None,
    ) -> Any:
        """Сохраняет значение по ключу.

        Args:
            key: Ключ записи.
            value: Сохраняемое значение.
            ttl_seconds: TTL в секундах; 0 удаляет ключ.

        Returns:
            Any: Сохранённое значение.
        """
        normalized_key = self._normalize_key(key)
        ttl_value = self._normalize_ttl(ttl_seconds)
        if ttl_value == 0:
            await self.delete(key)
            return value

        if self._redis is not None:
            try:
                payload = serialize(value).encode("utf-8")
            except TypeError as error:
                logger.error(
                    "cache_value_unserializable key=%s namespace=%s error=%s",
                    normalized_key,
                    self.namespace,
                    error,
                )
                return value
            try:
                if ttl_value is None:
                    await self._redis.set(normalized_key, payload)
                else:
                    await self._redis.setex(normalized_key, ttl_value, payload)
                return value
            except Exception as error:
                self._handle_backend_error("set", error)

        expires_at = None if ttl_value is None else monotonic() + ttl_value
        with self._lock:
            await self._prune_memory()
            self._items[normalized_key] = (expires_at, value)
        return value

    async def consume(
        self,
        key: str,
        ttl_seconds: float | int | None = None,
    ) -> bool:
        """Атомарно занимает ключ, если его ещё нет.

        Redis использует SET NX; фолбэк держит блокировку хранилища, поэтому
        ключ достаётся ровно одному потребителю даже при гонке.

        Args:
            key: Занимаемый ключ.
            ttl_seconds: TTL захваченной записи.

        Returns:
            bool: True, если ключ захвачен, False если он уже существовал.
        """
        normalized_key = self._normalize_key(key)
        ttl_value = self._normalize_ttl(ttl_seconds)
        if ttl_value == 0:
            return False

        if self._redis is not None:
            try:
                payload = b"true"
                if ttl_value is None:
                    claimed = await self._redis.set(normalized_key, payload, nx=True)
                else:
                    claimed = await self._redis.set(normalized_key, payload, nx=True, ex=ttl_value)
                return bool(claimed)
            except Exception as error:
                self._handle_backend_error("consume", error)

        expires_at = None if ttl_value is None else monotonic() + ttl_value
        with self._lock:
            await self._prune_memory()
            if normalized_key in self._items:
                return False
            self._items[normalized_key] = (expires_at, True)
        return True

    async def delete(self, key: str) -> None:
        """Удаляет ключ.

        Args:
            key: Удаляемый ключ.
        """
        normalized_key = self._normalize_key(key)
        if self._redis is not None:
            try:
                await self._redis.delete(normalized_key)
                return
            except Exception as error:
                self._handle_backend_error("delete", error)

        with self._lock:
            self._items.pop(normalized_key, None)

    async def delete_prefix(self, prefix: str) -> None:
        """Удаляет все ключи с указанным префиксом.

        Args:
            prefix: Префикс ключей.
        """
        normalized_prefix = self._normalize_key(prefix)
        if self._redis is not None:
            try:
                keys = [key async for key in self._redis.scan_iter(f"{normalized_prefix}*")]
                if keys:
                    await self._redis.delete(*keys)
                return
            except Exception as error:
                self._handle_backend_error("delete_prefix", error)

        with self._lock:
            await self._prune_memory()
            for key in [
                item_key
                for item_key in self._items.keys()
                if item_key.startswith(normalized_prefix)
            ]:
                self._items.pop(key, None)

    async def increment(
        self,
        key: str,
        ttl_seconds: float | int,
        amount: int = 1,
    ) -> int:
        """Атомарно увеличивает счётчик с TTL.

        Redis выполняет INCRBY и EXPIRE одним Lua-скриптом, поэтому
        конкурентный читатель не увидит счётчик без TTL. Фолбэк сохраняет
        исходный срок жизни существующего счётчика, повторяя семантику Redis.

        Args:
            key: Ключ счётчика.
            ttl_seconds: TTL в секундах.
            amount: Величина приращения.

        Returns:
            int: Новое значение счётчика.
        """
        normalized_key = self._normalize_key(key)
        ttl_value = max(int(ttl_seconds), 1)
        if self._redis is not None:
            try:
                value = await self._redis.eval(
                    _INCR_TTL_SCRIPT,
                    1,
                    normalized_key,
                    int(amount),
                    ttl_value,
                )
                return int(value)
            except Exception as error:
                self._handle_backend_error("increment", error)

        with self._lock:
            await self._prune_memory()
            existing = self._items.get(normalized_key)
            if existing is None:
                expires_at: float | None = monotonic() + ttl_value
                next_value = int(amount)
            else:
                current_expires_at, current_value = existing
                expires_at = current_expires_at
                next_value = int(current_value or 0) + int(amount)
            self._items[normalized_key] = (expires_at, next_value)
            return next_value

    async def get_ttl(self, key: str) -> int:
        """Возвращает остаток TTL ключа.

        Args:
            key: Проверяемый ключ.

        Returns:
            int: Остаток TTL в секундах; 0 для отсутствующего или бессрочного
            ключа.
        """
        normalized_key = self._normalize_key(key)
        if self._redis is not None:
            try:
                ttl_value = int(await self._redis.ttl(normalized_key))
                return max(ttl_value, 0)
            except Exception as error:
                self._handle_backend_error("get_ttl", error)

        with self._lock:
            found, _value = await self._get_memory_item(normalized_key)
            if not found:
                return 0
            expires_at = self._items.get(normalized_key, (None, None))[0]
            if expires_at is None:
                return 0
            return max(int(expires_at - monotonic()), 0)

    async def clear(self) -> None:
        """Удаляет все ключи текущего пространства имён."""
        await self.delete_prefix("")

    async def close(self) -> None:
        """Закрывает клиент Redis, если он был создан."""
        if self._redis is not None:
            close = getattr(self._redis, "aclose", None) or getattr(self._redis, "close", None)
            if close is not None:
                try:
                    result = close()
                except Exception as error:
                    logger.warning("store close failed reason=%s", error.__class__.__name__)
                    return
                if result is not None:
                    await result
