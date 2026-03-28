from collections import Counter
from datetime import datetime

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
        category: str | None = None,
        sort_by: str = "recent",
        created_date: str | None = None,
        query: str | None = None,
        include_spoilers: bool = True,
        viewer_user_id: int | None = None,
    ) -> HighlightDashboard:
        highlights = self.repo.get_by_user(user_id)
        return self._build_dashboard(
            highlights=highlights,
            anime_id=anime_id,
            emotion=emotion,
            category=category,
            sort_by=sort_by,
            created_date=created_date,
            query=query,
            include_spoilers=include_spoilers,
            viewer_user_id=viewer_user_id,
        )

    def _build_dashboard(
        self,
        highlights,
        anime_id: int | None,
        emotion: str | None,
        category: str | None,
        sort_by: str,
        created_date: str | None,
        query: str | None,
        include_spoilers: bool,
        viewer_user_id: int | None,
    ) -> HighlightDashboard:
        anime_cache: dict[int, tuple[str, str | None, int]] = {}

        def anime_meta(value: int) -> tuple[str, str | None, int]:
            if value not in anime_cache:
                anime = self.anime_api_client.get_by_id(value)
                watch_id = value
                if anime and anime.external_id:
                    try:
                        resolved_watch_id = int(str(anime.external_id).strip())
                        if resolved_watch_id > 0:
                            watch_id = resolved_watch_id
                    except (TypeError, ValueError):
                        watch_id = value
                anime_cache[value] = (
                    anime.title if anime and anime.title else f"Anime #{value}",
                    anime.cover_url if anime else None,
                    watch_id,
                )
            return anime_cache[value]

        filtered = []
        for highlight in highlights:
            anime_title, _cover, _watch_id = anime_meta(highlight.anime_id)
            if anime_id is not None and highlight.anime_id != anime_id:
                continue
            if emotion and (highlight.emotion or "") != emotion:
                continue
            if category and (highlight.category or "") != category:
                continue
            if created_date and highlight.created_at.strftime("%Y-%m-%d") != created_date:
                continue
            if not include_spoilers and highlight.is_spoiler:
                continue
            haystack = (
                f"{anime_title} {highlight.title or ''} {highlight.description or ''} "
                f"{highlight.category or ''} {(highlight.emotion or '')}"
            ).lower()
            if query and query.lower() not in haystack:
                continue
            filtered.append(highlight)

        filtered = self._sort_highlights(filtered, sort_by=sort_by)
        engagement_map = self.repo.get_engagement_map(
            [highlight.id for highlight in filtered if highlight.id is not None],
            viewer_user_id=viewer_user_id,
        )
        cards = []
        counter = Counter()
        emotions = set()
        categories = set()
        total_duration = 0.0

        for highlight in filtered:
            anime_title, cover, watch_id = anime_meta(highlight.anime_id)
            duration = max(highlight.end_timestamp - highlight.start_timestamp, 0.0)
            counter[(highlight.anime_id, anime_title)] += 1
            if highlight.emotion:
                emotions.add(highlight.emotion)
            if highlight.category:
                categories.add(highlight.category)
            total_duration += duration
            engagement = engagement_map.get(highlight.id or 0)
            cards.append(
                HighlightCard(
                    id=highlight.id or 0,
                    anime_id=highlight.anime_id,
                    anime_title=anime_title,
                    anime_cover=cover,
                    title=highlight.title or f"Момент {highlight.episode} серии",
                    category=highlight.category,
                    episode=highlight.episode,
                    start_timestamp=self._format_timestamp(highlight.start_timestamp),
                    end_timestamp=self._format_timestamp(highlight.end_timestamp),
                    duration_seconds=duration,
                    description=highlight.description or "",
                    is_spoiler=highlight.is_spoiler,
                    emotion=highlight.emotion,
                    created_at=highlight.created_at.strftime("%Y-%m-%d"),
                    likes_count=highlight.likes_count,
                    views_count=highlight.views_count,
                    comments_count=engagement.comments_count if engagement else 0,
                    is_liked=engagement.is_liked if engagement else False,
                    is_saved=engagement.is_saved if engagement else False,
                    watch_url=f"/watch/{watch_id}?episode={highlight.episode}",
                    share_url=f"/highlights/share/{highlight.id}",
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
            categories=sorted(categories),
            stats=HighlightStats(
                total_highlights=len(cards),
                top_anime_title=top_anime_title,
                average_duration_seconds=round(average_duration, 1),
            ),
            selected_anime_id=anime_id,
            selected_emotion=emotion,
            selected_category=category,
            selected_sort=sort_by if sort_by in {"recent", "popular"} else "recent",
            selected_date=created_date,
            selected_query=query,
            include_spoilers=include_spoilers,
        )

    def _format_timestamp(self, seconds: float) -> str:
        minutes = int(seconds // 60)
        sec = int(seconds % 60)
        return f"{minutes:02d}:{sec:02d}"

    def _sort_highlights(self, highlights, sort_by: str):
        if sort_by == "popular":
            return sorted(
                highlights,
                key=self._popularity_score,
                reverse=True,
            )
        return sorted(highlights, key=lambda item: item.created_at, reverse=True)

    def _popularity_score(self, highlight) -> float:
        age_hours = max(
            (datetime.utcnow() - highlight.created_at).total_seconds() / 3600,
            0.0,
        )
        freshness_bonus = max(72.0 - age_hours, 0.0) / 12.0
        return (
            float(highlight.likes_count or 0) * 4.0
            + float(getattr(highlight, "views_count", 0) or 0) * 2.0
            + freshness_bonus
        )
