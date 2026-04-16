from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


IdentifierField = Annotated[str, Field(min_length=3, max_length=320)]
PasswordField = Annotated[str, Field(min_length=12, max_length=256)]
UsernameField = Annotated[str, Field(min_length=3, max_length=32, pattern=r"^[a-z0-9_.-]+$")]


class RegistrationRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: Annotated[str, Field(min_length=5, max_length=320)]
    password: PasswordField
    username: UsernameField | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("email must be a valid address.")
        return normalized

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip().lower()
        if "@" in normalized:
            raise ValueError("username must not contain '@'.")
        return normalized


class LoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    login: IdentifierField
    password: PasswordField


class GoogleAuthRequest(BaseModel):
    """Request body for Google OAuth login (ID token from frontend)."""
    model_config = ConfigDict(str_strip_whitespace=True)

    id_token: Annotated[str, Field(min_length=10, max_length=8192)]


class RefreshRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    refresh_token: Annotated[str, Field(min_length=10, max_length=512)]


class LogoutRequest(RefreshRequest):
    pass


class ForgotPasswordRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    login: IdentifierField


class ForgotPasswordResponse(BaseModel):
    message: str
    reset_token: str | None = None


class ResetPasswordRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    reset_token: Annotated[str, Field(min_length=10, max_length=512)]
    new_password: PasswordField


class RegisterResponse(BaseModel):
    user_id: str
    email: str
    username: str | None
    tenant_key: str
    email_verified: bool


class AuthUserResponse(BaseModel):
    user_id: str
    tenant_key: str
    email: str
    username: str | None
    email_verified: bool
    account_status: str
    user_category: str = "full"
    is_new_user: bool = False


class TokenPairResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str
    refresh_expires_in: int
    user: AuthUserResponse | None = None


class LogoutResponse(BaseModel):
    message: str


# ── User property schemas ────────────────────────────────────────────────

class UserPropertyResponse(BaseModel):
    key: str
    value: str


class UserPropertyListResponse(BaseModel):
    properties: list[UserPropertyResponse]


class SetUserPropertyRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    value: Annotated[str, Field(min_length=1, max_length=2000)]


class BatchSetUserPropertiesRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    properties: dict[str, Annotated[str, Field(min_length=1, max_length=2000)]]


class BatchSetUserPropertiesResponse(BaseModel):
    properties: list[UserPropertyResponse]


# ── Property key schemas ────────────────────────────────────────────────

class PropertyKeyResponse(BaseModel):
    code: str
    name: str
    description: str
    data_type: str
    is_pii: bool
    is_required: bool
    sort_order: int


class PropertyKeyListResponse(BaseModel):
    keys: list[PropertyKeyResponse]


# ── Password change schemas ─────────────────────────────────────────────

class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    current_password: PasswordField
    new_password: PasswordField


# ── User account schemas ────────────────────────────────────────────────

class UserAccountResponse(BaseModel):
    account_type: str
    is_primary: bool
    is_active: bool
    properties: dict[str, str]


class UserAccountListResponse(BaseModel):
    accounts: list[UserAccountResponse]


# ── Email verification schemas ─────────────────────────────────────────

class RequestEmailVerificationResponse(BaseModel):
    message: str
    verification_token: str | None = None  # returned in dev environments only


class VerifyEmailRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    verification_token: Annotated[str, Field(min_length=10, max_length=512)]


# ── OTP verification schemas ─────────────────────────────────────────

class RequestOTPResponse(BaseModel):
    message: str
    otp_code: str | None = None  # returned in dev environments only


class VerifyOTPRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    otp_code: Annotated[str, Field(min_length=6, max_length=6, pattern=r"^\d{6}$")]
