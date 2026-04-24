"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getBatch,
  listQcCheckpoints,
  listQcOutcomes,
  patchBatch,
  patchBatchConsumption,
  patchBatchStep,
  recordBatchQc,
} from "@/lib/api";
import type {
  BatchConsumptionLine,
  BatchDetail,
  BatchQcResult,
  BatchStepLog,
  BatchSummary,
  ProductionBatch,
  ProductionBatchStatus,
  QcCheckpoint,
  QcOutcome,
} from "@/types/api";

type LoadState =
  | { status: "loading" }
  | { status: "ok"; detail: BatchDetail }
  | { status: "error"; message: string };

const STATUS_STYLES: Record<ProductionBatchStatus, string> = {
  planned: "bg-slate-200 text-slate-800",
  in_progress: "bg-amber-200 text-amber-900 animate-pulse",
  completed: "bg-emerald-200 text-emerald-900",
  cancelled: "bg-rose-200 text-rose-900",
};

function formatDecimal(
  val: string | null | undefined,
  digits = 2
): string {
  if (val === null || val === undefined || val === "") return "—";
  const n = Number.parseFloat(val);
  if (!Number.isFinite(n)) return val ?? "—";
  return n.toFixed(digits);
}

export default function BatchDetailPage() {
  const params = useParams<{ id: string }>();
  const batchId = params.id;
  const [state, setState] = useState<LoadState>({ status: "loading" });
  const [actualQtyInput, setActualQtyInput] = useState<string>("");
  const [notesInput, setNotesInput] = useState<string>("");
  const [checkpoints, setCheckpoints] = useState<QcCheckpoint[]>([]);
  const [outcomes, setOutcomes] = useState<QcOutcome[]>([]);
  const [confirmAction, setConfirmAction] = useState<
    "complete" | "cancel" | null
  >(null);
  const [mutating, setMutating] = useState<boolean>(false);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const detail = await getBatch(batchId);
      setState({ status: "ok", detail });
      if (detail.batch.actual_qty) setActualQtyInput(detail.batch.actual_qty);
      setNotesInput(detail.batch.notes ?? "");
    } catch (e: unknown) {
      setState({
        status: "error",
        message: e instanceof Error ? e.message : "Unknown error",
      });
    }
  }, [batchId]);

  useEffect(() => {
    void load();
    void listQcCheckpoints({ status: "active", limit: 100 })
      .then(setCheckpoints)
      .catch(() => setCheckpoints([]));
    void listQcOutcomes().then(setOutcomes).catch(() => setOutcomes([]));
  }, [load]);

  async function doTransition(
    status: ProductionBatchStatus,
    extra?: { actual_qty?: number; cancel_reason?: string }
  ) {
    setErr(null);
    setMutating(true);
    try {
      await patchBatch(batchId, {
        status,
        ...(extra?.actual_qty !== undefined
          ? { actual_qty: extra.actual_qty }
          : {}),
        ...(extra?.cancel_reason ? { cancel_reason: extra.cancel_reason } : {}),
      });
      await load();
      setConfirmAction(null);
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setMutating(false);
    }
  }

  async function onStepPatch(
    step: BatchStepLog,
    partial: { started_at?: string; completed_at?: string; notes?: string }
  ) {
    setErr(null);
    try {
      await patchBatchStep(batchId, step.id, partial);
      await load();
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Unknown error");
    }
  }

  async function onConsumptionPatch(
    line: BatchConsumptionLine,
    partial: { actual_qty?: number; lot_number?: string }
  ) {
    setErr(null);
    try {
      await patchBatchConsumption(batchId, line.id, partial);
      await load();
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Unknown error");
    }
  }

  async function onQcRecord(
    checkpointId: string,
    outcomeCode: "pass" | "fail"
  ) {
    const outcome = outcomes.find((o) => o.code === outcomeCode);
    if (!outcome) return;
    setErr(null);
    try {
      await recordBatchQc(batchId, {
        checkpoint_id: checkpointId,
        outcome_id: outcome.id,
      });
      await load();
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Unknown error");
    }
  }

  async function onNotesSave() {
    setErr(null);
    try {
      await patchBatch(batchId, { notes: notesInput });
      await load();
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Unknown error");
    }
  }

  if (state.status === "loading") {
    return (
      <div className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>Loading batch…</div>
    );
  }
  if (state.status === "error") {
    return (
      <div className="p-6">
        <Link
          href="/production/batches"
          className="text-sm" style={{ color: "var(--text-secondary)" }}
        >
          ← Batches
        </Link>
        <div className="mt-4 rounded border border-red-300 bg-red-50 p-4">
          <p className="font-semibold">Error</p>
          <p className="mt-1 text-sm opacity-80">{state.message}</p>
        </div>
      </div>
    );
  }

  const { detail } = state;
  const batch = detail.batch;
  const summary = detail.summary;

  return (
    <div className="max-w-5xl">
      {/* Sticky top: status + primary action */}
      <div className="sticky top-0 z-20 border-b border-slate-200 bg-white px-4 py-3 shadow-sm sm:px-6">
        <div className="flex items-center justify-between gap-3">
          <div>
            <Link
              href="/production/batches"
              className="text-xs text-sm" style={{ color: "var(--text-secondary)" }}
            >
              ← Batches
            </Link>
            <div className="mt-0.5 flex items-center gap-2">
              <span
                className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide ${STATUS_STYLES[batch.status]}`}
              >
                {batch.status.replace("_", " ")}
              </span>
              <span className="text-sm font-medium text-slate-800">
                {batch.product_name ?? "—"}
              </span>
            </div>
          </div>
          <PrimaryAction
            batch={batch}
            mutating={mutating}
            onStart={() => void doTransition("in_progress")}
            onComplete={() => setConfirmAction("complete")}
            onCancel={() => setConfirmAction("cancel")}
          />
        </div>
        {err && (
          <div className="mt-2 rounded bg-red-50 px-3 py-1.5 text-xs text-red-700">
            {err}
          </div>
        )}
      </div>

      <div className="mx-auto max-w-5xl space-y-4 p-4 sm:p-6">
        {/* Metrics */}
        <MetricsRow summary={summary} />

        {/* Info row */}
        <InfoRow batch={batch} />

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {/* Steps */}
          <div className="rounded border p-4" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide ">
              Steps ({detail.steps.filter((s) => s.completed_at).length}/
              {detail.steps.length})
            </h2>
            <ol className="space-y-2">
              {detail.steps.map((step, idx) => {
                const prevCompleted =
                  idx === 0 ||
                  detail.steps[idx - 1]?.completed_at !== null;
                return (
                  <StepCard
                    key={step.id}
                    step={step}
                    prevCompleted={prevCompleted}
                    batchStatus={batch.status}
                    onStart={() =>
                      void onStepPatch(step, {
                        started_at: new Date().toISOString(),
                      })
                    }
                    onComplete={() =>
                      void onStepPatch(step, {
                        completed_at: new Date().toISOString(),
                      })
                    }
                  />
                );
              })}
            </ol>
          </div>

          {/* Consumption */}
          <div className="rounded border p-4" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide ">
              Consumption ({detail.consumption.length})
            </h2>
            <ul className="space-y-2">
              {detail.consumption.map((line) => (
                <ConsumptionRow
                  key={line.id}
                  line={line}
                  locked={batch.status === "completed" || batch.status === "cancelled"}
                  onSave={(payload) => void onConsumptionPatch(line, payload)}
                />
              ))}
            </ul>
          </div>
        </div>

        {/* QC */}
        <div className="rounded border p-4" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide ">
            QC Checkpoints
          </h2>
          <QcPanel
            checkpoints={checkpoints}
            results={detail.qc_results}
            onRecord={onQcRecord}
          />
        </div>

        {/* Actual qty + complete */}
        {batch.status === "in_progress" && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 shadow-sm">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-amber-900">
              Close out batch
            </h2>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
              <label className="flex-1 text-sm">
                <span className="mb-1 block font-medium ">
                  Actual qty (bottles produced)
                </span>
                <input
                  type="number"
                  min="0"
                  step="1"
                  value={actualQtyInput}
                  onChange={(e) => setActualQtyInput(e.target.value)}
                  className="w-full rounded border border-slate-300 bg-white px-3 py-2 text-lg"
                  placeholder={`e.g. ${batch.planned_qty}`}
                />
              </label>
              <button
                type="button"
                disabled={
                  mutating ||
                  !Number.isFinite(Number.parseFloat(actualQtyInput))
                }
                onClick={() => setConfirmAction("complete")}
                className="rounded-md bg-emerald-600 px-5 py-3 text-sm font-semibold text-white hover:bg-emerald-700 disabled:bg-slate-300"
              >
                Complete Batch
              </button>
            </div>
          </div>
        )}

        {/* Notes */}
        <div className="rounded border p-4" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
          <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide ">
            Notes
          </h2>
          <textarea
            value={notesInput}
            onChange={(e) => setNotesInput(e.target.value)}
            onBlur={() => {
              if (notesInput !== (batch.notes ?? "")) void onNotesSave();
            }}
            rows={3}
            className="w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm"
            placeholder="Operator notes"
            disabled={batch.status === "completed"}
          />
        </div>
      </div>

      {/* Confirm modal */}
      {confirmAction && (
        <ConfirmModal
          action={confirmAction}
          batch={batch}
          actualQty={actualQtyInput}
          mutating={mutating}
          onClose={() => setConfirmAction(null)}
          onConfirm={(payload) => {
            if (confirmAction === "complete") {
              void doTransition("completed", {
                actual_qty: Number.parseFloat(actualQtyInput),
              });
            } else {
              void doTransition("cancelled", {
                cancel_reason: payload.reason,
              });
            }
          }}
        />
      )}
    </div>
  );
}

function PrimaryAction({
  batch,
  mutating,
  onStart,
  onComplete,
  onCancel,
}: {
  batch: ProductionBatch;
  mutating: boolean;
  onStart: () => void;
  onComplete: () => void;
  onCancel: () => void;
}) {
  if (batch.status === "planned") {
    return (
      <div className="flex items-center gap-2">
        <button
          onClick={onStart}
          disabled={mutating}
          className="rounded-md bg-amber-500 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-600 disabled:bg-slate-300"
        >
          Start Batch
        </button>
        <button
          onClick={onCancel}
          disabled={mutating}
          className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-semibold  hover:bg-slate-50"
        >
          Cancel
        </button>
      </div>
    );
  }
  if (batch.status === "in_progress") {
    return (
      <div className="flex items-center gap-2">
        <button
          onClick={onComplete}
          disabled={mutating}
          className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:bg-slate-300"
        >
          Complete
        </button>
        <button
          onClick={onCancel}
          disabled={mutating}
          className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-semibold  hover:bg-slate-50"
        >
          Cancel
        </button>
      </div>
    );
  }
  return (
    <div className="text-xs text-sm" style={{ color: "var(--text-muted)" }}>
      {batch.status === "completed"
        ? "Batch completed"
        : "Batch cancelled"}
    </div>
  );
}

function MetricsRow({ summary }: { summary: BatchSummary | null }) {
  if (!summary) return null;
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
      <Metric
        label="Yield %"
        value={formatDecimal(summary.yield_pct, 1)}
        suffix="%"
      />
      <Metric
        label="COGS / bottle"
        value={formatDecimal(summary.cogs_per_unit, 2)}
        prefix={summary.currency_code}
      />
      <Metric
        label="Gross margin"
        value={formatDecimal(summary.gross_margin_pct, 1)}
        suffix="%"
      />
      <Metric
        label="Duration"
        value={formatDecimal(summary.duration_min, 0)}
        suffix="min"
      />
    </div>
  );
}

function Metric({
  label,
  value,
  suffix,
  prefix,
}: {
  label: string;
  value: string;
  suffix?: string;
  prefix?: string;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-sm">
      <div className="text-[10px] font-semibold uppercase tracking-wider text-sm" style={{ color: "var(--text-muted)" }}>
        {label}
      </div>
      <div className="mt-0.5 font-mono text-lg ">
        {prefix ? <span className="text-xs text-sm" style={{ color: "var(--text-muted)" }}>{prefix} </span> : null}
        {value}
        {suffix ? <span className="text-xs text-sm" style={{ color: "var(--text-muted)" }}> {suffix}</span> : null}
      </div>
    </div>
  );
}

function InfoRow({ batch }: { batch: ProductionBatch }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3 text-sm shadow-sm">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between text-left"
      >
        <span className="font-medium ">
          {batch.kitchen_name ?? "—"} · v{batch.recipe_version ?? "?"} · run{" "}
          {batch.run_date}
        </span>
        <span className="text-xs text-sm" style={{ color: "var(--text-muted)" }}>
          {open ? "Hide" : "Details"}
        </span>
      </button>
      {open && (
        <dl className="mt-3 grid grid-cols-2 gap-x-3 gap-y-1 text-xs">
          <dt className="text-sm" style={{ color: "var(--text-muted)" }}>Kitchen</dt>
          <dd>{batch.kitchen_name ?? "—"}</dd>
          <dt className="text-sm" style={{ color: "var(--text-muted)" }}>Product</dt>
          <dd>{batch.product_name ?? "—"}</dd>
          <dt className="text-sm" style={{ color: "var(--text-muted)" }}>Recipe</dt>
          <dd>
            v{batch.recipe_version ?? "?"} · {batch.recipe_status ?? "?"}
          </dd>
          <dt className="text-sm" style={{ color: "var(--text-muted)" }}>Shift</dt>
          <dd>
            {batch.shift_start ?? "—"}
            {batch.shift_end ? ` → ${batch.shift_end}` : ""}
          </dd>
          <dt className="text-sm" style={{ color: "var(--text-muted)" }}>Planned / Actual</dt>
          <dd>
            {batch.planned_qty} / {batch.actual_qty ?? "—"}
          </dd>
          <dt className="text-sm" style={{ color: "var(--text-muted)" }}>Lead</dt>
          <dd>{batch.lead_user_id ?? "—"}</dd>
        </dl>
      )}
    </div>
  );
}

function StepCard({
  step,
  prevCompleted,
  batchStatus,
  onStart,
  onComplete,
}: {
  step: BatchStepLog;
  prevCompleted: boolean;
  batchStatus: ProductionBatchStatus;
  onStart: () => void;
  onComplete: () => void;
}) {
  const canAct = batchStatus === "in_progress";
  const isCompleted = step.completed_at !== null;
  const isStarted = step.started_at !== null && !isCompleted;
  return (
    <li
      className={`rounded-md border px-3 py-2.5 ${
        isCompleted
          ? "border-emerald-200 bg-emerald-50"
          : isStarted
          ? "border-amber-200 bg-amber-50"
          : "border-slate-200 bg-white"
      }`}
    >
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-sm font-semibold">
            {isCompleted && "✓ "}
            {step.step_number}. {step.name}
          </div>
          <div className="mt-0.5 text-xs text-sm" style={{ color: "var(--text-muted)" }}>
            {step.started_at && (
              <span>
                Started {new Date(step.started_at).toLocaleTimeString()}
              </span>
            )}
            {step.completed_at && (
              <span className="ml-2">
                · Done {new Date(step.completed_at).toLocaleTimeString()}
              </span>
            )}
            {step.duration_min && (
              <span className="ml-2">· {formatDecimal(step.duration_min, 1)} min</span>
            )}
          </div>
        </div>
        <div>
          {!isStarted && !isCompleted && (
            <button
              type="button"
              onClick={onStart}
              disabled={!canAct || !prevCompleted}
              className="rounded-md bg-amber-500 px-3 py-1.5 text-xs font-semibold text-white hover:bg-amber-600 disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              Start
            </button>
          )}
          {isStarted && (
            <button
              type="button"
              onClick={onComplete}
              disabled={!canAct}
              className="rounded-md bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-700 disabled:bg-slate-300"
            >
              Complete
            </button>
          )}
        </div>
      </div>
    </li>
  );
}

function ConsumptionRow({
  line,
  locked,
  onSave,
}: {
  line: BatchConsumptionLine;
  locked: boolean;
  onSave: (payload: { actual_qty?: number; lot_number?: string }) => void;
}) {
  const [actualQty, setActualQty] = useState<string>(line.actual_qty ?? "");
  const [lot, setLot] = useState<string>(line.lot_number ?? "");

  useEffect(() => {
    setActualQty(line.actual_qty ?? "");
    setLot(line.lot_number ?? "");
  }, [line.actual_qty, line.lot_number]);

  const commit = () => {
    const payload: { actual_qty?: number; lot_number?: string } = {};
    const parsed = Number.parseFloat(actualQty);
    if (
      Number.isFinite(parsed) &&
      parsed >= 0 &&
      actualQty !== (line.actual_qty ?? "")
    ) {
      payload.actual_qty = parsed;
    }
    if (lot !== (line.lot_number ?? "")) {
      payload.lot_number = lot;
    }
    if (Object.keys(payload).length > 0) onSave(payload);
  };

  const plannedNum = Number.parseFloat(line.planned_qty);
  const actualNum = Number.parseFloat(actualQty);
  const costNum = Number.parseFloat(line.unit_cost_snapshot);
  const lineCost =
    Number.isFinite(actualNum) && Number.isFinite(costNum)
      ? actualNum * costNum
      : null;

  return (
    <li className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="truncate font-medium">
            {line.raw_material_name ?? "—"}
          </div>
          <div className="mt-0.5 text-xs text-sm" style={{ color: "var(--text-muted)" }}>
            Planned {Number.isFinite(plannedNum) ? plannedNum.toFixed(2) : line.planned_qty}{" "}
            {line.unit_code ?? ""} · {line.currency_code}{" "}
            {formatDecimal(line.unit_cost_snapshot, 2)}/unit
          </div>
        </div>
        <div className="text-right font-mono text-xs ">
          {lineCost !== null
            ? `${line.currency_code} ${lineCost.toFixed(2)}`
            : "—"}
        </div>
      </div>
      <div className="mt-2 flex items-center gap-2">
        <div className="flex flex-1 items-center gap-1">
          <button
            type="button"
            disabled={locked}
            onClick={() => {
              const n = Number.parseFloat(actualQty);
              const next = (Number.isFinite(n) ? n : 0) - 1;
              setActualQty(String(Math.max(0, next)));
            }}
            className="rounded border border-slate-300 bg-white px-2 py-1 text-sm font-semibold  disabled:opacity-50"
          >
            –
          </button>
          <input
            type="number"
            min="0"
            step="0.01"
            value={actualQty}
            onChange={(e) => setActualQty(e.target.value)}
            onBlur={commit}
            disabled={locked}
            placeholder={line.planned_qty}
            className="w-full rounded border border-slate-300 bg-white px-2 py-1.5 text-right text-base font-mono disabled:bg-slate-100"
          />
          <button
            type="button"
            disabled={locked}
            onClick={() => {
              const n = Number.parseFloat(actualQty);
              const next = (Number.isFinite(n) ? n : 0) + 1;
              setActualQty(String(next));
            }}
            className="rounded border border-slate-300 bg-white px-2 py-1 text-sm font-semibold  disabled:opacity-50"
          >
            +
          </button>
          <span className="text-xs text-sm" style={{ color: "var(--text-muted)" }}>{line.unit_code ?? ""}</span>
        </div>
        <input
          type="text"
          value={lot}
          onChange={(e) => setLot(e.target.value)}
          onBlur={commit}
          disabled={locked}
          placeholder="Lot #"
          className="w-28 rounded border border-slate-300 bg-white px-2 py-1.5 text-xs font-mono disabled:bg-slate-100"
        />
      </div>
    </li>
  );
}

function QcPanel({
  checkpoints,
  results,
  onRecord,
}: {
  checkpoints: QcCheckpoint[];
  results: BatchQcResult[];
  onRecord: (checkpointId: string, outcome: "pass" | "fail") => void;
}) {
  const byCheckpoint = useMemo(() => {
    const m = new Map<string, BatchQcResult>();
    for (const r of results) m.set(r.checkpoint_id, r);
    return m;
  }, [results]);

  if (checkpoints.length === 0) {
    return (
      <p className="text-sm" style={{ color: "var(--text-muted)" }}>No checkpoints defined for this batch.</p>
    );
  }

  return (
    <ul className="space-y-1.5">
      {checkpoints.map((cp) => {
        const r = byCheckpoint.get(cp.id);
        const isPass = r?.outcome_code === "pass";
        const isFail = r?.outcome_code === "fail";
        return (
          <li
            key={cp.id}
            className="flex items-center justify-between gap-2 rounded border border-slate-200 bg-white px-3 py-2"
          >
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm font-medium">{cp.name}</div>
              <div className="text-xs text-sm" style={{ color: "var(--text-muted)" }}>
                {cp.scope_kind} · {cp.required ? "required" : "optional"}
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => onRecord(cp.id, "pass")}
                className={`rounded px-2.5 py-1 text-xs font-semibold ${
                  isPass
                    ? "bg-emerald-600 text-white"
                    : "bg-emerald-100 text-emerald-800 hover:bg-emerald-200"
                }`}
              >
                Pass
              </button>
              <button
                type="button"
                onClick={() => onRecord(cp.id, "fail")}
                className={`rounded px-2.5 py-1 text-xs font-semibold ${
                  isFail
                    ? "bg-rose-600 text-white"
                    : "bg-rose-100 text-rose-800 hover:bg-rose-200"
                }`}
              >
                Fail
              </button>
              {r && (
                <span className="ml-1 text-[10px] text-slate-400">
                  ×{r.events_count}
                </span>
              )}
            </div>
          </li>
        );
      })}
    </ul>
  );
}

function ConfirmModal({
  action,
  batch,
  actualQty,
  mutating,
  onClose,
  onConfirm,
}: {
  action: "complete" | "cancel";
  batch: ProductionBatch;
  actualQty: string;
  mutating: boolean;
  onClose: () => void;
  onConfirm: (payload: { reason?: string }) => void;
}) {
  const [reason, setReason] = useState<string>("");
  return (
    <div className="fixed inset-0 z-50 flex items-end bg-slate-900/60 p-4 sm:items-center sm:justify-center">
      <div className="w-full max-w-md rounded-lg bg-white p-5 shadow-lg">
        <h3 className="text-lg font-bold">
          {action === "complete" ? "Complete batch?" : "Cancel batch?"}
        </h3>
        <p className="mt-2 text-sm" style={{ color: "var(--text-secondary)" }}>
          {action === "complete"
            ? `Recording ${actualQty || "?"} bottles produced. This will emit inventory consumption movements for each ingredient line.`
            : "Cancelling this batch will stop the workflow. Inventory already consumed is NOT auto-reversed."}
        </p>
        {action === "cancel" && (
          <label className="mt-4 block text-sm">
            <span className="mb-1 block font-medium ">
              Reason
            </span>
            <input
              type="text"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full rounded border border-slate-300 px-3 py-2"
              placeholder="e.g. ingredient unavailable"
            />
          </label>
        )}
        <div className="mt-5 flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            disabled={mutating}
            className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold  hover:bg-slate-50"
          >
            Back
          </button>
          <button
            type="button"
            onClick={() =>
              onConfirm(action === "cancel" ? { reason } : {})
            }
            disabled={mutating}
            className={`rounded-md px-4 py-2 text-sm font-semibold text-white ${
              action === "complete"
                ? "bg-emerald-600 hover:bg-emerald-700"
                : "bg-rose-600 hover:bg-rose-700"
            } disabled:bg-slate-300`}
          >
            {mutating
              ? "Working…"
              : action === "complete"
              ? "Complete Batch"
              : "Cancel Batch"}
          </button>
        </div>
      </div>
    </div>
  );
}
