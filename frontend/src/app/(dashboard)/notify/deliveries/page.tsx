"use client";

import { useState } from "react";

import { ApplicationScopeBar } from "@/components/application-scope-bar";
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

function statusTone(code: string): "default" | "info" | "emerald" | "warning" | "danger" {
  switch (code) {
    case "pending":      return "default";
    case "queued":       return "info";
    case "sent":         return "info";
    case "delivered":    return "emerald";
    case "opened":       return "emerald";
    case "clicked":      return "emerald";
    case "bounced":      return "warning";
    case "failed":       return "danger";
    case "unsubscribed": return "warning";
    default:             return "default";
  }
}

function channelTone(code: NotifyChannelCode): "info" | "purple" | "amber" | "default" {
  switch (code) {
    case "email":   return "info";
    case "webpush": return "purple";
    case "in_app":  return "amber";
    default:        return "default";
  }
}

/** Delivery pipeline steps for a given status */
const PIPELINE_STEPS = ["queued", "sent", "delivered", "opened"] as const;
type PipelineStep = typeof PIPELINE_STEPS[number];

function DeliveryPipeline({ status }: { status: string }) {
  const stepIndex = PIPELINE_STEPS.indexOf(status as PipelineStep);
  if (stepIndex === -1) return null;

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
      {PIPELINE_STEPS.map((step, i) => {
        const done = i <= stepIndex;
        return (
          <div key={step} style={{ display: "flex", alignItems: "center", gap: 4 }}>
            <div
              style={{
                width: 6,
                height: 6,
                borderRadius: "50%",
                background: done ? "var(--success)" : "var(--border-bright)",
                transition: "background 0.15s",
              }}
              title={step}
            />
            {i < PIPELINE_STEPS.length - 1 && (
              <div
                style={{
                  width: 16,
                  height: 1,
                  background: done && i < stepIndex ? "var(--success)" : "var(--border)",
                }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

function StatCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: number;
  accent: "blue" | "green" | "amber" | "red" | "default";
}) {
  const accentColor =
    accent === "blue" ? "var(--info)"
    : accent === "green" ? "var(--success)"
    : accent === "amber" ? "var(--warning)"
    : accent === "red" ? "var(--danger)"
    : "var(--text-secondary)";

  return (
    <div
      style={{
        flex: 1,
        padding: "16px 20px",
        borderRadius: 8,
        border: "1px solid var(--border)",
        background: "var(--bg-surface)",
        borderLeft: `3px solid ${accentColor}`,
      }}
    >
      <div
        style={{
          fontSize: 11,
          textTransform: "uppercase",
          letterSpacing: "0.07em",
          fontWeight: 600,
          color: "var(--text-muted)",
          marginBottom: 6,
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontFamily: "'IBM Plex Mono', monospace",
          fontSize: 28,
          fontWeight: 700,
          color: accentColor,
          lineHeight: 1,
        }}
      >
        {value.toLocaleString()}
      </div>
    </div>
  );
}

const RETRYABLE = new Set(["failed", "bounced"]);

export default function DeliveriesPage() {
  const me    = useMe();
  const orgId = me.data?.session?.org_id ?? null;
  const { toast } = useToast();

  const [statusFilter, setStatusFilter]   = useState("");
  const [channelFilter, setChannelFilter] = useState("");
  const [appFilter, setAppFilter]         = useState<string | null>(null);

  const { data, isLoading, isError, error } = useDeliveries(orgId, {
    status:  statusFilter || undefined,
    channel: channelFilter || undefined,
  });
  const retry = useRetryDelivery();

  const items: NotifyDelivery[] = data?.items ?? [];

  const delivered  = items.filter((d) => ["delivered", "opened", "clicked"].includes(d.status_code)).length;
  const failed     = items.filter((d) => ["failed", "bounced"].includes(d.status_code)).length;
  const pending    = items.filter((d) => ["pending", "queued"].includes(d.status_code)).length;

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
        description="Real-time delivery tracking — every notification from queue to inbox."
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

      <div
        className="flex-1 overflow-y-auto"
        style={{ padding: "24px 32px" }}
        data-testid="notify-deliveries-body"
      >
        <div style={{ marginBottom: 20 }}>
          <ApplicationScopeBar
            appId={appFilter}
            onChange={setAppFilter}
            label="Deliveries for application"
          />
        </div>

        {/* Stat cards */}
        <div style={{ display: "flex", gap: 16, marginBottom: 24 }}>
          <StatCard label="Total" value={items.length} accent="default" />
          <StatCard label="Delivered" value={delivered} accent="green" />
          <StatCard label="Failed / Bounced" value={failed} accent="red" />
          <StatCard label="Pending / Queued" value={pending} accent="blue" />
        </div>

        {/* Filters */}
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: 16,
            padding: "12px 16px",
            borderRadius: 8,
            border: "1px solid var(--border)",
            background: "var(--bg-surface)",
            marginBottom: 20,
          }}
        >
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
                <TH>Pipeline</TH>
                <TH>Created</TH>
                <TH></TH>
              </TR>
            </THead>
            <TBody>
              {items.map((d) => {
                const isFailure = ["failed", "bounced"].includes(d.status_code);
                return (
                  <TR
                    key={d.id}
                    data-testid={`delivery-row-${d.id}`}
                    style={
                      isFailure
                        ? { background: "rgba(255, 63, 85, 0.04)" }
                        : undefined
                    }
                  >
                    <TD>
                      <span
                        style={{
                          fontFamily: "'IBM Plex Mono', monospace",
                          fontSize: 11,
                          color: "var(--text-secondary)",
                        }}
                      >
                        {d.recipient_user_id.slice(0, 8)}…
                      </span>
                    </TD>
                    <TD>
                      <span
                        style={{
                          fontFamily: "'IBM Plex Mono', monospace",
                          fontSize: 11,
                          color: "var(--text-muted)",
                        }}
                      >
                        {d.template_id.slice(0, 8)}…
                      </span>
                    </TD>
                    <TD>
                      <Badge tone={channelTone(d.channel_code)}>{d.channel_label}</Badge>
                    </TD>
                    <TD>
                      <span
                        style={{
                          fontSize: 12,
                          textTransform: "capitalize",
                          color: "var(--text-secondary)",
                        }}
                      >
                        {d.priority_label}
                      </span>
                    </TD>
                    <TD>
                      <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                        <Badge tone={statusTone(d.status_code)} dot>{d.status_label}</Badge>
                        {d.failure_reason && (
                          <div
                            style={{
                              maxWidth: 200,
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                              whiteSpace: "nowrap",
                              fontSize: 11,
                              color: "var(--danger)",
                            }}
                            title={d.failure_reason}
                          >
                            {d.failure_reason}
                          </div>
                        )}
                      </div>
                    </TD>
                    <TD>
                      <DeliveryPipeline status={d.status_code} />
                    </TD>
                    <TD>
                      <span
                        style={{
                          fontFamily: "'IBM Plex Mono', monospace",
                          fontSize: 11,
                          color: "var(--text-muted)",
                        }}
                      >
                        {new Date(d.created_at).toLocaleString()}
                      </span>
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
                );
              })}
            </TBody>
          </Table>
        )}
      </div>
    </>
  );
}
