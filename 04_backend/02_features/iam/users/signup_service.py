"""IAM signup service — public user self-registration.

Creates a user + optional org + workspace + memberships + roles in one
atomic transaction and returns a session so the caller is immediately
authenticated.
"""

from __future__ import annotations

import importlib
import random
import re
import string

_id_mod = importlib.import_module("scripts.00_core._id")
_errors_mod = importlib.import_module("04_backend.01_core.errors")
_password_mod = importlib.import_module("04_backend.02_features.iam.auth.password")
_audit = importlib.import_module("04_backend.02_features.audit.service")
_iam_ids = importlib.import_module("04_backend.02_features.iam._iam_attr_ids")
_sessions_repo = importlib.import_module("04_backend.02_features.iam.sessions.repository")
_jwt = importlib.import_module("04_backend.01_core.jwt_utils")
_settings = importlib.import_module("04_backend.01_core.settings")
_orgs_svc = importlib.import_module("04_backend.02_features.iam.orgs.service")
_workspaces_svc = importlib.import_module("04_backend.02_features.iam.workspaces.service")
_memberships_svc = importlib.import_module("04_backend.02_features.iam.memberships.service")
_rbac_repo = importlib.import_module("04_backend.02_features.iam.rbac.repository")

AppError = _errors_mod.AppError


def _derive_slug(name: str) -> str:
    """Convert a display name to a URL-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug[:64] or "org"


def _random_suffix(length: int = 4) -> str:
    """Return a random alphanumeric suffix (3-5 chars)."""
    n = random.randint(3, min(5, length))
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


async def _is_org_attr_taken(conn: object, attr_def_id: int, value: str) -> bool:
    """Check if any org already uses this value for the given EAV attr."""
    row = await conn.fetchval(  # type: ignore[union-attr]
        """
        SELECT 1 FROM "03_iam"."20_dtl_attrs"
         WHERE attr_def_id = $1 AND key_text = $2
         LIMIT 1
        """,
        attr_def_id,
        value,
    )
    return row is not None


async def _ensure_unique_org_name(conn: object, name: str) -> str:
    """Return `name` if no org with that name/slug exists, else append a random suffix.

    Checks both the name and derived slug for uniqueness — the DB has a unique
    constraint on slug so both must be collision-free.
    """
    attrs = await _iam_ids.iam_attr_ids(conn, "iam_org")
    name_attr_id = attrs.get("name")
    slug_attr_id = attrs.get("slug")
    if name_attr_id is None:
        return name

    # Check if the base name + slug are both available
    name_taken = await _is_org_attr_taken(conn, name_attr_id, name)
    slug_taken = slug_attr_id and await _is_org_attr_taken(conn, slug_attr_id, _derive_slug(name))
    if not name_taken and not slug_taken:
        return name

    # Try up to 5 times with a random suffix
    for _ in range(5):
        suffix = _random_suffix()
        candidate = f"{name} {suffix}"
        candidate_slug = _derive_slug(candidate)
        n_taken = await _is_org_attr_taken(conn, name_attr_id, candidate)
        s_taken = slug_attr_id and await _is_org_attr_taken(conn, slug_attr_id, candidate_slug)
        if not n_taken and not s_taken:
            return candidate

    # Fallback: use uuid fragment
    return f"{name} {_id_mod.uuid7()[:8]}"


async def _check_username_taken(conn: object, username: str) -> bool:
    row = await conn.fetchrow(  # type: ignore[union-attr]
        "SELECT id FROM \"03_iam\".\"20_dtl_attrs\" "
        "WHERE key_text = $1 AND attr_def_id = ("
        "  SELECT d.id FROM \"03_iam\".\"07_dim_attr_defs\" d"
        "  JOIN \"03_iam\".\"06_dim_entity_types\" et ON d.entity_type_id = et.id"
        "  WHERE et.code = 'iam_user' AND d.code = 'username'"
        ")",
        username,
    )
    return row is not None


async def _insert_user(
    conn: object,
    *,
    user_id: str,
    username: str,
    password: str,
    email: str | None,
    display_name: str | None,
    account_type_code: str,
) -> None:
    """Insert fct_users row + EAV attrs."""
    account_type_id = await conn.fetchval(  # type: ignore[union-attr]
        "SELECT id FROM \"03_iam\".\"06_dim_account_types\" WHERE code = $1",
        "personal" if account_type_code == "personal" else "default",
    )
    if account_type_id is None:
        # Fallback to any non-admin account type
        account_type_id = await conn.fetchval(  # type: ignore[union-attr]
            "SELECT id FROM \"03_iam\".\"06_dim_account_types\" LIMIT 1 OFFSET 1"
        )

    auth_type_id = await conn.fetchval(  # type: ignore[union-attr]
        "SELECT id FROM \"03_iam\".\"07_dim_auth_types\" WHERE code = 'username_password'"
    )

    password_hash = _password_mod.hash_password(password)

    await conn.execute(  # type: ignore[union-attr]
        """
        INSERT INTO "03_iam"."10_fct_users"
            (id, account_type_id, auth_type_id,
             is_active, is_test, created_by, updated_by, created_at, updated_at)
        VALUES ($1, $2, $3, TRUE, FALSE, $1, $1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        user_id,
        account_type_id,
        auth_type_id,
    )

    attrs = await _iam_ids.iam_attr_ids(conn, "iam_user")
    entity_type_id = await _iam_ids.iam_entity_type_id(conn, "iam_user")

    eav = [("username", username), ("password_hash", password_hash)]
    if email:
        eav.append(("email", email))
    if display_name:
        eav.append(("display_name", display_name))

    for attr_code, value in eav:
        attr_id = attrs.get(attr_code)
        if attr_id is None:
            continue
        await conn.execute(  # type: ignore[union-attr]
            """
            INSERT INTO "03_iam"."20_dtl_attrs"
                (id, entity_type_id, entity_id, attr_def_id,
                 key_text, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (entity_id, attr_def_id)
            DO UPDATE SET key_text = EXCLUDED.key_text, updated_at = CURRENT_TIMESTAMP
            """,
            _id_mod.uuid7(),
            entity_type_id,
            user_id,
            attr_id,
            value,
        )


async def _issue_session(
    conn: object,
    *,
    user_id: str,
    org_id: str | None,
    workspace_id: str | None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> dict:
    """Issue a fresh session for a newly-created user and return tokens."""
    import datetime as dt  # noqa: PLC0415
    from datetime import timezone  # noqa: PLC0415

    def _utcnow():
        return dt.datetime.now(timezone.utc).replace(tzinfo=None)

    access_ttl = _settings.get_int("03_iam", "jwt_access_ttl_seconds", default=900)
    refresh_ttl = _settings.get_int("03_iam", "jwt_refresh_ttl_seconds", default=604800)
    absolute_ttl = _settings.get_int("03_iam", "session_absolute_ttl_seconds", default=2592000)

    session_id = _id_mod.uuid7()

    access_token = await _jwt.issue_token(
        user_id,
        access_ttl,
        session_id=session_id,
        org_id=org_id,
        workspace_id=workspace_id,
    )
    access_payload = _jwt.verify_token(access_token)
    jti: str = access_payload["jti"]

    raw_refresh = _jwt.generate_refresh_token()
    refresh_hash = _password_mod.hash_token(raw_refresh)

    now = _utcnow()
    expires_at = now + dt.timedelta(seconds=access_ttl)
    refresh_expires_at = now + dt.timedelta(seconds=refresh_ttl)
    absolute_expires_at = now + dt.timedelta(seconds=absolute_ttl)

    session_status_active = await conn.fetchval(  # type: ignore[union-attr]
        "SELECT id FROM \"03_iam\".\"08_dim_session_statuses\" WHERE code = 'active'"
    )
    attrs = await _iam_ids.iam_attr_ids(conn, "iam_session")
    entity_type_id = await _iam_ids.iam_entity_type_id(conn, "iam_session")

    await _sessions_repo.insert_session(conn, id=session_id, user_id=user_id, status_id=session_status_active)

    token_prefix = access_token[:16]
    refresh_prefix = raw_refresh[:16]

    eav_entries = [
        ("jti", jti),
        ("token_prefix", token_prefix),
        ("refresh_token_hash", refresh_hash),
        ("refresh_token_prefix", refresh_prefix),
        ("refresh_expires_at", refresh_expires_at.isoformat(timespec="seconds")),
        ("expires_at", expires_at.isoformat(timespec="seconds")),
        ("absolute_expires_at", absolute_expires_at.isoformat(timespec="seconds")),
    ]
    if ip_address:
        eav_entries.append(("ip_address", ip_address))
    if user_agent:
        eav_entries.append(("user_agent", user_agent))
    if org_id:
        eav_entries.append(("active_org_id", org_id))
    if workspace_id:
        eav_entries.append(("active_workspace_id", workspace_id))

    for attr_code, value in eav_entries:
        attr_id = attrs.get(attr_code)
        if attr_id is None:
            continue
        await _sessions_repo.upsert_session_attr(
            conn,
            id=_id_mod.uuid7(),
            entity_type_id=entity_type_id,
            entity_id=session_id,
            attr_def_id=attr_id,
            value=value,
        )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": raw_refresh,
        "expires_in": access_ttl,
        "session_id": session_id,
        "org_id": org_id,
        "workspace_id": workspace_id,
    }


async def signup(
    conn: object,
    *,
    username: str,
    password: str,
    email: str | None = None,
    display_name: str | None = None,
    account_type: str = "personal",
    org_name: str | None = None,
    default_workspace_name: str = "kbio",
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> dict:
    """Public self-registration.

    Creates a user and, when org_name is provided, an org + default workspace,
    adds the user as a member of both, and assigns them org_admin + workspace_admin
    system roles. Returns the user dict and a fresh session (tokens).

    Raises:
        AppError(409) if username is already taken.
    """
    if await _check_username_taken(conn, username):
        raise AppError("USERNAME_TAKEN", f"Username '{username}' is already taken.", 409)

    user_id = _id_mod.uuid7()
    org: dict | None = None
    workspace: dict | None = None

    async with conn.transaction():  # type: ignore[union-attr]
        # 1. Create user
        await _insert_user(
            conn,
            user_id=user_id,
            username=username,
            password=password,
            email=email,
            display_name=display_name,
            account_type_code=account_type,
        )
        await _audit.emit(
            conn,
            category="setup",
            action="user.signup",
            outcome="success",
            user_id=user_id,
            session_id=None,
            org_id=None,
            workspace_id=None,
            target_id=user_id,
            target_type="iam_user",
        )

        # 2. If org_name is provided, create org + workspace + memberships + roles
        if org_name:
            org_name = await _ensure_unique_org_name(conn, org_name)
            org_slug_base = _derive_slug(org_name)

            # Create the org (create_org manages its own inner transaction via
            # conn.transaction(); we are already in an outer one — that is fine
            # because PostgreSQL savepoints handle nested asyncpg transactions)
            _org_data = await _orgs_svc.create_org(
                conn,
                name=org_name,
                slug=org_slug_base,
                owner_id=user_id,
                actor_id=user_id,
                is_provisioning=True,
            )
            org = _org_data
            org_id: str = str(_org_data["id"])

            # Create default workspace
            ws_slug = f"{org_slug_base}-{_derive_slug(default_workspace_name)}"
            _ws_data = await _workspaces_svc.create_workspace(
                conn,
                org_id=org_id,
                name=default_workspace_name,
                slug=ws_slug,
                actor_id=user_id,
                org_id_audit=org_id,
                is_provisioning=True,
            )
            workspace = _ws_data
            workspace_id: str = str(_ws_data["id"])

            # Add user to org + workspace
            await _memberships_svc.add_user_to_org(
                conn,
                user_id=user_id,
                org_id=org_id,
                actor_id=user_id,
                org_id_audit=org_id,
                is_provisioning=True,
            )
            await _memberships_svc.add_user_to_workspace(
                conn,
                user_id=user_id,
                workspace_id=workspace_id,
                org_id=org_id,
                actor_id=user_id,
                org_id_audit=org_id,
                workspace_id_audit=workspace_id,
                is_provisioning=True,
            )

            # Assign org_admin role
            org_admin_role = await conn.fetchrow(  # type: ignore[union-attr]
                "SELECT id FROM \"03_iam\".\"10_fct_org_roles\" "
                "WHERE org_id = $1 AND code = 'org_admin'",
                org_id,
            )
            if org_admin_role:
                await _rbac_repo.assign_user_org_role(
                    conn,
                    id=_id_mod.uuid7(),
                    user_id=user_id,
                    org_id=org_id,
                    org_role_id=org_admin_role["id"],
                    granted_by=user_id,
                )

            # Assign workspace_admin role
            ws_admin_role = await conn.fetchrow(  # type: ignore[union-attr]
                "SELECT id FROM \"03_iam\".\"10_fct_workspace_roles\" "
                "WHERE workspace_id = $1 AND code = 'workspace_admin'",
                workspace_id,
            )
            if ws_admin_role:
                await _rbac_repo.assign_user_workspace_role(
                    conn,
                    id=_id_mod.uuid7(),
                    user_id=user_id,
                    org_id=org_id,
                    workspace_id=workspace_id,
                    workspace_role_id=ws_admin_role["id"],
                    granted_by=user_id,
                )

            session_data = await _issue_session(
                conn,
                user_id=user_id,
                org_id=org_id,
                workspace_id=workspace_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        else:
            session_data = await _issue_session(
                conn,
                user_id=user_id,
                org_id=None,
                workspace_id=None,
                ip_address=ip_address,
                user_agent=user_agent,
            )

        await _audit.emit(
            conn,
            category="iam",
            action="session.login",
            outcome="success",
            user_id=user_id,
            session_id=session_data["session_id"],
            org_id=session_data.get("org_id"),
            workspace_id=session_data.get("workspace_id"),
            target_id=session_data["session_id"],
            target_type="iam_session",
            ip_address=ip_address,
            user_agent=user_agent,
        )

    # Fetch final user row from view
    user_row = await conn.fetchrow(  # type: ignore[union-attr]
        """
        SELECT id, account_type, auth_type,
               username, email, is_active, is_deleted,
               created_by, updated_by, created_at, updated_at
          FROM "03_iam".v_users
         WHERE id = $1
        """,
        user_id,
    )

    return {
        "user": dict(user_row) if user_row else {"id": user_id},
        "org": org,
        "workspace": workspace,
        "access_token": session_data["access_token"],
        "token_type": session_data["token_type"],
        "refresh_token": session_data["refresh_token"],
        "expires_in": session_data["expires_in"],
        "session_id": session_data["session_id"],
    }
