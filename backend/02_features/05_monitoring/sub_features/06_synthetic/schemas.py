"""Pydantic schemas for monitoring.synthetic."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


HttpMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"]


class SyntheticCheckCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    target_url: str = Field(min_length=1, max_length=2048)
    method: HttpMethod = "GET"
    expected_status: int = Field(default=200, ge=100, le=599)
    timeout_ms: int = Field(default=5000, ge=100, le=60000)
    interval_seconds: int = Field(default=60, ge=30, le=3600)
    headers: dict[str, str] = Field(default_factory=dict)
    body: str | None = None
    assertions: list[dict[str, Any]] = Field(default_factory=list)


class SyntheticCheckUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=200)
    target_url: str | None = Field(default=None, min_length=1, max_length=2048)
    method: HttpMethod | None = None
    expected_status: int | None = Field(default=None, ge=100, le=599)
    timeout_ms: int | None = Field(default=None, ge=100, le=60000)
    interval_seconds: int | None = Field(default=None, ge=30, le=3600)
    headers: dict[str, str] | None = None
    body: str | None = None
    assertions: list[dict[str, Any]] | None = None
    is_active: bool | None = None


class SyntheticCheckResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    org_id: str
    name: str
    target_url: str
    method: str
    expected_status: int
    timeout_ms: int
    interval_seconds: int
    headers: dict[str, Any]
    body: str | None = None
    assertions: list[dict[str, Any]]
    is_active: bool
    consecutive_failures: int | None = 0
    last_ok_at: datetime | None = None
    last_fail_at: datetime | None = None
    last_run_at: datetime | None = None
    last_status_code: int | None = None
    last_duration_ms: int | None = None
    last_error: str | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "SyntheticCheckResponse":
        import json as _json
        headers = row.get("headers") or {}
        if isinstance(headers, str):
            headers = _json.loads(headers)
        assertions = row.get("assertions") or []
        if isinstance(assertions, str):
            assertions = _json.loads(assertions)
        return cls(
            id=row["id"],
            org_id=row["org_id"],
            name=row["name"],
            target_url=row["target_url"],
            method=row["method"],
            expected_status=row["expected_status"],
            timeout_ms=row["timeout_ms"],
            interval_seconds=row["interval_seconds"],
            headers=headers,
            body=row.get("body"),
            assertions=assertions,
            is_active=row["is_active"],
            consecutive_failures=row.get("consecutive_failures") or 0,
            last_ok_at=row.get("last_ok_at"),
            last_fail_at=row.get("last_fail_at"),
            last_run_at=row.get("last_run_at"),
            last_status_code=row.get("last_status_code"),
            last_duration_ms=row.get("last_duration_ms"),
            last_error=row.get("last_error"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
