"""Pydantic schemas for monitoring.alerts (13-08a)."""

from __future__ import annotations

import json as _json
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


AlertSeverity = Literal["info", "warn", "error", "critical"]
AlertTarget = Literal["metrics", "logs"]
ConditionOp = Literal["gt", "gte", "lt", "lte", "eq", "ne"]
AlertState = Literal["firing", "resolved"]


class AlertCondition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    op: ConditionOp
    threshold: float
    for_duration_seconds: int = Field(default=0, ge=0, le=86400)


class AlertRuleCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    target: AlertTarget
    dsl: dict[str, Any]
    condition: AlertCondition
    severity: AlertSeverity
    notify_template_key: str = Field(min_length=1, max_length=200)
    labels: dict[str, str] = Field(default_factory=dict)


class AlertRuleUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    dsl: dict[str, Any] | None = None
    condition: AlertCondition | None = None
    severity: AlertSeverity | None = None
    notify_template_key: str | None = Field(default=None, min_length=1, max_length=200)
    labels: dict[str, str] | None = None
    is_active: bool | None = None
    paused_until: datetime | None = None
    clear_paused_until: bool | None = None


class AlertRulePauseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paused_until: datetime


class AlertRuleResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    org_id: str
    name: str
    description: str | None = None
    target: str
    dsl: dict[str, Any]
    condition: dict[str, Any]
    severity: str
    severity_label: str
    notify_template_key: str
    labels: dict[str, Any]
    is_active: bool
    paused_until: datetime | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "AlertRuleResponse":
        dsl = row.get("dsl") or {}
        if isinstance(dsl, str):
            dsl = _json.loads(dsl)
        condition = row.get("condition") or {}
        if isinstance(condition, str):
            condition = _json.loads(condition)
        labels = row.get("labels") or {}
        if isinstance(labels, str):
            labels = _json.loads(labels)
        return cls(
            id=str(row["id"]),
            org_id=str(row["org_id"]),
            name=row["name"],
            description=row.get("description"),
            target=row["target"],
            dsl=dsl,
            condition=condition,
            severity=row["severity_code"],
            severity_label=row["severity_label"],
            notify_template_key=row["notify_template_key"],
            labels=labels,
            is_active=row["is_active"],
            paused_until=row.get("paused_until"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class SilenceMatcher(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_id: str | None = None
    labels: dict[str, str] | None = None


class SilenceCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    matcher: SilenceMatcher
    starts_at: datetime
    ends_at: datetime
    reason: str = Field(min_length=1, max_length=1000)


class SilenceResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    org_id: str
    matcher: dict[str, Any]
    starts_at: datetime
    ends_at: datetime
    reason: str
    created_by: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "SilenceResponse":
        matcher = row.get("matcher") or {}
        if isinstance(matcher, str):
            matcher = _json.loads(matcher)
        return cls(
            id=str(row["id"]),
            org_id=str(row["org_id"]),
            matcher=matcher,
            starts_at=row["starts_at"],
            ends_at=row["ends_at"],
            reason=row["reason"],
            created_by=str(row["created_by"]),
            is_active=row["is_active"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class AlertEventResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    rule_id: str
    rule_name: str | None = None
    severity: str | None = None
    severity_label: str | None = None
    fingerprint: str
    state: str
    value: float | None = None
    threshold: float | None = None
    org_id: str
    started_at: datetime
    resolved_at: datetime | None = None
    last_notified_at: datetime | None = None
    notification_count: int
    silenced: bool
    silence_id: str | None = None
    labels: dict[str, Any]
    annotations: dict[str, Any]

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "AlertEventResponse":
        labels = row.get("labels") or {}
        if isinstance(labels, str):
            labels = _json.loads(labels)
        annotations = row.get("annotations") or {}
        if isinstance(annotations, str):
            annotations = _json.loads(annotations)
        return cls(
            id=str(row["id"]),
            rule_id=str(row["rule_id"]),
            rule_name=row.get("rule_name"),
            severity=row.get("severity_code"),
            severity_label=row.get("severity_label"),
            fingerprint=row["fingerprint"],
            state=row["state"],
            value=row.get("value"),
            threshold=row.get("threshold"),
            org_id=str(row["org_id"]),
            started_at=row["started_at"],
            resolved_at=row.get("resolved_at"),
            last_notified_at=row.get("last_notified_at"),
            notification_count=row.get("notification_count") or 0,
            silenced=row.get("silenced") or False,
            silence_id=(str(row["silence_id"]) if row.get("silence_id") else None),
            labels=labels,
            annotations=annotations,
        )
