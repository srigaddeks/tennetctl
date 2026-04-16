"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";

import { cn } from "@/lib/cn";

type ToastKind = "success" | "error" | "info";
type Toast = { id: string; kind: ToastKind; message: string };

type ToastContextValue = {
  toast: (message: string, kind?: ToastKind) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

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
    if (toasts.length === 0) return;
    const t = setTimeout(() => {
      setToasts((current) => current.slice(1));
    }, 3500);
    return () => clearTimeout(t);
  }, [toasts]);

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="pointer-events-none fixed top-4 right-4 z-50 flex w-96 flex-col gap-2">
        {toasts.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => dismiss(t.id)}
            className={cn(
              "pointer-events-auto rounded-lg border px-4 py-3 text-left text-sm shadow-lg backdrop-blur transition",
              t.kind === "success" &&
                "border-emerald-200 bg-emerald-50/95 text-emerald-900 dark:border-emerald-800/50 dark:bg-emerald-950/95 dark:text-emerald-100",
              t.kind === "error" &&
                "border-red-200 bg-red-50/95 text-red-900 dark:border-red-800/50 dark:bg-red-950/95 dark:text-red-100",
              t.kind === "info" &&
                "border-zinc-200 bg-white/95 text-zinc-900 dark:border-zinc-800 dark:bg-zinc-900/95 dark:text-zinc-50"
            )}
          >
            <div className="flex items-start gap-2">
              <span className="mt-0.5 text-base leading-none">
                {t.kind === "success" && "✓"}
                {t.kind === "error" && "✕"}
                {t.kind === "info" && "ℹ"}
              </span>
              <span className="flex-1 leading-snug">{t.message}</span>
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
