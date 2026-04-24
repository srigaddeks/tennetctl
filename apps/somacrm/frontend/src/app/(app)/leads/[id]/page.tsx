"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  getLead, updateLead,
  listActivities, listNotes,
  createActivity, createNote, updateNote,
  createContact,
} from "@/lib/api";
import type {
  Lead, LeadUpdate,
  Activity,
  Note,
  ActivityCreate, NoteCreate,
} from "@/types/api";

type Tab = "activities" | "notes" | "details";

type State<T> =
  | { status: "loading" }
  | { status: "ok"; data: T }
  | { status: "error"; message: string };

const ACTIVITY_TYPE_CONFIG: Record<string, { icon: string; color: string; bg: string }> = {
  whatsapp: { icon: "💬", color: "#16A34A", bg: "#F0FDF4" },
  call:     { icon: "📞", color: "#2563EB", bg: "#EFF6FF" },
  email:    { icon: "✉",  color: "#7C3AED", bg: "#F5F3FF" },
  meeting:  { icon: "📅", color: "#D97706", bg: "#FFFBEB" },
  task:     { icon: "✓",  color: "#6B7280", bg: "#F9FAFB" },
  note:     { icon: "📝", color: "#B45309", bg: "#FFFBEB" },
};

function activityConfig(type: string) {
  return ACTIVITY_TYPE_CONFIG[type] ?? ACTIVITY_TYPE_CONFIG.task;
}

const LEAD_STATUS_LABELS: Record<string, string> = {
  new:         "New",
  contacted:   "Contacted",
  qualified:   "Qualified",
  unqualified: "Unqualified",
  converted:   "Converted",
};

const LEAD_STATUS_COLORS: Record<string, { bg: string; color: string }> = {
  new:         { bg: "#F9FAFB", color: "#6B7280" },
  contacted:   { bg: "#EFF6FF", color: "#2563EB" },
  qualified:   { bg: "#ECFDF5", color: "#059669" },
  unqualified: { bg: "#FEF2F2", color: "#DC2626" },
  converted:   { bg: "#F5F3FF", color: "#7C3AED" },
};

function ScoreBar({ score }: { score: number }) {
  const color = score >= 70 ? "#059669" : score >= 40 ? "#D97706" : "#DC2626";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <div style={{ width: 120, height: 8, backgroundColor: "#E2E8F0", borderRadius: 4, overflow: "hidden" }}>
        <div style={{ width: `${score}%`, height: "100%", backgroundColor: color, borderRadius: 4 }} />
      </div>
      <span style={{ fontSize: 12, fontFamily: "monospace", color: "var(--text-secondary)", minWidth: 28 }}>{score}</span>
    </div>
  );
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffDays = Math.floor(diffMs / 86400000);
  if (diffDays === 0) return `Today ${d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
  if (diffDays === 1) return `Yesterday ${d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return d.toLocaleDateString([], { day: "numeric", month: "short", year: diffDays > 365 ? "numeric" : undefined });
}

export default function LeadDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [tab, setTab] = useState<Tab>("activities");
  const [lead, setLead] = useState<State<Lead>>({ status: "loading" });
  const [activities, setActivities] = useState<State<Activity[]>>({ status: "loading" });
  const [notes, setNotes] = useState<State<Note[]>>({ status: "loading" });
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState<LeadUpdate>({});
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Quick-add state
  const [showActivityForm, setShowActivityForm] = useState(false);
  const [showNoteForm, setShowNoteForm] = useState(false);
  const [activityForm, setActivityForm] = useState<ActivityCreate>({ activity_type_id: 2, title: "" });
  const [noteForm, setNoteForm] = useState<NoteCreate>({ entity_type: "lead", entity_id: id, content: "" });

  // Convert to contact panel
  const [showConvertPanel, setShowConvertPanel] = useState(false);
  const [convertForm, setConvertForm] = useState({ first_name: "", last_name: "", email: "", phone: "" });
  const [convertSuccess, setConvertSuccess] = useState<string | null>(null);
  const [converting, setConverting] = useState(false);
  const [convertError, setConvertError] = useState<string | null>(null);

  useEffect(() => {
    getLead(id)
      .then((data) => {
        setLead({ status: "ok", data });
        // Pre-fill convert form from lead data
        setConvertForm({
          first_name: data.full_name?.split(" ")[0] ?? "",
          last_name: data.full_name?.split(" ").slice(1).join(" ") ?? "",
          email: data.email ?? "",
          phone: data.phone ?? "",
        });
      })
      .catch((err: unknown) => setLead({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }));
  }, [id]);

  function refreshActivities() {
    listActivities({ entity_type: "lead", entity_id: id })
      .then((data) => setActivities({ status: "ok", data }))
      .catch((err: unknown) => setActivities({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }));
  }

  function refreshNotes() {
    listNotes({ entity_type: "lead", entity_id: id })
      .then((data) => setNotes({ status: "ok", data }))
      .catch((err: unknown) => setNotes({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }));
  }

  useEffect(() => {
    if (tab === "activities") refreshActivities();
    if (tab === "notes") refreshNotes();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, id]);

  async function handleStatusChange(statusId: string) {
    if (lead.status !== "ok") return;
    try {
      const updated = await updateLead(id, { status_id: parseInt(statusId) });
      setLead({ status: "ok", data: updated });
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to update status");
    }
  }

  async function handleConvert(e: React.FormEvent) {
    e.preventDefault();
    setConverting(true);
    setConvertError(null);
    try {
      const newContact = await createContact({
        first_name: convertForm.first_name,
        last_name: convertForm.last_name || undefined,
        email: convertForm.email || undefined,
        phone: convertForm.phone || undefined,
        lead_source: lead.status === "ok" ? (lead.data.lead_source ?? undefined) : undefined,
      });
      await updateLead(id, { status_id: 5, contact_id: newContact.id });
      // Refresh lead
      const updatedLead = await getLead(id);
      setLead({ status: "ok", data: updatedLead });
      setShowConvertPanel(false);
      setConvertSuccess(`Contact created — view in Contacts`);
    } catch (err: unknown) {
      setConvertError(err instanceof Error ? err.message : "Conversion failed");
    } finally { setConverting(false); }
  }

  async function handleSaveLead(e: React.FormEvent) {
    e.preventDefault();
    if (lead.status !== "ok") return;
    setSaving(true);
    setFormError(null);
    try {
      const updated = await updateLead(id, editData);
      setLead({ status: "ok", data: updated });
      setEditing(false);
      setEditData({});
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to update");
    } finally { setSaving(false); }
  }

  async function handleAddActivity(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setFormError(null);
    try {
      await createActivity({ ...activityForm, entity_type: "lead", entity_id: id });
      setShowActivityForm(false);
      setActivityForm({ activity_type_id: 2, title: "" });
      refreshActivities();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to log activity");
    } finally { setSaving(false); }
  }

  async function handleAddNote(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setFormError(null);
    try {
      await createNote({ ...noteForm, entity_type: "lead", entity_id: id });
      setShowNoteForm(false);
      setNoteForm({ entity_type: "lead", entity_id: id, content: "" });
      refreshNotes();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to add note");
    } finally { setSaving(false); }
  }

  async function handlePinToggle(note: Note) {
    await updateNote(note.id, { is_pinned: !note.is_pinned });
    refreshNotes();
  }

  if (lead.status === "loading") return <div style={{ padding: 32, color: "var(--text-muted)" }}>Loading…</div>;
  if (lead.status === "error") return <div style={{ padding: 32, color: "var(--status-error)" }}>{lead.message}</div>;

  const l = lead.data;
  const sc = LEAD_STATUS_COLORS[l.status] ?? LEAD_STATUS_COLORS.new;
  const isConverted = l.status === "converted";

  return (
    <div className="max-w-4xl">
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
        <div>
          <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 4 }}>
            <Link href="/leads" style={{ color: "var(--text-muted)", textDecoration: "none" }}>Leads</Link>
            {" / "}
            <span>{l.title}</span>
          </div>
          <h1 className="page-title">{l.title}</h1>
          {(l.full_name || l.company) && (
            <p className="page-subtitle">
              {[l.full_name, l.company].filter(Boolean).join(" · ")}
            </p>
          )}
          {/* Pills row */}
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 8, alignItems: "center" }}>
            <span style={{ fontSize: 12, fontWeight: 600, borderRadius: 20, padding: "2px 10px", background: sc.bg, color: sc.color }}>
              {LEAD_STATUS_LABELS[l.status] ?? l.status}
            </span>
            <ScoreBar score={l.score} />
            {l.lead_source && (
              <span style={{ fontSize: 12, background: "#F9FAFB", color: "var(--text-secondary)", borderRadius: 20, padding: "2px 10px" }}>
                via {l.lead_source.replace(/_/g, " ")}
              </span>
            )}
          </div>
        </div>

        {/* Action buttons */}
        <div style={{ display: "flex", gap: 8, flexShrink: 0, flexWrap: "wrap", justifyContent: "flex-end" }}>
          <select
            className="erp-select"
            style={{ fontSize: 12, padding: "6px 10px", width: "auto" }}
            value=""
            onChange={e => { if (e.target.value) handleStatusChange(e.target.value); }}
          >
            <option value="">Update Status ▾</option>
            <option value="1">New</option>
            <option value="2">Contacted</option>
            <option value="3">Qualified</option>
            <option value="4">Unqualified</option>
            <option value="5">Converted</option>
          </select>
          {!isConverted && (
            <button
              className="btn-primary"
              style={{ fontSize: 12, padding: "6px 14px" }}
              onClick={() => setShowConvertPanel(!showConvertPanel)}
            >
              Convert to Contact
            </button>
          )}
        </div>
      </div>

      {/* Convert to Contact panel */}
      {showConvertPanel && !isConverted && (
        <div className="rounded border p-5 mb-6"
          style={{ backgroundColor: "#F0FDF4", borderColor: "#86EFAC", borderLeft: "3px solid #059669" }}>
          <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 12, color: "#065F46" }}>Create a contact from this lead?</div>
          <form onSubmit={handleConvert}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
              <div className="erp-form-group">
                <label className="erp-label">First Name *</label>
                <input className="erp-input" required value={convertForm.first_name}
                  onChange={e => setConvertForm({ ...convertForm, first_name: e.target.value })} />
              </div>
              <div className="erp-form-group">
                <label className="erp-label">Last Name</label>
                <input className="erp-input" value={convertForm.last_name}
                  onChange={e => setConvertForm({ ...convertForm, last_name: e.target.value })} />
              </div>
              <div className="erp-form-group">
                <label className="erp-label">Email</label>
                <input type="email" className="erp-input" value={convertForm.email}
                  onChange={e => setConvertForm({ ...convertForm, email: e.target.value })} />
              </div>
              <div className="erp-form-group">
                <label className="erp-label">Phone</label>
                <input className="erp-input" value={convertForm.phone}
                  onChange={e => setConvertForm({ ...convertForm, phone: e.target.value })} />
              </div>
            </div>
            {convertError && <p style={{ color: "var(--status-error)", fontSize: 13, marginBottom: 8 }}>{convertError}</p>}
            <div style={{ display: "flex", gap: 8 }}>
              <button type="submit" className="btn-primary" disabled={converting}
                style={{ background: "#059669", borderColor: "#059669" }}>
                {converting ? "Converting…" : "Confirm — Create Contact"}
              </button>
              <button type="button" className="btn-secondary" onClick={() => setShowConvertPanel(false)}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      {/* Conversion success message */}
      {convertSuccess && (
        <div className="rounded border p-3 mb-4" style={{ backgroundColor: "#ECFDF5", borderColor: "#6EE7B7" }}>
          <span style={{ fontSize: 13, color: "#065F46", fontWeight: 600 }}>
            {convertSuccess} —{" "}
            {l.contact_id && (
              <Link href={`/contacts/${l.contact_id}`} style={{ color: "#059669", textDecoration: "underline" }}>
                View Contact
              </Link>
            )}
          </span>
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: "flex", gap: 0, borderBottom: "1px solid var(--border)", marginBottom: 24 }}>
        {([
          { key: "activities", label: "Activities" },
          { key: "notes",      label: "Notes" },
          { key: "details",    label: "Details" },
        ] as { key: Tab; label: string }[]).map(({ key, label }) => (
          <button
            key={key}
            onClick={() => { setTab(key); setFormError(null); setShowActivityForm(false); setShowNoteForm(false); }}
            style={{
              padding: "8px 18px",
              fontSize: 13,
              fontWeight: tab === key ? 700 : 500,
              border: "none",
              background: "none",
              cursor: "pointer",
              borderBottom: tab === key ? "2px solid var(--accent)" : "2px solid transparent",
              color: tab === key ? "var(--accent)" : "var(--text-secondary)",
            }}
          >
            {label}
            {key === "activities" && activities.status === "ok" && (
              <span style={{ marginLeft: 6, fontSize: 11, background: "var(--accent)", color: "#fff", borderRadius: 10, padding: "1px 6px" }}>
                {activities.data.length}
              </span>
            )}
            {key === "notes" && notes.status === "ok" && (
              <span style={{ marginLeft: 6, fontSize: 11, background: "var(--accent)", color: "#fff", borderRadius: 10, padding: "1px 6px" }}>
                {notes.data.length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* ── ACTIVITIES TAB ───────────────────────────────────────────────── */}
      {tab === "activities" && (
        <div>
          <div style={{ marginBottom: 16 }}>
            <button className="btn-primary" style={{ fontSize: 12, padding: "6px 12px" }} onClick={() => setShowActivityForm(!showActivityForm)}>
              {showActivityForm ? "Cancel" : "+ Log Activity"}
            </button>
          </div>

          {showActivityForm && (
            <form onSubmit={handleAddActivity} className="rounded border p-4 mb-6"
              style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)", borderLeft: "3px solid #2563EB" }}>
              <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 12, color: "var(--text-primary)" }}>Log Activity</div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
                <div className="erp-form-group">
                  <label className="erp-label">Type</label>
                  <select className="erp-select" value={activityForm.activity_type_id}
                    onChange={e => setActivityForm({ ...activityForm, activity_type_id: parseInt(e.target.value) })}>
                    <option value="6">💬 WhatsApp</option>
                    <option value="2">📞 Call</option>
                    <option value="3">✉ Email</option>
                    <option value="4">📅 Meeting</option>
                    <option value="1">✓ Task</option>
                    <option value="5">📝 Note</option>
                  </select>
                </div>
                <div className="erp-form-group">
                  <label className="erp-label">Title *</label>
                  <input className="erp-input" required placeholder="e.g. Discovery call"
                    value={activityForm.title}
                    onChange={e => setActivityForm({ ...activityForm, title: e.target.value })} />
                </div>
                <div className="erp-form-group">
                  <label className="erp-label">Date / Time</label>
                  <input type="datetime-local" className="erp-input"
                    onChange={e => setActivityForm({ ...activityForm, due_at: e.target.value || undefined })} />
                </div>
                <div className="erp-form-group">
                  <label className="erp-label">Duration (min)</label>
                  <input type="number" className="erp-input" placeholder="e.g. 30"
                    onChange={e => setActivityForm({ ...activityForm, duration_minutes: e.target.value ? parseInt(e.target.value) : undefined })} />
                </div>
                <div className="erp-form-group" style={{ gridColumn: "1 / -1" }}>
                  <label className="erp-label">Description</label>
                  <textarea className="erp-textarea" placeholder="What happened?"
                    onChange={e => setActivityForm({ ...activityForm, description: e.target.value || undefined })} />
                </div>
              </div>
              {formError && <p style={{ color: "var(--status-error)", fontSize: 13, marginBottom: 8 }}>{formError}</p>}
              <div style={{ display: "flex", gap: 8 }}>
                <button type="submit" className="btn-primary" disabled={saving}>{saving ? "Saving…" : "Log It"}</button>
                <button type="button" className="btn-secondary" onClick={() => setShowActivityForm(false)}>Cancel</button>
              </div>
            </form>
          )}

          {activities.status === "loading" && <p style={{ color: "var(--text-muted)", fontSize: 13 }}>Loading activities…</p>}
          {activities.status === "error" && <p style={{ color: "var(--status-error)", fontSize: 13 }}>{activities.message}</p>}
          {activities.status === "ok" && activities.data.length === 0 && (
            <div style={{ textAlign: "center", padding: "48px 0", color: "var(--text-muted)", fontSize: 13 }}>
              No activities logged yet. Log the first one above.
            </div>
          )}
          {activities.status === "ok" && activities.data.length > 0 && (
            <div style={{ position: "relative" }}>
              <div style={{ position: "absolute", left: 19, top: 0, bottom: 0, width: 2, backgroundColor: "var(--border)", zIndex: 0 }} />
              {activities.data.map((act) => {
                const cfg = activityConfig(act.activity_type);
                return (
                  <div key={act.id} style={{ display: "flex", gap: 14, marginBottom: 20, position: "relative", zIndex: 1 }}>
                    <div style={{
                      width: 38, height: 38, borderRadius: "50%", flexShrink: 0,
                      backgroundColor: cfg.bg, border: `2px solid ${cfg.color}`,
                      display: "flex", alignItems: "center", justifyContent: "center",
                      fontSize: 16, boxShadow: "0 0 0 3px var(--bg-main)",
                    }}>
                      {act.activity_type_icon ?? cfg.icon}
                    </div>
                    <div style={{
                      flex: 1,
                      backgroundColor: "var(--bg-card)",
                      border: `1px solid var(--border)`,
                      borderLeft: `3px solid ${cfg.color}`,
                      borderRadius: 8,
                      padding: "10px 14px",
                    }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 4 }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                          <span style={{ fontSize: 12, fontWeight: 700, color: cfg.color }}>
                            {act.activity_type_label ?? act.activity_type}
                          </span>
                          {act.status && act.status !== "done" && (
                            <span style={{
                              fontSize: 10, fontWeight: 600, borderRadius: 4, padding: "1px 6px",
                              background: act.status === "pending" ? "#FEF9C3" : "#EFF6FF",
                              color: act.status === "pending" ? "#B45309" : "#2563EB",
                              textTransform: "uppercase",
                            }}>{act.status}</span>
                          )}
                        </div>
                        <span style={{ fontSize: 11, color: "var(--text-muted)", whiteSpace: "nowrap" }}>
                          {formatDate(act.due_at ?? act.created_at)}
                        </span>
                      </div>
                      <div style={{ fontSize: 13.5, fontWeight: 600, color: "var(--text-primary)", marginBottom: act.description ? 4 : 0 }}>
                        {act.title}
                      </div>
                      {act.description && (
                        <div style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.5, whiteSpace: "pre-wrap" }}>
                          {act.description}
                        </div>
                      )}
                      {act.duration_minutes && (
                        <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4 }}>
                          ⏱ {act.duration_minutes} min
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ── NOTES TAB ───────────────────────────────────────────────────── */}
      {tab === "notes" && (
        <div>
          <div style={{ marginBottom: 16 }}>
            <button className="btn-primary" style={{ fontSize: 12, padding: "6px 12px" }} onClick={() => setShowNoteForm(!showNoteForm)}>
              {showNoteForm ? "Cancel" : "+ Add Note"}
            </button>
          </div>

          {showNoteForm && (
            <form onSubmit={handleAddNote} className="rounded border p-4 mb-6"
              style={{ backgroundColor: "#FFFBEB", borderColor: "#FDE68A", borderLeft: "3px solid #D97706" }}>
              <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 10, color: "var(--text-primary)" }}>Add Note</div>
              <textarea className="erp-textarea" required style={{ minHeight: 80 }}
                placeholder="Write a note about this lead…"
                value={noteForm.content}
                onChange={e => setNoteForm({ ...noteForm, content: e.target.value })} />
              {formError && <p style={{ color: "var(--status-error)", fontSize: 13, margin: "8px 0" }}>{formError}</p>}
              <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
                <button type="submit" className="btn-primary" disabled={saving}>{saving ? "Saving…" : "Save Note"}</button>
                <button type="button" className="btn-secondary" onClick={() => setShowNoteForm(false)}>Cancel</button>
              </div>
            </form>
          )}

          {notes.status === "loading" && <p style={{ color: "var(--text-muted)", fontSize: 13 }}>Loading notes…</p>}
          {notes.status === "error" && <p style={{ color: "var(--status-error)", fontSize: 13 }}>{notes.message}</p>}
          {notes.status === "ok" && notes.data.length === 0 && (
            <div style={{ textAlign: "center", padding: "48px 0", color: "var(--text-muted)", fontSize: 13 }}>
              No notes yet. Add the first one above.
            </div>
          )}
          {notes.status === "ok" && notes.data.length > 0 && (
            <div>
              {[...notes.data]
                .sort((a, b) => (b.is_pinned ? 1 : 0) - (a.is_pinned ? 1 : 0))
                .map((note) => (
                  <div key={note.id} className="rounded border p-4 mb-3"
                    style={{
                      backgroundColor: note.is_pinned ? "#FFFBEB" : "var(--bg-card)",
                      borderColor: note.is_pinned ? "#FDE68A" : "var(--border)",
                      borderLeft: "3px solid #D97706",
                    }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 6 }}>
                      <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                        <span style={{ fontSize: 12, fontWeight: 700, color: "#B45309" }}>Note</span>
                        {note.is_pinned && (
                          <span style={{ fontSize: 10, background: "#FEF3C7", color: "#B45309", borderRadius: 4, padding: "1px 6px", fontWeight: 700 }}>📌 PINNED</span>
                        )}
                      </div>
                      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                        <span style={{ fontSize: 11, color: "var(--text-muted)" }}>{formatDate(note.created_at)}</span>
                        <button
                          onClick={() => handlePinToggle(note)}
                          style={{ fontSize: 11, color: "var(--text-muted)", background: "none", border: "none", cursor: "pointer" }}>
                          {note.is_pinned ? "Unpin" : "Pin"}
                        </button>
                      </div>
                    </div>
                    <div style={{ fontSize: 13, color: "var(--text-primary)", lineHeight: 1.6, whiteSpace: "pre-wrap" }}>
                      {note.content}
                    </div>
                  </div>
                ))}
            </div>
          )}
        </div>
      )}

      {/* ── DETAILS TAB ─────────────────────────────────────────────────── */}
      {tab === "details" && (
        <div className="rounded border p-5" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
          {editing ? (
            <form onSubmit={handleSaveLead}>
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="erp-form-group">
                  <label className="erp-label">Title *</label>
                  <input className="erp-input" required defaultValue={l.title}
                    onChange={e => setEditData({ ...editData, title: e.target.value })} />
                </div>
                <div className="erp-form-group">
                  <label className="erp-label">First Name</label>
                  <input className="erp-input" defaultValue={l.full_name?.split(" ")[0] ?? ""}
                    onChange={e => setEditData({ ...editData, first_name: e.target.value || undefined })} />
                </div>
                <div className="erp-form-group">
                  <label className="erp-label">Last Name</label>
                  <input className="erp-input" defaultValue={l.full_name?.split(" ").slice(1).join(" ") ?? ""}
                    onChange={e => setEditData({ ...editData, last_name: e.target.value || undefined })} />
                </div>
                <div className="erp-form-group">
                  <label className="erp-label">Email</label>
                  <input type="email" className="erp-input" defaultValue={l.email ?? ""}
                    onChange={e => setEditData({ ...editData, email: e.target.value || undefined })} />
                </div>
                <div className="erp-form-group">
                  <label className="erp-label">Phone</label>
                  <input className="erp-input" defaultValue={l.phone ?? ""}
                    onChange={e => setEditData({ ...editData, phone: e.target.value || undefined })} />
                </div>
                <div className="erp-form-group">
                  <label className="erp-label">Company</label>
                  <input className="erp-input" defaultValue={l.company ?? ""}
                    onChange={e => setEditData({ ...editData, company: e.target.value || undefined })} />
                </div>
                <div className="erp-form-group">
                  <label className="erp-label">Lead Source</label>
                  <input className="erp-input" defaultValue={l.lead_source ?? ""}
                    onChange={e => setEditData({ ...editData, lead_source: e.target.value || undefined })} />
                </div>
                <div className="erp-form-group">
                  <label className="erp-label">Score (0–100)</label>
                  <input type="number" min="0" max="100" className="erp-input" defaultValue={l.score}
                    onChange={e => setEditData({ ...editData, score: e.target.value ? parseInt(e.target.value) : undefined })} />
                </div>
              </div>
              {formError && <p style={{ color: "var(--status-error)", fontSize: 13, marginBottom: 12 }}>{formError}</p>}
              <div className="flex gap-3">
                <button type="submit" className="btn-primary" disabled={saving}>{saving ? "Saving…" : "Save Changes"}</button>
                <button type="button" className="btn-secondary" onClick={() => { setEditing(false); setEditData({}); }}>Cancel</button>
              </div>
            </form>
          ) : (
            <>
              <div className="flex justify-end mb-4">
                <button className="btn-secondary" style={{ fontSize: 12 }} onClick={() => setEditing(true)}>Edit</button>
              </div>
              <dl className="grid grid-cols-2 gap-x-8 gap-y-4">
                {([
                  { label: "Title",       value: l.title },
                  { label: "Full Name",   value: l.full_name },
                  { label: "Email",       value: l.email },
                  { label: "Phone",       value: l.phone },
                  { label: "Company",     value: l.company },
                  { label: "Lead Source", value: l.lead_source },
                  { label: "Status",      value: LEAD_STATUS_LABELS[l.status] ?? l.status },
                  { label: "Score",       value: String(l.score) },
                  { label: "Contact",     value: l.contact_name, href: l.contact_id ? `/contacts/${l.contact_id}` : undefined },
                  { label: "Assigned To", value: l.assigned_to },
                ] as { label: string; value: string | null | undefined; href?: string }[]).map(({ label, value, href }) => value ? (
                  <div key={label}>
                    <dt style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)", marginBottom: 2 }}>{label}</dt>
                    <dd style={{ fontSize: 13.5, color: "var(--text-primary)" }}>
                      {href ? (
                        <Link href={href} style={{ color: "var(--accent)", textDecoration: "none" }} className="hover:underline">{value}</Link>
                      ) : value}
                    </dd>
                  </div>
                ) : null)}
              </dl>
            </>
          )}
        </div>
      )}
    </div>
  );
}
