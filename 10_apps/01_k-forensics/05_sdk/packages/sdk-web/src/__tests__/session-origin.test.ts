/**
 * session-origin.test.ts
 *
 * Tests for Finding 11: Session origin binding.
 * Validates that session_id is bound to origin via SHA-256(session_id + origin),
 * origin_hash is included in SessionState and batches, and origin mismatch
 * on resume forces a new session.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { SessionManager } from '../session/session-manager.js';
import type { IdentityStore } from '../session/identity-store.js';
import type { ResolvedConfig, WorkerToMainMsg } from '../runtime/wire-protocol.js';

// ─── Helpers ─────────────────────────────────────────────────────────────────

function makeIdentityStore(isIdentityCaptured = true) {
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

function makeConfig(): ResolvedConfig {
  return {
    api_key: 'kp_test_abc',
    environment: 'debug',
    transport: { mode: 'direct', endpoint: 'https://api.kprotect.io/v1/behavioral/ingest' },
    session: {
      pulse_interval_ms: 5000,
      idle_timeout_ms: 15 * 60 * 1000,
      keepalive_interval_ms: 30000,
    },
    identity: { username: { selectors: [], sso_globals: [] } },
    page_gate: { opt_out_patterns: [] },
    critical_actions: { actions: [] },
    fingerprinting: { enabled: true },
    consent: { mode: 'opt-out' },
  };
}

/**
 * Reference SHA-256 computation using Web Crypto API.
 * Used to verify the SessionManager produces the correct origin_hash.
 */
async function referenceSha256(input: string): Promise<string> {
  const encoded = new TextEncoder().encode(input);
  const buffer = await crypto.subtle.digest('SHA-256', encoded);
  return Array.from(new Uint8Array(buffer))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

// ─── Tests ───────────────────────────────────────────────────────────────────

describe('Session origin binding', () => {
  const TEST_SESSION_ID = '550e8400-e29b-41d4-a716-446655440000';
  const TEST_ORIGIN = 'https://bank.example.com';

  let postToMain: ReturnType<typeof vi.fn>;
  let onPulse: ReturnType<typeof vi.fn>;
  let onIdle: ReturnType<typeof vi.fn>;
  let identityStore: ReturnType<typeof makeIdentityStore>;

  beforeEach(() => {
    vi.useFakeTimers();
    postToMain = vi.fn();
    onPulse = vi.fn();
    onIdle = vi.fn();
    identityStore = makeIdentityStore(true);

    vi.stubGlobal('crypto', {
      randomUUID: vi.fn().mockReturnValue(TEST_SESSION_ID),
      subtle: globalThis.crypto.subtle,
      getRandomValues: globalThis.crypto.getRandomValues.bind(globalThis.crypto),
    });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('generates origin_hash on session start', async () => {
    const sm = new SessionManager(
      makeConfig(),
      identityStore as unknown as IdentityStore,
      postToMain,
      onPulse,
      onIdle,
      TEST_ORIGIN,
    );

    await sm.start();

    const state = sm.getSessionState();
    expect(state.origin_hash).toBeDefined();
    expect(typeof state.origin_hash).toBe('string');
    expect(state.origin_hash!.length).toBe(64); // SHA-256 hex = 64 chars
  });

  it('origin_hash equals SHA-256(session_id + origin)', async () => {
    const sm = new SessionManager(
      makeConfig(),
      identityStore as unknown as IdentityStore,
      postToMain,
      onPulse,
      onIdle,
      TEST_ORIGIN,
    );

    await sm.start();

    const expected = await referenceSha256(TEST_SESSION_ID + TEST_ORIGIN);
    const state = sm.getSessionState();
    expect(state.origin_hash).toBe(expected);
  });

  it('includes origin_hash in SessionState', async () => {
    const sm = new SessionManager(
      makeConfig(),
      identityStore as unknown as IdentityStore,
      postToMain,
      onPulse,
      onIdle,
      TEST_ORIGIN,
    );

    await sm.start();

    const state = sm.getSessionState();
    expect(state).toHaveProperty('origin_hash');
    expect(state.origin_hash).not.toBeNull();
  });

  it('origin_hash is null before session starts', () => {
    const sm = new SessionManager(
      makeConfig(),
      identityStore as unknown as IdentityStore,
      postToMain,
      onPulse,
      onIdle,
      TEST_ORIGIN,
    );

    const state = sm.getSessionState();
    expect(state.origin_hash).toBeNull();
  });

  it('getOriginHash returns the computed hash', async () => {
    const sm = new SessionManager(
      makeConfig(),
      identityStore as unknown as IdentityStore,
      postToMain,
      onPulse,
      onIdle,
      TEST_ORIGIN,
    );

    await sm.start();

    const hash = sm.getOriginHash();
    expect(hash).not.toBeNull();

    const expected = await referenceSha256(TEST_SESSION_ID + TEST_ORIGIN);
    expect(hash).toBe(expected);
  });

  it('origin mismatch on resume forces a new session', async () => {
    const sm = new SessionManager(
      makeConfig(),
      identityStore as unknown as IdentityStore,
      postToMain,
      onPulse,
      onIdle,
      TEST_ORIGIN,
    );

    await sm.start();

    const originalSessionId = sm.getSessionId();
    const originalOriginHash = sm.getOriginHash();

    // Simulate tab going hidden
    sm.setVisibility(false);

    // Change origin (simulating a hijack scenario)
    sm.setOrigin('https://evil.example.com');

    // Tab becomes visible again — should detect origin mismatch
    // and force a new session
    await sm.setVisibility(true);

    // Session should have been ended and restarted
    const endedCalls = postToMain.mock.calls.filter(
      (call) => (call[0] as Record<string, unknown>).type === 'SESSION_ENDED',
    );
    expect(endedCalls.length).toBeGreaterThanOrEqual(1);

    // The end reason should indicate origin mismatch
    const endMsg = endedCalls[endedCalls.length - 1]![0] as { type: string; reason: string };
    expect(endMsg.reason).toBe('origin_mismatch');
  });

  it('same origin on resume does NOT force a new session', async () => {
    const sm = new SessionManager(
      makeConfig(),
      identityStore as unknown as IdentityStore,
      postToMain,
      onPulse,
      onIdle,
      TEST_ORIGIN,
    );

    await sm.start();

    const originalSessionId = sm.getSessionId();

    // Simulate tab hidden then visible with SAME origin
    sm.setVisibility(false);
    sm.setVisibility(true);

    // Session should NOT have ended due to origin mismatch
    const endedCalls = postToMain.mock.calls.filter(
      (call) => {
        const msg = call[0] as Record<string, unknown>;
        return msg.type === 'SESSION_ENDED' && msg.reason === 'origin_mismatch';
      },
    );
    expect(endedCalls.length).toBe(0);

    // Session ID should remain the same
    expect(sm.getSessionId()).toBe(originalSessionId);
  });

  it('works without origin (graceful degradation)', async () => {
    const sm = new SessionManager(
      makeConfig(),
      identityStore as unknown as IdentityStore,
      postToMain,
      onPulse,
      onIdle,
      // No origin passed
    );

    await sm.start();

    const state = sm.getSessionState();
    // origin_hash should be null when no origin is available
    expect(state.origin_hash).toBeNull();
  });

  it('different sessions get different origin_hashes', async () => {
    const sm = new SessionManager(
      makeConfig(),
      identityStore as unknown as IdentityStore,
      postToMain,
      onPulse,
      onIdle,
      TEST_ORIGIN,
    );

    await sm.start();
    const hash1 = sm.getOriginHash();

    // End and start a new session with a different UUID
    sm.end('logout');
    vi.mocked(crypto.randomUUID).mockReturnValue('aaaabbbb-cccc-dddd-eeee-ffffffffffff');
    await sm.start();
    const hash2 = sm.getOriginHash();

    // Different session_id + same origin = different origin_hash
    expect(hash1).not.toBe(hash2);
    expect(hash1).not.toBeNull();
    expect(hash2).not.toBeNull();
  });
});
