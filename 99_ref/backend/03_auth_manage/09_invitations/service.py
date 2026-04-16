from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta
from importlib import import_module

from .constants import InviteScope, InviteStatus, VALID_ORG_ROLES, VALID_WORKSPACE_ROLES
from .repository import InvitationRepository
from .schemas import (
    AcceptInvitationRequest,
    BulkCreateInvitationRequest,
    BulkCreateInvitationResponse,
    BulkInviteResultEntry,
    CreateInvitationRequest,
    DeclineInvitationRequest,
    InvitationAcceptedResponse,
    InvitationCreatedResponse,
    InvitationListResponse,
    InvitationResponse,
    InvitationStatsResponse,
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
_constants_module = import_module("backend.03_auth_manage.constants")
_scoped_groups_module = import_module("backend.03_auth_manage._scoped_group_provisioning")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
ConflictError = _errors_module.ConflictError
NotFoundError = _errors_module.NotFoundError
ValidationError = _errors_module.ValidationError
assign_workspace_member_grc_role = _scoped_groups_module.assign_workspace_member_grc_role
_GRC_ROLE_CODES = _scoped_groups_module._GRC_ROLE_CODES
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
AuditEventType = _constants_module.AuditEventType
AuditEventCategory = _constants_module.AuditEventCategory
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql

_CACHE_TTL_INVITATIONS = 60  # 1 minute
_CACHE_TTL_STATS = 60


@instrument_class_methods(namespace="invitations.service", logger_name="backend.invitations.instrumentation")
class InvitationService:
    def __init__(self, *, settings: Settings, database_pool: DatabasePool, cache: CacheManager | NullCacheManager) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = InvitationRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.invitations")

    @staticmethod
    def _generate_token(invite_id: str) -> tuple[str, str]:
        secret = secrets.token_urlsafe(32)
        token_string = f"{invite_id}.{secret}"
        token_hash = hashlib.sha256(token_string.encode()).hexdigest()
        return token_string, token_hash

    @staticmethod
    def _hash_token(token_string: str) -> str:
        return hashlib.sha256(token_string.encode()).hexdigest()

    async def _require_invitation_permission(
        self,
        conn,
        *,
        user_id: str,
        permission_action: str,
        scope: str,
        org_id: str | None,
        workspace_id: str | None,
    ) -> None:
        if scope in {InviteScope.ORGANIZATION.value, InviteScope.WORKSPACE.value} and org_id:
            permission_by_action = {
                "create": "org_management.assign",
                "view": "org_management.view",
                "revoke": "org_management.revoke",
            }
            scoped_permission = permission_by_action.get(permission_action)
            if scoped_permission:
                await require_permission(
                    conn,
                    user_id,
                    scoped_permission,
                    scope_org_id=org_id,
                    scope_workspace_id=workspace_id if scope == InviteScope.WORKSPACE.value else None,
                )
                return
        await require_permission(conn, user_id, f"invitation_management.{permission_action}")

    async def create_invitation(
        self, *, user_id: str, tenant_key: str, request: CreateInvitationRequest
    ) -> InvitationCreatedResponse:
        now = utc_now_sql()
        email = request.email.strip().lower()
        scope = request.scope

        self._validate_scope_fields(scope, request.org_id, request.workspace_id, request.role)

        async with self._database_pool.transaction() as conn:
            await self._require_invitation_permission(
                conn,
                user_id=user_id,
                permission_action="create",
                scope=scope,
                org_id=request.org_id,
                workspace_id=request.workspace_id,
            )

            existing = await self._repository.find_pending_duplicate(
                conn,
                tenant_key=tenant_key,
                email=email,
                scope=scope,
                org_id=request.org_id,
                workspace_id=request.workspace_id,
                framework_id=getattr(request, "framework_id", None),
                engagement_id=getattr(request, "engagement_id", None),
            )
            if existing:
                raise ConflictError(
                    f"A pending invitation already exists for {email} with scope {scope}"
                )

            invite_id = str(uuid.uuid4())
            token_string, token_hash = self._generate_token(invite_id)
            expires_at = now + timedelta(hours=request.expires_in_hours)
            pending_status_id = await self._repository.get_pending_status_id(conn)

            grc_role_code = request.grc_role_code
            if grc_role_code and grc_role_code not in _GRC_ROLE_CODES:
                raise ValidationError(f"Invalid grc_role_code '{grc_role_code}'.")

            invitation = await self._repository.create_invitation(
                conn,
                invitation_id=invite_id,
                tenant_key=tenant_key,
                invite_token_hash=token_hash,
                email=email,
                scope=scope,
                org_id=request.org_id,
                workspace_id=request.workspace_id,
                role=request.role,
                grc_role_code=grc_role_code,
                engagement_id=getattr(request, "engagement_id", None),
                framework_id=getattr(request, "framework_id", None),
                status_id=pending_status_id,
                invited_by=user_id,
                expires_at=expires_at,
                now=now,
                framework_ids=getattr(request, "framework_ids", None),
                engagement_ids=getattr(request, "engagement_ids", None),
            )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="invitation",
                    entity_id=invite_id,
                    event_type=AuditEventType.INVITE_CREATED.value,
                    event_category=AuditEventCategory.AUTH.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "invite_email": email,
                        "invite_scope": scope,
                        "invite_role": request.role,
                        "invite_grc_role_code": grc_role_code,
                        "invite_org_id": request.org_id,
                        "invite_workspace_id": request.workspace_id,
                    },
                ),
            )

        await self._invalidate_caches(tenant_key)

        # Fire-and-forget: send invitation notification email (best-effort, never blocks)
        if getattr(self._settings, "notification_enabled", False):
            import asyncio as _asyncio
            _asyncio.create_task(
                self._dispatch_invite_notification(
                    invitation=invitation,
                    token_string=token_string,
                    tenant_key=tenant_key,
                    actor_id=user_id,
                    invite_id=invite_id,
                    grc_role_code=grc_role_code,
                    now=now,
                )
            )

        return InvitationCreatedResponse(
            **_invitation_dict(invitation),
            invite_token=token_string,
        )

    async def _dispatch_invite_notification(
        self,
        *,
        invitation,
        token_string: str,
        tenant_key: str,
        actor_id: str,
        invite_id: str,
        grc_role_code: str | None,
        now,
    ) -> None:
        """Send an invitation notification email via the notification dispatcher.

        Renders the appropriate template (GRC or standard) with invitation
        variables and queues via dispatch_to_email (supports pre-account recipients).
        Never raises — failures are logged.
        """
        try:
            import json as _json
            _renderer_module = import_module("backend.04_notifications.01_templates.renderer")
            _dispatcher_module = import_module("backend.04_notifications.02_dispatcher.dispatcher")
            TemplateRenderer = _renderer_module.TemplateRenderer
            NotificationDispatcher = _dispatcher_module.NotificationDispatcher

            renderer = TemplateRenderer()
            dispatcher = NotificationDispatcher(
                database_pool=self._database_pool,
                settings=self._settings,
            )

            # Build accept URL pointing at the accept-invite page
            base_url = getattr(self._settings, "platform_base_url", "").rstrip("/")
            accept_url = f"{base_url}/accept-invite?token={token_string}" if base_url else f"/accept-invite?token={token_string}"

            # Human-readable GRC role label map
            _GRC_ROLE_LABELS = {
                "grc_practitioner":  "GRC Practitioner",
                "grc_engineer":      "GRC Engineer",
                "grc_ciso":          "CISO",
                "grc_lead_auditor":  "Lead Auditor",
                "grc_staff_auditor": "Staff Auditor",
                "grc_vendor":        "Vendor",
            }
            grc_role_label = _GRC_ROLE_LABELS.get(grc_role_code, grc_role_code) if grc_role_code else None

            # Pick notification type + template based on whether this is a GRC invite
            is_grc_invite = bool(grc_role_code)
            notification_type_code = "workspace_invite_grc" if is_grc_invite else "workspace_invite_received"
            template_code = "workspace_invite_grc_email" if is_grc_invite else "workspace_invite_email"

            # Fetch template and workspace/org names from DB
            async with self._database_pool.acquire() as conn:
                template_row = await conn.fetchrow(
                    f"""
                    SELECT v.subject_line, v.body_html, v.body_text
                    FROM "03_notifications"."10_fct_templates" t
                    JOIN "03_notifications"."14_dtl_template_versions" v
                          ON v.id = t.active_version_id
                    WHERE t.code = $1
                      AND (t.tenant_key = $2 OR t.tenant_key = '__system__')
                      AND t.is_active = TRUE AND t.is_deleted = FALSE
                    ORDER BY CASE WHEN t.tenant_key = $2 THEN 0 ELSE 1 END
                    LIMIT 1
                    """,
                    template_code,
                    tenant_key,
                )

                # Resolve workspace, org display names, and inviter display name
                workspace_name = ""
                org_name = ""
                actor_display_name = ""
                if invitation.workspace_id:
                    ws_row = await conn.fetchrow(
                        'SELECT name FROM "03_auth_manage"."34_fct_workspaces" WHERE id = $1::uuid',
                        invitation.workspace_id,
                    )
                    if ws_row:
                        workspace_name = ws_row["name"] or ""
                if invitation.org_id:
                    org_row = await conn.fetchrow(
                        'SELECT name FROM "03_auth_manage"."29_fct_orgs" WHERE id = $1::uuid',
                        invitation.org_id,
                    )
                    if org_row:
                        org_name = org_row["name"] or ""
                if actor_id:
                    actor_row = await conn.fetchrow(
                        """
                        SELECT property_value FROM "03_auth_manage"."05_dtl_user_properties"
                        WHERE user_id = $1::uuid AND property_key = 'display_name'
                        LIMIT 1
                        """,
                        actor_id,
                    )
                    if actor_row:
                        actor_display_name = actor_row["property_value"] or ""

            if not template_row:
                self._logger.warning(
                    "invitation_notification_no_template",
                    extra={"invite_id": invite_id, "template_code": template_code},
                )
                return

            # For org-scoped invites (no workspace), use org name as the scope display
            scope_name = workspace_name if workspace_name else org_name

            # Template variables — flat dotted keys, renderer nests them automatically
            variables: dict[str, str] = {
                "user.display_name":       "",              # invitee may not have account yet
                "actor.display_name":      actor_display_name,
                "invite.accept_url":       accept_url,
                "invite.expires_in":       "72 hours",
                "invite.grc_role_code":    grc_role_code or "",
                "invite.grc_role_label":   grc_role_label or "",
                "invite.workspace_name":   scope_name,
                "invite.org_name":         org_name,
                "invite.engagement_name":  "",
                "invite.framework_name":   "",
                "workspace.name":          scope_name,
                "org.name":                org_name,
                "unsubscribe_url":         "#",
            }

            rendered = renderer.render_template_version(
                subject_line=template_row["subject_line"],
                body_html=template_row["body_html"],
                body_text=template_row["body_text"],
                body_short=None,
                variables=variables,
            )

            await dispatcher.dispatch_to_email(
                recipient_email=invitation.email,
                notification_type_code=notification_type_code,
                subject=rendered.get("subject_line") or "You have been invited",
                body_html=rendered.get("body_html") or "",
                body_text=rendered.get("body_text") or "",
                tenant_key=tenant_key,
                idempotency_key=f"invite:{invite_id}:{notification_type_code}:email",
                priority_code="high",
            )
        except Exception as _exc:
            self._logger.warning(
                "invitation_notification_failed",
                extra={"invite_id": invite_id, "reason": str(_exc)},
            )

    async def list_invitations(
        self,
        *,
        user_id: str,
        tenant_key: str,
        scope: str | None = None,
        org_id: str | None = None,
        workspace_id: str | None = None,
        status: str | None = None,
        email: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> InvitationListResponse:
        async with self._database_pool.acquire() as conn:
            # Infer scope from provided IDs when caller doesn't pass one explicitly,
            # so org members listing their own org's invitations are checked against
            # org_management.view rather than the platform-level invitation_management.view.
            effective_scope = scope
            if not effective_scope:
                if workspace_id:
                    effective_scope = InviteScope.WORKSPACE.value
                elif org_id:
                    effective_scope = InviteScope.ORGANIZATION.value
                else:
                    effective_scope = InviteScope.PLATFORM.value
            await self._require_invitation_permission(
                conn,
                user_id=user_id,
                permission_action="view",
                scope=effective_scope,
                org_id=org_id,
                workspace_id=workspace_id,
            )
            items, total = await self._repository.list_invitations(
                conn,
                tenant_key=tenant_key,
                scope=scope,
                org_id=org_id,
                workspace_id=workspace_id,
                status=status,
                email=email,
                page=page,
                page_size=page_size,
            )
        return InvitationListResponse(
            items=[InvitationResponse(**_invitation_dict(i)) for i in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_stats(self, *, user_id: str, tenant_key: str) -> InvitationStatsResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "invitation_management.view")

        cache_key = f"invitations:stats:{tenant_key}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return InvitationStatsResponse.model_validate_json(cached)

        async with self._database_pool.acquire() as conn:
            stats = await self._repository.get_stats(conn, tenant_key=tenant_key)

        result = InvitationStatsResponse(**stats)
        await self._cache.set(cache_key, result.model_dump_json(), _CACHE_TTL_STATS)
        return result

    async def get_invitation(self, *, user_id: str, invitation_id: str) -> InvitationResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "invitation_management.view")
            invitation = await self._repository.find_by_id(conn, invitation_id)
        if invitation is None:
            raise NotFoundError(f"Invitation '{invitation_id}' not found")
        return InvitationResponse(**_invitation_dict(invitation))

    async def resend_invitation(self, *, user_id: str, invitation_id: str, tenant_key: str) -> InvitationCreatedResponse:
        """Re-extend a pending invitation's expiry and re-dispatch the notification email.

        Only pending invitations can be resent. Generates a new token (old token becomes invalid).
        """
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            invitation = await self._repository.find_by_id(conn, invitation_id)
            if invitation is None:
                raise NotFoundError(f"Invitation '{invitation_id}' not found")
            await self._require_invitation_permission(
                conn,
                user_id=user_id,
                permission_action="create",
                scope=invitation.scope,
                org_id=invitation.org_id,
                workspace_id=invitation.workspace_id,
            )
            if invitation.status not in (InviteStatus.PENDING, InviteStatus.EXPIRED):
                raise ValidationError(f"Only pending or expired invitations can be resent (status: {invitation.status})")

            token_string, token_hash = self._generate_token(invitation_id)
            expires_at = now + timedelta(hours=72)
            await self._repository.update_status(
                conn,
                invitation_id=invitation_id,
                new_status_code=InviteStatus.PENDING,
                now=now,
            )
            await conn.execute(
                f"""
                UPDATE "03_auth_manage"."44_trx_invitations"
                SET invite_token_hash = $1, expires_at = $2, updated_at = $3
                WHERE id = $4::uuid
                """,
                token_hash,
                expires_at,
                now,
                invitation_id,
            )

        updated = await self._get_invitation_by_id(invitation_id)
        await self._invalidate_caches(tenant_key)

        if getattr(self._settings, "notification_enabled", False):
            import asyncio as _asyncio
            _asyncio.create_task(
                self._dispatch_invite_notification(
                    invitation=updated,
                    token_string=token_string,
                    tenant_key=tenant_key,
                    actor_id=user_id,
                    invite_id=invitation_id,
                    grc_role_code=updated.grc_role_code,
                    now=now,
                )
            )

        return InvitationCreatedResponse(
            **_invitation_dict(updated),
            invite_token=token_string,
        )

    async def revoke_invitation(self, *, user_id: str, invitation_id: str, tenant_key: str) -> InvitationResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            invitation = await self._repository.find_by_id(conn, invitation_id)
            if invitation is None:
                raise NotFoundError(f"Invitation '{invitation_id}' not found")
            await self._require_invitation_permission(
                conn,
                user_id=user_id,
                permission_action="revoke",
                scope=invitation.scope,
                org_id=invitation.org_id,
                workspace_id=invitation.workspace_id,
            )
            if invitation.status != InviteStatus.PENDING:
                raise ValidationError(f"Cannot revoke invitation with status '{invitation.status}'")

            await self._repository.update_status(
                conn,
                invitation_id=invitation_id,
                new_status_code=InviteStatus.REVOKED,
                now=now,
                revoked_by=user_id,
            )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="invitation",
                    entity_id=invitation_id,
                    event_type=AuditEventType.INVITE_REVOKED.value,
                    event_category=AuditEventCategory.AUTH.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "invite_email": invitation.email,
                        "invite_scope": invitation.scope,
                    },
                ),
            )

        await self._invalidate_caches(tenant_key)
        updated = await self._get_invitation_by_id(invitation_id)
        return InvitationResponse(**_invitation_dict(updated))

    async def preview_invitation(self, *, invite_token: str):
        """Return public invite context (org/workspace name, GRC role, expiry) without consuming the token.

        No authentication required — used by the accept-invite page to show context before the user decides.
        Also returns email and user_exists so the frontend can route new users to /register and
        returning users to /login before accepting.
        Returns None if the token is invalid or the invitation is not pending.
        """
        from .schemas import InvitationPreviewResponse
        token_hash = self._hash_token(invite_token)
        async with self._database_pool.acquire() as conn:
            invitation = await self._repository.find_by_token_hash(conn, token_hash)
            if invitation is None or invitation.status != InviteStatus.PENDING:
                return None

            org_name: str | None = None
            workspace_name: str | None = None
            if invitation.org_id:
                row = await conn.fetchrow(
                    'SELECT name FROM "03_auth_manage"."29_fct_orgs" WHERE id = $1::uuid',
                    invitation.org_id,
                )
                if row:
                    org_name = row["name"]
            if invitation.workspace_id:
                row = await conn.fetchrow(
                    'SELECT name FROM "03_auth_manage"."34_fct_workspaces" WHERE id = $1::uuid',
                    invitation.workspace_id,
                )
                if row:
                    workspace_name = row["name"]

            user_row = await conn.fetchrow(
                """
                SELECT u.id
                FROM "03_auth_manage"."05_dtl_user_properties" p
                JOIN "03_auth_manage"."03_fct_users" u ON u.id = p.user_id
                WHERE p.property_key = 'email' AND p.property_value = $1
                  AND u.is_deleted = FALSE
                LIMIT 1
                """,
                invitation.email,
            )
            user_exists = user_row is not None

        return InvitationPreviewResponse(
            scope=invitation.scope,
            org_name=org_name,
            workspace_name=workspace_name,
            grc_role_code=invitation.grc_role_code,
            expires_at=invitation.expires_at,
            status=invitation.status,
            email=invitation.email,
            user_exists=user_exists,
        )

    async def accept_invitation(self, *, request: AcceptInvitationRequest, caller_user_id: str) -> InvitationAcceptedResponse:
        """Accept a pending invitation.

        The caller must be logged in as the exact user whose email matches the invitation.
        This prevents a logged-in user from accidentally accepting someone else's invite.

        Args:
            request: Contains the invite token.
            caller_user_id: User ID from the JWT of the authenticated caller.
        """
        logger = get_logger("backend.invitations")
        logger.info("accept_invitation_requested", extra={"token_hash_prefix": request.invite_token[:10] if request.invite_token else "none"})
        
        # Consistent naive UTC now
        now = utc_now_sql()
        token_hash = self._hash_token(request.invite_token)

        async with self._database_pool.transaction() as conn:
            invitation = await self._repository.find_by_token_hash(conn, token_hash)
            if invitation is None:
                logger.warning("invite_not_found", extra={"token_hash": token_hash})
                raise NotFoundError("Invalid or expired invitation token")

            if invitation.status != InviteStatus.PENDING:
                logger.warning("invite_not_pending", extra={"status": invitation.status, "id": invitation.id})
                raise ValidationError(f"Invitation is no longer pending (status: {invitation.status})")

            # Defensive datetime parsing
            try:
                expires_at = datetime.fromisoformat(invitation.expires_at)
                if expires_at.tzinfo is not None:
                    expires_at = expires_at.replace(tzinfo=None)
            except (ValueError, TypeError) as e:
                logger.error("invite_expiry_parse_failed", extra={"val": invitation.expires_at, "error": str(e)})
                raise ValidationError("Invalid invitation expiry format")

            if now > expires_at:
                logger.info("invite_expired", extra={"id": invitation.id, "now": now.isoformat(), "expires": expires_at.isoformat()})
                await self._repository.update_status(
                    conn,
                    invitation_id=invitation.id,
                    new_status_code=InviteStatus.EXPIRED,
                    now=now,
                )
                raise ValidationError("Invitation has expired")

            # Verify the logged-in user's email matches the invited email
            caller_email_row = await conn.fetchrow(
                """
                SELECT property_value AS email
                FROM "03_auth_manage"."05_dtl_user_properties"
                WHERE user_id = $1::uuid AND property_key = 'email'
                LIMIT 1
                """,
                caller_user_id,
            )
            if caller_email_row is None:
                logger.warning("caller_email_not_found", extra={"user_id": caller_user_id})
                raise ValidationError("Caller user does not have a registered email property")
                
            caller_email = caller_email_row["email"]
            if caller_email.lower() != invitation.email.lower():
                logger.warning("invite_email_mismatch", extra={"caller": caller_email, "invite": invitation.email})
                raise ValidationError(
                    "You must be logged in as the invited email address to accept this invitation"
                )

            accepted_by = caller_user_id

            await self._repository.update_status(
                conn,
                invitation_id=invitation.id,
                new_status_code=InviteStatus.ACCEPTED,
                now=now,
                accepted_by=accepted_by,
            )

            # If user exists, auto-enroll into org/workspace
            if accepted_by:
                await self._auto_enroll(conn, invitation=invitation, user_id=accepted_by, now=now)

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=invitation.tenant_key,
                    entity_type="invitation",
                    entity_id=invitation.id,
                    event_type=AuditEventType.INVITE_ACCEPTED.value,
                    event_category=AuditEventCategory.AUTH.value,
                    occurred_at=now,
                    actor_id=accepted_by,
                    actor_type="user" if accepted_by else None,
                    properties={
                        "invite_email": invitation.email,
                        "invite_scope": invitation.scope,
                        "invite_role": invitation.role,
                        "accepted_by_existing_user": str(accepted_by is not None),
                    },
                ),
            )

        await self._invalidate_caches(invitation.tenant_key)
        if accepted_by:
            await self._cache.delete_pattern(f"access:{accepted_by}:*")
        return InvitationAcceptedResponse(
            message="Invitation accepted",
            scope=invitation.scope,
            org_id=invitation.org_id,
            workspace_id=invitation.workspace_id,
            role=invitation.role,
            grc_role_code=invitation.grc_role_code,
        )

    async def accept_invitation_by_token(self, *, invite_token: str) -> InvitationAcceptedResponse:
        """Public accept: applies invitation to the existing user matching the invited email.

        Used when the invited address already has an account. Token possession proves
        control of the inbox, so no JWT is required. Raises NotFoundError("user_not_found")
        if no matching user (caller should route to /register instead).
        """
        logger = get_logger("backend.invitations")
        logger.info(
            "accept_invitation_by_token_requested",
            extra={"token_hash_prefix": invite_token[:10] if invite_token else "none"},
        )

        now = utc_now_sql()
        token_hash = self._hash_token(invite_token)

        async with self._database_pool.transaction() as conn:
            invitation = await self._repository.find_by_token_hash(conn, token_hash)
            if invitation is None:
                logger.warning("invite_not_found_public", extra={"token_hash": token_hash})
                raise NotFoundError("Invalid or expired invitation token")

            if invitation.status != InviteStatus.PENDING:
                logger.warning(
                    "invite_not_pending_public",
                    extra={"status": invitation.status, "id": invitation.id},
                )
                raise ValidationError(
                    f"Invitation is no longer pending (status: {invitation.status})"
                )

            try:
                expires_at = datetime.fromisoformat(invitation.expires_at)
                if expires_at.tzinfo is not None:
                    expires_at = expires_at.replace(tzinfo=None)
            except (ValueError, TypeError) as e:
                logger.error(
                    "invite_expiry_parse_failed_public",
                    extra={"val": invitation.expires_at, "error": str(e)},
                )
                raise ValidationError("Invalid invitation expiry format")

            if now > expires_at:
                logger.info(
                    "invite_expired_public",
                    extra={"id": invitation.id, "now": now.isoformat(), "expires": expires_at.isoformat()},
                )
                await self._repository.update_status(
                    conn,
                    invitation_id=invitation.id,
                    new_status_code=InviteStatus.EXPIRED,
                    now=now,
                )
                raise ValidationError("Invitation has expired")

            # Look up the existing user matching the invited email
            user_row = await conn.fetchrow(
                """
                SELECT u.id::text AS user_id
                FROM "03_auth_manage"."05_dtl_user_properties" p
                JOIN "03_auth_manage"."03_fct_users" u ON u.id = p.user_id
                WHERE p.property_key = 'email' AND p.property_value = $1
                  AND u.is_deleted = FALSE
                LIMIT 1
                """,
                invitation.email,
            )
            if user_row is None:
                # Caller should route to /register — signal with a structured code
                logger.info(
                    "invite_public_accept_no_user",
                    extra={"invite_id": invitation.id, "email": invitation.email},
                )
                raise NotFoundError("user_not_found")

            user_id = user_row["user_id"]

            await self._repository.update_status(
                conn,
                invitation_id=invitation.id,
                new_status_code=InviteStatus.ACCEPTED,
                now=now,
                accepted_by=user_id,
            )

            await self._auto_enroll(conn, invitation=invitation, user_id=user_id, now=now)

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=invitation.tenant_key,
                    entity_type="invitation",
                    entity_id=invitation.id,
                    event_type=AuditEventType.INVITE_ACCEPTED.value,
                    event_category=AuditEventCategory.AUTH.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "invite_email": invitation.email,
                        "invite_scope": invitation.scope,
                        "invite_role": invitation.role,
                        "accepted_by_existing_user": "True",
                        "accept_path": "public_token",
                    },
                ),
            )

        await self._invalidate_caches(invitation.tenant_key)
        await self._cache.delete_pattern(f"access:{user_id}:*")
        return InvitationAcceptedResponse(
            message="Invitation accepted",
            scope=invitation.scope,
            org_id=invitation.org_id,
            workspace_id=invitation.workspace_id,
            role=invitation.role,
            grc_role_code=invitation.grc_role_code,
        )

    async def decline_invitation(self, *, request: DeclineInvitationRequest) -> InvitationResponse:
        now = utc_now_sql()
        token_hash = self._hash_token(request.invite_token)

        async with self._database_pool.transaction() as conn:
            invitation = await self._repository.find_by_token_hash(conn, token_hash)
            if invitation is None:
                raise NotFoundError("Invalid or expired invitation token")

            if invitation.status != InviteStatus.PENDING:
                raise ValidationError(f"Invitation is no longer pending (status: {invitation.status})")

            # Look up the user declining (may not be registered yet — that's OK)
            user_row = await conn.fetchrow(
                f"""
                SELECT u.id::text AS user_id
                FROM "03_auth_manage"."05_dtl_user_properties" p
                JOIN "03_auth_manage"."03_fct_users" u ON u.id = p.user_id
                WHERE p.property_key = 'email' AND p.property_value = $1
                  AND u.is_deleted = FALSE
                """,
                invitation.email,
            )
            declined_by = user_row["user_id"] if user_row else None

            await self._repository.update_status(
                conn,
                invitation_id=invitation.id,
                new_status_code=InviteStatus.DECLINED,
                now=now,
                revoked_by=declined_by,
            )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=invitation.tenant_key,
                    entity_type="invitation",
                    entity_id=invitation.id,
                    event_type=AuditEventType.INVITE_DECLINED.value,
                    event_category=AuditEventCategory.AUTH.value,
                    occurred_at=now,
                    actor_id=declined_by,
                    actor_type="user" if declined_by else None,
                    properties={
                        "invite_email": invitation.email,
                        "invite_scope": invitation.scope,
                    },
                ),
            )

        await self._invalidate_caches(invitation.tenant_key)
        updated = await self._get_invitation_by_id(invitation.id)
        return InvitationResponse(**_invitation_dict(updated))

    async def process_registration_invites(
        self, conn, *, email: str, user_id: str, tenant_key: str, now
    ) -> None:
        pending_invites = await self._repository.find_pending_invites_by_email(
            conn, email=email, tenant_key=tenant_key
        )
        for invitation in pending_invites:
            await self._repository.update_status(
                conn,
                invitation_id=invitation.id,
                new_status_code=InviteStatus.ACCEPTED,
                now=now,
                accepted_by=user_id,
            )
            await self._auto_enroll(conn, invitation=invitation, user_id=user_id, now=now)
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="invitation",
                    entity_id=invitation.id,
                    event_type=AuditEventType.INVITE_ACCEPTED.value,
                    event_category=AuditEventCategory.AUTH.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "invite_email": email,
                        "invite_scope": invitation.scope,
                        "invite_role": invitation.role,
                        "auto_accepted_on_registration": "true",
                    },
                ),
            )

    async def _auto_enroll(self, conn, *, invitation, user_id: str, now) -> None:
        invited_engagement_ids: list[str] = []
        raw_engagement_ids = getattr(invitation, "engagement_ids", None) or []
        if raw_engagement_ids:
            invited_engagement_ids.extend(raw_engagement_ids)
        if getattr(invitation, "engagement_id", None):
            invited_engagement_ids.append(invitation.engagement_id)
        # Preserve order while avoiding duplicate provisioning when both fields reference the same engagement.
        invited_engagement_ids = list(dict.fromkeys(invited_engagement_ids))

        if invitation.scope == InviteScope.ORGANIZATION and invitation.org_id:
            membership_id = str(uuid.uuid4())
            await conn.execute(
                """
                INSERT INTO "03_auth_manage"."31_lnk_org_memberships" (
                    id, org_id, user_id, membership_type, membership_status,
                    effective_from, effective_to,
                    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
                )
                VALUES (
                    $1, $2, $3, $4, 'active',
                    $5, NULL,
                    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                    $6, $7, $8, $9, NULL, NULL
                )
                ON CONFLICT (org_id, user_id)
                DO UPDATE SET
                    membership_type = EXCLUDED.membership_type,
                    membership_status = 'active',
                    is_active = TRUE,
                    updated_at = EXCLUDED.updated_at
                """,
                membership_id,
                invitation.org_id,
                user_id,
                invitation.role or "member",
                now,
                now,
                now,
                user_id,
                user_id,
            )
            # If framework-scoped, also add workspace membership for the framework's workspace
            if getattr(invitation, "framework_id", None):
                ws_id = await conn.fetchval(
                    """
                    SELECT workspace_id::text
                    FROM "05_grc_library"."16_fct_framework_deployments"
                    WHERE id = $1::UUID AND workspace_id IS NOT NULL
                    LIMIT 1
                    """,
                    invitation.framework_id,
                )
                if ws_id:
                    ws_membership_id = str(uuid.uuid4())
                    await conn.execute(
                        """
                        INSERT INTO "03_auth_manage"."36_lnk_workspace_memberships" (
                            id, workspace_id, user_id, membership_type, membership_status,
                            effective_from, effective_to,
                            is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                            created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
                        )
                        VALUES (
                            $1, $2, $3, $4, 'active',
                            $5, NULL,
                            TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                            $6, $7, $8, $9, NULL, NULL
                        )
                        ON CONFLICT (workspace_id, user_id)
                        DO NOTHING
                        """,
                        ws_membership_id,
                        ws_id,
                        user_id,
                        "viewer",
                        now, now, now, user_id, user_id,
                    )
            # If engagement-scoped, resolve workspace from engagement
            elif getattr(invitation, "engagement_id", None):
                ws_id = await conn.fetchval(
                    """
                    SELECT fd.workspace_id::text
                    FROM "12_engagements"."10_fct_audit_engagements" e
                    JOIN "05_grc_library"."16_fct_framework_deployments" fd
                      ON fd.id = e.framework_deployment_id
                    WHERE e.id = $1::UUID AND fd.workspace_id IS NOT NULL
                    LIMIT 1
                    """,
                    invitation.engagement_id,
                )
                if ws_id:
                    ws_membership_id = str(uuid.uuid4())
                    await conn.execute(
                        """
                        INSERT INTO "03_auth_manage"."36_lnk_workspace_memberships" (
                            id, workspace_id, user_id, membership_type, membership_status,
                            effective_from, effective_to,
                            is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                            created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
                        )
                        VALUES (
                            $1, $2, $3, $4, 'active',
                            $5, NULL,
                            TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                            $6, $7, $8, $9, NULL, NULL
                        )
                        ON CONFLICT (workspace_id, user_id)
                        DO NOTHING
                        """,
                        ws_membership_id,
                        ws_id,
                        user_id,
                        "viewer",
                        now, now, now, user_id, user_id,
                    )
        elif invitation.scope == InviteScope.WORKSPACE and invitation.workspace_id:
            # Add to org first if org_id is present
            if invitation.org_id:
                org_membership_id = str(uuid.uuid4())
                await conn.execute(
                    """
                    INSERT INTO "03_auth_manage"."31_lnk_org_memberships" (
                        id, org_id, user_id, membership_type, membership_status,
                        effective_from, effective_to,
                        is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                        created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
                    )
                    VALUES (
                        $1, $2, $3, 'member', 'active',
                        $4, NULL,
                        TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                        $5, $6, $7, $8, NULL, NULL
                    )
                    ON CONFLICT (org_id, user_id)
                    DO NOTHING
                    """,
                    org_membership_id,
                    invitation.org_id,
                    user_id,
                    now,
                    now,
                    now,
                    user_id,
                    user_id,
                )
            workspace_membership_id = str(uuid.uuid4())
            await conn.execute(
                """
                INSERT INTO "03_auth_manage"."36_lnk_workspace_memberships" (
                    id, workspace_id, user_id, membership_type, membership_status,
                    effective_from, effective_to,
                    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
                )
                VALUES (
                    $1, $2, $3, $4, 'active',
                    $5, NULL,
                    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                    $6, $7, $8, $9, NULL, NULL
                )
                ON CONFLICT (workspace_id, user_id)
                DO UPDATE SET
                    membership_type = EXCLUDED.membership_type,
                    membership_status = 'active',
                    is_active = TRUE,
                    updated_at = EXCLUDED.updated_at
                """,
                workspace_membership_id,
                invitation.workspace_id,
                user_id,
                invitation.role or "viewer",
                now,
                now,
                now,
                user_id,
                user_id,
            )
            # Auto-assign GRC role group if workspace-scoped
            if invitation.grc_role_code and invitation.grc_role_code in _GRC_ROLE_CODES and invitation.workspace_id:
                await assign_workspace_member_grc_role(
                    conn,
                    workspace_id=invitation.workspace_id,
                    user_id=user_id,
                    grc_role_code=invitation.grc_role_code,
                    now=now,
                    created_by=user_id,
                )

        # ── GRC role assignment + access grants (runs for BOTH org and workspace invites) ──
        if invitation.grc_role_code and invitation.grc_role_code in _GRC_ROLE_CODES and invitation.org_id:
            _org_id = invitation.org_id
            _existing = await conn.fetchval(
                """
                SELECT id FROM "03_auth_manage"."47_lnk_grc_role_assignments"
                WHERE org_id = $1::UUID AND user_id = $2::UUID
                  AND grc_role_code = $3 AND revoked_at IS NULL
                """,
                _org_id, user_id, invitation.grc_role_code,
            )
            if not _existing:
                _ra_id = str(uuid.uuid4())
                await conn.execute(
                    """
                    INSERT INTO "03_auth_manage"."47_lnk_grc_role_assignments"
                        (id, org_id, user_id, grc_role_code, assigned_by, assigned_at, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    _ra_id, _org_id, user_id, invitation.grc_role_code,
                    user_id, now, now,
                )
                # Create workspace access grant if workspace-scoped invite
                if invitation.workspace_id:
                    await conn.execute(
                        """
                        INSERT INTO "03_auth_manage"."48_lnk_grc_access_grants"
                            (id, grc_role_assignment_id, scope_type, scope_id, granted_by, granted_at, created_at)
                        VALUES ($1, $2, 'workspace', $3, $4, $5, $6)
                        """,
                        str(uuid.uuid4()), _ra_id, invitation.workspace_id,
                        user_id, now, now,
                    )
                # Create framework access grants (array takes precedence over single)
                _fw_ids = getattr(invitation, "framework_ids", None) or []
                if not _fw_ids and getattr(invitation, "framework_id", None):
                    _fw_ids = [invitation.framework_id]
                for _fw_id in _fw_ids:
                    await conn.execute(
                        """
                        INSERT INTO "03_auth_manage"."48_lnk_grc_access_grants"
                            (id, grc_role_assignment_id, scope_type, scope_id, granted_by, granted_at, created_at)
                        VALUES ($1, $2, 'framework', $3::UUID, $4, $5, $6)
                        """,
                        str(uuid.uuid4()), _ra_id, _fw_id,
                        user_id, now, now,
                    )
                # Create engagement access grants (array takes precedence over single)
                for _eng_id in invited_engagement_ids:
                    await conn.execute(
                        """
                        INSERT INTO "03_auth_manage"."48_lnk_grc_access_grants"
                            (id, grc_role_assignment_id, scope_type, scope_id, granted_by, granted_at, created_at)
                        VALUES ($1, $2, 'engagement', $3::UUID, $4, $5, $6)
                        """,
                        str(uuid.uuid4()), _ra_id, _eng_id,
                        user_id, now, now,
                    )

            # Provision auditor engagement access/membership for every invited engagement.
            for engagement_id in invited_engagement_ids:
                inv_expires = datetime.fromisoformat(invitation.expires_at) if isinstance(invitation.expires_at, str) else invitation.expires_at
                await self._provision_engagement_access(
                    conn,
                    engagement_id=engagement_id,
                    user_id=user_id,
                    email=invitation.email,
                    tenant_key=invitation.tenant_key,
                    expires_at=inv_expires,
                    now=now,
                )

    async def _provision_engagement_access(
        self,
        conn,
        *,
        engagement_id: str,
        user_id: str,
        email: str,
        tenant_key: str,
        expires_at,
        now,
    ) -> None:
        """Create an audit access token for an engagement when an auditor accepts an invitation.

        This links the auditor's email to the engagement so they can access controls
        and evidence scoped to that engagement via the auditor workspace.

        Args:
            conn: Active asyncpg database connection.
            engagement_id: UUID of the engagement to link.
            email: Auditor's email address.
            tenant_key: Tenant for the engagement.
            expires_at: Token expiry datetime.
            now: Current timestamp.
        """
        token_id = str(uuid.uuid4())
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        # Check if engagement exists for this tenant before linking
        exists = await conn.fetchval(
            'SELECT 1 FROM "12_engagements"."10_fct_audit_engagements" WHERE id = $1::UUID AND tenant_key = $2',
            engagement_id, tenant_key,
        )
        if not exists:
            return  # Engagement not found — skip silently rather than failing the invite acceptance

        # Upsert: if token already exists for this email + engagement, skip
        existing = await conn.fetchval(
            'SELECT 1 FROM "12_engagements"."11_fct_audit_access_tokens" WHERE engagement_id = $1::UUID AND auditor_email = $2 AND is_revoked = FALSE',
            engagement_id, email,
        )
        if existing:
            return  # Already has access

        await conn.execute(
            """
            INSERT INTO "12_engagements"."11_fct_audit_access_tokens"
                (id, engagement_id, auditor_email, token_hash, expires_at, is_revoked, created_at)
            VALUES ($1::UUID, $2::UUID, $3, $4, $5, FALSE, $6)
            ON CONFLICT DO NOTHING
            """,
            token_id, engagement_id, email, token_hash, expires_at, now,
        )

        await conn.execute(
            """
            INSERT INTO "12_engagements"."12_lnk_engagement_memberships" (
                id, tenant_key, engagement_id, org_id, workspace_id, user_id, external_email,
                membership_type_code, status_code, joined_at, expires_at,
                is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                created_at, updated_at, created_by, updated_by
            )
            SELECT
                $1::UUID,
                e.tenant_key,
                e.id,
                e.org_id,
                fd.workspace_id,
                $2::UUID,
                $3,
                'external_auditor',
                'active',
                $4,
                $5,
                TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                $4, $4, $2::UUID, $2::UUID
            FROM "12_engagements"."10_fct_audit_engagements" e
            LEFT JOIN "05_grc_library"."16_fct_framework_deployments" fd ON fd.id = e.framework_deployment_id
            WHERE e.id = $6::UUID
            ON CONFLICT (engagement_id, user_id) WHERE user_id IS NOT NULL AND is_deleted = FALSE
            DO UPDATE SET
                external_email = EXCLUDED.external_email,
                status_code = 'active',
                expires_at = EXCLUDED.expires_at,
                joined_at = COALESCE("12_engagements"."12_lnk_engagement_memberships".joined_at, EXCLUDED.joined_at),
                is_active = TRUE,
                is_disabled = FALSE,
                updated_at = EXCLUDED.updated_at,
                updated_by = EXCLUDED.updated_by
            """,
            str(uuid.uuid4()), user_id, email, now, expires_at, engagement_id,
        )

        await self._audit_writer.write_entry(
            conn,
            AuditEntry(
                id=str(uuid.uuid4()),
                tenant_key=tenant_key,
                entity_type="engagement_membership",
                entity_id=engagement_id,
                event_type="engagement_membership_activated",
                event_category=AuditEventCategory.AUTH.value,
                occurred_at=now,
                actor_id=user_id,
                actor_type="user",
                properties={
                    "engagement_id": engagement_id,
                    "member_user_id": user_id,
                    "member_email": email,
                    "membership_type_code": "external_auditor",
                    "source": "invitation_acceptance",
                },
            ),
        )

    def _validate_scope_fields(
        self, scope: str, org_id: str | None, workspace_id: str | None, role: str | None
    ) -> None:
        if scope == InviteScope.PLATFORM:
            if org_id or workspace_id or role:
                raise ValidationError(
                    "Platform scope invitations must not include org_id, workspace_id, or role"
                )
        elif scope == InviteScope.ORGANIZATION:
            if not org_id:
                raise ValidationError("Organization scope requires org_id")
            if workspace_id:
                raise ValidationError("Organization scope must not include workspace_id")
            if role and role not in VALID_ORG_ROLES:
                raise ValidationError(
                    f"Invalid org role '{role}'. Valid roles: {', '.join(sorted(VALID_ORG_ROLES))}"
                )
        elif scope == InviteScope.WORKSPACE:
            if not org_id or not workspace_id:
                raise ValidationError("Workspace scope requires both org_id and workspace_id")
            if role and role not in VALID_WORKSPACE_ROLES:
                raise ValidationError(
                    f"Invalid workspace role '{role}'. Valid roles: {', '.join(sorted(VALID_WORKSPACE_ROLES))}"
                )

    async def bulk_create_invitations(
        self,
        *,
        user_id: str,
        tenant_key: str,
        request: BulkCreateInvitationRequest,
    ) -> BulkCreateInvitationResponse:
        """Send invitations to multiple emails without a campaign."""
        now = utc_now_sql()
        self._validate_scope_fields(request.scope, request.org_id, request.workspace_id, request.role)

        # Deduplicate and normalise
        seen: set[str] = set()
        emails: list[str] = []
        for raw in request.emails:
            email = raw.strip().lower()
            if email and email not in seen:
                seen.add(email)
                emails.append(email)

        if not emails:
            return BulkCreateInvitationResponse(sent=0, skipped=0, errors=0, results=[])

        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "invitation_management.create")
            pending_status_id = await self._repository.get_pending_status_id(conn)

        results: list[BulkInviteResultEntry] = []
        sent = skipped = errors = 0

        for email in emails:
            try:
                async with self._database_pool.transaction() as conn:
                    dup = await self._repository.find_pending_duplicate(
                        conn,
                        tenant_key=tenant_key,
                        email=email,
                        scope=request.scope,
                        org_id=request.org_id,
                        workspace_id=request.workspace_id,
                    )
                    if dup:
                        results.append(BulkInviteResultEntry(
                            email=email, status="skipped",
                            reason="Pending invitation already exists",
                        ))
                        skipped += 1
                        continue

                    invite_id = str(uuid.uuid4())
                    token_string, token_hash = self._generate_token(invite_id)
                    expires_at = now + timedelta(hours=request.expires_in_hours)

                    invitation = await self._repository.create_invitation(
                        conn,
                        invitation_id=invite_id,
                        tenant_key=tenant_key,
                        invite_token_hash=token_hash,
                        email=email,
                        scope=request.scope,
                        org_id=request.org_id,
                        workspace_id=request.workspace_id,
                        role=request.role,
                        grc_role_code=getattr(request, "grc_role_code", None),
                        status_id=pending_status_id,
                        invited_by=user_id,
                        expires_at=expires_at,
                        now=now,
                        source_tag=request.source_tag,
                    )
                    await self._audit_writer.write_entry(
                        conn,
                        AuditEntry(
                            id=str(uuid.uuid4()),
                            tenant_key=tenant_key,
                            entity_type="invitation",
                            entity_id=invite_id,
                            event_type=AuditEventType.INVITE_CREATED.value,
                            event_category=AuditEventCategory.AUTH.value,
                            occurred_at=now,
                            actor_id=user_id,
                            actor_type="user",
                            properties={
                                "invite_email": email,
                                "invite_scope": request.scope,
                                "invite_role": request.role,
                                "source_tag": request.source_tag,
                                "bulk": "true",
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

        await self._invalidate_caches(tenant_key)
        return BulkCreateInvitationResponse(sent=sent, skipped=skipped, errors=errors, results=results)

    async def _invalidate_caches(self, tenant_key: str) -> None:
        await self._cache.delete_pattern(f"invitations:*:{tenant_key}*")
        await self._cache.delete(f"invitations:stats:{tenant_key}")

    async def _get_invitation_by_id(self, invitation_id: str) -> InvitationResponse:
        async with self._database_pool.acquire() as conn:
            invitation = await self._repository.find_by_id(conn, invitation_id)
        if invitation is None:
            raise NotFoundError(f"Invitation '{invitation_id}' not found")
        return invitation


def _invitation_dict(inv) -> dict:
    return {
        "id": inv.id,
        "email": inv.email,
        "scope": inv.scope,
        "org_id": inv.org_id,
        "workspace_id": inv.workspace_id,
        "role": inv.role,
        "grc_role_code": getattr(inv, "grc_role_code", None),
        "engagement_id": getattr(inv, "engagement_id", None),
        "framework_id": getattr(inv, "framework_id", None),
        "framework_ids": getattr(inv, "framework_ids", None),
        "engagement_ids": getattr(inv, "engagement_ids", None),
        "status": inv.status,
        "invited_by": inv.invited_by,
        "expires_at": inv.expires_at,
        "accepted_at": inv.accepted_at,
        "accepted_by": inv.accepted_by,
        "revoked_at": inv.revoked_at,
        "revoked_by": inv.revoked_by,
        "created_at": inv.created_at,
        "updated_at": inv.updated_at,
    }
