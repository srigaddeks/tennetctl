"""somaerp error hierarchy. Each subclass carries an `error_code`."""

from __future__ import annotations


class SomaerpError(Exception):
    """Base error. Subclasses set `error_code` and `status_code`."""

    error_code: str = "SOMAERP_ERROR"
    status_code: int = 500

    def __init__(self, message: str, *, code: str | None = None, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.error_code = code
        if status_code is not None:
            self.status_code = status_code

    @property
    def code(self) -> str:
        return self.error_code


class NotFoundError(SomaerpError):
    error_code = "NOT_FOUND"
    status_code = 404


class ValidationError(SomaerpError):
    error_code = "VALIDATION_ERROR"
    status_code = 422


class AuthError(SomaerpError):
    error_code = "UNAUTHORIZED"
    status_code = 401


class TennetctlProxyError(SomaerpError):
    """tennetctl returned ok=false or non-2xx. Maps to 502 by default."""

    error_code = "TENNETCTL_PROXY_ERROR"
    status_code = 502


class TenancyError(SomaerpError):
    """Cross-tenant access attempted, or tenant scope missing."""

    error_code = "TENANCY_ERROR"
    status_code = 403
