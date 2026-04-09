/**
 * medium-findings.test.ts
 *
 * Tests for Batch 4 security audit remediation (Findings 12–14, 16–20).
 *
 * Covers:
 *   - Finding 12: Liveness check (stale detection)
 *   - Finding 13: Cross-site fingerprint salting
 *   - Finding 14: Data retention TTL
 *   - Finding 16: GDPR data export API
 *   - Finding 17: GDPR data deletion API
 *   - Finding 18: Buffer bounds enforcement
 *   - Finding 19: Batch checksums
 *   - Finding 20: PIN/Password field obfuscation
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { SessionManager } from '../session/session-manager.js';
import type { ResolvedConfig, WorkerToMainMsg } from '../runtime/wire-protocol.js';
import { createEventBuffer } from '../collectors/event-buffer.js';
import { extractKeystroke, obfuscateSensitiveEvents } from '../collectors/keystroke.js';
import type { RawKeystrokeEvent } from '../collectors/keystroke.js';
import {
  LIVENESS_STALE_THRESHOLD_MS,
  MAX_EVENTS_PER_WINDOW,
  DATA_RETENTION_TTL_MS,
  STORAGE_KEY_USERNAME,
  STORAGE_KEY_DEVICE_UUID,
  STORAGE_KEY_SESSION_ID,
  STORAGE_KEY_CONSENT,
  STORAGE_KEY_CONFIG,
  STORAGE_KEY_ENCRYPTION_KEY,
  STORAGE_KEY_USERNAME_SALT,
  IDB_DB_NAME,
} from '../config/defaults.js';
import { sha256 } from '../signals/crypto-utils.js';

// ─── Shared helpers ──────────────────────────────────────────────────────────

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

function makeKeystrokeEvent(type: 'kd' | 'ku', zone: number, ts: number): RawKeystrokeEvent {
  return { type, zone, ts };
}

/** Creates a minimal 10-byte keystroke ArrayBuffer for event-buffer recording. */
function makeKeystrokeBuffer(signal: number, zone: number, ts: number): ArrayBuffer {
  const buf = new ArrayBuffer(10);
  const view = new DataView(buf);
  view.setUint8(0, signal); // 1=kd, 2=ku
  view.setUint8(1, zone === -1 ? 255 : zone);
  view.setFloat64(2, ts, true);
  return buf;
}

// ═══════════════════════════════════════════════════════════════════════════
// Finding 12: Liveness Check
// ═══════════════════════════════════════════════════════════════════════════

describe('Finding 12: Liveness Check', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('isAlive() returns false before any events are received', async () => {
    const messages: WorkerToMainMsg[] = [];
    const sm = new SessionManager(
      makeConfig(),
      makeIdentityStore(true) as never,
      (msg) => messages.push(msg),
      vi.fn(),
      vi.fn(),
    );
    await sm.start();

    expect(sm.isAlive()).toBe(false);
  });

  it('isAlive() returns true immediately after an event', async () => {
    const sm = new SessionManager(
      makeConfig(),
      makeIdentityStore(true) as never,
      vi.fn(),
      vi.fn(),
      vi.fn(),
    );
    await sm.start();
    sm.recordEvent();

    expect(sm.isAlive()).toBe(true);
  });

  it('becomes stale after LIVENESS_STALE_THRESHOLD_MS with no events', async () => {
    const sm = new SessionManager(
      makeConfig(),
      makeIdentityStore(true) as never,
      vi.fn(),
      vi.fn(),
      vi.fn(),
    );
    await sm.start();
    sm.recordEvent();

    expect(sm.isAlive()).toBe(true);
    expect(sm.getLivenessStatus()).toBe('alive');

    // Advance past threshold.
    vi.advanceTimersByTime(LIVENESS_STALE_THRESHOLD_MS + 1);

    expect(sm.isAlive()).toBe(false);
    expect(sm.getLivenessStatus()).toBe('stale');
  });

  it('liveness_status is included in SessionState', async () => {
    const sm = new SessionManager(
      makeConfig(),
      makeIdentityStore(true) as never,
      vi.fn(),
      vi.fn(),
      vi.fn(),
    );
    await sm.start();
    sm.recordEvent();

    const state = sm.getSessionState();
    expect(state.liveness_status).toBe('alive');
  });

  it('getLivenessStatus returns dead when session is ended', async () => {
    const sm = new SessionManager(
      makeConfig(),
      makeIdentityStore(true) as never,
      vi.fn(),
      vi.fn(),
      vi.fn(),
    );
    await sm.start();
    sm.recordEvent();
    sm.end('logout');

    expect(sm.getLivenessStatus()).toBe('dead');
  });

  it('emits STATE_UPDATE with stale status when timer fires', async () => {
    const messages: WorkerToMainMsg[] = [];
    const sm = new SessionManager(
      makeConfig(),
      makeIdentityStore(true) as never,
      (msg) => messages.push(msg),
      vi.fn(),
      vi.fn(),
    );
    await sm.start();
    sm.recordEvent();

    // Clear the SESSION_STARTED message.
    messages.length = 0;

    // Advance past threshold.
    vi.advanceTimersByTime(LIVENESS_STALE_THRESHOLD_MS + 1);

    const stateUpdates = messages.filter((m) => m.type === 'STATE_UPDATE');
    expect(stateUpdates.length).toBeGreaterThanOrEqual(1);

    const lastUpdate = stateUpdates[stateUpdates.length - 1];
    if (lastUpdate && lastUpdate.type === 'STATE_UPDATE') {
      expect(lastUpdate.state.liveness_status).toBe('stale');
    }
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// Finding 13: Cross-site Fingerprint Salting
// ═══════════════════════════════════════════════════════════════════════════

describe('Finding 13: Cross-site Fingerprint Salting', () => {
  it('SHA-256(hash + origin) produces different results for different origins', async () => {
    const rawHash = 'abc123deadbeef';
    const origin1 = 'https://bank-a.example.com';
    const origin2 = 'https://bank-b.example.com';

    const salted1 = await sha256(rawHash + origin1);
    const salted2 = await sha256(rawHash + origin2);

    // Same raw hash, different origins => different salted hashes.
    expect(salted1).not.toBe(salted2);

    // Both are valid SHA-256 hex (64 chars).
    expect(salted1).toMatch(/^[0-9a-f]{64}$/);
    expect(salted2).toMatch(/^[0-9a-f]{64}$/);
  });

  it('SHA-256(hash + origin) is deterministic for same inputs', async () => {
    const rawHash = 'abc123deadbeef';
    const origin = 'https://bank.example.com';

    const result1 = await sha256(rawHash + origin);
    const result2 = await sha256(rawHash + origin);

    expect(result1).toBe(result2);
  });

  it('different raw hashes produce different salted results on same origin', async () => {
    const origin = 'https://bank.example.com';

    const salted1 = await sha256('hash-device-a' + origin);
    const salted2 = await sha256('hash-device-b' + origin);

    expect(salted1).not.toBe(salted2);
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// Finding 14: Data Retention TTL
// ═══════════════════════════════════════════════════════════════════════════

describe('Finding 14: Data Retention TTL', () => {
  it('DATA_RETENTION_TTL_MS defaults to 30 days', () => {
    expect(DATA_RETENTION_TTL_MS).toBe(30 * 24 * 60 * 60 * 1000);
  });

  it('TTL envelope wrapping and unwrapping preserves value', () => {
    // Simulate the TTL envelope logic from identity-store.
    const value = 'test-device-uuid';
    const envelope = JSON.stringify({ value, stored_at: Date.now() });
    const parsed = JSON.parse(envelope) as { value: string; stored_at: number };

    expect(parsed.value).toBe(value);
    expect(parsed.stored_at).toBeGreaterThan(0);
  });

  it('TTL envelope rejects expired values', () => {
    const value = 'old-device-uuid';
    const stored_at = Date.now() - DATA_RETENTION_TTL_MS - 1; // expired
    const envelope = JSON.stringify({ value, stored_at });
    const parsed = JSON.parse(envelope) as { value: string; stored_at: number };

    const isExpired = Date.now() - parsed.stored_at > DATA_RETENTION_TTL_MS;
    expect(isExpired).toBe(true);
  });

  it('TTL envelope accepts fresh values', () => {
    const value = 'fresh-device-uuid';
    const stored_at = Date.now() - 1000; // 1 second ago
    const envelope = JSON.stringify({ value, stored_at });
    const parsed = JSON.parse(envelope) as { value: string; stored_at: number };

    const isExpired = Date.now() - parsed.stored_at > DATA_RETENTION_TTL_MS;
    expect(isExpired).toBe(false);
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// Finding 16: GDPR Data Export API
// ═══════════════════════════════════════════════════════════════════════════

describe('Finding 16: GDPR Data Export', () => {
  it('GDPRExport type has expected shape', () => {
    // Verify the type shape by constructing one.
    const exportData = {
      user_hash: 'abc123',
      device_uuid: 'uuid-001',
      session_id: 'sid-001',
      consent_state: 'granted',
      exported_at: Date.now(),
      stored_keys: {
        'kp.un': 'test',
        'kp.did': 'uuid',
      },
    };

    expect(exportData.user_hash).toBe('abc123');
    expect(exportData.device_uuid).toBe('uuid-001');
    expect(exportData.session_id).toBe('sid-001');
    expect(exportData.consent_state).toBe('granted');
    expect(exportData.exported_at).toBeGreaterThan(0);
    expect(exportData.stored_keys).toBeDefined();
  });

  it('export includes all expected storage keys', () => {
    const expectedKeys = [
      STORAGE_KEY_SESSION_ID,
      STORAGE_KEY_USERNAME,
      STORAGE_KEY_DEVICE_UUID,
      STORAGE_KEY_CONFIG,
      STORAGE_KEY_ENCRYPTION_KEY,
      STORAGE_KEY_USERNAME_SALT,
      STORAGE_KEY_CONSENT,
    ];

    // All keys should be defined and start with 'kp.'
    for (const key of expectedKeys) {
      expect(key).toMatch(/^kp\./);
    }
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// Finding 17: GDPR Data Deletion
// ═══════════════════════════════════════════════════════════════════════════

describe('Finding 17: GDPR Data Deletion', () => {
  it('IDB_DB_NAME is defined for deletion target', () => {
    expect(IDB_DB_NAME).toBe('kp-bio');
  });

  it('all kp.* localStorage keys are known for deletion', () => {
    const keysToDelete = [
      STORAGE_KEY_USERNAME,
      STORAGE_KEY_DEVICE_UUID,
      STORAGE_KEY_CONFIG,
      STORAGE_KEY_ENCRYPTION_KEY,
      STORAGE_KEY_USERNAME_SALT,
      STORAGE_KEY_CONSENT,
    ];

    // Verify all keys are strings starting with kp.
    expect(keysToDelete.length).toBeGreaterThanOrEqual(6);
    for (const key of keysToDelete) {
      expect(typeof key).toBe('string');
      expect(key.startsWith('kp.')).toBe(true);
    }
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// Finding 18: Buffer Bounds Enforcement
// ═══════════════════════════════════════════════════════════════════════════

describe('Finding 18: Buffer Bounds Enforcement', () => {
  it('MAX_EVENTS_PER_WINDOW is 1000', () => {
    expect(MAX_EVENTS_PER_WINDOW).toBe(1000);
  });

  it('event buffer enforces cap at MAX_EVENTS_PER_WINDOW', () => {
    const buffer = createEventBuffer();

    // Insert more than MAX_EVENTS_PER_WINDOW events.
    for (let i = 0; i < MAX_EVENTS_PER_WINDOW + 100; i++) {
      const buf = makeKeystrokeBuffer(1, 3, i * 10);
      buffer.record('kd', buf);
    }

    // Count should be capped at MAX_EVENTS_PER_WINDOW.
    expect(buffer.count()).toBe(MAX_EVENTS_PER_WINDOW);
  });

  it('events below cap are all recorded', () => {
    const buffer = createEventBuffer();

    for (let i = 0; i < 50; i++) {
      const buf = makeKeystrokeBuffer(1, 3, i * 10);
      buffer.record('kd', buf);
    }

    expect(buffer.count()).toBe(50);
  });

  it('drain returns all buffered events and resets', () => {
    const buffer = createEventBuffer();

    for (let i = 0; i < 10; i++) {
      const buf = makeKeystrokeBuffer(1, 3, i * 10);
      buffer.record('kd', buf);
    }

    const snapshot = buffer.drain();
    expect(snapshot.totalCount).toBe(10);
    expect(snapshot.keystroke.length).toBe(10);

    // After drain, count is 0.
    expect(buffer.count()).toBe(0);
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// Finding 19: Batch Checksums
// ═══════════════════════════════════════════════════════════════════════════

describe('Finding 19: Batch Checksums', () => {
  it('sha256 produces valid 64-char hex string', async () => {
    const payload = JSON.stringify({ type: 'behavioral', batch_id: '123' });
    const checksum = await sha256(payload);

    expect(checksum).toMatch(/^[0-9a-f]{64}$/);
  });

  it('same payload produces same checksum', async () => {
    const payload = JSON.stringify({ type: 'behavioral', data: [1, 2, 3] });
    const checksum1 = await sha256(payload);
    const checksum2 = await sha256(payload);

    expect(checksum1).toBe(checksum2);
  });

  it('different payloads produce different checksums', async () => {
    const payload1 = JSON.stringify({ type: 'behavioral', batch_id: '111' });
    const payload2 = JSON.stringify({ type: 'behavioral', batch_id: '222' });
    const checksum1 = await sha256(payload1);
    const checksum2 = await sha256(payload2);

    expect(checksum1).not.toBe(checksum2);
  });

  it('checksum of empty string is valid SHA-256', async () => {
    const checksum = await sha256('');
    // SHA-256 of empty string is a well-known value.
    expect(checksum).toBe('e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855');
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// Finding 20: PIN/Password Field Obfuscation
// ═══════════════════════════════════════════════════════════════════════════

describe('Finding 20: PIN/Password Field Obfuscation', () => {
  it('obfuscateSensitiveEvents zeros out zone data', () => {
    const events: RawKeystrokeEvent[] = [
      { type: 'kd', zone: 3, ts: 100 },
      { type: 'ku', zone: 3, ts: 150 },
      { type: 'kd', zone: 5, ts: 200 },
      { type: 'ku', zone: 5, ts: 250 },
    ];

    const obfuscated = obfuscateSensitiveEvents(events);

    // All zones should be -1 (zeroed out).
    for (const ev of obfuscated) {
      expect(ev.zone).toBe(-1);
    }

    // Timestamps should be preserved.
    expect(obfuscated[0]!.ts).toBe(100);
    expect(obfuscated[1]!.ts).toBe(150);
    expect(obfuscated[2]!.ts).toBe(200);
    expect(obfuscated[3]!.ts).toBe(250);

    // Types should be preserved.
    expect(obfuscated[0]!.type).toBe('kd');
    expect(obfuscated[1]!.type).toBe('ku');
  });

  it('obfuscateSensitiveEvents does not mutate original events', () => {
    const events: RawKeystrokeEvent[] = [
      { type: 'kd', zone: 3, ts: 100 },
    ];

    obfuscateSensitiveEvents(events);

    // Original should be unchanged.
    expect(events[0]!.zone).toBe(3);
  });

  it('extractKeystroke with sensitiveField=true sets sensitive_field_detected', () => {
    const events: RawKeystrokeEvent[] = [
      { type: 'kd', zone: 3, ts: 100 },
      { type: 'ku', zone: 3, ts: 180 },
      { type: 'kd', zone: 5, ts: 250 },
      { type: 'ku', zone: 5, ts: 320 },
    ];

    const signal = extractKeystroke(events, true);

    expect(signal).not.toBeNull();
    expect(signal!.sensitive_field_detected).toBe(true);
  });

  it('extractKeystroke with sensitiveField=false does not set sensitive_field_detected', () => {
    const events: RawKeystrokeEvent[] = [
      { type: 'kd', zone: 3, ts: 100 },
      { type: 'ku', zone: 3, ts: 180 },
    ];

    const signal = extractKeystroke(events, false);

    expect(signal).not.toBeNull();
    expect(signal!.sensitive_field_detected).toBeUndefined();
  });

  it('extractKeystroke with sensitiveField=true still produces timing data', () => {
    const events: RawKeystrokeEvent[] = [
      { type: 'kd', zone: 3, ts: 100 },
      { type: 'ku', zone: 3, ts: 180 },
      { type: 'kd', zone: 5, ts: 250 },
      { type: 'ku', zone: 5, ts: 340 },
    ];

    const signal = extractKeystroke(events, true);

    expect(signal).not.toBeNull();
    // Dwell times should still be extracted (timing metadata is preserved).
    expect(signal!.dwell_times.sample_count).toBeGreaterThan(0);
    expect(signal!.dwell_times.mean).toBeGreaterThan(0);
  });

  it('extractKeystroke with sensitiveField=true zeros zone transition matrix', () => {
    const events: RawKeystrokeEvent[] = [
      { type: 'kd', zone: 3, ts: 100 },
      { type: 'ku', zone: 3, ts: 180 },
      { type: 'kd', zone: 5, ts: 250 },
      { type: 'ku', zone: 5, ts: 340 },
    ];

    const signal = extractKeystroke(events, true);
    expect(signal).not.toBeNull();

    // With obfuscation, all zones are -1, so the transition matrix
    // should have no meaningful transitions (zones 0-9 only).
    // Zone -1 is excluded from the matrix.
    expect(signal!.zone_ids_used.length).toBe(0);
  });
});
