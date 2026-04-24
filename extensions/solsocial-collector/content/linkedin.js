/**
 * LinkedIn content script — thin adapter over lib/scanner.js.
 *
 * SAFETY RULES (unchanged):
 *   • No fetch() / XMLHttpRequest to linkedin.com.
 *   • No clicks / keyboard events / scrolls initiated by us.
 *   • No DOM mutations.
 *   • Processing deferred via requestIdleCallback.
 *   • Console logs gated behind the `solsocial_debug` storage flag.
 */

const _s = SolSocialScanner.createScanner({
  platform: "linkedin",
  extractor: typeof LinkedInExtractor !== "undefined" ? LinkedInExtractor : null,
  getOwnHandle: () => {
    const node = document.querySelector(
      "a[data-control-name='identity_profile_photo'], .global-nav__me a[href*='/in/']"
    );
    const href = node?.getAttribute("href") || node?.closest("a")?.getAttribute("href");
    const m = href?.match(/\/in\/([^/?#]+)/);
    return m ? m[1] : null;
  },
});

// Initial scans — staggered so we catch slow-loading feed chunks.
setTimeout(() => _s.scheduleScan("initial-1"), 1500);
setTimeout(() => _s.scheduleScan("initial-2"), 4500);
setTimeout(() => _s.scheduleScan("initial-3"), 9000);

// Periodic own-post reconciler: on some pages our click-based detection misses
// posts published via mobile-responsive composer or dictation. Every 30s we
// re-scan and mark posts authored by us as own_post.
setInterval(() => _s.scheduleScan("own-post-poll"), 30_000);
