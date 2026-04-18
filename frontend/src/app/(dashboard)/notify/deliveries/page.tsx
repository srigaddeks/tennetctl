"use client";

import { useState } from "react";

import { PageHeader } from "@/components/page-header";
import { useToast } from "@/components/toast";
import {
  Badge,
  Button,
  EmptyState,
  ErrorState,
  Field,
  Select,
  Skeleton,
  TBody,
  TD,
  TH,
  THead,
  TR,
  Table,
} from "@/components/ui";
import { useMe } from "@/features/auth/hooks/use-auth";
import {
  useDeliveries,
  useRetryDelivery,
} from "@/features/notify/hooks/use-deliveries";
import { ApiClientError } from "@/lib/api";
import { downloadCsv } from "@/lib/csv";
import type { NotifyChannelCode, NotifyDelivery } from "@/types/api";

const STATUS_OPTIONS = [
  { value: "", label: "All statuses" },
  { value: "pending",       label: "Pending" },
  { value: "queued",        label: "Queued" },
  { value: "sent",          label: "Sent" },
  { value: "delivered",     label: "Delivered" },
  { value: "opened",        label: "Opened" },
  { value: "clicked",       label: "Clicked" },
  { value: "bounced",       label: "Bounced" },
  { value: "failed",        label: "Failed" },
  { value: "unsubscribed",  label: "Unsubscribed" },
];

const CHANNEL_OPTIONS = [
  { value: "", label: "All channels" },
  { value: "email",   label: "Email" },
  { value: "webpush", label: "Web Push" },
  { value: "in_app",  label: "In-app" },
];

function statusTone(code: string): "zinc" | "blue" | "emerald" | "amber" | "red" | "purple" {
  switch (code) {
    case "pending":      return "zinc";
    case "queued":       return "blue";
    case "sent":         return "blue";
    case "delivered":    return "emerald";
    case "opened":       return "emerald";
    case "clicked":      return "emerald";
    case "bounced":      return "red";
    case "failed":       return "red";
    case "unsubscribed": return "amber";
    default:             return "zinc";
  }
}

function channelTone(code: NotifyChannelCode): "zinc" | "blue" | "purple" | "amber" {
  switch (code) {
    case "email":   return "blue";
    case "webpush": return "purple";
    case "in_app":  return "amber";
    default:        return "zinc";
  }
}

const RETRYABLE = new Set(["failed", "bounced"]);

export default function DeliveriesPage() {
  const me    = useMe();
  const orgId = me.data?.session?.org_id ?? null;
  const { toast } = useToast();

  const [statusFilter, setStatusFilter]   = useState("");
  const [channelFilter, setChannelFilter] = useState("");

  const { data, isLoading, isError, error } = useDeliveries(orgId, {
    status:  statusFilter || undefined,
    channel: channelFilter || undefined,
  });
  const retry = useRetryDelivery();

  const items: NotifyDelivery[] = data?.items ?? [];

  async function handleRetry(id: string) {
    try {
      await retry.mutateAsync(id);
      toast("Delivery requeued", "success");
    } catch (err) {
      const msg = err instanceof ApiClientError ? err.message : String(err);
      toast(msg, "error");
    }
  }

  return (
    <>
      <PageHeader
        title="Deliveries"
        description="All notification deliveries — filter by status, channel, or recipient."
        testId="heading-notify-deliveries"
        actions={
          <Button
            variant="secondary"
            onClick={() =>
              downloadCsv("notify-deliveries", items, [
                { key: "id", accessor: (d) => d.id },
                { key: "recipient_user_id", accessor: (d) => d.recipient_user_id },
                { key: "template_id", accessor: (d) => d.template_id },
                { key: "channel", accessor: (d) => d.channel_code },
                { key: "priority", accessor: (d) => d.priority_code },
                { key: "status", accessor: (d) => d.status_code },
                { key: "failure_reason", accessor: (d) => d.failure_reason ?? "" },
                { key: "created_at", accessor: (d) => d.created_at },
              ])
            }
            disabled={items.length === 0}
            data-testid="deliveries-export-csv"
          >
            Export CSV
          </Button>
        }
      />

      <div className="flex-1 overflow-y-auto px-8 py-6" data-testid="notify-deliveries-body">
        {/* Filters */}
        <div className="mb-4 flex flex-wrap gap-4">
          <Field label="Status" htmlFor="filter-status">
            <Select
              id="filter-status"
              data-testid="select-delivery-status"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              {STATUS_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </Select>
          </Field>
          <Field label="Channel" htmlFor="filter-channel">
            <Select
              id="filter-channel"
              data-testid="select-delivery-channel"
              value={channelFilter}
              onChange={(e) => setChannelFilter(e.target.value)}
            >
              {CHANNEL_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </Select>
          </Field>
        </div>

        {/* Table */}
        {isLoading && (
          <div className="flex flex-col gap-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        )}
        {isError && <ErrorState message={(error as Error).message} />}
        {!isLoading && !isError && items.length === 0 && (
          <EmptyState title="No deliveries" description="Send a notification to see it here." />
        )}
        {!isLoading && !isError && items.length > 0 && (
          <Table data-testid="deliveries-table">
            <THead>
              <TR>
                <TH>Recipient</TH>
                <TH>Template</TH>
                <TH>Channel</TH>
                <TH>Priority</TH>
                <TH>Status</TH>
                <TH>Created</TH>
                <TH></TH>
              </TR>
            </THead>
            <TBody>
              {items.map((d) => (
                <TR key={d.id} data-testid={`delivery-row-${d.id}`}>
                  <TD className="font-mono text-xs">{d.recipient_user_id.slice(0, 8)}…</TD>
                  <TD className="font-mono text-xs">{d.template_id.slice(0, 8)}…</TD>
                  <TD>
                    <Badge tone={channelTone(d.channel_code)}>{d.channel_label}</Badge>
                  </TD>
                  <TD className="text-xs capitalize">{d.priority_label}</TD>
                  <TD>
                    <Badge tone={statusTone(d.status_code)}>{d.status_label}</Badge>
                    {d.failure_reason && (
                      <div
                        className="mt-1 max-w-xs truncate text-[11px] text-red-500"
                        title={d.failure_reason}
                      >
                        {d.failure_reason}
                      </div>
                    )}
                  </TD>
                  <TD className="text-xs text-zinc-500">
                    {new Date(d.created_at).toLocaleString()}
                  </TD>
                  <TD>
                    {RETRYABLE.has(d.status_code) && (
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => handleRetry(d.id)}
                        loading={retry.isPending && retry.variables === d.id}
                        data-testid={`delivery-retry-${d.id}`}
                      >
                        Retry
                      </Button>
                    )}
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        )}
      </div>
    </>
  );
}
