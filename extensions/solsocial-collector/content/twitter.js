/**
 * Twitter / X content script.
 * Observes the feed for new tweets and enqueues captures.
 */

// ─── Own-handle detection ─────────────────────────────────────────────────────

let ownHandle = null;

function detectOwnHandle() {
  // Account switcher button has the logged-in handle in aria-label
  const switcher = document.querySelector("[data-testid='SideNav_AccountSwitcher_Button']");
  if (switcher) {
    const label = switcher.getAttribute("aria-label") || "";
    // "Account menu; logged in as @elonmusk" or similar
    const match = label.match(/@([A-Za-z0-9_]+)/);
    if (match) { ownHandle = match[1]; return; }
  }
  // Fallback: profile link in nav
  const profileLink = document.querySelector("a[data-testid='AppTabBar_Profile_Link']");
  if (profileLink) {
    const href = profileLink.getAttribute("href") || "";
    const match = href.match(/^\/([A-Za-z0-9_]+)$/);
    if (match) ownHandle = match[1];
  }
}

// ─── Seen dedup ───────────────────────────────────────────────────────────────

const seenTweetIds = new Set();

function isInViewport(el) {
  const rect = el.getBoundingClientRect();
  return rect.top < window.innerHeight && rect.bottom > 0;
}

// ─── Scan ─────────────────────────────────────────────────────────────────────

function scanAndEnqueue() {
  const tweets = TwitterExtractor.extractTweets(document);
  const fresh = [];

  for (const tweet of tweets) {
    if (seenTweetIds.has(tweet.platform_post_id)) continue;
    // Only capture tweets currently in viewport
    const article = document.querySelector(`article[data-testid='tweet'] a[href*='/status/${tweet.platform_post_id}']`)
      ?.closest("article");
    if (article && !isInViewport(article)) continue;

    seenTweetIds.add(tweet.platform_post_id);

    if (ownHandle && tweet.author_handle?.toLowerCase() === ownHandle.toLowerCase()) {
      tweet.is_own = true;
    }

    fresh.push(tweet);
  }

  if (fresh.length > 0) {
    chrome.runtime.sendMessage({ type: "enqueue", captures: fresh });
  }
}

function debounce(fn, ms) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

const debouncedScan = debounce(scanAndEnqueue, 600);

// ─── Own-tweet detection (compose submit) ────────────────────────────────────

document.addEventListener("click", (e) => {
  const btn = e.target.closest("[data-testid='tweetButtonInline'], [data-testid='tweetButton']");
  if (!btn) return;
  // After submit, next new tweet from own handle in feed = own_post_published
  setTimeout(() => {
    const tweets = TwitterExtractor.extractTweets(document);
    for (const tweet of tweets) {
      if (ownHandle && tweet.author_handle?.toLowerCase() === ownHandle.toLowerCase()
          && !seenTweetIds.has(tweet.platform_post_id)) {
        seenTweetIds.add(tweet.platform_post_id);
        tweet.is_own = true;
        tweet.type = "own_post_published";
        chrome.runtime.sendMessage({ type: "enqueue", captures: [tweet] });
      }
    }
  }, 2500);
}, true);

// ─── MutationObserver ─────────────────────────────────────────────────────────

detectOwnHandle();
setTimeout(detectOwnHandle, 3000);

const observer = new MutationObserver(debouncedScan);
observer.observe(document.body, { childList: true, subtree: true });

setTimeout(scanAndEnqueue, 1500);
