"""Domain facade: re-exports aggregates, entities, value objects and policies.

Порты (интерфейсы репозиториев, сервисов и UoW) живут в ``backend.application.interface`` —
домен знает только свой язык и не зависит от слоёв выше.
"""

from backend.domain.aggregates.highlight.highlight import Highlight
from backend.domain.aggregates.user.user import User
from backend.domain.entities.favorite.favorite import Favorite
from backend.domain.entities.moment.viewing_moment import ViewingMoment
from backend.domain.entities.rating.anime_rating import UserAnimeRating
from backend.domain.entities.reaction.episode_reaction import EpisodeReaction
from backend.domain.entities.support.channel import is_support_channel, normalize_support_channel
from backend.domain.entities.watch.highlight_context import HighlightContext
from backend.domain.entities.watch.translation import Translation
from backend.domain.entities.watch.user_anime_status import UserAnimeStatus
from backend.domain.entities.watch.viewing_session import ViewingSession
from backend.domain.entities.watch.watch_source import WatchSource
from backend.domain.policies.highlight_policy import HighlightPolicy
from backend.domain.value_objects.highlight.cards import (
    HighlightCard,
    HighlightCommentItem,
    HighlightEngagement,
    HighlightLikeUser,
    HighlightStats,
)
from backend.domain.value_objects.highlight.dashboard import HighlightDashboard
from backend.domain.value_objects.highlight.feed import HighlightAnimeGroup, HighlightFeedPage
from backend.domain.value_objects.highlight.profile_summary import (
    HighlightActivityItem,
    HighlightProfileSummary,
)
from backend.domain.value_objects.reaction.reaction_summary import (
    EpisodeReactionCount,
    EpisodeReactionSummary,
)
from backend.domain.value_objects.reaction.reaction_type import EpisodeReactionType
from backend.domain.value_objects.recommendation.recommendation_result import RecommendationResult
from backend.domain.value_objects.user.pending_email_verification import PendingEmailVerification
from backend.domain.value_objects.user.profile_overview import (
    FollowUserCard,
    ProfileOverview,
    PublicProfileOverview,
    RecentEpisodeCard,
    UserRatingCard,
)
from backend.domain.value_objects.user.smart_profile import (
    ProfileLevel,
    SmartProfile,
    TopAnimeEntry,
    ViewingHeatmapCell,
)

__all__ = [
    "EpisodeReaction",
    "EpisodeReactionCount",
    "EpisodeReactionSummary",
    "EpisodeReactionType",
    "Favorite",
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
    "ProfileLevel",
    "PublicProfileOverview",
    "RecommendationResult",
    "RecentEpisodeCard",
    "SmartProfile",
    "TopAnimeEntry",
    "Translation",
    "User",
    "UserAnimeRating",
    "UserAnimeStatus",
    "UserRatingCard",
    "ViewingHeatmapCell",
    "ViewingMoment",
    "ViewingSession",
    "WatchSource",
    "is_support_channel",
    "normalize_support_channel",
]
