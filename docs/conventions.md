# Конвенции

## Описание

Эти правила нужны для того, чтобы кодовая база оставалась предсказуемой по мере роста. Цель не в формальности, а в стабильности и читаемости. Практические команды и гейты — в [styleguide.md](styleguide.md).

## Как это работает

Базовые правила:

- routes разбирают HTTP-вход и сразу делегируют выполнение use case
- use cases оркестрируют бизнес-действия и вызовы зависимостей
- domain-модули содержат продуктовые сущности, политики и правила
- интерфейсы репозиториев и сервисов живут в domain, реализации — в infrastructure
- репозитории владеют деталями хранения данных
- infrastructure-клиенты владеют сетью и логикой внешних провайдеров
- настройки читаются из окружения через `src/backend/config`, сборка зависимостей — в `src/backend/infrastructure/di`
- build- и migration-файлы находятся в `build/`
- тесты зеркалят структуру `src/backend` в `tests/unit` и `tests/integration`
- новая документация должна следовать [templates/document-template.md](templates/document-template.md)

Практически это означает:

- новый endpoint обычно требует route, use case и тестов
- новое поле в БД требует изменения SQLAlchemy-модели и генерации Alembic-миграции
- новый провайдер требует infrastructure-клиент и wiring в dishka-контейнере
- новый параметр окружения требует функции чтения в `config/sections`, подключения в `Settings`
  и строки с комментарием в `.env.example`

Границы слоёв закреплены контрактом import-linter «Layer Boundaries»
(`presentation → infrastructure → application → domain`) и проверяются командой `lint-imports`.

## Почему это сделано так

- единообразие снижает стоимость онбординга
- зеркальные тесты уменьшают слепые зоны покрытия
- тонкие routes не дают FastAPI-деталям протечь в core-логику
- явные build-границы делают deployment-изменения аудируемыми
- односторонние зависимости между слоями позволяют менять инфраструктуру, не трогая домен

## Где в коде

- `src/backend/presentation/api/v1`
- `src/backend/application/use_cases`
- `src/backend/domain`
- `src/backend/infrastructure`
- `src/backend/config`
- `tests/unit`, `tests/integration`
- `build`
- `docs/templates/document-template.md`

## Связанные документы

- [Стайлгайд](styleguide.md)
- [Обзор архитектуры](architecture/overview.md)
- [Тестовая стратегия](testing/strategy.md)
- [Онбординг](onboarding.md)