"""SQLAlchemy models facade: re-exports all ORM model classes."""

from backend.infrastructure.models.collection import (
    AnimeCollectionItemModel,
    AnimeCollectionModel,
)
from backend.infrastructure.models.favorite import FavoriteModel
from backend.infrastructure.models.highlight import (
    HighlightCommentModel,
    HighlightContextModel,
    HighlightLikeModel,
    HighlightModel,
    SavedHighlightModel,
)
from backend.infrastructure.models.moment import ViewingMomentModel
from backend.infrastructure.models.reaction import EpisodeReactionModel
from backend.infrastructure.models.support import SupportTicketModel
from backend.infrastructure.models.user import UserFollowModel, UserModel
from backend.infrastructure.models.watch import (
    AnimeDiscussionCommentModel,
    AnimeDiscussionLikeModel,
    TranslationModel,
    UserAnimeStatusModel,
    ViewingSessionModel,
    WatchSourceModel,
)

__all__ = [
    "AnimeCollectionItemModel",
    "AnimeCollectionModel",
    "AnimeDiscussionCommentModel",
    "AnimeDiscussionLikeModel",
    "EpisodeReactionModel",
    "FavoriteModel",
    "HighlightCommentModel",
    "HighlightContextModel",
    "HighlightLikeModel",
    "HighlightModel",
    "SavedHighlightModel",
    "SupportTicketModel",
    "TranslationModel",
    "UserAnimeStatusModel",
    "UserFollowModel",
    "UserModel",
    "ViewingMomentModel",
    "ViewingSessionModel",
    "WatchSourceModel",
]
