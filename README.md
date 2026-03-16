# ПечьДаЛожка Backend

Production-ready starter backend for the mobile application `ПечьДаЛожка`.

Release gate and VPS rollout checklist: `PRODUCTION_CHECKLIST.md`

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
   - recovery stale `RUNNING` jobs, если процесс умер после старта генерации
5. Согласованность реализована прагматично:
   - сначала создается и фиксируется job
   - затем выполняются внешние вызовы
   - затем в одной DB transaction сохраняются recipe + image metadata + statuses
   - если upload уже был, а DB commit упал, выполняется compensating delete в storage
6. Секреты читаются только из env; `.env` не коммитится, есть `.env.example`.
7. Public API отдает только опубликованные рецепты; автоматическую публикацию можно включить env-флагом `AUTO_PUBLISH_GENERATED_RECIPES=true` только в `development`, `staging` или `test`.

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
├── api-client
│   └── bruno
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
- `api-client/bruno` - Bruno collection and environments for local/admin API checks
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
- `ADMIN_IDENTITIES` или legacy `ADMIN_BEARER_TOKEN`
- при необходимости `S3_*`, `DATABASE_URL`, `REDIS_URL`

For local development with Swagger/ReDoc enabled, explicitly set `APP_ENVIRONMENT=development`.

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

Detailed dependency readiness:

```bash
curl -H "Authorization: Bearer YOUR_ADMIN_TOKEN" http://localhost:8000/api/v1/admin/health/readiness
```

### 7. Открыть Swagger, ReDoc и OpenAPI

Swagger UI, ReDoc и `openapi.json` доступны, когда приложение запущено с `APP_ENVIRONMENT=development`
или `APP_DEBUG=true`.

При локальном запуске через `uvicorn` используйте:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

При запуске через `docker compose up --build` те же URL будут доступны через Nginx:

- Swagger UI: `http://localhost/docs`
- ReDoc: `http://localhost/redoc`
- OpenAPI JSON: `http://localhost/openapi.json`

### 8. Использовать Bearer token в Swagger

1. Откройте `/docs`.
2. Нажмите `Authorize`.
3. Вставьте только значение admin token без префикса `Bearer`.
4. Нажмите `Authorize`, затем `Close`.
5. Выполните любой endpoint из групп `admin` или `generation` через `Try it out`.

Swagger UI сам отправит заголовок `Authorization: Bearer <token>`.
Сохранение Bearer token в браузере включено только для `APP_ENVIRONMENT=development`; если docs открыты
через один лишь `APP_DEBUG=true`, `persistAuthorization` остается выключенным.

### 9. Проверить API локально через Bruno

Коллекция лежит в `api-client/bruno`.

Подготовить секреты для Bruno:

```bash
cp api-client/bruno/.env.sample api-client/bruno/.env
```

Заполните `BRUNO_ADMIN_TOKEN` в `api-client/bruno/.env`, затем:

1. Откройте папку `api-client/bruno` в Bruno desktop app.
2. Выберите environment `local` для прямого `uvicorn`-запуска на `http://localhost:8000`.
3. Выберите environment `docker` для `docker compose`-стека за Nginx на `http://localhost`.
4. Используйте `production-template` как шаблон для реального домена без коммита секретов.
5. После `Run Generation Now` скопируйте возвращенный `job.id` в `generationJobId` и используйте
   запрос `Get Generation Job` для poll async-статуса.

CLI-запуск из корня коллекции:

```bash
cd api-client/bruno
bru run --env-file ./environments/local.bru
```

Для Docker-стека:

```bash
cd api-client/bruno
bru run --env-file ./environments/docker.bru
```

## Запуск через Docker Compose

### Default API stack

```bash
docker compose up --build
```

This starts the default HTTP stack: `postgres`, `redis`, `minio`, `minio-init`, `migrate`, `api`, and `nginx`.
The `worker` service is intentionally profile-gated and is not started by default.

Снаружи будет доступен Nginx на `http://localhost`.
MinIO S3 access is bound to loopback by default via `127.0.0.1:9000` for safer local development.

### Worker profile in Compose

```bash
docker compose --profile worker up --build worker
```

For production hourly generation, prefer cron plus `docker compose run --rm worker ...` rather than a long-lived worker container.

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

Endpoint now returns `202 Accepted`, creates or reuses a job for the target slot, and attempts best-effort in-process background execution on the current API instance. Poll the job via `GET /api/v1/admin/generations/{job_id}`.
For the durable production path, prefer the hourly worker CLI under cron.

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
- `GET /api/v1/admin/health/readiness`
- `POST /api/v1/admin/recipes/{recipe_id}/publish`
- `POST /api/v1/admin/recipes/{recipe_id}/unpublish`

OpenAPI metadata is configured with explicit `public`, `admin`, `generation`, and `health` tags.
Admin endpoints expose Bearer auth in Swagger UI through the `AdminBearerAuth` security scheme.

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
- client-safe image metadata
- image URL

Public API intentionally does not expose storage keys, provider metadata, moderation status, or internal generation parameters.

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
- admin auth поддерживает несколько операторских bearer tokens с ролями `read` / `write`; legacy single token оставлен только как bootstrap fallback
- rate limiting для admin endpoints
- request id и correlation id middleware
- JSON structured logs
- CORS по явному allowlist
- non-root user в Docker image
- Nginx secure headers
- ограничение размера входящих запросов через `client_max_body_size`
- retry и timeout policy для OpenAI и storage
- идемпотентность и anti-duplicate защита для hourly jobs через Redis lock + PostgreSQL advisory lock + DB uniqueness
- stale `RUNNING` job recovery после process crash
- hashed safety identifier для OpenAI requests
- private bucket by default for MinIO/S3
- signed URLs by default through `S3_PUBLIC_ENDPOINT_URL`
- public `/health` не раскрывает внутреннюю карту зависимостей; подробная readiness доступна только через admin endpoint

## Что стоит усилить позже

- заменить env-based admin tokens на полноценную authn/authz систему с revocation и внешним identity provider
- добавить audit trail в отдельную таблицу, если потребуется compliance
- подключить OpenTelemetry / traces / metrics
- вынести background cleanup для orphaned storage objects
- добавить moderation pipeline, если recipes будут auto-publish в production
- добавить TLS termination и secret manager поверх `.env`
- добавить отдельный Redis/DB readiness monitoring на уровне инфраструктуры

## Production checklist

Перед первым реальным релизом пройдите `PRODUCTION_CHECKLIST.md`.

## Тесты

В проекте уже есть:

- smoke test для health endpoint
- integration test для public latest recipe endpoint
- integration tests для admin generation / publish / public latest flow
- unit test на idempotency generation service
- unit test на compensating delete при DB failure
- unit test на recovery stale `RUNNING` jobs
- unit tests для composite distributed locking
- unit tests для OpenAI provider adapters через fake wrapper

## Примечание по OpenAI

В коде выбран современный паттерн для новых проектов:

- text generation: `Responses API` + strict JSON schema output
- image generation: `Images API`

Это соответствует текущему официальному подходу OpenAI для новых text workflows и отдельной image generation интеграции.
