# Sandbox Live Sessions API

**Base path:** `/api/v1/sb`
**Auth:** Bearer JWT required on all endpoints
**Multi-tenant:** `org_id` query parameter required on all endpoints

---

## Overview

Live Sessions provide a temporary real-time mode where a connector instance streams actual data into the sandbox. Raw data flows directly into ClickHouse. Attached signals execute automatically as data arrives. Triggered threats are evaluated, and enabled policies fire automatically. Sessions have a configurable duration (max 60 min) and auto-complete when the timer expires.

### Data Flow

```text
Connector Instance
    → raw data points → ClickHouse (sandbox_live_logs)
    → signals auto-execute → ALL results → ClickHouse (sandbox_signal_results)
    → fail/warning/error results → PostgreSQL (25_fct_sandbox_runs)
    → threats auto-evaluate → triggered threats → PostgreSQL (26_fct_threat_evaluations)
    → policies auto-fire → policy executions → PostgreSQL (27_fct_policy_executions)
```

### Session Lifecycle

```text
starting → active
         → error (connector failed to connect)

active → paused   (manual)
       → completed (timer expired or manual stop)
       → error     (connector disconnected)

paused → active    (manual resume)
       → completed (timer expired or manual stop)
```

Session expiry is managed by an async background task registered in the application lifespan (same pattern as `notification_queue_processor`). It polls every 30 seconds for sessions past their `expires_at` timestamp and transitions them to `completed`.

---

## Resource Limits

| Limit | Default | Notes |
| --- | --- | --- |
| Max concurrent sessions per workspace | 5 | Configurable via workspace entity setting |
| Max session duration | 60 min | Hard cap; not configurable |
| Default session duration | 30 min | Overridable per session at creation |
| Max data per session | 100 MB | Configurable via workspace entity setting |
| ClickHouse raw log retention | 30 days | TTL on `sandbox_live_logs` |
| ClickHouse signal result retention | 90 days | TTL on `sandbox_signal_results` |
| ClickHouse threat evaluation retention | 90 days | TTL on `sandbox_threat_evaluations` |

---

## DB Tables

PostgreSQL (session metadata and link tables):

| Table | Schema | Type | Description |
| --- | --- | --- | --- |
| `28_fct_live_sessions` | `15_sandbox` | Fact | Session records: status, connector ref, duration, stats, timestamps |
| `52_lnk_live_session_signals` | `15_sandbox` | Link | Signals attached to a session for auto-execution |
| `53_lnk_live_session_threat_types` | `15_sandbox` | Link | Threat types attached to a session for auto-evaluation |

ClickHouse (high-volume streaming data):

| Table | Partitioning | Retention | Description |
| --- | --- | --- | --- |
| `sandbox_live_logs` | By day (`toYYYYMMDD(received_at)`) | 30 days | Raw data points received from connector |
| `sandbox_signal_results` | By day | 90 days | All signal execution results (includes pass) |
| `sandbox_threat_evaluations` | By day | 90 days | Threat evaluation results during sessions |

### Key columns — `28_fct_live_sessions`

| Column | Type | Description |
| --- | --- | --- |
| `id` | UUID | Primary key |
| `tenant_key` | TEXT | Tenant isolation |
| `org_id` | UUID FK | Owning organisation |
| `workspace_id` | UUID FK | Owning workspace |
| `connector_instance_id` | UUID FK | Connector instance being streamed |
| `session_status_code` | TEXT | starting / active / paused / completed / expired / error |
| `duration_minutes` | INT | Configured session duration (1–60) |
| `started_at` | TIMESTAMPTZ | When session transitioned to `active` |
| `expires_at` | TIMESTAMPTZ | `started_at + duration_minutes` |
| `paused_at` | TIMESTAMPTZ | Timestamp of last pause (nullable) |
| `completed_at` | TIMESTAMPTZ | Timestamp of completion or stop (nullable) |
| `data_points_received` | BIGINT | Running count updated by background task |
| `bytes_received` | BIGINT | Running byte total updated by background task |
| `signals_executed` | BIGINT | Total signal executions during session |
| `threats_evaluated` | BIGINT | Total threat evaluations during session |
| `created_at` | TIMESTAMPTZ | Record creation timestamp |

---

## POST /api/v1/sb/live-sessions

Start a new live session. Connects to the specified connector instance and begins streaming data into ClickHouse.

**Permission:** `sandbox.execute`

Query parameters:

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

Request body fields:

| Field | Type | Required | Validation | Description |
| --- | --- | --- | --- | --- |
| `connector_instance_id` | UUID | yes | Must be active, health_status = healthy | Connector to stream from |
| `workspace_id` | UUID | yes | Must exist within org | Workspace that owns the session |
| `signal_ids` | UUID[] | no | All must exist in tenant scope | Signals to attach for auto-execution on arrival |
| `threat_type_ids` | UUID[] | no | All must exist in tenant scope | Threat types to auto-evaluate |
| `duration_minutes` | int | no | 1–60, default 30 | Session duration before auto-completion |

```json
{
  "connector_instance_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "workspace_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "signal_ids": [
    "c3d4e5f6-a7b8-9012-cdef-123456789012",
    "d4e5f6a7-b8c9-0123-defa-234567890123"
  ],
  "threat_type_ids": [
    "e5f6a7b8-c9d0-1234-efab-567890123456"
  ],
  "duration_minutes": 30
}
```

**Response** `201 Created`

```json
{
  "id": "f6a7b8c9-d0e1-2345-fabc-678901234567",
  "connector_instance_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "connector_name": "AWS Production (us-east-1)",
  "workspace_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "session_status": "active",
  "duration_minutes": 30,
  "started_at": "2026-03-16T10:00:00Z",
  "expires_at": "2026-03-16T10:30:00Z",
  "paused_at": null,
  "completed_at": null,
  "stats": {
    "data_points_received": 0,
    "bytes_received": 0,
    "signals_executed": 0,
    "threats_evaluated": 0
  },
  "attached_signals": [
    {
      "signal_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "signal_code": "iam_mfa_disabled_check",
      "attached_at": "2026-03-16T10:00:00Z"
    },
    {
      "signal_id": "d4e5f6a7-b8c9-0123-defa-234567890123",
      "signal_code": "iam_unusual_login_time_check",
      "attached_at": "2026-03-16T10:00:00Z"
    }
  ],
  "attached_threat_types": [
    {
      "threat_type_id": "e5f6a7b8-c9d0-1234-efab-567890123456",
      "threat_type_code": "TH-IAM-001",
      "attached_at": "2026-03-16T10:00:00Z"
    }
  ],
  "created_at": "2026-03-16T10:00:00Z"
}
```

Error responses:

| Status | Code | Description |
| --- | --- | --- |
| 400 | `bad_request` | Malformed request body |
| 401 | `unauthorized` | Missing or invalid Bearer token |
| 403 | `forbidden` | Missing `sandbox.execute` permission |
| 404 | `not_found` | Connector instance, workspace, or attached signal/threat not found |
| 409 | `concurrent_session_limit` | Workspace has reached max 5 concurrent active sessions |
| 422 | `connector_not_active` | Connector instance is not active or health check failed |
| 422 | `duration_exceeded` | `duration_minutes` exceeds 60 |
| 422 | `connector_not_healthy` | Connector health_status is not `healthy` |

---

## GET /api/v1/sb/live-sessions

List live sessions for the organisation.

**Permission:** `sandbox.view`

Query parameters:

| Param | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `org_id` | UUID | yes | — | Owning organisation |
| `workspace_id` | UUID | no | — | Filter by workspace |
| `connector_instance_id` | UUID | no | — | Filter by connector instance |
| `session_status` | string | no | — | starting / active / paused / completed / expired / error |
| `sort_by` | string | no | `created_at` | created_at / session_status |
| `sort_dir` | string | no | `desc` | asc / desc |
| `limit` | int | no | 50 | 1–100 |
| `offset` | int | no | 0 | >= 0 |

**Response** `200 OK`

```json
{
  "items": [
    {
      "id": "f6a7b8c9-d0e1-2345-fabc-678901234567",
      "connector_instance_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "connector_name": "AWS Production (us-east-1)",
      "workspace_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "session_status": "active",
      "duration_minutes": 30,
      "started_at": "2026-03-16T10:00:00Z",
      "expires_at": "2026-03-16T10:30:00Z",
      "stats": {
        "data_points_received": 1247,
        "bytes_received": 524288,
        "signals_executed": 312,
        "threats_evaluated": 89
      },
      "created_at": "2026-03-16T10:00:00Z"
    },
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567891",
      "connector_instance_id": "b2c3d4e5-f6a7-8901-bcde-f12345678902",
      "connector_name": "GitHub Org (acme-corp)",
      "workspace_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "session_status": "completed",
      "duration_minutes": 15,
      "started_at": "2026-03-15T14:00:00Z",
      "expires_at": "2026-03-15T14:15:00Z",
      "stats": {
        "data_points_received": 543,
        "bytes_received": 219136,
        "signals_executed": 108,
        "threats_evaluated": 22
      },
      "created_at": "2026-03-15T14:00:00Z"
    }
  ],
  "total": 12
}
```

---

## GET /api/v1/sb/live-sessions/{id}

Get full session detail including attached signals, attached threat types, and current stats.

**Permission:** `sandbox.view`

Path parameters:

| Param | Type | Description |
| --- | --- | --- |
| `id` | UUID | Session ID |

Query parameters:

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

**Response** `200 OK`

```json
{
  "id": "f6a7b8c9-d0e1-2345-fabc-678901234567",
  "connector_instance_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "connector_name": "AWS Production (us-east-1)",
  "connector_type_code": "aws",
  "workspace_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "session_status": "active",
  "duration_minutes": 30,
  "started_at": "2026-03-16T10:00:00Z",
  "expires_at": "2026-03-16T10:30:00Z",
  "paused_at": null,
  "completed_at": null,
  "stats": {
    "data_points_received": 1247,
    "bytes_received": 524288,
    "signals_executed": 312,
    "threats_evaluated": 89,
    "threats_triggered": 4,
    "policies_fired": 2
  },
  "attached_signals": [
    {
      "signal_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "signal_code": "iam_mfa_disabled_check",
      "signal_name": "IAM MFA Disabled Check",
      "attached_at": "2026-03-16T10:00:00Z"
    },
    {
      "signal_id": "d4e5f6a7-b8c9-0123-defa-234567890123",
      "signal_code": "iam_unusual_login_time_check",
      "signal_name": "IAM Unusual Login Time Check",
      "attached_at": "2026-03-16T10:00:00Z"
    }
  ],
  "attached_threat_types": [
    {
      "threat_type_id": "e5f6a7b8-c9d0-1234-efab-567890123456",
      "threat_type_code": "TH-IAM-001",
      "threat_type_name": "Insider Threat — Compromised IAM Account",
      "attached_at": "2026-03-16T10:00:00Z"
    }
  ],
  "created_at": "2026-03-16T10:00:00Z"
}
```

Error responses:

| Status | Description |
| --- | --- |
| 401 | Missing or invalid Bearer token |
| 403 | Missing `sandbox.view` permission |
| 404 | Session not found or not in tenant scope |

---

## GET /api/v1/sb/live-sessions/{id}/stream

Poll for real-time events using cursor-based pagination. Returns data points, signal execution results, and threat evaluations received since the given sequence number. Clients poll repeatedly by passing `after_sequence={next_sequence}` from the previous response.

**Permission:** `sandbox.view`

Query parameters:

| Param | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `org_id` | UUID | yes | — | Owning organisation |
| `after_sequence` | int | no | 0 | Return events strictly after this sequence number |
| `limit` | int | no | 50 | 1–200 events per request |
| `event_type` | string | no | all | data_point / signal_result / threat_evaluation |

**Response** `200 OK`

```json
{
  "session_id": "f6a7b8c9-d0e1-2345-fabc-678901234567",
  "session_status": "active",
  "events": [
    {
      "sequence": 1248,
      "event_type": "data_point",
      "timestamp": "2026-03-16T10:15:32.456Z",
      "data": {
        "resource_type": "iam_user",
        "resource_id": "AIDABC123DEF456GHI789",
        "payload": {
          "username": "alice.dev",
          "mfa_active": false,
          "last_login_utc": "2026-03-16T03:14:22Z",
          "login_country": "US"
        }
      }
    },
    {
      "sequence": 1249,
      "event_type": "signal_result",
      "timestamp": "2026-03-16T10:15:32.512Z",
      "data": {
        "run_id": "d4e5f6a7-b8c9-0123-defa-234567890124",
        "signal_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
        "signal_code": "iam_mfa_disabled_check",
        "result_code": "fail",
        "summary": "IAM user alice.dev has MFA disabled",
        "resource_id": "AIDABC123DEF456GHI789",
        "details": {
          "username": "alice.dev",
          "mfa_active": false
        }
      }
    },
    {
      "sequence": 1250,
      "event_type": "threat_evaluation",
      "timestamp": "2026-03-16T10:15:32.530Z",
      "data": {
        "evaluation_id": "a7b8c9d0-e1f2-3456-abcd-789012345679",
        "threat_type_id": "e5f6a7b8-c9d0-1234-efab-567890123456",
        "threat_type_code": "TH-IAM-001",
        "threat_type_name": "Insider Threat — Compromised IAM Account",
        "triggered": true,
        "resource_id": "AIDABC123DEF456GHI789",
        "signal_results": {
          "iam_mfa_disabled_check": "fail",
          "iam_unusual_login_time_check": "fail"
        }
      }
    }
  ],
  "next_sequence": 1251,
  "has_more": false
}
```

Stream polling pattern:

```text
1. Initial call:  GET /live-sessions/{id}/stream?after_sequence=0
2. Receive:       events[], next_sequence=1251, has_more=false
3. Wait 2 seconds
4. Next call:     GET /live-sessions/{id}/stream?after_sequence=1251
5. Repeat until session_status = completed | expired | error
```

An empty `events` array means no new data has arrived since the last poll. `has_more: true` means more events exist beyond the current `limit` — fetch again immediately without waiting.

Business rules: The stream endpoint reads from ClickHouse `sandbox_live_logs` and is eventually consistent with a typical lag of under 500ms. Sequence numbers are monotonically increasing per session and are never reused. Gaps may appear if events are dropped due to the 100 MB session data cap. After a session reaches `completed`, `expired`, or `error`, the stream endpoint continues to serve previously stored events but will not receive new ones.

---

## POST /api/v1/sb/live-sessions/{id}/pause

Pause a running session. The connector data stream stops but the session timer continues ticking toward `expires_at`.

**Permission:** `sandbox.execute`

Query parameters:

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

**Response** `200 OK`

```json
{
  "id": "f6a7b8c9-d0e1-2345-fabc-678901234567",
  "session_status": "paused",
  "paused_at": "2026-03-16T10:12:00Z",
  "expires_at": "2026-03-16T10:30:00Z"
}
```

Error responses:

| Status | Description |
| --- | --- |
| 404 | Session not found |
| 409 | Session is not in `active` status — cannot pause |

---

## POST /api/v1/sb/live-sessions/{id}/resume

Resume a paused session. Reconnects the data stream and resumes auto-execution of attached signals.

**Permission:** `sandbox.execute`

Query parameters:

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

**Response** `200 OK`

```json
{
  "id": "f6a7b8c9-d0e1-2345-fabc-678901234567",
  "session_status": "active",
  "resumed_at": "2026-03-16T10:14:00Z",
  "expires_at": "2026-03-16T10:30:00Z"
}
```

Error responses:

| Status | Description |
| --- | --- |
| 404 | Session not found |
| 409 | Session is not in `paused` status — cannot resume |
| 422 | Session has expired while paused — use stop instead |

---

## POST /api/v1/sb/live-sessions/{id}/stop

Manually stop a running or paused session. Disconnects the data stream and finalises the session. After stopping, the session data can be saved as a dataset.

**Permission:** `sandbox.execute`

Query parameters:

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

**Response** `200 OK`

```json
{
  "id": "f6a7b8c9-d0e1-2345-fabc-678901234567",
  "session_status": "completed",
  "completed_at": "2026-03-16T10:18:00Z",
  "stats": {
    "data_points_received": 1247,
    "bytes_received": 524288,
    "signals_executed": 312,
    "threats_evaluated": 89,
    "threats_triggered": 4,
    "policies_fired": 2
  }
}
```

Error responses:

| Status | Description |
| --- | --- |
| 404 | Session not found |
| 409 | Session is already `completed`, `expired`, or `error` |

---

## POST /api/v1/sb/live-sessions/{id}/attach-signal

Attach a signal to a running or paused session for immediate auto-execution on subsequent data points.

**Permission:** `sandbox.execute`

Query parameters:

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

Request body fields:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `signal_id` | UUID | yes | Signal to attach |

```json
{
  "signal_id": "e5f6a7b8-c9d0-1234-efab-567890123457"
}
```

**Response** `200 OK`

```json
{
  "session_id": "f6a7b8c9-d0e1-2345-fabc-678901234567",
  "signal_id": "e5f6a7b8-c9d0-1234-efab-567890123457",
  "signal_code": "iam_key_rotation_check",
  "attached_at": "2026-03-16T10:10:00Z"
}
```

Error responses:

| Status | Description |
| --- | --- |
| 404 | Session or signal not found |
| 409 | Signal already attached to this session |
| 409 | Session is not in `active` or `paused` status |

---

## POST /api/v1/sb/live-sessions/{id}/detach-signal

Detach a signal from a session. The signal will no longer execute on subsequent data points.

**Permission:** `sandbox.execute`

Query parameters:

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

Request body fields:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `signal_id` | UUID | yes | Signal to detach |

```json
{
  "signal_id": "e5f6a7b8-c9d0-1234-efab-567890123457"
}
```

**Response** `204 No Content`

Error responses:

| Status | Description |
| --- | --- |
| 404 | Session not found or signal not attached to session |

---

## POST /api/v1/sb/live-sessions/{id}/attach-threat

Attach a threat type to a running or paused session for auto-evaluation on each signal result batch.

**Permission:** `sandbox.execute`

Query parameters:

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

Request body fields:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `threat_type_id` | UUID | yes | Threat type to attach |

```json
{
  "threat_type_id": "f6a7b8c9-d0e1-2345-fabc-678901234568"
}
```

**Response** `200 OK`

```json
{
  "session_id": "f6a7b8c9-d0e1-2345-fabc-678901234567",
  "threat_type_id": "f6a7b8c9-d0e1-2345-fabc-678901234568",
  "threat_type_code": "TH-IAM-002",
  "attached_at": "2026-03-16T10:10:00Z"
}
```

Error responses:

| Status | Description |
| --- | --- |
| 404 | Session or threat type not found |
| 409 | Threat type already attached to this session |
| 409 | Session is not in `active` or `paused` status |

---

## POST /api/v1/sb/live-sessions/{id}/detach-threat

Detach a threat type from a session. The threat type will no longer be evaluated on subsequent signal batches.

**Permission:** `sandbox.execute`

Query parameters:

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

Request body fields:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `threat_type_id` | UUID | yes | Threat type to detach |

```json
{
  "threat_type_id": "f6a7b8c9-d0e1-2345-fabc-678901234568"
}
```

**Response** `204 No Content`

Error responses:

| Status | Description |
| --- | --- |
| 404 | Session not found or threat type not attached to session |

---

## POST /api/v1/sb/live-sessions/{id}/save-dataset

Save the captured session data as a permanent PostgreSQL dataset. Copies the ClickHouse raw event log into a new dataset record with `dataset_source_code = 'live_capture'`. The session must have ended (completed, expired, or manually stopped) before saving.

**Permission:** `sandbox.create`

Query parameters:

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

Request body fields:

| Field | Type | Required | Validation | Description |
| --- | --- | --- | --- | --- |
| `name` | string | yes | max 200 chars | Human-readable dataset name |
| `description` | string | no | max 2000 chars | Optional description |
| `workspace_id` | UUID | no | Defaults to session workspace | Workspace for the saved dataset |

```json
{
  "name": "AWS IAM Live Capture — March 16 Morning",
  "description": "30-minute live session from AWS Production connector, captured 1,247 IAM events",
  "workspace_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901"
}
```

**Response** `201 Created`

```json
{
  "dataset_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567892",
  "dataset_source_code": "live_capture",
  "session_id": "f6a7b8c9-d0e1-2345-fabc-678901234567",
  "name": "AWS IAM Live Capture — March 16 Morning",
  "description": "30-minute live session from AWS Production connector, captured 1,247 IAM events",
  "workspace_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "data_points": 1247,
  "bytes": 524288,
  "connector_type_code": "aws",
  "created_at": "2026-03-16T10:35:00Z"
}
```

Business rules: Session must be in `completed`, `expired`, or `error` status. Active or paused sessions cannot be saved. Sessions with `data_points_received = 0` cannot be saved. Saving does not delete ClickHouse data; it copies it into the permanent dataset store. The resulting dataset can be used with `POST /runs` or `POST /runs/batch` like any other dataset.

Error responses:

| Status | Description |
| --- | --- |
| 404 | Session not found |
| 409 | Session is still `active` or `paused` — stop it first |
| 409 | Session has no data points to save |

---

## Background Task

The live session processor runs as an async background task registered in the application lifespan (same pattern as `notification_queue_processor` in `backend/01_core/application.py`).

Responsibilities:

1. Session expiry — polls every 30 seconds for sessions whose `expires_at` is in the past; transitions them from `active` or `paused` to `completed`
2. Stats refresh — periodically queries ClickHouse aggregates and updates `data_points_received`, `bytes_received`, `signals_executed`, and `threats_evaluated` on `28_fct_live_sessions`
3. Connector health checks — detects disconnected connectors during active sessions and transitions them to `error` with an error detail message
4. Data cap enforcement — transitions sessions to `completed` when `bytes_received` exceeds the configured max data cap

---

## Audit Events

All session lifecycle changes are written to the unified audit system (`40_aud_events` + `41_dtl_audit_event_properties`).

| Event Type | Entity | Key Properties |
| --- | --- | --- |
| `live_session_started` | `live_session` | connector_instance_id, duration_minutes, workspace_id, signal_count, threat_type_count |
| `live_session_paused` | `live_session` | elapsed_minutes, data_points_received |
| `live_session_resumed` | `live_session` | paused_duration_seconds |
| `live_session_stopped` | `live_session` | data_points_received, bytes_received, signals_executed |
| `live_session_expired` | `live_session` | data_points_received, bytes_received, signals_executed |
| `live_session_error` | `live_session` | error_message, data_points_received |
| `live_session_signal_attached` | `live_session` | signal_id, signal_code |
| `live_session_signal_detached` | `live_session` | signal_id, signal_code |
| `live_session_threat_attached` | `live_session` | threat_type_id, threat_type_code |
| `live_session_threat_detached` | `live_session` | threat_type_id, threat_type_code |
| `live_session_dataset_saved` | `live_session` | dataset_id, data_points, bytes |

---

## Cross-References

| Related Resource | Endpoint |
| --- | --- |
| Connector instance management | `GET /api/v1/sb/connectors/{id}` — see `20_sandbox_connectors.md` |
| Signal execution (non-live) | `POST /api/v1/sb/runs` — see `26_sandbox_execution.md` |
| Dataset management | `GET /api/v1/sb/datasets/{id}` — see `21_sandbox_datasets.md` |
| Threat type expression trees | `GET /api/v1/sb/threat-types/{id}` — see `23_sandbox_threat_types.md` |
| Policy management | `GET /api/v1/sb/policies/{id}` — see `24_sandbox_policies.md` |
