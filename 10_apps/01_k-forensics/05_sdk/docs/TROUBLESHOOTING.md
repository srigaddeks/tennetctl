# K-Protect Troubleshooting Guide

> Common issues, fallback behaviors, and debugging techniques.  
> For integration steps see [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) or [SDK_INTEGRATION.md](SDK_INTEGRATION.md).

---

## Enable Debug Logging

```ts
KProtect.init({
  api_key: 'kp_test_abc123',
  overrides: { environment: 'debug' },
});
```

Debug mode logs to the browser console:
- Session lifecycle events (start, end, idle, resume)
- Batch assembly and transmission (success/failure)
- Username detection attempts
- Critical action staging and commit
- Worker communication messages
- Page gating decisions

Use the **dev bundle** (`kprotect.dev.js`) during development for source maps and readable stack traces.

---

## Verify the SDK is Running

Open browser DevTools console:

```js
// Check session state
KProtect.getSessionState()
// → { session_id: "...", pulse: 5, page_class: "normal", identity_captured: true, ... }

// Check latest drift score (null until first batch response)
KProtect.getLatestDrift()

// Export audit log to see all SDK actions
const log = await KProtect.exportAuditLog();
console.table(log);
```

In the Network tab, look for `POST /v1/behavioral/ingest` requests every ~5 seconds after a username has been captured.

---

## Common Issues

### No batches sent after init

**Symptom:** SDK initialized but no network requests visible.

**Cause:** Transport is gated OFF until a username is captured.

**Fix:**
1. Type in a login field that matches the configured selectors, then blur (click away)
2. Or set the SSO global: `window.__KP_USER__ = 'user@example.com'`
3. Or configure custom selectors in `overrides.identity.username.selectors`

**Verify:** `KProtect.getSessionState()?.identity_captured` should be `true`.

---

### "consent required" status / SDK not starting

**Symptom:** `KProtect.init()` returns without starting the SDK.

**Cause:** Consent mode is `opt-in` and consent has not been granted.

**Fix:**
```ts
KProtect.consent.grant();
KProtect.init({ api_key: '...' }); // Now starts
```

**Verify:** `KProtect.consent.state()` should return `'granted'`.

---

### Worker spawn failed / main-thread fallback active

**Symptom:** Console shows `[KProtect] Worker spawn failed, using main-thread fallback` (debug mode).

**Cause:** CSP blocks `worker-src blob:`, or the browser doesn't support Workers in this context.

**Fix:** Add to your CSP header:
```
worker-src blob:;
```

**Impact if not fixed:** The SDK runs on the main thread via `requestIdleCallback` scheduling. All functionality is preserved, but:
- Feature extraction shares the main thread (runs during idle periods)
- May add ~1-2ms of main-thread work per 5s extraction window
- Performance impact is negligible for most applications

**How to detect:** `KProtect.getSessionState()` includes `worker_mode` in the batch metadata. In debug mode, check the `sdk.worker_mode` field in network requests — `'fallback_main_thread'` indicates the fallback is active.

---

### Username not detected

**Symptom:** `identity_captured` remains `false` after typing in login fields.

**Causes:**
1. Field doesn't match default selectors (`input[name="username"]`, `input[name="email"]`, `input[name="phoneNumber"]`)
2. Field is on a URL that doesn't match `/login` or `/signup`
3. SSO flow — username never typed into a form

**Fix — Custom selectors:**
```ts
KProtect.init({
  api_key: '...',
  overrides: {
    identity: {
      username: {
        selectors: [
          { selector: 'input#myCustomField', url: '/auth', event: 'blur' },
        ],
      },
    },
  },
});
```

**Fix — SSO:**
```ts
window.__KP_USER__ = authenticatedUser.email;
```

---

### Drift scores always null

**Symptom:** `KProtect.getLatestDrift()` returns `null` even after batches are sent.

**Causes:**
1. Server not running or unreachable
2. Invalid API key
3. User has insufficient baseline (< 5 sessions)

**Debug:**
- Check Network tab for response status codes on `/v1/behavioral/ingest`
- A `401` indicates an invalid API key
- A response with `baseline_quality: "insufficient"` and `drift_score: null` is normal for new users — the baseline needs 5-15 sessions to form

---

### Batches rejected with BATCH_TOO_OLD

**Symptom:** Server returns `400` with error code `BATCH_TOO_OLD`.

**Cause:** The `sent_at` timestamp in the batch is more than 5 minutes away from server time.

**Fix:** Ensure the client's system clock is reasonably accurate (within 5 minutes of UTC). This is a server-side validation to prevent replay attacks.

---

### IndexedDB errors in console

**Symptom:** IDB-related errors in the console, possibly in private/incognito mode.

**Impact:** None on SDK functionality. The SDK degrades gracefully:
- Username and device UUID fall back to localStorage-only storage
- TTL enforcement may be less precise
- All behavioral collection and transmission continues normally

**Why:** Some browsers restrict IndexedDB in private browsing mode. The SDK catches all IDB errors silently and falls back to localStorage.

---

## Liveness Detection

The SDK tracks whether the user is actively interacting with the page:

| Status | Meaning | Threshold |
|---|---|---|
| `alive` | Events received within the last 30 seconds | < 30s since last event |
| `stale` | No events for 30+ seconds (user idle but tab visible) | >= 30s, session active |
| `dead` | Session ended or not yet started | Session terminated |

**Check via:**
```js
KProtect.getSessionState()?.liveness_status
// → 'alive' | 'stale' | 'dead'
```

A `stale` status triggers a `STATE_UPDATE` message to the main thread, which fires any registered `session_state` event handlers.

---

## Storage Inspection

All SDK storage keys are namespaced under `kp.`:

**localStorage:**
```js
// View all K-Protect keys
Object.keys(localStorage).filter(k => k.startsWith('kp.'))
// → ['kp.un', 'kp.did', 'kp.us', 'kp.consent', 'kp.cfg']
```

**sessionStorage:**
```js
sessionStorage.getItem('kp.sid')  // Current session UUID (per-tab)
```

**IndexedDB:** Open DevTools → Application → IndexedDB → `kp-bio` → `kv` store.

---

## Performance Profiling

The SDK is designed to have minimal main-thread impact:

| Budget | Target |
|---|---|
| Main thread blocking after `init()` | < 1ms per event tap |
| Total main-thread work in 10s typing session | < 50ms |
| Main bundle (gzip) | < 15 KB |
| Worker bundle (gzip) | < 40 KB |

**To verify:**

1. Open DevTools → Performance tab
2. Record a 10-second typing session
3. Filter for `KProtect` or `kprotect` in the flame chart
4. Main-thread frames should show only passive event listener callbacks (< 0.1ms each)

If the main-thread fallback is active, you may see `requestIdleCallback` work items of 1-2ms during idle periods — this is normal.

---

## Reset Everything

To completely clear all SDK state and start fresh:

```ts
// Option 1: Via SDK API (recommended)
await KProtect.gdpr.delete();

// Option 2: Manual (when SDK is not loaded)
['kp.un', 'kp.did', 'kp.us', 'kp.consent', 'kp.cfg', 'kp.k'].forEach(k => localStorage.removeItem(k));
sessionStorage.removeItem('kp.sid');
indexedDB.deleteDatabase('kp-bio');
```

---

*Last updated: 2026-04-09 — K-Protect Engineering*
