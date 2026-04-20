"""
iam.auth — service layer.

Orchestrates iam.users + iam.credentials + iam.sessions for the four entry
points: signup, signin, signout, me. Also exposes Google/GitHub OAuth code
exchange that ends in the same outcome (user upserted, session minted).

Every successful authenticator emits an audit event with audit_category="setup"
because the user/session pair is being established by this very call — we use
the setup bypass for the chk_evt_audit_scope CHECK.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

import httpx

_config_mod: Any = import_module("backend.01_core.config")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_users_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.repository"
)
_users_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.service"
)
_orgs_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.01_orgs.service"
)
_orgs_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.01_orgs.repository"
)
_memberships_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.07_memberships.service"
)
_memberships_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.07_memberships.repository"
)
_credentials: Any = import_module(
    "backend.02_features.03_iam.sub_features.08_credentials.service"
)
_sessions: Any = import_module(
    "backend.02_features.03_iam.sub_features.09_sessions.service"
)

DEFAULT_ORG_SLUG = "default"
DEFAULT_ORG_DISPLAY_NAME = "Default Organization"

_AUDIT_NODE_KEY  = "audit.events.emit"
_METRIC_NODE_KEY = "monitoring.metrics.increment"


async def _emit_metric(
    pool: Any,
    ctx: Any,
    *,
    metric_key: str,
    labels: dict | None = None,
    value: float = 1.0,
) -> None:
    """Best-effort metric increment — never raises."""
    try:
        from dataclasses import replace as _replace
        metric_ctx = _replace(ctx, conn=None)
        await _catalog.run_node(
            pool,
            _METRIC_NODE_KEY,
            metric_ctx,
            {
                "org_id": ctx.org_id or "system",
                "metric_key": metric_key,
                "labels": labels or {},
                "value": value,
            },
        )
    except Exception:
        pass


async def _emit_audit(
    pool: Any,
    ctx: Any,
    *,
    event_key: str,
    metadata: dict,
    outcome: str = "success",
) -> None:
    # For failure outcomes: use a detached context (no ctx.conn) so the
    # audit insert uses its own pool connection and survives a caller tx rollback.
    from dataclasses import replace as _replace
    emit_ctx = _replace(ctx, conn=None) if outcome == "failure" else ctx
    try:
        await _catalog.run_node(
            pool,
            _AUDIT_NODE_KEY,
            emit_ctx,
            {"event_key": event_key, "outcome": outcome, "metadata": metadata},
        )
    except Exception:
        pass  # Audit failures must never crash the auth path.


async def _find_user_by_email_and_type(
    conn: Any, *, email: str, account_type: str,
) -> dict | None:
    row = await conn.fetchrow(
        'SELECT id FROM "03_iam"."v_users" '
        'WHERE email = $1 AND account_type = $2 AND deleted_at IS NULL '
        'LIMIT 1',
        email, account_type,
    )
    if row is None:
        return None
    return await _users_repo.get_by_id(conn, row["id"])


async def _email_exists_any_type(conn: Any, *, email: str) -> str | None:
    """Return the account_type code of any non-deleted user holding this email, else None."""
    row = await conn.fetchrow(
        'SELECT account_type FROM "03_iam"."v_users" '
        'WHERE email = $1 AND deleted_at IS NULL '
        'LIMIT 1',
        email,
    )
    return row["account_type"] if row else None


async def _ensure_default_org(pool: Any, conn: Any, ctx: Any) -> dict:
    """Fetch or lazily create the TENNETCTL_SINGLE_TENANT default org."""
    existing = await _orgs_repo.get_by_slug(conn, DEFAULT_ORG_SLUG)
    if existing is not None:
        return existing
    return await _orgs_service.create_org(
        pool, conn, ctx,
        slug=DEFAULT_ORG_SLUG,
        display_name=DEFAULT_ORG_DISPLAY_NAME,
    )


async def _attach_to_default_org_if_needed(
    pool: Any, conn: Any, ctx: Any, *, user_id: str,
) -> str | None:
    """In single-tenant mode, ensure user is a member of the default org and return org_id."""
    config = _config_mod.load_config()
    if not config.single_tenant:
        return None
    org = await _ensure_default_org(pool, conn, ctx)
    org_id = org["id"]
    existing = await _memberships_repo.get_org_membership_by_pair(conn, user_id, org_id)
    if existing is None:
        await _memberships_service.assign_org(
            pool, conn, ctx, user_id=user_id, org_id=org_id,
        )
    return org_id


# ── Signup ─────────────────────────────────────────────────────────

async def signup(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    vault_client: Any,
    email: str,
    display_name: str,
    password: str,
) -> tuple[str, dict, dict]:
    """Create email_password user + credential + session. Returns (token, user, session)."""
    # Reject any existing user with this email regardless of account_type —
    # OAuth + password on the same email would otherwise create silent
    # duplicates. Linking is a v0.2 feature (identity proof required first).
    clash = await _email_exists_any_type(conn, email=email)
    if clash is not None:
        raise _errors.ConflictError(
            f"email {email!r} already registered (account_type={clash!r})"
        )

    user = await _users_service.create_user(
        pool, conn, ctx,
        account_type="email_password",
        email=email,
        display_name=display_name,
    )
    user_id = user["id"]

    await _credentials.set_password(
        conn, vault_client=vault_client, user_id=user_id, value=password,
    )

    org_id = await _attach_to_default_org_if_needed(pool, conn, ctx, user_id=user_id)

    token, session = await _sessions.mint_session(
        conn, vault_client=vault_client,
        user_id=user_id, org_id=org_id,
    )

    await _emit_audit(
        pool, ctx,
        event_key="iam.auth.signup",
        metadata={"user_id": user_id, "account_type": "email_password", "org_id": org_id},
    )
    return token, user, session


# ── Signin ─────────────────────────────────────────────────────────

async def signin(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    vault_client: Any,
    email: str,
    password: str,
    source_ip: str | None = None,
    user_agent: str | None = None,
    previous_session_id: str | None = None,
) -> tuple[str, dict, dict]:
    user = await _find_user_by_email_and_type(
        conn, email=email, account_type="email_password",
    )
    if user is None:
        # Burn a verify cycle to prevent timing-based user enumeration.
        await _credentials.verify_password(
            conn, vault_client=vault_client,
            user_id="00000000-0000-0000-0000-000000000000",
            value=password,
        )
        # Record best-effort failure for IP tracking (no user_id)
        auth_policy = getattr(pool, "_auth_policy", None)
        if auth_policy is None:
            import sys as _sys
            for mod in _sys.modules.values():
                if hasattr(mod, "app") and hasattr(getattr(mod, "app", None), "state"):
                    _ap = getattr(mod.app.state, "auth_policy", None)
                    if _ap is not None:
                        auth_policy = _ap
                        break
        if auth_policy is not None:
            try:
                await _credentials.record_failure_and_maybe_lock(
                    pool, email=email, user_id=None,
                    source_ip=source_ip, auth_policy=auth_policy, org_id=None,
                )
            except Exception:
                pass
        await _emit_audit(
            pool, ctx,
            event_key="iam.auth.signin",
            metadata={"email": email, "reason": "no_such_user"},
            outcome="failure",
        )
        raise _errors.UnauthorizedError("invalid email or password")

    if not user["is_active"]:
        await _emit_audit(
            pool, ctx,
            event_key="iam.auth.signin",
            metadata={"email": email, "user_id": user["id"], "reason": "user_inactive"},
            outcome="failure",
        )
        raise _errors.ForbiddenError("account is deactivated", code="USER_INACTIVE")

    # Check lockout before attempting password verification.
    locked_until, lockout_was_cleared = await _credentials.check_lockout(conn, user_id=user["id"])
    if locked_until is not None:
        await _emit_audit(
            pool, ctx,
            event_key="iam.auth.signin",
            metadata={"user_id": user["id"], "reason": "account_locked",
                      "locked_until": locked_until.isoformat()},
            outcome="failure",
        )
        raise _errors.AppError(
            "ACCOUNT_LOCKED",
            f"Account is locked until {locked_until.isoformat()} UTC.",
            423,
        )

    ok = await _credentials.verify_password(
        conn, vault_client=vault_client, user_id=user["id"], value=password,
    )
    if not ok:
        # Retrieve auth_policy from app state
        import importlib as _imp
        _main_mod = _imp.import_module("backend.main")
        auth_policy = getattr(getattr(_main_mod, "app", None), "state", None)
        auth_policy = getattr(auth_policy, "auth_policy", None) if auth_policy else None
        locked = False
        if auth_policy is not None:
            try:
                org_id_for_policy = user.get("org_id")
                locked = await _credentials.record_failure_and_maybe_lock(
                    pool, email=email, user_id=user["id"],
                    source_ip=source_ip, auth_policy=auth_policy,
                    org_id=org_id_for_policy,
                )
            except Exception:
                pass
        if locked:
            await _emit_audit(
                pool, ctx,
                event_key="iam.lockout.triggered",
                metadata={"user_id": user["id"], "email": email},
                outcome="success",
            )
            await _emit_metric(pool, ctx, metric_key="iam_lockouts_triggered_total")
        await _emit_audit(
            pool, ctx,
            event_key="iam.credentials.verify_failed",
            metadata={"user_id": user["id"], "email": email},
            outcome="failure",
        )
        await _emit_metric(
            pool, ctx,
            metric_key="iam_failed_auth_total",
            labels={"reason": "bad_password", "source": "email_password"},
        )
        await _emit_audit(
            pool, ctx,
            event_key="iam.auth.signin",
            metadata={"user_id": user["id"], "reason": "bad_password"},
            outcome="failure",
        )
        raise _errors.UnauthorizedError("invalid email or password")

    # Emit lockout.cleared if the account had an expired lockout.
    if lockout_was_cleared:
        await _emit_audit(
            pool, ctx,
            event_key="iam.lockout.cleared",
            metadata={"user_id": user["id"], "email": email},
            outcome="success",
        )
    org_id = await _attach_to_default_org_if_needed(
        pool, conn, ctx, user_id=user["id"],
    )

    # MFA enforcement gate — check before minting session.
    _gate_org_id = ctx.org_id or org_id  # prefer request org header; fall back to attached org
    if _gate_org_id:
        try:
            import importlib as _imp
            _mfa_svc = _imp.import_module(
                "backend.02_features.03_iam.sub_features.24_mfa_policy.service"
            )
            reason = await _mfa_svc.check_mfa_gate(conn, org_id=_gate_org_id, user_id=user["id"])
            if reason:
                raise _errors.AppError(reason, "MFA enrollment required before sign-in.", 403)
        except _errors.AppError:
            raise
        except Exception:
            pass  # best-effort — never block sign-in on transient policy lookup failure

    token, session = await _sessions.mint_session(
        conn, vault_client=vault_client,
        user_id=user["id"], org_id=org_id,
        user_agent=user_agent, ip_address=source_ip,
    )
    # Session-fixation defense: if the client presented a pre-existing session
    # cookie, revoke it now that a fresh session_id is live.
    if previous_session_id and previous_session_id != session["id"]:
        try:
            await _sessions.rotate_on_login(
                pool, conn, ctx,
                previous_session_id=previous_session_id,
                new_session_id=session["id"],
                user_id=user["id"],
            )
        except Exception:
            pass  # best-effort — never block signin on rotation audit
    await _emit_audit(
        pool, ctx,
        event_key="iam.auth.signin",
        metadata={"user_id": user["id"], "account_type": "email_password", "org_id": org_id},
    )
    return token, user, session


# ── Signout ────────────────────────────────────────────────────────

async def signout(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    session_id: str,
    user_id: str,
) -> bool:
    revoked = await _sessions.revoke_session(
        conn, session_id=session_id, updated_by=user_id,
    )
    await _emit_audit(
        pool, ctx,
        event_key="iam.auth.signout",
        metadata={"session_id": session_id, "user_id": user_id, "revoked": revoked},
    )
    return revoked


# ── Me ─────────────────────────────────────────────────────────────

async def me(conn: Any, *, user_id: str) -> dict | None:
    return await _users_repo.get_by_id(conn, user_id)


# ── OAuth: Google + GitHub ────────────────────────────────────────

_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
_GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
_GITHUB_USER_URL = "https://api.github.com/user"
_GITHUB_EMAILS_URL = "https://api.github.com/user/emails"


async def _vault_get(vault_client: Any, key: str) -> str:
    try:
        return await vault_client.get(key)
    except Exception as e:  # VaultSecretNotFound or anything else
        raise _errors.AppError(
            "OAUTH_NOT_CONFIGURED",
            f"vault key {key!r} not set; configure OAuth before signing in via this provider",
            status_code=503,
        ) from e


async def _exchange_google(code: str, redirect_uri: str, vault_client: Any) -> dict:
    client_id = await _vault_get(vault_client, "auth.google.client_id")
    client_secret = await _vault_get(vault_client, "auth.google.client_secret")
    async with httpx.AsyncClient(timeout=10.0) as client:
        token_resp = await client.post(
            _GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            raise _errors.UnauthorizedError(
                f"google token exchange failed (status={token_resp.status_code})"
            )
        access_token = token_resp.json().get("access_token")
        if not access_token:
            raise _errors.UnauthorizedError("google token exchange returned no access_token")

        userinfo_resp = await client.get(
            _GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if userinfo_resp.status_code != 200:
            raise _errors.UnauthorizedError(
                f"google userinfo fetch failed (status={userinfo_resp.status_code})"
            )
    info = userinfo_resp.json()
    email = info.get("email")
    if not email:
        raise _errors.UnauthorizedError("google account has no email")
    return {
        "email": email,
        "display_name": info.get("name") or email.split("@", 1)[0],
        "avatar_url": info.get("picture"),
    }


async def _exchange_github(code: str, redirect_uri: str, vault_client: Any) -> dict:
    client_id = await _vault_get(vault_client, "auth.github.client_id")
    client_secret = await _vault_get(vault_client, "auth.github.client_secret")
    async with httpx.AsyncClient(timeout=10.0) as client:
        token_resp = await client.post(
            _GITHUB_TOKEN_URL,
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
            },
            headers={"Accept": "application/json"},
        )
        if token_resp.status_code != 200:
            raise _errors.UnauthorizedError(
                f"github token exchange failed (status={token_resp.status_code})"
            )
        access_token = token_resp.json().get("access_token")
        if not access_token:
            raise _errors.UnauthorizedError("github token exchange returned no access_token")

        user_resp = await client.get(
            _GITHUB_USER_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )
        if user_resp.status_code != 200:
            raise _errors.UnauthorizedError(
                f"github user fetch failed (status={user_resp.status_code})"
            )
        user_data = user_resp.json()

        email = user_data.get("email")
        if not email:
            emails_resp = await client.get(
                _GITHUB_EMAILS_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                },
            )
            if emails_resp.status_code == 200:
                primary = next(
                    (e for e in emails_resp.json() if e.get("primary") and e.get("verified")),
                    None,
                )
                if primary:
                    email = primary["email"]
        if not email:
            raise _errors.UnauthorizedError("github account has no verified primary email")
    return {
        "email": email,
        "display_name": user_data.get("name") or user_data.get("login") or email.split("@", 1)[0],
        "avatar_url": user_data.get("avatar_url"),
    }


async def oauth_signin(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    vault_client: Any,
    provider: str,
    code: str,
    redirect_uri: str,
) -> tuple[str, dict, dict]:
    """Exchange code -> upsert user (google_oauth/github_oauth account_type) -> mint session."""
    if provider == "google":
        account_type = "google_oauth"
        profile = await _exchange_google(code, redirect_uri, vault_client)
    elif provider == "github":
        account_type = "github_oauth"
        profile = await _exchange_github(code, redirect_uri, vault_client)
    else:
        raise _errors.ValidationError(f"unknown oauth provider {provider!r}")

    user = await _find_user_by_email_and_type(
        conn, email=profile["email"], account_type=account_type,
    )
    if user is None:
        # Block parallel account creation if the same email is already used by
        # a different account_type (e.g. email_password). Linking is a v0.2
        # feature — until then an operator must delete the clashing row or
        # pick a different OAuth account.
        clash = await _email_exists_any_type(conn, email=profile["email"])
        if clash is not None and clash != account_type:
            raise _errors.ConflictError(
                f"email {profile['email']!r} already registered "
                f"(account_type={clash!r}); cannot create a {account_type!r} "
                "account with the same address"
            )
        user = await _users_service.create_user(
            pool, conn, ctx,
            account_type=account_type,
            email=profile["email"],
            display_name=profile["display_name"],
            avatar_url=profile.get("avatar_url"),
        )

    org_id = await _attach_to_default_org_if_needed(
        pool, conn, ctx, user_id=user["id"],
    )
    token, session = await _sessions.mint_session(
        conn, vault_client=vault_client,
        user_id=user["id"], org_id=org_id,
    )
    await _emit_audit(
        pool, ctx,
        event_key=f"iam.auth.oauth.{provider}",
        metadata={"user_id": user["id"], "account_type": account_type, "org_id": org_id},
    )
    return token, user, session
