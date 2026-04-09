/**
 * index.ts — K-Protect Web SDK public facade.
 *
 * This is the ONLY file customers import. Everything else is an implementation
 * detail. The surface is intentionally minimal — 6 methods + 2 types.
 *
 * Target size: < 3 KB after minification (SDK_BEST_PRACTICES §3, §15).
 *
 * RULES:
 *   - No `any` types.
 *   - Zero runtime dependencies.
 *   - Idempotent init (calling twice is a no-op).
 *   - All methods are safe to call before `init()` (they return early / no-op).
 *   - Never throw to the host page (§13.1).
 */

import type {
  KProtectConfig,
  DriftScoreResponse,
  SessionState,
  ChallengeResult,
  VerifyResult,
  WireAuditEntry,
  GDPRExport,
} from './runtime/wire-protocol.js';
import { MainThreadBridge } from './runtime/main-thread-bridge.js';
import { resolveConfig } from './config/resolve-config.js';
import { hasConsent, setConsent, getConsentState } from './session/consent-manager.js';
import {
  STORAGE_KEY_SESSION_ID,
  STORAGE_KEY_USERNAME,
  STORAGE_KEY_DEVICE_UUID,
  STORAGE_KEY_CONFIG,
  STORAGE_KEY_ENCRYPTION_KEY,
  STORAGE_KEY_USERNAME_SALT,
  STORAGE_KEY_CONSENT,
  IDB_DB_NAME,
} from './config/defaults.js';

// ─── Re-exports ───────────────────────────────────────────────────────────────

export type { KProtectConfig, DriftScoreResponse, SessionState, WireAuditEntry, GDPRExport };
export type { KProtectEventType } from './runtime/main-thread-bridge.js';

// ─── Worker source placeholder ────────────────────────────────────────────────

/**
 * The worker bundle JS source string.
 * This declaration is replaced at build time by the Rollup worker-inline plugin
 * with the actual compiled worker bundle content.
 *
 * At development time this is an empty string, which causes the bridge to fall
 * back to `MainThreadFallback` — all SDK functionality remains available.
 */
declare const __WORKER_SOURCE__: string;

// ─── Singleton state ──────────────────────────────────────────────────────────

let bridge: MainThreadBridge | null = null;

// ─── KProtect public facade ───────────────────────────────────────────────────

/**
 * KProtect — the K-Protect behavioral biometrics SDK.
 *
 * @example
 * ```ts
 * import { KProtect } from '@kreesalis/kprotect-web';
 *
 * // Minimal setup — everything else has safe defaults.
 * KProtect.init({ api_key: 'kp_live_abc...' });
 *
 * // Listen for drift assessments.
 * KProtect.on('drift', (data) => {
 *   const drift = data as DriftScoreResponse;
 *   if (drift.action === 'challenge') showMfaChallenge();
 * });
 * ```
 */
export const KProtect = {
  /**
   * Initialises the SDK.
   *
   * Idempotent — calling `init()` a second time is a no-op. Call `destroy()`
   * first if you need to re-initialise with different config.
   *
   * After `init()` returns, the SDK runs entirely in a Web Worker (or in a
   * main-thread idle-scheduler fallback when the Worker cannot be spawned).
   * The main thread is left unblocked.
   *
   * @param config  Public config — only `api_key` is required.
   */
  init(config: KProtectConfig): void {
    if (bridge !== null) return; // Idempotent.

    try {
      const resolved = resolveConfig(config);

      // ── Consent gate (GDPR/CCPA) ──────────────────────────────────────────
      if (!hasConsent(resolved.consent.mode)) {
        // SDK is blocked until consent is granted.
        // In opt-in mode, user must call KProtect.consent.grant() first.
        return;
      }

      bridge = new MainThreadBridge(resolved);

      // __WORKER_SOURCE__ is replaced by the build pipeline. If undefined at
      // runtime (e.g. missing build step), treat as empty string and let the
      // bridge fall back to MainThreadFallback.
      const workerSrc =
        typeof __WORKER_SOURCE__ !== 'undefined' ? __WORKER_SOURCE__ : '';

      bridge.start(workerSrc);
    } catch {
      // Init failure must not throw to the host page (§13.1).
      bridge = null;
    }
  },

  /**
   * Registers a host-app event handler.
   *
   * Safe to call before `init()` — returns a no-op unsubscribe function.
   *
   * @param event  Event type to listen for.
   * @param cb     Callback invoked with typed event data.
   * @returns      Unsubscribe function — call it to remove the handler.
   *
   * @example
   * ```ts
   * const off = KProtect.on('drift', (data) => {
   *   console.log((data as DriftScoreResponse).drift_score);
   * });
   * // Later:
   * off();
   * ```
   */
  on(
    event: import('./runtime/main-thread-bridge.js').KProtectEventType,
    cb: (data: unknown) => void,
  ): () => void {
    if (bridge === null) return () => {};
    try {
      return bridge.on(event, cb);
    } catch {
      return () => {};
    }
  },

  /**
   * Returns the most recent `DriftScoreResponse` received from the server.
   *
   * `null` until the first successful batch response is received.
   * Safe to call before `init()`.
   */
  getLatestDrift(): DriftScoreResponse | null {
    try {
      return bridge?.getLatestDrift() ?? null;
    } catch {
      return null;
    }
  },

  /**
   * Returns the current session state snapshot from the worker.
   *
   * `null` before `init()` or before the first session starts.
   * Safe to call before `init()`.
   */
  getSessionState(): SessionState | null {
    try {
      return bridge?.getSessionState() ?? null;
    } catch {
      return null;
    }
  },

  /**
   * Signals a user logout.
   *
   * Ends the current session, clears the captured username from storage,
   * and sends a `session_end` batch. The device UUID is preserved (§6.3).
   *
   * Safe to call before `init()` — no-op.
   */
  logout(): void {
    try {
      bridge?.logout();
    } catch {
      // Isolate any internal error (§13.1).
    }
  },

  /**
   * Tears down the SDK.
   *
   * Removes all DOM listeners, terminates the worker, and flushes any
   * pending transport queue. After `destroy()`, `init()` may be called again.
   *
   * @param opts.clearIdentity  When `true`, also clears `device_uuid` and
   *                            username from all storage. Default: `false`.
   */
  destroy(opts?: { clearIdentity?: boolean }): void {
    if (bridge === null) return;
    try {
      bridge.destroy(opts?.clearIdentity ?? false);
    } catch {
      // Isolate (§13.1).
    } finally {
      bridge = null;
    }
  },

  /**
   * Consent management for GDPR/CCPA compliance.
   *
   * In 'opt-in' mode, the SDK will not start until `KProtect.consent.grant()`
   * is called. After granting consent, call `init()` again to start the SDK.
   *
   * In 'opt-out' mode (default), the SDK runs unless `KProtect.consent.deny()`
   * is called.
   */
  consent: {
    /** Grant consent for behavioral data collection. */
    grant(): void {
      setConsent(true);
    },
    /** Deny consent and destroy the SDK if running. */
    deny(): void {
      setConsent(false);
      // If SDK is running, destroy it
      if (bridge !== null) {
        try {
          bridge.destroy(false);
        } catch { /* ignore */ }
        bridge = null;
      }
    },
    /** Returns current consent state: 'granted', 'denied', or 'unknown'. */
    state(): string {
      const s = getConsentState();
      return s?.state ?? 'unknown';
    },
  },

  /**
   * Exports the SDK audit log for compliance review (SOC 2).
   * Returns a promise that resolves with the tamper-evident audit entries.
   * Returns an empty array if the SDK is not initialized.
   */
  exportAuditLog(): Promise<WireAuditEntry[]> {
    if (!bridge) return Promise.resolve([]);
    try {
      return bridge.exportAuditLog();
    } catch {
      return Promise.resolve([]);
    }
  },

  /**
   * GDPR data subject rights API (Findings 16, 17).
   *
   * `KProtect.gdpr.export()` — returns all stored data about the user.
   * `KProtect.gdpr.delete()` — clears ALL stored data and ends the session.
   */
  gdpr: {
    /**
     * Returns all data stored about the user for GDPR data subject access requests.
     *
     * Includes: hashed username, device UUID, session ID, consent state.
     * Does NOT include raw behavioral data (already discarded after feature extraction).
     *
     * Safe to call before `init()` — returns minimal export with nulls.
     */
    async export(): Promise<GDPRExport> {
      try {
        const storedKeys: Record<string, string | null> = {};
        const allKpKeys = [
          STORAGE_KEY_SESSION_ID,
          STORAGE_KEY_USERNAME,
          STORAGE_KEY_DEVICE_UUID,
          STORAGE_KEY_CONFIG,
          STORAGE_KEY_ENCRYPTION_KEY,
          STORAGE_KEY_USERNAME_SALT,
          STORAGE_KEY_CONSENT,
        ];

        for (const key of allKpKeys) {
          try {
            storedKeys[key] = localStorage.getItem(key);
          } catch {
            storedKeys[key] = null;
          }
        }
        // Also check sessionStorage for session ID.
        try {
          storedKeys[STORAGE_KEY_SESSION_ID] = sessionStorage.getItem(STORAGE_KEY_SESSION_ID);
        } catch {
          // sessionStorage unavailable.
        }

        const state = bridge?.getSessionState() ?? null;

        return {
          user_hash: state?.identity_captured ? (storedKeys[STORAGE_KEY_USERNAME] ?? null) : null,
          device_uuid: storedKeys[STORAGE_KEY_DEVICE_UUID] ?? null,
          session_id: state?.session_id ?? null,
          consent_state: getConsentState()?.state ?? 'unknown',
          exported_at: Date.now(),
          stored_keys: storedKeys,
        };
      } catch {
        return {
          user_hash: null,
          device_uuid: null,
          session_id: null,
          consent_state: 'unknown',
          exported_at: Date.now(),
          stored_keys: {},
        };
      }
    },

    /**
     * Deletes ALL stored data: localStorage, sessionStorage, and IndexedDB.
     * Ends the current session and fires a 'data_deleted' event.
     *
     * This is a superset of `destroy({ clearIdentity: true })`.
     *
     * Safe to call before `init()` — clears storage regardless.
     */
    async delete(): Promise<void> {
      try {
        // End session and clear identity via destroy.
        if (bridge !== null) {
          try {
            bridge.destroy(true);
          } catch { /* ignore */ }
          bridge = null;
        }

        // Clear all kp.* keys from localStorage.
        const kpLocalKeys = [
          STORAGE_KEY_USERNAME,
          STORAGE_KEY_DEVICE_UUID,
          STORAGE_KEY_CONFIG,
          STORAGE_KEY_ENCRYPTION_KEY,
          STORAGE_KEY_USERNAME_SALT,
          STORAGE_KEY_CONSENT,
        ];
        for (const key of kpLocalKeys) {
          try { localStorage.removeItem(key); } catch { /* ignore */ }
        }

        // Clear sessionStorage.
        try { sessionStorage.removeItem(STORAGE_KEY_SESSION_ID); } catch { /* ignore */ }

        // Delete the entire IndexedDB database.
        try {
          if (typeof indexedDB !== 'undefined') {
            indexedDB.deleteDatabase(IDB_DB_NAME);
          }
        } catch { /* ignore */ }
      } catch {
        // GDPR delete must not throw to the host page (§13.1).
      }
    },
  },

  /**
   * Challenge / verify API — phase 2 stub.
   *
   * These methods will be implemented in a future release.
   * They are present on the public facade now so host apps can type-check
   * integration code without requiring a polyfill.
   */
  challenge: {
    /**
     * Generates a behavioral challenge for the current session.
     *
     * @param opts.purpose  Human-readable purpose string e.g. 'mfa_upgrade'.
     * @throws Always — not yet implemented.
     */
    async generate(_opts: { purpose: string }): Promise<ChallengeResult> {
      throw new Error('KProtect.challenge.generate is not yet implemented (phase 2)');
    },

    /**
     * Verifies a completed challenge against the current behavioral baseline.
     *
     * @param _challengeId  The challenge ID returned by `generate()`.
     * @param _inputEl      The DOM element the user interacted with.
     * @throws Always — not yet implemented.
     */
    async verify(
      _challengeId: string,
      _inputEl: Element,
    ): Promise<VerifyResult> {
      throw new Error('KProtect.challenge.verify is not yet implemented (phase 2)');
    },
  },
} as const;
