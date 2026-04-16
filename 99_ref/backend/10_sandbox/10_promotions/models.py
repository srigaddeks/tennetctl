from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromotionRecord:
    id: str
    tenant_key: str
    signal_id: str | None
    policy_id: str | None
    library_id: str | None
    target_test_id: str | None
    promotion_status: str
    promoted_at: str | None
    promoted_by: str | None
    review_notes: str | None
    created_at: str
    created_by: str | None
    source_name: str | None = None
    source_code: str | None = None
    target_test_code: str | None = None
    source_org_id: str | None = None
