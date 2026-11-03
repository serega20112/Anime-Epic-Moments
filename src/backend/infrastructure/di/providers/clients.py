"""Клиенты внешних сервисов: каталог аниме, Kodik, AniLibria, YouTube, JustWatch, media proxy и LLM."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from dishka import Provider, Scope, provide

from backend.application.interface.services import (
    AnimeApiClientInterface,
    GoogleAuthClientInterface,
)
from backend.config import Settings
from backend.infrastructure.cache.key_value_store import KeyValueStore
from backend.infrastructure.external import (
    AniLibriaClient,
    AnimeApiClient,
    JustWatchClient,
    KodikClient,
)
from backend.infrastructure.external.google import GoogleAuthClient
from backend.infrastructure.external.llm import (
    FailoverLLMClient,
    GoogleGeminiLLMClient,
    HuggingFaceLLMClient,
    OpenRouterLLMClient,
)
from backend.infrastructure.external.video import YouTubeClient
from backend.infrastructure.external.video.hls_proxy import MediaProxyClient


class ClientProvidersMixin(Provider):
    """Клиенты внешних сервисов: каталог аниме, Kodik, AniLibria, YouTube, JustWatch, media proxy и LLM.

    Часть провайдера: методы `@provide` собираются dishka из базовых
    классов, поэтому mixin самодостаточен и наследует `Provider`.
    """

    @provide(scope=Scope.APP)
    async def anime_api_client(self, store: KeyValueStore) -> AsyncIterator[AnimeApiClient]:
        """Создать клиент API каталога аниме."""
        client = AnimeApiClient(store=store)
        yield client
        await client.aclose()

    @provide(scope=Scope.APP)
    async def anime_api_client_interface(
        self,
        client: AnimeApiClient,
    ) -> AnimeApiClientInterface:
        """Отдать клиент каталога под ключом его интерфейса."""
        return client

    @provide(scope=Scope.APP)
    async def kodik_client(self) -> AsyncIterator[KodikClient]:
        """Создать клиент Kodik."""
        client = KodikClient()
        yield client
        await client.aclose()

    @provide(scope=Scope.APP)
    async def anilibria_client(self) -> AsyncIterator[AniLibriaClient]:
        """Создать клиент AniLibria."""
        client = AniLibriaClient()
        yield client
        await client.aclose()

    @provide(scope=Scope.APP)
    async def youtube_client(self) -> AsyncIterator[YouTubeClient]:
        """Создать клиент YouTube."""
        client = YouTubeClient()
        yield client
        await client.aclose()

    @provide(scope=Scope.APP)
    async def justwatch_client(self) -> AsyncIterator[JustWatchClient]:
        """Создать клиент JustWatch."""
        client = JustWatchClient()
        yield client
        await client.aclose()

    @provide(scope=Scope.APP)
    async def google_auth_client(self) -> AsyncIterator[GoogleAuthClientInterface]:
        """Создать клиент проверки ID-токена Google."""
        client = GoogleAuthClient(
            client_id=Settings.google_client_id,
            tokeninfo_url=Settings.google_tokeninfo_url,
        )
        yield client
        await client.aclose()

    @provide(scope=Scope.APP)
    async def media_proxy_client(self) -> AsyncIterator[MediaProxyClient]:
        """Создать клиент проксирования медиа."""
        client = MediaProxyClient(upstream_proxy=Settings.media_proxy_upstream_proxy)
        yield client
        await client.aclose()

    @provide(scope=Scope.APP)
    async def llm_client(self) -> AsyncIterator[FailoverLLMClient]:
        """Создать клиент LLM с цепочкой переключения провайдеров."""
        gemini = GoogleGeminiLLMClient(
            api_key=Settings.google_api_key,
            model=Settings.google_model,
            api_url=Settings.google_api_url,
        )
        huggingface = HuggingFaceLLMClient(
            api_key=Settings.hf_token,
            model=Settings.hf_model,
            provider=Settings.hf_provider,
            api_url=Settings.hf_api_url,
        )
        if Settings.openrouter_api_key:
            primary: Any = OpenRouterLLMClient(
                api_key=Settings.openrouter_api_key,
                model=Settings.openrouter_model,
                api_url=Settings.openrouter_api_url,
            )
            fallback = gemini if Settings.google_api_key else huggingface
        else:
            primary = gemini
            fallback = huggingface
        client = FailoverLLMClient(primary=primary, fallback=fallback)
        yield client
        await client.aclose()
