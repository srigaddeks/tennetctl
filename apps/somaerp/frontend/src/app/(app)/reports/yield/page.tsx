"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listCogsTrends, listYieldTrends } from "@/lib/api";
import type {
  CogsTrendPoint,
  ReportBucket,
  YieldTrendPoint,
} from "@/types/api";

function isoDaysAgo(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().slice(0, 10);
}

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

type Row = {
  key: string;
  date: string;
  kitchen_name: string | null;
  product_name: string | null;
  planned_qty: string;
  actual_qty: string;
  yield_pct: string | null;
  batch_count: number;
  total_cogs: string | null;
  cogs_per_unit: string | null;
  currency_code: string | null;
};

function merge(
  yields: YieldTrendPoint[],
  cogs: CogsTrendPoint[],
): Row[] {
  const byKey = new Map<string, Row>();
  for (const y of yields) {
    const key = `${y.date}|${y.kitchen_id}|${y.product_id}`;
    byKey.set(key, {
      key,
      date: y.date,
      kitchen_name: y.kitchen_name,
      product_name: y.product_name,
      planned_qty: y.planned_qty,
      actual_qty: y.actual_qty,
      yield_pct: y.yield_pct,
      batch_count: y.batch_count,
      total_cogs: null,
      cogs_per_unit: null,
      currency_code: null,
    });
  }
  for (const c of cogs) {
    const key = `${c.date}|${c.kitchen_id}|${c.product_id}`;
    const existing = byKey.get(key);
    if (existing) {
      byKey.set(key, {
        ...existing,
        total_cogs: c.total_cogs,
        cogs_per_unit: c.cogs_per_unit,
        currency_code: c.currency_code,
      });
    } else {
      byKey.set(key, {
        key,
        date: c.date,
        kitchen_name: c.kitchen_name,
        product_name: c.product_name,
        planned_qty: "0",
        actual_qty: "0",
        yield_pct: null,
        batch_count: c.batch_count,
        total_cogs: c.total_cogs,
        cogs_per_unit: c.cogs_per_unit,
        currency_code: c.currency_code,
      });
    }
  }
  return [...byKey.values()].sort((a, b) => (a.date < b.date ? -1 : 1));
}

export default function YieldTrendsPage() {
  const [from, setFrom] = useState<string>(() => isoDaysAgo(30));
  const [to, setTo] = useState<string>(() => todayIso());
  const [kitchenId, setKitchenId] = useState("");
  const [productId, setProductId] = useState("");
  const [bucket, setBucket] = useState<ReportBucket>("daily");
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [y, c] = await Promise.all([
        listYieldTrends({
          from,
          to,
          kitchen_id: kitchenId || undefined,
          product_id: productId || undefined,
          bucket,
        }),
        listCogsTrends({
          from,
          to,
          kitchen_id: kitchenId || undefined,
          product_id: productId || undefined,
          bucket,
        }),
      ]);
      setRows(merge(y, c));
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

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <h1 className="mt-2 text-3xl font-bold tracking-tight">
          Yield &amp; COGS Trends
        </h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          Completed-batch yield % and COGS per unit over time.
        </p>
      </div>

      <form
        className="mb-6 grid grid-cols-1 gap-3 rounded-lg border border-slate-200 bg-white p-4 sm:grid-cols-6"
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
            placeholder="optional"
            className="w-full rounded border border-slate-300 px-2 py-1 text-sm"
            value={kitchenId}
            onChange={(e) => setKitchenId(e.target.value)}
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
        <label className="text-xs">
          <div className="mb-1 font-medium ">Bucket</div>
          <select
            className="w-full rounded border border-slate-300 px-2 py-1 text-sm"
            value={bucket}
            onChange={(e) => setBucket(e.target.value as ReportBucket)}
          >
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
          </select>
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
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Date</th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Kitchen</th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Product</th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Planned</th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Actual</th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Yield %</th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Batches</th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Total COGS</th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>COGS/unit</th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Yield bar</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && !loading && (
              <tr>
                <td
                  colSpan={10}
                  className="px-3 py-6 text-center text-sm" style={{ color: "var(--text-muted)" }}
                >
                  No completed batches in the selected window.
                </td>
              </tr>
            )}
            {rows.map((r) => {
              const pct = r.yield_pct ? Math.max(0, Math.min(100, Number(r.yield_pct))) : 0;
              return (
                <tr
                  key={r.key}
                  className="border-t border-slate-100 hover:bg-slate-50"
                >
                  <td className="px-3 py-2 font-mono">{r.date}</td>
                  <td className="px-3 py-2">{r.kitchen_name ?? "—"}</td>
                  <td className="px-3 py-2">{r.product_name ?? "—"}</td>
                  <td className="px-3 py-2 text-right tabular-nums">
                    {r.planned_qty}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums">
                    {r.actual_qty}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums">
                    {r.yield_pct ? `${Number(r.yield_pct).toFixed(1)}%` : "—"}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums">
                    {r.batch_count}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums">
                    {r.total_cogs
                      ? `${r.currency_code ?? ""} ${Number(r.total_cogs).toFixed(2)}`
                      : "—"}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums">
                    {r.cogs_per_unit
                      ? Number(r.cogs_per_unit).toFixed(2)
                      : "—"}
                  </td>
                  <td className="px-3 py-2">
                    <div className="h-2 w-24 overflow-hidden rounded bg-slate-200">
                      <div
                        className="h-full bg-emerald-500"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
