"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listKitchens, listServiceZones } from "@/lib/api";
import type { Kitchen, ServiceZone, ZoneStatus } from "@/types/api";

type KitchensState = { status: "loading" } | { status: "ok"; items: Kitchen[] } | { status: "error"; message: string };
type ZonesState = { status: "loading" } | { status: "ok"; items: ServiceZone[] } | { status: "error"; message: string };

export default function ServiceZonesListPage() {
  const [kitchens, setKitchens] = useState<KitchensState>({ status: "loading" });
  const [zones, setZones] = useState<ZonesState>({ status: "loading" });
  const [kitchenId, setKitchenId] = useState<string>("");

  useEffect(() => {
    let cancelled = false;
    listKitchens()
      .then((items) => { if (!cancelled) setKitchens({ status: "ok", items }); })
      .catch((err: unknown) => { if (!cancelled) setKitchens({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }); });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    let cancelled = false;
    setZones({ status: "loading" });
    listServiceZones({ kitchen_id: kitchenId === "" ? undefined : kitchenId })
      .then((items) => { if (!cancelled) setZones({ status: "ok", items }); })
      .catch((err: unknown) => { if (!cancelled) setZones({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }); });
    return () => { cancelled = true; };
  }, [kitchenId]);

  return (
    <div className="max-w-5xl">
      <div className="mb-5 flex items-center justify-between">
        <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>Service Zones</h1>
        <Link href="/geography/service-zones/new" className="inline-flex items-center rounded px-3 py-1.5 text-sm font-medium" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}>
          + New Service Zone
        </Link>
      </div>

      <div className="mb-4 rounded border p-4" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Kitchen</label>
        <select value={kitchenId} onChange={(e) => setKitchenId(e.target.value)} className="w-full rounded border px-3 py-2 text-sm focus:outline-none sm:max-w-xs" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}>
          <option value="">All kitchens</option>
          {kitchens.status === "ok" && kitchens.items.map((k) => <option key={k.id} value={k.id}>{k.name} ({k.location_name})</option>)}
        </select>
      </div>

      <div className="rounded border overflow-hidden" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        {zones.status === "loading" && <p className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>Loading service zones…</p>}
        {zones.status === "error" && (
          <div className="m-4 rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            <span className="font-semibold">Failed to load service zones</span>
            <span className="ml-2 opacity-80">{zones.message}</span>
          </div>
        )}
        {zones.status === "ok" && zones.items.length === 0 && (
          <div className="p-8 text-center text-sm" style={{ color: "var(--text-muted)" }}>No service zones yet.</div>
        )}
        {zones.status === "ok" && zones.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead style={{ backgroundColor: "var(--bg-table-header)", borderBottom: "1px solid var(--border)" }}>
                <tr>
                  {["Name", "Kitchen", "Status"].map((h) => (
                    <th key={h} className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {zones.items.map((z, idx) => (
                  <tr key={z.id} style={{ borderTop: idx > 0 ? "1px solid var(--border)" : undefined }}
                    onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-table-hover)"; }}
                    onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "transparent"; }}>
                    <td className="px-4 py-2.5 font-medium" style={{ color: "var(--text-primary)" }}>{z.name}</td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)" }}>{z.kitchen_name}</td>
                    <td className="px-4 py-2.5"><ZoneBadge status={z.status} /></td>
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

function ZoneBadge({ status }: { status: ZoneStatus }) {
  const style = status === "active"
    ? { backgroundColor: "var(--status-active-bg)", color: "var(--status-active)" }
    : { backgroundColor: "var(--status-paused-bg)", color: "var(--status-paused)" };
  return <span className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium" style={style}>{status}</span>;
}
