/**
 * LinkedIn content script — robust scanning with console feedback.
 */

let ownHandle = null;
const seenPostIds = new Set();

function detectOwnHandle() {
  const candidates = [
    document.querySelector("a[href*='/in/'][data-control-name='identity_profile_photo']"),
    document.querySelector(".global-nav__me a[href*='/in/']"),
    document.querySelector(".profile-rail-card__actor-link"),
  ];
  for (const el of candidates) {
    if (!el) continue;
    const m = (el.getAttribute("href") || "").match(/\/in\/([^/?#]+)/);
    if (m) { ownHandle = m[1]; break; }
  }
}

function scanAndEnqueue() {
  if (typeof LinkedInExtractor === "undefined") {
    console.warn("[SolSocial] LinkedInExtractor not loaded yet");
    return;
  }

  const posts = LinkedInExtractor.extractPosts(document);
  const fresh = [];

  for (const post of posts) {
    if (seenPostIds.has(post.platform_post_id)) continue;
    seenPostIds.add(post.platform_post_id);

    if (ownHandle && post.author_handle === ownHandle) {
      post.is_own = true;
    }
    fresh.push(post);
  }

  if (fresh.length > 0) {
    console.log(`[SolSocial] Enqueueing ${fresh.length} new LinkedIn posts`);
    chrome.runtime.sendMessage({ type: "enqueue", captures: fresh }, (resp) => {
      if (chrome.runtime.lastError) {
        console.warn("[SolSocial] sendMessage error:", chrome.runtime.lastError.message);
      } else {
        console.log("[SolSocial] Enqueued, queue size:", resp?.queued);
      }
    });
  } else {
    console.log(`[SolSocial] Scan: ${posts.length} posts found, ${seenPostIds.size} already seen`);
  }
}

function debounce(fn, ms) {
  let t;
  return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
}
const debouncedScan = debounce(scanAndEnqueue, 800);

// Own-post detection
let pendingOwnPost = false;
document.addEventListener("click", (e) => {
  if (e.target.closest("button.share-actions__primary-action, button[data-control-name='share.post']")) {
    pendingOwnPost = true;
  }
}, true);

let lastUrl = location.href;
setInterval(() => {
  if (location.href !== lastUrl) {
    lastUrl = location.href;
    if (pendingOwnPost) {
      pendingOwnPost = false;
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
}, 1000);

// MutationObserver — watch for new posts loading
const observer = new MutationObserver(debouncedScan);
observer.observe(document.body, { childList: true, subtree: true });

// Initial scans — staggered to catch slow-loading feeds
detectOwnHandle();
setTimeout(scanAndEnqueue, 1000);
setTimeout(scanAndEnqueue, 3000);
setTimeout(detectOwnHandle, 3000);
setTimeout(scanAndEnqueue, 6000);
