-- Seed: Signal Codegen Agent + Pipeline Tools
-- This seeds the agent for a SYSTEM scope (org_id = NULL sentinel uses a known system org UUID)
-- Apply per-org via service layer; this seeds the tool definitions only

DO $$
DECLARE
    v_system_org_id   UUID := '00000000-0000-0000-0000-000000000001';
    v_system_tenant   TEXT := 'system';
    v_actor           UUID := '00000000-0000-0000-0000-000000000000';
    v_now             TIMESTAMPTZ := NOW();

    -- Agent (resolved after insert)
    v_agent_id        UUID;

    -- Tool IDs
    v_t_inspect       UUID := gen_random_uuid();
    v_t_gen_dataset   UUID := gen_random_uuid();
    v_t_write_code    UUID := gen_random_uuid();
    v_t_run_dataset   UUID := gen_random_uuid();
    v_t_score         UUID := gen_random_uuid();
    v_t_patch_code    UUID := gen_random_uuid();
    v_t_save_signal   UUID := gen_random_uuid();
    v_t_live_run      UUID := gen_random_uuid();

    v_graph_source    TEXT := $GRAPH$
"""
Signal Codegen Agent — autonomous graph source.
Nodes walk: inspect → gen_dataset → write_code → run → score
  → [loop: patch → run → score until 100%]
  → save_signal → trigger_live_run → score_live
  → [outer loop if live fails]
"""
import json


async def inspect_schema_node(ctx):
    connector_id = ctx.state["connector_id"]
    asset_type = ctx.state["asset_type"]
    result = await ctx.tool("inspect_connector_schema", {
        "connector_id": connector_id,
        "asset_type": asset_type,
    })
    ctx.state["schema_columns"] = result.get("columns", [])
    ctx.state["sample_rows"] = result.get("sample_rows", [])
    ctx.emit("schema_inspected", {
        "columns": ctx.state["schema_columns"],
        "sample_count": len(ctx.state["sample_rows"]),
    })
    return "next"


async def generate_test_dataset_node(ctx):
    result = await ctx.tool("generate_test_dataset", {
        "schema_columns": ctx.state["schema_columns"],
        "sample_rows": ctx.state["sample_rows"],
        "signal_intent": ctx.state["signal_intent"],
        "asset_type": ctx.state["asset_type"],
        "live_failed_cases": ctx.state.get("live_failed_cases", []),
    })
    ctx.state["test_dataset"] = result.get("dataset", [])
    ctx.emit("dataset_generated", {"rows": len(ctx.state["test_dataset"])})
    return "next"


async def write_signal_code_node(ctx):
    result = await ctx.tool("write_signal_code", {
        "signal_intent": ctx.state["signal_intent"],
        "schema_columns": ctx.state["schema_columns"],
        "sample_rows": ctx.state["sample_rows"],
    })
    ctx.state["python_source"] = result.get("python_source", "")
    ctx.state["signal_code"] = result.get("signal_code", "")
    ctx.emit("code_written", {"signal_code": ctx.state["signal_code"]})
    ctx.state["inner_attempts"] = 0
    return "next"


async def run_on_dataset_node(ctx):
    result = await ctx.tool("run_signal_on_dataset", {
        "python_source": ctx.state["python_source"],
        "dataset": ctx.state["test_dataset"],
    })
    ctx.state["run_results"] = result.get("results", [])
    ctx.emit("dataset_run_complete", {"result_count": len(ctx.state["run_results"])})
    return "next"


async def score_accuracy_node(ctx):
    result = await ctx.tool("score_accuracy", {
        "results": ctx.state["run_results"],
        "dataset": ctx.state["test_dataset"],
    })
    accuracy = result.get("accuracy", 0.0)
    ctx.state["accuracy"] = accuracy
    ctx.state["test_accuracy"] = accuracy
    ctx.state["failed_cases"] = result.get("failed_cases", [])
    ctx.emit("accuracy_scored", {
        "accuracy": accuracy,
        "passed": result.get("passed", 0),
        "failed": result.get("failed", 0),
        "inner_attempts": ctx.state.get("inner_attempts", 0),
    })
    if accuracy >= 1.0:
        return "pass"
    if ctx.state.get("inner_attempts", 0) >= 20:
        return "give_up"
    return "patch"


async def patch_signal_code_node(ctx):
    ctx.state["inner_attempts"] = ctx.state.get("inner_attempts", 0) + 1
    result = await ctx.tool("patch_signal_code", {
        "python_source": ctx.state["python_source"],
        "failed_cases": ctx.state["failed_cases"],
        "signal_intent": ctx.state["signal_intent"],
    })
    ctx.state["python_source"] = result.get("python_source", ctx.state["python_source"])
    ctx.emit("code_patched", {"inner_attempts": ctx.state["inner_attempts"]})
    return "next"


async def give_up_node(ctx):
    ctx.emit("pipeline_failed", {
        "reason": "Could not reach 100% accuracy on test dataset after 20 patch iterations",
        "final_accuracy": ctx.state.get("accuracy", 0.0),
    })
    return None


async def save_signal_node(ctx):
    result = await ctx.tool("save_signal", {
        "signal_code": ctx.state.get("signal_code", "generated_signal"),
        "signal_intent": ctx.state["signal_intent"],
        "python_source": ctx.state["python_source"],
        "org_id": ctx.state["org_id"],
        "workspace_id": ctx.state.get("workspace_id", ""),
        "asset_type": ctx.state["asset_type"],
    })
    ctx.state["signal_id"] = result.get("signal_id", "")
    ctx.emit("signal_saved", {
        "signal_id": ctx.state["signal_id"],
        "signal_code": ctx.state.get("signal_code"),
    })
    return "next"


async def trigger_live_run_node(ctx):
    result = await ctx.tool("trigger_live_run", {
        "connector_id": ctx.state["connector_id"],
        "signal_id": ctx.state["signal_id"],
        "org_id": ctx.state["org_id"],
    })
    live_accuracy = result.get("accuracy", 0.0)
    ctx.state["live_accuracy"] = live_accuracy
    ctx.state["live_failed_cases"] = result.get("failed_cases", [])
    ctx.emit("live_run_complete", {
        "accuracy": live_accuracy,
        "total": result.get("total", 0),
        "passed": result.get("passed", 0),
        "failed": result.get("failed", 0),
    })
    if live_accuracy >= 1.0:
        return "pass"
    if ctx.state.get("outer_attempts", 0) >= 3:
        return "give_up"
    ctx.state["outer_attempts"] = ctx.state.get("outer_attempts", 0) + 1
    return "retry"


async def live_success_node(ctx):
    ctx.emit("pipeline_complete", {
        "signal_id": ctx.state.get("signal_id"),
        "signal_code": ctx.state.get("signal_code"),
        "test_accuracy": ctx.state.get("test_accuracy", 1.0),
        "live_accuracy": ctx.state.get("live_accuracy", 1.0),
    })
    return None


async def live_give_up_node(ctx):
    ctx.emit("pipeline_failed", {
        "reason": "Could not reach 100% on live data after 3 full pipeline runs",
        "live_accuracy": ctx.state.get("live_accuracy", 0.0),
    })
    return None


def build_graph(ctx):
    from backend.25_agent_sandbox.05_execution.compiler import Graph
    g = Graph()
    g.add_node("inspect_schema", inspect_schema_node, transitions={"next": "generate_test_dataset"})
    g.add_node("generate_test_dataset", generate_test_dataset_node, transitions={"next": "write_signal_code"})
    g.add_node("write_signal_code", write_signal_code_node, transitions={"next": "run_on_dataset"})
    g.add_node("run_on_dataset", run_on_dataset_node, transitions={"next": "score_accuracy"})
    g.add_node("score_accuracy", score_accuracy_node, transitions={
        "pass": "save_signal",
        "patch": "patch_signal_code",
        "give_up": "give_up",
    })
    g.add_node("patch_signal_code", patch_signal_code_node, transitions={"next": "run_on_dataset"})
    g.add_node("give_up", give_up_node)
    g.add_node("save_signal", save_signal_node, transitions={"next": "trigger_live_run"})
    g.add_node("trigger_live_run", trigger_live_run_node, transitions={
        "pass": "live_success",
        "retry": "generate_test_dataset",
        "give_up": "live_give_up",
    })
    g.add_node("live_success", live_success_node)
    g.add_node("live_give_up", live_give_up_node)
    g.set_entry_point("inspect_schema")
    return g
$GRAPH$;

    v_inspect_src TEXT := $TOOL$
def execute(input: dict) -> dict:
    """inspect_connector_schema — calls the internal API endpoint."""
    # This tool is api_endpoint type, so this python_source is unused.
    # The endpoint_url property is used instead.
    return {"error": "This tool uses endpoint_url, not python_source"}
$TOOL$;

    v_gen_dataset_src TEXT := $TOOL$
import json

def execute(input: dict) -> dict:
    """
    generate_test_dataset — LLM call to generate 10 synthetic test rows (5 pass, 5 fail).
    Input: schema_columns, sample_rows, signal_intent, asset_type, live_failed_cases (optional)
    Output: dataset (list of dicts, each with _expected: 'pass'|'fail')
    """
    import os, re

    schema_columns = input.get("schema_columns", [])
    sample_rows = input.get("sample_rows", [])
    signal_intent = input.get("signal_intent", "")
    asset_type = input.get("asset_type", "")
    live_failed_cases = input.get("live_failed_cases", [])

    # Build prompt
    sample_json = json.dumps(sample_rows[:2], indent=2, default=str) if sample_rows else "[]"
    live_context = ""
    if live_failed_cases:
        live_context = f"\n\nAdditionally, these real-data rows FAILED on live data — ensure the test dataset covers these edge cases:\n{json.dumps(live_failed_cases[:5], indent=2, default=str)}"

    prompt = f"""Generate exactly 10 synthetic test dataset rows for a compliance signal.

Signal intent: {signal_intent}
Asset type: {asset_type}
Schema columns: {json.dumps(schema_columns)}
Sample real data:
{sample_json}{live_context}

Rules:
- Generate exactly 10 rows: 5 that should PASS the signal check, 5 that should FAIL
- Each row must have an "_expected" field: "pass" or "fail"
- Use realistic field values matching the schema
- For PASS rows: set the relevant compliance field to a passing state
- For FAIL rows: set the relevant compliance field to a failing state
- Include ALL schema columns in each row (use null for unknown optional fields)

Respond with ONLY a valid JSON array of 10 objects. No explanation, no markdown.
"""

    # Make LLM call using httpx (synchronous-style via requests)
    import urllib.request
    api_key = os.environ.get("SANDBOX_AI_API_KEY", "")
    provider_url = os.environ.get("SANDBOX_AI_PROVIDER_URL", "https://api.openai.com/v1")
    model = os.environ.get("SANDBOX_AI_MODEL", "gpt-4o")

    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
    }).encode()

    req = urllib.request.Request(
        f"{provider_url}/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        response_data = json.loads(resp.read())

    content = response_data["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    # Handle both array and {"dataset": [...]} responses
    if isinstance(parsed, list):
        dataset = parsed
    elif isinstance(parsed, dict):
        dataset = parsed.get("dataset", parsed.get("rows", list(parsed.values())[0] if parsed else []))
    else:
        dataset = []

    return {"result": "pass", "summary": f"Generated {len(dataset)} test rows", "details": [], "dataset": dataset}
$TOOL$;

    v_write_code_src TEXT := $TOOL$
import json, os

def execute(input: dict) -> dict:
    """
    write_signal_code — LLM generates evaluate(dataset: dict) -> dict.
    Input: signal_intent, schema_columns, sample_rows
    Output: python_source, signal_code
    """
    signal_intent = input.get("signal_intent", "")
    schema_columns = input.get("schema_columns", [])
    sample_rows = input.get("sample_rows", [])

    # Use actual flattened column names from sample_rows if available
    if sample_rows:
        actual_keys = list(sample_rows[0].keys())
    else:
        actual_keys = schema_columns

    sample_json = json.dumps(sample_rows[:1], indent=2, default=str) if sample_rows else "[]"

    prompt = f"""Write a Python compliance signal function.

Signal intent: {signal_intent}

The function receives a single asset row as a dict. The actual field names in the dict are:
{json.dumps(actual_keys, indent=2)}

Sample row:
{sample_json}

Requirements:
1. Function signature: def evaluate(dataset: dict) -> dict
2. Return format:
   {{
     "result": "pass" | "fail" | "warning",
     "summary": "Human-readable one-line summary",
     "details": [{{"check": "name", "status": "pass|fail", "message": "..."}}],
     "metadata": {{}}
   }}
3. Use ONLY these modules: json, re, datetime, math, statistics, collections, ipaddress, hashlib
4. Handle None/null values gracefully
5. Use the EXACT field names from the sample row above

Also provide a snake_case code name for this signal (e.g. "github_branch_protection").

Respond with ONLY valid JSON in this exact format:
{{
  "signal_code": "snake_case_name",
  "python_source": "def evaluate(dataset: dict) -> dict:\\n    ..."
}}
"""

    api_key = os.environ.get("SANDBOX_AI_API_KEY", "")
    provider_url = os.environ.get("SANDBOX_AI_PROVIDER_URL", "https://api.openai.com/v1")
    model = os.environ.get("SANDBOX_AI_MODEL", "gpt-4o")

    import urllib.request
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }).encode()

    req = urllib.request.Request(
        f"{provider_url}/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        response_data = json.loads(resp.read())

    content = response_data["choices"][0]["message"]["content"]
    parsed = json.loads(content)

    return {
        "result": "pass",
        "summary": f"Generated signal code: {parsed.get('signal_code', 'unknown')}",
        "details": [],
        "python_source": parsed.get("python_source", ""),
        "signal_code": parsed.get("signal_code", "generated_signal"),
    }
$TOOL$;

    v_run_dataset_src TEXT := $TOOL$
def execute(input: dict) -> dict:
    """
    run_signal_on_dataset — calls the internal API endpoint.
    This is an api_endpoint type tool; this python_source is unused.
    """
    return {"error": "This tool uses endpoint_url"}
$TOOL$;

    v_score_src TEXT := $TOOL$
def execute(input: dict) -> dict:
    """
    score_accuracy — compares results against expected outcomes in dataset.
    Input: results (list), dataset (list with _expected field)
    Output: accuracy, passed, failed, failed_cases
    """
    results = input.get("results", [])
    dataset = input.get("dataset", [])

    passed = 0
    failed = 0
    failed_cases = []

    for i, (res, row) in enumerate(zip(results, dataset)):
        expected = row.get("_expected", "pass")
        actual = res.get("result", "error")
        if actual == expected:
            passed += 1
        else:
            failed += 1
            failed_cases.append({
                "row_index": i,
                "expected": expected,
                "actual": actual,
                "summary": res.get("summary", ""),
                "input_row": row,
            })

    total = passed + failed
    accuracy = passed / total if total > 0 else 1.0

    return {
        "result": "pass",
        "summary": f"Accuracy: {accuracy:.1%} ({passed}/{total} passed)",
        "details": [],
        "accuracy": accuracy,
        "passed": passed,
        "failed": failed,
        "failed_cases": failed_cases,
    }
$TOOL$;

    v_patch_src TEXT := $TOOL$
import json, os

def execute(input: dict) -> dict:
    """
    patch_signal_code — LLM fixes failed cases in the signal.
    Input: python_source, failed_cases, signal_intent
    Output: python_source (improved)
    """
    python_source = input.get("python_source", "")
    failed_cases = input.get("failed_cases", [])
    signal_intent = input.get("signal_intent", "")

    failed_summary = json.dumps(failed_cases[:5], indent=2, default=str)

    prompt = f"""Fix this Python compliance signal function.

Signal intent: {signal_intent}

Current code:
```python
{python_source}
```

These test cases FAILED (expected vs actual):
{failed_summary}

Fix the evaluate() function so all these cases pass.
- Keep the same function signature: def evaluate(dataset: dict) -> dict
- Use ONLY: json, re, datetime, math, statistics, collections, ipaddress, hashlib
- Handle None/null values gracefully

Respond with ONLY valid JSON:
{{"python_source": "def evaluate(dataset: dict) -> dict:\\n    ..."}}
"""

    api_key = os.environ.get("SANDBOX_AI_API_KEY", "")
    provider_url = os.environ.get("SANDBOX_AI_PROVIDER_URL", "https://api.openai.com/v1")
    model = os.environ.get("SANDBOX_AI_MODEL", "gpt-4o")

    import urllib.request
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }).encode()

    req = urllib.request.Request(
        f"{provider_url}/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        response_data = json.loads(resp.read())

    content = response_data["choices"][0]["message"]["content"]
    parsed = json.loads(content)

    return {
        "result": "pass",
        "summary": "Signal code patched",
        "details": [],
        "python_source": parsed.get("python_source", python_source),
    }
$TOOL$;

    v_save_signal_src TEXT := $TOOL$
def execute(input: dict) -> dict:
    """
    save_signal — saves signal to 15_sandbox schema.
    This is an api_endpoint type tool; this python_source is unused.
    """
    return {"error": "This tool uses endpoint_url"}
$TOOL$;

    v_live_run_src TEXT := $TOOL$
def execute(input: dict) -> dict:
    """
    trigger_live_run — runs signal against live Steampipe assets.
    This is an api_endpoint type tool; this python_source is unused.
    """
    return {"error": "This tool uses endpoint_url"}
$TOOL$;

BEGIN
    -- Insert agent or get existing ID
    v_agent_id := gen_random_uuid();
    INSERT INTO "25_agent_sandbox"."20_fct_agents"
        (id, tenant_key, org_id, workspace_id, agent_code,
         version_number, agent_status_code, graph_type,
         llm_model_id, temperature,
         max_iterations, max_tokens_budget, max_tool_calls,
         max_duration_ms, max_cost_usd, requires_approval,
         python_hash, is_active, is_deleted,
         created_at, updated_at, created_by, updated_by,
         deleted_at, deleted_by)
    VALUES
        (v_agent_id, v_system_tenant, v_system_org_id, NULL, 'signal_codegen_agent',
         1, 'published', 'cyclic',
         'gpt-4o', 0.2,
         50, 100000, 200,
         600000, 5.0, FALSE,
         NULL, TRUE, FALSE,
         v_now, v_now, v_actor, v_actor,
         NULL, NULL)
    ON CONFLICT DO NOTHING;

    -- Resolve actual agent ID (may already exist from a prior run)
    SELECT id INTO v_agent_id
    FROM "25_agent_sandbox"."20_fct_agents"
    WHERE org_id = v_system_org_id AND agent_code = 'signal_codegen_agent'
    ORDER BY version_number DESC LIMIT 1;

    -- Agent properties
    INSERT INTO "25_agent_sandbox"."40_dtl_agent_properties"
        (id, agent_id, property_key, property_value, created_at, updated_at, created_by, updated_by)
    VALUES
        (gen_random_uuid(), v_agent_id, 'name', 'Signal Codegen Agent', v_now, v_now, v_actor, v_actor),
        (gen_random_uuid(), v_agent_id, 'description', 'Autonomous agent that generates, tests, and validates compliance signal code using real connector data.', v_now, v_now, v_actor, v_actor),
        (gen_random_uuid(), v_agent_id, 'graph_source', v_graph_source, v_now, v_now, v_actor, v_actor)
    ON CONFLICT (agent_id, property_key) DO UPDATE
        SET property_value = EXCLUDED.property_value, updated_at = EXCLUDED.updated_at;

    -- ── Tool: inspect_connector_schema (api_endpoint) ──────────────────────
    INSERT INTO "25_agent_sandbox"."21_fct_agent_tools"
        (id, tenant_key, org_id, tool_code, tool_type_code,
         input_schema, output_schema,
         endpoint_url, mcp_server_url, python_source,
         signal_id, requires_approval, is_destructive, timeout_ms,
         is_active, is_deleted, created_at, updated_at, created_by, updated_by,
         deleted_at, deleted_by)
    VALUES
        (v_t_inspect, v_system_tenant, v_system_org_id, 'inspect_connector_schema', 'api_endpoint',
         '{"connector_id":"string","asset_type":"string"}'::jsonb,
         '{"columns":"list","sample_rows":"list"}'::jsonb,
         'http://127.0.0.1:8000/api/v1/asb/tools/inspect-schema', NULL, v_inspect_src,
         NULL, FALSE, FALSE, 60000,
         TRUE, FALSE, v_now, v_now, v_actor, v_actor, NULL, NULL)
    ON CONFLICT DO NOTHING;

    INSERT INTO "25_agent_sandbox"."41_dtl_tool_properties"
        (id, tool_id, property_key, property_value, created_at, updated_at, created_by, updated_by)
    VALUES
        (gen_random_uuid(), v_t_inspect, 'name', 'Inspect Connector Schema', v_now, v_now, v_actor, v_actor),
        (gen_random_uuid(), v_t_inspect, 'description', 'Loads connector credentials and runs Steampipe LIMIT 3 query to get schema and sample rows', v_now, v_now, v_actor, v_actor),
        (gen_random_uuid(), v_t_inspect, 'endpoint_url', 'http://127.0.0.1:8000/api/v1/asb/tools/inspect-schema', v_now, v_now, v_actor, v_actor)
    ON CONFLICT (tool_id, property_key) DO UPDATE SET property_value = EXCLUDED.property_value;

    -- ── Tool: generate_test_dataset (python_function) ──────────────────────
    INSERT INTO "25_agent_sandbox"."21_fct_agent_tools"
        (id, tenant_key, org_id, tool_code, tool_type_code,
         input_schema, output_schema,
         endpoint_url, mcp_server_url, python_source,
         signal_id, requires_approval, is_destructive, timeout_ms,
         is_active, is_deleted, created_at, updated_at, created_by, updated_by,
         deleted_at, deleted_by)
    VALUES
        (v_t_gen_dataset, v_system_tenant, v_system_org_id, 'generate_test_dataset', 'python_function',
         '{"schema_columns":"list","sample_rows":"list","signal_intent":"string","asset_type":"string"}'::jsonb,
         '{"dataset":"list"}'::jsonb,
         NULL, NULL, v_gen_dataset_src,
         NULL, FALSE, FALSE, 90000,
         TRUE, FALSE, v_now, v_now, v_actor, v_actor, NULL, NULL)
    ON CONFLICT DO NOTHING;

    INSERT INTO "25_agent_sandbox"."41_dtl_tool_properties"
        (id, tool_id, property_key, property_value, created_at, updated_at, created_by, updated_by)
    VALUES
        (gen_random_uuid(), v_t_gen_dataset, 'name', 'Generate Test Dataset', v_now, v_now, v_actor, v_actor),
        (gen_random_uuid(), v_t_gen_dataset, 'description', 'LLM call to generate 10 synthetic test rows (5 pass, 5 fail)', v_now, v_now, v_actor, v_actor),
        (gen_random_uuid(), v_t_gen_dataset, 'python_source', v_gen_dataset_src, v_now, v_now, v_actor, v_actor)
    ON CONFLICT (tool_id, property_key) DO UPDATE SET property_value = EXCLUDED.property_value;

    -- ── Tool: write_signal_code (python_function) ──────────────────────────
    INSERT INTO "25_agent_sandbox"."21_fct_agent_tools"
        (id, tenant_key, org_id, tool_code, tool_type_code,
         input_schema, output_schema,
         endpoint_url, mcp_server_url, python_source,
         signal_id, requires_approval, is_destructive, timeout_ms,
         is_active, is_deleted, created_at, updated_at, created_by, updated_by,
         deleted_at, deleted_by)
    VALUES
        (v_t_write_code, v_system_tenant, v_system_org_id, 'write_signal_code', 'python_function',
         '{"signal_intent":"string","schema_columns":"list","sample_rows":"list"}'::jsonb,
         '{"python_source":"string","signal_code":"string"}'::jsonb,
         NULL, NULL, v_write_code_src,
         NULL, FALSE, FALSE, 90000,
         TRUE, FALSE, v_now, v_now, v_actor, v_actor, NULL, NULL)
    ON CONFLICT DO NOTHING;

    INSERT INTO "25_agent_sandbox"."41_dtl_tool_properties"
        (id, tool_id, property_key, property_value, created_at, updated_at, created_by, updated_by)
    VALUES
        (gen_random_uuid(), v_t_write_code, 'name', 'Write Signal Code', v_now, v_now, v_actor, v_actor),
        (gen_random_uuid(), v_t_write_code, 'description', 'LLM generates evaluate() Python function for the signal', v_now, v_now, v_actor, v_actor),
        (gen_random_uuid(), v_t_write_code, 'python_source', v_write_code_src, v_now, v_now, v_actor, v_actor)
    ON CONFLICT (tool_id, property_key) DO UPDATE SET property_value = EXCLUDED.property_value;

    -- ── Tool: run_signal_on_dataset (api_endpoint) ─────────────────────────
    INSERT INTO "25_agent_sandbox"."21_fct_agent_tools"
        (id, tenant_key, org_id, tool_code, tool_type_code,
         input_schema, output_schema,
         endpoint_url, mcp_server_url, python_source,
         signal_id, requires_approval, is_destructive, timeout_ms,
         is_active, is_deleted, created_at, updated_at, created_by, updated_by,
         deleted_at, deleted_by)
    VALUES
        (v_t_run_dataset, v_system_tenant, v_system_org_id, 'run_signal_on_dataset', 'api_endpoint',
         '{"python_source":"string","dataset":"list"}'::jsonb,
         '{"results":"list"}'::jsonb,
         'http://127.0.0.1:8000/api/v1/asb/tools/run-signal-on-dataset', NULL, v_run_dataset_src,
         NULL, FALSE, FALSE, 120000,
         TRUE, FALSE, v_now, v_now, v_actor, v_actor, NULL, NULL)
    ON CONFLICT DO NOTHING;

    INSERT INTO "25_agent_sandbox"."41_dtl_tool_properties"
        (id, tool_id, property_key, property_value, created_at, updated_at, created_by, updated_by)
    VALUES
        (gen_random_uuid(), v_t_run_dataset, 'name', 'Run Signal On Dataset', v_now, v_now, v_actor, v_actor),
        (gen_random_uuid(), v_t_run_dataset, 'description', 'Executes signal python_source against each row in the test dataset via sandbox engine', v_now, v_now, v_actor, v_actor),
        (gen_random_uuid(), v_t_run_dataset, 'endpoint_url', 'http://127.0.0.1:8000/api/v1/asb/tools/run-signal-on-dataset', v_now, v_now, v_actor, v_actor)
    ON CONFLICT (tool_id, property_key) DO UPDATE SET property_value = EXCLUDED.property_value;

    -- ── Tool: score_accuracy (python_function) ────────────────────────────
    INSERT INTO "25_agent_sandbox"."21_fct_agent_tools"
        (id, tenant_key, org_id, tool_code, tool_type_code,
         input_schema, output_schema,
         endpoint_url, mcp_server_url, python_source,
         signal_id, requires_approval, is_destructive, timeout_ms,
         is_active, is_deleted, created_at, updated_at, created_by, updated_by,
         deleted_at, deleted_by)
    VALUES
        (v_t_score, v_system_tenant, v_system_org_id, 'score_accuracy', 'python_function',
         '{"results":"list","dataset":"list"}'::jsonb,
         '{"accuracy":"float","passed":"int","failed":"int","failed_cases":"list"}'::jsonb,
         NULL, NULL, v_score_src,
         NULL, FALSE, FALSE, 30000,
         TRUE, FALSE, v_now, v_now, v_actor, v_actor, NULL, NULL)
    ON CONFLICT DO NOTHING;

    INSERT INTO "25_agent_sandbox"."41_dtl_tool_properties"
        (id, tool_id, property_key, property_value, created_at, updated_at, created_by, updated_by)
    VALUES
        (gen_random_uuid(), v_t_score, 'name', 'Score Accuracy', v_now, v_now, v_actor, v_actor),
        (gen_random_uuid(), v_t_score, 'description', 'Compares signal results against _expected field in test dataset', v_now, v_now, v_actor, v_actor),
        (gen_random_uuid(), v_t_score, 'python_source', v_score_src, v_now, v_now, v_actor, v_actor)
    ON CONFLICT (tool_id, property_key) DO UPDATE SET property_value = EXCLUDED.property_value;

    -- ── Tool: patch_signal_code (python_function) ────────────────────────
    INSERT INTO "25_agent_sandbox"."21_fct_agent_tools"
        (id, tenant_key, org_id, tool_code, tool_type_code,
         input_schema, output_schema,
         endpoint_url, mcp_server_url, python_source,
         signal_id, requires_approval, is_destructive, timeout_ms,
         is_active, is_deleted, created_at, updated_at, created_by, updated_by,
         deleted_at, deleted_by)
    VALUES
        (v_t_patch_code, v_system_tenant, v_system_org_id, 'patch_signal_code', 'python_function',
         '{"python_source":"string","failed_cases":"list","signal_intent":"string"}'::jsonb,
         '{"python_source":"string"}'::jsonb,
         NULL, NULL, v_patch_src,
         NULL, FALSE, FALSE, 90000,
         TRUE, FALSE, v_now, v_now, v_actor, v_actor, NULL, NULL)
    ON CONFLICT DO NOTHING;

    INSERT INTO "25_agent_sandbox"."41_dtl_tool_properties"
        (id, tool_id, property_key, property_value, created_at, updated_at, created_by, updated_by)
    VALUES
        (gen_random_uuid(), v_t_patch_code, 'name', 'Patch Signal Code', v_now, v_now, v_actor, v_actor),
        (gen_random_uuid(), v_t_patch_code, 'description', 'LLM fixes failed test cases in the signal code', v_now, v_now, v_actor, v_actor),
        (gen_random_uuid(), v_t_patch_code, 'python_source', v_patch_src, v_now, v_now, v_actor, v_actor)
    ON CONFLICT (tool_id, property_key) DO UPDATE SET property_value = EXCLUDED.property_value;

    -- ── Tool: save_signal (api_endpoint) ─────────────────────────────────
    INSERT INTO "25_agent_sandbox"."21_fct_agent_tools"
        (id, tenant_key, org_id, tool_code, tool_type_code,
         input_schema, output_schema,
         endpoint_url, mcp_server_url, python_source,
         signal_id, requires_approval, is_destructive, timeout_ms,
         is_active, is_deleted, created_at, updated_at, created_by, updated_by,
         deleted_at, deleted_by)
    VALUES
        (v_t_save_signal, v_system_tenant, v_system_org_id, 'save_signal', 'api_endpoint',
         '{"signal_code":"string","signal_intent":"string","python_source":"string","org_id":"string","workspace_id":"string"}'::jsonb,
         '{"signal_id":"string","signal_code":"string"}'::jsonb,
         'http://127.0.0.1:8000/api/v1/asb/tools/save-signal', NULL, v_save_signal_src,
         NULL, FALSE, FALSE, 30000,
         TRUE, FALSE, v_now, v_now, v_actor, v_actor, NULL, NULL)
    ON CONFLICT DO NOTHING;

    INSERT INTO "25_agent_sandbox"."41_dtl_tool_properties"
        (id, tool_id, property_key, property_value, created_at, updated_at, created_by, updated_by)
    VALUES
        (gen_random_uuid(), v_t_save_signal, 'name', 'Save Signal', v_now, v_now, v_actor, v_actor),
        (gen_random_uuid(), v_t_save_signal, 'description', 'Persists the generated signal to 15_sandbox schema', v_now, v_now, v_actor, v_actor),
        (gen_random_uuid(), v_t_save_signal, 'endpoint_url', 'http://127.0.0.1:8000/api/v1/asb/tools/save-signal', v_now, v_now, v_actor, v_actor)
    ON CONFLICT (tool_id, property_key) DO UPDATE SET property_value = EXCLUDED.property_value;

    -- ── Tool: trigger_live_run (api_endpoint) ─────────────────────────────
    INSERT INTO "25_agent_sandbox"."21_fct_agent_tools"
        (id, tenant_key, org_id, tool_code, tool_type_code,
         input_schema, output_schema,
         endpoint_url, mcp_server_url, python_source,
         signal_id, requires_approval, is_destructive, timeout_ms,
         is_active, is_deleted, created_at, updated_at, created_by, updated_by,
         deleted_at, deleted_by)
    VALUES
        (v_t_live_run, v_system_tenant, v_system_org_id, 'trigger_live_run', 'api_endpoint',
         '{"connector_id":"string","signal_id":"string","org_id":"string"}'::jsonb,
         '{"accuracy":"float","total":"int","passed":"int","failed":"int","failed_cases":"list"}'::jsonb,
         'http://127.0.0.1:8000/api/v1/asb/tools/trigger-live-run', NULL, v_live_run_src,
         NULL, FALSE, FALSE, 300000,
         TRUE, FALSE, v_now, v_now, v_actor, v_actor, NULL, NULL)
    ON CONFLICT DO NOTHING;

    INSERT INTO "25_agent_sandbox"."41_dtl_tool_properties"
        (id, tool_id, property_key, property_value, created_at, updated_at, created_by, updated_by)
    VALUES
        (gen_random_uuid(), v_t_live_run, 'name', 'Trigger Live Run', v_now, v_now, v_actor, v_actor),
        (gen_random_uuid(), v_t_live_run, 'description', 'Collects live assets via Steampipe and runs signal against each', v_now, v_now, v_actor, v_actor),
        (gen_random_uuid(), v_t_live_run, 'endpoint_url', 'http://127.0.0.1:8000/api/v1/asb/tools/trigger-live-run', v_now, v_now, v_actor, v_actor)
    ON CONFLICT (tool_id, property_key) DO UPDATE SET property_value = EXCLUDED.property_value;

    -- ── Tool bindings ─────────────────────────────────────────────────────
    INSERT INTO "25_agent_sandbox"."50_lnk_agent_tool_bindings"
        (id, agent_id, tool_id, sort_order, is_active, created_at, created_by)
    VALUES
        (gen_random_uuid(), v_agent_id, v_t_inspect,     1, TRUE, v_now, v_actor),
        (gen_random_uuid(), v_agent_id, v_t_gen_dataset,  2, TRUE, v_now, v_actor),
        (gen_random_uuid(), v_agent_id, v_t_write_code,   3, TRUE, v_now, v_actor),
        (gen_random_uuid(), v_agent_id, v_t_run_dataset,  4, TRUE, v_now, v_actor),
        (gen_random_uuid(), v_agent_id, v_t_score,        5, TRUE, v_now, v_actor),
        (gen_random_uuid(), v_agent_id, v_t_patch_code,   6, TRUE, v_now, v_actor),
        (gen_random_uuid(), v_agent_id, v_t_save_signal,  7, TRUE, v_now, v_actor),
        (gen_random_uuid(), v_agent_id, v_t_live_run,     8, TRUE, v_now, v_actor)
    ON CONFLICT (agent_id, tool_id) DO NOTHING;

    RAISE NOTICE 'Signal Codegen Agent seeded successfully (agent_id=%)', v_agent_id;
END;
$$;
