"use client";

import { AlertTriangle, Info } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui";
import { cn } from "@/lib/cn";

import type { ConfirmAction } from "./types";

export function ConfirmDialog({
  action,
  onClose,
}: {
  action: ConfirmAction | null;
  onClose: () => void;
}) {
  const [running, setRunning] = useState(false);
  if (!action) return null;

  const colorsMap = {
    info: {
      icon: Info,
      iconColor: "text-blue-600",
      bg: "bg-blue-50 dark:bg-blue-950/40",
      border: "border-blue-200 dark:border-blue-900/50",
    },
    warning: {
      icon: AlertTriangle,
      iconColor: "text-amber-600",
      bg: "bg-amber-50 dark:bg-amber-950/40",
      border: "border-amber-200 dark:border-amber-900/50",
    },
    danger: {
      icon: AlertTriangle,
      iconColor: "text-red-600",
      bg: "bg-red-50 dark:bg-red-950/40",
      border: "border-red-200 dark:border-red-900/50",
    },
  };
  const colors = colorsMap[action.variant];
  const IconComp = colors.icon;

  async function confirm() {
    setRunning(true);
    try {
      await action?.onConfirm();
    } catch {
      /* errors surfaced by caller */
    }
    setRunning(false);
    onClose();
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-zinc-950/40 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      data-testid="confirm-dialog"
    >
      <div className="mx-4 w-full max-w-md rounded-2xl border border-zinc-200 bg-white shadow-2xl dark:border-zinc-800 dark:bg-zinc-950">
        <div className="flex items-start gap-3 p-6 pb-4">
          <div
            className={cn(
              "shrink-0 rounded-xl p-2 border",
              colors.bg,
              colors.border
            )}
          >
            <IconComp className={cn("h-5 w-5", colors.iconColor)} />
          </div>
          <div>
            <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-50">
              {action.title}
            </h2>
            <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
              {action.body}
            </p>
          </div>
        </div>
        <div className="flex justify-end gap-2 border-t border-zinc-200 px-6 py-4 dark:border-zinc-800">
          <Button variant="secondary" size="sm" onClick={onClose} disabled={running}>
            Cancel
          </Button>
          <Button
            size="sm"
            onClick={confirm}
            loading={running}
            variant={action.variant === "danger" ? "danger" : "primary"}
          >
            {action.confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}
