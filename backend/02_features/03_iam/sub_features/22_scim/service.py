"""
iam.scim — service layer.

SCIM 2.0 (RFC 7644) operations:
- Token management (create/list/revoke)
- Users: list, get, create (JIT), update, deprovision
- Groups: list, get, create, patch members
- PatchOp: simple add/replace/remove for common Okta/Azure fields
- Bearer auth: SHA256 token hash lookup on every SCIM request
"""

from __future__ import annotations

import hashlib
import re
import secrets
from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.22_scim.repository"
)
_users_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.service"
)
_users_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.repository"
)
_groups_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.05_groups.service"
)
_groups_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.05_groups.repository"
)
_orgs_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.01_orgs.repository"
)
_sessions_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.09_sessions.repository"
)

_AUDIT = "audit.events.emit"
_SCIM_ACCOUNT_TYPE = "email_password"  # SCIM provisioned users are standard email users


async def _emit(pool: Any, ctx: Any, *, event_key: str, metadata: dict, outcome: str = "success") -> None:
    try:
        await _catalog.run_node(pool, _AUDIT, ctx, {"event_key": event_key, "outcome": outcome, "metadata": metadata})
    except Exception:
        pass


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _generate_token() -> tuple[str, str]:
    raw = "scim_" + secrets.token_urlsafe(32)
    return raw, _hash_token(raw)


# ── Token management ──────────────────────────────────────────────────────────

async def create_scim_token(pool: Any, conn: Any, ctx: Any, *, org_id: str, label: str) -> tuple[dict, str]:
    raw, hashed = _generate_token()
    token_id = _core_id.uuid7()
    row = await _repo.insert_token(conn, id=token_id, org_id=org_id, label=label,
                                    token_hash=hashed, created_by=ctx.user_id or "sys")
    await _emit(pool, ctx, event_key="iam.scim.token.created", metadata={"token_id": token_id, "org_id": org_id})
    return row, raw


async def list_scim_tokens(conn: Any, org_id: str) -> list[dict]:
    return await _repo.list_tokens(conn, org_id)


async def revoke_scim_token(pool: Any, conn: Any, ctx: Any, *, token_id: str, org_id: str) -> None:
    revoked = await _repo.revoke_token(conn, token_id, org_id)
    if not revoked:
        raise _errors.NotFoundError(f"SCIM token {token_id!r} not found or already revoked")
    await _emit(pool, ctx, event_key="iam.scim.token.revoked", metadata={"token_id": token_id, "org_id": org_id})


async def authenticate_scim_request(conn: Any, *, org_slug: str, bearer: str) -> dict:
    org = await _orgs_repo.get_by_slug(conn, org_slug)
    if org is None:
        raise _errors.AppError("SCIM_ORG_NOT_FOUND", f"Org {org_slug!r} not found", 404)
    token_hash = _hash_token(bearer)
    token = await _repo.get_token_by_hash(conn, token_hash)
    if token is None:
        raise _errors.AppError("SCIM_UNAUTHORIZED", "Invalid or revoked SCIM bearer token", 401)
    if token["org_id"] != org["id"]:
        raise _errors.AppError("SCIM_UNAUTHORIZED", "Token does not belong to this org", 401)
    await _repo.touch_token(conn, token["id"])
    return org


# ── Filter parser ─────────────────────────────────────────────────────────────

def _parse_scim_filter(filter_str: str | None) -> dict:
    if not filter_str:
        return {}
    m = re.match(r'(\w+)\s+eq\s+"([^"]*)"', filter_str, re.IGNORECASE)
    if m:
        return {m.group(1).lower(): m.group(2)}
    return {}


# ── Users ─────────────────────────────────────────────────────────────────────

async def list_users(
    conn: Any, *, org_id: str, filter_str: str | None = None,
    start_index: int = 1, count: int = 100,
) -> tuple[list[dict], int]:
    parsed = _parse_scim_filter(filter_str)
    offset = max(0, start_index - 1)
    email_filter = parsed.get("username") or parsed.get("emails")

    if "externalid" in parsed:
        user = await _repo.get_user_by_external_id(conn, parsed["externalid"])
        if user is None:
            return [], 0
        enriched = await _repo.enrich_user_with_external_id(conn, user)
        return [enriched], 1

    users, total = await _users_service.list_users(conn, None, limit=count, offset=offset)
    if email_filter:
        users = [u for u in users if u.get("email", "").lower() == email_filter.lower()]
        total = len(users)

    enriched = []
    for u in users:
        enriched.append(await _repo.enrich_user_with_external_id(conn, u))
    return enriched, total


async def get_user(conn: Any, user_id: str) -> dict:
    user = await _users_repo.get_by_id(conn, user_id)
    if user is None:
        raise _errors.NotFoundError(f"User {user_id!r} not found")
    return await _repo.enrich_user_with_external_id(conn, user)


async def create_user(
    pool: Any, conn: Any, ctx: Any, *,
    user_name: str, display_name: str | None = None, active: bool = True, external_id: str | None = None,
) -> dict:
    existing = await conn.fetchrow(
        'SELECT id FROM "03_iam"."v_users" WHERE email = $1 AND deleted_at IS NULL LIMIT 1', user_name
    )
    if existing:
        raise _errors.AppError("SCIM_CONFLICT", f"User with userName {user_name!r} already exists", 409)

    if external_id:
        ext_existing = await _repo.get_user_by_external_id(conn, external_id)
        if ext_existing:
            raise _errors.AppError("SCIM_CONFLICT", f"User with externalId {external_id!r} already exists", 409)

    user = await _users_service.create_user(
        pool, conn, ctx,
        account_type=_SCIM_ACCOUNT_TYPE,
        email=user_name,
        display_name=display_name or user_name.split("@")[0],
    )

    if external_id:
        await _repo.set_external_id(conn, attr_row_id=_core_id.uuid7(),
                                    user_id=user["id"], external_id=external_id)

    if not active:
        await _users_service.deactivate_user(pool, conn, ctx, user_id=user["id"])
        user = await _users_repo.get_by_id(conn, user["id"]) or user

    await _emit(pool, ctx, event_key="iam.scim.user.created",
                metadata={"user_id": user["id"], "email": user_name, "external_id": external_id})
    return await _repo.enrich_user_with_external_id(conn, user)


async def update_user(pool: Any, conn: Any, ctx: Any, *, user_id: str, patch_ops: list[dict]) -> dict:
    user = await _users_repo.get_by_id(conn, user_id)
    if user is None:
        raise _errors.NotFoundError(f"User {user_id!r} not found")

    email: str | None = None
    display_name: str | None = None
    active: bool | None = None
    external_id: str | None = None

    for op in patch_ops:
        op_type = op.get("op", "").lower()
        path = (op.get("path") or "").lower()
        value = op.get("value")

        if op_type in ("add", "replace"):
            if path == "username" or path == "emails[type eq \"work\"].value":
                email = str(value) if value else None
            elif path == "displayname":
                display_name = str(value) if value else None
            elif path == "active":
                active = bool(value) if isinstance(value, bool) else (str(value).lower() == "true")
            elif path == "externalid":
                external_id = str(value) if value else None
            elif not path and isinstance(value, dict):
                email = value.get("userName", email)
                display_name = value.get("displayName", display_name)
                if "active" in value:
                    active = bool(value["active"])
                external_id = value.get("externalId", external_id)
        elif op_type == "remove":
            if path == "active":
                active = False

    updated = await _users_service.update_user(
        pool, conn, ctx, user_id=user_id,
        email=email, display_name=display_name, is_active=active,
    )
    if external_id is not None:
        await _repo.set_external_id(conn, attr_row_id=_core_id.uuid7(),
                                    user_id=user_id, external_id=external_id)

    await _emit(pool, ctx, event_key="iam.scim.user.updated", metadata={"user_id": user_id})
    return await _repo.enrich_user_with_external_id(conn, updated)


async def deprovision_user(pool: Any, conn: Any, ctx: Any, *, user_id: str) -> None:
    user = await _users_repo.get_by_id(conn, user_id)
    if user is None:
        raise _errors.NotFoundError(f"User {user_id!r} not found")
    await _users_service.deactivate_user(pool, conn, ctx, user_id=user_id)
    # Revoke all sessions
    await conn.execute(
        'UPDATE "03_iam"."16_fct_sessions" SET revoked_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP '
        'WHERE user_id = $1 AND revoked_at IS NULL',
        user_id,
    )
    await _emit(pool, ctx, event_key="iam.scim.user.deprovisioned",
                metadata={"user_id": user_id, "email": user.get("email")})


# ── Groups ────────────────────────────────────────────────────────────────────

async def list_groups(conn: Any, *, org_id: str, filter_str: str | None = None,
                      start_index: int = 1, count: int = 100) -> tuple[list[dict], int]:
    offset = max(0, start_index - 1)
    groups, total = await _groups_repo.list_groups(conn, org_id=org_id, limit=count, offset=offset)
    parsed = _parse_scim_filter(filter_str)
    if "displayname" in parsed:
        groups = [g for g in groups if g.get("label", "").lower() == parsed["displayname"].lower()]
        total = len(groups)
    return groups, total


async def get_group(conn: Any, group_id: str) -> dict:
    group = await _groups_repo.get_by_id(conn, group_id)
    if group is None:
        raise _errors.NotFoundError(f"Group {group_id!r} not found")
    members = await _repo.get_group_members(conn, group_id)
    return {**group, "_members": members}


async def create_group(
    pool: Any, conn: Any, ctx: Any, *,
    org_id: str, display_name: str, members: list[str] | None = None,
) -> dict:
    code = re.sub(r"[^a-z0-9_]", "_", display_name.lower())[:50]
    group = await _groups_service.create_group(pool, conn, ctx, org_id=org_id, code=code, label=display_name)
    if members:
        for user_id in members:
            try:
                await _repo.add_user_to_group(
                    conn, lnk_id=_core_id.uuid7(), user_id=user_id,
                    group_id=group["id"], org_id=org_id, created_by=ctx.user_id or "sys",
                )
            except Exception:
                pass
    await _emit(pool, ctx, event_key="iam.scim.group.created", metadata={"group_id": group["id"], "org_id": org_id})
    actual_members = await _repo.get_group_members(conn, group["id"])
    return {**group, "_members": actual_members}


async def patch_group(pool: Any, conn: Any, ctx: Any, *, group_id: str, org_id: str, patch_ops: list[dict]) -> dict:
    group = await _groups_repo.get_by_id(conn, group_id)
    if group is None:
        raise _errors.NotFoundError(f"Group {group_id!r} not found")

    for op in patch_ops:
        op_type = op.get("op", "").lower()
        path = (op.get("path") or "").lower()
        value = op.get("value")

        if op_type in ("add", "replace") and "members" in path:
            member_list = value if isinstance(value, list) else ([value] if value else [])
            for m in member_list:
                uid = m.get("value") if isinstance(m, dict) else str(m)
                try:
                    await _repo.add_user_to_group(
                        conn, lnk_id=_core_id.uuid7(), user_id=uid,
                        group_id=group_id, org_id=org_id, created_by=ctx.user_id or "sys",
                    )
                except Exception:
                    pass
        elif op_type == "remove" and "members" in path:
            member_list = value if isinstance(value, list) else ([value] if value else [])
            for m in member_list:
                uid = m.get("value") if isinstance(m, dict) else str(m)
                await _repo.remove_user_from_group(conn, user_id=uid, group_id=group_id)
        elif op_type == "replace" and not path and isinstance(value, dict):
            if "displayName" in value:
                await _groups_service.update_group(pool, conn, ctx, group_id=group_id, label=value["displayName"])
            if "members" in value:
                for m in (value["members"] or []):
                    uid = m.get("value") if isinstance(m, dict) else str(m)
                    try:
                        await _repo.add_user_to_group(
                            conn, lnk_id=_core_id.uuid7(), user_id=uid,
                            group_id=group_id, org_id=org_id, created_by=ctx.user_id or "sys",
                        )
                    except Exception:
                        pass

    await _emit(pool, ctx, event_key="iam.scim.group.updated", metadata={"group_id": group_id, "org_id": org_id})
    updated_group = await _groups_repo.get_by_id(conn, group_id) or group
    actual_members = await _repo.get_group_members(conn, group_id)
    return {**updated_group, "_members": actual_members}


async def delete_group(pool: Any, conn: Any, ctx: Any, *, group_id: str, org_id: str) -> None:
    group = await _groups_repo.get_by_id(conn, group_id)
    if group is None:
        raise _errors.NotFoundError(f"Group {group_id!r} not found")
    await _groups_service.delete_group(pool, conn, ctx, group_id=group_id)
    await _emit(pool, ctx, event_key="iam.scim.group.deleted", metadata={"group_id": group_id, "org_id": org_id})
