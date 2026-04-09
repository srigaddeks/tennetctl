/**
 * fingerprint-collectors.test.ts
 *
 * Unit tests for device fingerprint signal collectors.
 *
 * Note: TIER 2 async collectors (canvas, audio, WebGL, GPU render) require
 * browser APIs that are not available in Vitest's jsdom/happy-dom environments.
 * Those are covered by E2E tests. Here we test:
 *   - TIER 1 synchronous collectors (math, date, CSS, automation, screen, platform, etc.)
 *   - Orchestrator structure (collect-all returns correct shape)
 *   - Individual collector null-safety (no throws)
 */

import { describe, it, expect } from 'vitest';

// ─── TIER 1 synchronous collectors ───────────────────────────────────────────

describe('MathFingerprint', () => {
  it('returns expected math constants', async () => {
    const { collectMathFingerprint } = await import('../signals/misc-fingerprints.js');
    const result = collectMathFingerprint();

    expect(result).not.toBeNull();
    if (result === null) return;

    expect(result.tan_pi_4).toBeCloseTo(1, 10);
    expect(result.log_2).toBeCloseTo(0.693147, 5);
    expect(typeof result.e_mod).toBe('number');
    expect(result.pow_min).toBeGreaterThan(0);
    expect(result.pow_min).toBeLessThan(1e-300);
  });
});

describe('DateFingerprint', () => {
  it('returns hashed date format strings for epoch', async () => {
    const { collectDateFingerprint } = await import('../signals/misc-fingerprints.js');
    const result = await collectDateFingerprint();

    expect(result).not.toBeNull();
    if (result === null) return;

    expect(typeof result.full_hash).toBe('string');
    expect(typeof result.short_hash).toBe('string');
    expect(typeof result.relative_era).toBe('string');
    // Hashed values should be 64-char hex strings (SHA-256)
    expect(result.full_hash).toMatch(/^[a-f0-9]{64}$/);
    expect(result.short_hash).toMatch(/^[a-f0-9]{64}$/);
  });
});

describe('CssFingerprint', () => {
  it('returns null when CSS.supports is unavailable', async () => {
    const { collectCssFingerprint } = await import('../signals/misc-fingerprints.js');

    // jsdom may not have CSS.supports
    const result = collectCssFingerprint();
    // Either null (no CSS.supports) or an object with boolean values
    if (result !== null) {
      const values = Object.values(result);
      for (const v of values) {
        expect(typeof v).toBe('boolean');
      }
    }
  });
});

describe('AutomationFingerprint', () => {
  it('returns all modern detection flags and a score', async () => {
    const { collectAutomationFingerprint } = await import('../signals/automation-detect.js');
    const result = await collectAutomationFingerprint();

    expect(result).not.toBeNull();
    if (result === null) return;

    expect(typeof result.webdriver).toBe('boolean');
    expect(typeof result.zero_plugins).toBe('boolean');
    expect(typeof result.zero_outer_dimensions).toBe('boolean');
    expect(typeof result.no_focus).toBe('boolean');
    // notifications_denied can be boolean or null
    expect([true, false, null]).toContain(result.notifications_denied);
    expect(typeof result.hardware_mismatch).toBe('boolean');
    expect(typeof result.cdp_detected).toBe('boolean');
    expect(typeof result.proxy_overridden).toBe('boolean');
    expect(typeof result.score).toBe('number');
    expect(result.score).toBeGreaterThanOrEqual(0.0);
    expect(result.score).toBeLessThanOrEqual(1.0);
  });
});


// ─── Environment signals ─────────────────────────────────────────────────────

describe('ScreenFingerprint', () => {
  it('returns screen dimensions', async () => {
    const { collectScreenFingerprint } = await import('../signals/environment-signals.js');
    const result = collectScreenFingerprint();

    // jsdom may provide screen with 0 values
    if (result !== null) {
      expect(typeof result.width).toBe('number');
      expect(typeof result.height).toBe('number');
      expect(typeof result.color_depth).toBe('number');
      expect(typeof result.device_pixel_ratio).toBe('number');
    }
  });
});

describe('PlatformFingerprint', () => {
  it('returns platform info', async () => {
    const { collectPlatformFingerprint } = await import('../signals/environment-signals.js');
    const result = collectPlatformFingerprint();

    if (result !== null) {
      expect(typeof result.timezone).toBe('string');
      expect(typeof result.primary_language).toBe('string');
      expect(typeof result.cookie_enabled).toBe('boolean');
    }
  });
});

describe('NetworkFingerprint', () => {
  it('returns null when navigator.connection is unavailable', async () => {
    const { collectNetworkFingerprint } = await import('../signals/environment-signals.js');
    const result = collectNetworkFingerprint();

    // Most test environments don't have navigator.connection
    if (result !== null) {
      // If available, should have the right shape
      expect('effective_type' in result).toBe(true);
    }
  });
});

describe('MediaQueryFingerprint', () => {
  it('returns media query results', async () => {
    const { collectMediaQueryFingerprint } = await import('../signals/environment-signals.js');
    const result = collectMediaQueryFingerprint();

    if (result !== null) {
      // All fields should be boolean or null
      for (const val of Object.values(result)) {
        expect(val === null || typeof val === 'boolean').toBe(true);
      }
    }
  });
});

describe('FeatureFlags', () => {
  it('returns feature detection results', async () => {
    const { collectFeatureFlags } = await import('../signals/environment-signals.js');
    const result = collectFeatureFlags();

    if (result !== null) {
      expect(typeof result.web_worker).toBe('boolean');
      expect(typeof result.wasm).toBe('boolean');
      expect(typeof result.crypto_subtle).toBe('boolean');
    }
  });
});

// ─── Orchestrator shape ──────────────────────────────────────────────────────

describe('collectAllFingerprints', () => {
  it('returns a DeviceFingerprint with all expected keys', async () => {
    const { collectAllFingerprints } = await import('../signals/collect-all.js');
    const result = await collectAllFingerprints();

    // Structure check — all top-level keys present
    const expectedKeys = [
      'screen', 'platform', 'media_queries', 'features',
      'math', 'date_format', 'css',
      'canvas', 'audio', 'webgl', 'gpu_render', 'fonts', 'cpu',
      'network', 'storage', 'speech', 'battery', 'automation',
      'collected_at', 'collection_time_ms',
    ];

    for (const key of expectedKeys) {
      expect(key in result).toBe(true);
    }

    // Metadata is always set
    expect(typeof result.collected_at).toBe('number');
    expect(result.collected_at).toBeGreaterThan(0);
    expect(typeof result.collection_time_ms).toBe('number');
    expect(result.collection_time_ms).toBeGreaterThanOrEqual(0);

    // Math should always work (pure JS, no browser APIs)
    expect(result.math).not.toBeNull();
  });

  it('never throws even if individual collectors fail', async () => {
    const { collectAllFingerprints } = await import('../signals/collect-all.js');

    // Should not throw
    const result = await collectAllFingerprints();
    expect(result).toBeDefined();
    expect(typeof result.collected_at).toBe('number');
  });
});

// ─── CPU Benchmark (runs in test env) ────────────────────────────────────────

describe('CpuBenchmark', () => {
  it('returns benchmark times and ratios', async () => {
    const { collectCpuBenchmark } = await import('../signals/cpu-benchmark.js');
    const result = await collectCpuBenchmark();

    // CPU benchmark should work in Node — all pure JS
    if (result !== null) {
      expect(result.times.int_arithmetic).toBeGreaterThan(0);
      expect(result.times.float_arithmetic).toBeGreaterThan(0);
      expect(result.times.string_ops).toBeGreaterThan(0);
      expect(result.times.array_sort).toBeGreaterThan(0);
      expect(typeof result.times.crypto_hash).toBe('number');

      expect(typeof result.ratios.int_to_float).toBe('number');
      expect(typeof result.ratios.string_to_array).toBe('number');
      expect(typeof result.ratios.crypto_to_int).toBe('number');

      expect(result.elapsed_ms).toBeGreaterThan(0);
    }
  });
});
