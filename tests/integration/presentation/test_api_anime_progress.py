"""Интеграционные тесты мобильного JSON-маршрута сохранения прогресса.

Проверяется поведение, которое видит клиент: анонимный запрос получает 401 и
сценарий не вызывается, а авторизованный зритель получает признак
«просмотрено», посчитанный сервером по позиции и длительности серии.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from dishka import AsyncContainer, Provider, Scope, make_async_container, provide
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from backend.application.use_cases.watch.session.save_viewing_session import (
    SaveViewingSessionUseCase,
)
from backend.presentation.api.errors import register_exception_handlers
from backend.presentation.api.v1.anime import api_anime_router

OWNER_ID = 5
ANIME_ID = 7
JSON_ACCEPT = {"Accept": "application/json"}


class _FakeSaveSession:
    """Заглушка сохранения сессии, помняющая последнюю команду."""

    def __init__(self) -> None:
        """Создать заглушку со списком вызовов."""
        self.calls: list[object] = []

    async def execute(self, command):
        """Запомнить команду и вернуть успешный результат.

        Args:
            command: Команда сохранения сессии просмотра.

        Returns:
            SimpleNamespace: Результат с идентификатором сессии.
        """
        self.calls.append(command)
        return SimpleNamespace(ok=True, data=SimpleNamespace(id=1), status_code=200)


class _TestProvider(Provider):
    """Провайдер заглушки сценария сохранения для тестового приложения."""

    def __init__(self, save_session: _FakeSaveSession) -> None:
        """Сохранить экземпляр заглушки.

        Args:
            save_session: Заглушка сценария сохранения сессии.
        """
        super().__init__()
        self._save_session = save_session

    @provide(scope=Scope.REQUEST)
    def save_viewing_session(self) -> SaveViewingSessionUseCase:
        """Отдать заглушку сценария сохранения сессии.

        Returns:
            SaveViewingSessionUseCase: Экземпляр заглушки.
        """
        return self._save_session


def _build_client(user: object | None, save_session: _FakeSaveSession) -> TestClient:
    """Собрать приложение с маршрутом прогресса и указанной сессией.

    Args:
        user: Пользователь сессии либо None для анонимного запроса.
        save_session: Заглушка сценария сохранения сессии.

    Returns:
        TestClient: Клиент для обращения к маршруту.
    """
    app = FastAPI()
    container: AsyncContainer = make_async_container(_TestProvider(save_session))

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
    return TestClient(app, headers=JSON_ACCEPT)


@pytest.mark.integration
class TestSaveProgressRoute:
    """Проверка поведения мобильного маршрута сохранения прогресса."""

    def test_guest_gets_401_and_use_case_not_called(self):
        """Что тестируем: POST /api/v1/anime/{id}/progress без сессии.
        Что передаём: анонимный запрос с валидным телом.
        Что ожидаем: 401, сценарий сохранения не вызывается.
        """
        save_session = _FakeSaveSession()
        client = _build_client(None, save_session)

        response = client.post(
            f"/api/v1/anime/{ANIME_ID}/progress",
            json={"episode": 2, "position_seconds": 54.0, "duration_seconds": 60.0},
        )

        assert response.status_code == 401
        assert save_session.calls == []

    def test_owner_saves_progress_and_server_marks_watched(self):
        """Что тестируем: сохранение позиции владельцем с порогом 90 %.
        Что передаём: позицию 54 из 60 секунд.
        Что ожидаем: 200, saved истина, watched посчитан сервером как истина.
        """
        save_session = _FakeSaveSession()
        client = _build_client(SimpleNamespace(id=OWNER_ID), save_session)

        response = client.post(
            f"/api/v1/anime/{ANIME_ID}/progress",
            json={"episode": 2, "position_seconds": 54.0, "duration_seconds": 60.0},
        )

        assert response.status_code == 200
        assert response.json() == {"saved": True, "watched": True}
        assert save_session.calls[0].user_id == OWNER_ID
        assert save_session.calls[0].anime_id == ANIME_ID

    def test_below_threshold_is_not_watched(self):
        """Что тестируем: позицию ниже серверного порога просмотра.
        Что передаём: позицию 10 из 60 секунд.
        Что ожидаем: 200 с saved истина и watched ложь.
        """
        save_session = _FakeSaveSession()
        client = _build_client(SimpleNamespace(id=OWNER_ID), save_session)

        response = client.post(
            f"/api/v1/anime/{ANIME_ID}/progress",
            json={"episode": 3, "position_seconds": 10.0, "duration_seconds": 60.0},
        )

        assert response.status_code == 200
        assert response.json() == {"saved": True, "watched": False}
