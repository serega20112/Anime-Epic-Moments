"""Video source domain entities and enums."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class ProviderName(StrEnum):
    """Enum of supported video source providers."""

    SAMEBAND = "sameband"
    ANIBOOM = "aniboom"


@dataclass(frozen=True)
class VideoSourceMetadata:
    """Arbitrary provider-specific metadata attached to a video source."""

    values: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class VideoSource:
    """Normalized video source returned by a provider.

    Attributes:
        provider: Provider identifier.
        title: Anime title.
        episode: Episode number.
        translation: Translation name.
        quality: Video quality in pixels (e.g. 1080).
        url: Direct playable URL.
        embed_url: Embed player URL when no direct URL is available.
        mime_type: MIME type of the media.
        subtitles: List of subtitle track URLs.
        headers: HTTP headers required to play the source.
        expires_at: Optional expiration timestamp for the URL.
        is_direct: Whether the URL is a direct playable media URL.
        metadata: Provider-specific metadata.
    """

    provider: ProviderName
    title: str
    episode: int
    translation: str
    quality: int | None
    url: str
    embed_url: str | None = None
    mime_type: str | None = None
    subtitles: list[str] = field(default_factory=list)
    headers: dict[str, str] = field(default_factory=dict)
    expires_at: datetime | None = None
    is_direct: bool = True
    metadata: VideoSourceMetadata = field(default_factory=VideoSourceMetadata)
