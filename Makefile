.PHONY: install dev test lint format migrate migration up down logs

install:
	cd backend && python -m venv .venv && .venv/Scripts/python -m pip install -U pip && .venv/Scripts/python -m pip install -e ".[dev]"
	cd frontend && npm install

dev:
	cd backend && .venv/Scripts/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	cd backend && .venv/Scripts/python -m pytest

lint:
	cd backend && .venv/Scripts/python -m ruff check app tests && .venv/Scripts/python -m mypy app
	cd frontend && npm run lint && npm run type-check

format:
	cd backend && .venv/Scripts/python -m ruff format app tests
	cd frontend && npm run format

migrate:
	cd backend && .venv/Scripts/python -m alembic upgrade head

migration:
	cd backend && .venv/Scripts/python -m alembic revision --autogenerate -m "$(m)"

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f
