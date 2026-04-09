/**
 * worker-entry.ts
 *
 * Web Worker entry point for the K-Protect SDK.
 *
 * When loaded as a Web Worker this module:
 *   1. Receives the INIT message from the main thread.
 *   2. Instantiates all worker-side modules (IdentityStore, SessionManager,
 *      PageGate, CriticalActionRouter).
 *   3. Wires the pulse callback to the inline Transport.
 *   4. Routes all subsequent MainToWorkerMsg messages to the correct handler.
 *
 * Also exports `createWorkerMessageRouter` for use by MainThreadFallback,
 * which runs the same logic on the main thread in idle callbacks when Worker
 * instantiation fails.
 *
 * Runs in the Worker global scope — no DOM access.
 * SDK_BEST_PRACTICES §1.2, §8, §11 (Transport Contract).
 *
 * RULES:
 *   - No DOM APIs (document, window, location, history).
 *   - All timing via performance.now().
 *   - try/catch every browser API (IDB, fetch, CompressionStream).
 *   - Zero runtime npm dependencies.
 *   - No `any` types.
 */

import { IdentityStore } from '../session/identity-store.js';
import { SessionManager } from '../session/session-manager.js';
import { PageGate } from '../session/page-gate.js';
import { CriticalActionRouter } from '../session/critical-action-router.js';
import { AuditLogger } from '../session/audit-logger.js';
import type {
  MainToWorkerMsg,
  WorkerToMainMsg,
  ResolvedConfig,
  BehavioralBatch,
  CriticalActionBatch,
  KeepaliveBatch,
  SessionEventBatch,
  DeviceFingerprintBatch,
  DriftScoreResponse,
  EventTapMsg,
  SignalSet,
  DeviceFingerprint,
  SessionEndReason,
} from './wire-protocol.js';
import { MAX_TRANSPORT_QUEUE_DEPTH, MAX_BATCH_PAYLOAD_BYTES, MIN_EVENTS_FOR_PULSE } from '../config/defaults.js';
import { createEventBuffer } from '../collectors/event-buffer.js';
import { extractKeystroke } from '../collectors/keystroke.js';
import { extractGesture } from '../collectors/gesture.js';
import { extractScroll } from '../collectors/scroll.js';
import { sha256, hmacSha256, generateSigningKey } from '../signals/crypto-utils.js';

// ─── SDK version ──────────────────────────────────────────────────────────────

/** Semver placeholder — replaced by the build pipeline. */
const SDK_VERSION = '1.0.0';

// ─── Worker mode ──────────────────────────────────────────────────────────────

/**
 * Detects whether this code is running inside a Web Worker global scope.
 *
 * We avoid referencing `WorkerGlobalScope` / `DedicatedWorkerGlobalScope` by
 * name because those types only exist in the `lib.webworker.d.ts` declarations
 * and would cause compile errors when built against `lib.dom.d.ts`. Instead,
 * we probe for the absence of `document` (not present in workers) combined
 * with the presence of `self` and a `postMessage` function.
 */
const IS_WORKER: boolean = (() => {
  try {
    return (
      typeof self !== 'undefined' &&
      typeof document === 'undefined' &&
      typeof (self as unknown as Record<string, unknown>)['postMessage'] === 'function'
    );
  } catch {
    return false;
  }
})();

// ─── Transport ────────────────────────────────────────────────────────────────

/** Union of all batch types the transport can send. */
type AnyTransportBatch =
  | BehavioralBatch
  | CriticalActionBatch
  | DeviceFingerprintBatch
  | KeepaliveBatch
  | SessionEventBatch;

/**
 * Compresses `payload` using CompressionStream('gzip') if available.
 * Falls back to the raw JSON string on browsers that lack the API.
 *
 * @returns  A Blob that can be used as a fetch body, with the appropriate
 *           Content-Type header.
 */
async function compressPayload(payload: string): Promise<{ body: Blob; contentType: string }> {
  try {
    if (typeof CompressionStream === 'function') {
      const stream = new CompressionStream('gzip');
      const writer = stream.writable.getWriter();
      const encoder = new TextEncoder();
      await writer.write(encoder.encode(payload));
      await writer.close();
      const chunks: Uint8Array[] = [];
      const reader = stream.readable.getReader();
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        chunks.push(value);
      }
      const total = chunks.reduce((acc, c) => acc + c.byteLength, 0);
      const merged = new Uint8Array(total);
      let offset = 0;
      for (const chunk of chunks) {
        merged.set(chunk, offset);
        offset += chunk.byteLength;
      }
      return {
        body: new Blob([merged], { type: 'application/octet-stream' }),
        contentType: 'application/octet-stream',
      };
    }
  } catch {
    // CompressionStream unavailable or failed — fall through to JSON.
  }
  return {
    body: new Blob([payload], { type: 'application/json' }),
    contentType: 'application/json',
  };
}

/**
 * Sleeps for `ms` milliseconds. Used in retry back-off.
 * Uses a plain function reference (never a string) per §14.1.
 */
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => { setTimeout(resolve, ms); });
}

/**
 * createTransport — builds the transport object bound to the given config
 * and postToMain channel.
 *
 * The transport is intentionally kept minimal — it is not a class because
 * it is only ever instantiated once per worker session.
 */
function createTransport(
  config: ResolvedConfig,
  postToMain: (msg: WorkerToMainMsg) => void,
  signingKey: ArrayBuffer | null,
  auditLogger?: AuditLogger,
): {
  enqueue: (batch: AnyTransportBatch) => void;
  send: (batch: AnyTransportBatch, priority?: boolean) => Promise<void>;
  queueDepth: () => number;
} {
  const queue: AnyTransportBatch[] = [];

  /** Adds a batch to the retry queue with ring-buffer eviction (§11.4). */
  function enqueue(batch: AnyTransportBatch): void {
    if (queue.length >= MAX_TRANSPORT_QUEUE_DEPTH) {
      // Drop oldest — ring eviction.
      queue.shift();
    }
    queue.push(batch);
  }

  /**
   * Sends a single batch to the ingest endpoint.
   *
   * Retry policy (SDK_BEST_PRACTICES §11.4):
   *   - 2xx   → success, return.
   *   - 429   → backoff 2s → 4s → 8s → 16s (4 attempts).
   *   - 5xx   → backoff 1s → 2s → 4s (3 attempts).
   *   - net   → backoff 1s → 2s → 4s (3 attempts).
   *   - 4xx   → drop, log debug. Never retry.
   */
  async function send(batch: AnyTransportBatch, _priority = false): Promise<void> {
    let payload: string;
    try {
      payload = JSON.stringify(batch);
    } catch {
      // Serialization failed — drop silently.
      return;
    }

    // ── Payload size enforcement (Finding 18) ────────────────────────────────
    if (payload.length > MAX_BATCH_PAYLOAD_BYTES && 'signals' in batch) {
      const bb = batch as BehavioralBatch;
      if (bb.signals) {
        const dropOrder: (keyof SignalSet)[] = [
          'gesture', 'keystroke', 'scroll', 'sensor', 'credential', 'pointer', 'touch',
        ];
        const trimmed = { ...bb.signals };
        for (const key of dropOrder) {
          if (key in trimmed) {
            delete trimmed[key];
            const tp = JSON.stringify({ ...batch, signals: trimmed });
            if (tp.length <= MAX_BATCH_PAYLOAD_BYTES) {
              payload = tp;
              break;
            }
          }
        }
      }
    }

    // ── Batch checksum (Finding 19) — SHA-256 of serialized payload ────────
    let payloadChecksum: string | null = null;
    try {
      payloadChecksum = await sha256(payload);
    } catch {
      // crypto.subtle unavailable — skip checksum.
    }

    const { body, contentType } = await compressPayload(payload);
    const isGzip = contentType === 'application/octet-stream';

    const headers: Record<string, string> = {
      'Content-Type': contentType,
    };
    if (isGzip) {
      headers['Content-Encoding'] = 'gzip';
    }

    // Batch integrity checksum header.
    if (payloadChecksum) {
      headers['X-KP-Checksum'] = payloadChecksum;
    }

    // Session / device headers (present when batch is a behavioral/critical batch).
    if ('session_id' in batch) {
      headers['X-KP-Session'] = (batch as BehavioralBatch).session_id;
    }
    if ('device_uuid' in batch) {
      const uuid = (batch as unknown as Record<string, unknown>)['device_uuid'];
      if (typeof uuid === 'string') headers['X-KP-Device'] = uuid;
    }

    // Origin binding header (Finding 11).
    if ('origin_hash' in batch && typeof (batch as unknown as Record<string, unknown>)['origin_hash'] === 'string') {
      headers['X-KP-Origin-Hash'] = (batch as unknown as Record<string, unknown>)['origin_hash'] as string;
    }

    // ── API key authentication (never send raw key) ─────────────────────────
    // Token = HMAC-SHA256(api_key_as_key, timestamp + '.' + batch_id)
    // Server looks up the api_key by the key prefix (first 12 chars) and validates.
    try {
      const apiKeyBytes = new TextEncoder().encode(config.api_key);
      const sentAtStr = String(batch.sent_at);
      const authMessage = `${sentAtStr}.${batch.batch_id}`;
      const authToken = await hmacSha256(apiKeyBytes, authMessage);
      if (authToken) {
        headers['X-KP-Key-Id'] = config.api_key.substring(0, 12);
        headers['X-KP-Auth-Token'] = authToken;
        headers['X-KP-Auth-Timestamp'] = sentAtStr;
      } else {
        // crypto.subtle unavailable — fall back to raw key (insecure context only)
        headers['X-KP-API-Key'] = config.api_key;
      }
    } catch {
      // Auth derivation failed — fall back to raw key
      headers['X-KP-API-Key'] = config.api_key;
    }

    // ── HMAC-SHA256 payload signing (replay protection) ───────────────────────
    // Message: batch_id + '.' + sent_at + '.' + sha256(payload)
    // The batch_id (UUID) serves as nonce for replay protection.
    if (signingKey) {
      try {
        const payloadHash = await sha256(payload);
        const sentAtStr = String(batch.sent_at);
        const signatureMessage = `${batch.batch_id}.${sentAtStr}.${payloadHash}`;
        const signature = await hmacSha256(signingKey, signatureMessage);
        if (signature) {
          headers['X-KP-Signature'] = signature;
          headers['X-KP-Timestamp'] = sentAtStr;
          headers['X-KP-Nonce'] = batch.batch_id;
        } else {
          // hmacSha256 returned null — crypto.subtle unavailable at runtime.
          headers['X-KP-Unsigned'] = 'true';
        }
      } catch {
        // Signing failed — send unsigned so server can decide policy.
        headers['X-KP-Unsigned'] = 'true';
      }
    } else {
      // No signing key available (e.g., crypto.subtle was unavailable at init).
      headers['X-KP-Unsigned'] = 'true';
    }

    const delaysFor429 = [2000, 4000, 8000, 16000];
    const delaysFor5xx  = [1000, 2000, 4000];
    const delaysForNet  = [1000, 2000, 4000];

    let lastError: unknown = null;

    // Attempt with retry.
    const attemptSend = async (retryDelays: number[]): Promise<'ok' | 'drop' | 'retry'> => {
      for (let attempt = 0; attempt <= retryDelays.length; attempt++) {
        try {
          const response = await fetch(config.transport.endpoint, {
            method: 'POST',
            keepalive: true,
            headers,
            body,
          });

          if (response.ok) {
            // Parse the drift score response and forward to main thread.
            try {
              const json: unknown = await response.json();
              if (
                json !== null &&
                typeof json === 'object' &&
                'drift_score' in json
              ) {
                const drift = json as DriftScoreResponse;
                if (batch.type === 'critical_action') {
                  postToMain({ type: 'CRITICAL_ACTION_RESULT', response: drift });
                } else {
                  postToMain({ type: 'DRIFT_SCORE', response: drift });
                }
                // Forward any alerts.
                if (Array.isArray(drift.alerts) && drift.alerts.length > 0) {
                  postToMain({ type: 'ALERT', alerts: drift.alerts });
                }
              }
            } catch {
              // Response body parse failed — not fatal.
            }
            if (auditLogger) {
              void auditLogger.record('batch_sent', { batch_id: batch.batch_id, type: batch.type });
            }
            return 'ok';
          }

          if (response.status === 429) {
            if (attempt < retryDelays.length) {
              await sleep(delaysFor429[attempt] ?? 2000);
              continue;
            }
            return 'retry'; // Exhausted — re-enqueue.
          }

          if (response.status >= 500) {
            if (attempt < retryDelays.length) {
              await sleep(delaysFor5xx[attempt] ?? 1000);
              continue;
            }
            return 'retry';
          }

          // 4xx non-429 → drop.
          if (config.environment === 'debug') {
            // eslint-disable-next-line no-console
            console.debug(`KProtect: batch dropped, HTTP ${response.status.toString()}`);
          }
          return 'drop';
        } catch (err) {
          lastError = err;
          if (attempt < retryDelays.length) {
            await sleep(delaysForNet[attempt] ?? 1000);
          }
        }
      }
      return 'retry';
    };

    // Determine initial retry schedule — attempt first; inspect status.
    const outcome = await attemptSend(delaysFor5xx);
    if (outcome === 'retry') {
      if (auditLogger) {
        void auditLogger.record('batch_failed', { batch_id: batch.batch_id, type: batch.type });
      }
      // Re-enqueue for a later attempt (best-effort; no infinite loop).
      enqueue(batch);
      if (config.environment === 'debug') {
        // eslint-disable-next-line no-console
        console.debug('KProtect: batch re-queued after exhausting retries', lastError);
      }
    }
  }

  return {
    enqueue,
    send,
    queueDepth: () => queue.length,
  };
}

// ─── Feature extraction helper ────────────────────────────────────────────────

/**
 * Drains the event buffer and runs feature extraction for all signal types.
 * Returns the total event count and populated SignalSet.
 *
 * SDK_BEST_PRACTICES §5.4: raw events are discarded after each extraction window.
 */
function extractSignals(
  eventBuffer: ReturnType<typeof createEventBuffer>,
): { eventCount: number; signals: SignalSet } {
  const snapshot = eventBuffer.drain();

  const signals: SignalSet = {};

  const ks = extractKeystroke(snapshot.keystroke);
  if (ks) signals.keystroke = ks;

  const gs = extractGesture(snapshot.pointer, snapshot.touch);
  if (gs) signals.gesture = gs;

  const sc = extractScroll(snapshot.scroll);
  if (sc) signals.scroll = sc;

  return { eventCount: snapshot.totalCount, signals };
}

// ─── Session context builder ──────────────────────────────────────────────────

/** Type of the session-context provider passed to CriticalActionRouter. */
type SessionContextProvider = () => {
  session_id: string;
  pulse: number;
  user_hash: string;
  device_uuid: string;
  pulse_interval_ms: number;
  environment: 'production' | 'debug';
  session_start_epoch: number;
};

// ─── createWorkerMessageRouter ────────────────────────────────────────────────

/**
 * Builds and returns a message-routing function that processes
 * `MainToWorkerMsg` messages using fully instantiated worker-side modules.
 *
 * Exported so `MainThreadFallback` can run the same logic on the main thread
 * inside idle callbacks, without duplicating the module wiring.
 *
 * @param initialConfig  The resolved config — may be overridden once INIT is received.
 * @param postToMain     Channel for sending `WorkerToMainMsg` back to the bridge.
 * @returns              A message-handler function.
 */
export function createWorkerMessageRouter(
  initialConfig: ResolvedConfig,
  postToMain: (msg: WorkerToMainMsg) => void,
): (msg: MainToWorkerMsg) => void {

  // ── Module instances (lazily initialised on INIT) ──────────────────────────

  const auditLogger = new AuditLogger();

  let identityStore: IdentityStore | null = null;
  let sessionManager: SessionManager | null = null;
  let pageGate: PageGate | null = null;
  let criticalActionRouter: CriticalActionRouter | null = null;
  let transport: ReturnType<typeof createTransport> | null = null;
  let config: ResolvedConfig = initialConfig;
  let currentPath = '/';
  let sessionStartEpoch = 0;
  let sequenceCounter = 0;
  /** Per-session HMAC signing key, generated once at INIT. */
  let signingKey: ArrayBuffer | null = null;
  /** Origin from main thread for session origin binding (Finding 11). */
  let workerOrigin: string | undefined;
  /** Tracks whether the first behavioral/keepalive batch has been sent this session (Finding 6). */
  let firstBatchSent = false;
  /** Cached automation score from device fingerprint (0.0–1.0). */
  let cachedAutomationScore: number | undefined;

  const eventBuffer = createEventBuffer();

  // ── Context provider for CriticalActionRouter ──────────────────────────────

  const getSessionContext: SessionContextProvider = () => ({
    session_id: sessionManager?.getSessionId() ?? '',
    pulse: sessionManager?.getPulse() ?? 0,
    user_hash: identityStore?.getUserHash() ?? '',
    device_uuid: identityStore?.getDeviceUuid() ?? '',
    pulse_interval_ms: config.session.pulse_interval_ms,
    environment: config.environment,
    session_start_epoch: sessionStartEpoch,
  });

  // ── Pulse handler ──────────────────────────────────────────────────────────

  /**
   * Assembles and transmits a batch on each pulse tick.
   *
   * On 'normal' pages: sends a BehavioralBatch.
   * On 'critical_action' pages: sends a KeepaliveBatch (§8.2).
   *
   * @param phase  The pulse phase determined by SessionManager.
   */
  function onPulse(phase: 'normal' | 'keepalive'): void {
    if (!sessionManager || !identityStore || !transport) return;

    const sessionId = sessionManager.getSessionId();
    const userHash = identityStore.getUserHash();
    const deviceUuid = identityStore.getDeviceUuid();
    if (!sessionId || !userHash || !deviceUuid) return;

    // Skip normal pulses with too few events — avoids diluted/useless batches.
    if (phase === 'normal' && eventBuffer.count() < MIN_EVENTS_FOR_PULSE) return;

    sequenceCounter += 1;

    const now = performance.now();
    const sentAt = sessionStartEpoch + now;
    const { eventCount, signals } = extractSignals(eventBuffer);

    let batchId: string;
    try {
      batchId = crypto.randomUUID();
    } catch {
      batchId = `${now.toFixed(0)}-${Math.random().toString(36).slice(2)}`;
    }

    // Finding 6: Only include device_uuid and origin_hash in the first
    // behavioral/keepalive batch of a session to reduce per-batch redundancy.
    // SessionEventBatch and DeviceFingerprintBatch always include them.
    const includeDeviceContext = !firstBatchSent;

    if (phase === 'keepalive') {
      // Keepalive batch — no behavioral signals.
      const batch: KeepaliveBatch = {
        type: 'keepalive',
        batch_id: batchId,
        sent_at: sentAt,
        session_id: sessionId,
        pulse: sessionManager.getPulse(),
        pulse_interval_ms: config.session.keepalive_interval_ms,
        user_hash: userHash,
        ...(includeDeviceContext ? { device_uuid: deviceUuid } : {}),
        ...(includeDeviceContext ? { origin_hash: sessionManager.getOriginHash() ?? undefined as string | undefined } : {}),
        page_context: {
          url_path: currentPath,
          page_class: 'critical_action',
          critical_action: pageGate?.getCurrentAction()?.action ?? '',
        },
        sdk: { version: SDK_VERSION, platform: 'web' },
      };
      void transport.send(batch);
    } else {
      // Normal behavioral batch.
      const batch: BehavioralBatch = {
        type: 'behavioral',
        batch_id: batchId,
        sent_at: sentAt,
        session_id: sessionId,
        pulse: sessionManager.getPulse(),
        pulse_interval_ms: config.session.pulse_interval_ms,
        sequence: sequenceCounter,
        user_hash: userHash,
        ...(includeDeviceContext ? { device_uuid: deviceUuid } : {}),
        ...(includeDeviceContext ? { origin_hash: sessionManager.getOriginHash() ?? undefined } : {}),
        page_context: {
          url_path: currentPath,
          page_class: 'normal',
        },
        window_start_ms: now - config.session.pulse_interval_ms,
        window_end_ms: now,
        event_count: eventCount,
        signals,
        ...(cachedAutomationScore !== undefined ? { automation_score: cachedAutomationScore } : {}),
        sdk: {
          version: SDK_VERSION,
          platform: 'web',
          worker_mode: IS_WORKER ? 'worker' : 'fallback_main_thread',
          environment: config.environment,
        },
      };
      void transport.send(batch);
    }

    firstBatchSent = true;

    // Emit state update after each pulse.
    if (sessionManager) {
      postToMain({
        type: 'STATE_UPDATE',
        state: {
          ...sessionManager.getSessionState(),
          transport_queue_depth: transport.queueDepth(),
        },
      });
    }
  }

  /** Handles idle timeout from SessionManager. */
  function onIdle(): void {
    sessionManager?.end('idle_timeout');
  }

  // ── Session event batch helpers ────────────────────────────────────────────

  /**
   * Sends a session_start event batch to the ingest endpoint.
   * Called once when sessionManager.start() fires SESSION_STARTED.
   */
  function sendSessionStart(sessionId: string): void {
    if (!identityStore || !transport) return;

    const deviceUuid = identityStore.getDeviceUuid();
    if (!deviceUuid) return;

    sessionStartEpoch = Date.now();
    sequenceCounter = 0;
    firstBatchSent = false;

    let batchId: string;
    try {
      batchId = crypto.randomUUID();
    } catch {
      batchId = `${performance.now().toFixed(0)}-${Math.random().toString(36).slice(2)}`;
    }

    const batch: SessionEventBatch = {
      type: 'session_start',
      batch_id: batchId,
      sent_at: sessionStartEpoch,
      session_id: sessionId,
      user_hash: identityStore.getUserHash(),
      device_uuid: deviceUuid,
      session_start_ms: sessionStartEpoch,
      total_pulses: 0,
      origin_hash: sessionManager?.getOriginHash() ?? undefined,
      sdk: { version: SDK_VERSION, platform: 'web' },
    };

    void transport.send(batch, true);
  }

  /**
   * Sends a session_end event batch. Called from handleLogout / handleDestroy
   * and also from the idle-timeout path.
   */
  function sendSessionEnd(
    sessionId: string,
    reason: SessionEndReason,
  ): void {
    if (!identityStore || !transport) return;

    const deviceUuid = identityStore.getDeviceUuid();
    if (!deviceUuid) return;

    const now = sessionStartEpoch + performance.now();

    let batchId: string;
    try {
      batchId = crypto.randomUUID();
    } catch {
      batchId = `${performance.now().toFixed(0)}-${Math.random().toString(36).slice(2)}`;
    }

    const batch: SessionEventBatch = {
      type: 'session_end',
      batch_id: batchId,
      sent_at: now,
      session_id: sessionId,
      user_hash: identityStore.getUserHash(),
      device_uuid: deviceUuid,
      session_start_ms: sessionStartEpoch,
      session_end_ms: now,
      end_reason: reason,
      total_pulses: sessionManager?.getPulse() ?? 0,
      origin_hash: sessionManager?.getOriginHash() ?? undefined,
      sdk: { version: SDK_VERSION, platform: 'web' },
    };

    void transport.send(batch, true);
  }

  // ── Individual message handlers ────────────────────────────────────────────

  function handleInit(initConfig: ResolvedConfig, origin?: string): void {
    config = initConfig;
    workerOrigin = origin;

    void auditLogger.record('sdk_init', { environment: config.environment });

    // Generate per-session HMAC signing key for payload integrity + replay protection.
    try {
      const keyBytes = generateSigningKey();
      signingKey = keyBytes.buffer as ArrayBuffer;
    } catch {
      // crypto.getRandomValues unavailable — transport will send unsigned.
      signingKey = null;
    }

    transport = createTransport(config, postToMain, signingKey, auditLogger);

    identityStore = new IdentityStore(postToMain);
    pageGate = new PageGate(config);

    criticalActionRouter = new CriticalActionRouter(getSessionContext);

    // Intercept SESSION_STARTED / SESSION_ENDED to send event batches.
    const wrappedPostToMain = (msg: WorkerToMainMsg): void => {
      if (msg.type === 'SESSION_STARTED') {
        postToMain(msg);
        sendSessionStart(msg.session_id);
      } else if (msg.type === 'SESSION_ENDED') {
        postToMain(msg);
        sendSessionEnd(msg.session_id, msg.reason);
      } else {
        postToMain(msg);
      }
    };

    sessionManager = new SessionManager(
      config,
      identityStore,
      wrappedPostToMain,
      onPulse,
      onIdle,
      workerOrigin,
    );

    // Read seeds from main-thread localStorage (passed in separately via
    // the bridge in a real scenario). For now, init with null seeds —
    // IdentityStore will check IDB itself.
    void identityStore.init({ username: null, device_uuid: null }).then(() => {
      sessionManager?.start();
      // Update initial path in PageGate.
      if (pageGate) {
        try {
          // In worker scope, location is not available — use currentPath default '/'.
          pageGate.update(currentPath);
        } catch {
          // Not available in worker scope.
        }
      }
    });
  }

  function handleEventTap(msg: EventTapMsg): void {
    // Record liveness event on the session manager.
    sessionManager?.recordEvent();
    // Decode and buffer the raw event for feature extraction at next pulse.
    eventBuffer.record(msg.signal, msg.data);
  }

  function handleRouteChange(path: string): void {
    const previousPath = currentPath;
    currentPath = path;

    if (!pageGate || !sessionManager) return;

    const result = pageGate.update(path);

    if (result.changed) {
      sessionManager.setPageClass(result.pageClass, result.action);

      if (result.pageClass === 'critical_action' && result.action) {
        // Entering a critical-action page — reset the staging buffer.
        criticalActionRouter?.reset(result.action.action);
      } else if (pageGate.getCurrentClass() !== 'critical_action') {
        // Navigating AWAY from a critical-action page — abandon staged data.
        if (criticalActionRouter?.hasStagedData()) {
          const previousAction = pageGate.getCurrentAction()?.action ?? '';
          const batch = criticalActionRouter.abandon(previousAction, previousPath);
          if (batch && transport) {
            void transport.send(batch, true);
          }
          criticalActionRouter?.clear();
        }
      }
    }
  }

  function handleVisibilityChange(visible: boolean): void {
    void sessionManager?.setVisibility(visible);
  }

  function handleUsernameCaptured(userHash: string): void {
    identityStore?.setUsername(userHash, '');
    sessionManager?.onUsernameCapture();
    void auditLogger.record('username_captured');
    // Echo back to main thread so host app can observe identity capture.
    postToMain({ type: 'USERNAME_CAPTURED', user_hash: userHash });
  }

  function handleCriticalActionCommit(action: string): void {
    if (!criticalActionRouter || !transport) return;

    const batch = criticalActionRouter.commit(action, currentPath);
    if (batch) {
      void transport.send(batch, true);
    }
    criticalActionRouter.clear();
  }

  function handleLogout(): void {
    void auditLogger.record('logout');
    const sessionId = sessionManager?.getSessionId();
    identityStore?.clearUsername();
    if (sessionId) {
      sendSessionEnd(sessionId, 'logout');
    }
    sessionManager?.end('logout');
  }

  function handleDestroy(clearIdentity: boolean): void {
    void auditLogger.record('destroy', { clear_identity: clearIdentity });
    const sessionId = sessionManager?.getSessionId();
    if (clearIdentity) {
      identityStore?.clearAll();
    }
    if (sessionId) {
      sendSessionEnd(sessionId, 'destroy');
    }
    sessionManager?.end('destroy');
  }

  function handleDeviceFingerprint(fingerprint: DeviceFingerprint): void {
    if (!identityStore || !transport) return;

    const sessionId = sessionManager?.getSessionId();
    if (!sessionId) return;

    void auditLogger.record('fingerprint_collected', { session_id: sessionId });

    // Cache automation score for inclusion in behavioral batches.
    if (fingerprint.automation !== null && typeof fingerprint.automation.score === 'number') {
      cachedAutomationScore = fingerprint.automation.score;
    }

    let batchId: string;
    try {
      batchId = crypto.randomUUID();
    } catch {
      batchId = `${performance.now().toFixed(0)}-${Math.random().toString(36).slice(2)}`;
    }

    const batch: DeviceFingerprintBatch = {
      type: 'device_fingerprint',
      batch_id: batchId,
      sent_at: sessionStartEpoch + performance.now(),
      session_id: sessionId,
      user_hash: identityStore.getUserHash(),
      device_uuid: identityStore.getDeviceUuid() ?? '',
      fingerprint,
      sdk: {
        version: SDK_VERSION,
        platform: 'web',
      },
    };

    transport.send(batch, true).catch(() => {
      // Best-effort — enqueue for retry if send fails.
      transport?.enqueue(batch);
    });
  }

  // ── Return the routing function ────────────────────────────────────────────

  return function routeMessage(msg: MainToWorkerMsg): void {
    switch (msg.type) {
      case 'INIT':
        handleInit(msg.config, msg.origin);
        break;
      case 'EVENT_TAP':
        handleEventTap(msg);
        break;
      case 'ROUTE_CHANGE':
        handleRouteChange(msg.path);
        break;
      case 'VISIBILITY_CHANGE':
        handleVisibilityChange(msg.visible);
        break;
      case 'USERNAME_CAPTURED':
        handleUsernameCaptured(msg.user_hash);
        break;
      case 'CRITICAL_ACTION_COMMIT':
        handleCriticalActionCommit(msg.action);
        break;
      case 'LOGOUT':
        handleLogout();
        break;
      case 'DESTROY':
        handleDestroy(msg.clearIdentity);
        break;
      case 'DEVICE_FINGERPRINT':
        handleDeviceFingerprint(msg.fingerprint);
        break;
      case 'MUTABLE_SIGNALS_UPDATE':
        // Mutable signals (network, battery) refreshed from main thread.
        // Logged in debug mode — included in the next behavioral batch by
        // the server-side enrichment pipeline (no separate send needed).
        if (config.environment === 'debug') {
          // eslint-disable-next-line no-console
          console.debug('KProtect: mutable signals updated', {
            network: msg.network,
            battery: msg.battery,
          });
        }
        break;
      case 'EXPORT_AUDIT_LOG':
        postToMain({
          type: 'AUDIT_LOG_EXPORT',
          entries: auditLogger.export(),
        } as unknown as WorkerToMainMsg);
        break;
    }
  };
}

// ─── Worker global scope bootstrap ───────────────────────────────────────────

/**
 * When this module is loaded as a Web Worker script, install the message
 * router on `self.onmessage`.
 *
 * The `if` guard prevents this from running when the module is imported by
 * `MainThreadFallback` in the main thread context.
 */
if (IS_WORKER) {
  /**
   * Type alias for `self` in a Dedicated Worker context.
   * We use `Record<string, unknown>` as the base type because the DOM tsconfig
   * does not include `DedicatedWorkerGlobalScope`. The runtime check above
   * guarantees we are in a worker when this branch executes.
   */
  type WorkerSelf = typeof self & {
    postMessage: (msg: unknown) => void;
    onmessage: ((event: MessageEvent) => void) | null;
  };

  const workerSelf = self as WorkerSelf;
  let port: MessagePort | null = null;

  // postToMain uses the secure MessagePort when available,
  // falls back to self.postMessage for legacy compatibility.
  const postToMain = (msg: WorkerToMainMsg): void => {
    try {
      if (port) {
        port.postMessage(msg);
      } else {
        workerSelf.postMessage(msg);
      }
    } catch {
      // postMessage can fail if the context is already closed — ignore.
    }
  };

  // The router is created with a dummy config that will be replaced on INIT.
  // This is safe because all handlers guard against null module instances.
  const dummyConfig: ResolvedConfig = {
    api_key: '',
    environment: 'production',
    transport: { mode: 'direct', endpoint: '' },
    session: { pulse_interval_ms: 30000, idle_timeout_ms: 900000, keepalive_interval_ms: 30000 },
    identity: { username: { selectors: [], sso_globals: [] } },
    page_gate: { opt_out_patterns: [] },
    critical_actions: { actions: [] },
    fingerprinting: { enabled: true },
    consent: { mode: 'opt-out' },
  };

  const routeMessage = createWorkerMessageRouter(dummyConfig, postToMain);

  // Initial handler: wait for PORT_INIT to establish secure MessageChannel.
  // Once port2 is received, all further messages flow through the private
  // MessagePort — the global onmessage is disabled to prevent interception
  // by third-party scripts on the same page.
  workerSelf.onmessage = (event: MessageEvent): void => {
    try {
      // Check if this is the MessageChannel port transfer.
      if (event.data?.type === 'PORT_INIT' && event.ports.length > 0) {
        port = event.ports[0]!;
        port.onmessage = (portEvent: MessageEvent<MainToWorkerMsg>): void => {
          try {
            routeMessage(portEvent.data);
          } catch {
            // Top-level worker errors must not crash the worker process (§13.1).
          }
        };
        // Disable the global onmessage — all further messages go through the port.
        workerSelf.onmessage = null;
        return;
      }

      // Fallback: if no port transfer, handle messages directly (legacy mode).
      routeMessage(event.data as MainToWorkerMsg);
    } catch {
      // Top-level worker errors must not crash the worker process (§13.1).
    }
  };
}
