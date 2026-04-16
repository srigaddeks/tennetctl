"use client";

/**
 * Reveal-once dialog.
 *
 * Shows a freshly-created / freshly-rotated secret plaintext exactly once.
 * Returns null when `open=false` so the DOM textarea unmounts — preventing any
 * browser extension / devtools inspector from grabbing the value after dismiss.
 * The parent holds the value in a `useRef` and clears the ref on dismiss.
 */

import { Modal } from "@/components/modal";
import { useToast } from "@/components/toast";
import { Button, Textarea } from "@/components/ui";

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

  if (!open) return null;

  async function copyValue() {
    try {
      await navigator.clipboard.writeText(value);
      toast("Copied to clipboard", "success");
    } catch {
      toast("Clipboard unavailable — select and copy manually", "error");
    }
  }

  return (
    <Modal
      open={open}
      onClose={onDismiss}
      title="Reveal once"
      description={`Value for "${secretKey}" — shown exactly once.`}
      size="md"
    >
      <div
        className="flex flex-col gap-4"
        data-testid="reveal-once"
      >
        <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs font-medium text-red-800 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-200">
          This value will not be shown again. Copy it now and store it
          somewhere safe.
        </div>

        <Textarea
          readOnly
          value={value}
          rows={4}
          className="font-mono text-xs"
          data-testid="reveal-once-value"
          onFocus={(e) => e.currentTarget.select()}
        />

        <div className="flex items-center justify-end gap-2">
          <Button
            type="button"
            variant="secondary"
            onClick={copyValue}
            data-testid="reveal-once-copy"
          >
            Copy
          </Button>
          <Button
            type="button"
            onClick={onDismiss}
            data-testid="reveal-once-dismiss"
          >
            Got it
          </Button>
        </div>
      </div>
    </Modal>
  );
}
