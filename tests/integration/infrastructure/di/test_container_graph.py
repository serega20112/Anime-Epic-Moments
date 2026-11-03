"""Интеграционный тест полноты DI-графа.

Тест страхует главный риск рефакторинга: при переезде файлов провайдеры
dishka ломаются молча, и ошибка видна только в рантайме приложения.
Проверяются две инвариантности — контейнер резолвит каждый экспортируемый
сценарий, а каждый сценарий, объявленный провайдерами, экспортируется
фасадом ``backend.application.use_cases``.
"""

from __future__ import annotations

import inspect
from typing import get_type_hints

import dishka
import pytest
from dishka import AsyncContainer, Provider

from backend.application import use_cases as use_cases_facade
from backend.config import Settings
from backend.infrastructure.di.dishka_container import build_dishka_container
from backend.infrastructure.di.providers import (
    AnimeUseCaseProvider,
    AuthUseCaseProvider,
    CollectionUseCaseProvider,
    FavoriteUseCaseProvider,
    HighlightUseCaseProvider,
    MomentUseCaseProvider,
    NotificationUseCaseProvider,
    RatingUseCaseProvider,
    ReactionUseCaseProvider,
    SupportUseCaseProvider,
    UserUseCaseProvider,
    WatchUseCaseProvider,
)

USE_CASE_PROVIDERS: tuple[type[Provider], ...] = (
    AnimeUseCaseProvider,
    AuthUseCaseProvider,
    CollectionUseCaseProvider,
    FavoriteUseCaseProvider,
    HighlightUseCaseProvider,
    MomentUseCaseProvider,
    NotificationUseCaseProvider,
    RatingUseCaseProvider,
    ReactionUseCaseProvider,
    SupportUseCaseProvider,
    UserUseCaseProvider,
    WatchUseCaseProvider,
)


def use_case_types() -> list[type]:
    """Собрать классы сценариев, экспортируемые фасадом application.use_cases.

    Returns:
        list[type]: Классы с суффиксом ``UseCase``, отсортированные по имени.
    """
    exported = getattr(use_cases_facade, "__all__", None) or dir(use_cases_facade)
    types = [
        getattr(use_cases_facade, name)
        for name in exported
        if inspect.isclass(getattr(use_cases_facade, name, None)) and name.endswith("UseCase")
    ]
    return sorted(types, key=lambda item: item.__name__)


def provided_use_case_types() -> list[type]:
    """Собрать классы сценариев, объявленные провайдерами dishka.

    dishka оборачивает помеченные ``@provide`` методы в
    ``CompositeDependencySource``, поэтому исходная функция читается через
    атрибут ``origin``.

    Returns:
        list[type]: Классы с суффиксом ``UseCase`` из аннотаций ``@provide``,
            отсортированные по имени.
    """
    types: set[type] = set()
    for provider_type in USE_CASE_PROVIDERS:
        for _, member in inspect.getmembers(provider_type):
            origin = getattr(member, "origin", None)
            if origin is None or not callable(origin):
                continue
            returned = get_type_hints(origin).get("return")
            if inspect.isclass(returned) and returned.__name__.endswith("UseCase"):
                types.add(returned)
    return sorted(types, key=lambda item: item.__name__)


def provided_use_case_names() -> set[str]:
    """Собрать имена сценариев, которые провайдеры объявляют как результат.

    Returns:
        set[str]: Имена классов с суффиксом ``UseCase`` из аннотаций ``@provide``.
    """
    return {item.__name__ for item in provided_use_case_types()}


@pytest.fixture
def isolated_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Переписать настройки на автономные: sqlite в памяти и без Redis.

    Args:
        monkeypatch: Fixture pytest для точечной подмены настроек.
    """
    monkeypatch.setattr(Settings, "database_url", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setattr(Settings, "redis_enabled", False)
    monkeypatch.setattr(Settings, "redis_required", False)


@pytest.mark.integration
async def test_container_resolves_every_provided_use_case(
    isolated_settings: None,
) -> None:
    """Что тестируем: полноту DI-графа приложения.

    Что передаём: все классы сценариев, объявленные провайдерами dishka.
    Что ожидаем: каждый резолвится в REQUEST-скоупе; список отказов пуст.
    Отдельные отказы собираются в список, чтобы за один прогон видеть все
    разорванные связи графа, а не только первую из них.
    """
    container: AsyncContainer = build_dishka_container()
    unresolved: list[str] = []

    async with container(scope=dishka.Scope.REQUEST) as scoped:
        for use_case_type in provided_use_case_types():
            try:
                resolved = await scoped.get(use_case_type)
            except Exception as error:
                unresolved.append(f"{use_case_type.__name__}: {type(error).__name__}: {error}")
                continue
            assert isinstance(resolved, use_case_type)

    await container.close()
    assert unresolved == []


@pytest.mark.integration
def test_providers_and_use_case_facade_agree() -> None:
    """Что тестируем: согласованность провайдеров и фасада сценариев.

    Что передаём: аннотации возвращаемых типов всех ``@provide``-методов
    провайдеров сценариев и экспорты фасада.
    Что ожидаем: множество провайдеров непусто и каждый его класс доступен из
    фасада, иначе граф можно разорвать переименованием экспорта, и тест
    резолвинга этого не заметит.
    """
    exported = {item.__name__ for item in use_case_types()}
    provided = provided_use_case_names()

    assert provided
    assert sorted(provided - exported) == []
    assert sorted(exported - provided) == []
