/**
 * page-gate.test.ts
 *
 * Exhaustive tests for the PageGate class.
 * Covers evaluate(), update(), and getCriticalActionForPath() with all
 * combinations of opt-out patterns and critical-action definitions.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { PageGate } from '../session/page-gate.js';
import type { ResolvedConfig, CriticalAction } from '../runtime/wire-protocol.js';

// ─── Test fixture helpers ─────────────────────────────────────────────────────

function makeConfig(
  overrides: Partial<{
    optOutPatterns: Array<string | RegExp>;
    criticalActions: CriticalAction[];
  }> = {},
): ResolvedConfig {
  return {
    api_key: 'kp_test_abc',
    environment: 'debug',
    transport: { mode: 'direct', endpoint: 'https://api.kprotect.io/v1/behavioral/ingest' },
    session: { pulse_interval_ms: 5000, idle_timeout_ms: 900000, keepalive_interval_ms: 30000 },
    identity: { username: { selectors: [], sso_globals: [] } },
    page_gate: {
      opt_out_patterns: overrides.optOutPatterns ?? [],
    },
    critical_actions: {
      actions: overrides.criticalActions ?? [
        {
          page: /\/login/,
          action: 'login_submit',
          commit: { selector: 'button[type="submit"]' },
        },
        {
          page: /\/transfer/,
          action: 'transfer_confirm',
          commit: { selector: '[data-kp-commit="transfer"]' },
        },
      ],
    },
    fingerprinting: { enabled: true },
    consent: { mode: 'opt-out' },
  };
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('PageGate', () => {
  describe('evaluate()', () => {
    it('returns "normal" for paths with no matching patterns', () => {
      const gate = new PageGate(makeConfig());
      expect(gate.evaluate('/dashboard')).toBe('normal');
      expect(gate.evaluate('/account/settings')).toBe('normal');
      expect(gate.evaluate('/')).toBe('normal');
    });

    it('returns "opted_out" for string patterns (substring match)', () => {
      const gate = new PageGate(
        makeConfig({ optOutPatterns: ['/admin', '/debug'] }),
      );
      expect(gate.evaluate('/admin')).toBe('opted_out');
      expect(gate.evaluate('/admin/users')).toBe('opted_out');
      expect(gate.evaluate('/app/debug/console')).toBe('opted_out');
    });

    it('returns "normal" for paths that do not contain the opt-out string', () => {
      const gate = new PageGate(makeConfig({ optOutPatterns: ['/admin'] }));
      expect(gate.evaluate('/dashboard')).toBe('normal');
      expect(gate.evaluate('/administration')).toBe('opted_out'); // substring match — /admin is in /administration
    });

    it('returns "opted_out" for RegExp patterns', () => {
      const gate = new PageGate(
        makeConfig({ optOutPatterns: [/^\/internal\//, /\/test-only$/] }),
      );
      expect(gate.evaluate('/internal/tools')).toBe('opted_out');
      expect(gate.evaluate('/staging/test-only')).toBe('opted_out');
      expect(gate.evaluate('/dashboard')).toBe('normal');
    });

    it('returns "critical_action" for matching critical action pages', () => {
      const gate = new PageGate(makeConfig());
      expect(gate.evaluate('/login')).toBe('critical_action');
      expect(gate.evaluate('/transfer/confirm')).toBe('critical_action');
    });

    it('prioritises opted_out over critical_action for same path', () => {
      // /login would normally be critical_action, but if also opted-out, opted_out wins
      const gate = new PageGate(
        makeConfig({
          optOutPatterns: ['/login'],
          criticalActions: [
            {
              page: /\/login/,
              action: 'login_submit',
              commit: { selector: 'button[type="submit"]' },
            },
          ],
        }),
      );
      expect(gate.evaluate('/login')).toBe('opted_out');
    });

    it('returns "normal" when no patterns match', () => {
      const gate = new PageGate(
        makeConfig({
          optOutPatterns: ['/admin'],
          criticalActions: [
            {
              page: /\/payment/,
              action: 'payment_confirm',
              commit: { selector: 'button[type="submit"]' },
            },
          ],
        }),
      );
      expect(gate.evaluate('/home')).toBe('normal');
    });

    it('handles empty opt_out_patterns and empty critical_actions gracefully', () => {
      const gate = new PageGate(
        makeConfig({ optOutPatterns: [], criticalActions: [] }),
      );
      expect(gate.evaluate('/any/path')).toBe('normal');
    });
  });

  describe('update()', () => {
    let gate: PageGate;

    beforeEach(() => {
      gate = new PageGate(makeConfig());
    });

    it('returns changed=true when page class transitions from normal to critical_action', () => {
      // Initial class is 'normal' (before any update)
      const result = gate.update('/login');
      expect(result.pageClass).toBe('critical_action');
      expect(result.changed).toBe(true);
    });

    it('returns changed=true when page class transitions from critical_action to normal', () => {
      gate.update('/login'); // -> critical_action
      const result = gate.update('/dashboard'); // -> normal
      expect(result.pageClass).toBe('normal');
      expect(result.changed).toBe(true);
    });

    it('returns changed=false when page class stays the same (normal -> normal)', () => {
      gate.update('/dashboard'); // normal
      const result = gate.update('/account'); // still normal
      expect(result.pageClass).toBe('normal');
      expect(result.changed).toBe(false);
    });

    it('returns changed=false when navigating between two critical_action pages', () => {
      gate.update('/login'); // critical_action
      const result = gate.update('/transfer'); // still critical_action
      expect(result.pageClass).toBe('critical_action');
      expect(result.changed).toBe(false);
    });

    it('returns the matching CriticalAction when page is critical_action', () => {
      const result = gate.update('/login');
      expect(result.action).not.toBeNull();
      expect(result.action?.action).toBe('login_submit');
      expect(result.action?.commit.selector).toBe('button[type="submit"]');
    });

    it('returns null action for normal pages', () => {
      const result = gate.update('/dashboard');
      expect(result.action).toBeNull();
    });

    it('returns null action for opted_out pages', () => {
      const gateWithOptOut = new PageGate(
        makeConfig({ optOutPatterns: ['/admin'] }),
      );
      const result = gateWithOptOut.update('/admin/panel');
      expect(result.pageClass).toBe('opted_out');
      expect(result.action).toBeNull();
    });

    it('returns a shallow copy of the CriticalAction (not a reference to internal state)', () => {
      const result = gate.update('/login');
      const action = result.action!;
      // Mutating the returned object must not affect subsequent calls
      (action as { action: string }).action = 'tampered';
      const result2 = gate.update('/login');
      expect(result2.action?.action).toBe('login_submit');
    });

    it('updates getCurrentClass() after each call', () => {
      expect(gate.getCurrentClass()).toBe('normal');
      gate.update('/login');
      expect(gate.getCurrentClass()).toBe('critical_action');
      gate.update('/dashboard');
      expect(gate.getCurrentClass()).toBe('normal');
    });

    it('updates getCurrentPath() after each call', () => {
      expect(gate.getCurrentPath()).toBe('');
      gate.update('/login');
      expect(gate.getCurrentPath()).toBe('/login');
      gate.update('/transfer');
      expect(gate.getCurrentPath()).toBe('/transfer');
    });
  });

  describe('getCriticalActionForPath()', () => {
    let gate: PageGate;

    beforeEach(() => {
      gate = new PageGate(makeConfig());
    });

    it('returns the matching action for a critical-action path', () => {
      const action = gate.getCriticalActionForPath('/login');
      expect(action).not.toBeNull();
      expect(action?.action).toBe('login_submit');
    });

    it('returns the first matching action when multiple actions share a pattern', () => {
      const multiGate = new PageGate(
        makeConfig({
          criticalActions: [
            {
              page: /\/transfer/,
              action: 'transfer_confirm',
              commit: { selector: '[data-kp-commit="transfer"]' },
            },
            {
              page: /\/transfer\/review/,
              action: 'transfer_review',
              commit: { selector: 'button.review' },
            },
          ],
        }),
      );
      // /transfer/review matches both — first one wins
      const action = multiGate.getCriticalActionForPath('/transfer/review');
      expect(action?.action).toBe('transfer_confirm');
    });

    it('returns null for a non-matching path', () => {
      const action = gate.getCriticalActionForPath('/dashboard');
      expect(action).toBeNull();
    });

    it('returns null when critical_actions list is empty', () => {
      const emptyGate = new PageGate(makeConfig({ criticalActions: [] }));
      expect(emptyGate.getCriticalActionForPath('/login')).toBeNull();
    });

    it('returns a shallow copy — mutating the result does not corrupt internal state', () => {
      const action = gate.getCriticalActionForPath('/login')!;
      (action as { action: string }).action = 'hacked';
      // Subsequent call must still return the original value
      expect(gate.getCriticalActionForPath('/login')?.action).toBe('login_submit');
    });

    it('returns the commit selector correctly for a matched action', () => {
      const action = gate.getCriticalActionForPath('/transfer');
      expect(action?.commit.selector).toBe('[data-kp-commit="transfer"]');
    });
  });

  describe('getCurrentAction()', () => {
    it('returns null before any update', () => {
      const gate = new PageGate(makeConfig());
      expect(gate.getCurrentAction()).toBeNull();
    });

    it('returns the matched action after update() on a critical_action path', () => {
      const gate = new PageGate(makeConfig());
      gate.update('/login');
      expect(gate.getCurrentAction()?.action).toBe('login_submit');
    });

    it('returns null after navigating away from a critical_action page', () => {
      const gate = new PageGate(makeConfig());
      gate.update('/login');
      gate.update('/dashboard');
      expect(gate.getCurrentAction()).toBeNull();
    });
  });
});
