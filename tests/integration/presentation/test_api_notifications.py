"""Интеграционные тесты JSON-маршрутов центра уведомлений.

Проверяется поведение для клиента: анонимный запрос получает 401 и сценарии не
вызываются, авторизованный получает страницу уведомлений и результат отметки
прочтения. Область видимости — пользователь сессии, а не идентификатор из пути.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from dishka import AsyncContainer, Provider, Scope, make_async_container, provide
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from backend.application.use_cases.notification import (
    GetUserNotificationsUseCase,
    MarkAllNotificationsReadUseCase,
    MarkNotificationReadUseCase,
)
from backend.domain import Notification, NotificationFeedPage
from backend.presentation.api.errors import register_exception_handlers
from backend.presentation.api.v1.notifications import api_notifications_router

OWNER_ID = 5
JSON_ACCEPT = {"Accept": "application/json"}


class _FakeGet:
    """Заглушка чтения уведомлений, возвращающая одну страницу."""

    def __init__(self) -> None:
        """Создать заглушку со списком вызовов."""
        self.calls: list[object] = []

    async def execute(self, query):
        """Запомнить запрос и вернуть страницу с одним уведомлением.

        Args:
            query: Запрос уведомлений с ``user_id`` и страницей.

        Returns:
            NotificationFeedPage: Страница с одним уведомлением.
        """
        self.calls.append(query)
        return NotificationFeedPage(
            items=[
                Notification(
                    id=1,
                    user_id=query.user_id,
                    kind="highlight_like",
                    text="Ваш хайлайт оценили",
                    actor_user_id=42,
                )
            ],
            page=query.page,
            per_page=query.per_page,
            total=1,
            unread_count=1,
            actor_names={42: "alice"},
        )


def _build_client(user: object | None, get_use_case: _FakeGet) -> TestClient:
    """Собрать приложение с маршрутами уведомлений и указанной сессией.

    Args:
        user: Пользователь сессии либо None для анонимного запроса.
        get_use_case: Заглушка сценария чтения уведомлений.

    Returns:
        TestClient: Клиент для обращения к маршрутам.
    """
    app = FastAPI()
    container: AsyncContainer = make_async_container(_NotificationsProvider(get_use_case))

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

    app.include_router(api_notifications_router)
    register_exception_handlers(app)
    setup_dishka(container=container, app=app)
    return TestClient(app, headers=JSON_ACCEPT)


class _NotificationsProvider(Provider):
    """Провайдер заглушек сценариев уведомлений для тестового приложения."""

    def __init__(self, get_use_case: _FakeGet) -> None:
        """Сохранить заглушки сценариев.

        Args:
            get_use_case: Заглушка чтения уведомлений.
        """
        super().__init__()
        self._get = get_use_case
        self._mark = AsyncMock()
        self._mark_all = AsyncMock()
        self._mark.execute.return_value = 1
        self._mark_all.execute.return_value = 2

    @provide(scope=Scope.REQUEST)
    def get_user_notifications(self) -> GetUserNotificationsUseCase:
        """Отдать заглушку чтения уведомлений.

        Returns:
            GetUserNotificationsUseCase: Экземпляр заглушки.
        """
        return self._get

    @provide(scope=Scope.REQUEST)
    def mark_notification_read(self) -> MarkNotificationReadUseCase:
        """Отдать заглушку отметки одного уведомления.

        Returns:
            MarkNotificationReadUseCase: Экземпляр заглушки.
        """
        return self._mark

    @provide(scope=Scope.REQUEST)
    def mark_all_notifications_read(self) -> MarkAllNotificationsReadUseCase:
        """Отдать заглушку отметки всех уведомлений.

        Returns:
            MarkAllNotificationsReadUseCase: Экземпляр заглушки.
        """
        return self._mark_all


@pytest.mark.integration
class TestApiNotificationsRoutes:
    """Проверка маршрутов центра уведомлений мобильного клиента."""

    def test_guest_gets_401_on_list(self):
        """Что тестируем: GET /api/v1/notifications без сессии.
        Что передаём: анонимный запрос.
        Что ожидаем: 401.
        """
        client = _build_client(None, _FakeGet())

        response = client.get("/api/v1/notifications")

        assert response.status_code == 401

    def test_owner_gets_notifications_page(self):
        """Что тестируем: GET /api/v1/notifications владельцем сессии.
        Что передаём: сессию пользователя 5.
        Что ожидаем: 200, уведомление с именем автора и unread-счётчиком.
        """
        client = _build_client(SimpleNamespace(id=OWNER_ID), _FakeGet())

        response = client.get("/api/v1/notifications")

        assert response.status_code == 200
        payload = response.json()
        assert payload["total"] == 1
        assert payload["unread_count"] == 1
        assert payload["items"][0]["actor_name"] == "alice"

    def test_owner_marks_notification_read(self):
        """Что тестируем: POST /api/v1/notifications/{id}/read владельцем.
        Что передаём: сессию пользователя 5 и идентификатор уведомления.
        Что ожидаем: 200 с числом изменений из сценария.
        """
        get_use_case = _FakeGet()
        client = _build_client(SimpleNamespace(id=OWNER_ID), get_use_case)

        response = client.post("/api/v1/notifications/1/read")

        assert response.status_code == 200
        assert response.json() == {"marked": 1}
