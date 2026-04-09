# K-Protect Server API Reference

> For backend engineers integrating with the K-Protect API, and for those building the K-Protect server itself.  
> All endpoints require a valid API key. Production endpoints use HMAC request signing (see [WIRE_PROTOCOL.md](WIRE_PROTOCOL.md)).

---

## Base URL

| Environment | Base URL |
|---|---|
| Production | `https://api.kprotect.io` |
| Staging | `https://api-staging.kprotect.io` |
| Local dev | `http://localhost:8000` |

---

## Authentication

All requests include:
```
X-KP-API-Key: kp_live_abc...
```

Production requests also include:
```
X-KP-Sig: v1={hmac_hex}
```

Server validates the API key on every request. HMAC is validated on production keys only (keys prefixed `kp_live_`). Test keys (`kp_test_`) skip HMAC validation.

---

## POST /v1/behavioral/ingest

Primary ingestion endpoint. Accepts `BehavioralBatch`, `CriticalActionBatch`, `KeepaliveBatch`, and `SessionEventBatch`.

### Request

```
POST /v1/behavioral/ingest
Content-Type: application/octet-stream
Content-Encoding: gzip
X-KP-API-Key: kp_live_abc...
X-KP-Session: {session_id}
X-KP-Device: {device_uuid}
X-KP-SDK-Version: web/1.0.0

{gzip-compressed JSON body}
```

### Response 200

```json
{
  "ok": true,
  "data": {
    "batch_id": "550e8400-e29b-41d4-a716-446655440000",
    "processed_at": 1712620800000,
    "drift_score": 0.12,
    "confidence": 0.87,
    "signal_scores": {
      "keystroke": 0.08,
      "pointer": 0.15,
      "credential": 0.11
    },
    "action": "allow",
    "auth_state": {
      "session_trust": "trusted",
      "device_known": true,
      "baseline_age_days": 47,
      "baseline_quality": "strong"
    },
    "alerts": []
  }
}
```

### Response 400 — Missing user_hash

```json
{
  "ok": false,
  "error": {
    "code": "MISSING_USER_HASH",
    "message": "Batch must include user_hash. Ensure username was captured before transmitting."
  }
}
```

### Response 429 — Rate limited

```json
{
  "ok": false,
  "error": {
    "code": "RATE_LIMITED",
    "message": "Too many requests.",
    "retry_after_ms": 4000
  }
}
```

### Server processing logic

On receipt:
1. Validate API key → 401 on failure
2. Validate HMAC (production keys only) → 401 on failure
3. Validate `batch_id` uniqueness against 24h window → 400 `INVALID_BATCH_ID`
4. Validate `sent_at` within ±5 min of server time → 400 `BATCH_TOO_OLD`
5. Validate `user_hash` present → 400 `MISSING_USER_HASH`
6. If `automation_score` is present on a `behavioral` batch, feed it to the bot classifier alongside drift scoring
7. Route by `type`:
   - `behavioral` → FeatureIngestor → DriftScorer → return `DriftScoreResponse`
   - `critical_action` → CriticalActionHandler → DriftScorer (full pass) → AlertEngine → return `DriftScoreResponse`
   - `keepalive` → SessionTracker.heartbeat() → return `{ok: true, data: {pulse: n}}`
   - `session_start` → SessionTracker.open() → return `SessionMetadataResponse`
   - `session_end` → SessionTracker.close() → return `{ok: true}`
8. Write audit log entry (async, non-blocking to response)

**Batch field notes:**

- `device_uuid` and `origin_hash` are **required** on the first `behavioral`/`keepalive` batch and on all `session_start`/`session_end` batches. They are **optional** on subsequent `behavioral`/`keepalive` batches within the same session (the server uses the values from the first batch).
- `automation_score` (0.0--1.0) may be present on `behavioral` batches when device fingerprinting is enabled. Use it as an input to the bot classifier alongside drift scoring.
- `std_dev` fields in signal aggregates (keystroke dwell/flight, pointer acceleration, sensor accelerometer) are `null` when `sample_count < 2`. The server MUST handle null gracefully (treat as insufficient data, not zero variance).
- `sent_at` on all batch types is a **monotonic timestamp** (`sessionStartEpoch + performance.now()`), not `Date.now()`. Clock skew validation (the +/-5 min check) should account for this.

---

## GET /v1/session/{session_id}

Retrieve live session state. Used by fraud analysts and backend fraud pipelines.

### Request

```
GET /v1/session/550e8400-e29b-41d4-a716-446655440000
X-KP-API-Key: kp_live_abc...
```

### Response 200

```json
{
  "ok": true,
  "data": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_hash": "a665a45920422f9d417e4867efdc4fb8...",
    "device_uuid": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "started_at": 1712620000000,
    "last_pulse_at": 1712620750000,
    "pulse_count": 150,
    "page_class": "normal",
    "url_path": "/dashboard",
    "auth_state": "trusted",
    "current_drift_score": 0.12,
    "baseline_quality": "strong",
    "active": true
  }
}
```

### Response 404

```json
{
  "ok": false,
  "error": { "code": "SESSION_NOT_FOUND", "message": "Session ID not found or expired." }
}
```

---

## GET /v1/user/{user_hash}/drift-history

Retrieve drift score history for a user. For fraud analysis and baseline review.

### Request

```
GET /v1/user/a665a459.../drift-history?limit=50&since=1712534400000
X-KP-API-Key: kp_live_abc...
```

### Query parameters

| Param | Type | Default | Description |
|---|---|---|---|
| `limit` | integer | 50 | Max records to return (max 500) |
| `since` | integer | 7 days ago | Unix ms lower bound |
| `until` | integer | now | Unix ms upper bound |
| `action_filter` | string | none | Filter by action: `allow`, `monitor`, `challenge`, `block` |

### Response 200

```json
{
  "ok": true,
  "data": {
    "user_hash": "a665a459...",
    "baseline_quality": "strong",
    "baseline_age_days": 47,
    "records": [
      {
        "session_id": "550e8400...",
        "pulse": 42,
        "batch_id": "...",
        "recorded_at": 1712620800000,
        "drift_score": 0.12,
        "action": "allow",
        "page_class": "normal",
        "signal_scores": { "keystroke": 0.08, "pointer": 0.15 }
      }
    ],
    "total": 312,
    "returned": 50
  }
}
```

---

## POST /v1/user/{user_hash}/baseline/reset

Force a baseline reset for a user. Called when account is handed to a new legitimate user, or after a confirmed account takeover is resolved.

### Request

```
POST /v1/user/a665a459.../baseline/reset
X-KP-API-Key: kp_live_abc...
Content-Type: application/json

{
  "reason": "account_recovery",
  "operator_id": "fraud-analyst-7"
}
```

### Response 200

```json
{
  "ok": true,
  "data": {
    "user_hash": "a665a459...",
    "baseline_reset_at": 1712620900000,
    "new_baseline_quality": "insufficient"
  }
}
```

---

## GET /v1/user/{user_hash}/sessions

List recent sessions for a user.

### Response 200

```json
{
  "ok": true,
  "data": {
    "user_hash": "a665a459...",
    "sessions": [
      {
        "session_id": "550e8400...",
        "device_uuid": "7c9e6679...",
        "started_at": 1712620000000,
        "ended_at": 1712623600000,
        "total_pulses": 720,
        "end_reason": "pagehide",
        "max_drift_score": 0.18,
        "critical_actions": ["login_submit", "payment_confirm"],
        "device_known": true
      }
    ]
  }
}
```

---

## POST /v1/challenge/generate

Generate a behavioral challenge token. Used by the SDK's `KProtect.challenge.generate()`.

### Request

```
POST /v1/challenge/generate
X-KP-API-Key: kp_live_abc...
Content-Type: application/json

{
  "session_id": "550e8400...",
  "user_hash": "a665a459...",
  "purpose": "high_value_transfer"
}
```

### Response 200

```json
{
  "ok": true,
  "data": {
    "challenge_id": "ch_abc123...",
    "challenge_type": "behavioral_typing",
    "prompt": "Please type: 'Confirm transfer of $2,500'",
    "expires_at": 1712621100000,
    "nonce": "abc123..."
  }
}
```

---

## POST /v1/challenge/verify

Verify a behavioral challenge response.

### Request

```
POST /v1/challenge/verify
X-KP-API-Key: kp_live_abc...
Content-Type: application/json

{
  "challenge_id": "ch_abc123...",
  "session_id": "550e8400...",
  "user_hash": "a665a459...",
  "response_batch": { /* BehavioralBatch captured during challenge */ }
}
```

### Response 200

```json
{
  "ok": true,
  "data": {
    "challenge_id": "ch_abc123...",
    "passed": true,
    "drift_score": 0.09,
    "confidence": 0.94,
    "action": "allow"
  }
}
```

---

## POST /v1/device/fingerprint

Ingest a device fingerprint batch. Sent once per session when fingerprinting is enabled.

### Request

```
POST /v1/device/fingerprint
Content-Type: application/octet-stream
Content-Encoding: gzip
X-KP-API-Key: kp_live_abc...
X-KP-Session: {session_id}
X-KP-Device: {device_uuid}
X-KP-SDK-Version: web/1.0.0

{gzip-compressed DeviceFingerprintBatch JSON}
```

### Response 200

```json
{
  "ok": true,
  "data": {
    "batch_id": "550e8400-e29b-41d4-a716-446655440000",
    "processed_at": 1712620800000,
    "device_known": true,
    "fingerprint_match_score": 0.94,
    "previous_device_uuids": 2,
    "automation_risk": 0.02
  }
}
```

### Response 400

```json
{
  "ok": false,
  "error": {
    "code": "INVALID_FINGERPRINT",
    "message": "Fingerprint batch missing required signals."
  }
}
```

### Server processing logic

On receipt:

1. Validate API key and HMAC (production keys)
2. Validate `batch_id` uniqueness
3. Extract and normalize signal hashes
4. Compare against known device fingerprints for this `user_hash` and `device_uuid`
5. Compute `fingerprint_match_score` (0.0-1.0)
6. Run automation detection signals through bot classifier
7. Store fingerprint snapshot in device history
8. Return match results

---

## Webhook Events (Outbound)

K-Protect can push high-severity events to your backend via webhook. Configure in the dashboard.

### Event: `alert.critical`

Fired when `action === 'block'` or severity is `critical`.

```json
{
  "event": "alert.critical",
  "timestamp": 1712620800000,
  "data": {
    "alert_id": "alrt_abc...",
    "user_hash": "a665a459...",
    "session_id": "550e8400...",
    "device_uuid": "7c9e6679...",
    "severity": "critical",
    "type": "bot_pattern",
    "drift_score": 0.97,
    "page_context": {
      "url_path": "/payment",
      "page_class": "critical_action",
      "critical_action": "payment_confirm"
    }
  }
}
```

### Event: `session.anomalous`

Fired when `session_trust` transitions to `anomalous`.

```json
{
  "event": "session.anomalous",
  "timestamp": 1712620850000,
  "data": {
    "session_id": "550e8400...",
    "user_hash": "a665a459...",
    "previous_trust": "trusted",
    "current_trust": "anomalous",
    "trigger_batch_id": "...",
    "drift_score": 0.82
  }
}
```

### Webhook security

Webhook payloads include `X-KP-Webhook-Sig: v1={hmac_hex}`. Validate before processing:

```python
import hmac, hashlib

def validate_webhook(payload: bytes, sig_header: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    received = sig_header.removeprefix("v1=")
    return hmac.compare_digest(expected, received)
```

---

## Rate Limits

| Key type | Requests/min | Burst |
|---|---|---|
| `kp_test_*` | 60 | 10 |
| `kp_live_*` (standard) | 600 | 100 |
| `kp_live_*` (enterprise) | 6,000 | 500 |

Rate limits apply per API key. Exceeding returns `429` with `Retry-After` header.

---

## Response Envelope

All responses follow:

```json
{ "ok": true,  "data": {...} }
{ "ok": false, "error": { "code": "SNAKE_CASE_CODE", "message": "Human readable." } }
```

---

*Last updated: 2026-04-09 — K-Protect Engineering*
