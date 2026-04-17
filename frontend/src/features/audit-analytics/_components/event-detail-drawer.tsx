"use client";

import { Badge, Skeleton } from "@/components/ui";
import { useAuditEventDetail } from "@/features/audit-analytics/hooks/use-audit-events";

type Props = {
  eventId: string | null;
  onClose: () => void;
};

export function EventDetailDrawer({ eventId, onClose }: Props) {
  const { data, isLoading, isError, error } = useAuditEventDetail(eventId);

  if (!eventId) return null;

  return (
    <div
      data-testid="audit-detail-drawer"
      className="fixed inset-y-0 right-0 z-40 flex w-full max-w-2xl flex-col border-l border-zinc-200 bg-white shadow-2xl dark:border-zinc-800 dark:bg-zinc-950"
    >
      <div className="flex items-start justify-between border-b border-zinc-200 px-6 py-4 dark:border-zinc-800">
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
            Audit Event
          </div>
          <div className="mt-1 font-mono text-sm text-zinc-900 dark:text-zinc-50">
            {eventId}
          </div>
        </div>
        <button
          type="button"
          data-testid="audit-detail-close"
          className="rounded-md p-2 text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800"
          onClick={onClose}
          aria-label="Close"
        >
          ✕
        </button>
      </div>
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {isLoading && (
          <div className="flex flex-col gap-3">
            <Skeleton className="h-6 w-2/3" />
            <Skeleton className="h-40 w-full" />
          </div>
        )}
        {isError && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-900 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
            {error instanceof Error ? error.message : "Failed to load event"}
          </div>
        )}
        {data && (
          <div className="flex flex-col gap-5">
            <Row label="Event key" value={<span className="font-mono">{data.event_key}</span>} testid="detail-event-key" />
            {data.event_label && <Row label="Label" value={data.event_label} />}
            {data.event_description && (
              <Row label="Description" value={<span className="text-zinc-600 dark:text-zinc-400">{data.event_description}</span>} />
            )}
            <Row
              label="Category"
              value={<Badge tone="blue">{data.category_label ?? data.category_code}</Badge>}
            />
            <Row
              label="Outcome"
              value={<Badge tone={data.outcome === "success" ? "emerald" : "red"}>{data.outcome}</Badge>}
              testid="detail-outcome"
            />
            <Row label="Actor user" value={<span className="font-mono text-xs">{data.actor_user_id ?? "—"}</span>} />
            <Row label="Session" value={<span className="font-mono text-xs">{data.actor_session_id ?? "—"}</span>} />
            <Row label="Org" value={<span className="font-mono text-xs">{data.org_id ?? "—"}</span>} />
            <Row label="Workspace" value={<span className="font-mono text-xs">{data.workspace_id ?? "—"}</span>} />
            <Row label="Trace ID" value={<span className="font-mono text-xs" data-testid="detail-trace-id">{data.trace_id}</span>} />
            <Row label="Span ID" value={<span className="font-mono text-xs">{data.span_id}</span>} />
            {data.parent_span_id && (
              <Row label="Parent span" value={<span className="font-mono text-xs">{data.parent_span_id}</span>} />
            )}
            <Row label="Created at" value={<span className="font-mono text-xs">{data.created_at}</span>} />
            <div>
              <div className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
                Metadata
              </div>
              <pre
                data-testid="detail-metadata"
                className="max-h-96 overflow-auto rounded-lg border border-zinc-200 bg-zinc-50 p-3 font-mono text-[11px] leading-relaxed text-zinc-800 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-200"
              >
                {JSON.stringify(data.metadata, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Row({ label, value, testid }: { label: string; value: React.ReactNode; testid?: string }) {
  return (
    <div className="grid grid-cols-[140px_1fr] gap-3" {...(testid ? { "data-testid": testid } : {})}>
      <div className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
        {label}
      </div>
      <div className="text-sm text-zinc-900 dark:text-zinc-50">{value}</div>
    </div>
  );
}
