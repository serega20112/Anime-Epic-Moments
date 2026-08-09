.PHONY: install-dev lint check-imports test docker-build docker-run docker-down clean

install-dev:
	pip install -r requirements/dev.txt -r requirements/lint.txt

lint:
	ruff check src
	ruff format --check src

check-imports:
	lint-imports

test:
	python -m pytest

docker-build:
	docker build -f build/Dockerfile -t anime-epic-moments .

docker-run:
	docker compose -f build/docker-compose.yml up --build -d

docker-down:
	docker compose -f build/docker-compose.yml down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache .mypy_cache