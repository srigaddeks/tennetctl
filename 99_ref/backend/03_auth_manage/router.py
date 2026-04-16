from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Request, status

from .dependencies import get_auth_service, get_client_ip, get_current_access_claims, require_not_api_key
from .schemas import (
    AuthUserResponse,
    BatchSetUserPropertiesRequest,
    BatchSetUserPropertiesResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    GoogleAuthRequest,
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    PropertyKeyListResponse,
    RefreshRequest,
    RegisterResponse,
    RegistrationRequest,
    RequestEmailVerificationResponse,
    RequestOTPResponse,
    ResetPasswordRequest,
    SetUserPropertyRequest,
    TokenPairResponse,
    UserAccountListResponse,
    UserPropertyListResponse,
    UserPropertyResponse,
    VerifyEmailRequest,
    VerifyOTPRequest,
)
from .service import AuthService

_telemetry_module = import_module("backend.01_core.telemetry")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter


router = InstrumentedAPIRouter(prefix="/api/v1/auth/local", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=RegisterResponse)
async def register(
    payload: RegistrationRequest,
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
    client_ip: Annotated[str | None, Depends(get_client_ip)],
) -> RegisterResponse:
    return await service.register_user(
        payload,
        client_ip=client_ip,
        user_agent=request.headers.get("user-agent"),
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/login", response_model=TokenPairResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
    client_ip: Annotated[str | None, Depends(get_client_ip)],
) -> TokenPairResponse:
    return await service.authenticate_user(
        payload,
        client_ip=client_ip,
        user_agent=request.headers.get("user-agent"),
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/google", response_model=TokenPairResponse)
async def google_login(
    payload: GoogleAuthRequest,
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
    client_ip: Annotated[str | None, Depends(get_client_ip)],
) -> TokenPairResponse:
    """Authenticate with a Google ID token. Links or creates account automatically."""
    return await service.authenticate_google(
        id_token=payload.id_token,
        client_ip=client_ip,
        user_agent=request.headers.get("user-agent"),
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/refresh", response_model=TokenPairResponse)
async def refresh(
    payload: RefreshRequest,
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
    client_ip: Annotated[str | None, Depends(get_client_ip)],
) -> TokenPairResponse:
    return await service.refresh_session(
        payload,
        client_ip=client_ip,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
    client_ip: Annotated[str | None, Depends(get_client_ip)],
) -> ForgotPasswordResponse:
    return await service.request_password_reset(
        payload,
        client_ip=client_ip,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/reset-password", response_model=LogoutResponse)
async def reset_password(
    payload: ResetPasswordRequest,
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
    client_ip: Annotated[str | None, Depends(get_client_ip)],
) -> LogoutResponse:
    result = await service.reset_password(
        payload,
        client_ip=client_ip,
        request_id=getattr(request.state, "request_id", None),
    )
    return LogoutResponse(**result)


@router.post("/me/verify-email/request", response_model=RequestEmailVerificationResponse)
async def request_email_verification(
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
    claims=Depends(require_not_api_key),
    client_ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> RequestEmailVerificationResponse:
    return await service.request_email_verification(
        claims,
        client_ip=client_ip,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/me/verify-email", response_model=LogoutResponse)
async def verify_email(
    payload: VerifyEmailRequest,
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
    client_ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> LogoutResponse:
    result = await service.verify_email(
        payload,
        client_ip=client_ip,
        request_id=getattr(request.state, "request_id", None),
    )
    return LogoutResponse(**result)


@router.post("/me/otp/request", response_model=RequestOTPResponse)
async def request_otp(
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
    claims=Depends(require_not_api_key),
    client_ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> RequestOTPResponse:
    return await service.request_otp(
        claims,
        client_ip=client_ip,
        request_id=getattr(request.state, "request_id", None),
    )


@router.post("/me/otp/verify", response_model=LogoutResponse)
async def verify_otp(
    payload: VerifyOTPRequest,
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
    claims=Depends(require_not_api_key),
    client_ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> LogoutResponse:
    result = await service.verify_otp(
        claims,
        payload,
        client_ip=client_ip,
        request_id=getattr(request.state, "request_id", None),
    )
    return LogoutResponse(**result)


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    payload: LogoutRequest,
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
    claims=Depends(require_not_api_key),
    client_ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> LogoutResponse:
    result = await service.logout_session(
        payload,
        claims=claims,
        client_ip=client_ip,
        request_id=getattr(request.state, "request_id", None),
    )
    return LogoutResponse(**result)


@router.get("/me", response_model=AuthUserResponse)
async def me(
    service: Annotated[AuthService, Depends(get_auth_service)],
    claims=Depends(get_current_access_claims),
) -> AuthUserResponse:
    user = await service.get_authenticated_user(claims)
    return AuthUserResponse(
        user_id=user.user_id,
        tenant_key=user.tenant_key,
        email=user.email,
        username=user.username,
        email_verified=user.email_verified,
        account_status=user.account_status,
        user_category=user.user_category,
    )


@router.get("/me/properties", response_model=UserPropertyListResponse)
async def get_properties(
    service: Annotated[AuthService, Depends(get_auth_service)],
    claims=Depends(get_current_access_claims),
) -> UserPropertyListResponse:
    return await service.get_user_properties(claims)


@router.put("/me/properties", response_model=BatchSetUserPropertiesResponse)
async def batch_set_properties(
    payload: BatchSetUserPropertiesRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
    claims=Depends(get_current_access_claims),
    client_ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> BatchSetUserPropertiesResponse:
    return await service.batch_set_user_properties(
        claims, properties=payload.properties, client_ip=client_ip,
    )


@router.get("/me/property-keys", response_model=PropertyKeyListResponse)
async def get_property_keys(
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> PropertyKeyListResponse:
    return await service.list_property_keys()


@router.put("/me/properties/{key}", response_model=UserPropertyResponse)
async def set_property(
    key: str,
    payload: SetUserPropertyRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
    claims=Depends(get_current_access_claims),
    client_ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> UserPropertyResponse:
    return await service.set_user_property(
        claims,
        property_key=key,
        property_value=payload.value,
        client_ip=client_ip,
    )


@router.delete("/me/properties/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property(
    key: str,
    service: Annotated[AuthService, Depends(get_auth_service)],
    claims=Depends(get_current_access_claims),
    client_ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> None:
    await service.delete_user_property(claims, property_key=key, client_ip=client_ip)


@router.put("/me/password", response_model=LogoutResponse)
async def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
    claims=Depends(require_not_api_key),
    client_ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> LogoutResponse:
    result = await service.change_password(
        claims, payload=payload, client_ip=client_ip,
        request_id=getattr(request.state, "request_id", None),
    )
    return LogoutResponse(**result)


@router.get("/me/accounts", response_model=UserAccountListResponse)
async def get_accounts(
    service: Annotated[AuthService, Depends(get_auth_service)],
    claims=Depends(get_current_access_claims),
) -> UserAccountListResponse:
    return await service.list_user_accounts(claims)
