/**
 * Twitter / X feed extractor — pure DOM functions, no Chrome APIs.
 * Anchors only on data-testid attributes (Twitter's own test IDs — stable).
 *
 * Export: { extractTweets, VERSION }
 */

const VERSION = "twitter-v1";

/**
 * Extract all visible tweets from the current page.
 */
function extractTweets(root = document) {
  const tweets = [];

  // data-testid="tweet" is Twitter's own test hook — very stable
  const articles = root.querySelectorAll("article[data-testid='tweet']");

  for (const el of articles) {
    try {
      // Tweet ID from the first status URL in the article
      const statusLink = el.querySelector("a[href*='/status/']");
      if (!statusLink) continue;
      const href = statusLink.getAttribute("href") || "";
      const idMatch = href.match(/\/status\/(\d+)/);
      if (!idMatch) continue;
      const tweetId = idMatch[1];

      // Author handle: same status link, e.g. /elonmusk/status/123
      const handleMatch = href.match(/^\/([^/]+)\/status\//);
      const authorHandle = handleMatch ? handleMatch[1] : null;

      // Author display name
      const nameEl = el.querySelector("[data-testid='User-Name'] span");
      const authorName = nameEl?.textContent?.trim() || null;

      // Tweet text
      const textEl = el.querySelector("[data-testid='tweetText']");
      const textExcerpt = textEl ? textEl.textContent?.trim().slice(0, 512) : null;

      // Engagement via aria-labels on action buttons
      const likeCount = _parseAriaCount(el, "[data-testid='like']");
      const replyCount = _parseAriaCount(el, "[data-testid='reply']");
      const repostCount = _parseAriaCount(el, "[data-testid='retweet']");
      const viewCount = _parseAriaCount(el, "a[aria-label*='view']") ??
                        _parseAriaCount(el, "[data-testid='app-text-transition-container']");

      const url = `https://x.com${href}`;

      tweets.push({
        platform: "x",
        type: "feed_post_seen",
        platform_post_id: tweetId,
        observed_at: new Date().toISOString(),
        extractor_version: VERSION,
        author_handle: authorHandle,
        author_name: authorName,
        text_excerpt: textExcerpt,
        url,
        like_count: likeCount,
        reply_count: replyCount,
        repost_count: repostCount,
        view_count: viewCount,
        is_own: false,  // caller sets after comparing to cached own handle
        raw_attrs: {},
      });
    } catch {
      // Skip silently
    }
  }

  return tweets;
}

function _parseAriaCount(root, selector) {
  const el = root.querySelector(selector);
  if (!el) return null;
  const label = el.getAttribute("aria-label") || el.textContent || "";
  const match = label.match(/(\d[\d,\.KkMm]*)/);
  if (!match) return null;
  const raw = match[1].toLowerCase();
  if (raw.endsWith("k")) return Math.round(parseFloat(raw) * 1000);
  if (raw.endsWith("m")) return Math.round(parseFloat(raw) * 1_000_000);
  return parseInt(raw.replace(/[,\.]/g, ""), 10) || null;
}

globalThis.TwitterExtractor = { extractTweets, VERSION };
