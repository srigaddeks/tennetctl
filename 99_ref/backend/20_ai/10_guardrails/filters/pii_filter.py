from __future__ import annotations

import re

from .base import BaseFilter, FilterResult

# PII patterns
_PATTERNS = {
    "email":       re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "ssn":         re.compile(r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b"),
    "credit_card": re.compile(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6011[0-9]{12})\b"),
    "api_key":     re.compile(r"\b(?:sk|pk|key|token|secret|api_key)[_-]?[A-Za-z0-9]{16,}\b", re.IGNORECASE),
    "password":    re.compile(r"\b(?:password|passwd|pwd)\s*[:=]\s*\S+", re.IGNORECASE),
    "phone":       re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "ip_address":  re.compile(r"\b(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"),
}

_REDACTION_MAP = {
    "email":       "[EMAIL_REDACTED]",
    "ssn":         "[SSN_REDACTED]",
    "credit_card": "[CARD_REDACTED]",
    "api_key":     "[API_KEY_REDACTED]",
    "password":    "[PASSWORD_REDACTED]",
    "phone":       "[PHONE_REDACTED]",
    "ip_address":  "[IP_REDACTED]",
}


class PIIFilter(BaseFilter):
    @property
    def filter_name(self) -> str:
        return "pii_filter"

    @property
    def guardrail_type_code(self) -> str:
        return "pii_filter"

    async def apply(self, content: str, *, config: dict) -> FilterResult:
        matched: list[str] = []
        sanitized = content
        enabled_patterns = config.get("enabled_patterns", list(_PATTERNS.keys()))

        for pattern_name in enabled_patterns:
            pattern = _PATTERNS.get(pattern_name)
            if not pattern:
                continue
            if pattern.search(sanitized):
                matched.append(pattern_name)
                sanitized = pattern.sub(_REDACTION_MAP[pattern_name], sanitized)

        if matched:
            return FilterResult(
                allowed=True,       # PII is redacted, not blocked
                action="redact",
                severity="high",
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
