/**
 * crypto-utils.ts — Shared cryptographic helpers for fingerprint collectors.
 *
 * Single source of truth for SHA-256 hashing and HMAC-SHA256 signing.
 * All signal collectors import from here — no more duplicated sha256 functions.
 *
 * Rules:
 *   • Zero npm dependencies — Web Crypto API only.
 *   • No `any` types.
 *   • Never throws — callers handle null returns from collectors.
 */

/**
 * SHA-256 hash a string, returning lowercase hex.
 * Uses crypto.subtle.digest (available in all modern browsers + Web Workers).
 */
export async function sha256(input: string): Promise<string> {
  const encoded = new TextEncoder().encode(input);
  const buffer = await crypto.subtle.digest('SHA-256', encoded);
  return Array.from(new Uint8Array(buffer))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

/**
 * SHA-256 hash raw bytes (Uint8Array), returning lowercase hex.
 * Used by GPU render tasks for pixel data hashing.
 */
export async function sha256Bytes(data: Uint8Array): Promise<string> {
  const buffer = await crypto.subtle.digest('SHA-256', data.buffer as ArrayBuffer);
  return Array.from(new Uint8Array(buffer))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

/**
 * HMAC-SHA256 sign a message with a key, returning lowercase hex.
 * Used for payload signing in transport layer.
 *
 * @param key  Raw key bytes (from kp.k storage).
 * @param message  The message string to sign.
 * @returns  Lowercase hex HMAC digest, or null if Web Crypto unavailable.
 */
export async function hmacSha256(key: ArrayBuffer | Uint8Array, message: string): Promise<string | null> {
  try {
    const keyBuffer: ArrayBuffer = key instanceof Uint8Array ? key.buffer as ArrayBuffer : key;
    const cryptoKey = await crypto.subtle.importKey(
      'raw',
      keyBuffer,
      { name: 'HMAC', hash: 'SHA-256' },
      false,
      ['sign'],
    );
    const encoded = new TextEncoder().encode(message);
    const signature = await crypto.subtle.sign('HMAC', cryptoKey, encoded);
    return Array.from(new Uint8Array(signature))
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('');
  } catch {
    return null;
  }
}

/**
 * Generate a cryptographically random signing key (256-bit).
 * Used to create the per-device HMAC key stored in kp.k.
 */
export function generateSigningKey(): Uint8Array {
  return crypto.getRandomValues(new Uint8Array(32));
}

// ─── AES-GCM storage encryption ──────────────────────────────────────────────

/**
 * Generate 16 random bytes for use as a PBKDF2 salt.
 */
export function generateSalt(): Uint8Array {
  return crypto.getRandomValues(new Uint8Array(16));
}

/**
 * Derive an AES-GCM CryptoKey from a seed string using PBKDF2.
 *
 * @param seed  The derivation seed (e.g. device_uuid).
 * @param salt  Per-device salt (16 bytes recommended).
 * @returns  An AES-GCM CryptoKey usable for encrypt/decrypt.
 */
export async function deriveEncryptionKey(
  seed: string,
  salt: Uint8Array,
): Promise<CryptoKey> {
  const encoded = new TextEncoder().encode(seed);
  const keyMaterial = await crypto.subtle.importKey(
    'raw',
    encoded,
    'PBKDF2',
    false,
    ['deriveKey'],
  );
  return crypto.subtle.deriveKey(
    {
      name: 'PBKDF2',
      salt: salt.buffer as ArrayBuffer,
      iterations: 100_000,
      hash: 'SHA-256',
    },
    keyMaterial,
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt', 'decrypt'],
  );
}

/**
 * AES-GCM encrypt a plaintext string.
 * Returns base64(12-byte-IV + ciphertext).
 *
 * @param key       AES-GCM CryptoKey from deriveEncryptionKey().
 * @param plaintext The string to encrypt.
 * @returns         Base64-encoded string of IV + ciphertext.
 */
export async function aesGcmEncrypt(
  key: CryptoKey,
  plaintext: string,
): Promise<string> {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const encoded = new TextEncoder().encode(plaintext);
  const cipherBuf = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    key,
    encoded,
  );
  // Prepend IV to ciphertext
  const combined = new Uint8Array(iv.length + cipherBuf.byteLength);
  combined.set(iv, 0);
  combined.set(new Uint8Array(cipherBuf), iv.length);
  return uint8ToBase64(combined);
}

/**
 * AES-GCM decrypt a base64(IV + ciphertext) string.
 * Returns the original plaintext, or null if decryption fails
 * (wrong key, corrupted data, tampered ciphertext).
 *
 * @param key       AES-GCM CryptoKey from deriveEncryptionKey().
 * @param encrypted Base64-encoded string of IV + ciphertext.
 * @returns         Original plaintext or null on failure.
 */
export async function aesGcmDecrypt(
  key: CryptoKey,
  encrypted: string,
): Promise<string | null> {
  try {
    const combined = base64ToUint8(encrypted);
    if (combined.length < 13) return null; // 12-byte IV + at least 1 byte
    const iv = combined.slice(0, 12);
    const ciphertext = combined.slice(12);
    const plainBuf = await crypto.subtle.decrypt(
      { name: 'AES-GCM', iv },
      key,
      ciphertext,
    );
    return new TextDecoder().decode(plainBuf);
  } catch {
    return null;
  }
}

/**
 * Returns true if the value looks like a base64-encoded AES-GCM blob
 * (i.e. encrypted data), false if it looks like plaintext.
 * Used for migration detection.
 */
export function isEncryptedValue(value: string): boolean {
  // AES-GCM encrypted values are base64(12-byte IV + ciphertext).
  // Minimum length: base64 of 13 bytes = 20 chars.
  // Also must be valid base64 with no spaces or special chars typical of usernames.
  if (value.length < 20) return false;
  return /^[A-Za-z0-9+/]+=*$/.test(value);
}

// ─── Base64 helpers (no btoa/atob — works in Web Workers) ────────────────────

const B64_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';

function uint8ToBase64(bytes: Uint8Array): string {
  let result = '';
  const len = bytes.length;
  for (let i = 0; i < len; i += 3) {
    const a = bytes[i] as number;
    const b: number = i + 1 < len ? (bytes[i + 1] as number) : 0;
    const c: number = i + 2 < len ? (bytes[i + 2] as number) : 0;
    result += B64_CHARS[a >> 2];
    result += B64_CHARS[((a & 3) << 4) | (b >> 4)];
    result += i + 1 < len ? B64_CHARS[((b & 15) << 2) | (c >> 6)] : '=';
    result += i + 2 < len ? B64_CHARS[c & 63] : '=';
  }
  return result;
}

function base64ToUint8(b64: string): Uint8Array {
  const clean = b64.replace(/=+$/, '');
  const len = clean.length;
  const byteLen = (len * 3) >> 2;
  const bytes = new Uint8Array(byteLen);
  let p = 0;
  for (let i = 0; i < len; i += 4) {
    const a = B64_CHARS.indexOf(clean[i]!);
    const b = i + 1 < len ? B64_CHARS.indexOf(clean[i + 1]!) : 0;
    const c = i + 2 < len ? B64_CHARS.indexOf(clean[i + 2]!) : 0;
    const d = i + 3 < len ? B64_CHARS.indexOf(clean[i + 3]!) : 0;
    bytes[p++] = (a << 2) | (b >> 4);
    if (p < byteLen) bytes[p++] = ((b & 15) << 4) | (c >> 2);
    if (p < byteLen) bytes[p++] = ((c & 3) << 6) | d;
  }
  return bytes;
}

/**
 * PBKDF2-SHA256 key derivation for username hashing.
 * Uses a per-device salt to prevent rainbow table attacks.
 *
 * @param input  The username string to hash.
 * @param salt   Per-device salt (32 bytes recommended).
 * @param iterations  Number of PBKDF2 iterations (default: 100_000).
 * @returns  Lowercase hex of the derived key, or null if unavailable.
 */
export async function pbkdf2Hash(
  input: string,
  salt: Uint8Array,
  iterations = 100_000,
): Promise<string | null> {
  try {
    const encoded = new TextEncoder().encode(input);
    const keyMaterial = await crypto.subtle.importKey(
      'raw',
      encoded,
      'PBKDF2',
      false,
      ['deriveBits'],
    );
    const derived = await crypto.subtle.deriveBits(
      {
        name: 'PBKDF2',
        salt: salt.buffer as ArrayBuffer,
        iterations,
        hash: 'SHA-256',
      },
      keyMaterial,
      256, // 32 bytes output
    );
    return Array.from(new Uint8Array(derived))
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('');
  } catch {
    return null;
  }
}
