# Sandbox SSF Transmitter — Delivery Worker and Outbox API

**Base path:** `/api/v1/sb/ssf`
**Auth:** Bearer JWT required on all endpoints
**Multi-tenant:** `org_id` query parameter required on all endpoints
**Standards:** SET RFC 8417, SSF 1.0, OpenID Shared Signals Framework

---

## Overview

This document covers the **transmitter-side** internals of the Shared Signals Framework (SSF) implementation: the outbox pipeline, delivery worker, retry behaviour, delivery log querying, and SET generation mechanics. For stream management (create/list/configure/subject management), see `29_sandbox_ssf.md`.

K-Control acts as an SSF Transmitter. When a sandbox signal execution produces a `fail` or `warning` result, the engine routes the result through a SET generation pipeline and places the signed JWT into the outbox (`72_trx_ssf_outbox`). A background delivery worker drains the outbox, making push deliveries and serving poll accumulations.

### Transmitter Data Flow

```text
Signal execution → result: fail | warning
    → SET generation (outbox writer)
        → match streams by event_type URI + subject_identifier
        → sign JWT (RS256, kid=kcontrol-sandbox-key-v1)
        → insert row into 72_trx_ssf_outbox (status=pending)
    → background delivery worker
        → push streams: POST signed JWT to receiver_url
            → HTTP 2xx: mark delivered, write 73_trx_ssf_delivery_log
            → non-2xx:  retry with exponential backoff (3 attempts)
            → 3 failures: mark failed, auto-pause stream, emit audit event
        → poll streams: SET stays in outbox until receiver fetches + acks
```

---

## DB Tables

| Table | Schema | Type | Description |
| --- | --- | --- | --- |
| `70_fct_ssf_streams` | `15_sandbox` | Fact | Stream configuration (delivery method, receiver URL, events_requested, status) |
| `71_dtl_ssf_stream_subjects` | `15_sandbox` | Detail | Subjects (resources) attached to each stream — filters SET routing |
| `72_trx_ssf_outbox` | `15_sandbox` | Transaction | Pending SETs awaiting delivery; the outbox table drained by the delivery worker |
| `73_trx_ssf_delivery_log` | `15_sandbox` | Transaction | Per-attempt delivery audit log with HTTP status codes and timing |

### Key columns — `72_trx_ssf_outbox`

| Column | Type | Description |
| --- | --- | --- |
| `id` | UUID | Primary key |
| `tenant_key` | TEXT | Tenant isolation |
| `stream_id` | UUID FK → `70_fct_ssf_streams` | Target stream |
| `jti` | UUID | SET JWT ID (unique per SET) |
| `signed_jwt` | TEXT | Full signed compact JWT string |
| `event_type_uri` | TEXT | The `events` key URI this SET carries |
| `subject_format` | TEXT | SSF subject identifier format (iss_sub, email, etc.) |
| `subject_identifier` | TEXT | Subject value (e.g. IAM user ARN, email, org identifier) |
| `delivery_status` | TEXT | pending / delivering / delivered / failed / acknowledged |
| `attempt_count` | INT | Number of delivery attempts made (push) |
| `next_attempt_at` | TIMESTAMPTZ | Scheduled time for next push attempt (NULL for poll) |
| `created_at` | TIMESTAMPTZ | When the SET was queued |
| `delivered_at` | TIMESTAMPTZ | When delivery succeeded (nullable) |
| `source_run_id` | UUID FK → `25_fct_sandbox_runs` | Signal execution run that triggered this SET (nullable) |

### Key columns — `73_trx_ssf_delivery_log`

| Column | Type | Description |
| --- | --- | --- |
| `id` | UUID | Primary key |
| `outbox_id` | UUID FK → `72_trx_ssf_outbox` | Outbox entry this attempt belongs to |
| `stream_id` | UUID FK → `70_fct_ssf_streams` | Stream that was targeted |
| `jti` | UUID | SET JWT ID |
| `attempt_number` | INT | 1-based attempt counter |
| `delivery_method` | TEXT | push / poll |
| `http_status_code` | INT | HTTP response code (nullable for network errors) |
| `response_body` | TEXT | First 1000 chars of receiver response (nullable) |
| `error_detail` | TEXT | Network or TLS error detail (nullable) |
| `duration_ms` | INT | Time taken for the delivery attempt in milliseconds |
| `outcome` | TEXT | delivered / failed / network_error |
| `attempted_at` | TIMESTAMPTZ | When this attempt was made |

---

## Outbox Delivery Worker

The delivery worker is an async background task registered in the application lifespan (`backend/01_core/application.py`), following the same pattern as `notification_queue_processor`.

### Worker Behaviour

| Phase | Description |
| --- | --- |
| **Polling interval** | Every 5 seconds — queries `72_trx_ssf_outbox` for `delivery_status = pending` AND `next_attempt_at <= now()` |
| **Batch size** | Up to 100 SETs per cycle |
| **Push delivery** | HTTP POST to `receiver_url`, headers: `Content-Type: application/secevent+jwt`, `Authorization: {authorization_header}` |
| **Success condition** | HTTP 2xx response from receiver |
| **Failure condition** | HTTP non-2xx, TLS error, connection timeout, DNS failure |
| **Retry schedule** | Attempt 1: immediate; Attempt 2: +30 seconds; Attempt 3: +2 minutes; then mark `failed` |
| **Auto-pause on failure** | After 3 consecutive failed delivery attempts on a stream, the stream is transitioned to `paused` and `ssf_stream_auto_paused` audit event is emitted |
| **Poll streams** | No active delivery; SETs remain in outbox with `delivery_status = pending` until the receiver calls `GET /ssf/poll/{stream_id}` and acknowledges |

### Retry Schedule Details

| Attempt | Delay from previous | `next_attempt_at` |
| --- | --- | --- |
| 1 (initial) | — | Immediately (queued at creation) |
| 2 | 30 seconds | `attempted_at + 30s` |
| 3 | 2 minutes | `attempted_at + 2m` |
| 4+ | Not retried | `delivery_status = failed`, stream auto-paused |

---

## SET Generation

When a sandbox signal execution completes with `result_code = fail` or `warning`, the SET generator runs as part of the post-execution pipeline:

1. Load streams with `delivery_status_code = enabled` that have requested the signal's event type URI
2. For each stream: check `71_dtl_ssf_stream_subjects` — if subjects exist, only queue SETs for matching subjects; if no subjects configured, queue for all
3. Build JWT payload (see SET format in `29_sandbox_ssf.md`)
4. Sign with RS256 using the sandbox signing key (`kcontrol-sandbox-key-v1` from the key store)
5. Insert into `72_trx_ssf_outbox` with `delivery_status = pending`

### Event Type URI Derivation

| Signal EAV Property | Outcome |
| --- | --- |
| `caep_event_type` set (e.g. `credential-change`) | `https://schemas.openid.net/secevent/caep/event-type/{caep_event_type}` |
| `risc_event_type` set (e.g. `credential-compromise`) | `https://schemas.openid.net/secevent/risc/event-type/{risc_event_type}` |
| Neither set | `https://schemas.kcontrol.io/secevent/sandbox/event-type/{signal_code}` |

Only streams that include this derived URI in their `events_requested` array will receive the SET.

---

## Outbox Endpoints

### GET /api/v1/sb/ssf/outbox

List outbox entries with filtering. Use to monitor pending and failed SETs, diagnose delivery issues, or audit what has been queued.

**Permission:** `sandbox.view`

**Query params**

| Param | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `org_id` | UUID | yes | — | Owning organisation |
| `stream_id` | UUID | no | — | Filter to a specific stream |
| `delivery_status` | string | no | — | pending / delivering / delivered / failed / acknowledged |
| `event_type_uri` | string | no | — | Filter by exact event type URI |
| `date_from` | ISO8601 | no | — | Filter created on or after |
| `date_to` | ISO8601 | no | — | Filter created on or before |
| `sort_by` | string | no | `created_at` | created_at / next_attempt_at |
| `sort_dir` | string | no | `desc` | asc / desc |
| `limit` | int | no | 100 | 1–500 |
| `offset` | int | no | 0 | >= 0 |

**Response** `200 OK`

```json
{
  "items": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "stream_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "stream_delivery_method": "push",
      "jti": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "event_type_uri": "https://schemas.openid.net/secevent/caep/event-type/credential-change",
      "subject_format": "iss_sub",
      "subject_identifier": "AIDABC123DEF456GHI789",
      "delivery_status": "pending",
      "attempt_count": 2,
      "next_attempt_at": "2026-03-16T10:05:30Z",
      "source_run_id": "d4e5f6a7-b8c9-0123-defa-234567890123",
      "created_at": "2026-03-16T10:00:00Z",
      "delivered_at": null
    },
    {
      "id": "e5f6a7b8-c9d0-1234-efab-567890123456",
      "stream_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "stream_delivery_method": "push",
      "jti": "f6a7b8c9-d0e1-2345-fabc-678901234567",
      "event_type_uri": "https://schemas.kcontrol.io/secevent/sandbox/event-type/iam_mfa_disabled_check",
      "subject_format": "iss_sub",
      "subject_identifier": "AIDAJK012LMN345OPQ678",
      "delivery_status": "delivered",
      "attempt_count": 1,
      "next_attempt_at": null,
      "source_run_id": "d4e5f6a7-b8c9-0123-defa-234567890124",
      "created_at": "2026-03-16T09:55:00Z",
      "delivered_at": "2026-03-16T09:55:02Z"
    }
  ],
  "total": 47
}
```

**Error responses**

| Status | Description |
| --- | --- |
| 401 | Missing or invalid Bearer token |
| 403 | Missing `sandbox.view` permission |

---

### GET /api/v1/sb/ssf/outbox/{id}

Get a single outbox entry with full signed JWT, all delivery attempts, and source run linkage.

**Permission:** `sandbox.view`

**Query params**

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

**Response** `200 OK`

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "stream_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "stream_delivery_method": "push",
  "stream_receiver_url": "https://siem.example.com/api/ssf/ingest",
  "jti": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "signed_jwt": "eyJhbGciOiJSUzI1NiIsInR5cCI6InNlY2V2ZW50K2p3dCIsImtpZCI6Imtjb250cm9sLXNhbmRib3gta2V5LXYxIn0.eyJpc3MiOiJodHRwczovL2tjb250cm9sLmlvIiwiaWF0IjoxNzQyMTIzMzQ0LCJqdGkiOiJjM2Q0ZTVmNi1hN2I4LTkwMTItY2RlZi0xMjM0NTY3ODkwMTIiLCJhdWQiOiJodHRwczovL3NpZW0uZXhhbXBsZS5jb20vYXBpL3NzZi9pbmdlc3QiLCJldmVudHMiOnt9fQ.signature",
  "event_type_uri": "https://schemas.openid.net/secevent/caep/event-type/credential-change",
  "subject_format": "iss_sub",
  "subject_identifier": "AIDABC123DEF456GHI789",
  "delivery_status": "pending",
  "attempt_count": 2,
  "next_attempt_at": "2026-03-16T10:05:30Z",
  "source_run_id": "d4e5f6a7-b8c9-0123-defa-234567890123",
  "source_signal_code": "iam_key_rotation_check",
  "created_at": "2026-03-16T10:00:00Z",
  "delivered_at": null,
  "delivery_attempts": [
    {
      "id": "g7h8i9j0-k1l2-3456-mnop-789012345678",
      "attempt_number": 1,
      "http_status_code": 503,
      "response_body": "{\"error\":\"Service Unavailable\"}",
      "error_detail": null,
      "duration_ms": 1201,
      "outcome": "failed",
      "attempted_at": "2026-03-16T10:00:01Z"
    },
    {
      "id": "h8i9j0k1-l2m3-4567-nopq-890123456789",
      "attempt_number": 2,
      "http_status_code": 503,
      "response_body": "{\"error\":\"Service Unavailable\"}",
      "error_detail": null,
      "duration_ms": 887,
      "outcome": "failed",
      "attempted_at": "2026-03-16T10:00:31Z"
    }
  ]
}
```

**Error responses**

| Status | Description |
| --- | --- |
| 401 | Missing or invalid Bearer token |
| 403 | Missing `sandbox.view` permission |
| 404 | Outbox entry not found or not in tenant scope |

---

## Delivery Log Endpoints

### GET /api/v1/sb/ssf/delivery-log

List delivery attempt records across all streams. Use for monitoring delivery health, SLA tracking, and diagnosing receiver-side failures.

**Permission:** `sandbox.view`

**Query params**

| Param | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `org_id` | UUID | yes | — | Owning organisation |
| `stream_id` | UUID | no | — | Filter by stream |
| `outcome` | string | no | — | delivered / failed / network_error |
| `date_from` | ISO8601 | no | — | Filter on or after |
| `date_to` | ISO8601 | no | — | Filter on or before |
| `sort_by` | string | no | `attempted_at` | attempted_at |
| `sort_dir` | string | no | `desc` | asc / desc |
| `limit` | int | no | 100 | 1–500 |
| `offset` | int | no | 0 | >= 0 |

**Response** `200 OK`

```json
{
  "items": [
    {
      "id": "g7h8i9j0-k1l2-3456-mnop-789012345678",
      "outbox_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "stream_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "jti": "c3d4e5f6-a7b8-9012-cdef-123456789012",
      "attempt_number": 1,
      "delivery_method": "push",
      "http_status_code": 503,
      "error_detail": null,
      "duration_ms": 1201,
      "outcome": "failed",
      "attempted_at": "2026-03-16T10:00:01Z"
    },
    {
      "id": "i9j0k1l2-m3n4-5678-opqr-901234567890",
      "outbox_id": "e5f6a7b8-c9d0-1234-efab-567890123456",
      "stream_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "jti": "f6a7b8c9-d0e1-2345-fabc-678901234567",
      "attempt_number": 1,
      "delivery_method": "push",
      "http_status_code": 200,
      "error_detail": null,
      "duration_ms": 134,
      "outcome": "delivered",
      "attempted_at": "2026-03-16T09:55:02Z"
    }
  ],
  "total": 312
}
```

---

### GET /api/v1/sb/ssf/streams/{stream_id}/delivery-log

Stream-specific delivery log. Convenience alias for `GET /ssf/delivery-log?stream_id={stream_id}`.

**Permission:** `sandbox.view`

Query params are identical to `GET /ssf/delivery-log`, minus `stream_id`.

**Response** `200 OK` — same shape as `GET /ssf/delivery-log`

---

## Retry and Recovery Endpoints

### POST /api/v1/sb/ssf/outbox/{id}/retry

Manually trigger a retry of a failed outbox entry. Resets `attempt_count` to 0 and `delivery_status` to `pending`, scheduling an immediate delivery attempt. Useful for recovering after receiver downtime without waiting for auto-resume.

**Permission:** `sandbox.create`

**Query params**

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

**Response** `200 OK`

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "jti": "c3d4e5f6-a7b8-9012-cdef-123456789012",
  "delivery_status": "pending",
  "attempt_count": 0,
  "next_attempt_at": "2026-03-16T11:00:00Z"
}
```

**Business rules:**
- Only entries with `delivery_status = failed` can be manually retried.
- Retrying a SET does not re-enable a paused stream. Re-enable the stream separately via `PATCH /ssf/streams/{stream_id}/status`.
- If the stream is still paused, the retry will be queued but not delivered until the stream is re-enabled.

**Error responses**

| Status | Description |
| --- | --- |
| 403 | Missing `sandbox.create` permission |
| 404 | Outbox entry not found or not in tenant scope |
| 409 | Entry is not in `failed` status — cannot retry |

---

### POST /api/v1/sb/ssf/streams/{stream_id}/purge-outbox

Purge all pending SETs from a stream's outbox. Use when a stream has accumulated a large backlog that is no longer relevant (e.g. after a long receiver outage where stale security events should not be delivered).

**Permission:** `sandbox.create`

**Query params**

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

**Request body** (optional)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `delivery_status` | string | no | Restrict purge to: `pending` / `failed` / `all` (default: `all`) |
| `older_than_hours` | int | no | Only purge entries older than N hours |

```json
{
  "delivery_status": "pending",
  "older_than_hours": 24
}
```

**Response** `200 OK`

```json
{
  "stream_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "purged_count": 183,
  "purged_at": "2026-03-16T11:00:00Z"
}
```

**Error responses**

| Status | Description |
| --- | --- |
| 403 | Missing `sandbox.create` permission |
| 404 | Stream not found |

---

## Stream Delivery Statistics

### GET /api/v1/sb/ssf/streams/{stream_id}/stats

Delivery health summary for a stream. Aggregates from `73_trx_ssf_delivery_log` for the requested time window.

**Permission:** `sandbox.view`

**Query params**

| Param | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `org_id` | UUID | yes | — | Owning organisation |
| `days` | int | no | 7 | Lookback window in days (1–90) |

**Response** `200 OK`

```json
{
  "stream_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "window_days": 7,
  "total_sets_queued": 248,
  "total_sets_delivered": 231,
  "total_sets_failed": 12,
  "total_sets_pending": 5,
  "delivery_success_rate_pct": 93.1,
  "avg_delivery_duration_ms": 187,
  "p95_delivery_duration_ms": 634,
  "last_delivery_at": "2026-03-16T10:42:00Z",
  "last_failure_at": "2026-03-16T10:00:01Z",
  "auto_paused_count": 1,
  "events_by_type": [
    {
      "event_type_uri": "https://schemas.openid.net/secevent/caep/event-type/credential-change",
      "count": 142,
      "delivered": 135,
      "failed": 7
    },
    {
      "event_type_uri": "https://schemas.kcontrol.io/secevent/sandbox/event-type/iam_mfa_disabled_check",
      "count": 106,
      "delivered": 96,
      "failed": 5
    }
  ]
}
```

---

## Outbox Status Values

| Status | Description | Next State |
| --- | --- | --- |
| `pending` | Queued, awaiting delivery worker pickup | `delivering` |
| `delivering` | Worker is actively attempting delivery | `delivered` or `pending` (for retry) |
| `delivered` | Successfully delivered to receiver (push) or acknowledged by receiver (poll) | Terminal |
| `failed` | All retry attempts exhausted | Terminal (manual retry resets to `pending`) |
| `acknowledged` | Poll-mode SET was fetched and acknowledged via the `?ack=` param | Terminal |

---

## Delivery Worker Health

### GET /api/v1/sb/ssf/worker-status

Returns the health and lag metrics of the outbox delivery worker. Useful for operations monitoring.

**Permission:** `sandbox.view`

**Query params**

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `org_id` | UUID | yes | Owning organisation |

**Response** `200 OK`

```json
{
  "worker_running": true,
  "last_poll_at": "2026-03-16T10:59:55Z",
  "pending_set_count": 5,
  "oldest_pending_age_seconds": 42,
  "sets_delivered_last_minute": 17,
  "streams_auto_paused_total": 1,
  "worker_cycle_ms": 5000
}
```

**Notes:**
- `oldest_pending_age_seconds` is the age of the oldest pending SET across all push streams in the tenant scope. High values indicate delivery backlog.
- `worker_cycle_ms` is the polling interval configured in the worker; default is 5000ms.
- `worker_running: false` indicates the background task failed to start or crashed. This should trigger an alert.

---

## Cache Behaviour

| Cache Key | TTL | Cached By | Invalidated By |
| --- | --- | --- | --- |
| `ssf:streams:{org_id}` | 5 min | `GET /ssf/streams` | create stream, update stream, update status, delete stream |
| `ssf:stream:{stream_id}` | 5 min | `GET /ssf/streams/{id}` | PATCH stream, PATCH status, add/remove subject |
| `ssf:outbox:stats:{stream_id}` | 1 min | `GET /ssf/streams/{id}/stats` | Any new delivery log entry for the stream |

---

## Audit Events

All outbox mutations and delivery outcomes are written to the unified audit system (`40_aud_events` + `41_dtl_audit_event_properties`).

| Event Type | Entity | Key Properties |
| --- | --- | --- |
| `ssf_set_queued` | `ssf_outbox` | stream_id, jti, event_type_uri, subject_identifier, source_run_id |
| `ssf_set_delivered` | `ssf_outbox` | stream_id, jti, attempt_number, http_status_code, duration_ms |
| `ssf_set_delivery_failed` | `ssf_outbox` | stream_id, jti, attempt_number, http_status_code, error_detail |
| `ssf_set_all_attempts_exhausted` | `ssf_outbox` | stream_id, jti, attempt_count, last_http_status_code |
| `ssf_stream_auto_paused` | `ssf_stream` | stream_id, reason: delivery_failure, failed_jti |
| `ssf_set_manually_retried` | `ssf_outbox` | stream_id, jti, actor_id |
| `ssf_outbox_purged` | `ssf_stream` | stream_id, purged_count, delivery_status_filter, older_than_hours |
| `ssf_set_acknowledged` | `ssf_outbox` | stream_id, jti, acknowledged_by: poll |

---

## Error Responses

All management endpoints share this error response shape:

```json
{
  "detail": "Error description",
  "code": "machine_readable_code"
}
```

| Status | Code | Description |
| --- | --- | --- |
| 400 | `bad_request` | Malformed request body |
| 401 | `unauthorized` | Missing or invalid Bearer token |
| 403 | `forbidden` | Missing required permission |
| 404 | `not_found` | Outbox entry, stream, or delivery log entry not found in tenant scope |
| 409 | `conflict` | Operation not valid for current state (e.g. retry on non-failed entry) |
| 422 | `unprocessable` | Validation failure (e.g. unknown delivery_status value) |
| 429 | `rate_limited` | Too many requests |
| 500 | `internal_error` | Unexpected server error |

---

## Cross-References

| Related Resource | Endpoint |
| --- | --- |
| Stream management (create/configure/subjects/verify) | See `29_sandbox_ssf.md` |
| Signal execution that generates SETs | `POST /api/v1/sb/runs` — see `26_sandbox_execution.md` |
| Batch execution with threat evaluation | `POST /api/v1/sb/runs/batch` — see `26_sandbox_execution.md` |
| Signal EAV properties for CAEP/RISC mapping | See `23_sandbox_signals.md` — `caep_event_type`, `risc_event_type` keys |
| Discovery endpoint | `GET /.well-known/ssf-configuration` — see `29_sandbox_ssf.md` |
