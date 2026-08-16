"""Domain facade: re-exports entities, policies and repository interfaces."""

from backend.domain.favorite.entity import Favorite
from backend.domain.highlight.entity import Highlight
from backend.domain.highlight.policy import HighlightPolicy
from backend.domain.highlight.value_object import (
    HighlightActivityItem,
    HighlightAnimeGroup,
    HighlightCard,
    HighlightCommentItem,
    HighlightDashboard,
    HighlightEngagement,
    HighlightFeedPage,
    HighlightLikeUser,
    HighlightProfileSummary,
    HighlightStats,
)
from backend.domain.recommendation.value_object import RecommendationResult
from backend.domain.repositories.favorite_repository import FavoriteRepository
from backend.domain.repositories.user_repository import UserRepository
from backend.domain.repositories.watch_repository import WatchRepository
from backend.domain.support.channel import is_support_channel, normalize_support_channel
from backend.domain.user.entity import User
from backend.domain.user.value_object import (
    FollowUserCard,
    PendingEmailVerification,
    ProfileOverview,
    PublicProfileOverview,
    SmartProfile,
    TopAnimeEntry,
    ViewingHeatmapCell,
)
from backend.domain.watch.entity import (
    HighlightContext,
    Translation,
    UserAnimeStatus,
    ViewingSession,
    WatchSource,
)

__all__ = [
    "Favorite",
    "FavoriteRepository",
    "FollowUserCard",
    "Highlight",
    "HighlightActivityItem",
    "HighlightAnimeGroup",
    "HighlightCard",
    "HighlightCommentItem",
    "HighlightContext",
    "HighlightDashboard",
    "HighlightEngagement",
    "HighlightFeedPage",
    "HighlightLikeUser",
    "HighlightPolicy",
    "HighlightProfileSummary",
    "HighlightStats",
    "PendingEmailVerification",
    "ProfileOverview",
    "PublicProfileOverview",
    "RecommendationResult",
    "SmartProfile",
    "TopAnimeEntry",
    "Translation",
    "User",
    "UserAnimeStatus",
    "UserRepository",
    "ViewingHeatmapCell",
    "ViewingSession",
    "WatchRepository",
    "WatchSource",
    "is_support_channel",
    "normalize_support_channel",
]
