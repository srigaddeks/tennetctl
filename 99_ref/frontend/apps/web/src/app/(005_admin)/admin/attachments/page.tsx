"use client"

import { useCallback, useEffect, useState } from "react"
import { Button, Input } from "@kcontrol/ui"
import {
  Paperclip,
  AlertCircle,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Trash2,
  ShieldCheck,
  ShieldAlert,
  Clock,
  HardDrive,
  X,
  RotateCcw,
  Activity,
  Database,
  Shield,
  Loader2,
  CheckCircle2,
  FileImage,
  FileText,
  FileSpreadsheet,
  File,
} from "lucide-react"
import { fetchWithAuth } from "@/lib/api/apiClient"
import { gdprDeleteUserAttachments } from "@/lib/api/attachments"
import type { GdprAttachmentDeleteResult } from "@/lib/api/attachments"
import type { AttachmentRecord } from "@/lib/types/attachments"

// ── Constants ─────────────────────────────────────────────────────────────────

const PAGE_SIZE = 50

const ENTITY_TYPES = [
  "task",
  "risk",
  "control",
  "framework",
  "test",
  "evidence_template",
  "comment",
  "feedback_ticket",
] as const

const VIRUS_SCAN_STATUSES = ["pending", "clean", "infected", "error", "skipped"] as const
type VirusScanStatus = (typeof VIRUS_SCAN_STATUSES)[number]

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B"
  const units = ["B", "KB", "MB", "GB", "TB"]
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  const val = bytes / Math.pow(1024, i)
  return `${val % 1 === 0 ? val : val.toFixed(1)} ${units[i]}`
}

/** Classify file into a display type bucket. */
function fileCategory(contentType: string, filename: string): "image" | "document" | "spreadsheet" | "other" {
  const ct = contentType.toLowerCase()
  const ext = filename.split(".").pop()?.toLowerCase() ?? ""

  if (ct.startsWith("image/") || ["png", "jpg", "jpeg", "gif", "webp", "svg"].includes(ext)) {
    return "image"
  }
  if (
    ct.includes("spreadsheet") ||
    ct.includes("excel") ||
    ct.includes("csv") ||
    ["xlsx", "xls", "csv", "ods"].includes(ext)
  ) {
    return "spreadsheet"
  }
  if (
    ct === "application/pdf" ||
    ct.includes("word") ||
    ct.includes("text/") ||
    ct.includes("document") ||
    ["pdf", "doc", "docx", "txt", "md", "rtf"].includes(ext)
  ) {
    return "document"
  }
  return "other"
}

/** border-l color: document=blue-500, image=green-500, spreadsheet=amber-500, other=slate-400 */
function fileTypeBorderClass(contentType: string, filename: string): string {
  switch (fileCategory(contentType, filename)) {
    case "document":    return "border-l-blue-500"
    case "image":       return "border-l-green-500"
    case "spreadsheet": return "border-l-amber-500"
    default:            return "border-l-slate-400"
  }
}

function virusScanBadgeClass(status: VirusScanStatus): string {
  switch (status) {
    case "clean":    return "bg-emerald-500/10 text-emerald-600 border-emerald-500/20"
    case "infected": return "bg-red-500/10 text-red-600 border-red-500/20"
    case "pending":  return "bg-amber-500/10 text-amber-600 border-amber-500/20"
    case "error":    return "bg-orange-500/10 text-orange-600 border-orange-500/20"
    case "skipped":  return "bg-muted text-muted-foreground border-border"
    default:         return "bg-muted text-muted-foreground border-border"
  }
}

function virusScanIcon(status: VirusScanStatus) {
  switch (status) {
    case "clean":    return <ShieldCheck className="h-3 w-3" />
    case "infected": return <ShieldAlert className="h-3 w-3" />
    case "pending":  return <Clock className="h-3 w-3" />
    case "error":    return <AlertCircle className="h-3 w-3" />
    default:         return null
  }
}

function entityTypeBadgeClass(type: string): string {
  switch (type) {
    case "task":      return "bg-cyan-500/10 text-cyan-600 border-cyan-500/20"
    case "risk":      return "bg-red-500/10 text-red-600 border-red-500/20"
    case "control":   return "bg-blue-500/10 text-blue-600 border-blue-500/20"
    case "framework": return "bg-purple-500/10 text-purple-600 border-purple-500/20"
    case "comment":   return "bg-violet-500/10 text-violet-600 border-violet-500/20"
    case "workspace": return "bg-teal-500/10 text-teal-600 border-teal-500/20"
    case "org":       return "bg-green-500/10 text-green-600 border-green-500/20"
    default:          return "bg-muted text-muted-foreground border-border"
  }
}

function storageBadgeClass(provider: string): string {
  switch (provider.toLowerCase()) {
    case "s3":    return "bg-amber-500/10 text-amber-600 border-amber-500/20"
    case "gcs":   return "bg-blue-500/10 text-blue-600 border-blue-500/20"
    case "azure": return "bg-sky-500/10 text-sky-600 border-sky-500/20"
    case "local": return "bg-muted text-muted-foreground border-border"
    default:      return "bg-muted text-muted-foreground border-border"
  }
}

function FileTypeIcon({ contentType, filename }: { contentType: string; filename: string }) {
  switch (fileCategory(contentType, filename)) {
    case "image":       return <FileImage className="h-3.5 w-3.5 text-green-500 shrink-0" />
    case "spreadsheet": return <FileSpreadsheet className="h-3.5 w-3.5 text-amber-500 shrink-0" />
    case "document":    return <FileText className="h-3.5 w-3.5 text-blue-500 shrink-0" />
    default:            return <File className="h-3.5 w-3.5 text-slate-400 shrink-0" />
  }
}

// ── Admin API calls ───────────────────────────────────────────────────────────

interface AdminAttachmentListResponse {
  items: AttachmentRecord[]
  total: number
  page: number
  per_page: number
}

interface AttachmentStatsResponse {
  total_files: number
  total_size_bytes: number
  infected_count: number
  pending_scan_count: number
}

interface StorageHealthResponse {
  status: "healthy" | "degraded" | "unavailable"
  provider: string
  latency_ms?: number
  message?: string
}

async function adminListAttachments(opts: {
  page: number
  per_page: number
  entity_type?: string
  virus_scan_status?: string
  storage_provider?: string
  date_from?: string
  date_to?: string
}): Promise<AdminAttachmentListResponse> {
  const params = new URLSearchParams()
  params.set("page", String(opts.page))
  params.set("per_page", String(opts.per_page))
  if (opts.entity_type)       params.set("entity_type", opts.entity_type)
  if (opts.virus_scan_status) params.set("virus_scan_status", opts.virus_scan_status)
  if (opts.storage_provider)  params.set("storage_provider", opts.storage_provider)
  if (opts.date_from)         params.set("date_from", opts.date_from)
  if (opts.date_to)           params.set("date_to", opts.date_to)

  const res = await fetchWithAuth(`/api/v1/cm/admin/attachments?${params}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to list attachments")
  return data as AdminAttachmentListResponse
}

async function adminGetAttachmentStats(): Promise<AttachmentStatsResponse> {
  const res = await fetchWithAuth("/api/v1/cm/admin/attachments/stats")
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to load stats")
  return data as AttachmentStatsResponse
}

async function adminGetStorageHealth(): Promise<StorageHealthResponse> {
  const res = await fetchWithAuth("/api/v1/at/health")
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to get storage health")
  return data as StorageHealthResponse
}

async function adminRetriggerScan(attachmentId: string): Promise<AttachmentRecord> {
  const res = await fetchWithAuth(`/api/v1/cm/admin/attachments/${attachmentId}/scan`, { method: "POST" })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to trigger scan")
  return data as AttachmentRecord
}

async function adminMarkClean(attachmentId: string): Promise<AttachmentRecord> {
  const res = await fetchWithAuth(`/api/v1/cm/admin/attachments/${attachmentId}/mark-clean`, { method: "POST" })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to mark as clean")
  return data as AttachmentRecord
}

async function adminDeleteAttachment(attachmentId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/cm/admin/attachments/${attachmentId}`, { method: "DELETE" })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || data.error?.message || "Failed to delete attachment")
  }
}

async function adminBulkDeleteInfected(): Promise<{ deleted_count: number }> {
  const res = await fetchWithAuth("/api/v1/cm/admin/attachments/bulk-delete-infected", { method: "POST" })
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || data.error?.message || "Failed to bulk delete")
  return data as { deleted_count: number }
}

// ── Sub-components ────────────────────────────────────────────────────────────

function SkeletonRow({ cols }: { cols: number }) {
  return (
    <tr className="border-b border-border">
      {Array.from({ length: cols }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <div className="h-3.5 rounded bg-muted animate-pulse" style={{ width: `${40 + (i * 19) % 45}%` }} />
        </td>
      ))}
    </tr>
  )
}

function StorageHealthBadge({ health }: { health: StorageHealthResponse | null }) {
  if (!health) return null

  const classMap: Record<string, string> = {
    healthy:     "bg-emerald-500/10 text-emerald-600 border-emerald-500/20",
    degraded:    "bg-amber-500/10 text-amber-600 border-amber-500/20",
    unavailable: "bg-red-500/10 text-red-600 border-red-500/20",
  }
  const cls = classMap[health.status] ?? "bg-muted text-muted-foreground border-border"

  return (
    <div className={`inline-flex items-center gap-2 rounded-xl border px-4 py-3 ${cls}`}>
      <Activity className="h-4 w-4 shrink-0" />
      <div className="flex flex-col">
        <span className="text-xs font-semibold capitalize leading-none">
          Storage: {health.status}
        </span>
        <span className="text-[10px] leading-snug mt-0.5">
          {health.provider}{health.latency_ms != null ? ` · ${health.latency_ms}ms` : ""}
          {health.message ? ` · ${health.message}` : ""}
        </span>
      </div>
    </div>
  )
}

interface AttachmentRowProps {
  attachment: AttachmentRecord
  onDelete: (id: string) => void
  onRetriggerScan: (id: string) => void
  onMarkClean: (id: string) => void
  actionInFlight: string | null
}

function AttachmentRow({ attachment, onDelete, onRetriggerScan, onMarkClean, actionInFlight }: AttachmentRowProps) {
  const isActing = actionInFlight === attachment.id
  const scanStatus = attachment.virus_scan_status as VirusScanStatus
  const storageProvider = attachment.storage_key?.split(":")[0] ?? "unknown"
  const borderCls = fileTypeBorderClass(attachment.content_type, attachment.original_filename)

  return (
    <tr className={`border-b border-border hover:bg-muted/20 transition-colors border-l-[3px] ${borderCls}`}>
      {/* Filename */}
      <td className="px-4 py-3 max-w-[200px]">
        <div className="flex items-center gap-2">
          <FileTypeIcon contentType={attachment.content_type} filename={attachment.original_filename} />
          <div className="min-w-0">
            <p className="text-xs font-medium text-foreground truncate" title={attachment.original_filename}>
              {attachment.original_filename}
            </p>
            <p className="text-[10px] text-muted-foreground truncate" title={attachment.content_type}>
              {attachment.content_type}
            </p>
          </div>
        </div>
      </td>

      {/* Uploader */}
      <td className="px-4 py-3 whitespace-nowrap">
        <div className="flex flex-col">
          <span className="text-xs font-medium text-foreground">
            {attachment.uploader_display_name ?? "Unknown"}
          </span>
          <span className="font-mono text-[10px] text-muted-foreground" title={attachment.uploaded_by}>
            {attachment.uploaded_by.slice(0, 8)}…
          </span>
        </div>
      </td>

      {/* Entity */}
      <td className="px-4 py-3 whitespace-nowrap">
        <div className="flex flex-col gap-0.5">
          <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium w-fit ${entityTypeBadgeClass(attachment.entity_type)}`}>
            {attachment.entity_type}
          </span>
          <span className="font-mono text-[10px] text-muted-foreground" title={attachment.entity_id}>
            {attachment.entity_id.slice(0, 8)}…
          </span>
        </div>
      </td>

      {/* Size */}
      <td className="px-4 py-3 whitespace-nowrap">
        <span className="text-xs text-foreground">{formatBytes(attachment.file_size_bytes)}</span>
      </td>

      {/* Virus scan status */}
      <td className="px-4 py-3 whitespace-nowrap">
        <span className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium ${virusScanBadgeClass(scanStatus)}`}>
          {virusScanIcon(scanStatus)}
          {scanStatus}
        </span>
      </td>

      {/* Storage */}
      <td className="px-4 py-3 whitespace-nowrap">
        <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium ${storageBadgeClass(storageProvider)}`}>
          {storageProvider}
        </span>
      </td>

      {/* Uploaded */}
      <td className="px-4 py-3 whitespace-nowrap">
        <span className="text-xs text-muted-foreground">
          {new Date(attachment.created_at).toLocaleDateString()}{" "}
          <span className="text-[10px]">
            {new Date(attachment.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </span>
        </span>
      </td>

      {/* Actions */}
      <td className="px-4 py-3 whitespace-nowrap">
        <div className="flex items-center gap-1.5 flex-wrap">
          {(scanStatus === "pending" || scanStatus === "error") && (
            <Button
              variant="outline"
              size="sm"
              className="h-7 gap-1 text-xs"
              disabled={isActing}
              onClick={() => onRetriggerScan(attachment.id)}
              title="Re-trigger virus scan"
            >
              <RotateCcw className="h-3 w-3" />
              Re-scan
            </Button>
          )}
          {scanStatus === "infected" && (
            <Button
              variant="outline"
              size="sm"
              className="h-7 gap-1 text-xs text-emerald-600 hover:bg-emerald-500/10"
              disabled={isActing}
              onClick={() => onMarkClean(attachment.id)}
              title="Mark this file as clean (override)"
            >
              <ShieldCheck className="h-3 w-3" />
              Mark Clean
            </Button>
          )}
          <Button
            variant="outline"
            size="sm"
            className="h-7 gap-1 text-xs text-destructive hover:bg-destructive/10 hover:text-destructive"
            disabled={isActing}
            onClick={() => onDelete(attachment.id)}
          >
            <Trash2 className="h-3 w-3" />
            Delete
          </Button>
        </div>
      </td>
    </tr>
  )
}

// ── Stats bar ─────────────────────────────────────────────────────────────────

function StatsBar({
  stats,
  loading,
  health,
  healthLoading,
  attachments,
}: {
  stats: AttachmentStatsResponse | null
  loading: boolean
  health: StorageHealthResponse | null
  healthLoading: boolean
  attachments: AttachmentRecord[]
}) {
  if (loading) {
    return (
      <div className="flex gap-3 flex-wrap">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="relative flex items-center gap-3 rounded-xl border border-border bg-card px-4 py-3 animate-pulse">
            <div className="shrink-0 rounded-lg p-2 bg-muted h-8 w-8" />
            <div className="flex flex-col gap-1">
              <div className="h-5 w-10 rounded bg-muted" />
              <div className="h-2.5 w-16 rounded bg-muted" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  const documentCount = attachments.filter(a => fileCategory(a.content_type, a.original_filename) === "document").length
  const imageCount    = attachments.filter(a => fileCategory(a.content_type, a.original_filename) === "image").length

  return (
    <div className="flex gap-3 flex-wrap items-center">
      {stats && (
        <>
          {[
            {
              label: "Total Files",
              value: stats.total_files.toLocaleString(),
              borderCls: "border-l-sky-500",
              numCls: "text-foreground",
              icon: <Database className="h-4 w-4 text-sky-500" />,
            },
            {
              label: "Documents (page)",
              value: documentCount.toLocaleString(),
              borderCls: "border-l-blue-500",
              numCls: "text-blue-600",
              icon: <FileText className="h-4 w-4 text-blue-500" />,
            },
            {
              label: "Images (page)",
              value: imageCount.toLocaleString(),
              borderCls: "border-l-green-500",
              numCls: "text-green-600",
              icon: <FileImage className="h-4 w-4 text-green-500" />,
            },
            {
              label: "Total Size",
              value: formatBytes(stats.total_size_bytes),
              borderCls: "border-l-amber-500",
              numCls: "text-foreground",
              icon: <HardDrive className="h-4 w-4 text-amber-500" />,
            },
          ].map((s) => (
            <div key={s.label} className={`relative flex items-center gap-3 rounded-xl border border-l-[3px] ${s.borderCls} bg-card px-4 py-3`}>
              <div className="shrink-0 rounded-lg p-2 bg-muted">
                {s.icon}
              </div>
              <div className="flex flex-col">
                <span className={`text-2xl font-bold tabular-nums leading-none ${s.numCls}`}>{s.value}</span>
                <span className="text-[11px] text-muted-foreground mt-0.5 block truncate">{s.label}</span>
              </div>
            </div>
          ))}
        </>
      )}
      {!healthLoading && <StorageHealthBadge health={health} />}
    </div>
  )
}

// ── GDPR Compliance Panel ─────────────────────────────────────────────────────

function GdprCompliancePanel() {
  const [userId, setUserId] = useState("")
  const [result, setResult] = useState<GdprAttachmentDeleteResult | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [confirmDelete, setConfirmDelete] = useState(false)

  async function handleDelete() {
    if (!userId.trim()) return
    setDeleting(true)
    setError(null)
    setConfirmDelete(false)
    try {
      const data = await gdprDeleteUserAttachments(userId.trim())
      setResult(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete user data")
    } finally {
      setDeleting(false)
    }
  }

  return (
    <div className="rounded-xl border border-border bg-card px-4 py-3 space-y-3">
      <div className="flex items-center gap-2">
        <Shield className="h-4 w-4 text-amber-500 shrink-0" />
        <span className="text-sm font-semibold text-foreground">GDPR Compliance</span>
      </div>
      <p className="text-xs text-muted-foreground">
        Delete all attachment data for a specific user (Article 17 — Right to Erasure).
      </p>

      <div className="flex items-end gap-2">
        <div className="flex-1">
          <label className="text-xs font-medium text-muted-foreground mb-1 block">User ID</label>
          <Input
            placeholder="Enter user UUID..."
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            className="h-9 text-sm font-mono"
          />
        </div>
        {!confirmDelete ? (
          <Button
            size="sm"
            variant="destructive"
            className="h-9 gap-1.5 text-xs"
            onClick={() => { if (userId.trim()) setConfirmDelete(true) }}
            disabled={deleting || !userId.trim()}
          >
            <Trash2 className="h-3 w-3" />
            Delete All Attachments
          </Button>
        ) : (
          <div className="flex gap-1.5">
            <Button
              size="sm"
              variant="destructive"
              className="h-9 text-xs"
              onClick={handleDelete}
              disabled={deleting}
            >
              {deleting ? <Loader2 className="h-3 w-3 animate-spin" /> : "Confirm Delete"}
            </Button>
            <Button
              size="sm"
              variant="ghost"
              className="h-9 text-xs"
              onClick={() => setConfirmDelete(false)}
            >
              Cancel
            </Button>
          </div>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2">
          <AlertCircle className="h-3.5 w-3.5 text-red-500 shrink-0" />
          <p className="text-xs text-red-500">{error}</p>
        </div>
      )}

      {confirmDelete && (
        <div className="flex items-center gap-2 rounded-lg border border-amber-500/30 bg-amber-500/5 px-3 py-2">
          <AlertCircle className="h-3.5 w-3.5 text-amber-500 shrink-0" />
          <p className="text-xs text-amber-700 dark:text-amber-400">
            This will soft-delete all attachments uploaded by this user. Storage files will be removed.
          </p>
        </div>
      )}

      {result && (
        <div className="flex items-center gap-2 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2">
          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
          <p className="text-xs text-emerald-600">
            Deleted {result.attachments_deleted} attachment{result.attachments_deleted !== 1 ? "s" : ""} for user {result.user_id.slice(0, 8)}...
          </p>
        </div>
      )}
    </div>
  )
}

// ── Active filter chips ───────────────────────────────────────────────────────

interface ActiveChip {
  label: string
  color: "blue" | "green" | "amber" | "red" | "default"
  onDismiss: () => void
}

function ActiveFilterChips({ chips, onClearAll }: { chips: ActiveChip[]; onClearAll: () => void }) {
  if (chips.length === 0) return null

  const colorMap: Record<ActiveChip["color"], string> = {
    blue:    "border-blue-500/30 bg-blue-500/10 text-blue-700 dark:text-blue-400",
    green:   "border-green-500/30 bg-green-500/10 text-green-700 dark:text-green-400",
    amber:   "border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-400",
    red:     "border-red-500/30 bg-red-500/10 text-red-700 dark:text-red-400",
    default: "border-border bg-muted text-foreground",
  }

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {chips.map((chip) => (
        <span
          key={chip.label}
          className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium ${colorMap[chip.color]}`}
        >
          {chip.label}
          <button onClick={chip.onDismiss} className="opacity-60 hover:opacity-100 transition-opacity">
            <X className="h-2.5 w-2.5" />
          </button>
        </span>
      ))}
      {chips.length > 1 && (
        <button
          onClick={onClearAll}
          className="text-xs text-muted-foreground hover:text-foreground transition-colors underline underline-offset-2"
        >
          Clear all
        </button>
      )}
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function AdminAttachmentsPage() {
  // Filters
  const [entityTypeInput, setEntityTypeInput]           = useState("")
  const [scanStatusInput, setScanStatusInput]           = useState("")
  const [storageProviderInput, setStorageProviderInput] = useState("")
  const [dateFromInput, setDateFromInput]               = useState("")
  const [dateToInput, setDateToInput]                   = useState("")

  // Applied filters
  const [appliedFilters, setAppliedFilters] = useState({
    entity_type:       "",
    virus_scan_status: "",
    storage_provider:  "",
    date_from:         "",
    date_to:           "",
  })

  // Data
  const [attachments, setAttachments] = useState<AttachmentRecord[]>([])
  const [total, setTotal]             = useState(0)
  const [page, setPage]               = useState(1)
  const [loading, setLoading]         = useState(true)
  const [error, setError]             = useState<string | null>(null)

  // Stats
  const [stats, setStats]               = useState<AttachmentStatsResponse | null>(null)
  const [statsLoading, setStatsLoading] = useState(true)

  // Storage health
  const [health, setHealth]               = useState<StorageHealthResponse | null>(null)
  const [healthLoading, setHealthLoading] = useState(true)

  // Actions
  const [actionInFlight, setActionInFlight]       = useState<string | null>(null)
  const [actionError, setActionError]             = useState<string | null>(null)
  const [pendingDelete, setPendingDelete]         = useState<string | null>(null)
  const [bulkDeleteConfirm, setBulkDeleteConfirm] = useState(false)
  const [bulkResult, setBulkResult]               = useState<string | null>(null)

  // Load stats and health on mount
  useEffect(() => {
    adminGetAttachmentStats()
      .then(setStats)
      .catch(() => {})
      .finally(() => setStatsLoading(false))

    adminGetStorageHealth()
      .then(setHealth)
      .catch(() => {})
      .finally(() => setHealthLoading(false))
  }, [])

  const fetchAttachments = useCallback(
    async (pageIndex: number, filters: typeof appliedFilters) => {
      setLoading(true)
      setError(null)
      try {
        const result = await adminListAttachments({
          page: pageIndex,
          per_page: PAGE_SIZE,
          entity_type:       filters.entity_type       || undefined,
          virus_scan_status: filters.virus_scan_status || undefined,
          storage_provider:  filters.storage_provider  || undefined,
          date_from:         filters.date_from         || undefined,
          date_to:           filters.date_to           || undefined,
        })
        setAttachments(result.items)
        setTotal(result.total)
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load attachments")
      } finally {
        setLoading(false)
      }
    },
    []
  )

  useEffect(() => {
    fetchAttachments(page, appliedFilters)
  }, [page, appliedFilters, fetchAttachments])

  function handleApplyFilters() {
    setPage(1)
    setAppliedFilters({
      entity_type:       entityTypeInput,
      virus_scan_status: scanStatusInput,
      storage_provider:  storageProviderInput,
      date_from:         dateFromInput,
      date_to:           dateToInput,
    })
  }

  function handleClearFilters() {
    setEntityTypeInput("")
    setScanStatusInput("")
    setStorageProviderInput("")
    setDateFromInput("")
    setDateToInput("")
    setPage(1)
    setAppliedFilters({ entity_type: "", virus_scan_status: "", storage_provider: "", date_from: "", date_to: "" })
  }

  async function handleDelete(id: string) {
    setActionInFlight(id)
    setActionError(null)
    setPendingDelete(null)
    try {
      await adminDeleteAttachment(id)
      setAttachments((prev) => prev.filter((a) => a.id !== id))
      setTotal((t) => t - 1)
      adminGetAttachmentStats().then(setStats).catch(() => {})
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Failed to delete attachment")
    } finally {
      setActionInFlight(null)
    }
  }

  async function handleRetriggerScan(id: string) {
    setActionInFlight(id)
    setActionError(null)
    try {
      const updated = await adminRetriggerScan(id)
      setAttachments((prev) => prev.map((a) => (a.id === id ? updated : a)))
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Failed to re-trigger scan")
    } finally {
      setActionInFlight(null)
    }
  }

  async function handleMarkClean(id: string) {
    setActionInFlight(id)
    setActionError(null)
    try {
      const updated = await adminMarkClean(id)
      setAttachments((prev) => prev.map((a) => (a.id === id ? updated : a)))
      adminGetAttachmentStats().then(setStats).catch(() => {})
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Failed to mark as clean")
    } finally {
      setActionInFlight(null)
    }
  }

  async function handleBulkDeleteInfected() {
    setBulkDeleteConfirm(false)
    setActionError(null)
    setBulkResult(null)
    try {
      const result = await adminBulkDeleteInfected()
      setBulkResult(`Deleted ${result.deleted_count} infected file${result.deleted_count !== 1 ? "s" : ""}.`)
      fetchAttachments(1, appliedFilters)
      setPage(1)
      adminGetAttachmentStats().then(setStats).catch(() => {})
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Failed to bulk delete infected files")
    }
  }

  const totalPages    = Math.ceil(total / PAGE_SIZE)
  const rangeStart    = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1
  const rangeEnd      = Math.min(page * PAGE_SIZE, total)
  const infectedCount = stats?.infected_count ?? 0

  // Active filter chips
  const activeChips: ActiveChip[] = []
  if (appliedFilters.entity_type) activeChips.push({ label: `Entity: ${appliedFilters.entity_type}`, color: "blue", onDismiss: () => { setEntityTypeInput(""); setAppliedFilters(f => ({ ...f, entity_type: "" })); setPage(1) } })
  if (appliedFilters.virus_scan_status) {
    const scanColor: ActiveChip["color"] = appliedFilters.virus_scan_status === "infected" ? "red" : appliedFilters.virus_scan_status === "clean" ? "green" : "amber"
    activeChips.push({ label: `Scan: ${appliedFilters.virus_scan_status}`, color: scanColor, onDismiss: () => { setScanStatusInput(""); setAppliedFilters(f => ({ ...f, virus_scan_status: "" })); setPage(1) } })
  }
  if (appliedFilters.storage_provider) activeChips.push({ label: `Storage: ${appliedFilters.storage_provider.toUpperCase()}`, color: "amber", onDismiss: () => { setStorageProviderInput(""); setAppliedFilters(f => ({ ...f, storage_provider: "" })); setPage(1) } })
  if (appliedFilters.date_from) activeChips.push({ label: `From: ${appliedFilters.date_from}`, color: "default", onDismiss: () => { setDateFromInput(""); setAppliedFilters(f => ({ ...f, date_from: "" })); setPage(1) } })
  if (appliedFilters.date_to) activeChips.push({ label: `To: ${appliedFilters.date_to}`, color: "default", onDismiss: () => { setDateToInput(""); setAppliedFilters(f => ({ ...f, date_to: "" })); setPage(1) } })

  const hasActiveFilters = activeChips.length > 0

  return (
    <div className="space-y-6">
      {/* ── Header ────────────────────────────────────────────────────── */}
      <div className="flex items-start gap-4">
        <div className="rounded-xl bg-sky-500/10 p-3 shrink-0">
          <Paperclip className="h-6 w-6 text-sky-500" />
        </div>
        <div className="flex flex-col gap-1 flex-1">
          <h2 className="text-2xl font-semibold text-foreground">Attachments</h2>
          <p className="text-sm text-muted-foreground">
            Monitor all uploaded files, virus scan status, and storage health across the platform.
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {infectedCount > 0 && (
            <Button
              variant="destructive"
              size="sm"
              className="h-8 gap-1.5 text-xs"
              onClick={() => setBulkDeleteConfirm(true)}
            >
              <Trash2 className="h-3.5 w-3.5" />
              Delete {infectedCount} Infected
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0 rounded-lg"
            onClick={() => {
              fetchAttachments(page, appliedFilters)
              adminGetAttachmentStats().then(setStats).catch(() => {})
              adminGetStorageHealth().then(setHealth).catch(() => {})
            }}
            title="Refresh"
          >
            <RefreshCw className="h-4 w-4 text-muted-foreground" />
          </Button>
        </div>
      </div>

      {/* ── Stats ─────────────────────────────────────────────────────── */}
      <StatsBar
        stats={stats}
        loading={statsLoading}
        health={health}
        healthLoading={healthLoading}
        attachments={attachments}
      />

      {/* ── GDPR Compliance ───────────────────────────────────────────── */}
      <GdprCompliancePanel />

      {/* ── Filter bar ────────────────────────────────────────────────── */}
      <div className="rounded-xl border border-border bg-card px-4 py-3 space-y-3">
        <div className="flex flex-wrap items-end gap-3">
          {/* Entity type */}
          <div className="min-w-[160px]">
            <select
              value={entityTypeInput}
              onChange={(e) => setEntityTypeInput(e.target.value)}
              className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="">All entity types</option>
              {ENTITY_TYPES.map((t) => (
                <option key={t} value={t}>{t.replace(/_/g, " ")}</option>
              ))}
            </select>
          </div>

          {/* Virus scan status */}
          <div className="min-w-[160px]">
            <select
              value={scanStatusInput}
              onChange={(e) => setScanStatusInput(e.target.value)}
              className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="">All scan statuses</option>
              {VIRUS_SCAN_STATUSES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          {/* Storage provider */}
          <div className="min-w-[150px]">
            <select
              value={storageProviderInput}
              onChange={(e) => setStorageProviderInput(e.target.value)}
              className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="">All providers</option>
              <option value="s3">S3</option>
              <option value="gcs">GCS</option>
              <option value="azure">Azure</option>
              <option value="local">Local</option>
            </select>
          </div>

          {/* Date range */}
          <div className="flex items-center gap-1.5 min-w-[260px]">
            <Input
              type="date"
              value={dateFromInput}
              onChange={(e) => setDateFromInput(e.target.value)}
              className="h-9 text-sm"
              title="From date"
            />
            <span className="text-xs text-muted-foreground">–</span>
            <Input
              type="date"
              value={dateToInput}
              onChange={(e) => setDateToInput(e.target.value)}
              className="h-9 text-sm"
              title="To date"
            />
          </div>

          <Button size="sm" className="h-9 shrink-0" onClick={handleApplyFilters}>
            Apply
          </Button>
          {hasActiveFilters && (
            <Button
              size="sm"
              variant="ghost"
              className="h-9 shrink-0 gap-1 text-muted-foreground"
              onClick={handleClearFilters}
            >
              <X className="h-3.5 w-3.5" />
              Clear all
            </Button>
          )}
        </div>

        <ActiveFilterChips chips={activeChips} onClearAll={handleClearFilters} />
      </div>

      {/* ── Error banners ─────────────────────────────────────────────── */}
      {error && (
        <div className="flex items-center gap-3 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3">
          <AlertCircle className="h-4 w-4 shrink-0 text-red-500" />
          <p className="text-sm text-red-500">{error}</p>
        </div>
      )}
      {actionError && (
        <div className="flex items-center gap-3 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3">
          <AlertCircle className="h-4 w-4 shrink-0 text-red-500" />
          <p className="text-sm text-red-500">{actionError}</p>
          <button className="ml-auto text-xs text-red-500 underline" onClick={() => setActionError(null)}>Dismiss</button>
        </div>
      )}
      {bulkResult && (
        <div className="flex items-center gap-3 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3">
          <ShieldCheck className="h-4 w-4 shrink-0 text-emerald-500" />
          <p className="text-sm text-emerald-600">{bulkResult}</p>
          <button className="ml-auto text-xs text-emerald-600 underline" onClick={() => setBulkResult(null)}>Dismiss</button>
        </div>
      )}

      {/* ── Confirm banners ────────────────────────────────────────────── */}
      {pendingDelete && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 px-4 py-3 flex items-center gap-3">
          <AlertCircle className="h-4 w-4 shrink-0 text-amber-500" />
          <p className="text-sm text-amber-700 dark:text-amber-400 flex-1">
            Permanently delete this file from storage? This cannot be undone.
          </p>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="destructive"
              className="h-7 text-xs"
              onClick={() => handleDelete(pendingDelete)}
            >
              Delete permanently
            </Button>
            <Button
              size="sm"
              variant="ghost"
              className="h-7 text-xs"
              onClick={() => setPendingDelete(null)}
            >
              Cancel
            </Button>
          </div>
        </div>
      )}

      {bulkDeleteConfirm && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/5 px-4 py-3 flex items-center gap-3">
          <ShieldAlert className="h-4 w-4 shrink-0 text-red-500" />
          <p className="text-sm text-red-700 dark:text-red-400 flex-1">
            Bulk delete all {infectedCount} infected file{infectedCount !== 1 ? "s" : ""}? This permanently removes them from storage and cannot be undone.
          </p>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="destructive"
              className="h-7 text-xs"
              onClick={handleBulkDeleteInfected}
            >
              Delete all infected
            </Button>
            <Button
              size="sm"
              variant="ghost"
              className="h-7 text-xs"
              onClick={() => setBulkDeleteConfirm(false)}
            >
              Cancel
            </Button>
          </div>
        </div>
      )}

      {/* ── Table ─────────────────────────────────────────────────────── */}
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <div className="px-4 py-3 border-b border-border flex items-center justify-between">
          <div>
            <p className="text-base font-semibold text-foreground">Attachments</p>
            {!loading && !error && (
              <p className="text-xs text-muted-foreground mt-0.5">
                {total === 0
                  ? "No attachments found"
                  : `Showing ${rangeStart}–${rangeEnd} of ${total.toLocaleString()}`}
              </p>
            )}
          </div>
          {/* Legend */}
          <div className="hidden sm:flex items-center gap-3 text-[10px] text-muted-foreground">
            <span className="flex items-center gap-1"><span className="inline-block h-3 w-0.5 rounded bg-blue-500" />Document</span>
            <span className="flex items-center gap-1"><span className="inline-block h-3 w-0.5 rounded bg-green-500" />Image</span>
            <span className="flex items-center gap-1"><span className="inline-block h-3 w-0.5 rounded bg-amber-500" />Spreadsheet</span>
            <span className="flex items-center gap-1"><span className="inline-block h-3 w-0.5 rounded bg-slate-400" />Other</span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/30">
                {["File", "Uploader", "Entity", "Size", "Virus Scan", "Storage", "Uploaded", "Actions"].map((h) => (
                  <th
                    key={h}
                    className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground whitespace-nowrap"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 10 }).map((_, i) => <SkeletonRow key={i} cols={8} />)
              ) : attachments.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-16 text-center">
                    <div className="flex flex-col items-center gap-3">
                      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-muted">
                        <Paperclip className="h-6 w-6 text-muted-foreground" />
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm font-medium text-foreground">No attachments found</p>
                        <p className="text-xs text-muted-foreground">
                          Try adjusting your filters.
                        </p>
                      </div>
                    </div>
                  </td>
                </tr>
              ) : (
                attachments.map((attachment) => (
                  <AttachmentRow
                    key={attachment.id}
                    attachment={attachment}
                    onDelete={(id) => setPendingDelete(id)}
                    onRetriggerScan={handleRetriggerScan}
                    onMarkClean={handleMarkClean}
                    actionInFlight={actionInFlight}
                  />
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {!loading && total > 0 && (
          <div className="flex items-center justify-between border-t border-border px-4 py-3">
            <p className="text-xs text-muted-foreground">
              Showing {rangeStart}–{rangeEnd} of {total.toLocaleString()} attachments
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                className="h-8 gap-1"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                <ChevronLeft className="h-3.5 w-3.5" />
                Prev
              </Button>
              <span className="text-xs text-muted-foreground px-1">
                Page {page} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                className="h-8 gap-1"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
                <ChevronRight className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
