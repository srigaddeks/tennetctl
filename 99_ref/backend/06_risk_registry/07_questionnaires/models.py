from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass
from typing import Any


@dataclass(kw_only=True)
class QuestionnaireRecord:
    id: uuid.UUID
    tenant_key: str
    questionnaire_code: str
    name: str
    description: str | None
    intended_scope: str
    current_status: str
    latest_version_number: int
    active_version_id: uuid.UUID | None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    created_by: uuid.UUID | None
    updated_by: uuid.UUID | None
    is_active: bool
    is_deleted: bool


@dataclass(kw_only=True)
class QuestionnaireVersionRecord:
    id: uuid.UUID
    questionnaire_id: uuid.UUID
    version_number: int
    version_status: str
    content_jsonb: dict[str, Any]
    version_label: str | None
    change_notes: str | None
    published_at: datetime.datetime | None
    published_by: uuid.UUID | None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    created_by: uuid.UUID | None
    updated_by: uuid.UUID | None


@dataclass(kw_only=True)
class QuestionnaireAssignmentRecord:
    id: uuid.UUID
    tenant_key: str
    assignment_scope: str
    org_id: uuid.UUID | None
    workspace_id: uuid.UUID | None
    questionnaire_version_id: uuid.UUID
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
    created_by: uuid.UUID | None
    updated_by: uuid.UUID | None


@dataclass(kw_only=True)
class QuestionnaireResponseRecord:
    id: uuid.UUID
    tenant_key: str
    org_id: uuid.UUID
    workspace_id: uuid.UUID | None
    questionnaire_version_id: uuid.UUID
    response_status: str
    answers_jsonb: dict[str, Any]
    completed_at: datetime.datetime | None
    completed_by: uuid.UUID | None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    created_by: uuid.UUID | None
    updated_by: uuid.UUID | None
