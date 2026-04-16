# Signal Spec Agent (Markdown, Dataset-Grounded)

**Priority:** P0 — first stage of the pipeline
**Status:** Exists, needs enhancement (Markdown output + dataset grounding)
**Module:** `backend/20_ai/22_signal_spec/`
**Base path:** `/api/v1/ai/signal-spec`

---

## Overview

The Signal Spec Agent generates a structured specification for a compliance signal. The spec is the contract between the dataset schema and the Python `evaluate()` function. It defines what to check, which dataset fields to use, what configurable arguments exist, and what pass/fail/warning means.

**Current state:** Generates JSON spec via SSE streaming. Works.

**Enhancement needed:**
1. Generate Markdown representation alongside JSON (user-editable)
2. Ground field paths in exact dataset schema (not hallucinated paths)
3. Store Markdown in `current_spec.markdown` JSONB key + `spec.md` file
4. New PATCH endpoint for editing Markdown → round-trip back to JSON

---

## LangGraph Refactor

### State

```python
class SpecState(TypedDict):
    # Inputs
    session_id: str
    connector_type: str
    dataset_schema: dict          # rich schema: {field_path: {type, example, nullable}}
    sample_records: list[dict]    # 1-3 sample records from source dataset
    user_prompt: str
    conversation_history: list[dict]

    # Working state
    spec_json: dict | None
    feasibility: dict | None
    markdown: str | None
    iteration: int
    error: str | None
```

### Graph

```text
extract_schema → generate_spec → check_feasibility → generate_markdown → END
                                       ↓ (infeasible)
                                      END
```

### Nodes

| Node | Purpose |
|------|---------|
| `extract_schema` | Build rich schema from source dataset records (field paths, types, examples, nullable) |
| `generate_spec` | LLM generates full spec JSON using dataset schema + user prompt. Field paths MUST come from `dataset_schema` keys — no hallucinated paths. |
| `check_feasibility` | LLM evaluates if the spec is implementable with available fields. Status: feasible/partial/infeasible. |
| `generate_markdown` | Convert spec JSON to Markdown format (see template below). Only runs if feasible. |

---

## Markdown Template

The Markdown spec uses exact field paths from the dataset:

```markdown
# Signal: {signal_code}

## Description
{description}

## Intent
{intent — why this matters for compliance}

## Detection Logic
{step-by-step algorithm in plain English, referencing exact field paths}

## Dataset Fields Used

| Field Path | Type | Required | Purpose |
|---|---|---|---|
| postgres_roles[].rolname | string | yes | Role identifier |
| postgres_roles[].rolcanlogin | boolean | yes | Login capability check |
| postgres_stat_activity[].usename | string | no | Last activity lookup |

## Configurable Arguments

| Argument | Type | Default | Min | Max | Description |
|---|---|---|---|---|---|
| dormant_days | integer | 90 | 1 | 365 | Days of inactivity threshold |
| exclude_system_roles | boolean | true | — | — | Skip pg_ prefixed roles |

## Expected Outcomes

- **PASS**: {when all checks pass}
- **FAIL**: {when one or more checks fail}
- **WARNING**: {edge cases, incomplete data}

## Test Scenarios

| Scenario | Expected Result | Description |
|---|---|---|
| All roles active | pass | All login-capable roles active within threshold |
| Single dormant account | fail | One role exceeds dormant_days |
| No activity data | warning | Roles exist but no stat_activity records |

## SSF Mapping

- **Standard**: {caep|risc|custom}
- **Event Type**: {event type code}
- **Severity**: {critical|high|medium|low}
```

---

## API Endpoints

### Existing (keep as-is)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/sessions` | Create spec session |
| GET | `/sessions/{id}` | Get session details |
| POST | `/sessions/{id}/stream/generate` | SSE: generate spec |
| POST | `/sessions/{id}/stream/refine` | SSE: refine spec conversationally |
| POST | `/sessions/{id}/stream/feasibility` | SSE: standalone feasibility check |
| POST | `/sessions/{id}/approve` | Approve spec → auto-enqueue test dataset gen |

### New Endpoints

#### PATCH `/sessions/{id}/markdown`

Update the spec by editing the Markdown. Parses Markdown sections back into structured JSON fields.

**Request:**

```json
{
  "markdown": "# Signal: check_dormant_accounts\n\n## Description\n..."
}
```

**Response:** `200 OK`

```json
{
  "session_id": "...",
  "spec_json": { "...updated structured spec..." },
  "markdown": "...the saved markdown...",
  "parse_warnings": ["Could not parse 'Detection Logic' section — kept previous value"]
}
```

**Parsing rules:**
- Section headers (`## Description`, `## Configurable Arguments`, etc.) map to spec JSON keys
- Tables in `Dataset Fields Used` parse to `dataset_fields_used` array
- Tables in `Configurable Arguments` parse to `configurable_args` array
- Free text sections (`Description`, `Detection Logic`) map directly
- Unknown sections are ignored with a warning
- If a section can't be parsed, the previous JSON value is kept

---

## Files to Modify

| File | Change |
|------|--------|
| `backend/20_ai/22_signal_spec/agent.py` | Refactor to LangGraph StateGraph. Add `generate_markdown` node. |
| `backend/20_ai/22_signal_spec/prompts.py` | Add `MARKDOWN_SYSTEM_PROMPT`. Update `SPEC_SYSTEM_PROMPT` to enforce dataset field grounding. |
| `backend/20_ai/22_signal_spec/service.py` | Add `update_spec_markdown()` method with Markdown parser. |
| `backend/20_ai/22_signal_spec/schemas.py` | Add `UpdateMarkdownRequest`, `UpdateMarkdownResponse`. |
| `backend/20_ai/22_signal_spec/router.py` | Add `PATCH /sessions/{id}/markdown` endpoint. |

---

## Verification

1. Create spec session with a source dataset → verify Markdown generated with exact field paths
2. Edit Markdown (change `dormant_days` default from 90 to 60) → verify JSON updated
3. Approve spec → verify test dataset gen job enqueued
4. Frontend: Monaco/CodeMirror editor shows Markdown, edits save correctly
