/**
 * Canvas 2D fingerprint collector.
 *
 * Draws text (with specific fonts), emoji, a gradient rectangle, and an arc
 * onto an offscreen canvas, then SHA-256 hashes the resulting dataURL.
 *
 * Runs on the MAIN THREAD — requires DOM access for canvas creation.
 *
 * Privacy: no user data is captured. The hash is deterministic per
 * browser + GPU + OS combination and cannot be reversed.
 */

import type { CanvasFingerprint } from '../runtime/wire-protocol.js';
import { FINGERPRINT_COLLECTOR_TIMEOUT_MS } from '../config/defaults.js';

// ─── Helpers ──────────────────────────────────────────────────────────────────

/** SHA-256 hash a string, returning lowercase hex. */
async function sha256(input: string): Promise<string> {
  const encoded = new TextEncoder().encode(input);
  const buffer = await crypto.subtle.digest('SHA-256', encoded);
  return Array.from(new Uint8Array(buffer))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

/** Race a promise against a timeout. Returns `null` if the timeout fires first. */
function withTimeout<T>(
  promise: Promise<T>,
  ms: number,
): Promise<T | null> {
  return new Promise<T | null>((resolve) => {
    const timer = setTimeout(() => resolve(null), ms);
    promise
      .then((value) => {
        clearTimeout(timer);
        resolve(value);
      })
      .catch(() => {
        clearTimeout(timer);
        resolve(null);
      });
  });
}

// ─── Canvas drawing ───────────────────────────────────────────────────────────

const CANVAS_WIDTH = 300;
const CANVAS_HEIGHT = 150;

/** Render the deterministic fingerprint scene onto a 2D context. */
function drawScene(ctx: CanvasRenderingContext2D): void {
  // 1. Orange rectangle + blue text + green overlay text
  ctx.fillStyle = '#f60';
  ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

  ctx.font = '18px Arial, sans-serif';
  ctx.textBaseline = 'alphabetic';
  ctx.fillStyle = '#069';
  ctx.fillText('Cwm fjord vex quiz nymph', 2, 15);

  ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
  ctx.font = '18px Georgia, serif';
  ctx.fillText('Cwm fjord vex quiz nymph', 4, 45);

  // 2. Emoji string (house, lock, money bag)
  ctx.font = '20px Arial, sans-serif';
  ctx.fillStyle = '#000';
  ctx.fillText('\u{1F3E0}\u{1F512}\u{1F4B0}', 2, 75);

  // 3. Linear gradient red → green → blue rectangle
  const gradient = ctx.createLinearGradient(0, 80, CANVAS_WIDTH, 80);
  gradient.addColorStop(0, '#ff0000');
  gradient.addColorStop(0.5, '#00ff00');
  gradient.addColorStop(1, '#0000ff');
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 85, CANVAS_WIDTH, 30);

  // 4. Semi-transparent magenta arc
  ctx.beginPath();
  ctx.arc(CANVAS_WIDTH / 2, 130, 20, 0, Math.PI * 2);
  ctx.fillStyle = 'rgba(255, 0, 255, 0.5)';
  ctx.fill();
}

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Collect a canvas 2D fingerprint.
 *
 * Returns `null` on any failure (unsupported browser, timeout, security
 * restriction, etc.) — never throws.
 */
export async function collectCanvasFingerprint(): Promise<CanvasFingerprint | null> {
  return withTimeout(collectCanvasFingerprintInner(), FINGERPRINT_COLLECTOR_TIMEOUT_MS);
}

async function collectCanvasFingerprintInner(): Promise<CanvasFingerprint | null> {
  try {
    const canvas = document.createElement('canvas');
    canvas.width = CANVAS_WIDTH;
    canvas.height = CANVAS_HEIGHT;

    const ctx = canvas.getContext('2d');
    if (ctx === null) {
      return null;
    }

    drawScene(ctx);

    const dataURL = canvas.toDataURL('image/png');
    const hash = await sha256(dataURL);

    return { hash };
  } catch (_: unknown) {
    return null;
  }
}
