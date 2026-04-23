/**
 * LinkedIn content script.
 * Observes the feed for new posts and enqueues captures via the background worker.
 */

// ─── Own-handle detection ─────────────────────────────────────────────────────

let ownHandle = null;

function detectOwnHandle() {
  // Profile photo link in the global nav points to the logged-in user's profile
  const navLink = document.querySelector(
    "a[href*='/in/'][data-control-name='identity_profile_photo']" +
    ", .global-nav__me a[href*='/in/']" +
    ", a[href^='/in/'][aria-label*='profile']"
  );
  if (navLink) {
    const href = navLink.getAttribute("href") || "";
    const match = href.match(/\/in\/([^/?#]+)/);
    if (match) {
      ownHandle = match[1];
      return;
    }
  }
  // Fallback: look for "View profile" link in the sidebar
  const sidebarLink = document.querySelector(".profile-rail-card__actor-link");
  if (sidebarLink) {
    const href = sidebarLink.getAttribute("href") || "";
    const match = href.match(/\/in\/([^/?#]+)/);
    if (match) ownHandle = match[1];
  }
}

// ─── Seen-post dedup (in-memory for this page session) ───────────────────────

const seenPostIds = new Set();

// ─── Viewport check ──────────────────────────────────────────────────────────

function isInViewport(el) {
  const rect = el.getBoundingClientRect();
  return rect.top < window.innerHeight && rect.bottom > 0;
}

// ─── Scan and enqueue ─────────────────────────────────────────────────────────

function scanAndEnqueue() {
  const posts = LinkedInExtractor.extractPosts(document);
  const fresh = [];

  for (const post of posts) {
    if (seenPostIds.has(post.platform_post_id)) continue;
    const el = document.querySelector(`[data-urn='${post.platform_post_id}']`);
    if (el && !isInViewport(el)) continue;

    seenPostIds.add(post.platform_post_id);

    // Mark own posts
    if (ownHandle && post.author_handle === ownHandle) {
      post.is_own = true;
      post.type = "feed_post_seen"; // still "seen" unless freshly published
    }

    fresh.push(post);
  }

  if (fresh.length > 0) {
    chrome.runtime.sendMessage({ type: "enqueue", captures: fresh });
  }
}

// Debounce helper
function debounce(fn, ms) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

const debouncedScan = debounce(scanAndEnqueue, 600);

// ─── Own-post detection (compose submit) ─────────────────────────────────────

let pendingOwnPost = false;

document.addEventListener("click", (e) => {
  // LinkedIn's "Post" submit button inside the share modal
  const btn = e.target.closest(
    "button[data-control-name='share.post'], " +
    ".share-actions__primary-action, " +
    "button.artdeco-button--primary[type='submit']"
  );
  if (btn) pendingOwnPost = true;
}, true);

// Watch for URL change after post submit (pushState-based SPA)
let lastUrl = location.href;
function checkUrlChange() {
  if (location.href !== lastUrl) {
    lastUrl = location.href;
    if (pendingOwnPost) {
      pendingOwnPost = false;
      // Give the feed a moment to render the new post
      setTimeout(() => {
        const posts = LinkedInExtractor.extractPosts(document);
        for (const post of posts) {
          if (ownHandle && post.author_handle === ownHandle && !seenPostIds.has(post.platform_post_id)) {
            seenPostIds.add(post.platform_post_id);
            post.is_own = true;
            post.type = "own_post_published";
            chrome.runtime.sendMessage({ type: "enqueue", captures: [post] });
          }
        }
      }, 2000);
    }
  }
}
setInterval(checkUrlChange, 1000);

// ─── MutationObserver ─────────────────────────────────────────────────────────

detectOwnHandle();
setTimeout(detectOwnHandle, 3000); // retry after lazy nav loads

const observer = new MutationObserver(debouncedScan);
observer.observe(document.body, { childList: true, subtree: true });

// Initial scan
setTimeout(scanAndEnqueue, 1500);
