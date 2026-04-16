# Test Dataset Generator (AI, with Expected Outputs)

**Priority:** P0 — generates test data for signal validation
**Status:** Exists, needs enhancement (expected output comparison)
**Module:** `backend/20_ai/23_test_dataset_gen/`
**Job type:** `signal_test_dataset_gen`

---

## Overview

The Test Dataset Generator creates 15-20 test cases from a signal spec. Each test case contains:

1. **`dataset_input`** — realistic JSON matching the exact dataset schema
2. **`configurable_args`** — argument overrides for this specific test case
3. **`expected_output`** — the expected signal result (pass/fail/warning + summary + details)

The expected outputs enable **automated comparison** — run the signal against each test case, compare actual vs expected, show a pass/fail report. This is how signals get validated and improved.

---

## LangGraph Refactor

### State

```python
class TestDatasetState(TypedDict):
    # Inputs
    signal_id: str
    signal_spec: dict              # locked spec from stage 1
    rich_schema: dict              # {field_path: {type, example, nullable}}
    sample_records: list[dict]     # reference records for shape

    # Working state
    test_cases: list[dict]         # generated cases
    validation_errors: list[str]   # shape violations
    fix_attempts: int              # max 3
    rejected_cases: list[str]      # case_ids that couldn't be fixed

    # Output
    final_bundle: list[dict] | None
    dataset_id: str | None         # created dataset record
```

### Graph

```text
generate_cases → validate_shape ──→ finalize → END
                       ↓ (errors)
                  fix_cases ──→ validate_shape (loop, max 3 fixes)
```

---

## Test Case Structure

```json
{
  "case_id": "tc_001",
  "scenario_name": "all_roles_active_within_threshold",
  "description": "All login-capable roles have authenticated within dormant_days",
  "dataset_input": {
    "postgres_roles": [
      {"rolname": "app_user", "rolcanlogin": true, "rolsuper": false, "rolcreatedb": false},
      {"rolname": "admin", "rolcanlogin": true, "rolsuper": true, "rolcreatedb": true}
    ],
    "postgres_stat_activity": [
      {"usename": "app_user", "state": "idle", "state_change": "2026-03-19T10:00:00Z"},
      {"usename": "admin", "state": "active", "state_change": "2026-03-20T08:00:00Z"}
    ]
  },
  "configurable_args": {
    "dormant_days": 90,
    "exclude_system_roles": true
  },
  "expected_output": {
    "result": "pass",
    "summary": "All 2 login-capable roles have authenticated within 90 days",
    "details": [
      {"check": "app_user", "status": "pass", "message": "Last activity 1 day ago"},
      {"check": "admin", "status": "pass", "message": "Last activity today"}
    ]
  }
}
```

---

## Required Test Scenarios

The AI must generate cases covering all of these categories:

| Category | Example Cases |
|----------|---------------|
| **Happy path** | All checks pass, clean data |
| **Single failure** | One item fails, rest pass |
| **All failures** | Everything fails |
| **Edge: empty data** | Empty arrays, missing keys |
| **Edge: single item** | Only one record in arrays |
| **Boundary values** | Value exactly at threshold (e.g., dormant_days = 90, last activity 90 days ago) |
| **Argument variations** | Different configurable_args values (dormant_days=0, dormant_days=365) |
| **Warning cases** | Incomplete data that triggers warning instead of pass/fail |
| **Exclusion logic** | Items that should be skipped (e.g., system roles with exclude_system_roles=true) |
| **Type edge cases** | Null values, empty strings, unexpected types |

Minimum: 15 test cases. Target: 20.

---

## Shape Preservation

**Non-negotiable rule:** Test case `dataset_input` must match the exact JSON structure of the reference schema. The AI can only vary VALUES, never STRUCTURE.

The `structural_diff()` function (already exists in `agent.py`) validates:
- Same top-level keys
- Same nested object keys
- Arrays contain objects with same keys
- No extra keys added
- No required keys removed

If shape is violated:
1. LLM fix prompt with specific violations highlighted
2. Retry up to 3 times
3. If still broken, reject the case (log warning, continue with valid cases)

---

## Storage

Test dataset stored as:
- New dataset record: `dataset_source_code='ai_generated_tests'`
- Each test case as a payload row in `43_dtl_dataset_payloads`
- Full bundle as EAV property `test_bundle_json` on the dataset
- `test_dataset_id` written back to signal EAV properties

---

## Files to Modify

| File | Change |
|------|--------|
| `backend/20_ai/23_test_dataset_gen/agent.py` | Refactor to LangGraph StateGraph. Ensure expected_output is always generated. |
| `backend/20_ai/23_test_dataset_gen/prompts.py` | Update prompt to require expected_output with full result structure (not just result code). |
| `backend/20_ai/23_test_dataset_gen/job_handler.py` | Wire LangGraph graph execution. Pass checkpointer. |

---

## Verification

1. Generate test dataset from a spec → verify 15+ cases with expected_output
2. Verify shape preservation: all dataset_input structures match reference schema
3. Verify edge cases covered: empty arrays, boundary values, arg variations
4. Load test bundle → verify parseable and all cases have expected_output.result
