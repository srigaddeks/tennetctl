from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VersionRecord:
    id: str
    framework_id: str
    version_code: str
    change_severity: str
    lifecycle_state: str
    control_count: int
    previous_version_id: str | None
    is_active: bool
    created_at: str
    updated_at: str
    created_by: str | None
    # EAV properties
    version_label: str | None = None
    release_notes: str | None = None
    change_summary: str | None = None
