"use client";

import { useEffect, useRef } from "react";

import { Button } from "@/components/ui";
import { cn } from "@/lib/cn";

export function Modal({
  open,
  onClose,
  title,
  description,
  children,
  size = "md",
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  size?: "sm" | "md" | "lg";
}) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const el = dialogRef.current;
    if (!el) return;
    if (open && !el.open) el.showModal();
    if (!open && el.open) el.close();
  }, [open]);

  useEffect(() => {
    const el = dialogRef.current;
    if (!el) return;
    const handleCancel = (e: Event) => {
      e.preventDefault();
      onClose();
    };
    el.addEventListener("cancel", handleCancel);
    return () => el.removeEventListener("cancel", handleCancel);
  }, [onClose]);

  return (
    <dialog
      ref={dialogRef}
      className={cn(
        "m-auto w-full max-h-[90dvh] overflow-hidden whitespace-normal rounded border p-0",
        "backdrop:bg-black/60 backdrop:backdrop-blur-sm",
        size === "sm" && "max-w-md",
        size === "md" && "max-w-lg",
        size === "lg" && "max-w-2xl",
      )}
      style={{
        background: "var(--bg-elevated)",
        borderColor: "var(--border-bright)",
        color: "var(--text-primary)",
        boxShadow: "0 0 0 1px rgba(255,255,255,0.03), 0 24px 60px rgba(0,0,0,0.6)",
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="flex max-h-[90dvh] flex-col">
        <div
          className="flex items-start justify-between gap-4 border-b px-5 py-4"
          style={{ borderColor: "var(--border)" }}
        >
          <div>
            <div className="flex items-center gap-2">
              <div
                className="h-3.5 w-0.5 rounded-full"
                style={{ background: "var(--accent)" }}
                aria-hidden
              />
              <h2
                className="text-sm font-semibold tracking-wide"
                style={{ color: "var(--text-primary)" }}
              >
                {title}
              </h2>
            </div>
            {description && (
              <p
                className="mt-0.5 text-[11px] leading-relaxed pl-3"
                style={{ color: "var(--text-muted)" }}
              >
                {description}
              </p>
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            aria-label="Close"
            type="button"
          >
            ✕
          </Button>
        </div>
        <div className="flex-1 overflow-y-auto px-5 py-4">{children}</div>
      </div>
    </dialog>
  );
}
