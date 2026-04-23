/**
 * LinkedIn feed extractor — pure DOM functions, no Chrome APIs.
 * Anchors only on data-urn and ARIA attributes (stable across deploys).
 *
 * Export: { extractPosts, VERSION }
 */

const VERSION = "linkedin-v1";

/**
 * Extract all visible feed posts from a given root element (default: document).
 * Returns an array of raw capture objects (not yet sent to backend).
 */
function extractPosts(root = document) {
  const posts = [];

  // data-urn="urn:li:activity:..." is LinkedIn's stable post identity
  const containers = root.querySelectorAll("[data-urn^='urn:li:activity:']");

  for (const el of containers) {
    try {
      const urn = el.getAttribute("data-urn");
      if (!urn) continue;

      // Author: first profile link inside the post
      let authorHandle = null;
      let authorName = null;
      const authorLink = el.querySelector("a[href*='/in/']");
      if (authorLink) {
        const href = authorLink.getAttribute("href") || "";
        const match = href.match(/\/in\/([^/?#]+)/);
        if (match) authorHandle = match[1];
        // Name is in the link text or a child span
        authorName = authorLink.querySelector("span[aria-hidden='true']")?.textContent?.trim()
          || authorLink.textContent?.trim()
          || null;
      }

      // Text: first large text block (aria-hidden=false spans, not inside buttons)
      let textExcerpt = null;
      const textSpans = el.querySelectorAll("span[dir='ltr']");
      for (const span of textSpans) {
        if (span.closest("button")) continue;
        const t = span.textContent?.trim();
        if (t && t.length > 20) {
          textExcerpt = t.slice(0, 512);
          break;
        }
      }

      // Engagement counts via ARIA labels (accessibility contract — stable)
      const likeCount = _parseAriaCount(el, "button[aria-label*='reaction']") ??
                        _parseAriaCount(el, "button[aria-label*='like']");
      const replyCount = _parseAriaCount(el, "button[aria-label*='comment']");
      const repostCount = _parseAriaCount(el, "button[aria-label*='repost']");

      // Post URL
      const postLink = el.querySelector(`a[href*='/feed/update/${urn.replace(/:/g, '%3A')}/']`)
        || el.querySelector(`a[href*='${urn}']`);
      const url = postLink ? new URL(postLink.getAttribute("href"), location.origin).href : null;

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
        is_own: false,  // caller sets this after comparing to cached own-handle
        raw_attrs: {},
      });
    } catch (err) {
      // Skip broken posts silently — never crash the observer
    }
  }

  return posts;
}

/**
 * Extract engagement count from a button's aria-label.
 * e.g. "42 reactions" → 42
 */
function _parseAriaCount(root, selector) {
  const btn = root.querySelector(selector);
  if (!btn) return null;
  const label = btn.getAttribute("aria-label") || "";
  const match = label.match(/(\d[\d,]*)/);
  if (!match) return null;
  return parseInt(match[1].replace(/,/g, ""), 10) || null;
}

// Expose for content script (module export would be preferred but MV3
// content scripts support module syntax when using import maps, so we
// attach to globalThis as a fallback for simplicity)
globalThis.LinkedInExtractor = { extractPosts, VERSION };
