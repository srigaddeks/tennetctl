"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";

import { cn } from "@/lib/cn";
import { registerToastFn, unregisterToastFn } from "@/lib/toast-bus";

type ToastKind = "success" | "error" | "info" | "warning";
type Toast = { id: string; kind: ToastKind; message: string };

type ToastContextValue = {
  toast: (message: string, kind?: ToastKind) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

const TOAST_ICONS: Record<ToastKind, string> = {
  success: "✓",
  error: "✕",
  info: "·",
  warning: "!",
};

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const toast = useCallback((message: string, kind: ToastKind = "info") => {
    const id = Math.random().toString(36).slice(2);
    setToasts((t) => [...t, { id, kind, message }]);
  }, []);

  const dismiss = useCallback((id: string) => {
    setToasts((t) => t.filter((x) => x.id !== id));
  }, []);

  useEffect(() => {
    registerToastFn(toast);
    return () => unregisterToastFn();
  }, [toast]);

  useEffect(() => {
    if (toasts.length === 0) return;
    const t = setTimeout(() => {
      setToasts((current) => current.slice(1));
    }, 3500);
    return () => clearTimeout(t);
  }, [toasts]);

  const accentColor = (kind: ToastKind) => {
    if (kind === "success") return "var(--success)";
    if (kind === "error") return "var(--danger)";
    if (kind === "warning") return "var(--warning)";
    return "var(--accent)";
  };

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="pointer-events-none fixed top-4 right-4 z-50 flex w-80 flex-col gap-1.5">
        {toasts.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => dismiss(t.id)}
            className={cn(
              "pointer-events-auto rounded border text-left text-[12px] font-medium transition-all duration-200 animate-slide-up",
              "hover:opacity-80",
            )}
            style={{
              background: "var(--bg-elevated)",
              borderColor: `${accentColor(t.kind)}40`,
              borderLeft: `2px solid ${accentColor(t.kind)}`,
              padding: "10px 12px",
              boxShadow: "0 4px 20px rgba(0,0,0,0.4)",
            }}
          >
            <div className="flex items-start gap-2">
              <span
                className="mt-px font-mono text-[11px] font-bold"
                style={{ color: accentColor(t.kind) }}
              >
                {TOAST_ICONS[t.kind]}
              </span>
              <span
                className="flex-1 leading-snug"
                style={{ color: "var(--text-primary)" }}
              >
                {t.message}
              </span>
            </div>
          </button>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
