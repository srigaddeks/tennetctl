from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ControlCandidate:
    control_id: str
    control_code: str
    control_name: str | None
    control_category_code: str | None
    criticality_code: str | None
    framework_id: str
    framework_code: str
    framework_name: str | None
    tags: str | None
    description: str | None


@dataclass(frozen=True)
class ControlSuggestion:
    control_id: str
    control_code: str
    control_name: str | None
    control_category_code: str | None
    criticality_code: str | None
    framework_id: str
    framework_code: str
    framework_name: str | None
    suggested_link_type: str   # mitigating | compensating | related
    relevance_score: int       # 1–100
    rationale: str
    already_linked: bool


@dataclass(frozen=True)
class BulkLinkStats:
    framework_id: str
    framework_code: str
    total_controls: int
    risks_scanned: int
    mappings_created: int
    mappings_skipped: int
    errors: int
