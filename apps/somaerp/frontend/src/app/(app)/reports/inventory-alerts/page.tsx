"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listInventoryAlerts } from "@/lib/api";
import type {
  InventoryAlert,
  InventoryAlertLevel,
  InventoryAlertSeverity,
} from "@/types/api";

const BADGE: Record<InventoryAlertLevel, string> = {
  critical: "bg-red-100 text-red-800 border-red-300",
  low: "bg-amber-100 text-amber-800 border-amber-300",
  ok: "bg-emerald-100 text-emerald-800 border-emerald-300",
};

export default function InventoryAlertsPage() {
  const [kitchenId, setKitchenId] = useState("");
  const [severity, setSeverity] = useState<InventoryAlertSeverity>("all");
  const [rows, setRows] = useState<InventoryAlert[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listInventoryAlerts({
        kitchen_id: kitchenId || undefined,
        severity,
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

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <h1 className="mt-2 text-3xl font-bold tracking-tight">
          Inventory Reorder Alerts
        </h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          Critical = out of stock. Low = below reorder point (from raw material
          properties).
        </p>
      </div>

      <form
        className="mb-6 grid grid-cols-1 gap-3 rounded-lg border border-slate-200 bg-white p-4 sm:grid-cols-4"
        onSubmit={(e) => {
          e.preventDefault();
          load();
        }}
      >
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
          <div className="mb-1 font-medium ">Severity</div>
          <select
            className="w-full rounded border border-slate-300 px-2 py-1 text-sm"
            value={severity}
            onChange={(e) =>
              setSeverity(e.target.value as InventoryAlertSeverity)
            }
          >
            <option value="all">All</option>
            <option value="critical">Critical only</option>
            <option value="low">Low + Critical</option>
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
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Severity</th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Kitchen</th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Raw Material</th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Category</th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Current</th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Unit</th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Reorder Point</th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Primary Supplier</th>
              <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && !loading && (
              <tr>
                <td
                  colSpan={9}
                  className="px-3 py-6 text-center text-sm" style={{ color: "var(--text-muted)" }}
                >
                  No alerts for the selected filters.
                </td>
              </tr>
            )}
            {rows.map((r) => {
              const startUrl = r.primary_supplier_id
                ? `/procurement/runs/new?supplier_id=${encodeURIComponent(
                    r.primary_supplier_id,
                  )}&kitchen_id=${encodeURIComponent(r.kitchen_id)}`
                : null;
              return (
                <tr
                  key={`${r.kitchen_id}-${r.raw_material_id}`}
                  className="border-t border-slate-100"
                >
                  <td className="px-3 py-2">
                    <span
                      className={`inline-flex items-center rounded border px-2 py-0.5 text-xs font-medium ${
                        BADGE[r.alert_level]
                      }`}
                    >
                      {r.alert_level}
                    </span>
                  </td>
                  <td className="px-3 py-2">{r.kitchen_name ?? "—"}</td>
                  <td className="px-3 py-2">{r.raw_material_name ?? "—"}</td>
                  <td className="px-3 py-2 ">
                    {r.category_name ?? "—"}
                  </td>
                  <td className="px-3 py-2 text-right font-mono tabular-nums">
                    {r.current_qty}
                  </td>
                  <td className="px-3 py-2">{r.unit_code ?? "—"}</td>
                  <td className="px-3 py-2 text-right font-mono tabular-nums ">
                    {r.reorder_point_qty ?? "—"}
                  </td>
                  <td className="px-3 py-2 ">
                    {r.primary_supplier_name ?? "—"}
                  </td>
                  <td className="px-3 py-2">
                    {startUrl ? (
                      <Link
                        href={startUrl}
                        className="rounded border border-slate-900 px-2 py-1 text-xs font-medium  hover:bg-slate-900 hover:text-white"
                      >
                        Start Procurement Run
                      </Link>
                    ) : (
                      <span className="text-xs text-slate-400">
                        no primary supplier
                      </span>
                    )}
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
