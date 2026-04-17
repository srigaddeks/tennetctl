"""Pydantic schemas for notify.template_variables."""

from __future__ import annotations

from datetime import datetime
from importlib import import_module
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

_safelist: Any = import_module(
    "backend.02_features.06_notify.sub_features.03_templates.nodes.safelist"
)


class TemplateVariableCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern=r"^[a-z_][a-z0-9_]*$",
        description="Jinja2-safe identifier: lowercase letters, digits, underscores; must start with letter or underscore",
    )
    var_type: Literal["static", "dynamic_sql"]
    static_value: str | None = None
    sql_template: str | None = None
    param_bindings: dict[str, str] | None = None
    description: str | None = None

    @model_validator(mode="after")
    def _validate_type_fields(self) -> "TemplateVariableCreate":
        if self.var_type == "static":
            if self.static_value is None:
                raise ValueError("static_value is required when var_type='static'")
        elif self.var_type == "dynamic_sql":
            if not self.sql_template:
                raise ValueError("sql_template is required when var_type='dynamic_sql'")
            _safelist.validate_dynamic_sql(self.sql_template, self.param_bindings)
        return self


class TemplateVariableUpdate(BaseModel):
    static_value: str | None = None
    sql_template: str | None = None
    param_bindings: dict[str, str] | None = None
    description: str | None = None

    @model_validator(mode="after")
    def _validate_dynamic_if_sql(self) -> "TemplateVariableUpdate":
        if self.sql_template is not None:
            _safelist.validate_dynamic_sql(self.sql_template, self.param_bindings)
        return self


class ResolveRequest(BaseModel):
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Audit event context for dynamic SQL resolution (actor_user_id, org_id, workspace_id, event_metadata)",
    )


class TemplateVariableRow(BaseModel):
    id: str
    template_id: str
    name: str
    var_type: str
    static_value: str | None
    sql_template: str | None
    param_bindings: dict | None
    description: str | None
    created_at: datetime
    updated_at: datetime
