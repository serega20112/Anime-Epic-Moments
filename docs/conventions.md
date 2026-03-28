# Конвенции

## Описание

Эти правила нужны для того, чтобы кодовая база оставалась предсказуемой по мере роста. Цель не в формальности, а в стабильности и читаемости.

## Как это работает

Базовые правила:

- routes разбирают HTTP-вход и сразу делегируют выполнение
- use case оркестрируют бизнес-действия и вызовы зависимостей
- domain-модули содержат продуктовые сущности и правила
- репозитории владеют деталями хранения данных
- infrastructure-клиенты владеют сетью и логикой внешних провайдеров
- настройки и сборка зависимостей живут в `src/backend/dependencies`
- build- и migration-файлы находятся в `build/`
- тесты зеркалят backend-структуру
- новая документация должна следовать [templates/document-template.md](templates/document-template.md)

Практически это означает:

- новый endpoint обычно требует route, use case и тестов
- новое поле в БД требует изменения SQLAlchemy-модели и генерации Alembic-миграции
- новый провайдер требует infrastructure-клиент и wiring в контейнере

## Почему это сделано так

- единообразие снижает стоимость онбординга
- зеркальные тесты уменьшают слепые зоны покрытия
- тонкие routes не дают Flask-деталям протечь в core-логику
- явные build-границы делают deployment-изменения аудируемыми

## Где в коде

- `src/backend/delivery/api/v1`
- `src/backend/use_case`
- `src/backend/domain`
- `src/backend/infrastructure`
- `src/backend/dependencies`
- `src/backend/tests/backend`
- `build`
- `docs/templates/document-template.md`

## Связанные документы

- [Обзор архитектуры](architecture/overview.md)
- [Тестовая стратегия](testing/strategy.md)
- [Онбординг](onboarding.md)
