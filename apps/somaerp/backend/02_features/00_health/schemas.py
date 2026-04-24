"""Health response schema."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TennetctlProxyStatus(BaseModel):
    ok: bool
    base_url: str
    latency_ms: float
    last_error: str | None = None


class HealthResponse(BaseModel):
    somaerp_version: str
    somaerp_uptime_s: float
    tennetctl_proxy: TennetctlProxyStatus = Field(...)
