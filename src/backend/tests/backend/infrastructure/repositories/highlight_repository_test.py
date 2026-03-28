from __future__ import annotations

from datetime import datetime

from src.backend.domain.highlight.entity import Highlight
from src.backend.domain.user.entity import User
from src.backend.infrastructure.models.sqlalchemy_models import HighlightModel
from src.backend.infrastructure.repositories.highlight_repository import HighlightRepository
from src.backend.infrastructure.repositories.user_repository import UserRepository


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
            description="before",
            is_spoiler=False,
            emotion="funny",
        )
    )

    loaded = repo.get_by_id(highlight.id)
    highlight.edit(12.0, 24.0, "after", True)
    highlight.add_like()
    repo.update(highlight)
    updated = repo.get_by_id(highlight.id)
    repo.delete(highlight.id)

    assert loaded is not None
    assert loaded.description == "before"
    assert updated is not None
    assert updated.description == "after"
    assert updated.is_spoiler is True
    assert updated.likes_count == 1
    assert repo.get_by_id(highlight.id) is None


def test_highlight_repository_returns_public_top_ordered_by_likes(db_session):
    """Проверяем, что HighlightRepository возвращает публичный топ по убыванию likes_count."""
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
    db_session.query(HighlightModel).filter_by(id=first.id).first().likes_count = 1
    db_session.query(HighlightModel).filter_by(id=second.id).first().likes_count = 3
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
