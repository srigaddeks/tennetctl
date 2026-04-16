from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module


_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")

get_logger = _logging_module.get_logger
start_operation_span = _telemetry_module.start_operation_span
_LOGGER = get_logger("backend.errors")


@dataclass(slots=True)
class AppError(Exception):
    status_code: int
    code: str
    message: str

    def __post_init__(self) -> None:
        with start_operation_span(
            "app_error.create",
            attributes={
                "error.code": self.code,
                "http.response.status_code": self.status_code,
            },
        ):
            _LOGGER.info(
                "app_error_created",
                extra={
                    "action": "app_error.create",
                    "outcome": "error",
                    "error_code": self.code,
                    "http_status_code": self.status_code,
                },
            )

    def __str__(self) -> str:
        return self.message


class AuthFeatureDisabledError(AppError):
    def __init__(self) -> None:
        super().__init__(503, "auth_feature_disabled", "Local authentication is not enabled.")


class AuthenticationError(AppError):
    def __init__(self, message: str = "Authentication failed.") -> None:
        super().__init__(401, "authentication_failed", message)


class AuthorizationError(AppError):
    def __init__(self, message: str = "Access denied.") -> None:
        super().__init__(403, "access_denied", message)


class ConflictError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(409, "conflict", message)


class RateLimitError(AppError):
    def __init__(self, message: str = "Too many attempts. Please try again later.") -> None:
        super().__init__(429, "rate_limited", message)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found.") -> None:
        super().__init__(404, "not_found", message)


class ValidationError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(422, "validation_error", message)


class ServiceUnavailableError(AppError):
    def __init__(self, message: str = "Service temporarily unavailable. Please try again later.") -> None:
        super().__init__(503, "service_unavailable", message)
