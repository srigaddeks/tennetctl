/**
 * beacon-signing.ts — Payload signing for navigator.sendBeacon transport.
 *
 * sendBeacon does not support custom HTTP headers, so the HMAC-SHA256
 * signature must be embedded directly in the request body. This module
 * provides creation and verification of signed beacon payloads.
 *
 * Signature message format:
 *   HMAC-SHA256(api_key, nonce + '.' + timestamp + '.' + sha256(payload))
 *
 * Where:
 *   - nonce = batch_id (UUID, unique per batch — replay protection)
 *   - timestamp = Date.now() at signing time
 *   - payload = JSON-stringified batch data
 *
 * Rules:
 *   • Zero npm dependencies — Web Crypto API only.
 *   • No `any` types.
 *   • Returns new objects, never mutates inputs.
 */

import { sha256, hmacSha256 } from '../signals/crypto-utils.js';

// ─── Types ───────────────────────────────────────────────────────────────────

/**
 * Signed beacon payload — embeds HMAC signature in the body since
 * sendBeacon cannot set custom headers.
 *
 * The server extracts `key_id` to look up the API key, then verifies
 * `signature` over `payload` using the same HMAC-SHA256 scheme used
 * by the fetch transport's X-KP-Signature header.
 */
export interface SignedBeaconPayload {
  /** JSON-stringified batch data. */
  payload: string;
  /** HMAC-SHA256 hex digest of: nonce + '.' + timestamp + '.' + sha256(payload). */
  signature: string;
  /** First 12 characters of the API key — server uses this to look up the full key. */
  key_id: string;
  /** Unix timestamp in ms at signing time. */
  timestamp: number;
  /** Batch ID used as nonce for replay protection. */
  nonce: string;
}

// ─── Batch shape (minimal — we only need batch_id) ───────────────────────────

/** Minimal batch shape required for signing. */
interface SignableBatch {
  batch_id: string;
  [key: string]: unknown;
}

// ─── Public API ──────────────────────────────────────────────────────────────

/**
 * Creates a signed beacon payload from a batch object and API key.
 *
 * The signature is computed as:
 *   HMAC-SHA256(api_key_bytes, batch_id + '.' + timestamp + '.' + sha256(json_payload))
 *
 * @param batch   Any batch object that has a `batch_id` field.
 * @param apiKey  The full API key string (e.g. 'kp_live_abcdef123456_rest').
 * @returns       A SignedBeaconPayload ready to be JSON.stringified and sent via sendBeacon.
 */
export async function createSignedBeaconPayload(
  batch: SignableBatch,
  apiKey: string,
): Promise<SignedBeaconPayload> {
  const payload = JSON.stringify(batch);
  const timestamp = Date.now();
  const nonce = batch.batch_id;
  const keyId = apiKey.substring(0, 12);

  // Compute signature: HMAC-SHA256(api_key, nonce.timestamp.sha256(payload))
  const payloadHash = await sha256(payload);
  const message = `${nonce}.${String(timestamp)}.${payloadHash}`;
  const keyBytes = new TextEncoder().encode(apiKey);
  const signature = await hmacSha256(keyBytes, message);

  return {
    payload,
    signature: signature ?? '',
    key_id: keyId,
    timestamp,
    nonce,
  };
}

/**
 * Verifies a signed beacon payload against the expected API key.
 *
 * Recomputes the HMAC-SHA256 signature using the provided key and compares
 * it to the embedded signature. Any field tampering (payload, timestamp,
 * nonce) will cause verification to fail.
 *
 * @param signed  The SignedBeaconPayload to verify.
 * @param apiKey  The full API key to verify against.
 * @returns       true if the signature is valid, false otherwise.
 */
export async function verifyBeaconSignature(
  signed: SignedBeaconPayload,
  apiKey: string,
): Promise<boolean> {
  try {
    const payloadHash = await sha256(signed.payload);
    const message = `${signed.nonce}.${String(signed.timestamp)}.${payloadHash}`;
    const keyBytes = new TextEncoder().encode(apiKey);
    const expectedSignature = await hmacSha256(keyBytes, message);

    if (!expectedSignature) return false;

    // Constant-time comparison to prevent timing attacks.
    // Since we are comparing hex strings of fixed length (64 chars),
    // we compare every character regardless of mismatch position.
    if (signed.signature.length !== expectedSignature.length) return false;

    let mismatch = 0;
    for (let i = 0; i < expectedSignature.length; i++) {
      mismatch |= signed.signature.charCodeAt(i) ^ expectedSignature.charCodeAt(i);
    }
    return mismatch === 0;
  } catch {
    return false;
  }
}
