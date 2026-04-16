from __future__ import annotations

from importlib import import_module

_dimensions_module = import_module("backend.20_ai.01_dimensions.router")
_conversations_module = import_module("backend.20_ai.02_conversations.router")
_memory_module = import_module("backend.20_ai.03_memory.router")
_agents_module = import_module("backend.20_ai.04_agents.router")
_mcp_module = import_module("backend.20_ai.05_mcp.router")
_approvals_module = import_module("backend.20_ai.06_approvals.router")
_reporting_module = import_module("backend.20_ai.07_reporting.router")
_budgets_module = import_module("backend.20_ai.09_budgets.router")
_guardrails_module = import_module("backend.20_ai.10_guardrails.router")
_admin_module = import_module("backend.20_ai.11_admin.router")
_agent_config_module = import_module("backend.20_ai.12_agent_config.router")
_prompt_config_module = import_module("backend.20_ai.13_prompt_config.router")
_job_queue_module = import_module("backend.20_ai.15_job_queue.router")
_evidence_checker_module = import_module("backend.20_ai.16_evidence_checker.router")
_text_enhancer_module = import_module("backend.20_ai.17_text_enhancer.router")
_form_fill_module = import_module("backend.20_ai.18_form_fill.router")
_attachments_module = import_module("backend.20_ai.19_attachments.router")
_reports_module = import_module("backend.20_ai.20_reports.router")
_framework_builder_module = import_module("backend.20_ai.21_framework_builder.router")
_signal_spec_module = import_module("backend.20_ai.22_signal_spec.router")
_signal_codegen_module = import_module("backend.20_ai.24_signal_codegen.router")
_dataset_agent_module = import_module("backend.20_ai.27_dataset_agent.router")
_pdf_templates_module = import_module("backend.20_ai.28_pdf_templates.router")
_risk_advisor_module = import_module("backend.20_ai.29_risk_advisor.router")
_test_linker_module = import_module("backend.20_ai.30_test_linker.router")
_task_builder_module = import_module("backend.20_ai.31_task_builder.router")

dimensions_router = _dimensions_module.router
conversations_router = _conversations_module.router
memory_router = _memory_module.router
agents_router = _agents_module.router
mcp_router = _mcp_module.router
approvals_router = _approvals_module.router
reporting_router = _reporting_module.router
budgets_router = _budgets_module.router
guardrails_router = _guardrails_module.router
admin_router = _admin_module.router
agent_config_router = _agent_config_module.router
prompt_config_router = _prompt_config_module.router
job_queue_router = _job_queue_module.router
evidence_checker_router = _evidence_checker_module.router
text_enhancer_router = _text_enhancer_module.router
form_fill_router = _form_fill_module.router
attachments_router = _attachments_module.router
reports_router = _reports_module.router
framework_builder_router = _framework_builder_module.router
signal_spec_router = _signal_spec_module.router
signal_codegen_router = _signal_codegen_module.router
dataset_agent_router = _dataset_agent_module.router
pdf_templates_router = _pdf_templates_module.router
risk_advisor_router = _risk_advisor_module.router
test_linker_router = _test_linker_module.router
task_builder_router = _task_builder_module.router
