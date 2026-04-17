"use client";

/**
 * Web push subscription hooks.
 *
 * Flow:
 *   1. Fetch VAPID public key from backend (unauthenticated — it's public)
 *   2. Register service worker at /sw.js
 *   3. Request Notification permission from user
 *   4. Call PushManager.subscribe() with the VAPID key
 *   5. POST {endpoint, p256dh, auth} to backend /v1/notify/webpush/subscriptions
 *
 * Used by the preferences page to show an "Enable browser push" control.
 */

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";

type VapidPublicKeyResponse = { public_key: string };

export type WebPushSubscription = {
  id: string;
  org_id: string;
  user_id: string;
  endpoint: string;
  device_label: string | null;
  created_at: string;
};

type WebPushListResponse = {
  subscriptions: WebPushSubscription[];
  total: number;
};

const qk = {
  list: ["webpush-subscriptions"] as const,
};

function urlBase64ToUint8Array(base64String: string): BufferSource {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = atob(base64);
  const buffer = new ArrayBuffer(rawData.length);
  const view = new Uint8Array(buffer);
  for (let i = 0; i < rawData.length; i += 1) view[i] = rawData.charCodeAt(i);
  return buffer;
}

function arrayBufferToBase64(buf: ArrayBuffer | null): string {
  if (!buf) return "";
  const bytes = new Uint8Array(buf);
  let binary = "";
  for (let i = 0; i < bytes.byteLength; i += 1) binary += String.fromCharCode(bytes[i]);
  return btoa(binary);
}

/** True iff the browser supports the Push API and Service Workers. */
export function webPushSupported(): boolean {
  if (typeof window === "undefined") return false;
  return "serviceWorker" in navigator && "PushManager" in window && "Notification" in window;
}

/** Current browser notification permission: 'default' | 'granted' | 'denied'. */
export function notificationPermission(): NotificationPermission {
  if (typeof window === "undefined" || !("Notification" in window)) return "default";
  return Notification.permission;
}

export function useWebPushSubscriptions(): UseQueryResult<WebPushListResponse> {
  return useQuery({
    queryKey: qk.list,
    queryFn: () => apiFetch<WebPushListResponse>("/v1/notify/webpush/subscriptions"),
    enabled: webPushSupported(),
  });
}

async function fetchVapidKey(): Promise<string> {
  const res = await apiFetch<VapidPublicKeyResponse>("/v1/notify/webpush/vapid-public-key");
  return res.public_key;
}

async function registerSW(): Promise<ServiceWorkerRegistration> {
  return navigator.serviceWorker.register("/sw.js", { scope: "/" });
}

/** Subscribe the browser to push. Requests permission if needed. */
export function useEnableWebPush(): UseMutationResult<WebPushSubscription, Error, string | undefined> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (deviceLabel) => {
      if (!webPushSupported()) throw new Error("Browser does not support push notifications.");
      const permission = await Notification.requestPermission();
      if (permission !== "granted") {
        throw new Error(
          permission === "denied"
            ? "Notification permission denied. Enable it in browser settings."
            : "Notification permission was not granted.",
        );
      }
      const vapidKey = await fetchVapidKey();
      const reg = await registerSW();
      await navigator.serviceWorker.ready;

      const existing = await reg.pushManager.getSubscription();
      const sub =
        existing ??
        (await reg.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: urlBase64ToUint8Array(vapidKey),
        }));

      const json = sub.toJSON() as {
        endpoint?: string;
        keys?: { p256dh?: string; auth?: string };
      };
      const endpoint = json.endpoint ?? sub.endpoint;
      const p256dh =
        json.keys?.p256dh ?? arrayBufferToBase64(sub.getKey("p256dh"));
      const auth = json.keys?.auth ?? arrayBufferToBase64(sub.getKey("auth"));

      const body = JSON.stringify({
        endpoint,
        p256dh,
        auth,
        device_label: deviceLabel ?? navigator.userAgent.slice(0, 80),
      });
      const resp = await apiFetch<{ subscription: WebPushSubscription }>(
        "/v1/notify/webpush/subscriptions",
        { method: "POST", body },
      );
      return resp.subscription;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.list }),
  });
}

/** Revoke a browser push subscription by id. */
export function useDisableWebPush(): UseMutationResult<void, Error, string> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (subscriptionId) => {
      // Unsubscribe on browser side (best-effort — backend delete is authoritative).
      try {
        if (webPushSupported()) {
          const reg = await navigator.serviceWorker.getRegistration();
          const sub = await reg?.pushManager.getSubscription();
          if (sub) await sub.unsubscribe();
        }
      } catch {
        /* ignore — server side will still remove the row */
      }
      await apiFetch<void>(`/v1/notify/webpush/subscriptions/${subscriptionId}`, {
        method: "DELETE",
      });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: qk.list }),
  });
}
