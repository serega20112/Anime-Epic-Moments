# Тестовая стратегия

## Описание

Backend покрыт зеркальной тестовой структурой в `tests/`. Цель — прозрачность: у каждого backend-модуля есть
соответствующий тестовый файл, поэтому от реализации до проверки можно дойти без догадок.

Набор тестов построен на `pytest`, с активным использованием параметризации, async-тестов и прямого покрытия
use case.

## Как это работает

Тестовая структура повторяет backend-слои:

- `tests/unit/presentation`: тесты маршрутов, мапперов запросов/ответов
- `tests/unit/application`: use case и application-сервисы (с моками внешних зависимостей)
- `tests/unit/domain`: entity, policy и value object
- `tests/unit/infrastructure`: кэш, внешние клиенты, security, media_proxy
- `tests/integration/infrastructure/repositories`: репозитории на реальной in-memory БД
- `tests/integration/infrastructure/di`: wiring графа зависимостей

Марки тестов (зарегистрированы в `pyproject.toml`):

- `@pytest.mark.unit` — чистая логика без внешнего IO
- `@pytest.mark.integration` — реальные компоненты (БД, репозитории, контейнер DI)
- `@pytest.mark.e2e` — полные HTTP-сценарии

Запуск тестов:

```powershell
uv run pytest
```

Быстрый прогон без coverage:

```powershell
uv run pytest -q --no-cov
```

На что оптимизированы тесты:

- поведение маршрутов и HTTP-статусы
- orchestration в use case
- семантика работы репозиториев
- разбор ответов внешних клиентов и fallback-сценарии (в т.ч. failover LLM)
- поведение кэшей
- security-хелперы вроде JWT и password hashing

## Почему это сделано так

- зеркальная структура делает покрытие видимым и поддерживаемым
- use case тестируются без лишнего втягивания HTTP в каждый сценарий
- repository-тесты особенно важны после перехода на PostgreSQL
- параметризация снижает дублирование, но не прячет edge-case'ы
- async-тесты в режиме `auto` (pytest-asyncio) позволяют тестировать асинхронный стек напрямую

## Где в коде

- `tests/conftest.py`
- `tests/unit/`
- `tests/integration/`
- `pyproject.toml` (`[tool.pytest.ini_options]`)

## Связанные документы

- [Обзор архитектуры](../architecture/overview.md)
- [Конвенции](../conventions.md)
- [Стайлгайд](../styleguide.md)
- [Онбординг](../onboarding.md)