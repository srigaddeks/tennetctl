/**
 * Twitter / X content script — thin adapter over lib/scanner.js.
 */

const _s = SolSocialScanner.createScanner({
  platform: "x",
  extractor: typeof TwitterExtractor !== "undefined" ? TwitterExtractor : null,
  getOwnHandle: () => {
    const switcher = document.querySelector("[data-testid='SideNav_AccountSwitcher_Button']");
    const lbl = switcher?.getAttribute("aria-label") || "";
    const m1 = lbl.match(/@([A-Za-z0-9_]+)/);
    if (m1) return m1[1];
    const profileLink = document.querySelector("a[data-testid='AppTabBar_Profile_Link']");
    const href = profileLink?.getAttribute("href") || "";
    const m2 = href.match(/^\/([A-Za-z0-9_]+)$/);
    return m2 ? m2[1] : null;
  },
});

setTimeout(() => _s.scheduleScan("initial-1"), 1500);
setTimeout(() => _s.scheduleScan("initial-2"), 4500);
setTimeout(() => _s.scheduleScan("initial-3"), 9000);
setInterval(() => _s.scheduleScan("own-post-poll"), 30_000);
