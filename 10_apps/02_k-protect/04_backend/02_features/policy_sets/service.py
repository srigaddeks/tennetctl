"""kprotect policy_sets service — CRUD + member management + cache invalidation."""

from __future__ import annotations

import importlib
import uuid

_repo = importlib.import_module("02_features.policy_sets.repository")
_errors_mod = importlib.import_module("01_core.errors")
_valkey_mod = importlib.import_module("01_core.valkey")

AppError = _errors_mod.AppError


def _cache_client():
    return _valkey_mod.get_client()


async def _invalidate_org_cache(org_id: str) -> None:
    """Invalidate all policy-set cache keys for this org."""
    try:
        client = _cache_client()
        pattern = f"kp:policyset:{org_id}:*"
        cursor = 0
        while True:
            cursor, keys = await client.scan(cursor, match=pattern, count=100)
            if keys:
                await client.delete(*keys)
            if cursor == 0:
                break
    except Exception:
        pass


async def list_policy_sets(
    conn: object,
    org_id: str,
    *,
    limit: int,
    offset: int,
) -> dict:
    items_raw = await _repo.list_policy_sets(conn, org_id, limit=limit, offset=offset)
    total = await _repo.count_policy_sets(conn, org_id)

    # Attach member list to each set
    items = []
    for row in items_raw:
        members = await _repo.get_set_selections(conn, row["id"])
        items.append({**row, "members": members})

    return {"items": items, "total": total, "limit": limit, "offset": offset}


async def get_policy_set(conn: object, policy_set_id: str) -> dict:
    row = await _repo.get_policy_set(conn, policy_set_id)
    if row is None:
        raise AppError("POLICY_SET_NOT_FOUND", f"Policy set '{policy_set_id}' not found.", 404)
    members = await _repo.get_set_selections(conn, policy_set_id)
    return {**row, "members": members}


async def create_policy_set(
    conn: object,
    *,
    org_id: str,
    code: str,
    name: str,
    description: str | None,
    evaluation_mode: str,
    is_default: bool,
    member_selection_ids: list[dict],
    actor_id: str,
) -> dict:
    set_id = str(uuid.uuid4())

    async with conn.transaction():  # type: ignore[union-attr]
        await _repo.create_policy_set(
            conn,
            set_id=set_id,
            org_id=org_id,
            is_default=is_default,
            actor_id=actor_id,
        )
        # Store string attrs via EAV
        for attr_code, value in [
            ("code", code),
            ("name", name),
            ("evaluation_mode", evaluation_mode),
        ]:
            await _repo.upsert_policy_set_attr(
                conn,
                set_id=set_id,
                attr_code=attr_code,
                value=value,
                actor_id=actor_id,
            )
        if description is not None:
            await _repo.upsert_policy_set_attr(
                conn,
                set_id=set_id,
                attr_code="description",
                value=description,
                actor_id=actor_id,
            )
        # Add member links
        for member in member_selection_ids:
            await _repo.add_selection_to_set(
                conn,
                set_id=set_id,
                selection_id=member["selection_id"],
                sort_order=member["sort_order"],
                org_id=org_id,
                actor_id=actor_id,
            )

    await _invalidate_org_cache(org_id)
    return await get_policy_set(conn, set_id)


async def patch_policy_set(
    conn: object,
    policy_set_id: str,
    *,
    name: str | None,
    description: str | None,
    evaluation_mode: str | None,
    is_default: bool | None,
    member_selection_ids: list[dict] | None,
    actor_id: str,
) -> dict:
    existing = await _repo.get_policy_set(conn, policy_set_id)
    if existing is None:
        raise AppError("POLICY_SET_NOT_FOUND", f"Policy set '{policy_set_id}' not found.", 404)

    org_id = existing["org_id"]

    async with conn.transaction():  # type: ignore[union-attr]
        # Update fact-row columns that live there (is_default)
        if is_default is not None:
            await conn.execute(  # type: ignore[union-attr]
                """
                UPDATE "11_kprotect"."11_fct_policy_sets"
                   SET is_default  = $2,
                       updated_by  = $3,
                       updated_at  = CURRENT_TIMESTAMP
                 WHERE id = $1
                """,
                policy_set_id,
                is_default,
                actor_id,
            )
        else:
            await conn.execute(  # type: ignore[union-attr]
                """
                UPDATE "11_kprotect"."11_fct_policy_sets"
                   SET updated_by  = $2,
                       updated_at  = CURRENT_TIMESTAMP
                 WHERE id = $1
                """,
                policy_set_id,
                actor_id,
            )

        # Update EAV attrs
        for attr_code, value in [
            ("name", name),
            ("description", description),
            ("evaluation_mode", evaluation_mode),
        ]:
            if value is not None:
                await _repo.upsert_policy_set_attr(
                    conn,
                    set_id=policy_set_id,
                    attr_code=attr_code,
                    value=value,
                    actor_id=actor_id,
                )

        # Rewrite member list if provided
        if member_selection_ids is not None:
            await _repo.clear_set_selections(conn, policy_set_id)
            for member in member_selection_ids:
                await _repo.add_selection_to_set(
                    conn,
                    set_id=policy_set_id,
                    selection_id=member["selection_id"],
                    sort_order=member["sort_order"],
                    org_id=org_id,
                    actor_id=actor_id,
                )

    await _invalidate_org_cache(org_id)
    return await get_policy_set(conn, policy_set_id)


async def delete_policy_set(
    conn: object,
    policy_set_id: str,
    *,
    actor_id: str,
) -> None:
    existing = await _repo.get_policy_set(conn, policy_set_id)
    if existing is None:
        raise AppError("POLICY_SET_NOT_FOUND", f"Policy set '{policy_set_id}' not found.", 404)

    await _repo.soft_delete_policy_set(conn, policy_set_id, actor_id=actor_id)
    await _invalidate_org_cache(existing["org_id"])
