"""Провайдеры видео-источников: SameBand, AniBoom, HDRezka, Sibnet, Kinobox, AnimeGo и 18+."""

from __future__ import annotations

from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide

from backend.config import Settings
from backend.infrastructure.external import (
    AniBoomProvider,
    AnimeGoProvider,
    EpornerProvider,
    HanimeProvider,
    HDRezkaProvider,
    HentaigasmProvider,
    KinoboxProvider,
    SamebandProvider,
    SibnetProvider,
)


class VideoSourceProvidersMixin(Provider):
    """Провайдеры видео-источников: SameBand, AniBoom, HDRezka, Sibnet, Kinobox, AnimeGo и 18+.

    Часть провайдера: методы `@provide` собираются dishka из базовых
    классов, поэтому mixin самодостаточен и наследует `Provider`.
    """

    @provide(scope=Scope.APP)
    async def sameband_provider(self) -> AsyncIterator[SamebandProvider]:
        """Создать провайдер SameBand."""
        provider = SamebandProvider(
            base_url=Settings.sameband_base_url,
            enabled=Settings.sameband_enabled,
            timeout=Settings.sameband_timeout,
        )
        yield provider
        await provider.aclose()

    @provide(scope=Scope.APP)
    async def aniboom_provider(self) -> AsyncIterator[AniBoomProvider]:
        """Создать провайдер AniBoom."""
        provider = AniBoomProvider(
            base_url=Settings.aniboom_base_url,
            enabled=Settings.aniboom_enabled,
            timeout=Settings.aniboom_timeout,
        )
        yield provider
        await provider.aclose()

    @provide(scope=Scope.APP)
    async def hanime_provider(self) -> AsyncIterator[HanimeProvider]:
        """Создать провайдер Hanime.tv."""
        provider = HanimeProvider(
            base_url=Settings.hanime_base_url,
            enabled=Settings.hanime_enabled,
            timeout=Settings.hanime_timeout,
            proxy=Settings.hanime_proxy,
            cf_clearance=Settings.hanime_cf_clearance,
            user_agent=Settings.hanime_user_agent,
        )
        yield provider
        await provider.aclose()

    @provide(scope=Scope.APP)
    async def kinobox_provider(self) -> AsyncIterator[KinoboxProvider]:
        """Создать провайдер-агрегатор Kinobox."""
        provider = KinoboxProvider(
            base_url=Settings.kinobox_base_url,
            enabled=Settings.kinobox_enabled,
            timeout=Settings.kinobox_timeout,
        )
        yield provider
        await provider.aclose()

    @provide(scope=Scope.APP)
    async def animego_provider(
        self,
        sibnet_provider: SibnetProvider,
        aniboom_provider: AniBoomProvider,
    ) -> AsyncIterator[AnimeGoProvider]:
        """Создать скрапер AnimeGo с подключёнными экстракторами потоков."""
        provider = AnimeGoProvider(
            base_url=Settings.animego_base_url,
            enabled=Settings.animego_enabled,
            timeout=Settings.animego_timeout,
            sibnet_extractor=sibnet_provider,
            aniboom_extractor=aniboom_provider,
        )
        yield provider
        await provider.aclose()

    @provide(scope=Scope.APP)
    async def sibnet_provider(self) -> AsyncIterator[SibnetProvider]:
        """Создать экстрактор Sibnet."""
        provider = SibnetProvider(
            base_url=Settings.sibnet_base_url,
            enabled=Settings.sibnet_enabled,
            timeout=Settings.sibnet_timeout,
        )
        yield provider
        await provider.aclose()

    @provide(scope=Scope.APP)
    async def eporner_provider(self) -> AsyncIterator[EpornerProvider]:
        """Создать провайдер 18+ API Eporner."""
        provider = EpornerProvider(
            base_url=Settings.eporner_base_url,
            enabled=Settings.eporner_enabled,
            timeout=Settings.eporner_timeout,
        )
        yield provider
        await provider.aclose()

    @provide(scope=Scope.APP)
    async def hdrezka_provider(self) -> AsyncIterator[HDRezkaProvider]:
        """Создать парсер HDRezka."""
        provider = HDRezkaProvider(
            base_url=Settings.rezka_base_url,
            enabled=Settings.rezka_enabled,
            timeout=Settings.rezka_timeout,
        )
        yield provider
        await provider.aclose()

    @provide(scope=Scope.APP)
    async def hentaigasm_provider(self) -> AsyncIterator[HentaigasmProvider]:
        """Создать провайдер 18+ источника Hentaigasm."""
        provider = HentaigasmProvider(
            base_url=Settings.hentaigasm_base_url,
            enabled=Settings.hentaigasm_enabled,
            timeout=Settings.hentaigasm_timeout,
        )
        yield provider
        await provider.aclose()
