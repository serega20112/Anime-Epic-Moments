from __future__ import annotations

from unittest.mock import AsyncMock

import httpx
import pytest

from backend.infrastructure.external import HentaigasmProvider
from backend.infrastructure.external.errors import (
    ExternalServiceTimeoutError,
    ExternalServiceUnavailableError,
)


class _FakeResponse:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self):
        return None


def _search_html(*titles: str) -> str:
    cards = "".join(
        f'<li class="item"><div class="thumb">'
        f'<a class="clip-link" data-id="{index}" title="{title}" '
        f'href="https://hentaigasm.com/{title.lower().replace(" ", "-")}/">'
        f'<span class="clip"></span></a></div></li>'
        for index, title in enumerate(titles, start=1)
    )
    return f"<html><body><ul>{cards}</ul></body></html>"


def _page_html(file_url: str) -> str:
    return (
        "<html><body>"
        '<script src="https://content.jwplatform.com/libraries/SAHhwvZq.js"></script>'
        '<div id="player_01"></div><script>jwplayer("player_01").setup({ '
        f'file: "{file_url}", width: "620" }});</script>'
        "</body></html>"
    )


def _provider(enabled: bool = True) -> HentaigasmProvider:
    return HentaigasmProvider(
        base_url="https://hentaigasm.com",
        enabled=enabled,
        timeout=10,
    )


@pytest.mark.asyncio
async def test_hentaigasm_extracts_direct_mp4_from_search():
    """Поиск → страница ролика → прямой MP4 из настройки плеера."""
    provider = _provider()
    provider.session.get = AsyncMock(
        side_effect=[
            _FakeResponse(_search_html("Bible Black New Testament 1 Subbed")),
            _FakeResponse(_page_html("https://hgasm3.com/Bible Black.mp4")),
        ]
    )

    items = await provider.search_sources(title="Bible Black", episode=1)

    assert len(items) == 1
    assert items[0].provider_name == "Hentaigasm"
    assert items[0].episode == 1
    assert items[0].language == "ja"
    assert items[0].stream_url == "https://hgasm3.com/Bible Black.mp4"
    assert provider.session.get.await_count == 2


@pytest.mark.asyncio
async def test_hentaigasm_skips_permalink_and_admin_links():
    """Служебные ссылки выдачи не считаются результатами поиска."""
    provider = _provider()
    search_html = (
        "<html><body><ul>"
        '<li><a href="https://hentaigasm.com/bible-black-1/" '
        'title="Permalink to Bible Black 1 Subbed">x</a></li>'
        '<li><a href="https://hentaigasm.com/author/admin/" '
        'title="Posts by admin">x</a></li>'
        '<li><div class="thumb"><a class="clip-link" data-id="1" '
        'title="Bible Black 1 Subbed" '
        'href="https://hentaigasm.com/bible-black-1-subbed/"><span class="clip">'
        "</span></a></div></li>"
        "</ul></body></html>"
    )
    provider.session.get = AsyncMock(
        side_effect=[
            _FakeResponse(search_html),
            _FakeResponse(_page_html("https://hgasm2.com/Bible Black 1 Subbed.mp4")),
        ]
    )

    items = await provider.search_sources(title="Bible Black", episode=1)

    assert len(items) == 1
    assert items[0].source_name == "https://hentaigasm.com/bible-black-1-subbed/"


@pytest.mark.asyncio
async def test_hentaigasm_scans_past_irrelevant_results():
    """Релевантный ролик находится даже после нерелевантных карточек.

    Поиск сайта возвращает посторонние ролики в начале списка, поэтому
    ограничение выборки до ``limit`` до фильтрации скрывало бы результат.
    """
    provider = _provider()
    noise = tuple(f"Completely Different Show {index} Subbed" for index in range(1, 13))
    provider.session.get = AsyncMock(
        side_effect=[
            _FakeResponse(_search_html(*noise, "Bible Black Only 1 Subbed")),
            _FakeResponse(_page_html("https://hgasm2.com/Bible Black Only 1 Subbed.mp4")),
        ]
    )

    items = await provider.search_sources(title="Bible Black", episode=1)

    assert len(items) == 1
    assert "Bible Black Only 1" in items[0].stream_url


@pytest.mark.asyncio
async def test_hentaigasm_respects_limit():
    """Число найденных источников не превышает запрошенный limit."""
    provider = _provider()
    provider.session.get = AsyncMock(
        side_effect=[
            _FakeResponse(
                _search_html(
                    "Bible Black 1 Subbed",
                    "Bible Black 2 Subbed",
                    "Bible Black 3 Subbed",
                )
            ),
            _FakeResponse(_page_html("https://hgasm2.com/a.mp4")),
            _FakeResponse(_page_html("https://hgasm2.com/b.mp4")),
        ]
    )

    items = await provider.search_sources(title="Bible Black", episode=1, limit=2)

    assert len(items) == 2


@pytest.mark.asyncio
async def test_hentaigasm_filters_irrelevant_videos():
    """Ролики других тайтлов отбрасываются по токенам названия."""
    provider = _provider()
    provider.session.get = AsyncMock(
        side_effect=[
            _FakeResponse(
                _search_html(
                    "Totally Different Movie 1080p",
                    "Bible Black 1 Subbed",
                )
            ),
            _FakeResponse(_page_html("https://hgasm2.com/Bible Black 1 Subbed.mp4")),
        ]
    )

    items = await provider.search_sources(title="Bible Black", episode=1)

    assert len(items) == 1
    assert items[0].provider_name == "Hentaigasm"


@pytest.mark.asyncio
async def test_hentaigasm_detects_quality_label():
    """Метка качества извлекается из ссылки или заголовка."""
    provider = _provider()
    provider.session.get = AsyncMock(
        side_effect=[
            _FakeResponse(_search_html("Bible Black 1080p")),
            _FakeResponse(_page_html("https://hgasm2.com/movie.mp4")),
        ]
    )

    items = await provider.search_sources(title="Bible Black", episode=1)

    assert items[0].quality_label == "1080p"


@pytest.mark.asyncio
async def test_hentaigasm_default_quality_when_unknown():
    """Без указания качества подпись равна auto."""
    provider = _provider()
    provider.session.get = AsyncMock(
        side_effect=[
            _FakeResponse(_search_html("Bible Black")),
            _FakeResponse(_page_html("https://hgasm2.com/movie.mp4")),
        ]
    )

    items = await provider.search_sources(title="Bible Black", episode=1)

    assert items[0].quality_label == "auto"


@pytest.mark.asyncio
async def test_hentaigasm_skips_page_without_player_file():
    """Страница без настройки плеера не даёт источника."""
    provider = _provider()
    provider.session.get = AsyncMock(
        side_effect=[
            _FakeResponse(_search_html("Bible Black 1 Subbed")),
            _FakeResponse("<html><body>no player here</body></html>"),
        ]
    )

    assert await provider.search_sources(title="Bible Black", episode=1) == []


@pytest.mark.asyncio
async def test_hentaigasm_returns_nothing_when_disabled():
    """Выключенный провайдер не выполняет сетевых запросов."""
    provider = _provider(enabled=False)
    provider.session.get = AsyncMock(side_effect=AssertionError("must not be called"))

    assert await provider.search_sources(title="Bible Black", episode=1) == []


@pytest.mark.asyncio
async def test_hentaigasm_ignores_blank_title():
    """Пустое название не порождает сетевых запросов."""
    provider = _provider()
    provider.session.get = AsyncMock(side_effect=AssertionError("must not be called"))

    assert await provider.search_sources(title="   ", episode=1) == []


@pytest.mark.asyncio
async def test_hentaigasm_empty_search_results():
    """Пустая выдача поиска даёт пустой результат без ошибок."""
    provider = _provider()
    provider.session.get = AsyncMock(return_value=_FakeResponse("<html><body></body></html>"))

    assert await provider.search_sources(title="Monster Farm", episode=1) == []


@pytest.mark.asyncio
async def test_hentaigasm_timeout_returns_empty():
    """Таймаут поиска деградирует в пустой результат (без подъёма 500)."""
    provider = _provider()
    provider.session.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

    assert await provider.search_sources(title="Bible Black", episode=1) == []


@pytest.mark.asyncio
async def test_hentaigasm_network_error_returns_empty():
    """Сбой сети деградирует в пустой результат."""
    provider = _provider()
    provider.session.get = AsyncMock(side_effect=httpx.ConnectError("refused"))

    assert await provider.search_sources(title="Bible Black", episode=1) == []


@pytest.mark.asyncio
async def test_hentaigasm_transport_errors_type_map():
    """Транспортные ошибки внутренних запросов транслируются корректно."""
    checks = [
        (httpx.TimeoutException("t"), ExternalServiceTimeoutError),
        (httpx.ConnectError("c"), ExternalServiceUnavailableError),
    ]
    for exc_type, mapped_type in checks:
        provider = _provider()
        provider.session.get = AsyncMock(side_effect=exc_type)
        with pytest.raises(mapped_type):
            await provider._get("https://hentaigasm.com/")


@pytest.mark.asyncio
async def test_hentaigasm_availability_reports_relevant_video():
    """Карта доступности подтверждает наличие контента по тайтлу."""
    provider = _provider()
    provider.session.get = AsyncMock(
        side_effect=[
            _FakeResponse(
                _search_html(
                    "Totally Different Movie",
                    "Bible Black New Testament 1 Subbed",
                )
            )
        ]
    )

    availability = await provider.get_translations_availability(title="Bible Black")

    assert len(availability) == 1
    assert availability[0].episodes_count == 1
    assert availability[0].has_episode(1) is True
    assert availability[0].title == "Hentaigasm"
    assert availability[0].link is not None


@pytest.mark.asyncio
async def test_hentaigasm_availability_empty_when_no_relevant_video():
    """Нет релевантных роликов — пустая карта доступности."""
    provider = _provider()
    provider.session.get = AsyncMock(
        return_value=_FakeResponse(_search_html("Totally Different Movie"))
    )

    assert await provider.get_translations_availability(title="Bible Black") == []


@pytest.mark.asyncio
async def test_hentaigasm_availability_empty_when_disabled():
    """Выключенный провайдер не опрашивается при проверке доступности."""
    provider = _provider(enabled=False)
    provider.session.get = AsyncMock(side_effect=AssertionError("must not be called"))

    assert await provider.get_translations_availability(title="Bible Black") == []


@pytest.mark.asyncio
async def test_hentaigasm_availability_degrades_on_network_error():
    """Сбой сети при проверке доступности деградирует в пустой список."""
    provider = _provider()
    provider.session.get = AsyncMock(side_effect=httpx.ConnectError("refused"))

    assert await provider.get_translations_availability(title="Bible Black") == []


@pytest.mark.asyncio
async def test_hentaigasm_links_are_not_ephemeral():
    """Ссылки Hentaigasm не подписаны и не протухают, unlike Eporner."""
    provider = _provider()

    assert provider.ephemeral_links is False
