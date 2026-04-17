"""Pydantic schemas for monitoring.metrics — register + increment + set + observe."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MetricKind = Literal["counter", "gauge", "histogram"]


_KIND_TO_ID: dict[str, int] = {"counter": 1, "gauge": 2, "histogram": 3}
_ID_TO_KIND: dict[int, str] = {v: k for k, v in _KIND_TO_ID.items()}


def kind_to_id(kind: str) -> int:
    try:
        return _KIND_TO_ID[kind]
    except KeyError as e:
        raise ValueError(f"unknown metric kind {kind!r}") from e


def id_to_kind(kind_id: int) -> str:
    try:
        return _ID_TO_KIND[kind_id]
    except KeyError as e:
        raise ValueError(f"unknown kind_id {kind_id!r}") from e


class ResourceIdentity(BaseModel):
    """OTel resource identity — interned in fct_monitoring_resources."""

    model_config = ConfigDict(extra="forbid")

    service_name: str = Field(min_length=1)
    service_instance_id: str | None = None
    service_version: str | None = None
    attributes: dict[str, str] = Field(default_factory=dict)


class MetricRegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str = Field(min_length=1, pattern=r"^[a-z][a-z0-9_.]*$")
    kind: MetricKind
    label_keys: list[str] = Field(default_factory=list)
    description: str = ""
    unit: str = ""
    histogram_buckets: list[float] | None = None
    max_cardinality: int = Field(default=1000, ge=1, le=1_000_000)

    @field_validator("label_keys")
    @classmethod
    def _label_keys_unique_nonempty(cls, v: list[str]) -> list[str]:
        for lk in v:
            if not lk or not isinstance(lk, str):
                raise ValueError("label_keys entries must be non-empty strings")
        if len(set(v)) != len(v):
            raise ValueError("label_keys entries must be unique")
        return v

    @model_validator(mode="after")
    def _buckets_match_kind(self) -> "MetricRegisterRequest":
        if self.kind == "histogram":
            if not self.histogram_buckets:
                raise ValueError("histogram_buckets is required when kind='histogram'")
            if any(b <= 0 for b in self.histogram_buckets):
                raise ValueError("histogram_buckets must be strictly positive")
            if list(self.histogram_buckets) != sorted(self.histogram_buckets):
                raise ValueError("histogram_buckets must be sorted ascending")
        else:
            if self.histogram_buckets:
                raise ValueError(
                    f"histogram_buckets must be empty/null when kind='{self.kind}'"
                )
        return self


class MetricIncrementRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    labels: dict[str, str] = Field(default_factory=dict)
    value: float = 1.0
    resource: ResourceIdentity | None = None


class MetricSetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    labels: dict[str, str] = Field(default_factory=dict)
    value: float
    resource: ResourceIdentity | None = None


class MetricObserveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    labels: dict[str, str] = Field(default_factory=dict)
    value: float
    resource: ResourceIdentity | None = None


class MetricResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    org_id: str
    key: str
    kind: MetricKind
    label_keys: list[str] = Field(default_factory=list)
    histogram_buckets: list[float] | None = None
    description: str = ""
    unit: str = ""
    max_cardinality: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "MetricResponse":
        kind_code = row.get("kind_code") or id_to_kind(int(row["kind_id"]))
        return cls(
            id=int(row["id"]),
            org_id=row["org_id"],
            key=row["key"],
            kind=kind_code,  # type: ignore[arg-type]
            label_keys=list(row.get("label_keys") or []),
            histogram_buckets=(
                list(row["histogram_buckets"]) if row.get("histogram_buckets") else None
            ),
            description=row.get("description") or "",
            unit=row.get("unit") or "",
            max_cardinality=int(row["max_cardinality"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class IncrementResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric_id: int
    accepted: bool = True
