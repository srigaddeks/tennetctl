from __future__ import annotations
import asyncpg
import secrets
import hashlib
from datetime import datetime, timedelta, date
from uuid import uuid4
from typing import List, Optional
from importlib import import_module

from .repository import EngagementRepository
from .models import EngagementDetailRecord, EngagementRecord, AuditAccessTokenRecord, AuditorRequestRecord
from .schemas import EngagementCreate, EngagementUpdate, EngagementTaskCreateRequest, EngagementAssessmentCreate, AssessmentResponse

_assess_service_module = import_module("backend.09_assessments._02_assessments.service")
AssessmentService = _assess_service_module.AssessmentService

_assess_schemas_module = import_module("backend.09_assessments.schemas")
CreateAssessmentRequest = _assess_schemas_module.CreateAssessmentRequest

_errors_module = import_module("backend.01_core.errors")
_task_schemas_module = import_module("backend.07_tasks.02_tasks.schemas")
_audit_module = import_module("backend.01_core.audit")

ValidationError = _errors_module.ValidationError
CreateTaskRequest = _task_schemas_module.CreateTaskRequest
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter

instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


@instrument_class_methods(namespace="engagements.service", logger_name="backend.engagements.service.instrumentation")
class EngagementService:
    EVIDENCE_REQUEST_RETRY_COOLDOWN = timedelta(minutes=15)

    def __init__(self, repository: EngagementRepository):
        self._repo = repository
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")

    async def _get_or_create_auditor_token(
        self,
        connection: asyncpg.Connection,
        *,
        engagement_id: str,
        tenant_key: str,
        email: str,
    ) -> AuditAccessTokenRecord | None:
        tokens = await self._repo.list_access_tokens(
            connection,
            engagement_id,
            tenant_key,
            include_revoked=False,
        )
        token = next((t for t in tokens if t.auditor_email.lower() == email.lower()), None)
        if token:
            return token

        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        return await self._repo.create_auditor_token(
            connection,
            engagement_id=engagement_id,
            tenant_key=tenant_key,
            auditor_email=email,
            token_hash=token_hash,
            expires_at=datetime.now() + timedelta(days=30),
        )

    async def list_engagements(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        org_id: str,
        status_code: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[EngagementDetailRecord]:
        return await self._repo.list_engagements(
            connection,
            tenant_key=tenant_key,
            org_id=org_id,
            status_code=status_code,
            limit=limit,
            offset=offset,
        )

    async def list_my_engagements(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        email: str,
        org_id: str | None = None,
    ) -> List[EngagementDetailRecord]:
        return await self._repo.list_my_engagements(
            connection,
            user_id=user_id,
            email=email,
            org_id=org_id,
        )

    async def validate_auditor_access_and_get_tenant(
        self, connection: asyncpg.Connection, engagement_id: str, email: str
    ) -> Optional[str]:
        """Verify that the auditor has an active guest token and return the engagement tenant key."""
        return await self._repo.validate_auditor_access_and_get_tenant(connection, engagement_id, email)

    async def get_active_membership_access(
        self,
        connection: asyncpg.Connection,
        *,
        engagement_id: str,
        user_id: str,
    ) -> Optional[dict[str, str | None]]:
        return await self._repo.get_active_membership_access(
            connection,
            engagement_id=engagement_id,
            user_id=user_id,
        )

    async def is_user_globally_active(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
    ) -> bool:
        return await self._repo.is_user_globally_active(
            connection,
            user_id=user_id,
        )

    async def is_active_engagement_participant_user(
        self,
        connection: asyncpg.Connection,
        *,
        engagement_id: str,
        user_id: str,
    ) -> bool:
        return await self._repo.is_active_engagement_participant_user(
            connection,
            engagement_id=engagement_id,
            user_id=user_id,
        )

    async def list_active_engagement_participants(
        self,
        connection: asyncpg.Connection,
        *,
        engagement_id: str,
    ) -> list[dict[str, str | None]]:
        return await self._repo.list_active_engagement_participants(
            connection,
            engagement_id=engagement_id,
        )

    async def assert_task_entity_in_engagement_scope(
        self,
        connection: asyncpg.Connection,
        *,
        engagement_id: str,
        entity_type: str | None,
        entity_id: str | None,
    ) -> tuple[str, str]:
        normalized_entity_type = (entity_type or "engagement").strip().lower()
        normalized_entity_id = entity_id or engagement_id
        allowed = await self._repo.is_task_entity_in_engagement_scope(
            connection,
            engagement_id=engagement_id,
            entity_type=normalized_entity_type,
            entity_id=normalized_entity_id,
        )
        if not allowed:
            raise ValidationError("Task target must belong to the selected engagement.")
        return normalized_entity_type, normalized_entity_id

    async def build_engagement_task_request(
        self,
        connection: asyncpg.Connection,
        *,
        engagement: EngagementDetailRecord,
        engagement_id: str,
        task_request: EngagementTaskCreateRequest,
    ) -> CreateTaskRequest:
        if not engagement.workspace_id:
            raise ValidationError("The engagement must be linked to a workspace before tasks can be created.")

        entity_type, entity_id = await self.assert_task_entity_in_engagement_scope(
            connection,
            engagement_id=engagement_id,
            entity_type=task_request.entity_type,
            entity_id=task_request.entity_id,
        )

        if task_request.assignee_user_id:
            is_participant = await self.is_active_engagement_participant_user(
                connection,
                engagement_id=engagement_id,
                user_id=task_request.assignee_user_id,
            )
            if not is_participant:
                raise ValidationError("Assignee must be an active participant in the engagement.")

        return CreateTaskRequest(
            org_id=engagement.org_id,
            workspace_id=engagement.workspace_id,
            task_type_code=task_request.task_type_code,
            priority_code=task_request.priority_code,
            entity_type=entity_type,
            entity_id=entity_id,
            assignee_user_id=task_request.assignee_user_id,
            due_date=task_request.due_date,
            start_date=task_request.start_date,
            estimated_hours=task_request.estimated_hours,
            title=task_request.title,
            description=task_request.description,
            acceptance_criteria=task_request.acceptance_criteria,
            remediation_plan=task_request.remediation_plan,
        )

    async def assert_assessment_in_engagement_scope(
        self,
        connection: asyncpg.Connection,
        *,
        engagement_id: str,
        assessment_id: str,
    ) -> dict[str, str | None]:
        assessment_scope = await self._repo.get_assessment_in_engagement_scope(
            connection,
            engagement_id=engagement_id,
            assessment_id=assessment_id,
        )
        if not assessment_scope:
            raise ValidationError(
                "Assessment must belong to the same org, workspace, and framework scope as the selected engagement."
            )
        return assessment_scope

    async def list_assessments_in_engagement_scope(
        self,
        connection: asyncpg.Connection,
        *,
        engagement_id: str,
    ) -> list[dict[str, object | None]]:
        return await self._repo.list_assessments_in_engagement_scope(
            connection,
            engagement_id=engagement_id,
        )

    async def create_engagement_assessment(
        self,
        connection: asyncpg.Connection,
        *,
        engagement_id: str,
        tenant_key: str,
        user_id: str,
        request: EngagementAssessmentCreate,
        assessment_service: AssessmentService,
    ) -> AssessmentResponse:
        engagement = await self._repo.get_engagement_by_id(connection, engagement_id, tenant_key)
        if not engagement:
            raise ValidationError("Engagement not found")

        create_request = CreateAssessmentRequest(
            org_id=str(engagement.org_id),
            workspace_id=str(engagement.workspace_id) if engagement.workspace_id else None,
            framework_id=str(engagement.framework_id) if engagement.framework_id else None,
            assessment_type_code=request.assessment_type_code,
            lead_assessor_id=user_id,
            scheduled_start=request.scheduled_start.isoformat() if request.scheduled_start else None,
            scheduled_end=request.scheduled_end.isoformat() if request.scheduled_end else None,
            name=request.name,
            description=request.description,
        )

        return await assessment_service.create_assessment(
            user_id=user_id,
            tenant_key=tenant_key,
            request=create_request,
        )

    async def list_engagement_controls(
        self,
        connection: asyncpg.Connection,
        engagement_id: str,
        tenant_key: str,
        *,
        auditor_only: bool = False,
        viewer_membership_id: str | None = None,
    ) -> List[dict]:
        """List controls for an engagement with optional auditor evidence filtering.

        Args:
            connection: Active asyncpg database connection.
            engagement_id: UUID of the engagement.
            tenant_key: Tenant key for access control.
            auditor_only: When True, only count evidence marked auditor_access=TRUE.

        Returns:
            List of control dicts.
        """
        return await self._repo.list_engagement_controls(
            connection,
            engagement_id=engagement_id,
            tenant_key=tenant_key,
            auditor_only=auditor_only,
            viewer_membership_id=viewer_membership_id,
        )

    async def get_engagement(
        self, connection: asyncpg.Connection, engagement_id: str, tenant_key: str
    ) -> Optional[EngagementDetailRecord]:
        return await self._repo.get_engagement_by_id(connection, engagement_id, tenant_key)

    async def create_engagement(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        org_id: str,
        data: EngagementCreate,
        created_by: str,
    ) -> EngagementDetailRecord:
        now = datetime.now()
        eng_id = str(uuid4())
        
        # Create fact record
        await self._repo.create_engagement(
            connection,
            id=eng_id,
            tenant_key=tenant_key,
            org_id=org_id,
            engagement_code=data.engagement_code,
            framework_id=str(data.framework_id),
            framework_deployment_id=str(data.framework_deployment_id),
            status_code=data.status_code,
            target_completion_date=data.target_completion_date,
            created_by=created_by,
            now=now,
        )
        
        # Create EAV properties
        props = {
            "engagement_name": data.engagement_name,
            "auditor_firm": data.auditor_firm,
        }
        if data.engagement_type: props["engagement_type"] = data.engagement_type
        if data.scope_description: props["scope_description"] = data.scope_description
        if data.audit_period_start: props["audit_period_start"] = str(data.audit_period_start)
        if data.audit_period_end: props["audit_period_end"] = str(data.audit_period_end)
        if data.lead_grc_sme: props["lead_grc_sme"] = data.lead_grc_sme
        
        await self._repo.upsert_properties(connection, engagement_id=eng_id, tenant_key=tenant_key, properties=props, now=now)

        await self._audit_writer.write_entry(
            connection,
            AuditEntry(
                id=str(uuid4()),
                tenant_key=tenant_key,
                entity_type="engagement",
                entity_id=eng_id,
                event_type="engagement_created",
                event_category="engagement",
                occurred_at=now,
                actor_id=created_by,
                actor_type="user",
                properties={
                    "org_id": org_id,
                    "framework_id": str(data.framework_id),
                    "framework_deployment_id": str(data.framework_deployment_id),
                    "engagement_code": data.engagement_code,
                    "engagement_name": data.engagement_name,
                    "status_code": data.status_code,
                },
            ),
        )
        
        # Fetch full view
        return await self._repo.get_engagement_by_id(connection, eng_id, tenant_key)

    # Valid status transitions: current_status -> set of allowed next statuses
    ALLOWED_TRANSITIONS: dict[str, set[str]] = {
        "setup": {"active"},
        "active": {"review"},
        "review": {"completed", "active"},  # allow sending back to active
        "completed": {"closed"},
        "closed": set(),  # terminal state
    }

    async def update_engagement(
        self,
        connection: asyncpg.Connection,
        engagement_id: str,
        tenant_key: str,
        *,
        data: EngagementUpdate,
        updated_by: str,
    ) -> Optional[EngagementDetailRecord]:
        """Update engagement fields and/or transition status.

        Validates status transitions against the allowed state machine.
        """
        now = datetime.now()

        # Validate status transition if status_code is being changed
        if data.status_code:
            current = await self._repo.get_engagement_by_id(connection, engagement_id, tenant_key)
            if not current:
                raise ValueError(f"Engagement {engagement_id} not found")
            current_status = current.status_code
            allowed = self.ALLOWED_TRANSITIONS.get(current_status, set())
            if data.status_code != current_status and data.status_code not in allowed:
                raise ValueError(
                    f"Invalid status transition: '{current_status}' → '{data.status_code}'. "
                    f"Allowed: {', '.join(sorted(allowed)) if allowed else 'none (terminal state)'}"
                )

        # Update fact table (tenant_key enforced)
        await self._repo.update_engagement(
            connection,
            engagement_id,
            tenant_key,
            status_code=data.status_code,
            target_completion_date=data.target_completion_date,
            updated_by=updated_by,
            now=now,
        )
        
        # Update EAV properties
        props = {}
        if data.engagement_name is not None: props["engagement_name"] = data.engagement_name
        if data.auditor_firm is not None: props["auditor_firm"] = data.auditor_firm
        if data.scope_description is not None: props["scope_description"] = data.scope_description
        if data.audit_period_start is not None: props["audit_period_start"] = str(data.audit_period_start)
        if data.audit_period_end is not None: props["audit_period_end"] = str(data.audit_period_end)
        if data.lead_grc_sme is not None: props["lead_grc_sme"] = data.lead_grc_sme
        
        if props:
            await self._repo.upsert_properties(connection, engagement_id=engagement_id, tenant_key=tenant_key, properties=props, now=now)

        await self._audit_writer.write_entry(
            connection,
            AuditEntry(
                id=str(uuid4()),
                tenant_key=tenant_key,
                entity_type="engagement",
                entity_id=engagement_id,
                event_type="engagement_updated",
                event_category="engagement",
                occurred_at=now,
                actor_id=updated_by,
                actor_type="user",
                properties={
                    "status_code": data.status_code,
                    "target_completion_date": str(data.target_completion_date) if data.target_completion_date else None,
                    "engagement_name": data.engagement_name,
                    "auditor_firm": data.auditor_firm,
                    "scope_description": data.scope_description,
                },
            ),
        )
            
        return await self._repo.get_engagement_by_id(connection, engagement_id, tenant_key)

    async def invite_auditor(
        self,
        connection: asyncpg.Connection,
        *,
        engagement_id: str,
        tenant_key: str,
        email: str,
        expires_in_days: int = 30,
        platform_base_url: str,
    ) -> tuple[str, datetime]:
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        expires_at = datetime.now() + timedelta(days=expires_in_days)

        token = await self._repo.create_auditor_token(
            connection,
            engagement_id=engagement_id,
            tenant_key=tenant_key,
            auditor_email=email,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        if not token:
            raise ValueError("Engagement not found in this tenant")
        await self._audit_writer.write_entry(
            connection,
            AuditEntry(
                id=str(uuid4()),
                tenant_key=tenant_key,
                entity_type="engagement",
                entity_id=engagement_id,
                event_type="engagement_auditor_invited",
                event_category="engagement",
                occurred_at=datetime.now(),
                actor_type="user",
                properties={
                    "auditor_email": email,
                    "token_id": token.id,
                    "expires_at": expires_at.isoformat(),
                },
            ),
        )
        invite_url = f"{platform_base_url}/audit-workspace/verify?token={raw_token}"
        return invite_url, expires_at

    async def list_access_tokens(
        self,
        connection: asyncpg.Connection,
        engagement_id: str,
        tenant_key: str,
        *,
        include_revoked: bool = True,
    ) -> List[AuditAccessTokenRecord]:
        return await self._repo.list_access_tokens(connection, engagement_id, tenant_key, include_revoked=include_revoked)

    async def revoke_access_token(
        self,
        connection: asyncpg.Connection,
        token_id: str,
        tenant_key: str,
        *,
        revoked_by: str,
    ) -> bool:
        success = await self._repo.revoke_access_token(connection, token_id, tenant_key, revoked_by=revoked_by)
        if success:
            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()),
                    tenant_key=tenant_key,
                    entity_type="engagement_access_token",
                    entity_id=token_id,
                    event_type="engagement_access_token_revoked",
                    event_category="engagement",
                    occurred_at=datetime.now(),
                    actor_id=revoked_by,
                    actor_type="user",
                    properties={},
                ),
            )
        return success

    async def list_auditor_requests(
        self,
        connection: asyncpg.Connection,
        engagement_id: str,
        tenant_key: str,
        *,
        status: Optional[str] = None,
    ) -> List[AuditorRequestRecord]:
        return await self._repo.list_auditor_requests(connection, engagement_id, tenant_key, status=status)

    async def fulfill_auditor_request(
        self,
        connection: asyncpg.Connection,
        request_id: str,
        tenant_key: str,
        *,
        action: str,
        fulfilled_by: str,
        attachment_ids: Optional[list[str]] = None,
        response_notes: Optional[str] = None,
    ) -> bool:
        if action == "fulfill" and not attachment_ids:
            raise ValueError("attachment_ids is required when fulfilling an evidence request")
        async with connection.transaction():
            success = await self._repo.fulfill_auditor_request(
                connection, request_id, tenant_key,
                action=action,
                fulfilled_by=fulfilled_by,
                attachment_ids=attachment_ids,
                response_notes=response_notes,
                now=datetime.now(),
            )
            if success:
                await self._audit_writer.write_entry(
                    connection,
                    AuditEntry(
                        id=str(uuid4()),
                        tenant_key=tenant_key,
                        entity_type="engagement_evidence_request",
                        entity_id=request_id,
                        event_type="engagement_evidence_request_reviewed",
                        event_category="engagement",
                        occurred_at=datetime.now(),
                        actor_id=fulfilled_by,
                        actor_type="user",
                        properties={
                            "action": action,
                            "attachment_ids": attachment_ids,
                            "response_notes": response_notes,
                        },
                    ),
                )
            return success

    async def revoke_auditor_request_access(
        self,
        connection: asyncpg.Connection,
        request_id: str,
        tenant_key: str,
        *,
        revoked_by: str,
        response_notes: Optional[str] = None,
    ) -> bool:
        async with connection.transaction():
            success = await self._repo.revoke_auditor_request_access(
                connection,
                request_id,
                tenant_key,
                revoked_by=revoked_by,
                response_notes=response_notes,
                now=datetime.now(),
            )
            if success:
                await self._audit_writer.write_entry(
                    connection,
                    AuditEntry(
                        id=str(uuid4()),
                        tenant_key=tenant_key,
                        entity_type="engagement_evidence_request",
                        entity_id=request_id,
                        event_type="engagement_evidence_access_revoked",
                        event_category="engagement",
                        occurred_at=datetime.now(),
                        actor_id=revoked_by,
                        actor_type="user",
                        properties={
                            "response_notes": response_notes,
                        },
                    ),
                )
            return success

    async def verify_control(
        self,
        connection: asyncpg.Connection,
        *,
        engagement_id: str,
        tenant_key: str,
        control_id: str,
        email: str,
        outcome: str,
        observations: Optional[str] = None,
        finding_details: Optional[str] = None,
    ) -> bool:
        token = await self._get_or_create_auditor_token(
            connection,
            engagement_id=engagement_id,
            tenant_key=tenant_key,
            email=email,
        )
        if not token:
            return False

        success = await self._repo.upsert_control_verification(
            connection,
            engagement_id=engagement_id,
            tenant_key=tenant_key,
            control_id=control_id,
            token_id=token.id,
            outcome=outcome,
            observations=observations,
            finding_details=finding_details,
            now=datetime.now()
        )
        if success:
            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()),
                    tenant_key=tenant_key,
                    entity_type="engagement_control_verification",
                    entity_id=control_id,
                    event_type="engagement_control_verified",
                    event_category="engagement",
                    occurred_at=datetime.now(),
                    actor_type="auditor",
                    properties={
                        "engagement_id": engagement_id,
                        "auditor_email": email,
                        "outcome": outcome,
                    },
                ),
            )
        return success

    async def create_auditor_request(
        self,
        connection: asyncpg.Connection,
        *,
        engagement_id: str,
        tenant_key: str,
        control_id: Optional[str],
        email: str,
        description: str,
        task_id: Optional[str] = None,
    ) -> str:
        normalized_description = " ".join(description.split())
        if not normalized_description:
            raise ValueError("A request description is required")

        token = await self._get_or_create_auditor_token(
            connection,
            engagement_id=engagement_id,
            tenant_key=tenant_key,
            email=email,
        )
        if not token:
            raise ValueError("Auditor not found for this engagement")

        existing_request_id = await self._repo.get_open_auditor_request_id(
            connection,
            engagement_id=engagement_id,
            token_id=token.id,
            control_id=control_id,
            task_id=task_id,
        )
        if existing_request_id:
            raise ValueError("An open evidence request already exists for this target")

        latest_dismissed_description = await self._repo.get_latest_dismissed_auditor_request_description(
            connection,
            engagement_id=engagement_id,
            token_id=token.id,
            control_id=control_id,
        )
        latest_dismissed_at = await self._repo.get_latest_dismissed_auditor_request_at(
            connection,
            engagement_id=engagement_id,
            token_id=token.id,
            control_id=control_id,
        )
        if latest_dismissed_at:
            retry_allowed_at = latest_dismissed_at + self.EVIDENCE_REQUEST_RETRY_COOLDOWN
            if retry_allowed_at > datetime.now():
                raise ValueError("Please wait before resubmitting a dismissed evidence request")
        if latest_dismissed_description:
            normalized_previous = " ".join(str(latest_dismissed_description).split())
            if normalized_previous and normalized_previous.casefold() == normalized_description.casefold():
                raise ValueError("A dismissed evidence request requires fresh justification before resubmission")

        try:
            request_id = await self._repo.create_auditor_request(
                connection,
                engagement_id=engagement_id,
                tenant_key=tenant_key,
                token_id=token.id,
                control_id=control_id,
                task_id=task_id,
                description=normalized_description,
                now=datetime.now()
            )
        except asyncpg.UniqueViolationError as exc:
            raise ValueError("An open evidence request already exists for this control") from exc
        await self._audit_writer.write_entry(
            connection,
            AuditEntry(
                id=str(uuid4()),
                tenant_key=tenant_key,
                entity_type="engagement_evidence_request",
                entity_id=request_id,
                event_type="engagement_evidence_request_created",
                event_category="engagement",
                occurred_at=datetime.now(),
                actor_type="auditor",
                properties={
                    "engagement_id": engagement_id,
                    "control_id": control_id,
                    "task_id": task_id,
                    "auditor_email": email,
                    "description": normalized_description,
                },
            ),
        )
        return request_id

    async def get_control_detail(
        self,
        connection: asyncpg.Connection,
        engagement_id: str,
        tenant_key: str,
        control_id: str,
        *,
        auditor_only: bool = False,
        viewer_membership_id: str | None = None,
    ) -> dict:
        """Get control verification status and evidence library."""
        verification = await self._repo.get_control_verification(connection, engagement_id, tenant_key, control_id)
        evidence = await self._repo.list_control_evidence(
            connection,
            engagement_id=engagement_id,
            tenant_key=tenant_key,
            control_id=control_id,
            auditor_only=auditor_only,
            viewer_membership_id=viewer_membership_id,
        )
        
        return {
            "verification": verification,
            "evidence": evidence
        }
