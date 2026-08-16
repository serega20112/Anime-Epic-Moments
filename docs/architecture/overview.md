# Обзор архитектуры

## Описание

Система организована как многослойное FastAPI-приложение с DDD-подобными границами. Presentation-слой принимает HTTP-запросы,
use case оркестрируют действия, domain-объекты описывают язык продукта, а infrastructure-слой владеет побочными
эффектами: PostgreSQL, Redis, внешними провайдерами аниме, кэшированием, JWT и хешированием паролей.

Цель дизайна — не академическая чистота, а прагматичное разделение. Код должен быть легко прослеживаем от маршрута до
use case и репозитория и при этом оставаться тестопригодным по слоям.

## Как это работает

Высокоуровневая схема слоев:

```mermaid
flowchart TB
    Browser[Браузер или API-клиент]
    Routes[FastAPI routes]
    UseCases[Use case]
    Domain[Domain entities, policies, value objects]
    Services[Application services]
    Repos[Репозитории]
    External[Внешние API и mailer]
    DB[(PostgreSQL)]
    Redis[(Redis)]
    Templates[HTML-шаблоны или JSON]

    Browser --> Routes
    Routes --> UseCases
    UseCases --> Domain
    UseCases --> Services
    UseCases --> Repos
    Services --> Repos
    Services --> External
    Repos --> DB
    Services --> Redis
    Routes --> Templates
    UseCases --> Templates
```

Типичный путь пользовательского действия выглядит так:

```mermaid
sequenceDiagram
    participant U as Пользователь
    participant R as FastAPI route
    participant C as Container
    participant UC as Use case
    participant S as Service или Repository
    participant DB as PostgreSQL или внешний API

    U->>R: HTTP-запрос
    R->>C: Разрешение зависимости
    C->>UC: Сборка use case
    R->>UC: Выполнение с разобранным входом
    UC->>S: Чтение или запись данных
    S->>DB: Запрос в базу или провайдер
    DB-->>S: Результат
    S-->>UC: Domain object или DTO
    UC-->>R: View model
    R-->>U: HTML или JSON
```

Конкретные backend-слои:

- Presentation: FastAPI routes в `src/backend/presentation/api/v1` (тонкие: HTTP → use case)
- Application orchestration: `src/backend/application/use_cases`
- Domain-язык: `src/backend/domain`
- Побочные эффекты: `src/backend/infrastructure`
- Runtime-композиция (dishka): `src/backend/infrastructure/di`
- Настройки: `src/backend/config`
- Frontend-шаблоны и статика: `src/frontend`
- Окружение и упаковка: `build`

## Почему это сделано так

- Тонкие routes не смешивают HTTP-детали с бизнес-поведением.
- Use case дают явную точку входа для каждого пользовательского действия.
- Domain-типы не дают продуктовой логике расползтись по неструктурированным словарям.
- Infrastructure можно менять отдельно, что особенно важно при большом количестве внешних интеграций.
- Redis вынесен в infrastructure-слой, потому что это технический инструмент для кэша, лимитов и временных
  security-состояний, а не часть доменной модели.
- `build/` отделяет deployment- и migration-логику от кода приложения и уменьшает случайную связность.

## Где в коде

- `../../src/backend/main.py`
- `src/backend/presentation/app_factory.py`
- `src/backend/infrastructure/di/`
- `src/backend/config/settings.py`
- `src/backend/presentation/api/v1`
- `src/backend/application/use_cases`
- `src/backend/domain`
- `src/backend/infrastructure`
- `src/frontend`
- `build`

## Связанные документы

- [Хаб документации](../README.md)
- [Доменная модель](../domain/core.md)
- [API и маршруты](../api/endpoints.md)
- [Схема базы данных](../database/schema.md)
- [Деплой](../deployment/overview.md)
