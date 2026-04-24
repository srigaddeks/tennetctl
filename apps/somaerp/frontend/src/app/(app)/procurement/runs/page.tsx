"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  listKitchens,
  listProcurementRuns,
  listSuppliers,
} from "@/lib/api";
import type {
  Kitchen,
  ProcurementRun,
  ProcurementRunStatus,
  Supplier,
} from "@/types/api";

type RunsState =
  | { status: "loading" }
  | { status: "ok"; items: ProcurementRun[] }
  | { status: "error"; message: string };

const STATUSES: ReadonlyArray<ProcurementRunStatus | ""> = [
  "active",
  "reconciled",
  "cancelled",
];

export default function ProcurementRunsListPage() {
  const [runs, setRuns] = useState<RunsState>({ status: "loading" });
  const [kitchens, setKitchens] = useState<Kitchen[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);

  const [kitchenId, setKitchenId] = useState<string>("");
  const [supplierId, setSupplierId] = useState<string>("");
  const [status, setStatus] = useState<ProcurementRunStatus | "">("");
  const [dateFrom, setDateFrom] = useState<string>("");
  const [dateTo, setDateTo] = useState<string>("");

  useEffect(() => {
    let cancelled = false;
    listKitchens()
      .then((items) => {
        if (!cancelled) setKitchens(items);
      })
      .catch(() => undefined);
    listSuppliers()
      .then((items) => {
        if (!cancelled) setSuppliers(items);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    setRuns({ status: "loading" });
    listProcurementRuns({
      kitchen_id: kitchenId || undefined,
      supplier_id: supplierId || undefined,
      status: status || undefined,
      run_date_from: dateFrom || undefined,
      run_date_to: dateTo || undefined,
    })
      .then((items) => {
        if (!cancelled) setRuns({ status: "ok", items });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : "Unknown error";
        setRuns({ status: "error", message });
      });
    return () => {
      cancelled = true;
    };
  }, [kitchenId, supplierId, status, dateFrom, dateTo]);

  return (
    <div className="max-w-5xl">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="mt-2 text-3xl font-bold tracking-tight">
            Procurement Runs
          </h1>
          <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
            One row per shopping trip. Open a run to add line items.
          </p>
        </div>
        <Link
          href="/procurement/runs/new"
          className="inline-flex items-center justify-center rounded px-3 py-1.5 text-sm font-medium" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
        >
          + New Run
        </Link>
      </div>

      <div className="mb-4 flex flex-wrap gap-3 rounded border p-4" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        <label className="flex flex-col text-xs font-semibold uppercase tracking-wide ">
          Kitchen
          <select
            value={kitchenId}
            onChange={(e) => setKitchenId(e.target.value)}
            className="mt-1 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm "
          >
            <option value="">All kitchens</option>
            {kitchens.map((k) => (
              <option key={k.id} value={k.id}>
                {k.name}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col text-xs font-semibold uppercase tracking-wide ">
          Supplier
          <select
            value={supplierId}
            onChange={(e) => setSupplierId(e.target.value)}
            className="mt-1 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm "
          >
            <option value="">All suppliers</option>
            {suppliers.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col text-xs font-semibold uppercase tracking-wide ">
          Status
          <select
            value={status}
            onChange={(e) =>
              setStatus(e.target.value as ProcurementRunStatus | "")
            }
            className="mt-1 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm "
          >
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s === "" ? "All" : s}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col text-xs font-semibold uppercase tracking-wide ">
          Date from
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="mt-1 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm"
          />
        </label>
        <label className="flex flex-col text-xs font-semibold uppercase tracking-wide ">
          Date to
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="mt-1 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm"
          />
        </label>
      </div>

      <div className="rounded border overflow-hidden" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        {runs.status === "loading" && (
          <p className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>Loading runs…</p>
        )}
        {runs.status === "error" && (
          <div className="m-4 rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            <p className="font-semibold">Failed to load runs</p>
            <p className="mt-1 text-sm opacity-80">{runs.message}</p>
          </div>
        )}
        {runs.status === "ok" && runs.items.length === 0 && (
          <div className="p-8 text-center text-sm" style={{ color: "var(--text-muted)" }}>
            <p>No procurement runs yet.</p>
            <Link
              href="/procurement/runs/new"
              className="mt-2 inline-block text-sm  underline hover:no-underline"
            >
              Record the first run
            </Link>
          </div>
        )}
        {runs.status === "ok" && runs.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead style={{ backgroundColor: "var(--bg-table-header)", borderBottom: "1px solid var(--border)" }}>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Date</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Kitchen</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Supplier</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Lines</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Total</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Status</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}></th>
                </tr>
              </thead>
              <tbody >
                {runs.items.map((r) => (
                  <tr key={r.id} onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-table-hover)"; }} onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "transparent"; }}>
                    <td className="px-4 py-2.5 font-mono" style={{ color: "var(--text-secondary)" }}>
                      {r.run_date}
                    </td>
                    <td className="px-4 py-3 ">
                      {r.kitchen_name ?? r.kitchen_id}
                    </td>
                    <td className="px-4 py-3 ">
                      {r.supplier_name ?? r.supplier_id}
                    </td>
                    <td className="px-4 py-2.5 font-mono" style={{ color: "var(--text-secondary)" }}>
                      {r.line_count}
                    </td>
                    <td className="px-4 py-2.5 font-mono" style={{ color: "var(--text-secondary)" }}>
                      {r.currency_code} {Number.parseFloat(r.total_cost).toFixed(2)}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={r.status} />
                    </td>
                    <td className="px-4 py-3">
                      <Link
                        href={`/procurement/runs/${r.id}`}
                        className="text-sm  underline hover:no-underline"
                      >
                        Open
                      </Link>
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
