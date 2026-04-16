from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FrameworkSettingRecord:
    id: str
    framework_id: str
    setting_key: str
    setting_value: str
    created_at: str
    updated_at: str
