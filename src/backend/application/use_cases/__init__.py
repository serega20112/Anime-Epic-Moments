"""Application use cases facade."""

from __future__ import annotations

from backend.application.use_cases.anime.filter_anime_catalog import FilterAnimeCatalogUseCase
from backend.application.use_cases.anime.get_season_popular import GetSeasonPopularUseCase
from backend.application.use_cases.anime.search_anime import SearchAnimeUseCase
from backend.application.use_cases.anime.search_anime_by_description import (
    SearchAnimeByDescriptionUseCase,
)
from backend.application.use_cases.auth.get_profile_overview import GetProfileOverviewUseCase
from backend.application.use_cases.auth.logout_user import LogoutUserUseCase
from backend.application.use_cases.auth.refresh_session import RefreshSessionUseCase
from backend.application.use_cases.auth.register_user import RegisterUserUseCase
from backend.application.use_cases.auth.request_email_verification import (
    RequestEmailVerificationUseCase,
)
from backend.application.use_cases.auth.request_password_reset import RequestPasswordResetUseCase
from backend.application.use_cases.auth.resend_email_verification import (
    ResendEmailVerificationUseCase,
)
from backend.application.use_cases.auth.update_user_profile import UpdateUserProfileUseCase
from backend.application.use_cases.auth.verify_email import VerifyEmailUseCase
from backend.application.use_cases.collection.add_collection_item import AddCollectionItemUseCase
from backend.application.use_cases.collection.create_collection import CreateCollectionUseCase
from backend.application.use_cases.collection.get_shared_collection import (
    GetSharedCollectionUseCase,
)
from backend.application.use_cases.collection.get_user_collections import GetUserCollectionsUseCase
from backend.application.use_cases.collection.remove_collection_item import (
    RemoveCollectionItemUseCase,
)
from backend.application.use_cases.favorite.get_favorites import GetFavoritesUseCase
from backend.application.use_cases.highlight.add_highlight_comment import (
    AddHighlightCommentUseCase,
)
from backend.application.use_cases.highlight.delete_highlight import DeleteHighlightUseCase
from backend.application.use_cases.highlight.edit_highlight import EditHighlightUseCase
from backend.application.use_cases.highlight.get_highlight_comments import (
    GetHighlightCommentsUseCase,
)
from backend.application.use_cases.highlight.get_highlight_feed import GetHighlightFeedUseCase
from backend.application.use_cases.highlight.get_highlight_likers import (
    GetHighlightLikersUseCase,
)
from backend.application.use_cases.highlight.get_highlight_notifications import (
    GetHighlightNotificationsUseCase,
)
from backend.application.use_cases.highlight.get_liked_highlights import GetLikedHighlightsUseCase
from backend.application.use_cases.highlight.get_public_top_highlights import (
    GetPublicTopHighlightsUseCase,
)
from backend.application.use_cases.highlight.get_saved_highlights import (
    GetSavedHighlightsUseCase,
)
from backend.application.use_cases.highlight.get_shared_highlight import GetSharedHighlightUseCase
from backend.application.use_cases.highlight.get_user_highlights import GetUserHighlightsUseCase
from backend.application.use_cases.highlight.result import HighlightResult
from backend.application.use_cases.highlight.set_highlight_like import SetHighlightLikeUseCase
from backend.application.use_cases.highlight.set_saved_highlight import SetSavedHighlightUseCase
from backend.application.use_cases.moment.delete_viewing_moment import DeleteViewingMomentUseCase
from backend.application.use_cases.moment.get_user_viewing_moments import (
    GetUserViewingMomentsUseCase,
)
from backend.application.use_cases.moment.publish_viewing_moment import PublishViewingMomentUseCase
from backend.application.use_cases.moment.result import MomentResult
from backend.application.use_cases.moment.save_viewing_moment import SaveViewingMomentUseCase
from backend.application.use_cases.reaction.get_episode_reactions import (
    GetEpisodeReactionsUseCase,
)
from backend.application.use_cases.reaction.result import ReactionResult
from backend.application.use_cases.reaction.set_episode_reaction import (
    SetEpisodeReactionUseCase,
)
from backend.application.use_cases.recommendation.ask_ai_recommendations import (
    AskAiRecommendationsUseCase,
)
from backend.application.use_cases.recommendation.generate_recommendations import (
    GenerateRecommendationsUseCase,
)
from backend.application.use_cases.recommendation.refresh_recommendations import (
    RefreshRecommendationsUseCase,
)
from backend.application.use_cases.recommendation.result import RecommendationUseCaseResult
from backend.application.use_cases.support.create_support_ticket import CreateSupportTicketUseCase
from backend.application.use_cases.user.get_following_highlights import (
    GetFollowingHighlightsUseCase,
)
from backend.application.use_cases.user.get_public_profile_overview import (
    GetPublicProfileOverviewUseCase,
)
from backend.application.use_cases.user.result import UserResult
from backend.application.use_cases.user.set_user_follow import SetUserFollowUseCase
from backend.application.use_cases.watch.add_anime_comment import AddAnimeCommentUseCase
from backend.application.use_cases.watch.add_watch_source import AddWatchSourceUseCase
from backend.application.use_cases.watch.get_anime_discussion import GetAnimeDiscussionUseCase
from backend.application.use_cases.watch.get_watch_page import GetWatchPageUseCase
from backend.application.use_cases.watch.result import WatchResult
from backend.application.use_cases.watch.set_anime_comment_like import SetAnimeCommentLikeUseCase
from backend.application.use_cases.watch.sync_watch_sources import SyncWatchSourcesUseCase
from backend.application.use_cases.watch.upsert_user_anime_status import (
    UpsertUserAnimeStatusUseCase,
)

__all__ = [
    "AddAnimeCommentUseCase",
    "AddCollectionItemUseCase",
    "AddHighlightCommentUseCase",
    "AddWatchSourceUseCase",
    "AskAiRecommendationsUseCase",
    "CreateCollectionUseCase",
    "CreateSupportTicketUseCase",
    "DeleteHighlightUseCase",
    "DeleteViewingMomentUseCase",
    "EditHighlightUseCase",
    "FilterAnimeCatalogUseCase",
    "GenerateRecommendationsUseCase",
    "GetAnimeDiscussionUseCase",
    "GetFavoritesUseCase",
    "GetFollowingHighlightsUseCase",
    "GetEpisodeReactionsUseCase",
    "GetHighlightCommentsUseCase",
    "GetHighlightFeedUseCase",
    "GetHighlightLikersUseCase",
    "GetHighlightNotificationsUseCase",
    "GetLikedHighlightsUseCase",
    "GetProfileOverviewUseCase",
    "GetPublicProfileOverviewUseCase",
    "GetPublicTopHighlightsUseCase",
    "GetSavedHighlightsUseCase",
    "GetSeasonPopularUseCase",
    "GetSharedCollectionUseCase",
    "GetSharedHighlightUseCase",
    "GetUserCollectionsUseCase",
    "GetUserHighlightsUseCase",
    "GetUserViewingMomentsUseCase",
    "GetWatchPageUseCase",
    "HighlightResult",
    "LogoutUserUseCase",
    "MomentResult",
    "PublishViewingMomentUseCase",
    "RecommendationUseCaseResult",
    "ReactionResult",
    "RefreshRecommendationsUseCase",
    "RefreshSessionUseCase",
    "RegisterUserUseCase",
    "RemoveCollectionItemUseCase",
    "RequestEmailVerificationUseCase",
    "RequestPasswordResetUseCase",
    "ResendEmailVerificationUseCase",
    "SearchAnimeByDescriptionUseCase",
    "SearchAnimeUseCase",
    "SaveViewingMomentUseCase",
    "SetAnimeCommentLikeUseCase",
    "SetEpisodeReactionUseCase",
    "SetHighlightLikeUseCase",
    "SetSavedHighlightUseCase",
    "SetUserFollowUseCase",
    "SyncWatchSourcesUseCase",
    "UpdateUserProfileUseCase",
    "UpsertUserAnimeStatusUseCase",
    "UserResult",
    "VerifyEmailUseCase",
    "WatchResult",
]
