/**
 * resolve-config.ts — merges KProtectConfig + KProtectOverrides with defaults
 * to produce a fully-resolved ResolvedConfig that the worker works with.
 *
 * SDK_BEST_PRACTICES §2.3 (partial overrides merged with defaults).
 */

import type {
  KProtectConfig,
  ResolvedConfig,
} from '../runtime/wire-protocol.js';
import {
  API_BASE_URL,
  API_INGEST_PATH,
  DEFAULT_PULSE_INTERVAL_MS,
  DEFAULT_KEEPALIVE_INTERVAL_MS,
  DEFAULT_IDLE_TIMEOUT_MS,
  DEFAULT_USERNAME_SELECTORS,
  DEFAULT_CRITICAL_ACTIONS,
  DEFAULT_SSO_GLOBALS,
  DEFAULT_CONSENT_MODE,
} from './defaults.js';

/**
 * Merges the public KProtectConfig (api_key + optional overrides) with all
 * defaults and returns a fully-resolved ResolvedConfig.
 *
 * Rules:
 *   - Every field in ResolvedConfig is required — never undefined.
 *   - Arrays in overrides REPLACE their defaults (not concatenate).
 *   - Transport endpoint is resolved from mode + optional proxy endpoint.
 */
export function resolveConfig(config: KProtectConfig): ResolvedConfig {
  const overrides = config.overrides ?? {};

  // ── Transport ──────────────────────────────────────────────────────────────
  const transportMode = overrides.transport?.mode ?? 'direct';
  let endpoint: string;
  if (transportMode === 'proxy' && overrides.transport?.endpoint) {
    endpoint = overrides.transport.endpoint;
  } else {
    endpoint = `${API_BASE_URL}${API_INGEST_PATH}`;
  }

  // ── Session ────────────────────────────────────────────────────────────────
  const session = {
    pulse_interval_ms:
      overrides.session?.pulse_interval_ms ?? DEFAULT_PULSE_INTERVAL_MS,
    idle_timeout_ms:
      overrides.session?.idle_timeout_ms ?? DEFAULT_IDLE_TIMEOUT_MS,
    keepalive_interval_ms:
      overrides.session?.keepalive_interval_ms ?? DEFAULT_KEEPALIVE_INTERVAL_MS,
  };

  // ── Identity ───────────────────────────────────────────────────────────────
  const selectors =
    overrides.identity?.username?.selectors !== undefined
      ? [...overrides.identity.username.selectors]
      : [...DEFAULT_USERNAME_SELECTORS];

  const ssoGlobals =
    overrides.identity?.username?.sso_globals !== undefined
      ? [...overrides.identity.username.sso_globals]
      : [...DEFAULT_SSO_GLOBALS];

  // ── Page gate ──────────────────────────────────────────────────────────────
  const optOutPatterns =
    overrides.page_gate?.opt_out_patterns !== undefined
      ? [...overrides.page_gate.opt_out_patterns]
      : [];

  // ── Critical actions ───────────────────────────────────────────────────────
  const criticalActions =
    overrides.critical_actions?.actions !== undefined
      ? [...overrides.critical_actions.actions]
      : [...DEFAULT_CRITICAL_ACTIONS];

  return {
    api_key: config.api_key,
    environment: overrides.environment ?? 'production',

    transport: {
      mode: transportMode,
      endpoint,
    },

    session,

    identity: {
      username: {
        selectors,
        sso_globals: ssoGlobals,
      },
    },

    page_gate: {
      opt_out_patterns: optOutPatterns,
    },

    critical_actions: {
      actions: criticalActions,
    },

    fingerprinting: {
      enabled: config.overrides?.fingerprinting?.enabled ?? true,
    },

    consent: {
      mode: config.overrides?.consent?.mode ?? DEFAULT_CONSENT_MODE,
    },
  };
}
