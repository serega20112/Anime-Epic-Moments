# Anime Epic Moments

Anime Epic Moments — приложение для поиска аниме, просмотра (с выбором озвучки), сохранения избранного, создания
хайлайтов и персональных рекомендаций на основе действий пользователя.

Backend — FastAPI + dishka (DI), организован по DDD: тонкий presentation-слой, явные use case, домен без зависимостей
от фреймворков. Данные: PostgreSQL + Redis, миграции Alembic. Поиск по описанию — LLM (Google Gemini с fallback на
Hugging Face). Видео — Kodik и AniLibria через media-proxy с allowlist хостингов CDN.

## Быстрый старт

### Локальный запуск

Требования: установленный [uv](https://docs.astral.sh/uv/) (установка:

```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

).

1. Установи зависимости (создаст `.venv` и заберёт `uv.lock`):

```powershell
uv sync
```

2. Создай локальный `.env` на основе примера и заполни секреты и параметры PostgreSQL:

```powershell
Copy-Item .env.example .env
```

3. Примени миграции базы данных:

```powershell
uv run alembic -c build/alembic/alembic.ini upgrade head
```

4. Запусти приложение:

```powershell
$env:PYTHONPATH = "src"
uv run python -m backend.main
```

### Запуск в Docker

```powershell
docker compose -f build/docker-compose.yml up --build
```

`docker compose` поднимает `app`, `postgres`, `redis` и Redis GUI. По умолчанию Docker-запуск использует
`DATABASE_AUTO_INIT=1`, когда в `build/alembic/versions` нет revision-файлов.

Redis GUI после старта доступен в браузере:

```text
http://localhost:8081
```

## Миграции базы данных

Создать новую миграцию:

```powershell
uv run alembic -c build/alembic/alembic.ini revision --autogenerate -m "описание изменения"
```

Применить миграции:

```powershell
uv run alembic -c build/alembic/alembic.ini upgrade head
```

## Тесты

```powershell
uv run pytest
```

Линт, формат и границы слоёв — см. [docs/styleguide.md](docs/styleguide.md).

## Структура проекта

```text
build/                      Docker, Alembic, PostgreSQL/Redis runtime-скрипты и entrypoint
docs/                       Документация и стайлгайд
src/backend/                Backend-слои: presentation, application, domain, infrastructure, config
src/frontend/               Шаблоны, статические файлы и frontend-скрипты
tests/                      unit/ и integration/ тесты (зеркалят src/backend)
pyproject.toml + uv.lock    Зависимости (uv) и конфиги ruff/pytest/import-linter
ruff.toml                   Конфиг линта
```

## Карта документации

- Хаб документации: [docs/README.md](docs/README.md)
- **Стайлгайд по работе с проектом и репозиторием: [docs/styleguide.md](docs/styleguide.md)**
- Онбординг: [docs/onboarding.md](docs/onboarding.md)
- Конвенции разработки: [docs/conventions.md](docs/conventions.md)
- Обзор архитектуры: [docs/architecture/overview.md](docs/architecture/overview.md)
- Доменная модель: [docs/domain/core.md](docs/domain/core.md)
- API и маршруты: [docs/api/endpoints.md](docs/api/endpoints.md)
- База данных и миграции: [docs/database/schema.md](docs/database/schema.md)
- Безопасность: [docs/security/security.md](docs/security/security.md)
- Деплой и Docker: [docs/deployment/overview.md](docs/deployment/overview.md)
- Тестовая стратегия: [docs/testing/strategy.md](docs/testing/strategy.md)
- Глоссарий: [docs/glossary.md](docs/glossary.md)
- Пользовательские сценарии: [docs/use-cases.md](docs/use-cases.md)

## Ключевые точки входа в коде

- Точка входа и uvicorn: `src/backend/main.py`
- App factory (FastAPI): `src/backend/presentation/app_factory.py` / `create_app`
- Граф зависимостей (dishka): `src/backend/infrastructure/di/`
- Runtime-настройки: `src/backend/config/` (`Settings`)
- SQLAlchemy-модели: `src/backend/infrastructure/models/` (фасад — `__init__.py`, по папке на зону)
- HTTP-маршруты: `src/backend/presentation/api/v1/`
- Use cases: `src/backend/application/use_cases/`
- Внешние провайдеры (LLM, Kodik, AniLibria, YouTube): `src/backend/infrastructure/external/`
- Медиа-прокси: `src/backend/infrastructure/media_proxy/`
- Тесты: `tests/`

## Почему репозиторий устроен так

- Presentation-слой тонкий: HTTP-запросы переводятся в вызовы use case, никакой бизнес-логики на уровне роутов.
- Use cases оркестрируют бизнес-действия; домен описывает продуктовые сущности и правила, не зная про FastAPI/SQLAlchemy.
- Infrastructure владеет побочными эффектами: БД, внешние API, кэш, безопасность, DI.
- Границы слоёв проверяются import-linter (`Layer Boundaries`), гейты — ruff + pytest в CI.
- Зависимости управляются через uv: `pyproject.toml` + зафиксированный `uv.lock`.
- Build- и deployment-артефакты вынесены в `build/`.