from __future__ import annotations

from enum import StrEnum


class AIAuditEventType(StrEnum):
    # Conversations
    CONVERSATION_CREATED = "conversation_created"
    CONVERSATION_ARCHIVED = "conversation_archived"
    CONVERSATION_DELETED = "conversation_deleted"
    # Messages
    MESSAGE_SENT = "message_sent"
    MESSAGE_STREAMED = "message_streamed"
    # Agent runs
    AGENT_RUN_STARTED = "agent_run_started"
    AGENT_RUN_COMPLETED = "agent_run_completed"
    AGENT_RUN_FAILED = "agent_run_failed"
    AGENT_RUN_CANCELLED = "agent_run_cancelled"
    # Tool calls
    TOOL_CALLED = "tool_called"
    TOOL_CALL_FAILED = "tool_call_failed"
    # Approvals
    APPROVAL_CREATED = "approval_created"
    APPROVAL_APPROVED = "approval_approved"
    APPROVAL_REJECTED = "approval_rejected"
    APPROVAL_EXECUTED = "approval_executed"
    APPROVAL_EXPIRED = "approval_expired"
    APPROVAL_CANCELLED = "approval_cancelled"
    # Memory
    MEMORY_STORED = "memory_stored"
    MEMORY_DELETED = "memory_deleted"
    MEMORY_RECALLED = "memory_recalled"
    # Budgets
    BUDGET_CREATED = "budget_created"
    BUDGET_UPDATED = "budget_updated"
    BUDGET_EXCEEDED = "budget_exceeded"
    BUDGET_USAGE_RECORDED = "budget_usage_recorded"
    # Guardrails
    GUARDRAIL_TRIGGERED = "guardrail_triggered"
    GUARDRAIL_CONFIG_UPDATED = "guardrail_config_updated"
    # Agent config
    AGENT_CONFIG_CREATED = "agent_config_created"
    AGENT_CONFIG_UPDATED = "agent_config_updated"
    AGENT_CONFIG_DELETED = "agent_config_deleted"
    # Prompt templates
    PROMPT_TEMPLATE_CREATED = "prompt_template_created"
    PROMPT_TEMPLATE_UPDATED = "prompt_template_updated"
    PROMPT_TEMPLATE_DELETED = "prompt_template_deleted"
    # Admin
    ADMIN_CONVERSATION_VIEWED = "admin_conversation_viewed"
    ADMIN_AGENT_KILLED = "admin_agent_killed"
    APPROVAL_POLICY_UPDATED = "approval_policy_updated"
    # Job queue
    JOB_QUEUED = "job_queued"
    JOB_STARTED = "job_started"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    JOB_CANCELLED = "job_cancelled"
    JOB_RETRY_SCHEDULED = "job_retry_scheduled"
    BATCH_CREATED = "batch_created"
    BATCH_COMPLETED = "batch_completed"
    RATE_LIMIT_HIT = "rate_limit_hit"
    RATE_LIMIT_CONFIG_UPDATED = "rate_limit_config_updated"
    # Reports
    REPORT_UPDATED = "report_updated"
    REPORT_SUBMITTED = "report_submitted"
    # Swarm
    SWARM_DELEGATION_CREATED = "swarm_delegation_created"
    SWARM_DELEGATION_COMPLETED = "swarm_delegation_completed"
