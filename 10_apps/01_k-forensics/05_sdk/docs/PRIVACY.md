# K-Protect Privacy Mechanisms

> How K-Protect protects user privacy while performing behavioral biometrics.  
> For security implementation details see [SECURITY.md](SECURITY.md).  
> For GDPR/CCPA integration code see [SDK_INTEGRATION.md](SDK_INTEGRATION.md).

---

## Design Philosophy

K-Protect measures **how** users behave, never **what** they do. Every privacy mechanism exists to ensure that behavioral signals cannot be reversed into personal data, even if the entire batch payload is intercepted.

---

## Differential Privacy (Laplace Noise)

### Problem

The keystroke zone transition matrix records how often a user moves between keyboard zones (home row, top row, number row, bottom row). Without noise, this 4x4 frequency matrix could reveal password structure — e.g., a pattern like `[number_row → home_row → home_row → number_row]` leaks the shape of a PIN-style password.

### Solution

Before inclusion in any `BehavioralBatch`, the zone transition matrix is perturbed with calibrated Laplace noise.

**Algorithm:**

```
For each cell (i, j) in the 4x4 matrix:
  noisy_count = raw_count + Laplace(scale=2.0)
  noisy_count = max(0, round(noisy_count))
```

**Parameters:**

| Parameter | Value | Rationale |
|---|---|---|
| Scale (b) | 2.0 | `sensitivity / epsilon` where sensitivity=1 (count query), epsilon=0.5 |
| Distribution | Laplace via inverse CDF | Crypto-grade randomness (`crypto.getRandomValues`) |
| Post-processing | Clamp to >= 0, round to integer | Counts cannot be negative or fractional |

**Privacy guarantee:** epsilon-differential privacy with epsilon=0.5 per extraction window. This means an observer cannot distinguish, with high confidence, whether any single keystroke event was included or excluded from the matrix.

**Impact on drift scoring:** The noise is small relative to multi-session baselines (which average hundreds of windows). Individual-window noise washes out in the aggregate, preserving drift detection accuracy while protecting per-window patterns.

**Source:** [laplace-noise.ts](../packages/sdk-web/src/collectors/laplace-noise.ts).

---

## Cross-Site Fingerprint Salting

Device fingerprints could theoretically be used to track users across different websites. K-Protect prevents this by salting all hash-based fingerprint signals with the page origin before transmission.

**Algorithm:**

For each hash-based signal (canvas, audio, webgl, gpu_render, fonts, speech):

```
salted_hash = SHA-256(raw_hash + window.location.origin)
```

**Effect:** The same physical device produces different fingerprint hashes on `bank-a.com` vs `bank-b.com`. Even if two K-Protect tenants compared their fingerprint databases, they could not correlate devices across sites.

**What is salted:** Only hash-type signals (canvas, audio, webgl, gpu_render, fonts, speech). Numeric/boolean signals (screen dimensions, touch points, feature flags) are NOT salted because they are inherently non-unique and cannot be used for cross-site tracking on their own.

**Source:** [collect-all.ts](../packages/sdk-web/src/signals/collect-all.ts) — `saltHash()`, `saltFingerprint()`.

---

## Zone-Based Coordinate Abstraction

The SDK never captures absolute pixel coordinates. Instead, event targets are mapped to **zone IDs** — semantic regions of the page (e.g., `header`, `nav`, `main-content`, `form-area`).

- Mouse/pointer events: `zone_id` derived from the element under the cursor
- Touch events: `zone_id` from the touch target
- Keyboard events: `zone_id` from the focused element

This means:
- No screen geometry is captured
- Zone IDs cannot be reversed to pixel positions
- Behavioral patterns are consistent across screen sizes and layouts

---

## Data Retention & TTL

All client-side stored data has a maximum time-to-live:

| Data | Storage | TTL | Eviction |
|---|---|---|---|
| Username (encrypted) | IDB + localStorage | 30 days | Auto-deleted on read if expired |
| Device UUID | IDB + localStorage | 30 days | Auto-renewed on each session |
| Session ID | sessionStorage | Tab lifetime | Cleared on tab close |
| Consent state | localStorage | Indefinite | Persists until user revokes |
| Config cache | localStorage | Until `destroy()` | Cleared on SDK teardown |

**TTL implementation:** Values are stored in a `{ value, stored_at }` envelope. On read, if `Date.now() - stored_at > DATA_RETENTION_TTL_MS` (30 days), the value is treated as null and the key is deleted asynchronously.

**Legacy migration:** Pre-TTL values (plain strings without the envelope) are treated as valid on first read, then re-wrapped with a fresh timestamp on next write.

**Source:** [identity-store.ts](../packages/sdk-web/src/session/identity-store.ts) — `wrapWithTtl()`, `unwrapWithTtl()`.

---

## Raw Event Lifecycle

Raw behavioral events have the shortest possible lifetime:

```
Event fires (main thread)
  → postMessage to worker (ArrayBuffer transfer, zero-copy)
  → Enqueued in collector ring buffer (max 1,000 events per window)
  → Feature extraction runs (every 5s window)
  → Extracted features stored; raw events DISCARDED
  → Features assembled into batch → sent to server
```

**Key invariant:** Raw events never survive beyond the 5-second extraction window. After `FeatureExtractor` runs, the collector buffers are cleared. No raw event data is ever written to persistent storage, transmitted to the server, or accessible via the public API.

---

## Consent Management (GDPR/CCPA)

The SDK supports three consent modes, configured via `overrides.consent.mode`:

### Modes

| Mode | Behavior | When to use |
|---|---|---|
| `opt-out` (default) | SDK runs immediately; stops if user calls `consent.deny()` | Most jurisdictions; legitimate-interest basis |
| `opt-in` | SDK blocked until `consent.grant()` is called, then `init()` re-invoked | GDPR strict-consent jurisdictions |
| `none` | No consent gating; SDK always runs | Non-regulated environments, internal tools |

### Consent State Machine

```
                    consent.grant()
  [unknown] ──────────────────────────→ [granted]
      │                                     │
      │ consent.deny()         consent.deny()│
      ▼                                     ▼
  [denied] ←────────────────────────────────┘
      │
      │ consent.grant()
      ▼
  [granted]
```

### Storage

Consent state is persisted in localStorage at key `kp.consent`:

```json
{
  "state": "granted",
  "timestamp": 1712620800000
}
```

### Behavior on Deny

If `consent.deny()` is called while the SDK is running:
1. The SDK is immediately destroyed (equivalent to `destroy(false)`)
2. No further data is collected or transmitted
3. The consent state is persisted so subsequent `init()` calls are also blocked (in opt-in mode)

**Source:** [consent-manager.ts](../packages/sdk-web/src/session/consent-manager.ts), [index.ts](../packages/sdk-web/src/index.ts).

---

## GDPR Data Subject Rights

The SDK provides a built-in API for GDPR Article 15 (right of access) and Article 17 (right to erasure).

### Data Export (Article 15)

```ts
const data = await KProtect.gdpr.export();
// Returns:
// {
//   user_hash: string | null,
//   device_uuid: string | null,
//   session_id: string | null,
//   consent_state: 'granted' | 'denied' | 'unknown',
//   exported_at: number,
//   stored_keys: Record<string, string | null>  // all kp.* storage keys
// }
```

**What is included:** All data the SDK has stored about the user on this device.

**What is NOT included:** Raw behavioral data (already discarded after feature extraction), server-side baselines and drift scores (must be requested via the server API).

### Data Deletion (Article 17)

```ts
await KProtect.gdpr.delete();
```

This performs a complete erasure:
1. Ends the current session and destroys the SDK
2. Deletes all `kp.*` keys from localStorage
3. Deletes the session ID from sessionStorage
4. Deletes the entire `kp-bio` IndexedDB database
5. The device is treated as completely new on next visit

**Note:** `gdpr.delete()` is a superset of `destroy({ clearIdentity: true })`. It clears storage even if the SDK was never initialized in the current page load.

**Source:** [index.ts](../packages/sdk-web/src/index.ts) — `gdpr.export()`, `gdpr.delete()`.

---

## Audit Logging (SOC 2 Compliance)

The SDK maintains a tamper-evident audit log of all significant actions. This log can be exported for compliance review.

### What is Logged

| Action | When | Detail fields |
|---|---|---|
| `sdk_init` | `init()` called | config hash |
| `session_start` | New session minted | session_id |
| `session_end` | Session terminated | session_id, reason |
| `username_captured` | Username detected and hashed | (no PII) |
| `batch_sent` | Batch successfully transmitted | batch_id |
| `batch_failed` | Batch transmission failed | batch_id, error |
| `fingerprint_collected` | Device fingerprint gathered | signal count |
| `consent_granted` | User granted consent | timestamp |
| `consent_denied` | User denied consent | timestamp |
| `logout` | `logout()` called | — |
| `destroy` | `destroy()` called | clearIdentity |

### Tamper Evidence

Each entry includes `prev_hash` — the SHA-256 hash of the previous entry. This creates a hash chain where modifying or removing any entry breaks the chain and is detectable during verification.

```ts
interface AuditEntry {
  seq: number;           // Monotonic sequence number
  timestamp: string;     // ISO 8601
  action: AuditAction;
  detail: Record<string, string | number | boolean> | null;
  prev_hash: string;     // SHA-256 of previous entry (chain integrity)
}
```

### Limits

- Maximum 1,000 entries (ring buffer — oldest evicted on overflow)
- Log lives in worker memory only — not persisted to disk
- Export via `KProtect.exportAuditLog()` returns a deep copy

**Source:** [audit-logger.ts](../packages/sdk-web/src/session/audit-logger.ts).

---

## Username Handling

The raw username follows a strict one-way path:

```
User types in login field (main thread)
  → DomScanner detects blur event on matching selector
  → SHA-256(username) computed on main thread (crypto.subtle)
  → Only the hash crosses to the worker via postMessage
  → Worker stores hash in memory as user_hash
  → Raw username encrypted (AES-GCM) and stored in IDB for re-capture on reload
  → user_hash (never raw username) included in all outbound batches
```

**The server never receives the raw username.** It receives only `user_hash`, which is a one-way SHA-256 digest.

---

*Last updated: 2026-04-09 — K-Protect Engineering*
