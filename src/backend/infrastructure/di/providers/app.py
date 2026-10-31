"""AppProvider: сборка провайдера по областям.

Каждая область живёт в своём модуле (`cache`, `clients`, `video_sources`,
`security`, `policies`, `storage`, `notifications`); здесь объявлен только
публичный класс, который их смешивает.
"""

from __future__ import annotations

from dishka import Provider

from .cache import CacheProvidersMixin
from .clients import ClientProvidersMixin
from .notifications import NotificationProvidersMixin
from .policies import PolicyProvidersMixin
from .security import SecurityProvidersMixin
from .storage import StorageProvidersMixin
from .video_sources import VideoSourceProvidersMixin


class AppProvider(
    CacheProvidersMixin,
    ClientProvidersMixin,
    VideoSourceProvidersMixin,
    SecurityProvidersMixin,
    PolicyProvidersMixin,
    StorageProvidersMixin,
    NotificationProvidersMixin,
    Provider,
):
    """Провайдер общих синглтонов приложения."""
