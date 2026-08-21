# Конвенции

## Описание

Эти правила нужны, чтобы кодовая база оставалась предсказуемой по мере роста: где что лежит,
кто за что отвечает, что появляется при добавлении новой функциональности. Цель не формальность,
а стабильность и читаемость.

**Для кого:** все разработчики; читать после [architecture/overview.md](architecture/overview.md).

Разделение ответственности между документами:

- **здесь** — архитектурные соглашения и рецепты «что появится, если добавить X»;
- **[contribution-guide.md](contribution-guide.md)** — обязательные требования к коду, неймингу,
  ошибкам, коммитам, PR и review;
- **[styleguide.md](styleguide.md)** — окружение, команды, локальные гейты.

## Как это работает

### Базовые правила слоёв

- `presentation` (routes) разбирает HTTP-вход и сразу делегирует use case. В хендлере нет
  бизнес-логики, SQL и прямых обращений к моделям.
- `application` (use cases, services) оркестрирует бизнес-действия: валидирует политику через
  домен, зовёт репозитории/сервисы, управляет транзакцией (UnitOfWork), инвалидирует кэши.
- `domain` содержит сущности, value objects, политики и **интерфейсы** репозиториев и внешних
  сервисов. Не знает ни про FastAPI, ни про SQLAlchemy.
- `infrastructure` — реализации интерфейсов: репозитории, клиенты внешних API, кэш, безопасность,
  DI-провайдеры dishka. Владеет деталями хранения и сети.
- Настройки читаются только из окружения через `src/backend/config`; сборка зависимостей — только
  в `src/backend/infrastructure/di`.
- Границы закреплены контрактом import-linter «Layer Boundaries»
  (`presentation → infrastructure → application → domain`) и проверяются командой `lint-imports`.

### Рецепты: что появится при добавлении X

| Добавляем                        | Обязательно появляется                                                                                       |
|----------------------------------|--------------------------------------------------------------------------------------------------------------|
| Endpoint                         | route в `presentation/api/v1/<зона>_route.py`, command/query-DTO, use case, unit-тест use case + integration-тест роута, строка в [api/endpoints.md](api/endpoints.md) |
| Поле в таблице                   | изменение SQLAlchemy-модели, Alembic-миграция, тест репозитория, правка [database/schema.md](database/schema.md) |
| Доменное правило                 | метод политики (`<Сущность>Policy`) или инвариант сущности + unit-тесты домена                                |
| Внешний провайдер                | клиент в `infrastructure/external/`, интерфейс в `application/interface/services/`, wiring в `di/providers/`, fallback-логика |
| Параметр окружения               | функция в `config/sections/<зона>.py`, атрибут в `Settings`, закомментированная заглушка в `.env.example`      |
| Кэшируемая сущность              | интерфейс кэша в `application/interface/services/`, реализация в `infrastructure/cache/`, инвалидация в пишущих use cases |

Тесты зеркалят структуру `src/backend`: `tests/unit` — без внешнего IO, `tests/integration` —
реальные компоненты поверх SQLite in-memory. Правила написания тестов —
[testing/strategy.md](testing/strategy.md).

Новая документация обязана следовать шаблону [templates/document-template.md](templates/document-template.md)
и обновляться в том же PR, что и изменение кода ([contribution-guide.md](contribution-guide.md), п. 6).

## Почему это сделано так

- Единообразие снижает стоимость онбординга: новый разработчик находит код там же, где нашёл похожий.
- Зеркальные тесты уменьшают слепые зоны покрытия и упрощают навигацию от бага к тесту.
- Тонкие routes не дают деталям FastAPI протечь в core-логику — её можно запускать и тестировать
  без HTTP.
- Явная DI-граница делает граф зависимостей видимым целиком в одном месте (dishka-провайдеры),
  а не размазанным по конструкторам.
- Односторонние зависимости позволяют менять инфраструктуру, не трогая домен: Postgres → другая СУБД,
  Gemini → другой LLM — это изменения уровня infrastructure.

## Где в коде

- `src/backend/presentation/api/v1` — роутеры зон (anime, auth, watch, highlights, ...)
- `src/backend/application/use_cases`, `src/backend/application/dto` — use cases и их DTO
- `src/backend/domain` — агрегаты, сущности, value objects, политики; порты (репозитории, сервисы, UoW) — в `src/backend/application/interface`
- `src/backend/infrastructure` — репозитории, external-клиенты, кэш, security, DI
- `src/backend/config` — секции настроек и `Settings`
- `tests/unit`, `tests/integration` — зеркальные тесты
- `build` — Docker, Alembic, entrypoint

## Связанные документы

- [Contribution Guide](contribution-guide.md)
- [Стайлгайд](styleguide.md)
- [Архитектура](architecture/overview.md)
- [Тестовая стратегия](testing/strategy.md)
- [Онбординг](onboarding.md)
