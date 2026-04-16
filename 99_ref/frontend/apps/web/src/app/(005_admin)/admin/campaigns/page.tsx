"use client"

import { useEffect, useState, useCallback } from "react"
import { Button, Input } from "@kcontrol/ui"
import {
  Plus, X, Search, RefreshCw, AlertTriangle, ChevronDown, ChevronRight,
  Mail, CheckCircle2, Clock, XCircle, Megaphone, Pencil, Check,
  Tag, ChevronLeft, ChevronRight as ChevronRightIcon,
  BarChart2, Send, Pause, Archive, Ban, FileEdit,
} from "lucide-react"
import {
  listCampaigns, createCampaign, updateCampaign,
  bulkInviteCampaign, listCampaignInvitations,
} from "@/lib/api/admin"
import type {
  CampaignResponse, CreateCampaignRequest, UpdateCampaignRequest,
  BulkInviteResponse, InvitationResponse,
} from "@/lib/types/admin"

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmtDate(iso: string | null) {
  if (!iso) return "—"
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
}
function fmtDateTime(iso: string) {
  return new Date(iso).toLocaleString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
}

function slugify(name: string) {
  return name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")
}

// ── Badges ────────────────────────────────────────────────────────────────────

const CAMPAIGN_TYPE_META: Record<string, { label: string; color: string }> = {
  event:    { label: "Event",    color: "bg-violet-500/10 border-violet-500/20 text-violet-500" },
  referral: { label: "Referral", color: "bg-blue-500/10 border-blue-500/20 text-blue-500" },
  form:     { label: "Form",     color: "bg-emerald-500/10 border-emerald-500/20 text-emerald-500" },
  import:   { label: "Import",   color: "bg-amber-500/10 border-amber-500/20 text-amber-500" },
  other:    { label: "Other",    color: "bg-muted border-border text-muted-foreground" },
}

const STATUS_META: Record<string, { label: string; color: string; borderCls: string; icon: React.FC<{ className?: string }> }> = {
  active:   { label: "Active",   color: "bg-emerald-500/10 border-emerald-500/20 text-emerald-500", borderCls: "border-l-green-500",  icon: CheckCircle2 },
  paused:   { label: "Paused",   color: "bg-amber-500/10 border-amber-500/20 text-amber-500",       borderCls: "border-l-amber-500",  icon: Pause },
  closed:   { label: "Closed",   color: "bg-blue-500/10 border-blue-500/20 text-blue-500",          borderCls: "border-l-blue-500",   icon: Ban },
  archived: { label: "Archived", color: "bg-muted/40 border-border text-muted-foreground/60",       borderCls: "border-l-slate-400",  icon: Archive },
  draft:    { label: "Draft",    color: "bg-muted/60 border-border text-muted-foreground",          borderCls: "border-l-slate-400",  icon: FileEdit },
}

function TypeBadge({ type }: { type: string }) {
  const m = CAMPAIGN_TYPE_META[type] ?? { label: type, color: "bg-muted border-border text-muted-foreground" }
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium border ${m.color}`}>
      <Tag className="h-2.5 w-2.5" />
      {m.label}
    </span>
  )
}

function StatusBadge({ status }: { status: string }) {
  const m = STATUS_META[status] ?? { label: status, color: "bg-muted border-border text-muted-foreground", icon: Clock }
  const Icon = m.icon
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium border ${m.color}`}>
      <Icon className="h-2.5 w-2.5" />
      {m.label}
    </span>
  )
}

function InvStatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    pending:  "bg-amber-500/10 border-amber-500/20 text-amber-500",
    accepted: "bg-emerald-500/10 border-emerald-500/20 text-emerald-500",
    expired:  "bg-muted/40 border-border text-muted-foreground",
    revoked:  "bg-red-500/10 border-red-500/20 text-red-500",
    declined: "bg-muted/40 border-border text-muted-foreground",
  }
  const icons: Record<string, React.ReactNode> = {
    pending:  <Clock className="h-2.5 w-2.5" />,
    accepted: <CheckCircle2 className="h-2.5 w-2.5" />,
    expired:  <AlertTriangle className="h-2.5 w-2.5" />,
    revoked:  <XCircle className="h-2.5 w-2.5" />,
    declined: <XCircle className="h-2.5 w-2.5" />,
  }
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium border ${styles[status] ?? styles.pending}`}>
      {icons[status]}
      {status}
    </span>
  )
}

// ── Bulk Invite Panel ─────────────────────────────────────────────────────────

function BulkInvitePanel({
  campaign,
  onDone,
}: {
  campaign: CampaignResponse
  onDone: (result: BulkInviteResponse) => void
}) {
  const [emailsRaw, setEmailsRaw] = useState("")
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<BulkInviteResponse | null>(null)

  const emails = emailsRaw
    .split(/[\n,;]/)
    .map(e => e.trim().toLowerCase())
    .filter(e => e.includes("@"))

  const handleSend = async () => {
    if (!emails.length) return
    setSending(true); setError(null); setResult(null)
    try {
      const r = await bulkInviteCampaign(campaign.id, { emails })
      setResult(r)
      setEmailsRaw("")
      onDone(r)
    } catch (e) { setError((e as Error).message) }
    finally { setSending(false) }
  }

  return (
    <div className="space-y-3 p-4 border border-border rounded-xl bg-muted/20">
      <div className="flex items-center gap-2">
        <Send className="w-4 h-4 text-primary shrink-0" />
        <span className="text-sm font-medium">Bulk Invite</span>
        <span className="text-xs text-muted-foreground ml-auto">
          Scope: <strong>{campaign.default_scope}</strong>
          {campaign.default_expires_hours && ` · Expires in ${campaign.default_expires_hours}h`}
        </span>
      </div>

      {error && <p className="text-xs text-destructive bg-destructive/10 rounded px-2 py-1">{error}</p>}

      {result && (
        <div className="rounded-lg border border-border bg-card p-3 space-y-2">
          <div className="flex gap-4 text-xs">
            <span className="text-emerald-500 font-medium">✓ {result.sent} sent</span>
            {result.skipped > 0 && <span className="text-amber-500">{result.skipped} skipped</span>}
            {result.errors > 0 && <span className="text-red-500">{result.errors} failed</span>}
          </div>
          {result.results.filter(r => r.status !== "sent").map(r => (
            <div key={r.email} className="text-xs text-muted-foreground flex gap-2">
              <span className="font-mono truncate max-w-[200px]">{r.email}</span>
              <span className={r.status === "skipped" ? "text-amber-500" : "text-red-500"}>{r.reason}</span>
            </div>
          ))}
        </div>
      )}

      <textarea
        className="w-full h-28 rounded-lg border border-border bg-background text-sm px-3 py-2 font-mono resize-none focus:outline-none focus:ring-1 focus:ring-primary placeholder:text-muted-foreground/50"
        placeholder={"Paste emails, one per line or comma-separated:\nalice@example.com\nbob@example.com"}
        value={emailsRaw}
        onChange={e => setEmailsRaw(e.target.value)}
      />
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">
          {emails.length > 0 ? `${emails.length} email${emails.length !== 1 ? "s" : ""} ready` : "Paste emails above"}
        </span>
        <Button
          size="sm"
          className="h-8 px-4 gap-1.5"
          onClick={handleSend}
          disabled={sending || emails.length === 0}
        >
          <Send className="w-3.5 h-3.5" />
          {sending ? "Sending…" : `Send ${emails.length > 0 ? emails.length : ""} Invites`}
        </Button>
      </div>
    </div>
  )
}

// ── Campaign Invitations Panel ─────────────────────────────────────────────────

function CampaignInvitationsPanel({ campaign }: { campaign: CampaignResponse }) {
  const [invitations, setInvitations] = useState<InvitationResponse[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const PAGE_SIZE = 20

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const r = await listCampaignInvitations(campaign.id, { page, page_size: PAGE_SIZE })
      setInvitations(r.items)
      setTotal(r.total)
    } catch { /* non-fatal */ }
    finally { setLoading(false) }
  }, [campaign.id, page])

  useEffect(() => { load() }, [load])

  if (loading) return (
    <div className="space-y-2">
      {[...Array(4)].map((_, i) => <div key={i} className="h-8 bg-muted rounded-lg animate-pulse" />)}
    </div>
  )

  if (invitations.length === 0) return (
    <p className="text-xs text-muted-foreground py-4 text-center">No invitations sent yet.</p>
  )

  return (
    <div className="space-y-2">
      <p className="text-xs text-muted-foreground">{total} total invitation{total !== 1 ? "s" : ""}</p>
      <div className="space-y-1">
        {invitations.map(inv => (
          <div key={inv.id} className="flex items-center gap-3 rounded-lg px-3 py-2 bg-muted/30 hover:bg-muted/50 transition-colors text-xs">
            <span className="font-mono truncate flex-1 min-w-0">{inv.email}</span>
            <InvStatusBadge status={inv.status} />
            <span className="text-muted-foreground shrink-0">exp {fmtDate(inv.expires_at)}</span>
          </div>
        ))}
      </div>
      {total > PAGE_SIZE && (
        <div className="flex items-center justify-between pt-1">
          <span className="text-xs text-muted-foreground">{total} total</span>
          <div className="flex gap-1">
            <Button size="sm" variant="ghost" disabled={page === 1} onClick={() => setPage(p => p - 1)} className="h-6 px-2 text-xs">
              <ChevronLeft className="w-3 h-3" />
            </Button>
            <span className="text-xs text-muted-foreground px-1 flex items-center">{page}</span>
            <Button size="sm" variant="ghost" disabled={page * PAGE_SIZE >= total} onClick={() => setPage(p => p + 1)} className="h-6 px-2 text-xs">
              <ChevronRightIcon className="w-3 h-3" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

// ── Create Campaign Dialog ────────────────────────────────────────────────────

function CreateCampaignDialog({
  onCreated,
  onClose,
}: {
  onCreated: (c: CampaignResponse) => void
  onClose: () => void
}) {
  const [name, setName] = useState("")
  const [desc, setDesc] = useState("")
  const [type, setType] = useState<"event" | "referral" | "form" | "import" | "other">("event")
  const [scope, setScope] = useState<"platform" | "organization" | "workspace">("platform")
  const [expiresHours, setExpiresHours] = useState("168")
  const [codeManuallyEdited, setCodeManuallyEdited] = useState(false)
  const [manualCode, setManualCode] = useState("")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const autoCode = slugify(name) || ""
  const displayCode = codeManuallyEdited ? manualCode : autoCode

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) { setError("Name is required."); return }
    if (!displayCode.trim()) { setError("Campaign name must produce a valid code."); return }
    setSaving(true); setError(null)
    try {
      const c = await createCampaign({
        code: displayCode,
        name,
        description: desc || undefined,
        campaign_type: type,
        default_scope: scope,
        default_expires_hours: parseInt(expiresHours) || 168,
      } as CreateCampaignRequest)
      onCreated(c)
      onClose()
    } catch (e) { setError((e as Error).message) }
    finally { setSaving(false) }
  }

  const days = Math.floor(parseInt(expiresHours) / 24)
  const remHours = parseInt(expiresHours) % 24

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg max-h-[90vh] overflow-y-auto rounded-xl border border-border bg-card shadow-xl">
        <div className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-base">New Invite Campaign</h2>
            <button onClick={onClose} className="text-muted-foreground hover:text-foreground"><X className="w-4 h-4" /></button>
          </div>

          {error && <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">{error}</div>}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Name <span className="text-destructive">*</span></label>
              <Input
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="AWS Summit 2026"
                required
                className="h-8 text-sm"
              />
              <div className="mt-1 flex items-center gap-2">
                <span className="text-xs text-muted-foreground font-mono">code: </span>
                <Input
                  value={displayCode}
                  onChange={e => { setCodeManuallyEdited(true); setManualCode(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, "")) }}
                  className="h-6 text-xs font-mono flex-1 max-w-[220px] px-2"
                  placeholder="auto-generated"
                />
                {codeManuallyEdited && (
                  <button
                    type="button"
                    onClick={() => { setCodeManuallyEdited(false); setManualCode("") }}
                    className="text-xs text-muted-foreground hover:text-foreground"
                  >
                    reset
                  </button>
                )}
              </div>
            </div>

            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Description</label>
              <Input value={desc} onChange={e => setDesc(e.target.value)} placeholder="Optional description" className="h-8 text-sm" />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">Campaign Type</label>
                <select
                  className="w-full h-8 rounded-lg border border-border bg-background text-sm px-2 focus:outline-none focus:ring-1 focus:ring-primary"
                  value={type}
                  onChange={e => setType(e.target.value as typeof type)}
                >
                  <option value="event">Event</option>
                  <option value="referral">Referral</option>
                  <option value="form">Form</option>
                  <option value="import">Import</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">Default Scope</label>
                <select
                  className="w-full h-8 rounded-lg border border-border bg-background text-sm px-2 focus:outline-none focus:ring-1 focus:ring-primary"
                  value={scope}
                  onChange={e => setScope(e.target.value as typeof scope)}
                >
                  <option value="platform">Platform</option>
                  <option value="organization">Organization</option>
                  <option value="workspace">Workspace</option>
                </select>
              </div>
            </div>

            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Default Expiry (hours)</label>
              <Input
                type="number"
                min="1"
                max="2160"
                value={expiresHours}
                onChange={e => setExpiresHours(e.target.value)}
                className="h-8 text-sm"
              />
              <p className="text-xs text-muted-foreground mt-1">
                {parseInt(expiresHours) > 0
                  ? `${days} day${days !== 1 ? "s" : ""}${remHours > 0 ? ` ${remHours}h` : ""}`
                  : "Enter hours"}
              </p>
            </div>

            <div className="flex gap-2 pt-1">
              <Button type="submit" disabled={saving} className="flex-1 h-9">
                {saving ? "Creating…" : "Create Campaign"}
              </Button>
              <Button type="button" variant="ghost" onClick={onClose} className="h-9 px-4">Cancel</Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

// ── Campaign Row ──────────────────────────────────────────────────────────────

function CampaignCard({
  campaign,
  onUpdate,
}: {
  campaign: CampaignResponse
  onUpdate: (c: CampaignResponse) => void
}) {
  const [expanded, setExpanded] = useState(false)
  const [tab, setTab] = useState<"invite" | "invitations" | "details">("invite")
  const [editing, setEditing] = useState(false)
  const [editName, setEditName] = useState(campaign.name)
  const [editDesc, setEditDesc] = useState(campaign.description)
  const [editNotes, setEditNotes] = useState(campaign.notes ?? "")
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [inviteCount, setInviteCount] = useState(campaign.invite_count)

  const acceptRate = inviteCount > 0 ? Math.round((campaign.accepted_count / inviteCount) * 100) : 0
  const sm = STATUS_META[campaign.status] ?? STATUS_META.archived
  const borderCls = sm.borderCls

  const handleSave = async () => {
    setSaving(true); setSaveError(null)
    try {
      const updated = await updateCampaign(campaign.id, {
        name: editName,
        description: editDesc,
        notes: editNotes || null,
      } as UpdateCampaignRequest)
      onUpdate(updated)
      setEditing(false)
    } catch (e) { setSaveError((e as Error).message) }
    finally { setSaving(false) }
  }

  const handleStatusChange = async (newStatus: "active" | "paused" | "closed" | "archived") => {
    try {
      const updated = await updateCampaign(campaign.id, { status: newStatus })
      onUpdate(updated)
    } catch { /* non-fatal */ }
  }

  const isActive = campaign.status === "active"

  return (
    <div className={`group/card rounded-xl border border-l-[3px] ${borderCls} border-border bg-card overflow-hidden`}>
      {/* Header row */}
      <div
        className={`flex items-center gap-3 px-4 py-3 cursor-pointer transition-colors
          ${expanded ? "bg-primary/5 border-b border-border" : "hover:bg-muted/30"}`}
        onClick={() => setExpanded(v => !v)}
      >
        <span className="text-muted-foreground shrink-0">
          {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        </span>
        <Megaphone className={`w-4 h-4 shrink-0 ${isActive ? "text-primary" : "text-muted-foreground"}`} />

        <div className="flex-1 min-w-0 flex items-center gap-2 flex-wrap">
          <span className="font-medium text-sm truncate">{campaign.name}</span>
          <span className="font-mono text-xs text-muted-foreground hidden sm:inline">{campaign.code}</span>
          <TypeBadge type={campaign.campaign_type} />
          <StatusBadge status={campaign.status} />
        </div>

        {/* Stats */}
        <div className="flex items-center gap-4 shrink-0 text-xs text-muted-foreground" onClick={e => e.stopPropagation()}>
          <span className="flex items-center gap-1" title="Total invites">
            <Mail className="w-3 h-3" />
            {inviteCount}
          </span>
          <span className="flex items-center gap-1" title="Accepted">
            <CheckCircle2 className="w-3 h-3 text-emerald-500" />
            {campaign.accepted_count}
          </span>
          {inviteCount > 0 && (
            <span className="text-muted-foreground/60">{acceptRate}%</span>
          )}
          <button
            className="opacity-0 group-hover/card:opacity-100 p-1 rounded hover:bg-muted transition-all"
            onClick={e => { e.stopPropagation(); setEditing(v => !v); if (!expanded) setExpanded(true) }}
            title="Edit"
          >
            <Pencil className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* Expanded content */}
      {expanded && (
        <>
          {/* Inline edit */}
          {editing && (
            <div className="px-4 py-3 border-b border-border space-y-3 bg-muted/20">
              {saveError && <p className="text-xs text-destructive">{saveError}</p>}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-muted-foreground mb-1 block">Name</label>
                  <Input value={editName} onChange={e => setEditName(e.target.value)} className="h-8 text-sm" />
                </div>
                <div>
                  <label className="text-xs text-muted-foreground mb-1 block">Description</label>
                  <Input value={editDesc} onChange={e => setEditDesc(e.target.value)} className="h-8 text-sm" />
                </div>
              </div>
              <div>
                <label className="text-xs text-muted-foreground mb-1 block">Notes</label>
                <Input value={editNotes} onChange={e => setEditNotes(e.target.value)} placeholder="Internal notes" className="h-8 text-sm" />
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                <Button size="sm" onClick={handleSave} disabled={saving} className="h-7 px-3 text-xs gap-1">
                  <Check className="w-3 h-3" />{saving ? "Saving…" : "Save"}
                </Button>
                <Button size="sm" variant="ghost" onClick={() => { setEditing(false); setEditName(campaign.name); setEditDesc(campaign.description); setEditNotes(campaign.notes ?? "") }} className="h-7 px-3 text-xs">
                  Cancel
                </Button>
                <div className="ml-auto flex items-center gap-1">
                  {campaign.status === "active" && (
                    <button onClick={() => handleStatusChange("paused")} className="text-xs px-2 py-1 rounded border border-amber-300 text-amber-600 hover:bg-amber-50 dark:hover:bg-amber-900/20 transition-colors flex items-center gap-1">
                      <Pause className="w-3 h-3" /> Pause
                    </button>
                  )}
                  {campaign.status === "paused" && (
                    <button onClick={() => handleStatusChange("active")} className="text-xs px-2 py-1 rounded border border-emerald-300 text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 transition-colors flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Resume
                    </button>
                  )}
                  {(campaign.status === "active" || campaign.status === "paused") && (
                    <button onClick={() => handleStatusChange("closed")} className="text-xs px-2 py-1 rounded border border-border text-muted-foreground hover:bg-muted transition-colors flex items-center gap-1">
                      <Ban className="w-3 h-3" /> Close
                    </button>
                  )}
                  {campaign.status === "closed" && (
                    <button onClick={() => handleStatusChange("archived")} className="text-xs px-2 py-1 rounded border border-border text-muted-foreground hover:bg-muted transition-colors flex items-center gap-1">
                      <Archive className="w-3 h-3" /> Archive
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Tabs */}
          <div className="flex border-b border-border">
            {(["invite", "invitations", "details"] as const).map(t => (
              <button
                key={t}
                className={`px-4 py-2 text-xs font-medium capitalize transition-colors border-b-2 -mb-px
                  ${tab === t ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"}`}
                onClick={() => setTab(t)}
              >
                {t === "invite"       ? "Bulk Invite" :
                 t === "invitations"  ? `Invitations (${inviteCount})` :
                                       "Details"}
              </button>
            ))}
          </div>

          <div className="p-4">
            {tab === "invite" && campaign.status === "active" && (
              <BulkInvitePanel
                campaign={campaign}
                onDone={r => { setInviteCount(v => v + r.sent); onUpdate({ ...campaign, invite_count: inviteCount + r.sent }) }}
              />
            )}
            {tab === "invite" && campaign.status !== "active" && (
              <div className="flex flex-col items-center gap-2 py-6 text-center">
                <StatusBadge status={campaign.status} />
                <p className="text-sm text-muted-foreground">
                  {campaign.status === "paused"   ? "Campaign is paused — resume it to send more invites." :
                   campaign.status === "closed"   ? "Campaign is closed — no more invitations can be sent." :
                   campaign.status === "draft"    ? "Campaign is a draft — activate it to start sending invites." :
                                                    "Campaign is archived."}
                </p>
              </div>
            )}
            {tab === "invitations" && <CampaignInvitationsPanel campaign={campaign} />}
            {tab === "details" && (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-4 gap-y-2 text-xs">
                {[
                  { label: "Code",         value: campaign.code,                      mono: true },
                  { label: "Type",         value: campaign.campaign_type },
                  { label: "Scope",        value: campaign.default_scope },
                  { label: "Expires In",   value: `${campaign.default_expires_hours}h (${Math.floor(campaign.default_expires_hours / 24)}d)` },
                  { label: "Starts",       value: fmtDate(campaign.starts_at) },
                  { label: "Ends",         value: fmtDate(campaign.ends_at) },
                  { label: "Created",      value: fmtDateTime(campaign.created_at) },
                  { label: "Updated",      value: fmtDateTime(campaign.updated_at) },
                  { label: "Accept Rate",  value: inviteCount > 0 ? `${acceptRate}%` : "—" },
                ].map(row => (
                  <div key={row.label}>
                    <span className="text-muted-foreground">{row.label}</span>
                    <p className={`font-medium ${row.mono ? "font-mono" : ""}`}>{row.value}</p>
                  </div>
                ))}
                {campaign.notes && (
                  <div className="col-span-full">
                    <span className="text-muted-foreground">Notes</span>
                    <p className="text-foreground/80 mt-0.5">{campaign.notes}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

const STATUS_FILTERS = [
  { value: "",         label: "All" },
  { value: "active",   label: "Active" },
  { value: "draft",    label: "Draft" },
  { value: "paused",   label: "Paused" },
  { value: "closed",   label: "Closed" },
  { value: "archived", label: "Archived" },
]

const KPI_META: Record<string, { borderCls: string; bgCls: string; numCls: string }> = {
  total:     { borderCls: "border-l-primary",    bgCls: "bg-primary/10",   numCls: "text-primary" },
  active:    { borderCls: "border-l-green-500",  bgCls: "bg-green-500/10", numCls: "text-green-600" },
  draft:     { borderCls: "border-l-slate-400",  bgCls: "bg-muted",        numCls: "text-muted-foreground" },
  completed: { borderCls: "border-l-blue-500",   bgCls: "bg-blue-500/10",  numCls: "text-blue-600" },
}

export default function AdminCampaignsPage() {
  const [campaigns, setCampaigns] = useState<CampaignResponse[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState("")

  const load = useCallback(async (quiet = false) => {
    if (quiet) setRefreshing(true); else setLoading(true)
    setError(null)
    try {
      const r = await listCampaigns({ status: statusFilter || undefined })
      setCampaigns(r.campaigns)
      setTotal(r.total)
    } catch (e) { setError((e as Error).message) }
    finally { setLoading(false); setRefreshing(false) }
  }, [statusFilter])

  useEffect(() => { load() }, [load])

  const handleUpdate = useCallback((c: CampaignResponse) => {
    setCampaigns(prev => prev.map(x => x.id === c.id ? c : x))
  }, [])

  const handleCreated = useCallback((c: CampaignResponse) => {
    setCampaigns(prev => [c, ...prev])
    setTotal(v => v + 1)
  }, [])

  const filtered = search.trim()
    ? campaigns.filter(c =>
        c.name.toLowerCase().includes(search.toLowerCase()) ||
        c.code.toLowerCase().includes(search.toLowerCase())
      )
    : campaigns

  const activeCampaigns    = campaigns.filter(c => c.status === "active").length
  const draftCampaigns     = campaigns.filter(c => c.status === "draft").length
  const completedCampaigns = campaigns.filter(c => c.status === "closed" || c.status === "archived").length

  const kpis = [
    { key: "total",     label: "Total Campaigns", value: total,              icon: Megaphone },
    { key: "active",    label: "Active",           value: activeCampaigns,   icon: CheckCircle2 },
    { key: "draft",     label: "Draft",            value: draftCampaigns,    icon: FileEdit },
    { key: "completed", label: "Completed",        value: completedCampaigns, icon: BarChart2 },
  ]

  const hasFilters = !!(search.trim() || statusFilter)

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold">Invite Campaigns</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Organise bulk invitations by source — events, referrals, forms, imports
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={() => load(true)} disabled={refreshing} title="Refresh">
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
          </Button>
          <Button onClick={() => setShowCreate(true)} size="sm" className="h-8 px-3">
            <Plus className="w-3.5 h-3.5 mr-1" /> New Campaign
          </Button>
        </div>
      </div>

      {/* KPI stat cards */}
      <div className="grid grid-cols-4 gap-3">
        {kpis.map(s => {
          const m = KPI_META[s.key]
          return (
            <div key={s.key} className={`relative flex items-center gap-3 rounded-xl border border-l-[3px] ${m.borderCls} bg-card px-4 py-3`}>
              <div className={`shrink-0 rounded-lg p-2 ${m.bgCls}`}>
                <s.icon className="w-4 h-4 text-muted-foreground" />
              </div>
              <div className="min-w-0">
                <div className={`text-2xl font-bold tabular-nums leading-none ${m.numCls}`}>{s.value}</div>
                <span className="text-[11px] text-muted-foreground mt-0.5 block truncate">{s.label}</span>
              </div>
            </div>
          )
        })}
      </div>

      {/* Filter bar */}
      <div className="rounded-xl border border-border bg-card px-4 py-3 flex flex-wrap gap-3 items-center">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-muted-foreground" />
          <Input
            className="pl-9 h-9"
            placeholder="Search campaigns by name or code…"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>

        {/* Status filter pills */}
        <div className="flex gap-1 rounded-lg border border-border p-1 bg-muted/30">
          {STATUS_FILTERS.map(f => (
            <button
              key={f.value}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors
                ${statusFilter === f.value ? "bg-background shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"}`}
              onClick={() => setStatusFilter(f.value)}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Active filter chips */}
        {search.trim() && (
          <span className="inline-flex items-center gap-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs px-2 py-0.5 font-medium">
            &quot;{search}&quot;
            <button onClick={() => setSearch("")} className="ml-0.5 hover:opacity-70"><X className="w-3 h-3" /></button>
          </span>
        )}
        {statusFilter && (
          <span className="inline-flex items-center gap-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs px-2 py-0.5 font-medium">
            {STATUS_FILTERS.find(f => f.value === statusFilter)?.label ?? statusFilter}
            <button onClick={() => setStatusFilter("")} className="ml-0.5 hover:opacity-70"><X className="w-3 h-3" /></button>
          </span>
        )}
        {hasFilters && (
          <button
            onClick={() => { setSearch(""); setStatusFilter("") }}
            className="text-xs text-muted-foreground hover:text-foreground ml-auto"
          >
            Clear all
          </button>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertTriangle className="w-4 h-4 shrink-0" /> {error}
        </div>
      )}

      {/* Skeleton */}
      {loading && (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-16 rounded-xl border border-border bg-card animate-pulse" />
          ))}
        </div>
      )}

      {/* List */}
      {!loading && !error && (
        <div className="space-y-3">
          {filtered.length === 0 ? (
            <div className="flex flex-col items-center gap-3 py-16 text-center">
              <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center">
                <Megaphone className="w-6 h-6 text-muted-foreground" />
              </div>
              <div>
                <p className="text-sm font-medium">No campaigns yet</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {search ? `No results for "${search}"` : "Create a campaign to start tracking bulk invitations"}
                </p>
              </div>
              {!search && (
                <Button size="sm" onClick={() => setShowCreate(true)} className="gap-1.5">
                  <Plus className="w-3.5 h-3.5" /> New Campaign
                </Button>
              )}
            </div>
          ) : (
            filtered.map(c => (
              <CampaignCard key={c.id} campaign={c} onUpdate={handleUpdate} />
            ))
          )}
        </div>
      )}

      {/* Create dialog */}
      {showCreate && (
        <CreateCampaignDialog
          onCreated={handleCreated}
          onClose={() => setShowCreate(false)}
        />
      )}
    </div>
  )
}
