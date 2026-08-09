"""Media proxy infrastructure: host policy, HLS rewriting, and streaming client."""

from backend.infrastructure.media_proxy.hls_proxy import rewrite_hls_manifest
from backend.infrastructure.media_proxy.media_proxy_client import MediaProxyClient
from backend.infrastructure.media_proxy.url_policy import (
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