"use client"

import { useEffect, useState, useCallback, useRef, useMemo } from "react"
import { Button } from "@kcontrol/ui"
import {
  RefreshCw,
  Paperclip,
  Download,
  Trash2,
  Upload,
  X,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Pencil,
  Copy,
  Check,
  Eye,
  EyeOff,
} from "lucide-react"
import {
  listAttachments,
  uploadAttachment,
  getDownloadUrl,
  deleteAttachment,
  updateAttachmentDescription,
  updateAttachmentAuditorAccess,
} from "@/lib/api/attachments"
import type { AttachmentRecord } from "@/lib/types/attachments"

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
}

function formatDate(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
  } catch {
    return dateStr
  }
}

function getFileEmoji(contentType: string, filename: string): string {
  const ext = filename.split(".").pop()?.toLowerCase() ?? ""
  if (contentType.startsWith("image/") || ["png", "jpg", "jpeg", "gif", "webp", "svg"].includes(ext)) return "🖼️"
  if (contentType === "application/pdf" || ext === "pdf") return "📄"
  if (["doc", "docx"].includes(ext) || contentType.includes("word")) return "📝"
  if (["xls", "xlsx"].includes(ext) || contentType.includes("spreadsheet") || contentType.includes("excel")) return "📊"
  if (ext === "csv") return "📊"
  if (["ppt", "pptx"].includes(ext) || contentType.includes("presentation")) return "📽️"
  if (["txt", "md"].includes(ext) || contentType === "text/plain") return "📃"
  if (["mp4", "mov", "avi", "mkv", "webm"].includes(ext) || contentType.startsWith("video/")) return "🎬"
  if (["zip", "tar", "gz", "7z", "rar"].includes(ext) || contentType.includes("zip") || contentType.includes("tar") || contentType.includes("gzip")) return "🗜️"
  if (["json", "yaml", "yml", "xml", "toml"].includes(ext) || contentType.includes("json") || contentType.includes("xml")) return "🔧"
  if (["js", "ts", "py", "go", "rs", "java", "sh", "c", "cpp"].includes(ext) || contentType.startsWith("text/")) return "🔧"
  return "📎"
}

function isImageType(contentType: string, filename: string): boolean {
  const ext = filename.split(".").pop()?.toLowerCase() ?? ""
  return contentType.startsWith("image/") || ["png", "jpg", "jpeg", "gif", "webp"].includes(ext)
}

// ─────────────────────────────────────────────────────────────────────────────
// Virus Scan Badge
// ─────────────────────────────────────────────────────────────────────────────

function VirusScanBadge({ status }: { status: AttachmentRecord["virus_scan_status"] }) {
  const map: Record<AttachmentRecord["virus_scan_status"], { label: string; cls: string; icon: React.ReactNode }> = {
    pending: {
      label: "Scan pending...",
      cls: "text-amber-600 bg-amber-500/10 border-amber-500/20",
      icon: <RefreshCw className="h-2.5 w-2.5 animate-spin" aria-hidden="true" />,
    },
    clean: {
      label: "Clean",
      cls: "text-emerald-600 bg-emerald-500/10 border-emerald-500/20",
      icon: <CheckCircle2 className="h-2.5 w-2.5" aria-hidden="true" />,
    },
    infected: {
      label: "Infected",
      cls: "text-red-600 bg-red-500/10 border-red-500/20",
      icon: <AlertTriangle className="h-2.5 w-2.5" aria-hidden="true" />,
    },
    error: {
      label: "Scan Error",
      cls: "text-orange-600 bg-orange-500/10 border-orange-500/20",
      icon: <AlertTriangle className="h-2.5 w-2.5" aria-hidden="true" />,
    },
    skipped: {
      label: "Skipped",
      cls: "text-muted-foreground bg-muted border-border",
      icon: null,
    },
  }
  const meta = map[status] ?? map.skipped
  return (
    <span
      className={`inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded border text-[10px] font-medium ${meta.cls}`}
      aria-label={`Virus scan status: ${meta.label}`}
    >
      {meta.icon}
      {meta.label}
    </span>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Image Thumbnail
// ─────────────────────────────────────────────────────────────────────────────

function ImageThumbnail({ attachment }: { attachment: AttachmentRecord }) {
  const [url, setUrl] = useState<string | null>(null)
  const [loaded, setLoaded] = useState(false)
  const [error, setError] = useState(false)

  useEffect(() => {
    let cancelled = false
    getDownloadUrl(attachment.id)
      .then((res) => { if (!cancelled) setUrl(res.url) })
      .catch(() => { if (!cancelled) setError(true) })
    return () => { cancelled = true }
  }, [attachment.id])

  if (error) {
    return (
      <div className="mt-2 flex items-center gap-1.5 rounded-md border border-border bg-muted/50 px-3 py-2 w-fit">
        <span className="text-xs text-muted-foreground">Preview unavailable</span>
      </div>
    )
  }

  if (!url) return null

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="block mt-2 rounded-md overflow-hidden border border-border w-fit"
      aria-label={`Preview ${attachment.original_filename}`}
    >
      <img
        src={url}
        alt={attachment.original_filename}
        loading="lazy"
        className={`max-h-24 max-w-[200px] object-cover transition-opacity ${loaded ? "opacity-100" : "opacity-0"}`}
        onLoad={() => setLoaded(true)}
        onError={() => setError(true)}
      />
    </a>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Attachment Row
// ─────────────────────────────────────────────────────────────────────────────

interface AttachmentRowProps {
  attachment: AttachmentRecord
  currentUserId: string
  isWorkspaceAdmin: boolean
  showStorageKey?: boolean
  onDeleted: () => void
  onDescriptionUpdated: () => void
}

function AttachmentRow({
  attachment,
  currentUserId,
  isWorkspaceAdmin,
  showStorageKey = false,
  onDeleted,
  onDescriptionUpdated,
}: AttachmentRowProps) {
  const [downloading, setDownloading] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [editingDesc, setEditingDesc] = useState(false)
  const [descValue, setDescValue] = useState(attachment.description ?? "")
  const [savingDesc, setSavingDesc] = useState(false)
  const [copiedKey, setCopiedKey] = useState(false)
  const [auditAccess, setAuditAccess] = useState(attachment.auditor_access ?? false)
  const [togglingAudit, setTogglingAudit] = useState(false)
  const descInputRef = useRef<HTMLInputElement>(null)

  const canDelete = attachment.uploaded_by === currentUserId || isWorkspaceAdmin

  async function toggleAuditAccess() {
    setTogglingAudit(true)
    try {
      await updateAttachmentAuditorAccess(attachment.id, !auditAccess)
      setAuditAccess(!auditAccess)
    } catch {
      // revert on failure
    } finally {
      setTogglingAudit(false)
    }
  }

  useEffect(() => {
    if (editingDesc) descInputRef.current?.focus()
  }, [editingDesc])

  const [actionError, setActionError] = useState<string | null>(null)

  const handleDownload = useCallback(async () => {
    setDownloading(true)
    setActionError(null)
    try {
      const res = await getDownloadUrl(attachment.id)
      const a = document.createElement("a")
      a.href = res.url
      a.target = "_blank"
      a.rel = "noopener noreferrer"
      a.download = res.filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Failed to download file")
    } finally {
      setDownloading(false)
    }
  }, [attachment.id])

  const handleDelete = useCallback(async () => {
    setDeleting(true)
    setActionError(null)
    try {
      await deleteAttachment(attachment.id)
      setDeleteConfirm(false)
      onDeleted()
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Failed to delete file")
    } finally {
      setDeleting(false)
    }
  }, [attachment.id, onDeleted])

  const handleSaveDesc = useCallback(async () => {
    setSavingDesc(true)
    setActionError(null)
    try {
      await updateAttachmentDescription(attachment.id, descValue.trim())
      setEditingDesc(false)
      onDescriptionUpdated()
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Failed to save description")
    } finally {
      setSavingDesc(false)
    }
  }, [attachment.id, descValue, onDescriptionUpdated])

  const handleCopyKey = useCallback(() => {
    try {
      navigator.clipboard.writeText((attachment as AttachmentRecord & { storage_key?: string }).storage_key ?? attachment.id)
      setCopiedKey(true)
      const timer = setTimeout(() => setCopiedKey(false), 2000)
      return () => clearTimeout(timer)
    } catch {
      // ignore
    }
  }, [attachment])

  const showImage = isImageType(attachment.content_type, attachment.original_filename)
    && attachment.virus_scan_status === "clean"

  return (
    <div className="flex items-start gap-3 px-4 py-3 rounded-xl border border-border bg-card hover:bg-muted/20 transition-colors group">
      {/* File type emoji */}
      <span
        className="text-xl mt-0.5 shrink-0 leading-none select-none"
        aria-hidden="true"
        title={attachment.content_type}
      >
        {getFileEmoji(attachment.content_type, attachment.original_filename)}
      </span>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-medium text-foreground truncate max-w-xs">
            {attachment.original_filename}
          </span>
          <VirusScanBadge status={attachment.virus_scan_status} />
          {auditAccess && (
            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-500/10 text-blue-600 border border-blue-500/20">
              <Eye className="h-3 w-3" />
              Audit
            </span>
          )}
        </div>

        <div className="flex items-center gap-3 mt-0.5 text-xs text-muted-foreground flex-wrap">
          <span aria-label={`File size: ${formatBytes(attachment.file_size_bytes)}`}>
            {formatBytes(attachment.file_size_bytes)}
          </span>
          <span>by {attachment.uploader_display_name ?? "Unknown"}</span>
          <span>{formatDate(attachment.created_at)}</span>
          {showStorageKey && isWorkspaceAdmin && (
            <button
              onClick={handleCopyKey}
              className="flex items-center gap-1 hover:text-foreground transition-colors"
              aria-label="Copy storage path"
            >
              {copiedKey ? (
                <><Check className="h-2.5 w-2.5 text-emerald-500" /> Copied</>
              ) : (
                <><Copy className="h-2.5 w-2.5" /> Copy storage path</>
              )}
            </button>
          )}
        </div>

        {/* Image preview */}
        {showImage && <ImageThumbnail attachment={attachment} />}

        {/* Description */}
        {editingDesc ? (
          <div className="mt-2 flex items-center gap-2">
            <input
              ref={descInputRef}
              type="text"
              className="flex-1 h-7 px-2 text-xs rounded border border-border bg-background focus:outline-none focus:ring-1 focus:ring-ring"
              value={descValue}
              onChange={(e) => setDescValue(e.target.value)}
              placeholder="Add a description…"
              aria-label="Attachment description"
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSaveDesc()
                if (e.key === "Escape") setEditingDesc(false)
              }}
            />
            <Button
              size="sm"
              className="h-7 text-xs px-2"
              disabled={savingDesc}
              onClick={handleSaveDesc}
              aria-label="Save description"
            >
              Save
            </Button>
            <Button
              size="sm"
              variant="ghost"
              className="h-7 text-xs px-2"
              onClick={() => setEditingDesc(false)}
              aria-label="Cancel description edit"
            >
              Cancel
            </Button>
          </div>
        ) : attachment.description ? (
          <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
            {attachment.description}
            <button
              onClick={() => setEditingDesc(true)}
              className="opacity-0 group-hover:opacity-100 transition-opacity"
              aria-label="Edit description"
            >
              <Pencil className="h-2.5 w-2.5 text-muted-foreground hover:text-foreground" aria-hidden="true" />
            </button>
          </p>
        ) : (
          <button
            onClick={() => setEditingDesc(true)}
            className="text-xs text-muted-foreground hover:text-foreground mt-0.5 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1"
            aria-label="Add description"
          >
            <Pencil className="h-2.5 w-2.5" aria-hidden="true" /> Add description
          </button>
        )}

        {/* Action error */}
        {actionError && (
          <div className="mt-2 flex items-center gap-2 text-xs text-destructive" role="alert" aria-live="polite">
            <span>{actionError}</span>
            <button onClick={() => setActionError(null)} className="underline hover:no-underline" aria-label="Dismiss error">Dismiss</button>
          </div>
        )}

        {/* Delete confirm */}
        {deleteConfirm && (
          <div className="mt-2 flex items-center gap-2 text-sm" role="alert">
            <span className="text-muted-foreground text-xs">Delete this file?</span>
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="text-destructive text-xs font-medium hover:underline"
              aria-label="Confirm delete attachment"
            >
              {deleting ? "Deleting…" : "Delete"}
            </button>
            <button
              onClick={() => setDeleteConfirm(false)}
              className="text-muted-foreground text-xs hover:underline"
              aria-label="Cancel delete"
            >
              Cancel
            </button>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1 shrink-0">
        {attachment.virus_scan_status !== "infected" && (
          <button
            onClick={handleDownload}
            disabled={downloading}
            className="p-1.5 rounded hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
            aria-label={`Download ${attachment.original_filename}`}
          >
            {downloading
              ? <RefreshCw className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
              : <Download className="h-3.5 w-3.5" aria-hidden="true" />}
          </button>
        )}
        {/* Publish for Audit toggle */}
        <button
          onClick={toggleAuditAccess}
          disabled={togglingAudit}
          className={`p-1.5 rounded transition-colors ${
            auditAccess
              ? "bg-blue-500/10 text-blue-600 hover:bg-blue-500/20"
              : "text-muted-foreground hover:bg-muted opacity-0 group-hover:opacity-100"
          }`}
          title={auditAccess ? "Published for audit — click to unpublish" : "Publish for auditor access"}
          aria-label={auditAccess ? "Unpublish from audit" : "Publish for audit"}
        >
          {togglingAudit
            ? <RefreshCw className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
            : auditAccess
              ? <Eye className="h-3.5 w-3.5" aria-hidden="true" />
              : <EyeOff className="h-3.5 w-3.5" aria-hidden="true" />}
        </button>
        {canDelete && !deleteConfirm && (
          <button
            onClick={() => setDeleteConfirm(true)}
            className="p-1.5 rounded hover:bg-destructive/10 transition-colors text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100"
            aria-label={`Delete ${attachment.original_filename}`}
          >
            <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
          </button>
        )}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Upload Zone
// ─────────────────────────────────────────────────────────────────────────────

interface StagedFile {
  file: File
  description: string
}

interface PendingFile {
  file: File
  description: string
  progress: number
  error: string | null
  done: boolean
}

interface UploadZoneProps {
  entityType: string
  entityId: string
  onUploaded: () => void
}

function UploadZone({ entityType, entityId, onUploaded }: UploadZoneProps) {
  const [dragOver, setDragOver] = useState(false)
  const [staged, setStaged] = useState<StagedFile[]>([])
  const [pending, setPending] = useState<PendingFile[]>([])
  const [applyAllDesc, setApplyAllDesc] = useState("")
  const [validationErrors, setValidationErrors] = useState<string[]>([])
  const [uploading, setUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const dropZoneRef = useRef<HTMLDivElement>(null)

  const validateFiles = useCallback((files: File[]): { valid: File[]; errors: string[] } => {
    const errors: string[] = []
    const valid: File[] = []
    const MAX_SIZE = 100 * 1024 * 1024 // 100 MB per file
    for (const file of files) {
      if (file.size > MAX_SIZE) {
        errors.push(`"${file.name}" exceeds the 100 MB limit (${formatBytes(file.size)})`)
      } else {
        valid.push(file)
      }
    }
    return { valid, errors }
  }, [])

  const stageFiles = useCallback((files: File[]) => {
    const { valid, errors } = validateFiles(files)
    setValidationErrors(errors)
    if (valid.length === 0) return
    setStaged((prev) => [
      ...prev,
      ...valid.map((f) => ({ file: f, description: "" })),
    ])
  }, [validateFiles])

  const handleApplyAllDesc = useCallback(() => {
    if (!applyAllDesc.trim()) return
    setStaged((prev) => prev.map((s) => ({ ...s, description: applyAllDesc.trim() })))
  }, [applyAllDesc])

  const uploadAll = useCallback(async () => {
    if (staged.length === 0) return
    setUploading(true)

    // Move staged to pending
    setPending(staged.map((s) => ({
      file: s.file,
      description: s.description,
      progress: 0,
      error: null,
      done: false,
    })))
    const toUpload = [...staged]
    setStaged([])
    setApplyAllDesc("")

    for (const item of toUpload) {
      try {
        await uploadAttachment(entityType, entityId, item.file, item.description || undefined, (pct) => {
          setPending((prev) =>
            prev.map((u) => u.file === item.file ? { ...u, progress: pct } : u)
          )
        })
        setPending((prev) =>
          prev.map((u) => u.file === item.file ? { ...u, progress: 100, done: true } : u)
        )
        onUploaded()
      } catch (e) {
        const msg = e instanceof Error ? e.message : "Upload failed"
        setPending((prev) =>
          prev.map((u) => u.file === item.file ? { ...u, error: msg } : u)
        )
      }
    }
    setUploading(false)
    // Clean up completed after a brief moment
    setTimeout(() => {
      setPending((prev) => prev.filter((u) => !u.done))
    }, 1500)
  }, [staged, entityType, entityId, onUploaded])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) stageFiles(files)
  }, [stageFiles])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    // Only set dragOver false if leaving the drop zone itself, not a child
    if (!dropZoneRef.current?.contains(e.relatedTarget as Node)) {
      setDragOver(false)
    }
  }, [])

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? [])
    if (files.length > 0) {
      stageFiles(files)
      e.target.value = ""
    }
  }, [stageFiles])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault()
      fileInputRef.current?.click()
    }
  }, [])

  const activePending = pending.filter((u) => !u.done)

  return (
    <div className="space-y-3">
      {/* Drop zone */}
      <div
        ref={dropZoneRef}
        role="button"
        tabIndex={0}
        aria-label="Upload files. Press Enter or Space to browse, or drag and drop files here."
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        onKeyDown={handleKeyDown}
        className={`flex flex-col items-center justify-center gap-2 py-6 rounded-xl border-2 border-dashed cursor-pointer transition-all focus:outline-none focus:ring-2 focus:ring-ring
          ${dragOver
            ? "border-primary bg-primary/10 text-primary scale-[1.01] shadow-md"
            : "border-border hover:border-primary/50 hover:bg-muted/30 text-muted-foreground"
          }`}
      >
        <Upload className="h-5 w-5" aria-hidden="true" />
        <div className="text-center">
          <p className="text-sm font-medium">
            {dragOver ? "Release to upload" : "Drop files here or click to browse"}
          </p>
          <p className="text-xs mt-0.5">Max 100 MB per file</p>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          className="hidden"
          aria-hidden="true"
          onChange={handleFileInput}
        />
      </div>

      {/* Validation errors */}
      {validationErrors.length > 0 && (
        <div
          className="rounded-lg border border-destructive/20 bg-destructive/10 px-3 py-2 space-y-1"
          role="alert"
          aria-live="assertive"
        >
          {validationErrors.map((err, i) => (
            <p key={i} className="text-xs text-destructive">{err}</p>
          ))}
          <button
            className="text-xs text-destructive underline hover:no-underline mt-1"
            onClick={() => setValidationErrors([])}
            aria-label="Dismiss errors"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Pre-upload staged files with per-file descriptions */}
      {staged.length > 0 && (
        <div className="space-y-3 rounded-xl border border-border bg-muted/10 p-3">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold text-foreground">
              {staged.length} {staged.length === 1 ? "file" : "files"} ready to upload
            </p>
            <button
              onClick={() => setStaged([])}
              className="text-xs text-muted-foreground hover:text-foreground transition-colors"
              aria-label="Clear all staged files"
            >
              Clear all
            </button>
          </div>

          {/* Apply description to all */}
          {staged.length > 1 && (
            <div className="flex items-center gap-2">
              <input
                type="text"
                className="flex-1 h-7 px-2 text-xs rounded border border-border bg-background focus:outline-none focus:ring-1 focus:ring-ring"
                placeholder="Apply description to all files..."
                value={applyAllDesc}
                onChange={(e) => setApplyAllDesc(e.target.value)}
                aria-label="Description to apply to all files"
              />
              <Button
                size="sm"
                variant="outline"
                className="h-7 text-xs px-2"
                onClick={handleApplyAllDesc}
                disabled={!applyAllDesc.trim()}
                aria-label="Apply description to all files"
              >
                Apply to all
              </Button>
            </div>
          )}

          {/* Individual file list */}
          <div className="space-y-2">
            {staged.map((s, i) => (
              <div key={`${s.file.name}-${s.file.size}-${i}`} className="flex items-center gap-2">
                <span className="text-base shrink-0 select-none" aria-hidden="true">
                  {getFileEmoji(s.file.type || "application/octet-stream", s.file.name)}
                </span>
                <div className="flex-1 min-w-0 space-y-1">
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-foreground font-medium truncate">{s.file.name}</span>
                    <span className="text-muted-foreground shrink-0">{formatBytes(s.file.size)}</span>
                  </div>
                  <input
                    type="text"
                    className="w-full h-6 px-2 text-xs rounded border border-border bg-background focus:outline-none focus:ring-1 focus:ring-ring"
                    placeholder="Description (optional)"
                    value={s.description}
                    onChange={(e) => {
                      const val = e.target.value
                      setStaged((prev) => prev.map((item, idx) => idx === i ? { ...item, description: val } : item))
                    }}
                    aria-label={`Description for ${s.file.name}`}
                  />
                </div>
                <button
                  onClick={() => setStaged((prev) => prev.filter((_, idx) => idx !== i))}
                  className="p-1 rounded hover:bg-muted transition-colors shrink-0"
                  aria-label={`Remove ${s.file.name}`}
                >
                  <X className="h-3.5 w-3.5 text-muted-foreground hover:text-foreground" aria-hidden="true" />
                </button>
              </div>
            ))}
          </div>

          <Button
            size="sm"
            className="w-full text-xs gap-1"
            onClick={uploadAll}
            disabled={uploading}
            aria-label={`Upload ${staged.length} files`}
          >
            {uploading
              ? <RefreshCw className="h-3 w-3 animate-spin" aria-hidden="true" />
              : <Upload className="h-3 w-3" aria-hidden="true" />}
            Upload {staged.length === 1 ? "file" : `all ${staged.length} files`}
          </Button>
        </div>
      )}

      {/* Upload progress */}
      {activePending.length > 0 && (
        <div className="space-y-2" aria-live="polite" aria-label="Upload progress">
          {activePending.map((u, i) => (
            <div key={`${u.file.name}-${u.file.size}-${i}`} className="space-y-1">
              <div className="flex items-center justify-between text-xs gap-2">
                <span className="text-foreground truncate max-w-[200px]">{u.file.name}</span>
                <span className="text-muted-foreground shrink-0">{formatBytes(u.file.size)}</span>
                {u.error ? (
                  <span className="text-destructive shrink-0">{u.error}</span>
                ) : (
                  <span className="text-muted-foreground shrink-0 tabular-nums">{u.progress}%</span>
                )}
                <button
                  onClick={() => setPending((prev) => prev.filter((p) => p.file !== u.file))}
                  aria-label={`Remove ${u.file.name} from queue`}
                >
                  <X className="h-3 w-3 text-muted-foreground hover:text-foreground" aria-hidden="true" />
                </button>
              </div>
              {!u.error && (
                <div
                  className="w-full bg-muted rounded-full h-1.5"
                  role="progressbar"
                  aria-valuenow={u.progress}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-label={`Uploading ${u.file.name}: ${u.progress}%`}
                >
                  <div
                    className="bg-primary h-1.5 rounded-full transition-all"
                    style={{ width: `${u.progress}%` }}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// AttachmentsSection — Public Component
// ─────────────────────────────────────────────────────────────────────────────

interface AttachmentsSectionProps {
  entityType: string
  entityId: string
  currentUserId: string
  canUpload?: boolean
  isWorkspaceAdmin?: boolean
  /** If true, do not auto-fetch on mount. Caller triggers first load by passing active=true. */
  active?: boolean
  className?: string
  /** Called after any upload or delete so parent can refresh attachment count */
  onCountChange?: () => void
}

export function AttachmentsSection({
  entityType,
  entityId,
  currentUserId,
  canUpload = false,
  isWorkspaceAdmin = false,
  active = true,
  className = "",
  onCountChange,
}: AttachmentsSectionProps) {
  const [attachments, setAttachments] = useState<AttachmentRecord[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [hasNext, setHasNext] = useState(false)
  const [loading, setLoading] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showUpload, setShowUpload] = useState(false)
  const hasLoadedRef = useRef(false)

  const load = useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true)
    setError(null)
    try {
      const res = await listAttachments(entityType, entityId, 1, 25)
      setAttachments(res.items)
      setTotal(res.total)
      setHasNext(res.total > 25)
      setPage(1)
      onCountChange?.()
    } catch (e) {
      setError((e as Error).message || "Failed to load attachments")
    } finally {
      setLoading(false)
    }
  }, [entityType, entityId, onCountChange])

  const loadMore = useCallback(async () => {
    setLoadingMore(true)
    try {
      const nextPage = page + 1
      const res = await listAttachments(entityType, entityId, nextPage, 25)
      setAttachments((prev) => {
        const next = [...prev, ...res.items]
        setHasNext(next.length < res.total)
        return next
      })
      setPage(nextPage)
    } catch (e) {
      setError((e as Error).message || "Failed to load more attachments")
    } finally {
      setLoadingMore(false)
    }
  }, [entityType, entityId, page])

  // Lazy load: only fetch when active
  useEffect(() => {
    if (!active) return
    if (!hasLoadedRef.current) {
      hasLoadedRef.current = true
      load()
    }
  }, [active, load])

  // Poll for virus scan status updates when any attachment is pending
  useEffect(() => {
    const hasPending = attachments.some((a) => a.virus_scan_status === "pending")
    if (!hasPending) return

    const interval = setInterval(() => {
      load(true)
    }, 10000)

    return () => clearInterval(interval)
  }, [attachments, load])

  const infectedCount = useMemo(
    () => attachments.filter((a) => a.virus_scan_status === "infected").length,
    [attachments]
  )

  return (
    <div className={`space-y-4 ${className}`} aria-label="Attachments section">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Paperclip className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
          <span className="text-sm font-semibold text-foreground">
            {loading ? "Attachments" : `Attachments (${total})`}
          </span>
          {infectedCount > 0 && (
            <span
              className="inline-flex items-center gap-0.5 text-[10px] font-medium text-red-600 bg-red-500/10 border border-red-500/20 rounded px-1.5 py-0.5"
              aria-label={`${infectedCount} infected files detected`}
            >
              <AlertTriangle className="h-2.5 w-2.5" aria-hidden="true" />
              {infectedCount} infected
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => load(true)}
            className="p-1.5 rounded hover:bg-muted transition-colors"
            aria-label="Refresh attachments"
          >
            <RefreshCw
              className={`h-3.5 w-3.5 text-muted-foreground ${loading ? "animate-spin" : ""}`}
              aria-hidden="true"
            />
          </button>
          {canUpload && (
            <Button
              size="sm"
              variant={showUpload ? "secondary" : "outline"}
              className="h-7 text-xs gap-1"
              onClick={() => setShowUpload((v) => !v)}
              aria-expanded={showUpload}
              aria-label={showUpload ? "Cancel upload" : "Upload new file"}
            >
              <Upload className="h-3 w-3" aria-hidden="true" />
              {showUpload ? "Cancel" : "Upload"}
            </Button>
          )}
        </div>
      </div>

      {/* Live region */}
      <div aria-live="polite" aria-atomic="true" className="sr-only">
        {loading ? "Loading attachments..." : ""}
      </div>

      {/* Error */}
      {error && (
        <div
          className="flex items-center gap-2 rounded-lg border border-destructive/20 bg-destructive/10 px-3 py-2 text-sm text-destructive"
          role="alert"
          aria-live="assertive"
        >
          <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden="true" />
          {error}
          <button
            onClick={() => load()}
            className="ml-auto text-xs underline hover:no-underline"
            aria-label="Retry loading attachments"
          >
            Retry
          </button>
        </div>
      )}

      {/* Upload zone */}
      {showUpload && canUpload && (
        <UploadZone
          entityType={entityType}
          entityId={entityId}
          onUploaded={() => { load(true); setShowUpload(false) }}
        />
      )}

      {/* List */}
      {loading ? (
        <div className="space-y-2" aria-label="Loading attachments" aria-busy="true">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="flex items-center gap-3 px-4 py-3 rounded-xl border border-border animate-pulse"
              aria-hidden="true"
            >
              <div className="h-4 w-4 bg-muted rounded shrink-0" />
              <div className="flex-1 space-y-1.5">
                <div className="h-3 w-48 bg-muted rounded" />
                <div className="h-2.5 w-32 bg-muted rounded" />
              </div>
            </div>
          ))}
        </div>
      ) : attachments.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-10 gap-2 text-center">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-muted" aria-hidden="true">
            <Paperclip className="h-5 w-5 text-muted-foreground" />
          </div>
          <p className="text-sm font-medium text-foreground">No attachments yet</p>
          {canUpload && (
            <p className="text-xs text-muted-foreground">Upload files using the button above.</p>
          )}
        </div>
      ) : (
        <div className="space-y-2">
          {attachments.map((a) => (
            <AttachmentRow
              key={a.id}
              attachment={a}
              currentUserId={currentUserId}
              isWorkspaceAdmin={isWorkspaceAdmin}
              showStorageKey={isWorkspaceAdmin}
              onDeleted={() => load(true)}
              onDescriptionUpdated={() => load(true)}
            />
          ))}
        </div>
      )}

      {/* Load more */}
      {hasNext && !loading && (
        <div className="pt-2 border-t border-border">
          <Button
            variant="ghost"
            size="sm"
            className="w-full text-xs"
            disabled={loadingMore}
            onClick={loadMore}
            aria-label="Load more attachments"
          >
            {loadingMore
              ? <RefreshCw className="h-3 w-3 animate-spin mr-1" aria-hidden="true" />
              : null}
            Load more attachments
          </Button>
        </div>
      )}
    </div>
  )
}

export default AttachmentsSection
