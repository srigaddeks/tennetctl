"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  listInventoryCurrent,
  listKitchens,
  listRawMaterialCategories,
} from "@/lib/api";
import type {
  InventoryCurrent,
  Kitchen,
  RawMaterialCategory,
} from "@/types/api";

type StockState =
  | { status: "loading" }
  | { status: "ok"; items: InventoryCurrent[] }
  | { status: "error"; message: string };

export default function InventoryCurrentPage() {
  const [stock, setStock] = useState<StockState>({ status: "loading" });
  const [kitchens, setKitchens] = useState<Kitchen[]>([]);
  const [categories, setCategories] = useState<RawMaterialCategory[]>([]);
  const [kitchenId, setKitchenId] = useState<string>("");
  const [categoryId, setCategoryId] = useState<string>("");

  useEffect(() => {
    let cancelled = false;
    listKitchens()
      .then((items) => {
        if (!cancelled) setKitchens(items);
      })
      .catch(() => undefined);
    listRawMaterialCategories()
      .then((items) => {
        if (!cancelled) setCategories(items);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    setStock({ status: "loading" });
    listInventoryCurrent({
      kitchen_id: kitchenId || undefined,
      category_id:
        categoryId === "" ? undefined : Number.parseInt(categoryId, 10),
    })
      .then((items) => {
        if (!cancelled) setStock({ status: "ok", items });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : "Unknown error";
        setStock({ status: "error", message });
      });
    return () => {
      cancelled = true;
    };
  }, [kitchenId, categoryId]);

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <h1 className="mt-2 text-3xl font-bold tracking-tight">
          Current Stock
        </h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          Reads from v_inventory_current. Quantities converted to each
          material&apos;s default unit.
        </p>
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
          Category
          <select
            value={categoryId}
            onChange={(e) => setCategoryId(e.target.value)}
            className="mt-1 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm "
          >
            <option value="">All categories</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="rounded border overflow-hidden" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        {stock.status === "loading" && (
          <p className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>Loading stock…</p>
        )}
        {stock.status === "error" && (
          <div className="m-4 rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            <p className="font-semibold">Failed to load stock</p>
            <p className="mt-1 text-sm opacity-80">{stock.message}</p>
          </div>
        )}
        {stock.status === "ok" && stock.items.length === 0 && (
          <div className="p-8 text-center text-sm" style={{ color: "var(--text-muted)" }}>
            <p>No stock yet.</p>
            <p className="mt-1 text-sm">
              Record a procurement run to receive raw materials.
            </p>
          </div>
        )}
        {stock.status === "ok" && stock.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead style={{ backgroundColor: "var(--bg-table-header)", borderBottom: "1px solid var(--border)" }}>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Kitchen</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Raw Material</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Category</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Qty</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Unit</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Reorder</th>
                </tr>
              </thead>
              <tbody >
                {stock.items.map((s) => {
                  const qty = s.qty_in_default_unit
                    ? Number.parseFloat(s.qty_in_default_unit)
                    : 0;
                  const target = s.target_unit_cost
                    ? Number.parseFloat(s.target_unit_cost)
                    : null;
                  // Reorder alert: below 1 default unit (placeholder threshold).
                  const alert = qty < 1;
                  return (
                    <tr
                      key={`${s.kitchen_id}-${s.raw_material_id}`}
                      onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-table-hover)"; }} onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "transparent"; }}
                    >
                      <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)" }}>
                        {s.kitchen_name ?? s.kitchen_id}
                      </td>
                      <td className="px-4 py-2.5 font-medium" style={{ color: "var(--text-primary)" }}>
                        {s.raw_material_name ?? s.raw_material_id}
                      </td>
                      <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)" }}>
                        {s.category_name ?? "—"}
                      </td>
                      <td className="px-4 py-3 font-mono ">
                        {qty.toFixed(3)}
                      </td>
                      <td className="px-4 py-2.5 font-mono" style={{ color: "var(--text-secondary)" }}>
                        {s.default_unit_code ?? s.default_unit_id}
                      </td>
                      <td className="px-4 py-3">
                        {alert ? (
                          <span className="inline-flex items-center rounded-full border border-yellow-300 bg-yellow-100 px-2 py-0.5 text-xs font-medium text-yellow-800">
                            low stock
                          </span>
                        ) : (
                          <span className="text-xs text-slate-400">
                            {target !== null ? `target ${target.toFixed(2)}` : "—"}
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
