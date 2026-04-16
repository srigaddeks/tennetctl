from __future__ import annotations

from pydantic import BaseModel, Field


class CreateSignalRequest(BaseModel):
    signal_code: str = Field(
        ..., min_length=2, max_length=100, pattern=r"^[a-z0-9_]{2,100}$"
    )
    workspace_id: str | None = None
    timeout_ms: int = Field(default=5000, ge=100, le=60000)
    max_memory_mb: int = Field(default=128, ge=16, le=2048)
    properties: dict[str, str] = Field(
        ..., description="Must include 'name' and 'python_source'"
    )


class BulkSignalDefinition(BaseModel):
    signal_code: str = Field(
        ..., min_length=2, max_length=100, pattern=r"^[a-z0-9_]{2,100}$"
    )
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    python_source: str = Field(..., min_length=10)
    connector_type_codes: list[str] = Field(default_factory=list)
    timeout_ms: int = Field(default=5000, ge=100, le=60000)
    max_memory_mb: int = Field(default=128, ge=16, le=2048)


class BulkImportRequest(BaseModel):
    signals: list[BulkSignalDefinition] = Field(..., min_length=1, max_length=500)
    workspace_id: str | None = None


class BulkImportResultItem(BaseModel):
    signal_code: str
    status: str  # created | updated | failed
    signal_id: str | None = None
    error: str | None = None


class BulkImportResponse(BaseModel):
    total: int
    created: int
    updated: int
    failed: int
    results: list[BulkImportResultItem]


class UpdateSignalRequest(BaseModel):
    timeout_ms: int | None = Field(None, ge=100, le=60000)
    max_memory_mb: int | None = Field(None, ge=16, le=2048)
    properties: dict[str, str] | None = None


class GenerateSignalRequest(BaseModel):
    prompt: str = Field(..., min_length=10)
    connector_type_code: str = Field(..., min_length=1, max_length=50)
    sample_dataset_id: str | None = None
    asset_version_code: str | None = None


class GenerateSignalResponse(BaseModel):
    generated_code: str
    compile_status: str
    test_result: dict | None = None
    caep_event_type: str | None = None
    risc_event_type: str | None = None
    custom_event_type: str | None = None
    iterations_used: int = 0
    signal_name_suggestion: str = ""
    signal_description_suggestion: str = ""
    signal_args_schema: list[dict] | None = None
    ssf_mapping: dict | None = None


class ExecuteSignalRequest(BaseModel):
    dataset: dict | None = Field(
        default=None,
        description="Dataset to execute the signal against. If not provided, loads the signal's test dataset",
    )
    configurable_args: dict = Field(
        default_factory=dict,
        description="Named kwargs to pass to evaluate() — must match signal's args schema defaults",
    )


class ExecuteSignalResponse(BaseModel):
    status: str  # completed | failed | timeout
    result_code: str | None = None  # pass | fail | warning
    result_summary: str = ""
    result_details: list[dict] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    stdout_capture: str = ""
    error_message: str | None = None
    execution_time_ms: int = 0


class ValidateSignalRequest(BaseModel):
    pass


class SignalResponse(BaseModel):
    id: str
    tenant_key: str
    org_id: str
    workspace_id: str | None = None
    signal_code: str
    version_number: int
    signal_status_code: str
    signal_status_name: str | None = None
    python_hash: str | None = None
    timeout_ms: int
    max_memory_mb: int
    is_active: bool
    created_at: str
    updated_at: str
    name: str | None = None
    description: str | None = None
    python_source: str | None = None
    source_prompt: str | None = None
    caep_event_type: str | None = None
    risc_event_type: str | None = None
    properties: dict[str, str] | None = None


class SignalListResponse(BaseModel):
    items: list[SignalResponse]
    total: int


class SignalVersionResponse(BaseModel):
    version_number: int
    signal_status_code: str
    python_hash: str | None = None
    created_at: str
    created_by: str | None = None


# ── Test suite schemas ─────────────────────────────────────────────────────────


class TestCaseResult(BaseModel):
    case_id: str | None = None
    scenario_name: str | None = None
    expected: str  # pass | fail | warning
    actual: str | None = None  # pass | fail | warning | error
    passed: bool
    error: str | None = None
    execution_time_ms: int = 0
    diff: dict = Field(default_factory=dict)


class TestSuiteResponse(BaseModel):
    signal_id: str
    test_dataset_id: str | None = None
    total_cases: int
    passed: int
    failed: int
    errored: int
    pass_rate: float
    results: list[TestCaseResult]


class ExecuteLiveRequest(BaseModel):
    configurable_args: dict = Field(default_factory=dict)
    connector_instance_id: str | None = None


class ExecuteLiveResponse(BaseModel):
    signal_id: str
    status: str  # completed | failed | timeout
    result_code: str | None = None
    result_summary: str = ""
    result_details: list[dict] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    dataset_row_count: int = 0
    execution_time_ms: int = 0
