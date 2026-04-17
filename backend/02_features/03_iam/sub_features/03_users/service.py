"""
iam.users — service layer.

Business rules: account_type code → id resolution (ValidationError on unknown),
3 EAV attrs set on create, PATCH diff per-attr, audit emission on mutations.

Status lifecycle:
  active   ↔ inactive  (reversible — deactivate/reactivate)
  any      →  deleted  (one-way — pseudonymizes PII, preserves audit FKs)
"""

from __future__ import annotations

import hashlib
from typing import Any

from importlib import import_module

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.repository"
)
_sessions_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.09_sessions.repository"
)

_AUDIT_NODE_KEY = "audit.events.emit"


async def _emit_audit(pool: Any, ctx: Any, *, event_key: str, metadata: dict, outcome: str = "success") -> None:
    await _catalog.run_node(
        pool,
        _AUDIT_NODE_KEY,
        ctx,
        {"event_key": event_key, "outcome": outcome, "metadata": metadata},
    )


async def create_user(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    account_type: str,
    email: str,
    display_name: str,
    avatar_url: str | None = None,
) -> dict:
    account_type_id = await _repo.get_account_type_id(conn, account_type)
    if account_type_id is None:
        raise _errors.ValidationError(
            f"unknown account_type {account_type!r}; "
            f"must be one of email_password / magic_link / google_oauth / github_oauth"
        )

    user_id = _core_id.uuid7()
    created_by = ctx.user_id or "sys"

    await _repo.insert_user(
        conn,
        id=user_id,
        account_type_id=account_type_id,
        created_by=created_by,
    )
    await _repo.set_attr(
        conn,
        user_id=user_id,
        attr_code="email",
        value=email,
        attr_row_id=_core_id.uuid7(),
    )
    await _repo.set_attr(
        conn,
        user_id=user_id,
        attr_code="display_name",
        value=display_name,
        attr_row_id=_core_id.uuid7(),
    )
    if avatar_url is not None:
        await _repo.set_attr(
            conn,
            user_id=user_id,
            attr_code="avatar_url",
            value=avatar_url,
            attr_row_id=_core_id.uuid7(),
        )

    await _emit_audit(
        pool,
        ctx,
        event_key="iam.users.created",
        metadata={"user_id": user_id, "account_type": account_type, "email": email},
    )

    created = await _repo.get_by_id(conn, user_id)
    if created is None:
        raise RuntimeError(f"user {user_id} not visible after insert")
    return created


async def get_user(conn: Any, _ctx: Any, *, user_id: str) -> dict | None:
    return await _repo.get_by_id(conn, user_id)


async def list_users(
    conn: Any,
    _ctx: Any,
    *,
    limit: int = 50,
    offset: int = 0,
    account_type: str | None = None,
    is_active: bool | None = None,
) -> tuple[list[dict], int]:
    return await _repo.list_users(
        conn,
        limit=limit,
        offset=offset,
        account_type=account_type,
        is_active=is_active,
    )


async def update_user(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    user_id: str,
    email: str | None = None,
    display_name: str | None = None,
    avatar_url: str | None = None,
    is_active: bool | None = None,
    status: str | None = None,
) -> dict:
    current = await _repo.get_by_id(conn, user_id)
    if current is None:
        raise _errors.NotFoundError(f"User {user_id!r} not found.")

    # `status` takes precedence over deprecated `is_active`
    resolved_active: bool | None = None
    if status is not None:
        resolved_active = status == "active"
    elif is_active is not None:
        resolved_active = is_active

    # Handle status transitions as distinct operations with proper audit events.
    if resolved_active is not None and resolved_active != current["is_active"]:
        if resolved_active:
            return await reactivate_user(pool, conn, ctx, user_id=user_id)
        else:
            return await deactivate_user(pool, conn, ctx, user_id=user_id)

    changed: dict[str, object] = {}
    updated_by = ctx.user_id or "sys"

    attr_changes = {
        "email": (email, current.get("email")),
        "display_name": (display_name, current.get("display_name")),
        "avatar_url": (avatar_url, current.get("avatar_url")),
    }
    any_attr_changed = False
    for code, (new_val, cur_val) in attr_changes.items():
        if new_val is not None and new_val != cur_val:
            await _repo.set_attr(
                conn,
                user_id=user_id,
                attr_code=code,
                value=new_val,
                attr_row_id=_core_id.uuid7(),
            )
            changed[code] = new_val
            any_attr_changed = True

    if any_attr_changed:
        await _repo.touch_user(conn, id=user_id, updated_by=updated_by)

    if not changed:
        return current

    await _emit_audit(
        pool,
        ctx,
        event_key="iam.users.updated",
        metadata={"user_id": user_id, "changed": sorted(changed.keys())},
    )

    updated = await _repo.get_by_id(conn, user_id)
    if updated is None:
        raise RuntimeError(f"user {user_id} vanished after update")
    return updated


async def deactivate_user(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    user_id: str,
) -> dict:
    """Reversibly deactivate a user: sets is_active=False, revokes all sessions,
    blocks future sign-ins. Does NOT pseudonymize any PII."""
    current = await _repo.get_by_id(conn, user_id)
    if current is None:
        raise _errors.NotFoundError(f"User {user_id!r} not found.")

    updated_by = ctx.user_id or "sys"
    ok = await _repo.update_active(conn, id=user_id, is_active=False, updated_by=updated_by)
    if not ok:
        raise _errors.NotFoundError(f"User {user_id!r} not found.")

    # Revoke all active sessions.
    await _sessions_repo.revoke_all_for_user(conn, user_id=user_id, updated_by=updated_by)

    await _emit_audit(
        pool,
        ctx,
        event_key="iam.users.deactivated",
        metadata={"user_id": user_id},
    )

    updated = await _repo.get_by_id(conn, user_id)
    if updated is None:
        raise RuntimeError(f"user {user_id} vanished after deactivation")
    return updated


async def reactivate_user(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    user_id: str,
) -> dict:
    """Restore a deactivated user to active status. Does not mint new sessions."""
    current = await _repo.get_by_id(conn, user_id)
    if current is None:
        raise _errors.NotFoundError(f"User {user_id!r} not found.")

    updated_by = ctx.user_id or "sys"
    ok = await _repo.update_active(conn, id=user_id, is_active=True, updated_by=updated_by)
    if not ok:
        raise _errors.NotFoundError(f"User {user_id!r} not found.")

    await _emit_audit(
        pool,
        ctx,
        event_key="iam.users.reactivated",
        metadata={"user_id": user_id},
    )

    updated = await _repo.get_by_id(conn, user_id)
    if updated is None:
        raise RuntimeError(f"user {user_id} vanished after reactivation")
    return updated


async def delete_user(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    user_id: str,
) -> None:
    """Soft-delete + pseudonymize a user (one-way, GDPR-compliant).

    Replaces email / display_name / avatar_url with anonymous placeholders.
    Preserves the fct row so audit FKs remain valid. Original email is stored
    as a one-way SHA-256 hash in the audit event for forensic recovery within
    the audit retention window.
    """
    current = await _repo.get_by_id(conn, user_id)
    if current is None:
        raise _errors.NotFoundError(f"User {user_id!r} not found.")

    updated_by = ctx.user_id or "sys"
    original_email = current.get("email") or ""
    email_hash = hashlib.sha256(original_email.encode()).hexdigest() if original_email else ""

    # Pseudonymize PII attrs.
    pseudo_email = f"deleted-{_core_id.uuid7()}@removed.local"
    await _repo.set_attr(
        conn,
        user_id=user_id,
        attr_code="email",
        value=pseudo_email,
        attr_row_id=_core_id.uuid7(),
    )
    await _repo.set_attr(
        conn,
        user_id=user_id,
        attr_code="display_name",
        value="[deleted user]",
        attr_row_id=_core_id.uuid7(),
    )
    # Clear avatar_url by setting to empty string (will be exposed as empty/None via view).
    if current.get("avatar_url"):
        await _repo.set_attr(
            conn,
            user_id=user_id,
            attr_code="avatar_url",
            value="",
            attr_row_id=_core_id.uuid7(),
        )

    # Revoke all active sessions.
    await _sessions_repo.revoke_all_for_user(conn, user_id=user_id, updated_by=updated_by)

    # Soft-delete the fct row.
    ok = await _repo.soft_delete_user(conn, id=user_id, updated_by=updated_by)
    if not ok:
        raise _errors.NotFoundError(f"User {user_id!r} not found.")

    await _emit_audit(
        pool,
        ctx,
        event_key="iam.users.deleted",
        metadata={
            "user_id": user_id,
            "original_email_hash": email_hash,
            "pseudonymized_email": pseudo_email,
        },
    )
