# Тестовая стратегия

## Описание

Backend покрыт зеркальной тестовой структурой в `src/backend/tests/backend`. Цель — прозрачность: у каждого backend-модуля есть соответствующий тестовый файл, поэтому от реализации до проверки можно дойти без догадок.

Набор тестов построен на `pytest`, с активным использованием параметризации и прямого покрытия use case.

## Как это работает

Тестовая структура повторяет backend-слои:

- `src/backend/tests/backend/delivery`: тесты маршрутов
- `src/backend/tests/backend/dependencies`: тесты настроек и контейнера
- `src/backend/tests/backend/domain`: entity, policy и value object
- `src/backend/tests/backend/infrastructure`: кэш, внешние клиенты, модели, репозитории, security
- `src/backend/tests/backend/repository`: контрактные тесты репозиториев
- `src/backend/tests/backend/services`: сервисы оркестрации
- `src/backend/tests/backend/use_case`: пользовательские действия приложения

Запуск тестов:

```powershell
python -m pytest src/backend/tests -q
```

На что оптимизированы тесты:

- поведение маршрутов и HTTP-статусы
- orchestration в use case
- семантика работы репозиториев
- разбор ответов внешних клиентов и fallback-сценарии
- поведение кэшей
- security-хелперы вроде JWT и password hashing

## Почему это сделано так

- зеркальная структура делает покрытие видимым и поддерживаемым
- use case тестируются без лишнего втягивания HTTP в каждый сценарий
- repository-тесты особенно важны после перехода на PostgreSQL
- параметризация снижает дублирование, но не прячет edge-case'ы

## Где в коде

- `src/backend/tests/conftest.py`
- `src/backend/tests/backend`
- `src/backend/tests/backend/delivery/api/v1`
- `src/backend/tests/backend/infrastructure/repositories`
- `src/backend/tests/backend/use_case`

## Связанные документы

- [Обзор архитектуры](../architecture/overview.md)
- [Конвенции](../conventions.md)
- [Онбординг](../onboarding.md)
