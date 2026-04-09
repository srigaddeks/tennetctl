/**
 * Keystroke behavioral feature extraction.
 *
 * Runs in the Web Worker. Converts a window of raw keydown/keyup events
 * into the `KeystrokeSignal` wire type — timing summaries, rhythm metrics,
 * and zone-transition patterns. No key content is ever captured.
 *
 * @module collectors/keystroke
 */

import type { KeystrokeSignal, TimingSummary } from '../runtime/wire-protocol';
import { addLaplaceNoise2D } from './laplace-noise.js';
import { ZONE_MATRIX_LAPLACE_SCALE } from '../config/defaults.js';

// ─── Constants ───────────────────────────────────────────────────────────────

/** Zones 0–9 form the main keyboard model; zone 10 = special keys. */
const MATRIX_ZONES = 10;

/** Backspace lives in zone 4 of the 10-zone model. */
const BACKSPACE_ZONE = 4;

/** Keys-per-second threshold for "burst" typing (250 ms inter-key). */
const BURST_INTERVAL_MS = 250;

/** Minimum consecutive fast intervals to qualify as a burst. */
const BURST_MIN_LENGTH = 3;

/** Milliseconds per minute. */
const MS_PER_MINUTE = 60_000;

/** Average word length in characters (standard WPM convention). */
const CHARS_PER_WORD = 5;

// ─── Public types ────────────────────────────────────────────────────────────

/** Raw keystroke event stored in the worker buffer. */
export interface RawKeystrokeEvent {
  /** `kd` = keydown, `ku` = keyup */
  type: 'kd' | 'ku';
  /** 0–10 zone index, -1 for unmapped */
  zone: number;
  /** `performance.now()` timestamp in ms */
  ts: number;
}

// ─── Helpers (pure, zero-dependency) ─────────────────────────────────────────

/** Round to 2 decimal places. */
function r2(v: number): number {
  return Math.round(v * 100) / 100;
}

/** Arithmetic mean. Returns 0 for empty arrays. */
function mean(values: readonly number[]): number {
  if (values.length === 0) return 0;
  let sum = 0;
  for (let i = 0; i < values.length; i++) sum += values[i]!;
  return sum / values.length;
}

/** Population standard deviation. Returns null for fewer than 2 values (Finding 4). */
function stdDev(values: readonly number[]): number | null {
  if (values.length < 2) return null;
  const m = mean(values);
  let variance = 0;
  for (let i = 0; i < values.length; i++) {
    const diff = values[i]! - m;
    variance += diff * diff;
  }
  return Math.sqrt(variance / values.length);
}

/** Percentile from a pre-sorted array. */
function percentile(sorted: readonly number[], p: number): number {
  if (sorted.length === 0) return 0;
  const idx = Math.floor(sorted.length * p);
  return sorted[Math.min(idx, sorted.length - 1)] ?? 0;
}

/** Create a rows×cols matrix filled with zeroes. */
function zeros2D(rows: number, cols: number): number[][] {
  const matrix: number[][] = [];
  for (let r = 0; r < rows; r++) {
    const row: number[] = [];
    for (let c = 0; c < cols; c++) row.push(0);
    matrix.push(row);
  }
  return matrix;
}

// ─── TimingSummary builder ───────────────────────────────────────────────────

/**
 * Compute a `TimingSummary` (mean, std_dev, percentiles, sample_count)
 * from an array of timing values in milliseconds.
 *
 * Returns a zero-filled summary when the input array is empty.
 */
export function computeTimingSummary(values: readonly number[]): TimingSummary {
  if (values.length === 0) {
    return { mean: 0, std_dev: null, p25: 0, p50: 0, p75: 0, p95: 0, sample_count: 0 };
  }
  const sorted = values.slice().sort((a, b) => a - b);
  const sd = stdDev(values);
  return {
    mean: r2(mean(values)),
    std_dev: sd !== null ? r2(sd) : null,
    p25: r2(percentile(sorted, 0.25)),
    p50: r2(percentile(sorted, 0.50)),
    p75: r2(percentile(sorted, 0.75)),
    p95: r2(percentile(sorted, 0.95)),
    sample_count: values.length,
  };
}

// ─── Main extractor ──────────────────────────────────────────────────────────

/**
 * Obfuscates keystroke events from sensitive fields (password, PIN).
 * Preserves timing metadata (ts, type) but zeros out zone data.
 * Defense-in-depth: the spec already says no content capture, but this
 * adds explicit obfuscation for sensitive input fields (Finding 20).
 */
export function obfuscateSensitiveEvents(
  events: readonly RawKeystrokeEvent[],
): RawKeystrokeEvent[] {
  return events.map((ev) => ({
    type: ev.type,
    zone: -1,   // Zero out zone identity
    ts: ev.ts,  // Preserve timing only
  }));
}

/**
 * Extract a `KeystrokeSignal` from a window of raw keystroke events.
 *
 * Returns `null` when the events array is empty — the caller should omit
 * the keystroke signal from the batch in that case.
 *
 * @param sensitiveField  When true, key identity (zone) is zeroed out —
 *                        only timing metadata (dwell, flight) is preserved.
 */
export function extractKeystroke(
  events: readonly RawKeystrokeEvent[],
  sensitiveField = false,
): KeystrokeSignal | null {
  if (events.length === 0) return null;

  // Apply obfuscation for sensitive fields before processing.
  const processedEvents = sensitiveField ? obfuscateSensitiveEvents(events) : events;

  // ── Accumulators ─────────────────────────────────────────────────────────

  /** Pending keydown events awaiting their matching keyup. */
  const pendingDowns: Array<{ zone: number; ts: number }> = [];

  const dwells: number[] = [];
  const flights: number[] = [];

  let prevUpTs = -1;
  let backspaceCount = 0;
  let totalDown = 0;

  // Zone transition matrix (zones 0–9 only)
  const transitionCounts = zeros2D(MATRIX_ZONES, MATRIX_ZONES);
  let lastDownZone = -1;

  // Timestamps of valid keydowns (zones 0–9) for rhythm analysis
  const keyTimestamps: number[] = [];

  // Correction burst tracking
  let correctionSequences = 0;
  let consecutiveBackspaces = 0;

  // Set of zone IDs seen
  const zonesUsed = new Set<number>();

  // ── Single pass over events ──────────────────────────────────────────────

  for (let i = 0; i < processedEvents.length; i++) {
    const ev = processedEvents[i]!;
    const zone = ev.zone;

    if (ev.type === 'kd') {
      // ─ Keydown ─
      pendingDowns.push({ zone, ts: ev.ts });
      totalDown++;

      // Backspace detection: zone 4 in the 10-zone model
      if (zone === BACKSPACE_ZONE) {
        backspaceCount++;
        consecutiveBackspaces++;
      } else {
        // A non-backspace after one or more backspaces = correction sequence
        if (consecutiveBackspaces > 0) {
          correctionSequences++;
        }
        consecutiveBackspaces = 0;
      }

      // Only zones 0–9 participate in matrix & rhythm
      if (zone >= 0 && zone < MATRIX_ZONES) {
        zonesUsed.add(zone);
        keyTimestamps.push(ev.ts);

        if (lastDownZone >= 0 && lastDownZone < MATRIX_ZONES) {
          const row = transitionCounts[lastDownZone];
          if (row) row[zone] = (row[zone] ?? 0) + 1;
        }
        lastDownZone = zone;
      }
    } else {
      // ─ Keyup ─
      // Match to most-recent pending keydown with same zone (LIFO)
      let matchIdx = -1;
      for (let p = pendingDowns.length - 1; p >= 0; p--) {
        if (pendingDowns[p]!.zone === zone) {
          matchIdx = p;
          break;
        }
      }

      if (matchIdx >= 0) {
        const dwell = ev.ts - pendingDowns[matchIdx]!.ts;
        if (dwell >= 0) dwells.push(dwell);
        pendingDowns.splice(matchIdx, 1);
      }

      // Flight time: gap from previous keyup to this keyup
      if (prevUpTs > 0) {
        const flight = ev.ts - prevUpTs;
        if (flight >= 0) flights.push(flight);
      }
      prevUpTs = ev.ts;

      if (zone >= 0 && zone < MATRIX_ZONES) {
        zonesUsed.add(zone);
      }
    }
  }

  // ── Derived metrics ──────────────────────────────────────────────────────

  const firstEvent = processedEvents[0]!;
  const lastEvent = processedEvents[processedEvents.length - 1]!;
  const windowMs = processedEvents.length > 1
    ? lastEvent.ts - firstEvent.ts
    : 0;

  // Backspace rate: per 10 keystrokes
  const backspaceRate = totalDown > 0
    ? r2((backspaceCount / totalDown) * 10)
    : 0;

  // Correction burst rate: sequences per minute
  const correctionBurstRate = windowMs > 0
    ? r2((correctionSequences / windowMs) * MS_PER_MINUTE)
    : 0;

  // Words per minute: (keystrokes / chars_per_word) / (window_minutes)
  const windowMinutes = windowMs / MS_PER_MINUTE;
  const wordsPerMinute = windowMinutes > 0
    ? r2((totalDown / CHARS_PER_WORD) / windowMinutes)
    : 0;

  // Burst typing fraction
  const burstTypingFraction = computeBurstFraction(keyTimestamps);

  // Zone IDs as strings
  const zoneIdsUsed = Array.from(zonesUsed).sort((a, b) => a - b).map(String);

  // ── Assemble signal ──────────────────────────────────────────────────────

  const signal: KeystrokeSignal = {
    available: true,
    dwell_times: computeTimingSummary(dwells),
    flight_times: computeTimingSummary(flights),
    backspace_rate: backspaceRate,
    correction_burst_rate: correctionBurstRate,
    words_per_minute: wordsPerMinute,
    burst_typing_fraction: burstTypingFraction,
    zone_transition_matrix: addLaplaceNoise2D(transitionCounts, ZONE_MATRIX_LAPLACE_SCALE),
    zone_ids_used: zoneIdsUsed,
  };

  if (sensitiveField) {
    signal.sensitive_field_detected = true;
  }

  return signal;
}

// ─── Burst fraction helper ───────────────────────────────────────────────────

/**
 * Compute the fraction of typing time spent in "burst" mode (>4 keys/s).
 *
 * A burst is a run of ≥3 consecutive inter-key intervals each <250 ms.
 * The burst fraction is the total burst duration divided by the overall
 * typing window.
 */
function computeBurstFraction(timestamps: readonly number[]): number {
  if (timestamps.length < 2) return 0;

  const first = timestamps[0]!;
  const last = timestamps[timestamps.length - 1]!;
  const windowMs = last - first;
  if (windowMs <= 0) return 0;

  // Compute consecutive inter-key intervals
  const intervals: number[] = [];
  for (let i = 1; i < timestamps.length; i++) {
    intervals.push(timestamps[i]! - timestamps[i - 1]!);
  }

  // Identify bursts: runs of >=BURST_MIN_LENGTH consecutive fast intervals
  let burstDuration = 0;
  let currentRunDuration = 0;
  let currentRunLength = 0;

  for (let i = 0; i < intervals.length; i++) {
    const interval = intervals[i]!;
    if (interval < BURST_INTERVAL_MS) {
      currentRunDuration += interval;
      currentRunLength++;
    } else {
      if (currentRunLength >= BURST_MIN_LENGTH) {
        burstDuration += currentRunDuration;
      }
      currentRunDuration = 0;
      currentRunLength = 0;
    }
  }
  // Flush trailing burst
  if (currentRunLength >= BURST_MIN_LENGTH) {
    burstDuration += currentRunDuration;
  }

  return r2(burstDuration / windowMs);
}
