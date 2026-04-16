from __future__ import annotations

import re

from .base import BaseFilter, FilterResult

# Strip common LLM output leakage patterns
_LEAK_PATTERNS = [
    (re.compile(r"<system>.*?</system>", re.IGNORECASE | re.DOTALL), "[SYSTEM_PROMPT_REDACTED]"),
    (re.compile(r"\[INST\].*?\[/INST\]", re.DOTALL), "[INSTRUCTION_REDACTED]"),
    (re.compile(r'(?:schema|table)\s+"?\d\d_[a-z_]+"?', re.IGNORECASE), "[SCHEMA_REDACTED]"),
    (re.compile(r"Traceback \(most recent call last\).*?(?:\n\n|\Z)", re.DOTALL), "[TRACEBACK_REDACTED]"),
    (re.compile(r"postgres(?:ql)?\s+error", re.IGNORECASE), "[DB_ERROR_REDACTED]"),
    (re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"),
     lambda m: m.group(0)[:8] + "****"),  # Partially mask UUIDs
]


class OutputFilter(BaseFilter):
    @property
    def filter_name(self) -> str:
        return "output_filter"

    @property
    def guardrail_type_code(self) -> str:
        return "output_filter"

    async def apply(self, content: str, *, config: dict) -> FilterResult:
        sanitized = content
        matched: list[str] = []

        for pattern, replacement in _LEAK_PATTERNS:
            if isinstance(replacement, str):
                new_content = pattern.sub(replacement, sanitized)
            else:
                new_content = pattern.sub(replacement, sanitized)
            if new_content != sanitized:
                matched.append(pattern.pattern[:60])
                sanitized = new_content

        if matched:
            return FilterResult(
                allowed=True,
                action="redact",
                severity="medium",
                matched_patterns=matched,
                original_content=content,
                sanitized_content=sanitized,
                filter_name=self.filter_name,
            )
        return FilterResult(
            allowed=True, action="pass", severity="low",
            original_content=content, sanitized_content=content,
            filter_name=self.filter_name,
        )
