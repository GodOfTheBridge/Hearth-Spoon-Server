"""Unit tests for the scheduler CLI entrypoint."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from app.scheduler import cli


class FakeContainer:
    """Minimal fake container for scheduler CLI tests."""

    def __init__(self, *, generation_service) -> None:
        self._generation_service = generation_service
        self.was_closed = False

    def build_generation_service(self):
        return self._generation_service

    def close(self) -> None:
        self.was_closed = True


class FakeGenerationService:
    """Minimal fake generation service for scheduler CLI tests."""

    def __init__(self) -> None:
        self.hourly_call_count = 0
        self.slot_call_count = 0

    def run_hourly_generation(self, *, requested_by: str):
        return self._build_result(requested_by=requested_by, is_hourly=True)

    def run_for_slot(self, *, slot_time_utc, requested_by: str):
        _ = slot_time_utc
        return self._build_result(requested_by=requested_by, is_hourly=False)

    def _build_result(self, *, requested_by: str, is_hourly: bool):
        if is_hourly:
            self.hourly_call_count += 1
        else:
            self.slot_call_count += 1
        return SimpleNamespace(
            job=SimpleNamespace(id=uuid4()),
            was_created=True,
            recipe=SimpleNamespace(id=uuid4()),
            requested_by=requested_by,
        )


def test_scheduler_cli_runs_hourly_slot(monkeypatch) -> None:
    """The CLI should execute the hourly slot command successfully."""

    fake_generation_service = FakeGenerationService()
    fake_container = FakeContainer(generation_service=fake_generation_service)

    monkeypatch.setattr(cli, "get_settings", lambda: object())
    monkeypatch.setattr(cli, "configure_logging", lambda settings: None)
    monkeypatch.setattr(cli, "build_application_container", lambda settings: fake_container)

    exit_code = cli.main(["run-hourly-slot"])

    assert exit_code == 0
    assert fake_generation_service.hourly_call_count == 1
    assert fake_container.was_closed is True


def test_scheduler_cli_rejects_naive_slot_datetime(monkeypatch) -> None:
    """The CLI should fail fast for a naive slot datetime."""

    fake_generation_service = FakeGenerationService()
    fake_container = FakeContainer(generation_service=fake_generation_service)

    monkeypatch.setattr(cli, "get_settings", lambda: object())
    monkeypatch.setattr(cli, "configure_logging", lambda settings: None)
    monkeypatch.setattr(cli, "build_application_container", lambda settings: fake_container)

    exit_code = cli.main(["run-slot", "--slot-time-utc", "2026-03-15T12:00:00"])

    assert exit_code == 1
    assert fake_generation_service.slot_call_count == 0
    assert fake_container.was_closed is True
