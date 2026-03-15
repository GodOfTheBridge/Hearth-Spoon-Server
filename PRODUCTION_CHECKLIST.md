# PRODUCTION_CHECKLIST.md

## Goal

This checklist is the minimum operational baseline before the first real VPS deployment of `ПечьДаЛожка` backend.

Use it as a release gate, not as optional reading.

---

## Must Be True Before Deploy

- `OPENAI_API_KEY` is real and restricted to the intended project.
- `ADMIN_IDENTITIES` or a legacy `ADMIN_BEARER_TOKEN` is configured with long random tokens stored outside git.
- PostgreSQL, Redis, and S3-compatible storage credentials are not local defaults.
- TLS termination is configured in front of the public API.
- The object storage bucket is private by default unless a deliberate public-CDN design is used.
- Only the intended public ingress is exposed externally; internal data services are not bound to public interfaces.
- Firewall rules expose only the intended public ports.
- Database backups are configured.
- Logs are persisted or shipped somewhere operators can inspect them.

---

## Mandatory Pre-Release Checks

Run these on the exact revision you plan to deploy:

1. Install dependencies.
   - `uv sync --group dev`
2. Run static checks.
   - `make lint`
3. Run tests.
   - `make test`
4. Verify migrations on a clean database.
   - `uv run alembic upgrade head`
5. Validate container configuration.
   - `docker compose config`
6. Start the stack.
   - `docker compose up --build -d`
7. Verify public liveness.
   - `curl http://localhost/api/v1/health`
8. Verify authenticated readiness.
   - `curl -H "Authorization: Bearer <ADMIN_TOKEN>" http://localhost/api/v1/admin/health/readiness`
9. Trigger one manual generation.
   - `POST /api/v1/admin/generations/run-now`
10. Poll the job until completion.
   - `GET /api/v1/admin/generations/{job_id}`
11. Publish the generated recipe.
   - `POST /api/v1/admin/recipes/{recipe_id}/publish`
12. Verify public recipe delivery.
   - `GET /api/v1/recipes/latest`
13. Verify hourly worker command manually.
   - `uv run python -m app.scheduler.cli run-hourly-slot`

Do not ship if any of these are skipped without an explicit risk decision.

---

## VPS Rollout Sequence

1. Prepare the host.
   - create a dedicated app user
   - install Docker and Docker Compose plugin
   - configure reverse proxy or TLS termination
   - configure log rotation
2. Put the project on disk.
   - example path: `/opt/pech-da-lozhka-backend`
3. Create production `.env`.
   - use real credentials
   - do not keep development defaults
4. Run migrations before switching traffic.
   - `docker compose run --rm migrate`
5. Start the application stack.
   - `docker compose up -d api nginx postgres redis minio minio-init`
6. Verify health and readiness.
7. Run a single manual generation smoke.
8. Add cron for the hourly worker only after the manual smoke succeeds.

---

## Cron Baseline

Recommended production baseline:

```cron
0 * * * * cd /opt/pech-da-lozhka-backend && /usr/bin/docker compose run --rm worker uv run python -m app.scheduler.cli run-hourly-slot >> /var/log/pech-da-lozhka-worker.log 2>&1
```

This hourly worker path is the primary durable generation path.

`POST /api/v1/admin/generations/run-now` is an operator convenience endpoint and should not replace the scheduled worker for core production generation.

---

## What To Watch First

During the first deployment, monitor these failure points first:

- migration failures
- storage bucket access
- Redis availability for locks and admin rate limiting
- stale or repeatedly failing generation jobs
- provider timeouts and retry exhaustion
- signed image URL generation

---

## Still Second-Stage Hardening

These are valid production improvements, but not blockers for a starter release if the checklist above is fully completed:

- replace static admin bearer token with real authn/authz
- move secrets to a secret manager
- add metrics and tracing
- add durable background dispatch for manual admin `run-now`
- add centralized alerting
- add orphaned object cleanup job
- add moderation workflow before any future auto-publish rollout
