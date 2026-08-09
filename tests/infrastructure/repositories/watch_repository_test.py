from __future__ import annotations

from backend.infrastructure.repositories.user_repository import UserRepository

from backend.domain import Highlight
from backend.domain import (
    HighlightContext,
    Translation,
    UserAnimeStatus,
    ViewingSession,
    WatchSource,
)
from backend.domain import User
from backend.infrastructure.repositories.highlight_repository import HighlightRepository
from backend.infrastructure.repositories.watch_repository import WatchRepository


def test_watch_repository_upserts_and_reads_status(db_session):
    """Проверяем, что WatchRepository создает и обновляет статус просмотра пользователя."""
    user = UserRepository(db_session).add(
        User(email="watch-status@example.com", username="status-user", password_hash="hash")
    )
    repo = WatchRepository(db_session)

    created = repo.upsert_status(
        UserAnimeStatus(user_id=user.id, anime_id=7, status="watching")
    )
    updated = repo.upsert_status(
        UserAnimeStatus(user_id=user.id, anime_id=7, status="completed")
    )
    loaded = repo.get_status(user.id, 7)

    assert created.id is not None
    assert updated.id == created.id
    assert loaded is not None
    assert loaded.status == "completed"


def test_watch_repository_deduplicates_and_sorts_translations(db_session):
    """Проверяем, что WatchRepository не дублирует одинаковые переводы и сортирует их по имени."""
    repo = WatchRepository(db_session)
    first = repo.add_translation(
        Translation(anime_id=7, name="Zet", translation_type="voice")
    )
    second = repo.add_translation(
        Translation(anime_id=7, name="AniLibria", translation_type="voice")
    )
    duplicate = repo.add_translation(
        Translation(anime_id=7, name="AniLibria", translation_type="voice")
    )

    items = repo.get_translations(7)

    assert duplicate.id == second.id
    assert [item.name for item in items] == ["AniLibria", "Zet"]
    assert first.id is not None


def test_watch_repository_deduplicates_sources_and_filters_by_episode(db_session):
    """Проверяем, что WatchRepository не дублирует одинаковые источники и умеет фильтровать по эпизоду."""
    repo = WatchRepository(db_session)
    translation = repo.add_translation(
        Translation(anime_id=7, name="AniLibria", translation_type="voice")
    )
    source = repo.add_source(
        WatchSource(
            anime_id=7,
            episode=2,
            translation_id=translation.id,
            provider_name="Kodik",
            source_name="s1",
            stream_url="https://example.com/1.m3u8",
            quality_label="1080",
        )
    )
    duplicate = repo.add_source(
        WatchSource(
            anime_id=7,
            episode=2,
            translation_id=translation.id,
            provider_name="Kodik",
            source_name="s1",
            stream_url="https://example.com/1.m3u8",
            quality_label="1080",
        )
    )
    repo.add_source(
        WatchSource(
            anime_id=7,
            episode=3,
            translation_id=translation.id,
            provider_name="Kodik",
            source_name="s2",
            stream_url="https://example.com/2.m3u8",
            quality_label="720",
        )
    )

    episode_sources = repo.get_sources(anime_id=7, episode=2)
    all_sources = repo.get_sources(anime_id=7)

    assert duplicate.id == source.id
    assert [item.episode for item in episode_sources] == [2]
    assert [item.episode for item in all_sources] == [2, 3]


def test_watch_repository_upserts_and_reads_viewing_session(db_session):
    """Проверяем, что WatchRepository создает и обновляет viewing session пользователя."""
    user = UserRepository(db_session).add(
        User(email="session@example.com", username="session-user", password_hash="hash")
    )
    repo = WatchRepository(db_session)
    translation = repo.add_translation(
        Translation(anime_id=7, name="AniLibria", translation_type="voice")
    )
    source = repo.add_source(
        WatchSource(
            anime_id=7,
            episode=2,
            translation_id=translation.id,
            provider_name="Kodik",
            source_name="s1",
            stream_url="https://example.com/1.m3u8",
            quality_label="1080",
        )
    )

    created = repo.upsert_session(
        ViewingSession(
            user_id=user.id,
            anime_id=7,
            episode=2,
            watch_source_id=source.id,
            position_seconds=15.5,
            volume=0.5,
            quality_label="1080",
            is_paused=False,
        )
    )
    updated = repo.upsert_session(
        ViewingSession(
            user_id=user.id,
            anime_id=7,
            episode=2,
            watch_source_id=source.id,
            position_seconds=22.0,
            volume=0.8,
            quality_label="720",
            is_paused=True,
        )
    )
    loaded = repo.get_session(user.id, 7, 2)

    assert created.id is not None
    assert updated.id == created.id
    assert loaded is not None
    assert loaded.position_seconds == 22.0
    assert loaded.volume == 0.8
    assert loaded.quality_label == "720"
    assert loaded.is_paused is True


def test_watch_repository_adds_and_reads_highlight_contexts(db_session):
    """Проверяем, что WatchRepository сохраняет playback context для набора хайлайтов."""
    user_repo = UserRepository(db_session)
    user = user_repo.add(
        User(email="context@example.com", username="context-user", password_hash="hash")
    )
    watch_repo = WatchRepository(db_session)
    translation = watch_repo.add_translation(
        Translation(anime_id=7, name="AniLibria", translation_type="voice")
    )
    source = watch_repo.add_source(
        WatchSource(
            anime_id=7,
            episode=2,
            translation_id=translation.id,
            provider_name="Kodik",
            source_name="s1",
            stream_url="https://example.com/1.m3u8",
            quality_label="1080",
        )
    )
    highlight = HighlightRepository(db_session).add(
        Highlight(
            user_id=user.id,
            anime_id=7,
            episode=2,
            start_timestamp=1.0,
            end_timestamp=2.0,
        )
    )

    context = watch_repo.add_highlight_context(
        HighlightContext(
            highlight_id=highlight.id,
            watch_source_id=source.id,
            translation_id=translation.id,
            title="best clip",
        )
    )
    loaded = watch_repo.get_highlight_contexts([highlight.id, 999])

    assert context.id is not None
    assert len(loaded) == 1
    assert loaded[0].title == "best clip"
    assert watch_repo.get_highlight_contexts([]) == []


def test_watch_repository_returns_watched_anime_stats_and_heatmap(db_session):
    """Проверяем, что WatchRepository агрегирует просмотр по аниме и по дням активности."""
    user = UserRepository(db_session).add(
        User(email="stats@example.com", username="stats-user", password_hash="hash")
    )
    repo = WatchRepository(db_session)
    translation = repo.add_translation(
        Translation(anime_id=7, name="AniLibria", translation_type="voice")
    )
    source = repo.add_source(
        WatchSource(
            anime_id=7,
            episode=1,
            translation_id=translation.id,
            provider_name="Kodik",
            source_name="s1",
            stream_url="https://example.com/1.m3u8",
            quality_label="1080",
        )
    )
    second_source = repo.add_source(
        WatchSource(
            anime_id=8,
            episode=1,
            translation_id=translation.id,
            provider_name="Kodik",
            source_name="s2",
            stream_url="https://example.com/2.m3u8",
            quality_label="720",
        )
    )
    repo.upsert_session(
        ViewingSession(
            user_id=user.id,
            anime_id=7,
            episode=1,
            watch_source_id=source.id,
            position_seconds=1800.0,
            volume=1.0,
            quality_label="1080",
            is_paused=False,
        )
    )
    repo.upsert_session(
        ViewingSession(
            user_id=user.id,
            anime_id=8,
            episode=1,
            watch_source_id=second_source.id,
            position_seconds=900.0,
            volume=1.0,
            quality_label="720",
            is_paused=True,
        )
    )

    watched_stats = repo.get_watched_anime_stats(user.id)
    heatmap = repo.get_viewing_heatmap(user.id, days=7)

    assert [item.anime_id for item in watched_stats] == [7, 8]
    assert watched_stats[0].watched_seconds == 1800.0
    assert watched_stats[1].sessions_count == 1
    assert len(heatmap) == 1
    assert heatmap[0].interactions == 2


def test_watch_repository_adds_sorts_and_likes_anime_discussion_comments(db_session):
    """Проверяем, что WatchRepository ведет обсуждение аниме, сортирует комментарии и считает лайки."""
    user_repo = UserRepository(db_session)
    author = user_repo.add(
        User(email="discussion@example.com", username="author", password_hash="hash")
    )
    viewer = user_repo.add(
        User(email="discussion-2@example.com", username="viewer", password_hash="hash")
    )
    repo = WatchRepository(db_session)
    first = repo.add_anime_comment(anime_id=7, user_id=author.id, content="Первый коммент")
    second = repo.add_anime_comment(anime_id=7, user_id=viewer.id, content="Второй коммент")

    repo.set_anime_comment_like(comment_id=second.id, user_id=author.id, liked=True)
    popular = repo.get_anime_comments(anime_id=7, sort_by="popular", viewer_user_id=author.id)
    recent = repo.get_anime_comments(anime_id=7, sort_by="recent", viewer_user_id=author.id)

    assert popular[0].id == second.id
    assert popular[0].likes_count == 1
    assert popular[0].is_liked is True
    assert recent[0].id == second.id
    assert recent[1].id == first.id
