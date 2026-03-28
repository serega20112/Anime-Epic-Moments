from __future__ import annotations

from types import SimpleNamespace

from src.backend.dependencies import container as container_module


def _stub_class(name):
    class _Stub:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    _Stub.__name__ = name
    return _Stub


def test_container_wires_repositories_services_and_use_cases(monkeypatch):
    """Проверяем, что Container связывает репозитории, сервисы и расширенный highlight-слой с ожидаемыми зависимостями."""
    session = object()
    monkeypatch.setattr(container_module, "get_session", lambda: session)
    monkeypatch.setattr(
        container_module,
        "Settings",
        SimpleNamespace(
            hf_token="hf-token",
            hf_model="model",
            hf_provider="provider",
            hf_api_url="https://hf.example/api",
            redis_url="redis://redis:6379/0",
            redis_required=False,
            email_verification_expire_minutes=10,
        ),
    )

    for name in (
        "AnimeApiClient",
        "HighlightDashboardCache",
        "KeyValueStore",
        "KodikClient",
        "AniLibriaClient",
        "YouTubeClient",
        "JustWatchClient",
        "PasswordResetMailer",
        "EmailVerificationMailer",
        "PasswordService",
        "JWTService",
        "EmailVerificationStore",
        "RateLimiter",
        "TokenBlocklist",
        "UserRepository",
        "HighlightRepository",
        "FavoriteRepository",
        "WatchRepository",
        "RecommendationCache",
        "RecommendationService",
        "WatchSourceSyncService",
        "RegisterUserUseCase",
        "LoginUserUseCase",
        "LogoutUserUseCase",
        "UpdateUserProfileUseCase",
        "GetProfileOverviewUseCase",
        "RequestEmailVerificationUseCase",
        "ResendEmailVerificationUseCase",
        "RequestPasswordResetUseCase",
        "ResetPasswordUseCase",
        "VerifyEmailUseCase",
        "CreateHighlightUseCase",
        "DeleteHighlightUseCase",
        "EditHighlightUseCase",
        "GetUserHighlightsUseCase",
        "GetPublicTopHighlightsUseCase",
        "GetSavedHighlightsUseCase",
        "GetLikedHighlightsUseCase",
        "GetSharedHighlightUseCase",
        "GetHighlightFeedUseCase",
        "GetHighlightNotificationsUseCase",
        "SetHighlightLikeUseCase",
        "AddHighlightCommentUseCase",
        "GetHighlightCommentsUseCase",
        "GetHighlightLikersUseCase",
        "SetSavedHighlightUseCase",
        "AddFavoriteUseCase",
        "RemoveFavoriteUseCase",
        "GetFavoritesUseCase",
        "SearchAnimeUseCase",
        "SearchAnimeByDescriptionUseCase",
        "AutocompleteAnimeUseCase",
        "GetSeasonPopularUseCase",
        "GenerateRecommendationsUseCase",
        "RefreshRecommendationsUseCase",
        "CreateWatchHighlightUseCase",
        "GetWatchPageUseCase",
        "SaveViewingSessionUseCase",
        "SyncWatchSourcesUseCase",
        "UpsertUserAnimeStatusUseCase",
        "HuggingFaceLLMClient",
    ):
        monkeypatch.setattr(container_module, name, _stub_class(name))

    built = container_module.Container()

    assert built.db_session is session
    assert built.key_value_store.kwargs == {
        "redis_url": "redis://redis:6379/0",
        "namespace": "anime_epic_moments",
        "required": False,
    }
    assert built.user_repository.args == (session,)
    assert built.highlight_repository.args == (session,)
    assert built.favorite_repository.args == (session,)
    assert built.watch_repository.args == (session,)
    assert built.recommendation_service.args[:3] == (
        built.favorite_repository,
        built.highlight_repository,
        built.anime_api_client,
    )
    assert built.recommendation_cache.kwargs == {"store": built.key_value_store}
    assert built.highlight_dashboard_cache.kwargs == {"store": built.key_value_store}
    assert built.email_verification_store.kwargs == {
        "store": built.key_value_store,
        "ttl_seconds": 600,
    }
    assert built.watch_source_sync_service.args[0] is built.watch_repository
    assert built.request_email_verification_use_case().args == (
        built.user_repository,
        built.password_service,
        built.email_verification_store,
        built.email_verification_mailer,
    )
    assert built.resend_email_verification_use_case().args == (
        built.email_verification_store,
        built.email_verification_mailer,
    )
    assert built.verify_email_use_case().args == (
        built.user_repository,
        built.email_verification_store,
    )
    assert built.get_saved_highlights_use_case().args == (
        built.highlight_repository,
        built.anime_api_client,
    )
    assert built.get_profile_overview_use_case().args == (
        built.user_repository,
        built.highlight_repository,
        built.anime_api_client,
    )
    assert built.get_liked_highlights_use_case().args == (
        built.highlight_repository,
        built.anime_api_client,
    )
    assert built.get_shared_highlight_use_case().args == (
        built.highlight_repository,
        built.anime_api_client,
    )
    assert built.get_highlight_feed_use_case().args == (
        built.highlight_repository,
        built.anime_api_client,
        built.favorite_repository,
    )
    assert built.get_highlight_notifications_use_case().args == (
        built.highlight_repository,
    )



def test_container_builds_watch_highlight_use_case_via_inner_factory(monkeypatch):
    """Проверяем, что Container создает CreateWatchHighlightUseCase через create_highlight_use_case."""
    session = object()
    monkeypatch.setattr(container_module, "get_session", lambda: session)
    monkeypatch.setattr(
        container_module,
        "Settings",
        SimpleNamespace(
            hf_token="hf-token",
            hf_model="model",
            hf_provider="provider",
            hf_api_url="https://hf.example/api",
            redis_url="redis://redis:6379/0",
            redis_required=False,
            email_verification_expire_minutes=10,
        ),
    )

    for name in (
        "AnimeApiClient",
        "HighlightDashboardCache",
        "KeyValueStore",
        "KodikClient",
        "AniLibriaClient",
        "YouTubeClient",
        "JustWatchClient",
        "PasswordResetMailer",
        "EmailVerificationMailer",
        "PasswordService",
        "JWTService",
        "EmailVerificationStore",
        "RateLimiter",
        "TokenBlocklist",
        "UserRepository",
        "HighlightRepository",
        "FavoriteRepository",
        "WatchRepository",
        "RecommendationCache",
        "RecommendationService",
        "WatchSourceSyncService",
        "RegisterUserUseCase",
        "LoginUserUseCase",
        "LogoutUserUseCase",
        "UpdateUserProfileUseCase",
        "GetProfileOverviewUseCase",
        "RequestEmailVerificationUseCase",
        "ResendEmailVerificationUseCase",
        "RequestPasswordResetUseCase",
        "ResetPasswordUseCase",
        "VerifyEmailUseCase",
        "CreateHighlightUseCase",
        "DeleteHighlightUseCase",
        "EditHighlightUseCase",
        "GetUserHighlightsUseCase",
        "GetPublicTopHighlightsUseCase",
        "GetSavedHighlightsUseCase",
        "GetLikedHighlightsUseCase",
        "GetSharedHighlightUseCase",
        "GetHighlightFeedUseCase",
        "GetHighlightNotificationsUseCase",
        "SetHighlightLikeUseCase",
        "AddHighlightCommentUseCase",
        "GetHighlightCommentsUseCase",
        "GetHighlightLikersUseCase",
        "SetSavedHighlightUseCase",
        "AddFavoriteUseCase",
        "RemoveFavoriteUseCase",
        "GetFavoritesUseCase",
        "SearchAnimeUseCase",
        "SearchAnimeByDescriptionUseCase",
        "AutocompleteAnimeUseCase",
        "GetSeasonPopularUseCase",
        "GenerateRecommendationsUseCase",
        "RefreshRecommendationsUseCase",
        "CreateWatchHighlightUseCase",
        "GetWatchPageUseCase",
        "SaveViewingSessionUseCase",
        "SyncWatchSourcesUseCase",
        "UpsertUserAnimeStatusUseCase",
        "HuggingFaceLLMClient",
    ):
        monkeypatch.setattr(container_module, name, _stub_class(name))

    built = container_module.Container()

    first = built.create_watch_highlight_use_case()
    second = built.create_watch_highlight_use_case()

    assert first is not second
    assert first.args[0].args == (
        built.highlight_repository,
        built.recommendation_service,
        built.highlight_dashboard_cache,
    )
    assert first.args[1] is built.watch_repository
