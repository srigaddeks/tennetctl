from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TestScenarioRecord:
    id: str
    tenant_key: str
    org_id: str
    workspace_id: str | None
    scenario_code: str
    scenario_type_code: str
    agent_id: str | None
    is_active: bool
    created_at: str
    updated_at: str
    name: str | None
    description: str | None


@dataclass(frozen=True)
class TestCaseRecord:
    id: str
    scenario_id: str
    case_index: int
    input_messages: list[dict]
    initial_context: dict
    expected_behavior: dict
    evaluation_method_code: str
    evaluation_config: dict
    is_active: bool
    created_at: str
