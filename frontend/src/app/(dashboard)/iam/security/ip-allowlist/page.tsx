"use client";

import { useState } from "react";

import { ApplicationScopeBar } from "@/components/application-scope-bar";
import { ConfirmDialog } from "@/components/confirm-dialog";
import { Modal } from "@/components/modal";
import { PageHeader } from "@/components/page-header";
import { useToast } from "@/components/toast";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Skeleton,
  StatCard,
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
  const [appId, setAppId] = useState<string | null>(null);

  const isRestricted = entries.length > 0;

  return (
    <>
      <PageHeader
        title="IP Allowlist"
        description="When entries are present, only requests from matching CIDR ranges are allowed. An empty list permits all IPs."
        testId="heading-iam-ip-allowlist"
        breadcrumbs={BREADCRUMBS}
        actions={
          <Button
            variant="primary"
            data-testid="btn-new-ip"
            onClick={() => setCreateOpen(true)}
          >
            + Add entry
          </Button>
        }
      />
      <div
        className="flex-1 overflow-y-auto px-6 py-5 animate-fade-in"
        data-testid="iam-ip-allowlist-body"
      >
        <div className="mb-5">
          <ApplicationScopeBar appId={appId} onChange={setAppId} label="Restrict IPs to application" />
        </div>

        {/* Status banner */}
        <div
          className="mb-5 flex items-center gap-3 rounded border px-4 py-3"
          style={{
            background: isRestricted ? "var(--warning-muted)" : "var(--success-muted)",
            borderColor: isRestricted ? "var(--warning)" : "var(--success)",
          }}
        >
          <span
            className="inline-block h-2 w-2 rounded-full"
            style={{ background: isRestricted ? "var(--warning)" : "var(--success)" }}
          />
          <p
            className="text-xs font-medium"
            style={{ color: isRestricted ? "var(--warning)" : "var(--success)" }}
          >
            {isRestricted
              ? `Access restricted to ${entries.length} CIDR ${entries.length === 1 ? "range" : "ranges"}`
              : "All IPs permitted — no restrictions active"}
          </p>
        </div>

        {/* Stats */}
        {!isLoading && !isError && (
          <div className="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-3">
            <StatCard
              label="Total entries"
              value={entries.length}
              accent="blue"
            />
            <StatCard
              label="IPv4 ranges"
              value={entries.filter((e) => !e.cidr.includes(":")).length}
              accent="blue"
            />
            <StatCard
              label="IPv6 ranges"
              value={entries.filter((e) => e.cidr.includes(":")).length}
              accent="amber"
            />
          </div>
        )}

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
                <TH>Version</TH>
                <TH>Label</TH>
                <TH>Added</TH>
                <TH className="text-right">Actions</TH>
              </tr>
            </THead>
            <TBody>
              {entries.map((e) => (
                <TR key={e.id} data-testid={`ip-row-${e.id}`}>
                  <TD>
                    <span
                      className="font-mono-data text-xs"
                      style={{ color: "var(--info)" }}
                    >
                      {e.cidr}
                    </span>
                  </TD>
                  <TD>
                    <Badge tone={e.cidr.includes(":") ? "purple" : "blue"}>
                      {e.cidr.includes(":") ? "IPv6" : "IPv4"}
                    </Badge>
                  </TD>
                  <TD>
                    {e.label ? (
                      <span className="text-xs" style={{ color: "var(--text-secondary)" }}>
                        {e.label}
                      </span>
                    ) : (
                      <span style={{ color: "var(--text-muted)" }}>—</span>
                    )}
                  </TD>
                  <TD>
                    <span
                      className="font-mono-data text-xs"
                      style={{ color: "var(--text-muted)" }}
                    >
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
                      style={{ color: "var(--danger)" }}
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
        {err && (
          <p className="text-xs" style={{ color: "var(--danger)" }}>
            {err}
          </p>
        )}
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
