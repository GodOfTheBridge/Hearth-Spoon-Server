# ПечьДаЛожка Backend

Production-ready starter backend for the mobile application `ПечьДаЛожка`.

## Архитектура

Проект построен в слоистом стиле с четким разделением ответственности:

1. `presentation layer`
   - FastAPI endpoints
   - request/response schemas
   - exception mapping
   - admin/public API split
2. `application layer`
   - orchestration use cases
   - query services
   - publication service
   - provider/storage/repository abstractions
3. `domain layer`
   - enums
   - validated entities
   - recipe JSON schema
   - domain exceptions
4. `infrastructure layer`
   - SQLAlchemy repositories
   - OpenAI adapters
   - S3-compatible storage
   - Redis lock and rate limiting
   - PostgreSQL persistence

## Ключевые решения

1. Для текстовой генерации используется `OpenAI Responses API` со strict JSON schema structured output.
2. Для изображения используется отдельный `OpenAI Images API` adapter.
3. Hourly generation запускается не внутри web worker, а через отдельный cron-friendly CLI:
   - `python -m app.scheduler.cli run-hourly-slot`
4. Защита от дублей сделана в несколько слоев:
   - Redis lock как быстрый межпроцессный guard
   - PostgreSQL advisory lock как дополнительный источник истины для production deployments
   - уникальный `idempotency_key` и уникальный slot constraint в PostgreSQL
5. Согласованность реализована прагматично:
   - сначала создается и фиксируется job
   - затем выполняются внешние вызовы
   - затем в одной DB transaction сохраняются recipe + image metadata + statuses
   - если upload уже был, а DB commit упал, выполняется compensating delete в storage
6. Секреты читаются только из env; `.env` не коммитится, есть `.env.example`.
7. Public API отдает только опубликованные рецепты; автоматическую публикацию можно включить env-флагом `AUTO_PUBLISH_GENERATED_RECIPES=true`.

## Структура проекта

```text
.
├── app
│   ├── api
│   │   ├── admin
│   │   ├── public
│   │   └── schemas
│   ├── application
│   │   ├── ports
│   │   └── services
│   ├── config
│   ├── domain
│   ├── infrastructure
│   │   ├── cache
│   │   ├── database
│   │   │   └── repositories
│   │   ├── locking
│   │   ├── providers
│   │   │   └── openai
│   │   └── storage
│   ├── observability
│   ├── scheduler
│   ├── security
│   ├── bootstrap.py
│   └── main.py
├── alembic
│   ├── env.py
│   └── versions
├── tests
│   ├── fakes
│   ├── integration
│   └── unit
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── alembic.ini
├── docker-compose.yml
├── Dockerfile.api
├── Dockerfile.worker
├── Makefile
├── nginx.conf
├── pyproject.toml
└── README.md
```

## Основные файлы

- `app/main.py` - FastAPI app factory
- `app/bootstrap.py` - shared wiring for API and worker
- `app/application/services/generation_service.py` - central generation orchestration
- `app/infrastructure/providers/openai/client.py` - OpenAI SDK wrapper with retries and timeouts
- `app/infrastructure/storage/s3_storage.py` - S3-compatible object storage adapter
- `app/infrastructure/database/models.py` - SQLAlchemy models
- `app/infrastructure/database/repositories/*.py` - repositories
- `app/scheduler/cli.py` - cron-friendly job runner
- `alembic/versions/20260315_0001_initial_schema.py` - initial database schema
- `docker-compose.yml` - local stack with PostgreSQL, Redis, MinIO, API, Nginx

## Локальный запуск

### 1. Подготовить env

```bash
cp .env.example .env
```

Заполните минимум:

- `OPENAI_API_KEY`
- `ADMIN_BEARER_TOKEN`
- при необходимости `S3_*`, `DATABASE_URL`, `REDIS_URL`

For storage URL behavior:

- `S3_ENDPOINT_URL` is used by the backend for internal uploads
- `S3_PUBLIC_ENDPOINT_URL` is used to build signed URLs for mobile clients
- `S3_PUBLIC_BASE_URL` should be set only if you intentionally expose public image URLs

### 2. Установить зависимости

```bash
uv sync --group dev
```

### 3. Поднять инфраструктуру

```bash
docker compose up -d postgres redis minio minio-init migrate
```

### 4. Выполнить миграции

```bash
uv run alembic upgrade head
```

### 5. Запустить API

```bash
uv run uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000
```

### 6. Проверить health

```bash
curl http://localhost:8000/api/v1/health
```

## Запуск через Docker Compose

### Полный stack

```bash
docker compose up --build
```

`migrate` runs automatically before `api` and `worker`.

Снаружи будет доступен Nginx на `http://localhost`.

### Миграции в Compose

```bash
docker compose run --rm migrate
```

## Hourly generation через cron на VPS

Рекомендуемый стартовый способ:

1. API и инфраструктура поднимаются через `docker compose up -d`.
2. Cron раз в час запускает одноразовый worker command.

Пример crontab:

```cron
0 * * * * cd /opt/pech-da-lozhka-backend && /usr/bin/docker compose run --rm worker uv run python -m app.scheduler.cli run-hourly-slot >> /var/log/pech-da-lozhka-worker.log 2>&1
```

Если удобнее запускать без Docker:

```cron
0 * * * * cd /opt/pech-da-lozhka-backend && /usr/local/bin/uv run python -m app.scheduler.cli run-hourly-slot >> /var/log/pech-da-lozhka-worker.log 2>&1
```

## Ручной запуск генерации

### Через HTTP admin endpoint

```bash
curl -X POST \
  http://localhost/api/v1/admin/generations/run-now \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Через CLI

```bash
uv run python -m app.scheduler.cli run-hourly-slot
```

Или для конкретного slot:

```bash
uv run python -m app.scheduler.cli run-slot --slot-time-utc "2026-03-15T12:00:00+00:00"
```

## REST API

### Public API

- `GET /api/v1/health`
- `GET /api/v1/recipes/latest`
- `GET /api/v1/recipes/feed`
- `GET /api/v1/recipes/{recipe_id}`

### Admin API

- `POST /api/v1/admin/generations/run-now`
- `GET /api/v1/admin/generations/{job_id}`
- `POST /api/v1/admin/recipes/{recipe_id}/publish`
- `POST /api/v1/admin/recipes/{recipe_id}/unpublish`

## Как мобильному приложению читать latest recipe

Простой flow:

```bash
curl http://localhost/api/v1/recipes/latest
```

Клиент получает:

- recipe metadata
- ingredients
- steps
- style tags
- image metadata
- image URL

Для списка карточек можно использовать:

```bash
curl "http://localhost/api/v1/recipes/feed?limit=20&offset=0"
```

## Quality gates

```bash
make format
make lint
make test
```

## Что уже сделано по безопасности

- OpenAI API key не попадает в mobile client
- секреты читаются из env
- `.env` игнорируется git
- есть `.env.example`
- admin auth через bearer token из env
- rate limiting для admin endpoints
- request id и correlation id middleware
- JSON structured logs
- CORS по явному allowlist
- non-root user в Docker image
- Nginx secure headers
- ограничение размера входящих запросов через `client_max_body_size`
- retry и timeout policy для OpenAI и storage
- идемпотентность и anti-duplicate защита для hourly jobs через Redis lock + PostgreSQL advisory lock + DB uniqueness
- hashed safety identifier для OpenAI requests
- private bucket by default for MinIO/S3
- signed URLs by default through `S3_PUBLIC_ENDPOINT_URL`

## Что стоит усилить позже

- заменить static admin bearer token на полноценную authn/authz систему
- добавить audit trail в отдельную таблицу, если потребуется compliance
- подключить OpenTelemetry / traces / metrics
- вынести background cleanup для orphaned storage objects
- добавить moderation pipeline, если recipes будут auto-publish в production
- добавить TLS termination и secret manager поверх `.env`
- добавить отдельный Redis/DB readiness monitoring на уровне инфраструктуры

## Тесты

В проекте уже есть:

- smoke test для health endpoint
- integration test для public latest recipe endpoint
- integration tests для admin generation / publish / public latest flow
- unit test на idempotency generation service
- unit test на compensating delete при DB failure
- unit tests для composite distributed locking
- unit tests для OpenAI provider adapters через fake wrapper

## Примечание по OpenAI

В коде выбран современный паттерн для новых проектов:

- text generation: `Responses API` + strict JSON schema output
- image generation: `Images API`

Это соответствует текущему официальному подходу OpenAI для новых text workflows и отдельной image generation интеграции.
