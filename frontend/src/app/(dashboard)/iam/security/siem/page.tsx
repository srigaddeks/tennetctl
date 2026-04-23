"use client";

import { useState } from "react";

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
  Select,
  Skeleton,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
} from "@/components/ui";
import {
  useCreateSiemDestination,
  useDeleteSiemDestination,
  useSiemDestinations,
} from "@/features/iam-security/hooks/use-siem";
import { ApiClientError } from "@/lib/api";
import type { SiemDestination } from "@/types/api";

const BREADCRUMBS = [
  { label: "Identity", href: "/iam/users" },
  { label: "Security" },
  { label: "SIEM export" },
];

type DestKind = SiemDestination["kind"];

const KIND_OPTIONS: { value: DestKind; label: string; help: string; available: boolean }[] = [
  { value: "webhook", label: "Webhook", help: "POSTs JSON to your HTTPS endpoint.", available: true },
  { value: "splunk_hec", label: "Splunk HEC", help: "Planned for v0.4.0.", available: false },
  { value: "datadog", label: "Datadog", help: "Planned for v0.4.0.", available: false },
  { value: "s3", label: "Amazon S3", help: "Planned for v0.4.0.", available: false },
];

const KIND_TONE: Record<DestKind, "blue" | "purple" | "amber" | "cyan"> = {
  webhook: "blue",
  splunk_hec: "purple",
  datadog: "amber",
  s3: "cyan",
};

export default function SiemPage() {
  const { data: destinations = [], isLoading, isError, error, refetch } =
    useSiemDestinations();
  const [createOpen, setCreateOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<SiemDestination | null>(
    null,
  );

  return (
    <>
      <PageHeader
        title="SIEM Export"
        description="Stream audit events to an external SIEM. Only the webhook destination is wired today; other kinds are reserved for future releases."
        testId="heading-iam-siem"
        breadcrumbs={BREADCRUMBS}
        actions={
          <Button
            variant="primary"
            data-testid="btn-new-siem"
            onClick={() => setCreateOpen(true)}
          >
            + Add destination
          </Button>
        }
      />
      <div
        className="flex-1 overflow-y-auto px-6 py-5 animate-fade-in"
        data-testid="iam-siem-body"
      >
        {/* Architecture note */}
        <div
          className="mb-5 rounded border px-4 py-3 text-xs"
          style={{
            background: "var(--info-muted)",
            borderColor: "var(--info)",
            color: "var(--text-secondary)",
          }}
        >
          Audit events are buffered and delivered on a best-effort basis. Delivery
          failures increment the{" "}
          <code className="font-mono-data" style={{ color: "var(--info)" }}>
            failure_count
          </code>{" "}
          field. Splunk HEC, Datadog, and S3 destinations arrive in v0.4.0.
        </div>

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
        {!isLoading && !isError && destinations.length === 0 && (
          <EmptyState
            title="No SIEM destinations"
            description="Add a webhook URL to start streaming audit events to an external system."
            action={
              <Button onClick={() => setCreateOpen(true)}>
                + Add destination
              </Button>
            }
          />
        )}
        {destinations.length > 0 && (
          <Table>
            <THead>
              <tr>
                <TH>Kind</TH>
                <TH>Label</TH>
                <TH>Health</TH>
                <TH>Last exported</TH>
                <TH className="text-right">Actions</TH>
              </tr>
            </THead>
            <TBody>
              {destinations.map((d) => (
                <TR key={d.id} data-testid={`siem-row-${d.id}`}>
                  <TD>
                    <Badge tone={KIND_TONE[d.kind] ?? "blue"}>
                      {d.kind}
                    </Badge>
                  </TD>
                  <TD>
                    {d.label ? (
                      <span
                        className="text-xs"
                        style={{ color: "var(--text-secondary)" }}
                      >
                        {d.label}
                      </span>
                    ) : (
                      <span style={{ color: "var(--text-muted)" }}>—</span>
                    )}
                  </TD>
                  <TD>
                    {d.failure_count > 0 ? (
                      <Badge tone="danger" dot>
                        {d.failure_count} failures
                      </Badge>
                    ) : (
                      <Badge tone="success" dot>
                        healthy
                      </Badge>
                    )}
                  </TD>
                  <TD>
                    <span
                      className="font-mono-data text-xs"
                      style={{ color: "var(--text-muted)" }}
                    >
                      {d.last_exported_at
                        ? new Date(d.last_exported_at).toLocaleString()
                        : "—"}
                    </span>
                  </TD>
                  <TD className="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      type="button"
                      data-testid={`siem-delete-${d.id}`}
                      onClick={() => setDeleteTarget(d)}
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

      <CreateDestinationDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
      />
      <RemoveDestinationDialog
        destination={deleteTarget}
        onClose={() => setDeleteTarget(null)}
      />
    </>
  );
}

function CreateDestinationDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const create = useCreateSiemDestination();
  const [kind, setKind] = useState<DestKind>("webhook");
  const [label, setLabel] = useState("");
  const [url, setUrl] = useState("");
  const [err, setErr] = useState<string | null>(null);

  const selectedKind = KIND_OPTIONS.find((o) => o.value === kind);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    try {
      await create.mutateAsync({
        kind,
        label: label || undefined,
        config_jsonb: kind === "webhook" ? { url } : {},
      });
      toast("SIEM destination added", "success");
      setKind("webhook");
      setLabel("");
      setUrl("");
      onClose();
    } catch (e) {
      const msg = e instanceof ApiClientError ? e.message : String(e);
      setErr(msg);
      toast(msg, "error");
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Add SIEM destination" size="md">
      <form
        onSubmit={handleSubmit}
        className="flex flex-col gap-4"
        data-testid="create-siem-form"
      >
        <Field label="Kind" htmlFor="siem-kind" required hint={selectedKind?.help}>
          <Select
            id="siem-kind"
            value={kind}
            onChange={(e) => setKind(e.target.value as DestKind)}
            data-testid="create-siem-kind"
          >
            {KIND_OPTIONS.map((o) => (
              <option key={o.value} value={o.value} disabled={!o.available}>
                {o.label}{!o.available ? " (coming soon)" : ""}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Label" htmlFor="siem-label" hint="optional">
          <Input
            id="siem-label"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            placeholder="splunk-prod"
            data-testid="create-siem-label"
          />
        </Field>
        {kind === "webhook" && (
          <Field label="Webhook URL" htmlFor="siem-url" required>
            <Input
              id="siem-url"
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://siem.example.com/ingest"
              required
              data-testid="create-siem-url"
            />
          </Field>
        )}
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
            loading={create.isPending}
            data-testid="create-siem-submit"
          >
            Add destination
          </Button>
        </div>
      </form>
    </Modal>
  );
}

function RemoveDestinationDialog({
  destination,
  onClose,
}: {
  destination: SiemDestination | null;
  onClose: () => void;
}) {
  const { toast } = useToast();
  const remove = useDeleteSiemDestination();

  async function onConfirm() {
    if (!destination) return;
    try {
      await remove.mutateAsync(destination.id);
      toast("Destination removed", "success");
      onClose();
    } catch (e) {
      toast(e instanceof ApiClientError ? e.message : String(e), "error");
    }
  }

  return (
    <ConfirmDialog
      open={destination !== null}
      onClose={onClose}
      onConfirm={onConfirm}
      title="Remove SIEM destination"
      description={
        destination
          ? `Audit events will stop flowing to ${destination.label || destination.kind}.`
          : undefined
      }
      confirmLabel="Remove"
      tone="danger"
      loading={remove.isPending}
      testId="confirm-remove-siem"
    />
  );
}
