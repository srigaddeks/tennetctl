"""Action dispatchers for different delivery kinds (webhook, email, Slack, etc.)."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class DeliveryResult:
    """Result of an action delivery attempt."""

    success: bool
    status_code: Optional[int] = None
    response_excerpt: Optional[str] = None
    error_message: Optional[str] = None
