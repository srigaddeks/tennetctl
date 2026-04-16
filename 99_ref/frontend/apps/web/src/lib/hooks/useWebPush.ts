"use client";

import { useCallback, useEffect, useState } from "react";
import {
  getVapidPublicKey,
  subscribeWebPush,
  unsubscribeWebPush,
  listWebPushSubscriptions,
  type WebPushSubscription,
} from "@/lib/api/notifications";

type PushState = "unsupported" | "prompt" | "denied" | "subscribed";

function urlBase64ToUint8Array(base64String: string): Uint8Array<ArrayBuffer> {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = atob(base64);
  const arr = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i);
  return arr;
}

export function useWebPush() {
  const [state, setState] = useState<PushState>("unsupported");
  const [loading, setLoading] = useState(false);
  const [subscription, setSubscription] = useState<WebPushSubscription | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
      setState("unsupported");
      return;
    }

    const perm = Notification.permission;
    if (perm === "denied") {
      setState("denied");
      return;
    }

    // Register SW on mount so push events are received regardless of UI interaction.
    navigator.serviceWorker
      .register("/sw.js", { scope: "/" })
      .then((reg) => navigator.serviceWorker.ready.then(() => reg))
      .then(async (reg) => {
        const existing = await reg.pushManager.getSubscription();
        if (existing) {
          setState("subscribed");
          const subs = await listWebPushSubscriptions().catch(() => []);
          const match = subs.find((s) => s.endpoint === existing.endpoint);
          if (match) setSubscription(match);
        } else {
          setState("prompt");
        }
      })
      .catch(() => setState("prompt"));
  }, []);

  const subscribe = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const reg = await navigator.serviceWorker.register("/sw.js", { scope: "/" });
      await navigator.serviceWorker.ready;

      const vapidKey = await getVapidPublicKey();
      if (!vapidKey) throw new Error("Push notifications are not configured on this server");

      // This line triggers the browser's native "Allow / Block" permission dialog.
      const pushSub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapidKey),
      });

      const record = await subscribeWebPush(pushSub);
      setSubscription(record);
      setState("subscribed");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to enable push notifications";
      setError(msg);
      if (Notification.permission === "denied") setState("denied");
    } finally {
      setLoading(false);
    }
  }, []);

  const unsubscribe = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const reg = await navigator.serviceWorker.ready;
      const existing = await reg.pushManager.getSubscription();
      if (existing) await existing.unsubscribe();
      if (subscription) await unsubscribeWebPush(subscription.id);
      setSubscription(null);
      setState("prompt");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to disable push notifications");
    } finally {
      setLoading(false);
    }
  }, [subscription]);

  return { state, loading, subscription, error, subscribe, unsubscribe };
}
