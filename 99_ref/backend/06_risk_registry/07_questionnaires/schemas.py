from __future__ import annotations

import uuid
from typing import Any
from pydantic import BaseModel, Field


# --- Shared JSONB Schema Models ---


class QuestionOptionSchema(BaseModel):
    value: str | None = None
    label: str


class QuestionSchema(BaseModel):
    id: str | None = None
    label: str
    type: str  # single, multi, text
    required: bool = False
    options: list[QuestionOptionSchema] | None = None
    helperText: str | None = None
    placeholder: str | None = None
    subsection: str | None = None
    is_active: bool = True


class SectionSchema(BaseModel):
    id: str | None = None
    title: str
    description: str | None = None
    icon: str | None = None
    is_active: bool = True
    questions: list[QuestionSchema]


class QuestionnaireContentSchema(BaseModel):
    sections: list[SectionSchema]


# --- Questionnaire Templates ---


class QuestionnaireCreateRequest(BaseModel):
    questionnaire_code: str
    name: str
    description: str | None = None
    intended_scope: str = Field(..., description="platform, org, workspace")


class QuestionnaireUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    intended_scope: str | None = Field(
        default=None, description="platform, org, workspace"
    )


class QuestionnaireResponse(BaseModel):
    id: uuid.UUID
    questionnaire_code: str
    name: str
    description: str | None
    intended_scope: str
    current_status: str
    latest_version_number: int
    active_version_id: uuid.UUID | None
    is_active: bool


# --- Versions ---


class VersionPublishRequest(BaseModel):
    content_jsonb: QuestionnaireContentSchema
    version_label: str | None = None
    change_notes: str | None = None


class QuestionnaireVersionResponse(BaseModel):
    id: uuid.UUID
    questionnaire_id: uuid.UUID
    version_number: int
    version_status: str
    content_jsonb: QuestionnaireContentSchema
    version_label: str | None = None
    change_notes: str | None = None


# --- Assignments ---


class UpsertAssignmentRequest(BaseModel):
    assignment_scope: str = Field(..., description="platform, org, workspace")
    org_id: uuid.UUID | None = None
    workspace_id: uuid.UUID | None = None
    questionnaire_version_id: uuid.UUID


class AssignmentResponse(BaseModel):
    id: uuid.UUID
    assignment_scope: str
    org_id: uuid.UUID | None
    workspace_id: uuid.UUID | None
    questionnaire_version_id: uuid.UUID
    is_active: bool


# --- Runtime / Responses ---


class CurrentQuestionnaireResponse(BaseModel):
    # Returns the active version + any existing answers
    questionnaire_version_id: uuid.UUID
    version_number: int
    content_jsonb: QuestionnaireContentSchema
    response_status: str | None  # draft, completed, or None if brand new
    answers_jsonb: dict[str, Any]  # The user's answers


class SaveDraftRequest(BaseModel):
    answers_jsonb: dict[str, Any]


class SaveDraftResponse(BaseModel):
    response_id: uuid.UUID
    response_status: str


class CompleteResponseRequest(BaseModel):
    answers_jsonb: dict[str, Any]


class CompleteResponseOutput(BaseModel):
    response_id: uuid.UUID
    response_status: str
    missing_required_question_ids: list[str] | None = None


# --- Section Activation/Deactivation ---


class SectionActivateDeactivateRequest(BaseModel):
    is_active: bool


# --- Question Activation/Deactivation ---


class QuestionActivateDeactivateRequest(BaseModel):
    is_active: bool
