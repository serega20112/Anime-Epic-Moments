"""Request container adapter over the Dishka container."""

from __future__ import annotations

from dishka import AsyncContainer
from backend.infrastructure.repositories.user_repository import UserRepository

from backend.application.use_cases import AddAnimeCommentUseCase
from backend.application.use_cases import AddCollectionItemUseCase
from backend.application.use_cases import AddWatchSourceUseCase
from backend.application.use_cases import (
    AskAiRecommendationsUseCase,
)
from backend.application.use_cases import (
    CreateSupportTicketUseCase,
)
from backend.application.use_cases import DeleteHighlightUseCase
from backend.application.use_cases import (
    GenerateRecommendationsUseCase,
)
from backend.application.use_cases import GetAnimeDiscussionUseCase
from backend.application.use_cases import GetFavoritesUseCase
from backend.application.use_cases import (
    GetLikedHighlightsUseCase,
)
from backend.application.use_cases import GetProfileOverviewUseCase
from backend.application.use_cases import (
    GetPublicProfileOverviewUseCase,
)
from backend.application.use_cases import (
    GetPublicTopHighlightsUseCase,
)
from backend.application.use_cases import GetSeasonPopularUseCase
from backend.application.use_cases import (
    GetUserCollectionsUseCase,
)
from backend.application.use_cases import GetWatchPageUseCase
from backend.application.use_cases import LogoutUserUseCase
from backend.application.use_cases import (
    RefreshRecommendationsUseCase,
)
from backend.application.use_cases import RefreshSessionUseCase
from backend.application.use_cases import RegisterUserUseCase
from backend.application.use_cases import (
    RemoveCollectionItemUseCase,
)
from backend.application.use_cases import (
    RequestEmailVerificationUseCase,
)
from backend.application.use_cases import RequestPasswordResetUseCase
from backend.application.use_cases import (
    ResendEmailVerificationUseCase,
)
from backend.application.use_cases import SearchAnimeUseCase
from backend.application.use_cases import (
    SetAnimeCommentLikeUseCase,
)
from backend.application.use_cases import SetHighlightLikeUseCase
from backend.application.use_cases import SetUserFollowUseCase
from backend.application.use_cases import SyncWatchSourcesUseCase
from backend.application.use_cases import UpdateUserProfileUseCase
from backend.application.use_cases import (
    UpsertUserAnimeStatusUseCase,
)
from backend.application.use_cases import VerifyEmailUseCase
from backend.application.use_cases.anime.autocomplete_anime import AutocompleteAnimeUseCase
from backend.application.use_cases.anime.get_home_page import GetHomePageUseCase
from backend.application.use_cases.anime.search_anime_by_description import (
    SearchAnimeByDescriptionUseCase,
)
from backend.application.use_cases.auth.login_user import LoginUserUseCase
from backend.application.use_cases.auth.reset_password import ResetPasswordUseCase
from backend.application.use_cases.collection.create_collection import CreateCollectionUseCase
from backend.application.use_cases.collection.get_shared_collection import (
    GetSharedCollectionUseCase,
)
from backend.application.use_cases.favorite.add_favorite import AddFavoriteUseCase
from backend.application.use_cases.favorite.remove_favorite import RemoveFavoriteUseCase
from backend.application.use_cases.highlight.add_highlight_comment import (
    AddHighlightCommentUseCase,
)
from backend.application.use_cases.highlight.create_highlight import CreateHighlightUseCase
from backend.application.use_cases.highlight.edit_highlight import EditHighlightUseCase
from backend.application.use_cases.highlight.get_highlight_comments import (
    GetHighlightCommentsUseCase,
)
from backend.application.use_cases.highlight.get_highlight_feed import GetHighlightFeedUseCase
from backend.application.use_cases.highlight.get_highlight_likers import GetHighlightLikersUseCase
from backend.application.use_cases.highlight.get_highlight_notifications import (
    GetHighlightNotificationsUseCase,
)
from backend.application.use_cases.highlight.get_saved_highlights import (
    GetSavedHighlightsUseCase,
)
from backend.application.use_cases.highlight.get_shared_highlight import (
    GetSharedHighlightUseCase,
)
from backend.application.use_cases.highlight.get_user_highlights import GetUserHighlightsUseCase
from backend.application.use_cases.highlight.set_saved_highlight import SetSavedHighlightUseCase
from backend.application.use_cases.user.get_following_highlights import (
    GetFollowingHighlightsUseCase,
)
from backend.application.use_cases.watch.create_watch_highlight import (
    CreateWatchHighlightUseCase,
)
from backend.application.use_cases.watch.save_viewing_session import SaveViewingSessionUseCase
from backend.infrastructure.repositories.collection_repository import CollectionRepository
from backend.infrastructure.repositories.favorite_repository import FavoriteRepository
from backend.infrastructure.repositories.highlight_repository import HighlightRepository
from backend.infrastructure.repositories.support_repository import SupportRepository
from backend.infrastructure.repositories.watch_repository import WatchRepository
from backend.infrastructure.security.jwt_service import JWTService
from backend.infrastructure.security.token_blocklist import TokenBlocklist


class RequestContainer:
    """Adapter exposing the old container API over Dishka."""

    def __init__(self, dishka: AsyncContainer):
        """Initialize the adapter.

        Args:
            dishka: Dishka async container.
        """
        self._dishka = dishka

    async def get(self, dependency_type):
        """Resolve a dependency from the Dishka container.

        Args:
            dependency_type: Type to resolve.

        Returns:
            object: Resolved dependency.
        """
        return await self._dishka.get(dependency_type)

    @property
    def user_repository(self) -> UserRepository:
        """Return the user repository.

        Returns:
            UserRepository: User repository.
        """
        return self._sync_get(UserRepository)

    @property
    def highlight_repository(self) -> HighlightRepository:
        """Return the highlight repository.

        Returns:
            HighlightRepository: Highlight repository.
        """
        return self._sync_get(HighlightRepository)

    @property
    def favorite_repository(self) -> FavoriteRepository:
        """Return the favorite repository.

        Returns:
            FavoriteRepository: Favorite repository.
        """
        return self._sync_get(FavoriteRepository)

    @property
    def collection_repository(self) -> CollectionRepository:
        """Return the collection repository.

        Returns:
            CollectionRepository: Collection repository.
        """
        return self._sync_get(CollectionRepository)

    @property
    def watch_repository(self) -> WatchRepository:
        """Return the watch repository.

        Returns:
            WatchRepository: Watch repository.
        """
        return self._sync_get(WatchRepository)

    @property
    def support_repository(self) -> SupportRepository:
        """Return the support repository.

        Returns:
            SupportRepository: Support repository.
        """
        return self._sync_get(SupportRepository)

    @property
    def jwt_service(self) -> JWTService:
        """Return the JWT service.

        Returns:
            JWTService: JWT service.
        """
        return self._sync_get(JWTService)

    @property
    def token_blocklist(self) -> TokenBlocklist:
        """Return the token blocklist.

        Returns:
            TokenBlocklist: Token blocklist.
        """
        return self._sync_get(TokenBlocklist)

    def _sync_get(self, dependency_type):
        """Synchronously resolve a dependency.

        When called from an already-running event loop (async route handlers),
        `run_until_complete` is not allowed, so the resolution is driven on a
        short-lived loop in a worker thread.

        Args:
            dependency_type: Type to resolve.

        Returns:
            object: Resolved dependency.
        """
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        async def _resolve():
            return await self._dishka.get(dependency_type)

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(_resolve())

        with ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(asyncio.run, _resolve()).result()

    def register_user_use_case(self) -> RegisterUserUseCase:
        """Return the register user use case.

        Returns:
            RegisterUserUseCase: Use case.
        """
        return self._sync_get(RegisterUserUseCase)

    def request_email_verification_use_case(self) -> RequestEmailVerificationUseCase:
        """Return the request email verification use case.

        Returns:
            RequestEmailVerificationUseCase: Use case.
        """
        return self._sync_get(RequestEmailVerificationUseCase)

    def resend_email_verification_use_case(self) -> ResendEmailVerificationUseCase:
        """Return the resend email verification use case.

        Returns:
            ResendEmailVerificationUseCase: Use case.
        """
        return self._sync_get(ResendEmailVerificationUseCase)

    def verify_email_use_case(self) -> VerifyEmailUseCase:
        """Return the verify email use case.

        Returns:
            VerifyEmailUseCase: Use case.
        """
        return self._sync_get(VerifyEmailUseCase)

    def login_user_use_case(self) -> LoginUserUseCase:
        """Return the login user use case.

        Returns:
            LoginUserUseCase: Use case.
        """
        return self._sync_get(LoginUserUseCase)

    def logout_user_use_case(self) -> LogoutUserUseCase:
        """Return the logout user use case.

        Returns:
            LogoutUserUseCase: Use case.
        """
        return self._sync_get(LogoutUserUseCase)

    def refresh_session_use_case(self) -> RefreshSessionUseCase:
        """Return the refresh session use case.

        Returns:
            RefreshSessionUseCase: Use case.
        """
        return self._sync_get(RefreshSessionUseCase)

    def update_user_profile_use_case(self) -> UpdateUserProfileUseCase:
        """Return the update user profile use case.

        Returns:
            UpdateUserProfileUseCase: Use case.
        """
        return self._sync_get(UpdateUserProfileUseCase)

    def get_profile_overview_use_case(self) -> GetProfileOverviewUseCase:
        """Return the get profile overview use case.

        Returns:
            GetProfileOverviewUseCase: Use case.
        """
        return self._sync_get(GetProfileOverviewUseCase)

    def request_password_reset_use_case(self) -> RequestPasswordResetUseCase:
        """Return the request password reset use case.

        Returns:
            RequestPasswordResetUseCase: Use case.
        """
        return self._sync_get(RequestPasswordResetUseCase)

    def reset_password_use_case(self) -> ResetPasswordUseCase:
        """Return the reset password use case.

        Returns:
            ResetPasswordUseCase: Use case.
        """
        return self._sync_get(ResetPasswordUseCase)

    def create_highlight_use_case(self) -> CreateHighlightUseCase:
        """Return the create highlight use case.

        Returns:
            CreateHighlightUseCase: Use case.
        """
        return self._sync_get(CreateHighlightUseCase)

    def delete_highlight_use_case(self) -> DeleteHighlightUseCase:
        """Return the delete highlight use case.

        Returns:
            DeleteHighlightUseCase: Use case.
        """
        return self._sync_get(DeleteHighlightUseCase)

    def edit_highlight_use_case(self) -> EditHighlightUseCase:
        """Return the edit highlight use case.

        Returns:
            EditHighlightUseCase: Use case.
        """
        return self._sync_get(EditHighlightUseCase)

    def get_user_highlights_use_case(self) -> GetUserHighlightsUseCase:
        """Return the get user highlights use case.

        Returns:
            GetUserHighlightsUseCase: Use case.
        """
        return self._sync_get(GetUserHighlightsUseCase)

    def get_public_top_highlights_use_case(self) -> GetPublicTopHighlightsUseCase:
        """Return the get public top highlights use case.

        Returns:
            GetPublicTopHighlightsUseCase: Use case.
        """
        return self._sync_get(GetPublicTopHighlightsUseCase)

    def get_saved_highlights_use_case(self) -> GetSavedHighlightsUseCase:
        """Return the get saved highlights use case.

        Returns:
            GetSavedHighlightsUseCase: Use case.
        """
        return self._sync_get(GetSavedHighlightsUseCase)

    def get_liked_highlights_use_case(self) -> GetLikedHighlightsUseCase:
        """Return the get liked highlights use case.

        Returns:
            GetLikedHighlightsUseCase: Use case.
        """
        return self._sync_get(GetLikedHighlightsUseCase)

    def get_shared_highlight_use_case(self) -> GetSharedHighlightUseCase:
        """Return the get shared highlight use case.

        Returns:
            GetSharedHighlightUseCase: Use case.
        """
        return self._sync_get(GetSharedHighlightUseCase)

    def get_highlight_feed_use_case(self) -> GetHighlightFeedUseCase:
        """Return the get highlight feed use case.

        Returns:
            GetHighlightFeedUseCase: Use case.
        """
        return self._sync_get(GetHighlightFeedUseCase)

    def get_following_highlights_use_case(self) -> GetFollowingHighlightsUseCase:
        """Return the get following highlights use case.

        Returns:
            GetFollowingHighlightsUseCase: Use case.
        """
        return self._sync_get(GetFollowingHighlightsUseCase)

    def set_user_follow_use_case(self) -> SetUserFollowUseCase:
        """Return the set user follow use case.

        Returns:
            SetUserFollowUseCase: Use case.
        """
        return self._sync_get(SetUserFollowUseCase)

    def get_public_profile_overview_use_case(self) -> GetPublicProfileOverviewUseCase:
        """Return the get public profile overview use case.

        Returns:
            GetPublicProfileOverviewUseCase: Use case.
        """
        return self._sync_get(GetPublicProfileOverviewUseCase)

    def set_highlight_like_use_case(self) -> SetHighlightLikeUseCase:
        """Return the set highlight like use case.

        Returns:
            SetHighlightLikeUseCase: Use case.
        """
        return self._sync_get(SetHighlightLikeUseCase)

    def add_highlight_comment_use_case(self) -> AddHighlightCommentUseCase:
        """Return the add highlight comment use case.

        Returns:
            AddHighlightCommentUseCase: Use case.
        """
        return self._sync_get(AddHighlightCommentUseCase)

    def get_highlight_comments_use_case(self) -> GetHighlightCommentsUseCase:
        """Return the get highlight comments use case.

        Returns:
            GetHighlightCommentsUseCase: Use case.
        """
        return self._sync_get(GetHighlightCommentsUseCase)

    def get_highlight_likers_use_case(self) -> GetHighlightLikersUseCase:
        """Return the get highlight likers use case.

        Returns:
            GetHighlightLikersUseCase: Use case.
        """
        return self._sync_get(GetHighlightLikersUseCase)

    def get_highlight_notifications_use_case(self) -> GetHighlightNotificationsUseCase:
        """Return the get highlight notifications use case.

        Returns:
            GetHighlightNotificationsUseCase: Use case.
        """
        return self._sync_get(GetHighlightNotificationsUseCase)

    def set_saved_highlight_use_case(self) -> SetSavedHighlightUseCase:
        """Return the set saved highlight use case.

        Returns:
            SetSavedHighlightUseCase: Use case.
        """
        return self._sync_get(SetSavedHighlightUseCase)

    def add_favorite_use_case(self) -> AddFavoriteUseCase:
        """Return the add favorite use case.

        Returns:
            AddFavoriteUseCase: Use case.
        """
        return self._sync_get(AddFavoriteUseCase)

    def remove_favorite_use_case(self) -> RemoveFavoriteUseCase:
        """Return the remove favorite use case.

        Returns:
            RemoveFavoriteUseCase: Use case.
        """
        return self._sync_get(RemoveFavoriteUseCase)

    def get_favorites_use_case(self) -> GetFavoritesUseCase:
        """Return the get favorites use case.

        Returns:
            GetFavoritesUseCase: Use case.
        """
        return self._sync_get(GetFavoritesUseCase)

    def create_collection_use_case(self) -> CreateCollectionUseCase:
        """Return the create collection use case.

        Returns:
            CreateCollectionUseCase: Use case.
        """
        return self._sync_get(CreateCollectionUseCase)

    def add_collection_item_use_case(self) -> AddCollectionItemUseCase:
        """Return the add collection item use case.

        Returns:
            AddCollectionItemUseCase: Use case.
        """
        return self._sync_get(AddCollectionItemUseCase)

    def remove_collection_item_use_case(self) -> RemoveCollectionItemUseCase:
        """Return the remove collection item use case.

        Returns:
            RemoveCollectionItemUseCase: Use case.
        """
        return self._sync_get(RemoveCollectionItemUseCase)

    def get_user_collections_use_case(self) -> GetUserCollectionsUseCase:
        """Return the get user collections use case.

        Returns:
            GetUserCollectionsUseCase: Use case.
        """
        return self._sync_get(GetUserCollectionsUseCase)

    def get_shared_collection_use_case(self) -> GetSharedCollectionUseCase:
        """Return the get shared collection use case.

        Returns:
            GetSharedCollectionUseCase: Use case.
        """
        return self._sync_get(GetSharedCollectionUseCase)

    def search_anime_use_case(self) -> SearchAnimeUseCase:
        """Return the search anime use case.

        Returns:
            SearchAnimeUseCase: Use case.
        """
        return self._sync_get(SearchAnimeUseCase)

    def search_anime_by_description_use_case(self) -> SearchAnimeByDescriptionUseCase:
        """Return the search by description use case.

        Returns:
            SearchAnimeByDescriptionUseCase: Use case.
        """
        return self._sync_get(SearchAnimeByDescriptionUseCase)

    def autocomplete_anime_use_case(self) -> AutocompleteAnimeUseCase:
        """Return the autocomplete use case.

        Returns:
            AutocompleteAnimeUseCase: Use case.
        """
        return self._sync_get(AutocompleteAnimeUseCase)

    def get_home_page_use_case(self) -> GetHomePageUseCase:
        """Return the home page use case.

        Returns:
            GetHomePageUseCase: Use case.
        """
        return self._sync_get(GetHomePageUseCase)

    def get_season_popular_use_case(self) -> GetSeasonPopularUseCase:
        """Return the season popular use case.

        Returns:
            GetSeasonPopularUseCase: Use case.
        """
        return self._sync_get(GetSeasonPopularUseCase)

    def generate_recommendations_use_case(self) -> GenerateRecommendationsUseCase:
        """Return the generate recommendations use case.

        Returns:
            GenerateRecommendationsUseCase: Use case.
        """
        return self._sync_get(GenerateRecommendationsUseCase)

    def ask_ai_recommendations_use_case(self) -> AskAiRecommendationsUseCase:
        """Return the ask AI recommendations use case.

        Returns:
            AskAiRecommendationsUseCase: Use case.
        """
        return self._sync_get(AskAiRecommendationsUseCase)

    def refresh_recommendations_use_case(self) -> RefreshRecommendationsUseCase:
        """Return the refresh recommendations use case.

        Returns:
            RefreshRecommendationsUseCase: Use case.
        """
        return self._sync_get(RefreshRecommendationsUseCase)

    def create_support_ticket_use_case(self) -> CreateSupportTicketUseCase:
        """Return the create support ticket use case.

        Returns:
            CreateSupportTicketUseCase: Use case.
        """
        return self._sync_get(CreateSupportTicketUseCase)

    def get_watch_page_use_case(self) -> GetWatchPageUseCase:
        """Return the get watch page use case.

        Returns:
            GetWatchPageUseCase: Use case.
        """
        return self._sync_get(GetWatchPageUseCase)

    def add_watch_source_use_case(self) -> AddWatchSourceUseCase:
        """Return the add watch source use case.

        Returns:
            AddWatchSourceUseCase: Use case.
        """
        return self._sync_get(AddWatchSourceUseCase)

    def sync_watch_sources_use_case(self) -> SyncWatchSourcesUseCase:
        """Return the sync watch sources use case.

        Returns:
            SyncWatchSourcesUseCase: Use case.
        """
        return self._sync_get(SyncWatchSourcesUseCase)

    def upsert_user_anime_status_use_case(self) -> UpsertUserAnimeStatusUseCase:
        """Return the upsert user anime status use case.

        Returns:
            UpsertUserAnimeStatusUseCase: Use case.
        """
        return self._sync_get(UpsertUserAnimeStatusUseCase)

    def save_viewing_session_use_case(self) -> SaveViewingSessionUseCase:
        """Return the save viewing session use case.

        Returns:
            SaveViewingSessionUseCase: Use case.
        """
        return self._sync_get(SaveViewingSessionUseCase)

    def add_anime_comment_use_case(self) -> AddAnimeCommentUseCase:
        """Return the add anime comment use case.

        Returns:
            AddAnimeCommentUseCase: Use case.
        """
        return self._sync_get(AddAnimeCommentUseCase)

    def get_anime_discussion_use_case(self) -> GetAnimeDiscussionUseCase:
        """Return the get anime discussion use case.

        Returns:
            GetAnimeDiscussionUseCase: Use case.
        """
        return self._sync_get(GetAnimeDiscussionUseCase)

    def set_anime_comment_like_use_case(self) -> SetAnimeCommentLikeUseCase:
        """Return the set anime comment like use case.

        Returns:
            SetAnimeCommentLikeUseCase: Use case.
        """
        return self._sync_get(SetAnimeCommentLikeUseCase)

    def create_watch_highlight_use_case(self) -> CreateWatchHighlightUseCase:
        """Return the create watch highlight use case.

        Returns:
            CreateWatchHighlightUseCase: Use case.
        """
        return self._sync_get(CreateWatchHighlightUseCase)
