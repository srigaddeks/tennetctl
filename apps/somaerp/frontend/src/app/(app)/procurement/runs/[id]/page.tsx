"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import {
  addProcurementLine,
  deleteProcurementLine,
  getProcurementRun,
  listProcurementLines,
  listRawMaterials,
  listUnitsOfMeasure,
} from "@/lib/api";
import type {
  ProcurementLine,
  ProcurementRun,
  ProcurementRunStatus,
  RawMaterial,
  UnitOfMeasure,
} from "@/types/api";

type RunState =
  | { status: "loading" }
  | { status: "ok"; run: ProcurementRun }
  | { status: "error"; message: string };

type LinesState =
  | { status: "loading" }
  | { status: "ok"; items: ProcurementLine[] }
  | { status: "error"; message: string };

type NewLine = {
  raw_material_id: string;
  quantity: string;
  unit_id: string;
  unit_cost: string;
  lot_number: string;
  quality_grade: string;
};

export default function ProcurementRunDetailPage() {
  const params = useParams<{ id: string }>();
  const runId = params?.id ?? ""

  const [run, setRun] = useState<RunState>({ status: "loading" });
  const [lines, setLines] = useState<LinesState>({ status: "loading" });
  const [materials, setMaterials] = useState<RawMaterial[]>([]);
  const [units, setUnits] = useState<UnitOfMeasure[]>([]);
  const [draft, setDraft] = useState<NewLine>({
    raw_material_id: "",
    quantity: "",
    unit_id: "",
    unit_cost: "",
    lot_number: "",
    quality_grade: "",
  });
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState<boolean>(false);

  const loadRun = useCallback(() => {
    if (!runId) return;
    setRun({ status: "loading" });
    getProcurementRun(runId)
      .then((r) => setRun({ status: "ok", run: r }))
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : "Unknown error";
        setRun({ status: "error", message });
      });
  }, [runId]);

  const loadLines = useCallback(() => {
    if (!runId) return;
    setLines({ status: "loading" });
    listProcurementLines(runId)
      .then((items) => setLines({ status: "ok", items }))
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : "Unknown error";
        setLines({ status: "error", message });
      });
  }, [runId]);

  useEffect(() => {
    loadRun();
    loadLines();
    listRawMaterials()
      .then(setMaterials)
      .catch(() => undefined);
    listUnitsOfMeasure()
      .then(setUnits)
      .catch(() => undefined);
  }, [loadRun, loadLines]);

  async function onAddLine() {
    setFormError(null);
    const qty = Number.parseFloat(draft.quantity);
    const unitId = Number.parseInt(draft.unit_id, 10);
    const cost = Number.parseFloat(draft.unit_cost);
    const grade = draft.quality_grade.trim() === "" ? null
      : Number.parseInt(draft.quality_grade, 10);
    if (!draft.raw_material_id) {
      setFormError("Pick a raw material");
      return;
    }
    if (!Number.isFinite(qty) || qty <= 0) {
      setFormError("Quantity must be a positive number");
      return;
    }
    if (!Number.isFinite(unitId)) {
      setFormError("Pick a unit");
      return;
    }
    if (!Number.isFinite(cost) || cost < 0) {
      setFormError("Unit cost must be a non-negative number");
      return;
    }
    setBusy(true);
    try {
      await addProcurementLine(runId, {
        raw_material_id: draft.raw_material_id,
        quantity: qty,
        unit_id: unitId,
        unit_cost: cost,
        lot_number: draft.lot_number.trim() === "" ? null : draft.lot_number.trim(),
        quality_grade: grade,
      });
      setDraft({
        raw_material_id: "",
        quantity: "",
        unit_id: "",
        unit_cost: "",
        lot_number: "",
        quality_grade: "",
      });
      loadRun();
      loadLines();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setFormError(message);
    } finally {
      setBusy(false);
    }
  }

  async function onDeleteLine(lineId: string) {
    setBusy(true);
    try {
      await deleteProcurementLine(runId, lineId);
      loadRun();
      loadLines();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setFormError(message);
    } finally {
      setBusy(false);
    }
  }

  const runningTotal =
    lines.status === "ok"
      ? lines.items.reduce(
          (acc, l) => acc + Number.parseFloat(l.line_cost || "0"),
          0,
        )
      : 0;
  const currency = run.status === "ok" ? run.run.currency_code : "INR";

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <h1 className="mt-2 text-3xl font-bold tracking-tight">
          {run.status === "ok"
            ? `${run.run.supplier_name ?? "Supplier"} — ${run.run.run_date}`
            : "Procurement Run"}
        </h1>
      </div>

      {/* Run summary */}
      <div className="mb-6 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        {run.status === "loading" && (
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>Loading run…</p>
        )}
        {run.status === "error" && (
          <div className="rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            <p className="font-semibold">Failed to load run</p>
            <p className="mt-1 text-sm opacity-80">{run.message}</p>
          </div>
        )}
        {run.status === "ok" && (
          <dl className="grid grid-cols-1 gap-4 sm:grid-cols-4">
            <InfoField
              label="Kitchen"
              value={run.run.kitchen_name ?? run.run.kitchen_id}
            />
            <InfoField
              label="Supplier"
              value={run.run.supplier_name ?? run.run.supplier_id}
            />
            <InfoField
              label="Status"
              value={<StatusBadge status={run.run.status} />}
            />
            <InfoField
              label="Lines"
              value={<code className="font-mono">{run.run.line_count}</code>}
            />
            <InfoField
              label="Server Total"
              value={
                <code className="font-mono">
                  {run.run.currency_code} {Number.parseFloat(run.run.total_cost).toFixed(2)}
                </code>
              }
            />
            <InfoField
              label="Computed Total"
              value={
                <code className="font-mono">
                  {run.run.currency_code}{" "}
                  {run.run.computed_total
                    ? Number.parseFloat(run.run.computed_total).toFixed(2)
                    : "0.00"}
                </code>
              }
            />
            {run.run.notes && (
              <div className="sm:col-span-4">
                <dt className="text-xs font-semibold uppercase tracking-wide text-sm" style={{ color: "var(--text-muted)" }}>
                  Notes
                </dt>
                <dd className="mt-1 text-sm ">
                  {run.run.notes}
                </dd>
              </div>
            )}
          </dl>
        )}
      </div>

      {/* Lines table with inline add-row */}
      <div className="mb-6 rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="flex items-center justify-between px-4 py-3" style={{ borderBottom: "1px solid var(--border)" }}>
          <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Lines</h2>
        </div>
        {lines.status === "loading" && (
          <p className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>Loading lines…</p>
        )}
        {lines.status === "error" && (
          <div className="m-4 rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            <p className="font-semibold">Failed to load lines</p>
            <p className="mt-1 text-sm opacity-80">{lines.message}</p>
          </div>
        )}
        {lines.status === "ok" && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead style={{ backgroundColor: "var(--bg-table-header)", borderBottom: "1px solid var(--border)" }}>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Raw Material</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Quantity</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Unit</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Unit Cost</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Line Cost</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Lot #</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Grade</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}></th>
                </tr>
              </thead>
              <tbody >
                {lines.items.map((l) => (
                  <tr key={l.id} onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-table-hover)"; }} onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "transparent"; }}>
                    <td className="px-4 py-3 ">
                      {l.raw_material_name ?? l.raw_material_id}
                    </td>
                    <td className="px-4 py-2.5 font-mono" style={{ color: "var(--text-secondary)" }}>
                      {l.quantity}
                    </td>
                    <td className="px-4 py-2.5 font-mono" style={{ color: "var(--text-secondary)" }}>
                      {l.unit_code ?? l.unit_id}
                    </td>
                    <td className="px-4 py-2.5 font-mono" style={{ color: "var(--text-secondary)" }}>
                      {Number.parseFloat(l.unit_cost).toFixed(2)}
                    </td>
                    <td className="px-4 py-3 font-mono ">
                      {Number.parseFloat(l.line_cost).toFixed(2)}
                    </td>
                    <td className="px-4 py-2.5 font-mono" style={{ color: "var(--text-secondary)" }}>
                      {l.lot_number ?? "—"}
                    </td>
                    <td className="px-4 py-2.5 font-mono" style={{ color: "var(--text-secondary)" }}>
                      {l.quality_grade ?? "—"}
                    </td>
                    <td className="px-4 py-3">
                      <button
                        type="button"
                        onClick={() => onDeleteLine(l.id)}
                        disabled={busy}
                        className="rounded-md border border-slate-300 bg-white px-3 py-1 text-xs font-medium  shadow-sm hover:bg-slate-50 disabled:opacity-50"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
                {/* Add-row */}
                <tr className="bg-slate-50/50">
                  <td className="px-4 py-3">
                    <select
                      value={draft.raw_material_id}
                      onChange={(e) =>
                        setDraft((prev) => ({
                          ...prev,
                          raw_material_id: e.target.value,
                        }))
                      }
                      className="w-full rounded border px-2 py-1 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
                    >
                      <option value="">Pick…</option>
                      {materials.map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.name}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="px-4 py-3">
                    <input
                      type="number"
                      step="0.001"
                      value={draft.quantity}
                      onChange={(e) =>
                        setDraft((prev) => ({
                          ...prev,
                          quantity: e.target.value,
                        }))
                      }
                      placeholder="1.5"
                      className="w-24 rounded-md border border-slate-300 bg-white px-2 py-1 font-mono text-sm"
                    />
                  </td>
                  <td className="px-4 py-3">
                    <select
                      value={draft.unit_id}
                      onChange={(e) =>
                        setDraft((prev) => ({
                          ...prev,
                          unit_id: e.target.value,
                        }))
                      }
                      className="rounded-md border border-slate-300 bg-white px-2 py-1 text-sm"
                    >
                      <option value="">Unit…</option>
                      {units.map((u) => (
                        <option key={u.id} value={u.id}>
                          {u.code}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="px-4 py-3">
                    <input
                      type="number"
                      step="0.01"
                      value={draft.unit_cost}
                      onChange={(e) =>
                        setDraft((prev) => ({
                          ...prev,
                          unit_cost: e.target.value,
                        }))
                      }
                      placeholder="20.00"
                      className="w-24 rounded-md border border-slate-300 bg-white px-2 py-1 font-mono text-sm"
                    />
                  </td>
                  <td className="px-4 py-3 text-xs text-sm" style={{ color: "var(--text-muted)" }}>auto</td>
                  <td className="px-4 py-3">
                    <input
                      type="text"
                      value={draft.lot_number}
                      onChange={(e) =>
                        setDraft((prev) => ({
                          ...prev,
                          lot_number: e.target.value,
                        }))
                      }
                      placeholder="KPHB-001"
                      className="w-28 rounded-md border border-slate-300 bg-white px-2 py-1 text-sm"
                    />
                  </td>
                  <td className="px-4 py-3">
                    <input
                      type="number"
                      min={1}
                      max={5}
                      value={draft.quality_grade}
                      onChange={(e) =>
                        setDraft((prev) => ({
                          ...prev,
                          quality_grade: e.target.value,
                        }))
                      }
                      placeholder="1-5"
                      className="w-16 rounded-md border border-slate-300 bg-white px-2 py-1 text-sm"
                    />
                  </td>
                  <td className="px-4 py-3">
                    <button
                      type="button"
                      onClick={onAddLine}
                      disabled={busy}
                      className="rounded-md bg-slate-900 px-3 py-1 text-xs font-medium text-white shadow-sm hover:bg-slate-800 disabled:opacity-50"
                    >
                      Add
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        )}
      </div>

      {formError !== null && (
        <div className="mb-6 rounded border border-red-300 bg-red-50 p-4">
          <p className="font-semibold">Error</p>
          <p className="mt-1 text-sm opacity-80">{formError}</p>
        </div>
      )}
    </div>
  );
}

function InfoField({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase tracking-wide text-sm" style={{ color: "var(--text-muted)" }}>
        {label}
      </dt>
      <dd className="mt-1 text-sm ">{value}</dd>
    </div>
  );
}

function StatusBadge({ status }: { status: ProcurementRunStatus }) {
  const styles: Record<ProcurementRunStatus, string> = {
    active: "bg-green-100 text-green-800 border-green-200",
    reconciled: "bg-slate-100  border-slate-200",
    cancelled: "bg-red-100 text-red-800 border-red-200",
  };
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${styles[status]}`}
    >
      {status}
    </span>
  );
}
