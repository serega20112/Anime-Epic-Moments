"""Watch source provider contract re-export.

Абстрактный контракт провайдера живёт в domain
(:class:`backend.domain.services.watch_source_provider.WatchSourceProviderInterface`).
Здесь он лишь переэкспортируется, чтобы не менять импорты существующих клиентов
(Kodik, AniLibria, YouTube и т.д.), которые реализуют этот интерфейс.
"""

from backend.domain.services.watch_source_provider import (
    WatchSourceProviderInterface as WatchSourceProvider,
)

__all__ = ["WatchSourceProvider"]
