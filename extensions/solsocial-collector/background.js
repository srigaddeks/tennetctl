/**
 * SolSocial Collector — MV3 Service Worker
 *
 * Responsibilities:
 *  - Auth: signin/signout, token storage
 *  - Queue: receives captures from content scripts, persists to chrome.storage
 *  - Flush: alarm every 30s, batch-POSTs queue to TennetCTL
 *  - Status: answers popup status queries
 */

import { apiFetch, ApiError } from "./lib/api.js";
import { enqueue, drain, size } from "./lib/queue.js";

const STORAGE_AUTH_KEY = "solsocial_auth";
const FLUSH_ALARM = "solsocial_flush";
const FLUSH_INTERVAL_MINUTES = 0.5; // 30 seconds

// ─── Auth helpers ──────────────────────────────────────────────────────────────

async function getAuth() {
  const { [STORAGE_AUTH_KEY]: auth } = await chrome.storage.local.get(STORAGE_AUTH_KEY);
  return auth ?? null;
}

async function setAuth(auth) {
  await chrome.storage.local.set({ [STORAGE_AUTH_KEY]: auth });
}

async function clearAuth() {
  await chrome.storage.local.remove(STORAGE_AUTH_KEY);
}

// ─── Flush ─────────────────────────────────────────────────────────────────────

async function flush() {
  const auth = await getAuth();
  if (!auth?.token || auth.enabled === false) return;

  const items = await drain();
  if (items.length === 0) return;

  try {
    await apiFetch("/v1/social/captures", {
      method: "POST",
      token: auth.token,
      baseUrl: auth.baseUrl,
      body: { captures: items.slice(0, 100) },
    });

    // If we drained more than 100, put the rest back
    if (items.length > 100) {
      await enqueue(items.slice(100));
    }

    // Update today's count in storage
    const today = new Date().toISOString().slice(0, 10);
    const storageKey = `count_${today}`;
    const { [storageKey]: prev = 0 } = await chrome.storage.local.get(storageKey);
    await chrome.storage.local.set({ [storageKey]: prev + Math.min(items.length, 100) });

  } catch (err) {
    // Put items back on failure — don't lose data
    await enqueue(items);
    if (err instanceof ApiError && err.status === 401) {
      await clearAuth();
      console.warn("[SolSocial] Token expired — please sign in again");
    } else {
      console.warn("[SolSocial] Flush failed:", err.message);
    }
  }
}

// ─── Alarm setup ───────────────────────────────────────────────────────────────

chrome.alarms.get(FLUSH_ALARM, (existing) => {
  if (!existing) {
    chrome.alarms.create(FLUSH_ALARM, { periodInMinutes: FLUSH_INTERVAL_MINUTES });
  }
});

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === FLUSH_ALARM) flush();
});

// ─── Message router ────────────────────────────────────────────────────────────

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  handle(msg).then(sendResponse).catch((err) => sendResponse({ ok: false, error: err.message }));
  return true; // keep channel open for async response
});

async function handle(msg) {
  switch (msg.type) {
    case "signin": {
      const data = await apiFetch("/v1/auth/signin", {
        method: "POST",
        baseUrl: msg.baseUrl || "http://localhost:51734",
        body: { email: msg.email, password: msg.password },
      });
      await setAuth({
        token: data.token,
        user: data.user,
        session: data.session,
        baseUrl: msg.baseUrl || "http://localhost:51734",
        enabled: true,
      });
      return { ok: true, user: data.user };
    }

    case "signout": {
      const auth = await getAuth();
      if (auth?.token) {
        try {
          await apiFetch("/v1/auth/signout", {
            method: "POST",
            token: auth.token,
            baseUrl: auth.baseUrl,
          });
        } catch { /* best effort */ }
      }
      await clearAuth();
      return { ok: true };
    }

    case "toggle": {
      const auth = await getAuth();
      if (!auth) return { ok: false, error: "not signed in" };
      auth.enabled = !auth.enabled;
      await setAuth(auth);
      return { ok: true, enabled: auth.enabled };
    }

    case "enqueue": {
      const auth = await getAuth();
      if (!auth?.token || auth.enabled === false) return { ok: true, skipped: true };
      const qsize = await enqueue(msg.captures);
      return { ok: true, queued: qsize };
    }

    case "flush": {
      await flush();
      return { ok: true };
    }

    case "status": {
      const auth = await getAuth();
      const today = new Date().toISOString().slice(0, 10);
      const storageKey = `count_${today}`;
      const { [storageKey]: todayCount = 0 } = await chrome.storage.local.get(storageKey);
      const queueSize = await size();
      return {
        ok: true,
        signedIn: !!auth?.token,
        enabled: auth?.enabled ?? false,
        user: auth?.user ?? null,
        todayCount,
        queueSize,
        baseUrl: auth?.baseUrl ?? "http://localhost:51734",
      };
    }

    default:
      return { ok: false, error: `unknown message type: ${msg.type}` };
  }
}
