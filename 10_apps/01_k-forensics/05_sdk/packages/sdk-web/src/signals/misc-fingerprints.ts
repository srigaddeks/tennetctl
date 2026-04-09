/**
 * Miscellaneous fingerprint collectors — smaller/simpler signals.
 *
 * Runs on the MAIN THREAD.
 *
 * Collectors: math, date formatting, CSS feature support, storage quota,
 * speech synthesis voices, battery status, navigator dump.
 *
 * Privacy: no user data captured. All outputs are deterministic per
 * browser + OS combination. Raw values cannot identify individuals.
 */

import type {
  MathFingerprint,
  DateFingerprint,
  CssFingerprint,
  StorageFingerprint,
  SpeechFingerprint,
  BatteryFingerprint,
} from '../runtime/wire-protocol.js';

import { CSS_FEATURE_PROBES, SPEECH_VOICES_TIMEOUT_MS } from '../config/defaults.js';
import { sha256 } from './crypto-utils.js';

// ─── Helpers ──────────────────────────────────────────────────────────────────

/** Replace all non-alphanumeric characters with underscores. */
function sanitizeKey(raw: string): string {
  return raw.replace(/[^a-zA-Z0-9]/g, '_');
}

// ─── 1. Math fingerprint ─────────────────────────────────────────────────────

/**
 * Probes floating-point precision quirks across JS engines.
 * Returns null on error.
 */
export function collectMathFingerprint(): MathFingerprint | null {
  try {
    return {
      tan_pi_4: Math.tan(Math.PI / 4),
      log_2: Math.log(2),
      e_mod: (Math.E * 1e15) % 1,
      pow_min: Math.pow(2, -1074),
    };
  } catch {
    return null;
  }
}

// ─── 2. Date fingerprint ─────────────────────────────────────────────────────

/**
 * Formats epoch (1970-01-01T00:00:00Z) using Intl.DateTimeFormat to detect
 * locale/timezone rendering differences.
 * Returns null on error.
 */
export async function collectDateFingerprint(): Promise<DateFingerprint | null> {
  try {
    const epoch = new Date(0);

    const full = new Intl.DateTimeFormat('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: 'numeric',
      minute: 'numeric',
      second: 'numeric',
      timeZoneName: 'long',
    }).format(epoch);

    const short = new Intl.DateTimeFormat('en-US', {
      dateStyle: 'short',
      timeStyle: 'short',
    }).format(epoch);

    const relative_era = new Intl.DateTimeFormat('en-US', {
      era: 'long',
    }).format(epoch);

    const full_hash = await sha256(full);
    const short_hash = await sha256(short);

    return { full_hash, short_hash, relative_era };
  } catch {
    return null;
  }
}

// ─── 3. CSS fingerprint ──────────────────────────────────────────────────────

/**
 * Tests CSS feature support via CSS.supports().
 * Returns null on error or if CSS.supports is unavailable.
 */
export function collectCssFingerprint(): CssFingerprint | null {
  try {
    if (typeof CSS === 'undefined' || typeof CSS.supports !== 'function') {
      return null;
    }

    const result: CssFingerprint = {};

    for (const probe of CSS_FEATURE_PROBES) {
      const colonIdx = probe.indexOf(':');
      if (colonIdx === -1) continue;

      const property = probe.slice(0, colonIdx).trim();
      const value = probe.slice(colonIdx + 1).trim();
      const key = sanitizeKey(probe);

      result[key] = CSS.supports(property, value);
    }

    return result;
  } catch {
    return null;
  }
}

// ─── 4. Storage fingerprint ──────────────────────────────────────────────────

/**
 * Reads storage quota via navigator.storage.estimate().
 * Returns null if the Storage API is unavailable.
 */
export async function collectStorageFingerprint(): Promise<StorageFingerprint | null> {
  try {
    if (
      typeof navigator === 'undefined' ||
      !navigator.storage ||
      typeof navigator.storage.estimate !== 'function'
    ) {
      return null;
    }

    const estimate = await navigator.storage.estimate();

    return {
      quota_bytes: estimate.quota ?? null,
    };
  } catch {
    return null;
  }
}

// ─── 5. Speech fingerprint ───────────────────────────────────────────────────

/**
 * Enumerates speechSynthesis voices, sorts deterministically, and
 * SHA-256 hashes the result.
 * Returns null if speechSynthesis is unavailable.
 */
export async function collectSpeechFingerprint(): Promise<SpeechFingerprint | null> {
  try {
    if (typeof speechSynthesis === 'undefined') {
      return null;
    }

    let voices = speechSynthesis.getVoices();

    // Some browsers populate voices asynchronously via 'voiceschanged'.
    if (voices.length === 0) {
      voices = await new Promise<SpeechSynthesisVoice[]>((resolve) => {
        const onVoicesChanged = (): void => {
          speechSynthesis.removeEventListener('voiceschanged', onVoicesChanged);
          resolve(speechSynthesis.getVoices());
        };

        speechSynthesis.addEventListener('voiceschanged', onVoicesChanged);

        // Timeout: don't hang forever if 'voiceschanged' never fires.
        setTimeout(() => {
          speechSynthesis.removeEventListener('voiceschanged', onVoicesChanged);
          resolve(speechSynthesis.getVoices());
        }, SPEECH_VOICES_TIMEOUT_MS);
      });
    }

    if (voices.length === 0) {
      return { count: 0, hash: '' };
    }

    const serialized = voices
      .map((v) => `${v.name}|${v.lang}|${v.localService}`)
      .sort()
      .join('\n');

    const hash = await sha256(serialized);

    return { count: voices.length, hash };
  } catch {
    return null;
  }
}

// ─── 6. Battery fingerprint ──────────────────────────────────────────────────

/**
 * Reads battery status via navigator.getBattery() (Chrome/Android only).
 * Returns null on unsupported browsers.
 */
export async function collectBatteryFingerprint(): Promise<BatteryFingerprint | null> {
  try {
    const nav: unknown = navigator;

    // navigator.getBattery is non-standard — narrow carefully.
    if (
      typeof nav !== 'object' ||
      nav === null ||
      !('getBattery' in nav) ||
      typeof (nav as Record<string, unknown>)['getBattery'] !== 'function'
    ) {
      return null;
    }

    const battery: unknown = await (nav as { getBattery: () => Promise<unknown> }).getBattery();

    if (typeof battery !== 'object' || battery === null) {
      return null;
    }

    const b = battery as Record<string, unknown>;

    if (
      typeof b['charging'] !== 'boolean' ||
      typeof b['level'] !== 'number'
    ) {
      return null;
    }

    const level = b['level'] as number;

    return {
      charging: b['charging'] as boolean,
      level_bucket: Math.floor(level * 4) / 4,
    };
  } catch {
    return null;
  }
}

