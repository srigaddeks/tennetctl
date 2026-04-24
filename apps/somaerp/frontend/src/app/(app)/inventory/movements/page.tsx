"use client";

import { useCallback, useEffect, useState } from "react";
import {
  listInventoryMovements,
  listKitchens,
  listRawMaterials,
  recordInventoryMovement,
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

const MOVEMENT_TYPES: { value: InventoryMovementType; label: string }[] = [
  { value: "received", label: "Received" },
  { value: "consumed", label: "Consumed" },
  { value: "wasted", label: "Wasted" },
  { value: "adjusted", label: "Adjusted" },
  { value: "expired", label: "Expired" },
];

const TYPE_STYLES: Record<InventoryMovementType, string> = {
  received: "border-green-300 bg-green-50 text-green-900",
  consumed: "border-blue-300 bg-blue-50 text-blue-900",
  wasted: "border-red-300 bg-red-50 text-red-900",
  adjusted: "border-yellow-300 bg-yellow-50 text-yellow-900",
  expired: "border-slate-300 bg-slate-100",
};

type DraftMovement = {
  kitchen_id: string;
  raw_material_id: string;
  movement_type: InventoryMovementType | "";
  quantity: string;
  unit: string;
  lot_number: string;
  notes: string;
  movement_date: string;
};

const today = () => new Date().toISOString().slice(0, 10);

function emptyDraft(): DraftMovement {
  return {
    kitchen_id: "",
    raw_material_id: "",
    movement_type: "",
    quantity: "",
    unit: "",
    lot_number: "",
    notes: "",
    movement_date: today(),
  };
}

export default function InventoryMovementsPage() {
  const [feed, setFeed] = useState<FeedState>({ status: "loading" });
  const [kitchens, setKitchens] = useState<Kitchen[]>([]);
  const [materials, setMaterials] = useState<RawMaterial[]>([]);

  // filters
  const [kitchenId, setKitchenId] = useState<string>("");
  const [rawMaterialId, setRawMaterialId] = useState<string>("");
  const [movementType, setMovementType] = useState<InventoryMovementType | "">("");
  const [tsAfter, setTsAfter] = useState<string>("");
  const [tsBefore, setTsBefore] = useState<string>("");

  // create form
  const [showForm, setShowForm] = useState(false);
  const [draft, setDraft] = useState<DraftMovement>(emptyDraft());
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

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

  const loadFeed = useCallback(() => {
    setFeed({ status: "loading" });
    let cancelled = false;
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

  useEffect(() => {
    const cancel = loadFeed();
    return cancel;
  }, [loadFeed]);

  // When raw material changes, pre-fill the unit from its default_unit_code
  function onMaterialChange(materialId: string) {
    const mat = materials.find((m) => m.id === materialId);
    setDraft((prev) => ({
      ...prev,
      raw_material_id: materialId,
      unit: mat?.default_unit_code ?? "",
    }));
  }

  async function onSubmit() {
    setFormError(null);
    if (!draft.kitchen_id) { setFormError("Select a kitchen"); return; }
    if (!draft.raw_material_id) { setFormError("Select a raw material"); return; }
    if (!draft.movement_type) { setFormError("Select a movement type"); return; }
    const qty = Number.parseFloat(draft.quantity);
    if (!Number.isFinite(qty) || qty <= 0) { setFormError("Quantity must be a positive number"); return; }

    const mat = materials.find((m) => m.id === draft.raw_material_id);
    const unit_id = mat?.default_unit_id;
    if (!unit_id) { setFormError("Could not resolve unit for selected raw material"); return; }

    setBusy(true);
    try {
      await recordInventoryMovement({
        kitchen_id: draft.kitchen_id,
        raw_material_id: draft.raw_material_id,
        movement_type: draft.movement_type as InventoryMovementType,
        quantity: qty,
        unit_id,
        lot_number: draft.lot_number.trim() || null,
        reason: draft.notes.trim() || null,
        metadata: draft.movement_date ? { movement_date: draft.movement_date } : {},
      });
      setDraft(emptyDraft());
      setShowForm(false);
      loadFeed();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-5xl">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>
            Inventory Movements
          </h1>
          <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
            Append-only event log. Most recent first.
          </p>
        </div>
        <button
          type="button"
          onClick={() => { setShowForm((v) => !v); setFormError(null); }}
          className="inline-flex items-center justify-center rounded px-3 py-1.5 text-sm font-medium"
          style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
        >
          {showForm ? "Cancel" : "+ Log Movement"}
        </button>
      </div>

      {/* Inline create form */}
      {showForm && (
        <div className="mb-6 rounded border p-5" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
          <h2 className="mb-4 text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Log New Movement</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Kitchen *</label>
              <select
                value={draft.kitchen_id}
                onChange={(e) => setDraft((p) => ({ ...p, kitchen_id: e.target.value }))}
                className="w-full rounded border px-3 py-2 text-sm focus:outline-none"
                style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
              >
                <option value="">Select kitchen…</option>
                {kitchens.map((k) => (
                  <option key={k.id} value={k.id}>{k.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Raw Material *</label>
              <select
                value={draft.raw_material_id}
                onChange={(e) => onMaterialChange(e.target.value)}
                className="w-full rounded border px-3 py-2 text-sm focus:outline-none"
                style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
              >
                <option value="">Select material…</option>
                {materials.map((m) => (
                  <option key={m.id} value={m.id}>{m.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Movement Type *</label>
              <select
                value={draft.movement_type}
                onChange={(e) => setDraft((p) => ({ ...p, movement_type: e.target.value as InventoryMovementType | "" }))}
                className="w-full rounded border px-3 py-2 text-sm focus:outline-none"
                style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
              >
                <option value="">Select type…</option>
                {MOVEMENT_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Quantity *</label>
              <input
                type="number"
                step="0.001"
                min="0"
                value={draft.quantity}
                onChange={(e) => setDraft((p) => ({ ...p, quantity: e.target.value }))}
                placeholder="1.5"
                className="w-full rounded border px-3 py-2 text-sm focus:outline-none"
                style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
              />
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Unit</label>
              <input
                type="text"
                value={draft.unit}
                onChange={(e) => setDraft((p) => ({ ...p, unit: e.target.value }))}
                placeholder="kg"
                className="w-full rounded border px-3 py-2 text-sm focus:outline-none"
                style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
              />
              <p className="mt-0.5 text-xs" style={{ color: "var(--text-muted)" }}>Pre-filled from material default</p>
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Date</label>
              <input
                type="date"
                value={draft.movement_date}
                onChange={(e) => setDraft((p) => ({ ...p, movement_date: e.target.value }))}
                className="w-full rounded border px-3 py-2 text-sm focus:outline-none"
                style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
              />
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Lot Number</label>
              <input
                type="text"
                value={draft.lot_number}
                onChange={(e) => setDraft((p) => ({ ...p, lot_number: e.target.value }))}
                placeholder="optional"
                className="w-full rounded border px-3 py-2 text-sm focus:outline-none"
                style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
              />
            </div>

            <div className="sm:col-span-2">
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Notes</label>
              <input
                type="text"
                value={draft.notes}
                onChange={(e) => setDraft((p) => ({ ...p, notes: e.target.value }))}
                placeholder="optional"
                className="w-full rounded border px-3 py-2 text-sm focus:outline-none"
                style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
              />
            </div>
          </div>

          {formError && (
            <div className="mt-3 rounded border p-3 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
              {formError}
            </div>
          )}

          <div className="mt-4 flex gap-3">
            <button
              type="button"
              onClick={onSubmit}
              disabled={busy}
              className="inline-flex items-center rounded px-4 py-2 text-sm font-medium disabled:opacity-50"
              style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
            >
              {busy ? "Saving…" : "Save Movement"}
            </button>
            <button
              type="button"
              onClick={() => { setShowForm(false); setDraft(emptyDraft()); setFormError(null); }}
              className="inline-flex items-center rounded border px-4 py-2 text-sm font-medium"
              style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="mb-4 flex flex-wrap gap-3 rounded border p-4" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        <label className="flex flex-col text-xs font-semibold uppercase tracking-wide">
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
        <label className="flex flex-col text-xs font-semibold uppercase tracking-wide">
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
        <label className="flex flex-col text-xs font-semibold uppercase tracking-wide">
          Type
          <select
            value={movementType}
            onChange={(e) =>
              setMovementType(e.target.value as InventoryMovementType | "")
            }
            className="mt-1 rounded border px-3 py-1.5 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          >
            <option value="">All</option>
            {MOVEMENT_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </label>
        <label className="flex flex-col text-xs font-semibold uppercase tracking-wide">
          From
          <input
            type="date"
            value={tsAfter}
            onChange={(e) => setTsAfter(e.target.value)}
            className="mt-1 rounded border px-3 py-1.5 text-sm focus:outline-none" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
          />
        </label>
        <label className="flex flex-col text-xs font-semibold uppercase tracking-wide">
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
          <ul>
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
                  <p className="text-xs">
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
