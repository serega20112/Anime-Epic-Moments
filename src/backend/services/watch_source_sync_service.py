import re

from src.backend.domain.anime.entity import Anime
from src.backend.domain.watch.entity import Translation, WatchSource
from src.backend.infrastructure.external.kodik_client import KodikClient
from src.backend.repository.watch_repository import WatchRepository


class WatchSourceSyncService:
    """Синхронизирует источники просмотра из внешнего провайдера в локальное хранилище."""

    def __init__(self, watch_repo: WatchRepository, kodik_client: KodikClient):
        self.watch_repo = watch_repo
        self.kodik_client = kodik_client

    def is_enabled(self) -> bool:
        return self.kodik_client.is_configured()

    def sync_for_anime(
        self,
        anime_id: int,
        anime: Anime | None,
        episode: int,
        force: bool = False,
    ) -> list[WatchSource]:
        existing = self.watch_repo.get_sources(anime_id=anime_id, episode=episode)
        if existing and not force:
            return existing
        if not anime or not anime.title or not self.is_enabled():
            return existing

        discovered = []
        for title_variant in self._build_title_variants(anime.title):
            discovered = self.kodik_client.search_sources(
                title=title_variant,
                episode=episode,
                year=anime.year,
            )
            if discovered:
                break

        for item in discovered:
            translation = self.watch_repo.add_translation(
                Translation(
                    anime_id=anime_id,
                    name=item.translation_name,
                    translation_type=item.translation_type,
                    language=item.language,
                )
            )
            self.watch_repo.add_source(
                WatchSource(
                    anime_id=anime_id,
                    episode=item.episode,
                    translation_id=translation.id or 0,
                    provider_name=item.provider_name,
                    source_name=item.source_name,
                    stream_url=item.stream_url,
                    quality_label=item.quality_label,
                )
            )

        return self.watch_repo.get_sources(anime_id=anime_id, episode=episode)

    def _build_title_variants(self, title: str) -> list[str]:
        variants = [title.strip()]
        simplified = re.split(r"[:(\\[]", title, maxsplit=1)[0].strip()
        if simplified and simplified not in variants:
            variants.append(simplified)
        normalized = " ".join(title.replace("-", " ").split())
        if normalized and normalized not in variants:
            variants.append(normalized)
        return [item for item in variants if item]
