"""Helpers for privacy-preserving provider safety identifiers."""

from __future__ import annotations

from hashlib import sha256


def build_hashed_safety_identifier(*, namespace: str, raw_identifier: str) -> str:
    """Hash an internal identifier before sending it to external providers."""

    hash_payload = f"{namespace}:{raw_identifier}".encode("utf-8")
    return sha256(hash_payload).hexdigest()
