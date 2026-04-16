"use client"

import { useEffect, useState, useCallback } from "react"
import {
  Button,
  Input,
  Label,
  Badge,
  Separator,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@kcontrol/ui"
import {
  Share2,
  Plus,
  Trash2,
  AlertTriangle,
  Play,
  Pause,
  Square,
  RefreshCw,
  Send,
  CheckCircle2,
  XCircle,
  Globe,
  ArrowDownToLine,
  Shield,
  X,
  Filter,
} from "lucide-react"
import {
  listSSFStreams,
  createSSFStream,
  updateSSFStreamStatus,
  deleteSSFStream,
  verifySSFStream,
} from "@/lib/api/sandbox"
import type { SSFStreamResponse, SSFVerifyResult } from "@/lib/api/sandbox"
import { useSandboxOrgWorkspace } from "@/lib/context/SandboxOrgWorkspaceContext"
import { SandboxOrgWorkspaceSwitcher } from "@/components/layout/SandboxOrgWorkspaceSwitcher"

// ─────────────────────────────────────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────────────────────────────────────

const DELIVERY_METHODS = [
  { code: "push", label: "Push", description: "Server sends events to your receiver URL via HTTP POST" },
  { code: "poll", label: "Poll", description: "Client polls a K-Control endpoint for new events" },
]

const CAEP_EVENTS = [
  "https://schemas.openid.net/secevent/caep/event-type/session-revoked",
  "https://schemas.openid.net/secevent/caep/event-type/token-claims-change",
  "https://schemas.openid.net/secevent/caep/event-type/credential-change",
  "https://schemas.openid.net/secevent/caep/event-type/assurance-level-change",
  "https://schemas.openid.net/secevent/caep/event-type/device-compliance-change",
]

const RISC_EVENTS = [
  "https://schemas.openid.net/secevent/risc/event-type/account-credential-change-required",
  "https://schemas.openid.net/secevent/risc/event-type/account-purged",
  "https://schemas.openid.net/secevent/risc/event-type/account-disabled",
  "https://schemas.openid.net/secevent/risc/event-type/account-enabled",
  "https://schemas.openid.net/secevent/risc/event-type/identifier-changed",
  "https://schemas.openid.net/secevent/risc/event-type/identifier-recycled",
]

const CUSTOM_EVENTS = [
  "https://kcontrol.io/events/sandbox/signal-fired",
  "https://kcontrol.io/events/sandbox/threat-detected",
  "https://kcontrol.io/events/sandbox/policy-triggered",
]

const ALL_EVENT_GROUPS = [
  { label: "CAEP Events", events: CAEP_EVENTS },
  { label: "RISC Events", events: RISC_EVENTS },
  { label: "K-Control Custom Events", events: CUSTOM_EVENTS },
]

// border-l color per status
const STATUS_BORDER_L: Record<string, string> = {
  enabled:  "border-l-green-500",
  paused:   "border-l-amber-500",
  disabled: "border-l-slate-400",
}

// badge styling per status
const STATUS_CONFIG: Record<string, { label: string; bg: string; text: string; border: string }> = {
  enabled:  { label: "Enabled",  bg: "bg-green-500/10",  text: "text-green-500",  border: "border-green-500/30" },
  paused:   { label: "Paused",   bg: "bg-amber-500/10",  text: "text-amber-500",  border: "border-amber-500/30" },
  disabled: { label: "Disabled", bg: "bg-slate-500/10",  text: "text-slate-400",  border: "border-slate-400/30" },
}

function streamStatusConfig(status: string) {
  return STATUS_CONFIG[status] ?? { label: status, bg: "bg-muted", text: "text-muted-foreground", border: "border-border" }
}

function streamBorderL(status: string) {
  return STATUS_BORDER_L[status] ?? "border-l-primary"
}

function shortEventUri(uri: string) {
  const parts = uri.split("/")
  return parts[parts.length - 1]
}

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
}

// ─────────────────────────────────────────────────────────────────────────────
// Create Stream Dialog
// ─────────────────────────────────────────────────────────────────────────────

function CreateStreamDialog({
  open, onCreate, onClose,
}: {
  open: boolean
  onCreate: (data: { delivery_method: string; receiver_url?: string; events_requested: string[]; description?: string; authorization_header?: string }) => Promise<void>
  onClose: () => void
}) {
  const [deliveryMethod, setDeliveryMethod] = useState("push")
  const [receiverUrl, setReceiverUrl] = useState("")
  const [description, setDescription] = useState("")
  const [authHeader, setAuthHeader] = useState("")
  const [selectedEvents, setSelectedEvents] = useState<Set<string>>(new Set())
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      setDeliveryMethod("push"); setReceiverUrl(""); setDescription("")
      setAuthHeader(""); setSelectedEvents(new Set())
      setSaving(false); setError(null)
    }
  }, [open])

  function toggleEvent(uri: string) {
    setSelectedEvents((prev) => {
      const next = new Set(prev)
      if (next.has(uri)) next.delete(uri)
      else next.add(uri)
      return next
    })
  }

  function toggleGroup(events: string[]) {
    setSelectedEvents((prev) => {
      const next = new Set(prev)
      const allSelected = events.every((e) => next.has(e))
      if (allSelected) {
        events.forEach((e) => next.delete(e))
      } else {
        events.forEach((e) => next.add(e))
      }
      return next
    })
  }

  async function create() {
    if (selectedEvents.size === 0) { setError("Select at least one event type."); return }
    if (deliveryMethod === "push" && !receiverUrl.trim()) { setError("Receiver URL is required for Push delivery."); return }
    setSaving(true); setError(null)
    try {
      await onCreate({
        delivery_method: deliveryMethod,
        receiver_url: deliveryMethod === "push" ? receiverUrl.trim() : undefined,
        events_requested: Array.from(selectedEvents),
        description: description.trim() || undefined,
        authorization_header: authHeader.trim() || undefined,
      })
      onClose()
    } catch (e) { setError(e instanceof Error ? e.message : "Failed to create stream"); setSaving(false) }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-orange-500/10 p-2.5"><Plus className="h-4 w-4 text-orange-500" /></div>
            <div>
              <DialogTitle>Create SSF Stream</DialogTitle>
              <DialogDescription>Configure a new Shared Signals Framework event stream.</DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />
        <div className="space-y-5">
          {/* Delivery method */}
          <div className="space-y-2">
            <Label className="text-xs font-semibold">Delivery Method</Label>
            <div className="grid grid-cols-2 gap-3">
              {DELIVERY_METHODS.map((m) => (
                <button
                  key={m.code}
                  type="button"
                  onClick={() => setDeliveryMethod(m.code)}
                  className={`rounded-lg border px-3 py-2.5 text-left transition-colors ${
                    deliveryMethod === m.code
                      ? "border-primary bg-primary/5"
                      : "border-border bg-card hover:border-primary/30"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {m.code === "push" ? (
                      <Send className={`h-3.5 w-3.5 ${deliveryMethod === m.code ? "text-primary" : "text-muted-foreground"}`} />
                    ) : (
                      <ArrowDownToLine className={`h-3.5 w-3.5 ${deliveryMethod === m.code ? "text-primary" : "text-muted-foreground"}`} />
                    )}
                    <span className={`text-sm font-medium ${deliveryMethod === m.code ? "text-foreground" : "text-muted-foreground"}`}>
                      {m.label}
                    </span>
                  </div>
                  <p className="text-[10px] text-muted-foreground mt-1">{m.description}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Receiver URL (Push only) */}
          {deliveryMethod === "push" && (
            <div className="space-y-1.5">
              <Label className="text-xs">Receiver URL <span className="text-red-500">*</span></Label>
              <Input
                value={receiverUrl}
                onChange={(e) => setReceiverUrl(e.target.value)}
                placeholder="https://your-service.example.com/ssf/events"
                className="h-9 text-sm font-mono"
              />
            </div>
          )}

          {/* Description */}
          <div className="space-y-1.5">
            <Label className="text-xs">Description</Label>
            <Input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Production SIEM integration, Development testing..."
              className="h-9 text-sm"
            />
          </div>

          {/* Auth header (Push only) */}
          {deliveryMethod === "push" && (
            <div className="space-y-1.5">
              <Label className="text-xs">Authorization Header <span className="text-muted-foreground">(optional)</span></Label>
              <Input
                type="password"
                value={authHeader}
                onChange={(e) => setAuthHeader(e.target.value)}
                placeholder="Bearer eyJhbGciOiJSUzI1NiIs..."
                className="h-9 text-sm font-mono"
              />
              <p className="text-[10px] text-muted-foreground">Sent as the Authorization header with each push delivery.</p>
            </div>
          )}

          {/* Events requested */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label className="text-xs font-semibold">Events Requested <span className="text-red-500">*</span></Label>
              <span className="text-[10px] text-muted-foreground">{selectedEvents.size} selected</span>
            </div>
            <div className="space-y-3 rounded-lg border border-border bg-muted/10 p-3 max-h-[240px] overflow-y-auto">
              {ALL_EVENT_GROUPS.map((group) => {
                const allSelected = group.events.every((e) => selectedEvents.has(e))
                const someSelected = group.events.some((e) => selectedEvents.has(e))
                return (
                  <div key={group.label} className="space-y-1.5">
                    <button
                      type="button"
                      onClick={() => toggleGroup(group.events)}
                      className="flex items-center gap-2 text-xs font-semibold text-muted-foreground hover:text-foreground transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={allSelected}
                        ref={(el) => { if (el) el.indeterminate = someSelected && !allSelected }}
                        onChange={() => toggleGroup(group.events)}
                        className="h-3.5 w-3.5 rounded border-input"
                      />
                      {group.label}
                    </button>
                    <div className="space-y-0.5 pl-5">
                      {group.events.map((uri) => (
                        <label key={uri} className="flex items-center gap-2 py-0.5 cursor-pointer group/ev">
                          <input
                            type="checkbox"
                            checked={selectedEvents.has(uri)}
                            onChange={() => toggleEvent(uri)}
                            className="h-3.5 w-3.5 rounded border-input"
                          />
                          <span className="text-[11px] text-muted-foreground group-hover/ev:text-foreground transition-colors font-mono truncate">
                            {shortEventUri(uri)}
                          </span>
                        </label>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {error && <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500 mt-2">{error}</p>}
        <DialogFooter className="mt-3 gap-2 sm:gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={saving}>Cancel</Button>
          <Button size="sm" onClick={create} disabled={saving}>
            {saving ? <span className="flex items-center gap-1.5"><span className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />Creating...</span> : "Create Stream"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Delete Stream Dialog
// ─────────────────────────────────────────────────────────────────────────────

function DeleteStreamDialog({
  stream, onConfirm, onClose,
}: {
  stream: SSFStreamResponse | null
  onConfirm: (id: string) => Promise<void>
  onClose: () => void
}) {
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!stream) return null

  async function confirm() {
    setDeleting(true); setError(null)
    try {
      await onConfirm(stream!.id)
      onClose()
    } catch (e) { setError(e instanceof Error ? e.message : "Failed to delete"); setDeleting(false) }
  }

  return (
    <Dialog open onOpenChange={(o) => { if (!o) onClose() }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-red-500/10 p-2.5"><AlertTriangle className="h-4 w-4 text-red-500" /></div>
            <div>
              <DialogTitle>Delete Stream</DialogTitle>
              <DialogDescription>This will permanently remove the SSF stream configuration.</DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />
        <p className="text-sm">
          Are you sure you want to delete the stream{" "}
          <strong>{stream.stream_description || "Unnamed stream"}</strong>?
          Any connected receivers will stop receiving events immediately.
        </p>
        {error && <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500 mt-2">{error}</p>}
        <DialogFooter className="mt-3 gap-2 sm:gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={deleting}>Cancel</Button>
          <Button variant="destructive" size="sm" onClick={confirm} disabled={deleting}>
            {deleting ? <span className="flex items-center gap-1.5"><span className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />Deleting...</span> : "Delete Stream"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Verify Result Banner
// ─────────────────────────────────────────────────────────────────────────────

function VerifyBanner({ result, onDismiss }: { result: SSFVerifyResult; onDismiss: () => void }) {
  return (
    <div className={`rounded-lg border px-4 py-3 flex items-center gap-3 ${
      result.delivered
        ? "border-green-500/30 bg-green-500/10"
        : "border-red-500/30 bg-red-500/10"
    }`}>
      {result.delivered ? (
        <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
      ) : (
        <XCircle className="h-4 w-4 text-red-500 shrink-0" />
      )}
      <div className="flex-1 min-w-0">
        <p className={`text-sm font-medium ${result.delivered ? "text-green-500" : "text-red-500"}`}>
          {result.delivered ? "Test event delivered successfully" : "Test event delivery failed"}
        </p>
        <p className="text-[10px] text-muted-foreground font-mono">JTI: {result.jti}</p>
      </div>
      <button onClick={onDismiss} className="rounded-md p-1 hover:bg-muted/50 transition-colors shrink-0">
        <X className="h-3.5 w-3.5 text-muted-foreground" />
      </button>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Stream Row (god-tier: plain div, border-l-[3px])
// ─────────────────────────────────────────────────────────────────────────────

function StreamRow({
  stream, onStatusChange, onVerify, onDelete,
}: {
  stream: SSFStreamResponse
  onStatusChange: (id: string, status: string) => Promise<void>
  onVerify: (id: string) => Promise<SSFVerifyResult>
  onDelete: (s: SSFStreamResponse) => void
}) {
  const [verifying, setVerifying] = useState(false)
  const [verifyResult, setVerifyResult] = useState<SSFVerifyResult | null>(null)
  const [statusLoading, setStatusLoading] = useState(false)

  const sc = streamStatusConfig(stream.stream_status)
  const borderL = streamBorderL(stream.stream_status)

  async function handleVerify() {
    setVerifying(true); setVerifyResult(null)
    try {
      const result = await onVerify(stream.id)
      setVerifyResult(result)
    } catch { /* */ }
    finally { setVerifying(false) }
  }

  async function handleStatusChange(status: string) {
    setStatusLoading(true)
    try { await onStatusChange(stream.id, status) } catch { /* */ }
    finally { setStatusLoading(false) }
  }

  const maxEventsShown = 4
  const hiddenEvents = stream.events_requested.length - maxEventsShown

  return (
    <div className={`relative rounded-xl border border-l-[3px] ${borderL} bg-card px-4 py-4 space-y-3 hover:border-orange-500/30 hover:border-l-[3px] hover:${borderL} transition-colors`}>
      {/* Header */}
      <div className="flex items-start gap-3">
        <div className={`shrink-0 rounded-lg p-2 ${stream.delivery_method === "push" ? "bg-orange-500/10" : "bg-blue-500/10"}`}>
          {stream.delivery_method === "push" ? (
            <Send className="h-4 w-4 text-orange-500" />
          ) : (
            <ArrowDownToLine className="h-4 w-4 text-blue-500" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-semibold truncate">
              {stream.stream_description || "Unnamed stream"}
            </span>
            <Badge variant="outline" className={`text-[10px] font-semibold ${sc.bg} ${sc.text} ${sc.border}`}>
              {sc.label}
            </Badge>
          </div>
          <div className="flex items-center gap-2 mt-0.5">
            <Badge variant="outline" className="text-[10px] font-mono bg-muted/50 text-muted-foreground">
              {stream.delivery_method.toUpperCase()}
            </Badge>
            <span className="text-[10px] text-muted-foreground">{fmtDate(stream.created_at)}</span>
          </div>
        </div>
      </div>

      {/* Receiver URL or Poll */}
      {stream.delivery_method === "push" && stream.receiver_url && (
        <div className="flex items-center gap-2 rounded-lg border border-border bg-muted/20 px-3 py-2">
          <Globe className="h-3 w-3 text-muted-foreground shrink-0" />
          <code className="text-[11px] font-mono text-foreground truncate">{stream.receiver_url}</code>
        </div>
      )}
      {stream.delivery_method === "poll" && (
        <div className="flex items-center gap-2 rounded-lg border border-border bg-muted/20 px-3 py-2">
          <ArrowDownToLine className="h-3 w-3 text-muted-foreground shrink-0" />
          <span className="text-[11px] text-muted-foreground">Poll endpoint configured</span>
        </div>
      )}

      {/* Events requested */}
      <div className="space-y-1.5">
        <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Events ({stream.events_requested.length})</p>
        <div className="flex flex-wrap gap-1">
          {stream.events_requested.slice(0, maxEventsShown).map((uri) => (
            <span key={uri} className="rounded-md border border-border bg-muted/50 px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground">
              {shortEventUri(uri)}
            </span>
          ))}
          {hiddenEvents > 0 && (
            <span className="rounded-md border border-border bg-muted/50 px-1.5 py-0.5 text-[10px] text-muted-foreground">
              +{hiddenEvents} more
            </span>
          )}
        </div>
      </div>

      {/* Verify result */}
      {verifyResult && (
        <VerifyBanner result={verifyResult} onDismiss={() => setVerifyResult(null)} />
      )}

      {/* Actions */}
      <Separator />
      <div className="flex items-center gap-1.5 flex-wrap">
        {stream.stream_status !== "enabled" && (
          <Button size="sm" variant="ghost" className="h-7 text-xs gap-1 text-green-500 hover:text-green-400" onClick={() => handleStatusChange("enabled")} disabled={statusLoading}>
            <Play className="h-3 w-3" /> Enable
          </Button>
        )}
        {stream.stream_status === "enabled" && (
          <Button size="sm" variant="ghost" className="h-7 text-xs gap-1 text-amber-500 hover:text-amber-400" onClick={() => handleStatusChange("paused")} disabled={statusLoading}>
            <Pause className="h-3 w-3" /> Pause
          </Button>
        )}
        {stream.stream_status !== "disabled" && (
          <Button size="sm" variant="ghost" className="h-7 text-xs gap-1 text-red-500 hover:text-red-400" onClick={() => handleStatusChange("disabled")} disabled={statusLoading}>
            <Square className="h-3 w-3" /> Disable
          </Button>
        )}

        <Separator orientation="vertical" className="h-4 mx-1" />

        <Button size="sm" variant="ghost" className="h-7 text-xs gap-1" onClick={handleVerify} disabled={verifying}>
          <Send className="h-3 w-3" /> {verifying ? "Sending..." : "Send Test Event"}
        </Button>

        <Button size="sm" variant="ghost" className="h-7 text-xs gap-1 text-muted-foreground hover:text-red-500 ml-auto" onClick={() => onDelete(stream)}>
          <Trash2 className="h-3 w-3" />
        </Button>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Page
// ─────────────────────────────────────────────────────────────────────────────

const STATUS_FILTER_OPTIONS = [
  { value: "enabled",  label: "Enabled",  color: "text-green-500" },
  { value: "paused",   label: "Paused",   color: "text-amber-500" },
  { value: "disabled", label: "Disabled", color: "text-slate-400" },
]

const DELIVERY_FILTER_OPTIONS = [
  { value: "push", label: "Push" },
  { value: "poll", label: "Poll" },
]

export default function SSFStreamsPage() {
  const { selectedOrgId, ready } = useSandboxOrgWorkspace()
  const [streams, setStreams] = useState<SSFStreamResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filters
  const [statusFilter, setStatusFilter] = useState<string | null>(null)
  const [deliveryFilter, setDeliveryFilter] = useState<string | null>(null)

  // Dialogs
  const [showCreate, setShowCreate] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<SSFStreamResponse | null>(null)

  const loadData = useCallback(async () => {
    if (!selectedOrgId) {
      setStreams([])
      setLoading(false)
      setError(null)
      return
    }
    setLoading(true); setError(null)
    try {
      const res = await listSSFStreams(selectedOrgId)
      setStreams(res.items ?? [])
    } catch (e) { setError(e instanceof Error ? e.message : "Failed to load SSF streams") }
    finally { setLoading(false) }
  }, [selectedOrgId])

  useEffect(() => {
    if (ready) void loadData()
  }, [loadData, ready])

  async function handleCreate(data: { delivery_method: string; receiver_url?: string; events_requested: string[]; description?: string; authorization_header?: string }) {
    if (!selectedOrgId) return
    await createSSFStream({ orgId: selectedOrgId, ...data })
    await loadData()
  }

  async function handleStatusChange(id: string, status: string) {
    if (!selectedOrgId) return
    await updateSSFStreamStatus(id, selectedOrgId, status)
    await loadData()
  }

  async function handleVerify(id: string): Promise<SSFVerifyResult> {
    return await verifySSFStream(id)
  }

  async function handleDelete(id: string) {
    if (!selectedOrgId) return
    await deleteSSFStream(id, selectedOrgId)
    setDeleteTarget(null)
    await loadData()
  }

  // Stats
  const enabledCount  = streams.filter((s) => s.stream_status === "enabled").length
  const pausedCount   = streams.filter((s) => s.stream_status === "paused").length
  const disabledCount = streams.filter((s) => s.stream_status === "disabled").length
  const pushCount     = streams.filter((s) => s.delivery_method === "push").length
  const pollCount     = streams.filter((s) => s.delivery_method === "poll").length

  // Filtered list
  const filtered = streams.filter((s) => {
    if (statusFilter && s.stream_status !== statusFilter) return false
    if (deliveryFilter && s.delivery_method !== deliveryFilter) return false
    return true
  })

  const activeFilters: { key: string; label: string; onRemove: () => void }[] = []
  if (statusFilter) {
    const opt = STATUS_FILTER_OPTIONS.find((o) => o.value === statusFilter)
    activeFilters.push({ key: "status", label: `Status: ${opt?.label ?? statusFilter}`, onRemove: () => setStatusFilter(null) })
  }
  if (deliveryFilter) {
    activeFilters.push({ key: "delivery", label: `Delivery: ${deliveryFilter.toUpperCase()}`, onRemove: () => setDeliveryFilter(null) })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="rounded-xl bg-orange-500/10 p-3 shrink-0">
            <Share2 className="h-6 w-6 text-orange-500" />
          </div>
          <div className="flex flex-col gap-1">
            <h2 className="text-2xl font-semibold text-foreground">SSF Event Streams</h2>
            <p className="text-sm text-muted-foreground">
              Manage Shared Signals Framework (SSF) transmitter streams for real-time security event distribution.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <SandboxOrgWorkspaceSwitcher />
          <Button size="sm" className="gap-1.5 shrink-0" onClick={() => setShowCreate(true)} disabled={!selectedOrgId}>
            <Plus className="h-3.5 w-3.5" /> Create Stream
          </Button>
        </div>
      </div>

      {!selectedOrgId && (
        <div className="rounded-xl border border-border bg-card px-5 py-8 text-center text-sm text-muted-foreground">
          Select an organisation to manage SSF streams.
        </div>
      )}

      {/* KPI stat cards */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {([
          { label: "Total Streams", value: streams.length,          icon: Share2, iconBg: "bg-muted",          iconColor: "text-muted-foreground", borderCls: "border-l-primary",      numCls: "text-foreground" },
          { label: "Enabled",       value: enabledCount,            icon: Play,   iconBg: "bg-green-500/10",  iconColor: "text-green-500",         borderCls: "border-l-green-500",    numCls: "text-green-500" },
          { label: "Paused",        value: pausedCount,             icon: Pause,  iconBg: "bg-amber-500/10",  iconColor: "text-amber-500",         borderCls: "border-l-amber-500",    numCls: "text-amber-500" },
          { label: "Push / Poll",   value: `${pushCount}/${pollCount}`, icon: Send, iconBg: "bg-blue-500/10", iconColor: "text-blue-500",          borderCls: "border-l-blue-500",     numCls: "text-blue-500" },
        ] as const).map((s) => (
          <div key={s.label} className={`relative flex items-center gap-3 rounded-xl border border-l-[3px] ${s.borderCls} bg-card px-4 py-3`}>
            <div className={`shrink-0 rounded-lg p-2 ${s.iconBg}`}>
              <s.icon className={`h-4 w-4 ${s.iconColor}`} />
            </div>
            <div className="flex flex-col min-w-0">
              <span className={`text-2xl font-bold tabular-nums leading-none ${s.numCls}`}>{s.value}</span>
              <span className="text-[11px] text-muted-foreground mt-0.5 block truncate">{s.label}</span>
            </div>
          </div>
        ))}
      </div>

      {/* SSF Protocol info banner */}
      <div className="rounded-xl border border-border bg-muted/20 px-5 py-4 space-y-2">
        <div className="flex items-center gap-2">
          <Shield className="h-4 w-4 text-orange-500" />
          <h3 className="text-sm font-semibold text-foreground">Shared Signals Framework</h3>
        </div>
        <p className="text-xs text-muted-foreground leading-relaxed">
          SSF enables cross-domain security event sharing using standardized CAEP and RISC event types.
          Configure streams to transmit sandbox detection events to external SIEM, SOAR, or identity providers
          in real time via push or pull delivery.
        </p>
        <div className="flex items-center gap-2 text-xs text-muted-foreground pt-1">
          <span className="rounded-md border border-orange-500/30 bg-orange-500/10 px-2 py-0.5 font-medium text-orange-500">CAEP</span>
          <span className="rounded-md border border-blue-500/30 bg-blue-500/10 px-2 py-0.5 font-medium text-blue-500">RISC</span>
          <span className="rounded-md border border-purple-500/30 bg-purple-500/10 px-2 py-0.5 font-medium text-purple-500">Custom</span>
          <span className="text-muted-foreground ml-1">SET (Security Event Token) format</span>
        </div>
      </div>

      {/* Filter bar */}
      <div className="rounded-xl border border-border bg-card px-4 py-3 flex items-center gap-3 flex-wrap">
        <Filter className="h-3.5 w-3.5 text-muted-foreground shrink-0" />

        {/* Status filter */}
        <div className="flex items-center gap-1">
          {STATUS_FILTER_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => setStatusFilter(statusFilter === opt.value ? null : opt.value)}
              className={`rounded-md px-2.5 py-1 text-[11px] font-medium transition-colors ${
                statusFilter === opt.value
                  ? `bg-muted ${opt.color}`
                  : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>

        <Separator orientation="vertical" className="h-4" />

        {/* Delivery filter */}
        <div className="flex items-center gap-1">
          {DELIVERY_FILTER_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => setDeliveryFilter(deliveryFilter === opt.value ? null : opt.value)}
              className={`rounded-md px-2.5 py-1 text-[11px] font-medium transition-colors ${
                deliveryFilter === opt.value
                  ? "bg-muted text-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>

        {/* Active filter chips */}
        {activeFilters.length > 0 && (
          <>
            <Separator orientation="vertical" className="h-4" />
            <div className="flex items-center gap-1.5 flex-wrap">
              {activeFilters.map((f) => (
                <span
                  key={f.key}
                  className="flex items-center gap-1 rounded-md border border-border bg-muted/60 px-2 py-0.5 text-[11px] text-foreground"
                >
                  {f.label}
                  <button
                    type="button"
                    onClick={f.onRemove}
                    className="rounded-sm hover:bg-muted transition-colors ml-0.5"
                  >
                    <X className="h-2.5 w-2.5 text-muted-foreground" />
                  </button>
                </span>
              ))}
              <button
                type="button"
                onClick={() => { setStatusFilter(null); setDeliveryFilter(null) }}
                className="text-[11px] text-muted-foreground hover:text-foreground transition-colors"
              >
                Clear all
              </button>
            </div>
          </>
        )}

        <Button size="sm" variant="ghost" className="h-7 gap-1 ml-auto text-xs" onClick={loadData}>
          <RefreshCw className="h-3.5 w-3.5" /> Refresh
        </Button>

        {filtered.length !== streams.length && (
          <span className="text-[11px] text-muted-foreground">{filtered.length} of {streams.length}</span>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-500">
          {error}
        </div>
      )}

      {/* Loading skeleton */}
      {loading && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="rounded-xl border border-l-[3px] border-l-primary border-border bg-card px-4 py-4 space-y-3 animate-pulse">
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-lg bg-muted" />
                <div className="space-y-1 flex-1">
                  <div className="h-4 w-2/3 rounded bg-muted" />
                  <div className="h-2.5 w-1/3 rounded bg-muted" />
                </div>
              </div>
              <div className="h-8 w-full rounded bg-muted" />
              <div className="flex gap-1">
                <div className="h-5 w-20 rounded bg-muted" />
                <div className="h-5 w-16 rounded bg-muted" />
                <div className="h-5 w-24 rounded bg-muted" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Stream rows */}
      {!loading && filtered.length > 0 && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {filtered.map((stream) => (
            <StreamRow
              key={stream.id}
              stream={stream}
              onStatusChange={handleStatusChange}
              onVerify={handleVerify}
              onDelete={setDeleteTarget}
            />
          ))}
        </div>
      )}

      {/* Empty state — no streams at all */}
      {!loading && !error && streams.length === 0 && (
        <div className="rounded-xl border border-dashed border-border bg-muted/10 px-5 py-12 text-center space-y-3">
          <Share2 className="h-8 w-8 text-muted-foreground mx-auto" />
          <p className="text-sm font-medium text-foreground">No SSF streams configured</p>
          <p className="text-xs text-muted-foreground max-w-md mx-auto">
            Create your first SSF stream to start distributing sandbox security events to external systems
            using the Shared Signals Framework protocol.
          </p>
          <Button size="sm" variant="outline" className="gap-1.5" onClick={() => setShowCreate(true)}>
            <Plus className="h-3.5 w-3.5" /> Create Stream
          </Button>
        </div>
      )}

      {/* Empty state — filters produced no results */}
      {!loading && !error && streams.length > 0 && filtered.length === 0 && (
        <div className="rounded-xl border border-dashed border-border bg-muted/10 px-5 py-10 text-center space-y-2">
          <Filter className="h-6 w-6 text-muted-foreground mx-auto" />
          <p className="text-sm font-medium text-foreground">No streams match the active filters</p>
          <button
            type="button"
            onClick={() => { setStatusFilter(null); setDeliveryFilter(null) }}
            className="text-xs text-muted-foreground hover:text-foreground underline underline-offset-2 transition-colors"
          >
            Clear filters
          </button>
        </div>
      )}

      {/* Dialogs */}
      <CreateStreamDialog open={showCreate} onCreate={handleCreate} onClose={() => setShowCreate(false)} />
      <DeleteStreamDialog stream={deleteTarget} onConfirm={handleDelete} onClose={() => setDeleteTarget(null)} />
    </div>
  )
}
