from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ENHANCEABLE_ENTITY_TYPES = Literal[
    "control",
    "risk",
    "task",
    "framework",
    "requirement",
    "comment",
]

ENHANCEABLE_FIELD_NAMES = Literal[
    "description",
    "implementation_guidance",
    "acceptance_criteria",
    "remediation_plan",
    "notes",
    "business_impact",
    "guidance",
    "name",
    "title",
    "comment_body",
]


class EnhanceTextRequest(BaseModel):
    entity_type: str = Field(..., min_length=1, max_length=50)
    entity_id: str | None = Field(None, max_length=100)
    field_name: str = Field(..., min_length=1, max_length=100)
    current_value: str | list[str] = Field(...)
    instruction: str = Field(..., min_length=1, max_length=2000)
    org_id: str | None = Field(None, max_length=100)
    workspace_id: str | None = Field(None, max_length=100)
    # Optional structured context about the entity for richer prompting
    entity_context: dict | None = None
    # Model override (if not set, uses resolved config)
    model_id: str | None = Field(None, max_length=200)
