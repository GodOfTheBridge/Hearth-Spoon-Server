# AGENTS.md

## Scope

These instructions apply to the entire repository unless a deeper `AGENTS.md` overrides them for a specific subtree.

When multiple `AGENTS.md` files apply, use the most specific one for the files you touch.

---

## Start Here

Before making structural or production-sensitive changes, read:

1. `README.md`
2. `ARCHITECTURE.md`
3. the relevant runtime files for the task:
   - `pyproject.toml`
   - `docker-compose.yml`
   - `nginx.conf`
   - `alembic.ini`
   - `alembic/env.py`
4. the relevant tests under `tests/`

Do not introduce changes that contradict `ARCHITECTURE.md` unless you update the architecture doc in the same change.

---

## Repository Purpose

`ПечьДаЛожка` backend is the trusted server-side boundary for:

- scheduled AI recipe generation;
- AI image generation for recipes;
- storage of recipe content, image metadata, and job state;
- REST API delivery for mobile clients;
- admin operations for generation and publication.

Never move provider calls, secrets, or privileged logic into the mobile client.

---

## Repository Map

- `app/api` — FastAPI routes, request/response schemas, dependency wiring, error mapping
- `app/application` — use cases, orchestration services, ports
- `app/domain` — domain entities, enums, constants, schema definitions
- `app/infrastructure` — SQLAlchemy repositories, OpenAI adapters, locking, Redis, storage
- `app/security` — admin auth, rate limiting, safety helpers
- `app/observability` — logging, request context, correlation metadata
- `app/scheduler` — cron-friendly CLI entrypoints
- `alembic` — database migrations
- `tests` — unit and integration coverage

---

## Architecture Rules

Keep these boundaries intact:

1. Route handlers stay thin.
   They may do HTTP translation, auth, dependency resolution, and response shaping.
2. Business workflows live in application services.
3. Domain models stay free of FastAPI, SQLAlchemy session handling, Redis clients, and SDK details.
4. Infrastructure code implements ports and adapters; it does not own business rules.
5. Scheduled and manual generation flows must reuse the same orchestration path.
6. Provider output is untrusted until it passes provider-side structured output constraints and backend validation.
7. Generated images belong in object storage, not as database blobs.
8. Public API must never expose unpublished or incomplete content as ready content.

Do not call OpenAI SDKs, S3 clients, or repository persistence logic directly from route handlers.

---

## Production Invariants

These are non-negotiable unless the architecture is intentionally changed:

- hourly generation must remain idempotent;
- duplicate execution for the same slot must remain blocked;
- duplicate protection must stay storage-backed, not process-local;
- current duplicate protection relies on Redis lock, PostgreSQL advisory lock, and database uniqueness;
- external API calls must keep timeouts, retries, and error mapping;
- partial failures must be persisted and logged clearly;
- OpenAI keys and admin secrets must remain server-side only;
- object storage defaults should remain private unless a change explicitly documents a public exposure model.

If you touch generation or scheduling code, verify these invariants explicitly.

---

## Persistence and Migration Rules

When changing persistence:

- keep SQLAlchemy models, repositories, and Alembic migrations aligned;
- keep uniqueness constraints and indexes in sync with idempotency rules;
- prefer additive migrations unless a breaking change is intentional;
- update tests when schema changes affect behavior;
- check both application startup and migration flow.

Do not leave models and migrations out of sync.

---

## Security Rules

Never:

- commit secrets;
- hardcode credentials or tokens;
- log raw secrets, API keys, bearer tokens, or privileged headers;
- weaken admin auth, CORS, rate limiting, or storage access silently;
- expose provider-internal payloads to public clients without a clear reason.

Always:

- load secrets from environment variables;
- keep `.env.example` placeholder-only;
- preserve startup validation for critical configuration;
- prefer explicit allowlists over permissive defaults;
- review security impact when changing auth, CORS, rate limiting, storage, logging, or external providers.

---

## Code Style Rules

Prefer code that is explicit, typed, and easy to trace.

- Use clear, descriptive names.
- Keep functions focused.
- Add docstrings to important public classes and methods.
- Handle external-boundary errors deliberately.
- Reuse existing patterns before introducing new abstractions.

Avoid:

- vague names such as `util`, `helper`, `manager`, `data`, `result`, or `tmp` for long-lived concepts;
- giant mixed-responsibility files;
- broad catch-all exceptions without context;
- duplicate logic between API, worker, and admin flows;
- abstraction layers that do not reduce real complexity.

---

## Verification Checklist

Run the relevant checks for the area you changed:

- `uv sync --group dev`
- `make lint`
- `make test`
- `uv run alembic upgrade head`
- `docker compose config`
- `uv run python -m app.scheduler.cli --help`

If you touch scheduler, generation, persistence, Docker, or config, prefer running the most relevant command instead of assuming it works.

If a command cannot be run, say so clearly and describe what remains unverified.

---

## Documentation Rules

Update documentation when your change affects:

- architecture or layer boundaries;
- environment variables;
- migration flow;
- scheduling behavior;
- API contracts;
- deployment flow;
- security assumptions.

Write repository documentation, operator instructions, and OpenAPI/Swagger descriptions in Russian by default.
Use English only when an external contract, third-party interface, or required identifier explicitly needs it.

At minimum, consider whether `README.md` and `ARCHITECTURE.md` need updates.

---

## Final Reminder

This is not a generic CRUD service.

The repository contains scheduled generation, external AI providers, storage, locking, and production-sensitive invariants.

Optimize for correctness, operational safety, and maintainability over cleverness.
