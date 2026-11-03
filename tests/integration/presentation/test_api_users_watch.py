"""Интеграционные тесты JSON-маршрутов библиотеки и истории просмотра.

Проверяется поведение, которое видит мобильный клиент: анонимный запрос
получает 401, чужой идентификатор в пути — 403, а владелец получает страницу с
вложенной карточкой тайтла из каталога.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from dishka import AsyncContainer, Provider, Scope, make_async_container, provide
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from backend.application.use_cases import (
    GetPublicProfileOverviewUseCase,
    GetUserAnimeLibraryUseCase,
    GetUserViewingHistoryUseCase,
)
from backend.application.use_cases.result import UseCaseResult
from backend.domain.entities.anime.anime import Anime
from backend.domain.value_objects.watch.library_cards import HistoryAnimeCard, LibraryAnimeCard
from backend.presentation.api.errors import register_exception_handlers
from backend.presentation.api.v1.users import api_users_router

OWNER_ID = 5
INTRUDER_ID = 6
JSON_ACCEPT = {"Accept": "application/json"}


def _anime() -> Anime:
    """Собрать карточку тайтла каталога для проверки вложенного ответа."""
    return Anime(
        external_id="123",
        title="Gintama",
        original_title="Gintama Kyuu",
        genres=["Comedy"],
        year=2011,
        rating=8.9,
        cover_url="https://example.com/cover.jpg",
        episode_count=12,
    )


class _FakeLibrary:
    """Заглушка чтения библиотеки, возвращающая одну карточку дневника."""

    def __init__(self) -> None:
        """Создать заглушку со списком вызовов."""
        self.calls: list[int] = []

    async def execute(self, query):
        """Запомнить пользователя и вернуть одну карточку библиотеки.

        Args:
            query: Запрос библиотеки с ``user_id`` и необязательным статусом.

        Returns:
            list[LibraryAnimeCard]: Список из одной карточки.
        """
        self.calls.append(query.user_id)
        return [
            LibraryAnimeCard(
                anime=_anime(),
                status="watching",
                current_episode=3,
                rating=8.0,
                last_watched_at="2024-01-02",
            )
        ]


class _FakeHistory:
    """Заглушка чтения истории, возвращающая одну карточку сессии."""

    def __init__(self) -> None:
        """Создать заглушку со списком вызовов."""
        self.calls: list[int] = []

    async def execute(self, query):
        """Запомнить пользователя и вернуть одну карточку истории.

        Args:
            query: Запрос истории с ``user_id`` и лимитом.

        Returns:
            list[HistoryAnimeCard]: Список из одной карточки.
        """
        self.calls.append(query.user_id)
        return [
            HistoryAnimeCard(
                anime=_anime(),
                episode=4,
                position_seconds=120.5,
                watched_at="2024-03-10",
            )
        ]


class _TestProvider(Provider):
    """Провайдер заглушек сценариев чтения для тестового приложения."""

    def __init__(self, library: _FakeLibrary, history: _FakeHistory) -> None:
        """Сохранить экземпляры заглушек.

        Args:
            library: Заглушка чтения библиотеки.
            history: Заглушка чтения истории.
        """
        super().__init__()
        self._library = library
        self._history = history

    @provide(scope=Scope.REQUEST)
    def get_user_anime_library(self) -> GetUserAnimeLibraryUseCase:
        """Отдать заглушку сценария библиотеки.

        Returns:
            GetUserAnimeLibraryUseCase: Экземпляр заглушки.
        """
        return self._library

    @provide(scope=Scope.REQUEST)
    def get_user_viewing_history(self) -> GetUserViewingHistoryUseCase:
        """Отдать заглушку сценария истории.

        Returns:
            GetUserViewingHistoryUseCase: Экземпляр заглушки.
        """
        return self._history


def _build_client(user: object | None, library: _FakeLibrary, history: _FakeHistory) -> TestClient:
    """Собрать приложение с маршрутами библиотеки и истории.

    Args:
        user: Пользователь сессии либо None для анонимного запроса.
        library: Заглушка чтения библиотеки.
        history: Заглушка чтения истории.

    Returns:
        TestClient: Клиент для обращения к маршрутам.
    """
    app = FastAPI()
    container: AsyncContainer = make_async_container(_TestProvider(library, history))

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

    app.include_router(api_users_router)
    register_exception_handlers(app)
    setup_dishka(container=container, app=app)
    return TestClient(app, headers=JSON_ACCEPT)


@pytest.mark.integration
class TestApiUsersWatchReadRoutes:
    """Проверка владельца и формы маршрутов чтения «Моё»."""

    def test_guest_gets_401_on_library(self):
        """Что тестируем: GET /api/v1/users/{id}/library без сессии.
        Что передаём: анонимный запрос.
        Что ожидаем: 401, сценарий не вызывается.
        """
        library = _FakeLibrary()
        client = _build_client(None, library, _FakeHistory())

        response = client.get(f"/api/v1/users/{OWNER_ID}/library")

        assert response.status_code == 401
        assert library.calls == []

    def test_foreign_user_gets_403_on_history(self):
        """Что тестируем: GET /api/v1/users/{id}/history чужим пользователем.
        Что передаём: сессию пользователя 6 и идентификатор 5 в пути.
        Что ожидаем: 403, чужая история не читается.
        """
        history = _FakeHistory()
        client = _build_client(SimpleNamespace(id=INTRUDER_ID), _FakeLibrary(), history)

        response = client.get(f"/api/v1/users/{OWNER_ID}/history")

        assert response.status_code == 403
        assert history.calls == []

    def test_owner_gets_library_page_with_nested_card(self):
        """Что тестируем: GET /api/v1/users/{id}/library/{status} владельцем.
        Что передаём: сессию пользователя 5, статус watching в пути.
        Что ожидаем: 200, конверт страницы и вложенная карточка каталога.
        """
        library = _FakeLibrary()
        client = _build_client(SimpleNamespace(id=OWNER_ID), library, _FakeHistory())

        response = client.get(f"/api/v1/users/{OWNER_ID}/library/watching")

        assert response.status_code == 200
        assert library.calls == [OWNER_ID]
        payload = response.json()
        assert payload["page"] == 1
        assert payload["total"] == 1
        assert payload["items"][0]["status"] == "watching"
        assert payload["items"][0]["anime"]["title"] == "Gintama"

    def test_owner_gets_history_page(self):
        """Что тестируем: GET /api/v1/users/{id}/history владельцем.
        Что передаём: сессию пользователя 5.
        Что ожидаем: 200, карточка истории с позицией и датой сессии.
        """
        history = _FakeHistory()
        client = _build_client(SimpleNamespace(id=OWNER_ID), _FakeLibrary(), history)

        response = client.get(f"/api/v1/users/{OWNER_ID}/history")

        assert response.status_code == 200
        assert history.calls == [OWNER_ID]
        item = response.json()["items"][0]
        assert item["episode"] == 4
        assert item["position_seconds"] == 120.5
        assert item["watched_at"] == "2024-03-10"


class _FakeProfile:
    """Заглушка обзора публичного профиля, возвращающая успешный результат."""

    async def execute(self, query):
        """Вернуть обзор профиля указанной цели.

        Args:
            query: Запрос профиля с ``profile_user_id`` и зрителем.

        Returns:
            UseCaseResult: Обзор публичного профиля.
        """
        overview = SimpleNamespace(
            profile=SimpleNamespace(
                user_id=query.profile_user_id,
                username="owner",
                avatar_url=None,
                status="in a band",
                summary=SimpleNamespace(highlight_count=3),
            ),
            followers_count=10,
            following_count=5,
            is_following=bool(query.viewer_user_id),
        )
        return UseCaseResult.success(overview)


class _ProfileProvider(Provider):
    """Провайдер заглушки обзора профиля для тестового приложения."""

    @provide(scope=Scope.REQUEST)
    def get_public_profile_overview(self) -> GetPublicProfileOverviewUseCase:
        """Отдать заглушку обзора публичного профиля.

        Returns:
            GetPublicProfileOverviewUseCase: Экземпляр заглушки.
        """
        return _FakeProfile()


@pytest.mark.integration
class TestApiUsersProfileRoute:
    """Проверка маршрута публичного профиля мобильного клиента."""

    def test_guest_gets_profile_without_follow_state(self):
        """Что тестируем: GET /api/v1/users/{id} гостем.
        Что передаём: анонимный запрос.
        Что ожидаем: 200, профиль без признака подписки и без почты.
        """
        app = FastAPI()
        container: AsyncContainer = make_async_container(_ProfileProvider())
        app.include_router(api_users_router)
        setup_dishka(container=container, app=app)
        client = TestClient(app, headers=JSON_ACCEPT)

        response = client.get(f"/api/v1/users/{OWNER_ID}")

        assert response.status_code == 200
        payload = response.json()
        assert payload["username"] == "owner"
        assert payload["highlights_count"] == 3
        assert payload["is_followed"] is False
        assert "email" not in payload
