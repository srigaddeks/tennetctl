/**
 * consent-manager.ts — GDPR/CCPA consent gate for the K-Protect SDK.
 *
 * Manages user consent state. When consent mode is 'opt-in', the SDK
 * will not collect or transmit any data until consent is explicitly granted.
 *
 * Consent state is persisted in localStorage with a timestamp.
 *
 * Rules:
 *   • Never throws.
 *   • Zero npm dependencies.
 *   • No `any` types.
 */

import { STORAGE_KEY_CONSENT } from '../config/defaults.js';

export type ConsentMode = 'opt-in' | 'opt-out' | 'none';
export type ConsentState = 'granted' | 'denied' | 'unknown';

interface StoredConsent {
  state: ConsentState;
  timestamp: number;
}

/**
 * Checks whether the SDK has consent to operate.
 *
 * @param mode  The configured consent mode.
 * @returns     true if the SDK may collect data.
 */
export function hasConsent(mode: ConsentMode): boolean {
  if (mode === 'none') return true;

  const stored = readConsent();

  if (mode === 'opt-out') {
    // Runs unless user explicitly denied
    return stored?.state !== 'denied';
  }

  // opt-in: blocked until explicitly granted
  return stored?.state === 'granted';
}

/**
 * Records the user's consent decision.
 *
 * @param granted  true = user gave consent, false = user denied.
 */
export function setConsent(granted: boolean): void {
  const consent: StoredConsent = {
    state: granted ? 'granted' : 'denied',
    timestamp: Date.now(),
  };
  try {
    localStorage.setItem(STORAGE_KEY_CONSENT, JSON.stringify(consent));
  } catch {
    // Storage unavailable — best-effort.
  }
}

/**
 * Returns the current consent state, or null if never set.
 */
export function getConsentState(): StoredConsent | null {
  return readConsent();
}

/**
 * Clears stored consent (for testing or revocation).
 */
export function clearConsent(): void {
  try {
    localStorage.removeItem(STORAGE_KEY_CONSENT);
  } catch {
    // Ignore.
  }
}

function readConsent(): StoredConsent | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY_CONSENT);
    if (!raw) return null;
    const parsed: unknown = JSON.parse(raw);
    if (
      parsed !== null &&
      typeof parsed === 'object' &&
      'state' in parsed &&
      'timestamp' in parsed &&
      typeof (parsed as StoredConsent).state === 'string' &&
      typeof (parsed as StoredConsent).timestamp === 'number'
    ) {
      return parsed as StoredConsent;
    }
    return null;
  } catch {
    return null;
  }
}
