"""Tests for backend.01_core.errors."""

from __future__ import annotations

from importlib import import_module

_errors = import_module("backend.01_core.errors")


def test_app_error_has_fields():
    """AppError carries code, message, status_code."""
    err = _errors.AppError("TEST", "test message", 418)
    assert err.code == "TEST"
    assert err.message == "test message"
    assert err.status_code == 418
    assert str(err) == "test message"


def test_not_found_error():
    """NotFoundError defaults to 404."""
    err = _errors.NotFoundError("not here")
    assert err.status_code == 404
    assert err.code == "NOT_FOUND"


def test_validation_error():
    """ValidationError defaults to 422."""
    err = _errors.ValidationError("bad input")
    assert err.status_code == 422
    assert err.code == "VALIDATION_ERROR"


def test_conflict_error():
    """ConflictError defaults to 409."""
    err = _errors.ConflictError("already exists")
    assert err.status_code == 409
    assert err.code == "CONFLICT"


def test_forbidden_error():
    """ForbiddenError defaults to 403."""
    err = _errors.ForbiddenError("nope")
    assert err.status_code == 403
    assert err.code == "FORBIDDEN"


def test_unauthorized_error():
    """UnauthorizedError defaults to 401."""
    err = _errors.UnauthorizedError("login required")
    assert err.status_code == 401
    assert err.code == "UNAUTHORIZED"


def test_custom_code_override():
    """Subclass accepts custom code."""
    err = _errors.NotFoundError("gone", code="RESOURCE_GONE")
    assert err.code == "RESOURCE_GONE"
    assert err.status_code == 404


def test_app_error_is_exception():
    """AppError is an Exception subclass."""
    assert issubclass(_errors.AppError, Exception)
    assert issubclass(_errors.NotFoundError, _errors.AppError)
