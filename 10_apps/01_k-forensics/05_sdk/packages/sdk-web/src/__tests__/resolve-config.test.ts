/**
 * resolve-config.test.ts
 *
 * Tests for the resolveConfig() function — ensures defaults are applied
 * correctly, overrides are merged (not clobbered), and endpoint resolution
 * follows transport mode rules.
 */

import { describe, it, expect } from 'vitest';
import { resolveConfig } from '../config/resolve-config.js';
import type { KProtectConfig, CriticalAction, UsernameSelector } from '../runtime/wire-protocol.js';
import {
  DEFAULT_PULSE_INTERVAL_MS,
  DEFAULT_KEEPALIVE_INTERVAL_MS,
  DEFAULT_IDLE_TIMEOUT_MS,
  API_BASE_URL,
  API_INGEST_PATH,
  DEFAULT_USERNAME_SELECTORS,
  DEFAULT_CRITICAL_ACTIONS,
  DEFAULT_SSO_GLOBALS,
} from '../config/defaults.js';

// ─── Helpers ──────────────────────────────────────────────────────────────────

function minimalConfig(overrides: Partial<KProtectConfig> = {}): KProtectConfig {
  return {
    api_key: 'kp_test_abc123',
    ...overrides,
  };
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('resolveConfig()', () => {
  describe('defaults', () => {
    it('uses defaults when no overrides provided', () => {
      const resolved = resolveConfig(minimalConfig());
      expect(resolved.api_key).toBe('kp_test_abc123');
      expect(resolved.environment).toBe('production');
      expect(resolved.transport.mode).toBe('direct');
      expect(resolved.transport.endpoint).toBe(`${API_BASE_URL}${API_INGEST_PATH}`);
      expect(resolved.session.pulse_interval_ms).toBe(DEFAULT_PULSE_INTERVAL_MS);
      expect(resolved.session.idle_timeout_ms).toBe(DEFAULT_IDLE_TIMEOUT_MS);
      expect(resolved.session.keepalive_interval_ms).toBe(DEFAULT_KEEPALIVE_INTERVAL_MS);
    });

    it('includes default username selectors when identity overrides are absent', () => {
      const resolved = resolveConfig(minimalConfig());
      expect(resolved.identity.username.selectors).toEqual(
        expect.arrayContaining([...DEFAULT_USERNAME_SELECTORS]),
      );
      expect(resolved.identity.username.selectors).toHaveLength(
        DEFAULT_USERNAME_SELECTORS.length,
      );
    });

    it('includes default SSO globals when not overridden', () => {
      const resolved = resolveConfig(minimalConfig());
      expect(resolved.identity.username.sso_globals).toEqual(
        expect.arrayContaining([...DEFAULT_SSO_GLOBALS]),
      );
    });

    it('includes default critical actions when not overridden', () => {
      const resolved = resolveConfig(minimalConfig());
      expect(resolved.critical_actions.actions).toHaveLength(
        DEFAULT_CRITICAL_ACTIONS.length,
      );
    });

    it('returns an empty opt_out_patterns array by default', () => {
      const resolved = resolveConfig(minimalConfig());
      expect(resolved.page_gate.opt_out_patterns).toEqual([]);
    });

    it('sets environment to production by default', () => {
      const resolved = resolveConfig(minimalConfig());
      expect(resolved.environment).toBe('production');
    });
  });

  describe('session overrides', () => {
    it('merges session overrides with defaults', () => {
      const resolved = resolveConfig(
        minimalConfig({
          overrides: {
            session: { pulse_interval_ms: 10000 },
          },
        }),
      );
      expect(resolved.session.pulse_interval_ms).toBe(10000);
      // Other session fields should remain at defaults
      expect(resolved.session.idle_timeout_ms).toBe(DEFAULT_IDLE_TIMEOUT_MS);
      expect(resolved.session.keepalive_interval_ms).toBe(DEFAULT_KEEPALIVE_INTERVAL_MS);
    });

    it('overrides idle_timeout_ms independently', () => {
      const resolved = resolveConfig(
        minimalConfig({
          overrides: { session: { idle_timeout_ms: 60000 } },
        }),
      );
      expect(resolved.session.idle_timeout_ms).toBe(60000);
      expect(resolved.session.pulse_interval_ms).toBe(DEFAULT_PULSE_INTERVAL_MS);
    });

    it('overrides keepalive_interval_ms independently', () => {
      const resolved = resolveConfig(
        minimalConfig({
          overrides: { session: { keepalive_interval_ms: 15000 } },
        }),
      );
      expect(resolved.session.keepalive_interval_ms).toBe(15000);
      expect(resolved.session.pulse_interval_ms).toBe(DEFAULT_PULSE_INTERVAL_MS);
    });

    it('allows all session fields to be overridden simultaneously', () => {
      const resolved = resolveConfig(
        minimalConfig({
          overrides: {
            session: {
              pulse_interval_ms: 2000,
              idle_timeout_ms: 30000,
              keepalive_interval_ms: 10000,
            },
          },
        }),
      );
      expect(resolved.session.pulse_interval_ms).toBe(2000);
      expect(resolved.session.idle_timeout_ms).toBe(30000);
      expect(resolved.session.keepalive_interval_ms).toBe(10000);
    });
  });

  describe('transport overrides', () => {
    it('uses proxy endpoint when mode is proxy', () => {
      const resolved = resolveConfig(
        minimalConfig({
          overrides: {
            transport: { mode: 'proxy', endpoint: 'https://my-proxy.example.com/ingest' },
          },
        }),
      );
      expect(resolved.transport.mode).toBe('proxy');
      expect(resolved.transport.endpoint).toBe('https://my-proxy.example.com/ingest');
    });

    it('falls back to direct API URL for direct mode even when endpoint is set', () => {
      // If mode is 'direct' and endpoint is provided, the direct URL takes precedence
      const resolved = resolveConfig(
        minimalConfig({
          overrides: {
            transport: { mode: 'direct', endpoint: 'https://ignored.example.com' },
          },
        }),
      );
      expect(resolved.transport.mode).toBe('direct');
      expect(resolved.transport.endpoint).toBe(`${API_BASE_URL}${API_INGEST_PATH}`);
    });

    it('uses direct mode and default endpoint when transport overrides are absent', () => {
      const resolved = resolveConfig(minimalConfig());
      expect(resolved.transport.mode).toBe('direct');
      expect(resolved.transport.endpoint).toBe(`${API_BASE_URL}${API_INGEST_PATH}`);
    });

    it('uses proxy mode without endpoint, falls through to default URL', () => {
      // proxy mode but no endpoint provided — falls back to the default URL
      const resolved = resolveConfig(
        minimalConfig({
          overrides: {
            transport: { mode: 'proxy' }, // no endpoint
          },
        }),
      );
      expect(resolved.transport.mode).toBe('proxy');
      expect(resolved.transport.endpoint).toBe(`${API_BASE_URL}${API_INGEST_PATH}`);
    });
  });

  describe('identity overrides', () => {
    it('merges custom username selectors (replaces defaults)', () => {
      const customSelectors: UsernameSelector[] = [
        { selector: 'input[data-testid="username"]', url: '/auth', event: 'blur' },
      ];
      const resolved = resolveConfig(
        minimalConfig({
          overrides: { identity: { username: { selectors: customSelectors } } },
        }),
      );
      expect(resolved.identity.username.selectors).toEqual(customSelectors);
      // Should NOT include defaults when custom selectors are provided
      expect(resolved.identity.username.selectors).toHaveLength(1);
    });

    it('merges custom SSO globals (replaces defaults)', () => {
      const resolved = resolveConfig(
        minimalConfig({
          overrides: {
            identity: { username: { sso_globals: ['window.__MY_USER__', 'window.__SSO__'] } },
          },
        }),
      );
      expect(resolved.identity.username.sso_globals).toEqual([
        'window.__MY_USER__',
        'window.__SSO__',
      ]);
    });

    it('keeps default selectors when only sso_globals are overridden', () => {
      const resolved = resolveConfig(
        minimalConfig({
          overrides: {
            identity: { username: { sso_globals: ['window.__MY_USER__'] } },
          },
        }),
      );
      expect(resolved.identity.username.selectors).toHaveLength(
        DEFAULT_USERNAME_SELECTORS.length,
      );
    });
  });

  describe('page_gate overrides', () => {
    it('merges opt_out_patterns — string patterns', () => {
      const resolved = resolveConfig(
        minimalConfig({
          overrides: { page_gate: { opt_out_patterns: ['/admin', '/debug'] } },
        }),
      );
      expect(resolved.page_gate.opt_out_patterns).toEqual(['/admin', '/debug']);
    });

    it('merges opt_out_patterns — RegExp patterns', () => {
      const pattern = /^\/internal\//;
      const resolved = resolveConfig(
        minimalConfig({
          overrides: { page_gate: { opt_out_patterns: [pattern] } },
        }),
      );
      expect(resolved.page_gate.opt_out_patterns[0]).toBe(pattern);
    });

    it('merges mixed string and RegExp patterns', () => {
      const pattern = /^\/test/;
      const resolved = resolveConfig(
        minimalConfig({
          overrides: { page_gate: { opt_out_patterns: ['/admin', pattern] } },
        }),
      );
      expect(resolved.page_gate.opt_out_patterns).toHaveLength(2);
      expect(resolved.page_gate.opt_out_patterns[0]).toBe('/admin');
      expect(resolved.page_gate.opt_out_patterns[1]).toBe(pattern);
    });
  });

  describe('critical_actions overrides', () => {
    it('replaces default critical actions with custom ones', () => {
      const customActions: CriticalAction[] = [
        {
          page: /\/checkout/,
          action: 'checkout_confirm',
          commit: { selector: 'button#confirm-order' },
        },
      ];
      const resolved = resolveConfig(
        minimalConfig({
          overrides: { critical_actions: { actions: customActions } },
        }),
      );
      expect(resolved.critical_actions.actions).toHaveLength(1);
      expect(resolved.critical_actions.actions[0]?.action).toBe('checkout_confirm');
    });

    it('uses an empty critical actions list when explicitly set to []', () => {
      const resolved = resolveConfig(
        minimalConfig({
          overrides: { critical_actions: { actions: [] } },
        }),
      );
      expect(resolved.critical_actions.actions).toHaveLength(0);
    });
  });

  describe('environment override', () => {
    it('sets environment to debug when overridden', () => {
      const resolved = resolveConfig(
        minimalConfig({ overrides: { environment: 'debug' } }),
      );
      expect(resolved.environment).toBe('debug');
    });

    it('sets environment to production by default', () => {
      const resolved = resolveConfig(minimalConfig());
      expect(resolved.environment).toBe('production');
    });
  });

  describe('immutability', () => {
    it('returns new objects — mutating the result does not affect a second call', () => {
      const config = minimalConfig();
      const r1 = resolveConfig(config);
      const r2 = resolveConfig(config);
      // Mutate r1
      (r1.session as { pulse_interval_ms: number }).pulse_interval_ms = 99999;
      // r2 should be unaffected
      expect(r2.session.pulse_interval_ms).toBe(DEFAULT_PULSE_INTERVAL_MS);
    });

    it('selectors array is a copy — mutating it does not affect defaults', () => {
      const resolved = resolveConfig(minimalConfig());
      const originalLength = resolved.identity.username.selectors.length;
      (resolved.identity.username.selectors as UsernameSelector[]).push({
        selector: 'input[name="injected"]',
      });
      // Calling again should still return the original default length
      const resolved2 = resolveConfig(minimalConfig());
      expect(resolved2.identity.username.selectors).toHaveLength(originalLength);
    });
  });
});
