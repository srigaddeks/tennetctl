# Threat Composer + Library Builder + Auto-Chaining

**Priority:** P1 — downstream from codegen
**Status:** Exists, needs LangGraph refactor + auto-chaining
**Modules:** `backend/20_ai/25_threat_composer/`, `backend/20_ai/26_library_builder/`
**Job types:** `threat_composer`, `library_builder`

---

## Overview

After signals are generated and validated, the pipeline continues:

1. **Threat Composer** — Load validated signal catalog, LLM composes meaningful threat types using AND/OR/NOT expression trees
2. **Library Builder** — Group threat types by connector, create policies wrapping each threat, bundle into control libraries

Both need LangGraph refactor and auto-chaining from codegen.

---

## Auto-Chaining

### Current Chain (stops after codegen)

```text
spec_approve → signal_test_dataset_gen → signal_codegen → (STOPS)
```

### Target Chain (full pipeline)

```text
spec_approve → signal_test_dataset_gen → signal_codegen → threat_composer → library_builder
```

**Implementation:**

1. `ApproveSpecRequest` (in `22_signal_spec/schemas.py`) gets new flags:
   - `auto_compose_threats: bool = True`
   - `auto_build_library: bool = True`

2. These flags pass through the job chain via `input_json`:
   - Test dataset gen → passes to codegen input
   - Codegen → if `auto_compose_threats=true`, enqueues `threat_composer` on success
   - Threat composer → if `auto_build_library=true`, enqueues `library_builder` on success

3. Each stage checks the flag before auto-enqueuing. User can stop the chain at any point by setting flags to false.

---

## Threat Composer LangGraph

### State

```python
class ThreatComposerState(TypedDict):
    org_id: str
    workspace_id: str | None
    signal_catalog: list[dict]     # validated signals: code, name, description, connector_type
    proposals: list[dict]          # LLM-generated threat type proposals
    validated: list[dict]          # proposals that passed validation
    rejected: list[str]            # reasons for rejected proposals
    created_ids: list[str]         # IDs of created threat type records
```

### Graph

```text
load_signals → compose_threats → validate_trees → create_records → END
                                       ↓ (invalid trees)
                                  fix_trees → validate_trees (max 2 fixes)
```

### Expression Tree Structure

```json
{
  "operator": "AND",
  "conditions": [
    {"signal_code": "check_dormant_accounts", "expected_result": "fail"},
    {
      "operator": "OR",
      "conditions": [
        {"signal_code": "check_excessive_privileges", "expected_result": "fail"},
        {"signal_code": "check_mfa_disabled", "expected_result": "fail"}
      ]
    }
  ]
}
```

**Validation rules:**
- AND/OR: must have 2+ children
- NOT: must have exactly 1 child
- Leaf: must have `signal_code` (must exist in catalog) + `expected_result` (pass/fail/warning)
- Max depth: 5 levels

---

## Library Builder LangGraph

### State

```python
class LibraryBuilderState(TypedDict):
    org_id: str
    workspace_id: str | None
    threat_types: list[dict]       # created threat types with policies
    policies_created: list[str]    # policy IDs
    libraries_created: list[str]   # library IDs
```

### Graph

```text
load_threats → create_policies → group_by_connector → create_libraries → END
```

**Policy creation:**
- One policy per threat type: `{threat_code}_policy`
- Default action: `alert` with 1-hour cooldown
- EAV: `name`, `ai_generated=true`

**Library grouping:**
- Group threats by `connector_type_code`
- One library per connector type: `AI Control Library — {connector_type}`
- Link policies to library with sort_order

---

## Files to Modify

| File | Change |
|------|--------|
| `backend/20_ai/22_signal_spec/schemas.py` | Add `auto_compose_threats`, `auto_build_library` to `ApproveSpecRequest` |
| `backend/20_ai/24_signal_codegen/job_handler.py` | After success, enqueue `threat_composer` if flag set |
| `backend/20_ai/25_threat_composer/job_handler.py` | Refactor to LangGraph. After success, enqueue `library_builder` if flag set. |
| `backend/20_ai/26_library_builder/job_handler.py` | Refactor to LangGraph. |

---

## Verification

1. Generate 3 signals → run threat composer → verify 2+ threat types created with valid expression trees
2. Verify expression tree references only existing signal codes
3. Run library builder → verify library created with policies linked
4. Full auto-chain: approve spec → verify all 5 stages complete automatically
5. Set `auto_compose_threats=false` → verify pipeline stops after codegen
