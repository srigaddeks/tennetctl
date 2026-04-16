// K-Control Service Worker — Web Push handler
// Receives encrypted push payloads, shows OS-level notifications, handles deep-link clicks.

self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

// ── Push received ─────────────────────────────────────────────────────────────

self.addEventListener("push", (event) => {
  if (!event.data) return;

  let payload;
  try {
    payload = event.data.json();
  } catch {
    payload = { title: "K-Control", body: event.data.text() };
  }

  const title = payload.title || "K-Control";
  const url = (payload.data && payload.data.url) || payload.url || "/notifications";

  const options = {
    body: payload.body || "",
    icon: "/icons/icon-192.png",
    badge: "/icons/badge-72.png",
    tag: payload.tag || "kcontrol-" + Date.now(),
    renotify: true,
    requireInteraction: false,
    silent: false,
    vibrate: [100, 50, 100],
    // Clicking anywhere on the notification navigates to the deep link.
    // The `url` is also stored in `data` for the notificationclick handler.
    data: { url },
    actions: [
      { action: "open", title: "Open" },
      { action: "dismiss", title: "Dismiss" },
    ],
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

// ── Notification click — deep-link navigation ─────────────────────────────────

self.addEventListener("notificationclick", (event) => {
  event.notification.close();

  if (event.action === "dismiss") return;

  const url = event.notification.data?.url || "/notifications";
  const fullUrl = url.startsWith("http") ? url : self.location.origin + url;

  event.waitUntil(
    self.clients
      .matchAll({ type: "window", includeUncontrolled: true })
      .then((clients) => {
        // Focus an existing tab that is already on the target URL.
        for (const client of clients) {
          if (client.url === fullUrl && "focus" in client) {
            return client.focus();
          }
        }
        // Focus any open K-Control tab and navigate it, rather than opening a new one.
        const appOrigin = self.location.origin;
        const appTab = clients.find(
          (c) => c.url.startsWith(appOrigin) && "focus" in c
        );
        if (appTab) {
          appTab.navigate(fullUrl);
          return appTab.focus();
        }
        // Last resort: open a new tab.
        return self.clients.openWindow(fullUrl);
      })
  );
});
