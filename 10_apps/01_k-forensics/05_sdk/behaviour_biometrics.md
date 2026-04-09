# CLAUDE.md — K-Protect Behavioral Biometrics SDK

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
```