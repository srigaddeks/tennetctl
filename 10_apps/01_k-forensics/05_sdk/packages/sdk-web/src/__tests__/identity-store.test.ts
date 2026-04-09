/**
 * identity-store.test.ts
 *
 * Tests for IdentityStore: device_uuid minting, username persistence,
 * IDB heal-from-seed, clearUsername, clearAll, and STORAGE_WRITE messaging.
 *
 * Uses a Map-based IDB mock to simulate IndexedDB without a real DB.
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { webcrypto } from 'node:crypto';
import { IdentityStore } from '../session/identity-store.js';
import type { WorkerToMainMsg } from '../runtime/wire-protocol.js';

/** Node's webcrypto — jsdom does not provide crypto.subtle. */
const nodeCrypto = webcrypto as unknown as Crypto;

// ─── Minimal IDB mock ─────────────────────────────────────────────────────────
//
// The real IdentityStore uses: indexedDB.open(), IDBDatabase,
// IDBObjectStore.get/put/delete, and transaction callbacks.
// We simulate those with a synchronous Map and fire onsuccess/oncomplete
// via queueMicrotask so Promises resolve naturally.

/**
 * Build an IDB mock that reads and writes directly into the provided Map.
 * No copy is made — mutations inside the mock are visible to test assertions.
 */
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

  function makeTx(mode: 'readonly' | 'readwrite') {
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

  // Simulate: upgradeneeded fires first, then success
  queueMicrotask(() => {
    openReq.onupgradeneeded?.({});
    queueMicrotask(() => openReq.onsuccess?.({}));
  });

  return { openReq, store };
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('IdentityStore', () => {
  let postToMain: ReturnType<typeof vi.fn>;
  let idbStore: Map<string, string>;

  /** Unwrap a TTL-enveloped IDB value to get the inner string. */
  function unwrapIdb(raw: string | undefined): string | undefined {
    if (!raw) return undefined;
    try {
      const parsed = JSON.parse(raw) as { value: string };
      return parsed.value;
    } catch {
      return raw;
    }
  }

  /** Drain microtask/setTimeout queue so fire-and-forget async ops complete. */
  async function flush(): Promise<void> {
    for (let i = 0; i < 30; i++) {
      await new Promise((r) => setTimeout(r, 0));
    }
  }

  beforeEach(() => {
    postToMain = vi.fn();
    idbStore = new Map<string, string>();

    // Stub crypto with Node's webcrypto (jsdom lacks crypto.subtle)
    // Override randomUUID for deterministic device UUID minting
    vi.stubGlobal('crypto', {
      subtle: nodeCrypto.subtle,
      getRandomValues: (arr: Uint8Array) => nodeCrypto.getRandomValues(arr),
      randomUUID: vi.fn().mockReturnValue('new-device-uuid-111'),
    });

    // Stub indexedDB with the Map-based mock
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

  // ── init() ───────────────────────────────────────────────────────────────────

  describe('init()', () => {
    it('mints a device_uuid if none exists in IDB or seed', async () => {
      const store = new IdentityStore(postToMain as (msg: WorkerToMainMsg) => void);
      await store.init({ username: null, device_uuid: null });
      expect(store.getDeviceUuid()).toBe('new-device-uuid-111');
    });

    it('uses existing device_uuid from IDB (ignores seed)', async () => {
      idbStore.set('kp.did', 'existing-idb-device-uuid');
      const store = new IdentityStore(postToMain as (msg: WorkerToMainMsg) => void);
      await store.init({ username: null, device_uuid: 'seed-device-uuid' });
      expect(store.getDeviceUuid()).toBe('existing-idb-device-uuid');
    });

    it('uses seed device_uuid when IDB is empty', async () => {
      const store = new IdentityStore(postToMain as (msg: WorkerToMainMsg) => void);
      await store.init({ username: null, device_uuid: 'seed-uuid-from-main' });
      expect(store.getDeviceUuid()).toBe('seed-uuid-from-main');
    });

    it('heals IDB from seed value (writes seed back to IDB)', async () => {
      // IDB is empty; seed has a value — after init the seed should be stored in IDB
      const store = new IdentityStore(postToMain as (msg: WorkerToMainMsg) => void);
      await store.init({ username: null, device_uuid: 'seed-uuid-heal' });
      expect(unwrapIdb(idbStore.get('kp.did'))).toBe('seed-uuid-heal');
    });

    it('stores the minted device_uuid in IDB', async () => {
      const store = new IdentityStore(postToMain as (msg: WorkerToMainMsg) => void);
      await store.init({ username: null, device_uuid: null });
      // IDB should now have the minted UUID (TTL-wrapped)
      expect(unwrapIdb(idbStore.get('kp.did'))).toBe('new-device-uuid-111');
    });

    it('loads username from IDB when available', async () => {
      idbStore.set('kp.un', 'alice@example.com');
      const store = new IdentityStore(postToMain as (msg: WorkerToMainMsg) => void);
      await store.init({ username: null, device_uuid: null });
      expect(store.getUsername()).toBe('alice@example.com');
    });

    it('falls back to seed username when IDB has no username', async () => {
      const store = new IdentityStore(postToMain as (msg: WorkerToMainMsg) => void);
      await store.init({ username: 'bob@example.com', device_uuid: null });
      expect(store.getUsername()).toBe('bob@example.com');
    });

    it('leaves user_hash null after init even when username is restored', async () => {
      // user_hash must be re-derived per session — it is not persisted
      idbStore.set('kp.un', 'alice@example.com');
      const store = new IdentityStore(postToMain as (msg: WorkerToMainMsg) => void);
      await store.init({ username: null, device_uuid: null });
      expect(store.getUserHash()).toBeNull();
      expect(store.isIdentityCaptured()).toBe(false);
    });

    it('degrades gracefully when indexedDB throws on open', async () => {
      vi.stubGlobal('indexedDB', {
        open() {
          throw new Error('IDB not available');
        },
      });
      const store = new IdentityStore(postToMain as (msg: WorkerToMainMsg) => void);
      // Should not throw; falls back to minting a new UUID
      await expect(
        store.init({ username: null, device_uuid: null }),
      ).resolves.toBeUndefined();
      expect(store.getDeviceUuid()).toBe('new-device-uuid-111');
    });
  });

  // ── setUsername() ─────────────────────────────────────────────────────────────

  describe('setUsername()', () => {
    it('sets user_hash in memory', async () => {
      const store = new IdentityStore(postToMain as (msg: WorkerToMainMsg) => void);
      await store.init({ username: null, device_uuid: null });
      store.setUsername('hashdeadbeef', 'alice@example.com');
      expect(store.getUserHash()).toBe('hashdeadbeef');
    });

    it('sets username in memory', async () => {
      const store = new IdentityStore(postToMain as (msg: WorkerToMainMsg) => void);
      await store.init({ username: null, device_uuid: null });
      store.setUsername('hashdeadbeef', 'alice@example.com');
      expect(store.getUsername()).toBe('alice@example.com');
    });

    it('stores username to IDB (async, fire-and-forget, encrypted)', async () => {
      const store = new IdentityStore(postToMain as (msg: WorkerToMainMsg) => void);
      await store.init({ username: null, device_uuid: null });
      store.setUsername('hashdeadbeef', 'alice@example.com');
      // Wait for async encryption + IDB write to complete
      await flush();
      // IDB should contain the encrypted username (not plaintext)
      const innerValue = unwrapIdb(idbStore.get('kp.un'));
      expect(innerValue).toBeDefined();
      expect(innerValue).not.toBe('alice@example.com');
    });

    it('posts STORAGE_WRITE to main thread with encrypted username', async () => {
      const store = new IdentityStore(postToMain as (msg: WorkerToMainMsg) => void);
      await store.init({ username: null, device_uuid: null });
      postToMain.mockClear();
      store.setUsername('hashdeadbeef', 'alice@example.com');
      // writeEncryptedUsername is async — wait for it to complete
      await flush();
      const usernameWrite = postToMain.mock.calls.find(
        (c) => (c[0] as { key: string }).key === 'kp.un',
      );
      expect(usernameWrite).toBeDefined();
      // Value should be encrypted, not plaintext
      const value = (usernameWrite![0] as { value: string | null }).value;
      expect(value).not.toBe('alice@example.com');
      expect(value).not.toBeNull();
    });

    it('marks isIdentityCaptured() as true', async () => {
      const store = new IdentityStore(postToMain as (msg: WorkerToMainMsg) => void);
      await store.init({ username: null, device_uuid: null });
      expect(store.isIdentityCaptured()).toBe(false);
      store.setUsername('hashdeadbeef', 'alice@example.com');
      expect(store.isIdentityCaptured()).toBe(true);
    });
  });

  // ── clearUsername() ───────────────────────────────────────────────────────────

  describe('clearUsername()', () => {
    async function storeWithUser() {
      const store = new IdentityStore(postToMain as (msg: WorkerToMainMsg) => void);
      await store.init({ username: null, device_uuid: null });
      store.setUsername('hashdeadbeef', 'alice@example.com');
      postToMain.mockClear();
      return store;
    }

    it('clears username from memory', async () => {
      const store = await storeWithUser();
      store.clearUsername();
      expect(store.getUsername()).toBeNull();
    });

    it('clears user_hash from memory', async () => {
      const store = await storeWithUser();
      store.clearUsername();
      expect(store.getUserHash()).toBeNull();
    });

    it('marks isIdentityCaptured() as false after clearing', async () => {
      const store = await storeWithUser();
      store.clearUsername();
      expect(store.isIdentityCaptured()).toBe(false);
    });

    it('preserves device_uuid after clearUsername()', async () => {
      const store = await storeWithUser();
      const deviceUuid = store.getDeviceUuid();
      store.clearUsername();
      expect(store.getDeviceUuid()).toBe(deviceUuid);
    });

    it('posts STORAGE_WRITE(null) to main thread for username key', async () => {
      const store = await storeWithUser();
      store.clearUsername();
      expect(postToMain).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'STORAGE_WRITE',
          key: 'kp.un',
          value: null,
        }),
      );
    });

    it('does NOT post STORAGE_WRITE for device_uuid key', async () => {
      const store = await storeWithUser();
      store.clearUsername();
      const deviceWriteCalls = postToMain.mock.calls.filter(
        (c) => (c[0] as { key: string }).key === 'kp.did',
      );
      expect(deviceWriteCalls).toHaveLength(0);
    });
  });

  // ── clearAll() ────────────────────────────────────────────────────────────────

  describe('clearAll()', () => {
    it('clears everything including device_uuid from memory', async () => {
      const store = new IdentityStore(postToMain as (msg: WorkerToMainMsg) => void);
      await store.init({ username: null, device_uuid: null });
      store.setUsername('hashdeadbeef', 'alice@example.com');
      store.clearAll();
      expect(store.getDeviceUuid()).toBeNull();
      expect(store.getUsername()).toBeNull();
      expect(store.getUserHash()).toBeNull();
    });

    it('marks isIdentityCaptured() as false', async () => {
      const store = new IdentityStore(postToMain as (msg: WorkerToMainMsg) => void);
      await store.init({ username: null, device_uuid: null });
      store.setUsername('hash', 'user');
      store.clearAll();
      expect(store.isIdentityCaptured()).toBe(false);
    });

    it('posts STORAGE_WRITE(null) for both username and device_uuid keys', async () => {
      const store = new IdentityStore(postToMain as (msg: WorkerToMainMsg) => void);
      await store.init({ username: null, device_uuid: null });
      store.setUsername('hash', 'user');
      postToMain.mockClear();
      store.clearAll();

      const keys = postToMain.mock.calls.map((c) => (c[0] as { key: string }).key);
      expect(keys).toContain('kp.un');
      expect(keys).toContain('kp.did');

      const usernameMsg = postToMain.mock.calls.find(
        (c) => (c[0] as { key: string }).key === 'kp.un',
      )![0] as { value: string | null };
      expect(usernameMsg.value).toBeNull();

      const deviceMsg = postToMain.mock.calls.find(
        (c) => (c[0] as { key: string }).key === 'kp.did',
      )![0] as { value: string | null };
      expect(deviceMsg.value).toBeNull();
    });
  });
});
