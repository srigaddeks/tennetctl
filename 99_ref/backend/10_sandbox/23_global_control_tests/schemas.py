from __future__ import annotations

from pydantic import BaseModel, Field


# ── Bundle sub-schemas ────────────────────────────────────────────────────────

class SignalBundle(BaseModel):
    signal_code: str
    name: str
    description: str = ""
    python_source: str
    connector_type_codes: list[str] = Field(default_factory=list)
    timeout_ms: int = 5000
    max_memory_mb: int = 128
    source_prompt: str | None = None


class ThreatTypeBundle(BaseModel):
    threat_code: str
    name: str
    description: str = ""
    severity_code: str = "high"
    expression_tree: dict = Field(default_factory=dict)
    mitigation_guidance: str | None = None


class PolicyBundle(BaseModel):
    policy_code: str
    name: str
    description: str = ""
    actions: list[dict] = Field(default_factory=list)
    cooldown_minutes: int = 0


class TestDatasetRecord(BaseModel):
    record_name: str | None = None
    description: str | None = None
    record_data: dict = Field(default_factory=dict)
    expected_result: str | None = None  # pass/fail/warning
    scenario_name: str | None = None


class TestDatasetBundle(BaseModel):
    dataset_code: str
    name: str = ""
    description: str = ""
    record_count: int = 0
    records: list[TestDatasetRecord] = Field(default_factory=list)
    json_schema: dict | None = None  # field schema from source data


class DatasetTemplateBundle(BaseModel):
    connector_type_code: str = ""
    json_schema: dict = Field(default_factory=dict)  # {field_path: {type, example, nullable}}
    sample_records: list[dict] = Field(default_factory=list)  # first N real records (sanitized)
    field_count: int = 0


class ControlTestBundle(BaseModel):
    signals: list[SignalBundle] = Field(default_factory=list)
    threat_type: ThreatTypeBundle | None = None
    policy: PolicyBundle | None = None
    test_dataset: TestDatasetBundle | None = None
    dataset_template: DatasetTemplateBundle | None = None


# ── Request models ────────────────────────────────────────────────────────────

class PublishGlobalControlTestRequest(BaseModel):
    source_signal_id: str = Field(..., description="UUID of the signal to publish (chain extracted automatically)")
    global_code: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    linked_dataset_code: str | None = None
    properties: dict[str, str] = Field(default_factory=dict)


class UpdateGlobalControlTestRequest(BaseModel):
    properties: dict[str, str] | None = None
    is_featured: bool | None = None


class DeployControlTestRequest(BaseModel):
    org_id: str
    workspace_id: str
    connector_instance_id: str | None = None


# ── Response models ───────────────────────────────────────────────────────────

class GlobalControlTestResponse(BaseModel):
    id: str
    global_code: str
    connector_type_code: str
    connector_type_name: str | None = None
    version_number: int
    bundle: ControlTestBundle = Field(default_factory=ControlTestBundle)
    source_signal_id: str | None = None
    source_policy_id: str | None = None
    source_library_id: str | None = None
    source_org_id: str | None = None
    linked_dataset_code: str | None = None
    publish_status: str = "published"
    is_featured: bool = False
    download_count: int = 0
    signal_count: int = 0
    published_by: str | None = None
    published_at: str | None = None
    created_at: str = ""
    updated_at: str = ""
    # Flattened EAV
    name: str | None = None
    description: str | None = None
    tags: str | None = None
    category: str | None = None
    changelog: str | None = None
    compliance_references: str | None = None


class GlobalControlTestListResponse(BaseModel):
    items: list[GlobalControlTestResponse]
    total: int


class GlobalControlTestStatsResponse(BaseModel):
    total: int
    by_connector_type: dict[str, int] = Field(default_factory=dict)
    by_category: dict[str, int] = Field(default_factory=dict)
    featured_count: int = 0


class DeployResultResponse(BaseModel):
    created_signal_ids: list[str]
    created_threat_type_id: str | None = None
    created_policy_id: str | None = None
    created_test_dataset_id: str | None = None
    created_dataset_template_id: str | None = None
    promoted_test_id: str | None = None
    signal_count: int
    global_source_code: str
    global_source_version: int
