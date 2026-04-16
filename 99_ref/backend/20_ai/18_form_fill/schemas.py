from __future__ import annotations

from pydantic import BaseModel, Field


class FormFillOption(BaseModel):
    """A selectable dimension value (type, category, criticality, etc.)."""
    code: str
    name: str


class FormFillRequest(BaseModel):
    """
    Request to auto-fill a GRC create form using natural language.

    entity_type: framework | control | risk | task
    intent:      User's natural-language description of what they want to create.
    org_id / workspace_id: session context, injected from query params.
    available_*: Dimension options the LLM can choose from (helps it pick valid codes).
    entity_context: Extra context (e.g. selected framework name when filling a control).
    """
    entity_type: str = Field(..., min_length=1, max_length=50)
    intent: str = Field(..., min_length=1, max_length=2000)
    org_id: str | None = Field(None, max_length=100)
    workspace_id: str | None = Field(None, max_length=100)

    # Dimension options so LLM picks valid codes
    available_types: list[FormFillOption] = Field(default_factory=list)
    available_categories: list[FormFillOption] = Field(default_factory=list)
    available_criticalities: list[FormFillOption] = Field(default_factory=list)
    available_treatment_types: list[FormFillOption] = Field(default_factory=list)
    available_task_types: list[FormFillOption] = Field(default_factory=list)

    # Extra context (e.g. selected framework/requirement when creating a control)
    entity_context: dict | None = None

    # Model override
    model_id: str | None = Field(None, max_length=200)
