"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listLocations, listSuppliers, listSupplierSourceTypes } from "@/lib/api";
import type { Location, Supplier, SupplierSourceType, SupplierStatus } from "@/types/api";

type SourceTypesState = { status: "loading" } | { status: "ok"; items: SupplierSourceType[] } | { status: "error"; message: string };
type LocationsState = { status: "loading" } | { status: "ok"; items: Location[] } | { status: "error"; message: string };
type SuppliersState = { status: "loading" } | { status: "ok"; items: Supplier[] } | { status: "error"; message: string };
type StatusFilter = SupplierStatus | "all";

const inputStyle = { borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" };

export default function SuppliersListPage() {
  const [sourceTypes, setSourceTypes] = useState<SourceTypesState>({ status: "loading" });
  const [locations, setLocations] = useState<LocationsState>({ status: "loading" });
  const [suppliers, setSuppliers] = useState<SuppliersState>({ status: "loading" });
  const [sourceTypeId, setSourceTypeId] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [locationId, setLocationId] = useState<string>("");

  useEffect(() => {
    let cancelled = false;
    listSupplierSourceTypes().then((items) => { if (!cancelled) setSourceTypes({ status: "ok", items }); }).catch((err: unknown) => { if (!cancelled) setSourceTypes({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }); });
    listLocations().then((items) => { if (!cancelled) setLocations({ status: "ok", items }); }).catch((err: unknown) => { if (!cancelled) setLocations({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }); });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    let cancelled = false;
    setSuppliers({ status: "loading" });
    const stNum = sourceTypeId === "" ? undefined : Number.parseInt(sourceTypeId, 10);
    listSuppliers({ source_type_id: stNum !== undefined && Number.isFinite(stNum) ? stNum : undefined, status: statusFilter === "all" ? undefined : statusFilter, location_id: locationId || undefined })
      .then((items) => { if (!cancelled) setSuppliers({ status: "ok", items }); })
      .catch((err: unknown) => { if (!cancelled) setSuppliers({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }); });
    return () => { cancelled = true; };
  }, [sourceTypeId, statusFilter, locationId]);

  return (
    <div className="max-w-5xl">
      <div className="mb-5 flex items-center justify-between">
        <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>Suppliers</h1>
        <Link href="/supply/suppliers/new" className="inline-flex items-center rounded px-3 py-1.5 text-sm font-medium" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}>+ New Supplier</Link>
      </div>

      <div className="mb-4 grid grid-cols-3 gap-3 rounded border p-4" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Source Type</label>
          <select value={sourceTypeId} onChange={(e) => setSourceTypeId(e.target.value)} className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={inputStyle}>
            <option value="">All source types</option>
            {sourceTypes.status === "ok" && sourceTypes.items.map((s) => <option key={s.id} value={String(s.id)}>{s.name} ({s.code})</option>)}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Status</label>
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value as StatusFilter)} className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={inputStyle}>
            <option value="all">All</option>
            <option value="active">Active</option>
            <option value="paused">Paused</option>
            <option value="blacklisted">Blacklisted</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Location</label>
          <select value={locationId} onChange={(e) => setLocationId(e.target.value)} className="w-full rounded border px-3 py-2 text-sm focus:outline-none" style={inputStyle}>
            <option value="">All locations</option>
            {locations.status === "ok" && locations.items.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
          </select>
        </div>
      </div>

      <div className="rounded border overflow-hidden" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        {suppliers.status === "loading" && <p className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>Loading suppliers…</p>}
        {suppliers.status === "error" && (
          <div className="m-4 rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            <span className="font-semibold">Failed to load suppliers</span> <span className="opacity-80">{suppliers.message}</span>
          </div>
        )}
        {suppliers.status === "ok" && suppliers.items.length === 0 && <div className="p-8 text-center text-sm" style={{ color: "var(--text-muted)" }}>No suppliers match the current filters.</div>}
        {suppliers.status === "ok" && suppliers.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead style={{ backgroundColor: "var(--bg-table-header)", borderBottom: "1px solid var(--border)" }}>
                <tr>
                  {["Name", "Source Type", "Location", "Payment Terms", "Quality", "Status"].map((h) => (
                    <th key={h} className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {suppliers.items.map((s, idx) => (
                  <tr key={s.id} style={{ borderTop: idx > 0 ? "1px solid var(--border)" : undefined }}
                    onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-table-hover)"; }}
                    onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "transparent"; }}>
                    <td className="px-4 py-2.5 font-medium" style={{ color: "var(--text-primary)" }}>{s.name}</td>
                    <td className="px-4 py-2.5">
                      <span className="inline-flex items-center rounded-full px-2 py-0.5 text-xs" style={{ backgroundColor: "var(--status-draft-bg)", color: "var(--status-draft)" }}>{s.source_type_name}</span>
                    </td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)" }}>{s.location_name ?? "—"}</td>
                    <td className="px-4 py-2.5 font-mono text-xs" style={{ color: "var(--text-secondary)" }}>{s.payment_terms ?? "—"}</td>
                    <td className="px-4 py-2.5"><Stars rating={s.quality_rating} /></td>
                    <td className="px-4 py-2.5"><SupplierStatusPill status={s.status} /></td>
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

function Stars({ rating }: { rating: number | null }) {
  if (rating === null) return <span className="text-xs" style={{ color: "var(--text-muted)" }}>—</span>;
  const clamped = Math.max(1, Math.min(5, rating));
  return <span className="font-mono text-sm" style={{ color: "var(--status-paused)" }} title={`${clamped}/5`}>{"★".repeat(clamped)}<span style={{ color: "var(--border)" }}>{"☆".repeat(5 - clamped)}</span></span>;
}

function SupplierStatusPill({ status }: { status: SupplierStatus }) {
  const style = status === "active"
    ? { backgroundColor: "var(--status-active-bg)", color: "var(--status-active)" }
    : status === "paused"
    ? { backgroundColor: "var(--status-paused-bg)", color: "var(--status-paused)" }
    : { backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" };
  return <span className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium" style={style}>{status}</span>;
}
