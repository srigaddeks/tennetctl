import type { FontFingerprint } from '../runtime/wire-protocol.js';
import {
  FONT_TEST_LIST,
  FINGERPRINT_COLLECTOR_TIMEOUT_MS,
} from '../config/defaults.js';
import { sha256 } from './crypto-utils.js';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const BASELINES = ['monospace', 'serif', 'sans-serif'] as const;
const TEST_STRING = 'mmmmmmmmmmlli';
const FONT_SIZE = '72px';

/** Creates an off-screen measurement span inside the given container. */
function createProbeSpan(
  container: HTMLDivElement,
  fontFamily: string,
): HTMLSpanElement {
  const span = document.createElement('span');
  span.style.fontSize = FONT_SIZE;
  span.style.fontFamily = fontFamily;
  span.style.visibility = 'hidden';
  span.style.position = 'absolute';
  span.style.whiteSpace = 'nowrap';
  span.textContent = TEST_STRING;
  container.appendChild(span);
  return span;
}

// ---------------------------------------------------------------------------
// Public collector
// ---------------------------------------------------------------------------

/**
 * Enumerates locally-installed fonts by comparing rendered widths against
 * three baseline generic families. Runs on the **main thread** (needs DOM).
 *
 * Returns `null` on timeout, missing DOM APIs, or any unexpected error.
 */
export async function collectFontFingerprint(): Promise<FontFingerprint | null> {
  const container = document.createElement('div');
  container.style.position = 'absolute';
  container.style.left = '-9999px';
  container.style.visibility = 'hidden';

  try {
    document.body.appendChild(container);

    return await new Promise<FontFingerprint | null>((resolve) => {
      const timer = setTimeout(() => {
        resolve(null);
      }, FINGERPRINT_COLLECTOR_TIMEOUT_MS);

      (async () => {
        try {
          // --- measure baseline widths ---
          const baselineWidths: Record<string, number> = {};
          for (const baseline of BASELINES) {
            const span = createProbeSpan(container, baseline);
            baselineWidths[baseline] = span.offsetWidth;
          }

          // --- test each font against each baseline ---
          const detected: string[] = [];

          for (const font of FONT_TEST_LIST) {
            let found = false;

            for (const baseline of BASELINES) {
              const span = createProbeSpan(
                container,
                `"${font}",${baseline}`,
              );
              if (span.offsetWidth !== baselineWidths[baseline]) {
                found = true;
                break;
              }
            }

            if (found) {
              detected.push(font);
            }
          }

          // --- sort, hash, return ---
          detected.sort();
          const hash = await sha256(detected.join(','));

          clearTimeout(timer);
          resolve({ count: detected.length, hash });
        } catch {
          clearTimeout(timer);
          resolve(null);
        }
      })();
    });
  } catch {
    return null;
  } finally {
    if (container.parentNode) {
      container.parentNode.removeChild(container);
    }
  }
}
