/**
 * webgl-fingerprint.ts — WebGL parameter dump collector.
 *
 * Runs on the MAIN THREAD. Collects 13 GL parameters, 4 shader
 * precision combos, renderer info, and WebGL2 availability.
 * Returns null on any failure or timeout.
 *
 * Zero npm dependencies. TypeScript strict mode.
 */

import type { WebGLFingerprint, ShaderPrecision } from '../runtime/wire-protocol.js';
import { FINGERPRINT_COLLECTOR_TIMEOUT_MS } from '../config/defaults.js';
import { sha256 } from './crypto-utils.js';

// ─── GL parameter constants to collect ────────────────────────────────────

const GL_PARAMS = [
  'MAX_TEXTURE_SIZE',
  'MAX_RENDERBUFFER_SIZE',
  'MAX_VIEWPORT_DIMS',
  'MAX_VERTEX_ATTRIBS',
  'MAX_VARYING_VECTORS',
  'MAX_VERTEX_UNIFORM_VECTORS',
  'MAX_FRAGMENT_UNIFORM_VECTORS',
  'MAX_COMBINED_TEXTURE_IMAGE_UNITS',
  'MAX_VERTEX_TEXTURE_IMAGE_UNITS',
  'MAX_TEXTURE_IMAGE_UNITS',
  'MAX_CUBE_MAP_TEXTURE_SIZE',
  'ALIASED_LINE_WIDTH_RANGE',
  'ALIASED_POINT_SIZE_RANGE',
] as const;

// ─── Shader precision combos ──────────────────────────────────────────────

type ShaderType = 'VERTEX_SHADER' | 'FRAGMENT_SHADER';
type PrecisionType = 'HIGH_FLOAT' | 'MEDIUM_FLOAT';

const SHADER_PRECISION_COMBOS: ReadonlyArray<readonly [ShaderType, PrecisionType]> = [
  ['VERTEX_SHADER', 'HIGH_FLOAT'],
  ['VERTEX_SHADER', 'MEDIUM_FLOAT'],
  ['FRAGMENT_SHADER', 'HIGH_FLOAT'],
  ['FRAGMENT_SHADER', 'MEDIUM_FLOAT'],
] as const;

// ─── Typed-array → plain array conversion ─────────────────────────────────

function toSerializable(value: unknown): number | number[] | null {
  if (value instanceof Float32Array || value instanceof Int32Array) {
    return Array.from(value);
  }
  if (typeof value === 'number') {
    return value;
  }
  return null;
}

// ─── WebGL context acquisition ────────────────────────────────────────────

function getWebGLContext(canvas: HTMLCanvasElement): WebGLRenderingContext | null {
  const ctx = canvas.getContext('webgl') ?? canvas.getContext('experimental-webgl');
  if (ctx !== null && ctx instanceof WebGLRenderingContext) {
    return ctx;
  }
  return null;
}

// ─── Core collection logic ────────────────────────────────────────────────

async function collect(): Promise<WebGLFingerprint | null> {
  const canvas = document.createElement('canvas');
  const gl = getWebGLContext(canvas);
  if (gl === null) {
    return null;
  }

  // Collect GL parameters
  const params: Record<string, number | number[] | null> = {};
  for (const name of GL_PARAMS) {
    const glEnum = gl[name] as GLenum | undefined;
    if (glEnum !== undefined) {
      params[name] = toSerializable(gl.getParameter(glEnum));
    } else {
      params[name] = null;
    }
  }

  // Collect shader precision formats
  const precisions: Record<string, ShaderPrecision | null> = {};
  for (const [shaderType, precisionType] of SHADER_PRECISION_COMBOS) {
    const key = `${shaderType}_${precisionType}`;
    const shaderEnum = gl[shaderType] as GLenum;
    const precisionEnum = gl[precisionType] as GLenum;
    const format = gl.getShaderPrecisionFormat(shaderEnum, precisionEnum);
    if (format !== null) {
      precisions[key] = {
        rangeMin: format.rangeMin,
        rangeMax: format.rangeMax,
        precision: format.precision,
      };
    } else {
      precisions[key] = null;
    }
  }

  // Renderer info via WEBGL_debug_renderer_info
  let renderer: string | null = null;
  let vendor: string | null = null;
  const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
  if (debugInfo !== null) {
    renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) as string | null;
    vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) as string | null;
  }

  // WebGL2 availability
  const webgl2Canvas = document.createElement('canvas');
  const webgl2Ctx = webgl2Canvas.getContext('webgl2');
  const webgl2 = webgl2Ctx !== null;
  if (webgl2Ctx) {
    const loseExt = webgl2Ctx.getExtension('WEBGL_lose_context');
    if (loseExt) loseExt.loseContext();
  }

  // Hash renderer and vendor (quasi-PII — raw GPU strings)
  const hashedRenderer = renderer !== null ? await sha256(renderer) : null;
  const hashedVendor = vendor !== null ? await sha256(vendor) : null;

  // Hash the full dump
  const hashInput = JSON.stringify({ params, precisions, renderer: hashedRenderer, vendor: hashedVendor, webgl2 });
  const hash = await sha256(hashInput);

  // Clean up GL context
  const loseCtx = gl.getExtension('WEBGL_lose_context');
  if (loseCtx !== null) {
    loseCtx.loseContext();
  }

  return { params, precisions, renderer: hashedRenderer, vendor: hashedVendor, webgl2, hash };
}

// ─── Public API ───────────────────────────────────────────────────────────

/**
 * Collect WebGL fingerprint data with timeout protection.
 * Returns null on any failure, missing WebGL support, or timeout.
 */
export async function collectWebGLFingerprint(): Promise<WebGLFingerprint | null> {
  try {
    const result = await Promise.race([
      collect(),
      new Promise<null>((resolve) => {
        setTimeout(() => resolve(null), FINGERPRINT_COLLECTOR_TIMEOUT_MS);
      }),
    ]);
    return result;
  } catch {
    return null;
  }
}
