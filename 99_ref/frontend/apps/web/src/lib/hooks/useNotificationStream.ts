"use client"

import { useEffect, useCallback } from "react"
import { API_BASE_URL, getAccessToken } from "@/lib/api/apiClient"

export type NotificationStreamEvent = {
  type: "notification"
  notification_id: string
  channel_code: string
  notification_type_code?: string
  rendered_subject?: string
}

/**
 * Connects to the SSE `/api/v1/notifications/inbox/stream` endpoint and calls
 * `onEvent` whenever a new notification is delivered in real time.
 *
 * Automatically reconnects on disconnect with a 3-second back-off.
 * Disconnects on component unmount.
 */
export function useNotificationStream(
  enabled: boolean,
  onEvent: (event: NotificationStreamEvent) => void
) {
  const stableOnEvent = useCallback(onEvent, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!enabled) return

    let es: EventSource | null = null
    let retryTimeout: ReturnType<typeof setTimeout> | null = null
    let stopped = false

    const connect = () => {
      if (stopped) return
      // EventSource doesn't support Authorization headers — pass token as ?token= query param.
      const token = getAccessToken() ?? ""
      const base = API_BASE_URL || ""
      const url = `${base}/api/v1/notifications/inbox/stream${token ? `?token=${encodeURIComponent(token)}` : ""}`
      es = new EventSource(url, { withCredentials: true })

      es.onmessage = (e) => {
        try {
          const payload = JSON.parse(e.data) as NotificationStreamEvent
          stableOnEvent(payload)
        } catch {
          // ignore malformed events
        }
      }

      es.onerror = () => {
        es?.close()
        if (!stopped) {
          retryTimeout = setTimeout(connect, 3000)
        }
      }
    }

    connect()

    return () => {
      stopped = true
      if (retryTimeout) clearTimeout(retryTimeout)
      es?.close()
    }
  }, [enabled, stableOnEvent])
}
