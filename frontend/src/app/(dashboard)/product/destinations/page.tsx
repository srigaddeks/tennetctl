"use client";

import { useEffect, useState } from "react";

import { PageHeader } from "@/components/page-header";
import {
  Badge, Button, EmptyState, ErrorState, Field, Input, Select, Skeleton,
  Table, TBody, TD, TH, THead, TR, Textarea,
} from "@/components/ui";
import {
  useCreateDestination, useDeleteDestination, useDeliveries, useDestinations,
  useTestDestination,
} from "@/features/product-ops/hooks/use-destinations";
import type { DeliveryStatus, DestinationKind } from "@/types/api";

const KIND_TONE: Record<DestinationKind, "blue" | "purple" | "zinc"> = {
  webhook: "blue", slack: "purple", custom: "zinc",
};

const STATUS_TONE: Record<DeliveryStatus, "emerald" | "red" | "amber" | "zinc"> = {
  success: "emerald",
  failure: "red",
  timeout: "red",
  rejected_filter: "zinc",
  pending: "amber",
};

export default function DestinationsPage() {
  const [workspaceId, setWorkspaceId] = useState<string | undefined>();
  const [showForm, setShowForm] = useState(false);
  const [openDeliveriesFor, setOpenDeliveriesFor] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const ws = new URLSearchParams(window.location.search).get("workspace_id");
    if (ws) setWorkspaceId(ws);
  }, []);

  const list = useDestinations(workspaceId);
  const del = useDeleteDestination();
  const test = useTestDestination();

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Destinations / Webhooks"
        description="Outbound CDP fan-out. Each ingested event evaluates filter_rule against destination + posts to URL with optional HMAC signature. Every attempt is logged."
        actions={
          <Button variant="primary" onClick={() => setShowForm(v => !v)} data-testid="dest-new-toggle">
            {showForm ? "Cancel" : "New destination"}
          </Button>
        }
      />

      {!workspaceId && <EmptyState title="No workspace selected" description="Append ?workspace_id=…" />}
      {workspaceId && showForm && <CreateForm workspaceId={workspaceId} onDone={() => setShowForm(false)} />}
      {workspaceId && list.isLoading && <Skeleton className="h-72 w-full" />}
      {workspaceId && list.isError && (
        <ErrorState message={list.error instanceof Error ? list.error.message : "Failed"} retry={() => { void list.refetch(); }} />
      )}
      {workspaceId && list.data && list.data.items.length === 0 && (
        <EmptyState title="No destinations yet" description="Create one above to start fan-out." />
      )}

      {workspaceId && list.data && list.data.items.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-zinc-200 dark:border-zinc-800">
          <Table>
            <THead>
              <TR>
                <TH>Destination</TH>
                <TH>Kind</TH>
                <TH>URL</TH>
                <TH>Signed</TH>
                <TH>30d (success / failure / total)</TH>
                <TH>Actions</TH>
              </TR>
            </THead>
            <TBody>
              {list.data.items.map(d => (
                <TR key={d.id} data-testid={`dest-row-${d.id}`}>
                  <TD>
                    <div className="flex flex-col">
                      <span className="font-medium">{d.name}</span>
                      <code className="text-[10px] text-zinc-500">{d.slug}</code>
                    </div>
                  </TD>
                  <TD><Badge tone={KIND_TONE[d.kind]}>{d.kind}</Badge></TD>
                  <TD className="text-xs"><code>{d.url}</code></TD>
                  <TD>{d.has_secret ? <Badge tone="emerald">HMAC</Badge> : <Badge tone="zinc">no</Badge>}</TD>
                  <TD className="text-xs">
                    <span className="text-emerald-600 dark:text-emerald-400">{d.success_count_30d}</span>
                    {" / "}
                    <span className="text-red-600 dark:text-red-400">{d.failure_count_30d}</span>
                    {" / "}
                    <span className="text-zinc-500">{d.delivery_count_30d}</span>
                  </TD>
                  <TD className="space-x-2">
                    <Button variant="secondary" size="sm" onClick={() => test.mutate(d.id)} disabled={test.isPending}>
                      Test
                    </Button>
                    <Button
                      variant="secondary" size="sm"
                      onClick={() => setOpenDeliveriesFor(openDeliveriesFor === d.id ? null : d.id)}
                    >
                      {openDeliveriesFor === d.id ? "Hide" : "Deliveries"}
                    </Button>
                    <Button
                      variant="secondary" size="sm"
                      onClick={() => { if (confirm(`Delete ${d.slug}?`)) del.mutate(d.id); }}
                    >
                      Delete
                    </Button>
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        </div>
      )}

      {test.data && (
        <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-3 text-sm dark:border-zinc-800 dark:bg-zinc-900">
          Test result: <Badge tone={STATUS_TONE[test.data.status as DeliveryStatus] ?? "zinc"}>{test.data.status}</Badge>
        </div>
      )}

      {openDeliveriesFor && <DeliveriesPanel destinationId={openDeliveriesFor} />}
    </div>
  );
}

function DeliveriesPanel({ destinationId }: { destinationId: string }) {
  const q = useDeliveries(destinationId);
  if (q.isLoading) return <Skeleton className="h-32 w-full" />;
  if (q.isError) return <ErrorState message="Failed to load deliveries" />;
  const items = q.data?.items ?? [];
  if (items.length === 0) return <EmptyState title="No deliveries yet" description="Hit Test or send tracked events." />;
  return (
    <div className="overflow-hidden rounded-xl border border-zinc-200 dark:border-zinc-800">
      <Table>
        <THead><TR><TH>When</TH><TH>Status</TH><TH>HTTP</TH><TH>Duration</TH><TH>Error</TH></TR></THead>
        <TBody>
          {items.map(dd => (
            <TR key={dd.id}>
              <TD className="text-xs">{dd.occurred_at}</TD>
              <TD><Badge tone={STATUS_TONE[dd.status]}>{dd.status}</Badge></TD>
              <TD>{dd.response_code ?? "—"}</TD>
              <TD>{dd.duration_ms != null ? `${dd.duration_ms}ms` : "—"}</TD>
              <TD className="text-xs text-red-600">{dd.error_message ?? ""}</TD>
            </TR>
          ))}
        </TBody>
      </Table>
    </div>
  );
}

function CreateForm({ workspaceId, onDone }: { workspaceId: string; onDone: () => void }) {
  const create = useCreateDestination();
  const [slug, setSlug] = useState(""); const [name, setName] = useState("");
  const [kind, setKind] = useState<DestinationKind>("webhook");
  const [url, setUrl] = useState(""); const [secret, setSecret] = useState("");
  const [filterJson, setFilterJson] = useState("");

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    let filter: Record<string, unknown> = {};
    if (filterJson.trim()) {
      try { filter = JSON.parse(filterJson) as Record<string, unknown>; }
      catch { alert("filter_rule must be valid JSON"); return; }
    }
    await create.mutateAsync({
      slug, name, workspace_id: workspaceId, kind, url,
      secret: secret || undefined, filter_rule: filter,
    });
    setSlug(""); setName(""); setUrl(""); setSecret(""); setFilterJson("");
    onDone();
  };

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-4 rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
      <div className="grid grid-cols-2 gap-4">
        <Field label="Slug" required htmlFor="dest-slug">
          <Input id="dest-slug" value={slug} onChange={e => setSlug(e.target.value)} required placeholder="slack_signups" />
        </Field>
        <Field label="Name" required htmlFor="dest-name">
          <Input id="dest-name" value={name} onChange={e => setName(e.target.value)} required placeholder="Slack #signups" />
        </Field>
        <Field label="Kind" htmlFor="dest-kind">
          <Select id="dest-kind" value={kind} onChange={e => setKind(e.target.value as DestinationKind)}>
            <option value="webhook">Webhook (raw JSON POST)</option>
            <option value="slack">Slack incoming webhook</option>
            <option value="custom">Custom</option>
          </Select>
        </Field>
        <Field label="URL" required htmlFor="dest-url">
          <Input id="dest-url" type="url" value={url} onChange={e => setUrl(e.target.value)} required placeholder="https://hooks.slack.com/..." />
        </Field>
        <Field label="HMAC Secret (optional)" htmlFor="dest-secret">
          <Input id="dest-secret" value={secret} onChange={e => setSecret(e.target.value)} placeholder="signing key" />
        </Field>
      </div>
      <Field label="Filter rule (JSON, optional — empty = all events)" hint='e.g. {"op":"eq","field":"event.event_name","value":"signup_completed"}' htmlFor="dest-filter">
        <Textarea id="dest-filter" value={filterJson} onChange={e => setFilterJson(e.target.value)} rows={3} className="font-mono text-xs" />
      </Field>
      {create.isError && <p className="text-sm text-red-600">{create.error instanceof Error ? create.error.message : "Failed"}</p>}
      <div className="flex justify-end gap-2">
        <Button type="button" variant="secondary" onClick={onDone}>Cancel</Button>
        <Button type="submit" variant="primary" disabled={create.isPending}>
          {create.isPending ? "Creating…" : "Create"}
        </Button>
      </div>
    </form>
  );
}
