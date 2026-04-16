"""
Application error hierarchy.

All application errors extend AppError. Each subclass has a default
status code and error code. Middleware catches AppError and returns
the standard error envelope.
"""

from __future__ import annotations


class AppError(Exception):
    """Base application error."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 500,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class NotFoundError(AppError):
    def __init__(self, message: str, code: str = "NOT_FOUND") -> None:
        super().__init__(code=code, message=message, status_code=404)


class ValidationError(AppError):
    def __init__(self, message: str, code: str = "VALIDATION_ERROR") -> None:
        super().__init__(code=code, message=message, status_code=422)


class ConflictError(AppError):
    def __init__(self, message: str, code: str = "CONFLICT") -> None:
        super().__init__(code=code, message=message, status_code=409)


class ForbiddenError(AppError):
    def __init__(self, message: str, code: str = "FORBIDDEN") -> None:
        super().__init__(code=code, message=message, status_code=403)


class UnauthorizedError(AppError):
    def __init__(self, message: str, code: str = "UNAUTHORIZED") -> None:
        super().__init__(code=code, message=message, status_code=401)
