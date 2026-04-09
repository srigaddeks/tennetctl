/**
 * Automation / bot detection fingerprint collector.
 *
 * Runs on the MAIN THREAD. Probes modern automation signals including
 * headless browser detection, CDP presence, and behavioral anomalies.
 * Returns a scored fingerprint indicating automation likelihood.
 *
 * Zero npm dependencies. TypeScript strict mode.
 */

import type { AutomationFingerprint } from '../runtime/wire-protocol.js';

/** Timeout for async permission checks (ms). */
const PERMISSION_TIMEOUT_MS = 500;

/**
 * Check if navigator.permissions.query reports notifications as 'denied'
 * without ever prompting the user — a strong headless signal.
 * Returns null if the API is unavailable or times out.
 */
async function checkNotificationsDenied(): Promise<boolean | null> {
  try {
    if (
      typeof navigator === 'undefined' ||
      !navigator.permissions ||
      typeof navigator.permissions.query !== 'function'
    ) {
      return null;
    }

    const result = await Promise.race<PermissionStatus | null>([
      navigator.permissions.query({ name: 'notifications' as PermissionName }),
      new Promise<null>((resolve) =>
        setTimeout(() => resolve(null), PERMISSION_TIMEOUT_MS),
      ),
    ]);

    if (result === null) return null;
    return result.state === 'denied';
  } catch {
    return null;
  }
}

/**
 * Detect ChromeDriver / CDP artifacts.
 *
 * Checks for:
 *   1. Well-known ChromeDriver global (`cdc_adoQpoasnfa76pfcZLmcfl_`)
 *   2. CDP-injected stack frames in Error objects
 */
function checkCdpDetected(): boolean {
  try {
    const win = window as unknown as Record<string, unknown>;

    // ChromeDriver exposes this global
    if (win['cdc_adoQpoasnfa76pfcZLmcfl_'] !== undefined) {
      return true;
    }

    // Check for CDP-related frames in stack traces
    const stack = new Error().stack;
    if (typeof stack === 'string') {
      const cdpPatterns = [
        'puppeteer',
        'devtools',
        'cdp',
        '__puppeteer_evaluation_script__',
      ];
      const lowerStack = stack.toLowerCase();
      for (const pattern of cdpPatterns) {
        if (lowerStack.includes(pattern)) {
          return true;
        }
      }
    }

    return false;
  } catch {
    return false;
  }
}

/**
 * Detect whether window.Proxy has been overridden.
 *
 * Native `Proxy.toString()` returns `"function Proxy() { [native code] }"`.
 * Automation frameworks sometimes replace it.
 */
function checkProxyOverridden(): boolean {
  try {
    if (typeof Proxy === 'undefined') return false;
    const str = Function.prototype.toString.call(Proxy);
    return !str.includes('[native code]');
  } catch {
    return false;
  }
}

/**
 * Check for hardware inconsistency: hardwareConcurrency > 0 with
 * deviceMemory < 0.25 GB — real devices don't have <256MB with multiple cores.
 */
function checkHardwareMismatch(): boolean {
  try {
    const nav = navigator as unknown as Record<string, unknown>;
    const cores = navigator.hardwareConcurrency;
    const memory = nav['deviceMemory'];

    if (
      typeof cores === 'number' &&
      cores > 0 &&
      typeof memory === 'number' &&
      memory < 0.25
    ) {
      return true;
    }

    return false;
  } catch {
    return false;
  }
}

/**
 * Compute weighted automation score from individual flags.
 * Weights reflect signal strength. Capped at 1.0.
 */
function computeScore(flags: {
  webdriver: boolean;
  zero_plugins: boolean;
  zero_outer_dimensions: boolean;
  no_focus: boolean;
  notifications_denied: boolean | null;
  hardware_mismatch: boolean;
  cdp_detected: boolean;
  proxy_overridden: boolean;
}): number {
  let score = 0;

  if (flags.webdriver) score += 0.4;
  if (flags.zero_plugins) score += 0.15;
  if (flags.zero_outer_dimensions) score += 0.2;
  if (flags.no_focus) score += 0.05;
  if (flags.notifications_denied === true) score += 0.1;
  if (flags.hardware_mismatch) score += 0.1;
  if (flags.cdp_detected) score += 0.3;
  if (flags.proxy_overridden) score += 0.2;

  return Math.min(score, 1.0);
}

/**
 * Collect automation / bot detection signals.
 *
 * Async because the notifications permission check requires a promise.
 *
 * @returns `AutomationFingerprint` with boolean flags and a score, or `null` on error.
 */
export async function collectAutomationFingerprint(): Promise<AutomationFingerprint | null> {
  try {
    // ── Synchronous checks ──────────────────────────────────────────────
    const webdriver: boolean = navigator.webdriver === true;

    const zero_plugins: boolean = (() => {
      try {
        return navigator.plugins.length === 0;
      } catch {
        return false;
      }
    })();

    const zero_outer_dimensions: boolean = (() => {
      try {
        return window.outerHeight === 0 || window.outerWidth === 0;
      } catch {
        return false;
      }
    })();

    const no_focus: boolean = (() => {
      try {
        return !document.hasFocus();
      } catch {
        return false;
      }
    })();

    const hardware_mismatch = checkHardwareMismatch();
    const cdp_detected = checkCdpDetected();
    const proxy_overridden = checkProxyOverridden();

    // ── Async checks ────────────────────────────────────────────────────
    const notifications_denied = await checkNotificationsDenied();

    const score = computeScore({
      webdriver,
      zero_plugins,
      zero_outer_dimensions,
      no_focus,
      notifications_denied,
      hardware_mismatch,
      cdp_detected,
      proxy_overridden,
    });

    return {
      webdriver,
      zero_plugins,
      zero_outer_dimensions,
      no_focus,
      notifications_denied,
      hardware_mismatch,
      cdp_detected,
      proxy_overridden,
      score,
    };
  } catch {
    return null;
  }
}
