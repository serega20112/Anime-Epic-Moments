"""Проксирование видео: белый список хостов, переписывание HLS и потоковый клиент.

Подпакет закрывает SSRF-границу плеера: наружу выпускаются только запросы к хостам из
`url_policy.ALLOWED_MEDIA_HOST_SUFFIXES`, манифест HLS переписывается так, чтобы сегменты
шли через приложение, а `MediaProxyClient` отдаёт поток порциями, не буферизируя всё в
память. Роут presentation-слоя знает только про этот публичный интерфейс.
"""

from backend.infrastructure.external.video.hls_proxy.hls_proxy import rewrite_hls_manifest
from backend.infrastructure.external.video.hls_proxy.media_proxy_client import MediaProxyClient
from backend.infrastructure.external.video.hls_proxy.url_policy import (
    ALLOWED_MEDIA_HOST_SUFFIXES,
    browser_user_agent,
    is_allowed_media_url,
    is_hls_manifest,
)

__all__ = [
    "ALLOWED_MEDIA_HOST_SUFFIXES",
    "MediaProxyClient",
    "browser_user_agent",
    "is_allowed_media_url",
    "is_hls_manifest",
    "rewrite_hls_manifest",
]
