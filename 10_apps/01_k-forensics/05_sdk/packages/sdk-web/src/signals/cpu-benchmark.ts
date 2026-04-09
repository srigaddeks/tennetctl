/**
 * CPU micro-benchmark fingerprint collector.
 *
 * Runs five deterministic micro-benchmarks on the main thread and returns
 * raw times plus cross-benchmark ratios (ratios are more stable across
 * varying system load than raw times).
 *
 * Designed to run inside `requestIdleCallback` so it yields to higher-
 * priority work. Total execution target: ~200 ms.
 */

import type { CpuBenchmark } from '../runtime/wire-protocol.js';
import { CPU_BENCHMARK_TIMEOUT_MS } from '../config/defaults.js';

/* ------------------------------------------------------------------ */
/*  Anti-DCE sink — written but never read by external code.          */
/* ------------------------------------------------------------------ */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
let _sink: unknown;

/* ------------------------------------------------------------------ */
/*  Individual benchmarks                                             */
/* ------------------------------------------------------------------ */

function benchIntArithmetic(): number {
  const t0 = performance.now();
  let a = 1;
  let b = 2;
  for (let i = 0; i < 100_000; i++) {
    a = (a * 7 + 13) | 0;
    b = (b ^ a) | 0;
  }
  _sink = b;
  return performance.now() - t0;
}

function benchFloatArithmetic(): number {
  const t0 = performance.now();
  let a = 1.5;
  let b = 2.5;
  for (let i = 0; i < 100_000; i++) {
    a = Math.sin(a) * Math.cos(b);
    b = Math.sqrt(Math.abs(a * b + 0.001));
  }
  _sink = b;
  return performance.now() - t0;
}

function benchStringOps(): number {
  const t0 = performance.now();
  let str = '';
  let parts: string[] = [];
  for (let i = 0; i < 10_000; i++) {
    str += String.fromCharCode(65 + (i % 26));
    if (i % 100 === 99) {
      parts = str.split('');
      str = parts.slice(0, 50).join('');
    }
  }
  _sink = parts.length;
  return performance.now() - t0;
}

function benchArraySort(): number {
  const LCG_A = 1664525;
  const LCG_C = 1013904223;
  const LCG_M = 0x100000000; // 2^32

  // Seed the array with deterministic LCG values
  let seed = 42;
  const arr = new Float64Array(10_000);
  for (let i = 0; i < arr.length; i++) {
    seed = (LCG_A * seed + LCG_C) % LCG_M;
    arr[i] = seed / LCG_M;
  }

  // Float64Array.prototype.sort is in-place; re-shuffle between sorts
  const t0 = performance.now();
  for (let round = 0; round < 5; round++) {
    // Re-shuffle with LCG (skip on first round — already random)
    if (round > 0) {
      for (let i = arr.length - 1; i > 0; i--) {
        seed = (LCG_A * seed + LCG_C) % LCG_M;
        const j = seed % (i + 1);
        const tmp = arr[i] as number;
        arr[i] = arr[j] as number;
        arr[j] = tmp;
      }
    }
    arr.sort();
  }
  _sink = arr[0];
  return performance.now() - t0;
}

async function benchCryptoHash(): Promise<number> {
  const data = new TextEncoder().encode('A'.repeat(1024));
  const t0 = performance.now();
  let lastHash: ArrayBuffer | undefined;
  for (let i = 0; i < 100; i++) {
    lastHash = await crypto.subtle.digest('SHA-256', data);
  }
  _sink = lastHash;
  return performance.now() - t0;
}

/* ------------------------------------------------------------------ */
/*  Public collector                                                   */
/* ------------------------------------------------------------------ */

export async function collectCpuBenchmark(): Promise<CpuBenchmark | null> {
  try {
    const result = await Promise.race<CpuBenchmark | null>([
      runBenchmarks(),
      new Promise<null>((resolve) =>
        setTimeout(() => resolve(null), CPU_BENCHMARK_TIMEOUT_MS),
      ),
    ]);
    return result;
  } catch {
    return null;
  }
}

async function runBenchmarks(): Promise<CpuBenchmark> {
  const overallStart = performance.now();

  const intTime = benchIntArithmetic();
  await new Promise<void>((r) => setTimeout(r, 0));
  const floatTime = benchFloatArithmetic();
  await new Promise<void>((r) => setTimeout(r, 0));
  const stringTime = benchStringOps();
  await new Promise<void>((r) => setTimeout(r, 0));
  const arrayTime = benchArraySort();
  await new Promise<void>((r) => setTimeout(r, 0));
  const cryptoTime = await benchCryptoHash();

  const elapsed = performance.now() - overallStart;

  return {
    times: {
      int_arithmetic: intTime,
      float_arithmetic: floatTime,
      string_ops: stringTime,
      array_sort: arrayTime,
      crypto_hash: cryptoTime,
    },
    ratios: {
      int_to_float: floatTime === 0 ? 0 : intTime / floatTime,
      string_to_array: arrayTime === 0 ? 0 : stringTime / arrayTime,
      crypto_to_int: intTime === 0 ? 0 : cryptoTime / intTime,
    },
    elapsed_ms: elapsed,
  };
}
