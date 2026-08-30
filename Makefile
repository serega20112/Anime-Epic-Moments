.PHONY: install lint check-imports test test-fast precommit-install precommit-run-all precommit-init docker-build docker-run docker-down clean

install:
	uv sync

install-all:
	uv sync --all-groups

lint:
	uv run ruff check src tests
	uv run ruff format --check src tests

check-imports:
	PYTHONPATH=src uv run lint-imports

test:
	uv run pytest

test-fast:
	uv run pytest -q --no-cov

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

docker-down:
	docker compose -f docker-compose.yml down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache .mypy_cache
	rm -rf .venv