from __future__ import annotations

from typing import Any


class TennetctlError(Exception):
    def __init__(
        self,
        message: str,
        *,
        code: str = "UNKNOWN",
        status: int | None = None,
        data: Any = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.data = data

    def __repr__(self) -> str:
        return f"{type(self).__name__}(code={self.code!r}, status={self.status!r}, message={self.message!r})"


class AuthError(TennetctlError):
    """401 / 403 — missing, invalid, or expired credentials."""


class RateLimitError(TennetctlError):
    """429 — too many requests."""


class NotFoundError(TennetctlError):
    """404 — resource not found."""


class ValidationError(TennetctlError):
    """400 / 422 — request payload invalid."""


class ConflictError(TennetctlError):
    """409 — resource conflict (duplicate, stale write)."""


class ServerError(TennetctlError):
    """5xx — backend error after retries exhausted."""


class NetworkError(TennetctlError):
    """Connection / timeout before receiving a response."""


_STATUS_MAP: dict[int, type[TennetctlError]] = {
    400: ValidationError,
    401: AuthError,
    403: AuthError,
    404: NotFoundError,
    409: ConflictError,
    422: ValidationError,
    429: RateLimitError,
}


def map_error(status: int, envelope: dict | None) -> TennetctlError:
    """Convert an HTTP status + error envelope into a typed exception."""
    cls: type[TennetctlError]
    if status >= 500:
        cls = ServerError
    else:
        cls = _STATUS_MAP.get(status, TennetctlError)

    code = "UNKNOWN"
    message = f"HTTP {status}"
    if isinstance(envelope, dict):
        err = envelope.get("error")
        if isinstance(err, dict):
            code = str(err.get("code") or code)
            message = str(err.get("message") or message)
    return cls(message, code=code, status=status, data=envelope)
