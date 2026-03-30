UV=uv
COMPOSE=docker compose
DEV_COMPOSE=$(COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml
DEV_INFRA_SERVICES=postgres redis minio minio-init migrate

.PHONY: install format lint test dev-up dev-down dev-logs dev-up-infra dev-down-infra dev-logs-infra dev-migrate-local run-api run-api-reload run-worker migrate makemigrations

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

dev-up:
	$(DEV_COMPOSE) up --build -d

dev-down:
	$(DEV_COMPOSE) down --remove-orphans

dev-logs:
	$(DEV_COMPOSE) logs -f api nginx postgres redis minio

dev-up-infra:
	$(DEV_COMPOSE) up -d $(DEV_INFRA_SERVICES)

dev-down-infra:
	$(DEV_COMPOSE) stop $(DEV_INFRA_SERVICES)

dev-logs-infra:
	$(DEV_COMPOSE) logs -f $(DEV_INFRA_SERVICES)

dev-migrate-local:
	$(UV) run --env-file .env.local alembic upgrade head

run-api:
	$(UV) run uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000

run-api-reload:
	$(UV) run --env-file .env.local uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --reload

run-worker:
	$(UV) run python -m app.scheduler.cli run-hourly-slot

migrate:
	$(UV) run alembic upgrade head

makemigrations:
	$(UV) run alembic revision --autogenerate -m "$(message)"
