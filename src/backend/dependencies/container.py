"""
DI контейнер приложения
"""

from src.backend.infrastructure.files.database import get_session
from src.backend.infrastructure.repositories.user_repository import UserRepository
from src.backend.infrastructure.repositories.highlight_repository import (
    HighlightRepository,
)
from src.backend.infrastructure.repositories.favorite_repository import (
    FavoriteRepository,
)
from src.backend.infrastructure.repositories.watch_repository import WatchRepository
from src.backend.use_case.auth.register_user import RegisterUserUseCase
from src.backend.use_case.auth.login_user import LoginUserUseCase
from src.backend.use_case.auth.logout_user import LogoutUserUseCase
from src.backend.use_case.auth.update_user_profile import UpdateUserProfileUseCase
from src.backend.use_case.auth.request_password_reset import RequestPasswordResetUseCase
from src.backend.use_case.auth.reset_password import ResetPasswordUseCase
from src.backend.use_case.highlight.create_highlight import CreateHighlightUseCase
from src.backend.use_case.highlight.delete_highlight import DeleteHighlightUseCase
from src.backend.use_case.highlight.edit_highlight import EditHighlightUseCase
from src.backend.use_case.highlight.get_user_highlights import GetUserHighlightsUseCase
from src.backend.use_case.highlight.get_public_top_highlights import (
    GetPublicTopHighlightsUseCase,
)
from src.backend.use_case.favorite.add_favorite import AddFavoriteUseCase
from src.backend.use_case.favorite.remove_favorite import RemoveFavoriteUseCase
from src.backend.use_case.favorite.get_favorites import GetFavoritesUseCase
from src.backend.use_case.anime.search_anime import SearchAnimeUseCase
from src.backend.use_case.anime.search_anime_by_description import (
    SearchAnimeByDescriptionUseCase,
)
from src.backend.use_case.anime.autocomplete_anime import AutocompleteAnimeUseCase
from src.backend.use_case.anime.get_season_popular import GetSeasonPopularUseCase
from src.backend.use_case.recommendation.generate_recommendations import (
    GenerateRecommendationsUseCase,
)
from src.backend.use_case.recommendation.refresh_recommendations import (
    RefreshRecommendationsUseCase,
)
from src.backend.use_case.watch.add_watch_source import AddWatchSourceUseCase
from src.backend.use_case.watch.create_watch_highlight import (
    CreateWatchHighlightUseCase,
)
from src.backend.use_case.watch.get_watch_page import GetWatchPageUseCase
from src.backend.use_case.watch.save_viewing_session import SaveViewingSessionUseCase
from src.backend.use_case.watch.sync_watch_sources import SyncWatchSourcesUseCase
from src.backend.use_case.watch.upsert_user_anime_status import (
    UpsertUserAnimeStatusUseCase,
)
from src.backend.services.recommendation_service import RecommendationService
from src.backend.services.watch_source_sync_service import WatchSourceSyncService
from src.backend.infrastructure.external.anilibria_client import AniLibriaClient
from src.backend.infrastructure.external.anime_api_client import AnimeApiClient
from src.backend.infrastructure.external.huggingface_llm_client import (
    HuggingFaceLLMClient,
)
from src.backend.infrastructure.external.kodik_client import KodikClient
from src.backend.infrastructure.external.password_reset_mailer import (
    PasswordResetMailer,
)
from src.backend.infrastructure.security.password_service import PasswordService
from src.backend.infrastructure.security.jwt_service import JWTService
from src.backend.dependencies.settings import Settings


class Container:
    """
    Dependency Injection контейнер
    """

    def __init__(self):
        self.db_session = get_session()
        self.anime_api_client = AnimeApiClient()
        self.kodik_client = KodikClient()
        self.anilibria_client = AniLibriaClient()
        self.hf_llm_client = HuggingFaceLLMClient(
            api_key=Settings.hf_token,
            model=Settings.hf_model,
            provider=Settings.hf_provider,
            api_url=Settings.hf_api_url,
        )
        if not Settings.hf_token:
            print(
                "! HF_TOKEN не задан: поиск по описанию работает в fallback-режиме без LLM"
            )

        self.user_repository = UserRepository(self.db_session)
        self.highlight_repository = HighlightRepository(self.db_session)
        self.favorite_repository = FavoriteRepository(self.db_session)
        self.watch_repository = WatchRepository(self.db_session)

        # Recommendation service для генерации рекомендаций
        self.recommendation_service = RecommendationService(
            self.favorite_repository,
            self.highlight_repository,
            self.anime_api_client,
        )
        self.watch_source_sync_service = WatchSourceSyncService(
            self.watch_repository,
            [
                self.kodik_client,
                self.anilibria_client,
            ],
        )

        self.password_service = PasswordService()
        self.jwt_service = JWTService()
        self.password_reset_mailer = PasswordResetMailer()

        self.register_user_use_case = lambda: RegisterUserUseCase(
            self.user_repository, self.password_service
        )
        self.login_user_use_case = lambda: LoginUserUseCase(
            self.user_repository, self.password_service
        )
        self.logout_user_use_case = lambda: LogoutUserUseCase(self.user_repository)
        self.update_user_profile_use_case = lambda: UpdateUserProfileUseCase(
            self.user_repository
        )
        self.request_password_reset_use_case = lambda: RequestPasswordResetUseCase(
            self.user_repository, self.jwt_service, self.password_reset_mailer
        )
        self.reset_password_use_case = lambda: ResetPasswordUseCase(
            self.user_repository, self.jwt_service, self.password_service
        )

        self.create_highlight_use_case = lambda: CreateHighlightUseCase(
            self.highlight_repository
        )
        self.delete_highlight_use_case = lambda: DeleteHighlightUseCase(
            self.highlight_repository
        )
        self.edit_highlight_use_case = lambda: EditHighlightUseCase(
            self.highlight_repository
        )
        self.get_user_highlights_use_case = lambda: GetUserHighlightsUseCase(
            self.highlight_repository, self.anime_api_client
        )
        self.get_public_top_highlights_use_case = lambda: GetPublicTopHighlightsUseCase(
            self.highlight_repository, self.anime_api_client
        )

        self.add_favorite_use_case = lambda: AddFavoriteUseCase(
            self.favorite_repository
        )
        self.remove_favorite_use_case = lambda: RemoveFavoriteUseCase(
            self.favorite_repository
        )
        self.get_favorites_use_case = lambda: GetFavoritesUseCase(
            self.favorite_repository, self.anime_api_client
        )

        self.search_anime_use_case = lambda: SearchAnimeUseCase(self.anime_api_client)
        self.search_anime_by_description_use_case = (
            lambda: SearchAnimeByDescriptionUseCase(
                self.anime_api_client, self.hf_llm_client
            )
        )
        self.autocomplete_anime_use_case = lambda: AutocompleteAnimeUseCase(
            self.anime_api_client
        )
        self.get_season_popular_use_case = lambda: GetSeasonPopularUseCase(
            self.anime_api_client
        )

        self.generate_recommendations_use_case = lambda: GenerateRecommendationsUseCase(
            self.recommendation_service
        )
        self.refresh_recommendations_use_case = lambda: RefreshRecommendationsUseCase(
            self.recommendation_service
        )
        self.get_watch_page_use_case = lambda: GetWatchPageUseCase(
            self.watch_repository,
            self.highlight_repository,
            self.anime_api_client,
            self.watch_source_sync_service,
        )
        self.sync_watch_sources_use_case = lambda: SyncWatchSourcesUseCase(
            self.anime_api_client,
            self.watch_source_sync_service,
        )
        self.upsert_user_anime_status_use_case = lambda: UpsertUserAnimeStatusUseCase(
            self.watch_repository
        )
        self.add_watch_source_use_case = lambda: AddWatchSourceUseCase(
            self.watch_repository
        )
        self.save_viewing_session_use_case = lambda: SaveViewingSessionUseCase(
            self.watch_repository
        )
        self.create_watch_highlight_use_case = lambda: CreateWatchHighlightUseCase(
            CreateHighlightUseCase(self.highlight_repository), self.watch_repository
        )


container = Container()
