from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class FilterResult:
    allowed: bool
    action: str                    # "pass" | "redact" | "block" | "warn"
    severity: str                  # "low" | "medium" | "high" | "critical"
    matched_patterns: list[str] = field(default_factory=list)
    original_content: str = ""
    sanitized_content: str = ""
    filter_name: str = ""


class BaseFilter(ABC):
    """Abstract base for all guardrail filters."""

    @property
    @abstractmethod
    def filter_name(self) -> str: ...

    @property
    @abstractmethod
    def guardrail_type_code(self) -> str: ...

    @abstractmethod
    async def apply(self, content: str, *, config: dict) -> FilterResult: ...
