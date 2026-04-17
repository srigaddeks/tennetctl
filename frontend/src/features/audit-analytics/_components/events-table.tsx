"use client";

import { Badge, TBody, TD, TH, THead, TR, Table } from "@/components/ui";
import type { AuditEventRow } from "@/types/api";

type Props = {
  items: AuditEventRow[];
  onRowClick: (id: string) => void;
};

function categoryTone(code: string) {
  switch (code) {
    case "user": return "blue" as const;
    case "system": return "zinc" as const;
    case "integration": return "purple" as const;
    case "setup": return "amber" as const;
    default: return "zinc" as const;
  }
}

function outcomeTone(outcome: string) {
  return outcome === "success" ? ("emerald" as const) : ("red" as const);
}

function abbreviate(id: string | null): string {
  if (!id) return "—";
  return id.length <= 12 ? id : `${id.slice(0, 8)}…`;
}

function relTime(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return iso;
  const diffMs = Date.now() - then;
  const s = Math.floor(diffMs / 1000);
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  return `${d}d ago`;
}

export function EventsTable({ items, onRowClick }: Props) {
  if (items.length === 0) {
    return (
      <div
        data-testid="audit-events-empty"
        className="rounded-xl border border-dashed border-zinc-200 bg-white p-8 text-center text-sm text-zinc-500 dark:border-zinc-800 dark:bg-zinc-950"
      >
        No audit events match these filters.
      </div>
    );
  }

  return (
    <Table>
      <THead>
        <tr>
          <TH>Event</TH>
          <TH>Category</TH>
          <TH>Outcome</TH>
          <TH>Actor</TH>
          <TH>Org</TH>
          <TH>When</TH>
        </tr>
      </THead>
      <TBody>
        {items.map((r) => (
          <TR
            key={r.id}
            onClick={() => onRowClick(r.id)}
            data-testid={`audit-row-${r.id}`}
          >
            <TD>
              <div className="flex flex-col gap-0.5">
                <span className="font-mono text-xs text-zinc-900 dark:text-zinc-50">
                  {r.event_key}
                </span>
                {r.event_label && (
                  <span className="text-[11px] text-zinc-500">{r.event_label}</span>
                )}
              </div>
            </TD>
            <TD>
              <Badge tone={categoryTone(r.category_code)}>
                {r.category_label ?? r.category_code}
              </Badge>
            </TD>
            <TD>
              <Badge tone={outcomeTone(r.outcome)}>{r.outcome}</Badge>
            </TD>
            <TD>
              <span className="font-mono text-xs text-zinc-700 dark:text-zinc-300">
                {abbreviate(r.actor_user_id)}
              </span>
            </TD>
            <TD>
              <span className="font-mono text-xs text-zinc-700 dark:text-zinc-300">
                {abbreviate(r.org_id)}
              </span>
            </TD>
            <TD>
              <span className="text-xs text-zinc-600 dark:text-zinc-400">
                {relTime(r.created_at)}
              </span>
            </TD>
          </TR>
        ))}
      </TBody>
    </Table>
  );
}
