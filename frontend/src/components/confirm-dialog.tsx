"use client";

import { Modal } from "@/components/modal";
import { Button } from "@/components/ui";

export function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title,
  description,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  tone = "primary",
  loading,
  testId,
}: {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void | Promise<void>;
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  tone?: "primary" | "danger";
  loading?: boolean;
  testId?: string;
}) {
  return (
    <Modal open={open} onClose={onClose} title={title} description={description} size="sm">
      <div className="flex justify-end gap-2" data-testid={testId}>
        <Button variant="secondary" type="button" onClick={onClose}>
          {cancelLabel}
        </Button>
        <Button
          variant={tone === "danger" ? "danger" : "primary"}
          type="button"
          onClick={onConfirm}
          loading={loading}
          data-testid={testId ? `${testId}-confirm` : undefined}
        >
          {confirmLabel}
        </Button>
      </div>
    </Modal>
  );
}
