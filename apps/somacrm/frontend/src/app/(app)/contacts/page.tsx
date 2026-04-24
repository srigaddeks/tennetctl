"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listContacts, createContact } from "@/lib/api";
import type { Contact, ContactStatus, ContactCreate } from "@/types/api";

type ContactsState =
  | { status: "loading" }
  | { status: "ok"; items: Contact[] }
  | { status: "error"; message: string };

type StatusFilter = ContactStatus | "all";

const STATUS_LABELS: Record<ContactStatus, string> = {
  active: "Active",
  inactive: "Inactive",
  archived: "Archived",
};

const STATUS_STYLES: Record<ContactStatus, string> = {
  active: "bg-green-100 text-green-800",
  inactive: "bg-slate-100 text-slate-700",
  archived: "bg-red-100 text-red-800",
};

export default function ContactsPage() {
  const [contacts, setContacts] = useState<ContactsState>({ status: "loading" });
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [q, setQ] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<ContactCreate>({ first_name: "" });
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  function reload() {
    setContacts({ status: "loading" });
    listContacts({ status: statusFilter === "all" ? undefined : statusFilter, q: q || undefined })
      .then((items) => setContacts({ status: "ok", items }))
      .catch((err: unknown) => setContacts({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }));
  }

  useEffect(() => {
    let cancelled = false;
    setContacts({ status: "loading" });
    listContacts({ status: statusFilter === "all" ? undefined : statusFilter, q: q || undefined })
      .then((items) => { if (!cancelled) setContacts({ status: "ok", items }); })
      .catch((err: unknown) => {
        if (!cancelled) setContacts({ status: "error", message: err instanceof Error ? err.message : "Unknown error" });
      });
    return () => { cancelled = true; };
  }, [statusFilter, q]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setFormError(null);
    try {
      await createContact(formData);
      setShowForm(false);
      setFormData({ first_name: "" });
      reload();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to create contact");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="max-w-5xl">
      <div className="page-header">
        <div>
          <h1 className="page-title">Contacts</h1>
          <p className="page-subtitle">People in your network</p>
        </div>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Cancel" : "+ New Contact"}
        </button>
      </div>

      {showForm && (
        <div className="mb-6 rounded border p-5" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
          <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16, color: "var(--text-primary)" }}>New Contact</h3>
          <form onSubmit={handleCreate}>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="erp-form-group">
                <label className="erp-label">First Name *</label>
                <input className="erp-input" value={formData.first_name} onChange={e => setFormData({ ...formData, first_name: e.target.value })} required />
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
                <label className="erp-label">Job Title</label>
                <input className="erp-input" value={formData.job_title ?? ""} onChange={e => setFormData({ ...formData, job_title: e.target.value || undefined })} />
              </div>
              <div className="erp-form-group">
                <label className="erp-label">Company</label>
                <input className="erp-input" value={formData.company_name ?? ""} onChange={e => setFormData({ ...formData, company_name: e.target.value || undefined })} />
              </div>
            </div>
            {formError && <p style={{ color: "var(--status-error)", fontSize: 13, marginBottom: 12 }}>{formError}</p>}
            <div className="flex gap-3">
              <button type="submit" className="btn-primary" disabled={saving}>{saving ? "Saving…" : "Create Contact"}</button>
              <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      {/* Filter bar */}
      <div className="filter-bar">
        <div className="filter-group">
          <span className="filter-label">Status</span>
          <div className="flex gap-1">
            {(["all", "active", "inactive", "archived"] as const).map((s) => (
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
                {s === "all" ? "All" : STATUS_LABELS[s as ContactStatus]}
              </button>
            ))}
          </div>
        </div>
        <div className="filter-group" style={{ flex: 1 }}>
          <span className="filter-label">Search</span>
          <input
            className="erp-input"
            style={{ maxWidth: 280 }}
            placeholder="Name, email, phone…"
            value={q}
            onChange={e => setQ(e.target.value)}
          />
        </div>
      </div>

      {/* Table */}
      <div className="rounded border overflow-hidden" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        {contacts.status === "loading" && (
          <p className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>Loading contacts…</p>
        )}
        {contacts.status === "error" && (
          <div className="m-4 rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error-text)" }}>
            Failed to load contacts: {contacts.message}
          </div>
        )}
        {contacts.status === "ok" && contacts.items.length === 0 && (
          <div className="p-8 text-center" style={{ color: "var(--text-muted)", fontSize: 13 }}>
            No contacts match the current filters.
          </div>
        )}
        {contacts.status === "ok" && contacts.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead style={{ backgroundColor: "var(--bg-table-header)", borderBottom: "1px solid var(--border)" }}>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Name</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Email</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Phone</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Organization</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Status</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Deals</th>
                </tr>
              </thead>
              <tbody>
                {contacts.items.map((c) => (
                  <tr key={c.id} onMouseEnter={e => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-table-hover)"; }} onMouseLeave={e => { (e.currentTarget as HTMLElement).style.backgroundColor = "transparent"; }}>
                    <td className="px-4 py-2.5 font-medium">
                      <Link href={`/contacts/${c.id}`} className="hover:underline" style={{ color: "var(--text-primary)" }}>
                        {c.full_name}
                      </Link>
                      {c.job_title && <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{c.job_title}</div>}
                    </td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)", fontSize: 13 }}>{c.email ?? "—"}</td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)", fontSize: 13 }}>{c.phone ?? "—"}</td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)", fontSize: 13 }}>{c.organization_name ?? "—"}</td>
                    <td className="px-4 py-2.5">
                      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[c.status]}`}>
                        {STATUS_LABELS[c.status]}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-center font-mono text-sm" style={{ color: "var(--text-secondary)" }}>{c.deals_count}</td>
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
