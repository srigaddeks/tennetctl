"use client";

import Link from "next/link";
import { useState } from "react";
import { downloadComplianceCsv, listComplianceBatches } from "@/lib/api";
import type { ComplianceBatchRow } from "@/types/api";

function firstOfMonthIso(): string {
  const d = new Date();
  d.setDate(1);
  return d.toISOString().slice(0, 10);
}

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

export default function ComplianceExportPage() {
  const [from, setFrom] = useState<string>(() => firstOfMonthIso());
  const [to, setTo] = useState<string>(() => todayIso());
  const [productId, setProductId] = useState("");
  const [rows, setRows] = useState<ComplianceBatchRow[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadJson = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listComplianceBatches({
        from,
        to,
        product_id: productId || undefined,
      });
      setRows(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const triggerCsv = async () => {
    setDownloading(true);
    setError(null);
    try {
      const blob = await downloadComplianceCsv({
        from,
        to,
        product_id: productId || undefined,
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `fssai-compliance-${from}-${to}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <h1 className="mt-2 text-3xl font-bold tracking-tight">
          FSSAI Compliance Export
        </h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          One row per batch with lot numbers + QC results. Export for
          regulatory audit.
        </p>
      </div>

      <form
        className="mb-6 grid grid-cols-1 gap-3 rounded-lg border border-slate-200 bg-white p-4 sm:grid-cols-5"
        onSubmit={(e) => {
          e.preventDefault();
          loadJson();
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
          <div className="mb-1 font-medium ">Product ID</div>
          <input
            type="text"
            placeholder="optional"
            className="w-full rounded border border-slate-300 px-2 py-1 text-sm"
            value={productId}
            onChange={(e) => setProductId(e.target.value)}
          />
        </label>
        <button
          type="submit"
          className="self-end rounded bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-700"
          disabled={loading}
        >
          {loading ? "Loading…" : "View as JSON"}
        </button>
        <button
          type="button"
          onClick={triggerCsv}
          className="self-end rounded border border-slate-900 bg-white px-3 py-1.5 text-sm font-medium  hover:bg-slate-900 hover:text-white"
          disabled={downloading}
        >
          {downloading ? "Preparing…" : "Download CSV"}
        </button>
      </form>

      {error && (
        <div className="mb-4 rounded border border-red-300 bg-red-50 p-4 text-sm text-red-800">
          {error}
        </div>
      )}

      {rows !== null && (
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 text-xs uppercase ">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Batch</th>
                <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Run Date</th>
                <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Kitchen</th>
                <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Product</th>
                <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Recipe v</th>
                <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Planned</th>
                <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Actual</th>
                <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Lot Numbers</th>
                <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>QC Results</th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 && (
                <tr>
                  <td
                    colSpan={9}
                    className="px-3 py-6 text-center text-sm" style={{ color: "var(--text-muted)" }}
                  >
                    No batches in the selected window.
                  </td>
                </tr>
              )}
              {rows.map((r) => (
                <tr key={r.batch_id} className="border-t border-slate-100">
                  <td className="px-3 py-2 font-mono text-xs" style={{ color: "var(--text-secondary)" }}>
                    {r.batch_id.slice(0, 8)}…
                  </td>
                  <td className="px-3 py-2 font-mono">{r.run_date}</td>
                  <td className="px-3 py-2">{r.kitchen_name ?? "—"}</td>
                  <td className="px-3 py-2">{r.product_name ?? "—"}</td>
                  <td className="px-3 py-2 text-right tabular-nums">
                    {r.recipe_version ?? "—"}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums">
                    {r.planned_qty}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums">
                    {r.actual_qty ?? "—"}
                  </td>
                  <td className="px-3 py-2">
                    {r.lot_numbers.length === 0
                      ? "—"
                      : r.lot_numbers.join(", ")}
                  </td>
                  <td className="px-3 py-2">
                    {r.qc_results.length === 0 ? (
                      "—"
                    ) : (
                      <span className="text-xs ">
                        {r.qc_results.length} result
                        {r.qc_results.length === 1 ? "" : "s"}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
