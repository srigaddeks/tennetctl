/**
 * wire-protocol.ts — complete type backbone for the K-Protect Web SDK.
 *
 * Contains:
 *   1. Public config types (KProtectConfig, KProtectOverrides, sub-overrides)
 *   2. Internal resolved config (ResolvedConfig) — what the worker works with
 *   3. Main↔Worker postMessage discriminated unions
 *   4. All behavioral signal types (KeystrokeSignal, PointerSignal, …)
 *   5. All server wire types (BehavioralBatch, CriticalActionBatch, …)
 *   6. Server response types (DriftScoreResponse, SessionMetadataResponse, …)
 *   7. Supporting domain types (UsernameSelector, CriticalAction, SessionState, …)
 *
 * Rules (SDK_BEST_PRACTICES §1.4, §3.1):
 *   • No `any` types.
 *   • No runtime imports — this file is types-only (no side effects).
 *   • Used by BOTH main-thread tsconfig.json AND tsconfig.worker.json.
 */

// ═══════════════════════════════════════════════════════════════════════════
// §A  Domain primitives
// ═══════════════════════════════════════════════════════════════════════════

/** Opaque UUID string. Validated at runtime by the transport layer. */
export type UUID = string;

/** Unix timestamp in milliseconds (Date.now() / performance.now() base). */
export type EpochMs = number;

/** SHA-256 hex digest of the raw username. Never the plaintext. */
export type UserHash = string;

/** Monotonically increasing counter, reset per session. */
export type PulseCounter = number;

// ═══════════════════════════════════════════════════════════════════════════
// §B  Username / identity capture config
// ═══════════════════════════════════════════════════════════════════════════

/**
 * A CSS selector + optional URL pattern that the DomScanner watches for
 * username values. Hash captured on the main thread — plaintext never crosses
 * to the worker (SDK_BEST_PRACTICES §5.2).
 */
export interface UsernameSelector {
  /** CSS selector targeting the username input element. */
  selector: string;
  /**
   * Optional URL substring/path to scope the selector.
   * DomScanner only installs this listener when the current path includes
   * this string. Omit to match all pages.
   */
  url?: string;
  /** DOM event that triggers username capture. Default: 'blur'. */
  event?: 'blur' | 'change' | 'submit';
}

/** Config block for identity capture (username selectors + SSO polling). */
export interface UsernameCaptureConfig {
  selectors?: UsernameSelector[];
  /**
   * Window globals to poll on init and on each route change for an
   * SSO-provided username value. E.g. ['window.__KP_USER__'].
   */
  sso_globals?: string[];
}

// ═══════════════════════════════════════════════════════════════════════════
// §C  Critical-action config
// ═══════════════════════════════════════════════════════════════════════════

/** A commit trigger — the DOM element(s) the user clicks to confirm an action. */
export interface CommitTrigger {
  /** CSS selector for the commit element(s). Comma-separated for multi-select. */
  selector: string;
}

/**
 * A single critical-action definition. The PageGate uses `page` to classify
 * the current URL, and `commit` to detect the user's confirmation click.
 */
export interface CriticalAction {
  /** RegExp matched against the current URL path. */
  page: RegExp;
  /** Stable action name sent in CriticalActionBatch.page_context.critical_action. */
  action: string;
  /** The DOM element that constitutes a "commit" for this action. */
  commit: CommitTrigger;
}

// ═══════════════════════════════════════════════════════════════════════════
// §D  Public KProtectConfig + KProtectOverrides
// ═══════════════════════════════════════════════════════════════════════════

/** Transport mode for batch delivery. */
export type TransportMode = 'direct' | 'proxy';

/** Transport-layer overrides. */
export interface TransportOverrides {
  /** 'direct' = POST directly to api.kprotect.io (default). 'proxy' = POST to custom endpoint. */
  mode?: TransportMode;
  /** Custom ingest endpoint (required when mode = 'proxy'). */
  endpoint?: string;
}

/** Session-lifecycle overrides. */
export interface SessionOverrides {
  /** Behavioural-signal pulse interval in ms. Default: 5000. */
  pulse_interval_ms?: number;
  /** Idle timeout in ms. Default: 15 * 60 * 1000. */
  idle_timeout_ms?: number;
  /** Keepalive pulse interval on critical-action pages in ms. Default: 30000. */
  keepalive_interval_ms?: number;
}

/** Identity / username-capture overrides. */
export interface IdentityOverrides {
  username?: UsernameCaptureConfig;
}

/** Page-gate overrides — opt out URLs from collection. */
export interface PageGateOverrides {
  /**
   * URL patterns (string substring or RegExp) where the SDK should NOT collect.
   * Matched against `location.pathname`.
   */
  opt_out_patterns?: Array<string | RegExp>;
}

/** Critical-actions override — replace the default set entirely. */
export interface CriticalActionsOverrides {
  actions?: CriticalAction[];
}

/**
 * Full override block (SDK_BEST_PRACTICES §2.3).
 * Every field is optional — partial overrides are merged with defaults.
 */
export interface KProtectOverrides {
  transport?: TransportOverrides;
  session?: SessionOverrides;
  identity?: IdentityOverrides;
  page_gate?: PageGateOverrides;
  critical_actions?: CriticalActionsOverrides;
  environment?: 'production' | 'debug';
  /** Device fingerprinting config. */
  fingerprinting?: {
    /** Set to false to disable device fingerprinting entirely. Default: true. */
    enabled?: boolean;
  };
  /** Consent configuration for GDPR/CCPA compliance. */
  consent?: {
    /**
     * Consent mode. Default: 'opt-out' (SDK runs unless user opts out).
     * Set to 'opt-in' for GDPR-strict mode (SDK blocked until consent given).
     * Set to 'none' for environments without consent requirements.
     */
    mode?: 'opt-in' | 'opt-out' | 'none';
  };
}

/**
 * The minimal public config object passed to `KProtect.init()`.
 * Only `api_key` is required.
 */
export interface KProtectConfig {
  /** Live or test API key: `kp_live_…` or `kp_test_…`. */
  api_key: string;
  overrides?: KProtectOverrides;
}

// ═══════════════════════════════════════════════════════════════════════════
// §E  ResolvedConfig — internal, post-merge config used by the worker
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Fully resolved (defaults merged with overrides) config.
 * All fields are required here — the worker never checks for undefined.
 */
export interface ResolvedConfig {
  api_key: string;
  environment: 'production' | 'debug';

  transport: {
    mode: TransportMode;
    /** Full ingest URL — already resolved from base + path (or proxy endpoint). */
    endpoint: string;
  };

  session: {
    pulse_interval_ms: number;
    idle_timeout_ms: number;
    keepalive_interval_ms: number;
  };

  identity: {
    username: {
      selectors: UsernameSelector[];
      sso_globals: string[];
    };
  };

  page_gate: {
    opt_out_patterns: Array<string | RegExp>;
  };

  critical_actions: {
    actions: CriticalAction[];
  };

  fingerprinting: {
    enabled: boolean;
  };

  consent: {
    mode: 'opt-in' | 'opt-out' | 'none';
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// §F  Main → Worker postMessage discriminated union
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Raw event tap from a passive main-thread listener.
 *
 * `signal` codes:
 *   kd = keydown, ku = keyup
 *   pm = pointermove, pd = pointerdown, pu = pointerup
 *   ts = touchstart, te = touchend, tm = touchmove
 *   sc = scroll, cl = click, fb = focus/blur
 *
 * `data` is a transferable ArrayBuffer (zero-copy across the boundary).
 * The worker owns the buffer after receipt.
 */
export interface EventTapMsg {
  type: 'EVENT_TAP';
  signal: 'kd' | 'ku' | 'pm' | 'pd' | 'pu' | 'ts' | 'te' | 'tm' | 'sc' | 'cl' | 'fb';
  /** Serialized event payload (layout defined per collector). */
  data: ArrayBuffer;
  /** performance.now() timestamp from the main thread at event capture. */
  ts: number;
}

/** SPA route change — worker updates PageGate and starts/stops collectors. */
export interface RouteChangeMsg {
  type: 'ROUTE_CHANGE';
  /** New URL path (no query params, no fragment). */
  path: string;
}

/** Page visibility change (visibilitychange / pagehide). */
export interface VisibilityChangeMsg {
  type: 'VISIBILITY_CHANGE';
  visible: boolean;
}

/**
 * Username hash delivered from the main-thread DomScanner.
 * SHA-256 hex computed on main thread — plaintext never sent (§5.2).
 */
export interface UsernameCapturedMsgToWorker {
  type: 'USERNAME_CAPTURED';
  user_hash: UserHash;
}

/** User committed a critical action (clicked commit trigger). */
export interface CriticalActionCommitMsg {
  type: 'CRITICAL_ACTION_COMMIT';
  /** The `action` string from the matching CriticalAction definition. */
  action: string;
}

/** Worker initialisation — sent once on `KProtect.init()`. */
export interface InitMsg {
  type: 'INIT';
  config: ResolvedConfig;
  /** Main-thread location.origin for session origin binding (Finding 11). */
  origin?: string | undefined;
}

/** Explicit logout — worker clears username, ends session, keeps device_uuid. */
export interface LogoutMsg {
  type: 'LOGOUT';
}

/** Teardown the worker. `clearIdentity: true` wipes device_uuid and username. */
export interface DestroyMsg {
  type: 'DESTROY';
  clearIdentity: boolean;
}

/** Periodic mutable-signal refresh (network, battery) from main thread. */
export interface MutableSignalsUpdateMsg {
  type: 'MUTABLE_SIGNALS_UPDATE';
  network: NetworkFingerprint | null;
  battery: BatteryFingerprint | null;
}

/** Discriminated union of all main→worker messages. */
export type MainToWorkerMsg =
  | EventTapMsg
  | RouteChangeMsg
  | VisibilityChangeMsg
  | UsernameCapturedMsgToWorker
  | CriticalActionCommitMsg
  | InitMsg
  | LogoutMsg
  | DestroyMsg
  | DeviceFingerprintMsg
  | MutableSignalsUpdateMsg
  | ExportAuditLogMsg;

/** Request to export the tamper-evident audit log (SOC 2 compliance). */
export interface ExportAuditLogMsg {
  type: 'EXPORT_AUDIT_LOG';
}

// ═══════════════════════════════════════════════════════════════════════════
// §G  Worker → Main postMessage discriminated union
// ═══════════════════════════════════════════════════════════════════════════

/** Emitted once when the worker has finished initialising a new session. */
export interface SessionStartedMsg {
  type: 'SESSION_STARTED';
  session_id: UUID;
  /** Pulse counter at session start (always 0). */
  pulse: PulseCounter;
}

/** Reason a session was terminated. */
export type SessionEndReason = 'pagehide' | 'logout' | 'destroy' | 'idle_timeout' | 'origin_mismatch';

/** Emitted when the worker has closed the current session. */
export interface SessionEndedMsg {
  type: 'SESSION_ENDED';
  session_id: UUID;
  reason: SessionEndReason;
}

/** Drift assessment returned from the server, forwarded to the host app. */
export interface DriftScoreMsg {
  type: 'DRIFT_SCORE';
  response: DriftScoreResponse;
}

/** One or more security alerts forwarded to the host app. */
export interface AlertMsg {
  type: 'ALERT';
  alerts: Alert[];
}

/** Drift score result for a critical-action batch. */
export interface CriticalActionResultMsg {
  type: 'CRITICAL_ACTION_RESULT';
  response: DriftScoreResponse;
}

/**
 * Username hash confirmed — echoed from worker so the host app can
 * observe successful identity capture without accessing raw storage.
 */
export interface UsernameCapturedMsgFromWorker {
  type: 'USERNAME_CAPTURED';
  user_hash: UserHash;
}

/** Periodic worker state snapshot for the host app / debug panel. */
export interface StateUpdateMsg {
  type: 'STATE_UPDATE';
  state: SessionState;
}

/**
 * Storage write instruction from the worker to the main thread.
 * Keeps localStorage in sync with the worker's IDB-primary storage.
 * `value === null` instructs the main thread to delete the key.
 */
export interface StorageWriteMsg {
  type: 'STORAGE_WRITE';
  key: string;
  /** null = delete the key. */
  value: string | null;
  storage: 'local' | 'session';
}

/** Discriminated union of all worker→main messages. */
export type WorkerToMainMsg =
  | SessionStartedMsg
  | SessionEndedMsg
  | DriftScoreMsg
  | AlertMsg
  | CriticalActionResultMsg
  | UsernameCapturedMsgFromWorker
  | StateUpdateMsg
  | StorageWriteMsg
  | AuditLogExportMsg;

/** Audit log entry (wire format for export). */
export interface WireAuditEntry {
  seq: number;
  timestamp: string;
  action: string;
  detail: Record<string, string | number | boolean> | null;
  prev_hash: string;
}

/** Response containing the exported audit log. */
export interface AuditLogExportMsg {
  type: 'AUDIT_LOG_EXPORT';
  entries: WireAuditEntry[];
}

// ═══════════════════════════════════════════════════════════════════════════
// §H  Behavioral signal types (wire format — transmitted to server)
// ═══════════════════════════════════════════════════════════════════════════

/** Statistical summary for a series of timing measurements (all values in ms). */
export interface TimingSummary {
  mean: number;
  /** null when sample_count < 2 — insufficient data for meaningful std dev (Finding 4). */
  std_dev: number | null;
  p25: number;
  p50: number;
  p75: number;
  p95: number;
  sample_count: number;
}

/**
 * Keystroke timing patterns — NO key content, only dwell/flight timings
 * and rhythm features (SDK_BEST_PRACTICES §5.1).
 */
export interface KeystrokeSignal {
  available: boolean;

  /** How long each key is held (key-down to key-up), in ms. */
  dwell_times: TimingSummary;

  /** Gap between key-up and the next key-down, in ms. */
  flight_times: TimingSummary;

  /** Backspaces per 10 keystrokes. */
  backspace_rate: number;
  /** Rapid correction sequences (multiple backspaces) per minute. */
  correction_burst_rate: number;

  /** Estimated words per minute over the window. */
  words_per_minute: number;
  /** Fraction of time spent in "burst" typing mode (>4 keys/s). */
  burst_typing_fraction: number;

  /**
   * 10×10 inter-zone transition frequency matrix.
   * Zones: 0=L-pinky, 1=L-ring, 2=L-middle, 3=L-index, 4=R-pinky,
   * 5=R-index, 6=R-middle, 7=R-ring, 8=reserved, 9=thumbs.
   * Zone 10 (special keys) excluded from matrix.
   * matrix[i][j] = count of transitions from zone i to zone j.
   * No key names — only zone indices.
   */
  zone_transition_matrix: number[][];
  /** Zone IDs present in this window (subset of [0..10]). */
  zone_ids_used: string[];

  /** Per-input-field aggregates (keyed by field zone_id, not field name). */
  field_breakdown?: Array<{
    zone_id: string;
    event_count: number;
    dwell_mean: number;
    flight_mean: number;
  }>;

  /**
   * True when keystroke events originated from a sensitive field
   * (password, PIN). Key identity is zeroed out — only timing metadata remains.
   * Defense-in-depth: the spec already says no content capture, this adds
   * explicit obfuscation.
   */
  sensitive_field_detected?: boolean;
}

/** Mouse/trackpad movement and click patterns. No absolute coordinates (§5.3). */
export interface PointerSignal {
  available: boolean;

  /** Velocity profile (px/ms). */
  velocity: {
    mean: number;
    max: number;
    p50: number;
    p95: number;
  };

  /** Acceleration profile. */
  acceleration: {
    mean: number;
    std_dev: number;
    /** Direction reversals per second. */
    direction_changes_per_sec: number;
  };

  /** Click summary. */
  clicks: {
    count: number;
    double_click_count: number;
    /** How long the mouse button is held during a click (ms). */
    mean_dwell_ms: number;
    /** Zone IDs where clicks occurred (no pixel coordinates). */
    zone_ids: string[];
  };

  /** Fraction of the window where pointer was stationary. */
  idle_fraction: number;
  /** Fraction of movement classified as fast/straight ballistic motion. */
  ballistic_fraction: number;
  /** Small corrective micro-movements per cm of pointer travel. */
  micro_correction_rate: number;
  /** Mean path curvature: 0 = straight lines, 1 = circular arcs. */
  mean_curvature: number;
}

/** Mobile touch-screen patterns. No absolute coordinates (§5.3). */
export interface TouchSignal {
  available: boolean;

  /** Normalized contact area (0–1). */
  mean_contact_area: number;
  /** Normalized pressure (0–1, where hardware supports it). */
  mean_pressure: number;

  tap: {
    count: number;
    /** Mean time between touch-start and touch-end for taps (ms). */
    mean_dwell_ms: number;
    /** Mean time between consecutive taps (ms). */
    mean_flight_ms: number;
    /** Zone IDs where taps occurred. */
    zone_ids: string[];
  };

  swipe: {
    count: number;
    mean_velocity: number;    // normalized
    mean_distance: number;    // normalized (not pixel values)
    direction_distribution: {
      up: number;
      down: number;
      left: number;
      right: number;
    };
  };

  /** Two-finger pinch gesture count. */
  pinch_count: number;
  /** Two-finger spread gesture count. */
  spread_count: number;

  /** Dominant hand hint inferred from touch-zone bias patterns. */
  dominant_hand_hint: 'left' | 'right' | 'unknown';
}

/**
 * Unified gesture signal — combines pointer (mouse/trackpad) and touch
 * behavioral patterns into a single signal type.
 *
 * On desktop: pointer section populated, touch null.
 * On mobile: touch section populated, pointer may also be populated (stylus).
 * On hybrid: both sections populated.
 */
export interface GestureSignal {
  available: boolean;

  /** Mouse/trackpad gesture patterns. Null if no pointer events in window. */
  pointer: {
    velocity: { mean: number; max: number; p50: number; p95: number; std_dev: number | null };
    acceleration: { mean: number; std_dev: number | null; direction_changes_per_sec: number };
    clicks: { count: number; double_click_count: number; mean_dwell_ms: number; dwell_stdev: number | null };
    idle_fraction: number;
    ballistic_fraction: number;
    micro_correction_rate: number;
    mean_curvature: number;
    path_efficiency: number;
    angle_histogram: number[];
    segments: {
      count: number;
      duration_mean: number;
      distance_mean: number;
      efficiency_mean: number;
    };
    move_count: number;
    total_distance: number;
  } | null;

  /** Touch-screen gesture patterns. Null if no touch events in window. */
  touch: {
    mean_contact_area: number;
    area_stdev: number | null;
    tap: { count: number; mean_dwell_ms: number; dwell_stdev: number | null; mean_flight_ms: number; flight_stdev: number | null };
    swipe: { count: number; duration_mean: number; duration_stdev: number | null };
    pinch_count: number;
    heatmap_zones: number[];
    dominant_hand_hint: 'left' | 'right' | 'unknown';
  } | null;
}

/** Scroll behaviour — reading/navigation pattern analysis. */
export interface ScrollSignal {
  available: boolean;

  scroll_events: number;
  mean_velocity: number;           // normalized
  mean_distance_per_scroll: number; // normalized

  /** Pauses mid-content (not at top or bottom — reading pattern). */
  reading_pause_count: number;
  /** Fast top-to-bottom sweeps (navigation pattern). */
  rapid_scroll_count: number;

  direction_distribution: {
    up: number;
    down: number;
    horizontal: number;
  };
}

/** Device motion sensor data (mobile only). */
export interface SensorSignal {
  available: boolean;

  accelerometer?: {
    mean_magnitude: number;
    std_dev: number;
    /** Fraction of the window where device acceleration was near-zero. */
    stillness_fraction: number;
  };

  gyroscope?: {
    mean_rotation_rate: number;
    dominant_axis: 'x' | 'y' | 'z';
    stillness_fraction: number;
  };

  /** Inferred physical posture of the device during the window. */
  device_posture: 'flat' | 'portrait_stable' | 'landscape_stable' | 'moving' | 'unknown';
}

/**
 * Behavioral metadata captured from credential input fields.
 * Field VALUES are never read (SDK_BEST_PRACTICES §5.5).
 */
export interface CredentialSignal {
  available: boolean;

  /** Patterns observed on `input[type="password"]` fields. */
  password_field?: {
    total_keystrokes: number;
    backspace_count: number;
    /** true if Ctrl+V / right-click-paste observed. */
    paste_detected: boolean;
    /** true if field was filled programmatically (autofill). */
    autofill_detected: boolean;
    mean_dwell_ms: number;
    mean_flight_ms: number;
    /** Typed, deleted all, re-typed — hesitation/error pattern. */
    typed_then_cleared: boolean;
  };

  /** Patterns observed on username fields (type=text/email/tel). */
  username_field?: {
    total_keystrokes: number;
    backspace_count: number;
    paste_detected: boolean;
    autofill_detected: boolean;
    /** Browser auto-complete suggestion was selected. */
    autocomplete_selected: boolean;
  };

  /** Form-submission behaviour. */
  form?: {
    /** Time from first keystroke in form to submit event (ms). */
    time_to_submit_ms: number;
    /** Tab key presses used to navigate between form fields. */
    tab_navigation_count: number;
    submit_method: 'button_click' | 'enter_key' | 'programmatic';
  };
}

/** All behavioral signals included in a single batch window. */
export interface SignalSet {
  keystroke?: KeystrokeSignal;
  pointer?: PointerSignal;      // keep for backwards compat
  touch?: TouchSignal;          // keep for backwards compat
  gesture?: GestureSignal;      // NEW: unified pointer + touch
  scroll?: ScrollSignal;
  sensor?: SensorSignal;
  credential?: CredentialSignal;
}

// ═══════════════════════════════════════════════════════════════════════════
// §I  Server wire types — request payloads
// ═══════════════════════════════════════════════════════════════════════════

/** SDK metadata appended to every outbound batch. */
export interface SdkMeta {
  /** Semver string e.g. '1.0.0'. */
  version: string;
  platform: 'web' | 'android' | 'ios';
  worker_mode: 'worker' | 'fallback_main_thread';
  environment: 'production' | 'debug';
}

/** Minimal SDK metadata included in lightweight batches (keepalive, session events). */
export interface SdkMetaLite {
  version: string;
  platform: string;
}

/** Page context for normal (non-critical) pages. */
export interface NormalPageContext {
  /** URL path only — no query params, no fragment (§5.1). */
  url_path: string;
  page_class: 'normal';
  /** URL path of the referring page in the same session. */
  referrer_path?: string;
}

/** Page context for critical-action pages. */
export interface CriticalPageContext {
  url_path: string;
  page_class: 'critical_action';
  referrer_path?: string;
  /** Matches CriticalAction.action e.g. 'payment_confirm'. */
  critical_action: string;
  /** true = user clicked commit trigger; false = navigated away. */
  committed: boolean;
  /** Duration on this page before commit/abandon (ms). */
  time_on_page_ms: number;
}

/** Page context sent in keepalive batches (subset of CriticalPageContext). */
export interface KeepalivePageContext {
  url_path: string;
  page_class: 'critical_action';
  critical_action: string;
}

/**
 * BehavioralBatch — sent on every pulse tick on `normal` page class.
 * Wire format documentation: docs/WIRE_PROTOCOL.md §BehavioralBatch.
 */
export interface BehavioralBatch {
  type: 'behavioral';

  // ─── Batch identity ──────────────────────────────────────────────────────
  /** UUID, unique per batch — used as idempotency key. */
  batch_id: UUID;
  /** Unix ms: performance.now() offset + session_start epoch. */
  sent_at: EpochMs;

  // ─── Session identity ─────────────────────────────────────────────────────
  session_id: UUID;
  /** Monotonic counter starting at 0 for this session. */
  pulse: PulseCounter;
  /** Actual pulse interval used in this session (server detects gaps). */
  pulse_interval_ms: number;
  /** Monotonic counter of ALL batches in session (never resets on page nav). */
  sequence: number;

  // ─── User identity ────────────────────────────────────────────────────────
  user_hash: UserHash;
  /** Included only in the first batch of a session; omitted thereafter to reduce redundancy. */
  device_uuid?: UUID;

  // ─── Origin binding (Finding 11) ─────────────────────────────────────────
  /** SHA-256(session_id + origin) — binds session to its origin. */
  origin_hash?: string | undefined;

  // ─── Page context ─────────────────────────────────────────────────────────
  page_context: NormalPageContext;

  // ─── Window coverage ──────────────────────────────────────────────────────
  /** performance.now() of the first event captured in this batch. */
  window_start_ms: number;
  /** performance.now() of the last event captured in this batch. */
  window_end_ms: number;
  /** Total raw events collected before feature extraction. */
  event_count: number;

  // ─── Behavioral signals ───────────────────────────────────────────────────
  signals: SignalSet;

  // ─── Automation detection ──────────────────────────────────────────────────
  /** Bot/automation likelihood (0.0 = human, 1.0 = automated). From automation-detect. */
  automation_score?: number;

  // ─── SDK metadata ─────────────────────────────────────────────────────────
  sdk: SdkMeta;
}

/**
 * CriticalActionBatch — sent when a user commits or abandons a critical-action
 * page. Extends BehavioralBatch with richer page context.
 *
 * Wire format: docs/WIRE_PROTOCOL.md §CriticalActionBatch.
 */
export interface CriticalActionBatch
  extends Omit<BehavioralBatch, 'type' | 'page_context'> {
  type: 'critical_action';
  page_context: CriticalPageContext;
}

/**
 * KeepaliveBatch — sent on the slow keepalive cadence while the user is on
 * a critical-action page. Contains NO behavioral signals (keeps the session
 * alive server-side during extended form-filling).
 *
 * Wire format: docs/WIRE_PROTOCOL.md §KeepaliveBatch.
 */
export interface KeepaliveBatch {
  type: 'keepalive';
  batch_id: UUID;
  sent_at: EpochMs;
  session_id: UUID;
  pulse: PulseCounter;
  pulse_interval_ms: number;
  user_hash: UserHash;
  /** Included only in the first batch of a session; omitted thereafter to reduce redundancy. */
  device_uuid?: UUID;
  /** SHA-256(session_id + origin) — session origin binding (Finding 11). Included only in the first batch. */
  origin_hash?: string | undefined;
  page_context: KeepalivePageContext;
  sdk: SdkMetaLite;
}

/**
 * SessionEventBatch — sent on session-start and session-end.
 * No behavioral signals.
 *
 * Wire format: docs/WIRE_PROTOCOL.md §SessionEventBatches.
 */
export interface SessionEventBatch {
  type: 'session_start' | 'session_end';
  batch_id: UUID;
  sent_at: EpochMs;
  session_id: UUID;
  /** null when the session ended before a username was captured. */
  user_hash: UserHash | null;
  device_uuid: UUID;
  /** Epoch ms when this session began. */
  session_start_ms: EpochMs;
  /** Epoch ms when this session ended (session_end only). */
  session_end_ms?: EpochMs;
  end_reason?: SessionEndReason;
  total_pulses: number;
  /** SHA-256(session_id + origin) — session origin binding (Finding 11). */
  origin_hash?: string | undefined;
  sdk: SdkMetaLite;
}

/** Union of all outbound batch types. */
export type AnyBatch =
  | BehavioralBatch
  | CriticalActionBatch
  | KeepaliveBatch
  | SessionEventBatch
  | DeviceFingerprintBatch;

// ═══════════════════════════════════════════════════════════════════════════
// §J  Server response types
// ═══════════════════════════════════════════════════════════════════════════

/** Per-signal decomposed drift scores (each 0.0–1.0). */
export interface SignalScores {
  keystroke?: number;
  pointer?: number;
  touch?: number;
  gesture?: number;  // NEW: unified pointer + touch
  scroll?: number;
  sensor?: number;
  credential?: number;
}

/** Authentication / device trust state returned by the server. */
export interface AuthState {
  session_trust: 'trusted' | 'suspicious' | 'anomalous';
  /** Whether device_uuid has been seen before for this user. */
  device_known: boolean;
  /** Days since the behavioural baseline was first established. */
  baseline_age_days: number;
  /** Quality of the current baseline (data quantity indicator). */
  baseline_quality: 'insufficient' | 'forming' | 'established' | 'strong';
}

/** A security alert emitted by the server when drift is elevated. */
export interface Alert {
  alert_id: UUID;
  severity: 'low' | 'medium' | 'high' | 'critical';
  /** Machine-readable alert class e.g. 'device_change', 'bot_pattern'. */
  type: string;
  /** Human-readable explanation (debug mode only — stripped in production). */
  description: string;
  triggered_at: EpochMs;
}

/**
 * DriftScoreResponse — server response after processing any behavioral batch.
 * Wire format: docs/WIRE_PROTOCOL.md §DriftScoreResponse.
 */
export interface DriftScoreResponse {
  // ─── Batch acknowledgment ──────────────────────────────────────────────────
  /** Echo of the request batch_id (idempotency acknowledgment). */
  batch_id: UUID;
  processed_at: EpochMs;

  // ─── Drift assessment ─────────────────────────────────────────────────────
  /** Overall drift score: 0.0 = identical to baseline, 1.0 = maximum drift. */
  drift_score: number;
  /** Confidence in the assessment: 0.0 = no data, 1.0 = strong baseline. */
  confidence: number;
  signal_scores: SignalScores;

  // ─── Recommended action ───────────────────────────────────────────────────
  action: 'allow' | 'monitor' | 'challenge' | 'block';
  /** Human-readable reason string (debug mode only). */
  action_reason?: string;

  // ─── Multi-dimensional scores ─────────────────────────────────────────────
  /** Anomaly score: how unusual this session is vs population. 0=normal, 1=outlier. -1=unavailable. */
  anomaly_score: number;
  /** Trust score: composite of all trust factors. 0=no trust, 1=fully trusted. */
  trust_score: number;
  /** Bot score: probability of automation. 0=human, 1=bot. */
  bot_score: number;
  /** Server-generated decision ID for audit trail. */
  decision_id?: UUID;
  /** Policy that triggered the action (if any). */
  policy_id?: string;

  // ─── Auth state ───────────────────────────────────────────────────────────
  auth_state: AuthState;

  // ─── Alerts ───────────────────────────────────────────────────────────────
  /** Present when action is 'challenge' or 'block'. */
  alerts?: Alert[];
}

/**
 * SessionMetadataResponse — extends DriftScoreResponse and is returned
 * alongside the response to the `session_start` batch.
 */
export interface SessionMetadataResponse extends DriftScoreResponse {
  session_metadata: {
    session_id: UUID;
    user_hash: UserHash;
    /** Number of distinct device_uuids previously seen for this user. */
    device_history_count: number;
    /** Total historical sessions on record for this user. */
    session_history_count: number;
    /** Days since last seen (0 = today). */
    last_seen_days_ago: number;
  };
}

/**
 * ErrorResponse — standard error envelope from the API.
 * Wire format: docs/WIRE_PROTOCOL.md §ErrorResponses.
 */
export interface ErrorResponse {
  ok: false;
  error: {
    /** Machine-readable code e.g. 'RATE_LIMITED', 'INVALID_API_KEY'. */
    code: string;
    message: string;
    /** Present on 429 responses — minimum backoff duration (ms). */
    retry_after_ms?: number;
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// §K  SessionState — live worker state snapshot
// ═══════════════════════════════════════════════════════════════════════════

/** Page classification used by the PageGate. */
export type PageClass = 'normal' | 'critical_action' | 'opted_out';

/** Current lifecycle phase of the session. */
export type SessionPhase =
  | 'uninitialised'
  | 'active'
  | 'idle'
  | 'ended';

/** Liveness status of the SDK collection pipeline. */
export type LivenessStatus = 'alive' | 'stale' | 'dead';

/**
 * SessionState — periodic snapshot emitted by the worker via STATE_UPDATE.
 * Used by the host-app event callback and the debug panel.
 */
export interface SessionState {
  /** Current lifecycle phase. */
  phase: SessionPhase;
  /** Current session UUID (null before first session starts). */
  session_id: UUID | null;
  /** Current pulse counter. */
  pulse: PulseCounter;
  /** Whether a username hash has been captured this session. */
  identity_captured: boolean;
  /** Current page classification. */
  page_class: PageClass;
  /** Current critical-action name (null when page_class !== 'critical_action'). */
  current_action: string | null;
  /** Number of batches currently queued for transmission. */
  transport_queue_depth: number;
  /** Number of buffered feature windows in the pre-identity ring buffer. */
  ring_buffer_depth: number;
  /** Last known drift score from the server (null if no response yet). */
  last_drift_score: number | null;
  /** Last known recommended action from the server. */
  last_action: DriftScoreResponse['action'] | null;
  /** Liveness status: whether SDK is actively receiving events. */
  liveness_status: LivenessStatus;
  /** SHA-256(session_id + origin) — binds session to its origin (Finding 11). */
  origin_hash: string | null;
}

/**
 * GDPRExport — all stored data about the user, returned by KProtect.gdpr.export().
 * Does NOT return raw behavioral data (discarded after feature extraction).
 */
export interface GDPRExport {
  /** SHA-256 hashed username (never plaintext). */
  user_hash: string | null;
  /** Persistent device UUID. */
  device_uuid: string | null;
  /** Current session ID. */
  session_id: string | null;
  /** Current consent state. */
  consent_state: string;
  /** Timestamp of export. */
  exported_at: number;
  /** All localStorage keys under the kp.* namespace and their values (excluding raw user content). */
  stored_keys: Record<string, string | null>;
}

// ═══════════════════════════════════════════════════════════════════════════
// §K2  Device Fingerprint types
// ═══════════════════════════════════════════════════════════════════════════

/** Canvas 2D rendering fingerprint — text, shapes, gradients, emoji drawn and hashed. */
export interface CanvasFingerprint {
  /** SHA-256 of the canvas toDataURL() output. */
  hash: string;
}

/**
 * AudioContext fingerprint — OfflineAudioContext oscillator→compressor pipeline.
 * Spec: device_fingerprinting.md §TIER 2.
 */
export interface AudioFingerprint {
  /** SHA-256 of the first 100 float samples. */
  hash: string;
  /** Number of samples hashed. */
  sample_count: number;
}

/** WebGL shader precision format descriptor. */
export interface ShaderPrecision {
  rangeMin: number;
  rangeMax: number;
  precision: number;
}

/**
 * WebGL parameter dump — 14 GL params, shader precision, renderer info.
 * Spec: device_fingerprinting.md §TIER 1.
 */
export interface WebGLFingerprint {
  /** Raw GL parameter values keyed by GL constant name. */
  params: Record<string, number | number[] | null>;
  /** Shader precision formats (e.g. VERTEX_SHADER_HIGH_FLOAT). */
  precisions: Record<string, ShaderPrecision | null>;
  /** UNMASKED_RENDERER_WEBGL (via WEBGL_debug_renderer_info). */
  renderer: string | null;
  /** UNMASKED_VENDOR_WEBGL. */
  vendor: string | null;
  /** Whether WebGL2 context is available. */
  webgl2: boolean;
  /** SHA-256 of the full param+precision dump. */
  hash: string;
}

/**
 * GPU render task result — pixel-hash from a specific render test.
 * Spec: device_fingerprinting.md §TIER 2 GPU Render Tasks.
 */
export interface GpuRenderTaskResult {
  /** Test name: gradient_triangle, alpha_blend, float_precision, antialias_lines, texture_filter. */
  test: string;
  /** SHA-256 of readPixels output. */
  exact_hash: string;
  /** Quantized 4-bit hash for cross-browser matching. */
  quantized_hash: string;
}

/** Full GPU render fingerprint with all 5 test results. */
export interface GpuRenderFingerprint {
  tasks: GpuRenderTaskResult[];
  /** Combined hash of all task results. */
  combined_hash: string;
  /** Time taken to run all render tasks (ms). */
  elapsed_ms: number;
}

/** Font enumeration result — DOM measurement against baseline widths. */
export interface FontFingerprint {
  /** Count of detected fonts. */
  count: number;
  /** SHA-256 of the sorted, comma-joined font list. */
  hash: string;
}

/** CPU micro-benchmark results and computed ratios. */
export interface CpuBenchmark {
  /** Raw benchmark times in ms. */
  times: {
    int_arithmetic: number;
    float_arithmetic: number;
    string_ops: number;
    array_sort: number;
    crypto_hash: number;
  };
  /** Computed ratios (more stable across load than raw times). */
  ratios: {
    int_to_float: number;
    string_to_array: number;
    crypto_to_int: number;
  };
  /** Time taken to run all benchmarks (ms). */
  elapsed_ms: number;
}

/** Screen and display hardware signals. */
export interface ScreenFingerprint {
  width: number;
  height: number;
  avail_width: number;
  avail_height: number;
  color_depth: number;
  pixel_depth: number;
  device_pixel_ratio: number;
  orientation: string | null;
  color_gamut_p3: boolean;
  hdr: boolean;
}

/** Platform/navigator signals — TIER 1 stable. */
export interface PlatformFingerprint {
  hardware_concurrency: number | null;
  device_memory_gb: number | null;
  max_touch_points: number;
  platform: string;
  timezone: string;
  timezone_offset_min: number;
  primary_language: string;
  cookie_enabled: boolean;
  pdf_viewer: boolean | null;
  vendor: string | null;
  user_agent_data: UserAgentData | null;
}

/** Client-Hints user agent data. */
export interface UserAgentData {
  brands: string[] | null;
  mobile: boolean;
  platform: string | null;
  platform_version: string | null;
  architecture: string | null;
  model: string | null;
  bitness: string | null;
}

/** Network signals from navigator.connection (Chrome/Edge only). */
export interface NetworkFingerprint {
  effective_type: string | null;
  downlink_mbps: number | null;
  rtt_ms: number | null;
  save_data: boolean | null;
}

/** Math engine fingerprint — float precision quirks. */
export interface MathFingerprint {
  tan_pi_4: number;
  log_2: number;
  e_mod: number;
  pow_min: number;
}

/** Date/Intl formatting fingerprint. */
export interface DateFingerprint {
  full_hash: string;
  short_hash: string;
  relative_era: string;
}

/** CSS feature support fingerprint. */
export interface CssFingerprint {
  [feature: string]: boolean;
}

/** Storage quota fingerprint. */
export interface StorageFingerprint {
  quota_bytes: number | null;
}

/** Speech synthesis voice fingerprint. */
export interface SpeechFingerprint {
  count: number;
  hash: string;
}

/** Battery state (Chrome/Android). */
export interface BatteryFingerprint {
  charging: boolean;
  /** Bucketed to 4 levels: 0.0, 0.25, 0.5, 0.75, 1.0. */
  level_bucket: number;
}

/** Automation / bot detection flags. */
export interface AutomationFingerprint {
  // Legacy checks (keep for backward compat)
  webdriver: boolean;

  // Modern checks
  /** navigator.plugins.length === 0 (headless browsers have no plugins) */
  zero_plugins: boolean;
  /** window.outerHeight === 0 || window.outerWidth === 0 (headless) */
  zero_outer_dimensions: boolean;
  /** !document.hasFocus() at collection time */
  no_focus: boolean;
  /** navigator.permissions.query({name:'notifications'}) auto-denied */
  notifications_denied: boolean | null;
  /** Inconsistent hardwareConcurrency vs deviceMemory */
  hardware_mismatch: boolean;
  /** Chrome DevTools Protocol detection via Error.stack */
  cdp_detected: boolean;
  /** window.Proxy has been overridden (common in automation frameworks) */
  proxy_overridden: boolean;
  /** Overall automation score (0.0 = human, 1.0 = definitely automated) */
  score: number;
}

/** Media query environment fingerprint. */
export interface MediaQueryFingerprint {
  pointer_fine: boolean | null;
  hover_hover: boolean | null;
  color_gamut_p3: boolean | null;
  dynamic_range_high: boolean | null;
  prefers_reduced_motion: boolean | null;
  prefers_color_scheme_dark: boolean | null;
}

/** Browser feature flags. */
export interface FeatureFlags {
  web_worker: boolean;
  service_worker: boolean;
  web_gl: boolean;
  web_gl2: boolean;
  web_audio: boolean;
  compression_stream: boolean;
  crypto_subtle: boolean;
  intersection_observer: boolean;
  resize_observer: boolean;
  pointer_events: boolean;
  touch_events: boolean;
  gamepad: boolean;
  bluetooth: boolean;
  usb: boolean;
  media_devices: boolean;
  shared_array_buffer: boolean;
  wasm: boolean;
  webgpu: boolean;
}

/**
 * LoadIndicators — performance load state at collection time.
 * Used to contextualize fingerprint stability under heavy load.
 */
export interface LoadIndicators {
  /** Estimated frames per second (10-frame sample). Null if measurement timed out. */
  estimated_fps: number | null;
  /** Average event loop latency in ms (5 samples of setTimeout(0) delay). */
  event_loop_latency_ms: number | null;
  /** Heap memory used in MB (Chrome only). Null if unavailable. */
  memory_used_mb: number | null;
  /** Heap memory limit in MB (Chrome only). Null if unavailable. */
  memory_limit_mb: number | null;
  /** Whether the document was hidden at collection time. */
  document_was_hidden: boolean;
}

/**
 * Complete device fingerprint payload — collected once on init,
 * re-collected on significant environment changes.
 */
export interface DeviceFingerprint {
  /** TIER 1 — synchronous, cross-browser stable. */
  screen: ScreenFingerprint | null;
  platform: PlatformFingerprint | null;
  media_queries: MediaQueryFingerprint | null;
  features: FeatureFlags | null;
  math: MathFingerprint | null;
  date_format: DateFingerprint | null;
  css: CssFingerprint | null;

  /** TIER 2 — async, computation-required. */
  canvas: CanvasFingerprint | null;
  audio: AudioFingerprint | null;
  webgl: WebGLFingerprint | null;
  gpu_render: GpuRenderFingerprint | null;
  fonts: FontFingerprint | null;
  cpu: CpuBenchmark | null;

  /** TIER 3 — browser-specific, may be null. */
  network: NetworkFingerprint | null;
  storage: StorageFingerprint | null;
  speech: SpeechFingerprint | null;
  battery: BatteryFingerprint | null;
  automation: AutomationFingerprint | null;

  /** Performance load indicators. */
  load_indicators: LoadIndicators | null;

  /** Collection metadata. */
  collected_at: EpochMs;
  /** Time to collect all signals (ms). */
  collection_time_ms: number;
  /** Fingerprint collection algorithm version. Increment on any collection logic change. */
  fingerprint_version: number;
}

/**
 * DeviceFingerprintBatch — sent once per session (on session_start).
 * Separate from behavioral batches to avoid bloating every pulse.
 */
export interface DeviceFingerprintBatch {
  type: 'device_fingerprint';
  batch_id: UUID;
  sent_at: EpochMs;
  session_id: UUID;
  user_hash: UserHash | null;
  device_uuid: UUID;
  fingerprint: DeviceFingerprint;
  sdk: SdkMetaLite;
}

/** Main → Worker message carrying collected fingerprint from main thread. */
export interface DeviceFingerprintMsg {
  type: 'DEVICE_FINGERPRINT';
  fingerprint: DeviceFingerprint;
}

// ═══════════════════════════════════════════════════════════════════════════
// §K3  Signed Beacon Payload (sendBeacon transport)
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Signed beacon payload — used with navigator.sendBeacon where custom
 * HTTP headers are not available. The HMAC-SHA256 signature is embedded
 * directly in the request body instead of X-KP-Signature header.
 *
 * Signature message: HMAC-SHA256(api_key, nonce + '.' + timestamp + '.' + sha256(payload))
 *
 * See: transport/beacon-signing.ts for creation/verification functions.
 */
export interface SignedBeaconPayload {
  /** JSON-stringified batch data. */
  payload: string;
  /** HMAC-SHA256 hex digest of: nonce + '.' + timestamp + '.' + sha256(payload). */
  signature: string;
  /** First 12 characters of the API key — server uses this to look up the full key. */
  key_id: string;
  /** Unix timestamp in ms at signing time. */
  timestamp: EpochMs;
  /** Batch ID used as nonce for replay protection. */
  nonce: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// §L  Challenge / Verify — phase-2 stubs
// ═══════════════════════════════════════════════════════════════════════════

/**
 * ChallengeResult — returned by `KProtect.challenge.generate()`.
 * Implementation is deferred to phase 2.
 */
export interface ChallengeResult {
  challenge_id: string;
  challenge_type: string;
  prompt: string;
  expires_at: number;
}

/**
 * VerifyResult — returned by `KProtect.challenge.verify()`.
 * Implementation is deferred to phase 2.
 */
export interface VerifyResult {
  challenge_id: string;
  passed: boolean;
  drift_score: number;
  confidence: number;
  action: 'allow' | 'monitor' | 'challenge' | 'block';
}
