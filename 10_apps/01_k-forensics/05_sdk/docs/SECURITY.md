# K-Protect Security Reference

> Implementation details of all security mechanisms in the K-Protect SDK.  
> For integration instructions see [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md).  
> For wire format see [WIRE_PROTOCOL.md](WIRE_PROTOCOL.md).

---

## Overview

K-Protect is designed to run invisibly inside banking and fintech applications where the threat model includes XSS, session hijacking, credential stuffing, and bot attacks. Every security mechanism below is automatic — integrators do not need to enable or configure any of them.

---

## Origin Binding (Session Hijack Detection)

Each session is cryptographically bound to the page origin that created it.

**How it works:**

1. On `session_start`, the SDK computes `origin_hash = SHA-256(session_id + window.location.origin)`.
2. The `origin_hash` is stored in the worker's `SessionManager`.
3. On every `visibilitychange` (tab becomes visible again), the SDK re-derives `origin_hash` from the current origin and compares it to the stored value.
4. If the hashes differ, the session is immediately terminated with reason `origin_mismatch` and a new session is started.

**Why it matters:**

If an attacker injects a script that transfers the `session_id` to a different origin (e.g., via a compromised iframe), the origin binding check detects the mismatch and prevents the hijacked session from continuing.

**Source:** [session-manager.ts](../packages/sdk-web/src/session/session-manager.ts) — `computeOriginHash()`, `setVisibility()`.

---

## Encryption at Rest (Username Protection)

The captured username is encrypted before being written to IndexedDB or mirrored to localStorage.

**Scheme:**

| Step | Detail |
|---|---|
| Key derivation | `PBKDF2(device_uuid, salt, 100_000 iterations, SHA-256) → AES-GCM 256-bit key` |
| Salt | 16-byte `crypto.getRandomValues()`, stored in IDB key `kp.us` |
| Encryption | `AES-GCM(key, 12-byte IV, plaintext_username) → ciphertext` |
| Storage | Ciphertext stored in IDB key `kp.un`, mirrored to localStorage via `STORAGE_WRITE` |
| Decryption | On session init, ciphertext is decrypted with the derived key |

**Fallback:** If `crypto.subtle` is unavailable (rare — requires very old browsers or restricted contexts), the username is stored in plaintext. The SDK logs this at debug level but does not fail.

**Migration:** If the SDK detects a plaintext username in storage (legacy / pre-encryption), it automatically encrypts the value in-place on next read.

**Source:** [identity-store.ts](../packages/sdk-web/src/session/identity-store.ts) — `initEncryptionKey()`, `readEncryptedUsername()`, `writeEncryptedUsername()`.

---

## HMAC Request Signing

All production API requests are signed to prevent tampering and replay attacks.

### Fetch Transport (normal batches)

```
X-KP-Sig: v1={hex(sig)}

sig = HMAC-SHA256(
  key  = HKDF(api_key + device_uuid, salt="kp-sig-v1"),
  data = method + "\n" + path + "\n" + sent_at + "\n" + SHA256(body)
)
```

The server validates:
- Signature matches the expected HMAC
- `sent_at` is within ±5 minutes of server time
- `(batch_id, user_hash)` pair has not been seen in the last 24 hours (replay protection)

### SendBeacon Transport (session_end on page unload)

`navigator.sendBeacon()` cannot set custom HTTP headers, so the signature is embedded in the request body:

```ts
interface SignedBeaconPayload {
  payload: string;      // JSON-stringified batch
  signature: string;    // HMAC-SHA256 hex digest
  key_id: string;       // First 12 chars of API key (server lookup key)
  timestamp: number;    // Unix ms at signing time
  nonce: string;        // batch_id (replay protection)
}
```

**Signature formula:**
```
HMAC-SHA256(api_key_bytes, batch_id + '.' + timestamp + '.' + SHA256(payload))
```

**Constant-time comparison:** The server (and the SDK's `verifyBeaconSignature()`) uses bitwise XOR comparison to prevent timing side-channel attacks.

**Source:** [beacon-signing.ts](../packages/sdk-web/src/transport/beacon-signing.ts).

---

## Content Security Policy (CSP) Requirements

The SDK needs two CSP directives:

```
connect-src 'self' https://api.kprotect.io;
worker-src blob:;
```

| Directive | Why | If blocked |
|---|---|---|
| `connect-src https://api.kprotect.io` | SDK sends batches to the K-Protect API | Batches fail silently; no behavioral data collected |
| `worker-src blob:` | Worker spawned via `new Worker(URL.createObjectURL(blob))` | SDK falls back to main-thread idle scheduler (no functionality lost) |

**Not required:**
- `unsafe-eval` — the SDK never uses `eval`, `Function()`, or string-based `setTimeout`/`setInterval`
- `unsafe-inline` — no inline scripts are injected
- `script-src blob:` — only `worker-src` is needed; the blob is a Worker, not a script

---

## Worker Isolation (Security Boundary)

The Web Worker acts as a security boundary between the host page and behavioral data:

```
Host Page (main thread)          Web Worker
─────────────────────────        ─────────────────────────────
KProtect facade                  Collectors + FeatureExtractor
  - Receives: DriftScoreResponse   - Processes raw events
  - Receives: SessionState         - Computes features
  - Never sees raw behavioral      - Discards raw events after
    data or feature vectors           extraction (every 5s window)
                                   - Only user_hash (SHA-256) exits
```

The `postMessage` channel uses typed discriminated unions from `wire-protocol.ts`. No raw DOM objects, closures, or `Element` references cross the boundary.

**MessageChannel:** The SDK uses a dedicated `MessageChannel` for worker communication (not the global `postMessage`), making the channel unforgeable by other scripts on the page.

---

## Data Never Captured

The SDK enforces strict boundaries on what data is collected:

| Data type | SDK behavior |
|---|---|
| Keystroke content (what was typed) | Never read — only timing metadata (dwell, flight) |
| Absolute pixel coordinates | Never captured — only zone IDs |
| `input[type="password"]` values | Never read — behavioral metadata only |
| Raw username | Hashed (SHA-256) on main thread before crossing to worker |
| Query parameters / URL fragments | Stripped — only `url_path` is sent |
| Cookie values | Never read |
| DOM content | Never read — only element zone IDs from event targets |

---

## Replay Attack Prevention

Multiple layers prevent replay of captured batches:

1. **batch_id uniqueness:** Each batch has a UUID `batch_id`. The server rejects any `(batch_id, user_hash)` pair seen within 24 hours.
2. **Timestamp validation:** `sent_at` must be within ±5 minutes of server time. Old batches are rejected with `BATCH_TOO_OLD`.
3. **HMAC nonce:** The beacon signing scheme includes `batch_id` as a nonce in the signature message, binding the signature to a specific batch.
4. **Monotonic sequence:** The `sequence` field in `BehavioralBatch` is monotonically increasing per session. Gaps or rewinds are detectable server-side.

---

## API Key Security

- API keys are **never sent as plaintext in headers** in production mode. Instead, HMAC-derived signatures authenticate requests.
- Test keys (`kp_test_*`) skip HMAC validation for development convenience.
- Live keys (`kp_live_*`) require full HMAC validation on every request.
- The `key_id` (first 12 characters) is used for server-side key lookup without exposing the full key.

---

*Last updated: 2026-04-09 — K-Protect Engineering*
