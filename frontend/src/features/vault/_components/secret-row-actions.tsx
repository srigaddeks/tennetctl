"use client";

/**
 * Row actions for a vault secret — Rotate + Delete (with confirm).
 */

import { useState } from "react";

import { Modal } from "@/components/modal";
import { useToast } from "@/components/toast";
import { Button } from "@/components/ui";
import { RotateSecretDialog } from "@/features/vault/_components/rotate-secret-dialog";
import { useDeleteSecret } from "@/features/vault/hooks/use-secrets";
import { ApiClientError } from "@/lib/api";
import type { VaultSecretMeta } from "@/types/api";

export function SecretRowActions({ secret }: { secret: VaultSecretMeta }) {
  const { toast } = useToast();
  const [rotateOpen, setRotateOpen] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const del = useDeleteSecret(secret.key);

  async function confirmDelete() {
    try {
      await del.mutateAsync();
      toast(`Deleted "${secret.key}"`, "success");
      setConfirmOpen(false);
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : String(err);
      toast(msg, "error");
    }
  }

  return (
    <div
      className="flex items-center gap-2"
      onClick={(e) => e.stopPropagation()}
    >
      <Button
        variant="secondary"
        size="sm"
        onClick={() => setRotateOpen(true)}
        data-testid={`secret-row-rotate-${secret.key}`}
      >
        Rotate
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setConfirmOpen(true)}
        data-testid={`secret-row-delete-${secret.key}`}
      >
        Delete
      </Button>

      <RotateSecretDialog
        open={rotateOpen}
        secretKey={secret.key}
        onClose={() => setRotateOpen(false)}
      />

      <Modal
        open={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        title={`Delete "${secret.key}"?`}
        description="Soft-deletes every version of this key. Key cannot be reused in v0.2."
        size="md"
      >
        <div
          className="flex flex-col gap-4"
          data-testid={`delete-confirm-${secret.key}`}
        >
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            This cannot be undone from the UI. Anything reading{" "}
            <code className="break-all font-mono text-xs">{secret.key}</code>{" "}
            will immediately fail.
          </p>
          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setConfirmOpen(false)}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="danger"
              onClick={confirmDelete}
              loading={del.isPending}
              data-testid={`delete-confirm-yes-${secret.key}`}
            >
              Delete
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
