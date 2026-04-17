"""Pydantic schemas for monitoring.dashboards."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


PanelType = Literal["timeseries", "stat", "table", "log_stream", "trace_list"]


class GridPos(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: int = Field(default=0, ge=0, le=100)
    y: int = Field(default=0, ge=0, le=1000)
    w: int = Field(default=6, ge=1, le=24)
    h: int = Field(default=4, ge=1, le=100)


class PanelCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    panel_type: PanelType
    dsl: dict[str, Any]
    grid_pos: GridPos | None = None
    display_opts: dict[str, Any] | None = None


class PanelUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=200)
    panel_type: PanelType | None = None
    dsl: dict[str, Any] | None = None
    grid_pos: GridPos | None = None
    display_opts: dict[str, Any] | None = None


class PanelResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    dashboard_id: str
    title: str
    panel_type: PanelType
    dsl: dict[str, Any]
    grid_pos: dict[str, Any]
    display_opts: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "PanelResponse":
        import json as _json

        dsl = row.get("dsl")
        if isinstance(dsl, str):
            dsl = _json.loads(dsl)
        grid_pos = row.get("grid_pos")
        if isinstance(grid_pos, str):
            grid_pos = _json.loads(grid_pos)
        display_opts = row.get("display_opts")
        if isinstance(display_opts, str):
            display_opts = _json.loads(display_opts)
        return cls(
            id=row["id"],
            dashboard_id=row["dashboard_id"],
            title=row["title"],
            panel_type=row["panel_type"],  # type: ignore[arg-type]
            dsl=dsl or {},
            grid_pos=grid_pos or {"x": 0, "y": 0, "w": 6, "h": 4},
            display_opts=display_opts or {},
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class DashboardCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    layout: dict[str, Any] | None = None
    shared: bool = False


class DashboardUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    layout: dict[str, Any] | None = None
    shared: bool | None = None
    is_active: bool | None = None


class DashboardResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    org_id: str
    owner_user_id: str
    name: str
    description: str | None = None
    layout: dict[str, Any]
    shared: bool
    is_active: bool
    panel_count: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "DashboardResponse":
        import json as _json

        layout = row.get("layout")
        if isinstance(layout, str):
            layout = _json.loads(layout)
        return cls(
            id=row["id"],
            org_id=row["org_id"],
            owner_user_id=row["owner_user_id"],
            name=row["name"],
            description=row.get("description"),
            layout=layout or {},
            shared=bool(row["shared"]),
            is_active=bool(row["is_active"]),
            panel_count=int(row.get("panel_count") or 0),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class DashboardDetailResponse(DashboardResponse):
    panels: list[PanelResponse] = Field(default_factory=list)
