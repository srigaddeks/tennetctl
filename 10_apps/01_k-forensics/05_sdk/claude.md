# K-Protect Behavioral Biometrics SDK — Claude Instructions

This is the K-Protect behavioral biometrics project. It produces three platform SDKs (Web, Android, iOS) and a FastAPI server that scores behavioral drift in real time for fraud prevention in banking/fintech apps.

---

## What This Project Is

K-Protect captures how users behave (typing rhythm, pointer movement, touch patterns) without capturing what they type. It compares live behavior against a per-user baseline to detect account takeovers, bots, and session hijacking — invisibly, with a single `init()` call.

**Primary SDK**: `packages/sdk-web` — TypeScript, browser, Web Worker-based.
**Server**: `app/` — FastAPI (Python), drift scorer, baseline builder, alert engine.
**Specs**: `behaviour_biometrics.md` and `device_fingerprinting.md.md` are the authoritative design specs. Read them before making significant changes.

---

## Critical Rules (non-negotiable)

### Privacy
- **Never capture raw keystroke content** — only timing metadata (dwell, flight times)
- **Never capture absolute coordinates** — only zone IDs
- **Username must be SHA-256 hashed on the main thread** before it crosses to the Web Worker
- **Raw events must be discarded immediately** after feature extraction (every 5s window)
- **`input[type="password"]` values are never read** — behavioral metadata only

### Threading (Web SDK)
- **Main thread: event taps only.** All processing (feature extraction, batching, transport) lives in the Web Worker
- **All event listeners use `{ passive: true }`**
- **No synchronous work >1ms on main thread** after `init()` returns
- **Forbidden string-based code execution**: no eval-equivalent APIs, no Function constructor with string args, no setTimeout/setInterval with string first arg

### Identity
- **Username is mandatory for data transmission.** Transport is gated OFF until `user_hash` is set
- **`session_id` lives in `sessionStorage` only** — per-tab, never shared across tabs
- **`device_uuid` lives in `localStorage` + IndexedDB** — survives browser restart
- **`logout()` clears username but NOT `device_uuid`**

### Zero-config
- `KProtect.init({ api_key })` is the only required call
- **All tunable defaults live in `packages/sdk-web/src/config/defaults.ts`** — never hardcode constants elsewhere
- **No per-page SDK calls required** from host apps — URL-matching config handles everything

---

## Architecture (Web SDK)

```
Main Thread                          Web Worker
──────────────                       ─────────────────────────────
KProtect facade (2KB)                SessionManager
  └─ MainThreadBridge                IdentityStore
       ├─ EventTaps (passive)   →    PageGate
       ├─ DomScanner            →    Collectors (6 types)
       ├─ RouteListener         →    FeatureExtractor
       └─ VisibilityListener    →    BatchAssembler → Transport
```

Worker spawned via `new Worker(blobURL)` (blob URL for CSP compatibility). Falls back to `requestIdleCallback` on main thread if `worker-src blob:` is blocked.

---

## Key Files

| File | Purpose |
|---|---|
| `behaviour_biometrics.md` | **Primary spec** — 34 non-negotiable rules, all wire types, collector design |
| `device_fingerprinting.md.md` | Device intelligence spec (out of scope for SDK phase 1) |
| `docs/SDK_BEST_PRACTICES.md` | **The law** — every PR is reviewed against this |
| `docs/ARCHITECTURE.md` | System diagrams (Web + Android + iOS + Server) |
| `docs/WIRE_PROTOCOL.md` | Complete wire format for all batch types |
| `docs/INTEGRATION_GUIDE.md` | Step-by-step for Web, Android, iOS integrators |
| `docs/SERVER_API.md` | All server endpoints + response shapes |
| `packages/sdk-web/src/config/defaults.ts` | **Single source of truth** for all default values |
| `packages/sdk-web/src/runtime/wire-protocol.ts` | **All TypeScript types** for the SDK |

---

## Directory Layout

```
k-bio-main/
├── behaviour_biometrics.md       <- Primary behavioral spec (READ FIRST)
├── device_fingerprinting.md.md   <- Device intelligence spec
├── docs/
│   ├── SDK_BEST_PRACTICES.md     <- PR review law
│   ├── ARCHITECTURE.md
│   ├── WIRE_PROTOCOL.md
│   ├── INTEGRATION_GUIDE.md
│   └── SERVER_API.md
├── packages/
│   └── sdk-web/
│       ├── src/
│       │   ├── config/           <- defaults.ts (single source of truth)
│       │   ├── runtime/          <- wire-protocol.ts, main-thread-bridge.ts,
│       │   │                        worker-entry.ts, main-thread-fallback.ts
│       │   ├── session/          <- session-manager.ts, identity-store.ts,
│       │   │                        username-capture.ts, page-gate.ts,
│       │   │                        critical-action-router.ts
│       │   ├── collectors/       <- keystroke, pointer, touch, scroll,
│       │   │                        sensor, credential
│       │   ├── features/         <- feature extractors + batch-assembler
│       │   ├── transport/        <- transport.ts
│       │   └── index.ts          <- KProtect public facade
│       ├── src/__tests__/        <- Vitest unit tests
│       └── src/__benchmarks__/   <- Performance benchmarks
├── app/                          <- FastAPI server
└── tests/e2e/bio/                <- Robot Framework E2E tests
```

---

## Tech Stack

### Web SDK
- **Language**: TypeScript 5.4+ strict mode
- **Bundler**: Rollup (two outputs: `kprotect.min.js` + `kprotect.worker.js`)
- **Test runner**: Vitest (coverage target >= 80%)
- **Linter**: ESLint with `no-implied-eval` and `no-new-func` rules required
- **Zero runtime npm dependencies** — native browser APIs only
- **Bundle budget**: Main bundle <15KB gzip, worker bundle <40KB gzip

### Server
- **Language**: Python 3.11+
- **Framework**: FastAPI + uvicorn
- **Database**: PostgreSQL (entities) + Redis (sessions/cache) + TimescaleDB (time-series features)
- **Test runner**: pytest
- **Workers**: Celery (baseline building, model training, alert aggregation)

---

## Development Workflow

1. **Research first** — read `behaviour_biometrics.md` and `docs/SDK_BEST_PRACTICES.md` before any implementation
2. **Plan** — use planner agent for non-trivial work; confirm before coding
3. **TDD** — write failing test first (RED), minimal implementation (GREEN), refactor (IMPROVE)
4. **Review** — code-reviewer agent after writing/modifying; fix CRITICAL and HIGH findings
5. **Commit** — `feat|fix|refactor|docs|test|chore: description`

---

## Testing

| Layer | Tool | Location |
|---|---|---|
| Web SDK unit tests | Vitest | `packages/sdk-web/src/__tests__/` |
| Performance benchmarks | Vitest | `packages/sdk-web/src/__benchmarks__/` |
| Server unit tests | pytest | `tests/unit/` |
| E2E tests | Robot Framework + Playwright Browser library | `tests/e2e/bio/` |

**Never** use `@playwright/test` or `.spec.ts` files. All E2E is Robot Framework `.robot`.

---

## Storage Keys (all under `kp.` namespace)

| Key | Storage | Value | Lifetime |
|---|---|---|---|
| `kp.sid` | `sessionStorage` | Session UUID | Tab close |
| `kp.un` | `localStorage` (encrypted in prod) | Raw username | Until `logout()` |
| `kp.did` | `localStorage` + IndexedDB | Device UUID | Until `clearIdentity` |
| `kp.cfg` | `localStorage` | Merged config | Until `destroy()` |
| `kp.k` | `sessionStorage` | AES-GCM key (prod) | Tab close |

---

## Public API (stable contract — breaking changes = major version bump)

```ts
KProtect.init({ api_key, overrides? })         // only required call
KProtect.on(event, callback) → unsubscribe     // events: drift|alert|critical_action|session_start|session_end|username_captured
KProtect.getLatestDrift() → DriftScoreResponse | null
KProtect.getSessionState() → SessionState | null
KProtect.challenge.generate({ purpose }) → Promise<ChallengeResult>
KProtect.challenge.verify(challenge_id, inputEl) → Promise<VerifyResult>
KProtect.logout()                              // clears username, keeps device_uuid
KProtect.destroy({ clearIdentity? })           // stops worker, optionally wipes identity
```

---

## Agents to Use

| Trigger | Agent |
|---|---|
| Complex feature or new module | planner |
| Code just written/modified | code-reviewer |
| Security-sensitive code (transport, identity, hashing) | security-reviewer |
| Build type errors | build-error-resolver |
| Critical user flows (session, critical-action) | e2e-runner |

Always launch independent agents in parallel.

---

## Session Lifecycle Quick Reference

```
init() → [ACTIVE, no username] → username captured → [ACTIVE, transport ON]
       → tab hidden >15min → [SUSPENDED] → tab visible → [NEW SESSION]
       → pagehide/logout/destroy → [TERMINATED, session_end sent]
```

- **One session per tab** (sessionStorage ensures this)
- **Pulse counter**: monotonic from 0, increments by 1 per tick (not by missed ticks)
- **Critical-action pages**: keepalive pulses (30s, no behavioral data) + staging buffer until commit click
- **Abandoned critical action**: sends `CriticalActionBatch` with `committed: false`

---

## Response Envelope (all API responses)

```json
{ "ok": true,  "data": {...} }
{ "ok": false, "error": { "code": "SNAKE_CASE", "message": "..." } }
```