from __future__ import annotations

import pytest

from backend.infrastructure.di.dishka_container import build_dishka_container


@pytest.mark.unit
class TestDishkaContainer:
    """Юнит-тесты сборки Dishka-контейнера приложения."""

    def test_builds_async_container(self):
        """Что тестируем: build_dishka_container возвращает работоспособный контейнер.
        Что передаём: ничего.
        Что ожидаем: возвращается экземпляр AsyncContainer от dishka.
        """
        from dishka import AsyncContainer

        container = build_dishka_container()

        assert isinstance(container, AsyncContainer)