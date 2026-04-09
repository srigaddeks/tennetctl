/**
 * laplace-noise.ts — Differential privacy via Laplace mechanism.
 *
 * Adds calibrated Laplace noise to numeric values to provide
 * epsilon-differential privacy. Used to protect the zone transition
 * matrix from leaking password structure.
 *
 * Rules:
 *   • Zero npm dependencies.
 *   • No `any` types.
 *   • Deterministic test seeding not supported (crypto.getRandomValues only).
 */

/**
 * Generates a single Laplace-distributed random variable.
 *
 * Uses the inverse CDF method: L(mu, b) = mu - b * sign(u) * ln(1 - 2|u|)
 * where u is uniform on (-0.5, 0.5).
 *
 * @param scale  The Laplace scale parameter (b = sensitivity / epsilon).
 *               Higher scale = more noise = more privacy.
 */
function laplaceSample(scale: number): number {
  // Use crypto.getRandomValues for unbiased randomness
  const buf = new Uint32Array(1);
  crypto.getRandomValues(buf);
  // Map to (-0.5, 0.5), excluding exactly 0
  const u = (buf[0]! / 0x100000000) - 0.5;
  if (u === 0) return 0;
  return -scale * Math.sign(u) * Math.log(1 - 2 * Math.abs(u));
}

/**
 * Applies Laplace noise to a 2D matrix of counts.
 * Values are clamped to >= 0 and rounded to integers after noise addition.
 *
 * @param matrix  The raw count matrix (will NOT be mutated).
 * @param scale   Laplace scale parameter. Default: 2.0 (good for count queries with sensitivity=1).
 * @returns       New matrix with noise applied.
 */
export function addLaplaceNoise2D(
  matrix: readonly (readonly number[])[],
  scale = 2.0,
): number[][] {
  return matrix.map((row) =>
    row.map((count) => {
      const noisy = count + laplaceSample(scale);
      // Clamp to non-negative and round to integer
      return Math.max(0, Math.round(noisy));
    }),
  );
}
