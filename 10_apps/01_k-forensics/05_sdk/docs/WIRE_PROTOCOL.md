# K-Protect Wire Protocol Reference

> Complete specification of every message sent between the SDK and the K-Protect API.  
> Version: v1  
> Encoding: JSON (body), gzip compressed where CompressionStream is available.

---

## Overview

All behavioral data flows through a single endpoint:

```
POST https://api.kprotect.io/v1/behavioral/ingest
```

The SDK sends `BehavioralBatch` messages (normal pages) and `CriticalActionBatch` messages (critical-action pages). The server responds with `DriftScoreResponse`.

---

## Request Headers

| Header | Required | Value |
|---|---|---|
| `Content-Type` | Yes | `application/octet-stream` (gzip) or `application/json` (uncompressed fallback) |
| `Content-Encoding` | Conditional | `gzip` when compressed |
| `X-KP-API-Key` | Yes | API key: `kp_live_abc...` or `kp_test_abc...` |
| `X-KP-Session` | Yes | Current `session_id` (UUID) |
| `X-KP-Device` | Yes | Current `device_uuid` (UUID) |
| `X-KP-SDK-Version` | Yes | SDK version: `web/1.0.0`, `android/1.0.0`, `ios/1.0.0` |
| `X-KP-Sig` | Production only | HMAC-SHA256 signature of body (see §Signing) |

---

## BehavioralBatch (normal pages)

Sent on every pulse tick on `normal` page class.

```ts
interface BehavioralBatch {
  // ─── Routing ───────────────────────────────────────────────────────────────
  type: 'behavioral';

  // ─── Batch identity ────────────────────────────────────────────────────────
  batch_id: string;            // UUID, unique per batch (idempotency key)
  sent_at: number;             // Monotonic timestamp ms (sessionStartEpoch + performance.now()) — NOT Date.now()

  // ─── Session identity ──────────────────────────────────────────────────────
  session_id: string;          // UUID, per-tab, per-session
  pulse: number;               // Monotonic counter starting at 0 for this session
  pulse_interval_ms: number;   // Actual interval used — default 30000ms (server detects gaps)
  sequence: number;            // Monotonic counter of ALL batches in session (never resets)

  // ─── User identity ─────────────────────────────────────────────────────────
  user_hash: string;           // SHA-256(username) hex — never the raw username
  device_uuid?: string;        // Persistent device hint (required on first batch + session events, optional thereafter)

  // ─── Page context ──────────────────────────────────────────────────────────
  page_context: {
    url_path: string;          // URL path only — no query params, no fragment
    page_class: 'normal';
    referrer_path?: string;    // Previous page path (for navigation flow analysis)
  };

  // ─── Window coverage ───────────────────────────────────────────────────────
  window_start_ms: number;     // performance.now() of first event in this batch
  window_end_ms: number;       // performance.now() of last event in this batch
  event_count: number;         // Total raw events collected (before extraction)

  // ─── Origin binding ─────────────────────────────────────────────────────────
  origin_hash?: string;          // SHA-256(session_id + origin) — sent on first batch + session events, optional thereafter

  // ─── Behavioral signals ────────────────────────────────────────────────────
  signals: {
    keystroke?: KeystrokeSignal;
    pointer?: PointerSignal;     // Legacy — kept for backwards compat
    touch?: TouchSignal;         // Legacy — kept for backwards compat
    gesture?: GestureSignal;     // Unified pointer + touch (see §GestureSignal)
    scroll?: ScrollSignal;
    sensor?: SensorSignal;
    credential?: CredentialSignal;
  };

  // ─── Automation detection ───────────────────────────────────────────────────
  automation_score?: number;     // 0.0–1.0, from device fingerprint automation checks (present when fingerprinting enabled)

  // ─── SDK metadata ──────────────────────────────────────────────────────────
  sdk: {
    version: string;
    platform: 'web' | 'android' | 'ios';
    worker_mode: 'worker' | 'fallback_main_thread';
    environment: 'production' | 'debug';
  };
}
```

---

## CriticalActionBatch

Sent when user commits (or abandons) a critical-action page. Extends `BehavioralBatch`.

```ts
interface CriticalActionBatch extends Omit<BehavioralBatch, 'type' | 'page_context'> {
  type: 'critical_action';
  // Inherits origin_hash from BehavioralBatch

  page_context: {
    url_path: string;
    page_class: 'critical_action';
    referrer_path?: string;
    critical_action: string;   // e.g. 'payment_confirm', 'login_submit'
    committed: boolean;        // true = user clicked commit, false = navigated away
    time_on_page_ms: number;   // How long user spent on this page before commit/abandon
  };
}
```

---

## Keepalive Batch

Sent on the slow keepalive cadence during critical-action pages. Contains NO behavioral signals.

```ts
interface KeepaliveBatch {
  type: 'keepalive';
  batch_id: string;
  sent_at: number;               // Monotonic timestamp ms (sessionStartEpoch + performance.now())
  session_id: string;
  pulse: number;
  pulse_interval_ms: number;
  user_hash: string;
  device_uuid?: string;          // Required on first batch, optional thereafter
  origin_hash?: string;          // Required on first batch, optional thereafter
  page_context: {
    url_path: string;
    page_class: 'critical_action';
    critical_action: string;
  };
  sdk: { version: string; platform: string; };
}
```

---

## Session Event Batches

Sent on session start and session end. No behavioral data.

```ts
interface SessionEventBatch {
  type: 'session_start' | 'session_end';
  batch_id: string;
  sent_at: number;
  session_id: string;
  user_hash: string | null;    // null if session ended before username was captured
  device_uuid: string;
  origin_hash?: string;        // SHA-256(session_id + origin)
  session_start_ms: number;    // epoch ms when this session started
  session_end_ms?: number;     // epoch ms of end event (session_end only)
  end_reason?: 'pagehide' | 'logout' | 'destroy' | 'idle_timeout';
  total_pulses: number;
  sdk: { version: string; platform: string; };
}
```

---

## Signal Types

### KeystrokeSignal

Timing patterns for keyboard interactions. No key content.

```ts
interface KeystrokeSignal {
  available: boolean;

  // Dwell times: how long each key is held (ms)
  dwell_times: {
    mean: number;
    std_dev: number | null;      // null when sample_count < 2 (insufficient data for deviation)
    p25: number;
    p50: number;
    p75: number;
    p95: number;
    sample_count: number;
  };

  // Flight times: gap between key-up and next key-down (ms)
  flight_times: {
    mean: number;
    std_dev: number | null;      // null when sample_count < 2 (insufficient data for deviation)
    p25: number;
    p50: number;
    p75: number;
    p95: number;
    sample_count: number;
  };

  // Error patterns
  backspace_rate: number;        // backspaces per 10 keystrokes
  correction_burst_rate: number; // rapid correction sequences per minute

  // Typing rhythm
  words_per_minute: number;
  burst_typing_fraction: number; // fraction of time in "burst" (>4 keys/s) mode

  // Zone transitions (keyboard zones: home/top/bottom row, number row)
  zone_transition_matrix: number[][];  // 4x4 matrix of inter-zone frequencies
  zone_ids_used: string[];             // zone IDs, not key names

  // Field-level aggregates (per input field zone_id, not field name)
  field_breakdown?: {
    zone_id: string;
    event_count: number;
    dwell_mean: number;
    flight_mean: number;
  }[];
}
```

### PointerSignal

Mouse/trackpad patterns.

```ts
interface PointerSignal {
  available: boolean;

  // Velocity profile
  velocity: {
    mean: number;     // px/ms
    max: number;
    p50: number;
    p95: number;
  };

  // Acceleration profile
  acceleration: {
    mean: number;
    std_dev: number | null;      // null when sample_count < 2
    direction_changes_per_sec: number;
  };

  // Click patterns
  clicks: {
    count: number;
    double_click_count: number;
    mean_dwell_ms: number;       // how long button held
    zone_ids: string[];          // which zones were clicked
  };

  // Movement patterns
  idle_fraction: number;        // fraction of time with no movement
  ballistic_fraction: number;   // fraction of movement that is fast/straight
  micro_correction_rate: number; // small corrective movements per cm of travel

  // Path curvature
  mean_curvature: number;       // 0 = straight lines, 1 = circular
}
```

### TouchSignal

Mobile touch patterns.

```ts
interface TouchSignal {
  available: boolean;

  // Touch geometry (no coordinates — zone IDs only)
  mean_contact_area: number;   // normalized 0-1
  mean_pressure: number;       // normalized 0-1 (where available)

  // Touch timing
  tap: {
    count: number;
    mean_dwell_ms: number;
    mean_flight_ms: number;    // between consecutive taps
    zone_ids: string[];
  };

  // Gesture patterns
  swipe: {
    count: number;
    mean_velocity: number;     // normalized
    mean_distance: number;     // normalized (not pixel values)
    direction_distribution: { up: number; down: number; left: number; right: number };
  };

  // Multi-touch
  pinch_count: number;
  spread_count: number;

  // Hand posture indicator (left/right/unknown — inferred from touch zone patterns)
  dominant_hand_hint: 'left' | 'right' | 'unknown';
}
```

### GestureSignal (unified pointer + touch)

Combines pointer (mouse/trackpad) and touch patterns into a single signal. On desktop, only `pointer` is populated. On mobile, only `touch`. On hybrid devices, both sections may be present.

```ts
interface GestureSignal {
  available: boolean;

  pointer: {
    velocity: { mean: number; max: number; p50: number; p95: number; std_dev: number };
    acceleration: { mean: number; std_dev: number; direction_changes_per_sec: number };
    clicks: { count: number; double_click_count: number; mean_dwell_ms: number; dwell_stdev: number };
    idle_fraction: number;
    ballistic_fraction: number;
    micro_correction_rate: number;
    mean_curvature: number;
    path_efficiency: number;          // 0–1, straight-line distance / actual path length
    angle_histogram: number[];        // directional movement distribution
    segments: {
      count: number;
      duration_mean: number;
      distance_mean: number;
      efficiency_mean: number;
    };
    move_count: number;
    total_distance: number;
  } | null;

  touch: {
    mean_contact_area: number;
    area_stdev: number;
    tap: { count: number; mean_dwell_ms: number; dwell_stdev: number; mean_flight_ms: number; flight_stdev: number };
    swipe: { count: number; duration_mean: number; duration_stdev: number };
    pinch_count: number;
    heatmap_zones: number[];          // zone-based interaction heatmap
    dominant_hand_hint: 'left' | 'right' | 'unknown';
  } | null;
}
```

> **Note:** The separate `PointerSignal` and `TouchSignal` types are retained in the `signals` object for backwards compatibility. New integrations should read from `gesture` instead.

---

### ScrollSignal

Scroll behavior patterns.

```ts
interface ScrollSignal {
  available: boolean;

  scroll_events: number;
  mean_velocity: number;           // normalized
  mean_distance_per_scroll: number; // normalized

  // Reading vs navigation
  reading_pause_count: number;     // pauses within content (not at top/bottom)
  rapid_scroll_count: number;      // fast passes through content

  // Direction distribution
  direction_distribution: { up: number; down: number; horizontal: number };
}
```

> **Note:** Scroll signals are now actively extracted and included in behavioral batches. The `scroll` key in `signals` is populated whenever scroll events are collected during the pulse window.

### SensorSignal

Device motion sensors (mobile).

```ts
interface SensorSignal {
  available: boolean;

  // Accelerometer
  accelerometer?: {
    mean_magnitude: number;
    std_dev: number | null;      // null when sample_count < 2
    stillness_fraction: number; // fraction of window where device was still
  };

  // Gyroscope
  gyroscope?: {
    mean_rotation_rate: number;
    dominant_axis: 'x' | 'y' | 'z';
    stillness_fraction: number;
  };

  // Inferred posture
  device_posture: 'flat' | 'portrait_stable' | 'landscape_stable' | 'moving' | 'unknown';
}
```

### CredentialSignal

Behavioral patterns on login/credential fields. No field values.

```ts
interface CredentialSignal {
  available: boolean;            // true ONLY when actual credential data is present (password_field, username_field, or form)

  // Password field behavior (type=password)
  password_field?: {
    total_keystrokes: number;
    backspace_count: number;
    paste_detected: boolean;    // true if Ctrl+V / right-click paste observed
    autofill_detected: boolean; // true if field filled programmatically
    mean_dwell_ms: number;
    mean_flight_ms: number;
    typed_then_cleared: boolean; // typed, deleted all, re-typed (hesitation pattern)
  };

  // Username field behavior (type=text/email/tel)
  username_field?: {
    total_keystrokes: number;
    backspace_count: number;
    paste_detected: boolean;
    autofill_detected: boolean;
    autocomplete_selected: boolean; // browser autocomplete used
  };

  // Form submission behavior
  form?: {
    time_to_submit_ms: number;  // from first keystroke to submit
    tab_navigation_count: number; // times Tab used to move between fields
    submit_method: 'button_click' | 'enter_key' | 'programmatic';
  };
}
```

---

## DriftScoreResponse

Server response after processing a batch.

```ts
interface DriftScoreResponse {
  // ─── Batch acknowledgment ─────────────────────────────────────────────────
  batch_id: string;           // Echo of request batch_id
  processed_at: number;       // Server processing timestamp (Unix ms)

  // ─── Drift assessment ─────────────────────────────────────────────────────
  drift_score: number;        // 0.0–1.0 (0 = identical to baseline, 1 = maximum drift)
  confidence: number;         // 0.0–1.0 (how much data we have to make this call)

  // Decomposed scores by signal type
  signal_scores: {
    keystroke?: number;
    pointer?: number;
    touch?: number;
    scroll?: number;
    sensor?: number;
    credential?: number;
  };

  // ─── Recommended action ───────────────────────────────────────────────────
  action: 'allow' | 'monitor' | 'challenge' | 'block';
  action_reason?: string;     // Human-readable reason (debug mode only)

  // ─── Auth state ───────────────────────────────────────────────────────────
  auth_state: {
    session_trust: 'trusted' | 'suspicious' | 'anomalous';
    device_known: boolean;    // device_uuid recognized from history
    baseline_age_days: number; // days since baseline was established
    baseline_quality: 'insufficient' | 'forming' | 'established' | 'strong';
  };

  // ─── Alerts (when action = challenge or block) ────────────────────────────
  alerts?: Alert[];
}

interface Alert {
  alert_id: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  type: string;               // e.g. 'device_change', 'typing_anomaly', 'bot_pattern'
  description: string;        // debug mode only
  triggered_at: number;
}
```

---

## Session Metadata Response

Returned alongside the `DriftScoreResponse` on `session_start`:

```ts
interface SessionMetadataResponse extends DriftScoreResponse {
  session_metadata: {
    session_id: string;
    user_hash: string;
    device_history_count: number;  // how many prior device_uuids seen for this user
    session_history_count: number; // total sessions on record for this user
    last_seen_days_ago: number;
  };
}
```

---

## Error Responses

Standard error envelope:

```ts
interface ErrorResponse {
  ok: false;
  error: {
    code: string;        // e.g. 'INVALID_API_KEY', 'MISSING_USER_HASH', 'RATE_LIMITED'
    message: string;
    retry_after_ms?: number;  // present on 429
  };
}
```

Common error codes:

| Code | HTTP Status | Meaning | SDK Action |
|---|---|---|---|
| `INVALID_API_KEY` | 401 | API key not recognized | Drop batch, log warning |
| `MISSING_USER_HASH` | 400 | `user_hash` absent from batch | Drop batch (SDK bug) |
| `INVALID_BATCH_ID` | 400 | Duplicate or malformed batch_id | Drop batch |
| `BATCH_TOO_OLD` | 400 | `sent_at` > 5 min ago | Drop batch |
| `RATE_LIMITED` | 429 | Too many requests | Backoff per retry policy |
| `SERVER_ERROR` | 500 | Internal server error | Retry per retry policy |

---

## DeviceFingerprintBatch

Sent once per session (on init) when device fingerprinting is enabled. Contains the full `DeviceFingerprint` payload with signals organized by tier.

```ts
interface DeviceFingerprintBatch {
  type: 'device_fingerprint';
  batch_id: string;
  sent_at: number;
  session_id: string;
  user_hash: string | null;     // May be null if sent before username capture
  device_uuid: string;
  origin_hash?: string;         // SHA-256(session_id + origin) — origin binding

  fingerprint: DeviceFingerprint;  // Full device fingerprint payload (see below)

  sdk: { version: string; platform: string; };
}
```

### DeviceFingerprint Structure

The `fingerprint` field contains three tiers of signals. All fields are nullable — a `null` value means the signal could not be collected (browser restriction, timeout, or error).

```ts
interface DeviceFingerprint {
  // ─── TIER 1 — synchronous, cross-browser stable ─────────────────────────
  screen: ScreenFingerprint | null;        // width, height, colorDepth, DPR, HDR, P3
  platform: PlatformFingerprint | null;    // hardwareConcurrency, touchPoints, timezone, languages
  media_queries: MediaQueryFingerprint | null;  // pointer, hover, colorGamut, reducedMotion
  features: FeatureFlags | null;           // 18 browser API capability flags
  math: MathFingerprint | null;            // Float precision quirks (tan, log, pow)
  date_format: DateFingerprint | null;     // Intl.DateTimeFormat hashes
  css: CssFingerprint | null;              // CSS.supports() feature map

  // ─── TIER 2 — async, computation-required (~200-500ms) ──────────────────
  canvas: CanvasFingerprint | null;        // Canvas 2D render → SHA-256 hash
  audio: AudioFingerprint | null;          // OfflineAudioContext → SHA-256 hash
  webgl: WebGLFingerprint | null;          // 14 GL params + shader precision + renderer
  gpu_render: GpuRenderFingerprint | null; // 5 GPU render tasks (exact + quantized hashes)
  fonts: FontFingerprint | null;           // DOM measurement font enumeration → hash
  cpu: CpuBenchmark | null;               // 5 micro-benchmarks + 3 cross-browser ratios

  // ─── TIER 3 — browser-specific, may be unavailable ──────────────────────
  network: NetworkFingerprint | null;      // navigator.connection (Chrome/Edge only)
  storage: StorageFingerprint | null;      // StorageManager quota
  speech: SpeechFingerprint | null;        // speechSynthesis voices → hash
  battery: BatteryFingerprint | null;      // Charging state + bucketed level
  automation: AutomationFingerprint | null; // Bot/headless detection (8 checks + score)

  // ─── Metadata ───────────────────────────────────────────────────────────
  load_indicators: LoadIndicators | null;  // FPS, event loop latency, memory
  collected_at: number;                    // Unix ms timestamp
  collection_time_ms: number;              // Total collection duration
  fingerprint_version: number;             // Algorithm version (bumped on logic changes)
}
```

**Cross-site salting:** All hash-based signals (canvas, audio, webgl, gpu_render, fonts, speech) are salted with `SHA-256(raw_hash + window.location.origin)` before transmission, preventing cross-site fingerprint correlation.

**Mutable signal refresh:** Network and battery signals are re-collected every 3 minutes and sent to the worker via `MUTABLE_SIGNALS_UPDATE` messages. This ensures the server has up-to-date network context without re-running expensive TIER 2 collections.

See [device_fingerprinting.md.md](../device_fingerprinting.md.md) for the full signal taxonomy and collection rules.
```

---

## Beacon Signing (SendBeacon Transport)

`navigator.sendBeacon()` is used for `session_end` batches during page unload. Since `sendBeacon` cannot set custom HTTP headers, the HMAC signature is embedded directly in the request body.

### Signed Beacon Payload

```ts
interface SignedBeaconPayload {
  /** JSON-stringified batch data. */
  payload: string;
  /** HMAC-SHA256 hex digest. */
  signature: string;
  /** First 12 characters of API key (server lookup key). */
  key_id: string;
  /** Unix timestamp ms at signing time. */
  timestamp: number;
  /** batch_id used as nonce for replay protection. */
  nonce: string;
}
```

### Signature Algorithm

```
signature = HMAC-SHA256(
  key  = TextEncoder.encode(api_key),
  data = batch_id + '.' + timestamp + '.' + SHA256(JSON.stringify(batch))
)
```

The server validates by:

1. Looking up the full API key using `key_id` (first 12 chars)
2. Recomputing the HMAC with the same formula
3. Constant-time comparison of the signatures
4. Verifying `timestamp` is within ±5 minutes of server time
5. Verifying `nonce` (batch_id) has not been seen in the last 24 hours

---

## Signing (Production Mode)

In `environment: 'production'`, each request includes an `X-KP-Sig` header.

**Signature algorithm:**
```
sig = HMAC-SHA256(
  key  = HKDF(api_key + device_uuid, salt="kp-sig-v1"),
  data = method + "\n" + path + "\n" + sent_at + "\n" + SHA256(body)
)
header: X-KP-Sig: v1={hex(sig)}
```

The server validates this signature and rejects requests with:
- Invalid signature
- `sent_at` outside ±5 min of server time
- Same `(batch_id, user_hash)` pair seen within 24h (replay attack)

---

## Versioning

The API version is `v1`. Breaking changes increment the version in the path (`/v2/behavioral/ingest`). The SDK major version must match the API version.

Backwards-compatible additions (new optional fields in request/response) do not increment the version.

---

## Compression

```
Raw JSON → TextEncoder → Uint8Array
         → CompressionStream('gzip') → compressed Uint8Array
         → fetch body (Content-Encoding: gzip)
```

Fallback for browsers without `CompressionStream` (Firefox < 113, Safari < 16.4):
```
Raw JSON → fetch body (Content-Type: application/json, no Content-Encoding)
```

Server accepts both. Compression is transparent to all parsing logic.

---

*Last updated: 2026-04-09 — K-Protect Engineering*
