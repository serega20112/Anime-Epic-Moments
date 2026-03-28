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
    """Проверяем, что Container связывает репозитории, сервисы и use case с ожидаемыми зависимостями."""
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
        "PasswordService",
        "JWTService",
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
        "RequestPasswordResetUseCase",
        "ResetPasswordUseCase",
        "CreateHighlightUseCase",
        "DeleteHighlightUseCase",
        "EditHighlightUseCase",
        "GetUserHighlightsUseCase",
        "GetPublicTopHighlightsUseCase",
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
    assert built.watch_source_sync_service.args[0] is built.watch_repository
    assert built.search_anime_use_case().args == (built.anime_api_client,)
    assert built.get_favorites_use_case().args == (
        built.favorite_repository,
        built.anime_api_client,
    )
    assert built.sync_watch_sources_use_case().args == (
        built.anime_api_client,
        built.watch_source_sync_service,
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
        "PasswordService",
        "JWTService",
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
        "RequestPasswordResetUseCase",
        "ResetPasswordUseCase",
        "CreateHighlightUseCase",
        "DeleteHighlightUseCase",
        "EditHighlightUseCase",
        "GetUserHighlightsUseCase",
        "GetPublicTopHighlightsUseCase",
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
