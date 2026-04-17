"""
AuthPolicy — vault-backed, per-key auth policy configuration layer.

Resolves iam.policy.* values from vault.configs with per-org override
fallback to global. Values are cached 60s per (org_id, key) tuple and
invalidated inline when vault.configs writes touch iam.policy.* keys.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from importlib import import_module
from typing import Any

_repo: Any = import_module(
    "backend.02_features.02_vault.sub_features.02_configs.repository"
)

logger = logging.getLogger("tennetctl.iam.auth_policy")

# Maps short_key → (vault_value_type, hardcoded_default)
# vault_value_type must match dim_value_types: "boolean", "string", "number"
# Exactly 20 keys — verify command asserts this.
POLICY_KEYS: dict[str, tuple[str, object]] = {
    "password.min_length":                ("number",  12),
    "password.require_upper":             ("boolean", True),
    "password.require_digit":             ("boolean", True),
    "password.require_symbol":            ("boolean", False),
    "password.min_unique_chars":          ("number",  4),
    "lockout.threshold_failed_attempts":  ("number",  5),
    "lockout.window_seconds":             ("number",  900),
    "lockout.duration_seconds":           ("number",  900),
    "session.max_concurrent_per_user":    ("number",  10),
    "session.idle_timeout_seconds":       ("number",  1800),
    "session.absolute_ttl_seconds":       ("number",  604800),
    "session.eviction_policy":            ("string",  "oldest"),
    "magic_link.ttl_seconds":             ("number",  600),
    "magic_link.rate_limit_per_email":    ("number",  3),
    "magic_link.rate_window_seconds":     ("number",  900),
    "otp.email_ttl_seconds":              ("number",  300),
    "otp.email_max_attempts":             ("number",  3),
    "otp.rate_limit_per_email":           ("number",  3),
    "otp.rate_window_seconds":            ("number",  900),
    "password_reset.ttl_seconds":         ("number",  900),
}


@dataclass(frozen=True, slots=True)
class PasswordPolicy:
    min_length: int
    require_upper: bool
    require_digit: bool
    require_symbol: bool
    min_unique_chars: int


@dataclass(frozen=True, slots=True)
class LockoutPolicy:
    threshold_failed_attempts: int
    window_seconds: int
    duration_seconds: int


@dataclass(frozen=True, slots=True)
class SessionPolicy:
    max_concurrent_per_user: int
    idle_timeout_seconds: int
    absolute_ttl_seconds: int
    eviction_policy: str


@dataclass(frozen=True, slots=True)
class MagicLinkPolicy:
    ttl_seconds: int
    rate_limit_per_email: int
    rate_window_seconds: int


@dataclass(frozen=True, slots=True)
class OtpPolicy:
    email_ttl_seconds: int
    email_max_attempts: int
    rate_limit_per_email: int
    rate_window_seconds: int


@dataclass(frozen=True, slots=True)
class PasswordResetPolicy:
    ttl_seconds: int


def _cast(value: Any, vtype: str) -> object:
    if vtype == "number":
        return int(value)
    if vtype == "boolean":
        return bool(value)
    return str(value)


class AuthPolicy:
    def __init__(self, pool: Any, ttl_seconds: float = 60.0) -> None:
        self._pool = pool
        self._ttl = ttl_seconds
        # (org_id, short_key) → (fetched_at_monotonic, typed_value)
        self._cache: dict[tuple[str | None, str], tuple[float, object]] = {}
        self._fetch_count = 0  # DB hits only; used by tests

    async def resolve(self, org_id: str | None, key: str) -> Any:
        now = time.monotonic()
        cache_key = (org_id, key)
        cached = self._cache.get(cache_key)
        if cached is not None and now - cached[0] < self._ttl:
            return cached[1]

        raw = await self._fetch(org_id, key)
        vtype, default = POLICY_KEYS[key]
        if raw is None:
            logger.warning(
                "auth_policy: vault entry missing for iam.policy.%s — using hardcoded default",
                key,
            )
            value = _cast(default, vtype)
        else:
            value = _cast(raw, vtype)

        self._cache[cache_key] = (now, value)
        return value

    def invalidate(self, org_id: str | None, key: str) -> None:
        self._cache.pop((org_id, key), None)

    def invalidate_all_for_key(self, key: str) -> None:
        stale = [k for k in self._cache if k[1] == key]
        for k in stale:
            self._cache.pop(k, None)

    async def _fetch(self, org_id: str | None, key: str) -> Any:
        full_key = f"iam.policy.{key}"
        async with self._pool.acquire() as conn:
            row = None
            if org_id is not None:
                row = await _repo.get_by_scope_key(
                    conn, scope="org", org_id=org_id, workspace_id=None, key=full_key,
                )
            if row is None:
                row = await _repo.get_by_scope_key(
                    conn, scope="global", org_id=None, workspace_id=None, key=full_key,
                )
        self._fetch_count += 1
        if row is None or row.get("deleted_at") is not None:
            return None
        return row["value"]

    # ── domain getters ────────────────────────────────────────────────

    async def password(self, org_id: str | None) -> PasswordPolicy:
        return PasswordPolicy(
            min_length=int(await self.resolve(org_id, "password.min_length")),
            require_upper=bool(await self.resolve(org_id, "password.require_upper")),
            require_digit=bool(await self.resolve(org_id, "password.require_digit")),
            require_symbol=bool(await self.resolve(org_id, "password.require_symbol")),
            min_unique_chars=int(await self.resolve(org_id, "password.min_unique_chars")),
        )

    async def lockout(self, org_id: str | None) -> LockoutPolicy:
        return LockoutPolicy(
            threshold_failed_attempts=int(
                await self.resolve(org_id, "lockout.threshold_failed_attempts")
            ),
            window_seconds=int(await self.resolve(org_id, "lockout.window_seconds")),
            duration_seconds=int(await self.resolve(org_id, "lockout.duration_seconds")),
        )

    async def session(self, org_id: str | None) -> SessionPolicy:
        return SessionPolicy(
            max_concurrent_per_user=int(
                await self.resolve(org_id, "session.max_concurrent_per_user")
            ),
            idle_timeout_seconds=int(
                await self.resolve(org_id, "session.idle_timeout_seconds")
            ),
            absolute_ttl_seconds=int(
                await self.resolve(org_id, "session.absolute_ttl_seconds")
            ),
            eviction_policy=str(await self.resolve(org_id, "session.eviction_policy")),
        )

    async def magic_link(self, org_id: str | None) -> MagicLinkPolicy:
        return MagicLinkPolicy(
            ttl_seconds=int(await self.resolve(org_id, "magic_link.ttl_seconds")),
            rate_limit_per_email=int(
                await self.resolve(org_id, "magic_link.rate_limit_per_email")
            ),
            rate_window_seconds=int(
                await self.resolve(org_id, "magic_link.rate_window_seconds")
            ),
        )

    async def otp(self, org_id: str | None) -> OtpPolicy:
        return OtpPolicy(
            email_ttl_seconds=int(await self.resolve(org_id, "otp.email_ttl_seconds")),
            email_max_attempts=int(await self.resolve(org_id, "otp.email_max_attempts")),
            rate_limit_per_email=int(
                await self.resolve(org_id, "otp.rate_limit_per_email")
            ),
            rate_window_seconds=int(
                await self.resolve(org_id, "otp.rate_window_seconds")
            ),
        )

    async def password_reset(self, org_id: str | None) -> PasswordResetPolicy:
        return PasswordResetPolicy(
            ttl_seconds=int(await self.resolve(org_id, "password_reset.ttl_seconds")),
        )
