"""Cron-friendly job runner CLI."""

from __future__ import annotations

import argparse
from datetime import datetime

import structlog

from app.application.exceptions import IdempotencyConflictError, RetryExhaustedError
from app.bootstrap import build_application_container
from app.config.settings import get_settings
from app.observability.logging import configure_logging

logger = structlog.get_logger(__name__)


def build_argument_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""

    parser = argparse.ArgumentParser(description="ПечьДаЛожка background generation worker")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("run-hourly-slot", help="Generate a recipe for the current UTC hour slot")

    run_slot_parser = subparsers.add_parser("run-slot", help="Generate a recipe for a specific UTC slot")
    run_slot_parser.add_argument(
        "--slot-time-utc",
        required=True,
        help="Timezone-aware ISO 8601 datetime for the slot",
    )

    return parser


def _parse_slot_time(slot_time_utc: str) -> datetime:
    parsed_datetime = datetime.fromisoformat(slot_time_utc)
    if parsed_datetime.tzinfo is None:
        raise ValueError("The provided slot time must be timezone-aware.")
    return parsed_datetime


def main(argv: list[str] | None = None) -> int:
    """Run the worker CLI."""

    settings = get_settings()
    configure_logging(settings)
    parser = build_argument_parser()
    arguments = parser.parse_args(argv)
    container = build_application_container(settings)

    try:
        generation_service = container.build_generation_service()
        if arguments.command == "run-hourly-slot":
            result = generation_service.run_hourly_generation(requested_by="cron")
        else:
            slot_time_utc = _parse_slot_time(arguments.slot_time_utc)
            result = generation_service.run_for_slot(
                slot_time_utc=slot_time_utc,
                requested_by="manual-cli",
            )

        logger.info(
            "scheduler.job.completed",
            job_id=str(result.job.id),
            was_created=result.was_created,
            recipe_id=str(result.recipe.id) if result.recipe else None,
        )
        return 0
    except IdempotencyConflictError as error:
        logger.info("scheduler.job.skipped", reason=str(error))
        return 0
    except RetryExhaustedError as error:
        logger.error("scheduler.job.retry_exhausted", reason=str(error))
        return 1
    except Exception as error:  # noqa: BLE001
        logger.exception("scheduler.job.failed", error_type=type(error).__name__)
        return 1
    finally:
        container.close()


if __name__ == "__main__":
    raise SystemExit(main())
