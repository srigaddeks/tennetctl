from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, model_validator


class AddAssignmentRequest(BaseModel):
    user_id: str | None = None
    email: EmailStr | None = None
    role: str = Field(default="co_assignee", pattern=r"^(co_assignee|reviewer|observer)$")

    @model_validator(mode="after")
    def _validate_target(self) -> "AddAssignmentRequest":
        if not self.user_id and not self.email:
            raise ValueError("Either user_id or email must be provided.")
        return self


class TaskAssignmentResponse(BaseModel):
    id: str
    task_id: str
    user_id: str
    role: str
    assigned_at: str
    assigned_by: str | None = None
