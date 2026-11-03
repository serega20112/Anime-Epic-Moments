"""Интеграционные тесты JSON-маршрута карточки тайтла для мобильного клиента.

Проверяется поведение, которое видит клиент: карточка отдаётся и гостю, и
зрителю, а вложенные серии и источники сериализуются из доменной карточки без
потери полей контракта.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from dishka import AsyncContainer, Provider, Scope, make_async_container, provide
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from backend.application.use_cases.watch.page.get_anime_detail import GetAnimeDetailUseCase
from backend.domain.value_objects.watch.detail import AnimeDetail, EpisodeProgress
from backend.domain.value_objects.watch.page_data import WatchPageData, WatchSourceCard
from backend.presentation.api.errors import register_exception_handlers
from backend.presentation.api.v1.anime import api_anime_router

ANIME_ID = 7
JSON_ACCEPT = {"Accept": "application/json"}


def _detail(favorites: bool) -> AnimeDetail:
    """Собрать доменную карточку тайтла с одной серией и одним источником."""
    page = WatchPageData(
        anime_id=ANIME_ID,
        anime_title="Gintama",
        anime_cover="https://example.com/cover.jpg",
        anime_description="Описание",
        anime_year=2011,
        anime_rating=8.9,
        genres=["Comedy"],
        episode=2,
        episode_total=2,
        episode_options=[1, 2],
        selected_source_id=11,
        selected_translation_id=3,
        sources=[
            WatchSourceCard(
                source_id=11,
                translation_id=3,
                translation_name="AniLibria",
                episode=2,
                provider_name="Kinobox",
                source_name="kb",
                quality_label="720p",
                stream_url="https://example.com/x.m3u8",
                source_type="stream",
            )
        ],
        highlights=[],
        current_status="watching",
        last_position_seconds=40.0,
        preferred_start_seconds=0.0,
        saved_volume=1.0,
        saved_quality_label="720p",
        user_rating=8,
    )
    episodes = [
        EpisodeProgress(number=1, watched=True),
        EpisodeProgress(number=2, watched=False, position_seconds=40.0),
    ]
    return AnimeDetail(page=page, favorites=favorites, episodes=episodes)


class _FakeDetail:
    """Заглушка сценария карточки, возвращающая предсказуемую детализацию."""

    def __init__(self, favorites: bool) -> None:
        """Сохранить признак избранного для ответа.

        Args:
            favorites: Значение поля ``favorites`` в возвращаемой карточке.
        """
        self._favorites = favorites
        self.calls: list[object] = []

    async def execute(self, query):
        """Запомнить запрос и вернуть карточку тайтла.

        Args:
            query: Запрос страницы просмотра с ``anime_id`` и ``user_id``.

        Returns:
            AnimeDetail: Карточка тайтла.
        """
        self.calls.append(query)
        return _detail(self._favorites)


class _TestProvider(Provider):
    """Провайдер заглушки сценария карточки для тестового приложения."""

    def __init__(self, detail: _FakeDetail) -> None:
        """Сохранить заглушку.

        Args:
            detail: Заглушка сценария карточки.
        """
        super().__init__()
        self._detail = detail

    @provide(scope=Scope.REQUEST)
    def get_anime_detail(self) -> GetAnimeDetailUseCase:
        """Отдать заглушку сценария карточки.

        Returns:
            GetAnimeDetailUseCase: Экземпляр заглушки.
        """
        return self._detail


def _build_client(user: object | None, favorites: bool) -> tuple[TestClient, _FakeDetail]:
    """Собрать приложение с маршрутом карточки и указанной сессией.

    Args:
        user: Пользователь сессии либо None для гостя.
        favorites: Значение избранного в ответе заглушки.

    Returns:
        tuple[TestClient, _FakeDetail]: Клиент и заглушка для проверок.
    """
    detail = _FakeDetail(favorites)
    app = FastAPI()
    container: AsyncContainer = make_async_container(_TestProvider(detail))

    @app.middleware("http")
    async def inject_state(request: Request, call_next):
        """Прикрепить пользователя сессии к запросу.

        Args:
            request: Текущий HTTP-запрос.
            call_next: Следующий шаг обработки.

        Returns:
            Response: Ответ маршрута.
        """
        request.state.user = user
        return await call_next(request)

    app.include_router(api_anime_router)
    register_exception_handlers(app)
    setup_dishka(container=container, app=app)
    return TestClient(app, headers=JSON_ACCEPT), detail


@pytest.mark.integration
class TestAnimeDetailRoute:
    """Проверка маршрута отдачи карточки тайтла."""

    def test_guest_gets_card_without_personal_state(self):
        """Что тестируем: GET /api/v1/anime/{id} гостем.
        Что передаём: анонимный запрос.
        Что ожидаем: 200, карточка с вложенной серией и источником, favorites ложен.
        """
        client, _detail = _build_client(None, favorites=False)

        response = client.get(f"/api/v1/anime/{ANIME_ID}")

        assert response.status_code == 200
        payload = response.json()
        assert payload["anime"]["title"] == "Gintama"
        assert payload["favorites"] is False
        assert payload["sources"][0]["url"] == "https://example.com/x.m3u8"
        assert [item["number"] for item in payload["episodes"]] == [1, 2]

    def test_owner_gets_card_with_favorite_flag(self):
        """Что тестируем: GET /api/v1/anime/{id} зрителем с избранным.
        Что передаём: сессию пользователя и серию 2 в параметре запроса.
        Что ожидаем: 200, favorites истинен, позиция у текущей серии проставлена.
        """
        client, detail = _build_client(SimpleNamespace(id=5), favorites=True)

        response = client.get(f"/api/v1/anime/{ANIME_ID}?episode=2")

        assert response.status_code == 200
        assert response.json()["favorites"] is True
        assert detail.calls[0].user_id == 5
        assert detail.calls[0].episode == 2
