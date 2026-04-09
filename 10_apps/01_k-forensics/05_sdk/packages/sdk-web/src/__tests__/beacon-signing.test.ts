/**
 * beacon-signing.test.ts
 *
 * Tests for sendBeacon payload signing (Finding 10: payload signing for
 * beacon transport where custom headers are not available).
 *
 * Covers:
 *   - SignedBeaconPayload structure validation
 *   - HMAC-SHA256 signature correctness
 *   - Signature verification with correct / incorrect key
 *   - Nonce uniqueness per beacon
 *   - Timestamp recency tolerance
 *   - createSignedBeaconPayload integration
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { sha256, hmacSha256 } from '../signals/crypto-utils.js';
import {
  createSignedBeaconPayload,
  verifyBeaconSignature,
  type SignedBeaconPayload,
} from '../transport/beacon-signing.js';

// ─── Helpers ─────────────────────────────────────────────────────────────────

const TEST_API_KEY = 'kp_live_abcdef123456_rest_of_key';
const TEST_BATCH = {
  type: 'session_end' as const,
  batch_id: 'batch-uuid-001',
  session_id: 'sess-uuid-001',
  sent_at: Date.now(),
  end_reason: 'pagehide' as const,
};

// ─── createSignedBeaconPayload ───────────────────────────────────────────────

describe('createSignedBeaconPayload', () => {
  it('returns a SignedBeaconPayload with all required fields', async () => {
    const result = await createSignedBeaconPayload(TEST_BATCH, TEST_API_KEY);

    expect(result).toBeDefined();
    expect(result).toHaveProperty('payload');
    expect(result).toHaveProperty('signature');
    expect(result).toHaveProperty('key_id');
    expect(result).toHaveProperty('timestamp');
    expect(result).toHaveProperty('nonce');
  });

  it('embeds the JSON-stringified batch as payload', async () => {
    const result = await createSignedBeaconPayload(TEST_BATCH, TEST_API_KEY);
    const parsed = JSON.parse(result.payload);

    expect(parsed.type).toBe('session_end');
    expect(parsed.batch_id).toBe('batch-uuid-001');
    expect(parsed.session_id).toBe('sess-uuid-001');
  });

  it('sets key_id to first 12 chars of api_key', async () => {
    const result = await createSignedBeaconPayload(TEST_BATCH, TEST_API_KEY);

    expect(result.key_id).toBe('kp_live_abcd');
    expect(result.key_id.length).toBe(12);
  });

  it('sets timestamp to a recent epoch ms value', async () => {
    const before = Date.now();
    const result = await createSignedBeaconPayload(TEST_BATCH, TEST_API_KEY);
    const after = Date.now();

    expect(result.timestamp).toBeGreaterThanOrEqual(before);
    expect(result.timestamp).toBeLessThanOrEqual(after);
  });

  it('uses batch_id as nonce for replay protection', async () => {
    const result = await createSignedBeaconPayload(TEST_BATCH, TEST_API_KEY);

    expect(result.nonce).toBe(TEST_BATCH.batch_id);
  });

  it('generates a hex string signature', async () => {
    const result = await createSignedBeaconPayload(TEST_BATCH, TEST_API_KEY);

    // HMAC-SHA256 produces 64 hex chars
    expect(result.signature).toMatch(/^[0-9a-f]{64}$/);
  });
});

// ─── Signature verification ──────────────────────────────────────────────────

describe('verifyBeaconSignature', () => {
  it('verifies a correctly signed payload', async () => {
    const signed = await createSignedBeaconPayload(TEST_BATCH, TEST_API_KEY);
    const valid = await verifyBeaconSignature(signed, TEST_API_KEY);

    expect(valid).toBe(true);
  });

  it('rejects a payload signed with a different key', async () => {
    const signed = await createSignedBeaconPayload(TEST_BATCH, TEST_API_KEY);
    const valid = await verifyBeaconSignature(signed, 'kp_live_wrong_key_999');

    expect(valid).toBe(false);
  });

  it('rejects a payload with a tampered payload body', async () => {
    const signed = await createSignedBeaconPayload(TEST_BATCH, TEST_API_KEY);
    const tampered: SignedBeaconPayload = {
      ...signed,
      payload: signed.payload.replace('session_end', 'session_start'),
    };
    const valid = await verifyBeaconSignature(tampered, TEST_API_KEY);

    expect(valid).toBe(false);
  });

  it('rejects a payload with a tampered signature', async () => {
    const signed = await createSignedBeaconPayload(TEST_BATCH, TEST_API_KEY);
    const tampered: SignedBeaconPayload = {
      ...signed,
      signature: 'a'.repeat(64),
    };
    const valid = await verifyBeaconSignature(tampered, TEST_API_KEY);

    expect(valid).toBe(false);
  });

  it('rejects a payload with a tampered timestamp', async () => {
    const signed = await createSignedBeaconPayload(TEST_BATCH, TEST_API_KEY);
    const tampered: SignedBeaconPayload = {
      ...signed,
      timestamp: signed.timestamp - 100_000,
    };
    const valid = await verifyBeaconSignature(tampered, TEST_API_KEY);

    expect(valid).toBe(false);
  });

  it('rejects a payload with a tampered nonce', async () => {
    const signed = await createSignedBeaconPayload(TEST_BATCH, TEST_API_KEY);
    const tampered: SignedBeaconPayload = {
      ...signed,
      nonce: 'different-nonce-value',
    };
    const valid = await verifyBeaconSignature(tampered, TEST_API_KEY);

    expect(valid).toBe(false);
  });
});

// ─── Nonce uniqueness ────────────────────────────────────────────────────────

describe('nonce uniqueness', () => {
  it('produces distinct nonces for batches with different batch_ids', async () => {
    const batch1 = { ...TEST_BATCH, batch_id: 'batch-aaa' };
    const batch2 = { ...TEST_BATCH, batch_id: 'batch-bbb' };

    const signed1 = await createSignedBeaconPayload(batch1, TEST_API_KEY);
    const signed2 = await createSignedBeaconPayload(batch2, TEST_API_KEY);

    expect(signed1.nonce).not.toBe(signed2.nonce);
  });

  it('produces distinct signatures for different batches', async () => {
    const batch1 = { ...TEST_BATCH, batch_id: 'batch-aaa' };
    const batch2 = { ...TEST_BATCH, batch_id: 'batch-bbb' };

    const signed1 = await createSignedBeaconPayload(batch1, TEST_API_KEY);
    const signed2 = await createSignedBeaconPayload(batch2, TEST_API_KEY);

    expect(signed1.signature).not.toBe(signed2.signature);
  });
});

// ─── Timestamp recency ──────────────────────────────────────────────────────

describe('timestamp recency', () => {
  it('timestamp is within 5 seconds of current time', async () => {
    const result = await createSignedBeaconPayload(TEST_BATCH, TEST_API_KEY);
    const now = Date.now();
    const drift = Math.abs(now - result.timestamp);

    expect(drift).toBeLessThan(5000);
  });
});

// ─── Signature message format ────────────────────────────────────────────────

describe('signature message format', () => {
  it('signature is HMAC-SHA256 of nonce.timestamp.sha256(payload)', async () => {
    const signed = await createSignedBeaconPayload(TEST_BATCH, TEST_API_KEY);

    // Manually recompute the expected signature
    const payloadHash = await sha256(signed.payload);
    const message = `${signed.nonce}.${String(signed.timestamp)}.${payloadHash}`;
    const keyBytes = new TextEncoder().encode(TEST_API_KEY);
    const expectedSig = await hmacSha256(keyBytes, message);

    expect(signed.signature).toBe(expectedSig);
  });
});
