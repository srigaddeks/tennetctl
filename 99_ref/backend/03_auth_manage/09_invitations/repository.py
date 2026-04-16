from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import InvitationRecord

SCHEMA = '"03_auth_manage"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


@instrument_class_methods(namespace="invitations.repository", logger_name="backend.invitations.repository.instrumentation")
class InvitationRepository:

    async def get_pending_status_id(self, connection: asyncpg.Connection) -> str:
        row = await connection.fetchrow(
            f'SELECT id FROM {SCHEMA}."43_dim_invite_statuses" WHERE code = $1',
            "pending",
        )
        return str(row["id"])

    async def get_status_id_by_code(self, connection: asyncpg.Connection, code: str) -> str:
        row = await connection.fetchrow(
            f'SELECT id FROM {SCHEMA}."43_dim_invite_statuses" WHERE code = $1',
            code,
        )
        return str(row["id"])

    async def create_invitation(
        self,
        connection: asyncpg.Connection,
        *,
        invitation_id: str,
        tenant_key: str,
        invite_token_hash: str,
        email: str,
        scope: str,
        org_id: str | None,
        workspace_id: str | None,
        role: str | None,
        grc_role_code: str | None = None,
        engagement_id: str | None = None,
        framework_id: str | None = None,
        status_id: str,
        invited_by: str,
        expires_at,
        now,
        campaign_id: str | None = None,
        source_tag: str | None = None,
        framework_ids: list[str] | None = None,
        engagement_ids: list[str] | None = None,
    ) -> InvitationRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."44_trx_invitations" (
                id, tenant_key, invite_token_hash, email, scope,
                org_id, workspace_id, role, grc_role_code, engagement_id, framework_id, status_id, invited_by,
                expires_at, accepted_at, accepted_by, revoked_at, revoked_by,
                created_at, updated_at, campaign_id, source_tag,
                framework_ids, engagement_ids
            )
            VALUES (
                $1, $2, $3, $4, $5,
                $6, $7, $8, $9, $10::uuid, $11::uuid, $12, $13,
                $14, NULL, NULL, NULL, NULL,
                $15, $16, $17::uuid, $18,
                $19::jsonb, $20::jsonb
            )
            RETURNING id, tenant_key, email, scope, org_id::text, workspace_id::text,
                      role, grc_role_code, engagement_id::text, framework_id::text,
                      framework_ids, engagement_ids,
                      invited_by::text, expires_at::text,
                      accepted_at::text, accepted_by::text, revoked_at::text, revoked_by::text,
                      created_at::text, updated_at::text
            """,
            invitation_id,
            tenant_key,
            invite_token_hash,
            email,
            scope,
            org_id,
            workspace_id,
            role,
            grc_role_code,
            engagement_id,
            framework_id,
            status_id,
            invited_by,
            expires_at,
            now,
            now,
            campaign_id,
            source_tag,
            framework_ids,
            engagement_ids,
        )
        return _row_to_invitation(row, "pending")

    async def list_by_campaign(
        self,
        connection: asyncpg.Connection,
        *,
        campaign_id: str,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[InvitationRecord], int]:
        offset = (page - 1) * page_size
        count_row = await connection.fetchrow(
            f'SELECT COUNT(*) AS total FROM {SCHEMA}."44_trx_invitations" WHERE campaign_id = $1',
            campaign_id,
        )
        rows = await connection.fetch(
            f"""
            SELECT inv.id, inv.tenant_key, inv.email, inv.scope,
                   inv.org_id::text, inv.workspace_id::text, inv.role, inv.grc_role_code,
                   inv.engagement_id::text, inv.framework_id::text,
                   inv.framework_ids, inv.engagement_ids,
                   inv.invited_by::text, inv.expires_at::text,
                   inv.accepted_at::text, inv.accepted_by::text,
                   inv.revoked_at::text, inv.revoked_by::text,
                   inv.created_at::text, inv.updated_at::text,
                   st.code AS status
            FROM {SCHEMA}."44_trx_invitations" inv
            JOIN {SCHEMA}."43_dim_invite_statuses" st ON st.id = inv.status_id
            WHERE inv.campaign_id = $1
            ORDER BY inv.created_at DESC
            LIMIT $2 OFFSET $3
            """,
            campaign_id, page_size, offset,
        )
        return [_row_to_invitation_with_status(r) for r in rows], int(count_row["total"])

    async def find_by_token_hash(
        self, connection: asyncpg.Connection, token_hash: str
    ) -> InvitationRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT inv.id, inv.tenant_key, inv.email, inv.scope,
                   inv.org_id::text, inv.workspace_id::text, inv.role, inv.grc_role_code,
                   inv.engagement_id::text, inv.framework_id::text,
                   inv.framework_ids, inv.engagement_ids,
                   inv.invited_by::text, inv.expires_at::text,
                   inv.accepted_at::text, inv.accepted_by::text,
                   inv.revoked_at::text, inv.revoked_by::text,
                   inv.created_at::text, inv.updated_at::text,
                   st.code AS status
            FROM {SCHEMA}."44_trx_invitations" inv
            JOIN {SCHEMA}."43_dim_invite_statuses" st ON st.id = inv.status_id
            WHERE inv.invite_token_hash = $1
            """,
            token_hash,
        )
        return _row_to_invitation_with_status(row) if row else None

    async def find_by_id(
        self, connection: asyncpg.Connection, invitation_id: str
    ) -> InvitationRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT inv.id, inv.tenant_key, inv.email, inv.scope,
                   inv.org_id::text, inv.workspace_id::text, inv.role, inv.grc_role_code,
                   inv.engagement_id::text, inv.framework_id::text,
                   inv.framework_ids, inv.engagement_ids,
                   inv.invited_by::text, inv.expires_at::text,
                   inv.accepted_at::text, inv.accepted_by::text,
                   inv.revoked_at::text, inv.revoked_by::text,
                   inv.created_at::text, inv.updated_at::text,
                   st.code AS status
            FROM {SCHEMA}."44_trx_invitations" inv
            JOIN {SCHEMA}."43_dim_invite_statuses" st ON st.id = inv.status_id
            WHERE inv.id = $1
            """,
            invitation_id,
        )
        return _row_to_invitation_with_status(row) if row else None

    async def find_pending_duplicate(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        email: str,
        scope: str,
        org_id: str | None,
        workspace_id: str | None,
        framework_id: str | None = None,
        engagement_id: str | None = None,
    ) -> InvitationRecord | None:
        """Find an existing pending invitation matching the given criteria.

        Args:
            connection: Active asyncpg database connection.
            tenant_key: Tenant key.
            email: Invitee email address.
            scope: Invitation scope (organization, workspace, platform).
            org_id: Org UUID or None.
            workspace_id: Workspace UUID or None.
            framework_id: Framework deployment UUID or None.
            engagement_id: Engagement UUID or None.

        Returns:
            Matching pending InvitationRecord or None.
        """
        pending_id = await self.get_pending_status_id(connection)
        row = await connection.fetchrow(
            f"""
            SELECT inv.id, inv.tenant_key, inv.email, inv.scope,
                   inv.org_id::text, inv.workspace_id::text, inv.role, inv.grc_role_code,
                   inv.engagement_id::text, inv.framework_id::text,
                   inv.framework_ids, inv.engagement_ids,
                   inv.invited_by::text, inv.expires_at::text,
                   inv.accepted_at::text, inv.accepted_by::text,
                   inv.revoked_at::text, inv.revoked_by::text,
                   inv.created_at::text, inv.updated_at::text,
                   'pending' AS status
            FROM {SCHEMA}."44_trx_invitations" inv
            WHERE inv.tenant_key = $1
              AND inv.email = $2
              AND inv.scope = $3
              AND inv.status_id = $4
              AND (inv.org_id::text = $5 OR (inv.org_id IS NULL AND $5 IS NULL))
              AND (inv.workspace_id::text = $6 OR (inv.workspace_id IS NULL AND $6 IS NULL))
              AND (inv.framework_id::text = $7 OR (inv.framework_id IS NULL AND $7 IS NULL))
              AND (inv.engagement_id::text = $8 OR (inv.engagement_id IS NULL AND $8 IS NULL))
            """,
            tenant_key,
            email,
            scope,
            pending_id,
            org_id,
            workspace_id,
            framework_id,
            engagement_id,
        )
        return _row_to_invitation_with_status(row) if row else None

    async def list_invitations(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        scope: str | None = None,
        org_id: str | None = None,
        workspace_id: str | None = None,
        status: str | None = None,
        email: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[InvitationRecord], int]:
        conditions = [f"inv.tenant_key = $1"]
        values: list[object] = [tenant_key]
        idx = 2

        if scope is not None:
            conditions.append(f"inv.scope = ${idx}")
            values.append(scope)
            idx += 1
        if org_id is not None:
            conditions.append(f"inv.org_id = ${idx}::uuid")
            values.append(org_id)
            idx += 1
        if workspace_id is not None:
            conditions.append(f"inv.workspace_id = ${idx}::uuid")
            values.append(workspace_id)
            idx += 1
        if status is not None:
            conditions.append(f"st.code = ${idx}")
            values.append(status)
            idx += 1
        if email is not None:
            conditions.append(f"inv.email ILIKE ${idx}")
            values.append(f"%{email}%")
            idx += 1

        where_clause = " AND ".join(conditions)

        count_row = await connection.fetchrow(
            f"""
            SELECT COUNT(*) AS total
            FROM {SCHEMA}."44_trx_invitations" inv
            JOIN {SCHEMA}."43_dim_invite_statuses" st ON st.id = inv.status_id
            WHERE {where_clause}
            """,
            *values,
        )
        total = count_row["total"]

        offset = (page - 1) * page_size
        values.extend([page_size, offset])
        rows = await connection.fetch(
            f"""
            SELECT inv.id, inv.tenant_key, inv.email, inv.scope,
                   inv.org_id::text, inv.workspace_id::text, inv.role, inv.grc_role_code,
                   inv.engagement_id::text, inv.framework_id::text,
                   inv.framework_ids, inv.engagement_ids,
                   inv.invited_by::text, inv.expires_at::text,
                   inv.accepted_at::text, inv.accepted_by::text,
                   inv.revoked_at::text, inv.revoked_by::text,
                   inv.created_at::text, inv.updated_at::text,
                   st.code AS status
            FROM {SCHEMA}."44_trx_invitations" inv
            JOIN {SCHEMA}."43_dim_invite_statuses" st ON st.id = inv.status_id
            WHERE {where_clause}
            ORDER BY inv.created_at DESC
            LIMIT ${idx} OFFSET ${idx + 1}
            """,
            *values,
        )
        return [_row_to_invitation_with_status(r) for r in rows], total

    async def get_stats(
        self, connection: asyncpg.Connection, *, tenant_key: str
    ) -> dict[str, int]:
        rows = await connection.fetch(
            f"""
            SELECT st.code, COUNT(*) AS cnt
            FROM {SCHEMA}."44_trx_invitations" inv
            JOIN {SCHEMA}."43_dim_invite_statuses" st ON st.id = inv.status_id
            WHERE inv.tenant_key = $1
            GROUP BY st.code
            """,
            tenant_key,
        )
        result = {"pending": 0, "accepted": 0, "revoked": 0, "expired": 0, "declined": 0}
        total = 0
        for r in rows:
            result[r["code"]] = r["cnt"]
            total += r["cnt"]
        result["total"] = total
        return result

    async def update_status(
        self,
        connection: asyncpg.Connection,
        *,
        invitation_id: str,
        new_status_code: str,
        now,
        accepted_by: str | None = None,
        revoked_by: str | None = None,
    ) -> bool:
        new_status_id = await self.get_status_id_by_code(connection, new_status_code)
        extra_fields = ""
        values: list[object] = [new_status_id, now, invitation_id]
        idx = 4

        if new_status_code == "accepted":
            extra_fields = f", accepted_at = $2, accepted_by = ${idx}"
            values.append(accepted_by)
            idx += 1
        elif new_status_code in ("revoked", "declined"):
            extra_fields = f", revoked_at = $2, revoked_by = ${idx}"
            values.append(revoked_by)
            idx += 1

        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."44_trx_invitations"
            SET status_id = $1, updated_at = $2{extra_fields}
            WHERE id = $3
            """,
            *values,
        )
        return result != "UPDATE 0"

    async def find_pending_invites_by_email(
        self, connection: asyncpg.Connection, *, email: str, tenant_key: str
    ) -> list[InvitationRecord]:
        pending_id = await self.get_pending_status_id(connection)
        rows = await connection.fetch(
            f"""
            SELECT inv.id, inv.tenant_key, inv.email, inv.scope,
                   inv.org_id::text, inv.workspace_id::text, inv.role, inv.grc_role_code,
                   inv.engagement_id::text, inv.framework_id::text,
                   inv.framework_ids, inv.engagement_ids,
                   inv.invited_by::text, inv.expires_at::text,
                   inv.accepted_at::text, inv.accepted_by::text,
                   inv.revoked_at::text, inv.revoked_by::text,
                   inv.created_at::text, inv.updated_at::text,
                   'pending' AS status
            FROM {SCHEMA}."44_trx_invitations" inv
            WHERE inv.email = $1 AND inv.tenant_key = $2 AND inv.status_id = $3
              AND inv.expires_at > NOW()
            """,
            email,
            tenant_key,
            pending_id,
        )
        return [_row_to_invitation_with_status(r) for r in rows]

    async def expire_overdue_invitations(
        self, connection: asyncpg.Connection, *, now
    ) -> int:
        pending_id = await self.get_pending_status_id(connection)
        expired_id = await self.get_status_id_by_code(connection, "expired")
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."44_trx_invitations"
            SET status_id = $1, updated_at = $2
            WHERE status_id = $3 AND expires_at <= $2
            """,
            expired_id,
            now,
            pending_id,
        )
        count_str = result.split(" ")[-1]
        return int(count_str) if count_str.isdigit() else 0


def _row_to_invitation(r, status: str) -> InvitationRecord:
    # Parse JSONB array columns (may be list, JSON string, or None)
    import json as _json
    _fw_ids_raw = r.get("framework_ids")
    _eng_ids_raw = r.get("engagement_ids")
    _fw_ids = _fw_ids_raw if isinstance(_fw_ids_raw, list) else (_json.loads(_fw_ids_raw) if isinstance(_fw_ids_raw, str) else None)
    _eng_ids = _eng_ids_raw if isinstance(_eng_ids_raw, list) else (_json.loads(_eng_ids_raw) if isinstance(_eng_ids_raw, str) else None)
    return InvitationRecord(
        id=str(r["id"]),
        tenant_key=r["tenant_key"],
        email=r["email"],
        scope=r["scope"],
        org_id=r["org_id"],
        workspace_id=r["workspace_id"],
        role=r["role"],
        grc_role_code=r.get("grc_role_code"),
        engagement_id=r.get("engagement_id"),
        framework_id=r.get("framework_id"),
        framework_ids=_fw_ids,
        engagement_ids=_eng_ids,
        status=status,
        invited_by=r["invited_by"],
        expires_at=r["expires_at"],
        accepted_at=r["accepted_at"],
        accepted_by=r["accepted_by"],
        revoked_at=r["revoked_at"],
        revoked_by=r["revoked_by"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
    )


def _row_to_invitation_with_status(r) -> InvitationRecord:
    return _row_to_invitation(r, r["status"])
