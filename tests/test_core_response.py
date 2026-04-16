"""Tests for backend.01_core.response."""

from __future__ import annotations

from importlib import import_module

from fastapi.responses import JSONResponse

_resp = import_module("backend.01_core.response")


def test_success_envelope():
    """success() returns correct envelope."""
    result = _resp.success({"key": "val"})
    assert result == {"ok": True, "data": {"key": "val"}}


def test_success_with_list():
    """success() works with list data."""
    result = _resp.success([1, 2, 3])
    assert result == {"ok": True, "data": [1, 2, 3]}


def test_error_envelope():
    """error() returns correct envelope."""
    result = _resp.error("NOT_FOUND", "gone")
    assert result == {"ok": False, "error": {"code": "NOT_FOUND", "message": "gone"}}


def test_paginated_envelope():
    """paginated() includes data and pagination metadata."""
    result = _resp.paginated([1, 2], total=10, limit=2, offset=0)
    assert result["ok"] is True
    assert result["data"] == [1, 2]
    assert result["pagination"] == {"total": 10, "limit": 2, "offset": 0}


def test_success_response_is_json_response():
    """success_response() returns a JSONResponse."""
    result = _resp.success_response({"test": True})
    assert isinstance(result, JSONResponse)
    assert result.status_code == 200


def test_error_response_is_json_response():
    """error_response() returns a JSONResponse with correct status."""
    result = _resp.error_response("BAD", "wrong", 400)
    assert isinstance(result, JSONResponse)
    assert result.status_code == 400


def test_success_response_custom_status():
    """success_response() accepts custom status code."""
    result = _resp.success_response({"created": True}, status_code=201)
    assert result.status_code == 201
