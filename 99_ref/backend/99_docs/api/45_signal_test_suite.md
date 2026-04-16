# Signal Test Suite + Live Execution

**Priority:** P0 — validates signals against test data and live data
**Status:** New endpoints needed
**Module:** `backend/10_sandbox/04_signals/`
**Base path:** `/api/v1/sb`

---

## Overview

Two execution modes for signals:

1. **Test Suite** — Run signal against all test cases, compare actual vs expected output. Shows pass/fail comparison report.
2. **Live Execution** — Run signal against latest collected properties from a real connector. Production mode.

---

## Test Suite Execution

### POST `/api/v1/sb/signals/{id}/test-suite`

**Permission:** `sandbox.execute`
**Query params:** `org_id` (required)

Run the signal against its test dataset. For each test case, execute the signal and compare actual output against expected output.

**Request:**

```json
{
  "test_dataset_id": "uuid",
  "configurable_args_override": {}
}
```

If `test_dataset_id` omitted, uses the signal's linked test dataset (from `test_dataset_id` EAV property).

**Response:** `200 OK`

```json
{
  "signal_id": "uuid",
  "signal_code": "check_dormant_accounts",
  "test_dataset_id": "uuid",
  "total_cases": 15,
  "passed": 13,
  "failed": 2,
  "execution_time_ms": 4520,
  "cases": [
    {
      "case_id": "tc_001",
      "scenario_name": "All roles active within threshold",
      "status": "passed",
      "expected": {
        "result": "pass",
        "summary": "All 2 login-capable roles active within 90 days"
      },
      "actual": {
        "result": "pass",
        "summary": "All 2 login-capable roles have authenticated within 90 days"
      },
      "result_match": true,
      "summary_match": true,
      "details_match": true,
      "execution_time_ms": 280
    },
    {
      "case_id": "tc_003",
      "scenario_name": "No activity data for some roles",
      "status": "failed",
      "expected": {
        "result": "warning",
        "summary": "2 roles have no activity data"
      },
      "actual": {
        "result": "fail",
        "summary": "2 roles exceeded dormant threshold"
      },
      "result_match": false,
      "summary_match": false,
      "details_match": false,
      "diff": {
        "result": {"expected": "warning", "actual": "fail"},
        "summary": {"expected": "2 roles have no activity data", "actual": "2 roles exceeded dormant threshold"}
      },
      "execution_time_ms": 310
    }
  ]
}
```

### Comparison Logic

For each test case:

| Field | Comparison |
|-------|------------|
| `result` | Exact match: `expected.result == actual.result` |
| `summary` | Fuzzy: not compared for pass/fail (informational only) |
| `details` | Structural: same number of detail items, each `check` name exists, each `status` matches |

A test case **passes** if `result` matches AND `details` statuses match. Summary is informational.

---

## Live Execution

### POST `/api/v1/sb/signals/{id}/execute-live`

**Permission:** `sandbox.execute`
**Query params:** `org_id` (required)

Run signal against latest collected data from a real connector.

**Request:**

```json
{
  "connector_instance_id": "uuid",
  "configurable_args": {
    "dormant_days": 90,
    "exclude_system_roles": true
  }
}
```

**How it works:**

1. Fetch latest asset snapshots for the connector from `55_fct_assets` + `54_dtl_asset_properties`
2. Group by asset type → build dataset JSON: `{"postgres_roles": [...], "postgres_tables": [...], ...}`
3. Execute signal with the built dataset + configurable_args
4. Store result in `25_trx_sandbox_runs` with `execution_source='live'`
5. Return full execution result

**Response:** `200 OK`

```json
{
  "signal_id": "uuid",
  "signal_code": "check_dormant_accounts",
  "connector_instance_id": "uuid",
  "execution_source": "live",
  "result": {
    "result": "fail",
    "summary": "3 of 12 login-capable roles are dormant (>90 days inactive)",
    "details": [
      {"check": "old_service_acct", "status": "fail", "message": "Last activity 180 days ago"},
      {"check": "temp_user", "status": "fail", "message": "Last activity 95 days ago"},
      {"check": "legacy_admin", "status": "fail", "message": "No activity data found"}
    ],
    "metadata": {}
  },
  "execution_time_ms": 450,
  "dataset_snapshot": {
    "asset_count": 12,
    "asset_types": ["postgres_role", "postgres_stat_activity"],
    "collected_at": "2026-03-20T06:00:00Z"
  }
}
```

---

## Files to Create/Modify

| File | Change |
|------|--------|
| `backend/10_sandbox/04_signals/service.py` | Add `run_test_suite()` and `execute_live()` methods |
| `backend/10_sandbox/04_signals/schemas.py` | Add `TestSuiteRequest`, `TestSuiteResultResponse`, `ExecuteLiveRequest`, `ExecuteLiveResponse` |
| `backend/10_sandbox/04_signals/router.py` | Add `POST /{id}/test-suite` and `POST /{id}/execute-live` endpoints |
| `backend/10_sandbox/04_signals/repository.py` | Add method to fetch latest asset properties by connector_instance_id |

---

## Verification

1. Create signal with test dataset → run test suite → verify per-case comparison report
2. Test case with mismatched result → verify shows diff with expected vs actual
3. Execute live against PG connector → verify dataset built from latest snapshots
4. Verify run stored in `25_trx_sandbox_runs` with `execution_source='live'`
5. Frontend: test suite results table with green/red per case, diff expansion
