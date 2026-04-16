"use client";

/**
 * Row actions for a vault config — Edit + Delete (with confirm).
 */

import { useState } from "react";

import { Modal } from "@/components/modal";
import { useToast } from "@/components/toast";
import { Button } from "@/components/ui";
import { EditConfigDialog } from "@/features/vault/configs/_components/edit-config-dialog";
import { useDeleteConfig } from "@/features/vault/configs/hooks/use-configs";
import { ApiClientError } from "@/lib/api";
import type { VaultConfigMeta } from "@/types/api";

export function ConfigRowActions({ config }: { config: VaultConfigMeta }) {
  const { toast } = useToast();
  const [editOpen, setEditOpen] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const del = useDeleteConfig(config.id);

  async function confirmDelete() {
    try {
      await del.mutateAsync();
      toast(`Deleted "${config.key}"`, "success");
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
        onClick={() => setEditOpen(true)}
        data-testid={`config-row-edit-${config.key}`}
      >
        Edit
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setConfirmOpen(true)}
        data-testid={`config-row-delete-${config.key}`}
      >
        Delete
      </Button>

      <EditConfigDialog
        open={editOpen}
        config={config}
        onClose={() => setEditOpen(false)}
      />

      <Modal
        open={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        title={`Delete "${config.key}"?`}
        description={`Soft-delete config at scope=${config.scope}.`}
        size="md"
      >
        <div
          className="flex flex-col gap-4"
          data-testid={`config-delete-confirm-${config.key}`}
        >
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            Anything reading{" "}
            <code className="break-all font-mono text-xs">{config.key}</code>{" "}
            at scope <strong>{config.scope}</strong> will fall back to the next scope
            up (if any) or fail.
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
              data-testid={`config-delete-confirm-yes-${config.key}`}
            >
              Delete
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
