/**
 * critical-action-router.ts
 *
 * Manages the staging buffer for critical-action pages.
 *
 * Runs inside the Web Worker.
 *
 * On a critical-action page the BatchAssembler forwards each completed
 * feature window here instead of to the normal transport queue.  When the
 * user either commits (clicks the commit selector) or abandons (navigates
 * away), this router seals the windows into a CriticalActionBatch and
 * returns it for immediate transmission.
 *
 * SDK_BEST_PRACTICES §10 (Critical-Action Protocol).
 */

import type {
  SignalSet,
  CriticalActionBatch,
  CriticalPageContext,
  SdkMeta,
  TimingSummary,
  KeystrokeSignal,
  PointerSignal,
  TouchSignal,
  ScrollSignal,
  SensorSignal,
  CredentialSignal,
} from '../runtime/wire-protocol.js';

// ─── StagedWindow ──────────────────────────────────────────────────────────────

/**
 * A single feature-extraction window held in the staging buffer while the
 * user is on a critical-action page.
 */
export interface StagedWindow {
  /** performance.now() at the start of the extraction window. */
  window_start_ms: number;
  /** performance.now() at the end of the extraction window. */
  window_end_ms: number;
  /** Total raw events captured in this window. */
  event_count: number;
  /** Extracted behavioral signals for this window. */
  signals: SignalSet;
}

// ─── SDK_VERSION (placeholder — replaced by build pipeline) ───────────────────

const SDK_VERSION = '1.0.0';

// ─── Signal aggregation helpers ───────────────────────────────────────────────

/**
 * Merges an array of TimingSummary values into a single summary by computing
 * a weighted average across sample counts.
 * Returns a zero summary when the input is empty or all samples are zero.
 */
function mergeTimingSummaries(summaries: TimingSummary[]): TimingSummary {
  const valid = summaries.filter((s) => s.sample_count > 0);
  if (valid.length === 0) {
    return { mean: 0, std_dev: null, p25: 0, p50: 0, p75: 0, p95: 0, sample_count: 0 };
  }

  const totalSamples = valid.reduce((acc, s) => acc + s.sample_count, 0);
  const wavg = (field: keyof TimingSummary): number =>
    valid.reduce((acc, s) => acc + ((s[field] as number | null) ?? 0) * s.sample_count, 0) / totalSamples;

  // std_dev: weighted average of non-null values only; null when all are null (Finding 4).
  const withStdDev = valid.filter((s) => s.std_dev !== null);
  const mergedStdDev = withStdDev.length > 0
    ? withStdDev.reduce((acc, s) => acc + (s.std_dev as number) * s.sample_count, 0) /
      withStdDev.reduce((acc, s) => acc + s.sample_count, 0)
    : null;

  return {
    mean: wavg('mean'),
    std_dev: mergedStdDev,
    p25: wavg('p25'),
    p50: wavg('p50'),
    p75: wavg('p75'),
    p95: wavg('p95'),
    sample_count: totalSamples,
  };
}

/** Simple arithmetic mean of a numeric array. Returns 0 for empty arrays. */
function mean(values: number[]): number {
  if (values.length === 0) return 0;
  return values.reduce((a, b) => a + b, 0) / values.length;
}

/**
 * Aggregates an array of SignalSet objects into a single SignalSet.
 * Concatenates zone IDs across windows, averages scalar metrics, merges
 * TimingSummary objects by weighted sample count.
 * Signals unavailable in ALL windows are marked available:false.
 */
function aggregateSignalSets(windows: StagedWindow[]): SignalSet {
  const sets = windows.map((w) => w.signals);

  const result: SignalSet = {};
  const ks = aggregateKeystroke(sets);
  if (ks !== undefined) result.keystroke = ks;
  const ptr = aggregatePointer(sets);
  if (ptr !== undefined) result.pointer = ptr;
  const tch = aggregateTouch(sets);
  if (tch !== undefined) result.touch = tch;
  const scr = aggregateScroll(sets);
  if (scr !== undefined) result.scroll = scr;
  const sen = aggregateSensor(sets);
  if (sen !== undefined) result.sensor = sen;
  const cred = aggregateCredential(sets);
  if (cred !== undefined) result.credential = cred;
  return result;
}

function aggregateKeystroke(sets: SignalSet[]): KeystrokeSignal | undefined {
  const ks = sets.map((s) => s.keystroke).filter((k): k is KeystrokeSignal => k !== undefined);
  if (ks.length === 0) return undefined;

  const available = ks.some((k) => k.available);
  const zoneIds = [...new Set(ks.flatMap((k) => k.zone_ids_used))];
  // Sum zone-transition matrices element-wise.
  const matrix = ks.reduce<number[][]>((acc, k) => {
    if (acc.length === 0) return k.zone_transition_matrix.map((row) => [...row]);
    return acc.map((row, i) => row.map((val, j) => val + (k.zone_transition_matrix[i]?.[j] ?? 0)));
  }, []);

  return {
    available,
    dwell_times: mergeTimingSummaries(ks.map((k) => k.dwell_times)),
    flight_times: mergeTimingSummaries(ks.map((k) => k.flight_times)),
    backspace_rate: mean(ks.map((k) => k.backspace_rate)),
    correction_burst_rate: mean(ks.map((k) => k.correction_burst_rate)),
    words_per_minute: mean(ks.map((k) => k.words_per_minute)),
    burst_typing_fraction: mean(ks.map((k) => k.burst_typing_fraction)),
    zone_transition_matrix: matrix,
    zone_ids_used: zoneIds,
  };
}

function aggregatePointer(sets: SignalSet[]): PointerSignal | undefined {
  const ps = sets.map((s) => s.pointer).filter((p): p is PointerSignal => p !== undefined);
  if (ps.length === 0) return undefined;

  const available = ps.some((p) => p.available);
  const zoneIds = [...new Set(ps.flatMap((p) => p.clicks.zone_ids))];

  return {
    available,
    velocity: {
      mean: mean(ps.map((p) => p.velocity.mean)),
      max: Math.max(...ps.map((p) => p.velocity.max)),
      p50: mean(ps.map((p) => p.velocity.p50)),
      p95: mean(ps.map((p) => p.velocity.p95)),
    },
    acceleration: {
      mean: mean(ps.map((p) => p.acceleration.mean)),
      std_dev: mean(ps.map((p) => p.acceleration.std_dev)),
      direction_changes_per_sec: mean(ps.map((p) => p.acceleration.direction_changes_per_sec)),
    },
    clicks: {
      count: ps.reduce((acc, p) => acc + p.clicks.count, 0),
      double_click_count: ps.reduce((acc, p) => acc + p.clicks.double_click_count, 0),
      mean_dwell_ms: mean(ps.map((p) => p.clicks.mean_dwell_ms)),
      zone_ids: zoneIds,
    },
    idle_fraction: mean(ps.map((p) => p.idle_fraction)),
    ballistic_fraction: mean(ps.map((p) => p.ballistic_fraction)),
    micro_correction_rate: mean(ps.map((p) => p.micro_correction_rate)),
    mean_curvature: mean(ps.map((p) => p.mean_curvature)),
  };
}

function aggregateTouch(sets: SignalSet[]): TouchSignal | undefined {
  const ts = sets.map((s) => s.touch).filter((t): t is TouchSignal => t !== undefined);
  if (ts.length === 0) return undefined;

  const available = ts.some((t) => t.available);
  const zoneIds = [...new Set(ts.flatMap((t) => t.tap.zone_ids))];

  return {
    available,
    mean_contact_area: mean(ts.map((t) => t.mean_contact_area)),
    mean_pressure: mean(ts.map((t) => t.mean_pressure)),
    tap: {
      count: ts.reduce((acc, t) => acc + t.tap.count, 0),
      mean_dwell_ms: mean(ts.map((t) => t.tap.mean_dwell_ms)),
      mean_flight_ms: mean(ts.map((t) => t.tap.mean_flight_ms)),
      zone_ids: zoneIds,
    },
    swipe: {
      count: ts.reduce((acc, t) => acc + t.swipe.count, 0),
      mean_velocity: mean(ts.map((t) => t.swipe.mean_velocity)),
      mean_distance: mean(ts.map((t) => t.swipe.mean_distance)),
      direction_distribution: {
        up: mean(ts.map((t) => t.swipe.direction_distribution.up)),
        down: mean(ts.map((t) => t.swipe.direction_distribution.down)),
        left: mean(ts.map((t) => t.swipe.direction_distribution.left)),
        right: mean(ts.map((t) => t.swipe.direction_distribution.right)),
      },
    },
    pinch_count: ts.reduce((acc, t) => acc + t.pinch_count, 0),
    spread_count: ts.reduce((acc, t) => acc + t.spread_count, 0),
    // Use the mode of dominant_hand_hint across windows.
    dominant_hand_hint: dominantHandMode(ts.map((t) => t.dominant_hand_hint)),
  };
}

function dominantHandMode(
  hints: Array<'left' | 'right' | 'unknown'>,
): 'left' | 'right' | 'unknown' {
  const counts = { left: 0, right: 0, unknown: 0 };
  for (const h of hints) counts[h] += 1;
  if (counts.left >= counts.right && counts.left >= counts.unknown) return 'left';
  if (counts.right >= counts.unknown) return 'right';
  return 'unknown';
}

function aggregateScroll(sets: SignalSet[]): ScrollSignal | undefined {
  const ss = sets.map((s) => s.scroll).filter((s): s is ScrollSignal => s !== undefined);
  if (ss.length === 0) return undefined;

  const available = ss.some((s) => s.available);

  return {
    available,
    scroll_events: ss.reduce((acc, s) => acc + s.scroll_events, 0),
    mean_velocity: mean(ss.map((s) => s.mean_velocity)),
    mean_distance_per_scroll: mean(ss.map((s) => s.mean_distance_per_scroll)),
    reading_pause_count: ss.reduce((acc, s) => acc + s.reading_pause_count, 0),
    rapid_scroll_count: ss.reduce((acc, s) => acc + s.rapid_scroll_count, 0),
    direction_distribution: {
      up: mean(ss.map((s) => s.direction_distribution.up)),
      down: mean(ss.map((s) => s.direction_distribution.down)),
      horizontal: mean(ss.map((s) => s.direction_distribution.horizontal)),
    },
  };
}

function aggregateSensor(sets: SignalSet[]): SensorSignal | undefined {
  const sensors = sets.map((s) => s.sensor).filter((s): s is SensorSignal => s !== undefined);
  if (sensors.length === 0) return undefined;

  const available = sensors.some((s) => s.available);

  return {
    available,
    device_posture: sensors[sensors.length - 1]?.device_posture ?? 'unknown',
  };
}

function aggregateCredential(sets: SignalSet[]): CredentialSignal | undefined {
  const creds = sets.map((s) => s.credential).filter((c): c is CredentialSignal => c !== undefined);
  if (creds.length === 0) return undefined;

  const available = creds.some((c) => c.available);
  // For credential signals, use the last window's data (most recent interaction).
  const last = creds[creds.length - 1];

  // Finding 7: Only set available:true when at least one meaningful nested
  // field is present. Prevents misleading available:true with all-null data.
  const hasPasswordField = last?.password_field != null;
  const hasUsernameField = last?.username_field != null;
  const hasForm = last?.form != null;
  const hasMeaningfulData = hasPasswordField || hasUsernameField || hasForm;

  const result: CredentialSignal = { available: available && hasMeaningfulData };
  if (hasPasswordField) result.password_field = last!.password_field!;
  if (hasUsernameField) result.username_field = last!.username_field!;
  if (hasForm) result.form = last!.form!;
  return result;
}

// ─── CriticalActionRouter ─────────────────────────────────────────────────────

/**
 * CriticalActionRouter — manages the staging buffer for critical-action pages.
 *
 * The BatchAssembler routes feature windows here when page_class is
 * 'critical_action'.  On commit or abandon, this router seals them into a
 * complete CriticalActionBatch ready for transmission.
 */
export class CriticalActionRouter {
  /** Callback that provides live session context when building a batch. */
  private readonly getSessionContext: () => {
    session_id: string;
    pulse: number;
    user_hash: string;
    device_uuid: string;
    pulse_interval_ms: number;
    environment: 'production' | 'debug';
    session_start_epoch: number;
  };

  /** Buffered feature windows for the current critical-action page visit. */
  private stagedWindows: StagedWindow[] = [];

  /** performance.now() when the current critical-action page was entered. */
  private pageEnteredAt: number = 0;

  constructor(
    getSessionContext: () => {
      session_id: string;
      pulse: number;
      user_hash: string;
      device_uuid: string;
      pulse_interval_ms: number;
      environment: 'production' | 'debug';
      session_start_epoch: number;
    },
  ) {
    this.getSessionContext = getSessionContext;
  }

  // ─── Public API ────────────────────────────────────────────────────────────

  /**
   * Resets the router when entering a new critical-action page.
   * Records the entry timestamp and clears any previously staged windows.
   *
   * @param action  The action string for the new page (for logging context).
   */
  reset(_action: string): void {
    this.stagedWindows = [];
    this.pageEnteredAt = performance.now();
  }

  /**
   * Stages a completed feature window.  Called by the BatchAssembler whenever
   * a window closes while page_class === 'critical_action'.
   *
   * @param window  The completed feature window to buffer.
   */
  stage(window: StagedWindow): void {
    // Append a shallow copy for immutability.
    this.stagedWindows = [
      ...this.stagedWindows,
      { ...window, signals: { ...window.signals } },
    ];
  }

  /**
   * Seals the staging buffer into a committed CriticalActionBatch.
   * Returns null if no windows have been staged yet.
   *
   * @param action         The action string (from CriticalAction.action).
   * @param url_path       Current URL path.
   * @param referrer_path  Referring path in this session (optional).
   */
  commit(
    action: string,
    url_path: string,
    referrer_path?: string,
  ): CriticalActionBatch | null {
    return this.buildBatch(action, url_path, true, referrer_path);
  }

  /**
   * Seals the staging buffer into an abandoned CriticalActionBatch.
   * Returns null if no windows have been staged yet.
   *
   * @param action         The action string.
   * @param url_path       Current URL path.
   * @param referrer_path  Referring path in this session (optional).
   */
  abandon(
    action: string,
    url_path: string,
    referrer_path?: string,
  ): CriticalActionBatch | null {
    return this.buildBatch(action, url_path, false, referrer_path);
  }

  /** Returns true when at least one window is staged. */
  hasStagedData(): boolean {
    return this.stagedWindows.length > 0;
  }

  /** Returns the count of staged windows. */
  getStagedCount(): number {
    return this.stagedWindows.length;
  }

  /**
   * Clears the staging buffer.
   * Must be called after a commit/abandon batch has been handed off to transport.
   */
  clear(): void {
    this.stagedWindows = [];
    this.pageEnteredAt = 0;
  }

  // ─── Private helpers ───────────────────────────────────────────────────────

  /**
   * Builds a complete CriticalActionBatch from the staged windows.
   * Returns null if no windows are staged.
   */
  private buildBatch(
    action: string,
    url_path: string,
    committed: boolean,
    referrer_path?: string,
  ): CriticalActionBatch | null {
    if (this.stagedWindows.length === 0) return null;

    const ctx = this.getSessionContext();
    const now = performance.now();

    // Aggregate all staged windows into a single SignalSet.
    const signals = aggregateSignalSets(this.stagedWindows);

    // Window coverage spans from first to last staged window.
    const windowStart = this.stagedWindows[0]!.window_start_ms;
    const windowEnd = this.stagedWindows[this.stagedWindows.length - 1]!.window_end_ms;
    const totalEvents = this.stagedWindows.reduce((acc, w) => acc + w.event_count, 0);

    const pageContext: CriticalPageContext = {
      url_path,
      page_class: 'critical_action',
      critical_action: action,
      committed,
      time_on_page_ms: now - this.pageEnteredAt,
    };
    if (referrer_path !== undefined) pageContext.referrer_path = referrer_path;

    let batchId: string;
    try {
      batchId = crypto.randomUUID();
    } catch {
      batchId = `${now.toFixed(0)}-${Math.random().toString(36).slice(2)}`;
    }

    const sdk: SdkMeta = {
      version: SDK_VERSION,
      platform: 'web',
      worker_mode: 'worker',
      environment: ctx.environment,
    };

    const batch: CriticalActionBatch = {
      type: 'critical_action',
      batch_id: batchId,
      // Monotonic timestamp: sessionStartEpoch + performance.now() avoids
      // wall-clock jumps (NTP corrections, timezone changes). Consistent with
      // behavioral and keepalive batches (Finding 3).
      sent_at: ctx.session_start_epoch + performance.now(),
      session_id: ctx.session_id,
      pulse: ctx.pulse,
      pulse_interval_ms: ctx.pulse_interval_ms,
      sequence: ctx.pulse, // sequence tracks batches; reuse pulse as a proxy here
      user_hash: ctx.user_hash,
      device_uuid: ctx.device_uuid,
      page_context: pageContext,
      window_start_ms: windowStart,
      window_end_ms: windowEnd,
      event_count: totalEvents,
      signals,
      sdk,
    };

    return batch;
  }
}
