from __future__ import annotations

import re

from .base import BaseFilter, FilterResult

# Prompt injection heuristics
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions?", re.IGNORECASE),
    re.compile(r"forget\s+(?:everything|all)\s+(?:you\s+)?(?:know|were\s+told)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(?:a\s+)?(?:different|new|another)\s+(?:ai|assistant|bot|model)", re.IGNORECASE),
    re.compile(r"(?:system\s+)?prompt\s*[:=]\s*", re.IGNORECASE),
    re.compile(r"<\s*system\s*>", re.IGNORECASE),
    re.compile(r"\[system\]", re.IGNORECASE),
    re.compile(r"do\s+not\s+follow\s+(?:your\s+)?(?:instructions?|guidelines?|rules?)", re.IGNORECASE),
    re.compile(r"(?:reveal|show|print|output|display)\s+(?:your\s+)?(?:system\s+)?(?:prompt|instructions?|guidelines?)", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
    re.compile(r"DAN\s+mode", re.IGNORECASE),
    re.compile(r"act\s+as\s+(?:if\s+)?(?:you\s+(?:are|were)\s+)?(?:an?\s+)?(?:unrestricted|uncensored|free)", re.IGNORECASE),
]

_BLOCK_THRESHOLD = 2  # Number of pattern matches before blocking


class InjectionFilter(BaseFilter):
    @property
    def filter_name(self) -> str:
        return "injection_filter"

    @property
    def guardrail_type_code(self) -> str:
        return "injection_detect"

    async def apply(self, content: str, *, config: dict) -> FilterResult:
        threshold = config.get("block_threshold", _BLOCK_THRESHOLD)
        matched: list[str] = []

        for pattern in _INJECTION_PATTERNS:
            match = pattern.search(content)
            if match:
                matched.append(match.group(0)[:100])

        score = len(matched)
        if score == 0:
            return FilterResult(
                allowed=True, action="pass", severity="low",
                original_content=content, sanitized_content=content,
                filter_name=self.filter_name,
            )
        if score >= threshold:
            return FilterResult(
                allowed=False,
                action="block",
                severity="critical",
                matched_patterns=matched,
                original_content=content,
                sanitized_content="",
                filter_name=self.filter_name,
            )
        # Single match — warn but allow
        return FilterResult(
            allowed=True,
            action="warn",
            severity="medium",
            matched_patterns=matched,
            original_content=content,
            sanitized_content=content,
            filter_name=self.filter_name,
        )
