"""Shared schemas for the generic entity settings API."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class SettingResponse(BaseModel):
    key: str
    value: str


class SettingListResponse(BaseModel):
    settings: list[SettingResponse]


class SetSettingRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    value: Annotated[str, Field(min_length=1, max_length=2000)]


class BatchSetSettingsRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    settings: dict[str, Annotated[str, Field(min_length=1, max_length=2000)]]


class BatchSetSettingsResponse(BaseModel):
    settings: list[SettingResponse]


class SettingKeyResponse(BaseModel):
    code: str
    name: str
    description: str
    data_type: str
    is_pii: bool
    is_required: bool
    sort_order: int


class SettingKeyListResponse(BaseModel):
    keys: list[SettingKeyResponse]
