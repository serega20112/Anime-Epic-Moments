"""Хранилище файлов и проверка готовности приложения."""

from __future__ import annotations

from dishka import Provider, Scope, provide

from backend.application.interface.services import (
    HealthCheckPort,
    ImageStoragePort,
)
from backend.infrastructure.cache.key_value_store import KeyValueStore
from backend.infrastructure.health import ApplicationHealthCheck
from backend.infrastructure.storage import FileSystemImageStorage


class StorageProvidersMixin(Provider):
    """Хранилище файлов и проверка готовности приложения.

    Часть провайдера: методы `@provide` собираются dishka из базовых
    классов, поэтому mixin самодостаточен и наследует `Provider`.
    """

    @provide(scope=Scope.APP)
    async def image_storage(self) -> ImageStoragePort:
        """Опубликовать хранилище изображений через порт прикладного слоя.

        Returns:
            ImageStoragePort: Файловое хранилище картинок под каталог статики.
        """
        return FileSystemImageStorage()

    @provide(scope=Scope.APP)
    async def health_check(self, store: KeyValueStore) -> HealthCheckPort:
        """Опубликовать пробу готовности через порт прикладного слоя.

        Args:
            store: Общее хранилище ключ-значение, которое проба пингует.

        Returns:
            HealthCheckPort: Реализация, опрашивающая базу и Redis.
        """
        return ApplicationHealthCheck(store=store)
