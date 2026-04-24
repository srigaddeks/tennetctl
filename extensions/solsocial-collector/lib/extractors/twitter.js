/**
 * Twitter / X extractor — comprehensive, DOM-only.
 *
 * CRITICAL CONSTRAINTS (same as LinkedIn extractor):
 *   • Read-only: no clicks, no hovers, no scrolls initiated by us.
 *   • DOM-only: we never fetch() to twitter.com / x.com.
 *   • Robust: selectors prefer stable data-testid; text falls back to span trees.
 *   • Deterministic IDs: every capture has a stable platform_post_id.
 */

const VERSION = "twitter-v3";

// ── Utilities ───────────────────────────────────────────────────────────────

function _text(el, max = 512) {
  if (!el) return null;
  const t = el.textContent?.replace(/\s+/g, " ").trim();
  if (!t) return null;
  return t.slice(0, max);
}

function _parseCount(str) {
  if (!str) return null;
  const m = String(str).replace(/,/g, "").match(/(\d+(?:\.\d+)?)([KMB])?/i);
  if (!m) return null;
  const n = parseFloat(m[1]);
  const suf = (m[2] || "").toUpperCase();
  if (suf === "K") return Math.round(n * 1_000);
  if (suf === "M") return Math.round(n * 1_000_000);
  if (suf === "B") return Math.round(n * 1_000_000_000);
  return Math.round(n);
}

function _ariaCount(root, selector) {
  const el = root?.querySelector?.(selector);
  if (!el) return null;
  return _parseCount(el.getAttribute("aria-label") || el.textContent);
}

function _absUrl(href) {
  if (!href) return null;
  try { return new URL(href, location.origin).href; } catch { return null; }
}

function _linksIn(root) {
  if (!root) return [];
  const out = [];
  const seen = new Set();
  for (const a of root.querySelectorAll("a[href]")) {
    const href = a.getAttribute("href") || "";
    if (!href || href.startsWith("javascript:") || href === "#") continue;
    const abs = _absUrl(href);
    if (!abs || seen.has(abs)) continue;
    seen.add(abs);
    const isProfile = /^\/[A-Za-z0-9_]+(\/|$)/.test(href) && !href.includes("/status/");
    const isStatus  = /\/status\/\d+/.test(href);
    const isHashtag = /\/hashtag\//.test(href);
    const isExternal= !abs.startsWith(location.origin);
    out.push({
      url: abs,
      text: _text(a, 160) || null,
      kind: isStatus ? "status" : isProfile ? "profile" : isHashtag ? "hashtag" : isExternal ? "external" : "internal",
    });
    if (out.length >= 20) break;
  }
  return out;
}

function _hashtagsIn(text) {
  if (!text) return [];
  return Array.from(new Set((text.match(/#[A-Za-z0-9_]+/g) || []).map(h => h.slice(1))));
}

function _mentionsIn(text) {
  if (!text) return [];
  return Array.from(new Set((text.match(/@[A-Za-z0-9_]+/g) || []).map(m => m.slice(1))));
}

function _detectOwnHandle() {
  const link = document.querySelector("a[data-testid='AppTabBar_Profile_Link'], a[aria-label='Profile']");
  const href = link?.getAttribute("href") || "";
  const m = href.match(/^\/([^/]+)\/?$/);
  return m ? m[1] : null;
}

// ── Page-type router ────────────────────────────────────────────────────────

function detectPageType(url = location.href) {
  const path = new URL(url).pathname;
  if (path === "/home")                              return "home";
  if (/^\/explore/.test(path))                       return "explore";
  if (/^\/notifications/.test(path))                 return "notifications";
  if (/^\/messages/.test(path))                      return "messages";
  if (/^\/search/.test(path))                        return "search";
  if (/^\/i\/lists\//.test(path))                    return "list";
  if (/^\/i\/spaces\//.test(path))                   return "space";
  if (/^\/i\/communities\//.test(path))              return "community";
  if (/^\/hashtag\//.test(path))                     return "hashtag";
  if (/\/status\/\d+/.test(path))                    return "tweet_detail";
  if (/^\/[^/]+\/?$/.test(path))                     return "profile";
  return "unknown";
}

// ── Tweets (the primary card type across home, profile, search, hashtag) ────

function extractTweets(root = document, ownHandle = null) {
  const out = [];
  const seen = new Set();

  const articles = root.querySelectorAll("article[data-testid='tweet']");
  for (const el of articles) {
    try {
      const statusLink = el.querySelector("a[href*='/status/']");
      if (!statusLink) continue;
      const href = statusLink.getAttribute("href") || "";
      const idMatch = href.match(/\/status\/(\d+)/);
      if (!idMatch) continue;
      const tweetId = idMatch[1];
      if (seen.has(tweetId)) continue;
      seen.add(tweetId);

      const handleMatch = href.match(/^\/([^/]+)\/status\//);
      const authorHandle = handleMatch ? handleMatch[1] : null;

      const nameEl = el.querySelector("[data-testid='User-Name']");
      const authorName = _text(nameEl?.querySelector("span"), 120) || _text(nameEl, 120);

      const textEl = el.querySelector("[data-testid='tweetText']");
      const text = _text(textEl, 4096);

      const likes = _ariaCount(el, "[data-testid='like']");
      const replies = _ariaCount(el, "[data-testid='reply']");
      const reposts = _ariaCount(el, "[data-testid='retweet']");
      const views = _ariaCount(el, "a[aria-label*='view']") ??
                    _ariaCount(el, "[data-testid='app-text-transition-container']");

      // Media (images + GIF previews + videos)
      const mediaEls = el.querySelectorAll(
        "[data-testid='tweetPhoto'] img, " +
        "img[src*='pbs.twimg.com']:not([src*='profile_images']), " +
        "video[poster], " +
        "[data-testid='videoComponent'] video"
      );
      const media = Array.from(mediaEls).map(m => ({
        kind: m.tagName.toLowerCase() === "video" ? "video" : "image",
        url: m.getAttribute("src") || m.getAttribute("poster") || m.getAttribute("data-src"),
        alt: m.getAttribute("alt") || null,
      })).filter(m => m.url).slice(0, 10);
      const mediaUrls = media.map(m => m.url);

      // Quote tweet detection — the nested tweet block
      const quotedArticle = el.querySelector("[data-testid='quoteTweet'] article") ||
                            el.querySelector("div[role='link'][tabindex] article[data-testid='tweet']");
      const isQuote = !!el.querySelector("[data-testid='quoteTweet']") || !!quotedArticle;

      // Thread / reply context (LinkedIn-equivalent of "replying to @x")
      const socialContext = _text(el.querySelector("[data-testid='socialContext']"), 120);
      const isThread = !!socialContext && /thread|replying/i.test(socialContext);
      const replyingTo = Array.from(el.querySelectorAll("a[href*='/']"))
        .map(a => a.textContent?.trim()).filter(t => t && t.startsWith("@"))
        .slice(0, 5);

      // Timestamp
      const timeEl = el.querySelector("time");
      const tweetedAt = timeEl?.getAttribute("datetime") || null;
      const tweetedRelative = _text(timeEl, 24);

      // Author verified / subscribed icon + user info bar
      const isVerified = !!el.querySelector("[data-testid='icon-verified']");
      const authorAvatar = el.querySelector("[data-testid='Tweet-User-Avatar'] img")?.getAttribute("src") || null;

      // Author profile URL
      const authorProfileUrl = authorHandle ? _absUrl(`/${authorHandle}`) : null;

      // View count explicit from the analytics link
      const viewsLink = el.querySelector("a[href$='/analytics'], a[aria-label*='view' i]");
      const viewsExplicit = _parseCount(viewsLink?.getAttribute("aria-label") || viewsLink?.textContent);

      // Engagement action buttons visible
      const actionsAvailable = Array.from(el.querySelectorAll("[role='group'] button"))
        .map(b => b.getAttribute("data-testid") || b.textContent?.trim())
        .filter(Boolean).slice(0, 6);

      // Bookmarks / share counts (rarely shown but when they are)
      const bookmarkCount = _ariaCount(el, "[data-testid='bookmark']");
      const shareCount    = _ariaCount(el, "[aria-label*='Share' i]");

      // Community context (e.g. "From X Community") if present
      const communityLabel = _text(el.querySelector("[data-testid='socialContextTop']"), 200);

      // Links embedded in the tweet body (t.co shortlinks, hashtags, mentions)
      const links = _linksIn(textEl);

      // Raw card text for safety net
      const cardRawText = _text(el, 8192);

      const url = _absUrl(href);

      out.push({
        platform: "x",
        type: isQuote ? "quote_tweet_seen" : (isThread ? "thread_seen" : "feed_post_seen"),
        platform_post_id: tweetId,
        observed_at: new Date().toISOString(),
        extractor_version: VERSION,
        author_handle: authorHandle,
        author_name: authorName,
        text_excerpt: text ? text.slice(0, 512) : null,
        url,
        like_count: likes,
        reply_count: replies,
        repost_count: reposts,
        view_count: viewsExplicit ?? views,
        is_own: ownHandle && authorHandle === ownHandle,
        raw_attrs: {
          full_text: text,
          hashtags: _hashtagsIn(text),
          mentions: _mentionsIn(text),
          media_urls: mediaUrls,
          media,
          is_quote: !!isQuote,
          is_thread: !!isThread,
          tweeted_at: tweetedAt,
          tweeted_relative: tweetedRelative,
          is_verified: isVerified,
          author_avatar: authorAvatar,
          author_profile_url: authorProfileUrl,
          social_context: socialContext,
          replying_to: replyingTo,
          community_label: communityLabel,
          quoted_post_id: quotedArticle?.querySelector("a[href*='/status/']")?.getAttribute("href")?.match(/\/status\/(\d+)/)?.[1] || null,
          quoted_source: quotedArticle ? {
            author_handle: (quotedArticle.querySelector("a[href*='/status/']")?.getAttribute("href") || "").match(/^\/([^/]+)\/status\//)?.[1] || null,
            text: _text(quotedArticle.querySelector("[data-testid='tweetText']"), 2048),
          } : null,
          bookmark_count: bookmarkCount,
          share_count: shareCount,
          actions_available: actionsAvailable,
          links,
          card_raw_text: cardRawText,
        },
      });
    } catch (_) {}
  }
  return out;
}

// ── Replies to a tweet (when on /user/status/ID and the thread is expanded) ─

function extractReplies(root = document, ownHandle = null) {
  // When viewing a tweet_detail page, each reply is an article[data-testid=tweet]
  // below the main one. The main tweet is the first article; everything after
  // is a reply in the thread context.
  if (detectPageType() !== "tweet_detail") return [];
  const out = [];
  const articles = Array.from(root.querySelectorAll("article[data-testid='tweet']"));
  // Skip the first (main) tweet — already captured by extractTweets
  for (const el of articles.slice(1)) {
    try {
      const statusLink = el.querySelector("a[href*='/status/']");
      const href = statusLink?.getAttribute("href") || "";
      const idMatch = href.match(/\/status\/(\d+)/);
      if (!idMatch) continue;
      const replyId = idMatch[1];
      const handleMatch = href.match(/^\/([^/]+)\/status\//);
      const authorHandle = handleMatch ? handleMatch[1] : null;
      const authorName = _text(el.querySelector("[data-testid='User-Name']")?.querySelector("span"), 120);
      const textEl = el.querySelector("[data-testid='tweetText']");
      const text = _text(textEl, 4096);
      const likes = _ariaCount(el, "[data-testid='like']");
      const replies = _ariaCount(el, "[data-testid='reply']");
      const reposts = _ariaCount(el, "[data-testid='retweet']");
      const views = _ariaCount(el, "a[aria-label*='view']");
      const timeEl = el.querySelector("time");
      const tweetedAt = timeEl?.getAttribute("datetime") || null;
      const parentMatch = location.pathname.match(/\/status\/(\d+)/);
      const parentId = parentMatch ? parentMatch[1] : null;

      out.push({
        platform: "x",
        type: "comment_seen",
        platform_post_id: replyId,
        observed_at: new Date().toISOString(),
        extractor_version: VERSION,
        author_handle: authorHandle,
        author_name: authorName,
        text_excerpt: text ? text.slice(0, 512) : null,
        url: _absUrl(href),
        like_count: likes,
        reply_count: replies,
        repost_count: reposts,
        view_count: views,
        is_own: ownHandle && authorHandle?.toLowerCase() === ownHandle?.toLowerCase(),
        raw_attrs: {
          parent_post_id: parentId,
          full_text: text,
          hashtags: _hashtagsIn(text),
          mentions: _mentionsIn(text),
          links: _linksIn(textEl),
          posted_at: tweetedAt,
          card_raw_text: _text(el, 4096),
        },
      });
    } catch (_) {}
  }
  return out;
}

// ── Profile page (when on /<handle>) ────────────────────────────────────────

function extractProfilePage() {
  if (detectPageType() !== "profile") return [];
  const handle = location.pathname.replace(/^\//, "").replace(/\/$/, "");
  if (!handle || handle.includes("/")) return [];
  const nameEl = document.querySelector("[data-testid='UserName'] span, h2[role='heading'] span");
  const name = _text(nameEl, 200);
  const bio = _text(document.querySelector("[data-testid='UserDescription']"), 2048);
  const location_ = _text(document.querySelector("[data-testid='UserLocation']"), 200);
  const joined = _text(document.querySelector("[data-testid='UserJoinDate']"), 100);
  const website = document.querySelector("[data-testid='UserUrl'] a")?.getAttribute("href") || null;
  const followers = _parseCount(_text(document.querySelector("a[href$='/verified_followers'], a[href$='/followers']")));
  const following = _parseCount(_text(document.querySelector("a[href$='/following']")));

  return [{
    platform: "x",
    type: "profile_page_viewed",
    platform_post_id: `x:profile:${handle}`,
    observed_at: new Date().toISOString(),
    extractor_version: VERSION,
    author_handle: handle,
    author_name: name,
    text_excerpt: bio ? bio.slice(0, 512) : null,
    url: location.href,
    like_count: followers,
    reply_count: following,
    repost_count: null,
    view_count: null,
    is_own: false,
    raw_attrs: {
      handle, name, bio,
      location: location_,
      joined,
      website,
      followers,
      following,
      hashtags: _hashtagsIn(bio),
    },
  }];
}

// ── Hashtag / search context ────────────────────────────────────────────────

function extractSearchContext() {
  const page = detectPageType();
  if (page !== "search" && page !== "hashtag") return [];
  const q = page === "hashtag"
    ? (location.pathname.match(/\/hashtag\/([^/?#]+)/) || [])[1]
    : (new URLSearchParams(location.search).get("q") || "");
  if (!q) return [];
  return [{
    platform: "x",
    type: page === "hashtag" ? "hashtag_feed_seen" : "search_result_seen",
    platform_post_id: `x:${page}:${q}`.slice(0, 512),
    observed_at: new Date().toISOString(),
    extractor_version: VERSION,
    author_handle: null,
    author_name: page === "hashtag" ? `#${q}` : null,
    text_excerpt: q,
    url: location.href,
    like_count: null, reply_count: null, repost_count: null, view_count: null,
    is_own: false,
    raw_attrs: { query: q, page },
  }];
}

// ── Lists / Spaces / Communities ────────────────────────────────────────────

function extractListOrSpaceOrCommunity() {
  const page = detectPageType();
  const typeMap = { list: "list_viewed", space: "space_seen", community: "community_seen" };
  if (!typeMap[page]) return [];
  const id = location.pathname.split("/").filter(Boolean).pop();
  const title = _text(document.querySelector("h2, h1"), 400);
  return [{
    platform: "x",
    type: typeMap[page],
    platform_post_id: `x:${page}:${id}`,
    observed_at: new Date().toISOString(),
    extractor_version: VERSION,
    author_handle: null,
    author_name: title,
    text_excerpt: title,
    url: location.href,
    like_count: null, reply_count: null, repost_count: null, view_count: null,
    is_own: false,
    raw_attrs: { id, title },
  }];
}

// ── Top-level ───────────────────────────────────────────────────────────────

function scanAll(root = document) {
  const ownHandle = _detectOwnHandle();
  const page = detectPageType();
  const all = [];

  all.push(...extractTweets(root, ownHandle));
  if (page === "tweet_detail")                             all.push(...extractReplies(root, ownHandle));
  if (page === "profile")                                  all.push(...extractProfilePage());
  if (page === "search" || page === "hashtag")             all.push(...extractSearchContext());
  if (page === "list" || page === "space" || page === "community") {
    all.push(...extractListOrSpaceOrCommunity());
  }
  return all;
}

globalThis.TwitterExtractor = {
  VERSION,
  detectPageType,
  scanAll,
  extractTweets,
  extractReplies,
  extractProfilePage,
  extractSearchContext,
  extractListOrSpaceOrCommunity,
};
