"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { listRevenueProjection } from "@/lib/api";
import type { RevenueProjection } from "@/types/api";

export default function RevenueProjectionPage() {
  const [rows, setRows] = useState<RevenueProjection[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listRevenueProjection({ status: "active" });
      setRows(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const totals = useMemo(() => {
    let daily = 0;
    let weekly = 0;
    let monthly = 0;
    let currency: string | null = null;
    for (const r of rows) {
      daily += Number(r.daily_projected || 0);
      weekly += Number(r.weekly_projected || 0);
      monthly += Number(r.monthly_projected || 0);
      currency = currency ?? r.currency_code;
    }
    return { daily, weekly, monthly, currency };
  }, [rows]);

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <h1 className="mt-2 text-3xl font-bold tracking-tight">
          Revenue Projection
        </h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          Per active subscription: <span className="font-mono">
            price × deliveries_per_week × 4.333
          </span>{" "}
          per month.
        </p>
      </div>

      {error && (
        <div className="mb-4 rounded border border-red-300 bg-red-50 p-4 text-sm text-red-800">
          {error}
        </div>
      )}

      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-xs uppercase ">
            <tr>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Customer</th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Plan</th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Frequency</th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Price/Delivery</th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Deliveries/Week</th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Daily</th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Weekly</th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Monthly</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td
                  colSpan={8}
                  className="px-3 py-6 text-center text-sm" style={{ color: "var(--text-muted)" }}
                >
                  Loading…
                </td>
              </tr>
            )}
            {!loading && rows.length === 0 && (
              <tr>
                <td
                  colSpan={8}
                  className="px-3 py-6 text-center text-sm" style={{ color: "var(--text-muted)" }}
                >
                  No active subscriptions.
                </td>
              </tr>
            )}
            {rows.map((r) => (
              <tr
                key={r.subscription_id}
                className="border-t border-slate-100"
              >
                <td className="px-3 py-2">{r.customer_name ?? "—"}</td>
                <td className="px-3 py-2">{r.plan_name ?? "—"}</td>
                <td className="px-3 py-2 ">
                  {r.frequency_code ?? "—"}
                </td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {r.price_per_delivery ?? "—"}
                </td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {r.deliveries_per_week ?? "—"}
                </td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {r.daily_projected
                    ? Number(r.daily_projected).toFixed(2)
                    : "—"}
                </td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {r.weekly_projected
                    ? Number(r.weekly_projected).toFixed(2)
                    : "—"}
                </td>
                <td className="px-3 py-2 text-right font-semibold tabular-nums">
                  {r.monthly_projected
                    ? `${r.currency_code ?? ""} ${Number(r.monthly_projected).toFixed(2)}`
                    : "—"}
                </td>
              </tr>
            ))}
          </tbody>
          {rows.length > 0 && (
            <tfoot>
              <tr className="border-t-2 border-slate-300 bg-slate-50 font-semibold">
                <td colSpan={5} className="px-3 py-2 text-right">
                  Total
                </td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {totals.daily.toFixed(2)}
                </td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {totals.weekly.toFixed(2)}
                </td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {totals.currency ?? ""} {totals.monthly.toFixed(2)}
                </td>
              </tr>
            </tfoot>
          )}
        </table>
      </div>
    </div>
  );
}
