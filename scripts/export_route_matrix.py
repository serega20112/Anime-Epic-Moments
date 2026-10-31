"""Экспорт механической части таблицы роутов для docs/01-architecture/route-matrix.md.

Таблица роутов (задача S1) состоит из двух групп колонок: механических —
путь, методы, имя обработчика, откуда обработчик берёт ``user_id`` — и
смысловых: публичный роут или приватный и есть ли проверка владельца.
Смысловые колонки заполняет человек, механические генерируются отсюда, чтобы
таблица не расходилась с кодом после добавления нового роута.

Использование::

    uv run python scripts/export_route_matrix.py

Вывод — markdown-строки таблицы без смысловых колонок.
"""

from __future__ import annotations

import inspect
import re
import sys
from pathlib import Path
from types import ModuleType

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from backend.presentation.app_factory import create_app  # noqa: E402

USER_ID_FROM_SESSION = re.compile(
    r"require_user|get_current_user|get_current_user_id|require_self"
    r"|request\.state\.user|request\.state,\s*\"user\""
)
USER_ID_FROM_PATH = re.compile(r"user_id:\s*int")
USER_ID_FROM_PAYLOAD = re.compile(r'payload\.get\(\s*"user_id"|form\.get\(\s*"user_id"')
USER_ID_FROM_BODY = re.compile(r"body\.user_id")
BODY_SOURCE_LABEL = "тело"


def _unwrap_endpoint(endpoint: object) -> object:
    """Вернуть исходную функцию обработчика, сняв обёртки фреймворков.

    ``@rate_limit`` использует ``functools.wraps`` и раскрывается через
    атрибут ``__wrapped__``. ``DishkaRoute`` оборачивает обработчик в
    ``dishka_func_<имя>`` без ``__wrapped__``, и настоящая функция лежит в
    замыкании обёртки под именем ``func_<имя>``.

    Args:
        endpoint: Функция-обработчик роута, возможно обёрнутая декораторами.

    Returns:
        object: Внутренняя функция обработчика либо сама обёртка, если
            раскрыть её не удалось.
    """
    current = endpoint
    depth = 0
    while current is not None and hasattr(current, "__wrapped__") and depth < 10:
        current = getattr(current, "__wrapped__")
        depth += 1
    name = getattr(current, "__name__", "")
    for cell in getattr(current, "__closure__", None) or ():
        try:
            value = cell.cell_contents
        except ValueError:
            continue
        if (
            callable(value)
            and getattr(value, "__name__", "")
            and name.endswith(getattr(value, "__name__", "##"))
        ):
            return value
    return current


WRAPPER_MARKERS = ("container_getter", "dishka_func_")


def _is_wrapper_source(source: str) -> bool:
    """Отличить служебную обёртку фреймворка от кода обработчика.

    Args:
        source: Исходный код функции.

    Returns:
        bool: True, если в коде видны признаки обёртки dishka.
    """
    return any(marker in source for marker in WRAPPER_MARKERS)


def _find_handler_in_presentation(name: str) -> object:
    """Найти функцию обработчика по имени среди модулей presentation.

    Имена обработчиков уникальны в рамках слоя, так как задаются в
    ``name=`` декоратора роутера. Такой поиск надёжнее, чем модуль обёртки
    dishka: он указывает на ``dishka.integrations.fastapi``.

    Args:
        name: Имя функции обработчика без префикса роутера.

    Returns:
        object: Найденная функция либо None.
    """
    if not name:
        return None
    for module_name, module in list(sys.modules.items()):
        if not module_name.startswith("backend.presentation") or module is None:
            continue
        attribute = getattr(module, name, None)
        if callable(attribute) and getattr(attribute, "__name__", "") == name:
            return _unwrap_endpoint(attribute)
    return None


def _handler_function(route: object) -> object:
    """Вернуть настоящую функцию обработчика роута.

    ``DishkaRoute`` и ``@rate_limit`` оборачивают обработчик, и исходник
    обёртки ничего не говорит об источнике ``user_id``. Перебираются три
    источника: функция из замыкания обёртки, объект с тем же именем из
    модуля объявления и сама обёртка как последний вариант.

    Args:
        route: Объект маршрута FastAPI/Starlette.

    Returns:
        object: Функция обработчика либо обёртка, если поиск не удался.
    """
    endpoint = getattr(route, "endpoint", None)
    candidates: list[object] = [_unwrap_endpoint(endpoint)]
    registered = str(getattr(route, "name", "")) or getattr(endpoint, "__name__", "")
    short_name = registered.rsplit(".", 1)[-1]
    module = inspect.getmodule(endpoint) if endpoint is not None else None
    if module is not None:
        for candidate_name in (short_name, registered):
            attribute = getattr(module, candidate_name, None)
            if callable(attribute):
                candidates.append(_unwrap_endpoint(attribute))
    found = _find_handler_in_presentation(short_name)
    if found is not None:
        candidates.append(found)
    for candidate in candidates:
        try:
            source = inspect.getsource(candidate)
        except (OSError, TypeError):
            continue
        if not _is_wrapper_source(source):
            return candidate
    return candidates[-1] if candidates else endpoint


def _endpoint_source(route: object) -> str:
    """Вернуть исходный код обработчика роута, если он доступен.

    Args:
        route: Объект маршрута FastAPI/Starlette.

    Returns:
        str: Исходник обработчика либо пустая строка для lambda-обработчиков.
    """
    try:
        return inspect.getsource(_handler_function(route))
    except (OSError, TypeError):
        return ""


def _user_id_source(route: object) -> str:
    """Определить, откуда обработчик берёт идентификатор пользователя.

    Args:
        route: Объект маршрута FastAPI/Starlette.

    Returns:
        str: Метка ``путь``, ``тело``, ``сессия``, ``путь+сессия`` или
        ``нет`` — источник ``user_id`` из кода обработчика.
    """
    source = _endpoint_source(route)
    if not source:
        return "нет"
    origins: list[str] = []
    if USER_ID_FROM_PATH.search(source):
        origins.append("путь")
    if USER_ID_FROM_PAYLOAD.search(source) or USER_ID_FROM_BODY.search(source):
        origins.append(BODY_SOURCE_LABEL)
    if USER_ID_FROM_SESSION.search(source):
        origins.append("сессия")
    if not origins:
        return "нет"
    return "+".join(dict.fromkeys(origins))


def _path_params(route: object) -> str:
    """Собрать имена path-параметров роута.

    Args:
        route: Объект маршрута FastAPI/Starlette.

    Returns:
        str: Перечисленные через запятую имена параметров.
    """
    dependant = getattr(route, "dependant", None)
    if dependant is None:
        return ""
    return ", ".join(field.name for field in getattr(dependant, "path_params", []))


def _module_of(endpoint: object) -> str:
    """Вернуть имя модуля, где объявлен обработчик.

    Args:
        endpoint: Функция-обработчик роута.

    Returns:
        str: Дот-имя модуля либо пустая строка, если он неизвестен.
    """
    module = inspect.getmodule(endpoint) if endpoint is not None else None
    return module.__name__ if isinstance(module, ModuleType) else ""


def collect_routes() -> list[dict[str, str]]:
    """Пройти приложение и описать каждый HTTP-маршрут.

    Returns:
        list[dict[str, str]]: Отсортированные описания роутов с полями
            ``path``, ``methods``, ``name``, ``params``, ``user_id``,
            ``module``.
    """
    app = create_app()
    described: list[dict[str, str]] = []
    for route in app.routes:
        endpoint = getattr(route, "endpoint", None)
        if endpoint is None:
            continue
        described.append(
            {
                "path": str(getattr(route, "path", "")),
                "methods": ",".join(sorted(getattr(route, "methods", []) or [])),
                "name": str(getattr(route, "name", "")),
                "params": _path_params(route),
                "user_id": _user_id_source(route),
                "module": _module_of(endpoint),
            }
        )
    return sorted(described, key=lambda item: (item["path"], item["methods"]))


def main() -> None:
    """Напечатать markdown-строки таблицы: путь, метод, источник user_id."""
    routes = collect_routes()
    print("| Путь | Методы | Обработчик | user_id из | Требует auth | Проверка владельца |")
    print("| --- | --- | --- | --- | --- | --- |")
    for route in routes:
        module = route["module"].replace("backend.presentation.", "")
        handler = f"{module}.{route['name']}"
        print(f"| `{route['path']}` | {route['methods']} | `{handler}` | {route['user_id']} | | |")
    print(f"\nВсего роутов: {len(routes)}")


if __name__ == "__main__":
    main()
