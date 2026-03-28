from __future__ import annotations

from unittest.mock import Mock

from src.backend.infrastructure.external.justwatch_client import JustWatchClient


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_justwatch_client_returns_empty_when_disabled_or_year_missing():
    """Проверяем, что JustWatchClient не делает поиск без token или без года релиза."""
    client = JustWatchClient()
    client.partner_token = None

    assert client.search_sources(title="Gintama", episode=1, year=2024) == []

    client.partner_token = "token"

    assert client.search_sources(title="Gintama", episode=1, year=None) == []


def test_justwatch_client_caches_provider_map():
    """Проверяем, что JustWatchClient кеширует карту провайдеров и не дергает endpoint повторно."""
    client = JustWatchClient()
    client.partner_token = "token"
    client.session.get = Mock(
        return_value=_FakeResponse(
            [
                {"id": 1, "clear_name": "Netflix"},
                {"id": 2, "short_name": "Crunchyroll"},
            ]
        )
    )

    first = client._get_provider_map()
    second = client._get_provider_map()

    assert first == {1: "Netflix", 2: "Crunchyroll"}
    assert second == first
    client.session.get.assert_called_once()


def test_justwatch_client_maps_offers_to_external_sources(monkeypatch):
    """Проверяем, что JustWatchClient превращает офферы в discovered external sources без дублей."""
    client = JustWatchClient()
    client.partner_token = "token"
    monkeypatch.setattr(
        client,
        "_get_offers",
        lambda title, year: {
            "title": "Gintama",
            "offers": [
                {
                    "provider_id": 1,
                    "urls": {"standard_web": "https://netflix.example/gintama"},
                    "monetization_type": "flatrate",
                    "presentation_type": "hd",
                    "package_short_name": "Premium",
                },
                {
                    "provider_id": 1,
                    "urls": {"standard_web": "https://netflix.example/gintama"},
                    "monetization_type": "flatrate",
                    "presentation_type": "hd",
                    "package_short_name": "Premium",
                },
            ],
        },
    )
    monkeypatch.setattr(client, "_get_provider_map", lambda: {1: "Netflix"})

    items = client.search_sources(title="Gintama", episode=2, year=2024)

    assert len(items) == 1
    assert items[0].translation_name == "Netflix"
    assert items[0].provider_name == "JustWatch"
    assert items[0].source_type == "external"
    assert items[0].quality_label == "Flatrate • Hd • Premium"
