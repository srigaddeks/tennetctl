/**
 * event-buffer.ts
 *
 * Worker-side raw event buffer that stores decoded event data per signal type
 * and drains it each pulse for feature extraction.
 *
 * Replaces the stub `createEventCounter` in worker-entry.ts.
 *
 * SDK_BEST_PRACTICES §5.4: raw events are discarded after each extraction window.
 * No DOM APIs — runs in worker scope.
 */

import type { RawKeystrokeEvent } from './keystroke.js';
import type { RawPointerEvent, RawTouchEvent } from './gesture.js';
import type { RawScrollEvent } from './scroll.js';
import { MAX_EVENTS_PER_WINDOW } from '../config/defaults.js';

// ─── Raw event decoding ─────────────────────────────────────────────────────

/**
 * Decodes a 10-byte keystroke ArrayBuffer into a RawKeystrokeEvent.
 *
 * Layout:
 *   [0]    uint8   — signal type (1=kd, 2=ku)
 *   [1]    uint8   — zone index (0-10, 255=unmapped)
 *   [2..9] float64 — timestamp
 */
/** Valid zone indices: 0–10 for keyboard zones, -1 for unmapped (Finding 5). */
const VALID_ZONE_MAX = 10;

function decodeKeystroke(data: ArrayBuffer, signal: 'kd' | 'ku'): RawKeystrokeEvent {
  const view = new DataView(data);
  const zoneRaw = view.getUint8(1);
  // Map 255 → -1 (unmapped), then bounds-check: valid range is 0–10 or -1.
  // Out-of-range zones are clamped to -1 to prevent OOB matrix writes (Finding 5).
  let zone = zoneRaw === 255 ? -1 : zoneRaw;
  if (zone < -1 || zone > VALID_ZONE_MAX) {
    zone = -1;
  }
  const ts = view.getFloat64(2, true);
  return { type: signal, zone, ts };
}

/**
 * Decodes a 26-byte pointer ArrayBuffer into a RawPointerEvent.
 *
 * Layout:
 *   [0]      uint8   — signal type (3=pm, 4=pd, 10=cl)
 *   [1]      uint8   — zone index (unused for pointer)
 *   [2..9]   float64 — timestamp
 *   [10..17] float64 — vx
 *   [18..25] float64 — vy
 */
function decodePointer(data: ArrayBuffer, signal: 'pm' | 'pd' | 'pu' | 'cl'): RawPointerEvent {
  const view = new DataView(data);
  const ts = view.getFloat64(2, true);
  const vx = data.byteLength >= 26 ? view.getFloat64(10, true) : 0;
  const vy = data.byteLength >= 26 ? view.getFloat64(18, true) : 0;
  return { type: signal, ts, vx, vy };
}

/**
 * Decodes an 18-byte touch ArrayBuffer into a RawTouchEvent.
 *
 * Layout:
 *   [0]      uint8   — signal type (6=ts, 7=te, 8=tm)
 *   [1]      uint8   — touch count
 *   [2..9]   float64 — timestamp
 *   [10..17] float64 — contact area (0–1)
 */
function decodeTouch(data: ArrayBuffer, signal: 'ts' | 'te' | 'tm'): RawTouchEvent {
  const view = new DataView(data);
  const touchCount = view.getUint8(1);
  const ts = view.getFloat64(2, true);
  const contactArea = data.byteLength >= 18 ? view.getFloat64(10, true) : 0;
  return { type: signal, ts, touchCount, contactArea };
}

/**
 * Decodes a 10-byte scroll ArrayBuffer into a RawScrollEvent.
 *
 * Layout:
 *   [0]    uint8   — signal type (5=sc)
 *   [1]    uint8   — direction hint (0=unknown, 1=up, 2=down, 3=horizontal)
 *   [2..9] float64 — timestamp
 */
function decodeScroll(data: ArrayBuffer): RawScrollEvent {
  const view = new DataView(data);
  const dirRaw = view.getUint8(1);
  const ts = view.getFloat64(2, true);
  const direction: RawScrollEvent['direction'] =
    dirRaw === 1 ? 'up' :
    dirRaw === 2 ? 'down' :
    dirRaw === 3 ? 'horizontal' :
    'unknown';
  return { ts, direction };
}

// ─── Event buffer ────────────────────────────────────────────────────────────

export interface EventBufferSnapshot {
  keystroke: RawKeystrokeEvent[];
  pointer: RawPointerEvent[];
  touch: RawTouchEvent[];
  scroll: RawScrollEvent[];
  totalCount: number;
}

/**
 * Creates an event buffer that accumulates decoded raw events per signal type.
 *
 * Call `record()` for each EVENT_TAP message received from the main thread.
 * Call `drain()` at each pulse to get all buffered events and reset.
 */
export function createEventBuffer(): {
  record: (signal: string, data: ArrayBuffer) => void;
  drain: () => EventBufferSnapshot;
  count: () => number;
} {
  let keystrokeEvents: RawKeystrokeEvent[] = [];
  let pointerEvents: RawPointerEvent[] = [];
  let touchEvents: RawTouchEvent[] = [];
  let scrollEvents: RawScrollEvent[] = [];
  let totalCount = 0;

  return {
    record(signal: string, data: ArrayBuffer): void {
      // Hard cap: drop events beyond MAX_EVENTS_PER_WINDOW (Finding 18).
      if (totalCount >= MAX_EVENTS_PER_WINDOW) return;

      totalCount += 1;

      switch (signal) {
        case 'kd':
        case 'ku':
          keystrokeEvents.push(decodeKeystroke(data, signal));
          break;
        case 'pm':
        case 'pd':
        case 'pu':
        case 'cl':
          pointerEvents.push(decodePointer(data, signal));
          break;
        case 'ts':
        case 'te':
        case 'tm':
          touchEvents.push(decodeTouch(data, signal));
          break;
        case 'sc':
          scrollEvents.push(decodeScroll(data));
          break;
        // 'fb' (focus/blur) — not extracted yet, just counted
        default:
          break;
      }
    },

    drain(): EventBufferSnapshot {
      const snapshot: EventBufferSnapshot = {
        keystroke: keystrokeEvents,
        pointer: pointerEvents,
        touch: touchEvents,
        scroll: scrollEvents,
        totalCount,
      };
      // Reset buffers — raw events discarded per §5.4
      keystrokeEvents = [];
      pointerEvents = [];
      touchEvents = [];
      scrollEvents = [];
      totalCount = 0;
      return snapshot;
    },

    count(): number {
      return totalCount;
    },
  };
}
