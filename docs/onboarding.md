# Онбординг

## Описание

Этот документ — самый короткий практический путь для нового разработчика: как поднять приложение, понять структуру
репозитория и сделать первое безопасное изменение.

## Как это работает

### Чеклист первого часа

1. Прочитать [architecture/overview.md](architecture/overview.md).
2. Прочитать [domain/core.md](domain/core.md).
3. Установить [uv](https://docs.astral.sh/uv/) и зависимости проекта.
4. Создать `.env` на основе `.env.example`.
5. Убедиться, что PostgreSQL доступен и `DATABASE_URL` указывает на него.
6. Применить миграции через Alembic.
7. Запустить приложение.
8. Прогнать тесты, линт и границы слоёв.
9. Перед правками прочитать [styleguide.md](styleguide.md) и [conventions.md](conventions.md).

Команды (Windows PowerShell):

```powershell
irm https://astral.sh/uv/install.ps1 | iex
uv sync
Copy-Item .env.example .env
uv run alembic -c build/alembic/alembic.ini upgrade head
$env:PYTHONPATH = "src"
uv run python -m backend.main
uv run pytest
uv run ruff check src tests
$env:PYTHONPATH = "src"; uv run lint-imports
```

Куда смотреть для типовых задач:

- новый route или страница: `src/backend/presentation/api/v1` и `src/frontend/templates`
- новое бизнес-поведение: `src/backend/application/use_cases`
- доменные правила: `src/backend/domain`
- изменение БД: `src/backend/infrastructure/models` и `build/alembic`
- новая внешняя интеграция: `src/backend/infrastructure/external`
- новые настройки окружения: `src/backend/config/sections` и `.env.example`
- тесты: `tests/unit` и `tests/integration`

## Почему это сделано так

- новый разработчик не должен разбирать репозиторий по импортам вслепую
- PostgreSQL и Alembic обязательны с первого дня, чтобы локальное поведение совпадало с runtime
- чтение архитектуры и стайлгайда до начала правок снижает риск писать код не в том слое
- uv гарантирует одинаковое окружение локально и в CI (зафиксированный `uv.lock`)

## Где в коде

- `README.md`
- `../src/backend/main.py`
- `src/backend/presentation/app_factory.py`
- `src/backend/infrastructure/di/`
- `docker-compose.yml`
- `build/alembic/alembic.ini`
- `pyproject.toml`, `ruff.toml`

## Связанные документы

- [Хаб документации](README.md)
- [Стайлгайд](styleguide.md)
- [Конвенции](conventions.md)
- [Тестовая стратегия](testing/strategy.md)