# Sandbox AI Signal Agent API

**Base path:** `/api/v1/sb`
**Auth:** Bearer JWT required on all endpoints
**Multi-tenant:** `org_id` query parameter required on all endpoints
**Permission:** `sandbox.create`
**Dependencies:** `langgraph`, `langchain-core`
**Config:** First available of:
- `signal_generate` agent config in the database
- `SANDBOX_AI_PROVIDER_URL`, `SANDBOX_AI_API_KEY`, `SANDBOX_AI_MODEL`
- `AI_PROVIDER_URL`, `AI_API_KEY`, `AI_MODEL`

---

## Overview

The AI Signal Agent generates valid Python signal code from an English description using a LangGraph StateGraph. The agent autonomously analyzes intent, generates code, compiles it through the same RestrictedPython engine used for live execution, runs it against a sample dataset, and self-heals by iterating on compile errors and test failures. The agent produces working, validated signal code in up to 5 iterations.

If none of the supported AI config sources are available, generation endpoints return `422 validation_error`.

---

## Agent Workflow

```text
analyze_intent
    → generate_code
        → compile_validate ─── (fail) ──→ fix_code ─┐
              ↓ (pass)                                │
          run_tests ──────── (fail) ──→ fix_code ─────┘
              ↓ (pass)                 (max 5 total iterations)
          finalize
```

### Node Descriptions

| Node | Purpose |
| --- | --- |
| `analyze_intent` | Parses the English prompt to identify: what to check, connector type, expected dataset schema, candidate CAEP/RISC event type |
| `generate_code` | Produces a `def evaluate(dataset: dict) -> dict` function using the signal contract, allowed modules, dataset schema, and few-shot examples |
| `compile_validate` | Compiles with RestrictedPython (same engine as sandbox execution). On failure, extracts error and routes to `fix_code` |
| `run_tests` | Executes against sample or template dataset using the sandbox engine. On result mismatch, routes to `fix_code` |
| `fix_code` | Regenerates code with error context injected into the prompt. Routes back to `compile_validate`. Each iteration counts toward the max of 5 |
| `finalize` | Returns working code with CAEP/RISC mapping, name suggestion, and agent trace |

---

## Agent State

```python
class SignalGenState(TypedDict):
    prompt: str
    connector_type: str
    dataset_schema: dict
    sample_dataset: dict | None
    generated_code: str
    compile_error: str | None
    test_result: dict | None
    iteration: int
    caep_event_type: str | None
    risc_event_type: str | None
    final_code: str | None
    is_complete: bool
```

---

## Agent Tools

| Tool | Description |
| --- | --- |
| `compile_signal` | RestrictedPython compile check against generated code |
| `execute_signal` | Run signal in sandbox against a dataset, return result dict |
| `get_dataset_schema` | Infer JSON schema from sample dataset or connector type template |
| `get_caep_event_types` | Return full CAEP event type catalog |
| `get_risc_event_types` | Return full RISC event type catalog |
| `get_signal_examples` | Return 3–5 few-shot example signals for the given connector type |
| `get_allowed_modules` | Return allowed builtins and importable modules list |

---

## LLM System Prompt

The system prompt provided to the LLM includes:

1. **Signal function contract** — `evaluate(dataset: dict) -> dict` signature and return schema (`result`, `summary`, `details`, `metadata`)
2. **Allowed builtins** — `len`, `range`, `enumerate`, `zip`, `map`, `filter`, `sorted`, `reversed`, `min`, `max`, `sum`, `abs`, `round`, `all`, `any`, `isinstance`, `type`, `str`, `int`, `float`, `bool`, `list`, `dict`, `tuple`, `set`, `frozenset`, `print`
3. **Allowed modules** — `json`, `re`, `datetime`, `math`, `statistics`, `collections`, `ipaddress`, `hashlib`
4. **Dataset JSON schema** — derived from connector type template or provided sample dataset
5. **CAEP/RISC event type catalog** — full list of event type URIs for auto-mapping suggestions
6. **Few-shot examples** — 3–5 example signals for the same connector type
7. **Restrictions** — no imports beyond allowed list, no file/network/OS/subprocess access

---

## Signal Generation

### POST /api/v1/sb/signals/generate

Generate signal code from an English description using the AI agent. The agent analyzes intent, generates code, compiles, tests, and self-heals in up to 5 iterations.

**Permission:** `sandbox.create`

### Query Params

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

### Request Body Fields

| Field | Type | Required | Validation | Description |
| --- | --- | --- | --- | --- |
| `prompt` | string | yes | Non-empty, max 2000 chars | English description of what the signal should check |
| `connector_type_code` | string | yes | Must exist in `05_dim_connector_types` | Connector type for dataset schema and few-shot examples |
| `sample_dataset_id` | UUID | no | Must exist in tenant scope | Specific dataset to use for test execution |
| `asset_version_code` | string | no | — | Target asset version for schema selection |

```json
{
  "prompt": "Check that all GitHub repositories have branch protection enabled on the main branch, requiring at least 1 approving review before merging",
  "connector_type_code": "github",
  "sample_dataset_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "asset_version_code": null
}
```

**Response** `201 Created`

```json
{
  "generated_code": "def evaluate(dataset: dict) -> dict:\n    repos = dataset.get('repositories', [])\n    unprotected = []\n    for repo in repos:\n        bp = repo.get('branch_protection', {})\n        main = bp.get('main', {})\n        if not main.get('enabled', False):\n            unprotected.append({\n                'check': repo['name'],\n                'status': 'fail',\n                'message': 'No branch protection on main'\n            })\n        elif main.get('required_approving_review_count', 0) < 1:\n            count = main.get('required_approving_review_count', 0)\n            unprotected.append({\n                'check': repo['name'],\n                'status': 'fail',\n                'message': f'Only {count} reviews required (minimum 1)'\n            })\n    if unprotected:\n        return {\n            'result': 'fail',\n            'summary': f'{len(unprotected)} of {len(repos)} repos missing branch protection',\n            'details': {'non_compliant': unprotected, 'total_repos': len(repos)},\n            'metadata': {'rows_scanned': len(repos)}\n        }\n    return {\n        'result': 'pass',\n        'summary': f'All {len(repos)} repos have branch protection with >= 1 review',\n        'details': {},\n        'metadata': {'rows_scanned': len(repos)}\n    }",
  "compile_status": "success",
  "test_result": {
    "result": "pass",
    "summary": "All 5 repos have branch protection with >= 1 review",
    "details": {},
    "metadata": { "rows_scanned": 5 }
  },
  "caep_event_type": null,
  "risc_event_type": null,
  "custom_event_type": "https://schemas.kcontrol.io/secevent/sandbox/event-type/github_branch_protection_check",
  "iterations_used": 2,
  "signal_name_suggestion": "github_branch_protection_check",
  "signal_description_suggestion": "Checks that all repositories have branch protection enabled on the main branch with at least 1 required approving review",
  "agent_trace": [
    {
      "iteration": 1,
      "node": "analyze_intent",
      "output": "Connector: github. Check: branch protection on main. Threshold: >= 1 review. Dataset key: repositories[].branch_protection.main. No matching CAEP/RISC event type; will use custom namespace."
    },
    {
      "iteration": 1,
      "node": "generate_code",
      "output": "Generated evaluate() function accessing dataset.repositories[].branch_protection.main"
    },
    {
      "iteration": 1,
      "node": "compile_validate",
      "output": "RestrictedPython compile: FAILED",
      "error": "Line 8: name 'count' is not defined before use in f-string"
    },
    {
      "iteration": 2,
      "node": "fix_code",
      "output": "Fixed: moved count assignment before f-string usage"
    },
    {
      "iteration": 2,
      "node": "compile_validate",
      "output": "RestrictedPython compile: OK"
    },
    {
      "iteration": 2,
      "node": "run_tests",
      "output": "Test execution: PASS. result=pass, summary='All 5 repos have branch protection with >= 1 review'"
    },
    {
      "iteration": 2,
      "node": "finalize",
      "output": "Signal generation complete after 2 iterations"
    }
  ]
}
```

### Response Fields

| Field | Type | Description |
| --- | --- | --- |
| `generated_code` | string | Final Python `evaluate()` function body |
| `compile_status` | string | `success` — compiled clean; `failed` — max iterations exhausted before clean compile |
| `test_result` | object | Result dict from running against sample or template dataset; `null` if no dataset available |
| `caep_event_type` | string | Matched CAEP event type URI, or `null` |
| `risc_event_type` | string | Matched RISC event type URI, or `null` |
| `custom_event_type` | string | Suggested K-Control custom event type URI in `https://schemas.kcontrol.io/secevent/sandbox/event-type/{signal_code}` format, or `null` |
| `iterations_used` | int | Number of compile/fix cycles used (1–5) |
| `signal_name_suggestion` | string | Suggested `signal_code` value |
| `signal_description_suggestion` | string | Suggested human-readable description |
| `agent_trace` | object[] | Step-by-step log of agent node outputs and decisions |

### Agent Trace Fields

| Field | Type | Description |
| --- | --- | --- |
| `iteration` | int | Which iteration (1–5) this step occurred in |
| `node` | string | Agent node name (analyze_intent, generate_code, compile_validate, run_tests, fix_code, finalize) |
| `output` | string | Human-readable summary of what the node produced |
| `error` | string | Compile or test error detail (only present on failure nodes) |

### Error Responses

| Status | Description |
| --- | --- |
| 400 | Empty prompt |
| 401 | Missing or invalid Bearer token |
| 403 | Missing `sandbox.create` permission |
| 404 | `sample_dataset_id` not found in tenant scope |
| 422 | Unknown `connector_type_code` |
| 422 | Prompt exceeds 2000 characters |
| 500 | Agent exhausted all 5 iterations without producing valid code (body includes `last_compile_error`, `last_test_result`, `iterations_used`) |
| 503 | `SANDBOX_AI_PROVIDER_URL` is not configured |

### 500 Response Example (max iterations exceeded)

```json
{
  "detail": "AI agent failed to produce valid code after 5 iterations",
  "last_compile_error": "RestrictedPython: _inplacevar_ not allowed on line 12",
  "last_test_result": null,
  "iterations_used": 5,
  "agent_trace": [
    { "iteration": 1, "node": "generate_code", "output": "..." },
    { "iteration": 1, "node": "compile_validate", "output": "FAILED", "error": "..." },
    { "iteration": 2, "node": "fix_code", "output": "..." }
  ]
}
```

### 503 Response Example

```json
{
  "detail": "AI signal generation is not available: SANDBOX_AI_PROVIDER_URL is not configured"
}
```

---

## Workflow: Generate Then Save

The typical workflow after calling `POST /signals/generate`:

1. Review the `generated_code` and `agent_trace`
2. Optionally modify the code in the UI
3. Create a signal: `POST /api/v1/sb/signals` with `python_source = generated_code`
4. Run against a dataset: `POST /api/v1/sb/runs`
5. If results are satisfactory, promote to GRC: `POST /api/v1/sb/signals/{id}/promote`

---

## Signal Contract Reference

Every signal generated by the agent (and accepted by the system) must conform to this contract:

```python
def evaluate(dataset: dict) -> dict:
    # Dataset structure depends on connector_type_code
    # Access data via dataset.get('key', default)
    return {
        "result": "pass" | "fail" | "warning" | "error",
        "summary": "One-line description (max 500 chars)",
        "details": { },     # Signal-specific structured findings; arbitrary JSON
        "metadata": {       # Optional execution stats
            "execution_time_ms": 0,
            "rows_scanned": 0
        }
    }
```

### Sandbox Constraints (enforced on generated code)

| Constraint | Limit |
| --- | --- |
| CPU time | 10 seconds |
| Wall-clock timeout | 15 seconds |
| Memory | 128 MB |
| Open file descriptors | 10 |
| File system access | None |
| Network access | None |
| Subprocess creation | None |
| Allowed imports | json, re, datetime, math, statistics, collections, ipaddress, hashlib |

---

## Example Prompts by Connector Type

### AWS

```text
Check that all S3 buckets have server-side encryption enabled using AES-256 or KMS
```

```text
Verify that CloudTrail is enabled and multi-region in all AWS regions
```

```text
Flag IAM users with access keys older than 90 days that have been used in the last 30 days
```

### GitHub

```text
Check that all repositories have branch protection enabled on main with at least 1 review required
```

```text
Verify no repository has a plaintext secret in its most recent commit message
```

### Kubernetes

```text
Check that no pod is running as root (runAsNonRoot must be true in securityContext)
```

```text
Verify all namespaces have resource quotas defined for CPU and memory
```

---

## Audit Events

| Event Type | Entity | Key Properties |
| --- | --- | --- |
| `signal_generated` | `signal` | connector_type_code, iterations_used, compile_status, caep_event_type, risc_event_type |
| `signal_generation_failed` | `signal` | connector_type_code, iterations_used, last_compile_error |

---

## Cross-References

| Related Resource | Endpoint |
| --- | --- |
| Create signal after generation | `POST /api/v1/sb/signals` — see `22_sandbox_signals.md` |
| Run generated signal | `POST /api/v1/sb/runs` — see `26_sandbox_execution.md` |
| Promote signal to GRC | `POST /api/v1/sb/signals/{id}/promote` — see `28_sandbox_libraries.md` |
| SSF event type reference | See `29_sandbox_ssf.md` for CAEP/RISC URI catalog |
| Connector type dimensions | `GET /api/v1/sb/dimensions/connector-types` — see `20_sandbox_connectors.md` |
