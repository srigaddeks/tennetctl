"""iam.mfa_policy — service layer.

MFA enforcement policy stored as vault config per org.
Key: iam.policy.mfa.required (boolean, scope=org, org_id=<id>)
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_vault_configs_svc: Any = import_module(
    "backend.02_features.02_vault.sub_features.02_configs.service"
)
_vault_configs_repo: Any = import_module(
    "backend.02_features.02_vault.sub_features.02_configs.repository"
)
_otp_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.12_otp.repository"
)

_MFA_KEY = "iam.policy.mfa.required"
_AUDIT = "audit.events.emit"


async def _emit(pool: Any, ctx: Any, *, event_key: str, metadata: dict) -> None:
    try:
        await _catalog.run_node(pool, _AUDIT, ctx, {"event_key": event_key, "outcome": "success", "metadata": metadata})
    except Exception:
        pass


async def get_mfa_required(conn: Any, org_id: str) -> bool:
    """Return whether MFA is required for the org. Default: False."""
    row = await _vault_configs_repo.get_by_scope_key(
        conn, scope="org", org_id=org_id, workspace_id=None, key=_MFA_KEY,
    )
    if row is None:
        return False
    return str(row.get("value", "false")).lower() == "true"


async def set_mfa_required(
    pool: Any, conn: Any, ctx: Any, *, org_id: str, required: bool,
) -> None:
    """Enable or disable MFA requirement for an org."""
    existing = await _vault_configs_repo.get_by_scope_key(
        conn, scope="org", org_id=org_id, workspace_id=None, key=_MFA_KEY,
    )
    if existing is None:
        await _vault_configs_svc.create_config(
            pool, conn, ctx,
            key=_MFA_KEY, value_type="boolean", value=str(required).lower(),
            description="Require MFA for all org users", scope="org", org_id=org_id,
        )
    else:
        await _vault_configs_svc.update_config(
            pool, conn, ctx, config_id=existing["id"],
            value=str(required).lower(),
        )
    await _emit(pool, ctx, event_key="iam.mfa_policy.updated", metadata={
        "org_id": org_id, "required": required,
    })


async def is_totp_enrolled(conn: Any, user_id: str) -> bool:
    """Return True if the user has at least one verified TOTP credential."""
    creds = await _otp_repo.list_totp_credentials(conn, user_id)
    return len(creds) > 0


async def check_mfa_gate(conn: Any, *, org_id: str, user_id: str) -> str | None:
    """Return 'MFA_ENROLLMENT_REQUIRED' if org requires MFA but user is not enrolled.
    Return None if gate passes.
    """
    required = await get_mfa_required(conn, org_id)
    if not required:
        return None
    enrolled = await is_totp_enrolled(conn, user_id)
    if not enrolled:
        return "MFA_ENROLLMENT_REQUIRED"
    return None
