from __future__ import annotations

import re

from .base import BaseFilter, FilterResult

_BLOCKED_CATEGORIES = {
    "self_harm":  [re.compile(r"\b(?:suicide|self.harm|kill\s+myself)\b", re.IGNORECASE)],
    "hate":       [re.compile(r"\b(?:racial\s+slur|hate\s+speech)\b", re.IGNORECASE)],
    "off_topic":  [],  # Populated from config.blocked_keywords
}


class ContentFilter(BaseFilter):
    @property
    def filter_name(self) -> str:
        return "content_filter"

    @property
    def guardrail_type_code(self) -> str:
        return "content_policy"

    async def apply(self, content: str, *, config: dict) -> FilterResult:
        matched: list[str] = []

        # Built-in category checks
        for category, patterns in _BLOCKED_CATEGORIES.items():
            if not config.get(f"block_{category}", True):
                continue
            for pattern in patterns:
                if pattern.search(content):
                    matched.append(category)
                    break

        # Custom blocked keywords from org config
        custom_keywords = config.get("blocked_keywords", [])
        for kw in custom_keywords:
            if kw.lower() in content.lower():
                matched.append(f"keyword:{kw}")

        if matched:
            return FilterResult(
                allowed=False,
                action="block",
                severity="high",
                matched_patterns=matched,
                original_content=content,
                sanitized_content="",
                filter_name=self.filter_name,
            )
        return FilterResult(
            allowed=True, action="pass", severity="low",
            original_content=content, sanitized_content=content,
            filter_name=self.filter_name,
        )
