"use client";

import { useEffect, useMemo, useState } from "react";

import { PageHeader } from "@/components/page-header";
import { Badge, Button, EmptyState, ErrorState, Skeleton, Table, THead, TH, TR, TD, TBody } from "@/components/ui";
import { useProductEvents } from "@/features/product-ops/hooks/use-product-events";
import type { ProductEvent, ProductEventKind } from "@/types/api";

const KIND_TONE: Record<ProductEventKind, "blue" | "zinc" | "emerald" | "amber" | "purple"> = {
  page_view: "blue",
  custom: "zinc",
  click: "blue",
  identify: "emerald",
  alias: "purple",
  referral_attached: "amber",
};

const LIVE_TICK_MS = 3000;

function relativeTime(iso: string): string {
  const ms = Date.now() - new Date(iso).getTime();
  if (ms < 0 || Number.isNaN(ms)) return iso;
  const sec = Math.round(ms / 1000);
  if (sec < 60) return `${sec}s ago`;
  const min = Math.round(sec / 60);
  if (min < 60) return `${min}m ago`;
  const hr = Math.round(min / 60);
  if (hr < 24) return `${hr}h ago`;
  const d = Math.round(hr / 24);
  return `${d}d ago`;
}

function shortenId(id: string): string {
  return id.length > 12 ? `${id.slice(0, 8)}…${id.slice(-3)}` : id;
}

function truncateUrl(url: string | null, maxLen = 60): string {
  if (!url) return "—";
  if (url.length <= maxLen) return url;
  const headLen = Math.floor((maxLen - 1) / 2);
  return `${url.slice(0, headLen)}…${url.slice(-headLen)}`;
}

export default function ProductOpsPage() {
  // Workspace pulled from session middleware via apiFetch credentials/cookies.
  // For v1 we let the backend resolve session.workspace_id; the page reads
  // a query param if present (operators inspecting another workspace from a
  // shared admin link).
  const [workspaceId, setWorkspaceId] = useState<string | undefined>(undefined);
  const [liveOn, setLiveOn] = useState<boolean>(false);
  const [selected, setSelected] = useState<ProductEvent | null>(null);

  // Read ?workspace_id from URL on mount.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const ws = params.get("workspace_id");
    if (ws) setWorkspaceId(ws);
  }, []);

  const query = useProductEvents({ workspace_id: workspaceId, limit: 100 });

  // Live tail: poll the same endpoint every LIVE_TICK_MS while liveOn.
  useEffect(() => {
    if (!liveOn) return;
    const id = setInterval(() => {
      query.refetch();
    }, LIVE_TICK_MS);
    return () => clearInterval(id);
  }, [liveOn, query]);

  const events = query.data?.events ?? [];

  const headerActions = useMemo(
    () => (
      <div className="flex items-center gap-2">
        <Button
          variant={liveOn ? "primary" : "secondary"}
          onClick={() => setLiveOn((v) => !v)}
          data-testid="product-ops-live-tail-toggle"
        >
          {liveOn ? "Live tail: ON" : "Live tail"}
        </Button>
        <Button
          variant="secondary"
          onClick={() => query.refetch()}
          data-testid="product-ops-refresh"
        >
          Refresh
        </Button>
      </div>
    ),
    [liveOn, query],
  );

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Product Ops"
        description="Anonymous-first product analytics. Browser SDK ingest + UTM attribution + live event tail."
        actions={headerActions}
      />

      {!workspaceId && (
        <EmptyState
          title="No workspace selected"
          description="Append ?workspace_id=… to the URL or sign in to a workspace to see events."
        />
      )}

      {workspaceId && query.isLoading && <Skeleton className="h-72 w-full" />}

      {workspaceId && query.isError && (
        <ErrorState
          message={query.error instanceof Error ? query.error.message : "Couldn't load product events"}
          retry={() => {
            void query.refetch();
          }}
        />
      )}

      {workspaceId && query.data && events.length === 0 && (
        <EmptyState
          title="No events yet"
          description="POST /v1/track with a project_key resolved to this workspace to see events appear."
        />
      )}

      {workspaceId && events.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-zinc-200 dark:border-zinc-800">
          <Table>
            <THead>
              <TR>
                <TH>Kind</TH>
                <TH>Event Name</TH>
                <TH>Visitor</TH>
                <TH>Page</TH>
                <TH>When</TH>
              </TR>
            </THead>
            <TBody>
              {events.map((ev) => (
                <TR
                  key={ev.id}
                  onClick={() => setSelected(ev)}
                  data-testid={`product-event-row-${ev.id}`}
                  className="cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-900"
                >
                  <TD>
                    <Badge tone={KIND_TONE[ev.event_kind]}>{ev.event_kind}</Badge>
                  </TD>
                  <TD>{ev.event_name ?? "—"}</TD>
                  <TD>
                    <a
                      href={`/product/visitors/${ev.visitor_id}`}
                      onClick={(e) => e.stopPropagation()}
                      className="text-xs underline-offset-2 hover:underline"
                    >
                      <code>{shortenId(ev.visitor_id)}</code>
                    </a>
                  </TD>
                  <TD>
                    <span title={ev.page_url ?? undefined} className="text-xs">
                      {truncateUrl(ev.page_url)}
                    </span>
                  </TD>
                  <TD>
                    <span title={ev.occurred_at}>{relativeTime(ev.occurred_at)}</span>
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        </div>
      )}

      {selected && (
        <DetailPanel event={selected} onClose={() => setSelected(null)} />
      )}
    </div>
  );
}

function DetailPanel({ event, onClose }: { event: ProductEvent; onClose: () => void }) {
  return (
    <aside
      data-testid="product-event-detail"
      className="fixed inset-y-0 right-0 z-30 w-[480px] overflow-y-auto border-l border-zinc-200 bg-white p-6 shadow-2xl dark:border-zinc-800 dark:bg-zinc-950"
    >
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold">Event detail</h3>
        <Button variant="ghost" onClick={onClose} data-testid="product-event-detail-close">
          Close
        </Button>
      </div>
      <dl className="space-y-3 text-sm">
        <Row label="ID" value={<code>{event.id}</code>} />
        <Row label="Kind" value={<Badge tone={KIND_TONE[event.event_kind]}>{event.event_kind}</Badge>} />
        {event.event_name && <Row label="Event Name" value={event.event_name} />}
        <Row label="Visitor" value={<code>{event.visitor_id}</code>} />
        {event.user_id && <Row label="User" value={<code>{event.user_id}</code>} />}
        <Row label="Workspace" value={<code>{event.workspace_id}</code>} />
        <Row label="Occurred at" value={event.occurred_at} />
        <Row label="Created at" value={event.created_at} />
        {event.page_url && <Row label="Page URL" value={event.page_url} />}
        {event.referrer && <Row label="Referrer" value={event.referrer} />}
      </dl>
      <div className="mt-6">
        <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-zinc-500">
          Properties (metadata)
        </h4>
        <pre className="overflow-x-auto rounded-lg border border-zinc-200 bg-zinc-50 p-3 text-xs dark:border-zinc-800 dark:bg-zinc-900">
          {JSON.stringify(event.metadata, null, 2)}
        </pre>
      </div>
    </aside>
  );
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-3">
      <dt className="text-zinc-500">{label}</dt>
      <dd className="break-all text-right">{value}</dd>
    </div>
  );
}
