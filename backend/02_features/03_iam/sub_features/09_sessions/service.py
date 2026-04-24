"""
iam.sessions — service layer.

Mints + validates HMAC-SHA256 signed opaque tokens. Token format:

    <session_id>.<base64url(HMAC-SHA256(signing_key, session_id))>

Signing key is fetched from vault key auth.session.signing_key_v1 (32 random
bytes, base64-encoded). The vault client SWR-caches for 60s, so validation cost
is sub-millisecond after warmup.

`auth.session.ttl_days` (vault config, default 7) drives expires_at. Configs
arrive as JSONB; we coerce to int and clamp 1..90.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.09_sessions.repository"
)
_configs_repo: Any = import_module(
    "backend.02_features.02_vault.sub_features.02_configs.repository"
)

_SIGNING_KEY_VAULT_KEY = "auth.session.signing_key_v1"
_TTL_CONFIG_KEY = "auth.session.ttl_days"
_DEFAULT_TTL_DAYS = 7
_METRIC_NODE_KEY = "monitoring.metrics.increment"


async def _emit_metric(
    pool: Any, ctx: Any, *, metric_key: str, labels: dict | None = None
) -> None:
    """Best-effort metric increment — never raises."""
    try:
        from dataclasses import replace as _r
        await _catalog.run_node(pool, _METRIC_NODE_KEY, _r(ctx, conn=None), {
            "org_id": ctx.org_id or "system",
            "metric_key": metric_key,
            "labels": labels or {},
            "value": 1.0,
        })
    except Exception:
        pass


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _sign(session_id: str, signing_key: bytes) -> str:
    sig = hmac.new(signing_key, session_id.encode("ascii"), hashlib.sha256).digest()
    return _b64url_encode(sig)


async def _signing_key_bytes(vault_client: Any) -> bytes:
    """Fetch + base64-decode the signing key. Cached upstream by VaultClient (60s)."""
    raw = await vault_client.get(_SIGNING_KEY_VAULT_KEY)
    return base64.b64decode(raw)


async def _resolve_ttl_days(conn: Any) -> int:
    cfg = await _configs_repo.get_by_scope_key(
        conn, scope="global", org_id=None, workspace_id=None, key=_TTL_CONFIG_KEY,
    )
    if cfg is None:
        return _DEFAULT_TTL_DAYS
    raw = cfg["value"]
    try:
        n = int(raw)
    except (TypeError, ValueError):
        return _DEFAULT_TTL_DAYS
    return max(1, min(90, n))


def make_token(session_id: str, signing_key: bytes) -> str:
    return f"{session_id}.{_sign(session_id, signing_key)}"


def parse_token(token: str, signing_key: bytes) -> str | None:
    """Validate signature + return embedded session_id, or None if tampered."""
    if not token or "." not in token:
        return None
    session_id, _, sig = token.partition(".")
    if not session_id or not sig:
        return None
    expected = _sign(session_id, signing_key)
    if not hmac.compare_digest(sig, expected):
        return None
    return session_id


async def mint_session(
    conn: Any,
    *,
    vault_client: Any,
    user_id: str,
    org_id: str | None = None,
    workspace_id: str | None = None,
    application_id: str | None = None,
    ttl_days: int | None = None,
    pool: Any = None,
    ctx: Any = None,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> tuple[str, dict]:
    """Create a session row and return (token, session_metadata).
    If pool + ctx are provided, session-limit enforcement (20-04) runs first.
    """
    # Enforce concurrent-session limits if auth_policy is available.
    if pool is not None and ctx is not None:
        import importlib as _imp
        _main_mod = _imp.import_module("backend.main")
        auth_policy = getattr(getattr(_main_mod, "app", None), "state", None)
        auth_policy = getattr(auth_policy, "auth_policy", None) if auth_policy else None
        if auth_policy is not None:
            try:
                await enforce_session_limits(
                    pool, conn, ctx,
                    user_id=user_id, auth_policy=auth_policy, org_id=org_id,
                )
            except _errors.AppError:
                raise
            except Exception:
                pass  # best-effort

    session_id = _core_id.uuid7()
    ttl = ttl_days if ttl_days is not None else await _resolve_ttl_days(conn)
    expires = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=ttl)
    await _repo.insert_session(
        conn,
        id=session_id,
        user_id=user_id,
        org_id=org_id,
        workspace_id=workspace_id,
        application_id=application_id,
        expires_at=expires,
        created_by=user_id,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    signing_key = await _signing_key_bytes(vault_client)
    token = make_token(session_id, signing_key)
    metadata = await _repo.get_by_id(conn, session_id)
    if metadata is None:
        raise RuntimeError(f"session {session_id} not visible after insert")
    return token, metadata


async def validate_token(
    conn: Any,
    *,
    vault_client: Any,
    token: str,
) -> dict | None:
    """Return the session row iff signature matches AND row is_valid. Else None."""
    signing_key = await _signing_key_bytes(vault_client)
    session_id = parse_token(token, signing_key)
    if session_id is None:
        return None
    row = await _repo.get_by_id(conn, session_id)
    if row is None or not row["is_valid"]:
        return None
    return row


async def revoke_session(conn: Any, *, session_id: str, updated_by: str) -> bool:
    return await _repo.revoke_session(
        conn, session_id=session_id, updated_by=updated_by,
    )


# ── Self-service: list + revoke + extend the caller's own sessions ─

async def list_my_sessions(
    conn: Any,
    *,
    user_id: str,
    limit: int = 50,
    offset: int = 0,
    only_valid: bool = False,
) -> tuple[list[dict], int]:
    return await _repo.list_by_user(
        conn, user_id=user_id, limit=limit, offset=offset, only_valid=only_valid,
    )


async def get_my_session(conn: Any, *, user_id: str, session_id: str) -> dict | None:
    """Return the session iff it belongs to the caller. Else None (so route can 404)."""
    row = await _repo.get_by_id(conn, session_id)
    if row is None or row["user_id"] != user_id:
        return None
    return row


async def revoke_my_session(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    user_id: str,
    session_id: str,
) -> bool:
    """Revoke a session owned by `user_id`. Emits iam.sessions.revoked audit."""
    owned = await get_my_session(conn, user_id=user_id, session_id=session_id)
    if owned is None:
        raise _errors.NotFoundError(f"Session {session_id!r} not found.")

    revoked = await _repo.revoke_session(
        conn, session_id=session_id, updated_by=user_id,
    )
    await _catalog.run_node(
        pool, "audit.events.emit", ctx,
        {
            "event_key": "iam.sessions.revoked",
            "outcome": "success",
            "metadata": {
                "session_id": session_id,
                "user_id": user_id,
                "already_revoked": not revoked,
            },
        },
    )
    return revoked


async def extend_my_session(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    vault_client: Any,
    user_id: str,
    session_id: str,
) -> dict:
    """Push expires_at out by the configured TTL. Session must be owned + still live."""
    owned = await get_my_session(conn, user_id=user_id, session_id=session_id)
    if owned is None:
        raise _errors.NotFoundError(f"Session {session_id!r} not found.")
    if not owned["is_valid"]:
        raise _errors.UnauthorizedError("session is not valid and cannot be extended")

    ttl_days = await _resolve_ttl_days(conn)
    new_expires = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=ttl_days)
    ok = await _repo.extend_expires(
        conn, session_id=session_id, new_expires_at=new_expires, updated_by=user_id,
    )
    if not ok:
        raise _errors.UnauthorizedError("session is not valid and cannot be extended")

    await _catalog.run_node(
        pool, "audit.events.emit", ctx,
        {
            "event_key": "iam.sessions.extended",
            "outcome": "success",
            "metadata": {
                "session_id": session_id,
                "user_id": user_id,
                "ttl_days": ttl_days,
            },
        },
    )
    updated = await _repo.get_by_id(conn, session_id)
    if updated is None:
        raise RuntimeError(f"session {session_id} vanished after extend")
    # Silence unused-import warning: vault_client is the documented prerequisite
    # for session trust; future plans may re-sign the token here.
    del vault_client
    return updated


# ── Plan 38-01 + 38-02: Session rotation on privilege escalation ──────────────

async def rotate_on_privilege_escalation(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    previous_session_id: str,
    user_id: str,
    vault_client: Any,
    org_id: str | None = None,
    workspace_id: str | None = None,
    reason: str = "password_change",
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> tuple[str, dict]:
    """Mint fresh session, revoke previous, audit the rotation.

    Used at privilege boundaries where the effective auth state changes:
      - "password_change": caller just rotated their password
      - "mfa_enrolled":    caller just activated TOTP / MFA credential

    The login path uses `rotate_on_login` (which only revokes — it mints through
    the signin service's own code path). This helper is the combined mint + revoke
    flow for post-auth boundaries.

    Returns (new_token, new_session_meta). New session inherits (user_id, org_id,
    workspace_id) from the caller — no re-login required.
    """
    new_token, new_session = await mint_session(
        conn, vault_client=vault_client,
        user_id=user_id, org_id=org_id, workspace_id=workspace_id,
        user_agent=user_agent, ip_address=ip_address,
    )
    revoked = await _repo.revoke_session_by_reason(
        conn, session_id=previous_session_id, updated_by=user_id,
        reason=f"rotated_on_{reason}",
    )
    try:
        await _catalog.run_node(
            pool, "audit.events.emit", ctx,
            {
                "event_key": "iam.session.rotated",
                "outcome": "success",
                "metadata": {
                    "reason": reason,
                    "old_session_id": previous_session_id,
                    "new_session_id": new_session["id"],
                    "user_id": user_id,
                    "previous_was_active": revoked,
                },
            },
        )
    except Exception:
        pass  # rotation itself succeeded; audit is best-effort
    return new_token, new_session


async def rotate_on_login(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    previous_session_id: str,
    new_session_id: str,
    user_id: str,
) -> bool:
    """Revoke `previous_session_id` and audit the rotation.

    Called from the signin path when the client presented a pre-existing session
    cookie. Closes the classic session-fixation vector where an attacker plants
    a session_id in the victim's browser and rides the authenticated session
    after the victim signs in.

    `new_session_id` is already live at this point (mint_session succeeded);
    this helper only revokes + audits. If `previous_session_id == new_session_id`
    this is a no-op (defensive; shouldn't happen since we mint before rotate).
    """
    if previous_session_id == new_session_id:
        return False
    revoked = await _repo.revoke_session_by_reason(
        conn, session_id=previous_session_id, updated_by=user_id,
        reason="rotated_on_login",
    )
    try:
        await _catalog.run_node(
            pool, "audit.events.emit", ctx,
            {
                "event_key": "iam.session.rotated",
                "outcome": "success",
                "metadata": {
                    "reason": "login",
                    "old_session_id": previous_session_id,
                    "new_session_id": new_session_id,
                    "user_id": user_id,
                    "previous_was_active": revoked,
                },
            },
        )
    except Exception:
        pass  # rotation itself must not fail on audit glitches
    return revoked


# ── Plan 20-04: Session policy enforcement ────────────────────────────────────

async def enforce_session_limits(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    user_id: str,
    auth_policy: Any,
    org_id: str | None,
) -> str | None:
    """Enforce max_concurrent_per_user. Returns evicted session_id or None.
    Eviction policy: "oldest" = evict oldest by created_at; "lru" = evict by last_activity_at;
    "reject" = raise 429.
    """
    policy = await auth_policy.session(org_id)
    active = await _repo.list_active_for_user(conn, user_id=user_id)
    count = len(active)
    if count < policy.max_concurrent_per_user:
        return None

    eviction_policy = policy.eviction_policy
    if eviction_policy == "reject":
        raise _errors.AppError(
            "SESSION_LIMIT_EXCEEDED",
            f"Maximum of {policy.max_concurrent_per_user} concurrent sessions allowed.",
            429,
        )

    # Determine which session to evict.
    if eviction_policy == "lru":
        # active is already sorted by last_activity_at ASC (least recent first).
        victim = active[0]
    else:
        # "oldest" — sorted by created_at ASC.
        victim = min(active, key=lambda s: s["created_at"])

    evicted_id = victim["id"]
    await _repo.revoke_session(conn, session_id=evicted_id, updated_by=user_id)
    await _catalog.run_node(
        pool, "audit.events.emit", ctx,
        {
            "event_key": "iam.sessions.evicted",
            "outcome": "success",
            "metadata": {
                "session_id": evicted_id,
                "user_id": user_id,
                "reason": "max_concurrent",
                "policy": eviction_policy,
            },
        },
    )
    await _emit_metric(pool, ctx, metric_key="iam_sessions_evicted_total",
                       labels={"reason": "max_concurrent"})
    return evicted_id


async def check_session_timeouts(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    session_id: str,
    auth_policy: Any,
    org_id: str | None,
) -> str | None:
    """Check idle + absolute TTL. Returns revocation reason or None if still valid.
    On timeout, revokes the session and emits audit.
    """
    from importlib import import_module as _im
    _dt = _im("datetime")
    raw = await _repo.get_raw_by_id(conn, session_id)
    if raw is None:
        return "not_found"

    policy = await auth_policy.session(org_id)
    now = _dt.datetime.now(_dt.timezone.utc).replace(tzinfo=None)

    # Idle timeout.
    last_activity = raw.get("last_activity_at")
    if last_activity is not None:
        idle_secs = (now - last_activity).total_seconds()
        if idle_secs > policy.idle_timeout_seconds:
            await _repo.revoke_session(conn, session_id=session_id, updated_by="system")
            await _catalog.run_node(
                pool, "audit.events.emit", ctx,
                {
                    "event_key": "iam.sessions.evicted",
                    "outcome": "success",
                    "metadata": {
                        "session_id": session_id,
                        "user_id": raw.get("user_id"),
                        "reason": "idle_timeout",
                        "idle_seconds": int(idle_secs),
                    },
                },
            )
            await _emit_metric(pool, ctx, metric_key="iam_sessions_evicted_total",
                               labels={"reason": "idle_timeout"})
            return "idle_timeout"

    # Absolute TTL.
    created_at = raw.get("created_at")
    if created_at is not None:
        age_secs = (now - created_at).total_seconds()
        if age_secs > policy.absolute_ttl_seconds:
            await _repo.revoke_session(conn, session_id=session_id, updated_by="system")
            await _catalog.run_node(
                pool, "audit.events.emit", ctx,
                {
                    "event_key": "iam.sessions.evicted",
                    "outcome": "success",
                    "metadata": {
                        "session_id": session_id,
                        "user_id": raw.get("user_id"),
                        "reason": "absolute_ttl",
                        "age_seconds": int(age_secs),
                    },
                },
            )
            await _emit_metric(pool, ctx, metric_key="iam_sessions_evicted_total",
                               labels={"reason": "absolute_ttl"})
            return "absolute_ttl"

    return None
