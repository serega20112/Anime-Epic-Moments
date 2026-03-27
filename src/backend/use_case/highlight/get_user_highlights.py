from collections import Counter
from src.backend.domain.highlight.value_object import (
    HighlightAnimeGroup,
    HighlightCard,
    HighlightDashboard,
    HighlightStats,
)
from src.backend.infrastructure.external.anime_api_client import AnimeApiClient
from src.backend.repository.highlight_repository import HighlightRepository


class GetUserHighlightsUseCase:
    """Возвращает дашборд хайлайтов пользователя с фильтрами и статистикой."""

    def __init__(self, repo: HighlightRepository, anime_api_client: AnimeApiClient):
        self.repo = repo
        self.anime_api_client = anime_api_client

    def execute(
        self,
        user_id: int,
        anime_id: int | None = None,
        emotion: str | None = None,
        created_date: str | None = None,
        query: str | None = None,
        include_spoilers: bool = True,
    ) -> HighlightDashboard:
        """Принимает user_id и фильтры, возвращает карточки, группы и статистику."""
        highlights = self.repo.get_by_user(user_id)
        return self._build_dashboard(
            highlights=highlights,
            anime_id=anime_id,
            emotion=emotion,
            created_date=created_date,
            query=query,
            include_spoilers=include_spoilers,
        )

    def _build_dashboard(
        self,
        highlights,
        anime_id: int | None,
        emotion: str | None,
        created_date: str | None,
        query: str | None,
        include_spoilers: bool,
    ) -> HighlightDashboard:
        anime_cache: dict[int, tuple[str, str | None]] = {}

        def anime_meta(value: int) -> tuple[str, str | None]:
            if value not in anime_cache:
                anime = self.anime_api_client.get_by_id(value)
                anime_cache[value] = (
                    anime.title if anime and anime.title else f"Anime #{value}",
                    anime.cover_url if anime else None,
                )
            return anime_cache[value]

        filtered = []
        for highlight in highlights:
            title, _cover = anime_meta(highlight.anime_id)
            if anime_id is not None and highlight.anime_id != anime_id:
                continue
            if emotion and (highlight.emotion or "") != emotion:
                continue
            if (
                created_date
                and highlight.created_at.strftime("%Y-%m-%d") != created_date
            ):
                continue
            if not include_spoilers and highlight.is_spoiler:
                continue
            haystack = f"{title} {highlight.description or ''} {(highlight.emotion or '')}".lower()
            if query and query.lower() not in haystack:
                continue
            filtered.append(highlight)

        cards = []
        counter = Counter()
        emotions = set()
        total_duration = 0.0

        for highlight in filtered:
            title, cover = anime_meta(highlight.anime_id)
            duration = max(highlight.end_timestamp - highlight.start_timestamp, 0.0)
            counter[(highlight.anime_id, title)] += 1
            if highlight.emotion:
                emotions.add(highlight.emotion)
            total_duration += duration
            cards.append(
                HighlightCard(
                    id=highlight.id or 0,
                    anime_id=highlight.anime_id,
                    anime_title=title,
                    anime_cover=cover,
                    episode=highlight.episode,
                    start_timestamp=self._format_timestamp(highlight.start_timestamp),
                    end_timestamp=self._format_timestamp(highlight.end_timestamp),
                    duration_seconds=duration,
                    description=highlight.description or "",
                    is_spoiler=highlight.is_spoiler,
                    emotion=highlight.emotion,
                    created_at=highlight.created_at.strftime("%Y-%m-%d"),
                    likes_count=highlight.likes_count,
                    watch_url=f"/watch/{highlight.anime_id}?episode={highlight.episode}",
                    share_url=f"/highlights?highlight_id={highlight.id}",
                )
            )

        groups = [
            HighlightAnimeGroup(
                anime_id=item[0][0], anime_title=item[0][1], count=item[1]
            )
            for item in counter.most_common()
        ]
        top_anime_title = groups[0].anime_title if groups else "Нет данных"
        average_duration = (total_duration / len(cards)) if cards else 0.0

        return HighlightDashboard(
            items=cards,
            anime_groups=groups,
            emotions=sorted(emotions),
            stats=HighlightStats(
                total_highlights=len(cards),
                top_anime_title=top_anime_title,
                average_duration_seconds=round(average_duration, 1),
            ),
            selected_anime_id=anime_id,
            selected_emotion=emotion,
            selected_date=created_date,
            selected_query=query,
            include_spoilers=include_spoilers,
        )

    def _format_timestamp(self, seconds: float) -> str:
        minutes = int(seconds // 60)
        sec = int(seconds % 60)
        return f"{minutes:02d}:{sec:02d}"
