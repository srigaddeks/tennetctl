from __future__ import annotations
import uuid
import datetime
from importlib import import_module
from .models import ApprovalRecord
from .repository import ApprovalRepository
from .schemas import ApprovalListResponse, ApprovalResponse, ApproveRequest, RejectRequest

_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_errors_module = import_module("backend.01_core.errors")
_audit_module = import_module("backend.01_core.audit")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_constants_module = import_module("backend.20_ai.constants")

get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
ForbiddenError = _errors_module.AuthorizationError
ValidationError = _errors_module.ValidationError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
AIAuditEventType = _constants_module.AIAuditEventType
require_permission = _perm_check_module.require_permission

async def _execute_approved_tool(*, tool_name: str, payload: dict, caller_id: str, tenant_key: str, svc_kwargs: dict):
    """Execute the actual GRC write operation after approval."""
    _fw_mod = import_module("backend.05_grc_library.02_frameworks.service")
    _fw_schema = import_module("backend.05_grc_library.02_frameworks.schemas")
    _req_mod = import_module("backend.05_grc_library.04_requirements.service")
    _req_schema = import_module("backend.05_grc_library.04_requirements.schemas")
    _ctrl_mod = import_module("backend.05_grc_library.05_controls.service")
    _ctrl_schema = import_module("backend.05_grc_library.05_controls.schemas")
    _risk_mod = import_module("backend.06_risk_registry.02_risks.service")
    _risk_schema = import_module("backend.06_risk_registry.02_risks.schemas")
    _cm_mod = import_module("backend.06_risk_registry.05_control_mappings.service")
    _cm_schema = import_module("backend.06_risk_registry.05_control_mappings.schemas")
    _task_mod = import_module("backend.07_tasks.02_tasks.service")
    _task_schema = import_module("backend.07_tasks.02_tasks.schemas")

    if tool_name == "grc_create_framework":
        svc = _fw_mod.FrameworkService(**svc_kwargs)
        req = _fw_schema.CreateFrameworkRequest(**payload)
        result = await svc.create_framework(user_id=caller_id, tenant_key=tenant_key, request=req)
        return {"created": "framework", "id": str(result.id), "name": result.name}

    elif tool_name == "grc_create_requirement":
        svc = _req_mod.RequirementService(**svc_kwargs)
        p = dict(payload)
        framework_id = p.pop("framework_id")
        req = _req_schema.CreateRequirementRequest(**p)
        result = await svc.create_requirement(user_id=caller_id, tenant_key=tenant_key, framework_id=framework_id, request=req)
        return {"created": "requirement", "id": str(result.id), "name": result.name}

    elif tool_name == "grc_bulk_create_requirements":
        svc = _req_mod.RequirementService(**svc_kwargs)
        framework_id = payload["framework_id"]
        results = []
        for r in payload.get("requirements", []):
            req = _req_schema.CreateRequirementRequest(**r)
            created = await svc.create_requirement(user_id=caller_id, tenant_key=tenant_key, framework_id=framework_id, request=req)
            results.append({"id": str(created.id), "name": created.name})
        return {"created": "requirements", "count": len(results), "items": results}

    elif tool_name == "grc_create_control":
        svc = _ctrl_mod.ControlService(**svc_kwargs)
        p = dict(payload)
        framework_id = p.pop("framework_id")
        req = _ctrl_schema.CreateControlRequest(**p)
        result = await svc.create_control(user_id=caller_id, tenant_key=tenant_key, framework_id=framework_id, request=req)
        return {"created": "control", "id": str(result.id), "name": result.name}

    elif tool_name == "grc_bulk_create_controls":
        svc = _ctrl_mod.ControlService(**svc_kwargs)
        framework_id = payload["framework_id"]
        results = []
        for c in payload.get("controls", []):
            req = _ctrl_schema.CreateControlRequest(**c)
            created = await svc.create_control(user_id=caller_id, tenant_key=tenant_key, framework_id=framework_id, request=req)
            results.append({"id": str(created.id), "name": created.name})
        return {"created": "controls", "count": len(results), "items": results}

    elif tool_name == "grc_create_risk":
        svc = _risk_mod.RiskService(**svc_kwargs)
        req = _risk_schema.CreateRiskRequest(**payload)
        result = await svc.create_risk(user_id=caller_id, tenant_key=tenant_key, request=req)
        return {"created": "risk", "id": str(result.id), "risk_code": result.risk_code}

    elif tool_name == "grc_bulk_create_risks":
        svc = _risk_mod.RiskService(**svc_kwargs)
        org_id = payload["org_id"]
        workspace_id = payload["workspace_id"]
        results = []
        for r in payload.get("risks", []):
            req = _risk_schema.CreateRiskRequest(org_id=org_id, workspace_id=workspace_id, **r)
            created = await svc.create_risk(user_id=caller_id, tenant_key=tenant_key, request=req)
            results.append({"id": str(created.id), "risk_code": created.risk_code})
        return {"created": "risks", "count": len(results), "items": results}

    elif tool_name == "grc_create_task":
        svc = _task_mod.TaskService(**svc_kwargs)
        req = _task_schema.CreateTaskRequest(**payload)
        result = await svc.create_task(user_id=caller_id, tenant_key=tenant_key, request=req)
        return {"created": "task", "id": str(result.id), "title": result.title}

    elif tool_name == "grc_bulk_create_tasks":
        svc = _task_mod.TaskService(**svc_kwargs)
        org_id = payload["org_id"]
        workspace_id = payload["workspace_id"]
        entity_type = payload.get("entity_type")
        entity_id = payload.get("entity_id")
        results = []
        for t in payload.get("tasks", []):
            req = _task_schema.CreateTaskRequest(
                org_id=org_id, workspace_id=workspace_id,
                entity_type=entity_type, entity_id=entity_id,
                **t,
            )
            created = await svc.create_task(user_id=caller_id, tenant_key=tenant_key, request=req)
            results.append({"id": str(created.id), "title": created.title})
        return {"created": "tasks", "count": len(results), "items": results}

    elif tool_name == "grc_map_control_to_risk":
        svc = _cm_mod.ControlMappingService(**svc_kwargs)
        risk_id = payload["risk_id"]
        link_type = payload.get("effectiveness_rating", "mitigating")
        # Map effectiveness_rating values to link_type enum
        if link_type not in ("mitigating", "compensating", "related"):
            link_type = "mitigating"
        req = _cm_schema.CreateControlMappingRequest(
            control_id=payload["control_id"],
            link_type=link_type,
            notes=payload.get("notes"),
        )
        result = await svc.create_control_mapping(user_id=caller_id, risk_id=risk_id, request=req)
        return {"created": "control_risk_mapping", "id": str(result.id)}

    else:
        raise ValueError(f"Unknown write tool: {tool_name}")


def _to_response(r: ApprovalRecord, is_overdue: bool = False) -> ApprovalResponse:
    return ApprovalResponse(id=r.id, tenant_key=r.tenant_key, requester_id=r.requester_id,
        org_id=r.org_id, approver_id=r.approver_id, status_code=r.status_code,
        tool_name=r.tool_name, tool_category=r.tool_category, entity_type=r.entity_type,
        operation=r.operation, payload_json=r.payload_json, diff_json=r.diff_json,
        rejection_reason=r.rejection_reason, expires_at=r.expires_at,
        approved_at=r.approved_at, executed_at=r.executed_at,
        created_at=r.created_at, updated_at=r.updated_at, is_overdue=is_overdue)

@instrument_class_methods(namespace="ai.approvals.service", logger_name="backend.ai.approvals.instrumentation")
class ApprovalService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = ApprovalRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.ai.approvals")
        expiry_hours = getattr(settings, "ai_approval_expiry_hours", 72)
        self._expiry_hours = expiry_hours

    async def list_approvals(self, *, caller_id: str, tenant_key: str,
            status_code: str | None = None, limit: int = 50, offset: int = 0) -> ApprovalListResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, caller_id, "ai_copilot.view")
            rows = await self._repository.list_approvals(conn, tenant_key=tenant_key,
                requester_id=caller_id, status_code=status_code, limit=limit, offset=offset)
        items = [ApprovalResponse(**{k: v for k, v in r.items() if k in ApprovalResponse.model_fields}) for r in rows]
        return ApprovalListResponse(items=items, total=len(items))

    async def get_approval(self, *, approval_id: str, tenant_key: str, caller_id: str) -> ApprovalResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, caller_id, "ai_copilot.view")
            record = await self._repository.get_approval(conn, approval_id=approval_id, tenant_key=tenant_key)
            if not record:
                raise NotFoundError(f"Approval {approval_id} not found")
            if record.requester_id != caller_id:
                await require_permission(conn, caller_id, "ai_copilot.approve")
        return _to_response(record)

    async def approve(self, *, approval_id: str, tenant_key: str, caller_id: str) -> ApprovalResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, caller_id, "ai_copilot.approve")
            record = await self._repository.get_approval(conn, approval_id=approval_id, tenant_key=tenant_key)
            if not record:
                raise NotFoundError(f"Approval {approval_id} not found")
            if record.status_code != "pending":
                raise ValidationError(f"Approval is already {record.status_code}")
            updated = await self._repository.transition_status(conn, approval_id=approval_id,
                new_status="approved", approver_id=caller_id, rejection_reason=None)
            await self._audit_writer.write_entry(conn, AuditEntry(
                id=str(uuid.uuid4()), tenant_key=tenant_key, entity_type="approval",
                entity_id=approval_id, event_type=AIAuditEventType.APPROVAL_APPROVED,
                event_category="ai", actor_id=caller_id, actor_type="user",
                properties={"tool_name": record.tool_name},
                occurred_at=datetime.datetime.utcnow()))

        # Execute the approved action
        svc_kwargs = dict(settings=self._settings, database_pool=self._database_pool, cache=self._cache)
        execution_result = None
        try:
            execution_result = await _execute_approved_tool(
                tool_name=record.tool_name,
                payload=record.payload_json or {},
                caller_id=caller_id,
                tenant_key=tenant_key,
                svc_kwargs=svc_kwargs,
            )
        except Exception as exc:
            self._logger.warning("Approval %s execution failed: %s", approval_id, exc)
            execution_result = {"error": str(exc)}

        # Mark executed
        async with self._database_pool.acquire() as conn:
            final = await self._repository.transition_status(conn, approval_id=approval_id,
                new_status="executed", approver_id=caller_id, rejection_reason=None)

        resp = _to_response(final)
        resp.execution_result = execution_result
        return resp

    async def reject(self, *, approval_id: str, tenant_key: str, caller_id: str, reason: str) -> ApprovalResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, caller_id, "ai_copilot.approve")
            record = await self._repository.get_approval(conn, approval_id=approval_id, tenant_key=tenant_key)
            if not record:
                raise NotFoundError(f"Approval {approval_id} not found")
            if record.status_code != "pending":
                raise ValidationError(f"Approval is already {record.status_code}")
            updated = await self._repository.transition_status(conn, approval_id=approval_id,
                new_status="rejected", approver_id=caller_id, rejection_reason=reason)
            await self._audit_writer.write_entry(conn, AuditEntry(
                id=str(uuid.uuid4()), tenant_key=tenant_key, entity_type="approval",
                entity_id=approval_id, event_type=AIAuditEventType.APPROVAL_REJECTED,
                event_category="ai", actor_id=caller_id, actor_type="user",
                properties={"tool_name": record.tool_name, "reason": reason},
                occurred_at=datetime.datetime.utcnow()))
        return _to_response(updated)
