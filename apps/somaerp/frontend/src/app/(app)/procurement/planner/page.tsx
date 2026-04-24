"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  computeProcurementPlan,
  listKitchens,
  listProducts,
} from "@/lib/api";
import type {
  Kitchen,
  Product,
  ProcurementPlanResponse,
} from "@/types/api";

type DemandRow = {
  product_id: string;
  planned_qty: string;
  target_date: string;
};

type PlanState =
  | { status: "idle" }
  | { status: "computing" }
  | { status: "ok"; data: ProcurementPlanResponse }
  | { status: "error"; message: string };

export default function ProcurementPlannerPage() {
  const [kitchens, setKitchens] = useState<Kitchen[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [kitchenId, setKitchenId] = useState<string>("");
  const [rows, setRows] = useState<DemandRow[]>([
    { product_id: "", planned_qty: "", target_date: today() },
  ]);
  const [plan, setPlan] = useState<PlanState>({ status: "idle" });

  useEffect(() => {
    let cancelled = false;
    listKitchens()
      .then((items) => {
        if (cancelled) return;
        setKitchens(items);
        if (items.length > 0) setKitchenId(items[0].id);
      })
      .catch(() => undefined);
    listProducts()
      .then((items) => {
        if (!cancelled) setProducts(items);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  function updateRow(idx: number, patch: Partial<DemandRow>) {
    setRows((prev) =>
      prev.map((r, i) => (i === idx ? { ...r, ...patch } : r)),
    );
  }

  function addRow() {
    setRows((prev) => [
      ...prev,
      { product_id: "", planned_qty: "", target_date: today() },
    ]);
  }

  function removeRow(idx: number) {
    setRows((prev) => prev.filter((_, i) => i !== idx));
  }

  async function onCompute() {
    if (!kitchenId) {
      setPlan({ status: "error", message: "Pick a kitchen" });
      return;
    }
    const demand = rows
      .map((r) => {
        const qty = Number.parseFloat(r.planned_qty);
        if (!r.product_id || !Number.isFinite(qty) || qty <= 0 || !r.target_date) {
          return null;
        }
        return {
          product_id: r.product_id,
          planned_qty: qty,
          target_date: r.target_date,
        };
      })
      .filter((x): x is { product_id: string; planned_qty: number; target_date: string } =>
        x !== null,
      );
    if (demand.length === 0) {
      setPlan({
        status: "error",
        message: "Add at least one valid demand row",
      });
      return;
    }

    setPlan({ status: "computing" });
    try {
      const data = await computeProcurementPlan({
        kitchen_id: kitchenId,
        demand,
      });
      setPlan({ status: "ok", data });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setPlan({ status: "error", message });
    }
  }

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <h1 className="mt-2 text-3xl font-bold tracking-tight">
          MRP-lite Procurement Planner
        </h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          Enter planned production demand. The planner explodes each
          product&apos;s active recipe, subtracts current stock, and estimates
          cost from primary suppliers.
        </p>
      </div>

      {/* Demand form */}
      <div className="mb-6 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium" style={{ color: "var(--text-secondary)" }}>
              Kitchen
            </label>
            <select
              value={kitchenId}
              onChange={(e) => setKitchenId(e.target.value)}
              className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
            >
              {kitchens.length === 0 && (
                <option value="" disabled>
                  No kitchens
                </option>
              )}
              {kitchens.map((k) => (
                <option key={k.id} value={k.id}>
                  {k.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead style={{ backgroundColor: "var(--bg-table-header)", borderBottom: "1px solid var(--border)" }}>
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Product</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Planned Qty</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Target Date</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}></th>
              </tr>
            </thead>
            <tbody >
              {rows.map((r, idx) => (
                <tr key={idx}>
                  <td className="px-4 py-3">
                    <select
                      value={r.product_id}
                      onChange={(e) =>
                        updateRow(idx, { product_id: e.target.value })
                      }
                      className="w-full rounded border px-2 py-1 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
                    >
                      <option value="">Pick…</option>
                      {products.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="px-4 py-3">
                    <input
                      type="number"
                      step="0.01"
                      value={r.planned_qty}
                      onChange={(e) =>
                        updateRow(idx, { planned_qty: e.target.value })
                      }
                      placeholder="50"
                      className="w-28 rounded-md border border-slate-300 bg-white px-2 py-1 font-mono text-sm"
                    />
                  </td>
                  <td className="px-4 py-3">
                    <input
                      type="date"
                      value={r.target_date}
                      onChange={(e) =>
                        updateRow(idx, { target_date: e.target.value })
                      }
                      className="rounded-md border border-slate-300 bg-white px-2 py-1 font-mono text-sm"
                    />
                  </td>
                  <td className="px-4 py-3">
                    {rows.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeRow(idx)}
                        className="rounded border px-3 py-1 text-xs font-medium" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-secondary)" }}
                      >
                        Remove
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-4 flex gap-3">
          <button
            type="button"
            onClick={addRow}
            className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium  shadow-sm hover:bg-slate-50"
          >
            + Add Row
          </button>
          <button
            type="button"
            onClick={onCompute}
            disabled={plan.status === "computing"}
            className="rounded-md bg-slate-900 px-4 py-1.5 text-sm font-medium text-white shadow-sm hover:bg-slate-800 disabled:opacity-50"
          >
            {plan.status === "computing" ? "Computing…" : "Compute Plan"}
          </button>
        </div>

        {plan.status === "error" && (
          <div className="mt-4 rounded border border-red-300 bg-red-50 p-3 text-sm text-red-800">
            {plan.message}
          </div>
        )}
      </div>

      {/* Plan results */}
      {plan.status === "ok" && <PlanResults data={plan.data} />}
    </div>
  );
}

function PlanResults({ data }: { data: ProcurementPlanResponse }) {
  const totalCost = Number.parseFloat(data.total_estimated_cost || "0");
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded border p-5" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        <div className="flex items-baseline justify-between">
          <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Plan Results
          </h2>
        </div>
        <p className="mt-3 text-3xl font-bold ">
          {data.currency_code} {totalCost.toFixed(2)}
        </p>
      </div>

      {/* Requirements */}
      <div className="rounded border overflow-hidden" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        <div className="px-4 py-3" style={{ borderBottom: "1px solid var(--border)" }}>
          <h3 className="text-base font-semibold ">
            Raw Material Requirements
          </h3>
        </div>
        {data.requirements.length === 0 && (
          <p className="p-6 text-sm text-sm" style={{ color: "var(--text-muted)" }}>
            No requirements computed. Check the errors panel below.
          </p>
        )}
        {data.requirements.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead style={{ backgroundColor: "var(--bg-table-header)", borderBottom: "1px solid var(--border)" }}>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Raw Material</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Category</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Required</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>In Stock</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Gap</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Primary Supplier</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Est Cost</th>
                </tr>
              </thead>
              <tbody >
                {data.requirements.map((r) => (
                  <tr key={r.raw_material_id} onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-table-hover)"; }} onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "transparent"; }}>
                    <td className="px-4 py-3 ">
                      {r.raw_material_name ?? r.raw_material_id}
                    </td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)" }}>
                      {r.category_name ?? "—"}
                    </td>
                    <td className="px-4 py-2.5 font-mono" style={{ color: "var(--text-secondary)" }}>
                      {Number.parseFloat(r.required_qty).toFixed(3)}{" "}
                      {r.required_unit_code ?? ""}
                    </td>
                    <td className="px-4 py-2.5 font-mono" style={{ color: "var(--text-secondary)" }}>
                      {Number.parseFloat(r.in_stock_qty).toFixed(3)}
                    </td>
                    <td className="px-4 py-3 font-mono ">
                      {Number.parseFloat(r.gap_qty).toFixed(3)}
                    </td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)" }}>
                      {r.primary_supplier_name ?? (
                        <span className="text-yellow-700">not set</span>
                      )}
                    </td>
                    <td className="px-4 py-3 font-mono ">
                      {r.currency_code}{" "}
                      {Number.parseFloat(r.estimated_cost).toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot className="bg-slate-50 text-sm">
                <tr>
                  <td colSpan={6} className="px-4 py-3 text-right font-medium">
                    Total Estimated Cost
                  </td>
                  <td className="px-4 py-3 font-mono font-semibold">
                    {data.currency_code} {totalCost.toFixed(2)}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        )}
      </div>

      {/* Errors / unconvertible */}
      {(data.errors.length > 0 || data.unconvertible_units.length > 0) && (
        <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-6 shadow-sm">
          <h3 className="text-base font-semibold text-yellow-900">
            Planner Warnings
          </h3>
          {data.errors.length > 0 && (
            <div className="mt-3">
              <p className="text-sm font-semibold text-yellow-900">
                Errors ({data.errors.length})
              </p>
              <ul className="mt-1 space-y-1 text-sm text-yellow-800">
                {data.errors.map((e, idx) => (
                  <li key={idx}>
                    <code className="font-mono text-xs">{e.code}</code>{" "}
                    {e.product_id && (
                      <span className="text-xs text-yellow-700">
                        product={e.product_id}{" "}
                      </span>
                    )}
                    — {e.message}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {data.unconvertible_units.length > 0 && (
            <div className="mt-3">
              <p className="text-sm font-semibold text-yellow-900">
                Unconvertible units ({data.unconvertible_units.length})
              </p>
              <pre className="mt-1 overflow-x-auto rounded bg-white p-2 text-xs text-yellow-900">
                {JSON.stringify(data.unconvertible_units, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function today(): string {
  return new Date().toISOString().slice(0, 10);
}
