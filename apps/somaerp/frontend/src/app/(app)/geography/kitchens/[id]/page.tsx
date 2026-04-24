"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import {
  attachKitchenEquipment,
  closeKitchenCapacity,
  detachKitchenEquipment,
  getKitchen,
  listEquipment,
  listKitchenCapacity,
  listKitchenEquipment,
} from "@/lib/api";
import type { Equipment, Kitchen, KitchenCapacity, KitchenEquipmentLink, KitchenStatus } from "@/types/api";

type KitchenState = { status: "loading" } | { status: "ok"; kitchen: Kitchen } | { status: "error"; message: string };
type CapacityState = { status: "loading" } | { status: "ok"; items: KitchenCapacity[] } | { status: "error"; message: string };
type CloseState = { status: "idle" } | { status: "picking"; capacityId: string; validTo: string } | { status: "submitting"; capacityId: string } | { status: "error"; capacityId: string; message: string };
type EquipmentListState = { status: "loading" } | { status: "ok"; items: KitchenEquipmentLink[] } | { status: "error"; message: string };
type AllEquipmentState = { status: "loading" } | { status: "ok"; items: Equipment[] } | { status: "error"; message: string };

const inputStyle = { borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" };

export default function KitchenDetailPage() {
  const params = useParams<{ id: string }>();
  const kitchenId = params?.id ?? ""

  const [kitchen, setKitchen] = useState<KitchenState>({ status: "loading" });
  const [capacity, setCapacity] = useState<CapacityState>({ status: "loading" });
  const [showHistory, setShowHistory] = useState<boolean>(false);
  const [closing, setClosing] = useState<CloseState>({ status: "idle" });
  const [equipment, setEquipment] = useState<EquipmentListState>({ status: "loading" });
  const [allEquipment, setAllEquipment] = useState<AllEquipmentState>({ status: "loading" });
  const [draftEquipment, setDraftEquipment] = useState<{ equipment_id: string; quantity: string; notes: string }>({ equipment_id: "", quantity: "1", notes: "" });
  const [equipmentError, setEquipmentError] = useState<string | null>(null);
  const [equipmentBusy, setEquipmentBusy] = useState<boolean>(false);

  useEffect(() => {
    if (!kitchenId) return;
    let cancelled = false;
    setKitchen({ status: "loading" });
    getKitchen(kitchenId)
      .then((k) => { if (!cancelled) setKitchen({ status: "ok", kitchen: k }); })
      .catch((err: unknown) => { if (!cancelled) setKitchen({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }); });
    return () => { cancelled = true; };
  }, [kitchenId]);

  const loadCapacity = useCallback(() => {
    if (!kitchenId) return () => {};
    let cancelled = false;
    setCapacity({ status: "loading" });
    listKitchenCapacity(kitchenId, { include_history: showHistory })
      .then((items) => { if (!cancelled) setCapacity({ status: "ok", items }); })
      .catch((err: unknown) => { if (!cancelled) setCapacity({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }); });
    return () => { cancelled = true; };
  }, [kitchenId, showHistory]);

  useEffect(() => { const cleanup = loadCapacity(); return cleanup; }, [loadCapacity]);

  const loadEquipment = useCallback(() => {
    if (!kitchenId) return;
    setEquipment({ status: "loading" });
    listKitchenEquipment(kitchenId)
      .then((items) => setEquipment({ status: "ok", items }))
      .catch((err: unknown) => setEquipment({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }));
  }, [kitchenId]);

  useEffect(() => {
    loadEquipment();
    listEquipment()
      .then((items) => setAllEquipment({ status: "ok", items }))
      .catch((err: unknown) => setAllEquipment({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }));
  }, [loadEquipment]);

  async function onAttachEquipment() {
    setEquipmentError(null);
    if (!draftEquipment.equipment_id) { setEquipmentError("Pick equipment"); return; }
    const qty = Number.parseInt(draftEquipment.quantity, 10);
    if (!Number.isFinite(qty) || qty <= 0) { setEquipmentError("Quantity must be a positive integer"); return; }
    setEquipmentBusy(true);
    try {
      await attachKitchenEquipment(kitchenId, { equipment_id: draftEquipment.equipment_id, quantity: qty, notes: draftEquipment.notes.trim() === "" ? null : draftEquipment.notes.trim() });
      setDraftEquipment({ equipment_id: "", quantity: "1", notes: "" });
      loadEquipment();
    } catch (err: unknown) {
      setEquipmentError(err instanceof Error ? err.message : "Unknown error");
    } finally { setEquipmentBusy(false); }
  }

  async function onDetachEquipment(equipmentId: string) {
    setEquipmentBusy(true);
    try { await detachKitchenEquipment(kitchenId, equipmentId); loadEquipment(); }
    catch (err: unknown) { setEquipmentError(err instanceof Error ? err.message : "Unknown error"); }
    finally { setEquipmentBusy(false); }
  }

  async function onConfirmClose(capacityId: string, validTo: string) {
    if (!validTo) { setClosing({ status: "error", capacityId, message: "Pick a valid-to date" }); return; }
    setClosing({ status: "submitting", capacityId });
    try { await closeKitchenCapacity(kitchenId, capacityId, validTo); setClosing({ status: "idle" }); loadCapacity(); }
    catch (err: unknown) { setClosing({ status: "error", capacityId, message: err instanceof Error ? err.message : "Unknown error" }); }
  }

  return (
    <div className="max-w-5xl space-y-5">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>
          {kitchen.status === "ok" ? kitchen.kitchen.name : "Kitchen"}
        </h1>
        <Link href={`/geography/kitchens/${kitchenId}/capacity/new`} className="inline-flex items-center rounded px-3 py-1.5 text-sm font-medium" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}>
          + Add Capacity
        </Link>
      </div>

      {/* Kitchen info panel */}
      <div className="rounded border p-5" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        {kitchen.status === "loading" && <p className="text-sm" style={{ color: "var(--text-muted)" }}>Loading kitchen…</p>}
        {kitchen.status === "error" && (
          <div className="rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            <span className="font-semibold">Failed to load kitchen</span> <span className="opacity-80">{kitchen.message}</span>
          </div>
        )}
        {kitchen.status === "ok" && (
          <dl className="grid grid-cols-2 gap-4 sm:grid-cols-3">
            <InfoField label="Type" value={kitchen.kitchen.kitchen_type} />
            <InfoField label="Status" value={<KitchenStatusBadge status={kitchen.kitchen.status} />} />
            <InfoField label="Location" value={kitchen.kitchen.location_name} />
            <InfoField label="Slug" value={<code className="font-mono text-xs">{kitchen.kitchen.slug}</code>} />
            <InfoField label="Created" value={formatDate(kitchen.kitchen.created_at)} />
            <InfoField label="Updated" value={formatDate(kitchen.kitchen.updated_at)} />
          </dl>
        )}
      </div>

      {/* Capacity table */}
      <div className="rounded border overflow-hidden" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        <div className="flex items-center justify-between px-4 py-3" style={{ borderBottom: "1px solid var(--border)" }}>
          <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Capacity</h2>
          <label className="inline-flex cursor-pointer items-center gap-2 text-sm" style={{ color: "var(--text-secondary)" }}>
            <input type="checkbox" checked={showHistory} onChange={(e) => setShowHistory(e.target.checked)} className="h-4 w-4 rounded" />
            Show history
          </label>
        </div>
        {capacity.status === "loading" && <p className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>Loading capacity…</p>}
        {capacity.status === "error" && (
          <div className="m-4 rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            <span className="font-semibold">Failed to load capacity</span> <span className="opacity-80">{capacity.message}</span>
          </div>
        )}
        {capacity.status === "ok" && capacity.items.length === 0 && (
          <div className="p-8 text-center text-sm" style={{ color: "var(--text-muted)" }}>
            <p>No capacity rows yet.</p>
            <Link href={`/geography/kitchens/${kitchenId}/capacity/new`} className="mt-2 inline-block underline" style={{ color: "var(--text-accent)" }}>Add the first capacity row</Link>
          </div>
        )}
        {capacity.status === "ok" && capacity.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead style={{ backgroundColor: "var(--bg-table-header)", borderBottom: "1px solid var(--border)" }}>
                <tr>
                  {["Product Line", "Capacity", "Window", "Valid From", "Valid To", "Actions"].map((h) => (
                    <th key={h} className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {capacity.items.map((c, idx) => {
                  const isActive = c.valid_to === null;
                  const picking = closing.status === "picking" && closing.capacityId === c.id;
                  return (
                    <tr key={c.id} style={{ borderTop: idx > 0 ? "1px solid var(--border)" : undefined }}
                      onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-table-hover)"; }}
                      onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "transparent"; }}>
                      <td className="px-4 py-2.5 font-medium" style={{ color: "var(--text-primary)" }}>{c.product_line_name}</td>
                      <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)" }}>{c.capacity_value} {c.capacity_unit_code}</td>
                      <td className="px-4 py-2.5 font-mono text-xs" style={{ color: "var(--text-secondary)" }}>{formatTime(c.time_window_start)}–{formatTime(c.time_window_end)}</td>
                      <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)" }}>{c.valid_from}</td>
                      <td className="px-4 py-2.5" style={{ color: isActive ? "var(--status-active)" : "var(--text-secondary)" }}>
                        {isActive ? "— current —" : c.valid_to}
                      </td>
                      <td className="px-4 py-2.5">
                        {isActive && !picking && (
                          <button type="button" onClick={() => setClosing({ status: "picking", capacityId: c.id, validTo: today() })} className="rounded border px-3 py-1 text-xs font-medium" style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}>
                            Close
                          </button>
                        )}
                        {picking && (
                          <div className="flex items-center gap-2">
                            <input type="date" value={closing.status === "picking" ? closing.validTo : today()} onChange={(e) => setClosing({ status: "picking", capacityId: c.id, validTo: e.target.value })} className="rounded border px-2 py-1 text-xs" style={inputStyle} />
                            <button type="button" onClick={() => closing.status === "picking" && onConfirmClose(c.id, closing.validTo)} className="rounded px-2 py-1 text-xs font-medium" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}>Confirm</button>
                            <button type="button" onClick={() => setClosing({ status: "idle" })} className="rounded border px-2 py-1 text-xs" style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}>Cancel</button>
                          </div>
                        )}
                        {closing.status === "submitting" && closing.capacityId === c.id && <span className="text-xs" style={{ color: "var(--text-muted)" }}>Closing…</span>}
                        {closing.status === "error" && closing.capacityId === c.id && <p className="mt-1 text-xs" style={{ color: "var(--status-error)" }}>{closing.message}</p>}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Equipment section */}
      <div className="rounded border overflow-hidden" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        <div className="px-4 py-3" style={{ borderBottom: "1px solid var(--border)" }}>
          <h2 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Equipment</h2>
        </div>
        {equipment.status === "loading" && <p className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>Loading equipment…</p>}
        {equipment.status === "error" && (
          <div className="m-4 rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            <span className="font-semibold">Failed to load equipment</span> <span className="opacity-80">{equipment.message}</span>
          </div>
        )}
        {equipment.status === "ok" && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead style={{ backgroundColor: "var(--bg-table-header)", borderBottom: "1px solid var(--border)" }}>
                <tr>
                  {["Equipment", "Category", "Status", "Qty", "Notes",].map((h, i) => (
                    <th key={i} className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {equipment.items.map((eq, idx) => (
                  <tr key={eq.id} style={{ borderTop: idx > 0 ? "1px solid var(--border)" : undefined }}
                    onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-table-hover)"; }}
                    onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "transparent"; }}>
                    <td className="px-4 py-2.5 font-medium" style={{ color: "var(--text-primary)" }}>{eq.equipment_name ?? eq.equipment_id}</td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)" }}>{eq.equipment_category_name ?? eq.equipment_category_code}</td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)" }}>{eq.equipment_status ?? "—"}</td>
                    <td className="px-4 py-2.5 font-mono" style={{ color: "var(--text-secondary)" }}>{eq.quantity}</td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)" }}>{eq.notes ?? "—"}</td>
                    <td className="px-4 py-2.5">
                      <button type="button" onClick={() => onDetachEquipment(eq.equipment_id)} disabled={equipmentBusy} className="rounded border px-3 py-1 text-xs font-medium disabled:opacity-50" style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}>
                        Detach
                      </button>
                    </td>
                  </tr>
                ))}
                {/* Attach row */}
                <tr style={{ borderTop: "1px solid var(--border)", backgroundColor: "var(--bg-surface)" }}>
                  <td className="px-4 py-2.5" colSpan={2}>
                    <select value={draftEquipment.equipment_id} onChange={(e) => setDraftEquipment((prev) => ({ ...prev, equipment_id: e.target.value }))} className="w-full rounded border px-2 py-1 text-sm" style={inputStyle}>
                      <option value="">Pick equipment…</option>
                      {allEquipment.status === "ok" && allEquipment.items.map((e) => <option key={e.id} value={e.id}>{e.name} ({e.category_code})</option>)}
                    </select>
                  </td>
                  <td className="px-4 py-2.5" />
                  <td className="px-4 py-2.5">
                    <input type="number" min={1} value={draftEquipment.quantity} onChange={(e) => setDraftEquipment((prev) => ({ ...prev, quantity: e.target.value }))} className="w-20 rounded border px-2 py-1 font-mono text-sm" style={inputStyle} />
                  </td>
                  <td className="px-4 py-2.5">
                    <input type="text" value={draftEquipment.notes} onChange={(e) => setDraftEquipment((prev) => ({ ...prev, notes: e.target.value }))} placeholder="Notes" className="w-full rounded border px-2 py-1 text-sm" style={inputStyle} />
                  </td>
                  <td className="px-4 py-2.5">
                    <button type="button" onClick={onAttachEquipment} disabled={equipmentBusy} className="rounded px-3 py-1 text-xs font-medium disabled:opacity-50" style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}>
                      Attach
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        )}
        {equipmentError !== null && (
          <div className="m-4 rounded border p-3 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>{equipmentError}</div>
        )}
      </div>
    </div>
  );
}

function InfoField({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>{label}</dt>
      <dd className="mt-1 text-sm" style={{ color: "var(--text-primary)" }}>{value}</dd>
    </div>
  );
}

function KitchenStatusBadge({ status }: { status: KitchenStatus }) {
  const style = status === "active"
    ? { backgroundColor: "var(--status-active-bg)", color: "var(--status-active)" }
    : status === "paused"
    ? { backgroundColor: "var(--status-paused-bg)", color: "var(--status-paused)" }
    : { backgroundColor: "var(--status-draft-bg)", color: "var(--status-draft)" };
  return <span className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium" style={style}>{status}</span>;
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toISOString().slice(0, 10);
}

function formatTime(t: string): string {
  return t.length >= 5 ? t.slice(0, 5) : t;
}

function today(): string {
  return new Date().toISOString().slice(0, 10);
}
