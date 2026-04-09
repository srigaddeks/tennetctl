/**
 * mutable-refresh.ts — Periodically re-collects mutable signals (network, battery)
 * and posts updates to the worker via a MUTABLE_SIGNALS_UPDATE message.
 *
 * Network conditions and battery state change during a session — stale data
 * misses VPN toggling, network changes, etc. This module re-checks every
 * MUTABLE_REFRESH_INTERVAL_MS (default: 3 min) and only posts when values
 * have actually changed (shallow JSON equality).
 *
 * SDK_BEST_PRACTICES §4 (Performance): no heavy work on main thread.
 * The collectors here are lightweight synchronous reads (network) or a single
 * async Battery API call (battery).
 *
 * RULES:
 *   - No `any` types.
 *   - Return new objects, never mutate.
 *   - All timing via performance.now().
 *   - try/catch every browser API.
 */

import { collectNetworkFingerprint } from './environment-signals.js';
import { collectBatteryFingerprint } from './misc-fingerprints.js';
import { MUTABLE_REFRESH_INTERVAL_MS } from '../config/defaults.js';
import type { MainToWorkerMsg, NetworkFingerprint, BatteryFingerprint } from '../runtime/wire-protocol.js';

// ─── Shallow JSON equality ───────────────────────────────────────────────────

/**
 * Compares two values by their JSON serialisation.
 * Sufficient for the flat NetworkFingerprint / BatteryFingerprint shapes.
 */
function jsonEqual(a: unknown, b: unknown): boolean {
  try {
    return JSON.stringify(a) === JSON.stringify(b);
  } catch {
    return false;
  }
}

// ─── Public API ──────────────────────────────────────────────────────────────

/**
 * Starts periodic re-collection of mutable device signals (network, battery).
 *
 * On each tick:
 *   1. Calls collectNetworkFingerprint() (sync) and collectBatteryFingerprint() (async).
 *   2. Compares with last known values via shallow JSON equality.
 *   3. If either changed, posts a MUTABLE_SIGNALS_UPDATE message to the worker.
 *
 * @param postToWorker  Channel for sending MainToWorkerMsg to the worker/fallback.
 * @param intervalMs    Override interval in ms. Defaults to MUTABLE_REFRESH_INTERVAL_MS (3 min).
 * @returns             A cleanup function that clears the interval timer.
 */
export function startMutableRefresh(
  postToWorker: (msg: MainToWorkerMsg) => void,
  intervalMs: number = MUTABLE_REFRESH_INTERVAL_MS,
): () => void {
  let lastNetwork: NetworkFingerprint | null = null;
  let lastBattery: BatteryFingerprint | null = null;

  // Collect initial baseline so the first tick only posts if values differ.
  try {
    lastNetwork = collectNetworkFingerprint();
  } catch {
    lastNetwork = null;
  }

  const tick = async (): Promise<void> => {
    let currentNetwork: NetworkFingerprint | null = null;
    let currentBattery: BatteryFingerprint | null = null;

    try {
      currentNetwork = collectNetworkFingerprint();
    } catch {
      currentNetwork = null;
    }

    try {
      currentBattery = await collectBatteryFingerprint();
    } catch {
      currentBattery = null;
    }

    const networkChanged = !jsonEqual(currentNetwork, lastNetwork);
    const batteryChanged = !jsonEqual(currentBattery, lastBattery);

    if (networkChanged || batteryChanged) {
      lastNetwork = currentNetwork;
      lastBattery = currentBattery;

      postToWorker({
        type: 'MUTABLE_SIGNALS_UPDATE',
        network: currentNetwork,
        battery: currentBattery,
      });
    }
  };

  const id = setInterval(() => { void tick(); }, intervalMs);

  return () => { clearInterval(id); };
}
