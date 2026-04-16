from __future__ import annotations

import hashlib
import secrets
import uuid as _uuid
from datetime import timedelta
from importlib import import_module

import asyncpg

from .repository import CampaignRepository
from .schemas import (
    BulkInviteRequest,
    BulkInviteResponse,
    BulkInviteResultEntry,
    CampaignListResponse,
    CampaignResponse,
    CreateCampaignRequest,
    UpdateCampaignRequest,
)

_settings_module = import_module("backend.00_config.settings")
_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_errors_module = import_module("backend.01_core.errors")
_audit_module = import_module("backend.01_core.audit")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_time_module = import_module("backend.01_core.time_utils")
_inv_repo_module = import_module("backend.03_auth_manage.09_invitations.repository")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
ConflictError = _errors_module.ConflictError
NotFoundError = _errors_module.NotFoundError
ValidationError = _errors_module.ValidationError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql
InvitationRepository = _inv_repo_module.InvitationRepository

_CACHE_TTL = 120  # 2 minutes


@instrument_class_methods(namespace="invite_campaigns.service", logger_name="backend.invite_campaigns.instrumentation")
class CampaignService:
    def __init__(self, *, settings: Settings, database_pool: DatabasePool, cache: CacheManager | NullCacheManager) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repo = CampaignRepository()
        self._inv_repo = InvitationRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.invite_campaigns")

    @staticmethod
    def _generate_token(invite_id: str) -> tuple[str, str]:
        secret = secrets.token_urlsafe(32)
        token_string = f"{invite_id}.{secret}"
        token_hash = hashlib.sha256(token_string.encode()).hexdigest()
        return token_string, token_hash

    async def _invalidate(self, tenant_key: str) -> None:
        await self._cache.delete_pattern(f"campaigns:list:{tenant_key}*")

    # ── Campaigns CRUD ────────────────────────────────────────────────────────

    async def create_campaign(
        self,
        *,
        user_id: str,
        tenant_key: str,
        payload: CreateCampaignRequest,
    ) -> CampaignResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "invitation_management.create")
            existing = await self._repo.get_by_code(conn, payload.code, tenant_key)
            if existing:
                raise ConflictError(f"Campaign '{payload.code}' already exists.")
            campaign = await self._repo.create_campaign(
                conn,
                code=payload.code,
                name=payload.name,
                description=payload.description,
                campaign_type=payload.campaign_type,
                default_scope=payload.default_scope,
                default_role=payload.default_role,
                default_org_id=payload.default_org_id,
                default_workspace_id=payload.default_workspace_id,
                default_expires_hours=payload.default_expires_hours,
                starts_at=payload.starts_at,
                ends_at=payload.ends_at,
                notes=payload.notes,
                tenant_key=tenant_key,
                created_by=user_id,
                now=now,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(_uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="invite_campaign",
                    entity_id=campaign.id,
                    event_type="campaign_created",
                    event_category="access",
                    occurred_at=now,
                    actor_id=user_id,
                    properties={"campaign_code": campaign.code, "campaign_type": campaign.campaign_type},
                ),
            )
        await self._invalidate(tenant_key)
        return _to_response(campaign)

    async def list_campaigns(
        self,
        *,
        user_id: str,
        tenant_key: str,
        status: str | None = None,
        campaign_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> CampaignListResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "invitation_management.view")
            campaigns, total = await self._repo.list_campaigns(
                conn,
                tenant_key=tenant_key,
                status=status,
                campaign_type=campaign_type,
                limit=limit,
                offset=offset,
            )
        return CampaignListResponse(campaigns=[_to_response(c) for c in campaigns], total=total)

    async def get_campaign(self, *, user_id: str, campaign_id: str) -> CampaignResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "invitation_management.view")
            campaign = await self._repo.get_by_id(conn, campaign_id)
        if campaign is None:
            raise NotFoundError(f"Campaign '{campaign_id}' not found.")
        return _to_response(campaign)

    async def update_campaign(
        self,
        *,
        user_id: str,
        tenant_key: str,
        campaign_id: str,
        payload: UpdateCampaignRequest,
    ) -> CampaignResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "invitation_management.update")
            existing = await self._repo.get_by_id(conn, campaign_id)
            if existing is None:
                raise NotFoundError(f"Campaign '{campaign_id}' not found.")
            campaign = await self._repo.update_campaign(
                conn,
                campaign_id=campaign_id,
                name=payload.name,
                description=payload.description,
                status=payload.status,
                default_role=payload.default_role,
                default_expires_hours=payload.default_expires_hours,
                starts_at=payload.starts_at,
                ends_at=payload.ends_at,
                notes=payload.notes,
                updated_by=user_id,
                now=now,
            )
        await self._invalidate(tenant_key)
        return _to_response(campaign)  # type: ignore[arg-type]

    # ── Bulk invite ───────────────────────────────────────────────────────────

    async def bulk_invite(
        self,
        *,
        user_id: str,
        tenant_key: str,
        campaign_id: str,
        payload: BulkInviteRequest,
    ) -> BulkInviteResponse:
        """
        Send invitations in bulk under a campaign.

        Accepts either:
          - payload.emails: list[str] (plain emails, uniform role)
          - payload.entries: list[{email, role}] (per-recipient role override)
        Both can be combined; entries take precedence over emails.

        Skips duplicates (existing pending invitation with same email+scope).
        Returns per-email result summary.
        """
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "invitation_management.create")
            campaign = await self._repo.get_by_id(conn, campaign_id)

        if campaign is None:
            raise NotFoundError(f"Campaign '{campaign_id}' not found.")

        # Build unified list of (email, role_override)
        entries: list[tuple[str, str | None]] = []
        seen: set[str] = set()
        for raw_email in payload.emails:
            email = raw_email.strip().lower()
            if email and email not in seen:
                seen.add(email)
                entries.append((email, payload.role))
        for e in payload.entries:
            email = e.email.strip().lower()
            if email and email not in seen:
                seen.add(email)
                entries.append((email, e.role or payload.role))

        if not entries:
            return BulkInviteResponse(sent=0, skipped=0, errors=0, results=[])

        scope = payload.scope or campaign.default_scope
        org_id = payload.org_id or campaign.default_org_id
        workspace_id = payload.workspace_id or campaign.default_workspace_id
        expires_hours = payload.expires_in_hours or campaign.default_expires_hours
        source_tag = payload.source_tag or f"campaign:{campaign.code}"

        results: list[BulkInviteResultEntry] = []
        sent = skipped = errors = 0

        async with self._database_pool.acquire() as conn:
            pending_status_id = await self._inv_repo.get_pending_status_id(conn)

        for email, role_override in entries:
            role = role_override or campaign.default_role
            try:
                async with self._database_pool.transaction() as conn:
                    # Check duplicate
                    dup = await self._inv_repo.find_pending_duplicate(
                        conn,
                        tenant_key=tenant_key,
                        email=email,
                        scope=scope,
                        org_id=org_id,
                        workspace_id=workspace_id,
                    )
                    if dup:
                        results.append(BulkInviteResultEntry(
                            email=email, status="skipped",
                            reason="Pending invitation already exists"
                        ))
                        skipped += 1
                        continue

                    invite_id = str(_uuid.uuid4())
                    token_string, token_hash = self._generate_token(invite_id)
                    expires_at = now + timedelta(hours=expires_hours)

                    invitation = await self._inv_repo.create_invitation(
                        conn,
                        invitation_id=invite_id,
                        tenant_key=tenant_key,
                        invite_token_hash=token_hash,
                        email=email,
                        scope=scope,
                        org_id=org_id,
                        workspace_id=workspace_id,
                        role=role,
                        status_id=pending_status_id,
                        invited_by=user_id,
                        expires_at=expires_at,
                        now=now,
                        campaign_id=campaign_id,
                        source_tag=source_tag,
                    )
                    await self._audit_writer.write_entry(
                        conn,
                        AuditEntry(
                            id=str(_uuid.uuid4()),
                            tenant_key=tenant_key,
                            entity_type="invitation",
                            entity_id=invite_id,
                            event_type="invite_created",
                            event_category="access",
                            occurred_at=now,
                            actor_id=user_id,
                            properties={
                                "invite_email": email,
                                "invite_scope": scope,
                                "invite_role": role,
                                "campaign_id": campaign_id,
                                "campaign_code": campaign.code,
                                "source_tag": source_tag,
                            },
                        ),
                    )
                results.append(BulkInviteResultEntry(
                    email=email, status="sent", invitation_id=invitation.id
                ))
                sent += 1
            except Exception as exc:  # noqa: BLE001
                self._logger.warning("bulk_invite_error", email=email, error=str(exc))
                results.append(BulkInviteResultEntry(
                    email=email, status="error", reason=str(exc)
                ))
                errors += 1

        # Increment campaign invite_count
        if sent > 0:
            async with self._database_pool.acquire() as conn:
                await self._repo.increment_invite_count(conn, campaign_id, sent)

        await self._invalidate(tenant_key)
        return BulkInviteResponse(sent=sent, skipped=skipped, errors=errors, results=results)

    async def list_campaign_invitations(
        self,
        *,
        user_id: str,
        campaign_id: str,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "invitation_management.view")
            campaign = await self._repo.get_by_id(conn, campaign_id)
            if campaign is None:
                raise NotFoundError(f"Campaign '{campaign_id}' not found.")
            items, total = await self._inv_repo.list_by_campaign(
                conn, campaign_id=campaign_id, page=page, page_size=page_size
            )
        return {
            "items": [
                {
                    "id": i.id,
                    "email": i.email,
                    "scope": i.scope,
                    "role": i.role,
                    "status": i.status,
                    "expires_at": i.expires_at,
                    "accepted_at": i.accepted_at,
                    "created_at": i.created_at,
                }
                for i in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }


def _to_response(c) -> CampaignResponse:
    return CampaignResponse(
        id=c.id,
        tenant_key=c.tenant_key,
        code=c.code,
        name=c.name,
        description=c.description,
        campaign_type=c.campaign_type,
        status=c.status,
        default_scope=c.default_scope,
        default_role=c.default_role,
        default_org_id=c.default_org_id,
        default_workspace_id=c.default_workspace_id,
        default_expires_hours=c.default_expires_hours,
        starts_at=c.starts_at,
        ends_at=c.ends_at,
        invite_count=c.invite_count,
        accepted_count=c.accepted_count,
        notes=c.notes,
        created_at=c.created_at,
        updated_at=c.updated_at,
        created_by=c.created_by,
    )
