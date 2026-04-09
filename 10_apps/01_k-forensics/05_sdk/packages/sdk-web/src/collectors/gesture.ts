/**
 * Unified gesture feature extraction for pointer (mouse/trackpad) and touch events.
 *
 * Combines what were previously separate pointer and touch extractors into a single
 * "gesture" concept — on mobile these are gestures, and the same behavioral analysis
 * applies to mouse movement on desktop.
 *
 * Privacy: No absolute coordinates are ever used. Only velocities and derived features.
 */

// ─── Raw Event Interfaces ───────────────────────────────────────────────────

/** Raw pointer event (mouse/trackpad) posted from main thread. */
export interface RawPointerEvent {
  /** Event type: pointermove, pointerdown, pointerup, click */
  type: 'pm' | 'pd' | 'pu' | 'cl';
  /** Timestamp (ms, performance.now or Date.now) */
  ts: number;
  /** Velocity x (normalized, px/ms) */
  vx: number;
  /** Velocity y (normalized, px/ms) */
  vy: number;
}

/** Raw touch event posted from main thread. */
export interface RawTouchEvent {
  /** Event type: touchstart, touchend, touchmove */
  type: 'ts' | 'te' | 'tm';
  /** Timestamp (ms) */
  ts: number;
  /** Number of simultaneous touch points */
  touchCount: number;
  /** Normalized contact area (0-1) */
  contactArea: number;
}

// ─── Output Signal ──────────────────────────────────────────────────────────

/** Unified gesture signal combining pointer + touch behavioral features. */
export interface GestureSignal {
  available: boolean;

  /** Pointer/mouse section (null if no pointer events in window) */
  pointer: {
    velocity: { mean: number; max: number; p50: number; p95: number; std_dev: number | null };
    acceleration: { mean: number; std_dev: number | null; direction_changes_per_sec: number };
    clicks: { count: number; double_click_count: number; mean_dwell_ms: number; dwell_stdev: number | null };
    idle_fraction: number;
    ballistic_fraction: number;
    micro_correction_rate: number;
    mean_curvature: number;
    path_efficiency: number;
    angle_histogram: number[];
    segments: {
      count: number;
      duration_mean: number;
      distance_mean: number;
      efficiency_mean: number;
    };
    move_count: number;
    total_distance: number;
  } | null;

  /** Touch section (null if no touch events in window) */
  touch: {
    mean_contact_area: number;
    area_stdev: number | null;
    tap: { count: number; mean_dwell_ms: number; dwell_stdev: number | null; mean_flight_ms: number; flight_stdev: number | null };
    swipe: { count: number; duration_mean: number; duration_stdev: number | null };
    pinch_count: number;
    heatmap_zones: number[];
    dominant_hand_hint: 'left' | 'right' | 'unknown';
  } | null;
}

// ─── Math Helpers (zero dependencies) ───────────────────────────────────────

/** Round to 2 decimal places. */
function r2(v: number): number {
  return Math.round(v * 100) / 100;
}

function mean(arr: number[]): number {
  if (arr.length === 0) return 0;
  let sum = 0;
  for (let i = 0; i < arr.length; i++) sum += arr[i]!;
  return sum / arr.length;
}

/** Population standard deviation. Returns null for fewer than 2 values (Finding 4). */
function stdev(arr: number[]): number | null {
  if (arr.length < 2) return null;
  const m = mean(arr);
  let sumSq = 0;
  for (let i = 0; i < arr.length; i++) {
    const d = arr[i]! - m;
    sumSq += d * d;
  }
  return Math.sqrt(sumSq / arr.length);
}

/** Rounds stdev result, preserving null for insufficient samples. */
function r2StdDev(arr: number[]): number | null {
  const sd = stdev(arr);
  return sd !== null ? r2(sd) : null;
}

function percentile(sorted: number[], p: number): number {
  if (sorted.length === 0) return 0;
  const idx = p * (sorted.length - 1);
  const lo = Math.floor(idx);
  const hi = Math.ceil(idx);
  if (lo === hi) return sorted[lo]!;
  return sorted[lo]! + (sorted[hi]! - sorted[lo]!) * (idx - lo);
}

// ─── Pointer Segment Tracking ───────────────────────────────────────────────

interface PointerSegment {
  startTs: number;
  endTs: number;
  distance: number;
  /** Displacement derived from velocity integration (approximate). */
  displacementX: number;
  displacementY: number;
}

// ─── Pointer Feature Extraction ─────────────────────────────────────────────

function extractPointerFeatures(events: readonly RawPointerEvent[]): NonNullable<GestureSignal['pointer']> {
  const speeds: number[] = [];
  const accels: number[] = [];
  const angles: number[] = [];
  const clickDwells: number[] = [];

  let clickCount = 0;
  let dblClickCount = 0;
  let lastClickTs = 0;
  let dirChanges = 0;
  let prevVx = 0;
  let prevVy = 0;
  let prevSpeed = 0;
  let prevTs = 0;
  let idleTime = 0;
  let totalTime = 0;
  let moveCount = 0;
  let totalDist = 0;
  let pendingDownTs: number | null = null;

  // Displacement tracking via velocity integration
  let cumDx = 0;
  let cumDy = 0;

  // 8 compass bins: N, NE, E, SE, S, SW, W, NW
  const angleHist: number[] = [0, 0, 0, 0, 0, 0, 0, 0];

  // Segments: continuous motion separated by >100ms pause
  const segments: PointerSegment[] = [];
  let currentSegment: PointerSegment | null = null;

  for (const ev of events) {
    if (ev.type === 'pm') {
      const speed = Math.sqrt(ev.vx * ev.vx + ev.vy * ev.vy);
      speeds.push(speed);
      moveCount++;

      if (prevTs > 0) {
        const dt = ev.ts - prevTs;
        const segDist = speed * dt;
        totalDist += segDist;

        // Integrate velocity for displacement
        cumDx += ev.vx * dt;
        cumDy += ev.vy * dt;

        // Acceleration
        if (dt > 0) {
          accels.push(Math.abs(speed - prevSpeed) / dt * 1000);
        }

        // Direction analysis
        if (ev.vx !== 0 || ev.vy !== 0) {
          const angle = Math.atan2(ev.vy, ev.vx);
          angles.push(angle);

          // Map angle to 8 compass bins
          const deg = ((angle * 180 / Math.PI) + 360) % 360;
          const bin = Math.floor(((deg + 22.5) % 360) / 45);
          if (bin >= 0 && bin < 8) angleHist[bin] = (angleHist[bin] ?? 0) + 1;
        }

        // Direction change detection (>30 degrees)
        if (prevVx !== 0 || prevVy !== 0) {
          const prevAngle = Math.atan2(prevVy, prevVx);
          const currAngle = Math.atan2(ev.vy, ev.vx);
          let angleDiff = Math.abs(currAngle - prevAngle);
          if (angleDiff > Math.PI) angleDiff = 2 * Math.PI - angleDiff;
          if (angleDiff > Math.PI / 6) dirChanges++;
        }

        // Idle detection (gap > 2s)
        if (dt > 2000) {
          idleTime += dt;
        }

        // Segment boundary (>100ms pause starts new segment)
        if (dt > 100) {
          if (currentSegment !== null && currentSegment.distance > 0) {
            segments.push(currentSegment);
          }
          currentSegment = {
            startTs: ev.ts,
            endTs: ev.ts,
            distance: 0,
            displacementX: 0,
            displacementY: 0,
          };
        }

        // Accumulate into current segment
        if (currentSegment !== null) {
          currentSegment.distance += segDist;
          currentSegment.endTs = ev.ts;
          currentSegment.displacementX += ev.vx * dt;
          currentSegment.displacementY += ev.vy * dt;
        }

        totalTime += dt;
      } else {
        // First move event — start first segment
        currentSegment = {
          startTs: ev.ts,
          endTs: ev.ts,
          distance: 0,
          displacementX: 0,
          displacementY: 0,
        };
      }

      prevVx = ev.vx;
      prevVy = ev.vy;
      prevSpeed = speed;
      prevTs = ev.ts;

    } else if (ev.type === 'pd') {
      pendingDownTs = ev.ts;

    } else if (ev.type === 'pu') {
      if (pendingDownTs !== null) {
        clickDwells.push(ev.ts - pendingDownTs);
        pendingDownTs = null;
      }

    } else if (ev.type === 'cl') {
      clickCount++;
      if (lastClickTs > 0 && (ev.ts - lastClickTs) < 400) {
        dblClickCount++;
      }
      lastClickTs = ev.ts;
    }
  }

  // Close last segment
  if (currentSegment !== null && currentSegment.distance > 0) {
    segments.push(currentSegment);
  }

  // Ensure totalTime spans the full event window
  if (events.length > 1) {
    const firstEv = events[0];
    const lastEv = events[events.length - 1];
    if (firstEv !== undefined && lastEv !== undefined) {
      totalTime = Math.max(totalTime, lastEv.ts - firstEv.ts);
    }
  }

  // Curvature: average angle change normalized by PI
  let curvature = 0;
  if (angles.length > 1) {
    const angleChanges: number[] = [];
    for (let a = 1; a < angles.length; a++) {
      let ac = Math.abs(angles[a]! - angles[a - 1]!);
      if (ac > Math.PI) ac = 2 * Math.PI - ac;
      angleChanges.push(ac);
    }
    curvature = angleChanges.length > 0 ? r2(mean(angleChanges) / Math.PI) : 0;
  }

  // Path efficiency: displacement / total distance (from velocity integration)
  const displacement = Math.sqrt(cumDx * cumDx + cumDy * cumDy);
  const pathEfficiency = totalDist > 0 ? r2(displacement / totalDist) : 0;

  // Velocity percentiles
  const sortedSpeeds = speeds.slice().sort((a, b) => a - b);

  // Segment stats
  const segDurations = segments.map(s => s.endTs - s.startTs);
  const segDistances = segments.map(s => s.distance);
  const segEfficiencies = segments.map(s => {
    const d = Math.sqrt(s.displacementX * s.displacementX + s.displacementY * s.displacementY);
    return s.distance > 0 ? d / s.distance : 0;
  });

  // Normalize angle histogram
  const totalAngleEvents = angleHist.reduce((a, b) => a + b, 0);
  const normalizedAngleHist = totalAngleEvents > 0
    ? angleHist.map(v => r2(v / totalAngleEvents))
    : angleHist;

  return {
    velocity: {
      mean: speeds.length > 0 ? r2(mean(speeds)) : 0,
      max: speeds.length > 0 ? r2(Math.max(...speeds)) : 0,
      p50: r2(percentile(sortedSpeeds, 0.5)),
      p95: r2(percentile(sortedSpeeds, 0.95)),
      std_dev: r2StdDev(speeds),
    },
    acceleration: {
      mean: accels.length > 0 ? r2(mean(accels)) : 0,
      std_dev: r2StdDev(accels),
      direction_changes_per_sec: totalTime > 0 ? r2(dirChanges / (totalTime / 1000)) : 0,
    },
    clicks: {
      count: clickCount,
      double_click_count: dblClickCount,
      mean_dwell_ms: clickDwells.length > 0 ? r2(mean(clickDwells)) : 0,
      dwell_stdev: r2StdDev(clickDwells),
    },
    idle_fraction: totalTime > 0 ? r2(idleTime / totalTime) : 0,
    ballistic_fraction: speeds.length > 0
      ? r2(speeds.filter(v => v > 1.0).length / speeds.length)
      : 0,
    micro_correction_rate: moveCount > 0
      ? r2(speeds.filter(v => v > 0 && v < 0.05).length / moveCount)
      : 0,
    mean_curvature: curvature,
    path_efficiency: pathEfficiency,
    angle_histogram: normalizedAngleHist,
    segments: {
      count: segments.length,
      duration_mean: segDurations.length > 0 ? r2(mean(segDurations)) : 0,
      distance_mean: segDistances.length > 0 ? r2(mean(segDistances)) : 0,
      efficiency_mean: segEfficiencies.length > 0 ? r2(mean(segEfficiencies)) : 0,
    },
    move_count: moveCount,
    total_distance: r2(totalDist),
  };
}

// ─── Touch Feature Extraction ───────────────────────────────────────────────

function extractTouchFeatures(events: readonly RawTouchEvent[]): NonNullable<GestureSignal['touch']> {
  const areas: number[] = [];
  const tapDwells: number[] = [];
  const tapFlights: number[] = [];
  const swipeDurations: number[] = [];

  let tapCount = 0;
  let swipeCount = 0;
  let pinchCount = 0;
  let lastTapEnd = 0;
  let pendingStart: RawTouchEvent | null = null;

  for (const ev of events) {
    if (ev.contactArea > 0) {
      areas.push(ev.contactArea);
    }

    if (ev.type === 'ts') {
      pendingStart = ev;
      // Multi-touch = pinch gesture
      if (ev.touchCount > 1) pinchCount++;
      // Flight time from last tap end to this tap start
      if (lastTapEnd > 0) tapFlights.push(ev.ts - lastTapEnd);

    } else if (ev.type === 'te') {
      if (pendingStart !== null) {
        const dur = ev.ts - pendingStart.ts;
        if (dur < 300) {
          tapCount++;
          tapDwells.push(dur);
        } else {
          swipeCount++;
          swipeDurations.push(dur);
        }
      }
      lastTapEnd = ev.ts;
      pendingStart = null;
    }
    // 'tm' (touchmove) — area already collected above, no other action needed
  }

  // Heatmap: not possible from worker (no coordinates), fill with zeros
  const heatmapZones: number[] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];

  return {
    mean_contact_area: areas.length > 0 ? r2(mean(areas)) : 0,
    area_stdev: r2StdDev(areas),
    tap: {
      count: tapCount,
      mean_dwell_ms: tapDwells.length > 0 ? r2(mean(tapDwells)) : 0,
      dwell_stdev: r2StdDev(tapDwells),
      mean_flight_ms: tapFlights.length > 0 ? r2(mean(tapFlights)) : 0,
      flight_stdev: r2StdDev(tapFlights),
    },
    swipe: {
      count: swipeCount,
      duration_mean: swipeDurations.length > 0 ? r2(mean(swipeDurations)) : 0,
      duration_stdev: r2StdDev(swipeDurations),
    },
    pinch_count: pinchCount,
    heatmap_zones: heatmapZones,
    dominant_hand_hint: 'unknown',  // Needs heatmap data to infer
  };
}

// ─── Public API ─────────────────────────────────────────────────────────────

/**
 * Extract unified gesture features from raw pointer and touch events.
 *
 * Returns null if both arrays are empty (no gesture data in this window).
 * Returns a GestureSignal with pointer/touch sections populated only when
 * the corresponding event array has data.
 */
export function extractGesture(
  pointerEvents: readonly RawPointerEvent[],
  touchEvents: readonly RawTouchEvent[],
): GestureSignal | null {
  if (pointerEvents.length === 0 && touchEvents.length === 0) {
    return null;
  }

  return {
    available: true,
    pointer: pointerEvents.length > 0 ? extractPointerFeatures(pointerEvents) : null,
    touch: touchEvents.length > 0 ? extractTouchFeatures(touchEvents) : null,
  };
}
