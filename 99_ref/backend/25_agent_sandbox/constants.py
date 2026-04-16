from __future__ import annotations

from enum import StrEnum


class AgentSandboxAuditEventType(StrEnum):
    # Agents
    AGENT_CREATED = "agent_created"
    AGENT_UPDATED = "agent_updated"
    AGENT_DELETED = "agent_deleted"
    AGENT_STATUS_CHANGED = "agent_status_changed"
    # Tools
    TOOL_REGISTERED = "tool_registered"
    TOOL_UPDATED = "tool_updated"
    TOOL_DELETED = "tool_deleted"
    # Execution
    AGENT_RUN_STARTED = "agent_run_started"
    AGENT_RUN_COMPLETED = "agent_run_completed"
    AGENT_RUN_FAILED = "agent_run_failed"
    AGENT_RUN_CANCELLED = "agent_run_cancelled"
    AGENT_RUN_PAUSED = "agent_run_paused"
    AGENT_RUN_RESUMED = "agent_run_resumed"
    # Test scenarios
    TEST_SCENARIO_CREATED = "test_scenario_created"
    TEST_SCENARIO_UPDATED = "test_scenario_updated"
    TEST_SCENARIO_DELETED = "test_scenario_deleted"
    TEST_SCENARIO_EXECUTED = "test_scenario_executed"
    # Tool bindings
    TOOL_BOUND = "tool_bound"
    TOOL_UNBOUND = "tool_unbound"
