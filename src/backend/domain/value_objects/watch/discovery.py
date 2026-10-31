"""Найденный источник просмотра до сохранения."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DiscoveredWatchSource:
    """Источник видео, найденный у внешнего провайдера."""

    episode: int
    translation_name: str
    translation_type: str
    provider_name: str
    source_name: str
    quality_label: str
    stream_url: str
    source_type: str = "stream"
    language: str = "ru"
