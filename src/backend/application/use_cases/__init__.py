"""Application use cases facade."""

from __future__ import annotations

from backend.application.use_cases.watch.add_anime_comment import AddAnimeCommentUseCase
from backend.application.use_cases.collection.add_collection_item import AddCollectionItemUseCase
from backend.application.use_cases.watch.add_watch_source import AddWatchSourceUseCase
from backend.application.use_cases.recommendation.ask_ai_recommendations import AskAiRecommendationsUseCase
from backend.application.use_cases.support.create_support_ticket import CreateSupportTicketUseCase
from backend.application.use_cases.highlight.delete_highlight import DeleteHighlightUseCase
from backend.application.use_cases.recommendation.generate_recommendations import GenerateRecommendationsUseCase
from backend.application.use_cases.watch.get_anime_discussion import GetAnimeDiscussionUseCase
from backend.application.use_cases.favorite.get_favorites import GetFavoritesUseCase
from backend.application.use_cases.highlight.get_liked_highlights import GetLikedHighlightsUseCase
from backend.application.use_cases.auth.get_profile_overview import GetProfileOverviewUseCase
from backend.application.use_cases.user.get_public_profile_overview import GetPublicProfileOverviewUseCase
from backend.application.use_cases.highlight.get_public_top_highlights import GetPublicTopHighlightsUseCase
from backend.application.use_cases.anime.get_season_popular import GetSeasonPopularUseCase
from backend.application.use_cases.collection.get_user_collections import GetUserCollectionsUseCase
from backend.application.use_cases.watch.get_watch_page import GetWatchPageUseCase
from backend.application.use_cases.highlight.result import HighlightResult
from backend.application.use_cases.auth.logout_user import LogoutUserUseCase
from backend.application.use_cases.recommendation.result import RecommendationUseCaseResult
from backend.application.use_cases.recommendation.refresh_recommendations import RefreshRecommendationsUseCase
from backend.application.use_cases.auth.refresh_session import RefreshSessionUseCase
from backend.application.use_cases.auth.register_user import RegisterUserUseCase
from backend.application.use_cases.collection.remove_collection_item import RemoveCollectionItemUseCase
from backend.application.use_cases.auth.request_email_verification import RequestEmailVerificationUseCase
from backend.application.use_cases.auth.request_password_reset import RequestPasswordResetUseCase
from backend.application.use_cases.auth.resend_email_verification import ResendEmailVerificationUseCase
from backend.application.use_cases.anime.search_anime import SearchAnimeUseCase
from backend.application.use_cases.watch.set_anime_comment_like import SetAnimeCommentLikeUseCase
from backend.application.use_cases.highlight.set_highlight_like import SetHighlightLikeUseCase
from backend.application.use_cases.user.set_user_follow import SetUserFollowUseCase
from backend.application.use_cases.watch.sync_watch_sources import SyncWatchSourcesUseCase
from backend.application.use_cases.auth.update_user_profile import UpdateUserProfileUseCase
from backend.application.use_cases.watch.upsert_user_anime_status import UpsertUserAnimeStatusUseCase
from backend.application.use_cases.user.result import UserResult
from backend.application.use_cases.auth.verify_email import VerifyEmailUseCase
from backend.application.use_cases.watch.result import WatchResult

__all__ = [
    "AddAnimeCommentUseCase",
    "AddCollectionItemUseCase",
    "AddWatchSourceUseCase",
    "AskAiRecommendationsUseCase",
    "CreateSupportTicketUseCase",
    "DeleteHighlightUseCase",
    "GenerateRecommendationsUseCase",
    "GetAnimeDiscussionUseCase",
    "GetFavoritesUseCase",
    "GetLikedHighlightsUseCase",
    "GetProfileOverviewUseCase",
    "GetPublicProfileOverviewUseCase",
    "GetPublicTopHighlightsUseCase",
    "GetSeasonPopularUseCase",
    "GetUserCollectionsUseCase",
    "GetWatchPageUseCase",
    "HighlightResult",
    "LogoutUserUseCase",
    "RecommendationUseCaseResult",
    "RefreshRecommendationsUseCase",
    "RefreshSessionUseCase",
    "RegisterUserUseCase",
    "RemoveCollectionItemUseCase",
    "RequestEmailVerificationUseCase",
    "RequestPasswordResetUseCase",
    "ResendEmailVerificationUseCase",
    "SearchAnimeUseCase",
    "SetAnimeCommentLikeUseCase",
    "SetHighlightLikeUseCase",
    "SetUserFollowUseCase",
    "SyncWatchSourcesUseCase",
    "UpdateUserProfileUseCase",
    "UpsertUserAnimeStatusUseCase",
    "UserResult",
    "VerifyEmailUseCase",
    "WatchResult",
]
