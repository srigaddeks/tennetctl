"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listLocations } from "@/lib/api";
import type { Location } from "@/types/api";

type LoadState =
  | { status: "loading" }
  | { status: "ok"; items: Location[] }
  | { status: "error"; message: string };

export default function LocationsListPage() {
  const [state, setState] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;
    listLocations()
      .then((items) => {
        if (!cancelled) setState({ status: "ok", items });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : "Unknown error";
        setState({ status: "error", message });
      });
    return () => { cancelled = true; };
  }, []);

  return (
    <div className="max-w-5xl">
      <div className="page-header">
        <div>
          <h1 className="page-title">Locations</h1>
        </div>
        <Link href="/geography/locations/new" className="btn-primary">
          + New Location
        </Link>
      </div>

      <div className="rounded overflow-hidden" style={{ border: "1px solid var(--border)", backgroundColor: "var(--bg-card)" }}>
        {state.status === "loading" && (
          <p className="p-6" style={{ fontSize: 13, color: "var(--text-muted)" }}>Loading locations…</p>
        )}

        {state.status === "error" && (
          <div className="m-4 rounded p-4" style={{ border: "1px solid var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error-text)", fontSize: 13 }}>
            <span style={{ fontWeight: 600 }}>Failed to load locations</span>
            <span style={{ marginLeft: 8, opacity: 0.8 }}>{state.message}</span>
          </div>
        )}

        {state.status === "ok" && state.items.length === 0 && (
          <div className="p-8 text-center" style={{ color: "var(--text-muted)" }}>
            <p style={{ fontSize: 13 }}>No locations yet.</p>
            <p style={{ marginTop: 6, fontSize: 12 }}>Create your first location to start adding kitchens.</p>
          </div>
        )}

        {state.status === "ok" && state.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="erp-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Slug</th>
                  <th>Region</th>
                  <th>Timezone</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {state.items.map((loc) => (
                  <tr key={loc.id}>
                    <td style={{ fontWeight: 500 }}>{loc.name}</td>
                    <td className="td-mono">{loc.slug}</td>
                    <td className="td-mono">{loc.region_code}</td>
                    <td className="td-muted">{loc.timezone}</td>
                    <td className="td-mono td-muted">{formatDate(loc.created_at)}</td>
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

function formatDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toISOString().slice(0, 10);
}
