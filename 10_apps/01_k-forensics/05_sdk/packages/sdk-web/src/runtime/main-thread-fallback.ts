/**
 * main-thread-fallback.ts
 *
 * CSP / compat fallback: runs the worker-side message handlers on the main
 * thread via `requestIdleCallback` (or `setTimeout(fn, 0)` where rIC is
 * unavailable).
 *
 * Activated when `new Worker(blobUrl)` throws — typically because:
 *   - The page CSP lacks `worker-src blob:`.
 *   - The browser does not support Web Workers (rare, but handled).
 *
 * This is a thin adapter: it delegates to the same `createWorkerMessageRouter`
 * factory exported by `worker-entry.ts` so there is zero logic duplication.
 * Each message is scheduled in an idle slot to keep main-thread blocking low.
 *
 * SDK_BEST_PRACTICES §1.3 (CSP fallback), §13.3 (worker crash recovery).
 *
 * RULES:
 *   - Never throw to the host page (§13.1).
 *   - Use requestIdleCallback / setTimeout — never setInterval.
 *   - Log once at debug level (done by MainThreadBridge before calling this).
 */

import type { MainToWorkerMsg, WorkerToMainMsg, ResolvedConfig } from './wire-protocol.js';
import { createWorkerMessageRouter } from './worker-entry.js';

// ─── Idle scheduler shim ──────────────────────────────────────────────────────

/**
 * Normalized idle scheduler.
 * Uses `requestIdleCallback` when available; falls back to `setTimeout(fn, 0)`.
 * Returns a handle that can be cancelled via `cancelIdle`.
 */
function scheduleIdle(fn: () => void): ReturnType<typeof setTimeout> {
  if (typeof requestIdleCallback === 'function') {
    // requestIdleCallback returns a number; cast to the same type as setTimeout
    // so callers can use a single cancel function.
    return requestIdleCallback(() => {
      try { fn(); } catch { /* isolate — never rethrow (§13.1) */ }
    }) as unknown as ReturnType<typeof setTimeout>;
  }
  return setTimeout(() => {
    try { fn(); } catch { /* isolate */ }
  }, 0);
}

/** Cancels a previously scheduled idle callback. */
function cancelIdle(id: ReturnType<typeof setTimeout>): void {
  if (typeof cancelIdleCallback === 'function') {
    try {
      cancelIdleCallback(id as unknown as number);
    } catch {
      try { clearTimeout(id); } catch { /* ignore */ }
    }
  } else {
    try { clearTimeout(id); } catch { /* ignore */ }
  }
}

// ─── MainThreadFallback ───────────────────────────────────────────────────────

/**
 * MainThreadFallback — drop-in replacement for the Web Worker when the
 * worker environment is unavailable.
 *
 * Exposes the same `postMessage` / `terminate` interface as `Worker` so
 * `MainThreadBridge` can treat the two interchangeably after construction.
 *
 * All message processing is deferred to idle time to minimise main-thread
 * blocking. Full feature extraction is NOT available in fallback mode —
 * the SDK degrades gracefully (batches are sent with empty signals).
 */
export class MainThreadFallback {
  private terminated = false;

  /**
   * The worker message router built from `createWorkerMessageRouter`.
   * Processes each `MainToWorkerMsg` using the same logic as the real worker.
   */
  private readonly router: (msg: MainToWorkerMsg) => void;

  /** Pending idle-callback handles for cancellation on `terminate()`. */
  private readonly pendingHandles: Array<ReturnType<typeof setTimeout>> = [];

  /**
   * @param config      Fully resolved SDK config (used to initialise the
   *                    worker-side modules that run in this fallback).
   * @param postToMain  Callback that delivers `WorkerToMainMsg` responses back
   *                    to `MainThreadBridge.handleWorkerMessage`. Mirrors the
   *                    role of `worker.onmessage` in the real Worker path.
   */
  constructor(
    config: ResolvedConfig,
    postToMain: (msg: WorkerToMainMsg) => void,
  ) {
    this.router = createWorkerMessageRouter(config, postToMain);
  }

  /**
   * Accepts a main→worker message and schedules its processing in an idle
   * callback, matching the async delivery semantics of a real Worker.
   *
   * EVENT_TAP messages (very high frequency) are coalesced into the same idle
   * queue as all other message types.
   *
   * @param msg  The typed message to deliver.
   */
  postMessage(msg: MainToWorkerMsg): void {
    if (this.terminated) return;

    const handle = scheduleIdle(() => {
      if (this.terminated) return;
      try {
        this.router(msg);
      } catch {
        // Router threw — isolate, never rethrow to the host page (§13.1).
      }
    });

    this.pendingHandles.push(handle);

    // Prune completed handles to avoid unbounded array growth.
    // (They become stale references after the callback fires.)
    if (this.pendingHandles.length > 200) {
      this.pendingHandles.splice(0, 100);
    }
  }

  /**
   * Terminates the fallback, cancelling all pending idle callbacks.
   * After `terminate()`, `postMessage` is a no-op.
   * Mirrors `Worker.terminate()`.
   */
  terminate(): void {
    if (this.terminated) return;
    this.terminated = true;

    for (const handle of this.pendingHandles) {
      cancelIdle(handle);
    }
    this.pendingHandles.length = 0;
  }
}
