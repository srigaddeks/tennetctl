# CLAUDE.md — K-Protect Device Intelligence Engine

## Project Identity

You are building the **Device Intelligence Engine** for K-Protect, a fraud prevention and identity verification platform for regulated financial institutions. This is the client-side SDK + server-side resolution system that identifies devices across browsers, sessions, and resets — without relying on cookies or stored state.

This is enterprise-grade software. It will run on banking websites handling millions of sessions. Every decision must be auditable, every signal must be privacy-compliant, and the system must operate with sub-200ms latency.

---

## Architecture Overview

The system has three layers. Understand all three before writing any code.

### Layer 1: Client SDK (Signal Collection)

Platform-specific SDKs that silently collect device, network, and location signals:

- **Web SDK** (`packages/sdk-web/`): TypeScript, <15KB gzipped, zero dependencies
- **iOS SDK** (`packages/sdk-ios/`): Swift, XCFramework
- **Android SDK** (`packages/sdk-android/`): Kotlin, AAR
- **React Native Bridge** (`packages/sdk-react-native/`): Thin bridge over native SDKs

The Web SDK is the most constrained (browsers deliberately limit hardware access). Mobile SDKs get direct hardware access. The SDK's job is to collect the best signals possible and send them efficiently — it does NOT make identity decisions.

### Layer 2: FastAPI Backend (Signal Ingestion + Resolution)

The SDK sends signals via simple HTTPS POST to a Python FastAPI backend. The backend processes signals synchronously and returns the risk score + device resolution in the same response. No message bus, no event streaming, no async pipelines — just request → process → respond.

```
SDK (HTTPS POST) → FastAPI Backend → Response (risk score + device ID)
```

- HTTPS with TLS 1.3
- JSON payloads (Brotli/gzip compressed by SDK)
- Synchronous request-response (<200ms target)
- All processing happens in the request lifecycle
- Valkey for hot cache (session state, device profiles)
- PostgreSQL + Apache AGE for persistence + graph

### Layer 3: Server-Side Resolution (The Brain)

This is where device identity is actually resolved:

- **Signal Validator**: Anti-spoofing consistency checks
- **Fingerprint Matcher**: Exact hash → fuzzy weighted match → graph-assisted resolution
- **Knowledge Graph**: Device ↔ User ↔ Session ↔ Network entity relationships
- **Decision Engine**: Semi-deterministic rules first, ML second, graph reasoning third

---

## Tech Stack

| Component | Technology | Notes |
|---|---|---|
| Web SDK | TypeScript 5.x, Rollup bundler | Zero runtime deps. Tree-shakeable. |
| iOS SDK | Swift 5.9+, XCFramework | No third-party deps. iOS 15+ minimum. |
| Android SDK | Kotlin 1.9+, AAR | No third-party deps. API 26+ minimum. |
| RN Bridge | TypeScript | Thin wrapper, delegates to native. |
| Backend API | Python 3.12+, FastAPI, Uvicorn | Async endpoints, Pydantic validation. |
| ML Inference | Python, ONNX Runtime (or scikit-learn V1) | In-process, no separate service. |
| Knowledge Graph | Apache AGE on PostgreSQL | Graph queries without separate infra. |
| Hot Cache | Valkey (Redis-compatible) | <1ms session state and profile lookups. |
| Database | PostgreSQL 16+ (time-partitioned) | Audit trail, device registry, config. |
| IP Intelligence | MaxMind GeoIP2 (local DB file) | In-process lookup, no external API call. |

---

## Monorepo Structure

```
kprotect-device-intelligence/
├── CLAUDE.md                          # This file
├── package.json                       # Root workspace config (pnpm)
├── pnpm-workspace.yaml
├── turbo.json                         # Turborepo pipeline (SDK builds only)
│
├── packages/
│   ├── sdk-web/                       # Web SDK (TypeScript)
│   │   ├── src/
│   │   │   ├── index.ts               # Public API entry point
│   │   │   ├── core/
│   │   │   │   ├── collector.ts        # Main collection orchestrator
│   │   │   │   ├── transport.ts        # HTTPS POST transport (fetch-based)
│   │   │   │   ├── batcher.ts          # Event batching + compression
│   │   │   │   └── diff-engine.ts      # Snapshot diff computation
│   │   │   ├── signals/
│   │   │   │   ├── types.ts            # All signal type definitions
│   │   │   │   ├── gpu/
│   │   │   │   │   ├── webgl-params.ts       # Tier 1: WebGL hardware limits
│   │   │   │   │   ├── render-tasks.ts       # Tier 2: GPU render task execution
│   │   │   │   │   ├── shaders.ts            # GLSL shader source for render tasks
│   │   │   │   │   └── webgpu-probe.ts       # Optional WebGPU signals
│   │   │   │   ├── audio/
│   │   │   │   │   ├── oscillator.ts         # AudioContext fingerprint
│   │   │   │   │   └── peak-analysis.ts      # Cross-browser peak frequency extraction
│   │   │   │   ├── cpu/
│   │   │   │   │   ├── benchmarks.ts         # Micro-benchmark suite
│   │   │   │   │   ├── worker.ts             # Web Worker for isolated benchmarks
│   │   │   │   │   └── ratios.ts             # Cross-browser ratio computation
│   │   │   │   ├── screen/
│   │   │   │   │   └── display.ts            # Screen + display hardware signals
│   │   │   │   ├── fonts/
│   │   │   │   │   └── enumeration.ts        # Font detection via DOM measurement
│   │   │   │   ├── network/
│   │   │   │   │   └── client-network.ts     # navigator.connection + timezone
│   │   │   │   ├── environment/
│   │   │   │   │   ├── browser-detect.ts     # Browser/engine identification
│   │   │   │   │   ├── automation-detect.ts  # Bot/CDP/Puppeteer/Playwright detection
│   │   │   │   │   └── integrity.ts          # Client-side consistency pre-checks
│   │   │   │   └── platform/
│   │   │   │       └── tier1-stable.ts       # All Tier 1 stable signals (sync, fast)
│   │   │   └── __tests__/                    # Unit + integration tests
│   │   ├── rollup.config.ts
│   │   ├── tsconfig.json
│   │   └── package.json
│   │
│   ├── sdk-ios/                       # iOS SDK (Swift)
│   │   ├── Sources/KProtect/
│   │   │   ├── KProtect.swift                # Public API
│   │   │   ├── Collector/
│   │   │   │   ├── HardwareCollector.swift    # Direct hardware signals
│   │   │   │   ├── NetworkCollector.swift     # Network + carrier signals
│   │   │   │   └── IntegrityCollector.swift   # Jailbreak, hook detection
│   │   │   ├── Transport/
│   │   │   │   └── HTTPTransport.swift        # HTTPS POST to FastAPI
│   │   │   └── Models/
│   │   │       └── Signals.swift
│   │   ├── Tests/
│   │   └── Package.swift
│   │
│   ├── sdk-android/                   # Android SDK (Kotlin)
│   │   ├── src/main/kotlin/io/kprotect/
│   │   │   ├── KProtect.kt                   # Public API
│   │   │   ├── collector/
│   │   │   │   ├── HardwareCollector.kt       # Direct hardware signals
│   │   │   │   ├── NetworkCollector.kt        # Network + carrier signals
│   │   │   │   └── IntegrityCollector.kt      # Root, emulator, hook detection
│   │   │   ├── transport/
│   │   │   │   └── HTTPTransport.kt           # HTTPS POST to FastAPI
│   │   │   └── models/
│   │   │       └── Signals.kt
│   │   └── build.gradle.kts
│   │
│   ├── sdk-react-native/             # React Native bridge
│   │   ├── src/
│   │   │   └── index.ts
│   │   ├── ios/
│   │   └── android/
│   │
│   └── shared-types/                  # Shared signal type definitions
│       └── src/
│           ├── signals.ts             # Signal schema (source of truth)
│           ├── payloads.ts            # Wire format types
│           └── decisions.ts           # Risk score / decision types
│
├── backend/                           # Python FastAPI backend (SINGLE APP)
│   ├── pyproject.toml                 # Dependencies: fastapi, uvicorn, pydantic,
│   │                                  #   asyncpg, valkey-py, maxminddb, numpy,
│   │                                  #   scipy (for FFT/similarity), scikit-learn
│   ├── app/
│   │   ├── main.py                    # FastAPI app + lifespan (startup/shutdown)
│   │   ├── config.py                  # Settings via pydantic-settings
│   │   ├── dependencies.py            # Shared deps (db pool, valkey client, geoip reader)
│   │   │
│   │   ├── api/                       # API routes
│   │   │   ├── __init__.py
│   │   │   ├── ingest.py              # POST /v1/signals — receive SDK payloads
│   │   │   ├── score.py               # POST /v1/score — on-demand risk score
│   │   │   ├── session.py             # POST /v1/session/start, /v1/session/end
│   │   │   └── admin.py              # Tenant config, dashboard queries
│   │   │
│   │   ├── models/                    # Pydantic models (request/response schemas)
│   │   │   ├── __init__.py
│   │   │   ├── signals.py             # FullPayload, DiffPayload, BehavioralBatch
│   │   │   ├── device.py              # DeviceEntity, BrowserEnv, NetworkLoc
│   │   │   ├── decisions.py           # RiskScore, Decision, DeviceDrift, AuditRecord
│   │   │   ├── network.py            # GeoIP result, ASN info, IP classification
│   │   │   ├── metadata.py           # DeviceMetadata, InputMetadata, NetworkMetadata, SessionMetadata
│   │   │   └── trust.py              # TrustedDevice, TrustedNetwork, TrustedLocation
│   │   │
│   │   ├── services/                  # Business logic (called by API routes)
│   │   │   ├── __init__.py
│   │   │   ├── signal_validator.py    # Anti-spoofing consistency checks
│   │   │   ├── device_resolver.py     # Exact → fuzzy → graph resolution
│   │   │   ├── fuzzy_matcher.py       # Weighted similarity matching
│   │   │   ├── network_intel.py       # IP → geo, ASN, VPN, proxy, Tor, TLS fingerprint
│   │   │   ├── graph_resolver.py      # Apache AGE knowledge graph queries
│   │   │   ├── risk_scorer.py         # Rules engine + ML scoring + graph reasoning
│   │   │   ├── metadata_collector.py  # Collect + persist all metadata (background writes)
│   │   │   ├── trust_manager.py       # Trusted device/network/location registry management
│   │   │   └── audit.py              # Hash-chained audit trail generation
│   │   │
│   │   ├── comparators/              # Per-signal-type similarity functions
│   │   │   ├── __init__.py
│   │   │   ├── webgl.py              # WebGL param comparison
│   │   │   ├── gpu_render.py         # Quantized render task hash comparison
│   │   │   ├── audio.py              # Peak frequency Jaccard similarity
│   │   │   ├── fonts.py              # Font set Jaccard similarity
│   │   │   ├── cpu.py                # Benchmark ratio Euclidean distance
│   │   │   └── screen.py            # Screen/platform exact match
│   │   │
│   │   ├── db/                        # Database layer
│   │   │   ├── __init__.py
│   │   │   ├── postgres.py            # asyncpg connection pool + queries
│   │   │   ├── graph.py              # Apache AGE Cypher query helpers
│   │   │   ├── valkey.py             # Valkey (Redis) cache helpers
│   │   │   └── migrations/           # Alembic migrations
│   │   │       ├── env.py
│   │   │       └── versions/
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── hashing.py            # SHA-256, hash chain utilities
│   │       ├── geo.py                # MaxMind GeoIP2 local DB reader
│   │       └── tls.py                # JA3/JA4 TLS fingerprint extraction
│   │
│   ├── tests/
│   │   ├── conftest.py               # Fixtures: test DB, test Valkey, mock GeoIP
│   │   ├── test_ingest.py
│   │   ├── test_device_resolver.py
│   │   ├── test_fuzzy_matcher.py
│   │   ├── test_signal_validator.py
│   │   ├── test_network_intel.py
│   │   └── test_audit.py
│   │
│   ├── Dockerfile
│   └── docker-compose.yml            # Backend + PostgreSQL + Valkey (local dev)
│
├── infra/
│   ├── k8s/                          # Kubernetes manifests (production)
│   └── maxmind/                      # GeoIP2 database files (.mmdb)
│
└── docs/
    ├── architecture.md
    ├── signal-taxonomy.md
    ├── api-reference.md
    └── cross-browser-matching.md
```

---

## Critical Implementation Rules

### Rule 1: Signal Tiers (Web SDK)

Browsers deliberately prevent direct hardware access. Do NOT try to read exact RAM, CPU model, disk size, MAC address, or any hardware identifier from the web. Instead, use indirect hardware signals.

**TIER 1 — High reliability, cross-browser stable, synchronous:**
These produce identical output across Chrome, Firefox, and Safari on the same device. Collect these first, they are fast and always available.

```
WebGL parameter limits:
  gl.getParameter(gl.MAX_TEXTURE_SIZE)
  gl.getParameter(gl.MAX_RENDERBUFFER_SIZE)
  gl.getParameter(gl.MAX_VIEWPORT_DIMS)
  gl.getParameter(gl.MAX_VERTEX_ATTRIBS)
  gl.getParameter(gl.MAX_VARYING_VECTORS)
  gl.getParameter(gl.MAX_VERTEX_UNIFORM_VECTORS)
  gl.getParameter(gl.MAX_FRAGMENT_UNIFORM_VECTORS)
  gl.getParameter(gl.MAX_COMBINED_TEXTURE_IMAGE_UNITS)
  gl.getParameter(gl.MAX_VERTEX_TEXTURE_IMAGE_UNITS)
  gl.getParameter(gl.MAX_TEXTURE_IMAGE_UNITS)
  gl.getParameter(gl.MAX_CUBE_MAP_TEXTURE_SIZE)
  gl.getParameter(gl.ALIASED_LINE_WIDTH_RANGE)
  gl.getParameter(gl.ALIASED_POINT_SIZE_RANGE)

Shader precision formats:
  gl.getShaderPrecisionFormat(gl.VERTEX_SHADER, gl.HIGH_FLOAT)
  gl.getShaderPrecisionFormat(gl.VERTEX_SHADER, gl.MEDIUM_FLOAT)
  gl.getShaderPrecisionFormat(gl.FRAGMENT_SHADER, gl.HIGH_FLOAT)
  gl.getShaderPrecisionFormat(gl.FRAGMENT_SHADER, gl.MEDIUM_FLOAT)

Screen hardware:
  screen.width, screen.height, screen.colorDepth, screen.pixelDepth
  window.devicePixelRatio
  matchMedia('(color-gamut: p3)'), matchMedia('(dynamic-range: high)')

Platform:
  navigator.hardwareConcurrency
  navigator.maxTouchPoints
  navigator.platform
  Intl.DateTimeFormat().resolvedOptions().timeZone
  navigator.languages
  matchMedia('(prefers-color-scheme: dark)')
  matchMedia('(prefers-reduced-motion: reduce)')
```

**TIER 2 — High entropy, needs computation, ~200-500ms:**
These require the hardware to perform tasks. Output varies slightly across browsers due to different rendering backends (ANGLE vs native OpenGL), but patterns are stable. Server uses fuzzy matching.

```
GPU render tasks (5 tasks, ~300ms total):
  - Gradient triangle render → readPixels → hash (tests vertex interpolation)
  - Alpha blending render → readPixels → hash (tests compositing)
  - Float precision shader → readPixels → hash (tests GPU FPU — highest entropy)
  - Anti-aliasing diagonal lines → readPixels → hash (tests AA implementation)
  - Texture filtering quad → readPixels → hash (tests bilinear filtering)
  For cross-browser matching: produce BOTH exact hash AND quantized hash
  (reduce each color channel to 4 bits before hashing to absorb rendering differences)

AudioContext processing (~100ms):
  - OfflineAudioContext(1, 5000, 44100)
  - OscillatorNode(triangle, 1000Hz) → DynamicsCompressorNode → render
  - Produce exact hash (same-browser matching)
  - Extract top 10 peak frequencies via FFT, bin to 10Hz ranges (cross-browser matching)

CPU benchmark ratios (~200ms, run in Web Worker):
  - Run 5 micro-benchmarks: intArithmetic, floatArithmetic, stringOps, arraySort, cryptoHash
  - Take median of 3 runs each
  - Compute RATIOS: intToFloat, stringToArray, cryptoToJson
  - Ratios are CPU-architecture dependent, not JS-engine dependent

Font enumeration (~100ms):
  - Test presence of ~100 candidate fonts via DOM text measurement
  - Render test string in each font, compare bounding box to default
  - Installed font list is OS-level, same across browsers
  - Hash the sorted font list

Canvas 2D fingerprint (~50ms):
  - Draw specific text, shapes, gradients, emoji on 2D canvas
  - Read pixel data and hash
  - Less cross-browser stable than WebGL, but adds entropy
```

**TIER 3 — Browser-specific, high entropy within one browser:**
These do NOT help cross-browser linking but are strong for same-browser re-identification and spoofing detection.

```
navigator.deviceMemory       → Chrome only, returns 0.25/0.5/1/2/4/8
WebGL renderer string        → Format differs per browser for same GPU
Full canvas/audio hash       → Browser engine determines exact output
TLS fingerprint (JA3/JA4)    → Browser+version specific (server-side)
HTTP header order            → Browser specific (server-side)
navigator.connection          → Chrome only (effectiveType, downlink, rtt)
```

### Rule 1b: Signal Reliability Under Device Load

GPU render tasks produce deterministic pixel output — the GPU math is fixed-function and does not change under CPU load. However, OTHER signals degrade under load, and the SDK MUST detect this and report per-signal confidence to the server.

**What is load-immune (pixel output is deterministic):**

```
ALWAYS RELIABLE — hardware constants, never change under any conditions:
  WebGL parameter limits (MAX_TEXTURE_SIZE etc.)   → confidence: 1.0 always
  Shader precision formats                          → confidence: 1.0 always
  Screen resolution, DPR, colorDepth               → confidence: 1.0 always
  Platform, timezone, languages, maxTouchPoints     → confidence: 1.0 always
  Font enumeration (DOM measurement, not timing)    → confidence: 0.95 always

RELIABLE — pixel output is deterministic, but context can be lost:
  GPU render task pixel hashes                      → confidence: 1.0 if context alive
                                                    → confidence: 0.0 if context lost (retry once)
  AudioContext peak frequencies (binned to 10Hz)    → confidence: 0.95 normal
                                                    → confidence: 0.7 under memory pressure
```

**What DEGRADES under load:**

```
CPU benchmark ratios:
  Problem: Heavy CPU load skews timing. Thermal throttling on mobile changes
           clock frequencies. A benchmark that takes 12ms at idle may take 40ms
           under load. Ratios are MORE stable than absolutes (both operations
           slow down), but single-threaded contention can skew ratios 15-30%.
  Impact:  Cross-browser matching degrades from ~75% to ~50% accuracy.
  Confidence: 0.9 at idle → 0.4 under heavy load.

Canvas 2D hash:
  Problem: Some browsers deprioritize canvas rendering under load. The compositor
           may take shortcuts that produce subtly different pixel output.
  Impact:  Same-browser re-identification drops from ~95% to ~80%.
  Confidence: 0.85 normal → 0.5 under load.

Full AudioContext hash (NOT peaks — peaks are more stable):
  Problem: Under extreme memory pressure, OfflineAudioContext render may produce
           slightly different float results due to memory allocation patterns.
  Impact:  Same-browser matching drops. Peak analysis is resistant because
           peaks are binned to absorb floating-point noise.
  Confidence: 0.8 normal → 0.5 under pressure.

GPU render task TIMING (not pixel output — timing is different from pixels):
  Problem: GPU scheduling delays mean render time varies wildly under GPU load.
           Never use render task duration as a fingerprinting signal.
  Impact:  N/A — we hash pixels, not timing. But if you ever add timing signals,
           they will be unreliable.
  Rule:    NEVER use GPU render timing as a signal. Only use pixel output hash.
```

**WebGL context loss — the critical edge case:**

```
When the device is under extreme GPU pressure (gaming, video editing, many tabs
with WebGL content), the browser can evict your WebGL context. This fires the
"webglcontextlost" event. Your readPixels() call returns all zeros.

SDK MUST handle this:
  1. Listen for "webglcontextlost" event on the canvas
  2. If context lost during render tasks → mark all GPU signals as unavailable
  3. Listen for "webglcontextrestored" event
  4. On restore → retry render tasks ONCE
  5. If second attempt also fails → report gpu_available: false to server
  6. Server: if GPU signals unavailable, rely on remaining signals
     (WebGL parameters are already collected before render tasks, so Tier 1 is safe)

canvas.addEventListener('webglcontextlost', (e) => {
  e.preventDefault();  // allows context restoration
  this.gpuContextLost = true;
});
canvas.addEventListener('webglcontextrestored', () => {
  this.gpuContextLost = false;
  this.retryRenderTasks();  // one retry
});
```

**SDK must detect device load and report it:**

```typescript
interface LoadIndicators {
  // FRAME RATE — if main thread is struggling, rAF drops below 30fps
  estimatedFps: number;        // requestAnimationFrame-based measurement
  
  // EVENT LOOP LATENCY — how backed up is the main thread?
  eventLoopLatencyMs: number;  // schedule setTimeout(0), measure actual delay
  
  // MEMORY PRESSURE (Chrome only)
  memoryUsedMB: Optional<number>;     // performance.memory.usedJSHeapSize
  memoryLimitMB: Optional<number>;    // performance.memory.jsHeapSizeLimit
  memoryPressure: 'low' | 'moderate' | 'critical';
  
  // THERMAL STATE (mobile, if available)
  thermalState: Optional<string>;     // navigator.thermalState (limited support)
  
  // BATTERY CONTEXT (Chrome on laptops/mobile)
  batteryCharging: Optional<boolean>;
  batteryLevel: Optional<number>;
  
  // DOCUMENT VISIBILITY — was the tab in background during collection?
  documentWasHidden: boolean;
  
  // GPU CONTEXT STATUS
  gpuContextLost: boolean;
  gpuContextRestored: boolean;
  gpuRenderTasksRetried: boolean;
}

// Measure load BEFORE running Tier 2 signal collection
function detectLoad(): LoadIndicators {
  // FPS estimation: schedule 10 rAF callbacks, measure average interval
  // Event loop latency: schedule setTimeout(0) 5 times, measure average overshoot
  // Memory: performance.memory (Chrome only, non-standard)
  // Visibility: document.visibilityState
}
```

**Server-side confidence weighting:**

The server MUST use per-signal confidence when computing fuzzy match scores. Under heavy load, timing-based signals carry less weight.

```python
# backend/app/services/fuzzy_matcher.py

def compute_weighted_similarity(
    incoming: DeviceSignals,
    candidate: DeviceSignals,
    load_indicators: LoadIndicators
) -> float:
    """
    Adjust signal weights based on collection conditions.
    Under heavy load, timing-based signals get downweighted.
    """
    
    # Base weights (normal conditions)
    weights = {
        'webgl_params':           0.20,  # Load-immune
        'shader_precision':       0.10,  # Load-immune
        'screen_hardware':        0.10,  # Load-immune
        'platform_locale':        0.05,  # Load-immune
        'gpu_render_quantized':   0.25,  # Pixel-based, reliable if context alive
        'audio_peaks':            0.10,  # Mostly stable
        'font_set':               0.10,  # Load-immune (DOM measurement)
        'cpu_ratios':             0.05,  # Timing-based, degrades under load
        'canvas_hash':            0.05,  # Slightly variable under load
    }
    
    # Adjust for load conditions
    if load_indicators:
        is_under_load = (
            load_indicators.estimated_fps < 30 or
            load_indicators.event_loop_latency_ms > 50 or
            load_indicators.memory_pressure == 'critical'
        )
        
        if is_under_load:
            # Downweight timing-sensitive signals
            weights['cpu_ratios'] *= 0.3        # 0.05 → 0.015
            weights['canvas_hash'] *= 0.5       # 0.05 → 0.025
            
            # Redistribute weight to load-immune signals
            freed_weight = (0.05 * 0.7) + (0.05 * 0.5)  # 0.06
            weights['webgl_params'] += freed_weight * 0.4
            weights['gpu_render_quantized'] += freed_weight * 0.4
            weights['font_set'] += freed_weight * 0.2
        
        if load_indicators.gpu_context_lost:
            # GPU render tasks unavailable — redistribute to other signals
            gpu_weight = weights['gpu_render_quantized']
            weights['gpu_render_quantized'] = 0.0
            weights['webgl_params'] += gpu_weight * 0.4
            weights['audio_peaks'] += gpu_weight * 0.3
            weights['font_set'] += gpu_weight * 0.3
    
    # Compute weighted similarity
    total_score = 0.0
    total_weight = sum(w for w in weights.values() if w > 0)
    
    for signal_name, weight in weights.items():
        if weight == 0:
            continue
        similarity = compare_signal(signal_name, incoming, candidate)
        total_score += similarity * weight
    
    return total_score / total_weight  # Normalize to 0-1
```

**Key rules for the SDK:**

```
1. ALWAYS collect Tier 1 signals first (they are instantaneous and load-immune)
2. Measure load indicators BEFORE running Tier 2 (benchmarks, render tasks)
3. If load is extreme (FPS < 15, event loop > 200ms), SKIP CPU benchmarks entirely
   and report them as unavailable — garbage data is worse than no data
4. GPU render tasks: collect pixel hashes, NEVER timing. Handle context loss.
5. AudioContext: use peak frequency analysis (binned), not full hash, for resilience
6. Send load_indicators alongside signals so server can adjust confidence weights
7. If the tab was hidden during collection, flag it — background tabs get throttled
   by the browser and all timing-based signals are unreliable
```

### Rule 2: Network & Location Signals

**Client-side network signals (Web SDK, no permission needed):**

```typescript
// navigator.connection — Chrome/Edge ONLY, undefined in Firefox/Safari
interface ClientNetworkSignals {
  // Available in Chrome/Edge
  connectionEffectiveType?: string;  // '4g', '3g', '2g', 'slow-2g'
  connectionDownlink?: number;       // Mbps estimate
  connectionRtt?: number;            // ms estimate
  connectionSaveData?: boolean;      // data saver mode
  
  // Available everywhere
  timezone: string;                  // Intl.DateTimeFormat().resolvedOptions().timeZone
  timezoneOffset: number;            // new Date().getTimezoneOffset()
  languages: string[];               // navigator.languages
  
  // DO NOT attempt:
  // - WebRTC local IP leak (blocked in modern browsers)
  // - Wi-Fi SSID (not exposed)
  // - Bluetooth (not relevant)
  // - MAC address (never available)
}
```

**Server-side network intelligence (where the real data lives):**

The source IP address hits the server on every request. This is the richest network signal and requires zero client cooperation.

```
From the source IP (resolve server-side):
├─ GeoIP lookup (MaxMind GeoIP2 or equivalent)
│   ├─ Country (~99% accurate)
│   ├─ Region/State (~80% accurate)
│   ├─ City (~70% accurate)
│   ├─ Approximate lat/long (city center, NOT exact location)
│   └─ Postal code (where available)
├─ ASN / ISP identification
│   ├─ AS number + name (e.g., "AS9829 BSNL")
│   ├─ Organization name
│   └─ ISP name
├─ IP classification
│   ├─ Residential vs datacenter vs mobile carrier
│   ├─ Known VPN exit node (database lookup)
│   ├─ Known proxy (transparent/anonymous/elite)
│   ├─ Known Tor exit node (public list)
│   └─ Known cloud provider ranges (AWS, GCP, Azure, etc.)
├─ TLS fingerprint (from the TLS handshake, server-side)
│   ├─ JA3 hash (client-side TLS fingerprint)
│   ├─ JA4 hash (newer, more granular)
│   ├─ Supported cipher suites
│   ├─ TLS extensions
│   └─ ALPN protocols
└─ HTTP analysis
    ├─ Header order (browser-specific)
    ├─ Accept-Language consistency with client-reported languages
    └─ Request timing patterns (latency = distance indicator)
```

**Location: DO NOT use navigator.geolocation in the SDK.** It requires an explicit permission popup, which is unacceptable for a silent fraud detection SDK. Users will deny it, and asking makes the SDK visible. Instead, derive location from IP geolocation server-side. This gives city-level accuracy without any user interaction.

If the host application (the bank's app) has already obtained GPS permission for its own features and passes coordinates to the SDK, accept them as optional enrichment. But never request location permission from the SDK itself.

**Mobile-specific network signals (native SDKs):**

```
Android (no special permissions needed):
├─ ConnectivityManager
│   ├─ Active network type (WiFi/Cellular/Ethernet)
│   ├─ Network capabilities
│   └─ Link properties
├─ TelephonyManager (READ_PHONE_STATE permission — optional, don't require)
│   ├─ Network operator name (carrier)
│   ├─ SIM operator name
│   ├─ Network type (LTE/5G/3G)
│   └─ Data network type
└─ WifiManager (ACCESS_WIFI_STATE — optional)
    └─ Connection info (SSID if permission granted, signal strength)

iOS:
├─ NWPathMonitor
│   ├─ Path status (satisfied/unsatisfied)
│   ├─ Interface type (wifi/cellular/wiredEthernet)
│   └─ Is expensive / is constrained
├─ CTTelephonyNetworkInfo
│   ├─ Carrier name
│   ├─ Mobile country/network code
│   └─ Current radio access technology (LTE/5G/3G)
└─ CNCopyCurrentNetworkInfo (requires location permission — DON'T USE)
```

### Rule 2b: Comprehensive Metadata Collection (Collect Everything, Store Everything)

The SDK and backend must collect and persist ALL available metadata — even signals not used for device fingerprinting today. This data feeds future features: trusted device management, adaptive authentication, user risk profiling, fraud pattern mining, regulatory reporting, and ML model training.

**Principle: Collect wide, store structured, use selectively.** The cost of NOT collecting a signal now is re-deploying the SDK later. Collect it all from day one.

**The backend stores this metadata in PostgreSQL in structured tables per category.** Every metadata record is linked to `(tenant_id, session_id, device_id, timestamp)` so it can be queried, aggregated, and analyzed for any future use case.

#### 2b.1 Device Metadata (Web + Mobile)

Collect on every full payload. Store in `device_metadata` table.

```python
# backend/app/models/metadata.py

class DeviceMetadata(BaseModel):
    """Everything we know about the physical device."""
    
    # --- PLATFORM ---
    platform: str                           # navigator.platform: "MacIntel", "Win32", "Linux x86_64"
    platform_version: Optional[str]         # navigator.userAgentData.platformVersion (Chrome)
    mobile: bool                            # navigator.userAgentData.mobile
    
    # --- BROWSER ---
    browser_name: str                       # Parsed from UA or userAgentData
    browser_version: str                    # Major.minor.patch
    browser_engine: str                     # "Blink", "Gecko", "WebKit"
    browser_engine_version: str
    user_agent_full: str                    # Raw navigator.userAgent
    user_agent_brands: Optional[list[dict]] # navigator.userAgentData.brands (Chrome)
    
    # --- SCREEN / DISPLAY ---
    screen_width: int
    screen_height: int
    screen_avail_width: int                 # Available (minus taskbar etc)
    screen_avail_height: int
    color_depth: int
    pixel_depth: int
    device_pixel_ratio: float
    screen_orientation_type: Optional[str]  # "landscape-primary", "portrait-primary"
    screen_orientation_angle: Optional[int] # 0, 90, 180, 270
    color_gamut: str                        # "srgb", "p3", "rec2020"
    hdr_supported: bool
    
    # --- INPUT CAPABILITIES ---
    max_touch_points: int
    pointer_type: str                       # matchMedia: "fine", "coarse", "none"
    hover_capability: str                   # matchMedia: "hover", "none"
    any_pointer: str                        # matchMedia: "fine", "coarse"
    any_hover: str                          # matchMedia: "hover", "none"
    
    # --- HARDWARE (what browsers expose) ---
    hardware_concurrency: int               # CPU logical cores
    device_memory: Optional[float]          # Chrome only, rounded
    gpu_renderer: Optional[str]             # WebGL UNMASKED_RENDERER
    gpu_vendor: Optional[str]               # WebGL UNMASKED_VENDOR
    webgl_version: Optional[str]
    webgl_max_texture_size: Optional[int]
    webgpu_supported: bool
    
    # --- OS PREFERENCES ---
    prefers_color_scheme: str               # "dark", "light"
    prefers_reduced_motion: bool
    prefers_reduced_transparency: bool
    prefers_contrast: str                   # "no-preference", "more", "less"
    forced_colors: bool                     # Windows high contrast mode
    
    # --- ACCESSIBILITY ---
    # These tell us about the user's environment without identifying them
    inverted_colors: bool                   # matchMedia
    
    # --- FEATURE SUPPORT FLAGS ---
    webgl_supported: bool
    webgl2_supported: bool
    webgpu_supported: bool
    wasm_supported: bool
    service_worker_supported: bool
    web_crypto_supported: bool
    shared_array_buffer_supported: bool
    cross_origin_isolated: bool
    pdf_viewer_enabled: bool                # navigator.pdfViewerEnabled
    cookie_enabled: bool                    # navigator.cookieEnabled
    do_not_track: Optional[str]             # navigator.doNotTrack
    global_privacy_control: Optional[bool]  # navigator.globalPrivacyControl
```

#### 2b.2 Keyboard & Input Metadata

Collect from behavioral events. Store in `input_metadata` table. Aggregated per session.

```python
class InputMetadata(BaseModel):
    """Keyboard, input method, and language context."""
    
    # --- KEYBOARD / IME ---
    keyboard_layout_detected: Optional[str]   # Inferred from keyCode patterns
                                               # e.g., "QWERTY", "AZERTY", "Dvorak", "QWERTZ"
    ime_active: bool                           # Input Method Editor active (CJK, Indic scripts)
    composition_events_seen: bool              # compositionstart/end events = IME usage
    
    # --- LANGUAGE CONTEXT ---
    navigator_language: str                    # navigator.language (primary)
    navigator_languages: list[str]             # navigator.languages (full preference list)
    document_language: Optional[str]           # document.documentElement.lang
    content_language: Optional[str]            # From HTTP Content-Language header (server-side)
    accept_language: Optional[str]             # From HTTP Accept-Language header (server-side)
    
    # --- INPUT CHARACTERISTICS (aggregated per session) ---
    primary_input_method: str                  # "keyboard", "touch", "stylus", "voice"
    typing_hand_estimate: Optional[str]        # "right", "left", "both" — inferred from touch zones
    average_typing_speed_cpm: Optional[float]  # Characters per minute (aggregate, not per-keystroke)
    autocorrect_interaction_rate: Optional[float]  # Mobile: rate of autocorrect acceptance/rejection
    copy_paste_frequency: Optional[float]      # Rate of Ctrl+C/Ctrl+V events per minute
    
    # --- FORM INTERACTION PATTERNS ---
    tab_navigation_used: bool                  # Uses Tab to move between fields
    autofill_detected: bool                    # Rapid field fill suggests browser autofill
    password_manager_detected: bool            # Specific autofill patterns suggest password manager
```

#### 2b.3 Network & Location Metadata

Collected server-side from every request. Store in `network_metadata` table.

```python
class NetworkMetadata(BaseModel):
    """Complete network context — collected server-side, NOT from client."""
    
    # --- IP INTELLIGENCE ---
    ip_address_hash: str                    # SHA-256 hash of IP (don't store raw IP for privacy)
    ip_version: int                         # 4 or 6
    ip_country: str                         # ISO 3166-1 alpha-2
    ip_region: Optional[str]                # State/province
    ip_city: Optional[str]                  # City name
    ip_postal: Optional[str]               # Postal/ZIP code
    ip_latitude: Optional[float]            # City-center approximate
    ip_longitude: Optional[float]
    ip_accuracy_radius_km: Optional[int]    # GeoIP accuracy radius
    ip_timezone: Optional[str]              # Timezone from GeoIP (compare with client-reported)
    
    # --- ISP / ASN ---
    asn: Optional[int]                      # Autonomous System Number (numeric)
    asn_org: Optional[str]                  # e.g., "BSNL", "Reliance Jio", "Airtel"
    isp_name: Optional[str]
    network_name: Optional[str]             # More specific than ISP
    
    # --- IP CLASSIFICATION ---
    ip_type: str                            # "residential", "business", "datacenter",
                                            # "mobile_carrier", "education", "government"
    is_vpn: bool
    is_proxy: bool
    is_tor: bool
    is_relay: bool                          # iCloud Private Relay, Cloudflare WARP
    is_hosting: bool                        # Known hosting/cloud provider
    is_crawler: bool                        # Known search engine bot
    vpn_provider: Optional[str]             # If VPN detected, which provider (if known)
    
    # --- TLS FINGERPRINT ---
    tls_version: Optional[str]              # "TLSv1.3", "TLSv1.2"
    tls_cipher_suite: Optional[str]
    ja3_hash: Optional[str]                 # JA3 fingerprint (identifies browser+version)
    ja4_hash: Optional[str]                 # JA4 fingerprint (newer, more granular)
    
    # --- HTTP METADATA ---
    http_accept_language: Optional[str]     # Raw Accept-Language header
    http_accept_encoding: Optional[str]     # "gzip, deflate, br"
    http_header_order: Optional[list[str]]  # Order of HTTP headers (browser-specific)
    
    # --- CONNECTION CONTEXT (from client, Chrome-only) ---
    connection_type: Optional[str]          # "4g", "3g", "2g", "slow-2g"
    connection_downlink: Optional[float]    # Mbps estimate
    connection_rtt: Optional[int]           # ms estimate
    connection_save_data: Optional[bool]
    
    # --- TIMING ---
    request_latency_ms: Optional[int]       # Server-measured request processing time
    client_server_time_skew_ms: Optional[int]  # Diff between client timestamp and server timestamp
```

#### 2b.4 Session Metadata

Created on session start, enriched throughout. Store in `session_metadata` table.

```python
class SessionMetadata(BaseModel):
    """Everything about this specific session."""
    
    # --- TIMING ---
    session_start: datetime
    session_end: Optional[datetime]
    session_duration_seconds: Optional[int]
    
    # --- ENTRY CONTEXT ---
    referrer_url_hash: Optional[str]        # SHA-256 of document.referrer (not raw URL)
    referrer_domain: Optional[str]          # Domain only, for analytics
    entry_url_path: Optional[str]           # Path without query params
    
    # --- PAGE CONTEXT ---
    document_title_hash: Optional[str]      # Hash of page title
    page_load_time_ms: Optional[int]        # performance.timing based
    dom_content_loaded_ms: Optional[int]
    
    # --- VISIBILITY / FOCUS ---
    tab_visible_duration_seconds: int       # Time document was visible
    tab_hidden_duration_seconds: int        # Time document was hidden
    focus_changes_count: int                # Number of focus/blur events
    visibility_changes_count: int           # Number of visibilitychange events
    
    # --- INTERACTION SUMMARY ---
    total_keystrokes: int
    total_mouse_clicks: int
    total_touch_events: int
    total_scroll_events: int
    pages_navigated: int                    # SPA route changes
    forms_interacted: int                   # Number of forms user started filling
    
    # --- AUTHENTICATION CONTEXT ---
    user_authenticated: bool
    auth_method: Optional[str]              # "password", "otp", "biometric", "sso"
    auth_timestamp: Optional[datetime]
    auth_mfa_used: bool
    auth_step_up_triggered: bool            # Did we trigger a step-up auth?
    auth_step_up_passed: Optional[bool]     # Did the user pass it?
    
    # --- CONTINUOUS AUTH HISTORY ---
    auth_state_transitions: list[dict]      # [{ts, from_state, to_state, reason}]
    lowest_auth_confidence: float           # Lowest confidence seen in this session
    
    # --- TRANSACTION CONTEXT (if annotated by host app) ---
    transactions_attempted: int
    transactions_completed: int
    highest_transaction_amount: Optional[float]
    transaction_currency: Optional[str]
```

#### 2b.5 Trusted Device Registry

When a device has been seen enough times with consistent behavior and the user has authenticated, mark it as trusted. Store in `trusted_devices` table.

```python
class TrustedDevice(BaseModel):
    """A device that has been seen enough to be considered trusted."""
    
    device_id: str
    tenant_id: str
    user_id: str                            # Linked authenticated user
    
    # --- TRUST STATUS ---
    trust_level: str                        # "new", "recognized", "trusted", "compromised"
    trust_score: float                      # 0.0 - 1.0
    trust_established_at: Optional[datetime]
    trust_last_verified_at: Optional[datetime]
    
    # --- DEVICE PROFILE ---
    device_name: Optional[str]              # User-assigned name (if host app supports)
    platform: str                           # "Windows", "macOS", "iOS", "Android"
    browser_primary: str                    # Most-used browser
    browsers_seen: list[str]                # All browsers ever seen
    
    # --- BASELINE SIGNALS (snapshot of known-good state) ---
    baseline_hardware_hash: str             # Tier 1 composite hash when trust established
    baseline_gpu_render_hashes: dict        # Quantized render task hashes
    baseline_audio_peaks: list[dict]        # Binned peak frequencies
    baseline_font_hash: str                 # Font set hash
    baseline_cpu_ratios: dict               # Benchmark ratios
    
    # --- USAGE STATISTICS ---
    sessions_count: int
    total_usage_hours: float
    last_seen_at: datetime
    first_seen_at: datetime
    successful_auths_count: int
    failed_auths_count: int
    
    # --- LOCATION HISTORY ---
    usual_ip_countries: list[str]           # Countries this device usually connects from
    usual_ip_cities: list[str]              # Cities (top 5)
    usual_asns: list[int]                   # ISPs/networks (top 5)
    usual_timezones: list[str]              # Timezones seen
    
    # --- FLAGS ---
    factory_reset_detected: bool
    spoofing_ever_detected: bool
    compromised_at: Optional[datetime]
    compromised_reason: Optional[str]
```

#### 2b.6 Trusted Network Registry

Track networks the user commonly connects from. Store in `trusted_networks` table.

```python
class TrustedNetwork(BaseModel):
    """A network location that a user commonly connects from."""
    
    tenant_id: str
    user_id: str
    
    # --- NETWORK IDENTITY ---
    asn: int
    isp_name: str
    ip_country: str
    ip_region: Optional[str]
    ip_city: Optional[str]
    ip_type: str                            # "residential", "business", "mobile_carrier"
    
    # --- TRUST ---
    trust_level: str                        # "new", "recognized", "trusted"
    sessions_from_network: int
    first_seen_at: datetime
    last_seen_at: datetime
    successful_auths_from_network: int
    
    # --- PATTERN ---
    typical_time_of_day: Optional[str]      # "morning", "afternoon", "evening", "night"
    typical_days_of_week: list[str]         # ["MON", "TUE", "WED", ...]
    average_session_duration_minutes: float
```

#### 2b.7 Trusted Location Registry

Track geographic locations the user frequents. Store in `trusted_locations` table.

```python
class TrustedLocation(BaseModel):
    """A geographic area the user commonly operates from."""
    
    tenant_id: str
    user_id: str
    
    # --- LOCATION (derived from IP, city-level) ---
    country: str
    region: Optional[str]
    city: Optional[str]
    timezone: str
    
    # --- TRUST ---
    trust_level: str
    sessions_from_location: int
    first_seen_at: datetime
    last_seen_at: datetime
    
    # --- IMPOSSIBLE TRAVEL DETECTION ---
    # If user was in Location A at time T1 and Location B at time T2,
    # and distance(A,B) / (T2-T1) > physically_possible_speed → flag
    last_session_timestamp: datetime
    last_session_ip_lat: Optional[float]
    last_session_ip_lon: Optional[float]
```

#### 2b.8 PostgreSQL Schema for Metadata Storage

```sql
-- All metadata tables follow the same pattern:
-- (id, tenant_id, device_id, session_id, user_id, timestamp, ...columns...)
-- Partitioned by time for efficient queries and retention management.

CREATE TABLE device_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(64) NOT NULL,
    device_id VARCHAR(64) NOT NULL,
    session_id VARCHAR(64) NOT NULL,
    collected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- All fields from DeviceMetadata model stored as JSONB
    -- JSONB allows flexible schema evolution without migrations
    data JSONB NOT NULL,
    
    -- Indexes for common query patterns
    CONSTRAINT device_metadata_tenant_idx UNIQUE (tenant_id, device_id, session_id)
) PARTITION BY RANGE (collected_at);

-- Create monthly partitions
CREATE TABLE device_metadata_y2026m04 PARTITION OF device_metadata
    FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');

-- Same pattern for all metadata tables
CREATE TABLE input_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(64) NOT NULL,
    device_id VARCHAR(64) NOT NULL,
    session_id VARCHAR(64) NOT NULL,
    collected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    data JSONB NOT NULL
) PARTITION BY RANGE (collected_at);

CREATE TABLE network_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(64) NOT NULL,
    device_id VARCHAR(64) NOT NULL,
    session_id VARCHAR(64) NOT NULL,
    source_ip_hash VARCHAR(64) NOT NULL,      -- indexed for IP-based queries
    collected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    data JSONB NOT NULL
) PARTITION BY RANGE (collected_at);

CREATE TABLE session_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(64) NOT NULL,
    device_id VARCHAR(64) NOT NULL,
    session_id VARCHAR(64) NOT NULL UNIQUE,
    user_id VARCHAR(64),                       -- null if not authenticated
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    data JSONB NOT NULL
) PARTITION BY RANGE (started_at);

-- Trusted entity tables (not partitioned — small, long-lived)
CREATE TABLE trusted_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(64) NOT NULL,
    device_id VARCHAR(64) NOT NULL,
    user_id VARCHAR(64) NOT NULL,
    trust_level VARCHAR(20) NOT NULL DEFAULT 'new',
    trust_score REAL NOT NULL DEFAULT 0.0,
    data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, device_id, user_id)
);

CREATE TABLE trusted_networks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(64) NOT NULL,
    user_id VARCHAR(64) NOT NULL,
    asn INTEGER NOT NULL,
    ip_country VARCHAR(2) NOT NULL,
    ip_city VARCHAR(128),
    trust_level VARCHAR(20) NOT NULL DEFAULT 'new',
    data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, user_id, asn, ip_country, ip_city)
);

CREATE TABLE trusted_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(64) NOT NULL,
    user_id VARCHAR(64) NOT NULL,
    country VARCHAR(2) NOT NULL,
    region VARCHAR(128),
    city VARCHAR(128),
    timezone VARCHAR(64) NOT NULL,
    trust_level VARCHAR(20) NOT NULL DEFAULT 'new',
    data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, user_id, country, region, city)
);

-- Key indexes for future query patterns
CREATE INDEX idx_device_meta_device ON device_metadata (tenant_id, device_id, collected_at DESC);
CREATE INDEX idx_network_meta_ip ON network_metadata (source_ip_hash, collected_at DESC);
CREATE INDEX idx_session_meta_user ON session_metadata (tenant_id, user_id, started_at DESC);
CREATE INDEX idx_trusted_device_user ON trusted_devices (tenant_id, user_id);
CREATE INDEX idx_trusted_network_user ON trusted_networks (tenant_id, user_id);
CREATE INDEX idx_trusted_location_user ON trusted_locations (tenant_id, user_id);

-- Retention policy: metadata tables auto-purge after configurable period per tenant
-- Default: 90 days for raw metadata, trusted registries kept indefinitely
-- Implemented via pg_cron or application-level background task
```

#### 2b.9 Backend Metadata Service

```python
# backend/app/services/metadata_collector.py

class MetadataCollector:
    """
    Collects and persists all metadata from SDK payloads and server context.
    Called within every /v1/signals request handler.
    Writes are NON-BLOCKING — use FastAPI BackgroundTasks.
    """
    
    async def collect_and_store(
        self,
        payload: FullPayload | DiffPayload | BehavioralBatch,
        request: Request,
        network: NetworkContext,
        resolution: DeviceResolution,
        background_tasks: BackgroundTasks,
    ):
        # 1. Extract device metadata from payload
        device_meta = self.extract_device_metadata(payload)
        
        # 2. Extract input metadata from behavioral events (if present)
        input_meta = self.extract_input_metadata(payload)
        
        # 3. Build network metadata from server context
        network_meta = self.build_network_metadata(request, network)
        
        # 4. Update session metadata (enrichment)
        session_meta = self.update_session_metadata(payload, resolution)
        
        # 5. Evaluate trusted status updates
        trust_updates = self.evaluate_trust_updates(resolution, network)
        
        # ALL WRITES ARE BACKGROUND — don't block the risk response
        background_tasks.add_task(self.persist_device_metadata, device_meta)
        background_tasks.add_task(self.persist_input_metadata, input_meta)
        background_tasks.add_task(self.persist_network_metadata, network_meta)
        background_tasks.add_task(self.persist_session_metadata, session_meta)
        background_tasks.add_task(self.update_trusted_registries, trust_updates)
```

#### 2b.10 What This Enables in the Future

Store now, use later:

```
TRUSTED DEVICE MANAGEMENT:
  "Is this a device we've seen before? How often? From where?"
  → Query trusted_devices + device_metadata

ADAPTIVE AUTHENTICATION:
  "This user usually logs in from BSNL in Hyderabad at 9am. 
   Now they're on a VPN in Frankfurt at 3am. Step up auth."
  → Query trusted_networks + trusted_locations + session_metadata

IMPOSSIBLE TRAVEL DETECTION:
  "Last session was from Hyderabad 5 minutes ago. 
   Now connecting from London. Physically impossible."
  → Query trusted_locations.last_session_timestamp + IP geolocation

USER RISK PROFILING:
  "This user has 3 trusted devices, always uses the same 2 networks,
   typing speed is consistent, never triggered spoofing flags."
  → Aggregate across all metadata tables

FRAUD PATTERN MINING:
  "All accounts opened from datacenter IPs with AZERTY keyboards
   and French language but Indian phone numbers — fraud ring?"
  → Query network_metadata + input_metadata across tenants

REGULATORY REPORTING:
  "Show all sessions for user X in the last 90 days with
   network context and authentication events."
  → Query session_metadata + network_metadata joined on session_id

ML TRAINING DATA:
  "Build a model that predicts ATO from device drift + network change + 
   behavioral shift patterns."
  → Export from all metadata tables with labels from confirmed fraud cases
```

### Rule 3: Collection Protocol (Full → Diff)

The SDK MUST NOT re-send all signals on every heartbeat. This wastes bandwidth and CPU.

**Three signal categories with different collection strategies:**

```
IMMUTABLE (collected once per session, never changes):
  All Tier 1 signals, GPU render tasks, AudioContext, CPU benchmarks, fonts
  → Collected on SDK initialization
  → Sent as FULL payload (3-8KB compressed)
  → Never re-collected during the session

MUTABLE (re-checked every 2-5 minutes, only diff sent):
  Network context (connection type, speed estimates)
  Battery state (mobile)
  Window focus/visibility
  Screen orientation (mobile)
  → Re-collected on timer
  → Compute JSON Patch diff (RFC 6902) against previous snapshot
  → If diff is empty → send NOTHING (zero bytes)
  → If diff exists → send only changed fields (50-200 bytes compressed)

CONTINUOUS (event stream, always flowing):
  Behavioral events (keystroke, mouse, touch, scroll, navigation)
  → Collected via passive event listeners
  → Batched: flush every 500ms OR every 50 events, whichever comes first
  → If no events (user idle) → send NOTHING
  → Compact encoding: relative timestamps, 2-char signal codes
```

**Transport:**

The SDK sends payloads via standard `fetch()` (web) or `URLSession`/`OkHttp` (mobile) as HTTPS POST requests to the FastAPI backend. No WebSocket, no gRPC, no streaming — just simple HTTP.

```typescript
// Web SDK transport — just fetch()
async function sendPayload(payload: FullPayload | DiffPayload | BehavioralBatch): Promise<RiskResponse> {
  const compressed = await compress(JSON.stringify(payload), 'gzip');
  
  const response = await fetch(`${this.endpoint}/v1/signals`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Encoding': 'gzip',
      'X-KP-Tenant': this.tenantKey,
      'X-KP-Session': this.sessionId,
    },
    body: compressed,
    keepalive: true,  // survives page unload
  });
  
  return response.json();  // { device_id, score, decision, reason_codes, ... }
}
```

**Wire format:**

```typescript
// Full payload — sent once on init
interface FullPayload {
  v: 1;                        // protocol version
  type: 'full';
  sid: string;                 // session ID (UUID v4)
  ts: number;                  // timestamp (ms since epoch)
  sdk: string;                 // SDK version
  hw: HardwareFingerprint;     // all Tier 1 + Tier 2 signals
  env: EnvironmentFingerprint; // Tier 3 browser-specific signals
  net: ClientNetworkSignals;   // client-side network signals
  load: LoadIndicators;        // device load state during collection (Rule 1b)
  meta: ClientMetadata;        // all collectable metadata (Rule 2b)
  sh: string;                  // snapshot hash for future diff comparison
}

// Client metadata — everything the browser exposes, collected for future use
interface ClientMetadata {
  // User Agent data
  userAgent: string;
  userAgentBrands?: Array<{brand: string; version: string}>;
  platformVersion?: string;
  isMobile: boolean;
  
  // Screen
  screenAvailWidth: number;
  screenAvailHeight: number;
  orientationType?: string;
  orientationAngle?: number;
  
  // Input
  pointerType: string;         // "fine" | "coarse" | "none"
  hoverCapability: string;     // "hover" | "none"
  
  // OS preferences
  prefersContrast: string;     // "no-preference" | "more" | "less"
  forcedColors: boolean;
  invertedColors: boolean;
  
  // Feature flags
  wasmSupported: boolean;
  serviceWorkerSupported: boolean;
  webCryptoSupported: boolean;
  pdfViewerEnabled: boolean;
  cookieEnabled: boolean;
  doNotTrack?: string;
  globalPrivacyControl?: boolean;
  
  // Keyboard / language context
  navigatorLanguage: string;
  navigatorLanguages: string[];
  documentLanguage?: string;
  
  // Session context
  referrerDomain?: string;
  pageLoadTimeMs?: number;
  documentVisibilityState: string;
}

// Diff payload — sent on mutable signal change
interface DiffPayload {
  v: 1;
  type: 'diff';
  sid: string;
  ts: number;
  psh: string;                 // previous snapshot hash
  ops: JsonPatchOp[];          // RFC 6902 operations
  sh: string;                  // new snapshot hash
}

// Behavioral batch — sent every 500ms or 50 events
interface BehavioralBatch {
  v: 1;
  type: 'beh';
  sid: string;
  t0: number;                  // batch start timestamp
  t1: number;                  // batch end timestamp
  ev: CompactEvent[];          // [{t, s, d}] — relative ts, signal code, data
}

// Compact event format (minimize bytes)
interface CompactEvent {
  t: number;    // ms offset from t0 (not absolute timestamp — saves 8 bytes per event)
  s: string;    // 2-char signal code: 'kd'=keydown, 'ku'=keyup, 'mm'=mousemove,
                // 'cl'=click, 'sc'=scroll, 'ts'=touchstart, 'tm'=touchmove, 'te'=touchend
  d: unknown;   // signal-specific data, as compact as possible
}
```

### Rule 4: Server-Side Device Resolution

The client SDK does NOT compute a device ID. It sends raw signals. The server resolves identity.

**Resolution pipeline (all within a single FastAPI request handler):**

```
POST /v1/signals arrives with full or diff payload
│
├── 1. PARSE + VALIDATE (Pydantic model validation)
│   - Schema validation via Pydantic
│   - Tenant API key authentication
│   - Rate limiting check (Valkey counter)
│
├── 2. ENRICH with server-side signals
│   - Extract source IP from request (request.client.host or X-Forwarded-For)
│   - GeoIP lookup: country, region, city, lat/long (MaxMind local DB, <1ms)
│   - ASN/ISP lookup (MaxMind ASN DB, <1ms)
│   - IP classification: residential/datacenter/VPN/proxy/Tor
│   - TLS fingerprint: JA3/JA4 from connection metadata (if available via reverse proxy)
│
├── 3. ANTI-SPOOFING validation (signal_validator.py)
│   - Run 9 cross-signal consistency checks
│   - Compute spoofing score (0-1)
│   - Flag inconsistencies in response
│
├── 4. DEVICE RESOLUTION (device_resolver.py)
│   4a. Exact match: hash Tier 1 signals → lookup in Valkey cache → PG fallback
│   4b. Fuzzy match: weighted similarity against candidate devices
│   4c. Graph resolution: Apache AGE query for context boost
│   4d. New device creation: insert into PG + Valkey
│
├── 5. RISK SCORING (risk_scorer.py)
│   - Deterministic rules first (velocity, geo, device trust)
│   - ML scoring second (if model loaded)
│   - Graph reasoning third (if graph available)
│   - Produce final decision: ALLOW/CHALLENGE/BLOCK/REVIEW
│
├── 6. AUDIT TRAIL (audit.py)
│   - Generate hash-chained audit record
│   - Write to PG (can be async background task via BackgroundTasks)
│
└── 7. RESPOND
    Return full JSON risk response (see below)
    Target: <200ms total
```

**Response Format — The `POST /v1/signals` response must be a readable JSON object, not binary.**

This is the most important API contract. The client (and integration engineers at banks) will read this directly. It must be self-explanatory.

```python
# backend/app/models/decisions.py

from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional

class Decision(str, Enum):
    ALLOW = "allow"
    CHALLENGE = "challenge"
    BLOCK = "block"
    REVIEW = "review"

class AuthState(str, Enum):
    VERIFYING = "verifying"
    VERIFIED = "verified"
    DEGRADED = "degraded"
    LOST = "lost"

class ResolutionMethod(str, Enum):
    EXACT = "exact_match"
    FUZZY = "fuzzy_match"
    GRAPH = "graph_assisted"
    NEW = "new_device"

class DeviceDrift(BaseModel):
    """How much the current signals have drifted from the known baseline."""
    
    overall_drift_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="0.0 = identical to baseline, 1.0 = completely different device"
    )
    
    # Per-signal-group drift breakdown
    gpu_drift: float = Field(
        ..., ge=0.0, le=1.0,
        description="GPU render output drift from baseline"
    )
    audio_drift: float = Field(
        ..., ge=0.0, le=1.0,
        description="AudioContext peak frequency drift from baseline"
    )
    screen_drift: float = Field(
        ..., ge=0.0, le=1.0,
        description="Screen/display hardware drift from baseline"
    )
    font_drift: float = Field(
        ..., ge=0.0, le=1.0,
        description="Installed font set drift from baseline"
    )
    cpu_drift: float = Field(
        ..., ge=0.0, le=1.0,
        description="CPU benchmark ratio drift from baseline"
    )
    network_drift: float = Field(
        ..., ge=0.0, le=1.0,
        description="Network location / ISP / IP type drift from baseline"
    )
    behavior_drift: float = Field(
        ..., ge=0.0, le=1.0,
        description="Behavioral pattern drift (if behavioral signals present)"
    )
    
    # What caused the drift
    drift_reasons: list[str] = Field(
        default_factory=list,
        description="Human-readable reasons for drift, e.g. "
                    "['new_browser_detected', 'ip_region_changed', 'font_set_changed_3_fonts']"
    )
    
    # Is this drift expected or suspicious?
    drift_classification: str = Field(
        ...,
        description="'normal' (browser update, IP change), "
                    "'suspicious' (sudden hardware change), "
                    "'critical' (multiple signals changed simultaneously)"
    )

class NetworkContext(BaseModel):
    """Server-side network intelligence derived from the request IP."""
    ip_country: str
    ip_region: Optional[str] = None
    ip_city: Optional[str] = None
    ip_lat: Optional[float] = None
    ip_lon: Optional[float] = None
    asn: Optional[str] = None             # e.g., "AS9829"
    isp: Optional[str] = None             # e.g., "BSNL"
    ip_type: str                           # "residential", "datacenter", "mobile_carrier"
    vpn_detected: bool = False
    proxy_detected: bool = False
    tor_detected: bool = False
    tls_fingerprint: Optional[str] = None  # JA3/JA4 hash

class SpoofingFlags(BaseModel):
    """Results of anti-spoofing consistency checks."""
    spoofing_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="0.0 = all checks passed, 1.0 = definitely spoofed"
    )
    checks_passed: int
    checks_failed: int
    failed_checks: list[str] = Field(
        default_factory=list,
        description="Which specific checks failed, e.g. "
                    "['gpu_renderer_vs_performance', 'platform_vs_fonts']"
    )
    automation_detected: bool = False
    anti_detect_browser_suspected: bool = False

class RiskResponse(BaseModel):
    """
    The complete response returned by POST /v1/signals.
    This is a readable JSON object — not binary, not protobuf.
    Bank integration engineers will read this directly.
    """
    
    # === DEVICE IDENTITY ===
    device_id: Optional[str] = Field(
        None,
        description="Resolved device ID. Null if new device being created."
    )
    device_is_new: bool = Field(
        False,
        description="True if this is the first time we've seen this device."
    )
    resolution_method: ResolutionMethod = Field(
        ...,
        description="How the device was identified: exact_match, fuzzy_match, graph_assisted, new_device"
    )
    resolution_confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Confidence in device identification. "
                    ">0.85 = high, 0.65-0.85 = medium, <0.65 = low"
    )
    browsers_seen_on_device: int = Field(
        1,
        description="Number of distinct browsers seen on this device"
    )
    
    # === DEVICE DRIFT (the key differentiator) ===
    device_drift: DeviceDrift = Field(
        ...,
        description="How much the device signals have drifted from the known baseline. "
                    "This is what detects device changes, ATO, and environmental anomalies."
    )
    
    # === RISK SCORING ===
    risk_score: int = Field(
        ..., ge=0, le=1000,
        description="Composite risk score. 0 = no risk, 1000 = maximum risk. "
                    "Recommended thresholds: <200 allow, 200-600 monitor, 600-800 challenge, >800 block"
    )
    decision: Decision = Field(
        ...,
        description="Recommended action: allow, challenge, block, review"
    )
    reason_codes: list[str] = Field(
        default_factory=list,
        description="Machine-readable reason codes explaining the decision, e.g. "
                    "['DEVICE_NEW', 'IP_DATACENTER', 'GPU_DRIFT_HIGH', 'NETWORK_IMPOSSIBLE_TRAVEL']"
    )
    
    # === CONTINUOUS AUTH STATE ===
    continuous_auth_state: AuthState = Field(
        ...,
        description="Current authentication confidence: verifying, verified, degraded, lost"
    )
    
    # === NETWORK INTELLIGENCE ===
    network: NetworkContext = Field(
        ...,
        description="Server-side network intelligence derived from request IP"
    )
    
    # === SPOOFING DETECTION ===
    spoofing: SpoofingFlags = Field(
        ...,
        description="Anti-spoofing consistency check results"
    )
    
    # === SESSION ===
    session_id: str
    session_age_seconds: int = Field(
        0,
        description="How long this session has been active"
    )
    signals_received: int = Field(
        1,
        description="Total signal payloads received in this session"
    )

# Example response:
# {
#   "device_id": "dev_8f3a2b1c",
#   "device_is_new": false,
#   "resolution_method": "fuzzy_match",
#   "resolution_confidence": 0.87,
#   "browsers_seen_on_device": 2,
#   "device_drift": {
#     "overall_drift_score": 0.23,
#     "gpu_drift": 0.05,
#     "audio_drift": 0.02,
#     "screen_drift": 0.0,
#     "font_drift": 0.15,
#     "cpu_drift": 0.03,
#     "network_drift": 0.45,
#     "behavior_drift": 0.12,
#     "drift_reasons": [
#       "new_browser_detected",
#       "ip_region_changed_hyderabad_to_bangalore",
#       "font_set_changed_3_fonts_added"
#     ],
#     "drift_classification": "normal"
#   },
#   "risk_score": 320,
#   "decision": "allow",
#   "reason_codes": ["BROWSER_SWITCH", "IP_REGION_CHANGE"],
#   "continuous_auth_state": "verified",
#   "network": {
#     "ip_country": "IN",
#     "ip_region": "Karnataka",
#     "ip_city": "Bangalore",
#     "ip_lat": 12.97,
#     "ip_lon": 77.59,
#     "asn": "AS9829",
#     "isp": "BSNL",
#     "ip_type": "residential",
#     "vpn_detected": false,
#     "proxy_detected": false,
#     "tor_detected": false,
#     "tls_fingerprint": "ja3_abc123..."
#   },
#   "spoofing": {
#     "spoofing_score": 0.05,
#     "checks_passed": 8,
#     "checks_failed": 1,
#     "failed_checks": ["timezone_vs_ip_minor_mismatch"],
#     "automation_detected": false,
#     "anti_detect_browser_suspected": false
#   },
#   "session_id": "sess_9d4e5f6a",
#   "session_age_seconds": 342,
#   "signals_received": 7
# }
```

**FastAPI endpoint implementation pattern:**

```python
# backend/app/api/ingest.py

from fastapi import APIRouter, Request, Depends, BackgroundTasks
from app.models.signals import FullPayload, DiffPayload, BehavioralBatch
from app.models.decisions import RiskResponse
from app.services.signal_validator import SignalValidator
from app.services.device_resolver import DeviceResolver
from app.services.network_intel import NetworkIntelligence
from app.services.risk_scorer import RiskScorer
from app.services.audit import AuditService
from app.dependencies import get_db, get_cache, get_geoip

router = APIRouter()

@router.post("/v1/signals", response_model=RiskResponse)
async def ingest_signals(
    payload: FullPayload | DiffPayload | BehavioralBatch,
    request: Request,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
    cache=Depends(get_cache),
    geoip=Depends(get_geoip),
):
    # 1. Extract server-side signals
    client_ip = request.headers.get("X-Forwarded-For", request.client.host)
    network = await NetworkIntelligence(geoip).analyze(client_ip, request)
    
    # 2. Validate (anti-spoofing)
    spoofing = await SignalValidator().validate(payload, network)
    
    # 3. Resolve device identity
    resolution = await DeviceResolver(db, cache).resolve(payload, network)
    
    # 4. Compute drift from baseline
    drift = await DeviceResolver(db, cache).compute_drift(
        payload, resolution.device_id
    )
    
    # 5. Score risk
    risk = await RiskScorer(db).score(
        payload, resolution, drift, network, spoofing
    )
    
    # 6. Audit trail (non-blocking)
    background_tasks.add_task(
        AuditService(db).record,
        payload, resolution, drift, risk, network, spoofing
    )
    
    # 7. Return readable JSON
    return RiskResponse(
        device_id=resolution.device_id,
        device_is_new=resolution.is_new,
        resolution_method=resolution.method,
        resolution_confidence=resolution.confidence,
        browsers_seen_on_device=resolution.browser_count,
        device_drift=drift,
        risk_score=risk.score,
        decision=risk.decision,
        reason_codes=risk.reason_codes,
        continuous_auth_state=risk.auth_state,
        network=network,
        spoofing=spoofing,
        session_id=payload.sid,
        session_age_seconds=risk.session_age,
        signals_received=risk.signal_count,
    )
```

### Rule 5: Anti-Spoofing Consistency Matrix

Every full payload MUST pass these cross-signal validation checks. Failures don't necessarily mean fraud — they mean the signals are inconsistent, which itself is a risk signal.

```
CHECK 1: GPU renderer vs render task performance
  If renderer claims "RTX 4090" but render tasks complete at integrated-GPU speed → SPOOFED
  Implementation: maintain a lookup table of known GPU models → expected render time ranges

CHECK 2: Platform vs font set
  If navigator.platform = "MacIntel" but fonts include Windows-only fonts (Segoe UI, Calibri) → SPOOFED
  If navigator.platform = "Win32" but fonts include macOS-only fonts (SF Pro, Helvetica Neue) → SPOOFED

CHECK 3: Screen resolution vs platform
  Maintain a list of known resolution+DPR combinations per platform family
  e.g., MacBook at DPR=2 should have specific resolution sets
  Unknown combinations → SUSPICIOUS

CHECK 4: Canvas/Audio stability (same-session)
  Run canvas fingerprint twice in same session
  If hashes differ → NOISE INJECTION DETECTED (anti-fingerprinting extension active)
  This is itself a signal (flags privacy-conscious or potentially malicious environment)

CHECK 5: deviceMemory vs platform
  If present (Chrome-only) and value > 8 → SPOOFED (Chrome caps at 8)
  If present but browser claims to be Firefox/Safari → SPOOFED (these browsers don't expose it)

CHECK 6: Automation detection
  navigator.webdriver === true → AUTOMATION
  window.chrome === undefined on Chrome → HEADLESS
  Check for CDP (Chrome DevTools Protocol) artifacts
  Check for Playwright/Puppeteer specific markers
  Presence of common headless browser indicators

CHECK 7: Entropy anomaly
  If ALL signals are at maximum entropy (every signal is extremely unique) → ANTI-DETECT BROWSER
  Real devices have some signals that cluster with common devices
  Perfectly unique everything is actually suspicious

CHECK 8: Timezone vs IP geolocation
  Client-reported timezone must be plausible given IP geolocation
  User in IP range geolocated to India but timezone = "America/New_York" → SUSPICIOUS (VPN likely)

CHECK 9: Language vs IP geolocation
  navigator.languages should be plausible for IP-geolocated region
  Not a hard rule (multilingual users exist), but extreme mismatches add risk
```

### Rule 6: Knowledge Graph Schema

Use Apache AGE on PostgreSQL. Define these entity types and relationships:

```sql
-- Vertex labels (entities)
CREATE VLABEL IF NOT EXISTS Device;       -- Physical device
CREATE VLABEL IF NOT EXISTS BrowserEnv;   -- Browser environment on a device
CREATE VLABEL IF NOT EXISTS UserAccount;  -- Authenticated user
CREATE VLABEL IF NOT EXISTS Session;      -- Individual session
CREATE VLABEL IF NOT EXISTS NetworkLoc;   -- Network location (IP range + ASN)
CREATE VLABEL IF NOT EXISTS RiskIndicator;-- Flagged risk signal

-- Edge labels (relationships)
CREATE ELABEL IF NOT EXISTS SEEN_IN;      -- Device → BrowserEnv
CREATE ELABEL IF NOT EXISTS USED_BY;      -- Device → UserAccount
CREATE ELABEL IF NOT EXISTS HAS_SESSION;  -- UserAccount → Session
CREATE ELABEL IF NOT EXISTS FROM_DEVICE;  -- Session → Device
CREATE ELABEL IF NOT EXISTS FROM_NETWORK; -- Session → NetworkLoc
CREATE ELABEL IF NOT EXISTS FLAGGED;      -- any → RiskIndicator
CREATE ELABEL IF NOT EXISTS LINKED_TO;    -- UserAccount → UserAccount (fraud ring)
CREATE ELABEL IF NOT EXISTS SHARED_WITH;  -- Device → UserAccount (shared device)

-- Device properties
-- id, hardwareHash, tier1Hash, firstSeen, lastSeen, trustScore,
-- factoryResetCount, spoofingDetected, platform, gpuClass

-- BrowserEnv properties  
-- id, browser, version, environmentHash, tlsFingerprint, firstSeen, lastSeen

-- Session properties
-- id, startTime, endTime, authState (VERIFYING/VERIFIED/DEGRADED/LOST),
-- riskScore, decisionHistory[]

-- NetworkLoc properties
-- id, ipRange, asn, isp, country, region, city, ipType (residential/datacenter/mobile),
-- vpnDetected, proxyDetected, torDetected
```

### Rule 7: Audit Trail

Every device resolution decision MUST produce an immutable, hash-chained audit record. This is non-negotiable for regulated financial institutions.

```typescript
interface AuditRecord {
  id: string;                // UUID
  timestamp: string;         // ISO-8601
  tenantId: string;
  sessionId: string;
  deviceId: string | null;   // null if new device
  
  decision: 'RESOLVED_EXACT' | 'RESOLVED_FUZZY' | 'RESOLVED_GRAPH' | 'NEW_DEVICE' | 'SPOOFING_DETECTED';
  confidence: number;        // 0-1
  
  pipeline: {
    validation: {
      checksRun: number;
      checksFailed: string[];  // which consistency checks failed
      spoofingScore: number;
    };
    exactMatch: {
      attempted: boolean;
      matched: boolean;
      hash: string;
    };
    fuzzyMatch: {
      attempted: boolean;
      candidatesEvaluated: number;
      bestScore: number;
      signalScores: Record<string, number>;  // per-signal similarity
    };
    graphResolution: {
      attempted: boolean;
      boostApplied: number;
      pathsEvaluated: number;
      evidenceUsed: string[];  // e.g., ["same_user_auth", "network_overlap"]
    };
  };
  
  // Hash chain for tamper detection
  previousHash: string;
  hash: string;              // SHA-256(previousHash + JSON(this record without hash))
}
```

### Rule 8: Privacy Compliance

- **NEVER collect PII**: No names, emails, phone numbers, biometric templates.
- **NEVER request GPS permission**: Derive location from IP server-side.
- **Anonymize all signals before transit**: Hash-based anonymization at SDK layer.
- **Data residency**: Per-tenant configuration (IN, EU, US). Signals MUST NOT leave configured region.
- **GDPR**: Anonymized behavioral/device data with no PII = non-personal data under most interpretations. But treat it as personal data anyway for safety.
- **DPDP Act (India)**: No personal data processed. Anonymization at collection point.
- **Zero raw signal storage**: Server processes signals and stores only computed hashes, scores, and graph relationships. Raw signal payloads are discarded after processing (configurable retention per tenant).

### Rule 9: Performance Requirements

- Web SDK initialization: <500ms (non-blocking, async)
- Web SDK bundle size: <15KB gzipped (tree-shakeable)
- Full payload transmission: <100ms
- Server-side resolution: <200ms p99
- Behavioral batch latency: <50ms from flush to server receipt
- Memory overhead (web): <5MB additional heap
- CPU overhead (web): <2% additional CPU during idle, <5% during active collection

### Rule 11: Debug Mode vs Production Mode

The SDK and backend MUST support two distinct operating modes. Engineers need to see exactly what's happening during development; production must be locked down.

**SDK mode is set at initialization:**

```typescript
const kp = KProtect.init({
  tenantKey: 'TENANT_KEY',
  mode: 'debug' | 'production',  // explicit, never auto-detected
  endpoint: 'https://api.kprotect.io/v1',
});
```

**What changes between modes:**

```
┌──────────────────────────────┬───────────────────────┬──────────────────────────┐
│ Concern                      │ DEBUG mode            │ PRODUCTION mode          │
├──────────────────────────────┼───────────────────────┼──────────────────────────┤
│ Payload format               │ Plain JSON, readable  │ Compressed + encrypted   │
│ Payload signing (HMAC)       │ OFF                   │ ON (HMAC-SHA256)         │
│ Payload encryption           │ OFF (plain JSON body) │ ON (AES-256-GCM)         │
│ Console logging              │ ON (full signal dump) │ OFF (zero console output)│
│ SDK source                   │ Unminified, sourcemap │ Obfuscated + minified    │
│ Network inspector readable   │ YES (plain JSON)      │ NO (encrypted blob)      │
│ Replay protection (nonce)    │ ON (always enforced)  │ ON                       │
│ Timestamp validation         │ WARN only (log, pass) │ STRICT (reject if stale) │
│ Anti-tamper checks           │ WARN only             │ ENFORCE (reject)         │
│ Error details in response    │ FULL stack traces     │ Generic error codes only │
│ Render task config           │ Static (hardcoded)    │ Server-driven (rotating) │
│ Debug info in response       │ YES (see below)       │ NEVER                    │
└──────────────────────────────┴───────────────────────┴──────────────────────────┘
```

**SDK build produces TWO artifacts:**

```bash
pnpm build
# dist/kprotect.debug.js      — unminified, console logging, plain JSON payloads, sourcemap
# dist/kprotect.min.js        — obfuscated, minified, encrypted payloads, zero logging
```

**Debug mode SDK console output (shows every signal collected):**

```
[KProtect Debug] Full collection complete
  Tier 1: { webglParams: {maxTextureSize: 16384, ...}, screen: {width: 2560, ...} }
  Tier 2: { gpuRender: {task1: "sha256:abc...", ...}, audio: {peaks: [...]} }
  Load:   { fps: 58, eventLoopLatency: 4ms, memoryPressure: "low" }
  Payload: 4.2KB uncompressed JSON
```

**Debug mode backend response includes `debug` field:**

```python
class DebugInfo(BaseModel):
    raw_signals_received: dict              # echo back the payload
    signal_hashes_computed: dict            # all internal hashes
    resolution_trace: dict                  # step-by-step: exact → fuzzy → graph with scores
    anti_spoofing_details: list[dict]       # every check with pass/fail and detail string
    timing: dict                            # per-stage latency breakdown: validation_ms, fuzzy_ms, etc.
```

**Production mode payload on the wire:**

```
POST /v1/signals
Content-Type: application/octet-stream
X-KP-Tenant: tk_abc123
X-KP-Nonce: <uuid>
X-KP-Timestamp: 1712678400000
X-KP-Signature: <hmac_sha256_hex>
Body: <12-byte IV><AES-256-GCM ciphertext>
```

Network inspector sees opaque binary. Attacker learns nothing.

**Backend auto-detects mode from Content-Type:**

- `application/json` → debug mode → parse JSON directly
- `application/octet-stream` → production mode → verify HMAC → check nonce → check timestamp → decrypt AES-256-GCM → parse JSON

**Rollup production build pipeline:**

```
TypeScript → terser (drop_console, mangle, 2-pass compress)
           → javascript-obfuscator (controlFlowFlattening, deadCodeInjection,
             stringArray with RC4 encoding, selfDefending, renameGlobals)
           → output: kprotect.min.js (no sourcemap)
```

**Server-driven render task rotation (production only):**

In production, SDK calls `GET /v1/config/render-tasks` on init. Server returns the current set of GPU render tasks (vertex shaders, fragment shaders, viewport config). Tasks rotate server-side without SDK updates. A fraudster cannot hardcode expected pixel output because tasks change. In debug mode, tasks are hardcoded in the SDK source for simplicity.

### Rule 12: Replay Attack Prevention

Every payload includes `X-KP-Nonce` (UUID v4, fresh per request) and `X-KP-Timestamp` (ms since epoch).

**Server validation:**

1. **Nonce**: Store in Valkey with 5-min TTL. If already seen → `409 Conflict "replay_detected"`. Always enforced (both modes).
2. **Timestamp**: `abs(server_time - client_time) < 30_000ms`. If stale → debug: log warning and proceed. Production: `400 Bad Request "stale_payload"`.

### Rule 13: Payload Signing and Encryption

**Signing (HMAC-SHA256)** — Production only. SDK computes `HMAC-SHA256(raw_body_bytes, api_secret)`, sends as `X-KP-Signature`. Server verifies with constant-time comparison before any processing.

**Encryption (AES-256-GCM)** — Production only. SDK encrypts the JSON string using a key derived from `api_secret` via HKDF. 12-byte random IV prepended to ciphertext. Server extracts IV, decrypts, then parses JSON.

**API secret management:**

```
tenantKey (public):  "tk_" + 24 chars. Identifies tenant. Safe in client source code.
apiSecret (private): "sk_" + 48 chars. Signs + encrypts payloads.
                     NEVER in client source code.
                     Injected at runtime by host app:
                       - Server-rendered page variable: window.__KP_SECRET__
                       - Or fetched from host app's config endpoint on page load
                     Used for: HMAC signing + AES encryption (production only).
```

### Rule 14: Tenant API Key Lifecycle

```
ROTATION:    Every 90 days (configurable per tenant).
             During 24-hour rotation window, server accepts BOTH old and new apiSecret.
REVOCATION:  POST /admin/v1/keys/revoke → immediate. All payloads signed with that
             version rejected with 403.
STORAGE:     apiSecret stored encrypted (AES-256-GCM with server master key from env var).
             Never plaintext in database. Master key rotation is a separate process.
ENDPOINTS:
  POST /admin/v1/keys/rotate  → generates new apiSecret, returns it ONCE in response
  POST /admin/v1/keys/revoke  → invalidate a specific key version immediately
  GET  /admin/v1/keys         → list active keys (secrets redacted, shows version + status)
```

### Rule 15: Page Unload and Error Recovery

**Page unload — flush buffers before page dies:**

```typescript
// visibilitychange fires when tab goes background OR before close
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'hidden') {
    this.flushBehavioralBatch();
    this.sendSessionEnd();
  }
});

// pagehide is the true last chance — use sendBeacon (fire-and-forget, survives close)
window.addEventListener('pagehide', () => {
  navigator.sendBeacon(
    `${this.endpoint}/v1/signals`,
    JSON.stringify({ v: 1, type: 'session_end', sid: this.sessionId, ts: Date.now() })
  );
});
```

**Error recovery — exponential backoff + in-memory queue:**

```
On fetch failure (5xx or network error):
  Retry 3 times with exponential backoff: 1s, 2s, 4s
  If all retries fail → queue payload in memory (max 5 payloads)
  On next SUCCESSFUL request → drain the failed queue in background
  
  NEVER retry 4xx errors (those are client bugs, not transient failures)
  NEVER block the host page on a failed request
```

### Rule 16: CSP Compatibility

Banks run strict Content Security Policies. The SDK must work within them.

```
REQUIRED CSP directives (document in integration guide):
  connect-src:  must allow your API endpoint (https://api.kprotect.io)
  worker-src:   must allow blob: (for CPU benchmark Web Worker)

FALLBACKS when CSP blocks features:
  blob: Workers blocked  → run CPU benchmarks on main thread (noisier but works)
  WebGL blocked          → skip GPU signals, report gpu_available: false
  fetch blocked          → SDK cannot function, log error and stop

ABSOLUTE RULE: NEVER let a CSP error crash the host page. Every browser API call
               is wrapped in try/catch. Failed signals are reported as unavailable.
ABSOLUTE RULE: SDK uses NO eval(), NO new Function(), NO inline event handlers.
```

### Rule 17: Backend Resilience

**Valkey failover — circuit breaker:**

```
If 3 consecutive Valkey failures within 10 seconds:
  → Open circuit for 30 seconds (skip all cache operations)
  → Fall back to PostgreSQL-only resolution (slower but functional)
  → Log error with structured logging
  → After 30 seconds, attempt one Valkey probe to close circuit
  → NEVER crash the request. NEVER return 5xx because cache is down.
```

**Baseline cold start — no fake drift scores:**

```
First N sessions (default: 3) for a new device:
  device_drift.overall_drift_score = null (not 0.0 — null means "unknown")
  drift_classification = "baseline_building"
  drift_reasons = ["building_baseline_2_of_3"]

After N sessions: compute baseline from stored signal history, start reporting real drift.
NEVER return overall_drift_score = 0.0 for a device with no history. That would mean
"perfectly matching baseline" which is a lie when there is no baseline.
```

**MaxMind GeoIP refresh:**

```
On app startup: check .mmdb file age. If >30 days → download fresh from MaxMind.
Weekly background job: same check + download.
Requires: MAXMIND_LICENSE_KEY env var.
Include geoip_db_date in /ready and /metrics responses so stale DBs are visible.
```

### Rule 18: Observability

```
HEALTH ENDPOINTS:
  GET /health  → liveness: {"status": "ok"}
  GET /ready   → readiness: checks PostgreSQL + Valkey + GeoIP DB
  GET /metrics → request_count, resolution_method_distribution, cache_hit_rate,
                 latency_p50/p95/p99, spoofing_flag_rate, active_sessions

STRUCTURED LOGGING (every request, via middleware):
  Fields: method, path, status, duration_ms, tenant_id, session_id,
          ip_country, resolution_method, cache_hit, spoofing_flagged
  Format: JSON (structlog)
  Ship to: SigNoz / Grafana Loki / CloudWatch (tenant configurable)
```

### Rule 19: SDK Version Compatibility

```
PAYLOAD VERSION: { v: 1, sdk: "1.2.3", ... }
SERVER SUPPORTS: current version + N-1. Accept unknown future versions best-effort.
BREAKING CHANGES (new v: 2): 6-month deprecation window for v: 1.
SDK VERSION CHECK: Optional GET /v1/config/sdk-version → { latest, minimum }
PYDANTIC MODELS: extra='ignore' — unknown fields silently dropped, never rejected.
RULE: NEVER refuse to collect or process signals due to version mismatch.
      Some data is always better than no data.
```

### Rule 20: Testing Strategy

```
UNIT TESTS (per signal collector):
  - Each collector must have tests verifying:
    - Returns expected shape when API available
    - Returns graceful fallback when API unavailable (e.g., Firefox has no deviceMemory)
    - Does not throw on any browser configuration
    - Cleans up resources (WebGL context, AudioContext, canvas elements)

INTEGRATION TESTS (collection pipeline):
  - Full collection completes within 500ms
  - Diff computation produces correct JSON Patch operations
  - Empty diff produces zero-byte payload
  - Behavioral batching respects 500ms/50-event thresholds

CROSS-BROWSER TESTS (Playwright, run in CI):
  - Same machine, Chrome vs Firefox vs Safari
  - Verify Tier 1 signals produce identical output
  - Verify Tier 2 signals produce similar (fuzzy-matchable) output
  - Verify Tier 3 signals correctly differ

SERVER TESTS (resolution pipeline):
  - Exact match: known device returns same ID
  - Fuzzy match: same device in different browser resolves correctly
  - New device: unknown signals create new entity
  - Anti-spoofing: inconsistent signals trigger appropriate flags
  - Audit trail: every decision produces valid hash-chained record

LOAD TESTS:
  - 10,000 concurrent sessions via locust or k6
  - Resolution latency remains <200ms p99
  - FastAPI + Uvicorn handles burst traffic without 5xx errors
  - Valkey cache hit rate > 70% for exact match path
```

---

## Development Workflow

1. **Start with `packages/shared-types/`**: Define all signal types, payload schemas, and decision types. This is the contract between SDK and server.

2. **Build `backend/` skeleton**: FastAPI app with Pydantic models matching shared-types. `POST /v1/signals` endpoint that accepts a payload and returns a stub response. Docker Compose with PostgreSQL + Valkey.

3. **Build `packages/sdk-web/` Tier 1 signals**: Synchronous, fast, always available. Get the collection → JSON → fetch POST pipeline working end-to-end with the FastAPI backend.

4. **Build `backend/services/signal_validator.py`**: Anti-spoofing consistency checks. Return spoofing flags in response.

5. **Build `backend/services/device_resolver.py` exact match**: Simple hash lookup in Valkey → PostgreSQL fallback. This handles 70% of sessions.

6. **Build `backend/services/network_intel.py`**: Extract source IP from request, run MaxMind GeoIP2 lookup (local .mmdb file, no external API calls), ASN lookup, VPN/proxy/Tor detection. This enriches every request with server-side signals.

7. **Add Tier 2 signals to Web SDK**: GPU render tasks, AudioContext, CPU benchmarks, fonts. Each in its own module with independent tests.

8. **Build `backend/services/fuzzy_matcher.py`**: Weighted similarity scoring with per-signal comparators. Test with same-device-different-browser scenarios.

9. **Add knowledge graph**: Apache AGE schema via migrations, `backend/services/graph_resolver.py` for graph-assisted resolution.

10. **Build `backend/services/risk_scorer.py`**: Deterministic rules engine. ML scoring comes later when training data exists.

11. **Build `backend/services/audit.py`**: Hash-chained audit trail. Write via FastAPI `BackgroundTasks` to avoid blocking the response.

12. **Build mobile SDKs**: Start with Android (larger market share in India for banking), then iOS. These are simpler than web — direct hardware access. They POST to the same FastAPI endpoints.

13. **Add anti-spoofing**: Full consistency matrix, automation detection, entropy analysis.

**Local dev setup:**

```bash
# Start infrastructure
cd backend
docker compose up -d  # PostgreSQL + Valkey + (optional) MaxMind GeoIP

# Run backend
uvicorn app.main:app --reload --ho# CLAUDE.md — K-Protect Behavioral Biometrics SDK

> **This is the single source of truth.** Read it completely before starting any task. Every architectural decision, data model, algorithm, and coding rule is here.

---

## 1. Project Identity

**Project**: K-Protect Behavioral Biometrics SDK (`kp-biometrics`)
**Purpose**: End-to-end behavioral biometrics system for continuous authentication and active identity verification. Detects when the person using a device is NOT the enrolled user — even with correct credentials, same device, same network.

**Two Core Products in One SDK**:

1. **Passive Continuous Auth** — Silent background monitoring that produces a **Behavioral Drift Score** (0.0–1.0) measuring how far current behavior deviates from the enrolled user's baseline.
2. **KP-Challenge (Behavioral TOTP)** — Active challenge-response 2FA where the user types a dynamically generated phrase and identity is verified by HOW they type it, replacing SMS/email OTP entirely.

**Target Customers**: Regulated financial institutions, fintech platforms, enterprise identity providers.

---

## 2. System Architecture

```
┌────────────────────────────────────────────────────────────────┐
│  CLIENT SDK (TypeScript — zero runtime dependencies)           │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Collectors                                             │    │
│  │ ├─ KeystrokeCollector  → 10-zone keyboard mapping      │    │
│  │ ├─ PointerCollector    → mouse/trackpad aggregation    │    │
│  │ ├─ TouchCollector      → mobile touch patterns         │    │
│  │ ├─ SensorCollector     → gyro/accel/orientation        │    │
│  │ ├─ CredentialCollector → login field behavioral pwd    │    │
│  │ └─ ChallengeCollector  → KP-Challenge phrase capture   │    │
│  └────────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Feature Extractors (PURE functions — no side effects)  │    │
│  │ Raw events → aggregated feature vectors per window     │    │
│  │ Raw events DISCARDED after extraction                  │    │
│  └────────────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Transport                                              │    │
│  │ Batched HTTPS POST (gzip) every 5-10s                  │    │
│  │ Credential/Challenge features sent IMMEDIATELY         │    │
│  └────────────────────────────────────────────────────────┘    │
└────────────────────────┬───────────────────────────────────────┘
                         │
                         ▼
┌────────────────────────────────────────────────────────────────┐
│  SERVER (Python — FastAPI + PyTorch)                            │
│                                                                │
│  ┌─────────────────┐  ┌───────────────────┐  ┌─────────────┐  │
│  │ Ingestion API    │  │ Challenge API     │  │ Profile API  │  │
│  │ POST /ingest     │  │ POST /challenge   │  │ GET/PUT      │  │
│  │ Receives batches │  │ POST /verify      │  │ /profile     │  │
│  └────────┬────────┘  └────────┬──────────┘  └──────┬──────┘  │
│           │                    │                     │         │
│           ▼                    ▼                     ▼         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Global Encoder (TCN + Multi-Head Attention)             │   │
│  │ ONE model for ALL users. Per-modality heads.            │   │
│  │ keystroke→64d, pointer→32d, touch→32d, sensor→32d      │   │
│  └─────────────────────────┬───────────────────────────────┘   │
│                            │                                   │
│  ┌─────────────────────────▼───────────────────────────────┐   │
│  │ Drift Scorer                                            │   │
│  │ cosine_distance → z_score → sigmoid → drift (0.0-1.0)  │   │
│  │ Per-modality + adaptive weighted fusion                 │   │
│  │ Session trend: slope, acceleration, CUSUM changepoint   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌──────────────┐  ┌───────────────┐  ┌────────────────────┐  │
│  │ Profile Store │  │ Challenge     │  │ Audit Log          │  │
│  │ Valkey +      │  │ Store         │  │ Postgres           │  │
│  │ pgvector      │  │ Valkey (TTL)  │  │ append-only        │  │
│  └──────────────┘  └───────────────┘  └────────────────────┘  │
│                                                                │
│  Outputs:                                                      │
│  ├─ DriftScoreResponse (per batch, synchronous)                │
│  ├─ ChallengeVerification (per challenge, synchronous)         │
│  ├─ DriftAlerts (webhook, asynchronous)                        │
│  └─ SessionAuditRecord (append-only log)                       │
└────────────────────────────────────────────────────────────────┘
```

---

## 3. Keyboard Zone Map

10 zones based on standard touch-typing finger assignments. Each zone maps to one finger. This preserves behavioral signal while making text reconstruction computationally infeasible (4-8 keys per zone).

```
Zone 1 (L-pinky):   ` 1 Q A Z Tab CapsLock ShiftLeft
Zone 2 (L-ring):    2 W S X
Zone 3 (L-middle):  3 E D C
Zone 4 (L-index):   4 5 R T F G V B
Zone 5 (R-index):   6 7 Y U H J N M
Zone 6 (R-middle):  8 I K ,
Zone 7 (R-ring):    9 O L .
Zone 8 (R-pinky):   0 - = P [ ] \ ; ' Enter / ShiftRight Backspace
Zone 9 (Thumbs):    Space ControlLeft ControlRight AltLeft AltRight MetaLeft MetaRight
Zone 10 (Special):  Arrows, F1-F12, Numpad, Insert/Delete/Home/End/PageUp/PageDown
```

Zone mapper uses `event.code` (physical key position) for mapping, NEVER `event.key` (character). After mapping, `event.code` is immediately discarded. Only zone ID (1-10) retained.

---

## 4. Feature Extraction Specifications

### 4.1 Keystroke Features (per 5-second window)

| Feature | Shape | Description |
|---------|-------|-------------|
| `zone_transition_matrix` | `number[100]` | 10x10 flattened row-major. Cell `[i*10+j]` = mean flight time (ms) from zone `i` keyup to zone `j` keydown. `-1` for unobserved pairs. |
| `zone_transition_counts` | `number[100]` | Count of transitions per zone pair. |
| `zone_transition_stdevs` | `number[100]` | Stdev of flight times per pair. `-1` if < 2 samples. |
| `zone_dwell_means` | `number[10]` | Mean key hold duration per zone (ms). |
| `zone_dwell_stdevs` | `number[10]` | Stdev of key hold duration per zone. |
| `zone_hit_counts` | `number[10]` | Keystroke count per zone. |
| `rhythm.kps_mean` | `number` | Keystrokes per second — mean. |
| `rhythm.kps_stdev` | `number` | KPS variability. |
| `rhythm.burst_count` | `number` | Typing bursts separated by >500ms pause. |
| `rhythm.burst_length_mean/stdev` | `number` | Keys per burst statistics. |
| `rhythm.pause_count` | `number` | Pauses >1000ms. |
| `rhythm.inter_burst_gap_mean/stdev` | `number` | Duration between bursts. |
| `error_proxy.backspace_rate` | `number` | Correction keystrokes / total keystrokes (0-1). |
| `error_proxy.rapid_same_zone_count` | `number` | Same zone hit <50ms apart. |
| `error_proxy.correction_sequences` | `number` | Type→backspace→retype patterns. |
| `modifier_behavior.shift_hold_mean_ms` | `number` | Mean Shift hold duration. |
| `modifier_behavior.modifier_before_key` | `number` | Fraction where modifier pressed before the key. |
| `bigram_velocity_histogram` | `number[10]` | Flight time distribution: [0-25, 25-50, 50-75, 75-100, 100-150, 150-200, 200-300, 300-500, 500-1000, 1000+ms]. |

**Note on error detection**: Raw event stores `is_correction: boolean` flag (true for Backspace/Delete). Doesn't leak content, enables correction tracking.

### 4.2 Pointer Features (per 10-second window)

| Feature Group | Key Features |
|--------------|-------------|
| **Movement** | total_distance, displacement, path_efficiency, velocity mean/max/stdev/p25/p75, acceleration mean/stdev, direction_changes (>30°), curvature mean/stdev, angle_histogram (8 compass bins) |
| **Segments** | Continuous motions separated by >100ms pause. Count, duration/distance mean/stdev, efficiency mean. |
| **Clicks** | Count, hold_mean_ms, hold_stdev, double_click count+interval, approach_velocity_profile (5 bins: velocity at 500/400/300/200/100ms before click — Fitts's Law signature), overshoot_rate, overshoot_distance |
| **Scroll** | Event count, total_distance, velocity mean/stdev, direction_changes, burst count/size |
| **Idle** | Periods >2s without movement. Count, duration mean, micro_movement_amplitude, micro_movement_frequency (involuntary hand tremor — very discriminative) |

### 4.3 Touch Features (per 5-second window)

| Feature Group | Key Features |
|--------------|-------------|
| **Taps** | count, duration mean/stdev, force mean/stdev (-1 if unavailable), radius mean/stdev, inter_tap mean/stdev |
| **Swipes** | count, velocity mean/stdev, length mean/stdev, curvature, duration, angle_histogram (8 bins) |
| **Pinch** | count, speed_mean, spread_mean |
| **Spatial** | heatmap_zones (3x4=12 grid, tap distribution — captures thumb-reach patterns), touch_centroid x/y |

### 4.4 Sensor Features (per 2-second window)

| Feature Group | Key Features |
|--------------|-------------|
| **Accelerometer** | mean/stdev per axis [x,y,z], magnitude mean/stdev, peak_count (>2σ spikes), energy |
| **Gyroscope** | mean/stdev per axis, magnitude mean/stdev, zero_crossing_rate (hand steadiness) |
| **Orientation** | mean/stdev/range per axis [α,β,γ] |
| **Grasp Signature** | tilt_during_interaction, stability_score, interaction_accel_correlation, dominant_hold_axis |

### 4.5 Credential Field Features (per field, sent immediately on blur)

| Feature | Description |
|---------|-------------|
| `field_type` | username, email, password, pin, otp, other |
| `char_count` | Character count (NOT characters) |
| `total_duration_ms` | First keydown to last keyup |
| `zone_sequence` | **BEHAVIORAL PASSWORD** — ordered `[{from_zone, to_zone, flight_ms, dwell_ms}]` |
| `corrections` | Count, positions, correction_speed |
| `hesitation_points` | Indices where pause >300ms |
| `timing_summary` | flight/dwell mean/stdev/min/max, speed_trend |
| `field_entry_context` | time_since_page_load, autofill_detected, paste_detected, focus_method |

---

## 5. Drift Score System

### 5.1 What Is Drift?

Drift = continuous behavioral distance from baseline (0.0-1.0):

- **0.0–0.2**: Matches baseline closely
- **0.2–0.4**: Mild elevation — fatigue, new keyboard, stress
- **0.4–0.6**: Significant deviation — warrants monitoring
- **0.6–0.8**: Anomalous — likely different person
- **0.8–1.0**: Critical — fundamentally different behavior

Drift is **decomposable** (per-modality), **temporal** (session trend + changepoint), and **context-aware** (matches against appropriate centroid).

### 5.2 Drift Computation

```
STEP 1: ENCODE — feature window → modality encoder head → embedding (L2-normalized)
  keystroke→64d, pointer→32d, touch→32d, sensor→32d
  (V1: raw feature vector normalized. V2: learned TCN embeddings.)

STEP 2: SELECT CENTROID — match session context to nearest centroid

STEP 3: PER-MODALITY DISTANCE
  raw_dist  = cosine_distance(vec, centroid.vec)
  z_score   = (raw_dist - centroid.intra_distance.mean) / centroid.intra_distance.stdev
  drift     = sigmoid(z_score - 1.0)
  Mapping: z<1→~0.0, z=2→~0.27, z=3→~0.73, z>4→~1.0

STEP 4: ADAPTIVE FUSION
  Base: w_k=0.40, w_p=0.25, w_t=0.20, w_s=0.15
  Missing modality → redistribute. Low event count → reduce weight. Normalize to 1.0.

STEP 5: FUSE — drift_overall = Σ(w_m × drift_m)

STEP 6: CONFIDENCE = min(signal_richness, data_volume_factor, profile_maturity)

STEP 7: CREDENTIAL DRIFT (if credential fields in batch)
  timing_corr  = pearson(observed_flights, enrolled_flights)
  dwell_corr   = pearson(observed_dwells, enrolled_dwells)
  hesit_overlap = jaccard(observed_hesitations, enrolled_hesitations)
  cred_drift   = 0.4×(1-timing_corr) + 0.3×(1-dwell_corr) + 0.2×(1-hesit_overlap) + 0.1×speed_dev

STEP 8: SESSION TREND
  slope (OLS last 10 batches), acceleration, CUSUM changepoint
  target_mean = mean(first 5 batches), h = 4×stdev(first 5)
  CUSUM > h → changepoint_detected (session takeover signal)

STEP 9: ALERTS — compare against DriftThresholdConfig, fire if crossed AND confidence > min
```

### 5.3 Default Thresholds (Customer-Configurable)

| Level | Overall Drift | Credential Drift | Action |
|-------|--------------|-------------------|--------|
| Monitor | > 0.30 | > 0.25 | Enhanced logging |
| Warn | > 0.50 | > 0.40 | Webhook alert |
| Challenge | > 0.65 | > 0.55 | Trigger KP-Challenge / step-up |
| Block | > 0.85 | > 0.75 | Session termination |

---

## 6. KP-Challenge (Behavioral TOTP)

### 6.1 Concept

Replaces SMS/email OTP with behavioral verification. User types a dynamically generated phrase. Identity verified by HOW they type — the timing pattern of zone transitions.

```
Traditional TOTP:  Server → 6-digit code → user types code → server checks code
TypingDNA Verify:  Server → 4 fixed words → user types → server checks HOW
KP-Challenge:      Server → PERSONALIZED phrase targeting user's most discriminative
                   zone pairs → user types → server verifies BOTH text AND behavior
```

### 6.2 Advantages Over TypingDNA Verify

- **Personalized phrases** targeting user's tightest behavioral signatures (not generic words)
- **Zero extra enrollment** — already enrolled from passive collection
- **Never reuses challenges** — single-use, anti-replay by design
- **Multi-modal** — captures keystroke + pointer + touch + sensor during challenge
- **Integrated with continuous drift** — challenge triggered automatically when drift exceeds threshold

### 6.3 Challenge Flow

```
PHASE 1: GENERATE (Server)
  1. Load user's zone_transition_matrix
  2. Rank zone pairs: discriminative_score = count / stdev
  3. Take top 20 "target_pairs"
  4. Select 4-6 words from dictionary covering max target pairs
  5. Optimize word order for inter-word transitions (space = zone 9)
  6. Store in Valkey with TTL: { challenge_id, phrase, phrase_hash,
     expected_zone_sequence, discriminative_pairs, pair_weights, used: false }
  7. Return to client: { challenge_id, phrase, char_count, expires_at }
     (zone sequences + pair weights are SERVER-ONLY, never sent to client)

PHASE 2: CAPTURE (Client SDK)
  1. Customer app displays phrase in input field
  2. ChallengeCollector captures CredentialFieldFeatures (zone sequence + timing)
  3. Also captures pointer/touch/sensor windows during typing (if available)
  4. Sends ChallengeSubmission immediately on completion

PHASE 3: VERIFY (Server)
  Layer 1 — VALIDITY: challenge exists, not expired, not used, text hash matches
  Layer 2 — ANTI-BOT: reaction time 200ms-10s, typing >10ms/key, nonzero variance
  Layer 3 — BEHAVIORAL: for each discriminative pair in challenge:
    pair_z = abs(observed_flight - enrolled_mean) / enrolled_stdev
    (weighted by pair_weight — tighter stdev pairs count more)
    challenge_drift = sigmoid(weighted_mean(pair_z_scores) - 1.0)
  Layer 4 — MULTI-MODAL BOOST: if other modalities captured, fuse with keystroke drift
  
  Output: { verified, challenge_drift, confidence, text_correct, anti_replay, factors[] }
```

### 6.4 Phrase Generation Algorithm

```python
def generate_challenge(user_profile, locale='en', difficulty='standard'):
    matrix = user_profile.zone_transition_matrix
    
    # Rank zone pairs by discriminative power
    scored_pairs = []
    for i in range(10):
        for j in range(10):
            if matrix[i][j].count >= 5:
                scored_pairs.append((i, j, matrix[i][j].count / max(matrix[i][j].stdev, 1.0)))
    scored_pairs.sort(key=lambda x: -x[2])
    target_pairs = set((p[0], p[1]) for p in scored_pairs[:20])
    
    # Greedy word selection covering max target pairs
    max_words = 6 if difficulty == 'high' else 4
    uncovered = set(target_pairs)
    selected = []
    while uncovered and len(selected) < max_words:
        best = max(dictionary, key=lambda w: len(set(w.zone_pairs) & uncovered))
        selected.append(best)
        uncovered -= set(best.zone_pairs)
    
    # Optimize word order for inter-word space transitions
    phrase = optimize_and_join(selected, target_pairs)
    
    # Validate: 30-50 chars, ≥12 target pairs covered, not recently used
    return Challenge(phrase=phrase, ...)
```

### 6.5 Challenge Dictionary

Pre-computed per locale. Each entry:
```json
{ "word": "bright", "zone_seq": [4,4,6,3,5,4], "zone_pairs": [[4,4],[4,6],[6,3],[3,5],[5,4]], "length": 6 }
```
Constraints: frequency rank <10000, 4-10 chars, no offensive words, ~3000-5000 words per locale. V1: English only.

### 6.6 Integration: Passive + Active

```
Drift crosses 0.65 → webhook: step_up_recommended → customer triggers KP-Challenge
  → User types phrase → challenge_drift 0.15 → PASS → session continues
  → OR challenge_drift 0.72 → FAIL → escalate to SMS / block

Login 2FA: credentials typed (passive drift scored) → KP-Challenge displayed
  → User types phrase → challenge_drift 0.08 → login granted, no phone needed

Transaction verify: $50K wire → KP-Challenge → verified → approved
```

---

## 7. User Profile Model

```
UserBehavioralProfile {
  user_hash, tenant_id, status: enrolling|active|frozen|expired,
  
  centroids: [max 7] {
    centroid_id, embedding[128] (L2-norm), weight (sum=1.0),
    context: { platform, input_method, time_of_day },
    intra_distance: { mean, stdev, p95, p99 },
    session_count
  },
  
  credential_profiles: [{
    field_type, char_count, embedding[64],
    zone_sequence_template: [{ from_zone, to_zone, flight_mean/stdev, dwell_mean/stdev }],
    hesitation_pattern: number[],
    timing_stats, intra_distance, session_count
  }],
  
  zone_transition_matrix: { cells[100]: { zone_from, zone_to, flight_mean, flight_stdev, count } },
  
  stats: { total_sessions, profile_maturity(0-1), last_genuine_session, encoder_version }
}
```

**Update rules**: EMA α=0.1 on genuine sessions only (drift<0.3). New centroid if new context. Max 7 — merge two most similar if at limit. Credential profile updated separately; new profile on char_count change.

---

## 8. Wire Types Quick Reference

```typescript
// SDK → Server (every 5-10s)
BehavioralBatch { header, context, signals, keystroke_windows[], pointer_windows[],
                  touch_windows[], sensor_windows[], credential_fields[] }

// Server → SDK (synchronous)
DriftScoreResponse { drift: { overall, confidence, modalities, fusion_weights },
                     session: { drift_current/mean/max, drift_trend, timeline, stability_score },
                     credential_drift?, profile_state, alerts[] }

// Challenge generate: ChallengeRequest → Challenge { challenge_id, phrase, expires_at }
// Challenge verify: ChallengeSubmission → ChallengeVerification { verified, challenge_drift, anti_replay }

// Webhook: WebhookEvent { event_type, session_id, payload, signature(HMAC-SHA256) }
```

---

## 9. API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/behavioral/ingest` | Receive BehavioralBatch → DriftScoreResponse |
| GET | `/v1/drift/{session_id}` | Current session drift state |
| GET | `/v1/drift/history/{user_hash}` | Historical drift trends |
| GET | `/v1/profile/{user_hash}` | User behavioral profile |
| PUT | `/v1/profile/{user_hash}/freeze` | Admin freeze |
| PUT | `/v1/config/thresholds` | Set drift thresholds |
| POST | `/v1/challenge/generate` | Generate KP-Challenge |
| POST | `/v1/challenge/verify` | Verify KP-Challenge |

---

## 10. Directory Structure

```
kp-biometrics/
├── CLAUDE.md
├── package.json / pnpm-workspace.yaml / turbo.json
├── packages/
│   ├── sdk-web/
│   │   └── src/
│   │       ├── index.ts                   # Public API
│   │       ├── collectors/
│   │       │   ├── base-collector.ts
│   │       │   ├── keystroke.ts
│   │       │   ├── pointer.ts
│   │       │   ├── touch.ts
│   │       │   ├── sensor.ts
│   │       │   ├── credential.ts
│   │       │   └── challenge.ts           # KP-Challenge capture
│   │       ├── zones/
│   │       │   ├── zone-mapper.ts
│   │       │   └── qwerty.ts / azerty.ts / qwertz.ts
│   │       ├── features/
│   │       │   ├── keystroke-features.ts
│   │       │   ├── pointer-features.ts
│   │       │   ├── touch-features.ts
│   │       │   ├── sensor-features.ts
│   │       │   └── credential-features.ts
│   │       ├── challenge/
│   │       │   ├── challenge-client.ts    # API: generate + verify
│   │       │   └── challenge-ui.ts        # Optional minimal UI
│   │       ├── transport/
│   │       │   ├── batch-assembler.ts
│   │       │   └── sender.ts
│   │       └── utils/
│   │           ├── ring-buffer.ts
│   │           ├── sliding-window.ts
│   │           ├── stats.ts
│   │           ├── timer.ts
│   │           └── privacy.ts
│   ├── sdk-react-native/
│   ├── shared-types/                      # Wire contract types
│   └── server/
│       └── src/
│           ├── api/
│           │   ├── ingest.py / drift.py / history.py / profile.py
│           │   └── challenge.py
│           ├── encoder/
│           │   ├── model.py               # TCN + Attention
│           │   ├── keystroke_head.py / pointer_head.py / touch_head.py / sensor_head.py
│           │   └── credential_encoder.py
│           ├── scoring/
│           │   ├── drift_scorer.py / fusion.py / session_tracker.py
│           │   ├── credential_scorer.py / challenge_scorer.py
│           │   └── alerting.py
│           ├── challenge/
│           │   ├── generator.py / dictionary.py / word_analyzer.py
│           │   ├── anti_replay.py / store.py
│           │   └── ../../data/dictionaries/en.json
│           ├── profile/
│           │   ├── store.py / centroid_manager.py / enrollment.py
│           │   └── credential_profile.py
│           └── audit/ session_log.py / webhook.py
├── schemas/ *.v1.json
├── docs/
└── tools/ simulate-session.ts / replay-session.ts / build-dictionary.py
```

---

## 11. Tech Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| SDK (Web) | TypeScript, Rollup | Tree-shakeable, zero runtime deps |
| SDK (Mobile) | React Native + native modules | Shared TS core + native sensors |
| Server | Python, FastAPI, PyTorch | ML ecosystem, async, fast prototyping |
| Encoder | PyTorch (TCN + Multi-Head Attention) | Best for temporal sequence modeling |
| Profile Store | Valkey + PostgreSQL (pgvector) | Valkey <1ms hot lookups, pgvector for embeddings |
| Challenge Store | Valkey with TTL | Ephemeral, auto-evict expired challenges |
| Audit | PostgreSQL (append-only, time-partitioned) | Compliance for regulated FIs |
| Queue | NATS JetStream | Webhook delivery (V2) |
| Monorepo | Turborepo + pnpm | Cross-language TS+Python |

---

## 12. SDK Public API

```typescript
const kp = KProtect.init({
  api_key: 'kp_live_abc...',
  session_id: crypto.randomUUID(),
  user_hash: await sha256(userId),
  environment: 'production',
  collectors: {
    keystroke: { enabled: true, zone_map: 'qwerty_10zone', window_ms: 5000 },
    pointer:   { enabled: true, window_ms: 10000, sample_rate_hz: 30 },
    touch:     { enabled: true },
    sensor:    { enabled: true, permission_strategy: 'prompt_on_interaction' }
  },
  transport: { batch_interval_ms: 5000, compression: 'gzip' }
});

// PASSIVE
kp.start();
kp.on('drift', (score) => { if (score.drift.overall > 0.65) triggerStepUp(); });
kp.on('credential_drift', (d) => { if (d.drift > 0.55) blockLogin(); });
kp.on('alert', (a) => { if (a.alert_type === 'session_takeover_suspected') lockSession(); });

// ACTIVE (KP-Challenge)
const challenge = await kp.challenge.generate({ purpose: 'login_2fa' });
// Display challenge.phrase to user in an input field
const result = await kp.challenge.verify(challenge.challenge_id, inputElement);
// result.verified, result.challenge_drift, result.confidence

// LIFECYCLE
kp.stop(); kp.destroy();
kp.getLatestDrift(); kp.getSessionState();
```

---

## 13. Critical Rules

### Privacy (NON-NEGOTIABLE)
1. NEVER capture/store/transmit actual keystroke content. Only zone IDs (1-10).
2. NEVER capture text input values. No form content, passwords, usernames.
3. Raw events DISCARDED after feature extraction. Only aggregates leave device.
4. Pointer coords viewport-normalized then discarded. Only statistical aggregates shipped.
5. User ID by `user_hash` (SHA-256) only. SDK never sees raw identifiers.
6. Sensor permissions: `prompt_on_interaction` default. Never auto-request.
7. All features derived from HOW user interacts, never WHAT they typed.
8. KP-Challenge: phrase displayed to user (not sensitive — random words). Typed text verified by SHA-256 hash only — server never receives raw typed string.

### Data Model
9. Wire types: BehavioralBatch, DriftScoreResponse, ChallengeSubmission, ChallengeVerification.
10. Session-relative timestamps everywhere. Wall clock only in batch header.
11. Zone transition matrix: always 100 values (10×10 row-major). `-1` for unobserved.
12. Credential zone sequences are ORDERED arrays. Order matters.
13. All embeddings L2-normalized. Cosine distance = 1 - dot_product.
14. Drift: always 0.0–1.0. `sigmoid(z_score - 1.0)`.

### Architecture
15. One global encoder model. Per-user state = embeddings, not model weights.
16. Max 7 centroids per user. Weights sum to 1.0.
17. Credential profiles SEPARATE from general centroids. 64d vs 128d.
18. Adaptive fusion weights. Missing modality → redistribute.
19. CUSUM changepoint for session takeover detection.
20. EMA α=0.1 on genuine sessions only (drift<0.3).
21. Challenge phrases single-use. Mark used before scoring.
22. Challenge store uses Valkey TTL. Auto-evict.
23. Challenge generation per-user-personalized. Targets most discriminative pairs.
24. NEVER send discriminative_pairs or expected_zone_sequence to client.

### Coding
25. TDD-first. Test before implementation. Every file has tests.
26. Zero runtime dependencies in sdk-web.
27. Tree-shakeable. Named exports only.
28. Strict typing. No `any` (TS), no bare `dict` (Python).
29. Feature extraction = PURE functions.
30. `performance.now()` for all timing. NOT `Date.now()`.

### Testing
31. Synthetic data generators per modality.
32. Deterministic tests. Seeded randomness only.
33. Drift: same-person < 0.3, different-person > 0.6.
34. Challenge: same-person verified, different-person rejected, expired rejected, replay rejected.

---

## 14. Build Phases

### Phase 1 — SDK Core + Statistical Drift + Credential (Weeks 1-4)
sdk-web collectors (keystroke, pointer, credential), features, transport. Server ingest, profile store, V1 statistical drift scorer, credential scorer. Zone mapper. Full test coverage.

### Phase 2 — ML Encoder + KP-Challenge (Weeks 5-8)
TCN+Attention encoder, multi-centroid profiles, full drift pipeline. Challenge generator, dictionary, anti-replay, challenge scorer. ChallengeCollector in SDK.

### Phase 3 — Touch + Sensor + Mobile (Weeks 9-12)
TouchCollector, SensorCollector, React Native SDK. 4-modality fusion. CUSUM changepoint.

### Phase 4 — Production Hardening (Weeks 13-16)
Webhooks, audit, historical drift API. Rate limiting, tenant isolation. <50ms p99 scoring. <15KB SDK bundle. Security audit.

### Current: Phase 1
Build bottom-up: ring-buffer → stats → sliding-window → zone-mapper → keystroke collector → keystroke features → pointer collector → pointer features → credential collector → credential features → batch assembler → sender → public API → server ingest → profile store → drift scorer → credential scorer → integration test.

---

## 15. Test Scenarios

| # | Scenario | Expected |
|---|----------|----------|
| 1 | Same person, same device | drift < 0.3, confidence > 0.6 |
| 2 | Different person, same device, correct creds | credential_drift > 0.5, overall > 0.6 in 30s |
| 3 | Same person, different device | drift 0.2-0.5 initially, new centroid created |
| 4 | Mid-session takeover | changepoint_detected, drift spike |
| 5 | Autofill/paste login | autofill_detected, confidence ≈ 0 |
| 6 | New user enrollment | drift = -1, status = enrolling |
| 7 | Fatigued same person | drift 0.2-0.4, factors explain slowdown |
| 8 | KP-Challenge same person | challenge_drift < 0.25, verified |
| 9 | KP-Challenge different person | challenge_drift > 0.5, not verified |
| 10 | KP-Challenge expired | challenge_valid = false |
| 11 | KP-Challenge bot/replay | human_detected = false |
| 12 | KP-Challenge paste attempt | paste_detected, not verified |

---

## 16. Pitfalls

1. Don't use `event.key`/`event.code` in server payloads — zone IDs only
2. Don't use `Date.now()` — use `performance.now()`
3. Don't send empty feature windows
4. Don't compute drift during enrollment — return -1
5. Don't update profiles from high-drift sessions
6. Don't hardcode fusion weights
7. Don't manipulate DOM in SDK (except optional challenge UI)
8. Don't bundle test utilities into production
9. Don't store raw pointer coordinates
10. Don't mix credential/general drift (different embedding spaces)
11. Don't reuse challenge phrases — single-use enforced
12. Don't send discriminative_pairs to client — server-only
13. Don't accept expired challenges
14. Don't generate challenges with <12 target pairs covered

---

## 17. Environment Variables

```bash
KP_SDK_VERSION=1.0.0
KP_DATABASE_URL=postgresql://kprotect:secret@localhost:5432/kprotect
KP_VALKEY_URL=redis://localhost:6379
KP_JWT_SECRET=<random-32-bytes>
KP_CORS_ORIGINS=["https://*.customer.com"]
KP_LOG_LEVEL=info
KP_ENCODER_MODEL_PATH=./models/encoder_v1.pt
KP_MAX_BATCH_SIZE_KB=50
KP_SCORING_TIMEOUT_MS=100
KP_WEBHOOK_TIMEOUT_MS=5000
KP_CHALLENGE_DEFAULT_TTL=60
KP_CHALLENGE_MAX_TTL=300
KP_DICTIONARY_PATH=./data/dictionaries/en.json
```st 0.0.0.0 --port 8000

# Build and test web SDK
cd packages/sdk-web
pnpm install
pnpm test
pnpm build  # outputs dist/kprotect.min.js

# Test end-to-end: open test HTML page that loads SDK, check backend logs
```

---

## Key Reminders

- The Web SDK CANNOT read exact hardware specs. Do not waste time trying. Use indirect signals.
- Cross-browser device identity is a SERVER problem, not a client problem. The SDK collects signals; the server resolves identity via fuzzy matching + graph context.
- `navigator.deviceMemory` is Chrome-only, rounded to powers of 2, capped at 8. Firefox and Safari return undefined. Do not depend on it.
- `navigator.geolocation` requires a permission popup. NEVER use it in the SDK. Use IP geolocation server-side.
- GPU render tasks produce the highest-entropy cross-browser signal. Invest heavily here.
- AudioContext peak frequency analysis (binned) is the second-best cross-browser signal. Full audio hashes are NOT cross-browser stable.
- CPU benchmark RATIOS are cross-browser stable. Absolute timings are NOT (different JS engines).
- Every design decision must account for: Will this work when the user opens a different browser? Will this work after a device reset? Will this survive an anti-detect browser?
- Bandwidth matters. Full-on-first-load, diff-after. If nothing changed, send nothing.
- Every resolution decision must be auditable with a hash-chained audit trail. Banks require this.