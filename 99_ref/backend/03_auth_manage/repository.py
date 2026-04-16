from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

import asyncpg

from .models import (
    AccessSessionState,
    AuthenticatedUser,
    MagicLinkUserRecord,
    PasswordlessChallengeRecord,
    PasswordResetChallengeRecord,
    SessionRecord,
    UserAccountRecord,
    UserAuthRecord,
    UserPropertyRecord,
)
from importlib import import_module


SCHEMA = '"03_auth_manage"'
from_sql_timestamp = import_module("backend.01_core.time_utils").from_sql_timestamp
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


@instrument_class_methods(namespace="auth.repository", logger_name="backend.auth.repository.instrumentation")
class AuthRepository:

    # ── User fact table ──────────────────────────────────────────────────

    async def create_user(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        now: datetime,
        created_by: str | None,
    ) -> tuple[str, str]:
        user_id = str(uuid4())
        user_code = f"usr_{uuid4().hex[:12]}"
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."03_fct_users" (
                id, tenant_key, user_code, account_status,
                is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
            )
            VALUES ($1, $2, $3, 'pending_verification', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, $4, $5, $6, $7, NULL, NULL)
            """,
            user_id,
            tenant_key,
            user_code,
            now,
            now,
            created_by,
            created_by,
        )
        return user_id, user_code

    async def add_user_to_default_group(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        tenant_key: str,
        now: datetime,
    ) -> None:
        """Auto-enroll a new user into the seeded 'default_users' platform group."""
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."18_lnk_group_memberships" (
                id, group_id, user_id,
                membership_status,
                is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                effective_from, effective_to,
                created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
            )
            SELECT
                $1, g.id, $2,
                'active',
                TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                $3, NULL,
                $3, $3, NULL, NULL, NULL, NULL
            FROM {SCHEMA}."17_fct_user_groups" g
            WHERE g.code = 'default_users' AND g.tenant_key = $4 AND g.is_deleted = FALSE
            ON CONFLICT (group_id, user_id) DO NOTHING
            """,
            str(uuid4()),
            user_id,
            now,
            tenant_key,
        )

    # ── User properties (EAV) ───────────────────────────────────────────

    async def create_user_property(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        property_key: str,
        property_value: str,
        created_by: str | None,
        now: datetime,
    ) -> str:
        property_id = str(uuid4())
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."05_dtl_user_properties" (
                id, user_id, property_key, property_value,
                created_at, updated_at, created_by, updated_by
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            property_id,
            user_id,
            property_key,
            property_value,
            now,
            now,
            created_by,
            created_by,
        )
        return property_id

    async def upsert_user_property(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        property_key: str,
        property_value: str,
        updated_by: str | None,
        now: datetime,
    ) -> str:
        property_id = str(uuid4())
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."05_dtl_user_properties" (
                id, user_id, property_key, property_value,
                created_at, updated_at, created_by, updated_by
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (user_id, property_key)
            DO UPDATE SET property_value = EXCLUDED.property_value,
                         updated_at = EXCLUDED.updated_at,
                         updated_by = EXCLUDED.updated_by
            """,
            property_id,
            user_id,
            property_key,
            property_value,
            now,
            now,
            updated_by,
            updated_by,
        )
        return property_id

    async def delete_user_property(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        property_key: str,
    ) -> bool:
        result = await connection.execute(
            f"""
            DELETE FROM {SCHEMA}."05_dtl_user_properties"
            WHERE user_id = $1 AND property_key = $2
            """,
            user_id,
            property_key,
        )
        return result.endswith("1")

    async def list_user_properties(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
    ) -> list[UserPropertyRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id, user_id, property_key, property_value
            FROM {SCHEMA}."05_dtl_user_properties"
            WHERE user_id = $1
            ORDER BY property_key
            """,
            user_id,
        )
        return [
            UserPropertyRecord(
                id=row["id"],
                user_id=row["user_id"],
                property_key=row["property_key"],
                property_value=row["property_value"],
            )
            for row in rows
        ]

    async def get_user_property(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        property_key: str,
    ) -> UserPropertyRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, user_id, property_key, property_value
            FROM {SCHEMA}."05_dtl_user_properties"
            WHERE user_id = $1 AND property_key = $2
            LIMIT 1
            """,
            user_id,
            property_key,
        )
        if row is None:
            return None
        return UserPropertyRecord(
            id=row["id"],
            user_id=row["user_id"],
            property_key=row["property_key"],
            property_value=row["property_value"],
        )

    async def list_property_keys(self, connection: asyncpg.Connection) -> list[dict]:
        rows = await connection.fetch(
            f'SELECT code, name, description, data_type, is_pii, is_required, sort_order FROM {SCHEMA}."04_dim_user_property_keys" ORDER BY sort_order'
        )
        return [dict(row) for row in rows]

    async def validate_all_property_keys(
        self,
        connection: asyncpg.Connection,
        *,
        keys: list[str],
    ) -> list[str]:
        """Return list of keys that do NOT exist in 04_dim_user_property_keys."""
        if not keys:
            return []
        rows = await connection.fetch(
            f'SELECT code FROM {SCHEMA}."04_dim_user_property_keys" WHERE code = ANY($1::TEXT[])',
            keys,
        )
        valid = {row["code"] for row in rows}
        return [k for k in keys if k not in valid]

    async def property_key_exists(
        self,
        connection: asyncpg.Connection,
        *,
        property_key: str,
    ) -> bool:
        row = await connection.fetchrow(
            f"""
            SELECT 1 FROM {SCHEMA}."04_dim_user_property_keys"
            WHERE code = $1
            LIMIT 1
            """,
            property_key,
        )
        return row is not None

    # ── User accounts (EAV) ─────────────────────────────────────────────

    async def create_user_account(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        tenant_key: str,
        account_type_code: str,
        is_primary: bool,
        created_by: str | None,
        now: datetime,
    ) -> str:
        account_id = str(uuid4())
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."08_dtl_user_accounts" (
                id, user_id, tenant_key, account_type_code, is_primary,
                is_active, is_disabled, is_deleted, is_locked,
                created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
            )
            VALUES ($1, $2, $3, $4, $5, TRUE, FALSE, FALSE, FALSE, $6, $7, $8, $9, NULL, NULL)
            """,
            account_id,
            user_id,
            tenant_key,
            account_type_code,
            is_primary,
            now,
            now,
            created_by,
            created_by,
        )
        return account_id

    async def create_user_account_property(
        self,
        connection: asyncpg.Connection,
        *,
        user_account_id: str,
        property_key: str,
        property_value: str,
        now: datetime,
    ) -> str:
        prop_id = str(uuid4())
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."09_dtl_user_account_properties" (
                id, user_account_id, property_key, property_value, created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            prop_id,
            user_account_id,
            property_key,
            property_value,
            now,
            now,
        )
        return prop_id

    async def update_user_account_property(
        self,
        connection: asyncpg.Connection,
        *,
        user_account_id: str,
        property_key: str,
        property_value: str,
        now: datetime,
    ) -> None:
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."09_dtl_user_account_properties"
            SET property_value = $1, updated_at = $2
            WHERE user_account_id = $3 AND property_key = $4
            """,
            property_value,
            now,
            user_account_id,
            property_key,
        )

    async def get_user_account_by_type(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        account_type_code: str,
    ) -> UserAccountRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, user_id, tenant_key, account_type_code, is_primary,
                   is_active, is_disabled, is_deleted, is_locked
            FROM {SCHEMA}."08_dtl_user_accounts"
            WHERE user_id = $1 AND account_type_code = $2 AND is_deleted = FALSE
            LIMIT 1
            """,
            user_id,
            account_type_code,
        )
        if row is None:
            return None
        return UserAccountRecord(
            id=row["id"],
            user_id=row["user_id"],
            tenant_key=row["tenant_key"],
            account_type_code=row["account_type_code"],
            is_primary=bool(row["is_primary"]),
            is_active=bool(row["is_active"]),
            is_disabled=bool(row["is_disabled"]),
            is_deleted=bool(row["is_deleted"]),
            is_locked=bool(row["is_locked"]),
        )

    async def list_user_accounts(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
    ) -> list[UserAccountRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id, user_id, tenant_key, account_type_code, is_primary,
                   is_active, is_disabled, is_deleted, is_locked
            FROM {SCHEMA}."08_dtl_user_accounts"
            WHERE user_id = $1 AND is_deleted = FALSE
            ORDER BY account_type_code
            """,
            user_id,
        )
        return [
            UserAccountRecord(
                id=row["id"],
                user_id=row["user_id"],
                tenant_key=row["tenant_key"],
                account_type_code=row["account_type_code"],
                is_primary=bool(row["is_primary"]),
                is_active=bool(row["is_active"]),
                is_disabled=bool(row["is_disabled"]),
                is_deleted=bool(row["is_deleted"]),
                is_locked=bool(row["is_locked"]),
            )
            for row in rows
        ]

    async def list_account_properties_non_secret(
        self,
        connection: asyncpg.Connection,
        *,
        user_account_id: str,
    ) -> list[tuple[str, str]]:
        rows = await connection.fetch(
            f"""
            SELECT p.property_key, p.property_value
            FROM {SCHEMA}."09_dtl_user_account_properties" p
            JOIN {SCHEMA}."07_dim_account_property_keys" dim
              ON dim.code = p.property_key
             AND dim.account_type_code = (
                SELECT account_type_code FROM {SCHEMA}."08_dtl_user_accounts" WHERE id = $1
             )
            WHERE p.user_account_id = $1 AND dim.is_secret = FALSE
            ORDER BY dim.sort_order
            """,
            user_account_id,
        )
        return [(row["property_key"], row["property_value"]) for row in rows]

    # ── Login lookup (EAV join) ──────────────────────────────────────────

    async def find_user_by_identity(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        normalized_value: str,
        identity_type_code: str,
    ) -> UserAuthRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT
                u.id AS user_id,
                u.tenant_key,
                email_prop.property_value AS email,
                username_prop.property_value AS username,
                COALESCE(ev_prop.property_value, 'false') AS email_verified,
                u.account_status,
                pw_hash.property_value AS password_hash
            FROM {SCHEMA}."05_dtl_user_properties" AS login_prop
            JOIN {SCHEMA}."03_fct_users" AS u
              ON u.id = login_prop.user_id
             AND u.tenant_key = $3
             AND u.is_deleted = FALSE
             AND u.is_active = TRUE
             AND u.is_disabled = FALSE
             AND u.is_locked = FALSE
            JOIN {SCHEMA}."08_dtl_user_accounts" AS acct
              ON acct.user_id = u.id
             AND acct.account_type_code = 'local_password'
             AND acct.is_deleted = FALSE
             AND acct.is_active = TRUE
            JOIN {SCHEMA}."09_dtl_user_account_properties" AS pw_hash
              ON pw_hash.user_account_id = acct.id
             AND pw_hash.property_key = 'password_hash'
            LEFT JOIN {SCHEMA}."05_dtl_user_properties" AS email_prop
              ON email_prop.user_id = u.id AND email_prop.property_key = 'email'
            LEFT JOIN {SCHEMA}."05_dtl_user_properties" AS username_prop
              ON username_prop.user_id = u.id AND username_prop.property_key = 'username'
            LEFT JOIN {SCHEMA}."05_dtl_user_properties" AS ev_prop
              ON ev_prop.user_id = u.id AND ev_prop.property_key = 'email_verified'
            WHERE login_prop.property_key = $1
              AND login_prop.property_value = $2
            LIMIT 1
            """,
            identity_type_code,
            normalized_value,
            tenant_key,
        )
        if row is None:
            return None
        return UserAuthRecord(
            user_id=row["user_id"],
            tenant_key=row["tenant_key"],
            email=row["email"],
            username=row["username"],
            email_verified=row["email_verified"] == "true",
            account_status=row["account_status"],
            password_hash=row["password_hash"],
        )

    async def read_user_profile(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        user_id: str,
    ) -> AuthenticatedUser | None:
        row = await connection.fetchrow(
            f"""
            SELECT user_id, tenant_key, email, username, email_verified, account_status, user_category
            FROM {SCHEMA}."42_vw_auth_users"
            WHERE tenant_key = $1 AND user_id = $2
            LIMIT 1
            """,
            tenant_key,
            user_id,
        )
        if row is None:
            return None
        return AuthenticatedUser(
            user_id=row["user_id"],
            tenant_key=row["tenant_key"],
            email=row["email"],
            username=row["username"],
            email_verified=row["email_verified"] == "true",
            account_status=row["account_status"],
            user_category=row["user_category"],
        )

    # ── Login attempts ───────────────────────────────────────────────────

    async def record_login_attempt(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        normalized_identifier: str,
        identity_type_code: str | None,
        user_id: str | None,
        outcome: str,
        failure_reason: str | None,
        client_ip: str | None,
        now: datetime,
    ) -> str:
        attempt_id = str(uuid4())
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."11_trx_login_attempts" (
                id, tenant_key, normalized_identifier, identity_type_code, user_id, outcome,
                failure_reason, client_ip, occurred_at, created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """,
            attempt_id,
            tenant_key,
            normalized_identifier,
            identity_type_code,
            user_id,
            outcome,
            failure_reason,
            client_ip,
            now,
            now,
            now,
        )
        return attempt_id

    async def count_recent_failed_attempts(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        normalized_identifier: str,
        window_seconds: int,
        now: datetime,
    ) -> int:
        threshold = now - timedelta(seconds=window_seconds)
        row = await connection.fetchrow(
            f"""
            SELECT COUNT(*) AS attempt_count
            FROM {SCHEMA}."11_trx_login_attempts"
            WHERE tenant_key = $1
              AND normalized_identifier = $2
              AND outcome = 'failure'
              AND occurred_at >= $3
            """,
            tenant_key,
            normalized_identifier,
            threshold,
        )
        return int(row["attempt_count"]) if row is not None else 0

    # ── Sessions ─────────────────────────────────────────────────────────

    async def create_session(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        tenant_key: str,
        refresh_token_hash: str,
        refresh_expires_at: datetime,
        client_ip: str | None,
        user_agent: str | None,
        portal_mode: str | None = None,
        now: datetime,
    ) -> str:
        session_id = str(uuid4())
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."10_trx_auth_sessions" (
                id, user_id, tenant_key, refresh_token_hash, refresh_token_expires_at,
                rotated_at, revoked_at, revocation_reason, client_ip, user_agent, portal_mode, rotation_counter,
                created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, NULL, NULL, NULL, $6, $7, $8, 0, $9, $10)
            """,
            session_id,
            user_id,
            tenant_key,
            refresh_token_hash,
            refresh_expires_at,
            client_ip,
            user_agent,
            portal_mode,
            now,
            now,
        )
        return session_id

    async def get_session_by_id(self, connection: asyncpg.Connection, *, session_id: str) -> SessionRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, user_id, tenant_key, refresh_token_hash, refresh_token_expires_at, revoked_at,
                   rotation_counter, portal_mode, is_impersonation, impersonator_user_id
            FROM {SCHEMA}."10_trx_auth_sessions"
            WHERE id = $1
            LIMIT 1
            """,
            session_id,
        )
        if row is None:
            return None
        return SessionRecord(
            session_id=row["id"],
            user_id=row["user_id"],
            tenant_key=row["tenant_key"],
            refresh_token_hash=row["refresh_token_hash"],
            refresh_token_expires_at=from_sql_timestamp(row["refresh_token_expires_at"]),
            revoked_at=from_sql_timestamp(row["revoked_at"]),
            rotation_counter=int(row["rotation_counter"]),
            portal_mode=row["portal_mode"],
            is_impersonation=bool(row["is_impersonation"]),
            impersonator_user_id=str(row["impersonator_user_id"]) if row["impersonator_user_id"] else None,
        )

    async def get_access_session_state(
        self,
        connection: asyncpg.Connection,
        *,
        session_id: str,
    ) -> AccessSessionState | None:
        row = await connection.fetchrow(
            f"""
            SELECT
                session.id,
                session.user_id,
                session.tenant_key,
                session.refresh_token_expires_at,
                session.revoked_at,
                session.portal_mode,
                user_row.is_active,
                user_row.is_disabled,
                user_row.is_deleted,
                user_row.is_locked
            FROM {SCHEMA}."10_trx_auth_sessions" AS session
            JOIN {SCHEMA}."03_fct_users" AS user_row
              ON user_row.id = session.user_id
             AND user_row.tenant_key = session.tenant_key
            WHERE session.id = $1
            LIMIT 1
            """,
            session_id,
        )
        if row is None:
            return None
        return AccessSessionState(
            session_id=row["id"],
            user_id=row["user_id"],
            tenant_key=row["tenant_key"],
            refresh_token_expires_at=from_sql_timestamp(row["refresh_token_expires_at"]),
            revoked_at=from_sql_timestamp(row["revoked_at"]),
            user_is_active=bool(row["is_active"]),
            user_is_disabled=bool(row["is_disabled"]),
            user_is_deleted=bool(row["is_deleted"]),
            user_is_locked=bool(row["is_locked"]),
            portal_mode=row["portal_mode"],
        )

    async def rotate_session(
        self,
        connection: asyncpg.Connection,
        *,
        session_id: str,
        new_refresh_token_hash: str,
        now: datetime,
    ) -> None:
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."10_trx_auth_sessions"
            SET refresh_token_hash = $1,
                rotated_at = $2,
                updated_at = $3,
                rotation_counter = rotation_counter + 1
            WHERE id = $4 AND revoked_at IS NULL
            """,
            new_refresh_token_hash,
            now,
            now,
            session_id,
        )

    async def revoke_session(
        self,
        connection: asyncpg.Connection,
        *,
        session_id: str,
        reason: str,
        now: datetime,
    ) -> None:
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."10_trx_auth_sessions"
            SET revoked_at = COALESCE(revoked_at, $1),
                revocation_reason = COALESCE(revocation_reason, $2),
                updated_at = $3
            WHERE id = $4
            """,
            now,
            reason,
            now,
            session_id,
        )

    async def revoke_active_sessions_for_user(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        reason: str,
        now: datetime,
    ) -> None:
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."10_trx_auth_sessions"
            SET revoked_at = COALESCE(revoked_at, $1),
                revocation_reason = COALESCE(revocation_reason, $2),
                updated_at = $3
            WHERE user_id = $4
              AND revoked_at IS NULL
            """,
            now,
            reason,
            now,
            user_id,
        )

    # ── Password reset challenges ────────────────────────────────────────

    async def create_password_reset_challenge(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        tenant_key: str,
        target_value: str,
        secret_hash: str,
        expires_at: datetime,
        client_ip: str | None,
        now: datetime,
    ) -> str:
        challenge_id = str(uuid4())
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."12_trx_auth_challenges" (
                id, tenant_key, user_id, challenge_type_code, target_value, secret_hash,
                expires_at, consumed_at, requested_ip, created_at, updated_at
            )
            VALUES ($1, $2, $3, 'password_reset', $4, $5, $6, NULL, $7, $8, $9)
            """,
            challenge_id,
            tenant_key,
            user_id,
            target_value,
            secret_hash,
            expires_at,
            client_ip,
            now,
            now,
        )
        return challenge_id

    async def expire_active_password_reset_challenges(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        tenant_key: str,
        now: datetime,
    ) -> None:
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."12_trx_auth_challenges"
            SET consumed_at = COALESCE(consumed_at, $1),
                updated_at = $2
            WHERE user_id = $3
              AND tenant_key = $4
              AND challenge_type_code = 'password_reset'
              AND consumed_at IS NULL
            """,
            now,
            now,
            user_id,
            tenant_key,
        )

    async def get_password_reset_challenge(
        self,
        connection: asyncpg.Connection,
        *,
        challenge_id: str,
    ) -> PasswordResetChallengeRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, user_id, tenant_key, target_value, secret_hash, expires_at, consumed_at
            FROM {SCHEMA}."12_trx_auth_challenges"
            WHERE id = $1 AND challenge_type_code = 'password_reset'
            LIMIT 1
            """,
            challenge_id,
        )
        if row is None:
            return None
        return PasswordResetChallengeRecord(
            challenge_id=row["id"],
            user_id=row["user_id"],
            tenant_key=row["tenant_key"],
            target_value=row["target_value"],
            secret_hash=row["secret_hash"],
            expires_at=from_sql_timestamp(row["expires_at"]),
            consumed_at=from_sql_timestamp(row["consumed_at"]),
        )

    # ── Email verification challenges ────────────────────────────────────

    async def create_email_verification_challenge(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        tenant_key: str,
        target_value: str,
        secret_hash: str,
        expires_at: datetime,
        client_ip: str | None,
        now: datetime,
    ) -> str:
        challenge_id = str(uuid4())
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."12_trx_auth_challenges" (
                id, tenant_key, user_id, challenge_type_code, target_value, secret_hash,
                expires_at, consumed_at, requested_ip, created_at, updated_at
            )
            VALUES ($1, $2, $3, 'email_verification', $4, $5, $6, NULL, $7, $8, $9)
            """,
            challenge_id,
            tenant_key,
            user_id,
            target_value,
            secret_hash,
            expires_at,
            client_ip,
            now,
            now,
        )
        return challenge_id

    async def get_email_verification_challenge(
        self,
        connection: asyncpg.Connection,
        *,
        challenge_id: str,
    ) -> PasswordResetChallengeRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, user_id, tenant_key, target_value, secret_hash, expires_at, consumed_at
            FROM {SCHEMA}."12_trx_auth_challenges"
            WHERE id = $1 AND challenge_type_code = 'email_verification'
            LIMIT 1
            """,
            challenge_id,
        )
        if row is None:
            return None
        return PasswordResetChallengeRecord(
            challenge_id=row["id"],
            user_id=row["user_id"],
            tenant_key=row["tenant_key"],
            target_value=row["target_value"],
            secret_hash=row["secret_hash"],
            expires_at=from_sql_timestamp(row["expires_at"]),
            consumed_at=from_sql_timestamp(row["consumed_at"]),
        )

    async def expire_active_email_verification_challenges(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        tenant_key: str,
        now: datetime,
    ) -> None:
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."12_trx_auth_challenges"
            SET consumed_at = COALESCE(consumed_at, $1),
                updated_at = $2
            WHERE user_id = $3
              AND tenant_key = $4
              AND challenge_type_code = 'email_verification'
              AND consumed_at IS NULL
            """,
            now,
            now,
            user_id,
            tenant_key,
        )

    async def consume_password_reset_challenge(
        self,
        connection: asyncpg.Connection,
        *,
        challenge_id: str,
        now: datetime,
    ) -> None:
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."12_trx_auth_challenges"
            SET consumed_at = $1, updated_at = $2
            WHERE id = $3 AND consumed_at IS NULL
            """,
            now,
            now,
            challenge_id,
        )

    # ── Password update (via account properties) ─────────────────────────

    async def update_password_credential(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        tenant_key: str,
        new_password_hash: str,
        now: datetime,
    ) -> None:
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."09_dtl_user_account_properties" AS prop
            SET property_value = $1, updated_at = $2
            FROM {SCHEMA}."08_dtl_user_accounts" AS acct
            WHERE acct.user_id = $3
              AND acct.tenant_key = $4
              AND acct.account_type_code = 'local_password'
              AND acct.is_deleted = FALSE
              AND prop.user_account_id = acct.id
              AND prop.property_key = 'password_hash'
            """,
            new_password_hash,
            now,
            user_id,
            tenant_key,
        )
        # Increment password_version
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."09_dtl_user_account_properties" AS prop
            SET property_value = (CAST(prop.property_value AS INTEGER) + 1)::TEXT,
                updated_at = $1
            FROM {SCHEMA}."08_dtl_user_accounts" AS acct
            WHERE acct.user_id = $2
              AND acct.tenant_key = $3
              AND acct.account_type_code = 'local_password'
              AND acct.is_deleted = FALSE
              AND prop.user_account_id = acct.id
              AND prop.property_key = 'password_version'
            """,
            now,
            user_id,
            tenant_key,
        )
        # Update password_changed_at
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."09_dtl_user_account_properties" AS prop
            SET property_value = $1::TEXT,
                updated_at = $2
            FROM {SCHEMA}."08_dtl_user_accounts" AS acct
            WHERE acct.user_id = $3
              AND acct.tenant_key = $4
              AND acct.account_type_code = 'local_password'
              AND acct.is_deleted = FALSE
              AND prop.user_account_id = acct.id
              AND prop.property_key = 'password_changed_at'
            """,
            str(now),
            now,
            user_id,
            tenant_key,
        )

    # ── Impersonation ────────────────────────────────────────────────────

    async def create_impersonation_session(
        self,
        connection: asyncpg.Connection,
        *,
        target_user_id: str,
        impersonator_user_id: str,
        tenant_key: str,
        refresh_token_hash: str,
        refresh_expires_at: datetime,
        impersonation_reason: str | None,
        client_ip: str | None,
        user_agent: str | None,
        now: datetime,
    ) -> str:
        session_id = str(uuid4())
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."10_trx_auth_sessions" (
                id, user_id, tenant_key, refresh_token_hash, refresh_token_expires_at,
                rotated_at, revoked_at, revocation_reason, client_ip, user_agent, rotation_counter,
                is_impersonation, impersonator_user_id, impersonation_reason,
                created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, NULL, NULL, NULL, $6, $7, 0,
                    TRUE, $8, $9, $10, $11)
            """,
            session_id,
            target_user_id,
            tenant_key,
            refresh_token_hash,
            refresh_expires_at,
            client_ip,
            user_agent,
            impersonator_user_id,
            impersonation_reason,
            now,
            now,
        )
        return session_id

    async def has_active_impersonation_session(
        self,
        connection: asyncpg.Connection,
        *,
        impersonator_user_id: str,
    ) -> bool:
        row = await connection.fetchrow(
            f"""
            SELECT 1 FROM {SCHEMA}."10_trx_auth_sessions"
            WHERE impersonator_user_id = $1
              AND is_impersonation = TRUE
              AND revoked_at IS NULL
            LIMIT 1
            """,
            impersonator_user_id,
        )
        return row is not None

    async def user_has_elevated_role(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
    ) -> bool:
        """Check if user holds any super_admin or platform role."""
        row = await connection.fetchrow(
            f"""
            SELECT 1
            FROM {SCHEMA}."18_lnk_group_memberships" gm
            JOIN {SCHEMA}."19_lnk_group_role_assignments" gra ON gra.group_id = gm.group_id
            JOIN {SCHEMA}."16_fct_roles" r ON r.id = gra.role_id
            WHERE gm.user_id = $1
              AND r.role_level_code IN ('super_admin', 'platform')
              AND gm.is_active = TRUE AND gm.is_deleted = FALSE
              AND gra.is_active = TRUE AND gra.is_deleted = FALSE
              AND r.is_active = TRUE AND r.is_deleted = FALSE
            LIMIT 1
            """,
            user_id,
        )
        return row is not None

    async def get_user_basic(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
    ) -> dict | None:
        """Get basic user info for impersonation validation."""
        row = await connection.fetchrow(
            f"""
            SELECT id, tenant_key, account_status,
                   is_active, is_disabled, is_deleted, is_locked
            FROM {SCHEMA}."03_fct_users"
            WHERE id = $1
            LIMIT 1
            """,
            user_id,
        )
        if row is None:
            return None
        return dict(row)

    # ── API keys ──────────────────────────────────────────────────────────

    async def get_api_key_status_id(
        self, connection: asyncpg.Connection, *, status_code: str,
    ) -> str | None:
        row = await connection.fetchrow(
            f'SELECT id FROM {SCHEMA}."45_dim_api_key_statuses" WHERE code = $1',
            status_code,
        )
        return str(row["id"]) if row else None

    async def create_api_key(
        self,
        connection: asyncpg.Connection,
        *,
        key_id: str,
        user_id: str,
        tenant_key: str,
        name: str,
        key_prefix: str,
        key_hash: str,
        status_id: str,
        scopes: list[str] | None,
        expires_at: datetime | None,
        now: datetime,
    ) -> None:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."46_fct_api_keys" (
                id, user_id, tenant_key, name, key_prefix, key_hash,
                status_id, scopes, expires_at,
                is_deleted, created_at, updated_at, created_by
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, FALSE, $10, $11, $12)
            """,
            key_id, user_id, tenant_key, name, key_prefix, key_hash,
            status_id, scopes, expires_at,
            now, now, user_id,
        )

    async def get_api_key_by_hash(
        self, connection: asyncpg.Connection, *, key_hash: str,
    ) -> dict | None:
        row = await connection.fetchrow(
            f"""
            SELECT k.id, k.user_id, k.tenant_key, k.name, k.key_prefix,
                   k.scopes, k.expires_at, k.last_used_at,
                   k.revoked_at, k.is_deleted,
                   s.code AS status_code,
                   u.is_active AS user_is_active,
                   u.is_disabled AS user_is_disabled,
                   u.is_deleted AS user_is_deleted,
                   u.is_locked AS user_is_locked
            FROM {SCHEMA}."46_fct_api_keys" AS k
            JOIN {SCHEMA}."45_dim_api_key_statuses" AS s ON s.id = k.status_id
            JOIN {SCHEMA}."03_fct_users" AS u ON u.id = k.user_id
            WHERE k.key_hash = $1
              AND k.is_deleted = FALSE
            LIMIT 1
            """,
            key_hash,
        )
        return dict(row) if row else None

    async def get_api_key_by_id(
        self, connection: asyncpg.Connection, *, key_id: str, user_id: str,
    ) -> dict | None:
        row = await connection.fetchrow(
            f"""
            SELECT k.id, k.user_id, k.tenant_key, k.name, k.key_prefix,
                   k.scopes, k.expires_at, k.last_used_at, k.last_used_ip,
                   k.revoked_at, k.revoke_reason,
                   k.created_at, k.is_deleted,
                   s.code AS status_code
            FROM {SCHEMA}."46_fct_api_keys" AS k
            JOIN {SCHEMA}."45_dim_api_key_statuses" AS s ON s.id = k.status_id
            WHERE k.id = $1 AND k.user_id = $2 AND k.is_deleted = FALSE
            LIMIT 1
            """,
            key_id, user_id,
        )
        return dict(row) if row else None

    async def list_api_keys(
        self, connection: asyncpg.Connection, *, user_id: str, tenant_key: str,
    ) -> list[dict]:
        rows = await connection.fetch(
            f"""
            SELECT k.id, k.name, k.key_prefix,
                   k.scopes, k.expires_at, k.last_used_at, k.last_used_ip,
                   k.revoked_at, k.created_at,
                   s.code AS status_code
            FROM {SCHEMA}."46_fct_api_keys" AS k
            JOIN {SCHEMA}."45_dim_api_key_statuses" AS s ON s.id = k.status_id
            WHERE k.user_id = $1 AND k.tenant_key = $2 AND k.is_deleted = FALSE
            ORDER BY k.created_at DESC
            """,
            user_id, tenant_key,
        )
        return [dict(r) for r in rows]

    async def count_active_api_keys(
        self, connection: asyncpg.Connection, *, user_id: str, tenant_key: str,
    ) -> int:
        row = await connection.fetchrow(
            f"""
            SELECT COUNT(*) AS cnt
            FROM {SCHEMA}."46_fct_api_keys" AS k
            JOIN {SCHEMA}."45_dim_api_key_statuses" AS s ON s.id = k.status_id
            WHERE k.user_id = $1 AND k.tenant_key = $2
              AND k.is_deleted = FALSE AND s.code = 'active'
            """,
            user_id, tenant_key,
        )
        return int(row["cnt"])

    async def revoke_api_key(
        self,
        connection: asyncpg.Connection,
        *,
        key_id: str,
        revoked_by: str,
        revoke_reason: str | None,
        revoked_status_id: str,
        now: datetime,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."46_fct_api_keys"
            SET status_id = $1, revoked_at = $2, revoked_by = $3,
                revoke_reason = $4, updated_at = $5
            WHERE id = $6 AND is_deleted = FALSE AND revoked_at IS NULL
            """,
            revoked_status_id, now, revoked_by, revoke_reason, now, key_id,
        )
        return result == "UPDATE 1"

    async def soft_delete_api_key(
        self, connection: asyncpg.Connection, *, key_id: str, user_id: str, now: datetime,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."46_fct_api_keys"
            SET is_deleted = TRUE, updated_at = $1
            WHERE id = $2 AND user_id = $3 AND is_deleted = FALSE
            """,
            now, key_id, user_id,
        )
        return result == "UPDATE 1"

    async def update_api_key_last_used(
        self, connection: asyncpg.Connection, *, key_id: str, client_ip: str | None, now: datetime,
    ) -> None:
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."46_fct_api_keys"
            SET last_used_at = $1, last_used_ip = $2, updated_at = $3
            WHERE id = $4
            """,
            now, client_ip, now, key_id,
        )

    # ── Audit events ─────────────────────────────────────────────────────

    # ── Magic link (passwordless) ─────────────────────────────────────────

    async def find_user_by_email_for_magic_link(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        email: str,
    ) -> MagicLinkUserRecord | None:
        """Return a lightweight user record for magic link flows (does NOT require local_password account)."""
        row = await connection.fetchrow(
            f"""
            SELECT
                u.id::text AS user_id,
                u.tenant_key,
                u.account_status,
                COALESCE(u.user_category, 'full') AS user_category,
                u.is_active,
                u.is_disabled,
                u.is_deleted,
                u.is_locked,
                email_prop.property_value AS email,
                username_prop.property_value AS username,
                COALESCE(ev_prop.property_value, 'false') AS email_verified
            FROM {SCHEMA}."03_fct_users" AS u
            JOIN {SCHEMA}."05_dtl_user_properties" AS email_prop
              ON email_prop.user_id = u.id AND email_prop.property_key = 'email'
            LEFT JOIN {SCHEMA}."05_dtl_user_properties" AS username_prop
              ON username_prop.user_id = u.id AND username_prop.property_key = 'username'
            LEFT JOIN {SCHEMA}."05_dtl_user_properties" AS ev_prop
              ON ev_prop.user_id = u.id AND ev_prop.property_key = 'email_verified'
            WHERE u.tenant_key = $1
              AND u.is_deleted = FALSE
              AND email_prop.property_value = $2
            LIMIT 1
            """,
            tenant_key,
            email,
        )
        if row is None:
            return None
        return MagicLinkUserRecord(
            user_id=row["user_id"],
            tenant_key=row["tenant_key"],
            email=row["email"],
            username=row["username"],
            email_verified=row["email_verified"] == "true",
            account_status=row["account_status"],
            user_category=row["user_category"],
            is_active=row["is_active"],
            is_disabled=row["is_disabled"],
            is_deleted=row["is_deleted"],
            is_locked=row["is_locked"],
        )

    async def expire_active_magic_link_challenges(
        self,
        connection: asyncpg.Connection,
        *,
        target_value: str,
        tenant_key: str,
        challenge_type_code: str = "magic_link",
        now: datetime,
    ) -> None:
        """Mark any open magic_link challenges for this email as consumed."""
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."12_trx_auth_challenges"
            SET consumed_at = COALESCE(consumed_at, $1),
                updated_at  = $2
            WHERE target_value = $3
              AND tenant_key   = $4
              AND challenge_type_code = $5
              AND consumed_at IS NULL
            """,
            now,
            now,
            target_value,
            tenant_key,
            challenge_type_code,
        )

    async def create_magic_link_challenge(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str | None,
        tenant_key: str,
        target_value: str,
        secret_hash: str,
        expires_at: datetime,
        client_ip: str | None,
        challenge_type_code: str = "magic_link",
        now: datetime,
    ) -> str:
        """Insert a magic_link challenge record and return the challenge_id."""
        challenge_id = str(uuid4())
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."12_trx_auth_challenges" (
                id, tenant_key, user_id, challenge_type_code, target_value, secret_hash,
                expires_at, consumed_at, requested_ip, created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, NULL, $8, $9, $10)
            """,
            challenge_id,
            tenant_key,
            user_id,
            challenge_type_code,
            target_value,
            secret_hash,
            expires_at,
            client_ip,
            now,
            now,
        )
        return challenge_id

    async def get_magic_link_challenge(
        self,
        connection: asyncpg.Connection,
        *,
        challenge_id: str,
    ) -> PasswordlessChallengeRecord | None:
        """Fetch a passwordless challenge by ID."""
        row = await connection.fetchrow(
            f"""
            SELECT id, user_id, tenant_key, challenge_type_code, target_value, secret_hash, expires_at, consumed_at
            FROM {SCHEMA}."12_trx_auth_challenges"
            WHERE id = $1
              AND challenge_type_code IN ('magic_link', 'magic_link_assignee')
            LIMIT 1
            """,
            challenge_id,
        )
        if row is None:
            return None
        return PasswordlessChallengeRecord(
            challenge_id=row["id"],
            user_id=row["user_id"],
            tenant_key=row["tenant_key"],
            challenge_type_code=row["challenge_type_code"],
            target_value=row["target_value"],
            secret_hash=row["secret_hash"],
            expires_at=from_sql_timestamp(row["expires_at"]),
            consumed_at=from_sql_timestamp(row["consumed_at"]),
        )

    async def consume_magic_link_challenge(
        self,
        connection: asyncpg.Connection,
        *,
        challenge_id: str,
        now: datetime,
    ) -> None:
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."12_trx_auth_challenges"
            SET consumed_at = $1, updated_at = $2
            WHERE id = $3
              AND challenge_type_code IN ('magic_link', 'magic_link_assignee')
              AND consumed_at IS NULL
            """,
            now,
            now,
            challenge_id,
        )

    async def ensure_magic_link_account(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        tenant_key: str,
        now: datetime,
    ) -> None:
        """Upsert a magic_link account record for an existing user (idempotent)."""
        account_id = str(uuid4())
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."08_dtl_user_accounts" (
                id, user_id, tenant_key, account_type_code,
                is_primary, is_active, is_disabled, is_deleted, is_locked,
                created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
            )
            VALUES ($1, $2, $3, 'magic_link', FALSE, TRUE, FALSE, FALSE, FALSE,
                    $4, $5, $6, $7, NULL, NULL)
            ON CONFLICT (user_id, account_type_code) DO NOTHING
            """,
            account_id,
            user_id,
            tenant_key,
            now,
            now,
            user_id,
            user_id,
        )

    async def count_users_by_category(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        user_category: str,
    ) -> int:
        """Count active non-deleted users matching a user_category value."""
        row = await connection.fetchrow(
            f"""
            SELECT COUNT(*) AS cnt
            FROM {SCHEMA}."03_fct_users"
            WHERE tenant_key = $1
              AND is_deleted = FALSE
              AND is_active = TRUE
              AND COALESCE(user_category, 'full') = $2
            """,
            tenant_key,
            user_category,
        )
        return int(row["cnt"]) if row else 0

    async def has_any_task_assignment(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        user_id: str,
    ) -> bool:
        row = await connection.fetchrow(
            """
            SELECT 1
            FROM "08_tasks"."10_fct_tasks" AS t
            WHERE t.tenant_key = $1
              AND t.is_deleted = FALSE
              AND (
                  t.assignee_user_id = $2::uuid
                  OR EXISTS (
                      SELECT 1
                      FROM "08_tasks"."31_lnk_task_assignments" AS a
                      WHERE a.task_id = t.id
                        AND a.user_id = $2::uuid
                        AND a.is_deleted = FALSE
                  )
              )
            LIMIT 1
            """,
            tenant_key,
            user_id,
        )
        return row is not None

    async def create_external_user(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        now: datetime,
    ) -> tuple[str, str]:
        """Create a new external_collaborator user row and return (user_id, user_code)."""
        user_id = str(uuid4())
        user_code = f"ext_{uuid4().hex[:12]}"
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."03_fct_users" (
                id, tenant_key, user_code, account_status, user_category,
                is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
            )
            VALUES ($1, $2, $3, 'active', 'external_collaborator',
                    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                    $4, $5, $6, $7, NULL, NULL)
            """,
            user_id,
            tenant_key,
            user_code,
            now,
            now,
            user_id,
            user_id,
        )
        return user_id, user_code

    async def add_user_to_external_collaborators_group(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        tenant_key: str,
        now: datetime,
    ) -> None:
        """Enroll user into the seeded 'external_collaborators' platform group (if it exists)."""
        membership_id = str(uuid4())
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."18_lnk_group_memberships" (
                id, group_id, user_id,
                membership_status,
                is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                effective_from, effective_to,
                created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
            )
            SELECT
                $1, g.id, $2,
                'active',
                TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                $3, NULL,
                $4, $5, $6, $7, NULL, NULL
            FROM {SCHEMA}."17_fct_user_groups" AS g
            WHERE g.tenant_key = $8
              AND g.code = 'external_collaborators'
              AND g.is_deleted = FALSE
            ON CONFLICT DO NOTHING
            """,
            membership_id,
            user_id,
            now,
            now,
            now,
            user_id,
            user_id,
            tenant_key,
        )

    async def get_license_profile_setting_for_org(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        setting_key: str,
    ) -> str | None:
        """Get a license profile setting for the platform tenant, resolving via assigned profile."""
        row = await connection.fetchrow(
            f"""
            SELECT COALESCE(custom.setting_value, profile_setting.setting_value) AS setting_value
            FROM {SCHEMA}."30_dtl_org_settings" custom
            RIGHT JOIN {SCHEMA}."30_dtl_org_settings" profile_assign
              ON profile_assign.entity_id IN (
                  SELECT id FROM {SCHEMA}."29_fct_orgs" WHERE tenant_key = $1 AND is_deleted = FALSE LIMIT 1
              )
              AND profile_assign.setting_key = 'license_profile'
            LEFT JOIN {SCHEMA}."37_fct_license_profiles" lp ON lp.code = profile_assign.setting_value
            LEFT JOIN {SCHEMA}."38_dtl_license_profile_settings" profile_setting
              ON profile_setting.profile_id = lp.id AND profile_setting.setting_key = $2
            WHERE custom.setting_key = $2 LIMIT 1
            """,
            tenant_key,
            setting_key,
        )
        return row["setting_value"] if row else None

    async def list_audit_events(self, connection: asyncpg.Connection) -> list[asyncpg.Record]:
        """Return all audit events ordered by time ascending."""
        return await connection.fetch(f'SELECT * FROM {SCHEMA}."40_aud_events" ORDER BY occurred_at ASC')

    # ── Google OAuth lookup ─────────────────────────────────────────────

    async def find_user_by_google_id(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        google_id: str,
    ) -> AuthenticatedUser | None:
        """Find a user by their Google account's google_id property."""
        row = await connection.fetchrow(
            f"""
            SELECT
                u.id::text AS user_id,
                u.tenant_key,
                u.account_status,
                COALESCE(u.user_category, 'full') AS user_category,
                email_prop.property_value AS email,
                username_prop.property_value AS username,
                COALESCE(ev_prop.property_value, 'false') AS email_verified
            FROM {SCHEMA}."09_dtl_user_account_properties" AS gid_prop
            JOIN {SCHEMA}."08_dtl_user_accounts" AS acct
              ON acct.id = gid_prop.user_account_id
             AND acct.account_type_code = 'google'
             AND acct.is_deleted = FALSE
             AND acct.is_active = TRUE
            JOIN {SCHEMA}."03_fct_users" AS u
              ON u.id = acct.user_id
             AND u.tenant_key = $1
             AND u.is_deleted = FALSE
             AND u.is_active = TRUE
             AND u.is_disabled = FALSE
             AND u.is_locked = FALSE
            LEFT JOIN {SCHEMA}."05_dtl_user_properties" AS email_prop
              ON email_prop.user_id = u.id AND email_prop.property_key = 'email'
            LEFT JOIN {SCHEMA}."05_dtl_user_properties" AS username_prop
              ON username_prop.user_id = u.id AND username_prop.property_key = 'username'
            LEFT JOIN {SCHEMA}."05_dtl_user_properties" AS ev_prop
              ON ev_prop.user_id = u.id AND ev_prop.property_key = 'email_verified'
            WHERE gid_prop.property_key = 'google_id'
              AND gid_prop.property_value = $2
            LIMIT 1
            """,
            tenant_key,
            google_id,
        )
        if row is None:
            return None
        return AuthenticatedUser(
            user_id=row["user_id"],
            tenant_key=row["tenant_key"],
            email=row["email"],
            username=row["username"],
            email_verified=row["email_verified"] == "true",
            account_status=row["account_status"],
            user_category=row["user_category"],
        )

    async def find_google_account_for_user(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
    ) -> str | None:
        """Return the account ID of a user's google account, or None."""
        row = await connection.fetchrow(
            f"""
            SELECT id FROM {SCHEMA}."08_dtl_user_accounts"
            WHERE user_id = $1
              AND account_type_code = 'google'
              AND is_deleted = FALSE
            LIMIT 1
            """,
            user_id,
        )
        return row["id"] if row else None
