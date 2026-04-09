/**
 * session-manager.ts
 *
 * Manages the session lifecycle: session_id minting, pulse loop, idle timeout,
 * page-class cadence switching, and visibility gating.
 *
 * Runs inside the Web Worker.
 *
 * SDK_BEST_PRACTICES §7 (Session Lifecycle), §8 (Pulse Contract).
 */

import type {
  ResolvedConfig,
  WorkerToMainMsg,
  SessionEndReason,
  PageClass,
  CriticalAction,
  SessionState,
  SessionPhase,
  LivenessStatus,
} from '../runtime/wire-protocol.js';
import type { IdentityStore } from './identity-store.js';
import { LIVENESS_STALE_THRESHOLD_MS } from '../config/defaults.js';
import { sha256 } from '../signals/crypto-utils.js';

// Re-export so callers can import the type without hitting wire-protocol directly.
export type { SessionPhase };

// ─── SessionManager ────────────────────────────────────────────────────────────

/**
 * SessionManager — central coordinator for session state in the worker.
 *
 * Responsibilities:
 * - Mints a new `session_id` (UUID) on `start()`.
 * - Runs the pulse loop via `setInterval`, switching between normal and
 *   keepalive cadences based on page class.
 * - Tracks visibility and idles out after `idle_timeout_ms` of hidden state.
 * - Notifies the main thread via SESSION_STARTED / SESSION_ENDED messages.
 * - Provides a `getSessionState()` snapshot for STATE_UPDATE messages.
 */
export class SessionManager {
  private readonly config: ResolvedConfig;
  private readonly identityStore: IdentityStore;
  private readonly postToMain: (msg: WorkerToMainMsg) => void;
  private readonly onPulse: (phase: 'normal' | 'keepalive') => void;
  private readonly onIdle: () => void;

  // ── Runtime state ──────────────────────────────────────────────────────────

  private sessionId: string | null = null;
  private pulse: number = 0;
  private phase: SessionPhase = 'uninitialised';
  private pageClass: PageClass = 'normal';
  private currentAction: string | null = null;

  /** true while the tab is visible. */
  private isVisible: boolean = true;

  /**
   * true while username has not yet been captured —
   * the pulse loop ticks but onPulse is suppressed.
   */
  private preIdentity: boolean = true;

  /** The currently active pulse interval handle (normal or keepalive). */
  private intervalHandle: ReturnType<typeof setInterval> | null = null;

  /** Idle timeout handle — set when tab goes hidden. */
  private idleTimerHandle: ReturnType<typeof setTimeout> | null = null;

  /** Accumulated pulses missed while paused (for catch-up on resume). */
  private pausedPulseAccumulator: number = 0;

  /** Origin string received from the main thread (e.g. 'https://bank.example.com'). */
  private origin: string | null = null;

  /** SHA-256(session_id + origin) — binds this session to its origin (Finding 11). */
  private originHash: string | null = null;

  /** Timestamp of the last event received (for liveness detection). */
  private lastEventAt: number = 0;

  /** Liveness stale warning timer handle. */
  private livenessTimerHandle: ReturnType<typeof setTimeout> | null = null;

  constructor(
    config: ResolvedConfig,
    identityStore: IdentityStore,
    postToMain: (msg: WorkerToMainMsg) => void,
    onPulse: (phase: 'normal' | 'keepalive') => void,
    onIdle: () => void,
    origin?: string,
  ) {
    this.config = config;
    this.identityStore = identityStore;
    this.postToMain = postToMain;
    this.onPulse = onPulse;
    this.onIdle = onIdle;
    this.origin = origin ?? null;
  }

  // ─── Public API ────────────────────────────────────────────────────────────

  /**
   * Starts a new session.
   * - Mints a new session_id via crypto.randomUUID().
   * - Computes origin_hash = SHA-256(session_id + origin) for origin binding.
   * - Resets pulse counter to 0.
   * - Starts the pulse loop.
   * - Posts SESSION_STARTED to the main thread.
   */
  async start(): Promise<void> {
    // Mint session ID.
    try {
      this.sessionId = crypto.randomUUID();
    } catch {
      // Fallback: high-resolution timestamp + random suffix.
      this.sessionId = `${performance.now().toFixed(0)}-${Math.random()
        .toString(36)
        .slice(2)}`;
    }

    // Compute origin_hash for session origin binding (Finding 11).
    this.originHash = await this.computeOriginHash(this.sessionId);

    this.pulse = 0;
    this.phase = 'active';
    this.preIdentity = !this.identityStore.isIdentityCaptured();

    this.pausedPulseAccumulator = 0;

    this.startPulseLoop();

    this.postToMain({
      type: 'SESSION_STARTED',
      session_id: this.sessionId,
      pulse: this.pulse,
    });
  }

  /**
   * Ends the current session.
   * - Clears the pulse loop.
   * - Clears the idle timer.
   * - Posts SESSION_ENDED to the main thread.
   * - Transitions phase to 'ended'.
   *
   * @param reason  Why the session ended.
   */
  end(reason: SessionEndReason): void {
    this.clearPulseLoop();
    this.clearIdleTimer();
    this.clearLivenessTimer();

    const sid = this.sessionId;
    this.phase = 'ended';

    if (sid !== null) {
      this.postToMain({
        type: 'SESSION_ENDED',
        session_id: sid,
        reason,
      });
    }
  }

  /**
   * Called when the page visibility changes.
   *
   * visible=false:
   *   - Pauses the pulse loop (ticks are suppressed).
   *   - Starts the idle timeout timer.
   *
   * visible=true:
   *   - Cancels the idle timer.
   *   - Fires one immediate catch-up onPulse (if identity is captured and
   *     page class is not opted_out).
   *   - Resumes normal ticking.
   *
   * @param visible  Whether the page has become visible.
   */
  async setVisibility(visible: boolean): Promise<void> {
    const wasVisible = this.isVisible;
    this.isVisible = visible;


    if (!visible) {
      // Going hidden — start idle timer.
      this.clearIdleTimer();
      this.idleTimerHandle = setTimeout(() => {
        this.phase = 'idle';
        this.onIdle();
        this.end('idle_timeout');
      }, this.config.session.idle_timeout_ms);
      this.phase = 'idle';
    } else {
      // Coming back visible.
      this.clearIdleTimer();

      // ── Origin binding validation (Finding 11) ────────────────────────────
      // Re-derive the origin_hash and compare against the stored value.
      // A mismatch indicates potential session hijacking from a different origin.
      if (!wasVisible && this.sessionId && this.originHash && this.origin) {
        const freshHash = await this.computeOriginHash(this.sessionId);
        if (freshHash !== null && freshHash !== this.originHash) {
          // Origin mismatch — force new session (potential hijack).
          this.end('origin_mismatch');
          await this.start();
          return;
        }
      }

      this.phase = this.sessionId ? 'active' : 'uninitialised';

      // Fire a catch-up pulse immediately if conditions allow.
      if (!wasVisible && this.sessionId && this.shouldFirePulse()) {
        this.firePulse();
      }
    }
  }

  /**
   * Called when the page class changes (SPA navigation / PageGate update).
   *
   * - 'critical_action': switches to keepalive cadence.
   * - 'normal':          switches back to normal cadence.
   * - 'opted_out':       pauses all pulse loops.
   *
   * @param pageClass  New page classification.
   * @param action     Current critical action definition (may be null).
   */
  setPageClass(pageClass: PageClass, action: CriticalAction | null = null): void {
    const changed = pageClass !== this.pageClass;
    this.pageClass = pageClass;
    this.currentAction = action ? action.action : null;

    if (!changed) return;

    // Re-start the interval with the new cadence.
    this.clearPulseLoop();
    if (pageClass !== 'opted_out') {
      this.startPulseLoop();
    }
  }

  /**
   * Called when the username has been captured and identity is established.
   * Unblocks real pulse transmissions and drains any accumulated state.
   */
  onUsernameCapture(): void {
    this.preIdentity = false;


    // Fire an immediate catch-up pulse to drain the pre-identity window.
    if (this.sessionId && this.shouldFirePulse()) {
      this.firePulse();
    }
  }

  /** Returns the current session ID, or null before start() is called. */
  getSessionId(): string | null {
    return this.sessionId;
  }

  /** Returns the current pulse counter. */
  getPulse(): number {
    return this.pulse;
  }

  /** Returns the current session lifecycle phase. */
  getPhase(): SessionPhase {
    return this.phase;
  }

  /** Returns the current origin_hash, or null if no origin was provided. */
  getOriginHash(): string | null {
    return this.originHash;
  }

  /**
   * Updates the origin string. Used when the worker receives an origin
   * update (e.g. for testing or if origin was not available at construction).
   */
  setOrigin(origin: string): void {
    this.origin = origin;
  }

  /**
   * Records an event reception — updates the liveness timestamp.
   * Called by the worker message router on each EVENT_TAP.
   */
  recordEvent(): void {
    this.lastEventAt = Date.now();
    this.resetLivenessTimer();
  }

  /**
   * Returns true when events have been received recently (within stale threshold).
   * Returns false if the session is ended or no events have ever been received.
   */
  isAlive(): boolean {
    if (this.phase === 'ended' || this.phase === 'uninitialised') return false;
    if (this.lastEventAt === 0) return false;
    return (Date.now() - this.lastEventAt) < LIVENESS_STALE_THRESHOLD_MS;
  }

  /** Returns the current liveness status. */
  getLivenessStatus(): LivenessStatus {
    if (this.phase === 'ended') return 'dead';
    if (this.phase === 'uninitialised') return 'dead';
    if (this.lastEventAt === 0) return 'stale';
    return (Date.now() - this.lastEventAt) < LIVENESS_STALE_THRESHOLD_MS
      ? 'alive'
      : 'stale';
  }

  /**
   * Returns a full immutable snapshot of the current session state.
   * Used by the worker's STATE_UPDATE emitter.
   */
  getSessionState(): SessionState {
    return {
      phase: this.phase,
      session_id: this.sessionId,
      pulse: this.pulse,
      identity_captured: this.identityStore.isIdentityCaptured(),
      page_class: this.pageClass,
      current_action: this.currentAction,
      // These fields are managed by outer layers; set to 0/null as defaults.
      transport_queue_depth: 0,
      ring_buffer_depth: 0,
      last_drift_score: null,
      last_action: null,
      liveness_status: this.getLivenessStatus(),
      origin_hash: this.originHash,
    };
  }

  // ─── Private helpers ───────────────────────────────────────────────────────

  /**
   * Derives SHA-256(session_id + origin) for session origin binding (Finding 11).
   * Returns null if no origin is configured or if crypto.subtle is unavailable.
   */
  private async computeOriginHash(sessionId: string): Promise<string | null> {
    if (!this.origin) return null;
    try {
      return await sha256(sessionId + this.origin);
    } catch {
      return null;
    }
  }

  /**
   * Starts the pulse interval with the cadence appropriate for the current
   * page class. Only one interval runs at a time.
   */
  private startPulseLoop(): void {
    this.clearPulseLoop();

    const intervalMs =
      this.pageClass === 'critical_action'
        ? this.config.session.keepalive_interval_ms
        : this.config.session.pulse_interval_ms;

    this.intervalHandle = setInterval(() => {
      this.onTick();
    }, intervalMs);
  }

  /** Clears the active pulse interval, if any. */
  private clearPulseLoop(): void {
    if (this.intervalHandle !== null) {
      clearInterval(this.intervalHandle);
      this.intervalHandle = null;
    }
  }

  /**
   * Resets the liveness stale timer. When it fires (no events for LIVENESS_STALE_THRESHOLD_MS),
   * emits a STATE_UPDATE with liveness_status='stale'.
   */
  private resetLivenessTimer(): void {
    if (this.livenessTimerHandle !== null) {
      clearTimeout(this.livenessTimerHandle);
    }
    this.livenessTimerHandle = setTimeout(() => {
      if (this.phase === 'active') {
        // Emit stale warning via state update.
        this.postToMain({
          type: 'STATE_UPDATE',
          state: this.getSessionState(),
        });
      }
    }, LIVENESS_STALE_THRESHOLD_MS);
  }

  /** Clears the liveness timer, if any. */
  private clearLivenessTimer(): void {
    if (this.livenessTimerHandle !== null) {
      clearTimeout(this.livenessTimerHandle);
      this.livenessTimerHandle = null;
    }
  }

  /** Clears the idle timeout timer, if any. */
  private clearIdleTimer(): void {
    if (this.idleTimerHandle !== null) {
      clearTimeout(this.idleTimerHandle);
      this.idleTimerHandle = null;
    }
  }

  /**
   * Interval tick handler.
   * Increments the pulse counter and calls onPulse when all gating conditions
   * are met; otherwise increments the paused accumulator.
   */
  private onTick(): void {


    if (!this.shouldFirePulse()) {
      this.pausedPulseAccumulator += 1;
      return;
    }

    this.firePulse();
  }

  /**
   * Fires a single pulse — increments the counter and calls the onPulse
   * callback with the correct phase label.
   */
  private firePulse(): void {
    this.pulse += 1;
    this.pausedPulseAccumulator = 0;

    const pulsePhase: 'normal' | 'keepalive' =
      this.pageClass === 'critical_action' ? 'keepalive' : 'normal';

    this.onPulse(pulsePhase);
  }

  /**
   * Returns true when all gating conditions for firing a real pulse are met:
   * - Session is active (sessionId minted).
   * - Tab is visible.
   * - Page class is not opted_out.
   * - Identity has been captured (username known).
   */
  private shouldFirePulse(): boolean {
    return (
      this.sessionId !== null &&
      this.isVisible &&
      this.pageClass !== 'opted_out' &&
      !this.preIdentity
    );
  }
}
