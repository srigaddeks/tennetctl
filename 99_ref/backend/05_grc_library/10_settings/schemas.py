from __future__ import annotations

from pydantic import BaseModel, Field


class SetFrameworkSettingRequest(BaseModel):
    setting_value: str = Field(..., min_length=1)


class FrameworkSettingResponse(BaseModel):
    id: str
    framework_id: str
    setting_key: str
    setting_value: str
    created_at: str
    updated_at: str


class FrameworkSettingListResponse(BaseModel):
    items: list[FrameworkSettingResponse]
    total: int
