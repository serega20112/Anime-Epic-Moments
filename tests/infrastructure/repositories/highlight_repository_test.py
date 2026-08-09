from __future__ import annotations

from datetime import datetime

from backend.infrastructure.repositories.user_repository import UserRepository

from backend.domain import Highlight
from backend.domain import User
from backend.infrastructure.models import HighlightModel
from backend.infrastructure.repositories.highlight_repository import HighlightRepository


def test_highlight_repository_crud_flow(db_session):
    """Проверяем, что HighlightRepository создает, читает, обновляет и удаляет хайлайт."""
    user = UserRepository(db_session).add(
        User(email="highlight@example.com", username="highlight-user", password_hash="hash")
    )
    repo = HighlightRepository(db_session)
    highlight = repo.add(
        Highlight(
            user_id=user.id,
            anime_id=7,
            episode=1,
            start_timestamp=10.0,
            end_timestamp=20.0,
            title="before",
            category="комедия",
            description="before",
            is_spoiler=False,
            emotion="funny",
        )
    )

    loaded = repo.get_by_id(highlight.id)
    highlight.edit(12.0, 24.0, "after", "бой", "after", True, "hype")
    highlight.add_like()
    highlight.add_view()
    repo.update(highlight)
    updated = repo.get_by_id(highlight.id)
    repo.delete(highlight.id)

    assert loaded is not None
    assert loaded.title == "before"
    assert loaded.category == "комедия"
    assert updated is not None
    assert updated.title == "after"
    assert updated.category == "бой"
    assert updated.description == "after"
    assert updated.is_spoiler is True
    assert updated.likes_count == 1
    assert updated.views_count == 1
    assert repo.get_by_id(highlight.id) is None


def test_highlight_repository_returns_public_top_ordered_by_popularity(db_session):
    """Проверяем, что HighlightRepository сортирует публичный топ по формуле популярности."""
    user = UserRepository(db_session).add(
        User(email="top@example.com", username="top-user", password_hash="hash")
    )
    repo = HighlightRepository(db_session)
    first = repo.add(
        Highlight(user_id=user.id, anime_id=1, episode=1, start_timestamp=1.0, end_timestamp=2.0)
    )
    second = repo.add(
        Highlight(user_id=user.id, anime_id=2, episode=1, start_timestamp=1.0, end_timestamp=2.0)
    )
    first_model = db_session.query(HighlightModel).filter_by(id=first.id).first()
    second_model = db_session.query(HighlightModel).filter_by(id=second.id).first()
    first_model.likes_count = 1
    first_model.views_count = 1
    second_model.likes_count = 3
    second_model.views_count = 0
    db_session.commit()

    items = repo.get_public_top(limit=2)

    assert [item.id for item in items] == [second.id, first.id]


def test_highlight_repository_filters_by_anime_episode_and_user_and_orders_by_date(
        db_session,
):
    """Проверяем, что HighlightRepository фильтрует по эпизоду и user_id и сортирует новые записи выше."""
    user_repo = UserRepository(db_session)
    first_user = user_repo.add(
        User(email="h1@example.com", username="highlight-1", password_hash="hash")
    )
    second_user = user_repo.add(
        User(email="h2@example.com", username="highlight-2", password_hash="hash")
    )
    repo = HighlightRepository(db_session)
    first = repo.add(
        Highlight(
            user_id=first_user.id,
            anime_id=10,
            episode=3,
            start_timestamp=1.0,
            end_timestamp=3.0,
            description="first",
        )
    )
    second = repo.add(
        Highlight(
            user_id=second_user.id,
            anime_id=10,
            episode=3,
            start_timestamp=4.0,
            end_timestamp=8.0,
            description="second",
        )
    )
    db_session.query(HighlightModel).filter_by(id=first.id).first().created_at = datetime(
        2026, 3, 28, 10, 0, 0
    )
    db_session.query(HighlightModel).filter_by(id=second.id).first().created_at = datetime(
        2026, 3, 28, 11, 0, 0
    )
    db_session.commit()

    filtered = repo.get_by_anime_episode(anime_id=10, episode=3, user_id=first_user.id)
    all_items = repo.get_by_anime_episode(anime_id=10, episode=3)

    assert [item.id for item in filtered] == [first.id]
    assert [item.id for item in all_items] == [second.id, first.id]


def test_highlight_repository_supports_likes_comments_saves_and_profile_summary(db_session):
    """Проверяем, что репозиторий умеет работать с social-сценариями хайлайтов."""
    user_repo = UserRepository(db_session)
    owner = user_repo.add(User(email="owner@example.com", username="owner", password_hash="hash"))
    viewer = user_repo.add(User(email="viewer@example.com", username="viewer", password_hash="hash"))
    repo = HighlightRepository(db_session)
    highlight = repo.add(
        Highlight(
            user_id=owner.id,
            anime_id=11,
            episode=2,
            start_timestamp=2.0,
            end_timestamp=9.0,
            title="scene",
        )
    )

    liked_highlight = repo.set_like(highlight.id, viewer.id, True)
    likers = repo.get_likers(highlight.id)
    comment = repo.add_comment(highlight.id, viewer.id, "great")
    comments = repo.get_comments(highlight.id)
    saved_state = repo.set_saved(highlight.id, viewer.id, True)
    saved_items = repo.get_saved_by_user(viewer.id)
    liked_items = repo.get_liked_by_user(viewer.id)
    engagement = repo.get_engagement_map([highlight.id], viewer_user_id=viewer.id)
    summary = repo.get_profile_summary(viewer.id)
    activity = repo.get_recent_activity(owner.id)
    viewed_highlight = repo.increment_views(highlight.id)

    assert liked_highlight.likes_count == 1
    assert likers[0].username == "viewer"
    assert comment.content == "great"
    assert comments[0].content == "great"
    assert saved_state is True
    assert [item.id for item in saved_items] == [highlight.id]
    assert [item.id for item in liked_items] == [highlight.id]
    assert engagement[highlight.id].comments_count == 1
    assert engagement[highlight.id].is_liked is True
    assert engagement[highlight.id].is_saved is True
    assert summary.like_count == 1
    assert summary.saved_count == 1
    assert activity[0].action in {"like", "comment"}
    assert viewed_highlight.views_count == 1
