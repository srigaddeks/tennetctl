"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  listBatches,
  listQcCheckpoints,
  listQcChecks,
  listQcOutcomes,
  recordQcCheck,
} from "@/lib/api";
import type {
  ProductionBatch,
  QcCheck,
  QcCheckpoint,
  QcOutcome,
} from "@/types/api";

type ChecksState =
  | { status: "loading" }
  | { status: "ok"; items: QcCheck[] }
  | { status: "error"; message: string };

type DraftCheck = {
  checkpoint_id: string;
  batch_id: string;
  outcome_id: string;
  checked_by: string;
  notes: string;
};

function emptyDraft(): DraftCheck {
  return {
    checkpoint_id: "",
    batch_id: "",
    outcome_id: "",
    checked_by: "",
    notes: "",
  };
}

export default function QcChecksListPage() {
  const [state, setState] = useState<ChecksState>({ status: "loading" });
  const [checkpoints, setCheckpoints] = useState<QcCheckpoint[]>([]);
  const [outcomes, setOutcomes] = useState<QcOutcome[]>([]);
  const [inProgressBatches, setInProgressBatches] = useState<ProductionBatch[]>([]);

  // filters
  const [checkpointId, setCheckpointId] = useState<string>("");
  const [outcomeId, setOutcomeId] = useState<string>("");
  const [tsAfter, setTsAfter] = useState<string>("");
  const [tsBefore, setTsBefore] = useState<string>("");

  // create form
  const [showForm, setShowForm] = useState(false);
  const [draft, setDraft] = useState<DraftCheck>(emptyDraft());
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      listQcCheckpoints(),
      listQcOutcomes(),
      listBatches({ status: "in_progress" }),
    ])
      .then(([cps, ocs, batches]) => {
        if (cancelled) return;
        setCheckpoints(cps);
        setOutcomes(ocs);
        setInProgressBatches(batches);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  const filters = useMemo(
    () => ({
      checkpoint_id: checkpointId === "" ? undefined : checkpointId,
      outcome_id:
        outcomeId === "" ? undefined : Number.parseInt(outcomeId, 10),
      ts_after: tsAfter === "" ? undefined : `${tsAfter}T00:00:00`,
      ts_before: tsBefore === "" ? undefined : `${tsBefore}T23:59:59`,
    }),
    [checkpointId, outcomeId, tsAfter, tsBefore],
  );

  const loadChecks = useCallback(() => {
    setState({ status: "loading" });
    let cancelled = false;
    listQcChecks(filters)
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
  }, [filters]);

  useEffect(() => {
    const cancel = loadChecks();
    return cancel;
  }, [loadChecks]);

  async function onSubmit() {
    setFormError(null);
    if (!draft.checkpoint_id) { setFormError("Select a checkpoint"); return; }
    if (!draft.outcome_id) { setFormError("Select an outcome"); return; }
    setBusy(true);
    try {
      await recordQcCheck({
        checkpoint_id: draft.checkpoint_id,
        batch_id: draft.batch_id || null,
        outcome_id: Number.parseInt(draft.outcome_id, 10),
        notes: draft.notes.trim() || null,
        metadata: draft.checked_by.trim() ? { checked_by: draft.checked_by.trim() } : {},
      });
      setDraft(emptyDraft());
      setShowForm(false);
      loadChecks();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-5xl">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>Recent Checks</h1>
          <p className="mt-2 max-w-xl text-sm">
            Append-only event feed. Corrections are new rows — historical rows
            never change.
          </p>
        </div>
        <button
          type="button"
          onClick={() => { setShowForm((v) => !v); setFormError(null); }}
          className="inline-flex items-center justify-center rounded px-3 py-1.5 text-sm font-medium"
          style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
        >
          {showForm ? "Cancel" : "+ Record QC Check"}
        </button>
      </div>

      {/* Inline create form */}
      {showForm && (
        <div className="mb-6 rounded border p-5" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
          <h2 className="mb-4 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Record New QC Check</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Checkpoint *</label>
              <select
                value={draft.checkpoint_id}
                onChange={(e) => setDraft((p) => ({ ...p, checkpoint_id: e.target.value }))}
                className="w-full rounded border px-3 py-2 text-sm focus:outline-none"
                style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
              >
                <option value="">Select checkpoint…</option>
                {checkpoints.map((cp) => (
                  <option key={cp.id} value={cp.id}>{cp.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Production Batch</label>
              <select
                value={draft.batch_id}
                onChange={(e) => setDraft((p) => ({ ...p, batch_id: e.target.value }))}
                className="w-full rounded border px-3 py-2 text-sm focus:outline-none"
                style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
              >
                <option value="">Not batch-specific</option>
                {inProgressBatches.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.product_name ?? b.product_id} — {b.run_date}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Outcome *</label>
              <select
                value={draft.outcome_id}
                onChange={(e) => setDraft((p) => ({ ...p, outcome_id: e.target.value }))}
                className="w-full rounded border px-3 py-2 text-sm focus:outline-none"
                style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
              >
                <option value="">Select outcome…</option>
                {outcomes.map((o) => (
                  <option key={o.id} value={o.id}>{o.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Checked By</label>
              <input
                type="text"
                value={draft.checked_by}
                onChange={(e) => setDraft((p) => ({ ...p, checked_by: e.target.value }))}
                placeholder="Operator name"
                className="w-full rounded border px-3 py-2 text-sm focus:outline-none"
                style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
              />
            </div>

            <div className="sm:col-span-2">
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Notes</label>
              <textarea
                value={draft.notes}
                onChange={(e) => setDraft((p) => ({ ...p, notes: e.target.value }))}
                placeholder="optional"
                rows={3}
                className="w-full rounded border px-3 py-2 text-sm focus:outline-none"
                style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
              />
            </div>

            <div className="sm:col-span-2">
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Photo</label>
              <input
                type="text"
                disabled
                placeholder="(Photo upload coming in v0.10)"
                className="w-full rounded border px-3 py-2 text-sm opacity-50"
                style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-muted)" }}
              />
            </div>
          </div>

          {formError && (
            <div className="mt-3 rounded border p-3 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
              {formError}
            </div>
          )}

          <div className="mt-4 flex gap-3">
            <button
              type="button"
              onClick={onSubmit}
              disabled={busy}
              className="inline-flex items-center rounded px-4 py-2 text-sm font-medium disabled:opacity-50"
              style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
            >
              {busy ? "Saving…" : "Save Check"}
            </button>
            <button
              type="button"
              onClick={() => { setShowForm(false); setDraft(emptyDraft()); setFormError(null); }}
              className="inline-flex items-center rounded border px-4 py-2 text-sm font-medium"
              style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="mb-6 rounded border p-4" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-4">
          <div>
            <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-sm" style={{ color: "var(--text-muted)" }}>
              Checkpoint
            </label>
            <select
              value={checkpointId}
              onChange={(e) => setCheckpointId(e.target.value)}
              className="w-full rounded border px-2 py-1.5 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            >
              <option value="">All</option>
              {checkpoints.map((cp) => (
                <option key={cp.id} value={cp.id}>
                  {cp.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-sm" style={{ color: "var(--text-muted)" }}>
              Outcome
            </label>
            <select
              value={outcomeId}
              onChange={(e) => setOutcomeId(e.target.value)}
              className="w-full rounded border px-2 py-1.5 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            >
              <option value="">All</option>
              {outcomes.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-sm" style={{ color: "var(--text-muted)" }}>
              After
            </label>
            <input
              type="date"
              value={tsAfter}
              onChange={(e) => setTsAfter(e.target.value)}
              className="w-full rounded border px-2 py-1.5 font-mono text-xs focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-sm" style={{ color: "var(--text-muted)" }}>
              Before
            </label>
            <input
              type="date"
              value={tsBefore}
              onChange={(e) => setTsBefore(e.target.value)}
              className="w-full rounded border px-2 py-1.5 font-mono text-xs focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            />
          </div>
        </div>
      </div>

      <div className="rounded border overflow-hidden" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        {state.status === "loading" && (
          <p className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>Loading checks…</p>
        )}
        {state.status === "error" && (
          <div className="m-4 rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            <p className="font-semibold">Failed to load checks</p>
            <p className="mt-1 text-sm opacity-80">{state.message}</p>
          </div>
        )}
        {state.status === "ok" && state.items.length === 0 && (
          <p className="p-8 text-center text-sm" style={{ color: "var(--text-muted)" }}>No checks recorded.</p>
        )}
        {state.status === "ok" && state.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead style={{ backgroundColor: "var(--bg-table-header)", borderBottom: "1px solid var(--border)" }}>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Timestamp</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Checkpoint</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Stage</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Outcome</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Notes</th>
                </tr>
              </thead>
              <tbody>
                {state.items.map((c) => (
                  <tr key={c.id} onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-table-hover)"; }} onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "transparent"; }}>
                    <td className="px-4 py-2.5 font-mono text-xs" style={{ color: "var(--text-secondary)" }}>
                      {c.ts}
                    </td>
                    <td className="px-4 py-2.5 font-medium" style={{ color: "var(--text-primary)" }}>
                      {c.checkpoint_name ?? c.checkpoint_id}
                    </td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)" }}>
                      {c.stage_name ?? c.stage_code ?? "—"}
                    </td>
                    <td className="px-4 py-3">
                      <OutcomeBadge outcomeCode={c.outcome_code ?? "—"} />
                    </td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)" }}>
                      {truncate(c.notes, 80)}
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

function OutcomeBadge({ outcomeCode }: { outcomeCode: string }) {
  const styles: Record<string, string> = {
    pass: "bg-green-100 text-green-800 border-green-200",
    fail: "bg-red-100 text-red-800 border-red-200",
    partial_pass: "bg-yellow-100 text-yellow-800 border-yellow-200",
    skipped: "bg-slate-100  border-slate-200",
  };
  const cls = styles[outcomeCode] ?? "bg-slate-100  border-slate-200";
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${cls}`}
    >
      {outcomeCode}
    </span>
  );
}

function truncate(value: string | null, max: number): string {
  if (!value) return "—";
  if (value.length <= max) return value;
  return `${value.slice(0, max)}…`;
}
