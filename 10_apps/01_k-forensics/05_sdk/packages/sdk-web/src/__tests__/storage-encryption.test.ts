/**
 * storage-encryption.test.ts
 *
 * Tests for AES-GCM storage encryption:
 *   1. crypto-utils: round-trip, unique IVs, wrong-key rejection
 *   2. identity-store: encrypts before writing, decrypts after reading,
 *      migrates plaintext to encrypted on first read
 *
 * Uses Web Crypto API (available in Node 20+ / jsdom with globalThis.crypto).
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { webcrypto } from 'node:crypto';
import {
  aesGcmEncrypt,
  aesGcmDecrypt,
  deriveEncryptionKey,
  generateSalt,
  isEncryptedValue,
} from '../signals/crypto-utils.js';
import { IdentityStore } from '../session/identity-store.js';
import type { WorkerToMainMsg } from '../runtime/wire-protocol.js';

/**
 * jsdom does not provide crypto.subtle — we polyfill from Node's webcrypto
 * so that AES-GCM and PBKDF2 operations work in the test environment.
 */
const nodeCrypto = webcrypto as unknown as Crypto;

// ═══════════════════════════════════════════════════════════════════════════════
// §1  AES-GCM crypto-utils
// ═══════════════════════════════════════════════════════════════════════════════

describe('AES-GCM crypto-utils', () => {
  let key: CryptoKey;

  beforeEach(async () => {
    // Polyfill crypto.subtle for jsdom
    vi.stubGlobal('crypto', nodeCrypto);
    const salt = generateSalt();
    key = await deriveEncryptionKey('test-device-uuid', salt);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('round-trips: encrypt then decrypt returns original plaintext', async () => {
    const plaintext = 'alice@example.com';
    const encrypted = await aesGcmEncrypt(key, plaintext);
    const decrypted = await aesGcmDecrypt(key, encrypted);
    expect(decrypted).toBe(plaintext);
  });

  it('round-trips with empty string', async () => {
    const encrypted = await aesGcmEncrypt(key, '');
    const decrypted = await aesGcmDecrypt(key, encrypted);
    expect(decrypted).toBe('');
  });

  it('round-trips with unicode content', async () => {
    const plaintext = 'user@example.com — \u00e9\u00e8\u00ea \ud83d\udd12';
    const encrypted = await aesGcmEncrypt(key, plaintext);
    const decrypted = await aesGcmDecrypt(key, encrypted);
    expect(decrypted).toBe(plaintext);
  });

  it('produces different ciphertexts for same plaintext (unique IVs)', async () => {
    const plaintext = 'bob@example.com';
    const enc1 = await aesGcmEncrypt(key, plaintext);
    const enc2 = await aesGcmEncrypt(key, plaintext);
    expect(enc1).not.toBe(enc2);
    // Both still decrypt to the same value
    expect(await aesGcmDecrypt(key, enc1)).toBe(plaintext);
    expect(await aesGcmDecrypt(key, enc2)).toBe(plaintext);
  });

  it('returns null when decrypting with the wrong key', async () => {
    const encrypted = await aesGcmEncrypt(key, 'secret@example.com');
    const wrongSalt = generateSalt();
    const wrongKey = await deriveEncryptionKey('different-device-uuid', wrongSalt);
    const result = await aesGcmDecrypt(wrongKey, encrypted);
    expect(result).toBeNull();
  });

  it('returns null for corrupted ciphertext', async () => {
    const encrypted = await aesGcmEncrypt(key, 'test@example.com');
    // Flip a character in the middle to corrupt it
    const corrupted = encrypted.slice(0, 10) + 'X' + encrypted.slice(11);
    const result = await aesGcmDecrypt(key, corrupted);
    expect(result).toBeNull();
  });

  it('returns null for too-short input', async () => {
    const result = await aesGcmDecrypt(key, 'short');
    expect(result).toBeNull();
  });

  it('generateSalt returns 16 bytes', () => {
    const salt = generateSalt();
    expect(salt).toBeInstanceOf(Uint8Array);
    expect(salt.length).toBe(16);
  });

  it('deriveEncryptionKey produces a CryptoKey with AES-GCM algorithm', async () => {
    const salt = generateSalt();
    const derived = await deriveEncryptionKey('seed', salt);
    expect(derived).toBeDefined();
    expect((derived.algorithm as { name: string }).name).toBe('AES-GCM');
  });

  it('same seed + salt produces equivalent key (decrypts same ciphertext)', async () => {
    const salt = generateSalt();
    const key1 = await deriveEncryptionKey('my-device', salt);
    const key2 = await deriveEncryptionKey('my-device', salt);
    const encrypted = await aesGcmEncrypt(key1, 'hello');
    const decrypted = await aesGcmDecrypt(key2, encrypted);
    expect(decrypted).toBe('hello');
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// §2  isEncryptedValue
// ═══════════════════════════════════════════════════════════════════════════════

describe('isEncryptedValue', () => {
  beforeEach(() => {
    vi.stubGlobal('crypto', nodeCrypto);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('returns false for short plaintext usernames', () => {
    expect(isEncryptedValue('alice')).toBe(false);
    expect(isEncryptedValue('bob@ex.com')).toBe(false);
  });

  it('returns false for plaintext with special chars', () => {
    // Emails with @ and . are not valid base64
    expect(isEncryptedValue('alice@example.com')).toBe(false);
  });

  it('returns true for a valid base64 string of sufficient length', async () => {
    const salt = generateSalt();
    const key = await deriveEncryptionKey('test', salt);
    const encrypted = await aesGcmEncrypt(key, 'test');
    expect(isEncryptedValue(encrypted)).toBe(true);
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// §3  IdentityStore encryption integration
// ═══════════════════════════════════════════════════════════════════════════════

// ─── Minimal IDB mock (same pattern as identity-store.test.ts) ───────────────

function makeIdbMock(store: Map<string, string>) {
  function makeRequest<T>(result: T) {
    const req = {
      result,
      onsuccess: null as ((e: unknown) => void) | null,
      onerror: null as ((e: unknown) => void) | null,
    };
    queueMicrotask(() => req.onsuccess?.({}));
    return req;
  }

  function makeVoidRequest() {
    const req = {
      onsuccess: null as ((e: unknown) => void) | null,
      onerror: null as ((e: unknown) => void) | null,
    };
    queueMicrotask(() => req.onsuccess?.({}));
    return req;
  }

  function makeTx(_mode: 'readonly' | 'readwrite') {
    const tx = {
      oncomplete: null as ((e: unknown) => void) | null,
      onerror: null as ((e: unknown) => void) | null,
      objectStore(_name: string) {
        return {
          get(key: string) {
            const val = store.get(key) ?? undefined;
            return makeRequest<string | undefined>(val);
          },
          put(value: string, key: string) {
            store.set(key, value);
            queueMicrotask(() => tx.oncomplete?.({}));
            return makeVoidRequest();
          },
          delete(key: string) {
            store.delete(key);
            queueMicrotask(() => tx.oncomplete?.({}));
            return makeVoidRequest();
          },
        };
      },
    };
    return tx;
  }

  const db = {
    transaction(_storeName: string, mode: 'readonly' | 'readwrite' = 'readonly') {
      return makeTx(mode);
    },
    createObjectStore(_name: string) {
      // no-op
    },
  };

  const openReq = {
    result: db,
    onupgradeneeded: null as ((e: unknown) => void) | null,
    onsuccess: null as ((e: unknown) => void) | null,
    onerror: null as ((e: unknown) => void) | null,
  };

  queueMicrotask(() => {
    openReq.onupgradeneeded?.({});
    queueMicrotask(() => openReq.onsuccess?.({}));
  });

  return { openReq, store };
}

describe('IdentityStore encryption', () => {
  let postToMain: ReturnType<typeof vi.fn>;
  let idbStore: Map<string, string>;

  /**
   * Drain microtask queue.
   * The IDB mock uses queueMicrotask and the encryption functions are async,
   * so we need several rounds to let everything settle.
   */
  async function flush(): Promise<void> {
    for (let i = 0; i < 30; i++) {
      await new Promise((r) => setTimeout(r, 0));
    }
  }

  /**
   * Unwrap a TTL-enveloped IDB value to get the inner string.
   * IDB layer wraps all values in {"value":"...","stored_at":...}.
   */
  function unwrapIdb(raw: string | undefined): string | undefined {
    if (!raw) return undefined;
    try {
      const parsed = JSON.parse(raw) as { value: string };
      return parsed.value;
    } catch {
      return raw; // Legacy plain value
    }
  }

  beforeEach(() => {
    postToMain = vi.fn();
    idbStore = new Map<string, string>();

    // Polyfill crypto with Node's webcrypto (jsdom lacks crypto.subtle)
    // but override randomUUID for deterministic device UUID minting.
    const mockRandomUUID = vi.fn().mockReturnValue('test-device-uuid-001');
    vi.stubGlobal('crypto', {
      subtle: nodeCrypto.subtle,
      getRandomValues: (arr: Uint8Array) => nodeCrypto.getRandomValues(arr),
      randomUUID: mockRandomUUID,
    });

    vi.stubGlobal('indexedDB', {
      open(_name: string, _version: number) {
        const { openReq } = makeIdbMock(idbStore);
        return openReq;
      },
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('stores encrypted username in IDB (not plaintext)', async () => {
    const store = new IdentityStore(postToMain as (msg: WorkerToMainMsg) => void);
    await store.init({ username: null, device_uuid: null });
    store.setUsername('hash123', 'alice@example.com');
    await flush();

    const innerValue = unwrapIdb(idbStore.get('kp.un'));
    expect(innerValue).toBeDefined();
    // The stored value must NOT be the plaintext
    expect(innerValue).not.toBe('alice@example.com');
    // It should look like encrypted base64
    expect(isEncryptedValue(innerValue!)).toBe(true);
  });

  it('posts encrypted STORAGE_WRITE to main thread (not plaintext)', async () => {
    const store = new IdentityStore(postToMain as (msg: WorkerToMainMsg) => void);
    await store.init({ username: null, device_uuid: null });
    postToMain.mockClear();
    store.setUsername('hash123', 'alice@example.com');
    await flush();

    const usernameWrite = postToMain.mock.calls.find(
      (c) => (c[0] as { key: string }).key === 'kp.un',
    );
    expect(usernameWrite).toBeDefined();
    const value = (usernameWrite![0] as { value: string | null }).value;
    expect(value).not.toBe('alice@example.com');
    expect(value).not.toBeNull();
    expect(isEncryptedValue(value!)).toBe(true);
  });

  it('decrypts username on init when loading from IDB', async () => {
    // First session: set username (encrypts it)
    const store1 = new IdentityStore(postToMain as (msg: WorkerToMainMsg) => void);
    await store1.init({ username: null, device_uuid: 'persistent-device-id' });
    store1.setUsername('hash1', 'bob@example.com');
    await flush();

    // Second session: new IdentityStore, same IDB, same device_uuid
    const store2 = new IdentityStore(postToMain as (msg: WorkerToMainMsg) => void);
    await store2.init({ username: null, device_uuid: 'persistent-device-id' });
    expect(store2.getUsername()).toBe('bob@example.com');
  });

  it('migrates plaintext username to encrypted on first read', async () => {
    // Simulate legacy: plaintext username stored as raw string (pre-TTL format)
    idbStore.set('kp.did', 'legacy-device-uuid');
    idbStore.set('kp.un', 'plaintext-alice@example.com');

    const store = new IdentityStore(postToMain as (msg: WorkerToMainMsg) => void);
    await store.init({ username: null, device_uuid: null });

    // Username should be read correctly
    expect(store.getUsername()).toBe('plaintext-alice@example.com');

    // After migration, IDB should now contain encrypted value (inside TTL envelope)
    await flush();
    const innerValue = unwrapIdb(idbStore.get('kp.un'));
    expect(innerValue).not.toBe('plaintext-alice@example.com');
    expect(isEncryptedValue(innerValue!)).toBe(true);
  });

  it('creates and persists a salt in IDB on first init', async () => {
    const store = new IdentityStore(postToMain as (msg: WorkerToMainMsg) => void);
    await store.init({ username: null, device_uuid: null });
    await flush();

    const saltHex = unwrapIdb(idbStore.get('kp.us'));
    expect(saltHex).toBeDefined();
    // 16 bytes = 32 hex chars
    expect(saltHex!.length).toBe(32);
    expect(/^[0-9a-f]+$/.test(saltHex!)).toBe(true);
  });

  it('reuses existing salt on subsequent inits', async () => {
    // First init — creates salt
    const store1 = new IdentityStore(postToMain as (msg: WorkerToMainMsg) => void);
    await store1.init({ username: null, device_uuid: 'dev-uuid' });
    await flush();
    const salt1 = unwrapIdb(idbStore.get('kp.us'));

    // Second init — should reuse same salt
    const store2 = new IdentityStore(postToMain as (msg: WorkerToMainMsg) => void);
    await store2.init({ username: null, device_uuid: 'dev-uuid' });
    await flush();
    const salt2 = unwrapIdb(idbStore.get('kp.us'));

    expect(salt1).toBe(salt2);
  });

  it('encrypts seed username from main thread before persisting', async () => {
    const store = new IdentityStore(postToMain as (msg: WorkerToMainMsg) => void);
    await store.init({ username: 'seed-user@example.com', device_uuid: null });
    await flush();

    // In-memory value should be plaintext
    expect(store.getUsername()).toBe('seed-user@example.com');
    // IDB value should be encrypted (inside TTL envelope)
    const innerValue = unwrapIdb(idbStore.get('kp.un'));
    expect(innerValue).not.toBe('seed-user@example.com');
    expect(isEncryptedValue(innerValue!)).toBe(true);
  });

  it('clearAll removes salt from IDB and posts STORAGE_WRITE(null) for salt', async () => {
    const store = new IdentityStore(postToMain as (msg: WorkerToMainMsg) => void);
    await store.init({ username: null, device_uuid: null });
    store.setUsername('hash', 'user@example.com');
    await flush();

    expect(idbStore.has('kp.us')).toBe(true);
    postToMain.mockClear();

    store.clearAll();
    await flush();

    // Salt should be deleted from IDB
    expect(idbStore.has('kp.us')).toBe(false);

    // STORAGE_WRITE(null) should have been sent for salt key
    const saltWrite = postToMain.mock.calls.find(
      (c) => (c[0] as { key: string }).key === 'kp.us',
    );
    expect(saltWrite).toBeDefined();
    expect((saltWrite![0] as { value: string | null }).value).toBeNull();
  });

  it('in-memory username remains plaintext after setUsername', async () => {
    const store = new IdentityStore(postToMain as (msg: WorkerToMainMsg) => void);
    await store.init({ username: null, device_uuid: null });
    store.setUsername('hash123', 'carol@example.com');
    // In-memory must always be plaintext for session use
    expect(store.getUsername()).toBe('carol@example.com');
  });
});
