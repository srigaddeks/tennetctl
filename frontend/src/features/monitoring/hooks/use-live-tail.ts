"use client";

/**
 * Live tail via SSE. Keeps a rolling 500-event window.
 */

import { useCallback, useEffect, useRef, useState } from "react";

import type { Filter, LogRow } from "@/types/api";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:51734";

const MAX_BUFFER = 500;

export type UseLiveTailResult = {
  logs: LogRow[];
  paused: boolean;
  connected: boolean;
  pause: () => void;
  resume: () => void;
  clear: () => void;
};

export function useLiveTail(filter?: Filter | null): UseLiveTailResult {
  const [logs, setLogs] = useState<LogRow[]>([]);
  const [paused, setPaused] = useState(false);
  const [connected, setConnected] = useState(false);
  const pausedRef = useRef(false);
  const esRef = useRef<EventSource | null>(null);
  const filterKey = filter ? JSON.stringify(filter) : "";

  useEffect(() => {
    pausedRef.current = paused;
  }, [paused]);

  useEffect(() => {
    const params = new URLSearchParams();
    if (filterKey) params.set("filter", filterKey);
    const qs = params.toString();
    const url = `${API_BASE}/v1/monitoring/logs/tail${qs ? `?${qs}` : ""}`;
    const es = new EventSource(url, { withCredentials: true });
    esRef.current = es;

    es.onopen = () => setConnected(true);
    es.onerror = () => setConnected(false);

    es.onmessage = (ev) => {
      if (pausedRef.current) return;
      if (!ev.data) return;
      try {
        const row = JSON.parse(ev.data) as LogRow;
        setLogs((prev) => {
          const next = [row, ...prev];
          return next.length > MAX_BUFFER ? next.slice(0, MAX_BUFFER) : next;
        });
      } catch {
        // ignore non-JSON frames (: ready / : keepalive are comments)
      }
    };

    return () => {
      es.close();
      esRef.current = null;
      setConnected(false);
    };
  }, [filterKey]);

  const pause = useCallback(() => setPaused(true), []);
  const resume = useCallback(() => setPaused(false), []);
  const clear = useCallback(() => setLogs([]), []);

  return { logs, paused, connected, pause, resume, clear };
}
