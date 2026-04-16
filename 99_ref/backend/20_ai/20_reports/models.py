from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ReportRecord:
    id: str
    tenant_key: str
    org_id: str | None
    workspace_id: str | None
    report_type: str
    status_code: str
    title: str | None
    parameters_json: dict
    content_markdown: str | None
    word_count: int | None
    token_count: int | None
    generated_by_user_id: str | None
    agent_run_id: str | None
    job_id: str | None
    error_message: str | None
    is_auto_generated: bool
    trigger_entity_type: str | None
    trigger_entity_id: str | None
    created_at: str
    completed_at: str | None
    updated_at: str


@dataclass
class ReportGenState:
    """Mutable pipeline state threaded through all agent stages."""
    report_id: str
    job_id: str
    report_type: str
    org_id: str
    workspace_id: str | None
    parameters: dict
    user_id: str
    tenant_key: str

    # Pipeline state
    plan: dict = field(default_factory=dict)
    collected_data: dict = field(default_factory=dict)
    analysis: dict = field(default_factory=dict)
    sections: list[dict] = field(default_factory=list)
    markdown_content: str = ""

    # Meta
    status: str = "planning"
    error: str | None = None
    tokens_consumed: int = 0
    iteration: int = 0


@dataclass(frozen=True)
class ReportSummary:
    id: str
    report_type: str
    title: str | None
    status_code: str
    word_count: int | None
    is_auto_generated: bool
    created_at: str
    completed_at: str | None
