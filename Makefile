UV=uv

.PHONY: install format lint test run-api run-worker migrate makemigrations

install:
	$(UV) sync --group dev

format:
	$(UV) run ruff format .
	$(UV) run ruff check . --fix

lint:
	$(UV) run ruff format . --check
	$(UV) run ruff check .
	$(UV) run mypy .

test:
	$(UV) run pytest --cov

run-api:
	$(UV) run uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000

run-worker:
	$(UV) run python -m app.scheduler.cli run-hourly-slot

migrate:
	$(UV) run alembic upgrade head

makemigrations:
	$(UV) run alembic revision --autogenerate -m "$(message)"
