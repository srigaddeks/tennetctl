"use client";

import { useState } from "react";

import { ConfirmDialog } from "@/components/confirm-dialog";
import { Modal } from "@/components/modal";
import { PageHeader } from "@/components/page-header";
import { useToast } from "@/components/toast";
import {
  Button,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Skeleton,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
} from "@/components/ui";
import {
  useAddIpAllowlistEntry,
  useIpAllowlist,
  useRemoveIpAllowlistEntry,
} from "@/features/iam-security/hooks/use-ip-allowlist";
import { ApiClientError } from "@/lib/api";
import type { IpAllowlistEntry } from "@/types/api";

const BREADCRUMBS = [
  { label: "Identity", href: "/iam/users" },
  { label: "Security" },
  { label: "IP allowlist" },
];

export default function IpAllowlistPage() {
  const { data: entries = [], isLoading, isError, error, refetch } =
    useIpAllowlist();
  const [createOpen, setCreateOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<IpAllowlistEntry | null>(
    null,
  );

  return (
    <>
      <PageHeader
        title="IP Allowlist"
        description="When entries are present, only requests from matching CIDR ranges are allowed. An empty list permits all IPs."
        testId="heading-iam-ip-allowlist"
        breadcrumbs={BREADCRUMBS}
        actions={
          <Button
            data-testid="btn-new-ip"
            onClick={() => setCreateOpen(true)}
          >
            + Add entry
          </Button>
        }
      />
      <div
        className="flex-1 overflow-y-auto px-8 py-6"
        data-testid="iam-ip-allowlist-body"
      >
        {isLoading && (
          <div className="flex flex-col gap-2">
            <Skeleton className="h-9 w-full" />
            <Skeleton className="h-9 w-full" />
          </div>
        )}
        {isError && (
          <ErrorState
            message={error instanceof Error ? error.message : "Load failed"}
            retry={() => refetch()}
          />
        )}
        {!isLoading && !isError && entries.length === 0 && (
          <EmptyState
            title="No IP restrictions"
            description="All IPs are currently permitted. Add a CIDR range to restrict access."
            action={
              <Button onClick={() => setCreateOpen(true)}>
                + Add entry
              </Button>
            }
          />
        )}
        {entries.length > 0 && (
          <Table>
            <THead>
              <tr>
                <TH>CIDR</TH>
                <TH>Label</TH>
                <TH>Added</TH>
                <TH className="text-right">Actions</TH>
              </tr>
            </THead>
            <TBody>
              {entries.map((e) => (
                <TR key={e.id} data-testid={`ip-row-${e.id}`}>
                  <TD>
                    <span className="font-mono text-xs">{e.cidr}</span>
                  </TD>
                  <TD>
                    {e.label ? (
                      <span>{e.label}</span>
                    ) : (
                      <span className="text-zinc-400">—</span>
                    )}
                  </TD>
                  <TD>
                    <span className="text-xs text-zinc-500 dark:text-zinc-400">
                      {e.created_at
                        ? new Date(e.created_at).toLocaleDateString()
                        : "—"}
                    </span>
                  </TD>
                  <TD className="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      type="button"
                      data-testid={`ip-delete-${e.id}`}
                      onClick={() => setDeleteTarget(e)}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950/30"
                    >
                      Remove
                    </Button>
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        )}
      </div>

      <AddEntryDialog open={createOpen} onClose={() => setCreateOpen(false)} />
      <RemoveEntryDialog
        entry={deleteTarget}
        onClose={() => setDeleteTarget(null)}
      />
    </>
  );
}

function AddEntryDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const add = useAddIpAllowlistEntry();
  const [cidr, setCidr] = useState("");
  const [label, setLabel] = useState("");
  const [err, setErr] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    try {
      await add.mutateAsync({ cidr: cidr.trim(), label: label.trim() });
      toast(`Added ${cidr.trim()} to allowlist`, "success");
      setCidr("");
      setLabel("");
      onClose();
    } catch (e) {
      const msg = e instanceof ApiClientError ? e.message : String(e);
      setErr(msg);
      toast(msg, "error");
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Add IP entry" size="sm">
      <form
        onSubmit={handleSubmit}
        className="flex flex-col gap-4"
        data-testid="add-ip-form"
      >
        <Field label="CIDR" htmlFor="ip-cidr" required hint="IPv4 or IPv6 range">
          <Input
            id="ip-cidr"
            value={cidr}
            onChange={(e) => setCidr(e.target.value)}
            placeholder="10.0.0.0/8"
            autoFocus
            required
            data-testid="add-ip-cidr"
          />
        </Field>
        <Field label="Label" htmlFor="ip-label" hint="optional">
          <Input
            id="ip-label"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            placeholder="Office VPN"
            data-testid="add-ip-label"
          />
        </Field>
        {err && <p className="text-xs text-red-600">{err}</p>}
        <div className="mt-2 flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            loading={add.isPending}
            disabled={!cidr.trim()}
            data-testid="add-ip-submit"
          >
            Add entry
          </Button>
        </div>
      </form>
    </Modal>
  );
}

function RemoveEntryDialog({
  entry,
  onClose,
}: {
  entry: IpAllowlistEntry | null;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const remove = useRemoveIpAllowlistEntry();

  async function onConfirm() {
    if (!entry) return;
    try {
      await remove.mutateAsync(entry.id);
      toast(`Removed ${entry.cidr}`, "success");
      onClose();
    } catch (e) {
      toast(e instanceof ApiClientError ? e.message : String(e), "error");
    }
  }

  return (
    <ConfirmDialog
      open={entry !== null}
      onClose={onClose}
      onConfirm={onConfirm}
      title="Remove IP entry"
      description={
        entry
          ? `This removes ${entry.cidr} from the allowlist. If it was the only entry, all IPs will be permitted again.`
          : undefined
      }
      confirmLabel="Remove"
      tone="danger"
      loading={remove.isPending}
      testId="confirm-remove-ip"
    />
  );
}
