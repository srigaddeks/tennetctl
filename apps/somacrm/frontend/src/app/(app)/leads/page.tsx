"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listLeads, createLead } from "@/lib/api";
import type { Lead, LeadStatus, LeadCreate } from "@/types/api";

type LeadsState =
  | { status: "loading" }
  | { status: "ok"; items: Lead[] }
  | { status: "error"; message: string };

type StatusFilter = LeadStatus | "all";

const STATUS_LABELS: Record<LeadStatus, string> = {
  new: "New",
  contacted: "Contacted",
  qualified: "Qualified",
  unqualified: "Unqualified",
  converted: "Converted",
};

const STATUS_STYLES: Record<LeadStatus, string> = {
  new: "bg-blue-100 text-blue-800",
  contacted: "bg-yellow-100 text-yellow-800",
  qualified: "bg-green-100 text-green-800",
  unqualified: "bg-red-100 text-red-800",
  converted: "bg-purple-100 text-purple-800",
};

function ScoreBar({ score }: { score: number }) {
  const color = score >= 70 ? "#059669" : score >= 40 ? "#D97706" : "#DC2626";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <div style={{ flex: 1, height: 6, backgroundColor: "#E2E8F0", borderRadius: 3, overflow: "hidden" }}>
        <div style={{ width: `${score}%`, height: "100%", backgroundColor: color, borderRadius: 3 }} />
      </div>
      <span style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--text-secondary)", minWidth: 24 }}>{score}</span>
    </div>
  );
}

export default function LeadsPage() {
  const [leads, setLeads] = useState<LeadsState>({ status: "loading" });
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<LeadCreate>({ title: "" });
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  function reload() {
    listLeads({ status: statusFilter === "all" ? undefined : statusFilter })
      .then((items) => setLeads({ status: "ok", items }))
      .catch((err: unknown) => setLeads({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }));
  }

  useEffect(() => {
    let cancelled = false;
    setLeads({ status: "loading" });
    listLeads({ status: statusFilter === "all" ? undefined : statusFilter })
      .then((items) => { if (!cancelled) setLeads({ status: "ok", items }); })
      .catch((err: unknown) => { if (!cancelled) setLeads({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }); });
    return () => { cancelled = true; };
  }, [statusFilter]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setFormError(null);
    try {
      await createLead(formData);
      setShowForm(false);
      setFormData({ title: "" });
      reload();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to create lead");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="max-w-5xl">
      <div className="page-header">
        <div>
          <h1 className="page-title">Leads</h1>
          <p className="page-subtitle">Potential customers and opportunities</p>
        </div>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Cancel" : "+ New Lead"}
        </button>
      </div>

      {showForm && (
        <div className="mb-6 rounded border p-5" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
          <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16, color: "var(--text-primary)" }}>New Lead</h3>
          <form onSubmit={handleCreate}>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="erp-form-group">
                <label className="erp-label">Title *</label>
                <input className="erp-input" required value={formData.title} onChange={e => setFormData({ ...formData, title: e.target.value })} placeholder="Lead title or description" />
              </div>
              <div className="erp-form-group">
                <label className="erp-label">First Name</label>
                <input className="erp-input" value={formData.first_name ?? ""} onChange={e => setFormData({ ...formData, first_name: e.target.value || undefined })} />
              </div>
              <div className="erp-form-group">
                <label className="erp-label">Last Name</label>
                <input className="erp-input" value={formData.last_name ?? ""} onChange={e => setFormData({ ...formData, last_name: e.target.value || undefined })} />
              </div>
              <div className="erp-form-group">
                <label className="erp-label">Email</label>
                <input type="email" className="erp-input" value={formData.email ?? ""} onChange={e => setFormData({ ...formData, email: e.target.value || undefined })} />
              </div>
              <div className="erp-form-group">
                <label className="erp-label">Phone</label>
                <input className="erp-input" value={formData.phone ?? ""} onChange={e => setFormData({ ...formData, phone: e.target.value || undefined })} />
              </div>
              <div className="erp-form-group">
                <label className="erp-label">Company</label>
                <input className="erp-input" value={formData.company ?? ""} onChange={e => setFormData({ ...formData, company: e.target.value || undefined })} />
              </div>
              <div className="erp-form-group">
                <label className="erp-label">Lead Source</label>
                <input className="erp-input" value={formData.lead_source ?? ""} onChange={e => setFormData({ ...formData, lead_source: e.target.value || undefined })} placeholder="e.g. Website, Referral" />
              </div>
            </div>
            {formError && <p style={{ color: "var(--status-error)", fontSize: 13, marginBottom: 12 }}>{formError}</p>}
            <div className="flex gap-3">
              <button type="submit" className="btn-primary" disabled={saving}>{saving ? "Saving…" : "Create Lead"}</button>
              <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      {/* Status filter pills */}
      <div className="filter-bar">
        <div className="filter-group">
          <span className="filter-label">Status</span>
          <div className="flex gap-1 flex-wrap">
            {(["all", "new", "contacted", "qualified", "unqualified", "converted"] as const).map((s) => (
              <button
                key={s}
                onClick={() => setStatusFilter(s)}
                style={{
                  padding: "4px 10px",
                  borderRadius: 4,
                  fontSize: 12,
                  fontWeight: 600,
                  border: "1.5px solid",
                  cursor: "pointer",
                  borderColor: statusFilter === s ? "var(--accent)" : "var(--border)",
                  backgroundColor: statusFilter === s ? "var(--accent)" : "transparent",
                  color: statusFilter === s ? "#fff" : "var(--text-secondary)",
                }}
              >
                {s === "all" ? "All" : STATUS_LABELS[s as LeadStatus]}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="rounded border overflow-hidden" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        {leads.status === "loading" && <p className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>Loading leads…</p>}
        {leads.status === "error" && (
          <div className="m-4 rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error-text)" }}>
            Failed to load leads: {leads.message}
          </div>
        )}
        {leads.status === "ok" && leads.items.length === 0 && (
          <div className="p-8 text-center" style={{ color: "var(--text-muted)", fontSize: 13 }}>No leads match the current filter.</div>
        )}
        {leads.status === "ok" && leads.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead style={{ backgroundColor: "var(--bg-table-header)", borderBottom: "1px solid var(--border)" }}>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Title</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Name / Company</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Email</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Source</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Status</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Score</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Created</th>
                </tr>
              </thead>
              <tbody>
                {leads.items.map((lead) => (
                  <tr key={lead.id} onMouseEnter={e => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-table-hover)"; }} onMouseLeave={e => { (e.currentTarget as HTMLElement).style.backgroundColor = "transparent"; }}>
                    <td className="px-4 py-2.5 font-medium" style={{ color: "var(--text-primary)", maxWidth: 200 }}>
                      <Link href={`/leads/${lead.id}`} className="hover:underline" style={{ color: "var(--text-primary)" }}>{lead.title}</Link>
                    </td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)", fontSize: 13 }}>
                      {lead.full_name ?? "—"}
                      {lead.company && <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{lead.company}</div>}
                    </td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)", fontSize: 13 }}>{lead.email ?? "—"}</td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)", fontSize: 13 }}>{lead.lead_source ?? "—"}</td>
                    <td className="px-4 py-2.5">
                      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[lead.status]}`}>
                        {STATUS_LABELS[lead.status]}
                      </span>
                    </td>
                    <td className="px-4 py-2.5" style={{ minWidth: 100 }}>
                      <ScoreBar score={lead.score} />
                    </td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-muted)", fontSize: 12 }}>{new Date(lead.created_at).toLocaleDateString()}</td>
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
