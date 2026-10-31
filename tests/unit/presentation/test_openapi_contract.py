"""Контрактные тесты OpenAPI JSON API (этап 8, задачи M1, M3 и M5).

Схема OpenAPI — договорённость с мобильным клиентом, поэтому она хранится в
репозитории и сверяется здесь же: несовместимое изменение ответа (пропавшее
поле, свободный словарь вместо модели, HTML на пути ``/api/``) роняет тест до
выката. Скрипт генерации подключается по пути, а не как пакет: он относится к
инструментам репозитория.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = REPO_ROOT / "docs" / "api" / "openapi.json"
API_PATH_PREFIX = "/api/"
HTML_CONTENT_TYPES = ("text/html",)


def _load_exporter() -> ModuleType:
    """Загрузить скрипт экспорта схемы как модуль.

    Returns:
        ModuleType: Модуль ``scripts/export_openapi.py``.

    Raises:
        FileNotFoundError: Скрипт экспорта отсутствует в репозитории.
    """
    script_path = REPO_ROOT / "scripts" / "export_openapi.py"
    if not script_path.exists():
        raise FileNotFoundError(str(script_path))
    spec = importlib.util.spec_from_file_location("export_openapi", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def app() -> FastAPI:
    """Собрать приложение один раз на модуль тестов контракта.

    Returns:
        FastAPI: Настроенное приложение фабрики.
    """
    from backend.presentation.app_factory import create_app

    return create_app()


@pytest.fixture(scope="module")
def schema(app: FastAPI) -> dict:
    """Вернуть сгенерированную OpenAPI-схему приложения.

    Args:
        app: Приложение фабрики.

    Returns:
        dict: Разобранная схема OpenAPI.
    """
    return app.openapi() or {}


@pytest.mark.contract
def test_committed_schema_matches_generated() -> None:
    """Что тестируем: актуальность схемы, сохранённой в репозитории.
    Что передаём: результат генерации схемы и содержимое docs/api/openapi.json.
    Что ожидаем: побайтовое совпадение, иначе нужен make export-openapi.
    """
    exporter = _load_exporter()

    assert SCHEMA_PATH.read_text(encoding="utf-8") == exporter.render_schema()


@pytest.mark.contract
def test_api_routes_declare_response_models(app: FastAPI) -> None:
    """Что тестируем: наличие модели ответа у каждого JSON-маршрута (M1).
    Что передаём: маршруты приложения с путями из ``/api/``.
    Что ожидаем: у всех есть response_model; исключение — пустые ответы 204.
    """
    offenders: list[str] = []
    for route in app.routes:
        if not isinstance(route, APIRoute) or not route.path.startswith(API_PATH_PREFIX):
            continue
        if route.response_model is None and route.status_code != 204:
            offenders.append(f"{sorted(route.methods)} {route.path}")

    assert offenders == []


@pytest.mark.contract
def test_api_paths_never_return_html(schema: dict) -> None:
    """Что тестируем: HTML-страницы не появляются внутри JSON API (M1).
    Что передаём: пути и content-типы ответов схемы.
    Что ожидаем: ни на одном ``/api/`` пути нет ответа с text/html.
    """
    offenders: list[str] = []
    for path, operations in schema["paths"].items():
        if not path.startswith(API_PATH_PREFIX):
            continue
        for method, operation in operations.items():
            content_types = {
                content_type
                for response in operation.get("responses", {}).values()
                for content_type in response.get("content", {})
            }
            if any(content.startswith(HTML_CONTENT_TYPES) for content in content_types):
                offenders.append(f"{method.upper()} {path}")

    assert offenders == []


@pytest.mark.contract
def test_api_success_responses_have_schemas(schema: dict) -> None:
    """Что тестируем: каждый успешный JSON-ответ описан схемой (M3).
    Что передаём: ответы 2xx всех маршрутов ``/api/``.
    Что ожидаем: у ответа с содержимым есть $ref или type, пустых схем нет.
    """
    offenders: list[str] = []
    for path, operations in schema["paths"].items():
        if not path.startswith(API_PATH_PREFIX):
            continue
        for method, operation in operations.items():
            for status, response in operation.get("responses", {}).items():
                if not status.startswith("2"):
                    continue
                for content in response.get("content", {}).values():
                    if not content.get("schema"):
                        offenders.append(f"{method.upper()} {path} {status}")

    assert offenders == []


@pytest.mark.contract
def test_schema_has_no_free_form_objects(schema: dict) -> None:
    """Что тестируем: отсутствие «свободных» словарей в контракте (M3).
    Что передаём: все компоненты схемы.
    Что ожидаем: ни одна модель не допускает произвольные ключи.
    """
    offenders = [
        name
        for name, definition in schema["components"]["schemas"].items()
        if definition.get("additionalProperties") is True
    ]

    assert offenders == []
