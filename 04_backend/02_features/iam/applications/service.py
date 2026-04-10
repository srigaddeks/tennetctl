"""IAM applications service — CRUD, product links, token management, resolve-access."""

from __future__ import annotations

import importlib
import secrets
from datetime import datetime, timezone

_repo = importlib.import_module("04_backend.02_features.iam.applications.repository")
_id_mod = importlib.import_module("scripts.00_core._id")
_errors_mod = importlib.import_module("04_backend.01_core.errors")
_audit = importlib.import_module("04_backend.02_features.audit.service")
_iam_ids = importlib.import_module("04_backend.02_features.iam._iam_attr_ids")
_password = importlib.import_module("04_backend.02_features.iam.auth.password")
_rbac_repo = importlib.import_module("04_backend.02_features.iam.rbac.repository")
_ff_service = importlib.import_module("04_backend.02_features.iam.feature_flags.service")

AppError = _errors_mod.AppError

_APPLICATION_ENTITY_CODE = "platform_application"
_APP_TOKEN_WIRE_PREFIX   = "tnctl_app_"
_APP_TOKEN_PREFIX_LEN    = 16  # chars of random portion to store as prefix (after "tnctl_app_")


# ---------------------------------------------------------------------------
# Private EAV helper
# ---------------------------------------------------------------------------

async def _write_application_attrs(
    conn: object,
    application_id: str,
    attrs: dict,
    entity_type_id: int,
    *,
    description: str | None = None,
    slug: str | None = None,
    icon_url: str | None = None,
    redirect_uris: list | None = None,
    owner_user_id: str | None = None,
) -> None:
    """Write EAV attrs for an application. Only writes non-None values."""
    for attr_code, value, value_column in [
        ("description",   description,   "key_text"),
        ("slug",          slug,          "key_text"),
        ("icon_url",      icon_url,      "key_text"),
        ("redirect_uris", redirect_uris, "key_jsonb"),
        ("owner_user_id", owner_user_id, "key_text"),
    ]:
        if value is not None:
            await _repo.upsert_application_attr(
                conn,
                id=_id_mod.uuid7(),
                entity_type_id=entity_type_id,
                entity_id=application_id,
                attr_def_id=attrs[attr_code],
                value=value,
                value_column=value_column,
            )


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

async def list_applications(
    conn: object,
    *,
    limit: int = 50,
    offset: int = 0,
    category_id: int | None = None,
) -> dict:
    items, total = await _repo.list_applications(
        conn,
        limit=limit,
        offset=offset,
        category_id=category_id,
    )
    return {"items": items, "total": total, "limit": limit, "offset": offset}


async def get_application(conn: object, application_id: str) -> dict:
    app = await _repo.get_application(conn, application_id)
    if app is None:
        raise AppError(
            "APPLICATION_NOT_FOUND",
            f"Application '{application_id}' not found.",
            404,
        )
    return app


async def create_application(
    conn: object,
    *,
    code: str,
    name: str,
    category_id: int,
    description: str | None = None,
    slug: str | None = None,
    icon_url: str | None = None,
    redirect_uris: list | None = None,
    owner_user_id: str | None = None,
    actor_id: str,
    session_id: str | None = None,
    org_id_audit: str | None = None,
    workspace_id_audit: str | None = None,
) -> dict:
    # Validate category_type = 'application'
    valid = await _repo.check_category_type(conn, category_id, "application")
    if not valid:
        raise AppError(
            "INVALID_CATEGORY",
            f"Category {category_id} does not exist or is not of type 'application'.",
            422,
        )

    # Check code uniqueness
    code_taken = await _repo.check_code_exists(conn, code)
    if code_taken:
        raise AppError(
            "APPLICATION_CODE_CONFLICT",
            f"An application with code '{code}' already exists.",
            409,
        )

    application_id = _id_mod.uuid7()
    attrs = await _iam_ids.iam_attr_ids(conn, _APPLICATION_ENTITY_CODE)
    entity_type_id = await _iam_ids.iam_entity_type_id(conn, _APPLICATION_ENTITY_CODE)

    async with conn.transaction():  # type: ignore[union-attr]
        await _repo.insert_application(
            conn,
            application_id=application_id,
            code=code,
            name=name,
            category_id=category_id,
            actor_id=actor_id,
        )
        await _write_application_attrs(
            conn,
            application_id,
            attrs,
            entity_type_id,
            description=description,
            slug=slug,
            icon_url=icon_url,
            redirect_uris=redirect_uris,
            owner_user_id=owner_user_id,
        )
        await _audit.emit(
            conn,
            category="iam",
            action="application.create",
            outcome="success",
            user_id=actor_id,
            session_id=session_id,
            org_id=org_id_audit,
            workspace_id=workspace_id_audit,
            target_id=application_id,
            target_type="platform_application",
        )

    app = await _repo.get_application(conn, application_id)
    return app  # type: ignore[return-value]


async def update_application(
    conn: object,
    application_id: str,
    *,
    name: str | None = None,
    is_active: bool | None = None,
    description: str | None = None,
    slug: str | None = None,
    icon_url: str | None = None,
    redirect_uris: list | None = None,
    owner_user_id: str | None = None,
    actor_id: str,
    session_id: str | None = None,
    org_id_audit: str | None = None,
    workspace_id_audit: str | None = None,
) -> dict:
    existing = await _repo.get_application(conn, application_id)
    if existing is None:
        raise AppError(
            "APPLICATION_NOT_FOUND",
            f"Application '{application_id}' not found.",
            404,
        )

    attrs = await _iam_ids.iam_attr_ids(conn, _APPLICATION_ENTITY_CODE)
    entity_type_id = await _iam_ids.iam_entity_type_id(conn, _APPLICATION_ENTITY_CODE)

    async with conn.transaction():  # type: ignore[union-attr]
        await _repo.update_application_meta(
            conn,
            application_id,
            actor_id=actor_id,
            name=name,
            is_active=is_active,
        )
        await _write_application_attrs(
            conn,
            application_id,
            attrs,
            entity_type_id,
            description=description,
            slug=slug,
            icon_url=icon_url,
            redirect_uris=redirect_uris,
            owner_user_id=owner_user_id,
        )
        await _audit.emit(
            conn,
            category="iam",
            action="application.update",
            outcome="success",
            user_id=actor_id,
            session_id=session_id,
            org_id=org_id_audit,
            workspace_id=workspace_id_audit,
            target_id=application_id,
            target_type="platform_application",
        )

    return await _repo.get_application(conn, application_id)  # type: ignore[return-value]


async def delete_application(
    conn: object,
    application_id: str,
    *,
    actor_id: str,
    session_id: str | None = None,
    org_id_audit: str | None = None,
    workspace_id_audit: str | None = None,
) -> None:
    existing = await _repo.get_application(conn, application_id)
    if existing is None:
        raise AppError(
            "APPLICATION_NOT_FOUND",
            f"Application '{application_id}' not found.",
            404,
        )

    if existing.get("is_deleted"):
        return  # idempotent

    async with conn.transaction():  # type: ignore[union-attr]
        await _repo.soft_delete_application(conn, application_id, actor_id=actor_id)
        await _audit.emit(
            conn,
            category="iam",
            action="application.delete",
            outcome="success",
            user_id=actor_id,
            session_id=session_id,
            org_id=org_id_audit,
            workspace_id=workspace_id_audit,
            target_id=application_id,
            target_type="platform_application",
        )


# ---------------------------------------------------------------------------
# Product links
# ---------------------------------------------------------------------------

async def list_linked_products(
    conn: object,
    application_id: str,
    *,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    items, total = await _repo.list_linked_products(
        conn, application_id, limit=limit, offset=offset
    )
    return {"items": items, "total": total, "limit": limit, "offset": offset}


async def link_product(
    conn: object,
    application_id: str,
    product_id: str,
    *,
    actor_id: str,
    session_id: str | None = None,
    org_id_audit: str | None = None,
    workspace_id_audit: str | None = None,
) -> dict:
    # Validate application exists
    app = await _repo.get_application(conn, application_id)
    if app is None:
        raise AppError(
            "APPLICATION_NOT_FOUND",
            f"Application '{application_id}' not found.",
            404,
        )

    # Validate product exists (query v_products directly)
    product_rows = await _repo.list_products_by_ids(conn, [product_id])
    if not product_rows:
        raise AppError(
            "PRODUCT_NOT_FOUND",
            f"Product '{product_id}' not found.",
            404,
        )

    # Idempotency check — 409 if already linked
    existing = await _repo.get_link(conn, application_id, product_id)
    if existing is not None:
        raise AppError(
            "PRODUCT_LINK_ALREADY_EXISTS",
            f"Product '{product_id}' is already linked to application '{application_id}'.",
            409,
        )

    link_id = _id_mod.uuid7()

    async with conn.transaction():  # type: ignore[union-attr]
        link = await _repo.insert_link(
            conn,
            link_id=link_id,
            application_id=application_id,
            product_id=product_id,
            actor_id=actor_id,
        )
        await _audit.emit(
            conn,
            category="iam",
            action="application.product.link",
            outcome="success",
            user_id=actor_id,
            session_id=session_id,
            org_id=org_id_audit,
            workspace_id=workspace_id_audit,
            target_id=application_id,
            target_type="platform_application",
        )

    return link


async def unlink_product(
    conn: object,
    application_id: str,
    product_id: str,
    *,
    actor_id: str,
    session_id: str | None = None,
    org_id_audit: str | None = None,
    workspace_id_audit: str | None = None,
) -> None:
    removed = await _repo.deactivate_link(conn, application_id, product_id)
    if not removed:
        raise AppError(
            "PRODUCT_LINK_NOT_FOUND",
            f"Product '{product_id}' is not linked to application '{application_id}'.",
            404,
        )

    await _audit.emit(
        conn,
        category="iam",
        action="application.product.unlink",
        outcome="success",
        user_id=actor_id,
        session_id=session_id,
        org_id=org_id_audit,
        workspace_id=workspace_id_audit,
        target_id=application_id,
        target_type="platform_application",
    )


# ---------------------------------------------------------------------------
# Token management
# ---------------------------------------------------------------------------

async def list_tokens(conn: object, application_id: str) -> dict:
    items = await _repo.list_tokens(conn, application_id)
    return {"items": items, "total": len(items)}


async def _insert_token_inner(
    conn: object,
    *,
    application_id: str,
    name: str,
    expires_at: object,
    actor_id: str,
) -> dict:
    """Shared core for issuing a new token. Caller wraps in transaction."""
    raw_random = secrets.token_urlsafe(40)
    wire = f"{_APP_TOKEN_WIRE_PREFIX}{raw_random}"
    token_prefix = raw_random[:_APP_TOKEN_PREFIX_LEN]
    token_hash = _password.hash_token(wire)
    token_id = _id_mod.uuid7()

    await _repo.insert_token(
        conn,
        token_id=token_id,
        application_id=application_id,
        name=name,
        token_prefix=token_prefix,
        token_hash=token_hash,
        expires_at=expires_at,
        actor_id=actor_id,
    )

    return {
        "id": token_id,
        "application_id": application_id,
        "name": name,
        "token": wire,
        "token_prefix": token_prefix,
        "expires_at": expires_at,
    }


async def issue_token(
    conn: object,
    application_id: str,
    *,
    name: str,
    expires_at: object = None,
    actor_id: str,
    session_id: str | None = None,
    org_id_audit: str | None = None,
    workspace_id_audit: str | None = None,
) -> dict:
    # Validate application exists
    app = await _repo.get_application(conn, application_id)
    if app is None:
        raise AppError(
            "APPLICATION_NOT_FOUND",
            f"Application '{application_id}' not found.",
            404,
        )

    async with conn.transaction():  # type: ignore[union-attr]
        result = await _insert_token_inner(
            conn,
            application_id=application_id,
            name=name,
            expires_at=expires_at,
            actor_id=actor_id,
        )
        await _audit.emit(
            conn,
            category="iam",
            action="application.token.create",
            outcome="success",
            user_id=actor_id,
            session_id=session_id,
            org_id=org_id_audit,
            workspace_id=workspace_id_audit,
            target_id=application_id,
            target_type="platform_application",
            metadata={
                "token_id": result["id"],
                "token_prefix": result["token_prefix"],
            },
        )

    return result


async def revoke_token(
    conn: object,
    application_id: str,
    token_id: str,
    *,
    actor_id: str,
    session_id: str | None = None,
    org_id_audit: str | None = None,
    workspace_id_audit: str | None = None,
) -> None:
    token = await _repo.get_token_by_id(conn, application_id, token_id)
    if token is None:
        raise AppError(
            "TOKEN_NOT_FOUND",
            f"Token '{token_id}' not found for application '{application_id}'.",
            404,
        )

    async with conn.transaction():  # type: ignore[union-attr]
        await _repo.soft_delete_token(conn, application_id, token_id)
        await _audit.emit(
            conn,
            category="iam",
            action="application.token.revoke",
            outcome="success",
            user_id=actor_id,
            session_id=session_id,
            org_id=org_id_audit,
            workspace_id=workspace_id_audit,
            target_id=application_id,
            target_type="platform_application",
            metadata={"token_id": token_id},
        )


async def rotate_token(
    conn: object,
    application_id: str,
    token_id: str,
    *,
    name: str | None = None,
    actor_id: str,
    session_id: str | None = None,
    org_id_audit: str | None = None,
    workspace_id_audit: str | None = None,
) -> dict:
    existing_token = await _repo.get_token_by_id(conn, application_id, token_id)
    if existing_token is None:
        raise AppError(
            "TOKEN_NOT_FOUND",
            f"Token '{token_id}' not found for application '{application_id}'.",
            404,
        )

    new_name = name or (existing_token["name"] + " (rotated)")

    async with conn.transaction():  # type: ignore[union-attr]
        new_token = await _insert_token_inner(
            conn,
            application_id=application_id,
            name=new_name,
            expires_at=existing_token["expires_at"],
            actor_id=actor_id,
        )
        await _repo.soft_delete_token(conn, application_id, token_id)
        await _audit.emit(
            conn,
            category="iam",
            action="application.token.rotate",
            outcome="success",
            user_id=actor_id,
            session_id=session_id,
            org_id=org_id_audit,
            workspace_id=workspace_id_audit,
            target_id=application_id,
            target_type="platform_application",
            metadata={
                "old_token_id": token_id,
                "new_token_id": new_token["id"],
            },
        )

    return new_token


# ---------------------------------------------------------------------------
# Resolve-access
# ---------------------------------------------------------------------------

async def verify_application_token(
    conn: object, application_id: str, raw_token: str
) -> dict:
    """Verify a raw wire token and return the token row."""
    if not raw_token.startswith(_APP_TOKEN_WIRE_PREFIX):
        raise AppError("INVALID_APP_TOKEN", "Invalid application token format.", 401)

    token_prefix = raw_token[len(_APP_TOKEN_WIRE_PREFIX):][:_APP_TOKEN_PREFIX_LEN]
    row = await _repo.get_active_token_by_prefix(conn, application_id, token_prefix)
    if not row:
        raise AppError("INVALID_APP_TOKEN", "Application token not found or inactive.", 401)

    # Check expiry
    expires_at = row.get("expires_at")
    if expires_at is not None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if expires_at < now:
            raise AppError("APP_TOKEN_EXPIRED", "Application token has expired.", 401)

    # Verify hash
    if not _password.verify_token_hash(row["token_hash"], raw_token):
        raise AppError("INVALID_APP_TOKEN", "Application token verification failed.", 401)

    # Best-effort: update last_used_at
    try:
        await _repo.touch_token_last_used(conn, row["id"])
    except Exception:
        pass

    return row


async def resolve_access(
    conn: object,
    *,
    application_code: str,
    user_id: str,
    org_id: str | None,
    workspace_id: str | None,
    environment: str | None,
    application_token: str,
    actor_id: str,
    session_id: str | None,
) -> dict:
    """Resolve a user's full access context within an application.

    Returns the application metadata, user profile, roles by tier, groups,
    permissions, and fully-evaluated products/features/flags.
    """
    # 1. Resolve application
    app = await _repo.get_application_by_code(conn, application_code)
    if app is None:
        raise AppError(
            "APPLICATION_NOT_FOUND",
            f"Application '{application_code}' not found.",
            404,
        )

    # 2. Verify the application token
    await verify_application_token(conn, app["id"], application_token)

    # 3. Normalise environment
    env = environment or "prod"

    # 4. Resolve user (sanity check)
    user = await _repo.get_user_basic(conn, user_id)
    if user is None:
        raise AppError("USER_NOT_FOUND", f"User '{user_id}' not found.", 404)

    # 5. Roles by tier
    roles_by_tier = await _repo.list_user_role_codes_by_tier(
        conn, user_id=user_id, org_id=org_id, workspace_id=workspace_id
    )

    # 6. Groups (only if org_id is present)
    groups: list[dict] = []
    if org_id:
        groups = await _repo.list_user_groups_for_org(
            conn, user_id=user_id, org_id=org_id
        )

    # 7. Permissions
    permissions = await _rbac_repo.get_effective_permissions(
        conn, user_id=user_id, org_id=org_id, workspace_id=workspace_id
    )

    # Build a fast permission lookup: set of resource codes
    permitted_resources: set[str] = {p["resource"] for p in permissions}

    # 8. Product IDs linked to this application
    product_ids = await _repo.list_active_product_ids_for_application(conn, app["id"])

    if not product_ids:
        products_out: list[dict] = []
        await _audit.emit(
            conn,
            category="iam",
            action="application.access.resolve",
            outcome="success",
            user_id=actor_id,
            session_id=session_id,
            org_id=org_id,
            workspace_id=workspace_id,
            target_id=app["id"],
            target_type="platform_application",
            metadata={
                "application_code": application_code,
                "environment": env,
                "product_count": 0,
                "permission_count": len(permissions),
            },
        )
        return {
            "application": {"id": app["id"], "code": app["code"], "name": app["name"]},
            "user": {"id": user["id"], "username": user.get("username"), "email": user.get("email")},
            "scopes": {"org_id": org_id, "workspace_id": workspace_id},
            "environment": env,
            "roles": roles_by_tier,
            "groups": [{"id": g["id"], "name": g.get("name"), "slug": g.get("slug")} for g in groups],
            "products": [],
            "permissions": permissions,
        }

    # 9–10. Products
    products_rows = await _repo.list_products_by_ids(conn, product_ids)

    # 11. Features grouped by product_id
    features_list = await _repo.list_features_for_products(conn, product_ids)
    features_by_product: dict[str, list[dict]] = {}
    for feat in features_list:
        pid = feat["product_id"]
        features_by_product.setdefault(pid, []).append(feat)

    # 12. Flags grouped by feature_id (None = product-level)
    flags_list = await _repo.list_flags_for_products(conn, product_ids)
    flags_by_feature: dict[str | None, list[dict]] = {}
    for flag in flags_list:
        fid = flag.get("feature_id")
        flags_by_feature.setdefault(fid, []).append(flag)

    # 13. Evaluate each flag
    eval_results: dict[str, dict] = {}
    for flag in flags_list:
        try:
            result = await _ff_service.eval_flag(
                conn,
                flag_code=flag["code"],
                user_id=user_id,
                org_id=org_id,
                workspace_id=workspace_id,
                environment=env,
            )
            eval_results[flag["id"]] = {"value": result["value"], "type": flag.get("flag_type")}
        except Exception:
            eval_results[flag["id"]] = {"value": flag.get("default_value"), "type": flag.get("flag_type")}

    # 15. Assemble products output
    products_out = []
    for p in products_rows:
        pid = p["id"]
        feature_items = []

        # Feature-level entries
        for feat in features_by_product.get(pid, []):
            fid = feat["id"]
            is_enabled = bool(feat.get("is_active")) and (feat["code"] in permitted_resources)
            flag_items = [
                {
                    "code": fl["code"],
                    "value": eval_results.get(fl["id"], {}).get("value", fl.get("default_value")),
                    "type": fl.get("flag_type"),
                }
                for fl in flags_by_feature.get(fid, [])
            ]
            feature_items.append({
                "id": fid,
                "code": feat["code"],
                "name": feat["name"],
                "scope": feat.get("scope_code"),
                "is_enabled": is_enabled,
                "flags": flag_items,
            })

        # Product-level flags (feature_id IS NULL, matching this product)
        product_level_flags = [
            {
                "code": fl["code"],
                "value": eval_results.get(fl["id"], {}).get("value", fl.get("default_value")),
                "type": fl.get("flag_type"),
            }
            for fl in flags_by_feature.get(None, [])
            if fl.get("product_id") == pid
        ]
        if product_level_flags:
            feature_items.append({
                "id": None,
                "code": "_product",
                "name": "Product-level",
                "scope": "platform",
                "is_enabled": True,
                "flags": product_level_flags,
            })

        products_out.append({
            "id": pid,
            "code": p["code"],
            "name": p["name"],
            "features": feature_items,
        })

    # 16. Audit
    await _audit.emit(
        conn,
        category="iam",
        action="application.access.resolve",
        outcome="success",
        user_id=actor_id,
        session_id=session_id,
        org_id=org_id,
        workspace_id=workspace_id,
        target_id=app["id"],
        target_type="platform_application",
        metadata={
            "application_code": application_code,
            "environment": env,
            "product_count": len(products_out),
            "permission_count": len(permissions),
        },
    )

    # 17. Return
    return {
        "application": {"id": app["id"], "code": app["code"], "name": app["name"]},
        "user": {
            "id": user["id"],
            "username": user.get("username"),
            "email": user.get("email"),
        },
        "scopes": {"org_id": org_id, "workspace_id": workspace_id},
        "environment": env,
        "roles": roles_by_tier,
        "groups": [
            {"id": g["id"], "name": g.get("name"), "slug": g.get("slug")}
            for g in groups
        ],
        "products": products_out,
        "permissions": permissions,
    }
