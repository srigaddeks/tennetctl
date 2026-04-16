"""
Agent Catalog — declarative registry of all AI agents in the platform.

Auto-discovered at import time. Each entry describes:
- What the agent does
- How to invoke it (streaming vs batch)
- What inputs it accepts
- What outputs it produces
- What tools/capabilities it uses
- Default configuration
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AgentInput:
    name: str
    type: str  # text, json, file, select
    required: bool = True
    description: str = ""
    default: str | None = None
    options: list[str] | None = None  # for select type


@dataclass(frozen=True)
class AgentCatalogEntry:
    code: str
    name: str
    description: str
    category: str  # copilot, builder, generator, analyzer, evaluator, composer
    execution_mode: str  # streaming, batch, request_response
    module_path: str  # e.g. backend.20_ai.04_agents.grc_agent
    inputs: list[AgentInput] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    default_model: str = ""
    default_temperature: float = 0.3
    max_iterations: int = 10
    supports_conversation: bool = False
    icon: str = "bot"  # lucide icon name


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT CATALOG — all 14 platform agents
# ═══════════════════════════════════════════════════════════════════════════════

AGENT_CATALOG: list[AgentCatalogEntry] = [
    # ── Streaming Agents ──────────────────────────────────────

    AgentCatalogEntry(
        code="grc_copilot",
        name="GRC Copilot",
        description="Interactive GRC assistant with 20+ tools for frameworks, controls, risks, tasks, and compliance queries. Maintains conversation context across turns.",
        category="copilot",
        execution_mode="streaming",
        module_path="backend.20_ai.04_agents.grc_agent",
        inputs=[
            AgentInput(name="message", type="text", description="Your question or instruction"),
            AgentInput(name="page_context", type="json", required=False, description="Current page context (auto-populated)"),
        ],
        outputs=["tool_calls", "assistant_message", "conversation_history"],
        tools_used=[
            "grc_list_frameworks", "grc_get_framework", "grc_list_controls",
            "grc_get_control", "grc_list_risks", "grc_create_task",
            "grc_list_tasks", "grc_framework_health", "grc_compliance_posture",
        ],
        tags=["grc", "copilot", "tools", "conversation"],
        max_iterations=6,
        supports_conversation=True,
        icon="brain",
    ),

    AgentCatalogEntry(
        code="signal_spec",
        name="Signal Specification Agent",
        description="Interactively designs signal specifications from natural language. Analyzes connector schemas, checks field feasibility, and produces structured specs for code generation.",
        category="builder",
        execution_mode="streaming",
        module_path="backend.20_ai.22_signal_spec.agent",
        inputs=[
            AgentInput(name="prompt", type="text", description="Describe the signal you want to build"),
            AgentInput(name="connector_type_code", type="select", description="Connector type", options=["github", "aws_iam", "azure_ad", "okta"]),
            AgentInput(name="sample_dataset_id", type="text", required=False, description="Dataset ID for schema context"),
        ],
        outputs=["spec_analyzing", "spec_field_identified", "spec_section_ready", "feasibility_result", "spec_complete"],
        tools_used=[],
        tags=["sandbox", "signals", "specification"],
        supports_conversation=True,
        icon="zap",
    ),

    AgentCatalogEntry(
        code="framework_builder",
        name="Framework Builder Agent",
        description="Builds GRC compliance frameworks from uploaded documents. Phase 1: extracts requirement hierarchy. Phase 2: generates controls + risk mappings. Phase 3: writes to database.",
        category="builder",
        execution_mode="streaming",
        module_path="backend.20_ai.21_framework_builder.agent",
        inputs=[
            AgentInput(name="documents", type="text", description="Paste regulation/standard text or upload PDF"),
            AgentInput(name="user_message", type="text", description="Instructions for framework creation"),
        ],
        outputs=["phase1_result", "phase2_controls", "phase2_risks", "creation_complete"],
        tools_used=[],
        tags=["grc", "frameworks", "compliance", "documents"],
        max_iterations=3,
        icon="file-check",
    ),

    AgentCatalogEntry(
        code="form_fill",
        name="Form Fill Agent",
        description="Auto-fills GRC forms by reading existing data and proposing field values. Uses read-only GRC tools plus form field proposals.",
        category="copilot",
        execution_mode="streaming",
        module_path="backend.20_ai.18_form_fill.agent",
        inputs=[
            AgentInput(name="form_template", type="json", description="Form structure with field definitions"),
            AgentInput(name="user_input", type="json", required=False, description="User-provided field values"),
        ],
        outputs=["tool_calls", "form_proposal"],
        tools_used=["grc_list_controls", "grc_get_control", "grc_propose_form_fields"],
        tags=["grc", "forms", "auto-fill"],
        max_iterations=4,
        icon="clipboard-check",
    ),

    AgentCatalogEntry(
        code="text_enhancer",
        name="Text Enhancer",
        description="Improves GRC text fields (descriptions, names, remediation guidance) using domain-specific prompts. Fast single-call streaming.",
        category="analyzer",
        execution_mode="streaming",
        module_path="backend.20_ai.17_text_enhancer.service",
        inputs=[
            AgentInput(name="entity_type", type="select", description="Entity type", options=["control", "framework", "requirement", "risk", "task"]),
            AgentInput(name="field_name", type="select", description="Field to enhance", options=["description", "name", "remediation_guidance", "implementation_guidance"]),
            AgentInput(name="current_value", type="text", description="Current field text to improve"),
        ],
        outputs=["enhanced_text"],
        tools_used=[],
        tags=["grc", "text", "enhancement"],
        max_iterations=1,
        icon="sparkles",
    ),

    AgentCatalogEntry(
        code="dataset_agent",
        name="Dataset Agent",
        description="Analyzes dataset records, explains fields and compliance relevance, composes test data, and suggests dataset improvements.",
        category="analyzer",
        execution_mode="request_response",
        module_path="backend.20_ai.27_dataset_agent.service",
        inputs=[
            AgentInput(name="operation", type="select", description="Operation", options=["explain_record", "explain_dataset", "compose_test_data", "enhance_dataset"]),
            AgentInput(name="records", type="json", description="Dataset records (JSON array)"),
            AgentInput(name="asset_type_hint", type="text", required=False, description="Asset type hint"),
        ],
        outputs=["field_explanations", "compliance_relevance", "signal_ideas", "test_data"],
        tools_used=[],
        tags=["sandbox", "datasets", "analysis"],
        icon="database",
    ),

    # ── Background Job Agents ─────────────────────────────────

    AgentCatalogEntry(
        code="report_generator",
        name="Report Generator",
        description="Generates comprehensive GRC reports using a 5-stage pipeline: Plan → Collect (tool calls) → Analyze → Write → Format. 13 report types available.",
        category="generator",
        execution_mode="batch",
        module_path="backend.20_ai.20_reports.agent",
        inputs=[
            AgentInput(name="report_type", type="select", description="Report type",
                       options=["executive_summary", "compliance_posture", "framework_compliance",
                                "control_status", "risk_summary", "board_risk_report",
                                "remediation_plan", "task_health", "audit_trail", "evidence_report"]),
            AgentInput(name="parameters", type="json", required=False, description="Report parameters (framework_id, date range, etc.)"),
        ],
        outputs=["markdown_report", "report_metadata"],
        tools_used=["grc_list_frameworks", "grc_framework_health", "grc_list_controls", "grc_list_risks", "grc_list_tasks"],
        tags=["grc", "reports", "compliance"],
        max_iterations=15,
        icon="file-text",
    ),

    AgentCatalogEntry(
        code="signal_codegen",
        name="Signal Code Generator",
        description="Generates Python signal code from specifications. Iterative compile→test→fix loop up to 10 iterations. Auto-validates with RestrictedPython + test suite.",
        category="generator",
        execution_mode="batch",
        module_path="backend.20_ai.24_signal_codegen.job_handler",
        inputs=[
            AgentInput(name="spec", type="json", description="Signal specification (from SignalSpecAgent)"),
            AgentInput(name="rich_schema", type="json", description="Dataset schema with types and examples"),
            AgentInput(name="auto_compose_threats", type="select", required=False, description="Auto-compose threat types", options=["true", "false"], default="false"),
        ],
        outputs=["python_source", "args_schema", "ssf_mapping", "test_results"],
        tools_used=["compile_signal", "execute_signal"],
        tags=["sandbox", "signals", "codegen"],
        max_iterations=10,
        icon="code",
    ),

    AgentCatalogEntry(
        code="signal_generator",
        name="Signal Generator",
        description="Generates signals from scratch given a dataset and connector type. Legacy agent used by the sandbox auto-generate flow.",
        category="generator",
        execution_mode="batch",
        module_path="backend.10_sandbox.13_signal_agent.job_handler",
        inputs=[
            AgentInput(name="signal_id", type="text", description="Signal ID to generate code for"),
            AgentInput(name="dataset_id", type="text", description="Dataset ID for context"),
            AgentInput(name="connector_type", type="text", description="Connector type code"),
        ],
        outputs=["python_source", "args_schema", "ssf_mapping"],
        tools_used=["compile_signal", "execute_signal"],
        tags=["sandbox", "signals", "generation"],
        icon="zap",
    ),

    AgentCatalogEntry(
        code="test_dataset_gen",
        name="Test Dataset Generator",
        description="Generates 15-20 validated test cases from a signal spec. Shape-preserving validation ensures generated data matches real schema structure.",
        category="generator",
        execution_mode="batch",
        module_path="backend.20_ai.23_test_dataset_gen.agent",
        inputs=[
            AgentInput(name="spec", type="json", description="Signal specification"),
            AgentInput(name="rich_schema", type="json", description="Schema with types and examples"),
            AgentInput(name="num_cases", type="text", required=False, description="Number of test cases", default="18"),
        ],
        outputs=["test_cases", "validated_ratio", "fix_attempts"],
        tools_used=[],
        tags=["sandbox", "testing", "datasets"],
        icon="test-tubes",
    ),

    AgentCatalogEntry(
        code="threat_composer",
        name="Threat Composer",
        description="Composes threat types from a set of signals using AND/OR/NOT expression trees. Generates semantically meaningful threat definitions.",
        category="composer",
        execution_mode="batch",
        module_path="backend.20_ai.25_threat_composer.job_handler",
        inputs=[
            AgentInput(name="signal_ids", type="json", description="List of signal IDs to compose into threats"),
            AgentInput(name="max_threat_types", type="text", required=False, description="Max threats to generate", default="100"),
        ],
        outputs=["threat_types", "expression_trees"],
        tools_used=[],
        tags=["sandbox", "threats", "composition"],
        icon="shield-alert",
    ),

    AgentCatalogEntry(
        code="library_builder",
        name="Library Builder",
        description="Bundles threat types into policies and libraries. Creates alert policies with cooldowns and groups them by connector type. No LLM calls — purely structural.",
        category="composer",
        execution_mode="batch",
        module_path="backend.20_ai.26_library_builder.job_handler",
        inputs=[
            AgentInput(name="threat_type_ids", type="json", description="List of threat type IDs"),
            AgentInput(name="library_name_override", type="text", required=False, description="Custom library name"),
        ],
        outputs=["policies", "library"],
        tools_used=[],
        tags=["sandbox", "libraries", "policies"],
        icon="library",
    ),

    AgentCatalogEntry(
        code="evidence_checker",
        name="Evidence Checker",
        description="Multi-agentic RAG pipeline for evidence evaluation. 4-stage pipeline: Query Expansion (HyDE) → Semantic Retrieval (Qdrant) → Full Corpus Map → Re-Rank + Synthesis. Produces grounded verdicts with no hallucinated references.",
        category="evaluator",
        execution_mode="batch",
        module_path="backend.20_ai.16_evidence_checker.evidence_checker_agent",
        inputs=[
            AgentInput(name="task_id", type="text", description="Task ID with acceptance criteria"),
            AgentInput(name="evidence_collection_id", type="text", description="Evidence collection ID (chunked + embedded in Qdrant)"),
        ],
        outputs=["criterion_results", "verdicts", "grounded_references"],
        tools_used=["qdrant_search", "query_expansion", "map_agent", "rerank_agent", "synthesis_agent"],
        tags=["grc", "evidence", "rag", "evaluation"],
        max_iterations=4,
        icon="search-check",
    ),

    AgentCatalogEntry(
        code="signal_codegen_agent",
        name="Signal Codegen Agent",
        description="Autonomous AI agent that generates, tests, and validates compliance signal code using real connector data. Iterates until 100% accuracy on synthetic test data, then validates against live assets.",
        category="generator",
        execution_mode="streaming",
        module_path="backend.25_agent_sandbox.09_playground.dispatcher",
        inputs=[
            AgentInput(name="connector_id", type="text", description="Connector instance ID (GitHub connector)"),
            AgentInput(name="signal_intent", type="text", description="What the signal should check (e.g. 'All repos must have branch protection enabled')"),
            AgentInput(name="asset_type", type="select", description="Asset type to check", options=["github_repo", "github_org_member", "github_team", "github_workflow"]),
        ],
        outputs=["python_source", "signal_id", "test_accuracy", "live_accuracy"],
        tools_used=["inspect_connector_schema", "generate_test_dataset", "write_signal_code", "run_signal_on_dataset", "score_accuracy", "patch_signal_code", "save_signal", "trigger_live_run"],
        tags=["sandbox", "signals", "codegen", "autonomous"],
        max_iterations=50,
        icon="cpu",
    ),
]

# Index by code for fast lookup
_CATALOG_BY_CODE: dict[str, AgentCatalogEntry] = {a.code: a for a in AGENT_CATALOG}


def get_catalog() -> list[AgentCatalogEntry]:
    """Return all registered agents."""
    return AGENT_CATALOG


def get_agent_by_code(code: str) -> AgentCatalogEntry | None:
    """Look up an agent by its code."""
    return _CATALOG_BY_CODE.get(code)


def get_agents_by_category(category: str) -> list[AgentCatalogEntry]:
    """Return agents filtered by category."""
    return [a for a in AGENT_CATALOG if a.category == category]


def get_agents_by_tag(tag: str) -> list[AgentCatalogEntry]:
    """Return agents that have the given tag."""
    return [a for a in AGENT_CATALOG if tag in a.tags]
