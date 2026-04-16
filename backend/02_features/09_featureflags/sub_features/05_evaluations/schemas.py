"""featureflags.evaluations — request + response schemas."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

Environment = Literal["dev", "staging", "prod", "test"]

EvalReason = Literal[
    "user_override",
    "org_override",
    "application_override",
    "rule_match",
    "default_env",
    "default_flag",
    "flag_disabled_in_env",
    "flag_not_found",
    "flag_inactive",
]


class EvalContext(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: str | None = None
    org_id: str | None = None
    workspace_id: str | None = None
    application_id: str | None = None
    attrs: dict[str, Any] = {}


class EvaluateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    flag_key: str
    environment: Environment
    context: EvalContext = EvalContext()


class EvaluateResponse(BaseModel):
    value: Any
    reason: EvalReason
    flag_id: str | None = None
    flag_scope: str | None = None
    rule_id: str | None = None
    override_id: str | None = None
