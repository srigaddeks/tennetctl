from __future__ import annotations

import datetime
import uuid
from importlib import import_module
from typing import Any

from .constants import (
    SCOPE_ORG,
    SCOPE_PLATFORM,
    SCOPE_WORKSPACE,
    STATUS_DRAFT,
    STATUS_PUBLISHED,
    STATUS_COMPLETED,
)
from .models import (
    QuestionnaireAssignmentRecord,
    QuestionnaireRecord,
    QuestionnaireResponseRecord,
    QuestionnaireVersionRecord,
)
from .schemas import (
    AssignmentResponse,
    CompleteResponseOutput,
    CompleteResponseRequest,
    CurrentQuestionnaireResponse,
    QuestionnaireContentSchema,
    QuestionnaireCreateRequest,
    QuestionnaireResponse,
    QuestionnaireVersionResponse,
    QuestionActivateDeactivateRequest,
    QuestionnaireUpdateRequest,
    SaveDraftRequest,
    SaveDraftResponse,
    SectionActivateDeactivateRequest,
    UpsertAssignmentRequest,
    VersionPublishRequest,
)

_database_module = import_module("backend.01_core.database")
_settings_module = import_module("backend.00_config.settings")
_errors_module = import_module("backend.01_core.errors")
_telemetry_module = import_module("backend.01_core.telemetry")
_logging_module = import_module("backend.01_core.logging_utils")
_time_module = import_module("backend.01_core.time_utils")
_audit_module = import_module("backend.01_core.audit")

from .repository import QuestionnairesRepository

DatabasePool, Settings = _database_module.DatabasePool, _settings_module.Settings
AppError, NotFoundError, ValidationError = (
    _errors_module.AppError,
    _errors_module.NotFoundError,
    _errors_module.ValidationError,
)
instrument_class_methods, get_logger = (
    _telemetry_module.instrument_class_methods,
    _logging_module.get_logger,
)
utc_now_sql = _time_module.utc_now_sql

from zoneinfo import ZoneInfo

CET_TZ = ZoneInfo("Europe/Paris")


def cet_now() -> datetime.datetime:
    return datetime.datetime.now(tz=CET_TZ).replace(tzinfo=None)


def _filter_active_content(content: dict[str, Any]) -> dict[str, Any]:
    """Filter out inactive sections and inactive questions within active sections.
    Returns a new dictionary to avoid mutating the original input.
    """
    sections = content.get("sections", [])
    active_sections = []

    for section in sections:
        # Skip inactive sections
        if section.get("is_active", True) is False:
            continue

        # Rebuild section with filtered questions
        questions = section.get("questions", [])
        active_questions = [
            q for q in questions if q.get("is_active", True) is not False
        ]

        # Create a copy of the section to avoid mutating the original
        new_section = dict(section)
        new_section["questions"] = active_questions
        active_sections.append(new_section)

    return {"sections": active_sections}


def _is_valid_uuid(val: Any) -> bool:
    if not isinstance(val, str):
        return False
    try:
        uuid.UUID(val)
        return True
    except ValueError:
        return False


@instrument_class_methods(
    namespace="risk.questionnaires.service",
    logger_name="backend.risk.questionnaires.service.instrumentation",
)
class QuestionnairesService:
    def __init__(self, *, settings: Settings, database_pool: DatabasePool) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._repository = QuestionnairesRepository()
        self._audit_writer = _audit_module.AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.risk.questionnaires")

    def _ensure_stable_ids(self, content: dict[str, Any]) -> None:
        """Recursive helper to ensure every section, question, and option has a UUID.
        Strictly replaces any non-UUID ID with a fresh UUID for all three levels.
        """
        for section in content.get("sections", []):
            if not _is_valid_uuid(section.get("id")):
                section["id"] = str(uuid.uuid4())

            for question in section.get("questions", []):
                if not _is_valid_uuid(question.get("id")):
                    question["id"] = str(uuid.uuid4())

                options = question.get("options")
                if options and isinstance(options, list):
                    for opt in options:
                        # For options, 'value' acts as the stable ID for the choice
                        if not _is_valid_uuid(opt.get("value")):
                            opt["value"] = str(uuid.uuid4())

    # --- QUESTIONNAIRES (SUPER ADMIN) ---

    async def list_questionnaires(self, tenant_key: str) -> list[QuestionnaireResponse]:
        async with self._database_pool.acquire() as conn:
            records = await self._repository.list_questionnaires(conn, tenant_key)
            return [
                QuestionnaireResponse(
                    id=r.id,
                    questionnaire_code=r.questionnaire_code,
                    name=r.name,
                    description=r.description,
                    intended_scope=r.intended_scope,
                    current_status=r.current_status,
                    latest_version_number=r.latest_version_number,
                    active_version_id=r.active_version_id,
                    is_active=r.is_active,
                )
                for r in records
            ]

    async def list_active_questionnaires(
        self, tenant_key: str
    ) -> list[QuestionnaireResponse]:
        async with self._database_pool.acquire() as conn:
            records = await self._repository.list_active_questionnaires(
                conn, tenant_key
            )
            return [
                QuestionnaireResponse(
                    id=r.id,
                    questionnaire_code=r.questionnaire_code,
                    name=r.name,
                    description=r.description,
                    intended_scope=r.intended_scope,
                    current_status=r.current_status,
                    latest_version_number=r.latest_version_number,
                    active_version_id=r.active_version_id,
                    is_active=r.is_active,
                )
                for r in records
            ]

    async def create_questionnaire(
        self, tenant_key: str, request: QuestionnaireCreateRequest, user_id: uuid.UUID
    ) -> QuestionnaireResponse:
        now = cet_now()
        record = QuestionnaireRecord(
            id=uuid.uuid4(),
            tenant_key=tenant_key,
            questionnaire_code=request.questionnaire_code,
            name=request.name,
            description=request.description,
            intended_scope=request.intended_scope,
            current_status=STATUS_DRAFT,
            latest_version_number=0,
            active_version_id=None,
            created_at=now,
            updated_at=now,
            created_by=user_id,
            updated_by=user_id,
            is_active=True,
            is_deleted=False,
        )

        async with self._database_pool.transaction() as conn:
            try:
                await self._repository.create_questionnaire(conn, record=record)
                await self._audit_writer.write_entry(
                    conn,
                    _audit_module.AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="questionnaire",
                        entity_id=str(record.id),
                        event_type="create",
                        event_category="risk",
                        occurred_at=now,
                        actor_id=str(user_id),
                        actor_type="user",
                        properties={
                            "questionnaire_code": record.questionnaire_code,
                            "name": record.name,
                        },
                    ),
                )
            except Exception as e:
                if (
                    "unique constraint" in str(e).lower()
                    or "uq_37_fct" in str(e).lower()
                ):
                    raise ValidationError(
                        "A questionnaire with this code already exists."
                    )
                raise

        return QuestionnaireResponse(
            id=record.id,
            questionnaire_code=record.questionnaire_code,
            name=record.name,
            description=record.description,
            intended_scope=record.intended_scope,
            current_status=record.current_status,
            latest_version_number=record.latest_version_number,
            active_version_id=record.active_version_id,
            is_active=record.is_active,
        )

    async def update_questionnaire(
        self,
        tenant_key: str,
        questionnaire_id: uuid.UUID,
        request: QuestionnaireUpdateRequest,
        user_id: uuid.UUID,
    ) -> QuestionnaireResponse:
        now = cet_now()

        async with self._database_pool.transaction() as conn:
            q_record = await self._repository.get_questionnaire(
                conn, questionnaire_id, tenant_key
            )
            if not q_record:
                raise NotFoundError("Questionnaire not found.")

            await self._repository.update_questionnaire(
                conn,
                questionnaire_id,
                name=request.name,
                description=request.description,
                intended_scope=request.intended_scope,
            )

            await self._audit_writer.write_entry(
                conn,
                _audit_module.AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="questionnaire",
                    entity_id=str(questionnaire_id),
                    event_type="update",
                    event_category="risk",
                    occurred_at=now,
                    actor_id=str(user_id),
                    actor_type="user",
                    properties={
                        "questionnaire_code": q_record.questionnaire_code,
                        "name": request.name or q_record.name,
                        "description": request.description,
                        "intended_scope": request.intended_scope
                        or q_record.intended_scope,
                    },
                ),
            )

            updated_record = await self._repository.get_questionnaire(
                conn, questionnaire_id, tenant_key
            )
            if not updated_record:
                raise NotFoundError("Questionnaire not found after update.")

        return QuestionnaireResponse(
            id=updated_record.id,
            questionnaire_code=updated_record.questionnaire_code,
            name=updated_record.name,
            description=updated_record.description,
            intended_scope=updated_record.intended_scope,
            current_status=updated_record.current_status,
            latest_version_number=updated_record.latest_version_number,
            active_version_id=updated_record.active_version_id,
            is_active=updated_record.is_active,
        )

    async def delete_questionnaire(
        self,
        tenant_key: str,
        questionnaire_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, str]:
        now = cet_now()

        async with self._database_pool.transaction() as conn:
            q_record = await self._repository.get_questionnaire(
                conn, questionnaire_id, tenant_key
            )
            if not q_record:
                raise NotFoundError("Questionnaire not found.")

            if q_record.is_deleted:
                raise ValidationError("Questionnaire is already deleted.")

            await self._repository.soft_delete_questionnaire(conn, questionnaire_id)

            await self._audit_writer.write_entry(
                conn,
                _audit_module.AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="questionnaire",
                    entity_id=str(questionnaire_id),
                    event_type="delete",
                    event_category="risk",
                    occurred_at=now,
                    actor_id=str(user_id),
                    actor_type="user",
                    properties={
                        "questionnaire_code": q_record.questionnaire_code,
                        "name": q_record.name,
                    },
                ),
            )

        return {"message": "Questionnaire deleted successfully."}

    async def publish_version(
        self,
        tenant_key: str,
        questionnaire_id: uuid.UUID,
        request: VersionPublishRequest,
        user_id: uuid.UUID,
    ) -> QuestionnaireVersionResponse:
        now = cet_now()
        version_id = uuid.uuid4()

        async with self._database_pool.transaction() as conn:
            q_record = await self._repository.get_questionnaire(
                conn, questionnaire_id, tenant_key
            )
            if not q_record:
                raise NotFoundError("Questionnaire not found.")

            new_version_num = q_record.latest_version_number + 1

            content = request.content_jsonb.model_dump()
            self._ensure_stable_ids(content)

            v_record = QuestionnaireVersionRecord(
                id=version_id,
                questionnaire_id=questionnaire_id,
                version_number=new_version_num,
                version_status=STATUS_PUBLISHED,
                content_jsonb=content,
                version_label=request.version_label,
                change_notes=request.change_notes,
                published_at=now,
                published_by=user_id,
                created_at=now,
                updated_at=now,
                created_by=user_id,
                updated_by=user_id,
            )

            await self._repository.create_version(conn, record=v_record)
            await self._repository.increment_questionnaire_version(
                conn, questionnaire_id, new_version_num
            )
            await self._repository.update_questionnaire_status(
                conn, questionnaire_id, STATUS_PUBLISHED, version_id
            )
            await self._audit_writer.write_entry(
                conn,
                _audit_module.AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="questionnaire",
                    entity_id=str(questionnaire_id),
                    event_type="publish_version",
                    event_category="risk",
                    occurred_at=now,
                    actor_id=str(user_id),
                    actor_type="user",
                    properties={
                        "version_id": str(version_id),
                        "version_number": str(new_version_num),
                    },
                ),
            )

        return QuestionnaireVersionResponse(
            id=version_id,
            questionnaire_id=questionnaire_id,
            version_number=new_version_num,
            version_status=STATUS_PUBLISHED,
            content_jsonb=QuestionnaireContentSchema(**v_record.content_jsonb),
            version_label=v_record.version_label,
            change_notes=v_record.change_notes,
        )

    async def list_versions(
        self, tenant_key: str, questionnaire_id: uuid.UUID
    ) -> list[QuestionnaireVersionResponse]:
        async with self._database_pool.acquire() as conn:
            q_record = await self._repository.get_questionnaire(
                conn, questionnaire_id, tenant_key
            )
            if not q_record:
                raise NotFoundError("Questionnaire not found.")
            records = await self._repository.list_versions(conn, questionnaire_id)
            return [
                QuestionnaireVersionResponse(
                    id=r.id,
                    questionnaire_id=r.questionnaire_id,
                    version_number=r.version_number,
                    version_status=r.version_status,
                    content_jsonb=QuestionnaireContentSchema(**r.content_jsonb),
                    version_label=r.version_label,
                    change_notes=r.change_notes,
                )
                for r in records
            ]

    async def get_version(
        self, tenant_key: str, version_id: uuid.UUID, filter_inactive: bool = False
    ) -> QuestionnaireVersionResponse:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_version(conn, version_id)
            if not record:
                raise NotFoundError("Questionnaire version not found.")

            content = (
                _filter_active_content(record.content_jsonb)
                if filter_inactive
                else record.content_jsonb
            )
            return QuestionnaireVersionResponse(
                id=record.id,
                questionnaire_id=record.questionnaire_id,
                version_number=record.version_number,
                version_status=record.version_status,
                content_jsonb=QuestionnaireContentSchema(**content),
                version_label=record.version_label,
                change_notes=record.change_notes,
            )

    async def update_version_content(
        self,
        tenant_key: str,
        version_id: uuid.UUID,
        content: QuestionnaireContentSchema,
        filter_inactive: bool = False,
    ) -> QuestionnaireVersionResponse:
        async with self._database_pool.transaction() as conn:
            record = await self._repository.get_version(conn, version_id)
            if not record:
                raise NotFoundError("Questionnaire version not found.")

            content_data = content.model_dump()
            self._ensure_stable_ids(content_data)

            await self._repository.update_version_content(
                conn, version_id, content_data
            )

            response_content = (
                _filter_active_content(content_data)
                if filter_inactive
                else content_data
            )
            return QuestionnaireVersionResponse(
                id=record.id,
                questionnaire_id=record.questionnaire_id,
                version_number=record.version_number,
                version_status=record.version_status,
                content_jsonb=QuestionnaireContentSchema(**response_content),
                version_label=record.version_label,
                change_notes=record.change_notes,
            )

    # --- ASSIGNMENTS ---

    async def upsert_assignment(
        self, tenant_key: str, request: UpsertAssignmentRequest, user_id: uuid.UUID
    ) -> AssignmentResponse:
        now = cet_now()
        assignment_id = uuid.uuid4()

        record = QuestionnaireAssignmentRecord(
            id=assignment_id,
            tenant_key=tenant_key,
            assignment_scope=request.assignment_scope,
            org_id=request.org_id,
            workspace_id=request.workspace_id,
            questionnaire_version_id=request.questionnaire_version_id,
            is_active=True,
            created_at=now,
            updated_at=now,
            created_by=user_id,
            updated_by=user_id,
        )

        async with self._database_pool.transaction() as conn:
            version = await self._repository.get_version(
                conn, request.questionnaire_version_id
            )
            if not version:
                raise NotFoundError("Questionnaire version not found.")
            await self._repository.upsert_assignment(
                conn, record=record, questionnaire_id=version.questionnaire_id
            )

        return AssignmentResponse(
            id=record.id,
            assignment_scope=record.assignment_scope,
            org_id=record.org_id,
            workspace_id=record.workspace_id,
            questionnaire_version_id=record.questionnaire_version_id,
            is_active=record.is_active,
        )

    # --- RESPONSES (WORKSPACE) ---

    from typing import Optional

    async def _resolve_active_version_id_for_scope(
        self,
        conn: Any,
        tenant_key: str,
        org_id: uuid.UUID,
        workspace_id: Optional[uuid.UUID],
        questionnaire_id: uuid.UUID,
    ) -> Optional[uuid.UUID]:
        # Precedence: Workspace -> Org -> Platform
        if workspace_id:
            ws_assignment = await self._repository.get_assignment(
                conn,
                tenant_key,
                SCOPE_WORKSPACE,
                org_id,
                workspace_id,
                questionnaire_id,
            )
            if ws_assignment:
                return ws_assignment.questionnaire_version_id

        org_assignment = await self._repository.get_assignment(
            conn, tenant_key, SCOPE_ORG, org_id, None, questionnaire_id
        )
        if org_assignment:
            return org_assignment.questionnaire_version_id

        platform_assignment = await self._repository.get_assignment(
            conn, tenant_key, SCOPE_PLATFORM, None, None, questionnaire_id
        )
        if platform_assignment:
            return platform_assignment.questionnaire_version_id

        return None

    async def get_current_questionnaire(
        self,
        tenant_key: str,
        org_id: uuid.UUID,
        workspace_id: uuid.UUID | None,
        questionnaire_id: uuid.UUID,
    ) -> CurrentQuestionnaireResponse:
        async with self._database_pool.acquire() as conn:
            active_version_id = await self._resolve_active_version_id_for_scope(
                conn, tenant_key, org_id, workspace_id, questionnaire_id
            )
            if not active_version_id:
                raise NotFoundError(
                    "No active questionnaire assigned to this workspace."
                )

            version = await self._repository.get_version(conn, active_version_id)
            if not version:
                raise NotFoundError(
                    "Assigned questionnaire version not found in database."
                )

            filtered_content = _filter_active_content(version.content_jsonb)
            response = await self._repository.get_response(
                conn, tenant_key, org_id, workspace_id, active_version_id
            )

            if not response:
                latest = await self._repository.get_latest_response_for_scope(
                    conn, tenant_key, org_id, workspace_id, questionnaire_id
                )
                pre_filled = {}
                if latest:
                    valid_qids = {
                        q.get("id")
                        for sect in filtered_content.get("sections", [])
                        for q in sect.get("questions", [])
                    }
                    pre_filled = {
                        qid: val
                        for qid, val in latest.answers_jsonb.items()
                        if qid in valid_qids
                    }
                return CurrentQuestionnaireResponse(
                    questionnaire_version_id=active_version_id,
                    version_number=version.version_number,
                    content_jsonb=QuestionnaireContentSchema(**filtered_content),
                    response_status=None,
                    answers_jsonb=pre_filled,
                )

            return CurrentQuestionnaireResponse(
                questionnaire_version_id=active_version_id,
                version_number=version.version_number,
                content_jsonb=QuestionnaireContentSchema(**filtered_content),
                response_status=response.response_status,
                answers_jsonb=response.answers_jsonb,
            )

    async def _save_response(
        self,
        conn: Any,
        tenant_key: str,
        org_id: uuid.UUID,
        workspace_id: uuid.UUID | None,
        questionnaire_id: uuid.UUID,
        answers: dict[str, Any],
        status: str,
        user_id: uuid.UUID,
    ) -> uuid.UUID:
        active_version_id = await self._resolve_active_version_id_for_scope(
            conn, tenant_key, org_id, workspace_id, questionnaire_id
        )
        if not active_version_id:
            raise NotFoundError("No active questionnaire assigned to this workspace.")
        response = await self._repository.get_response(
            conn, tenant_key, org_id, workspace_id, active_version_id
        )
        now = cet_now()

        if response:
            await self._repository.update_response(
                conn,
                response.id,
                status,
                answers,
                (now if status == STATUS_COMPLETED else response.completed_at),
                (user_id if status == STATUS_COMPLETED else response.completed_by),
            )
            return response.id

        response_id = uuid.uuid4()
        record = QuestionnaireResponseRecord(
            id=response_id,
            tenant_key=tenant_key,
            org_id=org_id,
            workspace_id=workspace_id,
            questionnaire_version_id=active_version_id,
            response_status=status,
            answers_jsonb=answers,
            completed_at=now if status == STATUS_COMPLETED else None,
            completed_by=user_id if status == STATUS_COMPLETED else None,
            created_at=now,
            updated_at=now,
            created_by=user_id,
            updated_by=user_id,
        )
        await self._repository.create_response(conn, record=record)
        return response_id

    async def save_draft(
        self,
        tenant_key: str,
        org_id: uuid.UUID,
        workspace_id: uuid.UUID | None,
        questionnaire_id: uuid.UUID,
        request: SaveDraftRequest,
        user_id: uuid.UUID,
    ) -> SaveDraftResponse:
        async with self._database_pool.transaction() as conn:
            response_id = await self._save_response(
                conn,
                tenant_key,
                org_id,
                workspace_id,
                questionnaire_id,
                request.answers_jsonb,
                STATUS_DRAFT,
                user_id,
            )
        return SaveDraftResponse(response_id=response_id, response_status=STATUS_DRAFT)

    async def complete_response(
        self,
        tenant_key: str,
        org_id: uuid.UUID,
        workspace_id: uuid.UUID | None,
        questionnaire_id: uuid.UUID,
        request: CompleteResponseRequest,
        user_id: uuid.UUID,
    ) -> CompleteResponseOutput:
        async with self._database_pool.transaction() as conn:
            active_version_id = await self._resolve_active_version_id_for_scope(
                conn, tenant_key, org_id, workspace_id, questionnaire_id
            )
            if not active_version_id:
                raise NotFoundError(
                    "No active questionnaire assigned to this workspace."
                )
            version = await self._repository.get_version(conn, active_version_id)
            if not version:
                raise ValidationError("Version content is missing, cannot validate.")

            missing = [
                q.get("id")
                for sect in version.content_jsonb.get("sections", [])
                for q in sect.get("questions", [])
                if q.get("required") and not request.answers_jsonb.get(q.get("id"))
            ]
            if missing:
                raise ValidationError(f"Missing required fields: {', '.join(missing)}")

            response_id = await self._save_response(
                conn,
                tenant_key,
                org_id,
                workspace_id,
                questionnaire_id,
                request.answers_jsonb,
                STATUS_COMPLETED,
                user_id,
            )

        return CompleteResponseOutput(
            response_id=response_id, response_status=STATUS_COMPLETED
        )

    # --- SECTION ACTIVATION/DEACTIVATION ---

    async def set_section_active_status(
        self,
        tenant_key: str,
        version_id: uuid.UUID,
        section_id: str,
        request: SectionActivateDeactivateRequest,
    ) -> QuestionnaireVersionResponse:
        async with self._database_pool.transaction() as conn:
            version = await self._repository.get_version(conn, version_id)
            if not version:
                raise NotFoundError("Questionnaire version not found.")
            questionnaire = await self._repository.get_questionnaire(
                conn, version.questionnaire_id, tenant_key
            )
            if not questionnaire:
                raise NotFoundError("Questionnaire not found.")

            content = version.content_jsonb
            section = next(
                (s for s in content.get("sections", []) if s.get("id") == section_id),
                None,
            )
            if not section:
                raise NotFoundError(f"Section with id '{section_id}' not found.")
            section["is_active"] = request.is_active

            await self._repository.update_version_content(conn, version_id, content)

            questionnaire_is_active = (
                request.is_active
                if request.is_active
                else any(s.get("is_active", True) for s in content.get("sections", []))
            )
            await self._repository.update_questionnaire_active_status(
                conn, version.questionnaire_id, questionnaire_is_active
            )

            await self._audit_writer.write_entry(
                conn,
                _audit_module.AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="questionnaire_version",
                    entity_id=str(version.questionnaire_id),
                    event_type="update_version_content",
                    event_category="risk",
                    occurred_at=cet_now(),
                    actor_id=None,
                    actor_type="system",
                    properties={
                        "version_id": str(version_id),
                        "section_id": section_id,
                        "is_active": str(request.is_active),
                    },
                ),
            )

            return QuestionnaireVersionResponse(
                id=version.id,
                questionnaire_id=version.questionnaire_id,
                version_number=version.version_number,
                version_status=version.version_status,
                content_jsonb=QuestionnaireContentSchema(**content),
                version_label=version.version_label,
                change_notes=version.change_notes,
            )

    # --- QUESTION ACTIVATION/DEACTIVATION ---

    async def set_question_active_status(
        self,
        tenant_key: str,
        version_id: uuid.UUID,
        section_id: str,
        question_id: str,
        request: QuestionActivateDeactivateRequest,
    ) -> QuestionnaireVersionResponse:
        async with self._database_pool.transaction() as conn:
            version = await self._repository.get_version(conn, version_id)
            if not version:
                raise NotFoundError("Questionnaire version not found.")

            content = version.content_jsonb
            question = next(
                (
                    q
                    for s in content.get("sections", [])
                    if s.get("id") == section_id
                    for q in s.get("questions", [])
                    if q.get("id") == question_id
                ),
                None,
            )
            if not question:
                raise NotFoundError(
                    f"Question with id '{question_id}' not found in section '{section_id}'."
                )
            question["is_active"] = request.is_active

            await self._repository.update_version_content(conn, version_id, content)
            await self._audit_writer.write_entry(
                conn,
                _audit_module.AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="questionnaire_version",
                    entity_id=str(version.questionnaire_id),
                    event_type="update_question_active_status",
                    event_category="risk",
                    occurred_at=cet_now(),
                    actor_id=None,
                    actor_type="system",
                    properties={
                        "version_id": str(version_id),
                        "question_id": question_id,
                        "is_active": str(request.is_active),
                    },
                ),
            )

            return QuestionnaireVersionResponse(
                id=version.id,
                questionnaire_id=version.questionnaire_id,
                version_number=version.version_number,
                version_status=version.version_status,
                content_jsonb=QuestionnaireContentSchema(**content),
                version_label=version.version_label,
                change_notes=version.change_notes,
            )
