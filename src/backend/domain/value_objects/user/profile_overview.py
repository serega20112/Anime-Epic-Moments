"""Обзор профиля пользователя: активность, оценки и подписки."""

from dataclasses import dataclass
from datetime import datetime

from backend.domain.value_objects.collection.cards import CollectionCard
from backend.domain.value_objects.highlight.cards import HighlightCard
from backend.domain.value_objects.highlight.profile_summary import (
    HighlightActivityItem,
    HighlightProfileSummary,
)
from backend.domain.value_objects.user.smart_profile import ProfileLevel, SmartProfile


@dataclass(frozen=True)
class RecentEpisodeCard:
    """Карточка недавно просмотренной серии."""

    anime_id: int
    title: str
    original_title: str | None
    cover_url: str | None
    episode: int
    updated_at: datetime


@dataclass(frozen=True)
class UserRatingCard:
    """Карточка оценки, выставленной пользователем."""

    anime_id: int
    title: str
    cover_url: str | None
    score: int
    rated_at: str


@dataclass(frozen=True)
class ProfileOverview:
    """Полный обзор собственного профиля пользователя."""

    user_id: int
    email: str
    username: str
    avatar_url: str | None
    status: str | None
    show_watch_activity: bool
    show_recent_episodes: bool
    created_at: str
    summary: HighlightProfileSummary
    recent_highlights: list[HighlightCard]
    popular_highlights: list[HighlightCard]
    liked_highlights: list[HighlightCard]
    saved_highlights: list[HighlightCard]
    recent_activity: list[HighlightActivityItem]
    recent_episodes: list[RecentEpisodeCard]
    profile_level: ProfileLevel
    ratings: list[UserRatingCard]
    smart_profile: SmartProfile
    followers_count: int = 0
    following_count: int = 0


@dataclass(frozen=True)
class FollowUserCard:
    """Карточка пользователя из подписок или подписчиков."""

    user_id: int
    username: str
    avatar_url: str | None
    profile_url: str


@dataclass(frozen=True)
class PublicProfileOverview:
    """Обзор публичного профиля для других пользователей."""

    profile: ProfileOverview
    public_collections: list[CollectionCard]
    followers_preview: list[FollowUserCard]
    following_preview: list[FollowUserCard]
    followers_count: int
    following_count: int
    is_following: bool
    can_follow: bool
