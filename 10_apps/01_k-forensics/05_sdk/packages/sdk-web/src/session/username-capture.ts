/**
 * username-capture.ts
 *
 * Detects username fields on the MAIN THREAD and hashes values before
 * sending to the worker.
 *
 * Runs on the MAIN THREAD — not in the Web Worker.
 *
 * Design:
 *   - One delegated 'blur' listener on `document` (capture phase) to
 *     intercept all input blur events without per-element listeners.
 *   - SSO global polling via setInterval to catch framework-set globals
 *     (e.g. window.__KP_USER__).
 *   - After capture: all listeners and timers are removed (self-teardown).
 *
 * SDK_BEST_PRACTICES §5.2, §6.4.
 */

import type { ResolvedConfig } from '../runtime/wire-protocol.js';
import { pbkdf2Hash } from '../signals/crypto-utils.js';
import { STORAGE_KEY_USERNAME_SALT } from '../config/defaults.js';

// ─── Constants ─────────────────────────────────────────────────────────────────

/**
 * Values that look like placeholder text, not real usernames.
 * Compared against the lowercased, trimmed input value.
 */
const PLACEHOLDER_BLOCKLIST: readonly string[] = [
  'username',
  'email',
  'phone',
  'user',
  'login',
] as const;

/**
 * How often (ms) the SSO globals are polled.
 * Not in defaults.ts because it is not user-configurable.
 */
const SSO_POLL_INTERVAL_MS = 1_000;

// ─── Types ────────────────────────────────────────────────────────────────────

/**
 * Callback invoked when a username has been successfully hashed.
 *
 * @param user_hash     SHA-256 hex digest of the username.
 * @param raw_username  The original (trimmed) username value.
 *
 * NOTE: The plaintext `raw_username` is passed here so the calling layer
 * can persist it via IdentityStore. It MUST NOT be sent to the worker — only
 * user_hash crosses the thread boundary (SDK_BEST_PRACTICES §5.2).
 */
export type UsernameFoundCallback = (user_hash: string, raw_username: string) => void;

// ─── UsernameCapture ───────────────────────────────────────────────────────────

/**
 * UsernameCapture — main-thread username detector.
 *
 * Watches for username values via:
 *   1. A delegated blur listener on `document` (all `<input>` blurs).
 *   2. SSO global polling (window.__KP_USER__ and custom paths).
 *
 * After the first successful capture, `stop()` is called automatically to
 * remove all listeners and timers.
 */
export class UsernameCapture {
  private readonly config: ResolvedConfig;
  private readonly onFound: UsernameFoundCallback;

  /** Whether capture has already succeeded this session. */
  private captured: boolean = false;

  /** Bound reference kept so the same function can be removed. */
  private readonly blurHandler: (event: Event) => void;

  /** SSO polling interval handle. */
  private ssoPollHandle: ReturnType<typeof setInterval> | null = null;

  constructor(config: ResolvedConfig, onFound: UsernameFoundCallback) {
    this.config = config;
    this.onFound = onFound;
    // Bind once so removeEventListener receives the same reference.
    this.blurHandler = this.handleBlur.bind(this);
  }

  // ─── Public API ────────────────────────────────────────────────────────────

  /**
   * Starts listening for username values.
   *
   * - Attaches a single delegated blur listener on `document` (capture phase).
   * - Starts the SSO global polling interval.
   * - Polls SSO globals once immediately.
   */
  start(): void {
    if (this.captured) return;

    try {
      document.addEventListener('blur', this.blurHandler, {
        passive: true,
        capture: true,
      });
    } catch {
      // Defensive — addEventListener should never throw, but guard just in case.
    }

    // Poll SSO globals immediately, then on interval.
    this.pollSsoGlobals();

    this.ssoPollHandle = setInterval(() => {
      this.pollSsoGlobals();
    }, SSO_POLL_INTERVAL_MS);
  }

  /**
   * Called on SPA route change — re-polls SSO globals in case the SPA sets
   * them after navigation, and re-evaluates selector applicability.
   *
   * @param newPath  The new URL pathname.
   */
  onRouteChange(_newPath: string): void {
    if (this.captured) return;
    this.pollSsoGlobals();
  }

  /**
   * Stops all listeners and timers.
   * Called automatically after capture, or explicitly on teardown.
   */
  stop(): void {
    try {
      document.removeEventListener('blur', this.blurHandler, { capture: true });
    } catch {
      // Ignore — DOM may be gone (e.g. during unload).
    }

    if (this.ssoPollHandle !== null) {
      clearInterval(this.ssoPollHandle);
      this.ssoPollHandle = null;
    }
  }

  // ─── Private helpers ───────────────────────────────────────────────────────

  /**
   * Delegated blur handler.
   * Checks whether the blurring element matches any configured selector
   * and the current URL path matches the selector's optional url filter.
   */
  private handleBlur(event: Event): void {
    if (this.captured) return;
    if (!(event.target instanceof HTMLInputElement)) return;

    const el = event.target;
    const currentPath = this.currentPath();

    for (const selectorDef of this.config.identity.username.selectors) {
      try {
        // URL scope check — empty/undefined url means match all pages.
        const urlScope = selectorDef.url ?? '';
        if (urlScope && !currentPath.includes(urlScope)) continue;

        if (!el.matches(selectorDef.selector)) continue;

        const value = el.value;
        void this.tryCapture(value);
        return; // Only process the first matching selector per blur.
      } catch {
        // el.matches() can throw on invalid selectors — skip.
      }
    }
  }

  /**
   * Polls all configured SSO globals.
   * For each path in config.identity.username.sso_globals, resolves the
   * nested property on globalThis. If a non-empty string is found, captures.
   */
  private pollSsoGlobals(): void {
    if (this.captured) return;

    for (const globalPath of this.config.identity.username.sso_globals) {
      try {
        const value = resolveGlobalPath(globalPath);
        if (typeof value === 'string' && value.trim().length > 0) {
          void this.tryCapture(value);
          return;
        }
      } catch {
        // Property access threw (e.g. cross-origin frame) — skip.
      }
    }
  }

  /**
   * Validates the candidate value, hashes it, and calls onFound.
   * Triggers stop() on success.
   *
   * Validation:
   *   - Trim whitespace.
   *   - Skip empty strings.
   *   - Skip blocklisted placeholder values (case-insensitive).
   *
   * @param rawValue  The candidate username string.
   */
  private async tryCapture(rawValue: string): Promise<void> {
    if (this.captured) return;

    const trimmed = rawValue.trim();
    if (trimmed.length === 0) return;
    if (PLACEHOLDER_BLOCKLIST.includes(trimmed.toLowerCase())) return;

    const salt = this.getSalt();
    const hashHex = await pbkdf2Hash(trimmed, salt);
    if (!hashHex) return; // crypto unavailable (insecure context?)

    // Guard against concurrent captures (blur + SSO poll racing).
    if (this.captured) return;
    this.captured = true;

    this.stop();
    this.onFound(hashHex, trimmed);
  }

  /**
   * Returns the per-device PBKDF2 salt, creating and persisting one if absent.
   * Stored in localStorage as a 64-char hex string (32 bytes).
   */
  private getSalt(): Uint8Array {
    try {
      const stored = localStorage.getItem(STORAGE_KEY_USERNAME_SALT);
      if (stored) {
        const bytes = new Uint8Array(stored.match(/.{2}/g)!.map((b) => parseInt(b, 16)));
        if (bytes.length === 32) return bytes;
      }
    } catch {
      /* ignore — localStorage unavailable */
    }

    // Generate new salt
    const salt = crypto.getRandomValues(new Uint8Array(32));
    const hex = Array.from(salt)
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('');
    try {
      localStorage.setItem(STORAGE_KEY_USERNAME_SALT, hex);
    } catch {
      /* best-effort persist */
    }
    return salt;
  }

  /** Returns the current location.pathname, or '' if not available. */
  private currentPath(): string {
    try {
      return location.pathname;
    } catch {
      return '';
    }
  }
}

// ─── resolveGlobalPath ────────────────────────────────────────────────────────

/**
 * Resolves a dot-separated property path on globalThis.
 *
 * Example:
 *   resolveGlobalPath('window.__KP_USER__')
 *   → (globalThis as Record<string, unknown>)['window']['__KP_USER__']
 *
 * Returns undefined when any segment in the path is missing.
 */
function resolveGlobalPath(path: string): unknown {
  const segments = path.split('.');
  let current: unknown = globalThis;
  for (const segment of segments) {
    if (current === null || current === undefined) return undefined;
    if (typeof current !== 'object') return undefined;
    current = (current as Record<string, unknown>)[segment];
  }
  return current;
}
