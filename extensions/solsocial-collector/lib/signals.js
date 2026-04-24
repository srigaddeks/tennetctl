/**
 * Behavior + session instrumentation.
 *
 * Produces capture events that reflect what the user *actually* engaged with,
 * not just what the DOM rendered. These are pure observation — we never fire
 * synthetic events on the page. We only listen to genuine user actions:
 *   • IntersectionObserver → post_dwell (in viewport ≥ 1500ms)
 *   • click events → post_clicked
 *   • selection events → text_selected
 *   • copy events → text_copied
 *   • HTMLMediaElement 'play' → video_played
 *   • mouseenter+mouseleave on outbound links → link_hovered (≥ 800ms)
 *   • page navigation → page_visit (+ session id)
 *
 * Every event carries:
 *   • session_id (stable per tab load, regenerated on F5)
 *   • parent_post_id when the event is anchored to a feed post
 *   • dom path of the element (first two classnames) for debugging
 *
 * All outputs go through the same chrome.runtime.sendMessage({type:'enqueue'})
 * path as content captures — shared dedup + rate limiting.
 */

const SIGNALS_VERSION = "signals-v1";
const DWELL_MS = 1500;
const HOVER_MS = 800;

// ── Session id — one per tab load (F5 regenerates) ──────────────────────────
function _uuid() {
  // tiny v7-ish UUID; good enough for session correlation, not for auth
  const h = (n) => n.toString(16).padStart(2, "0");
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = Array.from(bytes, h).join("");
  return `${hex.slice(0,8)}-${hex.slice(8,12)}-${hex.slice(12,16)}-${hex.slice(16,20)}-${hex.slice(20)}`;
}
const SESSION_ID = _uuid();
const SESSION_START = Date.now();

function _enqueue(captures) {
  if (!captures.length) return;
  try {
    chrome.runtime.sendMessage({ type: "enqueue", captures }, () => {
      if (chrome.runtime.lastError) { /* silent */ }
    });
  } catch (_) {}
}

function _cardUrn(el) {
  const anc = el?.closest?.("[data-urn^='urn:li:activity:'], article[data-testid='tweet']");
  if (!anc) return null;
  if (anc.hasAttribute("data-urn")) return anc.getAttribute("data-urn");
  // Twitter: build a pseudo-urn from the status link
  const statusLink = anc.querySelector("a[href*='/status/']");
  const m = statusLink?.getAttribute("href")?.match(/\/status\/(\d+)/);
  return m ? `x:status:${m[1]}` : null;
}

function _platformFromUrl(u = location.href) {
  if (/linkedin\.com/.test(u)) return "linkedin";
  if (/twitter\.com|x\.com/.test(u)) return "x";
  return null;
}

function _domPath(el) {
  if (!el) return null;
  const parts = [];
  let cur = el;
  while (cur && parts.length < 4 && cur.tagName) {
    const cls = (cur.className && typeof cur.className === "string") ? cur.className.split(/\s+/).slice(0, 2).join(".") : "";
    parts.push(cur.tagName.toLowerCase() + (cls ? "." + cls : ""));
    cur = cur.parentElement;
  }
  return parts.join(" > ");
}

function _baseEvent(type, el, extra = {}) {
  const platform = _platformFromUrl();
  if (!platform) return null;
  return {
    platform,
    type,
    platform_post_id: `${type}:${SESSION_ID}:${Date.now()}:${Math.random().toString(36).slice(2, 6)}`,
    observed_at: new Date().toISOString(),
    extractor_version: SIGNALS_VERSION,
    author_handle: null,
    author_name: null,
    text_excerpt: null,
    url: location.href,
    like_count: null, reply_count: null, repost_count: null, view_count: null,
    is_own: false,
    raw_attrs: {
      session_id: SESSION_ID,
      session_age_ms: Date.now() - SESSION_START,
      page_url: location.href,
      page_title: document.title,
      referrer: document.referrer || null,
      page_type: extra.page_type || null,
      dom_path: _domPath(el),
      ...extra,
    },
  };
}

// ── IntersectionObserver: dwell-time on posts ───────────────────────────────

const dwellState = new WeakMap();           // el → { enteredAt, timer }
const emittedDwell = new Set();              // urn → true (dedup per session)

const dwellObserver = new IntersectionObserver((entries) => {
  for (const ent of entries) {
    const el = ent.target;
    if (ent.isIntersecting && ent.intersectionRatio > 0.5) {
      if (!dwellState.has(el)) {
        const urn = _cardUrn(el);
        const timer = setTimeout(() => {
          if (!urn || emittedDwell.has(urn)) return;
          emittedDwell.add(urn);
          const ev = _baseEvent("post_dwell", el, {
            post_urn: urn,
            dwell_ms: DWELL_MS,
            intersection_ratio: ent.intersectionRatio,
          });
          if (ev) _enqueue([ev]);
        }, DWELL_MS);
        dwellState.set(el, { enteredAt: Date.now(), timer, urn });
      }
    } else {
      const s = dwellState.get(el);
      if (s) { clearTimeout(s.timer); dwellState.delete(el); }
    }
  }
}, { threshold: [0, 0.5, 1] });

function observeDwellTargets(root = document) {
  // Feed post cards + tweet articles
  const targets = root.querySelectorAll(
    "[data-urn^='urn:li:activity:'], " +
    "div.feed-shared-update-v2, " +
    "article[data-testid='tweet']"
  );
  for (const t of targets) {
    try { dwellObserver.observe(t); } catch (_) {}
  }
}

// Re-observe on DOM mutations (infinite scroll)
const dwellMO = new MutationObserver(() => observeDwellTargets(document));
dwellMO.observe(document.body, { childList: true, subtree: true });
observeDwellTargets(document);

// ── Click-through: what did the user actually click? ────────────────────────

document.addEventListener("click", (e) => {
  const link = e.target.closest?.("a[href]");
  if (!link) return;
  const href = link.getAttribute("href") || "";
  if (!href || href.startsWith("javascript:")) return;
  const card = link.closest("[data-urn^='urn:li:activity:'], article[data-testid='tweet']");
  const ev = _baseEvent("post_clicked", link, {
    clicked_url: new URL(href, location.origin).href,
    clicked_text: (link.textContent || "").replace(/\s+/g, " ").trim().slice(0, 200),
    opened_in_new_tab: e.metaKey || e.ctrlKey || e.button === 1,
    is_external: !href.startsWith("/") && !href.includes(location.host),
    parent_post_id: card ? _cardUrn(card) : null,
  });
  if (ev) _enqueue([ev]);
}, true);

// ── Selection: text the user highlighted ────────────────────────────────────

let _selTimer = null;
document.addEventListener("selectionchange", () => {
  clearTimeout(_selTimer);
  _selTimer = setTimeout(() => {
    const sel = document.getSelection();
    const text = sel?.toString?.() || "";
    if (!text || text.length < 10) return;       // ignore trivial selections
    if (text.length > 4096) return;               // ignore pathological
    const anchorEl = sel.anchorNode?.parentElement || null;
    const card = anchorEl?.closest("[data-urn^='urn:li:activity:'], article[data-testid='tweet']");
    const ev = _baseEvent("text_selected", anchorEl, {
      selected_text: text.slice(0, 2048),
      char_count: text.length,
      parent_post_id: card ? _cardUrn(card) : null,
    });
    if (ev) {
      ev.text_excerpt = text.slice(0, 512);
      _enqueue([ev]);
    }
  }, 1200);  // debounce — only emit when selection settles
}, true);

// ── Copy: user executed copy on selected text ───────────────────────────────

document.addEventListener("copy", () => {
  const sel = document.getSelection();
  const text = sel?.toString?.() || "";
  if (!text) return;
  const anchorEl = sel.anchorNode?.parentElement || null;
  const card = anchorEl?.closest("[data-urn^='urn:li:activity:'], article[data-testid='tweet']");
  const ev = _baseEvent("text_copied", anchorEl, {
    copied_text: text.slice(0, 2048),
    char_count: text.length,
    parent_post_id: card ? _cardUrn(card) : null,
  });
  if (ev) {
    ev.text_excerpt = text.slice(0, 512);
    _enqueue([ev]);
  }
}, true);

// ── Video played: any <video> element in a post fires 'play' ───────────────

document.addEventListener("play", (e) => {
  const video = e.target;
  if (!(video instanceof HTMLMediaElement)) return;
  const card = video.closest?.("[data-urn^='urn:li:activity:'], article[data-testid='tweet']");
  const ev = _baseEvent("video_played", video, {
    video_src: video.currentSrc || video.getAttribute("src") || null,
    poster: video.getAttribute("poster") || null,
    duration: Number.isFinite(video.duration) ? video.duration : null,
    parent_post_id: card ? _cardUrn(card) : null,
  });
  if (ev) _enqueue([ev]);
}, true);

// ── Link hover (≥ HOVER_MS) → mild intent signal ───────────────────────────

const hoverTimers = new WeakMap();
document.addEventListener("mouseenter", (e) => {
  const link = e.target.closest?.("a[href]");
  if (!link) return;
  const href = link.getAttribute("href") || "";
  if (!href || href.startsWith("javascript:") || href.startsWith("#")) return;
  // Skip internal nav-style links to reduce noise; only record outbound hovers.
  if (!/^https?:\/\//.test(href) && !/lnkd\.in|t\.co/.test(href)) return;
  const t = setTimeout(() => {
    const card = link.closest("[data-urn^='urn:li:activity:'], article[data-testid='tweet']");
    const ev = _baseEvent("link_hovered", link, {
      hovered_url: new URL(href, location.origin).href,
      hover_ms: HOVER_MS,
      link_text: (link.textContent || "").trim().slice(0, 160),
      parent_post_id: card ? _cardUrn(card) : null,
    });
    if (ev) _enqueue([ev]);
  }, HOVER_MS);
  hoverTimers.set(link, t);
}, true);

document.addEventListener("mouseleave", (e) => {
  const link = e.target.closest?.("a[href]");
  const t = hoverTimers.get(link);
  if (t) { clearTimeout(t); hoverTimers.delete(link); }
}, true);

// ── Page visits — URL changes within the SPA ───────────────────────────────

let _lastPageUrl = null;
function emitPageVisit() {
  if (_lastPageUrl === location.href) return;
  _lastPageUrl = location.href;
  const ev = _baseEvent("page_visit", document.body, {
    page_type: (globalThis.LinkedInExtractor?.detectPageType?.() ??
                globalThis.TwitterExtractor?.detectPageType?.() ?? "unknown"),
    meta_description: document.querySelector("meta[name='description']")?.getAttribute("content") || null,
    og_title:         document.querySelector("meta[property='og:title']")?.getAttribute("content") || null,
    og_description:   document.querySelector("meta[property='og:description']")?.getAttribute("content") || null,
  });
  if (ev) {
    ev.text_excerpt = document.title?.slice(0, 512) || null;
    _enqueue([ev]);
  }
}

// Patch pushState/replaceState — SPA routing
(function patchHistory() {
  const push = history.pushState;
  history.pushState = function () { const r = push.apply(this, arguments); setTimeout(emitPageVisit, 200); return r; };
  const rep = history.replaceState;
  history.replaceState = function () { const r = rep.apply(this, arguments); setTimeout(emitPageVisit, 200); return r; };
  window.addEventListener("popstate", () => setTimeout(emitPageVisit, 200));
})();

// Fire once on load
setTimeout(emitPageVisit, 1000);

// Expose for debugging
globalThis.SolSocialSignals = {
  version: SIGNALS_VERSION,
  session_id: SESSION_ID,
  emitPageVisit,
};
