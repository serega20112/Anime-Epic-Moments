"""ORM-модели SQLAlchemy."""

from backend.infrastructure.database.models.collection import (
    AnimeCollectionItemModel,
    AnimeCollectionModel,
)
from backend.infrastructure.database.models.favorite import FavoriteModel
from backend.infrastructure.database.models.highlight import (
    HighlightCommentModel,
    HighlightContextModel,
    HighlightLikeModel,
    HighlightModel,
    SavedHighlightModel,
)
from backend.infrastructure.database.models.moment import ViewingMomentModel
from backend.infrastructure.database.models.rating import UserAnimeRatingModel
from backend.infrastructure.database.models.reaction import EpisodeReactionModel
from backend.infrastructure.database.models.support import SupportTicketModel
from backend.infrastructure.database.models.user import UserFollowModel, UserModel
from backend.infrastructure.database.models.watch import (
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
    "UserAnimeRatingModel",
    "UserAnimeStatusModel",
    "UserFollowModel",
    "UserModel",
    "ViewingMomentModel",
    "ViewingSessionModel",
    "WatchSourceModel",
]
