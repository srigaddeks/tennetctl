/**
 * load-indicators.ts — Collects performance load state at fingerprint time.
 *
 * Measures FPS, event loop latency, memory usage, and visibility state.
 * All measurements are best-effort — individual failures return null fields.
 *
 * Runs on the MAIN THREAD. Total wall-clock time: ~600ms worst case
 * (500ms FPS timeout + ~50ms latency samples).
 */

import type { LoadIndicators } from '../runtime/wire-protocol.js';

// ─── FPS measurement ────────────────────────────────────────────────────────

const FPS_FRAME_COUNT = 10;
const FPS_TIMEOUT_MS = 500;

/**
 * Measures average FPS over 10 rAF frames.
 * Returns null if rAF is unavailable or measurement times out.
 */
function measureFps(): Promise<number | null> {
  if (typeof requestAnimationFrame !== 'function') {
    return Promise.resolve(null);
  }

  return new Promise<number | null>((resolve) => {
    let frameCount = 0;
    let startTime = 0;
    let settled = false;

    const timeout = setTimeout(() => {
      if (!settled) {
        settled = true;
        resolve(null);
      }
    }, FPS_TIMEOUT_MS);

    function onFrame(timestamp: number): void {
      if (settled) return;

      if (frameCount === 0) {
        startTime = timestamp;
      }

      frameCount++;

      if (frameCount > FPS_FRAME_COUNT) {
        settled = true;
        clearTimeout(timeout);
        const elapsed = timestamp - startTime;
        const fps = elapsed > 0 ? (FPS_FRAME_COUNT / elapsed) * 1000 : null;
        resolve(fps !== null ? Math.round(fps * 10) / 10 : null);
        return;
      }

      requestAnimationFrame(onFrame);
    }

    requestAnimationFrame(onFrame);
  });
}

// ─── Event loop latency ─────────────────────────────────────────────────────

const LATENCY_SAMPLES = 5;

/**
 * Measures event loop latency by scheduling setTimeout(0) and measuring
 * actual delay. Averages over 5 samples.
 */
function measureEventLoopLatency(): Promise<number | null> {
  return new Promise<number | null>((resolve) => {
    const samples: number[] = [];

    function takeSample(): void {
      const before = performance.now();
      setTimeout(() => {
        const delay = performance.now() - before;
        samples.push(delay);

        if (samples.length < LATENCY_SAMPLES) {
          takeSample();
        } else {
          const sum = samples.reduce((a, b) => a + b, 0);
          resolve(Math.round((sum / samples.length) * 100) / 100);
        }
      }, 0);
    }

    takeSample();
  });
}

// ─── Memory usage ───────────────────────────────────────────────────────────

interface ChromeMemoryInfo {
  usedJSHeapSize: number;
  jsHeapSizeLimit: number;
  totalJSHeapSize: number;
}

function hasMemoryInfo(
  perf: unknown,
): perf is { memory: ChromeMemoryInfo } {
  if (typeof perf !== 'object' || perf === null) return false;
  const mem = (perf as Record<string, unknown>)['memory'];
  if (typeof mem !== 'object' || mem === null) return false;
  const m = mem as Record<string, unknown>;
  return (
    typeof m['usedJSHeapSize'] === 'number' &&
    typeof m['jsHeapSizeLimit'] === 'number'
  );
}

// ─── Public API ─────────────────────────────────────────────────────────────

/**
 * Collects performance load indicators.
 * Never throws — individual failures result in null fields.
 */
export async function collectLoadIndicators(): Promise<LoadIndicators> {
  const [estimated_fps, event_loop_latency_ms] = await Promise.all([
    measureFps().catch(() => null),
    measureEventLoopLatency().catch(() => null),
  ]);

  let memory_used_mb: number | null = null;
  let memory_limit_mb: number | null = null;

  if (hasMemoryInfo(performance)) {
    const BYTES_PER_MB = 1024 * 1024;
    memory_used_mb =
      Math.round((performance.memory.usedJSHeapSize / BYTES_PER_MB) * 100) /
      100;
    memory_limit_mb =
      Math.round((performance.memory.jsHeapSizeLimit / BYTES_PER_MB) * 100) /
      100;
  }

  return {
    estimated_fps,
    event_loop_latency_ms,
    memory_used_mb,
    memory_limit_mb,
    document_was_hidden: document.hidden,
  };
}
