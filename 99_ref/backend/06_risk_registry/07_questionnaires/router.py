from __future__ import annotations

import uuid
from importlib import import_module
from typing import Annotated, Optional

from fastapi import Depends, Query, status

from .dependencies import get_questionnaires_service
from .schemas import (
    AssignmentResponse,
    CompleteResponseOutput,
    CompleteResponseRequest,
    CurrentQuestionnaireResponse,
    QuestionnaireContentSchema,
    QuestionnaireCreateRequest,
    QuestionnaireResponse,
    QuestionnaireUpdateRequest,
    QuestionnaireVersionResponse,
    QuestionActivateDeactivateRequest,
    SaveDraftRequest,
    SaveDraftResponse,
    SectionActivateDeactivateRequest,
    UpsertAssignmentRequest,
    VersionPublishRequest,
)
from .service import QuestionnairesService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")
_errors_module = import_module("backend.01_core.errors")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims
NotFoundError = _errors_module.NotFoundError

router = InstrumentedAPIRouter(tags=["risk-questionnaires"])


# --- Super Admin Endpoints ---


@router.get("/questionnaires", response_model=list[QuestionnaireResponse])
async def list_questionnaires(
    service: Annotated[QuestionnairesService, Depends(get_questionnaires_service)],
    claims=Depends(get_current_access_claims),
) -> list[QuestionnaireResponse]:
    return await service.list_questionnaires(tenant_key=claims.tenant_key)


@router.get("/questionnaires/active", response_model=list[QuestionnaireResponse])
async def list_active_questionnaires(
    service: Annotated[QuestionnairesService, Depends(get_questionnaires_service)],
    claims=Depends(get_current_access_claims),
) -> list[QuestionnaireResponse]:
    """Returns only active questionnaires (is_active=true) for settings/workspace pages."""
    return await service.list_active_questionnaires(tenant_key=claims.tenant_key)


@router.post(
    "/questionnaires",
    response_model=QuestionnaireResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_questionnaire(
    body: QuestionnaireCreateRequest,
    service: Annotated[QuestionnairesService, Depends(get_questionnaires_service)],
    claims=Depends(get_current_access_claims),
) -> QuestionnaireResponse:
    return await service.create_questionnaire(
        tenant_key=claims.tenant_key, request=body, user_id=claims.subject
    )


@router.patch(
    "/questionnaires/{questionnaire_id}",
    response_model=QuestionnaireResponse,
)
async def update_questionnaire(
    questionnaire_id: uuid.UUID,
    body: QuestionnaireUpdateRequest,
    service: Annotated[QuestionnairesService, Depends(get_questionnaires_service)],
    claims=Depends(get_current_access_claims),
) -> QuestionnaireResponse:
    return await service.update_questionnaire(
        tenant_key=claims.tenant_key,
        questionnaire_id=questionnaire_id,
        request=body,
        user_id=claims.subject,
    )


@router.delete(
    "/questionnaires/{questionnaire_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_questionnaire(
    questionnaire_id: uuid.UUID,
    service: Annotated[QuestionnairesService, Depends(get_questionnaires_service)],
    claims=Depends(get_current_access_claims),
) -> dict[str, str]:
    return await service.delete_questionnaire(
        tenant_key=claims.tenant_key,
        questionnaire_id=questionnaire_id,
        user_id=claims.subject,
    )


@router.post(
    "/questionnaires/{questionnaire_id}/versions",
    response_model=QuestionnaireVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def publish_version(
    questionnaire_id: uuid.UUID,
    body: VersionPublishRequest,
    service: Annotated[QuestionnairesService, Depends(get_questionnaires_service)],
    claims=Depends(get_current_access_claims),
) -> QuestionnaireVersionResponse:
    return await service.publish_version(
        tenant_key=claims.tenant_key,
        questionnaire_id=questionnaire_id,
        request=body,
        user_id=claims.subject,
    )


@router.get(
    "/questionnaires/{questionnaire_id}/versions",
    response_model=list[QuestionnaireVersionResponse],
)
async def list_versions(
    questionnaire_id: uuid.UUID,
    service: Annotated[QuestionnairesService, Depends(get_questionnaires_service)],
    claims=Depends(get_current_access_claims),
) -> list[QuestionnaireVersionResponse]:
    return await service.list_versions(
        tenant_key=claims.tenant_key, questionnaire_id=questionnaire_id
    )


@router.get(
    "/questionnaires/versions/{version_id}",
    response_model=QuestionnaireVersionResponse,
)
async def get_version(
    version_id: uuid.UUID,
    service: Annotated[QuestionnairesService, Depends(get_questionnaires_service)],
    claims=Depends(get_current_access_claims),
) -> QuestionnaireVersionResponse:
    return await service.get_version(
        tenant_key=claims.tenant_key, version_id=version_id
    )


@router.patch(
    "/questionnaires/versions/{version_id}/content",
    response_model=QuestionnaireVersionResponse,
)
async def update_version_content(
    version_id: uuid.UUID,
    body: QuestionnaireContentSchema,
    service: Annotated[QuestionnairesService, Depends(get_questionnaires_service)],
    claims=Depends(get_current_access_claims),
) -> QuestionnaireVersionResponse:
    return await service.update_version_content(
        tenant_key=claims.tenant_key,
        version_id=version_id,
        content=body,
    )


@router.patch(
    "/questionnaires/versions/{version_id}/sections/{section_id}/active",
    response_model=QuestionnaireVersionResponse,
)
async def set_section_active_status(
    version_id: uuid.UUID,
    section_id: str,
    body: SectionActivateDeactivateRequest,
    service: Annotated[QuestionnairesService, Depends(get_questionnaires_service)],
    claims=Depends(get_current_access_claims),
) -> QuestionnaireVersionResponse:
    """
    Activate or deactivate a section within a questionnaire version.
    - Deactivating a section will set the questionnaire to inactive.
    - Activating a section will set the questionnaire to active (if any section is active).
    """
    return await service.set_section_active_status(
        tenant_key=claims.tenant_key,
        version_id=version_id,
        section_id=section_id,
        request=body,
    )


@router.patch(
    "/questionnaires/versions/{version_id}/sections/{section_id}/questions/{question_id}/active",
    response_model=QuestionnaireVersionResponse,
)
async def set_question_active_status(
    version_id: uuid.UUID,
    section_id: str,
    question_id: str,
    body: QuestionActivateDeactivateRequest,
    service: Annotated[QuestionnairesService, Depends(get_questionnaires_service)],
    claims=Depends(get_current_access_claims),
) -> QuestionnaireVersionResponse:
    """
    Activate or deactivate a question within a section in a questionnaire version.
    """
    return await service.set_question_active_status(
        tenant_key=claims.tenant_key,
        version_id=version_id,
        section_id=section_id,
        question_id=question_id,
        request=body,
    )


@router.put("/questionnaire-assignments", response_model=AssignmentResponse)
async def upsert_assignment(
    body: UpsertAssignmentRequest,
    service: Annotated[QuestionnairesService, Depends(get_questionnaires_service)],
    claims=Depends(get_current_access_claims),
) -> AssignmentResponse:
    return await service.upsert_assignment(
        tenant_key=claims.tenant_key, request=body, user_id=claims.subject
    )


# --- Workspace / Organization Endpoints ---


@router.get(
    "/questionnaire-responses/current",
    response_model=Optional[CurrentQuestionnaireResponse],
)
async def get_current_questionnaire(
    service: Annotated[QuestionnairesService, Depends(get_questionnaires_service)],
    claims=Depends(get_current_access_claims),
    org_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID | None = Query(None),
    questionnaire_id: uuid.UUID = Query(...),
) -> CurrentQuestionnaireResponse | None:
    """
    Returns the active questionnaire + user's answers for the given org/workspace and specific questionnaire form.
    Returns null (200) when no questionnaire is assigned yet — NOT a 404.
    """
    try:
        return await service.get_current_questionnaire(
            tenant_key=claims.tenant_key,
            org_id=org_id,
            workspace_id=workspace_id,
            questionnaire_id=questionnaire_id,
        )
    except NotFoundError:
        return None


@router.put("/questionnaire-responses/current/draft", response_model=SaveDraftResponse)
async def save_draft(
    body: SaveDraftRequest,
    service: Annotated[QuestionnairesService, Depends(get_questionnaires_service)],
    claims=Depends(get_current_access_claims),
    org_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID | None = Query(None),
    questionnaire_id: uuid.UUID = Query(...),
) -> SaveDraftResponse:
    return await service.save_draft(
        tenant_key=claims.tenant_key,
        org_id=org_id,
        workspace_id=workspace_id,
        questionnaire_id=questionnaire_id,
        request=body,
        user_id=claims.subject,
    )


@router.post(
    "/questionnaire-responses/current/complete", response_model=CompleteResponseOutput
)
async def complete_response(
    body: CompleteResponseRequest,
    service: Annotated[QuestionnairesService, Depends(get_questionnaires_service)],
    claims=Depends(get_current_access_claims),
    org_id: uuid.UUID = Query(...),
    workspace_id: uuid.UUID | None = Query(None),
    questionnaire_id: uuid.UUID = Query(...),
) -> CompleteResponseOutput:
    return await service.complete_response(
        tenant_key=claims.tenant_key,
        org_id=org_id,
        workspace_id=workspace_id,
        questionnaire_id=questionnaire_id,
        request=body,
        user_id=claims.subject,
    )
