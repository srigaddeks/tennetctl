"""
iam.users — service layer.

Business rules: account_type code → id resolution (ValidationError on unknown),
3 EAV attrs set on create, PATCH diff per-attr, audit emission on mutations.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.repository"
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
) -> dict:
    current = await _repo.get_by_id(conn, user_id)
    if current is None:
        raise _errors.NotFoundError(f"User {user_id!r} not found.")

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

    if is_active is not None and is_active != current["is_active"]:
        ok = await _repo.update_active(
            conn, id=user_id, is_active=is_active, updated_by=updated_by,
        )
        if not ok:
            raise _errors.NotFoundError(f"User {user_id!r} not found.")
        changed["is_active"] = is_active

    if any_attr_changed and "is_active" not in changed:
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


async def delete_user(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    user_id: str,
) -> None:
    ok = await _repo.soft_delete_user(
        conn, id=user_id, updated_by=(ctx.user_id or "sys"),
    )
    if not ok:
        raise _errors.NotFoundError(f"User {user_id!r} not found.")

    await _emit_audit(
        pool,
        ctx,
        event_key="iam.users.deleted",
        metadata={"user_id": user_id},
    )
