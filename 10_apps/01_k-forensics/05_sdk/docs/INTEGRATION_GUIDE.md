# K-Protect SDK Integration Guide

> For SDK developers and integrators. Covers Web, Android, and iOS.  
> See [SDK_BEST_PRACTICES.md](SDK_BEST_PRACTICES.md) for architectural rules.  
> See [WIRE_PROTOCOL.md](WIRE_PROTOCOL.md) for the complete wire format.

---

## Web SDK

### Step 1 — Install

**npm / pnpm / yarn:**
```bash
npm install @kprotect/sdk-web
```

**Script tag (CDN):**
```html
<script src="https://cdn.kprotect.io/v1/kprotect.min.js"></script>
```

### Step 2 — Initialize (one call, anywhere in your app)

```ts
import { KProtect } from '@kprotect/sdk-web';

KProtect.init({ api_key: 'kp_live_abc...' });
```

That's it. The SDK:
- Spawns a background worker
- Generates a session ID and device UUID
- Begins passive behavioral collection (keystroke, pointer, touch, scroll, sensor, credential)
- Sends behavioral batches every 30s with richer, higher-quality feature windows
- Skips near-empty windows (fewer than 10 events) to reduce noise
- Waits to transmit until a username is captured

**For most banking applications, no other configuration is needed.**

### Step 3 — Listen for results (optional)

```ts
KProtect.on('drift', (score) => {
  console.log('Drift score:', score.drift_score);
  if (score.action === 'block') {
    // Trigger step-up auth
    showMFAChallenge();
  }
});

KProtect.on('alert', (alert) => {
  // High-confidence fraud signal — handle immediately
  reportFraudAlert(alert);
});

KProtect.on('critical_action', (result) => {
  // Payment/transfer behavioral result received
  if (result.action === 'challenge') {
    triggerFrictionlessChallenge();
  }
});
```

### Step 4 — Handle logout

```ts
// Call this when the user logs out. Clears username, ends session.
KProtect.logout();
```

### Step 5 — CSP configuration

Add these directives to your `Content-Security-Policy` header:

```
connect-src 'self' https://api.kprotect.io;
worker-src blob:;
```

That's all. No `unsafe-eval`. No `unsafe-inline`.

---

### Web SDK — Advanced Configuration

All overrides are optional. Defaults work for 80%+ of banking apps.

```ts
KProtect.init({
  api_key: 'kp_live_abc...',
  overrides: {

    // Session timing
    session: {
      pulse_interval_ms: 30000,     // How often to send behavioral batches (default 30s, range 1s–60s)
      keepalive_interval_ms: 30000, // Heartbeat on critical-action pages (5s–120s)
      idle_timeout_ms: 900000,      // 15 min: how long hidden before new session
    },

    // Custom username capture (override if your fields have non-standard names)
    identity: {
      username: {
        selectors: [
          { selector: 'input[name="userId"]',    url: '/auth/login',  event: 'blur' },
          { selector: 'input[name="accountId"]', url: '/auth/signup', event: 'blur' },
        ],
        sso: {
          globals: ['window.currentUser.sub'],  // Set this in your SSO callback
          cookieNames: ['_session_user'],
        },
      },
    },

    // Opt-out pages (no collection on these URLs)
    page_gate: {
      opt_out_patterns: ['/marketing', '/about', '/help', /^\/public\//],
    },

    // Custom critical actions (override if your URLs differ from defaults)
    critical_actions: {
      actions: [
        { page: /\/send-money/,   action: 'send_money',    commit: { selector: '#confirm-send' } },
        { page: /\/wire-transfer/, action: 'wire_transfer', commit: { selector: '[data-kp-commit="wire"]' } },
      ],
    },

    // Proxy mode (if you need to route through your own backend)
    transport: {
      mode: 'proxy',
      endpoint: 'https://api.yourbank.com/security/kp-proxy',
    },

    environment: 'production', // or 'debug' for verbose logging
  },
});
```

### Web SDK — SSO Integration

For Google Sign-In, Auth0, Okta, and similar SSO providers:

**Option A — Global variable (simplest):**
```ts
// In your SSO success callback, before or alongside KProtect.init:
window.__KP_USER__ = user.email; // or user.sub, user.id — any stable identifier
KProtect.init({ api_key: 'kp_live_abc...' });
```

**Option B — Direct capture (for late-arriving SSO state):**
```ts
// After SSO completes, the SDK auto-polls window.__KP_USER__
// If your SSO fires after init, set the global and the SDK picks it up within 1s
authClient.on('authenticated', (user) => {
  window.__KP_USER__ = user.email;
});
```

**Option C — postMessage (for SSO popup flows):**
```ts
KProtect.init({
  api_key: 'kp_live_abc...',
  overrides: {
    identity: {
      username: {
        sso: { postMessageOrigin: 'https://accounts.google.com' },
      },
    },
  },
});
```

### Web SDK — Reading Data Programmatically

```ts
// Synchronous getter — returns last cached response or null
const drift = KProtect.getLatestDrift();
if (drift) {
  const { drift_score, confidence, action } = drift;
}

// Session state
const state = KProtect.getSessionState();
// { session_id, pulse, page_class, username_captured, auth_state }

// Unsubscribe from events
const unsubscribe = KProtect.on('drift', handler);
// later:
unsubscribe();
```

### Web SDK — Active Behavioral Challenge (Phase 2 — Not Yet Implemented)

> **Note:** The Challenge API is defined in the public facade for type-checking purposes, but calling `challenge.generate()` or `challenge.verify()` will throw an error in the current release. This feature is planned for Phase 2.

For high-risk moments (e.g., unusual large transfer) — available in a future release:

```ts
const challenge = await KProtect.challenge.generate({ purpose: 'high_value_transfer' });
// Show a UI element and observe behavior on it
const result = await KProtect.challenge.verify(challenge.challenge_id, document.getElementById('challenge-input'));

if (result.passed) {
  proceedWithTransfer();
} else {
  triggerHardMFA();
}
```

### Web SDK — data-kp-commit Attribute (Recommended)

Rather than relying on button selector fragility across redesigns, add `data-kp-commit` attributes:

```html
<!-- Payment confirmation button -->
<button type="submit" data-kp-commit="payment">Confirm Payment</button>

<!-- Wire transfer button -->
<button type="submit" data-kp-commit="wire_transfer">Send Wire</button>
```

Then reference these in your config:
```ts
commit: { selector: '[data-kp-commit="payment"]' }
```

This approach survives visual redesigns because the data attribute is semantic, not positional.

---

## Android SDK

### Step 1 — Add dependency

```kotlin
// build.gradle.kts (app module)
dependencies {
    implementation("io.kprotect:sdk-android:1.0.0")
}
```

```xml
<!-- settings.gradle.kts -->
dependencyResolutionManagement {
    repositories {
        maven { url = uri("https://maven.kprotect.io/releases") }
    }
}
```

### Step 2 — Initialize in Application

```kotlin
// MyApplication.kt
class MyApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        KProtect.init(
            context = this,
            apiKey = "kp_live_abc..."
        )
    }
}
```

```xml
<!-- AndroidManifest.xml -->
<application android:name=".MyApplication" ...>
```

### Step 3 — Provide username (mandatory)

The SDK cannot auto-read text fields in all scenarios. Call `setUsername` after successful authentication:

```kotlin
// After login API response
authRepository.login(credentials).onSuccess { user ->
    KProtect.setUsername(user.accountId)
    navigateToHome()
}
```

**For field-level auto-capture (optional):**
```kotlin
// Attach to your login field
KProtect.attachUsernameField(
    field = binding.usernameEditText,
    url = "/login"  // logical screen identifier
)
```

### Step 4 — Handle logout

```kotlin
KProtect.logout()
// Call this in your logout flow before clearing the user session
```

### Step 5 — Required permissions

```xml
<!-- AndroidManifest.xml -->
<uses-permission android:name="android.permission.INTERNET" />
<!-- Optional: for accelerometer/gyroscope behavioral signals -->
<uses-feature android:name="android.hardware.sensor.accelerometer" android:required="false" />
<uses-feature android:name="android.hardware.sensor.gyroscope" android:required="false" />
```

### Android SDK — Advanced Configuration

```kotlin
KProtect.init(
    context = this,
    apiKey = "kp_live_abc...",
    config = KProtectConfig {
        session {
            pulseIntervalMs = 30_000
            idleTimeoutMs = 900_000
        }
        pageGate {
            optOutActivities = listOf("MarketingActivity", "OnboardingActivity")
        }
        criticalActions {
            action(
                activity = "PaymentConfirmActivity",
                name = "payment_confirm",
                commitButtonId = R.id.btnConfirmPayment
            )
            action(
                activity = "TransferActivity",
                name = "transfer_confirm",
                commitButtonId = R.id.btnSubmitTransfer
            )
        }
        transport {
            mode = TransportMode.PROXY
            endpoint = "https://api.yourbank.com/security/kp-proxy"
        }
        environment = Environment.PRODUCTION
    }
)
```

### Android SDK — Lifecycle Integration

The SDK auto-hooks into `ProcessLifecycleOwner`. No per-Activity code required. For fine-grained screen tracking:

```kotlin
// Optional: tag activities for page gating
class PaymentActivity : AppCompatActivity() {
    // SDK auto-detects class name "PaymentActivity"
    // No code needed if class name matches criticalActions config
}
```

### Android SDK — Listening for Results

```kotlin
KProtect.addListener(object : KProtectListener {
    override fun onDriftScore(score: DriftScoreResponse) {
        if (score.action == "block") {
            runOnUiThread { showStepUpAuth() }
        }
    }

    override fun onAlert(alert: AlertResponse) {
        fraudPreventionService.report(alert)
    }

    override fun onCriticalAction(result: CriticalActionResponse) {
        if (!result.passed) triggerFrictionlessChallenge()
    }
})

// Remove when no longer needed
KProtect.removeListener(listener)
```

### Android SDK — ProGuard / R8

The AAR ships its own ProGuard rules. If you have a custom configuration, ensure these classes are kept:

```proguard
-keep class io.kprotect.sdk.** { *; }
-keepnames class io.kprotect.sdk.** { *; }
```

---

## iOS SDK

### Step 1 — Add dependency

**Swift Package Manager (recommended):**
```
https://github.com/kprotect/sdk-ios
```
Or in `Package.swift`:
```swift
dependencies: [
    .package(url: "https://github.com/kprotect/sdk-ios", from: "1.0.0")
],
targets: [
    .target(name: "YourApp", dependencies: ["KProtectSDK"])
]
```

**CocoaPods:**
```ruby
pod 'KProtectSDK', '~> 1.0'
```

### Step 2 — Initialize in AppDelegate / App

**UIKit:**
```swift
// AppDelegate.swift
func application(_ application: UIApplication,
                 didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
    KProtect.initialize(apiKey: "kp_live_abc...")
    return true
}
```

**SwiftUI:**
```swift
// YourApp.swift
@main
struct YourBankApp: App {
    init() {
        KProtect.initialize(apiKey: "kp_live_abc...")
    }
    var body: some Scene { WindowGroup { ContentView() } }
}
```

### Step 3 — Provide username (mandatory)

```swift
// After successful authentication
authService.login(credentials: creds) { result in
    switch result {
    case .success(let user):
        KProtect.setUsername(user.accountIdentifier)
        self.navigateToHome()
    case .failure:
        break
    }
}
```

**SwiftUI binding:**
```swift
// KProtect monitors the field automatically if attached
KProtect.attachUsernameField(textField, screen: "/login")
```

### Step 4 — Handle logout

```swift
KProtect.logout()
// Call before invalidating your session token
```

### Step 5 — Privacy manifest

Your app's `PrivacyInfo.xcprivacy` (or the SDK's bundled one) must declare:

```xml
<key>NSPrivacyAccessedAPITypes</key>
<array>
    <dict>
        <key>NSPrivacyAccessedAPIType</key>
        <string>NSPrivacyAccessedAPICategoryUserDefaults</string>
        <key>NSPrivacyAccessedAPITypeReasons</key>
        <array><string>CA92.1</string></array>
    </dict>
</array>
<key>NSPrivacyCollectedDataTypes</key>
<array>
    <dict>
        <key>NSPrivacyCollectedDataType</key>
        <string>NSPrivacyCollectedDataTypeOtherDiagnosticData</string>
        <key>NSPrivacyCollectedDataTypeLinked</key>
        <false/>
        <key>NSPrivacyCollectedDataTypeTracking</key>
        <false/>
        <key>NSPrivacyCollectedDataTypePurposes</key>
        <array><string>NSPrivacyCollectedDataTypePurposeFraudPrevention</string></array>
    </dict>
</array>
```

### iOS SDK — Advanced Configuration

```swift
KProtect.initialize(
    apiKey: "kp_live_abc...",
    config: KProtectConfig.Builder()
        .session(pulseIntervalMs: 30_000, idleTimeoutMs: 900_000)
        .pageGate(optOutViewControllers: ["MarketingViewController", "HelpViewController"])
        .criticalAction(
            viewController: "PaymentConfirmViewController",
            name: "payment_confirm",
            commitButtonTag: 101
        )
        .criticalAction(
            viewController: "TransferViewController",
            name: "transfer_confirm",
            commitButtonTag: 201
        )
        .transport(mode: .proxy, endpoint: "https://api.yourbank.com/security/kp-proxy")
        .environment(.production)
        .build()
)
```

### iOS SDK — Listening for Results

```swift
// Closure-based
KProtect.onDriftScore { score in
    DispatchQueue.main.async {
        if score.action == "block" { self.showStepUpAuth() }
    }
}

KProtect.onAlert { alert in
    FraudPreventionService.shared.report(alert)
}

// Combine publisher
KProtect.driftPublisher
    .receive(on: DispatchQueue.main)
    .sink { score in
        self.updateRiskUI(score)
    }
    .store(in: &cancellables)
```

### iOS SDK — Scene Phase (SwiftUI)

```swift
struct ContentView: View {
    @Environment(\.scenePhase) var scenePhase

    var body: some View {
        MainContent()
            .onChange(of: scenePhase) { phase in
                // SDK handles this automatically via NotificationCenter
                // No code needed here unless you need custom hooks
            }
    }
}
```

---

## Backend Integration (Proxy Mode)

If you use proxy mode, your backend forwards requests to K-Protect:

```python
# FastAPI example
from fastapi import Request
import httpx

@app.post("/security/kp-proxy")
async def kp_proxy(request: Request):
    body = await request.body()
    headers = {
        "Content-Type": request.headers.get("Content-Type", "application/json"),
        "Content-Encoding": request.headers.get("Content-Encoding", ""),
        "X-KP-API-Key": request.headers.get("X-KP-API-Key"),
        "X-KP-Session": request.headers.get("X-KP-Session"),
        "X-KP-Device": request.headers.get("X-KP-Device"),
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.kprotect.io/v1/behavioral/ingest",
            content=body,
            headers=headers,
            timeout=5.0,
        )
    # Optionally log response for your fraud pipeline
    await your_fraud_pipeline.ingest(response.json())
    return response.json()
```

The proxy is a thin pass-through. It receives the same `DriftScoreResponse` your fraud team can tap into server-side.

---

## Verification Checklist (for go-live)

### Web
- [ ] `KProtect.init()` called once on page load (before or after DOM ready — both work)
- [ ] CSP headers include `connect-src https://api.kprotect.io` and `worker-src blob:`
- [ ] `KProtect.logout()` called on user sign-out
- [ ] DevTools Network tab shows `POST /v1/behavioral/ingest` every ~30s after login (batches are skipped when fewer than 10 events are collected in a window)
- [ ] No JavaScript errors in console related to `kprotect`
- [ ] Main thread shows <50ms blocking in Performance tab during 10s typing session

### Android
- [ ] `KProtect.init()` called in `Application.onCreate()`
- [ ] `KProtect.setUsername()` called after every successful authentication
- [ ] `KProtect.logout()` called before session invalidation
- [ ] Network requests visible in `adb logcat` with tag `KProtect` (debug mode)
- [ ] `EncryptedSharedPreferences` keys visible under `kp.*` namespace
- [ ] ANR not triggered during test (StrictMode clean)

### iOS
- [ ] `KProtect.initialize()` called in `application(_:didFinishLaunchingWithOptions:)`
- [ ] `KProtect.setUsername()` called after every successful authentication
- [ ] Privacy manifest included and correctly declared
- [ ] Network requests visible in Xcode console (debug mode)
- [ ] Main queue clean in Time Profiler (no KProtect frames on main queue >0.5ms)
- [ ] App passes App Store privacy review with included manifest

---

*Last updated: 2026-04-09 — K-Protect Engineering*
