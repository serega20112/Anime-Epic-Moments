.PHONY: install install-dev lint test run docker-up docker-down clean

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt -r requirements-dev.txt

lint:
	ruff check src/

test:
	python -m pytest src/backend/tests -v

run:
	python -m src.main

docker-up:
	docker compose -f build/docker-compose.yml up --build -d

docker-down:
	docker compose -f build/docker-compose.yml down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache