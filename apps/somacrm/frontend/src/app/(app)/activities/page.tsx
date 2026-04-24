"use client";

import { useEffect, useState } from "react";
import { listActivities, createActivity, updateActivity } from "@/lib/api";
import type { Activity, ActivityStatus, ActivityCreate } from "@/types/api";

type ActivitiesState =
  | { status: "loading" }
  | { status: "ok"; items: Activity[] }
  | { status: "error"; message: string };

type TypeFilter = "all" | "task" | "call" | "email" | "meeting" | "note";
type StatusFilter = ActivityStatus | "all";

const STATUS_LABELS: Record<ActivityStatus, string> = {
  pending: "Pending",
  in_progress: "In Progress",
  done: "Done",
  cancelled: "Cancelled",
};

const STATUS_STYLES: Record<ActivityStatus, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  in_progress: "bg-blue-100 text-blue-800",
  done: "bg-green-100 text-green-800",
  cancelled: "bg-red-100 text-red-800",
};

const TYPE_IDS: Record<string, number> = {
  task: 1, call: 2, email: 3, meeting: 4, note: 5,
};

export default function ActivitiesPage() {
  const [activities, setActivities] = useState<ActivitiesState>({ status: "loading" });
  const [typeFilter, setTypeFilter] = useState<TypeFilter>("all");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<ActivityCreate>({ activity_type_id: 1, title: "" });
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  function reload() {
    listActivities({
      activity_type: typeFilter === "all" ? undefined : typeFilter,
      status: statusFilter === "all" ? undefined : statusFilter,
    })
      .then((items) => setActivities({ status: "ok", items }))
      .catch((err: unknown) => setActivities({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }));
  }

  useEffect(() => {
    let cancelled = false;
    setActivities({ status: "loading" });
    listActivities({
      activity_type: typeFilter === "all" ? undefined : typeFilter,
      status: statusFilter === "all" ? undefined : statusFilter,
    })
      .then((items) => { if (!cancelled) setActivities({ status: "ok", items }); })
      .catch((err: unknown) => { if (!cancelled) setActivities({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }); });
    return () => { cancelled = true; };
  }, [typeFilter, statusFilter]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setFormError(null);
    try {
      await createActivity(formData);
      setShowForm(false);
      setFormData({ activity_type_id: 1, title: "" });
      reload();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to create activity");
    } finally {
      setSaving(false);
    }
  }

  async function handleMarkDone(id: string) {
    try {
      await updateActivity(id, { status_id: 3, completed_at: new Date().toISOString() });
      reload();
    } catch {
      // ignore
    }
  }

  return (
    <div className="max-w-5xl">
      <div className="page-header">
        <div>
          <h1 className="page-title">Activities</h1>
          <p className="page-subtitle">Tasks, calls, emails, and meetings</p>
        </div>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Cancel" : "+ New Activity"}
        </button>
      </div>

      {showForm && (
        <div className="mb-6 rounded border p-5" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
          <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16, color: "var(--text-primary)" }}>New Activity</h3>
          <form onSubmit={handleCreate}>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="erp-form-group">
                <label className="erp-label">Title *</label>
                <input className="erp-input" required value={formData.title} onChange={e => setFormData({ ...formData, title: e.target.value })} />
              </div>
              <div className="erp-form-group">
                <label className="erp-label">Type</label>
                <select className="erp-select" value={formData.activity_type_id} onChange={e => setFormData({ ...formData, activity_type_id: parseInt(e.target.value) })}>
                  <option value="1">Task</option>
                  <option value="2">Call</option>
                  <option value="3">Email</option>
                  <option value="4">Meeting</option>
                  <option value="5">Note</option>
                  <option value="6">WhatsApp</option>
                </select>
              </div>
              <div className="erp-form-group">
                <label className="erp-label">Due Date</label>
                <input type="datetime-local" className="erp-input" onChange={e => setFormData({ ...formData, due_at: e.target.value || undefined })} />
              </div>
              <div className="erp-form-group">
                <label className="erp-label">Duration (minutes)</label>
                <input type="number" className="erp-input" onChange={e => setFormData({ ...formData, duration_minutes: e.target.value ? parseInt(e.target.value) : undefined })} />
              </div>
              <div className="erp-form-group col-span-2">
                <label className="erp-label">Description</label>
                <textarea className="erp-textarea" onChange={e => setFormData({ ...formData, description: e.target.value || undefined })} />
              </div>
            </div>
            {formError && <p style={{ color: "var(--status-error)", fontSize: 13, marginBottom: 12 }}>{formError}</p>}
            <div className="flex gap-3">
              <button type="submit" className="btn-primary" disabled={saving}>{saving ? "Saving…" : "Create Activity"}</button>
              <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      {/* Filters */}
      <div className="filter-bar">
        <div className="filter-group">
          <span className="filter-label">Type</span>
          <div className="flex gap-1 flex-wrap">
            {(["all", "task", "call", "email", "meeting", "note"] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTypeFilter(t)}
                style={{ padding: "4px 10px", borderRadius: 4, fontSize: 12, fontWeight: 600, border: "1.5px solid", cursor: "pointer", borderColor: typeFilter === t ? "var(--accent)" : "var(--border)", backgroundColor: typeFilter === t ? "var(--accent)" : "transparent", color: typeFilter === t ? "#fff" : "var(--text-secondary)", textTransform: "capitalize" }}
              >
                {t === "all" ? "All" : t}
              </button>
            ))}
          </div>
        </div>
        <div className="filter-group">
          <span className="filter-label">Status</span>
          <div className="flex gap-1 flex-wrap">
            {(["all", "pending", "done"] as const).map((s) => (
              <button
                key={s}
                onClick={() => setStatusFilter(s as StatusFilter)}
                style={{ padding: "4px 10px", borderRadius: 4, fontSize: 12, fontWeight: 600, border: "1.5px solid", cursor: "pointer", borderColor: statusFilter === s ? "var(--accent)" : "var(--border)", backgroundColor: statusFilter === s ? "var(--accent)" : "transparent", color: statusFilter === s ? "#fff" : "var(--text-secondary)" }}
              >
                {s === "all" ? "All" : s.charAt(0).toUpperCase() + s.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="rounded border overflow-hidden" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
        {activities.status === "loading" && <p className="p-6 text-sm" style={{ color: "var(--text-muted)" }}>Loading activities…</p>}
        {activities.status === "error" && (
          <div className="m-4 rounded border p-4 text-sm" style={{ borderColor: "var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error-text)" }}>
            Failed to load activities: {activities.message}
          </div>
        )}
        {activities.status === "ok" && activities.items.length === 0 && (
          <div className="p-8 text-center" style={{ color: "var(--text-muted)", fontSize: 13 }}>No activities match the current filters.</div>
        )}
        {activities.status === "ok" && activities.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead style={{ backgroundColor: "var(--bg-table-header)", borderBottom: "1px solid var(--border)" }}>
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Type</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Title</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Due Date</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Status</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Linked To</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {activities.items.map((act) => (
                  <tr key={act.id} onMouseEnter={e => { (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-table-hover)"; }} onMouseLeave={e => { (e.currentTarget as HTMLElement).style.backgroundColor = "transparent"; }}>
                    <td className="px-4 py-2.5">
                      <span style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 13 }}>
                        <span>{act.activity_type_icon}</span>
                        <span style={{ color: "var(--text-secondary)" }}>{act.activity_type_label}</span>
                      </span>
                    </td>
                    <td className="px-4 py-2.5 font-medium" style={{ color: "var(--text-primary)" }}>
                      {act.title}
                      {act.description && <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 1 }}>{act.description.slice(0, 60)}{act.description.length > 60 ? "…" : ""}</div>}
                    </td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-secondary)", fontSize: 12 }}>
                      {act.due_at ? new Date(act.due_at).toLocaleDateString() : "—"}
                    </td>
                    <td className="px-4 py-2.5">
                      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[act.status]}`}>
                        {STATUS_LABELS[act.status]}
                      </span>
                    </td>
                    <td className="px-4 py-2.5" style={{ color: "var(--text-muted)", fontSize: 12 }}>
                      {act.entity_type && act.entity_id ? (
                        <span style={{ textTransform: "capitalize" }}>{act.entity_type}</span>
                      ) : "—"}
                    </td>
                    <td className="px-4 py-2.5">
                      {act.status !== "done" && act.status !== "cancelled" && (
                        <button
                          onClick={() => handleMarkDone(act.id)}
                          style={{ fontSize: 12, color: "#059669", background: "none", border: "1px solid #059669", borderRadius: 4, padding: "2px 8px", cursor: "pointer" }}
                        >
                          Mark done
                        </button>
                      )}
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
