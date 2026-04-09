/**
 * critical-action-router.test.ts
 *
 * Tests for CriticalActionRouter: staging, commit, abandon, clear, reset.
 */

import { describe, it, expect, beforeEach, vi, type Mock } from 'vitest';
import {
  CriticalActionRouter,
  type StagedWindow,
} from '../session/critical-action-router.js';
import type { SignalSet } from '../runtime/wire-protocol.js';

// ─── Test helpers ─────────────────────────────────────────────────────────────

function makeSessionContext(overrides: Partial<{
  session_id: string;
  pulse: number;
  user_hash: string;
  device_uuid: string;
  pulse_interval_ms: number;
  environment: 'production' | 'debug';
  session_start_epoch: number;
}> = {}) {
  return {
    session_id: overrides.session_id ?? 'sess-123',
    pulse: overrides.pulse ?? 5,
    user_hash: overrides.user_hash ?? 'abc123hash',
    device_uuid: overrides.device_uuid ?? 'device-uuid-456',
    pulse_interval_ms: overrides.pulse_interval_ms ?? 5000,
    environment: overrides.environment ?? ('debug' as const),
    session_start_epoch: overrides.session_start_epoch ?? 1700000000000,
  };
}

function makeStagedWindow(overrides: Partial<StagedWindow> = {}): StagedWindow {
  return {
    window_start_ms: overrides.window_start_ms ?? 1000,
    window_end_ms: overrides.window_end_ms ?? 6000,
    event_count: overrides.event_count ?? 42,
    signals: overrides.signals ?? {},
  };
}

function makeSignals(): SignalSet {
  return {
    scroll: {
      available: true,
      scroll_events: 10,
      mean_velocity: 0.5,
      mean_distance_per_scroll: 200,
      reading_pause_count: 2,
      rapid_scroll_count: 1,
      direction_distribution: { up: 0.3, down: 0.6, horizontal: 0.1 },
    },
  };
}

// ─── CriticalActionRouter tests ───────────────────────────────────────────────

type SessionContext = {
  session_id: string;
  pulse: number;
  user_hash: string;
  device_uuid: string;
  pulse_interval_ms: number;
  environment: 'production' | 'debug';
  session_start_epoch: number;
};

describe('CriticalActionRouter', () => {
  let router: CriticalActionRouter;
  let getSessionContext: Mock<[], SessionContext>;

  beforeEach(() => {
    getSessionContext = vi.fn(() => makeSessionContext());
    router = new CriticalActionRouter(getSessionContext);

    // Stub performance.now() so time calculations are deterministic
    vi.stubGlobal('performance', { now: vi.fn().mockReturnValue(1000) });

    // Stub crypto.randomUUID for deterministic batch_id
    vi.stubGlobal('crypto', {
      randomUUID: vi.fn().mockReturnValue('00000000-0000-0000-0000-000000000001'),
    });
  });

  describe('stage()', () => {
    it('adds a window to the staging buffer', () => {
      router.stage(makeStagedWindow());
      expect(router.getStagedCount()).toBe(1);
    });

    it('accumulates multiple staged windows', () => {
      router.stage(makeStagedWindow({ window_start_ms: 1000, window_end_ms: 6000 }));
      router.stage(makeStagedWindow({ window_start_ms: 6000, window_end_ms: 11000 }));
      router.stage(makeStagedWindow({ window_start_ms: 11000, window_end_ms: 16000 }));
      expect(router.getStagedCount()).toBe(3);
    });

    it('does not mutate the input window (stores a shallow copy)', () => {
      const original = makeStagedWindow({ event_count: 10 });
      router.stage(original);
      // Mutate the original after staging
      (original as { event_count: number }).event_count = 999;
      // The staged count should still be 1 (object was copied, not referenced differently)
      expect(router.getStagedCount()).toBe(1);
      // Commit and verify the staged event_count is the original value
      const batch = router.commit('login_submit', '/login');
      expect(batch?.event_count).toBe(10);
    });

    it('increments getStagedCount() by 1 per stage() call', () => {
      expect(router.getStagedCount()).toBe(0);
      router.stage(makeStagedWindow());
      expect(router.getStagedCount()).toBe(1);
      router.stage(makeStagedWindow());
      expect(router.getStagedCount()).toBe(2);
    });

    it('sets hasStagedData() to true after first stage()', () => {
      expect(router.hasStagedData()).toBe(false);
      router.stage(makeStagedWindow());
      expect(router.hasStagedData()).toBe(true);
    });
  });

  describe('commit()', () => {
    it('returns null when no windows are staged', () => {
      const batch = router.commit('login_submit', '/login');
      expect(batch).toBeNull();
    });

    it('returns a CriticalActionBatch with committed: true', () => {
      router.stage(makeStagedWindow());
      const batch = router.commit('login_submit', '/login');
      expect(batch).not.toBeNull();
      expect(batch?.page_context.committed).toBe(true);
    });

    it('returns type: "critical_action"', () => {
      router.stage(makeStagedWindow());
      const batch = router.commit('login_submit', '/login');
      expect(batch?.type).toBe('critical_action');
    });

    it('sets correct page_context fields', () => {
      router.stage(makeStagedWindow());
      const batch = router.commit('login_submit', '/login', '/home');
      expect(batch?.page_context.url_path).toBe('/login');
      expect(batch?.page_context.page_class).toBe('critical_action');
      expect(batch?.page_context.critical_action).toBe('login_submit');
      expect(batch?.page_context.committed).toBe(true);
      expect(batch?.page_context.referrer_path).toBe('/home');
    });

    it('omits referrer_path when not provided', () => {
      router.stage(makeStagedWindow());
      const batch = router.commit('login_submit', '/login');
      expect(batch?.page_context.referrer_path).toBeUndefined();
    });

    it('aggregates event_count from multiple staged windows', () => {
      router.stage(makeStagedWindow({ event_count: 20 }));
      router.stage(makeStagedWindow({ event_count: 30 }));
      router.stage(makeStagedWindow({ event_count: 15 }));
      const batch = router.commit('transfer_confirm', '/transfer');
      expect(batch?.event_count).toBe(65);
    });

    it('aggregates signals from multiple staged windows', () => {
      router.stage(makeStagedWindow({
        signals: {
          scroll: {
            available: true,
            scroll_events: 5,
            mean_velocity: 0.4,
            mean_distance_per_scroll: 100,
            reading_pause_count: 1,
            rapid_scroll_count: 0,
            direction_distribution: { up: 0.2, down: 0.7, horizontal: 0.1 },
          },
        },
      }));
      router.stage(makeStagedWindow({
        signals: {
          scroll: {
            available: true,
            scroll_events: 10,
            mean_velocity: 0.6,
            mean_distance_per_scroll: 200,
            reading_pause_count: 3,
            rapid_scroll_count: 2,
            direction_distribution: { up: 0.3, down: 0.5, horizontal: 0.2 },
          },
        },
      }));
      const batch = router.commit('login_submit', '/login');
      // Scroll events are summed across windows
      expect(batch?.signals.scroll?.scroll_events).toBe(15);
    });

    it('includes session context from getSessionContext()', () => {
      getSessionContext.mockReturnValue(makeSessionContext({
        session_id: 'my-session-id',
        pulse: 7,
        user_hash: 'deadbeef',
        device_uuid: 'my-device',
        pulse_interval_ms: 5000,
        environment: 'production',
      }));
      router.stage(makeStagedWindow());
      const batch = router.commit('login_submit', '/login');
      expect(batch?.session_id).toBe('my-session-id');
      expect(batch?.pulse).toBe(7);
      expect(batch?.user_hash).toBe('deadbeef');
      expect(batch?.device_uuid).toBe('my-device');
      expect(batch?.sdk.environment).toBe('production');
    });

    it('sets window_start_ms from the first staged window', () => {
      router.stage(makeStagedWindow({ window_start_ms: 1000, window_end_ms: 6000 }));
      router.stage(makeStagedWindow({ window_start_ms: 6000, window_end_ms: 11000 }));
      const batch = router.commit('login_submit', '/login');
      expect(batch?.window_start_ms).toBe(1000);
    });

    it('sets window_end_ms from the last staged window', () => {
      router.stage(makeStagedWindow({ window_start_ms: 1000, window_end_ms: 6000 }));
      router.stage(makeStagedWindow({ window_start_ms: 6000, window_end_ms: 11000 }));
      const batch = router.commit('login_submit', '/login');
      expect(batch?.window_end_ms).toBe(11000);
    });

    it('sets sdk.platform to "web"', () => {
      router.stage(makeStagedWindow());
      const batch = router.commit('login_submit', '/login');
      expect(batch?.sdk.platform).toBe('web');
    });

    it('uses crypto.randomUUID() for batch_id', () => {
      router.stage(makeStagedWindow());
      const batch = router.commit('login_submit', '/login');
      expect(batch?.batch_id).toBe('00000000-0000-0000-0000-000000000001');
    });
  });

  describe('abandon()', () => {
    it('returns null when no windows are staged', () => {
      const batch = router.abandon('login_submit', '/login');
      expect(batch).toBeNull();
    });

    it('returns a CriticalActionBatch with committed: false', () => {
      router.stage(makeStagedWindow());
      const batch = router.abandon('login_submit', '/login');
      expect(batch).not.toBeNull();
      expect(batch?.page_context.committed).toBe(false);
    });

    it('returns type: "critical_action"', () => {
      router.stage(makeStagedWindow());
      const batch = router.abandon('login_submit', '/login');
      expect(batch?.type).toBe('critical_action');
    });

    it('includes all session context fields', () => {
      router.stage(makeStagedWindow());
      const batch = router.abandon('transfer_confirm', '/transfer', '/dashboard');
      expect(batch?.page_context.referrer_path).toBe('/dashboard');
      expect(batch?.page_context.critical_action).toBe('transfer_confirm');
    });

    it('aggregates event_count from staged windows just like commit()', () => {
      router.stage(makeStagedWindow({ event_count: 8 }));
      router.stage(makeStagedWindow({ event_count: 12 }));
      const batch = router.abandon('login_submit', '/login');
      expect(batch?.event_count).toBe(20);
    });
  });

  describe('clear()', () => {
    it('empties the staging buffer', () => {
      router.stage(makeStagedWindow());
      router.stage(makeStagedWindow());
      router.clear();
      expect(router.getStagedCount()).toBe(0);
    });

    it('resets hasStagedData() to false', () => {
      router.stage(makeStagedWindow());
      expect(router.hasStagedData()).toBe(true);
      router.clear();
      expect(router.hasStagedData()).toBe(false);
    });

    it('causes subsequent commit() to return null', () => {
      router.stage(makeStagedWindow());
      router.clear();
      expect(router.commit('login_submit', '/login')).toBeNull();
    });

    it('causes subsequent abandon() to return null', () => {
      router.stage(makeStagedWindow());
      router.clear();
      expect(router.abandon('login_submit', '/login')).toBeNull();
    });
  });

  describe('reset()', () => {
    it('clears previously staged windows', () => {
      router.stage(makeStagedWindow());
      router.stage(makeStagedWindow());
      router.reset('new_action');
      expect(router.getStagedCount()).toBe(0);
      expect(router.hasStagedData()).toBe(false);
    });

    it('records the entry timestamp (time_on_page_ms is positive after reset + wait)', () => {
      const nowMock = vi.fn();
      vi.stubGlobal('performance', { now: nowMock });

      // reset() is called at t=0
      nowMock.mockReturnValue(0);
      router.reset('login_submit');

      // stage a window, then commit at t=5000
      nowMock.mockReturnValue(5000);
      router.stage(makeStagedWindow());
      const batch = router.commit('login_submit', '/login');

      // time_on_page_ms = performance.now() - pageEnteredAt = 5000 - 0 = 5000
      expect(batch?.page_context.time_on_page_ms).toBe(5000);
    });

    it('allows staging new windows after reset', () => {
      router.stage(makeStagedWindow());
      router.reset('new_action');
      router.stage(makeStagedWindow({ event_count: 99 }));
      expect(router.getStagedCount()).toBe(1);
      const batch = router.commit('new_action', '/new-page');
      expect(batch?.event_count).toBe(99);
    });
  });

  describe('signal aggregation', () => {
    it('produces an empty signals object when no signals are present in any window', () => {
      router.stage(makeStagedWindow({ signals: {} }));
      router.stage(makeStagedWindow({ signals: {} }));
      const batch = router.commit('login_submit', '/login');
      expect(batch?.signals).toEqual({});
    });

    it('includes scroll signal when at least one window has scroll data', () => {
      router.stage(makeStagedWindow({ signals: {} }));
      router.stage(makeStagedWindow({ signals: makeSignals() }));
      const batch = router.commit('login_submit', '/login');
      expect(batch?.signals.scroll).toBeDefined();
      expect(batch?.signals.scroll?.available).toBe(true);
    });

    it('keystroke dwell_times is a weighted average across windows', () => {
      const ks1 = {
        available: true,
        dwell_times: { mean: 100, std_dev: 10, p25: 80, p50: 100, p75: 120, p95: 150, sample_count: 10 },
        flight_times: { mean: 50, std_dev: 5, p25: 40, p50: 50, p75: 60, p95: 80, sample_count: 10 },
        backspace_rate: 0.5,
        correction_burst_rate: 0.1,
        words_per_minute: 60,
        burst_typing_fraction: 0.3,
        zone_transition_matrix: [[1, 0], [0, 1]],
        zone_ids_used: ['home-row'],
      };
      const ks2 = {
        available: true,
        dwell_times: { mean: 200, std_dev: 20, p25: 160, p50: 200, p75: 240, p95: 300, sample_count: 10 },
        flight_times: { mean: 100, std_dev: 10, p25: 80, p50: 100, p75: 120, p95: 160, sample_count: 10 },
        backspace_rate: 1.0,
        correction_burst_rate: 0.2,
        words_per_minute: 40,
        burst_typing_fraction: 0.2,
        zone_transition_matrix: [[2, 1], [1, 0]],
        zone_ids_used: ['top-row', 'home-row'],
      };
      router.stage(makeStagedWindow({ signals: { keystroke: ks1 } }));
      router.stage(makeStagedWindow({ signals: { keystroke: ks2 } }));
      const batch = router.commit('login_submit', '/login');
      // Weighted mean = (100*10 + 200*10) / 20 = 150
      expect(batch?.signals.keystroke?.dwell_times.mean).toBe(150);
      expect(batch?.signals.keystroke?.dwell_times.sample_count).toBe(20);
    });
  });
});
