"use client";

import {
  AlertTriangle,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { useState } from "react";

import { cn } from "@/lib/cn";
import type { AuditEventRow } from "@/types/api";

import {
  CATEGORY_META,
  deriveCategoryCode,
  relativeTime,
} from "./authz-constants";

function MetaJson({ data }: { data: Record<string, unknown> }) {
  return (
    <pre className="overflow-x-auto rounded-lg bg-zinc-900 p-3 text-[11px] leading-relaxed text-zinc-100 dark:bg-zinc-950">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}

function Row({
  label,
  value,
  mono,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="flex items-start gap-2">
      <span className="w-20 shrink-0 text-zinc-400 dark:text-zinc-500">
        {label}
      </span>
      <span
        className={cn(
          "break-all text-zinc-700 dark:text-zinc-300",
          mono && "font-mono",
        )}
      >
        {value}
      </span>
    </div>
  );
}

export function EventRow({
  event,
  expanded,
  onToggle,
}: {
  event: AuditEventRow;
  expanded: boolean;
  onToggle: (id: string) => void;
}) {
  const catCode = deriveCategoryCode(event.event_key);
  const catMeta = CATEGORY_META[catCode];

  const actorLabel =
    event.actor_user_id
      ? event.actor_user_id.length > 12
        ? `${event.actor_user_id.slice(0, 8)}…`
        : event.actor_user_id
      : "system";

  return (
    <div
      className={cn(
        "border-b border-zinc-100 last:border-b-0 dark:border-zinc-800/60",
      )}
      data-testid={`audit-row-${event.id}`}
    >
      {/* Collapsed row */}
      <div
        className={cn(
          "grid grid-cols-[auto_auto_1fr_auto_auto_auto] items-center gap-x-3 border-l-[3px] px-4 py-2.5 transition hover:bg-zinc-50 dark:hover:bg-zinc-900/30",
          catMeta.borderCls,
          expanded && "bg-zinc-50 dark:bg-zinc-900/40",
        )}
      >
        {/* Expand toggle */}
        <button
          type="button"
          onClick={() => onToggle(event.id)}
          data-testid={`expand-row-${event.id}`}
          title={expanded ? "Collapse" : "Expand"}
          className="shrink-0 rounded-md p-1 text-zinc-400 transition hover:bg-zinc-200 hover:text-zinc-700 dark:hover:bg-zinc-700 dark:hover:text-zinc-200"
        >
          {expanded ? (
            <ChevronDown className="h-3.5 w-3.5" />
          ) : (
            <ChevronRight className="h-3.5 w-3.5" />
          )}
        </button>

        {/* Timestamp */}
        <span
          className="shrink-0 font-mono text-[11px] text-zinc-400 dark:text-zinc-500"
          title={event.created_at}
        >
          {relativeTime(event.created_at)}
        </span>

        {/* event_key */}
        <code className="min-w-0 truncate font-mono text-xs font-semibold text-zinc-800 dark:text-zinc-200">
          {event.event_key}
        </code>

        {/* Category badge */}
        <span
          className={cn(
            "inline-flex items-center rounded-full border px-1.5 py-0.5 text-[10px] font-medium",
            catMeta.badgeCls,
          )}
        >
          {catCode === "all" ? "other" : catMeta.label}
        </span>

        {/* Outcome badge */}
        <span
          className={cn(
            "inline-flex items-center gap-1 rounded-full border px-1.5 py-0.5 text-[10px] font-medium",
            event.outcome === "success"
              ? "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300"
              : "border-red-200 bg-red-50 text-red-700 dark:border-red-800 dark:bg-red-900/30 dark:text-red-300",
          )}
        >
          {event.outcome === "failure" && (
            <AlertTriangle className="h-2.5 w-2.5" />
          )}
          {event.outcome}
        </span>

        {/* Actor chip */}
        <span className="shrink-0 rounded-full border border-zinc-200 bg-zinc-50 px-2 py-0.5 font-mono text-[10px] text-zinc-600 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
          {actorLabel}
        </span>
      </div>

      {/* Expanded detail */}
      {expanded && (
        <div className="border-t border-zinc-100 bg-zinc-50 px-6 pb-4 pt-3 dark:border-zinc-800 dark:bg-zinc-900/40">
          <div className="grid gap-3 sm:grid-cols-2">
            {/* Left: key info */}
            <div className="flex flex-col gap-2 text-[11px]">
              <Row label="Event key" value={event.event_key} mono />
              {event.event_label && (
                <Row label="Label" value={event.event_label} />
              )}
              {event.event_description && (
                <Row label="Description" value={event.event_description} />
              )}
              <Row label="Outcome" value={event.outcome} />
              <Row
                label="Timestamp"
                value={new Date(event.created_at).toLocaleString()}
              />
              {event.actor_user_id && (
                <Row label="Actor" value={event.actor_user_id} mono />
              )}
              {event.actor_session_id && (
                <Row label="Session" value={event.actor_session_id} mono />
              )}
              {event.org_id && <Row label="Org" value={event.org_id} mono />}
              {event.workspace_id && (
                <Row label="Workspace" value={event.workspace_id} mono />
              )}
              <Row label="Trace ID" value={event.trace_id} mono />
              <Row label="Span ID" value={event.span_id} mono />
              {event.parent_span_id && (
                <Row label="Parent span" value={event.parent_span_id} mono />
              )}
            </div>

            {/* Right: metadata JSON */}
            <div>
              <p className="mb-1.5 text-[11px] font-medium text-zinc-500 dark:text-zinc-400">
                Metadata
              </p>
              <MetaJson data={event.metadata} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export function DateGroup({
  label,
  events,
  expandedId,
  onToggle,
}: {
  label: string;
  events: AuditEventRow[];
  expandedId: string | null;
  onToggle: (id: string) => void;
}) {
  const [open, setOpen] = useState(true);

  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left transition hover:bg-zinc-100 dark:hover:bg-zinc-800/50"
      >
        <span className="text-xs font-semibold text-zinc-900 dark:text-zinc-50">
          {label}
        </span>
        <span className="text-[11px] tabular-nums text-zinc-400 dark:text-zinc-500">
          {events.length} event{events.length !== 1 ? "s" : ""}
        </span>
        {open ? (
          <ChevronDown className="ml-auto h-3.5 w-3.5 text-zinc-400" />
        ) : (
          <ChevronRight className="ml-auto h-3.5 w-3.5 text-zinc-400" />
        )}
      </button>

      {open && (
        <div className="mb-3 ml-4 overflow-hidden rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950">
          {events.map((evt) => (
            <EventRow
              key={evt.id}
              event={evt}
              expanded={expandedId === evt.id}
              onToggle={onToggle}
            />
          ))}
        </div>
      )}
    </div>
  );
}
