"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  getDeal, updateDeal,
  listPipelineStages,
  listActivities, listNotes,
  createActivity, createNote, updateNote,
} from "@/lib/api";
import type {
  Deal, DealUpdate,
  PipelineStage,
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

export default function DealDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [tab, setTab] = useState<Tab>("activities");
  const [deal, setDeal] = useState<State<Deal>>({ status: "loading" });
  const [stages, setStages] = useState<State<PipelineStage[]>>({ status: "loading" });
  const [activities, setActivities] = useState<State<Activity[]>>({ status: "loading" });
  const [notes, setNotes] = useState<State<Note[]>>({ status: "loading" });
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState<DealUpdate>({});
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Quick-add state
  const [showActivityForm, setShowActivityForm] = useState(false);
  const [showNoteForm, setShowNoteForm] = useState(false);
  const [activityForm, setActivityForm] = useState<ActivityCreate>({ activity_type_id: 2, title: "" });
  const [noteForm, setNoteForm] = useState<NoteCreate>({ entity_type: "deal", entity_id: id, content: "" });

  useEffect(() => {
    getDeal(id)
      .then((data) => setDeal({ status: "ok", data }))
      .catch((err: unknown) => setDeal({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }));
    listPipelineStages()
      .then((data) => setStages({ status: "ok", data }))
      .catch(() => setStages({ status: "error", message: "Failed to load stages" }));
  }, [id]);

  function refreshActivities() {
    listActivities({ entity_type: "deal", entity_id: id })
      .then((data) => setActivities({ status: "ok", data }))
      .catch((err: unknown) => setActivities({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }));
  }

  function refreshNotes() {
    listNotes({ entity_type: "deal", entity_id: id })
      .then((data) => setNotes({ status: "ok", data }))
      .catch((err: unknown) => setNotes({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }));
  }

  useEffect(() => {
    if (tab === "activities") refreshActivities();
    if (tab === "notes") refreshNotes();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, id]);

  async function handleStageChange(stageId: string) {
    if (deal.status !== "ok") return;
    try {
      const updated = await updateDeal(id, { stage_id: stageId || undefined });
      setDeal({ status: "ok", data: updated });
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to update stage");
    }
  }

  async function handleMarkWon() {
    if (!window.confirm("Are you sure? This will mark the deal as Won.")) return;
    try {
      const today = new Date().toISOString().split("T")[0];
      const updated = await updateDeal(id, { status_id: 2, actual_close_date: today });
      setDeal({ status: "ok", data: updated });
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to mark as won");
    }
  }

  async function handleMarkLost() {
    if (!window.confirm("Are you sure? This will mark the deal as Lost.")) return;
    try {
      const updated = await updateDeal(id, { status_id: 3 });
      setDeal({ status: "ok", data: updated });
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to mark as lost");
    }
  }

  async function handleSaveDeal(e: React.FormEvent) {
    e.preventDefault();
    if (deal.status !== "ok") return;
    setSaving(true);
    setFormError(null);
    try {
      const updated = await updateDeal(id, editData);
      setDeal({ status: "ok", data: updated });
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
      await createActivity({ ...activityForm, entity_type: "deal", entity_id: id });
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
      await createNote({ ...noteForm, entity_type: "deal", entity_id: id });
      setShowNoteForm(false);
      setNoteForm({ entity_type: "deal", entity_id: id, content: "" });
      refreshNotes();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : "Failed to add note");
    } finally { setSaving(false); }
  }

  async function handlePinToggle(note: Note) {
    await updateNote(note.id, { is_pinned: !note.is_pinned });
    refreshNotes();
  }

  if (deal.status === "loading") return <div style={{ padding: 32, color: "var(--text-muted)" }}>Loading…</div>;
  if (deal.status === "error") return <div style={{ padding: 32, color: "var(--status-error)" }}>{deal.message}</div>;

  const d = deal.data;
  const isClosedOut = d.status === "won" || d.status === "lost";

  const statusColors: Record<string, { bg: string; color: string }> = {
    open: { bg: "#EFF6FF", color: "#2563EB" },
    won:  { bg: "#ECFDF5", color: "#059669" },
    lost: { bg: "#FEF2F2", color: "#DC2626" },
  };
  const sc = statusColors[d.status] ?? statusColors.open;

  return (
    <div className="max-w-4xl">
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20 }}>
        <div>
          <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 4 }}>
            <Link href="/deals" style={{ color: "var(--text-muted)", textDecoration: "none" }}>Deals</Link>
            {" / "}
            <span>{d.title}</span>
          </div>
          <h1 className="page-title">{d.title}</h1>
          <p className="page-subtitle">
            {[
              d.contact_id ? null : d.contact_name,
              d.organization_name,
            ].filter(Boolean).join(" · ")}
            {d.contact_id && d.contact_name && (
              <>
                <Link href={`/contacts/${d.contact_id}`} style={{ color: "var(--text-secondary)", textDecoration: "none" }} className="hover:underline">
                  {d.contact_name}
                </Link>
                {d.organization_name && ` · ${d.organization_name}`}
              </>
            )}
          </p>
          {/* Pills row */}
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 8 }}>
            <span style={{ fontSize: 12, fontWeight: 600, borderRadius: 20, padding: "2px 10px", background: sc.bg, color: sc.color }}>
              {d.status}
            </span>
            {d.value !== null && (
              <span style={{ fontSize: 12, background: "#F9FAFB", color: "var(--text-secondary)", borderRadius: 20, padding: "2px 10px", fontFamily: "monospace" }}>
                {d.currency} {d.value.toLocaleString()}
                {d.expected_close_date && ` · close ${new Date(d.expected_close_date).toLocaleDateString([], { day: "numeric", month: "short", year: "numeric" })}`}
              </span>
            )}
            {d.stage_name && (
              <span style={{ fontSize: 12, background: "#F0F9FF", color: "#0369A1", borderRadius: 20, padding: "2px 10px", display: "inline-flex", alignItems: "center", gap: 4 }}>
                {d.stage_color && <span style={{ width: 7, height: 7, borderRadius: "50%", backgroundColor: d.stage_color, display: "inline-block" }} />}
                {d.stage_name}
              </span>
            )}
          </div>
        </div>

        {/* Action buttons */}
        <div style={{ display: "flex", gap: 8, flexShrink: 0, flexWrap: "wrap", justifyContent: "flex-end" }}>
          {/* Stage move select */}
          <select
            className="erp-select"
            style={{ fontSize: 12, padding: "6px 10px", width: "auto" }}
            value={d.stage_id ?? ""}
            onChange={e => handleStageChange(e.target.value)}
          >
            <option value="">Move Stage ▾</option>
            {stages.status === "ok" && stages.data.map(s => (
              <option key={s.id} value={s.id}>{s.name}</option>
            ))}
          </select>
          <button
            className="btn-primary"
            style={{ fontSize: 12, padding: "6px 14px", background: "#059669", borderColor: "#059669" }}
            disabled={isClosedOut}
            onClick={handleMarkWon}
          >
            Mark Won
          </button>
          <button
            className="btn-secondary"
            style={{ fontSize: 12, padding: "6px 14px", color: "#DC2626", borderColor: "#DC2626" }}
            disabled={isClosedOut}
            onClick={handleMarkLost}
          >
            Mark Lost
          </button>
        </div>
      </div>

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
                  <input className="erp-input" required placeholder="e.g. Follow-up call"
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
                placeholder="Write a note about this deal…"
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
            <form onSubmit={handleSaveDeal}>
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="erp-form-group">
                  <label className="erp-label">Title *</label>
                  <input className="erp-input" required defaultValue={d.title}
                    onChange={e => setEditData({ ...editData, title: e.target.value })} />
                </div>
                <div className="erp-form-group">
                  <label className="erp-label">Stage</label>
                  <select className="erp-select" defaultValue={d.stage_id ?? ""}
                    onChange={e => setEditData({ ...editData, stage_id: e.target.value || undefined })}>
                    <option value="">No stage</option>
                    {stages.status === "ok" && stages.data.map(s => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>
                <div className="erp-form-group">
                  <label className="erp-label">Value</label>
                  <input type="number" className="erp-input" defaultValue={d.value ?? ""}
                    onChange={e => setEditData({ ...editData, value: e.target.value ? parseFloat(e.target.value) : undefined })} />
                </div>
                <div className="erp-form-group">
                  <label className="erp-label">Currency</label>
                  <select className="erp-select" defaultValue={d.currency}
                    onChange={e => setEditData({ ...editData, currency: e.target.value })}>
                    <option value="INR">INR — Indian Rupee</option>
                    <option value="USD">USD — US Dollar</option>
                    <option value="EUR">EUR — Euro</option>
                    <option value="GBP">GBP — British Pound</option>
                  </select>
                </div>
                <div className="erp-form-group">
                  <label className="erp-label">Expected Close Date</label>
                  <input type="date" className="erp-input" defaultValue={d.expected_close_date ?? ""}
                    onChange={e => setEditData({ ...editData, expected_close_date: e.target.value || undefined })} />
                </div>
                <div className="erp-form-group">
                  <label className="erp-label">Probability %</label>
                  <input type="number" min="0" max="100" className="erp-input" defaultValue={d.probability_pct ?? ""}
                    onChange={e => setEditData({ ...editData, probability_pct: e.target.value ? parseFloat(e.target.value) : undefined })} />
                </div>
                <div className="erp-form-group" style={{ gridColumn: "1 / -1" }}>
                  <label className="erp-label">Description</label>
                  <textarea className="erp-textarea" defaultValue={d.description ?? ""}
                    onChange={e => setEditData({ ...editData, description: e.target.value || undefined })} />
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
                  { label: "Title",           value: d.title },
                  { label: "Contact",         value: d.contact_name, href: d.contact_id ? `/contacts/${d.contact_id}` : undefined },
                  { label: "Organization",    value: d.organization_name },
                  { label: "Stage",           value: d.stage_name },
                  { label: "Status",          value: d.status },
                  { label: "Value",           value: d.value !== null ? `${d.currency} ${d.value.toLocaleString()}` : null },
                  { label: "Currency",        value: d.currency },
                  { label: "Expected Close",  value: d.expected_close_date ? new Date(d.expected_close_date).toLocaleDateString() : null },
                  { label: "Actual Close",    value: d.actual_close_date ? new Date(d.actual_close_date).toLocaleDateString() : null },
                  { label: "Probability",     value: d.probability_pct !== null ? `${d.probability_pct}%` : null },
                  { label: "Assigned To",     value: d.assigned_to },
                  { label: "Description",     value: d.description },
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
