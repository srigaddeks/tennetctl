"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  listInventoryMovements,
  listKitchens,
  listRawMaterials,
} from "@/lib/api";
import type {
  InventoryMovement,
  InventoryMovementType,
  Kitchen,
  RawMaterial,
} from "@/types/api";

type FeedState =
  | { status: "loading" }
  | { status: "ok"; items: InventoryMovement[] }
  | { status: "error"; message: string };

const TYPES: ReadonlyArray<InventoryMovementType | ""> = [
  "received",
  "consumed",
  "wasted",
  "adjusted",
  "expired",
];

const TYPE_STYLES: Record<InventoryMovementType, string> = {
  received: "border-green-300 bg-green-50 text-green-900",
  consumed: "border-blue-300 bg-blue-50 text-blue-900",
  wasted: "border-red-300 bg-red-50 text-red-900",
  adjusted: "border-yellow-300 bg-yellow-50 text-yellow-900",
  expired: "border-slate-300 bg-slate-100",
};

export default function InventoryMovementsPage() {
  const [feed, setFeed] = useState<FeedState>({ status: "loading" });
  const [kitchens, setKitchens] = useState<Kitchen[]>([]);
  const [materials, setMaterials] = useState<RawMaterial[]>([]);

  const [kitchenId, setKitchenId] = useState<string>("");
  const [rawMaterialId, setRawMaterialId] = useState<string>("");
  const [movementType, setMovementType] = useState<InventoryMovementType | "">("");
  const [tsAfter, setTsAfter] = useState<string>("");
  const [tsBefore, setTsBefore] = useState<string>("");

  useEffect(() => {
    let cancelled = false;
    listKitchens()
      .then((items) => {
        if (!cancelled) setKitchens(items);
      })
      .catch(() => undefined);
    listRawMaterials()
      .then((items) => {
        if (!cancelled) setMaterials(items);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    setFeed({ status: "loading" });
    listInventoryMovements({
      kitchen_id: kitchenId || undefined,
      raw_material_id: rawMaterialId || undefined,
      movement_type: movementType || undefined,
      ts_after: tsAfter ? `${tsAfter}T00:00:00` : undefined,
      ts_before: tsBefore ? `${tsBefore}T23:59:59` : undefined,
    })
      .then((items) => {
        if (!cancelled) setFeed({ status: "ok", items });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : "Unknown error";
        setFeed({ status: "error", message });
      });
    return () => {
      cancelled = true;
    };
  }, [kitchenId, rawMaterialId, movementType, tsAfter, tsBefore]);

  return (
    <div className="max-w-5xl">
      <div className="mb-6">
        <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>
          Inventory Movements
        </h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          Append-only event log. Most recent first.
        </p>
      </div>

      <div className="mb-4 flex flex-wrap gap-3 rounded border p-4" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        <label className="flex flex-col text-xs font-semibold uppercase tracking-wide ">
          Kitchen
          <select
            value={kitchenId}
            onChange={(e) => setKitchenId(e.target.value)}
            className="mt-1 rounded border px-3 py-1.5 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
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
          Raw Material
          <select
            value={rawMaterialId}
            onChange={(e) => setRawMaterialId(e.target.value)}
            className="mt-1 rounded border px-3 py-1.5 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          >
            <option value="">All materials</option>
            {materials.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col text-xs font-semibold uppercase tracking-wide ">
          Type
          <select
            value={movementType}
            onChange={(e) =>
              setMovementType(e.target.value as InventoryMovementType | "")
            }
            className="mt-1 rounded border px-3 py-1.5 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          >
            {TYPES.map((t) => (
              <option key={t} value={t}>
                {t === "" ? "All" : t}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col text-xs font-semibold uppercase tracking-wide ">
          From
          <input
            type="date"
            value={tsAfter}
            onChange={(e) => setTsAfter(e.target.value)}
            className="mt-1 rounded border px-3 py-1.5 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          />
        </label>
        <label className="flex flex-col text-xs font-semibold uppercase tracking-wide ">
          To
          <input
            type="date"
            value={tsBefore}
            onChange={(e) => setTsBefore(e.target.value)}
            className="mt-1 rounded border px-3 py-1.5 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          />
        </label>
      </div>

      <div className="rounded border overflow-hidden" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        {feed.status === "loading" && (
          <p className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>Loading movements…</p>
        )}
        {feed.status === "error" && (
          <div className="m-4 rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            <p className="font-semibold">
              Failed to load movements
            </p>
            <p className="mt-1 text-sm opacity-80">{feed.message}</p>
          </div>
        )}
        {feed.status === "ok" && feed.items.length === 0 && (
          <div className="p-8 text-center text-sm" style={{ color: "var(--text-muted)" }}>
            <p>No movements yet.</p>
          </div>
        )}
        {feed.status === "ok" && feed.items.length > 0 && (
          <ul >
            {feed.items.map((m) => (
              <li
                key={m.id}
                className={`flex items-center justify-between gap-4 border-l-4 px-4 py-3 ${TYPE_STYLES[m.movement_type]}`}
              >
                <div>
                  <p className="text-sm font-semibold">
                    <span className="mr-2 font-mono text-xs uppercase tracking-wide">
                      {m.movement_type}
                    </span>
                    {m.raw_material_name ?? m.raw_material_id}
                  </p>
                  <p className="text-xs ">
                    {m.kitchen_name ?? m.kitchen_id}
                    {m.lot_number && ` · lot ${m.lot_number}`}
                    {m.reason && ` · ${m.reason}`}
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-mono text-sm font-semibold">
                    {Number.parseFloat(m.quantity).toFixed(3)}{" "}
                    {m.unit_code ?? m.unit_id}
                  </p>
                  <p className="text-xs text-sm" style={{ color: "var(--text-muted)" }}>
                    {new Date(m.ts).toLocaleString()}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
