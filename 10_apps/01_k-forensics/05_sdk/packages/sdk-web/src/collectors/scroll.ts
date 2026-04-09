/**
 * Scroll behavioral feature extraction.
 *
 * Runs in the Web Worker. Converts a window of raw scroll events
 * into the `ScrollSignal` wire type — velocity, direction distribution,
 * reading pauses, and rapid-scroll detection.
 *
 * No absolute coordinates are captured (SDK_BEST_PRACTICES §5.3).
 * Only timing gaps and direction metadata are used.
 *
 * @module collectors/scroll
 */

import type { ScrollSignal } from '../runtime/wire-protocol.js';

// ─── Raw event type ─────────────────────────────────────────────────────────

/** A single decoded scroll event from the event buffer. */
export interface RawScrollEvent {
  /** performance.now() timestamp. */
  ts: number;
  /** Direction hint from main thread (up/down/horizontal/unknown). */
  direction: 'up' | 'down' | 'horizontal' | 'unknown';
}

// ─── Constants ──────────────────────────────────────────────────────────────

/** Minimum gap (ms) between events to count as a "reading pause". */
const READING_PAUSE_MIN_MS = 1000;

/** Maximum gap (ms) for a reading pause (longer = user left the page). */
const READING_PAUSE_MAX_MS = 5000;

/** Minimum gap (ms) between events for rapid-scroll detection. */
const RAPID_SCROLL_MAX_GAP_MS = 50;

/** Minimum consecutive rapid events to qualify as a rapid scroll. */
const RAPID_SCROLL_MIN_BURST = 3;

// ─── Helpers ────────────────────────────────────────────────────────────────

function mean(values: number[]): number {
  if (values.length === 0) return 0;
  let sum = 0;
  for (let i = 0; i < values.length; i++) sum += values[i]!;
  return sum / values.length;
}

// ─── Public extractor ───────────────────────────────────────────────────────

/**
 * Extracts scroll behavioral features from a window of raw scroll events.
 *
 * Returns `null` if the events array is empty (no scroll activity in window).
 */
export function extractScroll(events: RawScrollEvent[]): ScrollSignal | null {
  if (events.length === 0) return null;

  // Direction counts
  let upCount = 0;
  let downCount = 0;
  let horizontalCount = 0;

  // Timing analysis
  const interEventGaps: number[] = [];
  let readingPauseCount = 0;
  let rapidBurstLength = 0;
  let rapidScrollCount = 0;

  for (let i = 0; i < events.length; i++) {
    const ev = events[i]!;

    // Count directions
    switch (ev.direction) {
      case 'up': upCount += 1; break;
      case 'down': downCount += 1; break;
      case 'horizontal': horizontalCount += 1; break;
      default: break;
    }

    // Inter-event timing (from second event onward)
    if (i > 0) {
      const gap = ev.ts - events[i - 1]!.ts;
      interEventGaps.push(gap);

      // Reading pause: gap between READING_PAUSE_MIN_MS and READING_PAUSE_MAX_MS
      if (gap >= READING_PAUSE_MIN_MS && gap <= READING_PAUSE_MAX_MS) {
        readingPauseCount += 1;
      }

      // Rapid scroll burst detection
      if (gap <= RAPID_SCROLL_MAX_GAP_MS) {
        rapidBurstLength += 1;
      } else {
        if (rapidBurstLength >= RAPID_SCROLL_MIN_BURST) {
          rapidScrollCount += 1;
        }
        rapidBurstLength = 0;
      }
    }
  }
  // Flush final burst
  if (rapidBurstLength >= RAPID_SCROLL_MIN_BURST) {
    rapidScrollCount += 1;
  }

  // Velocity: events per second (inverse of mean gap)
  const meanGap = mean(interEventGaps);
  const meanVelocity = meanGap > 0 ? 1000 / meanGap : 0;

  // Mean distance per scroll is not available without absolute coordinates.
  // We use 0 as a placeholder — the server relies on velocity + direction.
  const meanDistancePerScroll = 0;

  // Direction distribution (normalized fractions)
  const total = upCount + downCount + horizontalCount;
  const safeDivisor = total > 0 ? total : 1;

  return {
    available: true,
    scroll_events: events.length,
    mean_velocity: Math.round(meanVelocity * 100) / 100,
    mean_distance_per_scroll: meanDistancePerScroll,
    reading_pause_count: readingPauseCount,
    rapid_scroll_count: rapidScrollCount,
    direction_distribution: {
      up: Math.round((upCount / safeDivisor) * 100) / 100,
      down: Math.round((downCount / safeDivisor) * 100) / 100,
      horizontal: Math.round((horizontalCount / safeDivisor) * 100) / 100,
    },
  };
}
