/**
 * LinkedIn extractor — comprehensive, DOM-only.
 *
 * CRITICAL CONSTRAINTS:
 *   • Read-only: we never click, hover, scroll, or otherwise drive the page.
 *   • DOM-only: we never fetch() or XHR to linkedin.com. Everything we know
 *     comes from what LinkedIn has already rendered in the tab.
 *   • Robust: selectors have multiple fallbacks; failing to extract a field
 *     is never fatal — we emit what we can with the rest as null.
 *   • Deterministic IDs: every record has a stable platform_post_id so
 *     repeated scans of the same DOM don't flood the backend (server dedupes
 *     on (user_id, platform_id, type_id, platform_post_id)).
 */

const VERSION = "linkedin-v5";

// ── Utilities ────────────────────────────────────────────────────────────────

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
  const btn = root?.querySelector?.(selector);
  return btn ? _parseCount(btn.getAttribute("aria-label") || btn.textContent) : null;
}

function _handleFromHref(href) {
  if (!href) return null;
  const m = href.match(/\/in\/([^/?#]+)/);
  return m ? decodeURIComponent(m[1]) : null;
}

function _companyFromHref(href) {
  const m = (href || "").match(/\/company\/([^/?#]+)/);
  return m ? decodeURIComponent(m[1]) : null;
}

function _hashtagsIn(text) {
  if (!text) return [];
  return Array.from(new Set((text.match(/#[A-Za-z0-9_]+/g) || []).map(h => h.slice(1))));
}

function _mentionsIn(text) {
  if (!text) return [];
  return Array.from(new Set((text.match(/@[A-Za-z0-9_.-]+/g) || []).map(m => m.slice(1))));
}

function _absUrl(href) {
  if (!href) return null;
  try { return new URL(href, location.origin).href; } catch { return null; }
}

// Extract every link from a subtree — url + anchor text + whether it's a profile/company/post URL
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
    out.push({
      url: abs,
      text: _text(a, 160) || null,
      kind:
        /\/in\//.test(href) ? "profile" :
        /\/company\//.test(href) ? "company" :
        /\/feed\/update\//.test(href) ? "post" :
        /\/pulse\//.test(href) ? "article" :
        /\/jobs\//.test(href) ? "job" :
        /\/feed\/hashtag\//.test(href) ? "hashtag" :
        /\/events\//.test(href) ? "event" :
        /lnkd\.in\//.test(href) ? "shortlink" :
        "external",
    });
    if (out.length >= 20) break;
  }
  return out;
}

// Capture every data-* attribute and aria-label we can find — safety net for
// fields we didn't anticipate but might be useful for later cleanup.
function _dumpSelectedAttrs(root, limit = 20) {
  if (!root) return {};
  const out = {};
  const atts = ["data-urn", "data-id", "data-test-id", "data-finite-scroll-hotkey-item",
                "data-ember-action", "data-view-name", "data-chameleon-result-urn"];
  for (const el of root.querySelectorAll("[" + atts.join("],[") + "]")) {
    for (const a of atts) {
      const v = el.getAttribute(a);
      if (v && !(a in out)) out[a] = v;
    }
    if (Object.keys(out).length >= limit) break;
  }
  return out;
}

function _detectOwnHandle() {
  const selectors = [
    "a[data-control-name='identity_profile_photo']",
    ".global-nav__me a[href*='/in/']",
    "a.global-nav__primary-link-me-menu-trigger",
  ];
  for (const sel of selectors) {
    const el = document.querySelector(sel);
    if (!el) continue;
    const href = el.getAttribute("href") || el.closest("a")?.getAttribute("href");
    const h = _handleFromHref(href);
    if (h) return h;
  }
  return null;
}

// ── Page-type router ─────────────────────────────────────────────────────────

function detectPageType(url = location.href) {
  const path = new URL(url).pathname;
  if (/^\/feed\/?$/.test(path))                           return "feed";
  if (/^\/feed\/update\//.test(path))                     return "post_detail";
  if (/^\/pulse\//.test(path))                            return "article";
  if (/^\/newsletters\//.test(path))                      return "newsletter";
  if (/^\/company\//.test(path))                          return "company";
  if (/^\/in\//.test(path))                               return "profile";
  if (/^\/jobs\/view\//.test(path))                       return "job_detail";
  if (/^\/jobs\//.test(path))                             return "jobs";
  if (/^\/search\//.test(path))                           return "search";
  if (/^\/feed\/hashtag\//.test(path))                    return "hashtag";
  if (/^\/notifications\//.test(path))                    return "notifications";
  if (/^\/events\//.test(path))                           return "event";
  if (/^\/messaging\//.test(path))                        return "messaging";
  return "unknown";
}

// ── Feed posts ──────────────────────────────────────────────────────────────

function extractFeedPosts(root = document, ownHandle = null) {
  const out = [];
  const seen = new Set();

  let containers = Array.from(root.querySelectorAll(
    "[data-urn^='urn:li:activity:'], " +
    "[data-urn^='urn:li:aggregate:'], " +
    "div.feed-shared-update-v2, " +
    "div[class*='occludable-update']"
  ));
  if (containers.length === 0) {
    for (const link of root.querySelectorAll("a[href*='/feed/update/urn:li:activity:']")) {
      const c = link.closest("div[class*='update'], div[class*='feed'], article, li");
      if (c) containers.push(c);
    }
  }

  for (const el of containers) {
    try {
      let urn = el.getAttribute("data-urn") || el.getAttribute("data-id");
      if (!urn) {
        const actLink = el.querySelector("a[href*='/feed/update/urn:li:activity:']");
        if (actLink) {
          const m = actLink.getAttribute("href").match(/(urn:li:activity:[^/?#&]+)/);
          if (m) urn = decodeURIComponent(m[1]);
        }
      }
      if (!urn || !urn.startsWith("urn:li:") || seen.has(urn)) continue;
      seen.add(urn);

      let authorHandle = null, authorName = null, authorHeadline = null;
      const authorLink = el.querySelector("a[href*='/in/']") || el.querySelector("a[href*='/company/']");
      if (authorLink) {
        const href = authorLink.getAttribute("href") || "";
        authorHandle = _handleFromHref(href) || _companyFromHref(href);
        authorName = _text(authorLink.querySelector("span[aria-hidden='true']") || authorLink, 120);
      }
      authorHeadline = _text(el.querySelector(".update-components-actor__description, .feed-shared-actor__description"), 200);

      let text = null;
      const textSel = el.querySelector(
        ".update-components-text, .feed-shared-update-v2__description, " +
        ".feed-shared-text, [class*='commentary']"
      );
      if (textSel) text = _text(textSel, 4096);
      if (!text) {
        for (const sp of el.querySelectorAll("span[dir='ltr']")) {
          if (sp.closest("button")) continue;
          const t = _text(sp, 4096);
          if (t && t.length > 20) { text = t; break; }
        }
      }

      const likes = _ariaCount(el, "button[aria-label*='reaction']") ??
                    _ariaCount(el, "[aria-label*='like']") ??
                    _parseCount(_text(el.querySelector(".social-details-social-counts__reactions-count")));
      const replies = _ariaCount(el, "button[aria-label*='comment']") ??
                      _parseCount(_text(el.querySelector(".social-details-social-counts__comments")));
      const reposts = _ariaCount(el, "button[aria-label*='repost']") ??
                      _parseCount(_text(el.querySelector(".social-details-social-counts__reposts")));

      // Reaction breakdown — LinkedIn renders a stack of icons even without hover
      const reactions = {};
      for (const img of el.querySelectorAll(
        "img.reactions-icon, img[data-test-reactions-icon-type], " +
        "li.social-details-reactors-facepile__reaction-list-item img, " +
        ".reactions-icon img"
      )) {
        const t = img.getAttribute("data-test-reactions-icon-type") ||
                  (img.alt || img.getAttribute("aria-label") || "")
                    .toLowerCase().trim().replace(/\s+/g, "_");
        if (!t) continue;
        const known = t.match(/^(like|celebrate|support|love|insightful|curious|funny)$/);
        const key = known ? known[1] : t.replace(/[^a-z_]/g, "").slice(0, 24);
        if (key) reactions[key] = (reactions[key] || 0) + 1;
      }

      // Post timestamp: the relative "3h" text or the element's datetime attribute
      const timeEl = el.querySelector("time[datetime], time");
      const postedAt = timeEl?.getAttribute("datetime") || null;
      const postedRelative = _text(timeEl, 32);

      // Sponsored / Promoted flag
      const subDesc = _text(el.querySelector(
        ".update-components-actor__sub-description, .feed-shared-actor__sub-description"
      ), 120) || "";
      const isSponsored = /promoted|sponsored/i.test(subDesc);

      // Poll detail (when the card has a poll)
      const pollEl = el.querySelector("[class*='poll']");
      let pollDetail = null;
      if (pollEl) {
        const q = _text(pollEl.querySelector("[class*='question'], h2, h3"), 400);
        const opts = Array.from(pollEl.querySelectorAll("[class*='option']"))
          .map(o => ({ label: _text(o, 120), pct: _parseCount(_text(o.querySelector("[class*='percent']"))) }))
          .filter(o => o.label);
        const totalVotes = _parseCount(_text(pollEl.querySelector("[class*='total-votes'], [class*='votes']")));
        pollDetail = { question: q, options: opts, total_votes: totalVotes };
      }

      // Media with type detection (image vs video)
      const mediaEls = el.querySelectorAll(
        "img.feed-shared-image, video, img.update-components-image, .update-components-image img"
      );
      const media = Array.from(mediaEls).map(m => ({
        kind: m.tagName.toLowerCase() === "video" ? "video" : "image",
        url: m.getAttribute("src") || m.getAttribute("data-src") || m.getAttribute("poster"),
        alt: m.getAttribute("alt") || null,
      })).filter(m => m.url).slice(0, 10);
      const mediaUrls = media.map(m => m.url);

      // Reactor facepile — names visible above the engagement counts.
      // "Venugopal Maddukuri and 68 others" → names: ["Venugopal Maddukuri"], others_count: 68
      const facepileEl = el.querySelector(
        ".social-details-reactors-facepile, " +
        ".update-v2-social-activity, " +
        ".social-details-social-counts"
      );
      const facepileText = _text(facepileEl, 400);
      const facepileNames = Array.from(el.querySelectorAll(
        ".social-details-reactors-facepile__reactor img, " +
        ".update-v2-social-activity__social-counts-avatars img, " +
        ".social-details-reactors-facepile a img"
      )).map(i => i.getAttribute("alt") || i.getAttribute("aria-label"))
        .filter(Boolean).filter((v, i, arr) => arr.indexOf(v) === i).slice(0, 10);
      // "and N others" — capture the total number of reactors beyond the shown faces.
      const othersMatch = (facepileText || "").match(/and\s+([\d,]+)\s+others?/i);
      const othersCount = othersMatch ? _parseCount(othersMatch[1]) : null;

      // Reaction-type icons in the facepile (the stack of small emoji).
      // Each img represents one distinct reaction type present in the post.
      const facepileReactionTypes = Array.from(el.querySelectorAll(
        ".social-details-social-counts__reactions img, " +
        ".social-details-reactors-facepile .reactions-icon, " +
        ".social-counts-reactions__reaction-icon"
      )).map(i => {
        const t = i.getAttribute("data-test-reactions-icon-type") ||
                  (i.getAttribute("alt") || i.getAttribute("aria-label") || "")
                    .toLowerCase().trim().replace(/\s+/g, "_");
        return t || null;
      }).filter(Boolean).filter((v, i, arr) => arr.indexOf(v) === i);

      // "Edited" flag — LinkedIn renders this inline next to the timestamp
      const actorSubtext = _text(el.querySelector(
        ".update-components-actor__sub-description, " +
        ".feed-shared-actor__sub-description, " +
        ".update-components-actor__meta"
      ), 200) || "";
      const isEdited = /\bedited\b/i.test(actorSubtext) || !!el.querySelector("[aria-label*='edited' i]");

      // Article / external-link preview card embedded in the post (OG card)
      const articlePreviewEl = el.querySelector(
        ".feed-shared-article, .update-components-article, " +
        ".feed-shared-external-video, .update-components-entity"
      );
      let articlePreview = null;
      if (articlePreviewEl) {
        const aLink = articlePreviewEl.querySelector("a[href]");
        articlePreview = {
          title: _text(articlePreviewEl.querySelector("[class*='title'], h3, h2"), 300),
          subtitle: _text(articlePreviewEl.querySelector("[class*='subtitle']"), 300),
          source: _text(articlePreviewEl.querySelector("[class*='source']"), 120),
          url: _absUrl(aLink?.getAttribute("href")),
        };
      }

      // Quoted/reshared source post — when a repost includes the original
      const reshareEl = el.querySelector(
        ".feed-shared-reshare, .update-components-mini-update-v2, " +
        ".feed-shared-update-v2__reshared-content"
      );
      let resharedSource = null;
      if (reshareEl) {
        const srcAuthorLink = reshareEl.querySelector("a[href*='/in/'], a[href*='/company/']");
        resharedSource = {
          author_handle: srcAuthorLink ? (_handleFromHref(srcAuthorLink.getAttribute("href")) || _companyFromHref(srcAuthorLink.getAttribute("href"))) : null,
          author_name: _text(srcAuthorLink?.querySelector("span[aria-hidden='true']") || srcAuthorLink, 120),
          headline: _text(reshareEl.querySelector(".update-components-actor__description"), 200),
          text: _text(reshareEl.querySelector(".update-components-text"), 2048),
          urn: reshareEl.getAttribute("data-urn") || null,
        };
      }

      // Translation affordance indicates non-default-language post
      const hasTranslateCTA = !!el.querySelector("button[aria-label*='Translate' i], [class*='translate']");

      // Engagement action buttons (Like / Comment / Repost / Send)
      // We capture which actions are *present* (some posts hide Repost etc).
      const actionsAvailable = Array.from(el.querySelectorAll(".social-actions-button, .feed-shared-social-action-bar button"))
        .map(b => _text(b, 40)).filter(Boolean).map(t => t.toLowerCase());

      const postLink = el.querySelector("a[href*='/feed/update/']") ||
                       el.querySelector(`a[href*='${urn}']`);
      const url = _absUrl(postLink?.getAttribute("href"));

      const isReshare = !!reshareEl;

      // Every outbound link inside the post body (including lnkd.in shortlinks)
      const bodyLinks = _linksIn(textSel) ?? _linksIn(el);

      // Raw text dump for the entire card as a debugging/backfill safety net.
      // Lets us reconstruct fields we missed later without re-scraping.
      const cardRawText = _text(el, 8192);

      out.push({
        platform: "linkedin",
        type: isReshare ? "reshare_seen" : (pollEl ? "poll_seen" : "feed_post_seen"),
        platform_post_id: urn,
        observed_at: new Date().toISOString(),
        extractor_version: VERSION,
        author_handle: authorHandle,
        author_name: authorName,
        text_excerpt: text ? text.slice(0, 512) : null,
        url,
        like_count: likes,
        reply_count: replies,
        repost_count: reposts,
        view_count: null,
        is_own: ownHandle && authorHandle === ownHandle,
        raw_attrs: {
          author_headline: authorHeadline,
          full_text: text,
          hashtags: _hashtagsIn(text),
          mentions: _mentionsIn(text),
          media_urls: mediaUrls,
          media,
          reactions: Object.keys(reactions).length ? reactions : null,
          facepile_reaction_types: facepileReactionTypes.length ? facepileReactionTypes : null,
          facepile_names: facepileNames.length ? facepileNames : null,
          facepile_text: facepileText,
          reactor_others_count: othersCount,
          posted_at: postedAt,
          posted_relative: postedRelative,
          is_sponsored: isSponsored,
          is_edited: isEdited,
          actor_subtext: actorSubtext,
          has_poll: !!pollEl,
          poll: pollDetail,
          is_reshare: isReshare,
          reshared_source: resharedSource,
          article_preview: articlePreview,
          has_translate_cta: hasTranslateCTA,
          body_links: bodyLinks,
          actions_available: actionsAvailable,
          engagers: facepileNames.length ? facepileNames : null,
          card_raw_text: cardRawText,
          dom_attrs: _dumpSelectedAttrs(el),
        },
      });
    } catch (_) { /* skip bad node */ }
  }

  return out;
}

// ── Comments (when expanded under a post) ───────────────────────────────────

function extractComments(root = document, ownHandle = null) {
  const out = [];
  const nodes = root.querySelectorAll(
    "article.comments-comment-item, " +
    "div.comments-comment-entity, " +
    "[data-id^='urn:li:comment:'], " +
    "article.comments-comments-list__comment-item"
  );
  for (const el of nodes) {
    try {
      const id = el.getAttribute("data-id") ||
                 el.querySelector("[data-id^='urn:li:comment:']")?.getAttribute("data-id");
      if (!id) continue;

      // Author
      const authorLink = el.querySelector("a[href*='/in/'], a[href*='/company/']") ||
                         el.querySelector(".comments-post-meta a");
      const authorHrefRaw = authorLink?.getAttribute("href") || "";
      const authorHandle = _handleFromHref(authorHrefRaw) || _companyFromHref(authorHrefRaw);
      const authorName = _text(
        authorLink?.querySelector("span[aria-hidden='true']") || authorLink,
        140,
      );
      const authorUrl = _absUrl(authorHrefRaw);

      // Author headline — "Vice President at Kidder Mathews", "Cybersecurity CMO | Top 100…"
      const authorHeadline = _text(
        el.querySelector(
          ".comments-post-meta__headline, " +
          ".comments-post-meta__profile-headline, " +
          ".comments-comment-item__main-content-container .t-12, " +
          ".comments-post-meta .t-black--light"
        ),
        300,
      );

      // Connection degree badge — "1st", "2nd", "3rd+", sometimes an ℹ icon
      // These appear in a dist-value or similar class.
      const degreeEl = el.querySelector(
        ".comments-post-meta__dist-value, " +
        ".distance-badge, " +
        ".comments-post-meta__name-text + .t-12"
      );
      let connectionDegree = _text(degreeEl, 10);
      if (!connectionDegree) {
        // Fallback: regex from the meta block text
        const meta = _text(el.querySelector(".comments-post-meta"), 200) || "";
        const m = meta.match(/\b(1st|2nd|3rd\+?|Following|Follow)\b/i);
        if (m) connectionDegree = m[1];
      }

      // "Author" badge — LinkedIn marks the post author's own comments with a badge.
      const isPostAuthor = !!el.querySelector(".comments-post-meta__author-badge") ||
                           /\bAuthor\b/.test(_text(el.querySelector(".comments-post-meta"), 100) || "");

      // Edited flag — "(edited)" label
      const metaText = _text(el.querySelector(".comments-post-meta, .comments-comment-meta"), 300) || "";
      const isEdited = /\bedited\b/i.test(metaText);

      // Timestamp — absolute (datetime attr) + relative text
      const timeEl = el.querySelector("time[datetime], time, .comments-comment-item__timestamp");
      const datetimeIso = timeEl?.getAttribute("datetime") || null;
      const timeAgo = _text(timeEl, 24) || (metaText.match(/\b\d+\s*[smhdwy]\b/) || [null])[0];

      // Main body text
      const bodyEl = el.querySelector(
        ".comments-comment-item__main-content, " +
        ".update-components-text, " +
        ".feed-shared-comment-text, " +
        ".comments-comment-item-content-body"
      );
      const text = _text(bodyEl, 4096);

      // Every link in the comment body — LinkedIn shortlinks (lnkd.in) + external
      const links = _linksIn(bodyEl);

      // Parent post URN — walk up the DOM
      let parentPost = null;
      const postAncestor = el.closest("[data-urn^='urn:li:activity:']");
      if (postAncestor) parentPost = postAncestor.getAttribute("data-urn");

      // Parent comment URN (for nested replies) — walk up through nested thread
      let parentCommentUrn = null;
      const commentAncestor = el.parentElement?.closest("[data-id^='urn:li:comment:']");
      if (commentAncestor && commentAncestor !== el) {
        parentCommentUrn = commentAncestor.getAttribute("data-id");
      }

      // Like count on the comment itself
      const likes = _parseCount(
        _text(
          el.querySelector(
            ".comments-comment-social-bar__reactions-count, " +
            "[class*='reactions-count'], " +
            ".comments-comment-social-bar__action-button--reaction .artdeco-button__text"
          ),
          40,
        )
      ) ?? _ariaCount(el, "[aria-label*='reaction']");

      // Reply count on the comment itself (distinct from parent's reply total)
      const commentReplies = _parseCount(
        _text(
          el.querySelector(
            ".comments-comment-social-bar__replies-count, " +
            ".comments-comment-item__replies, " +
            "button[aria-label*='replies' i]"
          ),
          80,
        )
      );

      // Reaction breakdown emojis on the comment
      const commentReactions = {};
      for (const img of el.querySelectorAll(
        ".comments-comment-social-bar__reactions img, " +
        ".reactions-menu img, " +
        "img.reactions-icon"
      )) {
        const t = img.getAttribute("data-test-reactions-icon-type") ||
                  (img.alt || "").toLowerCase().trim().replace(/\s+/g, "_");
        if (t) commentReactions[t] = (commentReactions[t] || 0) + 1;
      }

      // Media in the comment (LinkedIn allows image/GIF in comments)
      const commentMedia = Array.from(el.querySelectorAll(
        ".comments-comment-item__main-content img.evi-image-view, " +
        ".comments-comment-media img"
      )).map(img => ({
        kind: "image",
        url: img.getAttribute("src") || img.getAttribute("data-src"),
        alt: img.getAttribute("alt") || null,
      })).filter(m => m.url).slice(0, 5);

      // Raw text dump as safety net
      const cardRawText = _text(el, 4096);

      out.push({
        platform: "linkedin",
        type: "comment_seen",
        platform_post_id: id,
        observed_at: new Date().toISOString(),
        extractor_version: VERSION,
        author_handle: authorHandle,
        author_name: authorName,
        text_excerpt: text ? text.slice(0, 512) : null,
        url: parentPost ? _absUrl(`/feed/update/${parentPost}/?commentUrn=${encodeURIComponent(id)}`) : null,
        like_count: likes,
        reply_count: commentReplies,
        repost_count: null,
        view_count: null,
        is_own: ownHandle && authorHandle === ownHandle,
        raw_attrs: {
          parent_post_id: parentPost,
          parent_comment_id: parentCommentUrn,
          full_text: text,
          hashtags: _hashtagsIn(text),
          mentions: _mentionsIn(text),
          links,
          author_headline: authorHeadline,
          author_url: authorUrl,
          connection_degree: connectionDegree,
          is_post_author: isPostAuthor,
          is_edited: isEdited,
          time_ago: timeAgo,
          posted_at: datetimeIso,
          reactions: Object.keys(commentReactions).length ? commentReactions : null,
          media: commentMedia.length ? commentMedia : null,
          card_raw_text: cardRawText,
        },
      });
    } catch (_) {}
  }
  return out;
}

// ── Article cards visible in feed ───────────────────────────────────────────

function extractArticleCards(root = document) {
  const out = [];
  const seen = new Set();
  for (const a of root.querySelectorAll("a[href*='/pulse/'], a[href*='/newsletters/']")) {
    try {
      const href = a.getAttribute("href");
      if (!href) continue;
      const url = _absUrl(href);
      const id = `link:${url}`;
      if (seen.has(id)) continue;
      const isNewsletter = /\/newsletters\//.test(href);
      const titleEl = a.querySelector("h1,h2,h3,[class*='title'],[class*='headline']") || a;
      const title = _text(titleEl, 400);
      if (!title || title.length < 5) continue;
      seen.add(id);
      // Read time / shares inline — "4 min read", "143 shares"
      const metaContainer = a.closest("article, [class*='update']") || a.parentElement;
      const metaText = _text(metaContainer?.querySelector(".feed-shared-newsletter-metadata, [class*='subtitle']"), 200);
      const readMin = metaText && (metaText.match(/(\d+)\s*min/) || [])[1];
      const shareCount = _parseCount(_text(metaContainer?.querySelector("[class*='shares']")));
      out.push({
        platform: "linkedin",
        type: isNewsletter ? "newsletter_seen" : "article_seen",
        platform_post_id: id.slice(0, 512),
        observed_at: new Date().toISOString(),
        extractor_version: VERSION,
        author_handle: null, author_name: null,
        text_excerpt: title,
        url,
        like_count: null, reply_count: null, repost_count: shareCount, view_count: null,
        is_own: false,
        raw_attrs: {
          title,
          is_newsletter: isNewsletter,
          meta_text: metaText,
          read_minutes: readMin ? parseInt(readMin, 10) : null,
          share_count: shareCount,
        },
      });
    } catch (_) {}
  }
  return out;
}

// ── Current /pulse/ article page ────────────────────────────────────────────

function extractArticlePage() {
  if (detectPageType() !== "article") return [];
  const url = location.href;
  const title = _text(document.querySelector("h1"), 400);
  const author = document.querySelector("a[href*='/in/']");
  const authorName = _text(author?.querySelector("span") || author, 120);
  const authorHandle = _handleFromHref(author?.getAttribute("href"));
  const body = _text(document.querySelector("article, .reader-article-content"), 8192);
  const id = `article:${(url.match(/\/pulse\/([^?#]+)/) || [])[1] || url}`;
  return [{
    platform: "linkedin",
    type: "article_opened",
    platform_post_id: id.slice(0, 512),
    observed_at: new Date().toISOString(),
    extractor_version: VERSION,
    author_handle: authorHandle,
    author_name: authorName,
    text_excerpt: title,
    url,
    like_count: null, reply_count: null, repost_count: null, view_count: null,
    is_own: false,
    raw_attrs: {
      title,
      body_excerpt: body ? body.slice(0, 4096) : null,
      word_count: body ? body.split(/\s+/).length : null,
      hashtags: _hashtagsIn(body),
      mentions: _mentionsIn(body),
    },
  }];
}

// ── Company page ────────────────────────────────────────────────────────────

function extractCompanyPage() {
  if (detectPageType() !== "company") return [];
  const slug = (location.pathname.match(/\/company\/([^/]+)/) || [])[1];
  if (!slug) return [];
  const name = _text(document.querySelector("h1"), 200);
  const tagline = _text(
    document.querySelector(".org-top-card-summary__tagline, .org-top-card-summary-info-list"),
    400,
  );
  const followers = _parseCount(_text(document.querySelector("[class*='follower-count'], .org-top-card-summary-info-list__info-item")));
  const employees = _text(document.querySelector("[class*='company-industries'], .org-about-company-module__company-size-definition-text"), 200);
  const about = _text(document.querySelector(".org-about-us-organization-description, .about-us__description"), 4096);

  return [{
    platform: "linkedin",
    type: "company_viewed",
    platform_post_id: `urn:li:company:${slug}`,
    observed_at: new Date().toISOString(),
    extractor_version: VERSION,
    author_handle: slug,
    author_name: name,
    text_excerpt: tagline,
    url: location.href,
    like_count: followers,
    reply_count: null, repost_count: null, view_count: null,
    is_own: false,
    raw_attrs: { slug, name, tagline, about, employee_info: employees, followers, hashtags: _hashtagsIn(about) },
  }];
}

// ── Profile page ────────────────────────────────────────────────────────────

function extractProfilePage() {
  if (detectPageType() !== "profile") return [];
  const slug = (location.pathname.match(/\/in\/([^/]+)/) || [])[1];
  if (!slug) return [];
  const name = _text(document.querySelector("h1"), 200);
  const headline = _text(
    document.querySelector(".text-body-medium.break-words, .pv-text-details__left-panel .text-body-medium"),
    400,
  );
  const locationText = _text(document.querySelector("span.text-body-small.inline.t-black--light"), 200);
  const about = _text(document.querySelector("#about + .pvs-header + div, section[id*='about'] .inline-show-more-text"), 4096);
  const currentCompany = _text(document.querySelector("[aria-label*='Current company']"), 200);
  const openToWork = !!document.querySelector("[class*='open-to-work']");
  const connections = _parseCount(_text(document.querySelector("a[href*='/connections/']")));

  return [{
    platform: "linkedin",
    type: "profile_page_viewed",
    platform_post_id: `urn:li:person:${slug}`,
    observed_at: new Date().toISOString(),
    extractor_version: VERSION,
    author_handle: slug,
    author_name: name,
    text_excerpt: headline,
    url: location.href,
    like_count: connections,
    reply_count: null, repost_count: null, view_count: null,
    is_own: false,
    raw_attrs: {
      slug, name, headline,
      location: locationText,
      about,
      current_company: currentCompany,
      open_to_work: openToWork,
      connection_count: connections,
    },
  }];
}

// ── Job cards and job detail ────────────────────────────────────────────────

function extractJobCards(root = document) {
  const out = [];
  const seen = new Set();
  for (const card of root.querySelectorAll(
    "[data-job-id], a[href*='/jobs/view/'], .job-card-container, .jobs-search-results__list-item"
  )) {
    try {
      const jobId = card.getAttribute("data-job-id") ||
                    (card.querySelector("a[href*='/jobs/view/']")?.getAttribute("href")
                      ?.match(/\/jobs\/view\/(\d+)/) || [])[1];
      if (!jobId || seen.has(jobId)) continue;
      seen.add(jobId);
      const title = _text(card.querySelector("h3, [class*='job-title'], [class*='job-card-list__title']"), 300);
      const company = _text(card.querySelector(".job-card-container__company-name, [class*='company-name'], h4"), 200);
      const loc = _text(card.querySelector(".job-card-container__metadata-item, [class*='job-card-container__metadata']"), 200);
      const url = _absUrl(card.querySelector("a[href*='/jobs/view/']")?.getAttribute("href"));
      if (!title) continue;
      out.push({
        platform: "linkedin",
        type: "job_post_seen",
        platform_post_id: `urn:li:job:${jobId}`,
        observed_at: new Date().toISOString(),
        extractor_version: VERSION,
        author_handle: null,
        author_name: company,
        text_excerpt: title,
        url,
        like_count: null, reply_count: null, repost_count: null, view_count: null,
        is_own: false,
        raw_attrs: { job_id: jobId, title, company, location: loc },
      });
    } catch (_) {}
  }
  return out;
}

function extractJobDetail() {
  if (detectPageType() !== "job_detail") return [];
  const jobId = (location.pathname.match(/\/jobs\/view\/(\d+)/) || [])[1];
  if (!jobId) return [];
  const title = _text(document.querySelector("h1, .top-card-layout__title"), 300);
  const company = _text(document.querySelector(".topcard__org-name-link, .job-details-jobs-unified-top-card__company-name"), 200);
  const loc = _text(document.querySelector(".topcard__flavor--bullet, .job-details-jobs-unified-top-card__bullet"), 200);
  const description = _text(document.querySelector(".show-more-less-html__markup, .jobs-description__content"), 8192);
  return [{
    platform: "linkedin",
    type: "job_post_opened",
    platform_post_id: `urn:li:job:${jobId}`,
    observed_at: new Date().toISOString(),
    extractor_version: VERSION,
    author_handle: null,
    author_name: company,
    text_excerpt: title,
    url: location.href,
    like_count: null, reply_count: null, repost_count: null, view_count: null,
    is_own: false,
    raw_attrs: { job_id: jobId, title, company, location: loc, description, hashtags: _hashtagsIn(description) },
  }];
}

// ── Search results ──────────────────────────────────────────────────────────

function extractSearchResults(root = document) {
  if (detectPageType() !== "search") return [];
  const out = [];
  const seen = new Set();
  const q = new URLSearchParams(location.search).get("keywords") || "";
  for (const li of root.querySelectorAll("li.reusable-search__result-container, .search-results-container li")) {
    try {
      const link = li.querySelector("a[href*='/in/'], a[href*='/company/'], a[href*='/jobs/']");
      const href = link?.getAttribute("href");
      if (!href) continue;
      const stableId = href.split("?")[0];
      if (seen.has(stableId)) continue;
      seen.add(stableId);
      const title = _text(li.querySelector("span[aria-hidden='true'], .entity-result__title-text"), 200);
      const subtitle = _text(li.querySelector(".entity-result__primary-subtitle, .entity-result__secondary-subtitle"), 300);
      out.push({
        platform: "linkedin",
        type: "search_result_seen",
        platform_post_id: `search:${q}:${stableId}`.slice(0, 512),
        observed_at: new Date().toISOString(),
        extractor_version: VERSION,
        author_handle: _handleFromHref(href) || _companyFromHref(href),
        author_name: title,
        text_excerpt: subtitle,
        url: _absUrl(href),
        like_count: null, reply_count: null, repost_count: null, view_count: null,
        is_own: false,
        raw_attrs: { query: q, title, subtitle, result_href: stableId },
      });
    } catch (_) {}
  }
  return out;
}

// ── People-you-may-know cards ───────────────────────────────────────────────

function extractConnectionSuggestions(root = document) {
  const out = [];
  const seen = new Set();
  for (const card of root.querySelectorAll("[class*='discover-entity'], [class*='pymk'], [data-test-component='pymk']")) {
    try {
      const link = card.querySelector("a[href*='/in/']");
      const handle = _handleFromHref(link?.getAttribute("href"));
      if (!handle || seen.has(handle)) continue;
      seen.add(handle);
      const name = _text(link?.querySelector("span[aria-hidden='true']") || link, 120);
      const headline = _text(card.querySelector("[class*='subtitle'], [class*='headline']"), 200);
      const mutual = _parseCount(_text(card.querySelector("[class*='mutual']")));
      out.push({
        platform: "linkedin",
        type: "connection_suggested",
        platform_post_id: `pymk:${handle}`,
        observed_at: new Date().toISOString(),
        extractor_version: VERSION,
        author_handle: handle,
        author_name: name,
        text_excerpt: headline,
        url: _absUrl(link?.getAttribute("href")),
        like_count: mutual,
        reply_count: null, repost_count: null, view_count: null,
        is_own: false,
        raw_attrs: { name, headline, mutual_connections: mutual },
      });
    } catch (_) {}
  }
  return out;
}

// ── Notifications panel ─────────────────────────────────────────────────────

function extractNotifications(root = document) {
  if (detectPageType() !== "notifications") return [];
  const out = [];
  const seen = new Set();
  for (const card of root.querySelectorAll("article.nt-card, [class*='notification-card']")) {
    try {
      const text = _text(card, 800);
      if (!text) continue;
      const link = card.querySelector("a[href]");
      const id = (link?.getAttribute("href") || `notif:${text.slice(0, 80)}`).slice(0, 512);
      if (seen.has(id)) continue;
      seen.add(id);
      out.push({
        platform: "linkedin",
        type: "notification_seen",
        platform_post_id: id,
        observed_at: new Date().toISOString(),
        extractor_version: VERSION,
        author_handle: null, author_name: null,
        text_excerpt: text.slice(0, 512),
        url: _absUrl(link?.getAttribute("href")),
        like_count: null, reply_count: null, repost_count: null, view_count: null,
        is_own: false,
        raw_attrs: { full_text: text },
      });
    } catch (_) {}
  }
  return out;
}

// ── Hashtag feed context ────────────────────────────────────────────────────

function extractHashtagContext() {
  if (detectPageType() !== "hashtag") return [];
  const tag = (location.pathname.match(/\/feed\/hashtag\/([^/?#]+)/) || [])[1];
  if (!tag) return [];
  const followers = _parseCount(_text(document.querySelector("[class*='follower']")));
  return [{
    platform: "linkedin",
    type: "hashtag_feed_seen",
    platform_post_id: `hashtag:${tag}`,
    observed_at: new Date().toISOString(),
    extractor_version: VERSION,
    author_handle: null,
    author_name: `#${tag}`,
    text_excerpt: null,
    url: location.href,
    like_count: followers,
    reply_count: null, repost_count: null, view_count: null,
    is_own: false,
    raw_attrs: { hashtag: tag, followers },
  }];
}

// ── "Jobs recommended for you" section (visible on feed + job pages) ────────

function extractJobRecommendations(root = document) {
  const out = [];
  const container = root.querySelector(
    "[aria-label*='Jobs recommended for you' i], " +
    "[data-view-name*='job-recommendations' i], " +
    "section[class*='job-recommendations']"
  );
  if (!container) return out;

  const seen = new Set();
  for (const card of container.querySelectorAll("a[href*='/jobs/view/'], [data-job-id], li")) {
    try {
      const jobId = card.getAttribute("data-job-id") ||
                    (card.querySelector("a[href*='/jobs/view/']")?.getAttribute("href")
                      ?.match(/\/jobs\/view\/(\d+)/) || [])[1];
      if (!jobId || seen.has(jobId)) continue;
      seen.add(jobId);
      const title   = _text(card.querySelector("h3, [class*='job-title'], strong"), 300);
      const company = _text(card.querySelector("[class*='company'], h4"), 200);
      const loc     = _text(card.querySelector("[class*='location'], [class*='secondary']"), 200);
      if (!title) continue;
      out.push({
        platform: "linkedin",
        type: "job_recommendation",
        platform_post_id: `jobrec:${jobId}`,
        observed_at: new Date().toISOString(),
        extractor_version: VERSION,
        author_handle: null,
        author_name: company,
        text_excerpt: title,
        url: _absUrl(card.querySelector("a[href*='/jobs/view/']")?.getAttribute("href") || `/jobs/view/${jobId}`),
        like_count: null, reply_count: null, repost_count: null, view_count: null,
        is_own: false,
        raw_attrs: {
          job_id: jobId, title, company,
          location: loc,
          card_raw_text: _text(card, 1024),
        },
      });
    } catch (_) {}
  }
  return out;
}

// ── Messaging inbox thread previews ────────────────────────────────────────
// We read only the previews LinkedIn already rendered — we NEVER open a thread.

function extractMessagingThreads(root = document) {
  if (detectPageType() !== "messaging") return [];
  const out = [];
  const threads = root.querySelectorAll(
    "li.msg-conversation-listitem, " +
    "li[class*='conversation-listitem']"
  );
  for (const li of threads) {
    try {
      const link = li.querySelector("a[href*='/messaging/thread/']");
      const threadId = (link?.getAttribute("href")?.match(/\/messaging\/thread\/([^/?#]+)/) || [])[1];
      if (!threadId) continue;
      const name = _text(li.querySelector(
        ".msg-conversation-card__participant-names, " +
        "[class*='participant-names']"
      ), 200);
      const preview = _text(li.querySelector(
        ".msg-conversation-card__message-snippet, " +
        "[class*='message-snippet']"
      ), 400);
      const time    = _text(li.querySelector(".msg-conversation-card__time-stamp, time"), 24);
      const isUnread = !!li.querySelector("[class*='unread']");
      out.push({
        platform: "linkedin",
        type: "messaging_thread",
        platform_post_id: `msgthread:${threadId}`,
        observed_at: new Date().toISOString(),
        extractor_version: VERSION,
        author_handle: null,
        author_name: name,
        text_excerpt: preview,
        url: _absUrl(link?.getAttribute("href")),
        like_count: null, reply_count: null, repost_count: null, view_count: null,
        is_own: false,
        raw_attrs: {
          thread_id: threadId,
          participants: name,
          last_message_preview: preview,
          time_label: time,
          is_unread: isUnread,
        },
      });
    } catch (_) {}
  }
  return out;
}

// ── Own-profile activity feed ──────────────────────────────────────────────
// When the user is on /in/{self}/recent-activity/, each row tells us
// something about what they engage with.

function extractActivityItems(root = document) {
  if (!/\/recent-activity\//.test(location.pathname)) return [];
  const out = [];
  const items = root.querySelectorAll(
    ".pv-recent-activity-section__content li, " +
    "[class*='recent-activity'] li, " +
    "section[class*='activity'] li"
  );
  for (const li of items) {
    try {
      const link = li.querySelector("a[href*='/feed/update/'], a[href*='/in/'], a[href*='/company/']");
      const href = link?.getAttribute("href") || "";
      const label = _text(li.querySelector("[class*='kicker'], [class*='activity-title']"), 200);
      const preview = _text(li, 600);
      const id = href || `activity:${label?.slice(0, 40)}:${preview?.slice(0, 40)}`;
      out.push({
        platform: "linkedin",
        type: "activity_item",
        platform_post_id: `act:${id}`.slice(0, 512),
        observed_at: new Date().toISOString(),
        extractor_version: VERSION,
        author_handle: null,
        author_name: label,
        text_excerpt: preview.slice(0, 512),
        url: _absUrl(href) || location.href,
        like_count: null, reply_count: null, repost_count: null, view_count: null,
        is_own: true,                 // by definition, this is the user's own activity
        raw_attrs: { label, full_text: preview },
      });
    } catch (_) {}
  }
  return out;
}

// ── Saved items list ──────────────────────────────────────────────────────

function extractSavedItems(root = document) {
  if (!/\/my-items\/saved-|\/saved-posts\//.test(location.pathname)) return [];
  const out = [];
  const items = root.querySelectorAll(
    "li.artdeco-list__item, " +
    "[class*='saved-items'] li, " +
    "section[class*='saved'] li"
  );
  for (const li of items) {
    try {
      const link = li.querySelector("a[href]");
      const href = link?.getAttribute("href") || "";
      if (!href) continue;
      const title = _text(li.querySelector("h3, [class*='title'], strong"), 300);
      const subtitle = _text(li.querySelector("[class*='subtitle'], [class*='secondary']"), 300);
      out.push({
        platform: "linkedin",
        type: "saved_item",
        platform_post_id: `saved:${href}`.slice(0, 512),
        observed_at: new Date().toISOString(),
        extractor_version: VERSION,
        author_handle: null,
        author_name: subtitle,
        text_excerpt: title,
        url: _absUrl(href),
        like_count: null, reply_count: null, repost_count: null, view_count: null,
        is_own: true,
        raw_attrs: { title, subtitle },
      });
    } catch (_) {}
  }
  return out;
}

// ── Reactors list modal ("All reactions" popup) ────────────────────────────

function extractReactorsList(root = document) {
  // LinkedIn opens a modal showing names + reaction type per reactor.
  const modal = root.querySelector(
    ".social-details-reactors-modal, " +
    "[aria-label*='Reactions' i][role='dialog']"
  );
  if (!modal) return [];
  const out = [];
  const parentUrn = _cardUrnFromModal();
  for (const row of modal.querySelectorAll("li, [class*='reactor']")) {
    try {
      const link = row.querySelector("a[href*='/in/'], a[href*='/company/']");
      const href = link?.getAttribute("href") || "";
      const handle = _handleFromHref(href) || _companyFromHref(href);
      if (!handle) continue;
      const name = _text(row.querySelector("span[aria-hidden='true']"), 200);
      const headline = _text(row.querySelector("[class*='subtitle'], [class*='headline']"), 200);
      const reactionImg = row.querySelector("img.reactions-icon, [class*='reaction-type'] img");
      const reactionType = reactionImg?.getAttribute("data-test-reactions-icon-type") ||
                           (reactionImg?.getAttribute("alt") || "").toLowerCase();
      out.push({
        platform: "linkedin",
        type: "reactors_list",
        platform_post_id: `reactor:${parentUrn || "?"}:${handle}`.slice(0, 512),
        observed_at: new Date().toISOString(),
        extractor_version: VERSION,
        author_handle: handle,
        author_name: name,
        text_excerpt: headline,
        url: _absUrl(href),
        like_count: null, reply_count: null, repost_count: null, view_count: null,
        is_own: false,
        raw_attrs: { parent_post_id: parentUrn, reaction_type: reactionType, headline },
      });
    } catch (_) {}
  }
  return out;
}

function _cardUrnFromModal() {
  // Best-effort: whichever post's "Reactions" button opened the modal is the
  // topmost visible post in the main feed.
  const visible = document.querySelector("[data-urn^='urn:li:activity:']");
  return visible?.getAttribute("data-urn") || null;
}

// ── Follower / Following lists ─────────────────────────────────────────────

function extractFollowerItems(root = document) {
  if (!/\/mynetwork\/|\/connections\/|\/followers\/|\/following\//.test(location.pathname)) return [];
  const out = [];
  for (const card of root.querySelectorAll(
    "li.mn-connection-card, " +
    "[class*='connection-card'], " +
    "[class*='follower-card'], " +
    ".scaffold-finite-scroll__content li"
  )) {
    try {
      const link = card.querySelector("a[href*='/in/'], a[href*='/company/']");
      const href = link?.getAttribute("href") || "";
      const handle = _handleFromHref(href) || _companyFromHref(href);
      if (!handle) continue;
      const name = _text(card.querySelector("span[aria-hidden='true'], [class*='name']"), 200);
      const headline = _text(card.querySelector("[class*='occupation'], [class*='subtitle']"), 200);
      out.push({
        platform: "linkedin",
        type: "follower_item",
        platform_post_id: `fol:${handle}`,
        observed_at: new Date().toISOString(),
        extractor_version: VERSION,
        author_handle: handle,
        author_name: name,
        text_excerpt: headline,
        url: _absUrl(href),
        like_count: null, reply_count: null, repost_count: null, view_count: null,
        is_own: false,
        raw_attrs: { name, headline },
      });
    } catch (_) {}
  }
  return out;
}

// ── Event page ──────────────────────────────────────────────────────────────

function extractEventPage() {
  if (detectPageType() !== "event") return [];
  const id = (location.pathname.match(/\/events\/([^/?#]+)/) || [])[1];
  if (!id) return [];
  const title = _text(document.querySelector("h1"), 400);
  const when = _text(document.querySelector("[class*='event-date'], [class*='event-time'], time"), 200);
  const where = _text(document.querySelector("[class*='event-location']"), 400);
  const organizer = _text(document.querySelector("[class*='organizer']"), 200);
  const attendees = _parseCount(_text(document.querySelector("[class*='attendees'], [class*='invitees']")));
  const description = _text(document.querySelector("[class*='event-description'], [class*='description']"), 4096);
  return [{
    platform: "linkedin",
    type: "event_seen",
    platform_post_id: `urn:li:event:${id}`,
    observed_at: new Date().toISOString(),
    extractor_version: VERSION,
    author_handle: null,
    author_name: organizer,
    text_excerpt: title,
    url: location.href,
    like_count: attendees,
    reply_count: null, repost_count: null, view_count: null,
    is_own: false,
    raw_attrs: { id, title, when, where, organizer, attendees, description, hashtags: _hashtagsIn(description) },
  }];
}

// ── Top-level: run every applicable extractor for the current DOM ───────────

function scanAll(root = document) {
  const ownHandle = _detectOwnHandle();
  const page = detectPageType();
  const all = [];

  // Feed cards appear on many pages (feed, profile activity, hashtag, company updates)
  all.push(...extractFeedPosts(root, ownHandle));
  all.push(...extractComments(root, ownHandle));
  all.push(...extractArticleCards(root));
  all.push(...extractJobCards(root));
  all.push(...extractConnectionSuggestions(root));

  // Page-specific single-record extractors
  if (page === "article")      all.push(...extractArticlePage());
  if (page === "company")      all.push(...extractCompanyPage());
  if (page === "profile")      all.push(...extractProfilePage());
  if (page === "job_detail")   all.push(...extractJobDetail());
  if (page === "search")       all.push(...extractSearchResults(root));
  if (page === "notifications")all.push(...extractNotifications(root));
  if (page === "hashtag")      all.push(...extractHashtagContext());
  if (page === "event")        all.push(...extractEventPage());
  if (page === "messaging")    all.push(...extractMessagingThreads(root));

  // These run on every page if visible (most produce 0 matches except on their page)
  all.push(...extractJobRecommendations(root));
  all.push(...extractActivityItems(root));
  all.push(...extractSavedItems(root));
  all.push(...extractReactorsList(root));
  all.push(...extractFollowerItems(root));

  return all;
}

globalThis.LinkedInExtractor = {
  VERSION,
  detectPageType,
  scanAll,
  extractFeedPosts,
  extractComments,
  extractArticleCards,
  extractArticlePage,
  extractCompanyPage,
  extractProfilePage,
  extractJobCards,
  extractJobDetail,
  extractSearchResults,
  extractConnectionSuggestions,
  extractNotifications,
  extractHashtagContext,
  extractEventPage,
  extractJobRecommendations,
  extractMessagingThreads,
  extractActivityItems,
  extractSavedItems,
  extractReactorsList,
  extractFollowerItems,
  // v2 compatibility
  extractPosts: (root) => extractFeedPosts(root, _detectOwnHandle()),
};
