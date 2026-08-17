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
from backend.domain.moment.entity import ViewingMoment
from backend.domain.reaction.entity import EpisodeReaction, EpisodeReactionType
from backend.domain.reaction.value_object import EpisodeReactionCount, EpisodeReactionSummary
from backend.domain.recommendation.value_object import RecommendationResult
from backend.domain.repositories.favorite_repository import FavoriteRepository
from backend.domain.repositories.moment_repository import MomentRepository
from backend.domain.repositories.reaction_repository import ReactionRepository
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
    "EpisodeReaction",
    "EpisodeReactionCount",
    "EpisodeReactionSummary",
    "EpisodeReactionType",
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
    "MomentRepository",
    "PendingEmailVerification",
    "ProfileOverview",
    "PublicProfileOverview",
    "ReactionRepository",
    "RecommendationResult",
    "SmartProfile",
    "TopAnimeEntry",
    "Translation",
    "User",
    "UserAnimeStatus",
    "UserRepository",
    "ViewingHeatmapCell",
    "ViewingMoment",
    "ViewingSession",
    "WatchRepository",
    "WatchSource",
    "is_support_channel",
    "normalize_support_channel",
]
