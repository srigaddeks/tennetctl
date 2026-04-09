"""kbio devices schemas.

Pydantic v2 models for the device registry sub-feature.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class DeviceData(BaseModel):
    """Single device record as returned by the API."""

    id: str
    device_uuid: str
    trusted: bool = False
    platform: Optional[str] = None
    first_seen_at: Optional[str] = None
    last_seen_at: Optional[str] = None
    session_count: int = 0
    fingerprint_match_score: float = 0.0
    automation_risk: float = 0.0


class DeviceListData(BaseModel):
    """Paginated list of device records."""

    items: list[DeviceData]
    total: int
    limit: int
    offset: int


class PatchDeviceRequest(BaseModel):
    """Request body for updating device trust status."""

    trusted: bool = Field(..., description="New trust status for the device")
    reason: str = Field(..., description="Human-readable reason for the change")
