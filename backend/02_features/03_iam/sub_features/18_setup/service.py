"""
iam.setup — first-run setup service.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.18_setup.repository"
)
_users_svc: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.service"
)
_creds_svc: Any = import_module(
    "backend.02_features.03_iam.sub_features.08_credentials.service"
)
_otp_svc: Any = import_module(
    "backend.02_features.03_iam.sub_features.12_otp.service"
)
_sessions_svc: Any = import_module(
    "backend.02_features.03_iam.sub_features.09_sessions.service"
)

_AUDIT_NODE_KEY = "audit.events.emit"
_SYSTEM_INITIALIZED_KEY = "system.initialized"


async def check_setup_required(conn: Any) -> bool:
    """Return True when zero active users exist (setup mode active)."""
    count = await _repo.count_users(conn)
    return count == 0


async def _ensure_platform_admin_role(conn: Any, created_by: str) -> str:
    """Get or create the global platform_admin system role. Returns role_id."""
    existing = await _repo.get_role_by_code(conn, "platform_admin")
    if existing is not None:
        return existing["id"]

    _roles_repo: Any = import_module(
        "backend.02_features.03_iam.sub_features.04_roles.repository"
    )
    role_type_id = await _roles_repo.get_role_type_id(conn, "system")
    if role_type_id is None:
        raise RuntimeError("dim_role_types missing 'system' row — re-run seeds.")

    role_id = _core_id.uuid7()
    await _roles_repo.insert_role(
        conn,
        id=role_id,
        org_id=None,
        role_type_id=role_type_id,
        created_by=created_by,
    )
    # Set code + label via EAV attrs (roles use EAV, not columns).
    await _roles_repo.set_attr(
        conn,
        role_id=role_id,
        attr_code="code",
        value="platform_admin",
        attr_row_id=_core_id.uuid7(),
    )
    await _roles_repo.set_attr(
        conn,
        role_id=role_id,
        attr_code="label",
        value="Platform Admin",
        attr_row_id=_core_id.uuid7(),
    )
    return role_id


async def complete_initial_admin(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    email: str,
    password: str,
    display_name: str,
    vault_client: Any,
) -> dict:
    """Create the initial super-admin user.

    Returns dict with: user_id, email, display_name, totp_credential_id,
    otpauth_uri, backup_codes, session_token, session.
    """
    # AC-4: idempotency — reject if any users exist.
    user_count = await _repo.count_users(conn)
    if user_count > 0:
        raise _errors.AppError(
            "ALREADY_INITIALIZED",
            "System is already initialized. Cannot create another initial admin.",
            409,
        )

    created_by = "sys"

    # 1. Create user (email_password account type).
    user = await _users_svc.create_user(
        pool, conn, ctx,
        account_type="email_password",
        email=email,
        display_name=display_name,
    )
    user_id = user["id"]

    # 2. Set password credential (hashed + peppered via vault).
    await _creds_svc.set_password(
        conn,
        vault_client=vault_client,
        user_id=user_id,
        value=password,
    )

    # 3. Ensure platform_admin role record exists (best-effort; no org assignment yet
    #    because lnk_user_roles requires a non-null org_id FK).
    try:
        await _ensure_platform_admin_role(conn, created_by)
    except Exception:
        pass

    # 4. Generate TOTP + backup codes with user-scoped context.
    from dataclasses import replace as _replace
    ctx_with_user = _replace(ctx, user_id=user_id)

    totp_result = await _otp_svc.setup_totp(
        pool, conn, ctx_with_user,
        user_id=user_id,
        device_name="Initial admin device",
        vault_client=vault_client,
    )

    backup_codes = await _otp_svc.generate_backup_codes(
        conn, pool, ctx_with_user, user_id=user_id,
    )

    # 5. Set vault config system.initialized = true.
    _configs_svc: Any = import_module(
        "backend.02_features.02_vault.sub_features.02_configs.service"
    )
    _configs_repo: Any = import_module(
        "backend.02_features.02_vault.sub_features.02_configs.repository"
    )
    existing_cfg = await _configs_repo.get_by_scope_key(
        conn, scope="global", org_id=None, workspace_id=None,
        key=_SYSTEM_INITIALIZED_KEY,
    )
    if existing_cfg is None:
        await _configs_svc.create_config(
            pool, conn, ctx_with_user,
            key=_SYSTEM_INITIALIZED_KEY,
            value_type="boolean",
            value=True,
            description="Set to true after the initial admin is created.",
            scope="global",
        )
    else:
        await _configs_svc.update_config(
            pool, conn, ctx_with_user,
            config_id=existing_cfg["id"],
            value=True,
        )

    # 6. Mint session.
    session_token, session = await _sessions_svc.mint_session(
        conn, vault_client=vault_client, user_id=user_id, org_id=None,
    )

    # 7. Emit audit (best-effort).
    try:
        await _catalog.run_node(
            pool, _AUDIT_NODE_KEY, ctx_with_user,
            {
                "event_key": "iam.setup.completed",
                "outcome": "success",
                "metadata": {"user_id": user_id, "email": email},
            },
        )
    except Exception:
        pass

    return {
        "user_id": user_id,
        "email": email,
        "display_name": display_name,
        "totp_credential_id": totp_result["credential_id"],
        "otpauth_uri": totp_result["otpauth_uri"],
        "backup_codes": backup_codes,
        "session_token": session_token,
        "session": dict(session) if session else {},
    }
