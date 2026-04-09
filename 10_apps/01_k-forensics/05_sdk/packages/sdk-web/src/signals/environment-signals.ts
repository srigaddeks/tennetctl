/**
 * environment-signals.ts
 *
 * Synchronous (TIER 1) fingerprint collectors for the K-Protect SDK.
 * Runs on the MAIN THREAD — all functions are synchronous and return null on error.
 *
 * Zero npm dependencies. TypeScript strict mode. No `any` types.
 */

import type {
  ScreenFingerprint,
  PlatformFingerprint,
  UserAgentData,
  NetworkFingerprint,
  MediaQueryFingerprint,
  FeatureFlags,
} from '../runtime/wire-protocol.js';

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

/** Safe matchMedia wrapper — returns null if the API is unavailable. */
function mqMatches(query: string): boolean | null {
  try {
    return typeof matchMedia === 'function' ? matchMedia(query).matches : null;
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// NavigatorUAData types (not in all TS libs)
// ---------------------------------------------------------------------------

interface NavigatorUABrand {
  readonly brand: string;
  readonly version: string;
}

interface NavigatorUADataSync {
  readonly brands: readonly NavigatorUABrand[];
  readonly mobile: boolean;
  readonly platform: string;
  getHighEntropyValues(hints: string[]): Promise<Record<string, unknown>>;
}

interface NavigatorWithUAData {
  readonly userAgentData?: NavigatorUADataSync;
}

// ---------------------------------------------------------------------------
// NetworkInformation type (Chrome / Edge only)
// ---------------------------------------------------------------------------

interface NetworkInformation {
  readonly effectiveType?: string;
  readonly downlink?: number;
  readonly rtt?: number;
  readonly saveData?: boolean;
}

interface NavigatorWithConnection {
  readonly connection?: NetworkInformation;
}

// ---------------------------------------------------------------------------
// 1. Screen fingerprint
// ---------------------------------------------------------------------------

export function collectScreenFingerprint(): ScreenFingerprint | null {
  try {
    const s = screen;
    return {
      width: s.width,
      height: s.height,
      avail_width: s.availWidth,
      avail_height: s.availHeight,
      color_depth: s.colorDepth,
      pixel_depth: s.pixelDepth,
      device_pixel_ratio: window.devicePixelRatio,
      orientation: s.orientation?.type ?? null,
      color_gamut_p3: mqMatches('(color-gamut: p3)') ?? false,
      hdr: mqMatches('(dynamic-range: high)') ?? false,
    };
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// 2. Platform fingerprint
// ---------------------------------------------------------------------------

export function collectPlatformFingerprint(): PlatformFingerprint | null {
  try {
    const nav = navigator;

    // userAgentData (Chromium-only API, not in all TS libs)
    let uaData: UserAgentData | null = null;
    const navUA = nav as unknown as NavigatorWithUAData;
    if (navUA.userAgentData) {
      const raw = navUA.userAgentData;
      uaData = {
        brands: raw.brands
          ? Array.from(raw.brands).map((b) => `${b.brand} ${b.version}`)
          : null,
        mobile: raw.mobile,
        platform: raw.platform || null,
        // Async high-entropy values — not available synchronously
        platform_version: null,
        architecture: null,
        model: null,
        bitness: null,
      };
    }

    return {
      hardware_concurrency: nav.hardwareConcurrency ?? null,
      device_memory_gb:
        (nav as unknown as { deviceMemory?: number }).deviceMemory ?? null,
      max_touch_points: nav.maxTouchPoints,
      platform: nav.platform,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      timezone_offset_min: new Date().getTimezoneOffset(),
      primary_language: nav.language || '',
      cookie_enabled: nav.cookieEnabled,
      pdf_viewer:
        (nav as unknown as { pdfViewerEnabled?: boolean }).pdfViewerEnabled ??
        null,
      vendor: nav.vendor ?? null,
      user_agent_data: uaData,
    };
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// 3. Network fingerprint
// ---------------------------------------------------------------------------

export function collectNetworkFingerprint(): NetworkFingerprint | null {
  try {
    const conn = (navigator as unknown as NavigatorWithConnection).connection;
    if (!conn) {
      return {
        effective_type: null,
        downlink_mbps: null,
        rtt_ms: null,
        save_data: null,
      };
    }
    return {
      effective_type: conn.effectiveType ?? null,
      downlink_mbps: conn.downlink ?? null,
      rtt_ms: conn.rtt ?? null,
      save_data: conn.saveData ?? null,
    };
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// 4. Media query fingerprint
// ---------------------------------------------------------------------------

export function collectMediaQueryFingerprint(): MediaQueryFingerprint | null {
  try {
    return {
      pointer_fine: mqMatches('(pointer: fine)'),
      hover_hover: mqMatches('(hover: hover)'),
      color_gamut_p3: mqMatches('(color-gamut: p3)'),
      dynamic_range_high: mqMatches('(dynamic-range: high)'),
      prefers_reduced_motion: mqMatches('(prefers-reduced-motion: reduce)'),
      prefers_color_scheme_dark: mqMatches('(prefers-color-scheme: dark)'),
    };
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// 5. Feature flags
// ---------------------------------------------------------------------------

export function collectFeatureFlags(): FeatureFlags | null {
  try {
    const win = globalThis as unknown as Record<string, unknown>;
    const nav = navigator;

    return {
      web_worker: typeof Worker !== 'undefined',
      service_worker: 'serviceWorker' in nav,
      web_gl: hasWebGL(1),
      web_gl2: hasWebGL(2),
      web_audio:
        typeof (win['AudioContext'] ?? win['webkitAudioContext']) === 'function',
      compression_stream: typeof win['CompressionStream'] === 'function',
      crypto_subtle: !!(crypto && crypto.subtle),
      intersection_observer: typeof win['IntersectionObserver'] === 'function',
      resize_observer: typeof win['ResizeObserver'] === 'function',
      pointer_events: typeof win['PointerEvent'] === 'function',
      touch_events: 'ontouchstart' in window || nav.maxTouchPoints > 0,
      gamepad: 'getGamepads' in nav,
      bluetooth: 'bluetooth' in nav,
      usb: 'usb' in nav,
      media_devices: 'mediaDevices' in nav,
      shared_array_buffer: typeof win['SharedArrayBuffer'] === 'function',
      wasm: typeof WebAssembly === 'object' && typeof WebAssembly.compile === 'function',
      webgpu: 'gpu' in nav,
    };
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------------------
// WebGL probe helper
// ---------------------------------------------------------------------------

function hasWebGL(version: 1 | 2): boolean {
  try {
    const canvas = document.createElement('canvas');
    const ctx =
      version === 2
        ? canvas.getContext('webgl2')
        : canvas.getContext('webgl') ?? canvas.getContext('experimental-webgl');
    const supported = ctx !== null;
    // Clean up the context to free GPU resources
    if (ctx && 'getExtension' in ctx) {
      (ctx as WebGLRenderingContext).getExtension('WEBGL_lose_context')?.loseContext();
    }
    return supported;
  } catch {
    return false;
  }
}
