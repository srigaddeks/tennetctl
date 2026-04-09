/**
 * identity-store.ts
 *
 * Manages username, user_hash, and device_uuid persistence.
 * Runs inside the Web Worker.
 *
 * Primary storage: IndexedDB (full worker access).
 * Mirror sync: sends STORAGE_WRITE to the main thread so localStorage
 * stays in sync for cross-tab reads.
 *
 * SDK_BEST_PRACTICES §6.1, §6.3, §6.5, §12.
 */

import type { WorkerToMainMsg } from '../runtime/wire-protocol.js';
import {
  IDB_DB_NAME,
  IDB_STORE_NAME,
  STORAGE_KEY_USERNAME,
  STORAGE_KEY_DEVICE_UUID,
  STORAGE_KEY_USERNAME_SALT,
  DATA_RETENTION_TTL_MS,
} from '../config/defaults.js';
import {
  generateSalt,
  deriveEncryptionKey,
  aesGcmEncrypt,
  aesGcmDecrypt,
  isEncryptedValue,
} from '../signals/crypto-utils.js';

// ─── Minimal IDB key-value wrapper ────────────────────────────────────────────

/**
 * Opens (or re-uses) the kp-bio IndexedDB and resolves the kv object store.
 * Returns the open IDBDatabase on success, null if IDB is unavailable.
 */
function openDb(): Promise<IDBDatabase | null> {
  return new Promise((resolve) => {
    try {
      const req = indexedDB.open(IDB_DB_NAME, 1);
      req.onupgradeneeded = () => {
        try {
          req.result.createObjectStore(IDB_STORE_NAME);
        } catch {
          // Store already exists — safe to ignore.
        }
      };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => resolve(null);
    } catch {
      resolve(null);
    }
  });
}

// ─── TTL envelope ────────────────────────────────────────────────────────────

/** Wrapper that timestamps stored values for TTL expiration (Finding 14). */
interface TtlEnvelope {
  value: string;
  stored_at: number;
}

/** Encodes a value with a storage timestamp. */
function wrapWithTtl(value: string): string {
  const envelope: TtlEnvelope = { value, stored_at: Date.now() };
  return JSON.stringify(envelope);
}

/** Decodes a TTL-wrapped value. Returns null if expired or malformed. */
function unwrapWithTtl(raw: string, ttlMs: number): string | null {
  try {
    const parsed: unknown = JSON.parse(raw);
    if (
      parsed !== null &&
      typeof parsed === 'object' &&
      'value' in parsed &&
      'stored_at' in parsed
    ) {
      const envelope = parsed as TtlEnvelope;
      if (Date.now() - envelope.stored_at > ttlMs) return null; // Expired
      return envelope.value;
    }
    // Legacy value (pre-TTL) — treat as valid, no expiry.
    return raw;
  } catch {
    // Not JSON — legacy plain-string value.
    return raw;
  }
}

/** Reads a string value from IDB by key. Returns null on miss, error, or TTL expiry. */
async function idbGet(key: string, ttlMs: number = DATA_RETENTION_TTL_MS): Promise<string | null> {
  try {
    const db = await openDb();
    if (!db) return null;
    return new Promise((resolve) => {
      try {
        const tx = db.transaction(IDB_STORE_NAME, 'readonly');
        const req = tx.objectStore(IDB_STORE_NAME).get(key);
        req.onsuccess = () => {
          const val: unknown = req.result;
          if (typeof val !== 'string') {
            resolve(null);
            return;
          }
          const unwrapped = unwrapWithTtl(val, ttlMs);
          if (unwrapped === null) {
            // Expired — schedule delete (fire-and-forget).
            void idbDelete(key);
            resolve(null);
            return;
          }
          resolve(unwrapped);
        };
        req.onerror = () => resolve(null);
      } catch {
        resolve(null);
      }
    });
  } catch {
    return null;
  }
}

/** Writes a string value to IDB with TTL metadata. Silently swallows errors. */
async function idbSet(key: string, value: string): Promise<void> {
  try {
    const db = await openDb();
    if (!db) return;
    await new Promise<void>((resolve) => {
      try {
        const tx = db.transaction(IDB_STORE_NAME, 'readwrite');
        tx.objectStore(IDB_STORE_NAME).put(wrapWithTtl(value), key);
        tx.oncomplete = () => resolve();
        tx.onerror = () => resolve();
      } catch {
        resolve();
      }
    });
  } catch {
    // IDB unavailable — degrade silently.
  }
}

/** Deletes a key from IDB. Silently swallows errors. */
async function idbDelete(key: string): Promise<void> {
  try {
    const db = await openDb();
    if (!db) return;
    await new Promise<void>((resolve) => {
      try {
        const tx = db.transaction(IDB_STORE_NAME, 'readwrite');
        tx.objectStore(IDB_STORE_NAME).delete(key);
        tx.oncomplete = () => resolve();
        tx.onerror = () => resolve();
      } catch {
        resolve();
      }
    });
  } catch {
    // IDB unavailable — degrade silently.
  }
}

// ─── StorageWriteMsg (worker→main for localStorage mirror) ────────────────────

/**
 * Internal subset of WorkerToMainMsg used by IdentityStore to mirror
 * values into main-thread localStorage.
 *
 * NOTE: This shape is structurally compatible with WorkerToMainMsg but
 * is not part of the public discriminated union — it is a transport detail.
 * We cast through WorkerToMainMsg using the postToMain callback.
 */
interface StorageWriteMsg {
  type: 'STORAGE_WRITE';
  key: string;
  value: string | null; // null = delete
}

// ─── IdentityStore ────────────────────────────────────────────────────────────

/**
 * IdentityStore — manages the three persistent identifiers used by K-Protect:
 * - `username` (raw, stored in IDB + mirrored to localStorage via main thread)
 * - `user_hash` (SHA-256 hex; in-memory only)
 * - `device_uuid` (IDB primary; minted once per browser-origin)
 *
 * Lives in the worker. Bridges to main-thread localStorage via STORAGE_WRITE
 * postMessage for cross-tab consistency.
 */
export class IdentityStore {
  private username: string | null = null;
  private user_hash: string | null = null;
  private device_uuid: string | null = null;

  /** AES-GCM key derived from device_uuid — used to encrypt username at rest. */
  private encryptionKey: CryptoKey | null = null;

  /** postMessage channel back to the main thread. */
  private readonly postToMain: (msg: WorkerToMainMsg) => void;

  constructor(postToMain: (msg: WorkerToMainMsg) => void) {
    this.postToMain = postToMain;
  }

  /**
   * Initialises the store.
   *
   * Order of precedence for device_uuid:
   *   1. IDB (worker-primary)
   *   2. seedFromMain.device_uuid (from main-thread localStorage on INIT)
   *   3. Mint a new crypto.randomUUID()
   *
   * Order of precedence for username:
   *   1. IDB kp.un value (encrypted; decrypted on read)
   *   2. seedFromMain.username (from main-thread localStorage on INIT)
   *
   * Migration: if plaintext username is found, it is encrypted in-place.
   */
  async init(seedFromMain: {
    username: string | null;
    device_uuid: string | null;
  }): Promise<void> {
    // ── device_uuid ──────────────────────────────────────────────────────────
    let did = await idbGet(STORAGE_KEY_DEVICE_UUID);
    if (!did && seedFromMain.device_uuid) {
      did = seedFromMain.device_uuid;
    }
    if (!did) {
      try {
        did = crypto.randomUUID();
      } catch {
        // crypto.randomUUID unavailable (should never happen in modern browsers)
        did = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
      }
    }
    this.device_uuid = did;
    await idbSet(STORAGE_KEY_DEVICE_UUID, did);

    // ── encryption key derivation ────────────────────────────────────────────
    await this.initEncryptionKey(did);

    // ── username ─────────────────────────────────────────────────────────────
    let un = await this.readEncryptedUsername();
    if (!un && seedFromMain.username) {
      un = seedFromMain.username;
      // Seed value came from main thread (plaintext) — encrypt and persist.
      await this.writeEncryptedUsername(un);
    }
    if (un) {
      this.username = un;
      // user_hash is not persisted — it must be re-derived each session.
      // We leave user_hash null here; the session layer must re-capture it.
    }
  }

  // ─── Encryption key management ──────────────────────────────────────────────

  /**
   * Derives (or re-derives) the AES-GCM encryption key from device_uuid.
   * Creates and persists a new salt in IDB + localStorage if none exists.
   */
  private async initEncryptionKey(deviceUuid: string): Promise<void> {
    try {
      let salt = await this.loadSalt();
      if (!salt) {
        salt = generateSalt();
        await this.persistSalt(salt);
      }
      this.encryptionKey = await deriveEncryptionKey(deviceUuid, salt);
    } catch {
      // Web Crypto unavailable — encryption disabled, fall back to plaintext.
      this.encryptionKey = null;
    }
  }

  /** Loads the PBKDF2 salt from IDB. Returns null if absent. */
  private async loadSalt(): Promise<Uint8Array | null> {
    const hex = await idbGet(STORAGE_KEY_USERNAME_SALT);
    if (!hex) return null;
    const match = hex.match(/.{2}/g);
    if (!match || match.length !== 16) return null;
    return new Uint8Array(match.map((b) => parseInt(b, 16)));
  }

  /** Persists the PBKDF2 salt to IDB + mirrors to localStorage. */
  private async persistSalt(salt: Uint8Array): Promise<void> {
    const hex = Array.from(salt)
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('');
    await idbSet(STORAGE_KEY_USERNAME_SALT, hex);
    this.postStorageWrite(STORAGE_KEY_USERNAME_SALT, hex);
  }

  /**
   * Reads the username from IDB, decrypting if encrypted.
   * Handles migration: if plaintext is detected, encrypts it in-place.
   */
  private async readEncryptedUsername(): Promise<string | null> {
    const raw = await idbGet(STORAGE_KEY_USERNAME);
    if (!raw) return null;

    // If we have an encryption key and the value looks encrypted, decrypt it.
    if (this.encryptionKey && isEncryptedValue(raw)) {
      const decrypted = await aesGcmDecrypt(this.encryptionKey, raw);
      if (decrypted !== null) return decrypted;
      // Decryption failed — value may be corrupted; discard.
      return null;
    }

    // Value is plaintext (legacy / pre-encryption). Migrate to encrypted.
    if (this.encryptionKey) {
      await this.writeEncryptedUsername(raw);
    }
    return raw;
  }

  /**
   * Encrypts and writes the username to IDB + mirrors to localStorage.
   * Falls back to plaintext if encryption key is unavailable.
   */
  private async writeEncryptedUsername(plaintext: string): Promise<void> {
    let stored = plaintext;
    if (this.encryptionKey) {
      try {
        stored = await aesGcmEncrypt(this.encryptionKey, plaintext);
      } catch {
        // Encryption failed — fall back to plaintext.
      }
    }
    await idbSet(STORAGE_KEY_USERNAME, stored);
    this.postStorageWrite(STORAGE_KEY_USERNAME, stored);
  }

  /**
   * Records a captured identity.
   *
   * @param user_hash   SHA-256 hex of the raw username (never stored raw here).
   * @param raw_username  The plaintext username — encrypted before storage in
   *                      IDB and mirrored to main-thread localStorage.
   */
  setUsername(user_hash: string, raw_username: string): void {
    this.user_hash = user_hash;
    this.username = raw_username;

    // Persist encrypted to IDB + mirror to localStorage (fire-and-forget).
    void this.writeEncryptedUsername(raw_username);
  }

  /** Returns the raw username, or null if not yet captured. */
  getUsername(): string | null {
    return this.username;
  }

  /** Returns the SHA-256 user hash, or null if not yet captured. */
  getUserHash(): string | null {
    return this.user_hash;
  }

  /** Returns the persistent device UUID. */
  getDeviceUuid(): string | null {
    return this.device_uuid;
  }

  /**
   * Returns true when a user_hash has been established for this session.
   * Used by SessionManager to gate transport (§6.2).
   */
  isIdentityCaptured(): boolean {
    return this.user_hash !== null;
  }

  /**
   * Clears the captured username and user_hash from memory and IDB.
   * Mirrors the deletion to main-thread localStorage.
   * Preserves device_uuid (per §6.3 — logout does not clear device identity).
   */
  clearUsername(): void {
    this.username = null;
    this.user_hash = null;

    void idbDelete(STORAGE_KEY_USERNAME);
    this.postStorageWrite(STORAGE_KEY_USERNAME, null);
  }

  /**
   * Full wipe — clears everything including device_uuid, encryption key, and salt.
   * Called only from `KProtect.destroy({ clearIdentity: true })`.
   */
  clearAll(): void {
    this.username = null;
    this.user_hash = null;
    this.device_uuid = null;
    this.encryptionKey = null;

    void idbDelete(STORAGE_KEY_USERNAME);
    void idbDelete(STORAGE_KEY_DEVICE_UUID);
    void idbDelete(STORAGE_KEY_USERNAME_SALT);
    this.postStorageWrite(STORAGE_KEY_USERNAME, null);
    this.postStorageWrite(STORAGE_KEY_DEVICE_UUID, null);
    this.postStorageWrite(STORAGE_KEY_USERNAME_SALT, null);
  }

  // ─── Private helpers ───────────────────────────────────────────────────────

  /**
   * Sends a STORAGE_WRITE message to the main thread.
   * value === null means delete the key.
   */
  private postStorageWrite(key: string, value: string | null): void {
    // StorageWriteMsg is an internal transport detail; cast is intentional.
    const msg: StorageWriteMsg = { type: 'STORAGE_WRITE', key, value };
    this.postToMain(msg as unknown as WorkerToMainMsg);
  }
}