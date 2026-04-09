# K-Protect Web SDK — Integration Guide

## Quick Start

One line of code. No per-page configuration.

```html
<!-- Production -->
<script src="https://cdn.kprotect.io/v1/kprotect.min.js"></script>
<script>
  KProtect.init({ api_key: 'kp_live_YOUR_KEY' });
</script>
```

That's it. The SDK handles everything else automatically:
- Session management (per-tab, survives SPA navigation)
- Username detection (auto-scans login/signup forms)
- Behavioral signal collection (keystroke, pointer, scroll, touch)
- Device fingerprinting (canvas, audio, WebGL, fonts, battery)
- Drift scoring (real-time, per-pulse batch transmission)
- Critical action detection (login, payment, transfer pages)
- Graceful degradation (CSP fallback, no-crypto fallback, silent errors)

---

## SDK Bundles

The build produces two bundles for different deployment stages:

| Bundle | File | Size | Debug logs | Source maps | Obfuscated | Use for |
|--------|------|------|-----------|-------------|------------|---------|
| **Dev** | `kprotect.dev.js` | ~120KB | Yes | Yes | No | Development, staging, QA |
| **Prod** | `kprotect.min.js` | ~45KB | No | No | Yes | Production deployments |

### Building

```bash
cd packages/sdk-web

# Build both dev + prod bundles
npm run build

# Build only dev (fast, with sourcemaps + debug logs)
npm run build:dev

# Build only prod (minified, obfuscated, no console output)
npm run build:prod
```

### Output files

```
dist/
  kprotect.dev.js        # Dev bundle — debug logs, readable, sourcemaps
  kprotect.dev.js.map    # Source map for dev bundle
  kprotect.min.js        # Prod bundle — minified, obfuscated, no console
  kprotect.esm.js        # ES module (for bundler imports)
  kprotect.esm.js.map    # Source map for ESM
  kprotect.worker.js     # Worker bundle (inlined into main bundles)
```

---

## Installation Methods

### Script tag (recommended for most sites)

```html
<!-- Dev / staging -->
<script src="/path/to/kprotect.dev.js"></script>

<!-- Production -->
<script src="/path/to/kprotect.min.js"></script>

<script>
  KProtect.init({ api_key: 'kp_live_abc123' });
</script>
```

### npm / ES module

```bash
npm install @kprotect/sdk-web
```

```ts
import { KProtect } from '@kprotect/sdk-web';

KProtect.init({ api_key: 'kp_live_abc123' });
```

### Next.js / React

```tsx
// app/layout.tsx
import Script from 'next/script';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Script src="/kprotect.min.js" strategy="afterInteractive" />
        <Script id="kp-init" strategy="afterInteractive">
          {`KProtect.init({ api_key: 'kp_live_abc123' });`}
        </Script>
      </body>
    </html>
  );
}
```

---

## Configuration

Only `api_key` is required. Everything else has safe defaults.

```ts
KProtect.init({
  api_key: 'kp_live_abc123',

  overrides: {
    // Environment — 'production' (default) or 'debug'
    // Debug mode enables console logging for development
    environment: 'debug',

    // Transport
    transport: {
      // 'direct' (default) or 'proxy'
      mode: 'direct',
      // Only needed for proxy mode — route through your backend
      proxy_endpoint: '/api/kp-proxy',
    },

    // Consent (GDPR/CCPA)
    consent: {
      // 'opt-out' (default) — SDK runs unless user denies
      // 'opt-in'  — SDK blocked until user grants consent
      // 'none'    — no consent check (non-regulated environments)
      mode: 'opt-in',
    },

    // Device fingerprinting
    fingerprinting: {
      // Set to false to disable device fingerprinting entirely
      enabled: true,
    },

    // Session timing
    session: {
      pulse_interval_ms: 5000,       // Behavioral batch cadence (default: 5s)
      idle_timeout_ms: 900000,       // Session ends after 15min idle
      keepalive_interval_ms: 30000,  // Critical action keepalive (default: 30s)
    },

    // Username detection — auto-scans these selectors on matching URLs
    identity: {
      username: {
        selectors: [
          { selector: 'input[name="username"]', url: '/login', event: 'blur' },
          { selector: 'input[name="email"]',    url: '/login', event: 'blur' },
        ],
        // SSO globals — SDK polls these window properties for username
        sso_globals: ['__KP_USER__', '__SSO_USER__'],
      },
    },

    // Critical action pages — SDK switches to staging mode on these pages
    critical_actions: {
      actions: [
        { page: /\/login/,    action: 'login_submit',     commit: { selector: 'button[type="submit"]' } },
        { page: /\/transfer/, action: 'transfer_confirm', commit: { selector: '[data-kp-commit="transfer"]' } },
        { page: /\/payment/,  action: 'payment_confirm',  commit: { selector: '[data-kp-commit="payment"]' } },
      ],
    },

    // Pages to exclude from collection
    page_gate: {
      opt_out_patterns: ['/help', '/faq', /\/static\/.*/],
    },
  },
});
```

---

## Public API

### Core

```ts
// Initialize — only required call
KProtect.init({ api_key: 'kp_live_abc123' });

// Listen for drift assessments
const off = KProtect.on('drift', (data) => {
  const drift = data as DriftScoreResponse;
  if (drift.action === 'challenge') showMfaPrompt();
});
off(); // Unsubscribe

// Get latest drift score
const drift = KProtect.getLatestDrift();

// Get session state
const state = KProtect.getSessionState();

// User logged out — clears username, keeps device fingerprint
KProtect.logout();

// Full teardown — stops SDK, optionally wipes all identity
KProtect.destroy();
KProtect.destroy({ clearIdentity: true }); // Also wipes device_uuid
```

### Events

```ts
KProtect.on('drift',            (data) => { /* DriftScoreResponse */ });
KProtect.on('alert',            (data) => { /* AlertData[] */ });
KProtect.on('critical_action',  (data) => { /* CriticalActionEvent */ });
KProtect.on('session_start',    (data) => { /* { session_id, pulse } */ });
KProtect.on('session_end',      (data) => { /* SessionEndEvent */ });
KProtect.on('username_captured',(data) => { /* { user_hash } */ });
```

### Consent (GDPR/CCPA)

```ts
// Check current consent state
KProtect.consent.state(); // 'granted' | 'denied' | 'unknown'

// Grant consent — SDK starts collecting on next init()
KProtect.consent.grant();
KProtect.init({ api_key: '...' }); // Now starts

// Deny consent — stops SDK immediately if running
KProtect.consent.deny();
```

### Audit Log (SOC 2)

```ts
// Export tamper-evident audit log
const log = await KProtect.exportAuditLog();
// Returns: Array<{ seq, timestamp, action, detail, prev_hash }>
// Actions: sdk_init, session_start, session_end, username_captured,
//          batch_sent, batch_failed, fingerprint_collected, logout, destroy
```

---

## Critical Action Pages

For high-risk pages (login, payment, transfer), add `data-kp-commit` to the submit button:

```html
<!-- Payment page -->
<button type="submit" data-kp-commit="payment">Confirm Payment</button>

<!-- Transfer page -->
<button type="submit" data-kp-commit="transfer">Send Wire Transfer</button>
```

The SDK automatically:
1. Switches to staging mode when the user navigates to a critical page
2. Buffers behavioral data in a staging buffer (not sent yet)
3. On commit click: sends a `critical_action` batch with `committed: true`
4. On navigation away without clicking: sends with `committed: false` (abandoned)

No additional SDK calls required.

---

## SSO Integration

For SSO/OAuth flows where the username isn't typed into a form:

```ts
// Option 1: Set a global before SDK init
window.__KP_USER__ = ssoResponse.email;

// Option 2: Set after SSO callback (SDK polls for it)
auth.onLogin((user) => {
  window.__KP_USER__ = user.email;
});
```

The SDK auto-detects globals listed in `identity.username.sso_globals`.

---

## Security Features

All security is automatic — no integration code required.

| Feature | What it does | Integrator action |
|---------|-------------|-------------------|
| HMAC auth | API key never sent in headers — HMAC-derived token instead | None |
| PBKDF2 username hash | 100k-iteration salted hash, not reversible | None |
| Differential privacy | Laplace noise on keystroke zone matrix | None |
| MessageChannel | Private worker communication, unforgeable | None |
| Consent gate | Blocks SDK until consent granted (opt-in mode) | Configure `consent.mode` |
| Audit trail | Hash-chained log of all SDK actions | Call `exportAuditLog()` for SOC 2 |

---

## Content Security Policy

The SDK spawns a Web Worker via blob URL. Add this CSP directive:

```
worker-src blob:;
```

If `worker-src blob:` is blocked, the SDK automatically falls back to running
on the main thread via `requestIdleCallback` — no functionality is lost.

---

## Browser Support

| Browser | Version | Notes |
|---------|---------|-------|
| Chrome | 80+ | Full support |
| Firefox | 78+ | Full support |
| Safari | 14+ | Full support |
| Edge | 80+ | Full support (Chromium) |
| Mobile Safari | 14+ | Touch signals included |
| Chrome Android | 80+ | Touch + sensor signals |

The SDK gracefully degrades on older browsers:
- No `crypto.subtle` → username hashing disabled, batches sent unsigned
- No `CompressionStream` → batches sent as plain JSON
- No `requestIdleCallback` → falls back to `setTimeout`
- No Web Workers → main-thread fallback via idle scheduling

---

## Troubleshooting

### Dev mode — enable debug logs

```ts
KProtect.init({
  api_key: 'kp_test_abc123',
  overrides: { environment: 'debug' },
});
```

Debug mode logs to the browser console:
- Session lifecycle events
- Batch send success/failure
- Username detection events
- Critical action staging
- Worker communication

### Verify SDK is running

```js
// In browser console:
KProtect.getSessionState()
// → { session_id: "...", pulse: 5, page_class: "normal", username_captured: true, ... }
```

### Check audit log

```js
const log = await KProtect.exportAuditLog();
console.table(log);
```

### Common issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| SDK silent, no batches | Missing `api_key` | Pass `api_key` to `init()` |
| No batches after init | Username not captured yet | Type in a login field, or set `window.__KP_USER__` |
| `consent required` status | Using `opt-in` consent mode | Call `KProtect.consent.grant()` before `init()` |
| Worker spawn failed | CSP blocks `worker-src blob:` | Add `worker-src blob:` to CSP, or accept main-thread fallback |
| No drift scores | Server not configured | Check server endpoint and API key validity |

---

## Storage Keys

The SDK uses these browser storage keys (all namespaced under `kp.`):

| Key | Storage | Contains | Lifetime |
|-----|---------|----------|----------|
| `kp.sid` | sessionStorage | Session UUID | Tab close |
| `kp.un` | localStorage | Username (for re-capture on reload) | Until `logout()` |
| `kp.did` | localStorage + IndexedDB | Device UUID | Until `destroy({ clearIdentity: true })` |
| `kp.us` | localStorage | PBKDF2 salt (hex) | Permanent (per-device) |
| `kp.consent` | localStorage | Consent state + timestamp | Until cleared |
| `kp.cfg` | localStorage | Merged config cache | Until `destroy()` |

---

## Size Budget

| Bundle | Target | Actual |
|--------|--------|--------|
| Main (prod, gzip) | < 15 KB | TBD after first build |
| Worker (prod, gzip) | < 40 KB | TBD after first build |
| Main (dev, uncompressed) | < 150 KB | ~120 KB |
