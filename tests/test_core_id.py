"""Tests for backend.01_core.id."""

from __future__ import annotations

import uuid
from importlib import import_module

_id = import_module("backend.01_core.id")


def test_uuid7_returns_string():
    """uuid7() returns a string."""
    result = _id.uuid7()
    assert isinstance(result, str)


def test_uuid7_valid_format():
    """uuid7() returns a valid UUID string (36 chars, parseable)."""
    result = _id.uuid7()
    assert len(result) == 36
    parsed = uuid.UUID(result)
    assert str(parsed) == result


def test_uuid7_is_version_7():
    """uuid7() returns UUID version 7."""
    result = _id.uuid7()
    parsed = uuid.UUID(result)
    assert parsed.version == 7


def test_uuid7_unique():
    """Multiple uuid7() calls return unique values."""
    ids = {_id.uuid7() for _ in range(100)}
    assert len(ids) == 100
