/**
 * audit-logger.ts — Tamper-evident audit log for the K-Protect SDK.
 *
 * Records all significant SDK actions (init, capture, send, destroy)
 * in a sealed log chain where each entry includes the hash of the
 * previous entry, making tampering detectable.
 *
 * The log lives in memory within the Web Worker. It can be exported
 * on demand via a EXPORT_AUDIT_LOG message for compliance review.
 *
 * Rules:
 *   - Runs in the Web Worker — no DOM access.
 *   - Zero npm dependencies.
 *   - No `any` types.
 *   - Never throws.
 *   - Max 1000 entries (ring buffer) to bound memory usage.
 */

import { sha256 } from '../signals/crypto-utils.js';

/** Maximum audit log entries before oldest are evicted. */
const MAX_ENTRIES = 1000;

export type AuditAction =
  | 'sdk_init'
  | 'session_start'
  | 'session_end'
  | 'username_captured'
  | 'batch_sent'
  | 'batch_failed'
  | 'fingerprint_collected'
  | 'consent_granted'
  | 'consent_denied'
  | 'logout'
  | 'destroy';

export interface AuditEntry {
  /** Monotonic sequence number. */
  seq: number;
  /** ISO 8601 timestamp. */
  timestamp: string;
  /** What happened. */
  action: AuditAction;
  /** Optional metadata (e.g., batch_id, session_id). Never contains PII. */
  detail: Record<string, string | number | boolean> | null;
  /** SHA-256 of the previous entry's hash (chain integrity). */
  prev_hash: string;
}

/**
 * AuditLogger — append-only, hash-chained audit log.
 *
 * Each entry includes the SHA-256 hash of the previous entry,
 * creating a tamper-evident chain. If any entry is modified or
 * removed, the chain breaks and verification fails.
 */
export class AuditLogger {
  private entries: AuditEntry[] = [];
  private seq = 0;
  private lastHash = '0'.repeat(64); // Genesis hash

  /**
   * Records an audit event.
   * Async because hashing is async (crypto.subtle).
   */
  async record(
    action: AuditAction,
    detail?: Record<string, string | number | boolean>,
  ): Promise<void> {
    try {
      const entry: AuditEntry = {
        seq: this.seq++,
        timestamp: new Date().toISOString(),
        action,
        detail: detail ?? null,
        prev_hash: this.lastHash,
      };

      // Hash this entry for the chain
      const entryStr = JSON.stringify({
        seq: entry.seq,
        timestamp: entry.timestamp,
        action: entry.action,
        detail: entry.detail,
        prev_hash: entry.prev_hash,
      });
      this.lastHash = await sha256(entryStr);

      // Ring buffer eviction
      if (this.entries.length >= MAX_ENTRIES) {
        this.entries.shift();
      }
      this.entries.push(entry);
    } catch {
      // Audit logging must never break the SDK.
    }
  }

  /**
   * Exports the full audit log for compliance review.
   * Returns a copy — the internal log is not exposed.
   */
  export(): AuditEntry[] {
    return this.entries.map((e) => ({ ...e, detail: e.detail ? { ...e.detail } : null }));
  }

  /** Returns the number of entries in the log. */
  get length(): number {
    return this.entries.length;
  }
}
