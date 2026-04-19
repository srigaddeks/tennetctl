"""Unified Python SDK for the TennetCTL platform."""

from .audit import Audit, AuditEvents
from .auth import ApiKeys, Auth, Sessions
from .catalog import Catalog
from .client import Tennetctl
from .flags import Flags
from .iam import IAM
from .logs import Logs
from .metrics import Metrics
from .notify import Notify
from .traces import Traces
from .vault import Vault, VaultConfigs, VaultSecrets
from .errors import (
    AuthError,
    ConflictError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TennetctlError,
    ValidationError,
)

__version__ = "0.1.0"

__all__ = [
    "Tennetctl",
    "Auth",
    "Sessions",
    "ApiKeys",
    "Flags",
    "IAM",
    "Audit",
    "AuditEvents",
    "Notify",
    "Metrics",
    "Logs",
    "Traces",
    "Vault",
    "VaultSecrets",
    "VaultConfigs",
    "Catalog",
    "TennetctlError",
    "AuthError",
    "RateLimitError",
    "NotFoundError",
    "ValidationError",
    "ConflictError",
    "ServerError",
    "NetworkError",
    "__version__",
]
