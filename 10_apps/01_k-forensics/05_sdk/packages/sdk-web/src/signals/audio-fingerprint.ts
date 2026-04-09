/**
 * audio-fingerprint.ts — AudioContext fingerprint collector.
 *
 * Runs on the MAIN THREAD (requires OfflineAudioContext).
 * Pipeline: OscillatorNode(triangle, 1000Hz) → DynamicsCompressorNode → destination.
 * Hashes first 100 float samples with SHA-256.
 *
 * Spec: device_fingerprinting.md §TIER 2.
 *
 * Rules:
 *   • Zero npm dependencies — native browser APIs only.
 *   • No `any` types — TypeScript strict mode.
 *   • Returns null on any failure (unsupported browser, timeout, etc).
 */

import type { AudioFingerprint } from '../runtime/wire-protocol.js';
import { FINGERPRINT_COLLECTOR_TIMEOUT_MS } from '../config/defaults.js';

// ─── Vendor prefix handling ────────────────────────────────────────────────

/**
 * Resolve OfflineAudioContext constructor, including webkit-prefixed variant.
 */
function getOfflineAudioContextCtor(): typeof OfflineAudioContext | null {
  if (typeof OfflineAudioContext !== 'undefined') {
    return OfflineAudioContext;
  }
  // Safari ≤ 14 ships `webkitOfflineAudioContext` instead.
  const win = globalThis as unknown as Record<string, unknown>;
  if (typeof win['webkitOfflineAudioContext'] === 'function') {
    return win['webkitOfflineAudioContext'] as typeof OfflineAudioContext;
  }
  return null;
}

// ─── SHA-256 helper ────────────────────────────────────────────────────────

/**
 * Compute SHA-256 hex digest of a string using crypto.subtle.
 */
async function sha256(input: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(input);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  return Array.from(new Uint8Array(hashBuffer))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

// ─── Core render pipeline ──────────────────────────────────────────────────

/**
 * Render the audio fingerprint pipeline and return the hash + sample count.
 */
async function renderAudioFingerprint(): Promise<AudioFingerprint> {
  const Ctor = getOfflineAudioContextCtor();
  if (Ctor === null) {
    throw new Error('OfflineAudioContext not supported');
  }

  const context = new Ctor(1, 5000, 44100);

  // Oscillator: triangle wave at 1000 Hz.
  const oscillator = context.createOscillator();
  oscillator.type = 'triangle';
  oscillator.frequency.setValueAtTime(1000, context.currentTime);

  // Dynamics compressor with fixed parameters.
  const compressor = context.createDynamicsCompressor();
  compressor.threshold.setValueAtTime(-50, context.currentTime);
  compressor.knee.setValueAtTime(40, context.currentTime);
  compressor.ratio.setValueAtTime(12, context.currentTime);
  compressor.attack.setValueAtTime(0, context.currentTime);
  compressor.release.setValueAtTime(0.25, context.currentTime);

  // Pipeline: oscillator → compressor → destination.
  oscillator.connect(compressor);
  compressor.connect(context.destination);

  oscillator.start(0);

  const renderedBuffer = await context.startRendering();
  const channelData = renderedBuffer.getChannelData(0);

  // Hash first 100 float samples (toFixed(10) for cross-platform consistency).
  const sampleCount = Math.min(100, channelData.length);
  const parts: string[] = [];
  for (let i = 0; i < sampleCount; i++) {
    const sample = channelData[i] as number;
    parts.push(sample.toFixed(10));
  }

  const hash = await sha256(parts.join(','));

  return { hash, sample_count: sampleCount };
}

// ─── Public API ────────────────────────────────────────────────────────────

/**
 * Collect an AudioContext fingerprint.
 *
 * Returns `null` if the browser does not support OfflineAudioContext,
 * the render times out, or any other error occurs.
 */
export async function collectAudioFingerprint(): Promise<AudioFingerprint | null> {
  try {
    const result = await Promise.race([
      renderAudioFingerprint(),
      new Promise<null>((resolve) =>
        setTimeout(() => resolve(null), FINGERPRINT_COLLECTOR_TIMEOUT_MS),
      ),
    ]);
    return result;
  } catch {
    return null;
  }
}
