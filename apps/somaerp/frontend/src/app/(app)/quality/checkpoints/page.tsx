"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listQcCheckpoints } from "@/lib/api";
import type {
  QcCheckpoint,
  QcCheckpointScopeKind,
  QcCheckpointStatus,
} from "@/types/api";

type CheckpointsState =
  | { status: "loading" }
  | { status: "ok"; items: QcCheckpoint[] }
  | { status: "error"; message: string };

export default function QcCheckpointsListPage() {
  const [state, setState] = useState<CheckpointsState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;
    listQcCheckpoints()
      .then((items) => {
        if (!cancelled) setState({ status: "ok", items });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : "Unknown error";
        setState({ status: "error", message });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="max-w-5xl">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="mt-2 text-3xl font-bold tracking-tight">
            Checkpoints
          </h1>
        </div>
        <Link
          href="/quality/checkpoints/new"
          className="inline-flex items-center justify-center rounded px-3 py-1.5 text-sm font-medium" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
        >
          + New Checkpoint
        </Link>
      </div>

      <div className="rounded border overflow-hidden" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        {state.status === "loading" && (
          <p className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>Loading checkpoints…</p>
        )}
        {state.status === "error" && (
          <div className="m-4 rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            <p className="font-semibold">
              Failed to load checkpoints
            </p>
            <p className="mt-1 text-sm opacity-80">{state.message}</p>
          </div>
        )}
        {state.status === "ok" && state.items.length === 0 && (
          <div className="p-8 text-center text-sm" style={{ color: "var(--text-muted)" }}>
            <p>No checkpoints yet.</p>
            <Link
              href="/quality/checkpoints/new"
              className="mt-2 inline-block text-sm  underline hover:no-underline"
            >
              Add the first checkpoint
            </Link>
          </div>
        )}
        {state.status === "ok" && state.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead style={{ backgroundColor: "var(--bg-table-header)", borderBottom: "1px solid var(--border)" }}>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Name</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Stage</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Check Type</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Scope</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Required</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Status</th>
                </tr>
              </thead>
              <tbody >
                {state.items.map((cp) => (
                  <tr key={cp.id} onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-table-hover)"; }} onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "transparent"; }}>
                    <td className="px-4 py-2.5 font-medium" style={{ color: "var(--text-primary)" }}>
                      {cp.name}
                    </td>
                    <td className="px-4 py-3">
                      <Badge tone="slate" label={cp.stage_name ?? cp.stage_code ?? "—"} />
                    </td>
                    <td className="px-4 py-3">
                      <Badge
                        tone="indigo"
                        label={cp.check_type_name ?? cp.check_type_code ?? "—"}
                      />
                    </td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)" }}>
                      <ScopeCell
                        scopeKind={cp.scope_kind}
                        scopeRefId={cp.scope_ref_id}
                      />
                    </td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)" }}>
                      {cp.required ? "Yes" : "No"}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={cp.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function ScopeCell({
  scopeKind,
  scopeRefId,
}: {
  scopeKind: QcCheckpointScopeKind;
  scopeRefId: string | null;
}) {
  if (scopeKind === "universal") {
    return <Badge tone="emerald" label="universal" />;
  }
  const refShort =
    scopeRefId && scopeRefId.length > 8 ? `${scopeRefId.slice(0, 8)}…` : scopeRefId ?? "—";
  return (
    <span className="inline-flex items-center gap-2">
      <Badge tone="slate" label={scopeKind} />
      <span className="font-mono text-xs text-sm" style={{ color: "var(--text-muted)" }}>{refShort}</span>
    </span>
  );
}

function StatusBadge({ status }: { status: QcCheckpointStatus }) {
  const styles: Record<QcCheckpointStatus, string> = {
    active: "bg-green-100 text-green-800 border-green-200",
    paused: "bg-yellow-100 text-yellow-800 border-yellow-200",
    archived: "bg-slate-100  border-slate-200",
  };
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${styles[status]}`}
    >
      {status}
    </span>
  );
}

type BadgeTone = "slate" | "indigo" | "emerald";

function Badge({ tone, label }: { tone: BadgeTone; label: string }) {
  const styles: Record<BadgeTone, string> = {
    slate: "bg-slate-100 text-slate-800 border-slate-200",
    indigo: "bg-indigo-100 text-indigo-800 border-indigo-200",
    emerald: "bg-emerald-100 text-emerald-800 border-emerald-200",
  };
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${styles[tone]}`}
    >
      {label}
    </span>
  );
}
