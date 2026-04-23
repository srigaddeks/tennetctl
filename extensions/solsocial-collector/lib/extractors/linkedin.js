/**
 * LinkedIn feed extractor — multiple selector fallbacks for DOM resilience.
 */

const VERSION = "linkedin-v2";

function extractPosts(root = document) {
  const posts = [];

  // Strategy 1: data-urn (classic, most stable)
  let containers = Array.from(root.querySelectorAll("[data-urn^='urn:li:activity:']"));

  // Strategy 2: feed update containers (fallback if data-urn not present)
  if (containers.length === 0) {
    containers = Array.from(root.querySelectorAll(
      ".feed-shared-update-v2, " +
      "[data-id^='urn:li:activity:'], " +
      "div[class*='occludable-update']"
    ));
  }

  // Strategy 3: any article-like element with a LinkedIn activity link
  if (containers.length === 0) {
    const activityLinks = root.querySelectorAll("a[href*='/feed/update/urn:li:activity:']");
    const seen = new Set();
    for (const link of activityLinks) {
      const container = link.closest("div[class*='update'], div[class*='feed'], li, article") || link.parentElement?.parentElement;
      if (container && !seen.has(container)) {
        seen.add(container);
        containers.push(container);
      }
    }
  }

  console.log(`[SolSocial] LinkedIn extractor: found ${containers.length} containers (${VERSION})`);

  for (const el of containers) {
    try {
      // Get post ID from data-urn, data-id, or activity URL
      let urn = el.getAttribute("data-urn") || el.getAttribute("data-id");
      if (!urn) {
        const actLink = el.querySelector("a[href*='/feed/update/urn:li:activity:']");
        if (actLink) {
          const m = actLink.getAttribute("href").match(/(urn:li:activity:[^/?#&]+)/);
          if (m) urn = decodeURIComponent(m[1]);
        }
      }
      if (!urn || !urn.startsWith("urn:li:")) continue;

      // Author
      let authorHandle = null, authorName = null;
      const authorLink = el.querySelector("a[href*='/in/']");
      if (authorLink) {
        const href = authorLink.getAttribute("href") || "";
        const m = href.match(/\/in\/([^/?#]+)/);
        if (m) authorHandle = m[1];
        authorName = (
          authorLink.querySelector("span[aria-hidden='true']")?.textContent?.trim() ||
          authorLink.textContent?.trim() || ""
        ).slice(0, 100) || null;
      }

      // Text — try multiple approaches
      let textExcerpt = null;

      // Try span[dir=ltr] first
      for (const span of el.querySelectorAll("span[dir='ltr']")) {
        if (span.closest("button")) continue;
        const t = span.textContent?.trim();
        if (t && t.length > 20) { textExcerpt = t.slice(0, 512); break; }
      }
      // Fallback: any paragraph-like element with substantial text
      if (!textExcerpt) {
        for (const p of el.querySelectorAll("p, [class*='commentary'], [class*='body']")) {
          const t = p.textContent?.trim();
          if (t && t.length > 20) { textExcerpt = t.slice(0, 512); break; }
        }
      }

      // Engagement via ARIA
      const likeCount = _parseAriaCount(el, "button[aria-label*='reaction']") ??
                        _parseAriaCount(el, "button[aria-label*='like']");
      const replyCount = _parseAriaCount(el, "button[aria-label*='comment']");
      const repostCount = _parseAriaCount(el, "button[aria-label*='repost']");

      // URL
      const postLink = el.querySelector("a[href*='/feed/update/']") ||
                       el.querySelector(`a[href*='${urn}']`);
      const url = postLink
        ? new URL(postLink.getAttribute("href"), location.origin).href
        : null;

      posts.push({
        platform: "linkedin",
        type: "feed_post_seen",
        platform_post_id: urn,
        observed_at: new Date().toISOString(),
        extractor_version: VERSION,
        author_handle: authorHandle,
        author_name: authorName,
        text_excerpt: textExcerpt,
        url,
        like_count: likeCount,
        reply_count: replyCount,
        repost_count: repostCount,
        view_count: null,
        is_own: false,
        raw_attrs: {},
      });
    } catch (_) {}
  }

  return posts;
}

function _parseAriaCount(root, selector) {
  const btn = root.querySelector(selector);
  if (!btn) return null;
  const m = (btn.getAttribute("aria-label") || "").match(/(\d[\d,]*)/);
  return m ? parseInt(m[1].replace(/,/g, ""), 10) || null : null;
}

globalThis.LinkedInExtractor = { extractPosts, VERSION };
