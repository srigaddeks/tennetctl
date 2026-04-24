"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import {
  attachKitchenEquipment,
  detachKitchenEquipment,
  getEquipment,
  listEquipmentCategories,
  listKitchens,
  listKitchenEquipment,
  updateEquipment,
} from "@/lib/api";
import type {
  Equipment,
  EquipmentCategory,
  EquipmentStatus,
  Kitchen,
  KitchenEquipmentLink,
} from "@/types/api";

type EquipmentState =
  | { status: "loading" }
  | { status: "ok"; item: Equipment }
  | { status: "error"; message: string };

type KitchensState =
  | { status: "loading" }
  | { status: "ok"; items: KitchenEquipmentLink[] }
  | { status: "error"; message: string };

type Tab = "details" | "kitchens";

type EditDraft = {
  name: string;
  slug: string;
  category_id: string;
  status: EquipmentStatus;
  purchase_date: string;
  expected_lifespan_months: string;
  notes: string;
};

function equipmentToEditDraft(e: Equipment): EditDraft {
  return {
    name: e.name,
    slug: e.slug,
    category_id: String(e.category_id),
    status: e.status,
    purchase_date: e.purchase_date ?? "",
    expected_lifespan_months: e.expected_lifespan_months != null ? String(e.expected_lifespan_months) : "",
    notes: "",
  };
}

export default function EquipmentDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params?.id ?? "";

  const [tab, setTab] = useState<Tab>("details");
  const [state, setState] = useState<EquipmentState>({ status: "loading" });
  const [kitchenLinks, setKitchenLinks] = useState<KitchensState>({ status: "loading" });
  const [categories, setCategories] = useState<EquipmentCategory[]>([]);
  const [allKitchens, setAllKitchens] = useState<Kitchen[]>([]);

  // Edit mode
  const [editing, setEditing] = useState(false);
  const [editDraft, setEditDraft] = useState<EditDraft | null>(null);
  const [editError, setEditError] = useState<string | null>(null);
  const [editBusy, setEditBusy] = useState(false);

  // Assign kitchen form
  const [showAssign, setShowAssign] = useState(false);
  const [assignKitchenId, setAssignKitchenId] = useState("");
  const [assignQty, setAssignQty] = useState("1");
  const [assignNotes, setAssignNotes] = useState("");
  const [assignError, setAssignError] = useState<string | null>(null);
  const [assignBusy, setAssignBusy] = useState(false);

  const loadEquipment = useCallback(() => {
    if (!id) return;
    setState({ status: "loading" });
    getEquipment(id)
      .then((item) => setState({ status: "ok", item }))
      .catch((err: unknown) => {
        setState({ status: "error", message: err instanceof Error ? err.message : "Unknown error" });
      });
  }, [id]);

  const loadKitchenLinks = useCallback(() => {
    if (!id) return;
    setKitchenLinks({ status: "loading" });
    // listKitchenEquipment is kitchen-centric; we need to find all kitchens with this equipment.
    // We load all kitchens first then filter by equipment_id by loading each kitchen's links.
    // However, a simpler approach: load all kitchens, then for each kitchen load its equipment links.
    // Since there's no equipment-centric endpoint, we check all kitchens.
    listKitchens()
      .then((kitchenList) => {
        return Promise.all(
          kitchenList.map((k) =>
            listKitchenEquipment(k.id).then((links) =>
              links.filter((l) => l.equipment_id === id)
            ).catch(() => [] as KitchenEquipmentLink[])
          )
        ).then((nested) => nested.flat());
      })
      .then((items) => setKitchenLinks({ status: "ok", items }))
      .catch((err: unknown) => {
        setKitchenLinks({ status: "error", message: err instanceof Error ? err.message : "Unknown error" });
      });
  }, [id]);

  useEffect(() => {
    loadEquipment();
    loadKitchenLinks();
    listEquipmentCategories()
      .then(setCategories)
      .catch(() => undefined);
    listKitchens()
      .then(setAllKitchens)
      .catch(() => undefined);
  }, [loadEquipment, loadKitchenLinks]);

  function startEditing() {
    if (state.status !== "ok") return;
    setEditDraft(equipmentToEditDraft(state.item));
    setEditing(true);
    setEditError(null);
  }

  async function saveEdit() {
    if (!editDraft) return;
    setEditError(null);
    if (!editDraft.name.trim()) { setEditError("Name is required"); return; }
    setEditBusy(true);
    try {
      await updateEquipment(id, {
        name: editDraft.name.trim(),
        slug: editDraft.slug.trim(),
        category_id: editDraft.category_id ? Number(editDraft.category_id) : undefined,
        status: editDraft.status,
        purchase_date: editDraft.purchase_date.trim() || null,
        expected_lifespan_months: editDraft.expected_lifespan_months.trim()
          ? Number.parseInt(editDraft.expected_lifespan_months, 10)
          : null,
      });
      setEditing(false);
      loadEquipment();
    } catch (err: unknown) {
      setEditError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setEditBusy(false);
    }
  }

  async function onAssign() {
    setAssignError(null);
    if (!assignKitchenId) { setAssignError("Select a kitchen"); return; }
    const qty = Number.parseInt(assignQty, 10);
    if (!Number.isFinite(qty) || qty < 1) { setAssignError("Quantity must be at least 1"); return; }
    setAssignBusy(true);
    try {
      await attachKitchenEquipment(assignKitchenId, {
        equipment_id: id,
        quantity: qty,
        notes: assignNotes.trim() || null,
      });
      setShowAssign(false);
      setAssignKitchenId("");
      setAssignQty("1");
      setAssignNotes("");
      loadKitchenLinks();
    } catch (err: unknown) {
      setAssignError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setAssignBusy(false);
    }
  }

  async function onDetach(kitchenId: string) {
    try {
      await detachKitchenEquipment(kitchenId, id);
      loadKitchenLinks();
    } catch (err: unknown) {
      // surface error minimally
      setAssignError(err instanceof Error ? err.message : "Failed to remove");
    }
  }

  const equipment = state.status === "ok" ? state.item : null;

  return (
    <div className="max-w-4xl">
      {/* Header */}
      <div className="mb-6">
        {state.status === "loading" && (
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>Loading…</p>
        )}
        {state.status === "error" && (
          <div className="rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
            <p className="font-semibold">Failed to load equipment</p>
            <p className="mt-1 opacity-80">{state.message}</p>
          </div>
        )}
        {equipment && (
          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="text-xl font-semibold" style={{ color: "var(--text-primary)" }}>
                {equipment.name}
              </h1>
              <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
                {equipment.category_name ?? equipment.category_code ?? "Unknown category"}
              </p>
            </div>
            <StatusBadge status={equipment.status} />
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="mb-4 flex gap-1 border-b" style={{ borderColor: "var(--border)" }}>
        {(["details", "kitchens"] as Tab[]).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className="px-4 py-2 text-sm font-medium capitalize"
            style={{
              color: tab === t ? "var(--accent)" : "var(--text-secondary)",
              borderBottom: tab === t ? "2px solid var(--accent)" : "2px solid transparent",
              marginBottom: "-1px",
            }}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Details tab */}
      {tab === "details" && equipment && (
        <div className="rounded border p-5" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
          {!editing ? (
            <>
              <div className="mb-4 flex justify-end">
                <button
                  type="button"
                  onClick={startEditing}
                  className="rounded border px-3 py-1.5 text-sm font-medium"
                  style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
                >
                  Edit
                </button>
              </div>
              <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                <InfoField label="Name" value={equipment.name} />
                <InfoField label="Slug" value={equipment.slug} />
                <InfoField label="Category" value={equipment.category_name ?? equipment.category_code ?? "—"} />
                <InfoField label="Status" value={<StatusBadge status={equipment.status} />} />
                <InfoField label="Purchase Date" value={equipment.purchase_date ?? "—"} />
                <InfoField label="Lifespan" value={equipment.expected_lifespan_months != null ? `${equipment.expected_lifespan_months} months` : "—"} />
                <InfoField label="Purchase Cost" value={equipment.purchase_cost ? `${equipment.currency_code ?? ""} ${Number.parseFloat(equipment.purchase_cost).toFixed(2)}` : "—"} />
              </dl>
            </>
          ) : (
            editDraft && (
              <>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  <div>
                    <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Name *</label>
                    <input
                      type="text"
                      value={editDraft.name}
                      onChange={(e) => setEditDraft((p) => p ? { ...p, name: e.target.value } : p)}
                      className="w-full rounded border px-3 py-2 text-sm focus:outline-none"
                      style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Slug</label>
                    <input
                      type="text"
                      value={editDraft.slug}
                      onChange={(e) => setEditDraft((p) => p ? { ...p, slug: e.target.value } : p)}
                      className="w-full rounded border px-3 py-2 text-sm focus:outline-none"
                      style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Category</label>
                    <select
                      value={editDraft.category_id}
                      onChange={(e) => setEditDraft((p) => p ? { ...p, category_id: e.target.value } : p)}
                      className="w-full rounded border px-3 py-2 text-sm focus:outline-none"
                      style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
                    >
                      <option value="">Select…</option>
                      {categories.map((c) => (
                        <option key={c.id} value={c.id}>{c.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Status</label>
                    <select
                      value={editDraft.status}
                      onChange={(e) => setEditDraft((p) => p ? { ...p, status: e.target.value as EquipmentStatus } : p)}
                      className="w-full rounded border px-3 py-2 text-sm focus:outline-none"
                      style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
                    >
                      <option value="active">Active</option>
                      <option value="maintenance">Maintenance</option>
                      <option value="retired">Retired</option>
                    </select>
                  </div>
                  <div>
                    <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Purchase Date</label>
                    <input
                      type="date"
                      value={editDraft.purchase_date}
                      onChange={(e) => setEditDraft((p) => p ? { ...p, purchase_date: e.target.value } : p)}
                      className="w-full rounded border px-3 py-2 text-sm focus:outline-none"
                      style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Lifespan (months)</label>
                    <input
                      type="number"
                      min="1"
                      value={editDraft.expected_lifespan_months}
                      onChange={(e) => setEditDraft((p) => p ? { ...p, expected_lifespan_months: e.target.value } : p)}
                      placeholder="24"
                      className="w-full rounded border px-3 py-2 text-sm focus:outline-none"
                      style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
                    />
                  </div>
                </div>

                {editError && (
                  <div className="mt-3 rounded border p-3 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
                    {editError}
                  </div>
                )}

                <div className="mt-4 flex gap-3">
                  <button
                    type="button"
                    onClick={saveEdit}
                    disabled={editBusy}
                    className="inline-flex items-center rounded px-4 py-2 text-sm font-medium disabled:opacity-50"
                    style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
                  >
                    {editBusy ? "Saving…" : "Save Changes"}
                  </button>
                  <button
                    type="button"
                    onClick={() => { setEditing(false); setEditError(null); }}
                    className="inline-flex items-center rounded border px-4 py-2 text-sm font-medium"
                    style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
                  >
                    Cancel
                  </button>
                </div>
              </>
            )
          )}
        </div>
      )}

      {/* Kitchens tab */}
      {tab === "kitchens" && (
        <div>
          <div className="mb-4 flex justify-end">
            <button
              type="button"
              onClick={() => { setShowAssign((v) => !v); setAssignError(null); }}
              className="inline-flex items-center justify-center rounded px-3 py-1.5 text-sm font-medium"
              style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
            >
              {showAssign ? "Cancel" : "Assign to Kitchen"}
            </button>
          </div>

          {showAssign && (
            <div className="mb-4 rounded border p-4" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <div>
                  <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Kitchen *</label>
                  <select
                    value={assignKitchenId}
                    onChange={(e) => setAssignKitchenId(e.target.value)}
                    className="w-full rounded border px-3 py-2 text-sm focus:outline-none"
                    style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
                  >
                    <option value="">Select kitchen…</option>
                    {allKitchens.map((k) => (
                      <option key={k.id} value={k.id}>{k.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Quantity</label>
                  <input
                    type="number"
                    min="1"
                    value={assignQty}
                    onChange={(e) => setAssignQty(e.target.value)}
                    className="w-full rounded border px-3 py-2 text-sm focus:outline-none"
                    style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
                  />
                </div>
                <div>
                  <label className="mb-1 block text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Notes</label>
                  <input
                    type="text"
                    value={assignNotes}
                    onChange={(e) => setAssignNotes(e.target.value)}
                    placeholder="optional"
                    className="w-full rounded border px-3 py-2 text-sm focus:outline-none"
                    style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-card)", color: "var(--text-primary)" }}
                  />
                </div>
              </div>
              {assignError && (
                <div className="mt-3 rounded border p-3 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
                  {assignError}
                </div>
              )}
              <div className="mt-3 flex gap-3">
                <button
                  type="button"
                  onClick={onAssign}
                  disabled={assignBusy}
                  className="inline-flex items-center rounded px-4 py-2 text-sm font-medium disabled:opacity-50"
                  style={{ backgroundColor: "var(--accent)", color: "var(--accent-text)" }}
                >
                  {assignBusy ? "Assigning…" : "Assign"}
                </button>
              </div>
            </div>
          )}

          <div className="rounded border overflow-hidden" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
            {kitchenLinks.status === "loading" && (
              <p className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>Loading kitchen assignments…</p>
            )}
            {kitchenLinks.status === "error" && (
              <div className="m-4 rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error)" }}>
                <p className="font-semibold">Failed to load kitchen assignments</p>
                <p className="mt-1 opacity-80">{kitchenLinks.message}</p>
              </div>
            )}
            {kitchenLinks.status === "ok" && kitchenLinks.items.length === 0 && (
              <p className="p-8 text-center text-sm" style={{ color: "var(--text-muted)" }}>
                Not assigned to any kitchen yet.
              </p>
            )}
            {kitchenLinks.status === "ok" && kitchenLinks.items.length > 0 && (
              <table className="min-w-full text-sm">
                <thead style={{ backgroundColor: "var(--bg-table-header)", borderBottom: "1px solid var(--border)" }}>
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Kitchen</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Quantity</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Assigned</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Notes</th>
                    <th className="px-4 py-3"></th>
                  </tr>
                </thead>
                <tbody>
                  {kitchenLinks.items.map((link) => (
                    <tr
                      key={link.id}
                      onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-table-hover)"; }}
                      onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.backgroundColor = "transparent"; }}
                    >
                      <td className="px-4 py-2.5 font-medium" style={{ color: "var(--text-primary)" }}>
                        {link.kitchen_name ?? link.kitchen_id}
                      </td>
                      <td className="px-4 py-2.5 font-mono" style={{ color: "var(--text-secondary)" }}>
                        {link.quantity}
                      </td>
                      <td className="px-4 py-2.5 text-xs font-mono" style={{ color: "var(--text-secondary)" }}>
                        {link.created_at.slice(0, 10)}
                      </td>
                      <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)" }}>
                        {link.notes ?? "—"}
                      </td>
                      <td className="px-4 py-2.5">
                        <button
                          type="button"
                          onClick={() => onDetach(link.kitchen_id)}
                          className="rounded border px-3 py-1 text-xs font-medium hover:bg-red-50"
                          style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
                        >
                          Remove
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function InfoField({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
        {label}
      </dt>
      <dd className="mt-1 text-sm" style={{ color: "var(--text-primary)" }}>{value}</dd>
    </div>
  );
}

function StatusBadge({ status }: { status: EquipmentStatus }) {
  const styles: Record<EquipmentStatus, string> = {
    active: "bg-green-100 text-green-800 border-green-200",
    maintenance: "bg-yellow-100 text-yellow-800 border-yellow-200",
    retired: "bg-slate-100 border-slate-200",
  };
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${styles[status]}`}>
      {status}
    </span>
  );
}
