.PHONY: run test lint format openapi migrate docker-up docker-down

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/

lint:
	ruff check app tests
	mypy app

format:
	ruff format app tests
	ruff check --fix app tests

openapi:
	python scripts/export_openapi.py

migrate:
	alembic upgrade head

docker-up:
	docker compose up -d

docker-down:
	docker compose down
