"""
IAM feature router — aggregates sub-feature routers.

Mounted from backend.main.MODULE_ROUTERS when the 'iam' module is enabled
(always on per feature.manifest.yaml). Each sub-feature router owns its prefix
(/v1/orgs, /v1/workspaces, etc.) so this file only composes.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter

_orgs_routes: Any = import_module(
    "backend.02_features.03_iam.sub_features.01_orgs.routes"
)
_ws_routes: Any = import_module(
    "backend.02_features.03_iam.sub_features.02_workspaces.routes"
)
_users_routes: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.routes"
)
_memberships_routes: Any = import_module(
    "backend.02_features.03_iam.sub_features.07_memberships.routes"
)
_roles_routes: Any = import_module(
    "backend.02_features.03_iam.sub_features.04_roles.routes"
)
_groups_routes: Any = import_module(
    "backend.02_features.03_iam.sub_features.05_groups.routes"
)
_applications_routes: Any = import_module(
    "backend.02_features.03_iam.sub_features.06_applications.routes"
)
_auth_routes: Any = import_module(
    "backend.02_features.03_iam.sub_features.10_auth.routes"
)
_credentials_routes: Any = import_module(
    "backend.02_features.03_iam.sub_features.08_credentials.routes"
)
_sessions_routes: Any = import_module(
    "backend.02_features.03_iam.sub_features.09_sessions.routes"
)
_magic_link_routes: Any = import_module(
    "backend.02_features.03_iam.sub_features.11_magic_link.routes"
)
_otp_routes: Any = import_module(
    "backend.02_features.03_iam.sub_features.12_otp.routes"
)
_passkeys_routes: Any = import_module(
    "backend.02_features.03_iam.sub_features.13_passkeys.routes"
)
_pw_reset_routes: Any = import_module(
    "backend.02_features.03_iam.sub_features.14_password_reset.routes"
)
_api_keys_routes: Any = import_module(
    "backend.02_features.03_iam.sub_features.15_api_keys.routes"
)
_email_verification_routes: Any = import_module(
    "backend.02_features.03_iam.sub_features.16_email_verification.routes"
)
_gdpr_routes: Any = import_module(
    "backend.02_features.03_iam.sub_features.19_gdpr.routes"
)
_invites_routes: Any = import_module(
    "backend.02_features.03_iam.sub_features.17_invites.routes"
)
_oidc_sso_routes: Any = import_module(
    "backend.02_features.03_iam.sub_features.20_oidc_sso.routes"
)

router = APIRouter()
router.include_router(_orgs_routes.router)
router.include_router(_ws_routes.router)
router.include_router(_users_routes.router)
router.include_router(_memberships_routes.router)
router.include_router(_roles_routes.router)
router.include_router(_groups_routes.router)
router.include_router(_applications_routes.router)
router.include_router(_credentials_routes.router)
router.include_router(_sessions_routes.router)
router.include_router(_auth_routes.router)
router.include_router(_magic_link_routes.router)
router.include_router(_otp_routes.router)
router.include_router(_passkeys_routes.router)
router.include_router(_pw_reset_routes.router)
router.include_router(_api_keys_routes.router)
router.include_router(_email_verification_routes.router)
router.include_router(_gdpr_routes.router)
router.include_router(_invites_routes.router)
router.include_router(_oidc_sso_routes.router)

# OIDC auth routes (no session required — browser-facing)
from fastapi import Request  # noqa: E402
from fastapi.responses import RedirectResponse  # noqa: E402

_oidc_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.20_oidc_sso.service"
)
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_core_id_mod: Any = import_module("backend.01_core.id")

_oidc_router = APIRouter(prefix="/v1/auth/oidc", tags=["iam.oidc_sso.auth"])


@_oidc_router.get("/{org_slug}/initiate")
async def oidc_initiate(org_slug: str, request: Request, provider: str = "default") -> Any:
    pool = request.app.state.pool
    vault = request.app.state.vault
    async with pool.acquire() as conn:
        try:
            url = await _oidc_service.build_initiate_url(
                pool, conn, vault, org_slug=org_slug, provider_slug=provider,
            )
        except Exception as exc:
            code = getattr(exc, "code", "OIDC_ERROR")
            return RedirectResponse(f"/auth/signin?error={code}", status_code=302)
    return RedirectResponse(url, status_code=302)


@_oidc_router.get("/{org_slug}/callback")
async def oidc_callback(org_slug: str, request: Request, code: str = "", state: str = "") -> Any:
    pool = request.app.state.pool
    vault = request.app.state.vault
    ctx = _catalog_ctx.NodeContext(
        user_id=None, session_id=None, org_id=None, workspace_id=None,
        trace_id=_core_id_mod.uuid7(), span_id=_core_id_mod.uuid7(),
        request_id=_core_id_mod.uuid7(), audit_category="setup",
        extras={"pool": pool},
    )
    if not code or not state:
        return RedirectResponse("/auth/signin?error=oidc_failed", status_code=302)
    async with pool.acquire() as conn:
        try:
            _user, token = await _oidc_service.handle_callback(
                pool, conn, ctx, vault, org_slug=org_slug, code=code, state=state,
            )
        except Exception:
            return RedirectResponse("/auth/signin?error=oidc_failed", status_code=302)

    response = RedirectResponse("/", status_code=302)
    response.set_cookie(
        key="tennetctl_session",
        value=token,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
    )
    return response


router.include_router(_oidc_router)
