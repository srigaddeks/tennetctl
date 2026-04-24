/**
 * Shared scanner scaffolding — used by both LinkedIn and Twitter content scripts.
 *
 * Responsibilities:
 *   • Bounded seen-set (so we don't re-enqueue the same DOM node infinitely).
 *   • Per-scan cap to prevent /search result blowouts from flooding the queue.
 *   • Debounced + idle-scheduled scan runs.
 *   • MutationObserver with a cheap "meaningful change" guard.
 *   • SPA URL-change observer via pushState/replaceState/popstate.
 *   • Telemetry: total scans, captures emitted, version — retrievable via
 *     chrome.runtime.sendMessage({type:'scanner_stats'}) from the popup.
 *   • Console logs gated behind a debug flag stored in chrome.storage.local.
 *
 * This file runs in each content script's isolated world; no cross-tab state.
 */

const DEFAULTS = {
  SEEN_MAX: 10_000,          // cap on in-memory dedup set
  PER_SCAN_CAP: 100,          // max captures sent per single scan call
  DEBOUNCE_MS: 750,
  IDLE_TIMEOUT_MS: 1500,
  MIN_MUTATION_ADDED_NODES: 1,  // require ≥1 added node to re-scan on mutation
};

function createScanner({ platform, extractor, getOwnHandle }) {
  const seen = new Set();
  const stats = {
    version: extractor?.VERSION || "unknown",
    platform,
    scans: 0,
    captures_emitted: 0,
    last_scan_at: null,
    last_scan_count: 0,
    last_page_type: "unknown",
    zero_scan_streak: 0,
    debug: false,
  };

  // ── chrome.storage-backed debug flag ─────────────────────────────────────
  try {
    chrome.storage?.local?.get?.(["solsocial_debug"], (d) => {
      stats.debug = !!d?.solsocial_debug;
    });
    chrome.storage?.onChanged?.addListener?.((changes) => {
      if (changes.solsocial_debug) stats.debug = !!changes.solsocial_debug.newValue;
    });
  } catch (_) { /* not available in some contexts */ }

  function log(...args) { if (stats.debug) console.log("[SolSocial]", ...args); }
  function warn(...args) { console.warn("[SolSocial]", ...args); }

  function markSeen(id) {
    if (seen.size >= DEFAULTS.SEEN_MAX) {
      const half = Math.floor(DEFAULTS.SEEN_MAX / 2);
      let n = 0;
      for (const v of seen) { seen.delete(v); if (++n >= half) break; }
    }
    seen.add(id);
  }

  function filterFresh(captures) {
    const fresh = [];
    const ownHandle = getOwnHandle?.() || null;
    for (const c of captures) {
      if (!c?.platform_post_id) continue;
      if (seen.has(c.platform_post_id)) continue;
      markSeen(c.platform_post_id);
      if (ownHandle && c.author_handle &&
          String(c.author_handle).toLowerCase() === String(ownHandle).toLowerCase()) {
        c.is_own = true;
      }
      fresh.push(c);
      if (fresh.length >= DEFAULTS.PER_SCAN_CAP) break;
    }
    return fresh;
  }

  function enqueue(captures) {
    if (!captures.length) return;
    try {
      chrome.runtime.sendMessage({ type: "enqueue", captures }, (resp) => {
        if (chrome.runtime.lastError) {
          warn("sendMessage error:", chrome.runtime.lastError.message);
          return;
        }
        log(`enqueued ${captures.length}, queue=${resp?.queued ?? "?"}`);
      });
    } catch (err) {
      warn("enqueue threw:", err?.message || err);
    }
  }

  function scan(reason) {
    if (!extractor) return;
    stats.scans += 1;
    try {
      const pageType = extractor.detectPageType?.() || "unknown";
      stats.last_page_type = pageType;
      const all = extractor.scanAll(document);
      const fresh = filterFresh(all);
      stats.last_scan_at = Date.now();
      stats.last_scan_count = fresh.length;
      stats.captures_emitted += fresh.length;
      if (fresh.length === 0) {
        stats.zero_scan_streak += 1;
      } else {
        stats.zero_scan_streak = 0;
      }
      if (fresh.length) {
        const byType = fresh.reduce((a, c) => ((a[c.type] = (a[c.type] || 0) + 1), a), {});
        log(`[${reason}] ${fresh.length} fresh on ${pageType}:`, byType);
        enqueue(fresh);
      } else {
        log(`[${reason}] scan on ${pageType} → 0 fresh (streak=${stats.zero_scan_streak})`);
      }
    } catch (err) {
      warn("scan error:", err?.message || err, err?.stack);
    }
  }

  // ── Debounced idle scheduler ────────────────────────────────────────────
  let scanTimer = null;
  function scheduleScan(reason) {
    if (scanTimer) clearTimeout(scanTimer);
    scanTimer = setTimeout(() => {
      scanTimer = null;
      const run = () => scan(reason);
      if (typeof requestIdleCallback === "function") {
        requestIdleCallback(run, { timeout: DEFAULTS.IDLE_TIMEOUT_MS });
      } else {
        run();
      }
    }, DEFAULTS.DEBOUNCE_MS);
  }

  // ── MutationObserver with cheap meaningful-change guard ─────────────────
  const mo = new MutationObserver((records) => {
    let addedNodes = 0;
    for (const r of records) {
      addedNodes += r.addedNodes?.length || 0;
      if (addedNodes >= DEFAULTS.MIN_MUTATION_ADDED_NODES) break;
    }
    if (addedNodes >= DEFAULTS.MIN_MUTATION_ADDED_NODES) {
      scheduleScan("mutation");
    }
  });
  mo.observe(document.body, { childList: true, subtree: true });

  // ── SPA URL-change detection ────────────────────────────────────────────
  let lastUrl = location.href;
  (function patchHistory() {
    const fire = () => {
      if (location.href !== lastUrl) {
        lastUrl = location.href;
        seen.clear();   // new page = fresh local dedup window (backend still dedupes)
        scheduleScan("url-change");
        setTimeout(() => scheduleScan("url-change-late"), 2500);
      }
    };
    const push = history.pushState;
    history.pushState = function () { const r = push.apply(this, arguments); fire(); return r; };
    const rep = history.replaceState;
    history.replaceState = function () { const r = rep.apply(this, arguments); fire(); return r; };
    window.addEventListener("popstate", fire);
  })();

  // ── Stats responder for popup / SW ──────────────────────────────────────
  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg?.type === "scanner_stats") {
      sendResponse({ ok: true, stats: { ...stats } });
      return true;
    }
    if (msg?.type === "force_scan") {
      scheduleScan("force");
      sendResponse({ ok: true });
      return true;
    }
    return false;  // not handled
  });

  return { scan, scheduleScan, stats, log };
}

globalThis.SolSocialScanner = { createScanner, DEFAULTS };
