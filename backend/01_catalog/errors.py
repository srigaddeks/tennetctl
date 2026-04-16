"""
Runner error hierarchy for the node catalog runtime.

These errors are raised by `run_node` (runner.py) and by user node handlers.
TransientError is the ONLY class that triggers runner retries; every other
error propagates immediately.
"""

from __future__ import annotations


class RunnerError(Exception):
    """Base class for catalog runtime errors."""

    code: str = "CAT_UNKNOWN"

    def __init__(self, message: str, *, node_key: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.node_key = node_key

    def __str__(self) -> str:
        if self.node_key:
            return f"[{self.code}] {self.message} (node={self.node_key})"
        return f"[{self.code}] {self.message}"


class NodeNotFound(RunnerError):
    code = "CAT_NODE_NOT_FOUND"


class NodeTombstoned(RunnerError):
    code = "CAT_NODE_TOMBSTONED"


class NodeAuthDenied(RunnerError):
    code = "CAT_AUTH_DENIED"


class NodeTimeout(RunnerError):
    code = "CAT_TIMEOUT"


class IdempotencyRequired(RunnerError):
    code = "CAT_IDEMPOTENCY_REQUIRED"


class TransientError(RunnerError):
    """Retryable failure. Subclass in user code for domain-specific transients."""

    code = "CAT_TRANSIENT"


class DomainError(RunnerError):
    """Non-retryable domain failure. Runner never retries this class."""

    code = "CAT_DOMAIN"
