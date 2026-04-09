/**
 * session-manager.test.ts
 *
 * Tests for SessionManager: start/end lifecycle, pulse loop, visibility gating,
 * idle timeout, and page-class cadence switching.
 *
 * All time-based tests use vi.useFakeTimers() to control setInterval/setTimeout.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { SessionManager } from '../session/session-manager.js';
import type { IdentityStore } from '../session/identity-store.js';
import type { ResolvedConfig, WorkerToMainMsg, CriticalAction } from '../runtime/wire-protocol.js';

// ─── Minimal IdentityStore stub ───────────────────────────────────────────────

function makeIdentityStore(isIdentityCaptured = false) {
  return {
    isIdentityCaptured: vi.fn().mockReturnValue(isIdentityCaptured),
    getDeviceUuid: vi.fn().mockReturnValue('device-uuid-001'),
    getUserHash: vi.fn().mockReturnValue(isIdentityCaptured ? 'hash-abc' : null),
    getUsername: vi.fn().mockReturnValue(null),
    setUsername: vi.fn(),
    clearUsername: vi.fn(),
    clearAll: vi.fn(),
    init: vi.fn(),
  };
}

// ─── Config helper ────────────────────────────────────────────────────────────

function makeConfig(overrides: Partial<{
  pulse_interval_ms: number;
  idle_timeout_ms: number;
  keepalive_interval_ms: number;
}> = {}): ResolvedConfig {
  return {
    api_key: 'kp_test_abc',
    environment: 'debug',
    transport: { mode: 'direct', endpoint: 'https://api.kprotect.io/v1/behavioral/ingest' },
    session: {
      pulse_interval_ms: overrides.pulse_interval_ms ?? 5000,
      idle_timeout_ms: overrides.idle_timeout_ms ?? 15 * 60 * 1000,
      keepalive_interval_ms: overrides.keepalive_interval_ms ?? 30000,
    },
    identity: { username: { selectors: [], sso_globals: [] } },
    page_gate: { opt_out_patterns: [] },
    critical_actions: { actions: [] },
    fingerprinting: { enabled: true },
    consent: { mode: 'opt-out' },
  };
}

function makeCriticalAction(action = 'login_submit'): CriticalAction {
  return {
    page: /\/login/,
    action,
    commit: { selector: 'button[type="submit"]' },
  };
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('SessionManager', () => {
  let postToMain: ReturnType<typeof vi.fn>;
  let onPulse: ReturnType<typeof vi.fn>;
  let onIdle: ReturnType<typeof vi.fn>;
  let identityStore: ReturnType<typeof makeIdentityStore>;

  beforeEach(() => {
    vi.useFakeTimers();

    postToMain = vi.fn();
    onPulse = vi.fn();
    onIdle = vi.fn();
    identityStore = makeIdentityStore(true); // identity captured by default

    vi.stubGlobal('crypto', {
      randomUUID: vi.fn().mockReturnValue('550e8400-e29b-41d4-a716-446655440000'),
    });
    vi.stubGlobal('performance', { now: vi.fn().mockReturnValue(1000) });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  function makeManager(
    configOverrides: Parameters<typeof makeConfig>[0] = {},
    identityCaptured = true,
  ): SessionManager {
    identityStore = makeIdentityStore(identityCaptured);
    return new SessionManager(
      makeConfig(configOverrides),
      identityStore as unknown as IdentityStore,
      postToMain as (msg: WorkerToMainMsg) => void,
      onPulse,
      onIdle,
    );
  }

  // ── start() ─────────────────────────────────────────────────────────────────

  describe('start()', () => {
    it('sets phase to "active"', async () => {
      const mgr = makeManager();
      await mgr.start();
      expect(mgr.getPhase()).toBe('active');
    });

    it('posts SESSION_STARTED to main thread', async () => {
      const mgr = makeManager();
      await mgr.start();
      expect(postToMain).toHaveBeenCalledWith(
        expect.objectContaining({ type: 'SESSION_STARTED' }),
      );
    });

    it('mints a session_id in UUID format', async () => {
      const mgr = makeManager();
      await mgr.start();
      const call = postToMain.mock.calls.find(
        (c) => (c[0] as WorkerToMainMsg).type === 'SESSION_STARTED',
      );
      const msg = call![0] as { type: 'SESSION_STARTED'; session_id: string };
      expect(msg.session_id).toBe('550e8400-e29b-41d4-a716-446655440000');
    });

    it('starts pulse counter at 0', async () => {
      const mgr = makeManager();
      await mgr.start();
      const call = postToMain.mock.calls.find(
        (c) => (c[0] as WorkerToMainMsg).type === 'SESSION_STARTED',
      );
      const msg = call![0] as { type: 'SESSION_STARTED'; pulse: number };
      expect(msg.pulse).toBe(0);
      expect(mgr.getPulse()).toBe(0);
    });

    it('getSessionId() returns the minted UUID', async () => {
      const mgr = makeManager();
      expect(mgr.getSessionId()).toBeNull();
      await mgr.start();
      expect(mgr.getSessionId()).toBe('550e8400-e29b-41d4-a716-446655440000');
    });
  });

  // ── end() ───────────────────────────────────────────────────────────────────

  describe('end()', () => {
    it('posts SESSION_ENDED with correct reason', async () => {
      const mgr = makeManager();
      await mgr.start();
      mgr.end('logout');
      expect(postToMain).toHaveBeenCalledWith(
        expect.objectContaining({ type: 'SESSION_ENDED', reason: 'logout' }),
      );
    });

    it('includes the session_id in SESSION_ENDED', async () => {
      const mgr = makeManager();
      await mgr.start();
      mgr.end('pagehide');
      const call = postToMain.mock.calls.find(
        (c) => (c[0] as WorkerToMainMsg).type === 'SESSION_ENDED',
      );
      const msg = call![0] as { type: 'SESSION_ENDED'; session_id: string };
      expect(msg.session_id).toBe('550e8400-e29b-41d4-a716-446655440000');
    });

    it('clears the pulse loop (no more onPulse calls after end)', async () => {
      const mgr = makeManager({ pulse_interval_ms: 1000 });
      await mgr.start();
      mgr.end('logout');
      onPulse.mockClear();
      vi.advanceTimersByTime(5000);
      expect(onPulse).not.toHaveBeenCalled();
    });

    it('sets phase to "ended"', async () => {
      const mgr = makeManager();
      await mgr.start();
      mgr.end('destroy');
      expect(mgr.getPhase()).toBe('ended');
    });

    it('does not post SESSION_ENDED when no session was started', () => {
      const mgr = makeManager();
      mgr.end('logout'); // session_id is null — should not post
      const calls = postToMain.mock.calls.filter(
        (c) => (c[0] as WorkerToMainMsg).type === 'SESSION_ENDED',
      );
      expect(calls).toHaveLength(0);
    });
  });

  // ── pulse loop ───────────────────────────────────────────────────────────────

  describe('pulse loop', () => {
    it('calls onPulse after pulse_interval_ms', async () => {
      const mgr = makeManager({ pulse_interval_ms: 5000 });
      await mgr.start();
      expect(onPulse).not.toHaveBeenCalled();
      vi.advanceTimersByTime(5000);
      expect(onPulse).toHaveBeenCalledTimes(1);
      expect(onPulse).toHaveBeenCalledWith('normal');
    });

    it('increments pulse counter by 1 per tick', async () => {
      const mgr = makeManager({ pulse_interval_ms: 1000 });
      await mgr.start();
      vi.advanceTimersByTime(3000);
      expect(mgr.getPulse()).toBe(3);
    });

    it('does NOT fire onPulse before username capture (preIdentity=true)', async () => {
      const mgr = makeManager({ pulse_interval_ms: 1000 }, false); // identity NOT captured
      await mgr.start();
      vi.advanceTimersByTime(3000);
      expect(onPulse).not.toHaveBeenCalled();
      // Pulse counter should not have incremented either
      expect(mgr.getPulse()).toBe(0);
    });

    it('fires onPulse immediately after onUsernameCapture() is called', async () => {
      const mgr = makeManager({ pulse_interval_ms: 5000 }, false);
      await mgr.start();
      vi.advanceTimersByTime(2000); // Not enough to tick
      expect(onPulse).not.toHaveBeenCalled();

      // Simulate identity capture
      identityStore.isIdentityCaptured.mockReturnValue(true);
      mgr.onUsernameCapture();

      // Should fire a catch-up pulse immediately
      expect(onPulse).toHaveBeenCalledTimes(1);
      expect(mgr.getPulse()).toBe(1);
    });

    it('pauses when tab is hidden (setVisibility(false))', async () => {
      const mgr = makeManager({ pulse_interval_ms: 1000 });
      await mgr.start();
      vi.advanceTimersByTime(2000); // 2 pulses
      expect(mgr.getPulse()).toBe(2);

      await mgr.setVisibility(false);
      vi.advanceTimersByTime(3000); // 3 more ticks — but should be suppressed
      expect(mgr.getPulse()).toBe(2); // counter does not advance
    });

    it('fires a catch-up pulse on resume (setVisibility(true))', async () => {
      const mgr = makeManager({ pulse_interval_ms: 1000 });
      await mgr.start();
      vi.advanceTimersByTime(1000); // 1 pulse
      expect(mgr.getPulse()).toBe(1);

      await mgr.setVisibility(false);
      vi.advanceTimersByTime(3000); // 3 ticks missed

      await mgr.setVisibility(true); // resume
      // Should fire ONE catch-up pulse immediately
      expect(onPulse).toHaveBeenCalledWith('normal');
      expect(mgr.getPulse()).toBe(2); // only +1, not +3
    });

    it('counter increments by exactly 1 on catch-up, not by missed tick count', async () => {
      const mgr = makeManager({ pulse_interval_ms: 1000 });
      await mgr.start();
      await mgr.setVisibility(false);
      vi.advanceTimersByTime(10000); // many ticks missed
      await mgr.setVisibility(true);
      expect(mgr.getPulse()).toBe(1); // exactly 1 catch-up pulse
    });

    it('fires onPulse with "keepalive" phase on critical_action pages', async () => {
      const mgr = makeManager({ keepalive_interval_ms: 2000 });
      await mgr.start();
      mgr.setPageClass('critical_action', makeCriticalAction());
      vi.advanceTimersByTime(2000);
      expect(onPulse).toHaveBeenCalledWith('keepalive');
    });
  });

  // ── setPageClass() ───────────────────────────────────────────────────────────

  describe('setPageClass()', () => {
    it('switches to keepalive cadence for critical_action pages', async () => {
      const mgr = makeManager({ pulse_interval_ms: 5000, keepalive_interval_ms: 2000 });
      await mgr.start();

      // Normal: should tick at 5000ms
      mgr.setPageClass('critical_action', makeCriticalAction());

      // Should tick at 2000ms (keepalive), not 5000ms
      vi.advanceTimersByTime(2000);
      expect(onPulse).toHaveBeenCalledWith('keepalive');
      onPulse.mockClear();

      // Should NOT have ticked at 5000ms in normal mode
      vi.advanceTimersByTime(2000); // t=4000 total
      expect(onPulse).toHaveBeenCalledTimes(1); // 1 more keepalive tick
    });

    it('switches back to normal cadence for normal pages', async () => {
      const mgr = makeManager({ pulse_interval_ms: 1000, keepalive_interval_ms: 5000 });
      await mgr.start();
      mgr.setPageClass('critical_action', makeCriticalAction());
      mgr.setPageClass('normal');
      vi.advanceTimersByTime(1000);
      expect(onPulse).toHaveBeenCalledWith('normal');
    });

    it('stops pulsing entirely for opted_out pages', async () => {
      const mgr = makeManager({ pulse_interval_ms: 1000 });
      await mgr.start();
      mgr.setPageClass('opted_out');
      vi.advanceTimersByTime(5000);
      expect(onPulse).not.toHaveBeenCalled();
    });

    it('does not restart interval when page class does not change', async () => {
      const mgr = makeManager({ pulse_interval_ms: 1000 });
      await mgr.start();
      // Normal -> normal: interval should keep running without reset
      vi.advanceTimersByTime(500); // halfway through tick
      mgr.setPageClass('normal'); // no change — should not restart interval
      vi.advanceTimersByTime(500); // complete the original tick
      expect(onPulse).toHaveBeenCalledTimes(1);
    });

    it('updates current_action in session state for critical_action page', async () => {
      const mgr = makeManager();
      await mgr.start();
      mgr.setPageClass('critical_action', makeCriticalAction('payment_confirm'));
      const state = mgr.getSessionState();
      expect(state.current_action).toBe('payment_confirm');
    });

    it('sets current_action to null for normal pages', async () => {
      const mgr = makeManager();
      await mgr.start();
      mgr.setPageClass('critical_action', makeCriticalAction());
      mgr.setPageClass('normal');
      const state = mgr.getSessionState();
      expect(state.current_action).toBeNull();
    });
  });

  // ── idle timeout ─────────────────────────────────────────────────────────────

  describe('idle timeout', () => {
    it('fires onIdle after idle_timeout_ms of being hidden', async () => {
      const mgr = makeManager({ idle_timeout_ms: 5000 });
      await mgr.start();
      await mgr.setVisibility(false);
      expect(onIdle).not.toHaveBeenCalled();
      vi.advanceTimersByTime(5000);
      expect(onIdle).toHaveBeenCalledTimes(1);
    });

    it('does NOT fire onIdle if tab becomes visible before timeout', async () => {
      const mgr = makeManager({ idle_timeout_ms: 5000 });
      await mgr.start();
      await mgr.setVisibility(false);
      vi.advanceTimersByTime(4000); // not yet expired
      await mgr.setVisibility(true); // cancel the idle timer
      vi.advanceTimersByTime(5000); // well past the original timeout
      expect(onIdle).not.toHaveBeenCalled();
    });

    it('calls end("idle_timeout") via onIdle being followed by end in the manager', async () => {
      // The manager calls onIdle() AND then end('idle_timeout') internally
      const mgr = makeManager({ idle_timeout_ms: 2000 });
      await mgr.start();
      await mgr.setVisibility(false);
      vi.advanceTimersByTime(2000);

      // SESSION_ENDED with idle_timeout should have been posted
      expect(postToMain).toHaveBeenCalledWith(
        expect.objectContaining({ type: 'SESSION_ENDED', reason: 'idle_timeout' }),
      );
      expect(mgr.getPhase()).toBe('ended');
    });

    it('sets phase to "idle" when tab goes hidden', async () => {
      const mgr = makeManager();
      await mgr.start();
      await mgr.setVisibility(false);
      expect(mgr.getPhase()).toBe('idle');
    });

    it('resets phase to "active" when tab comes back visible before idle timeout', async () => {
      const mgr = makeManager({ idle_timeout_ms: 10000 });
      await mgr.start();
      await mgr.setVisibility(false);
      expect(mgr.getPhase()).toBe('idle');
      vi.advanceTimersByTime(5000);
      await mgr.setVisibility(true);
      expect(mgr.getPhase()).toBe('active');
    });

    it('only fires idle once even if called multiple times', async () => {
      const mgr = makeManager({ idle_timeout_ms: 1000 });
      await mgr.start();
      await mgr.setVisibility(false);
      vi.advanceTimersByTime(1000);
      vi.advanceTimersByTime(5000); // long extra wait
      expect(onIdle).toHaveBeenCalledTimes(1);
    });
  });

  // ── getSessionState() ─────────────────────────────────────────────────────────

  describe('getSessionState()', () => {
    it('returns uninitialised phase before start()', () => {
      const mgr = makeManager();
      const state = mgr.getSessionState();
      expect(state.phase).toBe('uninitialised');
    });

    it('returns a full state snapshot with all required fields', async () => {
      const mgr = makeManager();
      await mgr.start();
      const state = mgr.getSessionState();
      expect(state).toMatchObject({
        phase: 'active',
        session_id: '550e8400-e29b-41d4-a716-446655440000',
        pulse: 0,
        identity_captured: true,
        page_class: 'normal',
        current_action: null,
        transport_queue_depth: 0,
        ring_buffer_depth: 0,
        last_drift_score: null,
        last_action: null,
      });
    });

    it('reflects incremented pulse count', async () => {
      const mgr = makeManager({ pulse_interval_ms: 1000 });
      await mgr.start();
      vi.advanceTimersByTime(3000);
      const state = mgr.getSessionState();
      expect(state.pulse).toBe(3);
    });
  });
});
