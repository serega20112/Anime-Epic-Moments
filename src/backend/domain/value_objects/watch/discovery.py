from dataclasses import dataclass


@dataclass
class DiscoveredWatchSource:
    episode: int
    translation_name: str
    translation_type: str
    provider_name: str
    source_name: str
    quality_label: str
    stream_url: str
    source_type: str = "stream"
    language: str = "ru"
