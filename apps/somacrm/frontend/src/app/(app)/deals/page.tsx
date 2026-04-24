"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listDeals, createDeal, listPipelineStages } from "@/lib/api";
import type { Deal, DealStatus, DealCreate, PipelineStage } from "@/types/api";

type DealsState =
  | { status: "loading" }
  | { status: "ok"; items: Deal[] }
  | { status: "error"; message: string };

type StagesState =
  | { status: "loading" }
  | { status: "ok"; items: PipelineStage[] }
  | { status: "error" };

type StatusFilter = DealStatus | "all";

const STATUS_LABELS: Record<DealStatus, string> = {
  open: "Open",
  won: "Won",
  lost: "Lost",
};

const STATUS_STYLES: Record<DealStatus, string> = {
  open: "bg-blue-100 text-blue-800",
  won: "bg-green-100 text-green-800",
  lost: "bg-red-100 text-red-800",
};

export default function DealsPage() {
  const [deals, setDeals] = useState<DealsState>({ status: "loading" });
  const [stages, setStages] = useState<StagesState>({ status: "loading" });
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [stageFilter, setStageFilter] = useState("");
  const [q, setQ] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<DealCreate>({ title: "", currency: "INR" });
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    listPipelineStages()
      .then((items) => setStages({ status: "ok", items }))
      .catch(() => setStages({ status: "error" }));
  }, []);

  function reload() {
    listDeals({ status: statusFilter === "all" ? undefined : statusFilter, stage_id: stageFilter || undefined, q: q || undefined })
      .then((items) => setDeals({ status: "ok", items }))
      .catch((err: unknown) => setDeals({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }));
  }

  useEffect(() => {
    let cancelled = false;
    setDeals({ status: "loading" });
    listDeals({ status: statusFilter === "all" ? undefined : statusFilter, stage_id: stageFilter || undefined, q: q || undefined })
      .then((items) => { if (!cancelled) setDeals({ status: "ok", items }); })
      .catch((err: unknown) => { if (!cancelled) setDeals({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }); });
    return () => { cancelled = true; };
  }, [statusFilter, stageFilter, q]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setFormError(null);
    try {
      await createDeal(formData);
      setShowForm(false);
      setFormData({ title: "" });
      reload();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to create deal");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="max-w-5xl">
      <div className="page-header">
        <div>
          <h1 className="page-title">Deals</h1>
          <p className="page-subtitle">Revenue opportunities and close rates</p>
        </div>
        <div className="flex gap-2">
          <Link href="/pipeline" className="btn-secondary">Kanban View</Link>
          <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
            {showForm ? "Cancel" : "+ New Deal"}
          </button>
        </div>
      </div>

      {showForm && (
        <div className="mb-6 rounded border p-5" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
          <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16, color: "var(--text-primary)" }}>New Deal</h3>
          <form onSubmit={handleCreate}>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="erp-form-group">
                <label className="erp-label">Title *</label>
                <input className="erp-input" required value={formData.title} onChange={e => setFormData({ ...formData, title: e.target.value })} />
              </div>
              <div className="erp-form-group">
                <label className="erp-label">Stage</label>
                <select className="erp-select" value={formData.stage_id ?? ""} onChange={e => setFormData({ ...formData, stage_id: e.target.value || undefined })}>
                  <option value="">No stage</option>
                  {stages.status === "ok" && stages.items.map(s => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>
              <div className="erp-form-group">
                <label className="erp-label">Value</label>
                <input type="number" className="erp-input" value={formData.value ?? ""} onChange={e => setFormData({ ...formData, value: e.target.value ? parseFloat(e.target.value) : undefined })} />
              </div>
              <div className="erp-form-group">
                <label className="erp-label">Currency</label>
                <input className="erp-input" value={formData.currency ?? "INR"} onChange={e => setFormData({ ...formData, currency: e.target.value || undefined })} placeholder="INR" />
              </div>
              <div className="erp-form-group">
                <label className="erp-label">Expected Close Date</label>
                <input type="date" className="erp-input" value={formData.expected_close_date ?? ""} onChange={e => setFormData({ ...formData, expected_close_date: e.target.value || undefined })} />
              </div>
              <div className="erp-form-group">
                <label className="erp-label">Probability %</label>
                <input type="number" min="0" max="100" className="erp-input" value={formData.probability_pct ?? ""} onChange={e => setFormData({ ...formData, probability_pct: e.target.value ? parseFloat(e.target.value) : undefined })} />
              </div>
              <div className="erp-form-group col-span-2">
                <label className="erp-label">Description</label>
                <textarea className="erp-textarea" value={formData.description ?? ""} onChange={e => setFormData({ ...formData, description: e.target.value || undefined })} />
              </div>
            </div>
            {formError && <p style={{ color: "var(--status-error)", fontSize: 13, marginBottom: 12 }}>{formError}</p>}
            <div className="flex gap-3">
              <button type="submit" className="btn-primary" disabled={saving}>{saving ? "Saving…" : "Create Deal"}</button>
              <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      {/* Filters */}
      <div className="filter-bar">
        <div className="filter-group">
          <span className="filter-label">Status</span>
          <div className="flex gap-1">
            {(["all", "open", "won", "lost"] as const).map((s) => (
              <button
                key={s}
                onClick={() => setStatusFilter(s)}
                style={{ padding: "4px 10px", borderRadius: 4, fontSize: 12, fontWeight: 600, border: "1.5px solid", cursor: "pointer", borderColor: statusFilter === s ? "var(--accent)" : "var(--border)", backgroundColor: statusFilter === s ? "var(--accent)" : "transparent", color: statusFilter === s ? "#fff" : "var(--text-secondary)" }}
              >
                {s === "all" ? "All" : STATUS_LABELS[s as DealStatus]}
              </button>
            ))}
          </div>
        </div>
        {stages.status === "ok" && stages.items.length > 0 && (
          <div className="filter-group">
            <span className="filter-label">Stage</span>
            <select className="erp-select" style={{ width: "auto", fontSize: 12 }} value={stageFilter} onChange={e => setStageFilter(e.target.value)}>
              <option value="">All stages</option>
              {stages.items.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </div>
        )}
        <div className="filter-group" style={{ flex: 1 }}>
          <span className="filter-label">Search</span>
          <input className="erp-input" style={{ maxWidth: 240 }} placeholder="Deal title…" value={q} onChange={e => setQ(e.target.value)} />
        </div>
      </div>

      {/* Table */}
      <div className="rounded border overflow-hidden" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        {deals.status === "loading" && <p className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>Loading deals…</p>}
        {deals.status === "error" && (
          <div className="m-4 rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error-text)" }}>
            Failed to load deals: {deals.message}
          </div>
        )}
        {deals.status === "ok" && deals.items.length === 0 && (
          <div className="p-8 text-center" style={{ color: "var(--text-muted)", fontSize: 13 }}>No deals match the current filters.</div>
        )}
        {deals.status === "ok" && deals.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead style={{ backgroundColor: "var(--bg-table-header)", borderBottom: "1px solid var(--border)" }}>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Title</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Contact</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Organization</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Stage</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Value</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Close Date</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {deals.items.map((deal) => (
                  <tr key={deal.id} onMouseEnter={e => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-table-hover)"; }} onMouseLeave={e => { (e.currentTarget as HTMLElement).style.backgroundColor = "transparent"; }}>
                    <td className="px-4 py-2.5 font-medium" style={{ color: "var(--text-primary)" }}>{deal.title}</td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)", fontSize: 13 }}>
                      {deal.contact_id ? (
                        <Link href={`/contacts/${deal.contact_id}`} className="hover:underline" style={{ color: "var(--text-secondary)" }}>
                          {deal.contact_name ?? "View"}
                        </Link>
                      ) : "—"}
                    </td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)", fontSize: 13 }}>{deal.organization_name ?? "—"}</td>
                    <td className="px-4 py-2.5">
                      {deal.stage_name ? (
                        <span style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 12 }}>
                          {deal.stage_color && <span style={{ width: 8, height: 8, borderRadius: "50%", backgroundColor: deal.stage_color, display: "inline-block" }} />}
                          {deal.stage_name}
                        </span>
                      ) : <span style={{ color: "var(--text-muted)", fontSize: 12 }}>No stage</span>}
                    </td>
                    <td className="px-4 py-2.5 font-mono text-sm" style={{ color: "var(--text-primary)" }}>
                      {deal.value !== null ? `${deal.currency} ${deal.value.toLocaleString()}` : "—"}
                    </td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)", fontSize: 12 }}>
                      {deal.expected_close_date ? new Date(deal.expected_close_date).toLocaleDateString() : "—"}
                    </td>
                    <td className="px-4 py-2.5">
                      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[deal.status]}`}>
                        {STATUS_LABELS[deal.status]}
                      </span>
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
