"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listRawMaterialCategories, listRawMaterials, listUnitsOfMeasure } from "@/lib/api";
import type { RawMaterial, RawMaterialCategory, RawMaterialStatus, UnitOfMeasure } from "@/types/api";

type CategoriesState = { status: "loading" } | { status: "ok"; items: RawMaterialCategory[] } | { status: "error"; message: string };
type UnitsState = { status: "loading" } | { status: "ok"; items: UnitOfMeasure[] } | { status: "error"; message: string };
type MaterialsState = { status: "loading" } | { status: "ok"; items: RawMaterial[] } | { status: "error"; message: string };
type StatusFilter = RawMaterialStatus | "all";

const inputStyle = { borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" };

export default function RawMaterialsListPage() {
  const [categories, setCategories] = useState<CategoriesState>({ status: "loading" });
  const [, setUnits] = useState<UnitsState>({ status: "loading" });
  const [materials, setMaterials] = useState<MaterialsState>({ status: "loading" });
  const [categoryId, setCategoryId] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");

  useEffect(() => {
    let cancelled = false;
    listRawMaterialCategories()
      .then((items) => { if (!cancelled) setCategories({ status: "ok", items }); })
      .catch((err: unknown) => { if (!cancelled) setCategories({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }); });
    listUnitsOfMeasure()
      .then((items) => { if (!cancelled) setUnits({ status: "ok", items }); })
      .catch((err: unknown) => { if (!cancelled) setUnits({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }); });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    let cancelled = false;
    setMaterials({ status: "loading" });
    const catNum = categoryId === "" ? undefined : Number.parseInt(categoryId, 10);
    listRawMaterials({ category_id: catNum !== undefined && Number.isFinite(catNum) ? catNum : undefined, status: statusFilter === "all" ? undefined : statusFilter })
      .then((items) => { if (!cancelled) setMaterials({ status: "ok", items }); })
      .catch((err: unknown) => { if (!cancelled) setMaterials({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }); });
    return () => { cancelled = true; };
  }, [categoryId, statusFilter]);

  return (
    <div className="max-w-5xl">
      <div className="mb-5 flex items-center justify-between">
        <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>Raw Materials</h1>
        <Link href="/supply/raw-materials/new" className="inline-flex items-center rounded px-3 py-1.5 text-sm font-medium" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}>+ New Raw Material</Link>
      </div>

      <div className="mb-4 grid grid-cols-2 gap-3 rounded border p-4" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Category</label>
          <select value={categoryId} onChange={(e) => setCategoryId(e.target.value)} className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={inputStyle}>
            <option value="">All categories</option>
            {categories.status === "ok" && categories.items.map((c) => <option key={c.id} value={String(c.id)}>{c.name} ({c.code})</option>)}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Status</label>
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value as StatusFilter)} className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={inputStyle}>
            <option value="all">All</option>
            <option value="active">Active</option>
            <option value="paused">Paused</option>
            <option value="discontinued">Discontinued</option>
          </select>
        </div>
      </div>

      <div className="rounded border overflow-hidden" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        {materials.status === "loading" && <p className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>Loading raw materials…</p>}
        {materials.status === "error" && (
          <div className="m-4 rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            <span className="font-semibold">Failed to load raw materials</span> <span className="opacity-80">{materials.message}</span>
          </div>
        )}
        {materials.status === "ok" && materials.items.length === 0 && <div className="p-8 text-center text-sm" style={{ color: "var(--text-muted)" }}>No raw materials match the current filters.</div>}
        {materials.status === "ok" && materials.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead style={{ backgroundColor: "var(--bg-table-header)", borderBottom: "1px solid var(--border)" }}>
                <tr>
                  {["Name", "Slug", "Category", "Unit", "Lot-Tracked", "Target Cost", "Status"].map((h) => (
                    <th key={h} className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {materials.items.map((m, idx) => (
                  <tr key={m.id} style={{ borderTop: idx > 0 ? "1px solid var(--border)" : undefined }}
                    onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-table-hover)"; }}
                    onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "transparent"; }}>
                    <td className="px-4 py-2.5 font-medium" style={{ color: "var(--text-primary)" }}>{m.name}</td>
                    <td className="px-4 py-2.5 font-mono text-xs" style={{ color: "var(--text-secondary)" }}>{m.slug}</td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)" }}>{m.category_name}</td>
                    <td className="px-4 py-2.5 font-mono text-xs" style={{ color: "var(--text-secondary)" }}>{m.default_unit_code}</td>
                    <td className="px-4 py-2.5">
                      <span className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
                        style={m.requires_lot_tracking ? { backgroundColor: "var(--status-active-bg)", color: "var(--status-active)" } : { backgroundColor: "var(--status-draft-bg)", color: "var(--status-draft)" }}>
                        {m.requires_lot_tracking ? "YES" : "NO"}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 font-mono text-xs" style={{ color: "var(--text-secondary)" }}>{m.target_unit_cost !== null ? `${m.target_unit_cost} ${m.currency_code}` : "—"}</td>
                    <td className="px-4 py-2.5"><MatStatusPill status={m.status} /></td>
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

function MatStatusPill({ status }: { status: RawMaterialStatus }) {
  const style = status === "active"
    ? { backgroundColor: "var(--status-active-bg)", color: "var(--status-active)" }
    : status === "paused"
    ? { backgroundColor: "var(--status-paused-bg)", color: "var(--status-paused)" }
    : { backgroundColor: "var(--status-draft-bg)", color: "var(--status-draft)" };
  return <span className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium" style={style}>{status}</span>;
}
