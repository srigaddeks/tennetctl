// TennetCTL web push service worker.
// Receives push events from the server (notify.webpush sender) and shows
// browser notifications. On click, focuses an existing tab or opens a new one.

self.addEventListener("install", (event) => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("push", (event) => {
  let payload = {};
  try {
    payload = event.data ? event.data.json() : {};
  } catch {
    payload = { title: "TennetCTL", body: event.data ? event.data.text() : "" };
  }
  const title = payload.title || "TennetCTL";
  const options = {
    body: payload.body || "",
    icon: payload.icon || "/next.svg",
    badge: payload.badge || "/next.svg",
    tag: payload.tag,
    data: {
      url: payload.url || "/",
      delivery_id: payload.delivery_id || null,
    },
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const data = event.notification.data || {};
  const targetUrl = data.url || "/";
  const deliveryId = data.delivery_id || null;

  const markRead = deliveryId
    ? fetch(`/api/v1/notify/deliveries/${deliveryId}`, {
        method: "PATCH",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "opened" }),
      }).catch(() => {})
    : Promise.resolve();

  const focusOrOpen = self.clients
    .matchAll({ type: "window", includeUncontrolled: true })
    .then((clients) => {
      for (const client of clients) {
        if (client.url.includes(self.location.origin) && "focus" in client) {
          client.navigate(targetUrl);
          return client.focus();
        }
      }
      if (self.clients.openWindow) {
        return self.clients.openWindow(targetUrl);
      }
    });

  event.waitUntil(Promise.all([markRead, focusOrOpen]));
});
