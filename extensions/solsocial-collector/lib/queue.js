/**
 * chrome.storage.local–backed capture queue.
 * The MV3 service worker can be evicted at any time, so the queue
 * must survive that — it lives entirely in chrome.storage.local.
 */

const QUEUE_KEY = "solsocial_queue";
const MAX_QUEUE_SIZE = 500;

export async function enqueue(captures) {
  const { [QUEUE_KEY]: existing = [] } = await chrome.storage.local.get(QUEUE_KEY);
  const merged = [...existing, ...captures].slice(-MAX_QUEUE_SIZE);
  await chrome.storage.local.set({ [QUEUE_KEY]: merged });
  return merged.length;
}

export async function drain() {
  const { [QUEUE_KEY]: items = [] } = await chrome.storage.local.get(QUEUE_KEY);
  if (items.length === 0) return [];
  await chrome.storage.local.set({ [QUEUE_KEY]: [] });
  return items;
}

export async function size() {
  const { [QUEUE_KEY]: items = [] } = await chrome.storage.local.get(QUEUE_KEY);
  return items.length;
}
