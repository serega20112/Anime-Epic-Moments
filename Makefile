.PHONY: install install-all lock lock-check lock-upgrade lint check-style check-imports export-openapi check-openapi db-upgrade db-revision db-check db-history test test-fast precommit-install precommit-run-all precommit-init docker-build docker-run docker-up docker-dev docker-rebuild docker-restart docker-shell docker-logs docker-down docker-nuke clean run test-integration-pg db-create-test

install:
	uv sync

install-all:
	uv sync --all-groups

# Пересобрать uv.lock после правок в pyproject.toml.
lock:
	uv lock

# Проверить, что uv.lock соответствует pyproject.toml (гейт как в CI).
lock-check:
	uv lock --check

# Обновить версии зависимостей в uv.lock.
lock-upgrade:
	uv lock --upgrade

lint:
	uv run ruff check src tests migrations
	uv run ruff format --check src tests migrations

# Стандарт заказа (п. 1.1 ТЗ): докстринги на русском, объяснения не в #-комментариях.
check-style:
	uv run ruff check src tests --select ERA001
	uv run python scripts/check_style.py

check-imports:
	uv run python scripts/check_imports.py

export-openapi:
	uv run python scripts/export_openapi.py

check-openapi:
	uv run python scripts/export_openapi.py --check

db-upgrade:
	uv run alembic -c migrations/alembic.ini upgrade head

# Новая миграция: make db-revision M="add index on highlights"
db-revision:
	uv run alembic -c migrations/alembic.ini revision --autogenerate -m "$(M)"

db-check:
	uv run alembic -c migrations/alembic.ini check

db-history:
	uv run alembic -c migrations/alembic.ini history

test:
	uv run pytest

test-fast:
	uv run pytest -q --no-cov

# Интеграционные тесты против боевого PostgreSQL: нужен `docker compose up -d postgres`
# и одноразовый `make db-create-test`. Без TEST_DATABASE_URL фикстуры используют in-memory sqlite.
test-integration-pg:
	TEST_DATABASE_URL=postgresql+asyncpg://anime_epic_moments_user:anime_epic_moments_password@localhost:5432/anime_epic_moments_test uv run pytest tests/integration -q --no-cov

db-create-test:
	docker compose exec -T postgres createdb -U anime_epic_moments_user anime_epic_moments_test || true

precommit-install:
	uv run pre-commit install

precommit-run-all:
	uv run pre-commit run --all-files

precommit-init:
	uv run pre-commit install
	uv run pre-commit autoupdate

docker-build:
	docker build -f Dockerfile -t anime-epic-moments .

docker-run:
	docker compose -f docker-compose.yml up --build -d

docker-up:
	docker compose up -d

docker-rebuild:
	docker compose up -d --build

docker-restart:
	docker compose restart app

docker-shell:
	docker compose exec app sh

# Локальный запуск приложения без контейнера (postgres/redis остаются в docker).
run:
	PYTHONPATH=src uv run python -m backend.main

# Dev-контейнер приложения с автоперезагрузкой кода поверх postgres/redis из compose.
docker-dev:
	docker compose up -d postgres redis
	docker compose run --rm --service-ports app dev

docker-logs:
	docker compose logs -f app

docker-down:
	docker compose down

docker-nuke:
	docker compose down -v --remove-orphans

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache .mypy_cache
	rm -rf .venv