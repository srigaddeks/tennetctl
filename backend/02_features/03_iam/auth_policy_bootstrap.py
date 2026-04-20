"""
Auth policy bootstrap — seeds 20 safe-default iam.policy.* entries in vault.configs.

Idempotent: skips any key that already exists. Preserves operator-tuned values.
Runs on every boot after vault is initialised.
"""

from __future__ import annotations

import logging
from dataclasses import replace
from importlib import import_module
from typing import Any

_auth_policy_mod: Any = import_module("backend.02_features.03_iam.auth_policy")
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_core_id: Any = import_module("backend.01_core.id")
_configs_repo: Any = import_module(
    "backend.02_features.02_vault.sub_features.02_configs.repository"
)
_configs_svc: Any = import_module(
    "backend.02_features.02_vault.sub_features.02_configs.service"
)

logger = logging.getLogger("tennetctl.iam.auth_policy_bootstrap")

_DESCRIPTIONS: dict[str, str] = {
    "password.min_length":               "Minimum password length (NIST 800-63B)",
    "password.require_upper":            "Require at least one uppercase letter",
    "password.require_digit":            "Require at least one digit",
    "password.require_symbol":           "Require at least one special character",
    "password.min_unique_chars":         "Minimum unique characters in password",
    "lockout.threshold_failed_attempts": "Failed login attempts before lockout",
    "lockout.window_seconds":            "Rolling window for failed attempt count (seconds)",
    "lockout.duration_seconds":          "Account lockout duration (seconds)",
    "session.max_concurrent_per_user":   "Maximum concurrent sessions per user",
    "session.idle_timeout_seconds":      "Session idle timeout (seconds)",
    "session.absolute_ttl_seconds":      "Absolute session lifetime (seconds; default 7 days)",
    "session.eviction_policy":           "When max sessions exceeded: oldest or reject",
    "magic_link.ttl_seconds":            "Magic link token expiry (seconds)",
    "magic_link.rate_limit_per_email":   "Max magic links per email per window",
    "magic_link.rate_window_seconds":    "Rate limit window for magic links (seconds)",
    "otp.email_ttl_seconds":             "Email OTP code expiry (seconds)",
    "otp.email_max_attempts":            "Max OTP verification attempts before invalidation",
    "otp.rate_limit_per_email":          "Max OTP sends per email per window",
    "otp.rate_window_seconds":           "Rate limit window for OTP sends (seconds)",
    "password_reset.ttl_seconds":        "Password reset token expiry (seconds)",
}


async def ensure_policy_defaults(pool: Any) -> int:
    """
    Seed default iam.policy.* rows into vault.configs at scope=global.
    Returns count of newly inserted rows (0 on subsequent boots).
    """
    ctx = _catalog_ctx.NodeContext(
        user_id="sys",
        session_id="bootstrap",
        org_id=None,
        workspace_id=None,
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=_core_id.uuid7(),
        audit_category="setup",
        pool=pool,
        extras={"pool": pool},
    )

    inserted = 0
    for key, (value_type, default_value) in _auth_policy_mod.POLICY_KEYS.items():
        full_key = f"iam.policy.{key}"
        try:
            async with pool.acquire() as conn:
                existing = await _configs_repo.get_by_scope_key(
                    conn,
                    scope="global",
                    org_id=None,
                    workspace_id=None,
                    key=full_key,
                )
                if existing is not None:
                    continue
                ctx_conn = replace(ctx, conn=conn)
                await _configs_svc.create_config(
                    pool, conn, ctx_conn,
                    key=full_key,
                    value_type=value_type,
                    value=default_value,
                    description=_DESCRIPTIONS.get(key, ""),
                    scope="global",
                    org_id=None,
                    workspace_id=None,
                )
                inserted += 1
        except Exception:
            pass

    if inserted == 0:
        logger.info("Auth policy bootstrap: no-op (all defaults present).")
    else:
        logger.info("Auth policy bootstrap: seeded %d default(s).", inserted)
    return inserted
