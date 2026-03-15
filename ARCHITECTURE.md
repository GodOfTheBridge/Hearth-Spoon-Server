# ARCHITECTURE.md

## Purpose

`ПечьДаЛожка` backend is a server-side system that generates AI recipes and dish images on a schedule, persists the resulting content and generation state, and exposes published content through REST API.

The backend is the trust boundary between mobile clients and external providers. Provider credentials, generation rules, moderation/publication decisions, and background execution stay on the server.

---

## Architectural Style

The project uses a layered architecture with explicit boundaries:

1. `presentation layer`
   - FastAPI routes
   - HTTP schemas
   - dependency injection
   - auth and request-level concerns
2. `application layer`
   - orchestration services
   - use cases
   - repository/provider/storage/locking ports
3. `domain layer`
   - entities
   - enums
   - constants
   - recipe schema and domain rules
4. `infrastructure layer`
   - SQLAlchemy persistence
   - OpenAI adapters
   - Redis and PostgreSQL locking
   - S3-compatible object storage
   - operational integrations

Allowed dependency direction:

- `api -> application -> domain`
- `infrastructure -> application/domain`

The domain layer must not depend on FastAPI, SQLAlchemy sessions, Redis clients, or OpenAI SDK objects.

---

## Runtime Components

### API application

- entrypoint: `app.main:create_app`
- responsibilities:
  - public API
  - admin API
  - dependency wiring
  - request context and logging
  - auth and rate limiting

### Scheduler / worker

- entrypoint: `python -m app.scheduler.cli run-hourly-slot`
- responsibilities:
  - invoke the same generation orchestration used by manual admin generation
  - run safely under cron
  - avoid embedding scheduling inside web workers

### Shared container

- file: `app/bootstrap.py`
- responsibilities:
  - instantiate settings
  - create DB engine and session factory
  - create Redis client
  - create object storage adapter
  - wire distributed locking
  - wire OpenAI providers
  - build services used by API and worker

---

## Main Generation Flow

The core workflow lives in `app/application/services/generation_service.py`.

High-level flow:

1. Normalize the target UTC hour slot.
2. Build an idempotency key for that slot.
3. Acquire distributed duplicate protection.
   - Redis lock
   - PostgreSQL advisory lock in PostgreSQL deployments
4. Create or load the schedule slot.
5. Create or load the generation job.
6. If the slot is already completed, return the existing result.
7. Build recipe prompts and call text generation provider.
8. Validate structured recipe output before continuing.
9. Build the image prompt and call image generation provider.
10. Upload the generated image to object storage.
11. Persist recipe, image metadata, job state, and slot state.
12. If persistence fails after upload, delete the orphaned object from storage.
13. Return a stable application result for API or CLI consumers.

Manual admin generation and scheduled generation must continue to use this same workflow.

---

## Idempotency and Anti-Duplicate Strategy

Hourly generation is production-sensitive. Duplicate content for the same hour slot is considered a correctness failure.

Current protection layers:

1. Redis distributed lock for fast coarse-grained contention control
2. PostgreSQL advisory lock for DB-backed coordination in PostgreSQL deployments
3. unique slot constraint in PostgreSQL
4. unique job idempotency key in PostgreSQL
5. repository-level duplicate handling for race conditions

Important rule:

- do not replace these protections with in-memory flags or per-process state

If locking strategy changes, update this document and the related tests.

---

## Validation Strategy

Provider output is treated as untrusted.

Validation layers:

1. provider-side structured output constraints
2. backend schema validation with Pydantic
3. application/domain validation through typed commands and entities

Schema-valid JSON is not automatically business-valid. Application services remain responsible for workflow-level correctness.

---

## Persistence Model

Core persisted concepts:

- `GenerationScheduleSlot`
- `GenerationJob`
- `Recipe`
- `RecipeImage`

Relational storage responsibilities:

- canonical recipe content
- image metadata and storage references
- job state
- provider metadata needed for debugging or auditing
- publication state

Object storage responsibilities:

- generated image bytes

The database stores metadata and references, not image blobs.

---

## Consistency Model

The project intentionally uses a pragmatic consistency model rather than a heavy outbox design in the starter baseline.

Current approach:

- create and persist job state first;
- perform external generation and storage actions next;
- persist recipe, image metadata, and final job state in the database;
- if storage upload succeeded but DB persistence failed, perform compensating delete for the uploaded object.

This approach is acceptable for the current system shape because generation is slot-based, idempotent, and externally observable through persisted job state.

If the system later adds fan-out side effects, downstream event consumers, or multi-step publication pipelines, reevaluate this design.

---

## Security and Operational Boundaries

The following assumptions are part of the architecture:

- OpenAI API keys never reach the mobile client
- admin access is protected by bearer token auth and rate limiting
- secrets come from environment variables
- request and job correlation metadata are logged in structured form
- storage defaults are private-by-default
- public API exposes only published recipes
- incomplete or failed generation must not appear as ready public content

If auth, storage exposure, or public visibility rules change, update this file and `README.md`.

---

## Change Guidance

### When changing API

- keep route handlers thin
- do not move business logic into FastAPI endpoints
- keep public DTOs stable and client-safe

### When changing generation logic

- preserve idempotency
- preserve shared orchestration between admin and scheduler flows
- preserve clear failure state persistence

### When changing persistence

- align models, repositories, and Alembic migrations
- review indexes and uniqueness constraints

### When changing provider integrations

- preserve timeouts, retries, and error mapping
- keep provider SDK code inside infrastructure adapters
- avoid leaking provider-specific shapes into domain or public API

### When changing deployment files

- keep Docker, Compose, env docs, and runtime assumptions in sync
- validate `docker-compose.yml` and related commands where possible

---

## Required Documentation Updates

Update `README.md` and this file whenever a change affects:

- entrypoints
- environment variables
- deployment flow
- scheduling model
- locking strategy
- persistence invariants
- security assumptions
