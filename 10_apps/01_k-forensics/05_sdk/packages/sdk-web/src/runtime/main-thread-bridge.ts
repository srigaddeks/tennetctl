/**
 * main-thread-bridge.ts
 *
 * Main-thread orchestrator for the K-Protect Web SDK.
 *
 * Responsibilities:
 *   - Spawns the Web Worker via blob URL (CSP-safe: worker-src blob:).
 *   - Attaches all passive event listeners that postMessage raw events to
 *     the worker as transferable ArrayBuffers (zero-copy).
 *   - Delegates username detection to UsernameCapture.
 *   - Patches history.pushState / replaceState for SPA route detection.
 *   - Handles visibilitychange and pagehide lifecycle events.
 *   - Routes worker→main messages to registered host-app event handlers.
 *   - Falls back to MainThreadFallback when Worker spawn fails (CSP/compat).
 *
 * SDK_BEST_PRACTICES §1 (Threading), §4 (Performance), §13 (Error Handling).
 *
 * RULES:
 *   - All event listeners use { passive: true }.
 *   - performance.now() for all timestamps.
 *   - try/catch every browser API.
 *   - Main thread MUST NOT do feature extraction, compression, or heavy work.
 *   - All listeners are fire-and-forget postMessage calls.
 */

import type {
  ResolvedConfig,
  WorkerToMainMsg,
  MainToWorkerMsg,
  DriftScoreResponse,
  SessionState,
  WireAuditEntry,
} from './wire-protocol.js';
import { UsernameCapture } from '../session/username-capture.js';
import { MainThreadFallback } from './main-thread-fallback.js';
import { collectAllFingerprints } from '../signals/collect-all.js';
import { startMutableRefresh } from '../signals/mutable-refresh.js';
import { createSignedBeaconPayload } from '../transport/beacon-signing.js';

// ─── Public event type ────────────────────────────────────────────────────────

/**
 * All event types emitted by the KProtect SDK to host-app listeners.
 * Registered via `KProtect.on(event, callback)`.
 */
export type KProtectEventType =
  | 'drift'
  | 'alert'
  | 'critical_action'
  | 'session_start'
  | 'session_end'
  | 'username_captured';

// ─── Signal type codes (binary encoding) ─────────────────────────────────────

/** Uint8 signal type codes used in ArrayBuffer event payloads. */
const SIGNAL_KD = 1;  // keydown
const SIGNAL_KU = 2;  // keyup
const SIGNAL_PM = 3;  // pointermove
const SIGNAL_PD = 4;  // pointerdown
const SIGNAL_SC = 5;  // scroll
const SIGNAL_TS = 6;  // touchstart
const SIGNAL_TE = 7;  // touchend
const SIGNAL_TM = 8;  // touchmove
const SIGNAL_FB = 9;  // focus/blur
const SIGNAL_CL = 10; // click
const SIGNAL_PU = 11; // pointerup

/**
 * 10-zone finger-based keyboard zone map.
 *
 * Maps KeyboardEvent.code → zone number:
 *   0: L-pinky    (Q,A,Z,1,`,Tab,CapsLock,ShiftLeft)
 *   1: L-ring     (W,S,X,2)
 *   2: L-middle   (E,D,C,3)
 *   3: L-index    (R,T,F,G,V,B,4,5)
 *   4: R-pinky    (P,;,/,0,-,=,[,],\,',Enter,Backspace,ShiftRight)
 *   5: R-index    (Y,U,H,J,N,M,6,7)
 *   6: R-middle   (I,K,Comma,8)
 *   7: R-ring     (O,L,Period,9)
 *   8: (reserved for split keyboards)
 *   9: Thumbs     (Space,Ctrl,Alt,Meta)
 *  10: Special    (Arrows,F-keys,Numpad,Escape,Delete,Insert,Home,End,PageUp,PageDown)
 *  -1: Unmapped
 */
const ZONE_MAP: Record<string, number> = {
  // Zone 0 — left pinky
  KeyQ: 0, KeyA: 0, KeyZ: 0, Digit1: 0, Backquote: 0, Tab: 0, CapsLock: 0, ShiftLeft: 0,
  // Zone 1 — left ring
  KeyW: 1, KeyS: 1, KeyX: 1, Digit2: 1,
  // Zone 2 — left middle
  KeyE: 2, KeyD: 2, KeyC: 2, Digit3: 2,
  // Zone 3 — left index
  KeyR: 3, KeyT: 3, KeyF: 3, KeyG: 3, KeyV: 3, KeyB: 3, Digit4: 3, Digit5: 3,
  // Zone 4 — right pinky
  KeyP: 4, Semicolon: 4, Slash: 4, Digit0: 4, Minus: 4, Equal: 4,
  BracketLeft: 4, BracketRight: 4, Backslash: 4, Quote: 4,
  Enter: 4, Backspace: 4, ShiftRight: 4,
  // Zone 5 — right index
  KeyY: 5, KeyU: 5, KeyH: 5, KeyJ: 5, KeyN: 5, KeyM: 5, Digit6: 5, Digit7: 5,
  // Zone 6 — right middle
  KeyI: 6, KeyK: 6, Comma: 6, Digit8: 6,
  // Zone 7 — right ring
  KeyO: 7, KeyL: 7, Period: 7, Digit9: 7,
  // Zone 9 — thumbs: space + all modifiers
  Space: 9, ControlLeft: 9, ControlRight: 9, AltLeft: 9, AltRight: 9, MetaLeft: 9, MetaRight: 9,
};

/** Regex for zone 10 (special keys): arrows, F-keys, numpad, Escape, etc. */
const SPECIAL_ZONE_RE = /^(Arrow|F\d|Numpad|Escape|Delete|Insert|Home|End|Page)/;

// ─── Helpers ──────────────────────────────────────────────────────────────────

/**
 * Maps a KeyboardEvent.code to a finger-based zone number (0–10).
 * Returns -1 for unmapped codes.
 *
 * Lookup order:
 *   1. Direct match in ZONE_MAP (zones 0–9)
 *   2. Regex match for special keys (zone 10)
 *   3. Unmapped → -1
 */
function getKeyZone(code: string): number {
  if (!code) return -1;
  const z = ZONE_MAP[code];
  if (z !== undefined) return z;
  if (SPECIAL_ZONE_RE.test(code)) return 10;
  return -1;
}

/**
 * Creates a debounced version of fn — calls are coalesced into a single
 * call that fires `ms` after the last invocation.
 * No lodash dependency — hand-rolled per SDK_BEST_PRACTICES §3.1.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function debounce<T extends (...args: any[]) => void>(fn: T, ms: number): T {
  let timer: ReturnType<typeof setTimeout> | null = null;
  return ((...args: Parameters<T>) => {
    if (timer !== null) clearTimeout(timer);
    timer = setTimeout(() => {
      timer = null;
      fn(...args);
    }, ms);
  }) as T;
}

/**
 * Allocates and writes a 10-byte event buffer:
 *   [0] uint8  — signal type code
 *   [1] uint8  — zone index
 *   [2..9]     — float64 — timestamp (performance.now())
 */
function makeKeyBuffer(signalCode: number, zone: number, ts: number): ArrayBuffer {
  const buf = new ArrayBuffer(10);
  const view = new DataView(buf);
  view.setUint8(0, signalCode);
  view.setUint8(1, zone === -1 ? 255 : Math.min(Math.max(zone, 0), 254));
  view.setFloat64(2, ts, true); // little-endian
  return buf;
}

/**
 * Allocates and writes a 26-byte pointer event buffer:
 *   [0]    uint8   — signal type code
 *   [1]    uint8   — zone index
 *   [2..9] float64 — timestamp
 *   [10..17] float64 — vx (velocity x, normalized)
 *   [18..25] float64 — vy (velocity y, normalized)
 */
function makePointerBuffer(
  signalCode: number,
  zoneIndex: number,
  ts: number,
  vx: number,
  vy: number,
): ArrayBuffer {
  const buf = new ArrayBuffer(26);
  const view = new DataView(buf);
  view.setUint8(0, signalCode);
  view.setUint8(1, zoneIndex);
  view.setFloat64(2, ts, true);
  view.setFloat64(10, vx, true);
  view.setFloat64(18, vy, true);
  return buf;
}

/**
 * Allocates and writes a 10-byte scroll event buffer:
 *   [0]    uint8   — signal type code (SIGNAL_SC)
 *   [1]    uint8   — direction hint (0=unknown, 1=up, 2=down, 3=horizontal)
 *   [2..9] float64 — timestamp
 * Only direction metadata is captured — no absolute coordinates per §5.3.
 */
function makeScrollBuffer(ts: number, direction: number): ArrayBuffer {
  const buf = new ArrayBuffer(10);
  const view = new DataView(buf);
  view.setUint8(0, SIGNAL_SC);
  view.setUint8(1, direction);
  view.setFloat64(2, ts, true);
  return buf;
}

/**
 * Allocates and writes an 18-byte touch event buffer:
 *   [0]    uint8   — signal type code
 *   [1]    uint8   — touch count (number of active touches)
 *   [2..9] float64 — timestamp
 *   [10..17] float64 — contact area (normalized, 0–1)
 */
function makeTouchBuffer(signalCode: number, touchCount: number, ts: number, contactArea: number): ArrayBuffer {
  const buf = new ArrayBuffer(18);
  const view = new DataView(buf);
  view.setUint8(0, signalCode);
  view.setUint8(1, Math.min(touchCount, 255));
  view.setFloat64(2, ts, true);
  view.setFloat64(10, contactArea, true);
  return buf;
}

/**
 * Allocates and writes a 10-byte focus/blur event buffer:
 *   [0]    uint8   — signal type code (SIGNAL_FB)
 *   [1]    uint8   — 1=focus, 0=blur
 *   [2..9] float64 — timestamp
 */
function makeFocusBlurBuffer(isFocus: boolean, ts: number): ArrayBuffer {
  const buf = new ArrayBuffer(10);
  const view = new DataView(buf);
  view.setUint8(0, SIGNAL_FB);
  view.setUint8(1, isFocus ? 1 : 0);
  view.setFloat64(2, ts, true);
  return buf;
}

/** Reads `location.pathname` safely, returns '' on error. */
function safePatchname(): string {
  try {
    return location.pathname;
  } catch {
    return '';
  }
}

/** Reads a localStorage value safely, returns null on error. */
function safeLocalStorageGet(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

/** Writes to localStorage safely, silently drops on QuotaExceededError. */
function safeLocalStorageSet(key: string, value: string): void {
  try {
    localStorage.setItem(key, value);
  } catch {
    // QuotaExceededError or security restriction — degrade silently (§12.3).
  }
}

/** Deletes a localStorage key safely. */
function safeLocalStorageRemove(key: string): void {
  try {
    localStorage.removeItem(key);
  } catch {
    // Ignore — storage may be unavailable.
  }
}

/** Writes to sessionStorage safely. */
function safeSessionStorageSet(key: string, value: string): void {
  try {
    sessionStorage.setItem(key, value);
  } catch {
    // Ignore.
  }
}

/** Deletes a sessionStorage key safely. */
function safeSessionStorageRemove(key: string): void {
  try {
    sessionStorage.removeItem(key);
  } catch {
    // Ignore.
  }
}

// ─── Worker restart state ─────────────────────────────────────────────────────

/** Maximum number of worker restart attempts before falling back. */
const MAX_WORKER_RESTART_ATTEMPTS = 1;

// ─── MainThreadBridge ─────────────────────────────────────────────────────────

/**
 * MainThreadBridge — main-thread orchestrator.
 *
 * Instantiated once by `KProtect.init()`. Manages the full lifecycle of the
 * Web Worker, all DOM event listeners, username capture, and SPA routing.
 *
 * The bridge is the ONLY class that touches the DOM. Worker modules never
 * see DOM objects (SDK_BEST_PRACTICES §1.4).
 */
export class MainThreadBridge {
  private worker: Worker | null = null;
  private channel: MessageChannel | null = null;
  private fallback: MainThreadFallback | null = null;
  private usernameCapture: UsernameCapture | null = null;
  private readonly config: ResolvedConfig;
  private readonly handlers: Map<KProtectEventType, Set<(data: unknown) => void>> = new Map();
  private latestDrift: DriftScoreResponse | null = null;
  private latestState: SessionState | null = null;
  private destroyed = false;

  /** Cleanup functions for all registered event listeners. */
  private readonly unlisten: Array<() => void> = [];

  /** The worker bundle source string (blob URL content). */
  private workerSource = '';

  /** Number of restart attempts made after worker error. */
  private restartAttempts = 0;

  /** Cleanup function for the mutable-signal refresh interval. */
  private mutableRefreshCleanup: (() => void) | null = null;

  /** Last recorded pointer position for velocity computation. */
  private lastPointerX = 0;
  private lastPointerY = 0;
  private lastPointerTs = 0;

  /** Pending resolver for an audit log export request. */
  private auditLogResolve: ((entries: WireAuditEntry[]) => void) | null = null;

  /**
   * Pre-signed beacon payload for pagehide.
   * Refreshed on each STATE_UPDATE so the pagehide handler can send
   * a signed session_end beacon synchronously (no async crypto needed).
   */
  private cachedBeaconPayload: string | null = null;

  constructor(config: ResolvedConfig) {
    this.config = config;
    // Pre-populate handler sets.
    const types: KProtectEventType[] = [
      'drift', 'alert', 'critical_action', 'session_start', 'session_end', 'username_captured',
    ];
    for (const t of types) {
      this.handlers.set(t, new Set());
    }
  }

  // ─── Public API ─────────────────────────────────────────────────────────────

  /**
   * Starts the bridge.
   *
   * 1. Attempts to spawn a blob-URL Web Worker from `workerSource`.
   * 2. On failure, logs debug and switches to MainThreadFallback.
   * 3. Posts INIT message to the worker.
   * 4. Attaches all passive DOM event listeners.
   * 5. Starts username capture.
   * 6. Patches history for SPA route detection.
   *
   * @param workerSource  The worker bundle JS source as a string.
   *                      Inlined at build time by the Rollup plugin.
   */
  start(workerSource: string): void {
    if (this.destroyed) return;
    this.workerSource = workerSource;

    const spawned = this.spawnWorker(workerSource);
    if (!spawned) {
      this.startFallback(workerSource);
    }

    this.setupEventListeners();
    this.setupRouteListener();
    this.setupVisibilityListeners();
    this.startUsernameCapture();
    this.startFingerprintCollection();
    this.startMutableRefresh();
  }

  /**
   * Posts a message to the worker (or fallback).
   * No-ops if the bridge has been destroyed.
   *
   * @param msg  The typed MainToWorkerMsg to send.
   */
  postToWorker(msg: MainToWorkerMsg): void {
    if (this.destroyed) return;

    if (this.channel !== null) {
      try {
        // Transfer ArrayBuffer payloads for zero-copy (§1.4).
        if (msg.type === 'EVENT_TAP') {
          this.channel.port1.postMessage(msg, [msg.data]);
        } else {
          this.channel.port1.postMessage(msg);
        }
      } catch {
        // postMessage can throw if the worker has terminated — ignore.
      }
    } else if (this.fallback !== null) {
      this.fallback.postMessage(msg);
    }
  }

  /**
   * Registers a host-app event handler.
   *
   * @param event  The event type to listen for.
   * @param cb     Callback invoked with typed event data.
   * @returns      An unsubscribe function.
   */
  on(event: KProtectEventType, cb: (data: unknown) => void): () => void {
    const set = this.handlers.get(event);
    if (set) {
      set.add(cb);
      return () => { set.delete(cb); };
    }
    return () => {};
  }

  /** Returns the most recent DriftScoreResponse received from the worker. */
  getLatestDrift(): DriftScoreResponse | null {
    return this.latestDrift;
  }

  /** Returns the most recent SessionState snapshot from the worker. */
  getSessionState(): SessionState | null {
    return this.latestState;
  }

  /**
   * Exports the tamper-evident audit log from the worker (SOC 2 compliance).
   * Returns a promise that resolves with the audit entries, or an empty array
   * on timeout (5s) or if the bridge is destroyed.
   */
  exportAuditLog(): Promise<WireAuditEntry[]> {
    if (this.destroyed) return Promise.resolve([]);
    return new Promise((resolve) => {
      this.auditLogResolve = resolve;
      this.postToWorker({ type: 'EXPORT_AUDIT_LOG' });
      // Timeout after 5s — never hang the caller.
      setTimeout(() => {
        if (this.auditLogResolve) {
          this.auditLogResolve([]);
          this.auditLogResolve = null;
        }
      }, 5000);
    });
  }

  /**
   * Sends a LOGOUT message to the worker — clears username, ends session,
   * preserves device_uuid per SDK_BEST_PRACTICES §7.5.
   */
  logout(): void {
    this.postToWorker({ type: 'LOGOUT' });
  }

  /**
   * Kicks off async device fingerprint collection on the main thread.
   * When complete, posts the result to the worker via DEVICE_FINGERPRINT message.
   * Fire-and-forget — failures are silently ignored.
   */
  private startFingerprintCollection(): void {
    if (!this.config.fingerprinting.enabled) return;

    const run = () => {
      collectAllFingerprints()
        .then((fingerprint) => {
          this.postToWorker({ type: 'DEVICE_FINGERPRINT', fingerprint });
        })
        .catch(() => {
          // Fingerprint collection is best-effort — never block SDK init.
        });
    };

    if (typeof requestIdleCallback === 'function') {
      requestIdleCallback(() => run(), { timeout: 2000 });
    } else {
      setTimeout(run, 0);
    }
  }

  /**
   * Starts periodic re-collection of mutable signals (network, battery).
   * Posts MUTABLE_SIGNALS_UPDATE to the worker only when values change.
   * Stores the cleanup function for teardown in destroy().
   */
  private startMutableRefresh(): void {
    this.mutableRefreshCleanup = startMutableRefresh((msg) => this.postToWorker(msg));
  }

  /**
   * Tears down the bridge.
   *
   * 1. Posts DESTROY to the worker (optional identity wipe).
   * 2. Removes all DOM event listeners.
   * 3. Stops username capture.
   * 4. Terminates the worker.
   *
   * @param clearIdentity  When true, wipes device_uuid + username from storage.
   */
  destroy(clearIdentity: boolean): void {
    if (this.destroyed) return;
    this.destroyed = true;

    this.postToWorker({ type: 'DESTROY', clearIdentity });

    // Remove all DOM listeners.
    for (const unlisten of this.unlisten) {
      try { unlisten(); } catch { /* ignore */ }
    }
    this.unlisten.length = 0;

    // Stop mutable-signal refresh.
    this.mutableRefreshCleanup?.();
    this.mutableRefreshCleanup = null;

    // Stop username capture.
    try { this.usernameCapture?.stop(); } catch { /* ignore */ }

    // Close MessageChannel ports.
    try { this.channel?.port1.close(); } catch { /* ignore */ }
    this.channel = null;

    // Terminate worker.
    try { this.worker?.terminate(); } catch { /* ignore */ }
    this.worker = null;

    // Terminate fallback.
    try { this.fallback?.terminate(); } catch { /* ignore */ }
    this.fallback = null;
  }

  // ─── Private: worker lifecycle ───────────────────────────────────────────────

  /**
   * Attempts to spawn the blob-URL worker.
   * Returns true on success, false if Worker construction fails.
   */
  private spawnWorker(source: string): boolean {
    try {
      const blob = new Blob([source], { type: 'application/javascript' });
      const url = URL.createObjectURL(blob);
      this.worker = new Worker(url);
      // Release the object URL after the worker has loaded — it is no longer
      // needed once the Worker is constructed.
      URL.revokeObjectURL(url);

      // Use MessageChannel for secure, private communication.
      // Unlike worker.onmessage, MessageChannel ports cannot be intercepted
      // by other scripts on the page.
      this.channel = new MessageChannel();

      this.channel.port1.onmessage = (event: MessageEvent<WorkerToMainMsg>) => {
        this.handleWorkerMessage(event);
      };

      this.worker.onerror = (event: ErrorEvent) => {
        this.handleWorkerError(event);
      };

      // Transfer port2 to the worker — only the worker can use it.
      this.worker.postMessage(
        { type: 'PORT_INIT' },
        [this.channel.port2],
      );

      // Send INIT via the secure channel (port1).
      // Include location.origin for session origin binding (Finding 11).
      this.channel.port1.postMessage({
        type: 'INIT',
        config: this.config,
        origin: typeof location !== 'undefined' ? location.origin : undefined,
      } satisfies MainToWorkerMsg);

      return true;
    } catch {
      this.worker = null;
      this.channel = null;
      return false;
    }
  }

  /**
   * Routes a message from the worker to the appropriate handler and fires
   * any registered host-app event callbacks.
   */
  private handleWorkerMessage(event: MessageEvent<WorkerToMainMsg>): void {
    const msg = event.data;

    switch (msg.type) {
      case 'DRIFT_SCORE': {
        this.latestDrift = msg.response;
        this.fireHandlers('drift', msg.response);
        break;
      }
      case 'ALERT': {
        this.fireHandlers('alert', msg.alerts);
        break;
      }
      case 'SESSION_STARTED': {
        this.fireHandlers('session_start', { session_id: msg.session_id, pulse: msg.pulse });
        break;
      }
      case 'SESSION_ENDED': {
        this.fireHandlers('session_end', { session_id: msg.session_id, reason: msg.reason });
        break;
      }
      case 'CRITICAL_ACTION_RESULT': {
        this.fireHandlers('critical_action', msg.response);
        break;
      }
      case 'USERNAME_CAPTURED': {
        this.fireHandlers('username_captured', { user_hash: msg.user_hash });
        break;
      }
      case 'STATE_UPDATE': {
        this.latestState = msg.state;
        // Pre-sign the beacon payload for pagehide so it can be sent synchronously.
        void this.refreshBeaconPayload(msg.state);
        break;
      }
      case 'STORAGE_WRITE': {
        this.handleStorageWrite(msg.key, msg.value, msg.storage);
        break;
      }
      case 'AUDIT_LOG_EXPORT': {
        if (this.auditLogResolve) {
          this.auditLogResolve(msg.entries);
          this.auditLogResolve = null;
        }
        break;
      }
    }
  }

  /**
   * Writes or deletes a storage entry on behalf of the worker.
   * The worker manages IDB but mirrors keys to localStorage for cross-tab reads.
   */
  private handleStorageWrite(key: string, value: string | null, storage: 'local' | 'session'): void {
    if (storage === 'local') {
      if (value === null) {
        safeLocalStorageRemove(key);
      } else {
        safeLocalStorageSet(key, value);
      }
    } else {
      if (value === null) {
        safeSessionStorageRemove(key);
      } else {
        safeSessionStorageSet(key, value);
      }
    }
  }

  /**
   * Handles a worker error event.
   * Per §13.3: attempt one restart after 2s; if that fails, start fallback.
   */
  private handleWorkerError(_event: ErrorEvent): void {
    if (this.destroyed) return;

    try { this.channel?.port1.close(); } catch { /* ignore */ }
    this.channel = null;
    try { this.worker?.terminate(); } catch { /* ignore */ }
    this.worker = null;

    if (this.restartAttempts < MAX_WORKER_RESTART_ATTEMPTS) {
      this.restartAttempts += 1;
      setTimeout(() => {
        if (this.destroyed) return;
        const restarted = this.spawnWorker(this.workerSource);
        if (!restarted) {
          this.startFallback(this.workerSource);
        }
      }, 2000);
    } else {
      this.startFallback(this.workerSource);
    }
  }

  // ─── Private: fallback ───────────────────────────────────────────────────────

  /**
   * Starts the main-thread fallback scheduler.
   * Called when Worker construction fails or the worker crashes irrecoverably.
   * Logs once at debug level — never surfaces to the host app (§13.3).
   */
  private startFallback(_workerSource: string): void {
    if (this.destroyed) return;

    try {
      if (this.config.environment === 'debug') {
        // eslint-disable-next-line no-console
        console.debug('KProtect: worker unavailable, running in fallback mode');
      }

      this.fallback = new MainThreadFallback(
        this.config,
        (msg: WorkerToMainMsg) => {
          // Route fallback messages through the same handler as the worker.
          this.handleWorkerMessage({ data: msg } as MessageEvent<WorkerToMainMsg>);
        },
      );

      this.fallback.postMessage({
        type: 'INIT',
        config: this.config,
        origin: typeof location !== 'undefined' ? location.origin : undefined,
      });
    } catch {
      // Fallback itself failed — degrade silently (§13.1).
    }
  }

  // ─── Private: event listeners ────────────────────────────────────────────────

  /**
   * Attaches all passive DOM event listeners.
   *
   * Every listener is fire-and-forget: it encodes the raw event into an
   * ArrayBuffer and posts it to the worker. No feature extraction here.
   *
   * All listeners use `{ passive: true }` per §4.1.
   *
   * Critical-action click detection:
   *   Checks if the clicked element matches any commit selector. If so, posts
   *   CRITICAL_ACTION_COMMIT instead of EVENT_TAP.
   */
  private setupEventListeners(): void {
    // ── Keyboard ──────────────────────────────────────────────────────────────

    const onKeydown = (e: Event): void => {
      const ke = e as KeyboardEvent;
      const ts = performance.now();
      const zone = getKeyZone(ke.code);
      const buf = makeKeyBuffer(SIGNAL_KD, zone, ts);
      this.postToWorker({ type: 'EVENT_TAP', signal: 'kd', data: buf, ts });
    };

    const onKeyup = (e: Event): void => {
      const ke = e as KeyboardEvent;
      const ts = performance.now();
      const zone = getKeyZone(ke.code);
      const buf = makeKeyBuffer(SIGNAL_KU, zone, ts);
      this.postToWorker({ type: 'EVENT_TAP', signal: 'ku', data: buf, ts });
    };

    // ── Pointer ───────────────────────────────────────────────────────────────

    const onPointermoveRaw = (e: Event): void => {
      const pe = e as PointerEvent;
      const ts = performance.now();

      // Compute velocity from delta since last move — no absolute coords (§5.3).
      const dx = pe.clientX - this.lastPointerX;
      const dy = pe.clientY - this.lastPointerY;
      const dt = ts - this.lastPointerTs;
      const vx = dt > 0 ? dx / dt : 0;
      const vy = dt > 0 ? dy / dt : 0;

      this.lastPointerX = pe.clientX;
      this.lastPointerY = pe.clientY;
      this.lastPointerTs = ts;

      const buf = makePointerBuffer(SIGNAL_PM, 0, ts, vx, vy);
      this.postToWorker({ type: 'EVENT_TAP', signal: 'pm', data: buf, ts });
    };
    const onPointermove = debounce(onPointermoveRaw, 16);

    const onPointerdown = (e: Event): void => {
      const pe = e as PointerEvent;
      const ts = performance.now();
      this.lastPointerX = pe.clientX;
      this.lastPointerY = pe.clientY;
      this.lastPointerTs = ts;
      const buf = makePointerBuffer(SIGNAL_PD, 0, ts, 0, 0);
      this.postToWorker({ type: 'EVENT_TAP', signal: 'pd', data: buf, ts });
    };

    const onPointerup = (_e: Event): void => {
      const ts = performance.now();
      const buf = makePointerBuffer(SIGNAL_PU, 0, ts, 0, 0);
      this.postToWorker({ type: 'EVENT_TAP', signal: 'pu', data: buf, ts });
    };

    // ── Scroll ────────────────────────────────────────────────────────────────

    let prevScrollY = 0;
    try { prevScrollY = window.scrollY; } catch { /* worker-safe */ }

    const onScrollRaw = (_e: Event): void => {
      const ts = performance.now();
      let direction = 0; // 0=unknown
      try {
        const currentY = window.scrollY;
        if (currentY < prevScrollY) direction = 1;      // up
        else if (currentY > prevScrollY) direction = 2;  // down
        else direction = 3;                               // horizontal
        prevScrollY = currentY;
      } catch { /* fallback: direction stays 0 */ }
      const buf = makeScrollBuffer(ts, direction);
      this.postToWorker({ type: 'EVENT_TAP', signal: 'sc', data: buf, ts });
    };
    const onScroll = debounce(onScrollRaw, 16);

    // ── Touch ─────────────────────────────────────────────────────────────────

    const onTouchstart = (e: Event): void => {
      const te = e as TouchEvent;
      const ts = performance.now();
      const area = te.touches.length > 0 && (te.touches[0] as Touch & { radiusX?: number }).radiusX !== undefined
        ? Math.min(((te.touches[0] as Touch & { radiusX?: number }).radiusX ?? 0) / 50, 1)
        : 0;
      const buf = makeTouchBuffer(SIGNAL_TS, te.touches.length, ts, area);
      this.postToWorker({ type: 'EVENT_TAP', signal: 'ts', data: buf, ts });
    };

    const onTouchend = (e: Event): void => {
      const te = e as TouchEvent;
      const ts = performance.now();
      const buf = makeTouchBuffer(SIGNAL_TE, te.changedTouches.length, ts, 0);
      this.postToWorker({ type: 'EVENT_TAP', signal: 'te', data: buf, ts });
    };

    const onTouchmoveRaw = (e: Event): void => {
      const te = e as TouchEvent;
      const ts = performance.now();
      const buf = makeTouchBuffer(SIGNAL_TM, te.touches.length, ts, 0);
      this.postToWorker({ type: 'EVENT_TAP', signal: 'tm', data: buf, ts });
    };
    const onTouchmove = debounce(onTouchmoveRaw, 16);

    // ── Focus / Blur ──────────────────────────────────────────────────────────

    const onFocus = (_e: Event): void => {
      const ts = performance.now();
      const buf = makeFocusBlurBuffer(true, ts);
      this.postToWorker({ type: 'EVENT_TAP', signal: 'fb', data: buf, ts });
    };

    const onBlur = (_e: Event): void => {
      const ts = performance.now();
      const buf = makeFocusBlurBuffer(false, ts);
      this.postToWorker({ type: 'EVENT_TAP', signal: 'fb', data: buf, ts });
    };

    // ── Click — also handles critical-action commit detection ─────────────────

    const onClickRaw = (e: Event): void => {
      const ts = performance.now();
      const target = e.target;

      // Check for critical-action commit triggers.
      if (target instanceof Element) {
        for (const critAction of this.config.critical_actions.actions) {
          try {
            if (target.matches(critAction.commit.selector)) {
              this.postToWorker({
                type: 'CRITICAL_ACTION_COMMIT',
                action: critAction.action,
              });
              return; // Don't also post EVENT_TAP for commit clicks.
            }
          } catch {
            // Invalid CSS selector — skip.
          }
        }
      }

      const buf = makePointerBuffer(SIGNAL_CL, 0, ts, 0, 0);
      this.postToWorker({ type: 'EVENT_TAP', signal: 'cl', data: buf, ts });
    };

    // ── Register all listeners ────────────────────────────────────────────────

    this.addListener(document, 'keydown', onKeydown, { passive: true });
    this.addListener(document, 'keyup', onKeyup, { passive: true });
    this.addListener(document, 'pointermove', onPointermove as EventListener, { passive: true });
    this.addListener(document, 'pointerdown', onPointerdown, { passive: true });
    this.addListener(document, 'pointerup', onPointerup, { passive: true });
    this.addListener(document, 'scroll', onScroll as EventListener, { passive: true, capture: true });
    this.addListener(document, 'touchstart', onTouchstart, { passive: true });
    this.addListener(document, 'touchend', onTouchend, { passive: true });
    this.addListener(document, 'touchmove', onTouchmove as EventListener, { passive: true });
    // Focus/blur use capture phase to catch all elements.
    this.addListener(document, 'focus', onFocus, { passive: true, capture: true });
    this.addListener(document, 'blur', onBlur, { passive: true, capture: true });
    this.addListener(document, 'click', onClickRaw, { passive: true });
  }

  /**
   * Registers an event listener and stores a cleanup function for destroy().
   */
  private addListener(
    target: EventTarget,
    type: string,
    handler: EventListener,
    options: AddEventListenerOptions,
  ): void {
    try {
      target.addEventListener(type, handler, options);
      this.unlisten.push(() => {
        try {
          target.removeEventListener(type, handler, options);
        } catch { /* ignore */ }
      });
    } catch {
      // addEventListener can fail (e.g. detached document) — degrade silently.
    }
  }

  // ─── Private: SPA routing ────────────────────────────────────────────────────

  /**
   * Patches `history.pushState` and `history.replaceState` to intercept SPA
   * navigation events, and listens to `popstate`.
   *
   * Per SDK_BEST_PRACTICES §9.2 — sends ROUTE_CHANGE to the worker on every
   * navigation so PageGate can reclassify the page.
   */
  private setupRouteListener(): void {
    const notifyRouteChange = (): void => {
      if (this.destroyed) return;
      const path = safePatchname();
      this.postToWorker({ type: 'ROUTE_CHANGE', path });
      // Notify username capture so it re-polls SSO globals.
      try { this.usernameCapture?.onRouteChange(path); } catch { /* ignore */ }
    };

    // Patch pushState.
    try {
      const originalPushState = history.pushState.bind(history);
      history.pushState = (...args: Parameters<typeof history.pushState>): void => {
        originalPushState(...args);
        notifyRouteChange();
      };
      this.unlisten.push(() => {
        try { history.pushState = originalPushState; } catch { /* ignore */ }
      });
    } catch {
      // history.pushState may not be available (non-browser env) — skip.
    }

    // Patch replaceState.
    try {
      const originalReplaceState = history.replaceState.bind(history);
      history.replaceState = (...args: Parameters<typeof history.replaceState>): void => {
        originalReplaceState(...args);
        notifyRouteChange();
      };
      this.unlisten.push(() => {
        try { history.replaceState = originalReplaceState; } catch { /* ignore */ }
      });
    } catch {
      // Skip if unavailable.
    }

    // Listen to popstate (browser back/forward).
    this.addListener(window, 'popstate', notifyRouteChange as EventListener, { passive: true });
  }

  // ─── Private: visibility + pagehide ──────────────────────────────────────────

  /**
   * Attaches visibility and pagehide listeners.
   *
   * visibilitychange:
   *   Posts VISIBILITY_CHANGE to the worker with the new visible state.
   *
   * pagehide (persisted=false):
   *   Sends a session_end beacon via navigator.sendBeacon so the server
   *   receives a clean close even when the page is being discarded.
   */
  private setupVisibilityListeners(): void {
    const onVisibilityChange = (): void => {
      if (this.destroyed) return;
      let visible = true;
      try {
        visible = document.visibilityState === 'visible';
      } catch { /* default to visible */ }
      this.postToWorker({ type: 'VISIBILITY_CHANGE', visible });
    };

    const onPagehide = (e: Event): void => {
      if (this.destroyed) return;
      const pe = e as PageTransitionEvent;
      // Only send session_end beacon when the page is truly being discarded
      // (persisted=false means it won't enter the bfcache).
      if (pe.persisted) return;

      const sessionId = this.latestState?.session_id;
      if (!sessionId) return;

      try {
        const endpoint = this.config.transport.endpoint;

        // Use the pre-signed beacon payload if available (signed during
        // the last STATE_UPDATE via refreshBeaconPayload). This avoids
        // async crypto in the synchronous pagehide handler.
        // Falls back to unsigned payload if signing was unavailable.
        if (this.cachedBeaconPayload) {
          navigator.sendBeacon(endpoint, this.cachedBeaconPayload);
        } else {
          // Fallback: unsigned payload (crypto.subtle was unavailable).
          const payload = JSON.stringify({
            type: 'session_end',
            api_key_id: this.config.api_key.substring(0, 12),
            session_id: sessionId,
            sent_at: Date.now(),
            end_reason: 'pagehide',
            unsigned: true,
          });
          navigator.sendBeacon(endpoint, payload);
        }
      } catch {
        // sendBeacon may be unavailable or fail — degrade silently.
      }
    };

    this.addListener(document, 'visibilitychange', onVisibilityChange as EventListener, { passive: true });
    this.addListener(window, 'pagehide', onPagehide as EventListener, { passive: true });
  }

  // ─── Private: beacon payload pre-signing ─────────────────────────────────────

  /**
   * Pre-signs a session_end beacon payload using the API key so the pagehide
   * handler can send it synchronously without needing async crypto.
   *
   * Called on every STATE_UPDATE. The signed payload includes the current
   * session_id and a fresh batch_id + timestamp. The server verifies the
   * embedded HMAC-SHA256 signature from the body (since sendBeacon cannot
   * set custom headers).
   */
  private async refreshBeaconPayload(state: SessionState): Promise<void> {
    if (!state.session_id) {
      this.cachedBeaconPayload = null;
      return;
    }

    try {
      let batchId: string;
      try {
        batchId = crypto.randomUUID();
      } catch {
        batchId = `${Date.now().toString()}-${Math.random().toString(36).slice(2)}`;
      }

      const batch = {
        type: 'session_end' as const,
        batch_id: batchId,
        session_id: state.session_id,
        sent_at: Date.now(),
        end_reason: 'pagehide' as const,
      };

      const signed = await createSignedBeaconPayload(batch, this.config.api_key);
      this.cachedBeaconPayload = JSON.stringify(signed);
    } catch {
      // Signing failed — pagehide will fall back to unsigned payload.
      this.cachedBeaconPayload = null;
    }
  }

  // ─── Private: username capture ───────────────────────────────────────────────

  /**
   * Initialises and starts the UsernameCapture instance.
   *
   * When a username is found:
   *   1. Posts USERNAME_CAPTURED (user_hash only) to the worker.
   *   2. Stores the raw username in localStorage via the worker's STORAGE_WRITE
   *      path — the raw value is NOT sent to the worker directly.
   */
  private startUsernameCapture(): void {
    if (this.destroyed) return;
    try {
      this.usernameCapture = new UsernameCapture(
        this.config,
        (user_hash: string, _raw_username: string) => {
          // Only the hash crosses the thread boundary (§5.2).
          this.postToWorker({ type: 'USERNAME_CAPTURED', user_hash });
        },
      );
      this.usernameCapture.start();
    } catch {
      // Username capture is non-critical — degrade silently (§13.4).
    }
  }

  // ─── Private: helpers ────────────────────────────────────────────────────────

  /** Fires all registered callbacks for the given event type. */
  private fireHandlers(event: KProtectEventType, data: unknown): void {
    const set = this.handlers.get(event);
    if (!set) return;
    for (const cb of set) {
      try { cb(data); } catch { /* host-app callback threw — isolate (§13.1) */ }
    }
  }
}

// Re-export for use by callers that only need the storage-key constants.
export { safeLocalStorageGet };
