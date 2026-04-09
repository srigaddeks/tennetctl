# K-Protect SDK Best Practices

> **Status**: Living document. Every PR that touches `packages/sdk-web`, `packages/sdk-android`, or `packages/sdk-ios` must be reviewed against this document.  
> **Authority**: This document overrides any individual implementation decision that contradicts it. If a rule here conflicts with "what seemed easier", the rule wins.

---

## Table of Contents

1. [Threading Model](#1-threading-model)
2. [Zero-Config Principle](#2-zero-config-principle)
3. [Bundle Budget](#3-bundle-budget)
4. [Performance Budget](#4-performance-budget)
5. [Privacy Invariants](#5-privacy-invariants)
6. [Identity Model](#6-identity-model)
7. [Session Lifecycle](#7-session-lifecycle)
8. [Pulse Contract](#8-pulse-contract)
9. [Page Gating](#9-page-gating)
10. [Critical-Action Protocol](#10-critical-action-protocol)
11. [Transport Contract](#11-transport-contract)
12. [Storage Contract](#12-storage-contract)
13. [Error Handling](#13-error-handling)
14. [Security Requirements](#14-security-requirements)
15. [Public API Surface](#15-public-api-surface)
16. [Code Review Checklist](#16-code-review-checklist)
17. [Android SDK Addendum](#17-android-sdk-addendum)
18. [iOS SDK Addendum](#18-ios-sdk-addendum)

---

## 1. Threading Model

### 1.1 Rule: The main thread is for event taps only

All behavioral signal processing MUST run inside a dedicated Web Worker. The main thread hosts only:

- Passive event listeners (`{ passive: true }`) that `postMessage` raw events to the worker
- A `DomScanner` that detects username fields and hashes the value before crossing to the worker
- SPA route listeners (`pushState`/`replaceState`/`popstate` patch)
- `visibilitychange` and `pagehide` listeners
- The `KProtect` public facade (thin proxy to worker messages)

**Nothing else runs on the main thread after `init()` returns.**

### 1.2 Thread topology

```
Main thread (host page)
├── KProtect public facade (~2KB, no collector imports)
├── EventTaps (passive listeners → postMessage to Worker)
│   └── keydown/up, pointermove/down/up, touchstart/end/move,
│       scroll, visibilitychange, pagehide, focus/blur,
│       submit, click, popstate, pushState (patched)
└── DomScanner (MutationObserver on username selectors only,
               detaches after first capture)

Worker thread (kprotect.worker.js — the brain)
├── SessionManager   — id, pulse loop, lifecycle, idle timeout
├── IdentityStore    — username + device_uuid (bridges to persistent storage)
├── PageGate         — URL matching, page_class transitions
├── Collectors       — keystroke / pointer / touch / sensor / credential
├── FeatureExtractor — pure functions, discards raw events post-extract
├── BatchAssembler   — 30s batches, pulse-aligned
├── Transport        — gzip + fetch POST, retries, queue, keepalive flag
└── Router           — drop / buffer / send-on-pulse / send-immediate
```

### 1.3 Worker instantiation

```ts
// Primary: blob URL (survives strict CSP with worker-src blob:)
const blob = new Blob([WORKER_SOURCE], { type: 'application/javascript' });
const worker = new Worker(URL.createObjectURL(blob));

// Fallback: if Worker() throws, run worker modules on main thread
// via requestIdleCallback (or setTimeout(fn, 0) where rIC unavailable).
// Log once at debug level. Never surface to host app.
```

### 1.4 postMessage protocol

- All main→worker messages use transferable `ArrayBuffer` for raw event payloads (zero-copy).
- All main→worker messages are typed discriminated unions from `wire-protocol.ts`.
- Worker→main messages are typed responses (drift scores, session state).
- **Never** send raw DOM objects, closures, or `Element` references across the boundary.

### 1.5 Forbidden on the main thread

After `init()` completes, the main thread MUST NOT:

- Run feature extraction (zone matrices, velocity histograms, correlations)
- Compress payloads
- Access IndexedDB
- Execute regex matching on URL patterns
- Schedule `setInterval` timers (pulse loop lives in worker)

**Forbidden browser APIs (anywhere in SDK code):**

- Dynamic code execution via string arguments: `eval`-equivalent APIs, the `Function` constructor invoked with string arguments, `setTimeout`/`setInterval` with a string as the first argument (always pass a function reference instead)
- Legacy document-writing APIs (`document.write`, `document.writeln`) — use DOM methods (`createElement`, `appendChild`) instead
- `innerHTML` assignment — use `textContent` or explicit DOM construction
- Synchronous XHR (`open(..., false)`)

---

## 2. Zero-Config Principle

### 2.1 The one required call

```ts
KProtect.init({ api_key: 'kp_live_abc...' });
```

That is the entire integration. Everything else — identity capture, session management, pulse cadence, page gating, critical actions, transport mode — has a safe default and runs without customer configuration.

### 2.2 Defaults file is the source of truth

All tunable defaults MUST live in exactly one file: `packages/sdk-web/src/config/defaults.ts`. No magic numbers elsewhere. If a constant appears in two places, it belongs in defaults.

### 2.3 Override shape

Customers who need custom behavior pass an `overrides` block. The shape must be:

```ts
KProtect.init({
  api_key: 'kp_live_abc...',
  overrides: {
    transport:        { mode?: 'direct' | 'proxy', endpoint?: string },
    session:          { pulse_interval_ms?: number, idle_timeout_ms?: number, keepalive_interval_ms?: number },
    identity:         { username?: UsernameCaptureConfig },
    page_gate:        { opt_out_patterns?: (string | RegExp)[] },
    critical_actions: { actions?: CriticalAction[] },
    environment:      'production' | 'debug',
  }
});
```

Every `?` field has a default. Partial overrides are merged with defaults (deep merge for arrays, shallow merge for objects). Host apps NEVER need to provide a complete config.

### 2.4 No per-page SDK calls

Customers MUST NOT be required to call any SDK function on individual pages. URL-matching config handles all per-page behavior. If a feature requires a per-page call, it is not zero-config and must be redesigned.

---

## 3. Bundle Budget

| Artifact | Max size (gzip) |
|---|---|
| `kprotect.min.js` (main thread facade + event taps) | 15 KB |
| `kprotect.worker.js` (full worker bundle) | 40 KB |
| Combined | 55 KB |

### 3.1 Rules

- **Zero runtime dependencies.** No lodash, axios, uuid library, idb library, or any npm package with side effects. Use native browser APIs only.
- **Tree-shakeable named exports.** No default export that imports everything.
- **Dynamic imports for collector modules.** If a customer opt-out config means a collector will never fire, the collector module should never load. Use `import()` inside the worker.
- **Rollup with `format: 'iife'`** for the main bundle (script-tag compatible). Separate entry for the worker.
- **No TypeScript `lib.dom.d.ts` bleedthrough into tests.** Worker types via `lib: ["webworker"]` in a separate tsconfig.

### 3.2 CI enforcement

A Rollup `bundlesize` check runs on every PR. PRs that exceed the size budget are blocked.

---

## 4. Performance Budget

| Metric | Limit | Measurement |
|---|---|---|
| Main thread blocking time (post-init, 10s idle) | < 50ms total | Playwright `performance.measure` |
| CPU usage (idle browsing) | < 2% | Chrome Performance profiler |
| CPU usage (active typing/clicking) | < 5% | Chrome Performance profiler |
| Heap contribution | < 5 MB | Chrome Memory snapshot |
| Worker heap | < 10 MB | Worker `performance.measureUserAgentSpecificMemory` |

### 4.1 Rules

- Use `{ passive: true }` on ALL event listeners.
- Use `performance.now()` for ALL timestamps. Never `Date.now()`, never `new Date()`.
- Debounce high-frequency events (scroll, pointermove) before posting to worker. Default debounce: 16ms (one frame).
- Feature extraction windows are 30s. Raw events are discarded immediately after extraction (not buffered).
- Pulses with fewer than `MIN_EVENTS_FOR_PULSE` (10) events are skipped — no batch is sent for near-empty windows. This avoids sending noise to the server.
- The bounded ring buffer for pre-username events holds at most 30 windows (~15 min). Oldest windows dropped on overflow — never grow unbounded.

### 4.2 Synthetic benchmarks

`packages/sdk-web/src/__benchmarks__/` must contain fixtures that:
1. Simulate 1,000 events/10s and assert main-thread blocking < 50ms.
2. Assert memory < 5MB after 60s of simulated activity.

These run in CI via Vitest with a `--reporter=verbose` flag. Benchmark regressions fail the build.

---

## 5. Privacy Invariants

These rules are NON-NEGOTIABLE. They derive from the behavioral biometrics spec §13 rules 1-8.

### 5.1 What is NEVER captured, stored, or transmitted

- **Raw keystroke content** (which keys were pressed, the text typed). Only timing and zone metadata.
- **Raw mouse positions** (absolute screen coordinates). Only velocity, acceleration, zones.
- **PII of any kind**: name, email, phone, address, card number, IP address in SDK payloads.
- **The username plaintext value** after hashing. It is hashed on the main thread via `crypto.subtle.digest('SHA-256', ...)`. The hash only crosses to the worker. The plaintext is never stored anywhere by the SDK.

### 5.2 Hashing rule

Username hashing happens on the **main thread**, **before** the value is posted to the worker. The worker ONLY ever sees `user_hash`. It never reconstructs the username.

```ts
// On main thread, inside DomScanner
const encoder = new TextEncoder();
const data = encoder.encode(inputElement.value);
const hashBuffer = await crypto.subtle.digest('SHA-256', data);
const hashArray = Array.from(new Uint8Array(hashBuffer));
const user_hash = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
// POST user_hash to worker — raw value is never referenced again
```

### 5.3 Zone IDs, not coordinates

Pointer and touch collectors report zone IDs (from the pre-registered zone map), not pixel coordinates. The zone map is built once on page load and stored in the worker. Absolute coordinates are discarded after zone-ID assignment.

### 5.4 Raw event discard

After a feature extraction window closes (every 30s), the raw event queue for that window is cleared. The worker holds extracted features only — timing aggregates, histograms, matrices. Raw event arrays are garbage-collected.

### 5.5 Credential field special handling

For credential fields (`input[type="password"]`), ONLY the behavioral metadata is captured: typing rhythm (dwell + flight times), correction patterns (backspace counts), paste detection, and autofill detection. The field value is never read. Confirmed via a `type === 'password'` guard on the collector — value access is a compile-time forbidden path.

### 5.6 Zone index validation

Keystroke zone IDs MUST be validated before feature extraction. Invalid zone indices (negative, out-of-range, or non-integer) are rejected or clamped to the valid range before being used in zone transition matrices or field breakdowns. This prevents corrupted zone data from poisoning feature vectors and drift scoring.

### 5.7 Credential `available` flag semantics

The `available` field on `CredentialSignal` MUST be `true` only when actual credential behavioral data is present (at least one of `password_field`, `username_field`, or `form` is non-null with real data). Setting `available: true` on an empty signal produces false positives in the server's feature ingestor.

---

## 6. Identity Model

The SDK manages four distinct identifiers with four distinct lifetimes.

### 6.1 Identifier table

| Identifier | What it is | Storage | Lifetime | Transmitted? |
|---|---|---|---|---|
| `session_id` | Random UUID per tab | `sessionStorage['kp.sid']` + worker memory | Tab close / logout / destroy | Yes — every batch |
| `user_hash` | SHA-256 of username | Worker memory only (re-derived each session) | Session | Yes — every batch |
| `device_uuid` | Random UUID, minted once per browser-origin | `localStorage['kp.did']` + IndexedDB fallback | Until explicit `clearIdentity` | Yes — every batch |
| `username` (raw) | The actual account identifier | `localStorage['kp.un']` (encrypted in production mode) | Until `logout()` or `clearIdentity` | Never (hash only) |

### 6.2 Username is mandatory for transmission

```
username captured? → YES → transport ON, drain ring buffer
username captured? → NO  → collectors run, features extracted,
                           transport OFF, ring buffer accumulates
```

The SDK never sends a `BehavioralBatch` without `user_hash`. The server MUST reject batches missing `user_hash`.

### 6.3 Device UUID semantics

`device_uuid` is a **hint, not an assertion**. It helps the server build a trusted-device baseline and detect device substitution. The server MUST NOT use it as a sole authentication factor. Behavioral drift is the authoritative signal.

Device UUID is wiped only on explicit `kp.destroy({ clearIdentity: true })`. It survives:
- Browser restart
- Tab close
- Session end
- Logout (logout clears username but NOT device_uuid — this is intentional)

### 6.4 Username capture — selector-based

```ts
type UsernameSelector = {
  selector: string;       // CSS selector, e.g. 'input[name="username"]'
  url?: string;           // optional URL pattern, e.g. "/login"
  event?: 'blur' | 'change' | 'submit';  // default 'blur'
};
```

Default selectors shipped with the SDK (cover 80% of banking apps with zero config):

```ts
const DEFAULT_USERNAME_SELECTORS: UsernameSelector[] = [
  { selector: 'input[name="username"]',    url: '/login' },
  { selector: 'input[name="phoneNumber"]', url: '/login' },
  { selector: 'input[name="email"]',       url: '/login' },
  { selector: 'input[name="username"]',    url: '/signup' },
  { selector: 'input[name="phoneNumber"]', url: '/signup' },
  { selector: 'input[name="email"]',       url: '/signup' },
];
```

SSO globals polled once on init and on each route change:
```ts
sso: { globals: ['window.__KP_USER__'] }  // integrator sets window.__KP_USER__ in their SSO callback
```

### 6.5 Storage resilience

```ts
// localStorage primary, IndexedDB fallback (survives "clear cookies" in some browsers)
async function getOrCreateDeviceUuid(): Promise<string> {
  let uuid = localStorage.getItem('kp.did');
  if (uuid && isValidUuid(uuid)) return uuid;

  uuid = await idbGet('kp.did');
  if (uuid && isValidUuid(uuid)) {
    localStorage.setItem('kp.did', uuid); // heal localStorage
    return uuid;
  }

  uuid = crypto.randomUUID();
  localStorage.setItem('kp.did', uuid);
  await idbSet('kp.did', uuid);
  return uuid;
}
```

---

## 7. Session Lifecycle

### 7.1 State diagram

```
                    ┌──────────────────────────────────────────────────────┐
                    │                    UNINITIALIZED                      │
                    └──────────────────────┬───────────────────────────────┘
                                           │ KProtect.init()
                                           ▼
                    ┌──────────────────────────────────────────────────────┐
                    │               ACTIVE (no username)                    │
                    │  collectors: ON  │  transport: OFF  │  ring: filling  │
                    └──────────────────┬───────────────────────────────────┘
                                       │ username captured
                                       ▼
                    ┌──────────────────────────────────────────────────────┐
                    │              ACTIVE (username known)                  │
                    │  collectors: ON  │  transport: ON   │  pulse loop: ON │
                    └───┬──────────────┬──────────────────┬────────────────┘
                        │              │                  │
                tab hidden        idle timeout       pagehide/logout/destroy
                >15 min              fires                  fires
                        │              │                  │
                        ▼              ▼                  ▼
                    SUSPENDED      SUSPENDED           TERMINATED
                (pulse paused)  (pulse paused)    (session_end sent,
                                                   buffer flushed)
                        │              │
              visible again        visible again
              < idle_timeout      > idle_timeout
                        │              │
                        ▼              ▼
                    ACTIVE         NEW SESSION
                  (resume)      (new session_id,
                               old session_end sent)
```

### 7.2 Session start conditions

A new session starts when:
1. `KProtect.init()` is called on a fresh tab (no existing `sessionStorage['kp.sid']`)
2. An idle-timeout fires while the tab is hidden and the user returns after the timeout

### 7.3 Session end conditions

A session ends (sends `session_end`, flushes buffers) when ANY of:
1. `pagehide` fires with `persisted === false` → use `navigator.sendBeacon`
2. `KProtect.logout()` is called
3. `KProtect.destroy()` is called
4. `visibilitychange` → hidden, and the tab remains hidden for > `idle_timeout_ms` (default 15 min). On return, a NEW session is created and the old `session_end` is sent lazily.

### 7.4 Multi-tab rule: one session per tab

`session_id` lives in `sessionStorage` — it is physically impossible for two tabs to share it. This is the correct semantics: each tab is an independent interaction context. The server correlates tabs via `user_hash` + `device_uuid`.

**Never attempt to synchronize `session_id` across tabs.** `BroadcastChannel`, `SharedWorker`, and `localStorage` session propagation are all forbidden for this purpose.

### 7.5 Logout behavior

`KProtect.logout()`:
1. Sends `session_end` batch for the current session
2. Clears `localStorage['kp.un']` (username) and `sessionStorage['kp.sid']`
3. Resets `user_hash` in worker memory to `null`
4. Keeps `device_uuid` intact (logout does NOT clear device identity)
5. Puts transport back in gated-off state until next username capture

---

## 8. Pulse Contract

### 8.1 What a pulse is

A pulse is a scheduled transmission of accumulated behavioral feature windows. It is NOT a raw event dump — it is a batch of extracted features plus session metadata.

The pulse counter (`pulse`) is a **monotonic integer** starting at `0` on session start. It increments by exactly `1` per pulse tick, regardless of how many events occurred or how many ticks were skipped while paused.

### 8.2 Two cadences

| Page class | Pulse type | Default interval | Payload |
|---|---|---|---|
| `normal` | Full batch | 30,000ms | Complete feature windows (skipped if < 10 events in window) |
| `critical_action` | Keepalive | 30,000ms | `{session_id, pulse, page_context, device_uuid, user_hash}` only — NO behavioral data |

Only one cadence is active at a time. `PageGate` switches them on URL change.

### 8.3 Pause conditions

The pulse loop **pauses** (skips ticks, does NOT increment counter) when:
- `document.visibilityState === 'hidden'` — background tabs are throttled, sending ghost pulses wastes bandwidth
- Transport is gated off (no username captured yet)

On resume after a pause, the loop sends exactly one catch-up batch containing all features accumulated during the pause window. The counter increments by 1 for this catch-up batch — not by the number of missed ticks.

### 8.4 Minimum event threshold

Pulse windows with fewer than `MIN_EVENTS_FOR_PULSE` (default: 10) raw events are skipped entirely — no batch is assembled or transmitted. This prevents sending near-empty windows that would add noise to the server's drift scoring model. The pulse counter still increments on skipped windows to maintain monotonicity. The threshold is defined in `config/defaults.ts`.

### 8.5 Wire format additions to BehavioralBatch header

The following fields extend the spec §8 definition:

```ts
interface BatchHeader {
  // ... existing spec fields ...
  session_id: string;            // per-tab UUID
  pulse: number;                 // monotonic counter from 0
  pulse_interval_ms: number;     // actual interval used (server detects gaps)
  device_uuid: string;           // persistent device hint
  user_hash: string;             // SHA-256(username)
  page_context: {
    url_path: string;            // URL path only, no query params (privacy)
    page_class: 'normal' | 'critical_action' | 'opted_out';
    critical_action?: string;    // e.g. 'payment_confirm', 'login_submit'
  };
}
```

---

## 9. Page Gating

### 9.1 Three page classes

| Class | Collection | Pulse | Transport |
|---|---|---|---|
| `normal` | ON | Full cadence (30s) | ON if username known |
| `critical_action` | ON (held in staging buffer) | Keepalive only (30s) | ON for keepalives only; behavioral data sent at commit |
| `opted_out` | OFF (collectors sleep) | OFF | OFF |

### 9.2 SPA route detection

The SDK patches `history.pushState` and `history.replaceState` to intercept SPA navigation:

```ts
const originalPushState = history.pushState.bind(history);
history.pushState = (...args) => {
  originalPushState(...args);
  bridge.postRouteChange(location.pathname);
};
```

`popstate` is also listened to. All route changes trigger `PageGate.evaluate(newPath)` in the worker.

### 9.3 Opt-out behavior

When a page enters `opted_out` class:
- Collectors call `sleep()` (listeners stay attached, enqueue functions short-circuit)
- Pulse loop skips tick
- Any features buffered during the transition are discarded

### 9.4 Collector sleep contract

Every collector MUST implement `sleep()` and `wake()` methods:

```ts
enqueue(event: RawEvent): void {
  if (this.sleeping) return;  // first line — short-circuit costs ~1ns
  // ... rest of enqueue logic
}
```

This avoids the overhead of `addEventListener`/`removeEventListener` on every route change.

---

## 10. Critical-Action Protocol

### 10.1 What a critical-action page is

A page matching a pattern in `critical_actions.actions[].page`. On these pages, the complete behavioral signal for the entire page visit is sent as a single batch at commit — not pulsed continuously.

### 10.2 Staging buffer

On entering a critical-action page:
1. `PageGate` transitions to `critical_action`
2. Collectors continue running normally
3. Extracted feature windows go into the **staging buffer** (per-action, in worker memory)
4. Normal pulse loop replaced by keepalive loop (30s, liveness only)

Staging buffer is:
- Worker memory only (never persisted)
- Unbounded within a single page visit
- Cleared on commit OR navigation-away

### 10.3 Commit detection

```
Main thread: click on [data-kp-commit="payment"] detected
→ postMessage({ type: 'CRITICAL_ACTION_COMMIT', action: 'payment_confirm' }) to worker
Worker: seals staging buffer → creates CriticalActionBatch with committed: true
→ sends immediately (not pulse-aligned), priority: high
→ clears staging buffer
```

### 10.4 Abandoned transaction

```
Worker receives ROUTE_CHANGE while page_class === 'critical_action'
→ creates CriticalActionBatch with committed: false
→ sends immediately (abandoned checkout is a fraud signal)
→ clears staging buffer
```

### 10.5 CriticalActionBatch wire type

```ts
interface CriticalActionBatch extends BehavioralBatch {
  type: 'critical_action';
  page_context: {
    page_class: 'critical_action';
    critical_action: string;
    committed: boolean;
  };
}
```

### 10.6 Default critical actions

```ts
const DEFAULT_CRITICAL_ACTIONS: CriticalAction[] = [
  { page: /\/login/,        action: 'login_submit',      commit: { selector: 'button[type="submit"]' } },
  { page: /\/signup/,       action: 'signup_submit',     commit: { selector: 'button[type="submit"]' } },
  { page: /\/transfer/,     action: 'transfer_confirm',  commit: { selector: '[data-kp-commit="transfer"], button[type="submit"]' } },
  { page: /\/payment/,      action: 'payment_confirm',   commit: { selector: '[data-kp-commit="payment"], button[type="submit"]' } },
  { page: /\/password/,     action: 'password_change',   commit: { selector: 'button[type="submit"]' } },
  { page: /\/profile.*sec/, action: 'security_change',   commit: { selector: 'button[type="submit"]' } },
];
```

---

## 11. Transport Contract

### 11.1 Two integration modes

**Mode A — Direct (default)**: SDK posts directly to `https://api.kprotect.io/v1/behavioral/ingest`. SDK fires events with the response. Host app reads from SDK events/getters.

**Mode B — Proxy**: For customers with regulatory requirements:
```ts
overrides: { transport: { mode: 'proxy', endpoint: 'https://bank.example.com/kp-proxy/ingest' } }
```
Both modes fire the same client-side events. A customer can use both simultaneously.

### 11.2 Request format

```
POST /v1/behavioral/ingest
Content-Type: application/octet-stream
Content-Encoding: gzip
X-KP-API-Key: kp_live_abc...
X-KP-Session: {session_id}
X-KP-Device: {device_uuid}
```

Payload: `BehavioralBatch` serialized to JSON, then gzip-compressed via `CompressionStream('gzip')`.
Fallback for browsers without `CompressionStream`: send uncompressed with `Content-Type: application/json`.

### 11.3 Fetch options

```ts
fetch(endpoint, {
  method: 'POST',
  keepalive: true,     // ensures delivery even if page is unloading
  headers: { ... },
  body: compressedPayload,
});
```

On `pagehide` with `persisted === false`:
```ts
navigator.sendBeacon(endpoint, compressedPayload);
```

### 11.4 Retry policy

| Condition | Action |
|---|---|
| HTTP 2xx | Success, clear from retry queue |
| HTTP 429 | Backoff: 2s → 4s → 8s → 16s (max 4 retries) |
| HTTP 5xx | Backoff: 1s → 2s → 4s (max 3 retries) |
| Network error | Backoff: 1s → 2s → 4s (max 3 retries) |
| HTTP 4xx (non-429) | Drop, log at debug level (do NOT retry) |
| Queue depth > 50 batches | Drop oldest, keep newest (ring eviction) |

### 11.5 Replay protection

Each batch carries a `batch_id` (UUID) and `sent_at` timestamp. Server MUST reject:
- Duplicate `batch_id` within 24h
- Batches with `sent_at` > 5 min in the past

---

## 12. Storage Contract

All SDK keys namespaced under `kp.` to avoid collisions.

| Key | Storage | Value | Lifetime |
|---|---|---|---|
| `kp.sid` | `sessionStorage` | Session UUID | Tab close |
| `kp.un` | `localStorage` (encrypted in prod) | Raw username string | Until `logout()` or `clearIdentity` |
| `kp.did` | `localStorage` + IndexedDB mirror | Device UUID | Until `clearIdentity` |
| `kp.cfg` | `localStorage` | Serialized merged config | Until `destroy()` |

### 12.1 Encryption at rest

In `environment: 'production'`, `kp.un` is AES-GCM encrypted via `crypto.subtle`. The key lives in `sessionStorage['kp.k']` (tab-scoped, never persists). This protects against naive localStorage readers — TLS handles transit security.

### 12.2 IndexedDB wrapper

Minimal 30-line wrapper (no external library). Store name: `kp-bio`. Object store: `kv` with keyPath `k`.

### 12.3 Quota handling

If `localStorage.setItem` throws `QuotaExceededError`: log at debug level, continue with in-memory fallback. Never throw to the host page.

---

## 13. Error Handling

### 13.1 The golden rule

**The SDK MUST NEVER:**
- Throw an unhandled exception into the host page's global scope
- Reject an unhandled Promise that propagates to the host page
- Block page load or navigation
- Write to `console.error` in production mode (debug mode only)

### 13.2 Wrap every browser API call

```ts
try {
  localStorage.setItem('kp.did', uuid);
} catch {
  this.memoryFallback.set('kp.did', uuid);
}
```

This applies to: `localStorage`, `sessionStorage`, IndexedDB, `Worker`, `crypto.subtle`, `CompressionStream`, `navigator.sendBeacon`, `fetch`, `history.pushState` patching.

### 13.3 Worker crash recovery

If `worker.onerror` fires:
1. Append to internal debug log (bounded ring, max 20 entries)
2. Attempt restart once after 2s
3. If second start fails → fall back to main-thread idle-scheduler mode
4. Log one debug message: `KProtect: worker unavailable, running in fallback mode`
5. NEVER throw to the host page

### 13.4 Failed signals

If a collector fails to attach (`PointerEvent` not supported, etc.), the batch is sent with that signal type marked `unavailable: true`. Collection failures are never fatal.

---

## 14. Security Requirements

### 14.1 No dynamic code execution from strings

The SDK MUST NOT execute code constructed at runtime from string data. Specifically:
- Do not pass strings to `setTimeout`/`setInterval` as the first argument — always pass a function reference
- Do not use the `Function` constructor to compile strings into executable code
- Do not use any `eval`-equivalent API that compiles and runs strings
- ESLint rules `no-implied-eval` and `no-new-func` enforce this at the lint level and are required in the SDK's ESLint config

### 14.2 DOM safety

- Use `textContent` or explicit `createElement`/`appendChild` for any SDK-controlled DOM manipulation
- Never assign to `innerHTML` in SDK code
- Never call legacy document-writing APIs

### 14.3 Content Security Policy

Minimum required directives on the host page:

```
Content-Security-Policy:
  connect-src 'self' https://api.kprotect.io;
  worker-src blob:;
```

No `unsafe-eval` and no `unsafe-inline` are needed. If `worker-src blob:` is unavailable, SDK silently falls back to main-thread mode.

### 14.4 Input sanitization

URL patterns supplied as strings are matched via `String.prototype.includes()` or exact match — no runtime regex construction from strings. Integrators who supply `RegExp` patterns own their own regex safety. The SDK never constructs regex from untrusted input.

### 14.5 API key handling

The API key:
- Stored only in worker memory (never in `localStorage` or `sessionStorage`)
- Sent in `X-KP-API-Key` request header (not in URL)
- Never logged (even in debug mode)
- Is a public-facing key that authenticates the origin domain, not the individual user

### 14.6 HMAC signing (production mode)

In `environment: 'production'`, every batch is signed per spec rule 13. Key derivation and HMAC are performed inside the worker using `crypto.subtle`. Signature sent in `X-KP-Sig` header. Not applied in debug mode.

---

## 15. Public API Surface

This is the stable contract. Changes to these signatures are BREAKING CHANGES requiring a major version bump.

```ts
// ─── Required ────────────────────────────────────────────────────────────────

KProtect.init(config: KProtectConfig): void;

interface KProtectConfig {
  api_key: string;              // required
  overrides?: KProtectOverrides; // all optional, see §2.3
}

// ─── Events ──────────────────────────────────────────────────────────────────

type KProtectEvent =
  | 'drift'              // DriftScoreResponse received from server
  | 'alert'              // Critical/block-level alert from server
  | 'critical_action'    // CriticalActionBatch response received
  | 'session_start'      // New session_id minted
  | 'session_end'        // Session terminated
  | 'username_captured'; // Username captured (user_hash now available)

KProtect.on(event: KProtectEvent, callback: (data: unknown) => void): () => void;
// Returns an unsubscribe function

// ─── Getters ─────────────────────────────────────────────────────────────────

KProtect.getLatestDrift(): DriftScoreResponse | null;
// Synchronous, returns last cached response. null if no response yet.

KProtect.getSessionState(): SessionState | null;
// Returns { session_id, pulse, page_class, username_captured, auth_state }

// ─── Challenge (optional active verification) ────────────────────────────────

KProtect.challenge.generate(opts: { purpose: string }): Promise<ChallengeResult>;
KProtect.challenge.verify(challenge_id: string, inputEl: Element): Promise<VerifyResult>;

// ─── Lifecycle ───────────────────────────────────────────────────────────────

KProtect.logout(): void;
// Clears username, ends session, keeps device_uuid

KProtect.destroy(opts?: { clearIdentity?: boolean }): void;
// Stops worker, flushes buffers.
// clearIdentity: true → also clears kp.un, kp.did, IndexedDB kp-bio
```

### 15.1 Versioning

Semantic versioning. `api_key` prefix encodes API version: `kp_live_v2_abc...`. SDK warns once at init if key version is incompatible.

---

## 16. Code Review Checklist

Use this checklist on EVERY PR that touches SDK code.

### Threading (§1)
- [ ] No synchronous work >1ms after `init()` on main thread
- [ ] Feature extraction is in the worker, not in bridge
- [ ] All event listeners use `{ passive: true }`
- [ ] No string-based code execution anywhere (lint passes)
- [ ] `postMessage` data is a typed wire-protocol message
- [ ] No DOM objects or closures cross the main↔worker boundary

### Zero-config (§2)
- [ ] New tunables have defaults in `config/defaults.ts`
- [ ] No new required fields in `KProtectConfig`
- [ ] No per-page SDK calls required from host app

### Bundle (§3)
- [ ] No new npm runtime dependencies
- [ ] `bundlesize` CI check passes
- [ ] New collectors are dynamically imported

### Performance (§4)
- [ ] `performance.now()` used for all timestamps
- [ ] High-frequency events debounced before `postMessage`
- [ ] No unbounded arrays or maps in worker memory

### Privacy (§5)
- [ ] No raw keystroke content anywhere in call chain
- [ ] Username hashed on main thread BEFORE posting to worker
- [ ] Raw events discarded after feature extraction
- [ ] No pixel coordinates in any wire type (zone IDs only)
- [ ] No `input[type="password"]` value read at any point

### Identity (§6)
- [ ] `session_id` only in `sessionStorage` and worker memory
- [ ] `device_uuid` in `localStorage` + IndexedDB (never `sessionStorage`)
- [ ] Transport gated off until `user_hash` available
- [ ] `device_uuid` NOT cleared on `logout()` (only on `clearIdentity`)

### Session (§7)
- [ ] No cross-tab session_id synchronization
- [ ] `pagehide` uses `sendBeacon`
- [ ] Idle timeout fires in worker, not main thread
- [ ] `logout()` clears username but not device_uuid

### Pulses (§8)
- [ ] Pulse counter increments by 1 per tick (not missed count)
- [ ] Pulse pauses when `visibilityState === 'hidden'`
- [ ] Catch-up batch sent on resume (one batch, one increment)
- [ ] Keepalive carries NO behavioral payload

### Page gating (§9)
- [ ] Opted-out pages: collectors sleep, pulse skipped, buffered features discarded
- [ ] `pushState`/`replaceState` patches post route change to worker
- [ ] Collectors use `sleep()`/`wake()` pattern

### Critical actions (§10)
- [ ] Staging buffer held until commit or navigation-away
- [ ] `committed: false` sent on navigation-away (not dropped)
- [ ] `committed: true` batch sent with `priority: high`
- [ ] Keepalive during critical-action carries no behavioral data

### Transport (§11)
- [ ] `keepalive: true` on all fetch calls
- [ ] `sendBeacon` used on `pagehide`
- [ ] 4xx-non-429 treated as permanent failure (no retry)
- [ ] Queue depth capped at 50 batches
- [ ] `batch_id` UUID generated per batch

### Storage (§12)
- [ ] All keys prefixed with `kp.`
- [ ] `QuotaExceededError` caught and handled
- [ ] `kp.un` encrypted at rest in production mode
- [ ] No unbounded storage growth

### Error handling (§13)
- [ ] Every browser API call wrapped in try/catch
- [ ] No unhandled Promise rejections to host page
- [ ] Worker crash triggers restart then idle-scheduler fallback
- [ ] No `console.error` in production paths

### Security (§14)
- [ ] ESLint `no-implied-eval` and `no-new-func` pass with zero violations
- [ ] API key only in worker memory and request header
- [ ] HMAC signing present for production mode
- [ ] No `innerHTML` assignments in SDK code
- [ ] No legacy document-writing API calls

### API surface (§15)
- [ ] No new required parameters in stable API methods
- [ ] `on()` returns an unsubscribe function
- [ ] Version tag in `api_key` validated on init

---

## 17. Android SDK Addendum

> Language: Kotlin. Min SDK: API 24 (Android 7.0). Target SDK: API 34.

### 17.1 Threading model

- **Main thread rule is identical**: zero blocking work on the Android main (UI) thread.
- Use a dedicated `HandlerThread` named `kp-bio-worker` for all processing. Equivalent to the Web Worker.
- Event collectors post `Message` objects to the handler's `Looper` — fire-and-forget.
- Sensors (accelerometer, gyroscope) use `SensorManager.registerListener` with `SENSOR_DELAY_UI` (16ms) on the worker thread.

### 17.2 Identity storage

| Identifier | Android Storage | Notes |
|---|---|---|
| `session_id` | In-memory only | Cleared on `Activity.onDestroy` |
| `device_uuid` | `EncryptedSharedPreferences` (Jetpack Security) | AES-256-GCM at rest |
| `username` (raw) | `EncryptedSharedPreferences` | Same key as device_uuid store |
| `user_hash` | In-memory (worker thread) | Re-derived per session |

`EncryptedSharedPreferences` wraps Android Keystore — the encryption key never leaves secure hardware on API 28+.

### 17.3 Username capture

- Standard text field: observe `TextWatcher.afterTextChanged` on fields matching selector config.
- Hash on the calling thread using `MessageDigest.getInstance("SHA-256")`.
- Pass hash only to the worker `HandlerThread`.
- For SSO flows: expose `KProtect.setUsername(username: String)` — the app calls this from its SSO callback.

### 17.4 Session lifecycle hooks

```kotlin
// In Application.onCreate()
KProtect.init(context, apiKey = "kp_live_abc...")

// In Activity.onStop() → send session heartbeat
// In Activity.onDestroy() → flush and send session_end
// ProcessLifecycleOwner.get().lifecycle.addObserver(kpLifecycleObserver)
```

Use `ProcessLifecycleOwner` to detect app-to-background transitions (equivalent to `visibilitychange`). Use `ActivityLifecycleCallbacks` for per-screen (page) events.

### 17.5 Transport

- `OkHttp` with a dedicated `Dispatcher` (2 threads max, named `kp-transport`).
- GZIP via `OkHttp` `RequestBody` compression interceptor.
- Respect spec retry policy. Use `OkHttp` `Interceptor` for retry logic.
- On app-kill: use `WorkManager` `OneTimeWorkRequest` with `EXPEDITED` run mode to flush the pending queue.

### 17.6 Page gating equivalent

Android has no URLs — use `Activity` class names and `Fragment` tags:

```kotlin
page_gate: {
  opt_out_activities: listOf("MarketingActivity", "OnboardingActivity"),
  critical_action_activities: mapOf(
    "PaymentActivity" to CriticalAction("payment_confirm", R.id.confirm_button),
    "TransferActivity" to CriticalAction("transfer_confirm", R.id.submit_transfer),
  )
}
```

### 17.7 Performance budget (Android)

| Metric | Limit |
|---|---|
| Main thread blocking (per event tap) | < 0.5ms |
| Background CPU (idle) | < 1% |
| Memory overhead | < 10 MB |

Measure with Android Profiler. CI uses `benchmark:connectedCheck` with `BenchmarkRule`.

### 17.8 Bundle size

- AAR file: < 200 KB
- No transitive dependencies beyond Jetpack Security and OkHttp (both are already common in banking apps)
- ProGuard rules shipped with the AAR to prevent minification of public API classes

---

## 18. iOS SDK Addendum

> Language: Swift 5.9+. Min deployment: iOS 16.0. Frameworks: Foundation, CryptoKit, UIKit/SwiftUI.

### 18.1 Threading model

- **Main thread rule is identical**: zero blocking work on the main queue.
- Use a private `DispatchQueue(label: "io.kprotect.bio-worker", qos: .utility)` for all processing. Serial queue — equivalent to the Web Worker.
- Event collectors post `DispatchWorkItem` closures to the worker queue — fire-and-forget.
- CoreMotion events: `CMMotionManager` with `deviceMotionUpdateInterval = 0.016` (16ms), updates delivered on the worker queue's underlying `OperationQueue`.

### 18.2 Identity storage

| Identifier | iOS Storage | Notes |
|---|---|---|
| `session_id` | In-memory only | Cleared on `applicationWillTerminate` |
| `device_uuid` | Keychain (kSecClassGenericPassword) | `kSecAttrAccessibleAfterFirstUnlock` |
| `username` (raw) | Keychain (kSecClassGenericPassword) | Same accessibility as device_uuid |
| `user_hash` | In-memory (worker queue) | Re-derived per session |

Keychain items use the app's bundle ID as the service name to isolate per-app. Items survive app reinstall only if `kSecAttrSynchronizable = false` (default).

### 18.3 Username capture

- Standard UITextField: use `UITextField.addTarget(_, action:, for: .editingDidEnd)` for `blur`-equivalent.
- SwiftUI: use `.onSubmit {}` or `.onChange(of: binding)` depending on field type.
- Hash immediately on receipt: `SHA256.hash(data: Data(username.utf8))`.
- Pass hash only to the worker queue. Raw username never escapes the hashing closure.
- For SSO: expose `KProtect.setUsername(_ username: String)` — called from the SSO delegate.

### 18.4 Session lifecycle hooks

```swift
// In AppDelegate.application(_:didFinishLaunchingWithOptions:)
KProtect.initialize(apiKey: "kp_live_abc...")

// Use NotificationCenter observers:
// UIApplication.didEnterBackgroundNotification → suspend pulse, start idle timer
// UIApplication.willEnterForegroundNotification → resume or new session
// UIApplication.willTerminateNotification → flush and send session_end
```

For SwiftUI apps, use `@Environment(\.scenePhase)` to detect foreground/background transitions.

### 18.5 Transport

- `URLSession` with a dedicated configuration (`URLSessionConfiguration.background(withIdentifier: "io.kprotect.transport")`) for background uploads.
- Gzip via `(data as NSData).compressed(using: .zlib)` (Foundation, iOS 13+) or `Compression.compress`.
- Background `URLSession` survives app-kill — iOS resumes the upload. This is the equivalent of `sendBeacon`.
- On critical batches (`committed: true`): use foreground `URLSession` for immediate delivery.

### 18.6 Page gating equivalent

iOS has no URLs — use `UIViewController` class names and `SceneDelegate` scene identifiers:

```swift
pageGate: KProtectPageGate(
  optOutViewControllers: ["MarketingVC", "OnboardingVC"],
  criticalActionViewControllers: [
    "PaymentConfirmVC": CriticalAction(name: "payment_confirm", buttonTag: 101),
    "TransferVC":       CriticalAction(name: "transfer_confirm", buttonTag: 201),
  ]
)
```

Use `UIViewController` swizzling (or a base class `KPTrackedViewController`) to auto-detect `viewDidAppear`/`viewDidDisappear` events for page transitions.

### 18.7 Performance budget (iOS)

| Metric | Limit |
|---|---|
| Main queue blocking (per event tap) | < 0.5ms |
| Background CPU (idle) | < 1% |
| Memory overhead | < 10 MB |

Measure with Instruments (Time Profiler + Allocations). CI uses XCTest with `XCTMetric` performance tests.

### 18.8 Bundle size

- XCFramework: < 500 KB (fat binary with device + simulator slices)
- Static library preferred over dynamic framework to minimize app launch overhead
- Swift Package Manager support required (no CocoaPods-only)
- Privacy manifest (`PrivacyInfo.xcprivacy`) MUST be shipped with the XCFramework declaring:
  - `NSPrivacyAccessedAPITypes` for `UserDefaults` (if used) and Keychain
  - `NSPrivacyCollectedDataTypes`: behavioral interaction data, device identifiers
  - `NSPrivacyCollectedDataTypePurposes`: fraud prevention

---

*Last updated: 2026-04-09 — K-Protect Engineering*
