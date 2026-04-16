# Sandbox Execution Engine API

**Base path:** `/api/v1/sb`
**Auth:** Bearer JWT required on all endpoints
**Multi-tenant:** `org_id` query parameter required on all endpoints

---

## Overview

The Execution Engine is the core runtime of the K-Control Sandbox. It compiles and runs Python signal functions in an isolated subprocess sandbox, stores results in a dual-write strategy (ClickHouse for all results, PostgreSQL for actionable results only), and orchestrates a post-execution pipeline that evaluates threat expression trees and fires policy actions.

### Execution Chain

```text
Signal (python_source) + Dataset (payload)
    → RestrictedPython compile
    → subprocess isolate (RLIMIT_AS, RLIMIT_DATA, RLIMIT_NOFILE, timeout)
    → result: pass | fail | warning | error
    → ClickHouse: ALL results (sandbox_signal_results)
    → PostgreSQL: fail | warning | error only (25_fct_sandbox_runs)
    → [batch only] evaluate threat expression trees
    → [batch only] fire enabled policies for triggered threats
```

### Signal Function Contract

Every signal must define a top-level `evaluate` function with the following signature and return structure:

```python
def evaluate(dataset: dict) -> dict:
    return {
        "result": "pass" | "fail" | "warning" | "error",
        "summary": "Human-readable one-liner (max 500 chars)",
        "details": { ... },    # Signal-specific structured data; arbitrary JSON
        "metadata": {          # Optional execution stats
            "execution_time_ms": 245,
            "rows_scanned": 12
        }
    }
```

### Sandbox Isolation Constraints

| Constraint | Limit | Notes |
| --- | --- | --- |
| CPU time | 10 seconds | RLIMIT_CPU via subprocess |
| Wall-clock timeout | 15 seconds | Subprocess kill after 15s |
| Memory (virtual) | 128 MB | RLIMIT_AS |
| Memory (data segment) | 128 MB | RLIMIT_DATA |
| Open file descriptors | 10 | RLIMIT_NOFILE |
| File system access | None | No open() allowed |
| Network access | None | No socket() allowed |
| Subprocess creation | None | No os.fork/exec |
| Allowed modules | See below | Import whitelist enforced |

**Allowed modules:** `json`, `re`, `datetime`, `math`, `statistics`, `collections`, `ipaddress`, `hashlib`

**Allowed builtins:** `len`, `range`, `enumerate`, `zip`, `map`, `filter`, `sorted`, `reversed`, `min`, `max`, `sum`, `abs`, `round`, `all`, `any`, `isinstance`, `type`, `str`, `int`, `float`, `bool`, `list`, `dict`, `tuple`, `set`, `frozenset`, `print`

### Dual-Write Strategy

| Result Code | PostgreSQL (`25_fct_sandbox_runs`) | ClickHouse (`sandbox_signal_results`) | Rationale |
| --- | --- | --- | --- |
| `pass` | Not written | Written | Pass results are non-actionable; ClickHouse only for analytics |
| `fail` | Written | Written | Actionable; needs querying, alerting, threat evaluation |
| `warning` | Written | Written | Semi-actionable; needs review |
| `error` | Written | Written | Execution failure; needs debugging |

---

## DB Tables

| Table | Schema | Type | Description |
| --- | --- | --- | --- |
| `06_dim_execution_statuses` | `15_sandbox` | Dimension | Execution lifecycle status codes |
| `07_dim_result_codes` | `15_sandbox` | Dimension | Signal result codes (pass, fail, warning, error) |
| `25_fct_sandbox_runs` | `15_sandbox` | Fact | Signal execution runs — fail/warning/error results only |
| `26_fct_threat_evaluations` | `15_sandbox` | Fact | Threat type evaluation records from batch runs |
| `27_fct_policy_executions` | `15_sandbox` | Fact | Policy execution audit trail |

ClickHouse tables:

| Table | Partitioning | Retention | Description |
| --- | --- | --- | --- |
| `sandbox_signal_results` | By day (`toYYYYMMDD(executed_at)`) | 90 days | All signal execution results including pass |
| `sandbox_threat_evaluations` | By day | 90 days | All threat evaluation results from batch runs |

### Key columns — `25_fct_sandbox_runs`

| Column | Type | Description |
| --- | --- | --- |
| `id` | UUID | Primary key |
| `tenant_key` | TEXT | Tenant isolation |
| `org_id` | UUID FK | Owning organisation |
| `workspace_id` | UUID FK | Owning workspace |
| `signal_id` | UUID FK → `44_fct_signals` | Signal that was executed |
| `dataset_id` | UUID FK → `42_fct_datasets` | Dataset used as input |
| `execution_status_code` | TEXT | queued / running / completed / failed / timeout / cancelled |
| `result_code` | TEXT | fail / warning / error (pass never written here) |
| `summary` | TEXT | One-line result description |
| `details` | JSONB | Signal-specific structured output |
| `metadata` | JSONB | Execution stats (time_ms, rows_scanned) |
| `python_source_snapshot` | TEXT | Snapshot of `python_source` at time of execution |
| `signal_version` | INT | Version of signal at time of execution |
| `created_at` | TIMESTAMPTZ | Execution timestamp |

---

## Dimensions

### GET /api/v1/sb/dimensions/execution-statuses

Returns all execution status dimension records. No authentication required.

**Response** `200 OK`

```json
[
  { "code": "queued",    "name": "Queued",    "description": "Waiting in execution queue",            "sort_order": 1 },
  { "code": "running",   "name": "Running",   "description": "Currently executing in subprocess",     "sort_order": 2 },
  { "code": "completed", "name": "Completed", "description": "Execution finished, result available",  "sort_order": 3 },
  { "code": "failed",    "name": "Failed",    "description": "Execution error or unhandled exception", "sort_order": 4 },
  { "code": "timeout",   "name": "Timeout",   "description": "Exceeded CPU or wall-clock limit",      "sort_order": 5 },
  { "code": "cancelled", "name": "Cancelled", "description": "Cancelled before execution began",      "sort_order": 6 }
]
```

### GET /api/v1/sb/dimensions/result-codes

Returns all signal result code dimension records. No authentication required.

**Response** `200 OK`

```json
[
  { "code": "pass",    "name": "Pass",    "description": "Signal evaluated successfully, no issue found", "sort_order": 1 },
  { "code": "fail",    "name": "Fail",    "description": "Signal detected a policy violation",            "sort_order": 2 },
  { "code": "warning", "name": "Warning", "description": "Signal detected a potential issue",             "sort_order": 3 },
  { "code": "error",   "name": "Error",   "description": "Signal threw an exception or timed out",        "sort_order": 4 }
]
```

---

## Signal Execution

### POST /api/v1/sb/runs

Execute a single signal against a dataset. The signal's `python_source` EAV property is loaded from `45_dtl_signal_properties`, the dataset payload from `43_dtl_dataset_payloads`, then compiled and run in the subprocess sandbox.

**Permission:** `sandbox.execute`

Query parameters:

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

Request body fields:

| Field | Type | Required | Validation | Description |
| --- | --- | --- | --- | --- |
| `signal_id` | UUID | yes | Must exist, tenant-scoped | Signal to execute |
| `dataset_id` | UUID | yes | Must exist, tenant-scoped | Dataset to evaluate against |
| `workspace_id` | UUID | yes | Must exist within org | Target workspace for result storage |

```json
{
  "signal_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "dataset_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "workspace_id": "c3d4e5f6-a7b8-9012-cdef-123456789012"
}
```

**Response** `201 Created`

```json
{
  "id": "d4e5f6a7-b8c9-0123-defa-234567890123",
  "signal_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "signal_code": "iam_mfa_disabled_check",
  "signal_version": 4,
  "dataset_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "workspace_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "execution_status": "completed",
  "result_code": "fail",
  "summary": "3 of 12 IAM users have MFA disabled",
  "details": {
    "total_users": 12,
    "compliant_count": 9,
    "non_compliant_count": 3,
    "non_compliant_users": [
      { "username": "alice.dev",  "user_id": "AIDABC123DEF456GHI789", "account_type": "human" },
      { "username": "bob.ops",    "user_id": "AIDAJK012LMN345OPQ678", "account_type": "human" },
      { "username": "svc-deploy", "user_id": "AIDARST901UVW234XYZ567", "account_type": "service" }
    ]
  },
  "metadata": {
    "execution_time_ms": 312,
    "rows_scanned": 12,
    "sandbox_memory_kb": 18432
  },
  "python_source_snapshot": "def evaluate(dataset: dict) -> dict:\n    users = dataset.get('iam_users', [])\n    disabled = [u for u in users if not u.get('mfa_active', False)]\n    if disabled:\n        return {'result': 'fail', 'summary': f'{len(disabled)} of {len(users)} IAM users have MFA disabled', 'details': {'non_compliant_users': disabled}, 'metadata': {}}\n    return {'result': 'pass', 'summary': 'All IAM users have MFA enabled', 'details': {}, 'metadata': {}}",
  "created_at": "2026-03-16T09:42:18Z"
}
```

Note: `result_code: "pass"` responses are returned in the API but not persisted to PostgreSQL. They are written to ClickHouse only.

Error responses:

| Status | Code | Description |
| --- | --- | --- |
| 400 | `bad_request` | Malformed request body |
| 401 | `unauthorized` | Missing or invalid Bearer token |
| 403 | `forbidden` | Missing `sandbox.execute` permission |
| 404 | `not_found` | Signal or dataset not found in tenant scope |
| 422 | `missing_python_source` | Signal has no `python_source` EAV property set |
| 422 | `missing_dataset_payload` | Dataset has no payload loaded |
| 429 | `rate_limited` | Execution concurrency limit reached |
| 500 | `execution_error` | Compilation error, runtime exception, or sandbox infrastructure failure |

---

### POST /api/v1/sb/runs/batch

Execute multiple signals against a dataset in parallel. After all signals complete, the engine evaluates all threat types whose expression trees reference the executed signal codes, then fires policies for any triggered threats.

**Permission:** `sandbox.execute`

Query parameters:

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

Request body fields:

| Field | Type | Required | Validation | Description |
| --- | --- | --- | --- | --- |
| `signal_ids` | UUID[] | yes | 1–50 items; all must exist | Signals to execute |
| `dataset_id` | UUID | yes | Must exist, tenant-scoped | Shared input dataset |
| `workspace_id` | UUID | yes | Must exist within org | Target workspace |

```json
{
  "signal_ids": [
    "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "e5f6a7b8-c9d0-1234-efab-567890123456",
    "f6a7b8c9-d0e1-2345-fabc-678901234567"
  ],
  "dataset_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "workspace_id": "c3d4e5f6-a7b8-9012-cdef-123456789012"
}
```

**Response** `201 Created`

```json
{
  "runs": [
    {
      "id": "d4e5f6a7-b8c9-0123-defa-234567890123",
      "signal_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "signal_code": "iam_mfa_disabled_check",
      "execution_status": "completed",
      "result_code": "fail",
      "summary": "3 of 12 IAM users have MFA disabled"
    },
    {
      "id": "e5f6a7b8-c9d0-1234-efab-567890123456",
      "signal_id": "e5f6a7b8-c9d0-1234-efab-567890123456",
      "signal_code": "iam_unusual_login_time_check",
      "execution_status": "completed",
      "result_code": "fail",
      "summary": "Login at 03:14 UTC outside normal business hours (06:00-22:00 UTC)"
    },
    {
      "id": "f6a7b8c9-d0e1-2345-fabc-678901234567",
      "signal_id": "f6a7b8c9-d0e1-2345-fabc-678901234567",
      "signal_code": "iam_geo_anomaly_check",
      "execution_status": "completed",
      "result_code": "pass",
      "summary": "No geographic login anomalies detected"
    }
  ],
  "signal_results": {
    "iam_mfa_disabled_check": "fail",
    "iam_unusual_login_time_check": "fail",
    "iam_geo_anomaly_check": "pass"
  },
  "threat_evaluations": [
    {
      "id": "a7b8c9d0-e1f2-3456-abcd-789012345678",
      "threat_type_id": "b8c9d0e1-f2a3-4567-bcde-890123456789",
      "threat_code": "TH-IAM-001",
      "threat_name": "Insider Threat — Compromised IAM Account",
      "triggered": true,
      "signal_results": {
        "iam_mfa_disabled_check": "fail",
        "iam_unusual_login_time_check": "fail",
        "iam_geo_anomaly_check": "pass"
      },
      "threat_type_version": 5
    }
  ],
  "policy_executions": [
    {
      "id": "c9d0e1f2-a3b4-5678-cdef-901234567890",
      "policy_id": "d0e1f2a3-b4c5-6789-defa-012345678901",
      "policy_code": "POL-IAM-001",
      "policy_name": "Critical IAM Threat Response",
      "threat_evaluation_id": "a7b8c9d0-e1f2-3456-abcd-789012345678",
      "outcome": "succeeded",
      "actions_executed": [
        { "action_type": "notification",    "status": "succeeded", "duration_ms": 145 },
        { "action_type": "evidence_report", "status": "succeeded", "duration_ms": 512 }
      ],
      "policy_version": 3
    }
  ]
}
```

Batch execution flow:

1. Validate all `signal_ids` and `dataset_id` exist within tenant scope
2. Load all signal `python_source` properties from `45_dtl_signal_properties` in batch
3. Load dataset payload from `43_dtl_dataset_payloads`
4. Execute all signals in parallel via subprocess pool (each in isolated sandbox)
5. Dual-write results: all to ClickHouse, fail/warning/error to PostgreSQL `25_fct_sandbox_runs`
6. Build `signal_results` map: `{ signal_code: result_code }`
7. Query `24_fct_threat_types` for threat types referencing any executed signal codes
8. Evaluate each threat type's expression tree against `signal_results` map
9. Write `26_fct_threat_evaluations` for all evaluated threats
10. Find enabled policies linked to triggered threat types (via `50_lnk_threat_type_policies`)
11. For each policy: check `cooldown_minutes` — skip if last execution is within cooldown window
12. Execute policy actions in defined sort order; write `27_fct_policy_executions`

Error responses:

| Status | Code | Description |
| --- | --- | --- |
| 400 | `bad_request` | Empty `signal_ids`, or more than 50 signals |
| 401 | `unauthorized` | Missing or invalid Bearer token |
| 403 | `forbidden` | Missing `sandbox.execute` permission |
| 404 | `not_found` | One or more signal IDs or dataset not found |
| 422 | `missing_python_source` | One or more signals have no `python_source` property |
| 422 | `missing_dataset_payload` | Dataset has no payload |
| 429 | `rate_limited` | Batch concurrency limit reached |
| 500 | `execution_error` | Sandbox infrastructure failure |

---

## Run History — PostgreSQL

### GET /api/v1/sb/runs

List signal execution runs from PostgreSQL. Contains only `fail`, `warning`, and `error` results. For `pass` results and full history, use `/runs/history` (ClickHouse).

**Permission:** `sandbox.view`

Query parameters:

| Param | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `org_id` | UUID | yes | — | Owning organisation |
| `workspace_id` | UUID | no | — | Filter by workspace |
| `signal_id` | UUID | no | — | Filter by signal |
| `dataset_id` | UUID | no | — | Filter by dataset |
| `execution_status` | string | no | — | queued / running / completed / failed / timeout / cancelled |
| `result_code` | string | no | — | fail / warning / error |
| `date_from` | ISO8601 | no | — | Filter runs created on or after this date |
| `date_to` | ISO8601 | no | — | Filter runs created on or before this date |
| `sort_by` | string | no | `created_at` | created_at |
| `sort_dir` | string | no | `desc` | asc / desc |
| `limit` | int | no | 100 | 1–500 |
| `offset` | int | no | 0 | >= 0 |

**Response** `200 OK`

```json
{
  "items": [
    {
      "id": "d4e5f6a7-b8c9-0123-defa-234567890123",
      "signal_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "signal_code": "iam_mfa_disabled_check",
      "signal_version": 4,
      "dataset_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "workspace_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "execution_status": "completed",
      "result_code": "fail",
      "summary": "3 of 12 IAM users have MFA disabled",
      "metadata": { "execution_time_ms": 312, "rows_scanned": 12 },
      "created_at": "2026-03-16T09:42:18Z"
    }
  ],
  "total": 156
}
```

---

### GET /api/v1/sb/runs/{id}

Get a single run record with full `details`, `metadata`, and `python_source_snapshot`.

**Permission:** `sandbox.view`

Query parameters:

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

**Response** `200 OK`

```json
{
  "id": "d4e5f6a7-b8c9-0123-defa-234567890123",
  "signal_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "signal_code": "iam_mfa_disabled_check",
  "signal_version": 4,
  "dataset_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "dataset_name": "AWS IAM Snapshot — March 16",
  "workspace_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "execution_status": "completed",
  "result_code": "fail",
  "summary": "3 of 12 IAM users have MFA disabled",
  "details": {
    "total_users": 12,
    "compliant_count": 9,
    "non_compliant_count": 3,
    "non_compliant_users": [
      { "username": "alice.dev",  "user_id": "AIDABC123DEF456GHI789" },
      { "username": "bob.ops",    "user_id": "AIDAJK012LMN345OPQ678" },
      { "username": "svc-deploy", "user_id": "AIDARST901UVW234XYZ567" }
    ]
  },
  "metadata": { "execution_time_ms": 312, "rows_scanned": 12, "sandbox_memory_kb": 18432 },
  "python_source_snapshot": "def evaluate(dataset: dict) -> dict:\n    users = dataset.get('iam_users', [])\n    disabled = [u for u in users if not u.get('mfa_active', False)]\n    ...",
  "created_at": "2026-03-16T09:42:18Z"
}
```

Error responses:

| Status | Description |
| --- | --- |
| 401 | Missing or invalid Bearer token |
| 403 | Missing `sandbox.view` permission |
| 404 | Run not found or not in tenant scope |

---

### GET /api/v1/sb/signals/{signal_id}/runs

Signal-specific run history from PostgreSQL (fail/warning/error only). Convenience alias for `GET /runs?signal_id={signal_id}`.

**Permission:** `sandbox.view`

Query params are identical to `GET /runs`, minus `signal_id` (inferred from path).

**Response** `200 OK` — same shape as `GET /runs`

---

## Full History — ClickHouse

### GET /api/v1/sb/runs/history

Query ClickHouse for full execution history including `pass` results. Use for analytics, trend analysis, compliance evidence collection, and SLA tracking.

**Permission:** `sandbox.view`

Query parameters:

| Param | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `org_id` | UUID | yes | — | Owning organisation |
| `workspace_id` | UUID | no | — | Filter by workspace |
| `signal_code` | string | no | — | Filter by signal code (exact match) |
| `dataset_id` | UUID | no | — | Filter by dataset |
| `result_code` | string | no | — | pass / fail / warning / error |
| `days` | int | no | 30 | Lookback window in days (max 365) |
| `date_from` | ISO8601 | no | — | Override for explicit start date |
| `date_to` | ISO8601 | no | — | Override for explicit end date |
| `sort_dir` | string | no | `desc` | asc / desc (sorts by `executed_at`) |
| `limit` | int | no | 1000 | 1–10000 |
| `offset` | int | no | 0 | >= 0 |

**Response** `200 OK`

```json
{
  "items": [
    {
      "run_id": "d4e5f6a7-b8c9-0123-defa-234567890123",
      "signal_code": "iam_mfa_disabled_check",
      "dataset_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "workspace_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "result_code": "fail",
      "summary": "3 of 12 IAM users have MFA disabled",
      "execution_time_ms": 312,
      "executed_at": "2026-03-16T09:42:18Z"
    },
    {
      "run_id": "b2c3d4e5-f6a7-8901-bcde-f12345678910",
      "signal_code": "iam_mfa_disabled_check",
      "dataset_id": "c3d4e5f6-a7b8-9012-cdef-123456789011",
      "workspace_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "result_code": "pass",
      "summary": "All 12 IAM users have MFA enabled",
      "execution_time_ms": 271,
      "executed_at": "2026-03-15T08:00:00Z"
    }
  ],
  "total": 842,
  "source": "clickhouse"
}
```

Business rules: `days` and `date_from`/`date_to` are mutually exclusive; explicit dates take precedence. Maximum `days` is 365; data beyond the ClickHouse TTL (90 days default) may not be available.

---

## Threat Evaluations

### GET /api/v1/sb/threat-evaluations

List threat evaluation records. Records are created whenever a batch run evaluates a threat type's expression tree against the collected signal results.

**Permission:** `sandbox.view`

Query parameters:

| Param | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `org_id` | UUID | yes | — | Owning organisation |
| `workspace_id` | UUID | no | — | Filter by workspace |
| `threat_type_id` | UUID | no | — | Filter to a specific threat type |
| `dataset_id` | UUID | no | — | Filter to a specific dataset |
| `triggered` | boolean | no | — | `true` for triggered only, `false` for not-triggered only |
| `date_from` | ISO8601 | no | — | Filter created on or after |
| `date_to` | ISO8601 | no | — | Filter created on or before |
| `sort_dir` | string | no | `desc` | asc / desc |
| `limit` | int | no | 100 | 1–500 |
| `offset` | int | no | 0 | >= 0 |

**Response** `200 OK`

```json
{
  "items": [
    {
      "id": "a7b8c9d0-e1f2-3456-abcd-789012345678",
      "threat_type_id": "b8c9d0e1-f2a3-4567-bcde-890123456789",
      "threat_code": "TH-IAM-001",
      "threat_name": "Insider Threat — Compromised IAM Account",
      "dataset_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "workspace_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "triggered": true,
      "signal_results": {
        "iam_mfa_disabled_check": "fail",
        "iam_unusual_login_time_check": "fail",
        "iam_geo_anomaly_check": "pass"
      },
      "threat_type_version": 5,
      "created_at": "2026-03-16T09:42:21Z"
    }
  ],
  "total": 67
}
```

---

### GET /api/v1/sb/threat-evaluations/{id}

Get a single threat evaluation with full `evaluation_trace` (step-by-step expression tree walk).

**Permission:** `sandbox.view`

Query parameters:

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

**Response** `200 OK`

```json
{
  "id": "a7b8c9d0-e1f2-3456-abcd-789012345678",
  "threat_type_id": "b8c9d0e1-f2a3-4567-bcde-890123456789",
  "threat_code": "TH-IAM-001",
  "threat_name": "Insider Threat — Compromised IAM Account",
  "dataset_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "workspace_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "triggered": true,
  "signal_results": {
    "iam_mfa_disabled_check": "fail",
    "iam_unusual_login_time_check": "fail",
    "iam_geo_anomaly_check": "pass"
  },
  "evaluation_trace": [
    { "node": "root",    "operator": "AND", "result": true },
    { "node": "root.0",  "signal_code": "iam_mfa_disabled_check",     "expected_result": "fail", "actual_result": "fail", "match": true },
    { "node": "root.1",  "operator": "OR",  "result": true },
    { "node": "root.1.0","signal_code": "iam_unusual_login_time_check","expected_result": "fail", "actual_result": "fail", "match": true },
    { "node": "root.1.1","signal_code": "iam_geo_anomaly_check",       "expected_result": "fail", "actual_result": "pass", "match": false }
  ],
  "threat_type_version": 5,
  "created_at": "2026-03-16T09:42:21Z"
}
```

Error responses:

| Status | Description |
| --- | --- |
| 401 | Missing or invalid Bearer token |
| 403 | Missing `sandbox.view` permission |
| 404 | Threat evaluation not found or not in tenant scope |

---

## Policy Executions

### GET /api/v1/sb/policy-executions

List policy execution audit records. A policy execution is created when a triggered threat causes a policy's action list to fire.

**Permission:** `sandbox.view`

Query parameters:

| Param | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `org_id` | UUID | yes | — | Owning organisation |
| `workspace_id` | UUID | no | — | Filter by workspace |
| `policy_id` | UUID | no | — | Filter to a specific policy |
| `threat_evaluation_id` | UUID | no | — | Filter to a specific threat evaluation |
| `outcome` | string | no | — | succeeded / partial_failure / failed / skipped_cooldown |
| `date_from` | ISO8601 | no | — | Filter created on or after |
| `date_to` | ISO8601 | no | — | Filter created on or before |
| `sort_dir` | string | no | `desc` | asc / desc |
| `limit` | int | no | 100 | 1–500 |
| `offset` | int | no | 0 | >= 0 |

Outcome values:

| Value | Description |
| --- | --- |
| `succeeded` | All actions in the policy completed without error |
| `partial_failure` | One or more actions failed; others succeeded |
| `failed` | All actions failed |
| `skipped_cooldown` | Policy was within its `cooldown_minutes` window; no actions fired |

**Response** `200 OK`

```json
{
  "items": [
    {
      "id": "c9d0e1f2-a3b4-5678-cdef-901234567890",
      "policy_id": "d0e1f2a3-b4c5-6789-defa-012345678901",
      "policy_code": "POL-IAM-001",
      "policy_name": "Critical IAM Threat Response",
      "threat_evaluation_id": "a7b8c9d0-e1f2-3456-abcd-789012345678",
      "outcome": "succeeded",
      "actions_executed": [
        { "action_type": "notification",    "status": "succeeded", "duration_ms": 145 },
        { "action_type": "evidence_report", "status": "succeeded", "duration_ms": 512 }
      ],
      "policy_version": 3,
      "created_at": "2026-03-16T09:42:24Z"
    }
  ],
  "total": 34
}
```

---

### GET /api/v1/sb/policy-executions/{id}

Get a single policy execution with full per-action detail including config snapshots and results.

**Permission:** `sandbox.view`

Query parameters:

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

**Response** `200 OK`

```json
{
  "id": "c9d0e1f2-a3b4-5678-cdef-901234567890",
  "policy_id": "d0e1f2a3-b4c5-6789-defa-012345678901",
  "policy_code": "POL-IAM-001",
  "policy_name": "Critical IAM Threat Response",
  "threat_evaluation_id": "a7b8c9d0-e1f2-3456-abcd-789012345678",
  "threat_type_id": "b8c9d0e1-f2a3-4567-bcde-890123456789",
  "threat_code": "TH-IAM-001",
  "dataset_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "outcome": "succeeded",
  "actions_executed": [
    {
      "action_type": "notification",
      "sort_order": 1,
      "status": "succeeded",
      "duration_ms": 145,
      "config": { "channel": "slack", "severity": "critical", "template": "insider_threat_alert" },
      "result": { "message_id": "C05KXXX-1234567890.123456", "channel": "#security-ops" }
    },
    {
      "action_type": "evidence_report",
      "sort_order": 2,
      "status": "succeeded",
      "duration_ms": 512,
      "config": { "template": "security_incident", "include_datasets": true },
      "result": { "report_id": "RPT-2026-0142", "pages": 4 }
    },
    {
      "action_type": "create_task",
      "sort_order": 3,
      "status": "succeeded",
      "duration_ms": 88,
      "config": { "task_type": "control_remediation", "priority": "critical" },
      "result": { "task_id": "f2a3b4c5-d6e7-8901-fabc-234567890126", "task_code": "TASK-2026-0389" }
    }
  ],
  "policy_version": 3,
  "created_at": "2026-03-16T09:42:24Z"
}
```

---

### GET /api/v1/sb/policies/{policy_id}/executions

Policy-specific execution history. Convenience alias for `GET /policy-executions?policy_id={policy_id}`.

**Permission:** `sandbox.view`

Query params are identical to `GET /policy-executions`, minus `policy_id`.

**Response** `200 OK` — same shape as `GET /policy-executions`

---

## Audit Events

All execution events are written to the unified audit system (`40_aud_events` + `41_dtl_audit_event_properties`).

| Event Type | Entity | Key Properties |
| --- | --- | --- |
| `signal_executed` | `sandbox_run` | signal_id, signal_code, dataset_id, result_code, execution_time_ms |
| `signal_batch_executed` | `sandbox_run` | signal_ids, dataset_id, run_count, results_summary |
| `threat_evaluated` | `threat_evaluation` | threat_type_id, threat_code, triggered, signal_results |
| `policy_executed` | `policy_execution` | policy_id, policy_code, outcome, action_count |
| `policy_execution_skipped` | `policy_execution` | policy_id, policy_code, reason: cooldown, last_executed_at |

---

## Cross-References

| Related Resource | Endpoint |
| --- | --- |
| Signal management | `GET /api/v1/sb/signals/{id}` — see `22_sandbox_signals.md` |
| Dataset management | `GET /api/v1/sb/datasets/{id}` — see `21_sandbox_datasets.md` |
| Threat type management | `GET /api/v1/sb/threat-types/{id}` — see `23_sandbox_threat_types.md` |
| Policy management | `GET /api/v1/sb/policies/{id}` — see `24_sandbox_policies.md` |
| Live session execution | `POST /api/v1/sb/live-sessions` — see `27_sandbox_live_sessions.md` |
| Promotion to GRC | `POST /api/v1/sb/signals/{id}/promote` — see `28_sandbox_libraries.md` |
