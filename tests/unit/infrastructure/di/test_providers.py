from __future__ import annotations

import pytest
from dishka import make_async_container

from backend.infrastructure.cache import HighlightDashboardCache, RecommendationCache
from backend.infrastructure.cache.key_value_store import KeyValueStore
from backend.infrastructure.cache.profile_overview_cache import ProfileOverviewCache
from backend.infrastructure.di.providers import (
    AppProvider,
    RequestProvider,
    UseCaseProvider,
)
from backend.infrastructure.external import AnimeApiClient
from backend.infrastructure.security.csrf_service import CSRFService
from backend.infrastructure.security.jwt_service import JWTService
from backend.infrastructure.security.password_service import PasswordService


@pytest.fixture
def app_container():
    return make_async_container(AppProvider())


async def test_app_provider_resolves_key_value_store(app_container):
    store = await app_container.get(KeyValueStore)
    assert isinstance(store, KeyValueStore)


async def test_app_provider_resolves_password_and_jwt(app_container):
    assert isinstance(await app_container.get(PasswordService), PasswordService)
    assert isinstance(await app_container.get(JWTService), JWTService)


async def test_app_provider_resolves_csrf(app_container):
    assert isinstance(await app_container.get(CSRFService), CSRFService)


async def test_app_provider_resolves_anime_api_client(app_container):
    client = await app_container.get(AnimeApiClient)
    assert isinstance(client, AnimeApiClient)


async def test_app_provider_resolves_caches(app_container):
    assert isinstance(await app_container.get(RecommendationCache), RecommendationCache)
    assert isinstance(
        await app_container.get(HighlightDashboardCache), HighlightDashboardCache
    )
    assert isinstance(await app_container.get(ProfileOverviewCache), ProfileOverviewCache)


def test_providers_are_instances_of_dishka_provider():
    for provider in (AppProvider(), RequestProvider(), UseCaseProvider()):
        from dishka import Provider

        assert isinstance(provider, Provider)