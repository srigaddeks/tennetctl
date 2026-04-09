/**
 * gpu-render-fingerprint.ts --- GPU render task fingerprint collector.
 *
 * Runs on the MAIN THREAD (needs WebGL canvas). Executes 5 independent
 * GPU render tests on a 256x256 offscreen canvas and SHA-256 hashes
 * the readPixels output. Each test produces both an exact hash and a
 * quantized (4-bit) hash for cross-browser stability.
 *
 * Tests:
 *   1. gradient_triangle   -- colored gradient triangle via vertex/fragment shader
 *   2. alpha_blend          -- overlapping semi-transparent quads with blend modes
 *   3. float_precision      -- fract(sin(...)) pattern (GPU float precision varies)
 *   4. antialias_lines      -- diagonal lines at various angles
 *   5. texture_filter       -- checkerboard texture with LINEAR filtering
 *
 * Privacy: no user data is captured. Hashes are deterministic per
 * GPU + driver + OS combination and cannot be reversed.
 *
 * Zero npm dependencies. TypeScript strict mode.
 */

import type { GpuRenderFingerprint, GpuRenderTaskResult } from '../runtime/wire-protocol.js';
import { GPU_RENDER_TIMEOUT_MS } from '../config/defaults.js';

// ─── Constants ───────────────────────────────────────────────────────────────

const CANVAS_SIZE = 256;

// ─── SHA-256 helper ──────────────────────────────────────────────────────────

/** SHA-256 hash a Uint8Array, returning lowercase hex. */
async function sha256(data: Uint8Array): Promise<string> {
  const buffer = await crypto.subtle.digest('SHA-256', data.buffer as ArrayBuffer);
  return Array.from(new Uint8Array(buffer))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

/** SHA-256 hash a plain string, returning lowercase hex. */
async function sha256String(input: string): Promise<string> {
  const encoded = new TextEncoder().encode(input);
  return sha256(encoded);
}

// ─── Quantization helper ─────────────────────────────────────────────────────

/** Reduce each byte to 4-bit (value >> 4), pack into new Uint8Array. */
function quantizePixels(pixels: Uint8Array): Uint8Array {
  const quantized = new Uint8Array(pixels.length);
  for (let i = 0; i < pixels.length; i++) {
    quantized[i] = (pixels[i] as number) >> 4;
  }
  return quantized;
}

// ─── Timeout helper ──────────────────────────────────────────────────────────

function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T | null> {
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

// ─── WebGL helpers ───────────────────────────────────────────────────────────

function createShader(
  gl: WebGLRenderingContext,
  type: GLenum,
  source: string,
): WebGLShader | null {
  const shader = gl.createShader(type);
  if (shader === null) return null;
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    gl.deleteShader(shader);
    return null;
  }
  return shader;
}

function createProgram(
  gl: WebGLRenderingContext,
  vertexSource: string,
  fragmentSource: string,
): WebGLProgram | null {
  const vs = createShader(gl, gl.VERTEX_SHADER, vertexSource);
  if (vs === null) return null;
  const fs = createShader(gl, gl.FRAGMENT_SHADER, fragmentSource);
  if (fs === null) {
    gl.deleteShader(vs);
    return null;
  }
  const program = gl.createProgram();
  if (program === null) {
    gl.deleteShader(vs);
    gl.deleteShader(fs);
    return null;
  }
  gl.attachShader(program, vs);
  gl.attachShader(program, fs);
  gl.linkProgram(program);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    gl.deleteProgram(program);
    gl.deleteShader(vs);
    gl.deleteShader(fs);
    return null;
  }
  // Shaders can be deleted after linking -- GL retains them while program lives.
  gl.deleteShader(vs);
  gl.deleteShader(fs);
  return program;
}

/** Create a fullscreen quad VBO (two triangles covering clip space). */
function createFullscreenQuadBuffer(gl: WebGLRenderingContext): WebGLBuffer | null {
  const buffer = gl.createBuffer();
  if (buffer === null) return null;
  gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
  // prettier-ignore
  const vertices = new Float32Array([
    -1, -1,
     1, -1,
    -1,  1,
    -1,  1,
     1, -1,
     1,  1,
  ]);
  gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);
  return buffer;
}

/** Draw a fullscreen quad using the currently bound program. */
function drawFullscreenQuad(gl: WebGLRenderingContext, buffer: WebGLBuffer, posLoc: number): void {
  gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
  gl.enableVertexAttribArray(posLoc);
  gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);
  gl.drawArrays(gl.TRIANGLES, 0, 6);
  gl.disableVertexAttribArray(posLoc);
}

/** Read the full canvas pixels as RGBA Uint8Array. */
function readPixels(gl: WebGLRenderingContext): Uint8Array {
  const pixels = new Uint8Array(CANVAS_SIZE * CANVAS_SIZE * 4);
  gl.readPixels(0, 0, CANVAS_SIZE, CANVAS_SIZE, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
  return pixels;
}

/** Reset GL state between tests. */
function resetState(gl: WebGLRenderingContext): void {
  gl.disable(gl.BLEND);
  gl.disable(gl.DEPTH_TEST);
  gl.disable(gl.SCISSOR_TEST);
  gl.colorMask(true, true, true, true);
  gl.viewport(0, 0, CANVAS_SIZE, CANVAS_SIZE);
  gl.clearColor(0, 0, 0, 1);
  gl.clear(gl.COLOR_BUFFER_BIT);
}

// ─── Shader sources ──────────────────────────────────────────────────────────

// Passthrough vertex shader for fullscreen quad (fragment-only tests)
const PASSTHROUGH_VS = `
attribute vec2 a_position;
varying vec2 v_uv;
void main() {
  v_uv = a_position * 0.5 + 0.5;
  gl_Position = vec4(a_position, 0.0, 1.0);
}
`;

// Vertex shader for the gradient triangle test (with vertex colors)
const TRIANGLE_VS = `
attribute vec2 a_position;
attribute vec3 a_color;
varying vec3 v_color;
void main() {
  v_color = a_color;
  gl_Position = vec4(a_position, 0.0, 1.0);
}
`;

const TRIANGLE_FS = `
precision mediump float;
varying vec3 v_color;
void main() {
  gl_FragColor = vec4(v_color, 1.0);
}
`;

// Alpha-blend fragment shader -- solid color per quad, blended by GL blend modes
const SOLID_COLOR_VS = `
attribute vec2 a_position;
void main() {
  gl_Position = vec4(a_position, 0.0, 1.0);
}
`;

const SOLID_COLOR_FS = `
precision mediump float;
uniform vec4 u_color;
void main() {
  gl_FragColor = u_color;
}
`;

// Float precision test fragment shader
const FLOAT_PRECISION_FS = `
precision mediump float;
varying vec2 v_uv;
void main() {
  float val = fract(sin(gl_FragCoord.x * 12.9898 + gl_FragCoord.y * 78.233) * 43758.5453);
  gl_FragColor = vec4(val, val, val, 1.0);
}
`;

// Antialias lines vertex shader
const LINES_VS = `
attribute vec2 a_position;
void main() {
  gl_Position = vec4(a_position, 0.0, 1.0);
}
`;

const LINES_FS = `
precision mediump float;
void main() {
  gl_FragColor = vec4(1.0, 1.0, 1.0, 1.0);
}
`;

// Texture filter fragment shader
const TEXTURE_FILTER_FS = `
precision mediump float;
varying vec2 v_uv;
uniform sampler2D u_texture;
void main() {
  gl_FragColor = texture2D(u_texture, v_uv);
}
`;

// ─── Individual test runners ─────────────────────────────────────────────────

async function runGradientTriangle(gl: WebGLRenderingContext): Promise<GpuRenderTaskResult | null> {
  resetState(gl);

  const program = createProgram(gl, TRIANGLE_VS, TRIANGLE_FS);
  if (program === null) return null;

  gl.useProgram(program);

  const posLoc = gl.getAttribLocation(program, 'a_position');
  const colorLoc = gl.getAttribLocation(program, 'a_color');

  // Three vertices: red top, green bottom-left, blue bottom-right
  // prettier-ignore
  const vertexData = new Float32Array([
    // x,    y,     r,   g,   b
     0.0,  0.8,   1.0, 0.0, 0.0,
    -0.8, -0.8,   0.0, 1.0, 0.0,
     0.8, -0.8,   0.0, 0.0, 1.0,
  ]);

  const buffer = gl.createBuffer();
  if (buffer === null) { gl.deleteProgram(program); return null; }
  gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
  gl.bufferData(gl.ARRAY_BUFFER, vertexData, gl.STATIC_DRAW);

  const stride = 5 * 4; // 5 floats * 4 bytes
  gl.enableVertexAttribArray(posLoc);
  gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, stride, 0);
  gl.enableVertexAttribArray(colorLoc);
  gl.vertexAttribPointer(colorLoc, 3, gl.FLOAT, false, stride, 2 * 4);

  gl.drawArrays(gl.TRIANGLES, 0, 3);

  gl.disableVertexAttribArray(posLoc);
  gl.disableVertexAttribArray(colorLoc);

  const pixels = readPixels(gl);
  const exact_hash = await sha256(pixels);
  const quantized_hash = await sha256(quantizePixels(pixels));

  gl.deleteBuffer(buffer);
  gl.deleteProgram(program);

  return { test: 'gradient_triangle', exact_hash, quantized_hash };
}

async function runAlphaBlend(gl: WebGLRenderingContext): Promise<GpuRenderTaskResult | null> {
  resetState(gl);

  const program = createProgram(gl, SOLID_COLOR_VS, SOLID_COLOR_FS);
  if (program === null) return null;

  gl.useProgram(program);

  const posLoc = gl.getAttribLocation(program, 'a_position');
  const colorLoc = gl.getUniformLocation(program, 'u_color');

  // Define overlapping quad geometries
  const quads: Array<{ vertices: Float32Array; color: [number, number, number, number] }> = [
    {
      // Bottom-left quad -- semi-transparent red
      vertices: new Float32Array([-0.8, -0.8,  0.4, -0.8, -0.8, 0.4, -0.8, 0.4,  0.4, -0.8,  0.4, 0.4]),
      color: [1.0, 0.0, 0.0, 0.5],
    },
    {
      // Center quad -- semi-transparent green
      vertices: new Float32Array([-0.4, -0.4,  0.8, -0.4, -0.4, 0.8, -0.4, 0.8,  0.8, -0.4,  0.8, 0.8]),
      color: [0.0, 1.0, 0.0, 0.5],
    },
    {
      // Top-right quad -- semi-transparent blue
      vertices: new Float32Array([0.0, 0.0,  0.9, 0.0,  0.0, 0.9,  0.0, 0.9,  0.9, 0.0,  0.9, 0.9]),
      color: [0.0, 0.0, 1.0, 0.5],
    },
    {
      // Overlapping diagonal quad -- semi-transparent yellow
      vertices: new Float32Array([-0.6, -0.2,  0.6, -0.2, -0.6, 0.6, -0.6, 0.6,  0.6, -0.2,  0.6, 0.6]),
      color: [1.0, 1.0, 0.0, 0.3],
    },
  ];

  gl.enable(gl.BLEND);

  const buffer = gl.createBuffer();
  if (buffer === null) { gl.deleteProgram(program); return null; }

  // Draw with standard alpha blending first
  gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
  for (const q of quads.slice(0, 2)) {
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, q.vertices, gl.STATIC_DRAW);
    gl.enableVertexAttribArray(posLoc);
    gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);
    gl.uniform4f(colorLoc, q.color[0]!, q.color[1]!, q.color[2]!, q.color[3]!);
    gl.drawArrays(gl.TRIANGLES, 0, 6);
    gl.disableVertexAttribArray(posLoc);
  }

  // Switch to additive blending
  gl.blendFunc(gl.SRC_ALPHA, gl.ONE);
  for (const q of quads.slice(2)) {
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, q.vertices, gl.STATIC_DRAW);
    gl.enableVertexAttribArray(posLoc);
    gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);
    gl.uniform4f(colorLoc, q.color[0]!, q.color[1]!, q.color[2]!, q.color[3]!);
    gl.drawArrays(gl.TRIANGLES, 0, 6);
    gl.disableVertexAttribArray(posLoc);
  }

  gl.disable(gl.BLEND);

  const pixels = readPixels(gl);
  const exact_hash = await sha256(pixels);
  const quantized_hash = await sha256(quantizePixels(pixels));

  gl.deleteBuffer(buffer);
  gl.deleteProgram(program);

  return { test: 'alpha_blend', exact_hash, quantized_hash };
}

async function runFloatPrecision(gl: WebGLRenderingContext): Promise<GpuRenderTaskResult | null> {
  resetState(gl);

  const program = createProgram(gl, PASSTHROUGH_VS, FLOAT_PRECISION_FS);
  if (program === null) return null;

  gl.useProgram(program);

  const posLoc = gl.getAttribLocation(program, 'a_position');
  const buffer = createFullscreenQuadBuffer(gl);
  if (buffer === null) { gl.deleteProgram(program); return null; }

  drawFullscreenQuad(gl, buffer, posLoc);

  const pixels = readPixels(gl);
  const exact_hash = await sha256(pixels);
  const quantized_hash = await sha256(quantizePixels(pixels));

  gl.deleteBuffer(buffer);
  gl.deleteProgram(program);

  return { test: 'float_precision', exact_hash, quantized_hash };
}

async function runAntialiasLines(gl: WebGLRenderingContext): Promise<GpuRenderTaskResult | null> {
  resetState(gl);

  const program = createProgram(gl, LINES_VS, LINES_FS);
  if (program === null) return null;

  gl.useProgram(program);

  const posLoc = gl.getAttribLocation(program, 'a_position');

  // Generate diagonal lines at various angles (0, 15, 30, 45, 60, 75, 90 degrees)
  const lineVertices: number[] = [];
  const angles = [0, 15, 30, 45, 60, 75, 90, 120, 135, 150];
  const lineLength = 0.8;

  for (let i = 0; i < angles.length; i++) {
    const angle = ((angles[i] as number) * Math.PI) / 180;
    const cx = ((i % 5) / 5) * 1.6 - 0.64;
    const cy = i < 5 ? 0.3 : -0.3;
    const dx = Math.cos(angle) * lineLength * 0.5;
    const dy = Math.sin(angle) * lineLength * 0.5;

    lineVertices.push(cx - dx, cy - dy, cx + dx, cy + dy);
  }

  const buffer = gl.createBuffer();
  if (buffer === null) { gl.deleteProgram(program); return null; }
  gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(lineVertices), gl.STATIC_DRAW);

  gl.enableVertexAttribArray(posLoc);
  gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);
  gl.lineWidth(1.0);
  gl.drawArrays(gl.LINES, 0, lineVertices.length / 2);
  gl.disableVertexAttribArray(posLoc);

  const pixels = readPixels(gl);
  const exact_hash = await sha256(pixels);
  const quantized_hash = await sha256(quantizePixels(pixels));

  gl.deleteBuffer(buffer);
  gl.deleteProgram(program);

  return { test: 'antialias_lines', exact_hash, quantized_hash };
}

async function runTextureFilter(gl: WebGLRenderingContext): Promise<GpuRenderTaskResult | null> {
  resetState(gl);

  const program = createProgram(gl, PASSTHROUGH_VS, TEXTURE_FILTER_FS);
  if (program === null) return null;

  gl.useProgram(program);

  // Create a small 4x4 checkerboard texture
  const texSize = 4;
  const texData = new Uint8Array(texSize * texSize * 4);
  for (let y = 0; y < texSize; y++) {
    for (let x = 0; x < texSize; x++) {
      const idx = (y * texSize + x) * 4;
      const isWhite = (x + y) % 2 === 0;
      const val = isWhite ? 255 : 0;
      texData[idx] = val;       // R
      texData[idx + 1] = val;   // G
      texData[idx + 2] = val;   // B
      texData[idx + 3] = 255;   // A
    }
  }

  const texture = gl.createTexture();
  if (texture === null) { gl.deleteProgram(program); return null; }
  gl.bindTexture(gl.TEXTURE_2D, texture);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, texSize, texSize, 0, gl.RGBA, gl.UNSIGNED_BYTE, texData);

  // LINEAR filtering -- bilinear interpolation differs per GPU
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);

  const texLoc = gl.getUniformLocation(program, 'u_texture');
  gl.activeTexture(gl.TEXTURE0);
  gl.uniform1i(texLoc, 0);

  const posLoc = gl.getAttribLocation(program, 'a_position');
  const buffer = createFullscreenQuadBuffer(gl);
  if (buffer === null) {
    gl.deleteTexture(texture);
    gl.deleteProgram(program);
    return null;
  }

  drawFullscreenQuad(gl, buffer, posLoc);

  const pixels = readPixels(gl);
  const exact_hash = await sha256(pixels);
  const quantized_hash = await sha256(quantizePixels(pixels));

  gl.deleteTexture(texture);
  gl.deleteBuffer(buffer);
  gl.deleteProgram(program);

  return { test: 'texture_filter', exact_hash, quantized_hash };
}

// ─── Core collection logic ───────────────────────────────────────────────────

type TestRunner = (gl: WebGLRenderingContext) => Promise<GpuRenderTaskResult | null>;

const TEST_RUNNERS: readonly TestRunner[] = [
  runGradientTriangle,
  runAlphaBlend,
  runFloatPrecision,
  runAntialiasLines,
  runTextureFilter,
];

async function collect(): Promise<GpuRenderFingerprint | null> {
  const start = performance.now();

  const canvas = document.createElement('canvas');
  canvas.width = CANVAS_SIZE;
  canvas.height = CANVAS_SIZE;

  const gl = canvas.getContext('webgl', {
    preserveDrawingBuffer: true,
    antialias: true,
    alpha: false,
  });
  if (gl === null || !(gl instanceof WebGLRenderingContext)) {
    return null;
  }

  const tasks: GpuRenderTaskResult[] = [];

  for (const runner of TEST_RUNNERS) {
    const result = await runner(gl);
    if (result !== null) {
      tasks.push(result);
    }
  }

  // Clean up GL context
  const loseCtx = gl.getExtension('WEBGL_lose_context');
  if (loseCtx !== null) {
    loseCtx.loseContext();
  }

  if (tasks.length === 0) {
    return null;
  }

  // Combined hash: concatenate all exact hashes and hash again
  const combinedInput = tasks.map((t) => `${t.test}:${t.exact_hash}`).join('|');
  const combined_hash = await sha256String(combinedInput);

  const elapsed_ms = Math.round(performance.now() - start);

  return { tasks, combined_hash, elapsed_ms };
}

// ─── Public API ──────────────────────────────────────────────────────────────

/**
 * Collect a GPU render fingerprint by running 5 WebGL render tests.
 *
 * Returns `null` on any failure (unsupported browser, WebGL unavailable,
 * timeout, security restriction, etc.) --- never throws.
 */
export async function collectGpuRenderFingerprint(): Promise<GpuRenderFingerprint | null> {
  return withTimeout(collect(), GPU_RENDER_TIMEOUT_MS);
}
