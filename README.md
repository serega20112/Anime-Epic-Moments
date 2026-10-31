# Anime Epic Moments (AEM)

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116-009688?logo=fastapi&logoColor=white)
![Dishka](https://img.shields.io/badge/DI-Dishka-6B4FBB)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0_async-D71F00?logo=sqlalchemy&logoColor=white)
![Ruff](https://img.shields.io/badge/lint-Ruff-D7FF64?logo=ruff&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-compose-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

**AEM** (Anime Epic Moments) — веб-платформа для аниме: каталог тайтлов, умный
поиск по описанию на естественном языке, хайлайты (моменты серий) с публичной
лентой, коллекции, избранное, оценки и персональные рекомендации.

AEM не хранит и не раздаёт видеофайлы: платформа агрегирует **источники
просмотра** (озвучки и качества) от внешних провайдеров и проксирует HLS-поток
через собственный медиа-прокси.

## Быстрый старт (Docker)

Требуется Docker с плагином Compose.

```bash
git clone https://github.com/serega20112/Anime-Epic-Moments.git
cd Anime-Epic-Moments
cp .env.example .env
docker compose up -d
```

Контейнер `app` при старте сам применяет миграции Alembic, после чего поднимает
`gunicorn` с воркерами `uvicorn`.

| Что | Адрес |
| --- | --- |
| Приложение | http://localhost:5000 |
| Swagger UI | http://localhost:5000/docs |
| ReDoc | http://localhost:5000/redoc |
| Живость процесса | http://localhost:5000/health |
| Готовность зависимостей | http://localhost:5000/ready |
| Redis GUI (Redis Commander) | http://localhost:8081 |

Порт приложения задаётся переменной `APP_PORT` (по умолчанию `5000`), порт Redis
GUI — `REDIS_COMMANDER_PORT` (по умолчанию `8081`). Перед выкатом в интернет
обязательно смените `SECRET_KEY` в `.env`: вне режима отладки приложение не
стартует без него.

## Локальный старт (нативный uv)

Требуются Python 3.12, [uv](https://docs.astral.sh/uv/) и Docker (только для
PostgreSQL и Redis).

```bash
uv sync
cp .env.example .env
docker compose up -d postgres redis
uv run alembic -c migrations/alembic.ini upgrade head
uv run uvicorn backend.main:app --app-dir src --reload --port 5000
```

`--app-dir src` добавляет каталог `src` в путь импорта, поэтому запуск не зависит
от переменных оболочки конкретной ОС. То же касается остальных команд ниже.

## Проверки перед коммитом

| Проверка | Команда |
| --- | --- |
| Линтер и формат | `uv run ruff check src tests migrations` |
| Форматирование | `uv run ruff format --check src tests migrations` |
| Границы слоёв | `uv run python scripts/check_imports.py` |
| Докстринги и комментарии | `uv run python scripts/check_style.py` |
| Контракт OpenAPI | `uv run python scripts/export_openapi.py --check` |
| Тесты с покрытием | `uv run pytest` |
| Соответствие `uv.lock` | `uv lock --check` |

Те же проверки выполняет CI в `.github/workflows/ci.yml`. Стандарты тестирования —
уровни, нейминг, фикстуры и изоляция — зафиксированы в
[docs/05-testing](docs/05-testing/01-testing-strategy.md).

## Карта документации

Документация живёт в каталоге [docs/](docs/README.md). Точка входа — навигатор
[`docs/README.md`](docs/README.md), ниже — короткий маршрут по разделам.

| Блок | Для кого | Что внутри |
| --- | --- | --- |
| [00-foundation](docs/00-foundation/) | Продукт, заказчик, интеграторы | [Глоссарий](docs/00-foundation/glossary.md) (единый язык AEM), [Видение продукта](docs/00-foundation/product-vision.md) |
| [01-architecture](docs/01-architecture/) | Разработчики, архитектор | [Обзор и C4](docs/01-architecture/overview.md), [Слои и правила](docs/01-architecture/layers-and-rules.md), [Модель предметной области](docs/01-architecture/domain-model.md), [Поток запроса](docs/01-architecture/data-flow.md), [DI на Dishka](docs/01-architecture/di-dishka.md), [Модель данных](docs/01-architecture/data-model.md), [Безопасность](docs/01-architecture/security.md) |
| [02-integrations-and-services](docs/02-integrations-and-services/) | Разработчики интеграций | [Провайдеры источников](docs/02-integrations-and-services/providers.md), [Умный поиск и LLM](docs/02-integrations-and-services/llm-search.md), [Медиа-прокси](docs/02-integrations-and-services/media-proxy.md) |
| [03-ops](docs/03-ops/) | DevOps, дежурный | [Переменные окружения](docs/03-ops/env-reference.md), [Развёртывание](docs/03-ops/deployment.md), [Сопровождение](docs/03-ops/maintenance.md) |
| [04-dev-guide](docs/04-dev-guide/) | Новый разработчик | [Онбординг](docs/04-dev-guide/onboarding.md), [Как добавить фичу](docs/04-dev-guide/feature-workflow.md), [Соглашения](docs/04-dev-guide/conventions.md) |
| [05-testing](docs/05-testing/) | Все, кто пишет и ревьюит тесты | [Стратегия](docs/05-testing/01-testing-strategy.md), [Unit](docs/05-testing/02-unit-testing.md), [Integration](docs/05-testing/03-integration-testing.md), [E2E](docs/05-testing/04-e2e-testing.md), [Фикстуры и изоляция](docs/05-testing/05-fixtures-and-isolation.md) |
| [06-adr](docs/06-adr/) | Архитектор, ревьюер | Решения: [Clean Architecture](docs/06-adr/0001-clean-architecture.md), [Dishka](docs/06-adr/0002-dishka-di.md), [uv](docs/06-adr/0003-uv-package-manager.md), [LLM-fallback](docs/06-adr/0004-llm-fallback-resilience.md), [Раскладка infrastructure](docs/06-adr/0005-infrastructure-packages.md) |

## Структура репозитория

```text
src/backend/
├── domain/          чистое ядро: сущности, value objects, политики, исключения
├── application/     сценарии (use cases), порты, DTO, прикладные сервисы
├── infrastructure/  адаптеры: SQLAlchemy, Redis, внешние API, DI на Dishka
├── presentation/    FastAPI-роуты, схемы запросов и ответов, Jinja2-страницы
├── config/          Settings и секции переменных окружения
└── events/          lifespan приложения
src/frontend/        HTML-шаблоны и статика
migrations/          Alembic (alembic.ini, env.py, versions/)
scripts/             гейты качества и генераторы артефактов
tests/               unit, integration, support-фикстуры
```

## Лицензия

Проект распространяется по лицензии MIT — см. [LICENSE](LICENSE).
