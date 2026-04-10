"use client";

import { useRef, useState } from "react";
import { X, Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";

type AppTokenIssuedModalProps = {
  token: string;
  onClose: () => void;
};

export function AppTokenIssuedModal({ token, onClose }: AppTokenIssuedModalProps) {
  const [copied, setCopied] = useState(false);
  const backdropRef = useRef<HTMLDivElement>(null);

  function handleCopy() {
    navigator.clipboard.writeText(token).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <div
      ref={backdropRef}
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60"
      onClick={(e) => { if (e.target === backdropRef.current) onClose(); }}
    >
      <div className="relative w-full max-w-lg rounded-md border border-border bg-surface shadow-xl">
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <h2 className="text-sm font-semibold">Token Issued</h2>
          <button
            onClick={onClose}
            className="rounded-sm p-1 text-foreground-muted hover:bg-surface-3 hover:text-foreground"
            aria-label="Close"
            data-testid="token-issued-close"
          >
            <X className="size-4" />
          </button>
        </div>

        <div className="space-y-4 p-5">
          <p className="rounded-md border border-[color:var(--warning)]/40 bg-[color:var(--warning-bg)] px-3 py-2.5 text-xs font-medium text-[color:var(--warning)]">
            Copy and store this token now — it will not be shown again.
          </p>

          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-foreground-muted">Token</span>
              <button
                onClick={handleCopy}
                className="flex items-center gap-1.5 rounded-sm px-2 py-1 text-xs text-foreground-muted hover:bg-surface-3 hover:text-foreground"
                data-testid="token-issued-copy"
              >
                {copied ? (
                  <><Check className="size-3.5 text-success" /> Copied</>
                ) : (
                  <><Copy className="size-3.5" /> Copy</>
                )}
              </button>
            </div>
            <pre
              className="w-full break-all rounded-md border border-border bg-surface-2 px-3 py-2.5 font-mono text-[11px] text-foreground"
              data-testid="token-issued-value"
            >
              {token}
            </pre>
          </div>

          <div className="flex justify-end">
            <Button
              size="sm"
              onClick={onClose}
              data-testid="token-issued-done"
            >
              Done
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
