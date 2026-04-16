from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LicenseProfileSettingResponse(BaseModel):
    key: str
    value: str


class LicenseProfileResponse(BaseModel):
    id: str
    code: str
    name: str
    description: str
    tier: str  # free, pro, pro_trial, enterprise, partner, internal
    is_active: bool
    sort_order: int
    settings: list[LicenseProfileSettingResponse] = []
    org_count: int = 0
    created_at: datetime
    updated_at: datetime


class LicenseProfileListResponse(BaseModel):
    profiles: list[LicenseProfileResponse]


class CreateLicenseProfileRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    code: str = Field(min_length=2, max_length=50, pattern=r"^[a-z0-9_]+$")
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=500)
    tier: str = Field(default="free", pattern=r"^(free|pro|pro_trial|enterprise|partner|internal)$")
    sort_order: int = Field(default=100, ge=0)


class UpdateLicenseProfileRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    tier: str | None = Field(default=None, pattern=r"^(free|pro|pro_trial|enterprise|partner|internal)$")
    is_active: bool | None = None
    sort_order: int | None = Field(default=None, ge=0)


class SetProfileSettingRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    value: str = Field(min_length=1, max_length=2000)


class BatchSetProfileSettingsRequest(BaseModel):
    settings: dict[str, str]
