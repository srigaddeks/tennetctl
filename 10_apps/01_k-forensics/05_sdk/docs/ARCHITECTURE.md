# K-Protect System Architecture

> High-level overview of the entire K-Protect behavioral biometrics system.  
> For implementation rules see [SDK_BEST_PRACTICES.md](SDK_BEST_PRACTICES.md).  
> For wire format see [WIRE_PROTOCOL.md](WIRE_PROTOCOL.md).

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           HOST APPLICATIONS                                  │
│                                                                              │
│  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐                 │
│  │  Web App      │   │  Android App  │   │  iOS App      │                 │
│  │  (Browser)    │   │  (Kotlin)     │   │  (Swift)      │                 │
│  │               │   │               │   │               │                 │
│  │ KProtect.     │   │ KProtect.     │   │ KProtect.     │                 │
│  │ init({key})   │   │ init(ctx,key) │   │ initialize(   │                 │
│  │               │   │               │   │   apiKey)     │                 │
│  └──────┬────────┘   └──────┬────────┘   └──────┬────────┘                 │
└─────────┼───────────────────┼───────────────────┼──────────────────────────┘
          │                   │                   │
          │ HTTPS + gzip      │ HTTPS + gzip      │ HTTPS + gzip
          │ (or via proxy)    │                   │
          ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      K-PROTECT API (FastAPI)                                 │
│                                                                              │
│  POST /v1/behavioral/ingest                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ AuthMiddleware → BatchValidator → Router                             │    │
│  │                                                                      │    │
│  │   behavioral  ─→  FeatureIngestor ─→  DriftScorer ─→  Response      │    │
│  │   critical    ─→  CriticalHandler ─→  DriftScorer ─→  AlertEngine   │    │
│  │   keepalive   ─→  SessionTracker.heartbeat()      ─→  Response      │    │
│  │   session_*   ─→  SessionTracker.open()/close()   ─→  Response      │    │
│  └──────────────────────────────┬──────────────────────────────────────┘    │
│                                 │                                            │
│  ┌──────────────────────────────▼──────────────────────────────────────┐    │
│  │                        PERSISTENCE LAYER                             │    │
│  │                                                                      │    │
│  │  PostgreSQL             Redis               TimescaleDB              │    │
│  │  ─────────────          ──────────────      ──────────────────────   │    │
│  │  users                  session:*           behavioral_features      │    │
│  │  sessions               drift_cache:*       drift_scores             │    │
│  │  audit_log              rate_limits:*       baseline_windows         │    │
│  │  api_keys               batch_ids:*         alert_history            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         BACKGROUND WORKERS                            │   │
│  │  BaselineBuilder   DriftModelTrainer   AlertAggregator   Archiver    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## SDK Architecture — Web

```
Browser Tab
┌────────────────────────────────────────────────────────────────────────────┐
│  MAIN THREAD                                                                │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  KProtect Public Facade (~2KB)                                        │   │
│  │  init() / on() / getLatestDrift() / getSessionState()                │   │
│  │  logout() / destroy() / challenge.generate() / challenge.verify()   │   │
│  └─────────────────────────────┬───────────────────────────────────────┘   │
│                                │  postMessage (typed wire-protocol)         │
│  ┌─────────────────────────────▼───────────────────────────────────────┐   │
│  │  MainThreadBridge                                                     │   │
│  │                                                                       │   │
│  │  EventTaps (passive):                                                 │   │
│  │    keydown/keyup → { t, s:'kd'/'ku', d: {code, zone_id, ts} }        │   │
│  │    pointermove   → { t, s:'pm',      d: {zone_id, vx, vy, ts} }      │   │
│  │    pointerdown   → { t, s:'pd',      d: {zone_id, ts} }              │   │
│  │    touchstart    → { t, s:'ts',      d: {zone_id, area, ts} }        │   │
│  │    scroll        → { t, s:'sc',      d: {dy, ts} }                   │   │
│  │    focus/blur    → { t, s:'fb',      d: {zone_id, ts} }              │   │
│  │    submit/click  → { t, s:'cl',      d: {zone_id, ts, is_commit} }   │   │
│  │                                                                       │   │
│  │  DomScanner (MutationObserver):                                       │   │
│  │    watches username selectors → hashes value → postMessage hash      │   │
│  │    detaches after first capture                                       │   │
│  │                                                                       │   │
│  │  RouteListener:                                                       │   │
│  │    patches pushState/replaceState/popstate                            │   │
│  │    → postMessage ROUTE_CHANGE on navigation                          │   │
│  │                                                                       │   │
│  │  VisibilityListener:                                                  │   │
│  │    visibilitychange → postMessage VISIBILITY_CHANGE                  │   │
│  │    pagehide (persisted=false) → sendBeacon session_end               │   │
│  └─────────────────────────────┬───────────────────────────────────────┘   │
│                                │ Blob URL Worker                            │
└────────────────────────────────┼───────────────────────────────────────────┘
                                 │ postMessage (ArrayBuffer transferables)
┌────────────────────────────────▼───────────────────────────────────────────┐
│  WEB WORKER (kprotect.worker.js)                                            │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────────┐   │
│  │ SessionManager  │  │ IdentityStore   │  │ PageGate                 │   │
│  │                 │  │                 │  │                          │   │
│  │ session_id      │  │ username/hash   │  │ page_class evaluation    │   │
│  │ pulse loop      │  │ device_uuid     │  │ opt-out matching         │   │
│  │ idle timeout    │  │ LS+IDB bridge   │  │ critical-action matching │   │
│  │ lifecycle FSM   │  │ ring buffer     │  │ SPA route changes        │   │
│  └────────┬────────┘  └────────┬────────┘  └────────────┬─────────────┘   │
│           │                    │                        │                  │
│  ┌────────▼────────────────────▼────────────────────────▼─────────────┐   │
│  │ Router / Orchestrator                                                │   │
│  │                                                                      │   │
│  │  EVENT_TAP     → Collectors → FeatureExtractor → BatchAssembler     │   │
│  │  ROUTE_CHANGE  → PageGate.evaluate() → adjust pulse cadence         │   │
│  │  PULSE_TICK    → BatchAssembler.flush() → Transport.enqueue()       │   │
│  │  COMMIT        → CriticalActionRouter.seal() → Transport.urgent()   │   │
│  │  USERNAME      → IdentityStore.set() → Transport.drain_ring()       │   │
│  └────────┬────────────────────────────────────────────────────────────┘   │
│           │                                                                 │
│  ┌────────▼──────────────────────────────────────────────────────────┐     │
│  │ Collectors                                                         │     │
│  │  KeystrokeCollector  PointerCollector  TouchCollector              │     │
│  │  ScrollCollector     SensorCollector   CredentialCollector         │     │
│  │                                                                    │     │
│  │  Each implements: enqueue(event) / sleep() / wake() / extract()   │     │
│  └────────┬──────────────────────────────────────────────────────────┘     │
│           │                                                                 │
│  ┌────────▼──────────────────────────────────────────────────────────┐     │
│  │ FeatureExtractor (pure functions)                                  │     │
│  │  computeDwellFlightStats()   computeZoneMatrix()                  │     │
│  │  computeVelocityProfile()    computeTouchGeometry()               │     │
│  │  → discards raw events after extraction                           │     │
│  └────────┬──────────────────────────────────────────────────────────┘     │
│           │                                                                 │
│  ┌────────▼──────────────────────────────────────────────────────────┐     │
│  │ Transport                                                          │     │
│  │  queue: BehavioralBatch[]  (ring, max 50)                         │     │
│  │  send(): CompressionStream('gzip') → fetch(keepalive: true)       │     │
│  │  retry(): exponential backoff per retry policy                    │     │
│  │  gate: OFF until user_hash set                                    │     │
│  └───────────────────────────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## SDK Architecture — Android

```
Host App (Android)
┌────────────────────────────────────────────────────────────────────────────┐
│  MAIN (UI) THREAD                                                           │
│                                                                             │
│  KProtect.init(context, apiKey)                                             │
│  ├── ProcessLifecycleObserver (foreground/background transitions)           │
│  ├── ActivityLifecycleCallbacks (per-screen page gating)                    │
│  └── UsernameFieldWatcher (TextWatcher on configured fields)                │
│       └── hashes value → HandlerThread.post(USERNAME_CAPTURED)             │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
                                 │  Message
┌────────────────────────────────▼───────────────────────────────────────────┐
│  kp-bio-worker (HandlerThread + Looper)                                     │
│                                                                             │
│  SessionManager    IdentityStore         PageGate                           │
│  (identical        (EncryptedShared      (Activity class name matching)     │
│   semantics to      Preferences)                                            │
│   web worker)                                                               │
│                                                                             │
│  Collectors:                                                                │
│  ├── KeyEventCollector    (AccessibilityService or InputConnection)         │
│  ├── MotionEventCollector (Window.Callback intercept)                       │
│  ├── TouchEventCollector  (MotionEvent.ACTION_DOWN/UP/MOVE)                 │
│  ├── SensorCollector      (SensorManager + AccelerometerListener)           │
│  └── CredentialCollector  (EditText with inputType=password)                │
│                                                                             │
│  Transport: OkHttp (dedicated Dispatcher, 2 threads)                        │
│  Session flush on app-kill: WorkManager OneTimeWorkRequest (EXPEDITED)      │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## SDK Architecture — iOS

```
Host App (iOS)
┌────────────────────────────────────────────────────────────────────────────┐
│  MAIN QUEUE                                                                 │
│                                                                             │
│  KProtect.initialize(apiKey)                                                │
│  ├── NotificationCenter observers (foreground/background)                   │
│  ├── UIViewController swizzle (viewDidAppear/Disappear for page gating)     │
│  └── UITextField target/action (blur = editingDidEnd)                       │
│       └── hashes value → workerQueue.async { USERNAME_CAPTURED }           │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
                                 │  DispatchWorkItem
┌────────────────────────────────▼───────────────────────────────────────────┐
│  kp-bio-worker (DispatchQueue serial, qos: .utility)                        │
│                                                                             │
│  SessionManager    IdentityStore              PageGate                      │
│  (identical        (Keychain via              (UIViewController class name  │
│   semantics to      SecItem APIs)              matching)                    │
│   web worker)                                                               │
│                                                                             │
│  Collectors:                                                                │
│  ├── UIKeyInput observation (timing only, no content)                       │
│  ├── UIEvent (touches) via UIWindow.sendEvent swizzle                       │
│  ├── CoreMotion (CMMotionManager, delivered on workerQueue's OperationQueue)│
│  └── UITextField observation for credential field patterns                  │
│                                                                             │
│  Transport: URLSession background configuration                             │
│  Session flush on kill: background URLSession (iOS resumes upload)          │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Server Architecture

```
                             ┌──────────────────┐
                    HTTPS    │   Load Balancer   │
   SDK ─────────────────────►│   (Nginx/ALB)     │
                             └────────┬─────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                  │
             ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
             │  API Worker │  │  API Worker │  │  API Worker │  (FastAPI + uvicorn)
             │  (Process 1)│  │  (Process 2)│  │  (Process N)│
             └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
                    │                │                  │
                    └────────────────┼──────────────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
     ┌────────▼────────┐  ┌──────────▼──────────┐  ┌───────▼────────┐
     │   PostgreSQL     │  │   Redis 7 Cluster    │  │  TimescaleDB   │
     │                  │  │                      │  │                │
     │  users           │  │  session:{id}        │  │  features      │
     │  sessions        │  │  drift_cache:{hash}  │  │  drift_scores  │
     │  audit_log       │  │  rate:{key}          │  │  baselines     │
     │  api_keys        │  │  batch_ids (24h TTL) │  │  alerts        │
     │  device_history  │  │                      │  │                │
     └──────────────────┘  └──────────────────────┘  └────────────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
     ┌────────▼────────┐  ┌──────────▼──────────┐  ┌───────▼────────┐
     │ BaselineBuilder  │  │  DriftModelTrainer   │  │ AlertAggregator│
     │ (Celery worker)  │  │  (Celery worker)     │  │ (Celery worker)│
     │                  │  │                      │  │                │
     │  Runs every 4h   │  │  Runs nightly        │  │  Real-time     │
     │  Updates user    │  │  Fine-tunes drift     │  │  threshold     │
     │  baselines from  │  │  model weights        │  │  evaluation    │
     │  feature history │  │                      │  │                │
     └──────────────────┘  └──────────────────────┘  └────────────────┘
```

---

## Mutable Signal Refresh

Network and battery signals change during a session (e.g., user switches from WiFi to cellular, device charges). The SDK re-collects these on a 3-minute interval:

```
Main Thread                              Web Worker
─────────────                            ──────────────
setInterval(180_000ms)
  → collectNetworkFingerprint()
  → collectBatteryFingerprint()
  → postMessage MUTABLE_SIGNALS_UPDATE ──→ Worker updates cached signals
                                           → Next batch includes fresh values
```

Only lightweight TIER 3 signals are refreshed (no canvas, GPU, or audio re-computation). The `MUTABLE_REFRESH_INTERVAL_MS` default is 3 minutes, defined in `defaults.ts`.

---

## Data Flow — Normal Session

```
1. User opens browser tab
   → SDK init() called
   → Worker spawned (blob URL)
   → session_id = crypto.randomUUID() stored in sessionStorage
   → device_uuid loaded from localStorage (or minted + stored)
   → POST session_start batch to API
   → Server creates session record, returns SessionMetadataResponse

2. User interacts (before login)
   → Event listeners fire (passive, <0.1ms each)
   → Events postMessage'd to worker (ArrayBuffer transfer)
   → Worker enqueues in collector ring buffers
   → FeatureExtractor runs every 30s
   → Features stored in pre-username ring buffer (max 30 windows)
   → Transport GATED OFF — no network requests

3. User fills username field and blurs
   → DomScanner detects field match
   → Value hashed (crypto.subtle.SHA-256) on main thread
   → Hash postMessage'd to worker
   → Worker calls IdentityStore.setUsername(hash)
   → Ring buffer drained: all 30 buffered windows enqueued in Transport
   → Transport gate OPENS
   → First batch immediately dispatched

4. Normal session running
   → Every 30s: BatchAssembler.flush() called by pulse timer
   → Pulses with < 10 events are skipped (MIN_EVENTS_FOR_PULSE threshold)
   → Features from 30s window assembled into BehavioralBatch
   → automation_score from device fingerprint included when available
   → Scroll signals extracted and included alongside keystroke/pointer/touch
   → Batch gzip-compressed, fetch POST'd to /v1/behavioral/ingest
   → Server scores drift, returns DriftScoreResponse
   → Worker caches response, postMessage's to main thread
   → KProtect.on('drift', handler) fires on main thread

5. User navigates to /payment
   → RouteListener detects pushState
   → postMessage ROUTE_CHANGE("/payment") to worker
   → PageGate evaluates: matches /\/payment/ → critical_action
   → Pulse cadence switches: normal 30s behavioral → keepalive 30s liveness-only
   → Collectors continue running → features go to staging buffer

6. User types amount, reviews, clicks "Confirm Payment"
   → MainThreadBridge detects click on [data-kp-commit="payment"]
   → postMessage CRITICAL_ACTION_COMMIT to worker
   → CriticalActionRouter seals staging buffer
   → CriticalActionBatch created (committed: true)
   → Transport sends immediately (priority: high, keepalive: true)
   → Server scores full critical-action batch → alert engine evaluates
   → DriftScoreResponse returned → KProtect.on('critical_action', handler) fires

7. User closes tab
   → pagehide fires (persisted: false)
   → MainThreadBridge calls navigator.sendBeacon(endpoint, session_end_batch)
   → Browser delivers beacon even after page unload
   → Server marks session closed
```

---

## Data Flow — Account Takeover Detection

```
1. Legitimate user (Alice) uses app for 45 days
   → BaselineBuilder accumulates 45 days of feature windows
   → Baseline quality: "strong"
   → Drift scores consistently 0.05–0.15 (normal variation)

2. Attacker steals Alice's credentials and logs in
   → SDK captures attacker's behavioral signals
   → After 2-3 pulses (60-90s), drift score spikes to 0.78-0.95
   → DriftScorer detects anomaly vs Alice's baseline
   → AlertEngine fires: severity=critical, type=typing_anomaly
   → Webhook POST to bank's fraud system
   → Bank's system triggers step-up auth for Alice's session
   → SDK receives action='block' → fires 'alert' event on client

3. Bank's app shows step-up auth challenge
   → If attacker fails (doesn't know Alice's MFA) → session killed
   → If attacker somehow passes MFA → KP-Challenge behavioral challenge
   → KProtect.challenge.generate({ purpose: 'identity_verification' })
   → Server generates typing challenge unique to Alice's known patterns
   → Attacker can't replicate Alice's typing patterns
   → challenge.verify() returns passed: false → hard block
```

---

## Baseline Building

```
New user first login
  → Baseline quality: "insufficient" (< 5 sessions)
  → No drift scoring yet — scores returned as null
  → action always: "allow" during insufficient period

After 5-15 sessions (~1-3 days typical)
  → Baseline quality: "forming"
  → Drift scoring active but with high confidence intervals
  → action: "monitor" possible, "block" not yet

After 30+ sessions (~1-2 weeks typical)
  → Baseline quality: "established"
  → Full drift scoring active
  → All actions possible (allow/monitor/challenge/block)

After 100+ sessions (~1-2 months typical)
  → Baseline quality: "strong"
  → High confidence, tight drift thresholds
  → Low false-positive rate
```

---

## Security Boundaries

```
┌─────────────────────────────────────────────────────────┐
│                    HOST PAGE                             │
│  KProtect facade receives: DriftScoreResponse,          │
│  session state, events. Never sees raw behavioral data.  │
└───────────────────────────┬─────────────────────────────┘
                            │  postMessage (typed, no PII)
┌───────────────────────────▼─────────────────────────────┐
│                   WEB WORKER                             │
│  Processes raw events. Computes features.               │
│  Only user_hash (SHA-256) exits — never plaintext.      │
│  Raw events discarded after extraction.                  │
└───────────────────────────┬─────────────────────────────┘
                            │  HTTPS + gzip + HMAC
┌───────────────────────────▼─────────────────────────────┐
│                K-PROTECT API                             │
│  Receives extracted features + user_hash.               │
│  Never receives: raw events, usernames, key content,    │
│  pixel coordinates, device hardware identifiers.        │
└─────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
k-bio-main/
├── docs/
│   ├── SDK_BEST_PRACTICES.md   ← Rules every contributor must follow
│   ├── SDK_INTEGRATION.md      ← Web SDK build, install, config, and public API
│   ├── INTEGRATION_GUIDE.md    ← Step-by-step for Web/Android/iOS integrators
│   ├── WIRE_PROTOCOL.md        ← Complete wire format specification
│   ├── SERVER_API.md           ← Server endpoint reference
│   ├── SECURITY.md             ← Security mechanisms (signing, encryption, origin binding)
│   ├── PRIVACY.md              ← Privacy mechanisms (DP, GDPR, consent, data retention)
│   ├── TROUBLESHOOTING.md      ← Common issues, fallback modes, debugging
│   └── ARCHITECTURE.md         ← This document
│
├── packages/
│   ├── sdk-web/                ← TypeScript/Browser SDK
│   │   ├── src/
│   │   │   ├── config/
│   │   │   │   └── defaults.ts
│   │   │   ├── runtime/
│   │   │   │   ├── main-thread-bridge.ts
│   │   │   │   ├── worker-entry.ts
│   │   │   │   ├── main-thread-fallback.ts
│   │   │   │   └── wire-protocol.ts
│   │   │   ├── session/
│   │   │   │   ├── session-manager.ts
│   │   │   │   ├── identity-store.ts
│   │   │   │   ├── username-capture.ts
│   │   │   │   ├── page-gate.ts
│   │   │   │   ├── critical-action-router.ts
│   │   │   │   ├── consent-manager.ts  ← GDPR/CCPA consent gate
│   │   │   │   └── audit-logger.ts     ← Tamper-evident audit log
│   │   │   ├── collectors/
│   │   │   │   ├── keystroke-collector.ts
│   │   │   │   ├── pointer-collector.ts
│   │   │   │   ├── touch-collector.ts
│   │   │   │   ├── scroll-collector.ts
│   │   │   │   ├── sensor-collector.ts
│   │   │   │   ├── credential-collector.ts
│   │   │   │   ├── gesture.ts
│   │   │   │   ├── event-buffer.ts
│   │   │   │   └── laplace-noise.ts    ← Differential privacy
│   │   │   ├── signals/                ← Device fingerprinting collectors
│   │   │   │   ├── collect-all.ts      ← Orchestrator
│   │   │   │   ├── canvas-fingerprint.ts
│   │   │   │   ├── audio-fingerprint.ts
│   │   │   │   ├── webgl-fingerprint.ts
│   │   │   │   ├── gpu-render-fingerprint.ts
│   │   │   │   ├── cpu-benchmark.ts
│   │   │   │   ├── font-fingerprint.ts
│   │   │   │   ├── automation-detect.ts
│   │   │   │   ├── environment-signals.ts
│   │   │   │   ├── mutable-refresh.ts
│   │   │   │   ├── misc-fingerprints.ts
│   │   │   │   ├── load-indicators.ts
│   │   │   │   └── crypto-utils.ts     ← SHA-256, HMAC, AES-GCM helpers
│   │   │   ├── features/
│   │   │   │   ├── keystroke-features.ts
│   │   │   │   ├── pointer-features.ts
│   │   │   │   ├── touch-features.ts
│   │   │   │   ├── scroll-features.ts
│   │   │   │   └── batch-assembler.ts
│   │   │   ├── transport/
│   │   │   │   └── transport.ts
│   │   │   └── index.ts        ← Public facade
│   │   ├── src/__tests__/      ← Unit tests (Vitest)
│   │   ├── src/__benchmarks__/ ← Performance benchmarks
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   └── rollup.config.ts
│   │
│   ├── sdk-android/            ← Kotlin SDK (Phase 2)
│   └── sdk-ios/                ← Swift SDK (Phase 2)
│
├── app/                        ← FastAPI server (from behaviour_biometrics.md)
│   ├── main.py
│   ├── routes/
│   │   └── behavioral.py
│   ├── services/
│   │   ├── drift_scorer.py
│   │   ├── baseline_builder.py
│   │   └── alert_engine.py
│   └── models/
│
├── tests/
│   ├── e2e/
│   │   └── bio/
│   │       └── 01_session_lifecycle.robot
│   └── unit/
│
├── package.json                ← Workspace root
├── pnpm-workspace.yaml
├── turbo.json
└── tsconfig.base.json
```

---

*Last updated: 2026-04-09 — K-Protect Engineering*
