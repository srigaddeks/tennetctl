/**
 * defaults.ts — single source of truth for all default values.
 *
 * Rules (SDK_BEST_PRACTICES §2.2):
 *   • No magic numbers anywhere else in the codebase.
 *   • If a constant appears in two places, it belongs here.
 *   • All keys under `kp.` namespace.
 */

import type { UsernameSelector, CriticalAction } from '../runtime/wire-protocol.js';

// ─── Pulse cadences ────────────────────────────────────────────────────────

/** How often the worker fires the behavioural-signal pulse on normal pages (ms). */
export const DEFAULT_PULSE_INTERVAL_MS = 30_000;

/** Minimum raw events required before a normal pulse sends a batch. Avoids diluted/useless batches. */
export const MIN_EVENTS_FOR_PULSE = 10;

/** Slow keepalive pulse cadence on critical-action pages (ms). */
export const DEFAULT_KEEPALIVE_INTERVAL_MS = 30_000;

/** Idle timeout — session ends after this much inactivity (ms). 15 min. */
export const DEFAULT_IDLE_TIMEOUT_MS = 15 * 60 * 1_000;

// ─── Ring buffer / queue limits ────────────────────────────────────────────

/**
 * Maximum extracted-feature windows held in the pre-username ring buffer.
 * At 5s windows this is ~2.5 min of buffered data.
 * Oldest windows dropped on overflow — never grow unbounded (§4.1).
 */
export const MAX_RING_BUFFER_WINDOWS = 30;

/** Maximum number of unsent batches held in the transport retry queue. */
export const MAX_TRANSPORT_QUEUE_DEPTH = 50;

/** Maximum debug-log entries kept in memory (worker-side circular log). */
export const MAX_DEBUG_LOG_ENTRIES = 20;

// ─── Differential privacy ─────────────────────────────────────────────────

/** Laplace noise scale for zone transition matrix differential privacy. Higher = more privacy, less utility. */
export const ZONE_MATRIX_LAPLACE_SCALE = 2.0;

// ─── Feature extraction ────────────────────────────────────────────────────

/** Feature extraction window size (ms). Raw events discarded after extract (§5.4). */
export const FEATURE_WINDOW_MS = 5_000;

/**
 * Scroll event debounce (ms) before posting to worker.
 * Default: 16 ms ≈ one frame (§4.1).
 */
export const SCROLL_DEBOUNCE_MS = 16;

/**
 * Pointer-move event debounce (ms) before posting to worker.
 * Default: 16 ms ≈ one frame (§4.1).
 */
export const POINTER_DEBOUNCE_MS = 16;

// ─── Storage keys (all under `kp.` namespace — §6.1) ──────────────────────

/** sessionStorage key for the per-tab session UUID. */
export const STORAGE_KEY_SESSION_ID = 'kp.sid';

/** localStorage key for the raw (or encrypted-in-production) username. */
export const STORAGE_KEY_USERNAME = 'kp.un';

/** localStorage key for the persistent device UUID hint. */
export const STORAGE_KEY_DEVICE_UUID = 'kp.did';

/** localStorage key for persisted SDK config overrides. */
export const STORAGE_KEY_CONFIG = 'kp.cfg';

/** localStorage / IDB key for the per-device HMAC signing key (production). */
export const STORAGE_KEY_ENCRYPTION_KEY = 'kp.k';

/** localStorage key for the per-device PBKDF2 username salt. */
export const STORAGE_KEY_USERNAME_SALT = 'kp.us';

/** localStorage key for user consent state. */
export const STORAGE_KEY_CONSENT = 'kp.consent';

/** Default consent mode. 'opt-out' = SDK runs by default, user can opt out. */
export const DEFAULT_CONSENT_MODE = 'opt-out' as const;

// ─── IndexedDB ─────────────────────────────────────────────────────────────

/** IDB database name for the localStorage-fallback key-value store. */
export const IDB_DB_NAME = 'kp-bio';

/** IDB object-store name inside IDB_DB_NAME. */
export const IDB_STORE_NAME = 'kv';

// ─── API ───────────────────────────────────────────────────────────────────

/** Base URL for the K-Protect API (no trailing slash). */
export const API_BASE_URL = 'https://api.kprotect.io';

/** Path to the behavioural ingest endpoint. */
export const API_INGEST_PATH = '/v1/internal/ingest';

// ─── Username capture selectors ────────────────────────────────────────────

/**
 * Default username selectors covering ~80% of banking apps with zero config.
 * See SDK_BEST_PRACTICES §6.4.
 */
export const DEFAULT_USERNAME_SELECTORS: readonly UsernameSelector[] = [
  { selector: 'input[name="username"]',    url: '/login',  event: 'blur' },
  { selector: 'input[name="phoneNumber"]', url: '/login',  event: 'blur' },
  { selector: 'input[name="email"]',       url: '/login',  event: 'blur' },
  { selector: 'input[name="username"]',    url: '/signup', event: 'blur' },
  { selector: 'input[name="phoneNumber"]', url: '/signup', event: 'blur' },
  { selector: 'input[name="email"]',       url: '/signup', event: 'blur' },
] as const;

// ─── Critical actions ──────────────────────────────────────────────────────

/**
 * Default critical-action definitions.
 * Covers common high-risk flows in banking/fintech apps with zero config.
 */
export const DEFAULT_CRITICAL_ACTIONS: readonly CriticalAction[] = [
  { page: /\/login/,        action: 'login_submit',     commit: { selector: 'button[type="submit"]' } },
  { page: /\/signup/,       action: 'signup_submit',    commit: { selector: 'button[type="submit"]' } },
  { page: /\/transfer/,     action: 'transfer_confirm', commit: { selector: '[data-kp-commit="transfer"], button[type="submit"]' } },
  { page: /\/payment/,      action: 'payment_confirm',  commit: { selector: '[data-kp-commit="payment"], button[type="submit"]' } },
  { page: /\/password/,     action: 'password_change',  commit: { selector: 'button[type="submit"]' } },
  { page: /\/profile.*sec/, action: 'security_change',  commit: { selector: 'button[type="submit"]' } },
] as const;

// ─── SSO globals ───────────────────────────────────────────────────────────

/**
 * Global window properties polled once on init and on each route change
 * for SSO-set username values. Integrators set e.g. `window.__KP_USER__`
 * in their SSO callback (§6.4).
 */
export const DEFAULT_SSO_GLOBALS: readonly string[] = [
  'window.__KP_USER__',
] as const;

// ─── Retry policy delays ───────────────────────────────────────────────────

/** Exponential back-off delays (ms) for 429 Rate-Limited responses. */
export const RETRY_DELAYS_429: readonly number[] = [2000, 4000, 8000, 16000] as const;

/** Exponential back-off delays (ms) for 5xx Server Error responses. */
export const RETRY_DELAYS_5XX: readonly number[] = [1000, 2000, 4000] as const;

/** Exponential back-off delays (ms) for network-failure (fetch throws). */
export const RETRY_DELAYS_NETWORK: readonly number[] = [1000, 2000, 4000] as const;

// ─── Liveness check ──────────────────────────────────────────────────────

/** Threshold (ms) of no events before the session is considered "stale". */
export const LIVENESS_STALE_THRESHOLD_MS = 30_000;

// ─── Data retention TTL ──────────────────────────────────────────────────

/** Default TTL for stored data in localStorage/IDB (ms). 30 days. */
export const DATA_RETENTION_TTL_MS = 30 * 24 * 60 * 60 * 1_000;

// ─── Buffer bounds ───────────────────────────────────────────────────────

/** Maximum raw events buffered per extraction window. */
export const MAX_EVENTS_PER_WINDOW = 1_000;

/** Maximum serialized batch payload size in bytes before splitting. */
export const MAX_BATCH_PAYLOAD_BYTES = 512 * 1024;

// ─── Mutable signal refresh ───────────────────────────────────────────────

/** How often to re-check mutable signals (network, battery) in ms. Default: 3 min. */
export const MUTABLE_REFRESH_INTERVAL_MS = 3 * 60 * 1_000;

// ─── Device fingerprinting ────────────────────────────────────────────────

/** Current fingerprint collection algorithm version. Increment on any collection logic change. */
export const FINGERPRINT_VERSION = 1;

/** Maximum time (ms) to wait for all fingerprint collectors before giving up. */
export const FINGERPRINT_TIMEOUT_MS = 5_000;

/** Maximum time (ms) for a single async collector (canvas, audio, webgl, etc). */
export const FINGERPRINT_COLLECTOR_TIMEOUT_MS = 2_000;

/** Maximum time (ms) for GPU render tasks (all 5 tasks combined). */
export const GPU_RENDER_TIMEOUT_MS = 3_000;

/** Maximum time (ms) for CPU benchmarks. */
export const CPU_BENCHMARK_TIMEOUT_MS = 2_000;

/** Maximum time (ms) for speech synthesis voice enumeration. */
export const SPEECH_VOICES_TIMEOUT_MS = 1_000;

/** API path for the device fingerprint ingest endpoint. */
export const API_FINGERPRINT_PATH = '/v1/device/fingerprint';

/**
 * Font families to test during font enumeration.
 * Covers ~30 common fonts across Windows, macOS, and Linux.
 */
export const FONT_TEST_LIST: readonly string[] = [
  'Arial', 'Arial Black', 'Arial Narrow', 'Book Antiqua', 'Bookman Old Style',
  'Calibri', 'Cambria', 'Century', 'Century Gothic', 'Comic Sans MS',
  'Consolas', 'Courier', 'Courier New', 'Georgia', 'Helvetica',
  'Impact', 'Lucida Console', 'Lucida Grande', 'Lucida Sans Unicode',
  'Microsoft Sans Serif', 'Monaco', 'Monotype Corsiva', 'Palatino Linotype',
  'Segoe UI', 'Tahoma', 'Times', 'Times New Roman', 'Trebuchet MS',
  'Verdana', 'Wingdings',
] as const;

/**
 * CSS features to probe during CSS feature fingerprinting.
 * Each entry is a CSS property: value pair for CSS.supports().
 */
export const CSS_FEATURE_PROBES: readonly string[] = [
  'display: grid', 'display: flex', 'display: subgrid',
  'color: oklch(0.5 0.2 240)', 'backdrop-filter: blur(1px)',
  'container-type: inline-size', 'anchor-name: --a',
  'view-transition-name: a', 'text-wrap: balance',
  'accent-color: red', 'aspect-ratio: 1',
  'overscroll-behavior: contain', 'scroll-snap-type: x mandatory',
  'content-visibility: auto',
] as const;
