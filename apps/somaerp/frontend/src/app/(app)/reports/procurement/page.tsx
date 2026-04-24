"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { listProcurementSpend } from "@/lib/api";
import type { ProcurementSpendPoint } from "@/types/api";

function firstOfMonthIso(monthsBack: number): string {
  const d = new Date();
  d.setMonth(d.getMonth() - monthsBack);
  d.setDate(1);
  return d.toISOString().slice(0, 10);
}

function lastOfMonthIso(): string {
  const d = new Date();
  d.setMonth(d.getMonth() + 1);
  d.setDate(0);
  return d.toISOString().slice(0, 10);
}

export default function ProcurementSpendPage() {
  const [from, setFrom] = useState<string>(() => firstOfMonthIso(5));
  const [to, setTo] = useState<string>(() => lastOfMonthIso());
  const [kitchenId, setKitchenId] = useState("");
  const [supplierId, setSupplierId] = useState("");
  const [rows, setRows] = useState<ProcurementSpendPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listProcurementSpend({
        from,
        to,
        kitchen_id: kitchenId || undefined,
        supplier_id: supplierId || undefined,
        bucket: "monthly",
      });
      setRows(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const totals = useMemo(() => {
    let total = 0;
    let currency: string | null = null;
    let runs = 0;
    let lines = 0;
    for (const r of rows) {
      total += Number(r.total_spend || 0);
      runs += r.run_count;
      lines += r.line_count;
      currency = currency ?? r.currency_code;
    }
    return { total, currency, runs, lines };
  }, [rows]);

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <h1 className="mt-2 text-3xl font-bold tracking-tight">
          Procurement Spend — Monthly
        </h1>
      </div>

      <form
        className="mb-6 grid grid-cols-1 gap-3 rounded-lg border border-slate-200 bg-white p-4 sm:grid-cols-5"
        onSubmit={(e) => {
          e.preventDefault();
          load();
        }}
      >
        <label className="text-xs">
          <div className="mb-1 font-medium ">From</div>
          <input
            type="date"
            className="w-full rounded border border-slate-300 px-2 py-1 text-sm"
            value={from}
            onChange={(e) => setFrom(e.target.value)}
          />
        </label>
        <label className="text-xs">
          <div className="mb-1 font-medium ">To</div>
          <input
            type="date"
            className="w-full rounded border border-slate-300 px-2 py-1 text-sm"
            value={to}
            onChange={(e) => setTo(e.target.value)}
          />
        </label>
        <label className="text-xs">
          <div className="mb-1 font-medium ">Kitchen ID</div>
          <input
            type="text"
            className="w-full rounded border border-slate-300 px-2 py-1 text-sm"
            value={kitchenId}
            onChange={(e) => setKitchenId(e.target.value)}
          />
        </label>
        <label className="text-xs">
          <div className="mb-1 font-medium ">Supplier ID</div>
          <input
            type="text"
            className="w-full rounded border border-slate-300 px-2 py-1 text-sm"
            value={supplierId}
            onChange={(e) => setSupplierId(e.target.value)}
          />
        </label>
        <button
          type="submit"
          className="self-end rounded bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-700"
          disabled={loading}
        >
          {loading ? "Loading…" : "Run"}
        </button>
      </form>

      {error && (
        <div className="mb-4 rounded border border-red-300 bg-red-50 p-4 text-sm text-red-800">
          {error}
        </div>
      )}

      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-xs uppercase ">
            <tr>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Month</th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Kitchen</th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Supplier</th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Runs</th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Lines</th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Total Spend</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && !loading && (
              <tr>
                <td
                  colSpan={6}
                  className="px-3 py-6 text-center text-sm" style={{ color: "var(--text-muted)" }}
                >
                  No procurement runs in the selected window.
                </td>
              </tr>
            )}
            {rows.map((r) => (
              <tr
                key={`${r.year_month}-${r.kitchen_id}-${r.supplier_id}`}
                className="border-t border-slate-100"
              >
                <td className="px-3 py-2 font-mono">{r.year_month}</td>
                <td className="px-3 py-2">{r.kitchen_name ?? "—"}</td>
                <td className="px-3 py-2">{r.supplier_name ?? "—"}</td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {r.run_count}
                </td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {r.line_count}
                </td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {r.currency_code ?? ""} {Number(r.total_spend).toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
          {rows.length > 0 && (
            <tfoot>
              <tr className="border-t-2 border-slate-300 bg-slate-50 font-semibold">
                <td colSpan={3} className="px-3 py-2 text-right">
                  Total
                </td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {totals.runs}
                </td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {totals.lines}
                </td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {totals.currency ?? ""} {totals.total.toFixed(2)}
                </td>
              </tr>
            </tfoot>
          )}
        </table>
      </div>
    </div>
  );
}
