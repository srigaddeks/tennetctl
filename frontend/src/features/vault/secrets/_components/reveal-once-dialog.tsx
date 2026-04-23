"use client";

/**
 * Reveal-once dialog.
 *
 * Shows a freshly-created / freshly-rotated secret plaintext exactly once.
 * Returns null when `open=false` so the DOM textarea unmounts — preventing any
 * browser extension / devtools inspector from grabbing the value after dismiss.
 * The parent holds the value in a `useRef` and clears the ref on dismiss.
 */

import { ShieldAlert, Copy, CheckCheck, Eye, Lock } from "lucide-react";
import { useState } from "react";

import { Modal } from "@/components/modal";
import { useToast } from "@/components/toast";
import { Button } from "@/components/ui";

export function RevealOnceDialog({
  open,
  secretKey,
  value,
  onDismiss,
}: {
  open: boolean;
  secretKey: string;
  value: string;
  onDismiss: () => void;
}) {
  const { toast } = useToast();
  const [copied, setCopied] = useState(false);

  if (!open) return null;

  async function copyValue() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      toast("Copied to clipboard", "success");
      setTimeout(() => setCopied(false), 3000);
    } catch {
      toast("Clipboard unavailable — select and copy manually", "error");
    }
  }

  return (
    <Modal
      open={open}
      onClose={onDismiss}
      title="Secret revealed"
      description={`Plaintext value for "${secretKey}" — this is your only chance to copy it.`}
      size="md"
    >
      <div
        className="flex flex-col gap-5"
        data-testid="reveal-once"
      >
        {/* Dramatic warning */}
        <div
          className="rounded-xl px-4 py-4"
          style={{
            background: "var(--danger-muted)",
            border: "1px solid var(--danger)",
          }}
        >
          <div className="flex items-start gap-3">
            <div
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl"
              style={{
                background: "rgba(255,63,85,0.15)",
                border: "1px solid var(--danger)",
              }}
            >
              <ShieldAlert className="h-4 w-4" style={{ color: "var(--danger)" }} />
            </div>
            <div>
              <p className="text-sm font-bold" style={{ color: "var(--danger)" }}>
                This value will not be shown again
              </p>
              <p className="mt-1 text-xs" style={{ color: "var(--text-secondary)" }}>
                Once you close this dialog, the plaintext is gone forever. Copy it now and store it
                in a password manager or secure secrets store.
              </p>
            </div>
          </div>
        </div>

        {/* Secret key label */}
        <div>
          <div
            className="mb-2 flex items-center gap-2"
          >
            <Lock className="h-3.5 w-3.5" style={{ color: "var(--warning)" }} />
            <span
              className="text-xs font-medium"
              style={{ color: "var(--text-muted)" }}
            >
              Secret key
            </span>
            <code
              className="ml-1 text-xs font-semibold"
              style={{ color: "var(--warning)", fontFamily: "var(--font-mono)" }}
            >
              {secretKey}
            </code>
          </div>

          {/* Value display */}
          <div
            className="relative rounded-xl overflow-hidden"
            style={{
              background: "var(--bg-elevated)",
              border: "1px solid var(--warning)",
            }}
          >
            <div
              className="flex items-center gap-2 px-4 py-2"
              style={{
                borderBottom: "1px solid var(--border)",
                background: "var(--warning-muted)",
              }}
            >
              <Eye className="h-3.5 w-3.5" style={{ color: "var(--warning)" }} />
              <span className="label-caps text-[10px]" style={{ color: "var(--warning)" }}>
                Plaintext value — visible now only
              </span>
            </div>
            <textarea
              readOnly
              value={value}
              rows={5}
              className="w-full resize-none bg-transparent px-4 py-3 text-xs focus:outline-none"
              style={{
                color: "var(--warning)",
                fontFamily: "var(--font-mono)",
                lineHeight: "1.6",
              }}
              data-testid="reveal-once-value"
              onFocus={(e) => e.currentTarget.select()}
            />
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs" style={{ color: "var(--text-muted)" }}>
            {copied
              ? "Value copied. Store it somewhere safe before closing."
              : "Click Copy, then close once it's stored safely."}
          </p>
          <div className="flex items-center gap-2 shrink-0">
            <Button
              type="button"
              variant="secondary"
              onClick={copyValue}
              data-testid="reveal-once-copy"
            >
              {copied
                ? <><CheckCheck className="h-3.5 w-3.5 mr-1.5" style={{ color: "var(--success)" }} />Copied</>
                : <><Copy className="h-3.5 w-3.5 mr-1.5" />Copy value</>}
            </Button>
            <Button
              type="button"
              variant="primary"
              onClick={onDismiss}
              data-testid="reveal-once-dismiss"
            >
              Done — close
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  );
}
