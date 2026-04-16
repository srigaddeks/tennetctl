from __future__ import annotations

import json
import uuid
from importlib import import_module
from typing import Any

import asyncpg

from .models import (
    QuestionnaireAssignmentRecord,
    QuestionnaireRecord,
    QuestionnaireResponseRecord,
    QuestionnaireVersionRecord,
)

SCHEMA = '"14_risk_registry"'
instrument_class_methods = import_module(
    "backend.01_core.telemetry"
).instrument_class_methods

# Explicit column lists — protects against extra DB-convention columns (is_disabled, etc.)
_Q_COLS = """
    id, tenant_key, questionnaire_code, name, description,
    intended_scope, current_status, latest_version_number,
    active_version_id, is_active, is_deleted,
    created_at, updated_at, created_by, updated_by
"""

_V_COLS = """
    id, questionnaire_id, version_number, version_status, content_jsonb,
    version_label, change_notes, published_at, published_by, 
    created_at, updated_at, created_by, updated_by
"""

_A_COLS = """
    id, tenant_key, assignment_scope, org_id, workspace_id,
    questionnaire_version_id, is_active, 
    created_at, updated_at, created_by, updated_by
"""

_R_COLS = """
    id, tenant_key, org_id, workspace_id, questionnaire_version_id,
    response_status, answers_jsonb, completed_at, completed_by,
    created_at, updated_at, created_by, updated_by
"""


@instrument_class_methods(
    namespace="risk.questionnaires.repository",
    logger_name="backend.risk.questionnaires.repository.instrumentation",
)
class QuestionnairesRepository:
    # --- QUESTIONNAIRES ---

    async def list_questionnaires(
        self, connection: asyncpg.Connection, tenant_key: str
    ) -> list[QuestionnaireRecord]:
        rows = await connection.fetch(
            f"""
            SELECT {_Q_COLS} FROM {SCHEMA}."37_fct_risk_questionnaires"
            WHERE tenant_key = $1 AND is_deleted = FALSE
            ORDER BY created_at DESC
            """,
            tenant_key,
        )
        return [QuestionnaireRecord(**dict(r)) for r in rows]

    async def list_active_questionnaires(
        self, connection: asyncpg.Connection, tenant_key: str
    ) -> list[QuestionnaireRecord]:
        rows = await connection.fetch(
            f"""
            SELECT {_Q_COLS} FROM {SCHEMA}."37_fct_risk_questionnaires"
            WHERE tenant_key = $1 AND is_deleted = FALSE AND is_active = TRUE
            ORDER BY created_at DESC
            """,
            tenant_key,
        )
        return [QuestionnaireRecord(**dict(r)) for r in rows]

    async def get_questionnaire(
        self,
        connection: asyncpg.Connection,
        questionnaire_id: uuid.UUID,
        tenant_key: str,
    ) -> QuestionnaireRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT {_Q_COLS} FROM {SCHEMA}."37_fct_risk_questionnaires"
            WHERE id = $1 AND tenant_key = $2 AND is_deleted = FALSE
            """,
            questionnaire_id,
            tenant_key,
        )
        if not row:
            return None
        return QuestionnaireRecord(**dict(row))

    async def create_questionnaire(
        self, connection: asyncpg.Connection, *, record: QuestionnaireRecord
    ) -> None:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."37_fct_risk_questionnaires" (
                id, tenant_key, questionnaire_code, name, description, intended_scope, current_status, latest_version_number,
                active_version_id, is_active, is_deleted, created_at, updated_at, created_by, updated_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
            """,
            record.id,
            record.tenant_key,
            record.questionnaire_code,
            record.name,
            record.description,
            record.intended_scope,
            record.current_status,
            record.latest_version_number,
            record.active_version_id,
            record.is_active,
            record.is_deleted,
            record.created_at,
            record.updated_at,
            record.created_by,
            record.updated_by,
        )

    async def update_questionnaire_status(
        self,
        connection: asyncpg.Connection,
        questionnaire_id: uuid.UUID,
        new_status: str,
        active_version_id: uuid.UUID | None,
    ) -> None:
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."37_fct_risk_questionnaires"
            SET current_status = $2, active_version_id = $3, updated_at = NOW()
            WHERE id = $1
            """,
            questionnaire_id,
            new_status,
            active_version_id,
        )

    async def increment_questionnaire_version(
        self,
        connection: asyncpg.Connection,
        questionnaire_id: uuid.UUID,
        new_version_number: int,
    ) -> None:
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."37_fct_risk_questionnaires"
            SET latest_version_number = $2, updated_at = NOW()
            WHERE id = $1
            """,
            questionnaire_id,
            new_version_number,
        )

    # --- VERSIONS ---

    async def list_versions(
        self, connection: asyncpg.Connection, questionnaire_id: uuid.UUID
    ) -> list[QuestionnaireVersionRecord]:
        rows = await connection.fetch(
            f"""
            SELECT {_V_COLS} FROM {SCHEMA}."38_vrs_risk_questionnaire_versions"
            WHERE questionnaire_id = $1
            ORDER BY version_number DESC
            """,
            questionnaire_id,
        )
        results = []
        for row in rows:
            d = dict(row)
            d["content_jsonb"] = (
                json.loads(d["content_jsonb"])
                if isinstance(d["content_jsonb"], str)
                else d["content_jsonb"]
            )
            results.append(QuestionnaireVersionRecord(**d))
        return results

    async def get_version(
        self, connection: asyncpg.Connection, version_id: uuid.UUID
    ) -> QuestionnaireVersionRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT {_V_COLS} FROM {SCHEMA}."38_vrs_risk_questionnaire_versions"
            WHERE id = $1
            """,
            version_id,
        )
        if not row:
            return None
        d = dict(row)
        d["content_jsonb"] = (
            json.loads(d["content_jsonb"])
            if isinstance(d["content_jsonb"], str)
            else d["content_jsonb"]
        )
        return QuestionnaireVersionRecord(**d)

    async def get_latest_version(
        self, connection: asyncpg.Connection, questionnaire_id: uuid.UUID
    ) -> QuestionnaireVersionRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT {_V_COLS} FROM {SCHEMA}."38_vrs_risk_questionnaire_versions"
            WHERE questionnaire_id = $1
            ORDER BY version_number DESC
            LIMIT 1
            """,
            questionnaire_id,
        )
        if not row:
            return None
        d = dict(row)
        d["content_jsonb"] = (
            json.loads(d["content_jsonb"])
            if isinstance(d["content_jsonb"], str)
            else d["content_jsonb"]
        )
        return QuestionnaireVersionRecord(**d)

    async def create_version(
        self, connection: asyncpg.Connection, *, record: QuestionnaireVersionRecord
    ) -> None:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."38_vrs_risk_questionnaire_versions" (
                id, questionnaire_id, version_number, version_status, content_jsonb, version_label, change_notes,
                published_at, published_by, created_at, updated_at, created_by, updated_by
            ) VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8, $9, $10, $11, $12, $13)
            """,
            record.id,
            record.questionnaire_id,
            record.version_number,
            record.version_status,
            json.dumps(record.content_jsonb),
            record.version_label,
            record.change_notes,
            record.published_at,
            record.published_by,
            record.created_at,
            record.updated_at,
            record.created_by,
            record.updated_by,
        )

    async def update_version_status(
        self,
        connection: asyncpg.Connection,
        version_id: uuid.UUID,
        version_status: str,
        published_at: Any,
        published_by: uuid.UUID | None,
    ) -> None:
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."38_vrs_risk_questionnaire_versions"
            SET version_status = $2, published_at = $3, published_by = $4, updated_at = NOW()
            WHERE id = $1
            """,
            version_id,
            version_status,
            published_at,
            published_by,
        )

    async def update_version_content(
        self,
        connection: asyncpg.Connection,
        version_id: uuid.UUID,
        content_jsonb: dict[str, Any],
    ) -> None:
        content_json_str = json.dumps(content_jsonb)
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."38_vrs_risk_questionnaire_versions"
            SET content_jsonb = $2::jsonb, updated_at = NOW()
            WHERE id = $1
            """,
            version_id,
            content_json_str,
        )

    # --- ASSIGNMENTS ---

    async def get_assignment(
        self,
        connection: asyncpg.Connection,
        tenant_key: str,
        assignment_scope: str,
        org_id: uuid.UUID | None,
        workspace_id: uuid.UUID | None,
        questionnaire_id: uuid.UUID,
    ) -> QuestionnaireAssignmentRecord | None:
        query = f"""
            SELECT a.* FROM {SCHEMA}."39_lnk_risk_questionnaire_assignments" a
            JOIN {SCHEMA}."38_vrs_risk_questionnaire_versions" v ON a.questionnaire_version_id = v.id
            WHERE a.tenant_key = $1 AND a.assignment_scope = $2
              AND a.is_active = TRUE AND v.questionnaire_id = $3
        """
        args: list[Any] = [tenant_key, assignment_scope, questionnaire_id]

        query += " AND a.org_id = $4" if org_id else " AND a.org_id IS NULL"
        if org_id:
            args.append(org_id)

        query += (
            f" AND a.workspace_id = ${len(args) + 1}"
            if workspace_id
            else " AND a.workspace_id IS NULL"
        )
        if workspace_id:
            args.append(workspace_id)

        query += " ORDER BY a.created_at DESC LIMIT 1"
        row = await connection.fetchrow(query, *args)
        if not row:
            return None
        return QuestionnaireAssignmentRecord(**dict(row))

    async def list_assignments_for_tenant(
        self, connection: asyncpg.Connection, tenant_key: str
    ) -> list[QuestionnaireAssignmentRecord]:
        rows = await connection.fetch(
            f"""
            SELECT {_A_COLS} FROM {SCHEMA}."39_lnk_risk_questionnaire_assignments"
            WHERE tenant_key = $1 AND is_active = TRUE
            """,
            tenant_key,
        )
        return [QuestionnaireAssignmentRecord(**dict(r)) for r in rows]

    async def deactivate_old_assignments(
        self,
        connection: asyncpg.Connection,
        tenant_key: str,
        assignment_scope: str,
        org_id: uuid.UUID | None,
        workspace_id: uuid.UUID | None,
        questionnaire_id: uuid.UUID,
    ) -> None:
        query = f"""
            UPDATE {SCHEMA}."39_lnk_risk_questionnaire_assignments" a
            SET is_active = FALSE, updated_at = NOW()
            FROM {SCHEMA}."38_vrs_risk_questionnaire_versions" v
            WHERE a.questionnaire_version_id = v.id
              AND v.questionnaire_id = $1
              AND a.tenant_key = $2
              AND a.assignment_scope = $3
              AND a.is_active = TRUE
        """
        args: list[Any] = [questionnaire_id, tenant_key, assignment_scope]

        query += " AND a.org_id = $4" if org_id else " AND a.org_id IS NULL"
        if org_id:
            args.append(org_id)

        query += (
            f" AND a.workspace_id = ${len(args) + 1}"
            if workspace_id
            else " AND a.workspace_id IS NULL"
        )
        if workspace_id:
            args.append(workspace_id)

        await connection.execute(query, *args)

    async def upsert_assignment(
        self,
        connection: asyncpg.Connection,
        *,
        record: QuestionnaireAssignmentRecord,
        questionnaire_id: uuid.UUID,
    ) -> None:
        await self.deactivate_old_assignments(
            connection,
            record.tenant_key,
            record.assignment_scope,
            record.org_id,
            record.workspace_id,
            questionnaire_id,
        )
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."39_lnk_risk_questionnaire_assignments" (
                id, tenant_key, assignment_scope, org_id, workspace_id, questionnaire_version_id, is_active, 
                created_at, updated_at, created_by, updated_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """,
            record.id,
            record.tenant_key,
            record.assignment_scope,
            record.org_id,
            record.workspace_id,
            record.questionnaire_version_id,
            record.is_active,
            record.created_at,
            record.updated_at,
            record.created_by,
            record.updated_by,
        )

    # --- RESPONSES ---

    async def get_response(
        self,
        connection: asyncpg.Connection,
        tenant_key: str,
        org_id: uuid.UUID,
        workspace_id: uuid.UUID | None,
        questionnaire_version_id: uuid.UUID,
    ) -> QuestionnaireResponseRecord | None:
        query = f"""
            SELECT {_R_COLS} FROM {SCHEMA}."41_fct_risk_questionnaire_responses"
            WHERE tenant_key = $1 AND org_id = $2
              AND questionnaire_version_id = $3
        """
        args: list[Any] = [tenant_key, org_id, questionnaire_version_id]

        query += (
            " AND workspace_id = $4" if workspace_id else " AND workspace_id IS NULL"
        )
        if workspace_id:
            args.append(workspace_id)

        query += " ORDER BY created_at DESC LIMIT 1"
        row = await connection.fetchrow(query, *args)
        if not row:
            return None
        d = dict(row)
        d["answers_jsonb"] = (
            json.loads(d["answers_jsonb"])
            if isinstance(d["answers_jsonb"], str)
            else d["answers_jsonb"]
        )
        return QuestionnaireResponseRecord(**d)

    async def get_latest_response_for_scope(
        self,
        connection: asyncpg.Connection,
        tenant_key: str,
        org_id: uuid.UUID,
        workspace_id: uuid.UUID | None,
        questionnaire_id: uuid.UUID,
    ) -> QuestionnaireResponseRecord | None:
        query = f"""
            SELECT r.* FROM {SCHEMA}."41_fct_risk_questionnaire_responses" r
            JOIN {SCHEMA}."38_vrs_risk_questionnaire_versions" v ON r.questionnaire_version_id = v.id
            WHERE r.tenant_key = $1 AND r.org_id = $2 AND v.questionnaire_id = $3
        """
        args: list[Any] = [tenant_key, org_id, questionnaire_id]

        query += (
            " AND r.workspace_id = $4"
            if workspace_id
            else " AND r.workspace_id IS NULL"
        )
        if workspace_id:
            args.append(workspace_id)

        query += " ORDER BY r.created_at DESC LIMIT 1"
        row = await connection.fetchrow(query, *args)
        if not row:
            return None
        d = dict(row)
        d["answers_jsonb"] = (
            json.loads(d["answers_jsonb"])
            if isinstance(d["answers_jsonb"], str)
            else d["answers_jsonb"]
        )
        return QuestionnaireResponseRecord(**d)

    async def create_response(
        self, connection: asyncpg.Connection, *, record: QuestionnaireResponseRecord
    ) -> None:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."41_fct_risk_questionnaire_responses" (
                id, tenant_key, org_id, workspace_id, questionnaire_version_id, response_status, answers_jsonb, completed_at,
                completed_by, created_at, updated_at, created_by, updated_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8, $9, $10, $11, $12, $13)
            """,
            record.id,
            record.tenant_key,
            record.org_id,
            record.workspace_id,
            record.questionnaire_version_id,
            record.response_status,
            json.dumps(record.answers_jsonb),
            record.completed_at,
            record.completed_by,
            record.created_at,
            record.updated_at,
            record.created_by,
            record.updated_by,
        )

    async def update_response(
        self,
        connection: asyncpg.Connection,
        response_id: uuid.UUID,
        response_status: str,
        answers_jsonb: dict[str, Any],
        completed_at: Any,
        completed_by: uuid.UUID | None,
    ) -> None:
        answers_json_str = json.dumps(answers_jsonb)
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."41_fct_risk_questionnaire_responses"
            SET response_status = $2, answers_jsonb = $3::jsonb, completed_at = $4, completed_by = $5, updated_at = NOW()
            WHERE id = $1
            """,
            response_id,
            response_status,
            answers_json_str,
            completed_at,
            completed_by,
        )

    # --- Questionnaire Active Status ---

    async def update_questionnaire_active_status(
        self,
        connection: asyncpg.Connection,
        questionnaire_id: uuid.UUID,
        is_active: bool,
    ) -> None:
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."37_fct_risk_questionnaires"
            SET is_active = $2, updated_at = NOW()
            WHERE id = $1
            """,
            questionnaire_id,
            is_active,
        )

    async def update_questionnaire(
        self,
        connection: asyncpg.Connection,
        questionnaire_id: uuid.UUID,
        name: str | None = None,
        description: str | None = None,
        intended_scope: str | None = None,
    ) -> None:
        set_clauses: list[str] = []
        args: list[Any] = [questionnaire_id]
        idx = 2

        if name is not None:
            set_clauses.append(f"name = ${idx}")
            args.append(name)
            idx += 1
        if description is not None:
            set_clauses.append(f"description = ${idx}")
            args.append(description)
            idx += 1
        if intended_scope is not None:
            set_clauses.append(f"intended_scope = ${idx}")
            args.append(intended_scope)
            idx += 1

        if not set_clauses:
            return

        set_clauses.append("updated_at = NOW()")

        await connection.execute(
            f"""
            UPDATE {SCHEMA}."37_fct_risk_questionnaires"
            SET {", ".join(set_clauses)}
            WHERE id = $1
            """,
            *args,
        )

    async def soft_delete_questionnaire(
        self,
        connection: asyncpg.Connection,
        questionnaire_id: uuid.UUID,
    ) -> None:
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."37_fct_risk_questionnaires"
            SET is_deleted = TRUE, is_active = FALSE, updated_at = NOW()
            WHERE id = $1
            """,
            questionnaire_id,
        )
