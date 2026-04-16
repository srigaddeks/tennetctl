# Signal Codegen Agent (LangGraph Deep Agent)

**Priority:** P0 — most critical stage, generates the Python function
**Status:** Exists (for-loop), needs LangGraph refactor
**Module:** `backend/20_ai/24_signal_codegen/`
**Job type:** `signal_codegen`

---

## Overview

The Signal Codegen Agent generates a Python `evaluate()` function from a signal spec, then iteratively compiles, tests, and fixes it until all test cases pass. This is the heart of the platform — if this doesn't work reliably, nothing else matters.

**Current state:** 10-iteration for-loop with LLM calls. Works but no checkpointing, no per-node observability, no resume-on-crash.

**Target:** LangGraph StateGraph with named nodes, conditional edges, PostgreSQL checkpointing, and file-based code output.

---

## LangGraph StateGraph

### State

```python
class CodegenState(TypedDict):
    # Inputs
    signal_id: str
    signal_spec: dict              # locked spec from stage 1
    rich_schema: dict              # dataset schema
    test_cases: list[dict]         # from stage 2 (with expected_output)
    configurable_args: dict        # default args from spec

    # Working state
    code: str | None               # current Python code
    compile_error: str | None      # last compile error
    test_results: list[dict]       # per-case {case_id, expected, actual, passed}
    failed_cases: list[dict]       # cases that didn't match expected
    fix_history: list[str]         # previous errors (context for LLM)
    iteration: int                 # current iteration (0-based)
    max_iterations: int            # default 10

    # Output
    final_code: str | None
    args_schema: list[dict] | None # extracted configurable args JSON schema
    codegen_iterations: int        # total iterations consumed
    success: bool
```

### Graph

```text
generate ──→ compile ──→ test ──→ extract_args ──→ write_files ──→ END
                ↓ (error)    ↓ (failures)
               fix ←────── fix
                ↓            ↓
             compile       compile (loop, max_iterations)
```

### Nodes

| Node | Purpose |
|------|---------|
| `generate` | LLM generates initial Python code from spec + dataset schema + examples |
| `compile` | RestrictedPython compile check. Sets `compile_error` or clears it. |
| `test` | Execute against ALL test cases. Compare actual vs expected_output. Track failed_cases. |
| `fix` | LLM regenerates code with error context (compile error or failed test cases + fix_history). Increments iteration. |
| `extract_args` | LLM extracts kwargs from function signature → JSON schema array |
| `write_files` | Write Python + spec.md + args_schema.json + test_bundle.json to filesystem |

### Conditional Edges

```python
def after_compile(state: CodegenState) -> str:
    if state["compile_error"]:
        return "fix" if state["iteration"] < state["max_iterations"] else "__end__"
    return "test"

def after_test(state: CodegenState) -> str:
    if state["failed_cases"]:
        return "fix" if state["iteration"] < state["max_iterations"] else "__end__"
    return "extract_args"

def after_fix(state: CodegenState) -> str:
    return "compile"  # always loop back to compile after fix
```

---

## Code Generation Prompt

The generation prompt must include:

1. **Signal spec** — full spec JSON with detection_logic, field paths, configurable_args
2. **Dataset schema** — rich schema with types and example values
3. **Function contract** — `evaluate(dataset: dict, **kwargs) -> dict`
4. **Allowed modules** — json, re, datetime, math, statistics, collections, ipaddress, hashlib
5. **Restrictions** — no file I/O, no network, no subprocess, no exec/eval, no __import__
6. **Few-shot examples** — 2-3 working signals for the same connector type
7. **Configurable args** — must accept as kwargs with defaults matching spec

---

## Fix Prompt Context

When fixing, the LLM receives:

1. Current code that failed
2. Error type: `compile_error` or `test_failure`
3. For compile errors: full traceback
4. For test failures: list of failed cases with:
   - `case_id`, `scenario_name`
   - `expected_output` (what the test expects)
   - `actual_output` (what the signal returned)
   - Diff highlighting
5. Fix history: previous errors (to avoid repeating the same fix)

---

## Test Execution

For each test case:

```python
result = await execution_engine.execute(
    code=state["code"],
    dataset=test_case["dataset_input"],
    configurable_args=test_case.get("configurable_args", state["configurable_args"]),
    timeout_ms=10_000,
    max_memory_mb=256
)

passed = (
    result["result_code"] == test_case["expected_output"]["result"]
    # Optionally also compare summary/details for stricter validation
)
```

---

## Output: Signal EAV Properties Written

| Property Key | Value |
|--------------|-------|
| `python_source` | Final validated Python code |
| `signal_args_schema` | JSON array of `{name, type, default, label, description}` |
| `codegen_iterations` | Number of iterations consumed |
| `codegen_test_results` | Summary: `{total, passed, failed}` |
| `codegen_failure_reason` | (Only on failure) Last error + test results |

Signal status updated to `validated` on success, stays `draft` on failure.

---

## File Output

After successful codegen, write to filesystem:

```text
{SIGNAL_STORE_ROOT}/{org_id}/{signal_code}/v{version}/
    evaluate.py          — the Python function
    spec.md              — the Markdown signal spec
    args_schema.json     — configurable arguments schema
    test_bundle.json     — test cases with expected outputs
    metadata.json        — {signal_id, created_at, iterations, status, org_id}
```

See: [47_signal_file_store.md](47_signal_file_store.md) for details.

---

## Files to Modify

| File | Change |
|------|--------|
| `backend/20_ai/24_signal_codegen/job_handler.py` | Replace for-loop with LangGraph StateGraph. Add checkpointing. Add auto-chain to threat_composer. |
| `backend/20_ai/24_signal_codegen/prompts.py` | Enhance fix prompt with diff-style failed case comparison. |
| `backend/20_ai/24_signal_codegen/job_processor.py` | Update dispatcher to use new handler. |

---

## Verification

1. Generate signal from spec → verify Python code compiles
2. Run test suite → verify all test cases pass (actual matches expected)
3. Kill process mid-iteration → restart → verify resume from checkpoint (not restart from 0)
4. Verify files written: `{store_root}/{org_id}/{signal_code}/v1/evaluate.py` exists
5. Verify EAV properties: `python_source`, `signal_args_schema` populated
6. Failure case: bad spec → verify iterations exhaust → signal stays `draft` with `codegen_failure_reason`
7. Verify auto-chain: codegen success → threat_composer job enqueued (if flag set)
