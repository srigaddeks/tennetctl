/**
 * page-gate.ts
 *
 * Classifies the current URL path into a PageClass and tracks transitions.
 * Runs inside the Web Worker.
 *
 * Matching precedence (SDK_BEST_PRACTICES §9.1):
 *   1. opt_out_patterns  → 'opted_out'
 *   2. critical_actions  → 'critical_action'
 *   3. (default)         → 'normal'
 *
 * All methods return new immutable objects — no internal mutation after
 * construction (except via update()).
 */

import type {
  ResolvedConfig,
  PageClass,
  CriticalAction,
} from '../runtime/wire-protocol.js';

// ─── PageGate ─────────────────────────────────────────────────────────────────

/**
 * PageGate — maps URL paths to page classes and surfaces the matching
 * CriticalAction definition when applicable.
 *
 * Constructed once per session. `update()` is called on every SPA navigation.
 */
export class PageGate {
  private readonly config: ResolvedConfig;

  /** Last evaluated path. */
  private currentPath: string = '';
  /** Last evaluated page class. */
  private currentClass: PageClass = 'normal';
  /** Last matched CriticalAction, or null. */
  private currentAction: CriticalAction | null = null;

  constructor(config: ResolvedConfig) {
    this.config = config;
  }

  // ─── Public API ────────────────────────────────────────────────────────────

  /**
   * Classifies a URL path into a PageClass.
   *
   * Precedence:
   *   1. opt_out_patterns  (string: path.includes, RegExp: pattern.test)
   *   2. critical_actions  (RegExp: pattern.test)
   *   3. 'normal'
   *
   * @param path  URL pathname (no query params, no fragment).
   * @returns     The PageClass for this path.
   */
  evaluate(path: string): PageClass {
    // 1. Opt-out check.
    for (const pattern of this.config.page_gate.opt_out_patterns) {
      try {
        if (
          typeof pattern === 'string'
            ? path.includes(pattern)
            : pattern.test(path)
        ) {
          return 'opted_out';
        }
      } catch {
        // Malformed RegExp — skip silently.
      }
    }

    // 2. Critical-action check.
    for (const action of this.config.critical_actions.actions) {
      try {
        if (action.page.test(path)) {
          return 'critical_action';
        }
      } catch {
        // Malformed RegExp — skip silently.
      }
    }

    // 3. Default.
    return 'normal';
  }

  /**
   * Returns the CriticalAction definition whose `page` RegExp matches
   * the given path, or null if no match.
   *
   * @param path  URL pathname.
   */
  getCriticalActionForPath(path: string): CriticalAction | null {
    for (const action of this.config.critical_actions.actions) {
      try {
        if (action.page.test(path)) {
          // Return a shallow copy — callers must not mutate the original.
          return { ...action };
        }
      } catch {
        // Malformed RegExp — skip silently.
      }
    }
    return null;
  }

  /**
   * Returns the page class from the most recent `update()` call.
   * Returns 'normal' before any update.
   */
  getCurrentClass(): PageClass {
    return this.currentClass;
  }

  /**
   * Returns the URL path from the most recent `update()` call.
   * Returns '' before any update.
   */
  getCurrentPath(): string {
    return this.currentPath;
  }

  /**
   * Returns the CriticalAction matched on the most recent `update()` call,
   * or null when the current page class is not 'critical_action'.
   */
  getCurrentAction(): CriticalAction | null {
    return this.currentAction !== null ? { ...this.currentAction } : null;
  }

  /**
   * Evaluates a new path, updates internal state, and returns an immutable
   * result object describing the new classification and whether it changed.
   *
   * @param newPath  Incoming URL pathname.
   * @returns        New page class, matching action (or null), and a
   *                 `changed` flag set when the page class differs from the
   *                 previous classification.
   */
  update(newPath: string): {
    pageClass: PageClass;
    action: CriticalAction | null;
    changed: boolean;
  } {
    const previousClass = this.currentClass;

    const pageClass = this.evaluate(newPath);
    const action =
      pageClass === 'critical_action'
        ? this.getCriticalActionForPath(newPath)
        : null;

    // Immutably update internal state.
    this.currentPath = newPath;
    this.currentClass = pageClass;
    this.currentAction = action;

    return {
      pageClass,
      action: action !== null ? { ...action } : null,
      changed: pageClass !== previousClass,
    };
  }
}
