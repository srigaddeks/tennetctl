from __future__ import annotations

from pydantic import BaseModel, Field


class PromoteSignalRequest(BaseModel):
    target_test_code: str | None = Field(
        None,
        min_length=2,
        max_length=100,
        description="Test code for the GRC control test. Auto-generated if not provided.",
    )
    linked_asset_id: str | None = Field(
        None,
        description="Connector instance ID to link as the asset for this test.",
    )
    workspace_id: str | None = Field(
        None,
        description="Workspace to scope this promoted test to. Falls back to source signal's workspace if not provided.",
    )


class PromotePolicyRequest(BaseModel):
    target_test_code: str | None = Field(
        None,
        min_length=2,
        max_length=100,
        description="Test code for the GRC control test. Auto-generated if not provided.",
    )
    linked_asset_id: str | None = Field(
        None,
        description="Connector instance ID to link as the asset for this test.",
    )
    workspace_id: str | None = Field(
        None,
        description="Workspace to scope this promoted test to. Falls back to source policy's workspace if not provided.",
    )


class PromoteLibraryRequest(BaseModel):
    target_test_code_prefix: str | None = Field(
        None,
        min_length=2,
        max_length=80,
        description="Prefix for generated test codes. Auto-generated if not provided.",
    )
    linked_asset_id: str | None = Field(
        None,
        description="Connector instance ID to link as the asset for all tests in this library.",
    )
    workspace_id: str | None = Field(
        None,
        description="Workspace to scope promoted tests to. Falls back to source policy's workspace if not provided.",
    )


class PromotionResponse(BaseModel):
    id: str
    tenant_key: str
    signal_id: str | None = None
    policy_id: str | None = None
    library_id: str | None = None
    target_test_id: str | None = None
    target_test_code: str | None = None
    source_name: str | None = None
    source_code: str | None = None
    promotion_status: str
    promoted_at: str | None = None
    promoted_by: str | None = None
    review_notes: str | None = None
    created_at: str
    created_by: str | None = None


class PromotionListResponse(BaseModel):
    items: list[PromotionResponse]
    total: int
