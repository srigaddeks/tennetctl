"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listEquipment } from "@/lib/api";
import type { Equipment, EquipmentStatus } from "@/types/api";

type EquipmentState =
  | { status: "loading" }
  | { status: "ok"; items: Equipment[] }
  | { status: "error"; message: string };

export default function EquipmentListPage() {
  const [equipment, setEquipment] = useState<EquipmentState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;
    listEquipment()
      .then((items) => {
        if (!cancelled) setEquipment({ status: "ok", items });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : "Unknown error";
        setEquipment({ status: "error", message });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="max-w-5xl">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>Equipment</h1>
        </div>
        <Link
          href="/equipment/new"
          className="inline-flex items-center justify-center rounded px-3 py-1.5 text-sm font-medium" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
        >
          + New Equipment
        </Link>
      </div>

      <div className="rounded border overflow-hidden" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        {equipment.status === "loading" && (
          <p className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>Loading equipment…</p>
        )}
        {equipment.status === "error" && (
          <div className="m-4 rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            <p className="font-semibold">Failed to load equipment</p>
            <p className="mt-1 text-sm opacity-80">{equipment.message}</p>
          </div>
        )}
        {equipment.status === "ok" && equipment.items.length === 0 && (
          <div className="p-8 text-center text-sm" style={{ color: "var(--text-muted)" }}>
            <p>No equipment yet.</p>
            <Link
              href="/equipment/new"
              className="mt-2 inline-block text-sm  underline hover:no-underline"
            >
              Add the first equipment
            </Link>
          </div>
        )}
        {equipment.status === "ok" && equipment.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead style={{ backgroundColor: "var(--bg-table-header)", borderBottom: "1px solid var(--border)" }}>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Name</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Category</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Status</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Purchase Cost</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Purchase Date</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Age</th>
                </tr>
              </thead>
              <tbody >
                {equipment.items.map((e) => (
                  <tr key={e.id} onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-table-hover)"; }} onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "transparent"; }}>
                    <td className="px-4 py-2.5 font-medium" style={{ color: "var(--text-primary)" }}>
                      <Link href={`/equipment/${e.id}`} className="hover:underline">{e.name}</Link>
                    </td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)" }}>{e.category_name ?? e.category_code}</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={e.status} />
                    </td>
                    <td className="px-4 py-2.5 font-mono" style={{ color: "var(--text-secondary)" }}>
                      {e.purchase_cost
                        ? `${e.currency_code ?? ""} ${Number.parseFloat(e.purchase_cost).toFixed(2)}`
                        : "—"}
                    </td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)" }}>{e.purchase_date ?? "—"}</td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)" }}>
                      {ageLabel(e.purchase_date, e.expected_lifespan_months)}
                    </td>
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

function StatusBadge({ status }: { status: EquipmentStatus }) {
  const styles: Record<EquipmentStatus, string> = {
    active: "bg-green-100 text-green-800 border-green-200",
    maintenance: "bg-yellow-100 text-yellow-800 border-yellow-200",
    retired: "bg-slate-100  border-slate-200",
  };
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${styles[status]}`}
    >
      {status}
    </span>
  );
}

function ageLabel(purchaseDate: string | null, lifespan: number | null): string {
  if (!purchaseDate) return "—";
  const d = new Date(purchaseDate);
  if (Number.isNaN(d.getTime())) return "—";
  const now = new Date();
  const months =
    (now.getFullYear() - d.getFullYear()) * 12 + (now.getMonth() - d.getMonth());
  if (lifespan && lifespan > 0) {
    return `${months} / ${lifespan} mo`;
  }
  return `${months} mo`;
}
