/**
 * collect-all.ts — Orchestrates all device fingerprint collectors.
 *
 * Runs on the MAIN THREAD (most collectors need DOM/canvas/audio APIs).
 * Called once on init, result posted to the worker via DEVICE_FINGERPRINT message.
 *
 * Collection strategy:
 *   1. TIER 1 signals are collected synchronously (fast, no async APIs).
 *   2. TIER 2 + TIER 3 signals are collected concurrently with Promise.allSettled.
 *   3. A global timeout caps total collection time.
 *
 * Rules:
 *   • Never throws — always returns a DeviceFingerprint (with nulls for failures).
 *   • Zero npm dependencies.
 *   • No `any` types.
 */

import type { DeviceFingerprint } from '../runtime/wire-protocol.js';
import { FINGERPRINT_TIMEOUT_MS, FINGERPRINT_VERSION } from '../config/defaults.js';
import { sha256 } from './crypto-utils.js';

// TIER 1 — synchronous collectors
import {
  collectScreenFingerprint,
  collectPlatformFingerprint,
  collectNetworkFingerprint,
  collectMediaQueryFingerprint,
  collectFeatureFlags,
} from './environment-signals.js';
import {
  collectMathFingerprint,
  collectCssFingerprint,
} from './misc-fingerprints.js';

// TIER 2+3 — async collectors
import { collectCanvasFingerprint } from './canvas-fingerprint.js';
import { collectAudioFingerprint } from './audio-fingerprint.js';
import { collectWebGLFingerprint } from './webgl-fingerprint.js';
import { collectGpuRenderFingerprint } from './gpu-render-fingerprint.js';
import { collectFontFingerprint } from './font-fingerprint.js';
import { collectCpuBenchmark } from './cpu-benchmark.js';
import { collectAutomationFingerprint } from './automation-detect.js';
import {
  collectDateFingerprint,
  collectStorageFingerprint,
  collectSpeechFingerprint,
  collectBatteryFingerprint,
} from './misc-fingerprints.js';

import { collectLoadIndicators } from './load-indicators.js';

// ─── Helpers ─────────────────────────────────────────────────────────────────

/** Wraps a promise so it resolves to null on rejection. */
async function safe<T>(promise: Promise<T>): Promise<T | null> {
  try {
    return await promise;
  } catch {
    return null;
  }
}

/**
 * Salts a fingerprint hash with the current origin (Finding 13).
 * Prevents cross-site tracking via fingerprint correlation:
 * SHA-256(raw_hash + origin) means the same device gets different
 * fingerprint hashes on different sites.
 */
async function saltHash(hash: string | null | undefined, origin: string): Promise<string | null> {
  if (!hash) return hash ?? null;
  try {
    return await sha256(hash + origin);
  } catch {
    return hash;
  }
}

/**
 * Applies origin-based salting to all hash fields in the fingerprint.
 * Only modifies hash fields — numeric/boolean signals are unaffected.
 */
async function saltFingerprint(fp: DeviceFingerprint, origin: string): Promise<DeviceFingerprint> {
  const salted = { ...fp };

  // Salt TIER 2 hash-based fingerprints.
  if (salted.canvas) {
    salted.canvas = { ...salted.canvas, hash: (await saltHash(salted.canvas.hash, origin)) ?? '' };
  }
  if (salted.audio) {
    salted.audio = { ...salted.audio, hash: (await saltHash(salted.audio.hash, origin)) ?? '' };
  }
  if (salted.webgl) {
    salted.webgl = { ...salted.webgl, hash: (await saltHash(salted.webgl.hash, origin)) ?? '' };
  }
  if (salted.gpu_render) {
    salted.gpu_render = {
      ...salted.gpu_render,
      combined_hash: (await saltHash(salted.gpu_render.combined_hash, origin)) ?? '',
    };
  }
  if (salted.fonts) {
    salted.fonts = { ...salted.fonts, hash: (await saltHash(salted.fonts.hash, origin)) ?? '' };
  }
  if (salted.speech) {
    salted.speech = { ...salted.speech, hash: (await saltHash(salted.speech.hash, origin)) ?? '' };
  }

  return salted;
}

// ─── Public API ──────────────────────────────────────────────────────────────

export async function collectAllFingerprints(): Promise<DeviceFingerprint> {
  const startTime = performance.now();

  // ── TIER 1: synchronous (instant) ──────────────────────────────────────
  const screen = collectScreenFingerprint();
  const platform = collectPlatformFingerprint();
  const network = collectNetworkFingerprint();
  const media_queries = collectMediaQueryFingerprint();
  const features = collectFeatureFlags();
  const math = collectMathFingerprint();
  const css = collectCssFingerprint();

  // ── TIER 2+3: all async collectors run concurrently ────────────────────
  let canvas: DeviceFingerprint['canvas'] = null;
  let audio: DeviceFingerprint['audio'] = null;
  let webgl: DeviceFingerprint['webgl'] = null;
  let gpu_render: DeviceFingerprint['gpu_render'] = null;
  let fonts: DeviceFingerprint['fonts'] = null;
  let cpu: DeviceFingerprint['cpu'] = null;
  let storage: DeviceFingerprint['storage'] = null;
  let speech: DeviceFingerprint['speech'] = null;
  let battery: DeviceFingerprint['battery'] = null;
  let date_format: DeviceFingerprint['date_format'] = null;
  let automation: DeviceFingerprint['automation'] = null;
  let load_indicators: DeviceFingerprint['load_indicators'] = null;

  // Load indicators are fast — collect early
  try {
    load_indicators = await collectLoadIndicators();
  } catch {
    // Best-effort — null on failure
  }

  try {
    const asyncResults = await Promise.race([
      Promise.allSettled([
        safe(collectCanvasFingerprint()),        // 0
        safe(collectAudioFingerprint()),         // 1
        safe(collectWebGLFingerprint()),         // 2
        safe(collectGpuRenderFingerprint()),     // 3
        safe(collectFontFingerprint()),          // 4
        safe(collectCpuBenchmark()),             // 5
        safe(collectStorageFingerprint()),       // 6
        safe(collectSpeechFingerprint()),        // 7
        safe(collectBatteryFingerprint()),       // 8
        safe(collectDateFingerprint()),          // 9
        safe(collectAutomationFingerprint()),    // 10
      ]),
      new Promise<PromiseSettledResult<unknown>[]>((resolve) => {
        setTimeout(() => resolve([]), FINGERPRINT_TIMEOUT_MS);
      }),
    ]);

    if (asyncResults.length > 0) {
      const get = <T>(idx: number): T | null => {
        const r = asyncResults[idx];
        return r?.status === 'fulfilled' ? (r.value as T | null) : null;
      };

      canvas = get(0);
      audio = get(1);
      webgl = get(2);
      gpu_render = get(3);
      fonts = get(4);
      cpu = get(5);
      storage = get(6);
      speech = get(7);
      battery = get(8);
      date_format = get(9);
      automation = get(10);
    }
  } catch {
    // Global timeout or unexpected error — async signals remain null
  }

  const collectionTime = performance.now() - startTime;

  const rawFingerprint: DeviceFingerprint = {
    screen,
    platform,
    media_queries,
    features,
    math,
    date_format,
    css,
    canvas,
    audio,
    webgl,
    gpu_render,
    fonts,
    cpu,
    network,
    storage,
    speech,
    battery,
    automation,
    load_indicators,
    collected_at: Date.now(),
    collection_time_ms: Math.round(collectionTime),
    fingerprint_version: FINGERPRINT_VERSION,
  };

  // ── Cross-site fingerprint salting (Finding 13) ──────────────────────────
  // Mix location.origin into all hash-based fingerprint signals so the same
  // device produces different hashes on different sites.
  try {
    const origin = typeof location !== 'undefined' ? location.origin : '';
    if (origin) {
      return await saltFingerprint(rawFingerprint, origin);
    }
  } catch {
    // location unavailable (e.g. in worker scope) — return unsalted.
  }

  return rawFingerprint;
}
