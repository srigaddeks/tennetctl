"use client"

import { useEffect, useState, useCallback, useRef } from "react"
import {
  Card,
  CardContent,
  Button,
  Input,
  Label,
  Badge,
  Separator,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
} from "@kcontrol/ui"
import {
  MessageSquarePlus,
  Plus,
  Search,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Circle,
  Clock,
  X,
  ChevronDown,
  Loader2,
  Bug,
  Lightbulb,
  MessageSquare,
  ShieldAlert,
  Zap,
  Inbox,
  Paperclip,
} from "lucide-react"
import {
  listMyTickets,
  createTicket,
  deleteTicket,
  getFeedbackDimensions,
  getTicket,
} from "@/lib/api/feedback"
import { uploadAttachment } from "@/lib/api/attachments"
import { CommentsSection } from "@/components/comments/CommentsSection"
import { AttachmentsSection } from "@/components/attachments/AttachmentsSection"
import type {
  TicketResponse,
  TicketDimensionsResponse,
  CreateTicketRequest,
} from "@/lib/api/feedback"

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

function getJwtSubject(): string | null {
  try {
    const token = localStorage.getItem("access_token")
    if (!token) return null
    const payload = JSON.parse(atob(token.split(".")[1]))
    return payload.sub || null
  } catch {
    return null
  }
}

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  })
}

const TYPE_ICONS: Record<string, React.ElementType> = {
  bug_report: Bug,
  feature_request: Lightbulb,
  general_feedback: MessageSquare,
  service_issue: ShieldAlert,
  security_concern: Zap,
}

const STATUS_COLORS: Record<string, string> = {
  open: "bg-blue-500/10 text-blue-600 border-blue-500/20",
  in_review: "bg-purple-500/10 text-purple-600 border-purple-500/20",
  in_progress: "bg-amber-500/10 text-amber-700 border-amber-500/20",
  resolved: "bg-emerald-500/10 text-emerald-600 border-emerald-500/20",
  closed: "bg-muted text-muted-foreground border-border",
  wont_fix: "bg-red-500/10 text-red-600 border-red-500/20",
  duplicate: "bg-gray-500/10 text-gray-600 border-gray-500/20",
}

const PRIORITY_COLORS: Record<string, string> = {
  critical: "text-red-600",
  high: "text-orange-600",
  medium: "text-amber-600",
  low: "text-muted-foreground",
}

function StatusBadge({ code, label }: { code: string; label?: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium ${STATUS_COLORS[code] ?? "bg-muted text-muted-foreground border-border"}`}
    >
      {label ?? code}
    </span>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Submit Dialog
// ─────────────────────────────────────────────────────────────────────────────

function SubmitDialog({
  open,
  dimensions,
  onClose,
  onSubmitted,
}: {
  open: boolean
  dimensions: TicketDimensionsResponse | null
  onClose: () => void
  onSubmitted: (t: TicketResponse) => void
}) {
  const MAX_FILES = 5
  const MAX_FILE_SIZE_MB = 25
  const [typeCode, setTypeCode] = useState("general_feedback")
  const [priorityCode, setPriorityCode] = useState("medium")
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [contextUrl, setContextUrl] = useState("")
  const [stepsToReproduce, setStepsToReproduce] = useState("")
  const [files, setFiles] = useState<File[]>([])
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const selected = Array.from(e.target.files ?? [])
    if (selected.length === 0) return
    const oversized = selected.find((f) => f.size > MAX_FILE_SIZE_MB * 1024 * 1024)
    if (oversized) {
      setError(`File "${oversized.name}" exceeds ${MAX_FILE_SIZE_MB}MB limit.`)
      return
    }
    const combined = [...files, ...selected].slice(0, MAX_FILES)
    setFiles(combined)
    if (files.length + selected.length > MAX_FILES) {
      setError(`Maximum ${MAX_FILES} files allowed.`)
    }
    e.target.value = ""
  }

  function removeFile(index: number) {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }

  async function handleSubmit() {
    if (!title.trim() || !description.trim()) {
      setError("Title and description are required.")
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      const body: CreateTicketRequest = {
        ticket_type_code: typeCode,
        priority_code: priorityCode,
        title: title.trim(),
        description: description.trim(),
        context_url: contextUrl.trim() || null,
        steps_to_reproduce: stepsToReproduce.trim() || null,
      }
      const ticket = await createTicket(body)

      // Upload attachments (best-effort — ticket is already created)
      if (files.length > 0) {
        const uploadErrors: string[] = []
        for (const file of files) {
          try {
            await uploadAttachment("feedback_ticket", ticket.id, file)
          } catch {
            uploadErrors.push(file.name)
          }
        }
        if (uploadErrors.length > 0) {
          setError(`Ticket created but failed to upload: ${uploadErrors.join(", ")}`)
        }
      }

      onSubmitted(ticket)
      // Reset
      setTypeCode("general_feedback")
      setPriorityCode("medium")
      setTitle("")
      setDescription("")
      setContextUrl("")
      setStepsToReproduce("")
      setFiles([])
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to submit ticket")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Submit Feedback or Report an Issue</DialogTitle>
          <DialogDescription>
            Tell us what you need — we review every submission.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          {error && (
            <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label>Type</Label>
              <select
                className="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring"
                value={typeCode}
                onChange={(e) => setTypeCode(e.target.value)}
              >
                {(dimensions?.ticket_types ?? []).filter((t) => t.is_active).sort((a, b) => a.sort_order - b.sort_order).map((t) => (
                  <option key={t.code} value={t.code}>
                    {t.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <Label>Priority</Label>
              <select
                className="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring"
                value={priorityCode}
                onChange={(e) => setPriorityCode(e.target.value)}
              >
                {(dimensions?.ticket_priorities ?? []).sort((a, b) => a.sort_order - b.sort_order).map((p) => (
                  <option key={p.code} value={p.code}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="fb-title">Title <span className="text-destructive">*</span></Label>
            <Input
              id="fb-title"
              placeholder="Brief summary of your feedback or issue"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              maxLength={300}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="fb-desc">Description <span className="text-destructive">*</span></Label>
            <textarea
              id="fb-desc"
              className="w-full min-h-[120px] rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="Provide as much detail as possible..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          {(typeCode === "bug_report" || typeCode === "service_issue") && (
            <div className="space-y-1.5">
              <Label htmlFor="fb-steps">Steps to Reproduce</Label>
              <textarea
                id="fb-steps"
                className="w-full min-h-[80px] rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                placeholder="1. Go to...\n2. Click on...\n3. See error"
                value={stepsToReproduce}
                onChange={(e) => setStepsToReproduce(e.target.value)}
              />
            </div>
          )}

          <div className="space-y-1.5">
            <Label htmlFor="fb-url">Page URL (optional)</Label>
            <Input
              id="fb-url"
              placeholder="https://..."
              value={contextUrl}
              onChange={(e) => setContextUrl(e.target.value)}
            />
          </div>

          {/* Attachments */}
          <div className="space-y-1.5">
            <Label>Attachments</Label>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              className="hidden"
              onChange={handleFileSelect}
              accept="image/*,.pdf,.doc,.docx,.txt,.csv,.json,.xml,.zip,.yaml,.yml,.md,.rtf"
            />
            {files.length > 0 && (
              <div className="space-y-1">
                {files.map((f, i) => (
                  <div
                    key={`${f.name}-${i}`}
                    className="flex items-center gap-2 rounded-md border border-input bg-muted/50 px-2 py-1 text-xs"
                  >
                    <Paperclip className="h-3 w-3 shrink-0 text-muted-foreground" />
                    <span className="truncate flex-1">{f.name}</span>
                    <span className="text-muted-foreground shrink-0">
                      {f.size < 1024 * 1024
                        ? `${Math.round(f.size / 1024)}KB`
                        : `${(f.size / (1024 * 1024)).toFixed(1)}MB`}
                    </span>
                    <button
                      type="button"
                      onClick={() => removeFile(i)}
                      className="shrink-0 rounded p-0.5 hover:bg-muted"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </div>
                ))}
              </div>
            )}
            {files.length < MAX_FILES && (
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="gap-1.5 text-xs"
                onClick={() => fileInputRef.current?.click()}
              >
                <Paperclip className="h-3 w-3" />
                {files.length === 0 ? "Attach files" : "Add more"}
              </Button>
            )}
            <p className="text-[11px] text-muted-foreground">
              Up to {MAX_FILES} files, {MAX_FILE_SIZE_MB}MB each. Screenshots, logs, documents.
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={submitting}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={submitting}>
            {submitting ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <MessageSquarePlus className="h-4 w-4 mr-2" />}
            Submit
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Ticket Detail Panel
// ─────────────────────────────────────────────────────────────────────────────

function TicketDetailPanel({
  ticket,
  dimensions,
  onClose,
}: {
  ticket: TicketResponse
  dimensions: TicketDimensionsResponse | null
  onClose: () => void
}) {
  const typeDef = dimensions?.ticket_types.find((t) => t.code === ticket.ticket_type_code)
  const statusDef = dimensions?.ticket_statuses.find((s) => s.code === ticket.status_code)
  const TypeIcon = TYPE_ICONS[ticket.ticket_type_code] ?? MessageSquare

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <span className="mt-0.5 p-2 rounded-lg bg-primary/10 text-primary">
            <TypeIcon className="h-5 w-5" />
          </span>
          <div>
            <h2 className="text-xl font-semibold">{ticket.title}</h2>
            <div className="flex items-center gap-2 mt-1.5 flex-wrap">
              <StatusBadge code={ticket.status_code} label={statusDef?.name} />
              <span className={`text-xs font-medium ${PRIORITY_COLORS[ticket.priority_code] ?? ""}`}>
                {ticket.priority_code}
              </span>
              <span className="text-xs text-muted-foreground">{typeDef?.name ?? ticket.ticket_type_code}</span>
              <span className="text-xs text-muted-foreground">#{ticket.id.slice(0, 8)}</span>
              <span className="text-xs text-muted-foreground">Submitted {fmtDate(ticket.created_at)}</span>
            </div>
          </div>
        </div>
        <Button variant="ghost" size="sm" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      {ticket.description && (
        <div className="space-y-1">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Description</h3>
          <p className="text-sm whitespace-pre-wrap leading-relaxed">{ticket.description}</p>
        </div>
      )}

      {ticket.steps_to_reproduce && (
        <div className="space-y-1">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Steps to Reproduce</h3>
          <p className="text-sm whitespace-pre-wrap leading-relaxed">{ticket.steps_to_reproduce}</p>
        </div>
      )}

      {ticket.context_url && (
        <div className="space-y-1">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Related URL</h3>
          <a href={ticket.context_url} target="_blank" rel="noopener noreferrer" className="text-sm text-primary hover:underline break-all">
            {ticket.context_url}
          </a>
        </div>
      )}

      {ticket.admin_note && (
        <div className="rounded-lg border border-primary/20 bg-primary/5 p-4 space-y-1">
          <h3 className="text-sm font-semibold text-primary">Admin Note</h3>
          <p className="text-sm whitespace-pre-wrap">{ticket.admin_note}</p>
        </div>
      )}

      <Separator />

      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Attachments</h3>
        <AttachmentsSection entityType="feedback_ticket" entityId={ticket.id} currentUserId={getJwtSubject() ?? ""} />
      </div>

      <Separator />

      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Comments</h3>
        <CommentsSection entityType="feedback_ticket" entityId={ticket.id} currentUserId={getJwtSubject() ?? ""} />
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Page
// ─────────────────────────────────────────────────────────────────────────────

export default function FeedbackPage() {
  const [tickets, setTickets] = useState<TicketResponse[]>([])
  const [total, setTotal] = useState(0)
  const [dimensions, setDimensions] = useState<TicketDimensionsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [filterStatus, setFilterStatus] = useState("")
  const [filterType, setFilterType] = useState("")
  const [showSubmit, setShowSubmit] = useState(false)
  const [selectedTicket, setSelectedTicket] = useState<TicketResponse | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [dimRes, ticketRes] = await Promise.all([
        getFeedbackDimensions(),
        listMyTickets({
          status_code: filterStatus || undefined,
          ticket_type_code: filterType || undefined,
          limit: 50,
        }),
      ])
      setDimensions(dimRes)
      setTickets(ticketRes.items)
      setTotal(ticketRes.total)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load feedback")
    } finally {
      setLoading(false)
    }
  }, [filterStatus, filterType])

  useEffect(() => {
    load()
  }, [load])

  function handleSubmitted(ticket: TicketResponse) {
    setShowSubmit(false)
    setTickets((prev) => [ticket, ...prev])
    setTotal((prev) => prev + 1)
    setSelectedTicket(ticket)
  }

  const filtered = tickets.filter((t) => {
    if (!search) return true
    const q = search.toLowerCase()
    return (
      t.title?.toLowerCase().includes(q) ||
      t.description?.toLowerCase().includes(q) ||
      t.ticket_type_code.includes(q)
    )
  })

  if (selectedTicket) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" size="sm" className="gap-2" onClick={() => setSelectedTicket(null)}>
          <X className="h-4 w-4" />
          Back to my submissions
        </Button>
        <TicketDetailPanel
          ticket={selectedTicket}
          dimensions={dimensions}
          onClose={() => setSelectedTicket(null)}
        />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Feedback & Support</h1>
          <p className="text-muted-foreground mt-1 text-sm">
            Report issues, request features, or share your thoughts. We read everything.
          </p>
        </div>
        <Button onClick={() => setShowSubmit(true)} className="gap-2">
          <Plus className="h-4 w-4" />
          New Ticket
        </Button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            className="pl-9"
            placeholder="Search tickets..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <select
          className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm"
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
        >
          <option value="">All statuses</option>
          {(dimensions?.ticket_statuses ?? []).sort((a, b) => a.sort_order - b.sort_order).map((s) => (
            <option key={s.code} value={s.code}>{s.name}</option>
          ))}
        </select>

        <select
          className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm"
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
        >
          <option value="">All types</option>
          {(dimensions?.ticket_types ?? []).filter((t) => t.is_active).sort((a, b) => a.sort_order - b.sort_order).map((t) => (
            <option key={t.code} value={t.code}>{t.name}</option>
          ))}
        </select>

        <Button variant="ghost" size="icon" onClick={load} title="Refresh">
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        </Button>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-4 flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Ticket list */}
      {loading ? (
        <div className="flex items-center justify-center py-16 text-muted-foreground gap-2">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span>Loading tickets...</span>
        </div>
      ) : filtered.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 gap-3">
            <Inbox className="h-10 w-10 text-muted-foreground/40" />
            <p className="text-muted-foreground text-sm">
              {tickets.length === 0
                ? "No tickets yet. Submit your first feedback!"
                : "No tickets match your filters."}
            </p>
            {tickets.length === 0 && (
              <Button onClick={() => setShowSubmit(true)} className="mt-2 gap-2">
                <Plus className="h-4 w-4" />
                Submit Feedback
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2">
          {filtered.map((ticket) => {
            const TypeIcon = TYPE_ICONS[ticket.ticket_type_code] ?? MessageSquare
            const statusDef = dimensions?.ticket_statuses.find((s) => s.code === ticket.status_code)
            return (
              <Card
                key={ticket.id}
                className="cursor-pointer hover:border-primary/30 transition-colors"
                onClick={() => setSelectedTicket(ticket)}
              >
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <span className="mt-0.5 p-1.5 rounded-md bg-primary/10 text-primary shrink-0">
                      <TypeIcon className="h-4 w-4" />
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2 flex-wrap">
                        <span className="font-medium text-sm truncate">{ticket.title}</span>
                        <div className="flex items-center gap-2 shrink-0">
                          <StatusBadge code={ticket.status_code} label={statusDef?.name} />
                          <span className={`text-xs font-medium ${PRIORITY_COLORS[ticket.priority_code] ?? ""}`}>
                            {ticket.priority_code}
                          </span>
                        </div>
                      </div>
                      {ticket.description && (
                        <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{ticket.description}</p>
                      )}
                      <p className="text-xs text-muted-foreground mt-1.5">{fmtDate(ticket.created_at)}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      <SubmitDialog
        open={showSubmit}
        dimensions={dimensions}
        onClose={() => setShowSubmit(false)}
        onSubmitted={handleSubmitted}
      />
    </div>
  )
}
