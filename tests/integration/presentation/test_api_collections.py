"""Интеграционные тесты JSON-маршрутов коллекций мобильного клиента.

Проверяется поведение для клиента: чужой идентификатор в пути не даёт прочитать
или создать чужую коллекцию (403), аноним — 401, а владелец получает карточки и
созданную коллекцию. Добавление элемента использует пользователя сессии.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from dishka import AsyncContainer, Provider, Scope, make_async_container, provide
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from backend.application.use_cases import (
    AddCollectionItemUseCase,
    CreateCollectionUseCase,
    GetUserCollectionsUseCase,
)
from backend.domain.value_objects.collection.cards import CollectionCard, CollectionDetails
from backend.presentation.api.errors import register_exception_handlers
from backend.presentation.api.v1.collections import api_collections_router

OWNER_ID = 5
INTRUDER_ID = 6
JSON_ACCEPT = {"Accept": "application/json"}


def _details() -> list[CollectionDetails]:
    """Собрать одну карточку коллекции с одним элементом для ответа сценария."""
    return [
        CollectionDetails(
            collection=CollectionCard(
                id=2,
                title="Favourites",
                description="",
                items_count=1,
                is_public=True,
                created_at="2024-01-02",
                share_url="/collections/share/2",
                cover_url=None,
            ),
            items=[],
        )
    ]


class _FakeList:
    """Заглушка списка коллекций."""

    def __init__(self) -> None:
        """Создать заглушку со списком вызовов."""
        self.calls: list[int] = []

    async def execute(self, query):
        """Запомнить владельца и вернуть карточки коллекций.

        Args:
            query: Запрос списка коллекций с ``user_id``.

        Returns:
            list[CollectionDetails]: Список из одной коллекции.
        """
        self.calls.append(query.user_id)
        return _details()


class _FakeCreate:
    """Заглушка создания коллекции."""

    async def execute(self, command):
        """Вернуть созданную коллекцию с переданным названием.

        Args:
            command: Команда создания коллекции.

        Returns:
            SimpleNamespace: Минимальная коллекция с идентификатором.
        """
        return SimpleNamespace(
            id=7, title=command.title, is_public=command.is_public, cover_url=None
        )


class _CollectionsProvider(Provider):
    """Провайдер заглушек сценариев коллекций."""

    def __init__(self) -> None:
        """Создать провайдер с заглушками."""
        super().__init__()
        self._list = _FakeList()
        self._create = _FakeCreate()
        self._add = AsyncMock()

    @provide(scope=Scope.REQUEST)
    def get_user_collections(self) -> GetUserCollectionsUseCase:
        """Отдать заглушку списка коллекций.

        Returns:
            GetUserCollectionsUseCase: Экземпляр заглушки.
        """
        return self._list

    @provide(scope=Scope.REQUEST)
    def create_collection(self) -> CreateCollectionUseCase:
        """Отдать заглушку создания коллекции.

        Returns:
            CreateCollectionUseCase: Экземпляр заглушки.
        """
        return self._create

    @provide(scope=Scope.REQUEST)
    def add_collection_item(self) -> AddCollectionItemUseCase:
        """Отдать заглушку добавления элемента коллекции.

        Returns:
            AddCollectionItemUseCase: Экземпляр двойника.
        """
        return self._add

    @property
    def list_use_case(self) -> _FakeList:
        """Вернуть заглушку списка для проверок вызовов.

        Returns:
            _FakeList: Экземпляр заглушки.
        """
        return self._list


def _build_client(user: object | None) -> tuple[TestClient, _CollectionsProvider]:
    """Собрать приложение с маршрутами коллекций и указанной сессией.

    Args:
        user: Пользователь сессии либо None для анонимного запроса.

    Returns:
        tuple[TestClient, _CollectionsProvider]: Клиент и провайдер заглушек.
    """
    provider = _CollectionsProvider()
    app = FastAPI()
    container: AsyncContainer = make_async_container(provider)

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

    app.include_router(api_collections_router)
    register_exception_handlers(app)
    setup_dishka(container=container, app=app)
    return TestClient(app, headers=JSON_ACCEPT), provider


@pytest.mark.integration
class TestApiCollectionsRoutes:
    """Проверка маршрутов коллекций мобильного клиента."""

    def test_foreign_user_gets_403_on_list(self):
        """Что тестируем: GET /api/v1/users/{id}/collections чужим пользователем.
        Что передаём: сессию пользователя 6 и идентификатор 5 в пути.
        Что ожидаем: 403, список чужих коллекций не отдаётся.
        """
        client, provider = _build_client(SimpleNamespace(id=INTRUDER_ID))

        response = client.get(f"/api/v1/users/{OWNER_ID}/collections")

        assert response.status_code == 403
        assert provider.list_use_case.calls == []

    def test_owner_gets_collection_list(self):
        """Что тестируем: GET /api/v1/users/{id}/collections владельцем.
        Что передаём: сессию пользователя 5.
        Что ожидаем: 200, карточка коллекции с владельцем из сессии.
        """
        client, provider = _build_client(SimpleNamespace(id=OWNER_ID))

        response = client.get(f"/api/v1/users/{OWNER_ID}/collections")

        assert response.status_code == 200
        payload = response.json()
        assert payload["items"][0]["id"] == 2
        assert payload["items"][0]["owner_id"] == OWNER_ID
        assert provider.list_use_case.calls == [OWNER_ID]

    def test_owner_creates_collection(self):
        """Что тестируем: POST /api/v1/users/{id}/collections владельцем.
        Что передаём: тело новой коллекции и сессию пользователя 5.
        Что ожидаем: 201, созданная коллекция с названием и владельцем.
        """
        client, _provider = _build_client(SimpleNamespace(id=OWNER_ID))

        response = client.post(
            f"/api/v1/users/{OWNER_ID}/collections",
            json={"title": "Watch later", "is_public": False},
        )

        assert response.status_code == 201
        payload = response.json()
        assert payload["title"] == "Watch later"
        assert payload["is_public"] is False
        assert payload["id"] == 7
