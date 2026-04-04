# Anime Epic Moments

Anime Epic Moments — это Flask-приложение для поиска аниме, просмотра, сохранения избранного, создания хайлайтов и персональных рекомендаций на основе действий пользователя.

Проект организован как DDD-ориентированный backend с тонким delivery-слоем, явными use case, PostgreSQL, Redis, Alembic и серверным frontend-слоем в `src/frontend`.

## Быстрый старт

### Локальный запуск

1. Создай и активируй виртуальное окружение:

```powershell
python -m venv venv
venv\Scripts\activate
```

2. Установи зависимости:

```powershell
pip install -r requirements.txt
```

3. Создай локальный `.env` на основе примера и заполни секреты и параметры PostgreSQL:

```powershell
Copy-Item .env.example .env
```

4. Примени миграции базы данных:

```powershell
alembic -c build/alembic/alembic.ini upgrade head
```

5. Запусти приложение:

```powershell
python -m src.main
```

### Запуск в Docker

```powershell
docker compose -f build/docker-compose.yml up --build
```

`docker compose` поднимает `app`, `postgres`, `redis` и Redis GUI.
По умолчанию Docker-запуск использует `DATABASE_AUTO_INIT=1` и `RUN_DB_MIGRATIONS=0`,
потому что в репозитории нет revision-файлов Alembic в `build/alembic/versions`.

Redis GUI после старта доступен в браузере:

```text
http://localhost:8081
```

## Миграции базы данных

Создать новую миграцию:

```powershell
alembic -c build/alembic/alembic.ini revision --autogenerate -m "описание изменения"
```

Применить миграции:

```powershell
alembic -c build/alembic/alembic.ini upgrade head
```

## Тесты

Запуск backend-тестов:

```powershell
python -m pytest src/backend/tests -q
```

## Структура проекта

```text
build/                      Docker, Alembic, PostgreSQL/Redis runtime-скрипты и entrypoint
docs/                       Навигационная документация по проекту
src/main.py                 Локальная точка входа приложения
src/backend/                Backend-слои: delivery, use_case, domain, infrastructure
src/frontend/               Шаблоны, статические файлы и frontend-скрипты
```

## Карта документации

- Хаб документации: [docs/README.md](docs/README.md)
- Обзор архитектуры: [docs/architecture/overview.md](docs/architecture/overview.md)
- Доменная модель: [docs/domain/core.md](docs/domain/core.md)
- API и маршруты: [docs/api/endpoints.md](docs/api/endpoints.md)
- База данных и миграции: [docs/database/schema.md](docs/database/schema.md)
- Безопасность: [docs/security/security.md](docs/security/security.md)
- Деплой и Docker: [docs/deployment/overview.md](docs/deployment/overview.md)
- Тестовая стратегия: [docs/testing/strategy.md](docs/testing/strategy.md)
- Онбординг: [docs/onboarding.md](docs/onboarding.md)
- Конвенции разработки: [docs/conventions.md](docs/conventions.md)
- Глоссарий: [docs/glossary.md](docs/glossary.md)
- Пользовательские сценарии: [docs/use-cases.md](docs/use-cases.md)

## Путь чтения

1. [docs/architecture/overview.md](docs/architecture/overview.md)
2. [docs/domain/core.md](docs/domain/core.md)
3. [docs/api/endpoints.md](docs/api/endpoints.md)
4. [docs/database/schema.md](docs/database/schema.md)
5. [docs/security/security.md](docs/security/security.md)
6. [docs/deployment/overview.md](docs/deployment/overview.md)
7. [docs/testing/strategy.md](docs/testing/strategy.md)

## Ключевые точки входа в коде

- Bootstrap приложения: `src/main.py`
- Flask app factory: `src/backend/create_app.py`
- Граф зависимостей: `src/backend/dependencies/container.py`
- Runtime-настройки: `src/backend/dependencies/settings.py`
- Инициализация БД: `src/backend/infrastructure/files/database.py`
- SQLAlchemy-модели: `src/backend/infrastructure/models/sqlalchemy_models.py`
- HTTP-маршруты: `src/backend/delivery/api/v1`
- Use case: `src/backend/use_case`
- Тесты: `src/backend/tests/backend`

## Почему репозиторий устроен так

- Delivery-слой остается тонким и только переводит HTTP-запросы в вызовы use case.
- Use case содержат orchestration-логику, а не детали фреймворка.
- Domain-объекты описывают продуктовые сущности, а не наборы словарей.
- Infrastructure-слой содержит все побочные эффекты: БД, внешние API, кэш и auth-хелперы.
- Build- и deployment-артефакты вынесены в `build/`, чтобы код приложения и окружение не были перемешаны.
- Redis используется для кэшей, rate limiting и blacklist-а JWT, но при локальной деградации приложение умеет откатываться на in-memory fallback.
