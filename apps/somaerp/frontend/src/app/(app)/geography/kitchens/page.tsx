"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listKitchens, listLocations } from "@/lib/api";
import type { Kitchen, KitchenStatus, Location } from "@/types/api";

type LocationsState =
  | { status: "loading" }
  | { status: "ok"; items: Location[] }
  | { status: "error"; message: string };

type KitchensState =
  | { status: "loading" }
  | { status: "ok"; items: Kitchen[] }
  | { status: "error"; message: string };

type StatusFilter = KitchenStatus | "all";

export default function KitchensListPage() {
  const [locations, setLocations] = useState<LocationsState>({ status: "loading" });
  const [kitchens, setKitchens] = useState<KitchensState>({ status: "loading" });
  const [locationId, setLocationId] = useState<string>("");
  const [status, setStatus] = useState<StatusFilter>("all");

  useEffect(() => {
    let cancelled = false;
    listLocations()
      .then((items) => { if (!cancelled) setLocations({ status: "ok", items }); })
      .catch((err: unknown) => {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : "Unknown error";
        setLocations({ status: "error", message });
      });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    let cancelled = false;
    setKitchens({ status: "loading" });
    listKitchens({
      location_id: locationId === "" ? undefined : locationId,
      status: status === "all" ? undefined : status,
    })
      .then((items) => { if (!cancelled) setKitchens({ status: "ok", items }); })
      .catch((err: unknown) => {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : "Unknown error";
        setKitchens({ status: "error", message });
      });
    return () => { cancelled = true; };
  }, [locationId, status]);

  return (
    <div className="max-w-5xl">
      <div className="mb-5 flex items-center justify-between">
        <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>Kitchens</h1>
        <Link
          href="/geography/kitchens/new"
          className="inline-flex items-center justify-center rounded px-3 py-1.5 text-sm font-medium"
          style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
        >
          + New Kitchen
        </Link>
      </div>

      {/* Filters */}
      <div
        className="mb-4 grid grid-cols-1 gap-3 rounded border p-4 sm:grid-cols-2"
        style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
      >
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Location</label>
          <select
            value={locationId}
            onChange={(e) => setLocationId(e.target.value)}
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none"
            style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          >
            <option value="">All locations</option>
            {locations.status === "ok" && locations.items.map((l) => (
              <option key={l.id} value={l.id}>{l.name} ({l.region_code})</option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Status</label>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as StatusFilter)}
            className="w-full rounded border px-3 py-2 text-sm focus:outline-none"
            style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          >
            <option value="all">All</option>
            <option value="active">Active</option>
            <option value="paused">Paused</option>
            <option value="decommissioned">Decommissioned</option>
          </select>
        </div>
      </div>

      <div className="rounded border overflow-hidden" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        {kitchens.status === "loading" && (
          <p className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>Loading kitchens…</p>
        )}
        {kitchens.status === "error" && (
          <div className="m-4 rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            <span className="font-semibold">Failed to load kitchens</span>
            <span className="ml-2 opacity-80">{kitchens.message}</span>
          </div>
        )}
        {kitchens.status === "ok" && kitchens.items.length === 0 && (
          <div className="p-8 text-center text-sm" style={{ color: "var(--text-muted)" }}>No kitchens match the current filters.</div>
        )}
        {kitchens.status === "ok" && kitchens.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead style={{ backgroundColor: "var(--bg-table-header)", borderBottom: "1px solid var(--border)" }}>
                <tr>
                  {["Name", "Type", "Status", "Location", "Created"].map((h) => (
                    <th key={h} className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {kitchens.items.map((k, idx) => (
                  <tr
                    key={k.id}
                    style={{ borderTop: idx > 0 ? "1px solid var(--border)" : undefined }}
                    onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-table-hover)"; }}
                    onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "transparent"; }}
                  >
                    <td className="px-4 py-2.5 font-medium" style={{ color: "var(--text-primary)" }}>
                      <Link href={`/geography/kitchens/${k.id}`} className="hover:underline" style={{ color: "var(--text-accent)" }}>{k.name}</Link>
                    </td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)" }}>{k.kitchen_type}</td>
                    <td className="px-4 py-2.5"><KitchenStatusBadge status={k.status} /></td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)" }}>{k.location_name}</td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-muted)" }}>{formatDate(k.created_at)}</td>
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

function KitchenStatusBadge({ status }: { status: KitchenStatus }) {
  const style =
    status === "active"
      ? { backgroundColor: "var(--status-active-bg)", color: "var(--status-active)" }
      : status === "paused"
      ? { backgroundColor: "var(--status-paused-bg)", color: "var(--status-paused)" }
      : { backgroundColor: "var(--status-draft-bg)", color: "var(--status-draft)" };
  return (
    <span className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium" style={style}>
      {status}
    </span>
  );
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toISOString().slice(0, 10);
}
