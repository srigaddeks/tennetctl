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
  DialogFooter,
  DialogTitle,
  DialogDescription,
} from "@kcontrol/ui"
import {
  BookOpen,
  Download,
  Upload,
  Search,
  RefreshCw,
  AlertTriangle,
  Loader2,
  FileText,
  X,
  Globe,
  Building2,
  Plus,
  Tag,
  FileArchive,
  Edit,
  Trash2,
  FileEdit,
  MoreHorizontal,
  History,
} from "lucide-react"
import {
  listDocCategories,
  listGlobalDocs,
  listOrgDocs,
  getDocDownloadUrl,
  uploadOrgDoc,
  updateDocument,
  deleteDocument,
  replaceDocumentFile,
  getDocumentHistory,
  revertDocument,
} from "@/lib/api/docs"
import type { DocCategoryResponse, DocumentResponse, UpdateDocumentRequest, DocEventResponse } from "@/lib/api/docs"
import { useOrgWorkspace } from "@/lib/context/OrgWorkspaceContext"
import { useAccess } from "@/components/providers/AccessProvider"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@kcontrol/ui"

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  })
}

function fmtFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

// Map category codes to border colors
const CATEGORY_BORDER: Record<string, string> = {
  policy: "border-l-primary",
  procedure: "border-l-blue-500",
  standard: "border-l-purple-500",
  guideline: "border-l-green-500",
  template: "border-l-amber-500",
  regulation: "border-l-red-500",
}

function getCategoryBorder(categoryName?: string | null): string {
  if (!categoryName) return "border-l-border"
  const key = categoryName.toLowerCase().split(" ")[0]
  return CATEGORY_BORDER[key] ?? "border-l-border"
}

// ─────────────────────────────────────────────────────────────────────────────
// Doc row component
// ─────────────────────────────────────────────────────────────────────────────

function DocumentRow({
  doc,
  onDownload,
  downloading,
  canManage,
  onEdit,
  onReplace,
  onDelete,
  onHistory,
}: {
  doc: DocumentResponse
  onDownload: (doc: DocumentResponse) => void
  downloading: boolean
  canManage?: boolean
  onEdit?: (doc: DocumentResponse) => void
  onReplace?: (doc: DocumentResponse) => void
  onDelete?: (doc: DocumentResponse) => void
  onHistory?: (doc: DocumentResponse) => void
}) {
  const borderCls = getCategoryBorder(doc.category_name)
  return (
    <div className={`flex items-start gap-4 rounded-xl border border-l-[3px] ${borderCls} bg-card px-4 py-3 shadow-sm hover:shadow-md hover:border-primary/20 hover:bg-muted/30 transition-all duration-300 group`}>
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/5 text-primary group-hover:bg-primary/10 transition-colors mt-0.5">
        <FileText className="h-5 w-5" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors">{doc.title}</span>
          {doc.version_label && (
            <Badge variant="outline" className="text-[10px] shrink-0 hidden sm:flex">{doc.version_label}</Badge>
          )}
          {doc.category_name && (
            <Badge variant="secondary" className="text-[10px]">{doc.category_name}</Badge>
          )}
        </div>
        {doc.description && (
          <p className="text-xs text-muted-foreground mt-1 line-clamp-1 hidden sm:block">{doc.description}</p>
        )}
        <div className="flex items-center gap-3 mt-1.5 text-[11px] text-muted-foreground flex-wrap">
          <span className="font-mono bg-muted/50 px-1.5 py-0.5 rounded">{doc.original_filename}</span>
          <span className="hidden sm:inline">{fmtFileSize(doc.file_size_bytes)}</span>
          <span className="hidden sm:inline">•</span>
          <span>{fmtDate(doc.created_at)}</span>
          {doc.tags.length > 0 && (
            <div className="flex items-center gap-1 hidden sm:flex">
              <Separator orientation="vertical" className="h-2.5 mx-0.5" />
              <Tag className="h-2.5 w-2.5" />
              {doc.tags.slice(0, 3).map((tag) => (
                <span key={tag} className="rounded-full bg-muted px-1.5 py-0.5 text-[10px]">{tag}</span>
              ))}
              {doc.tags.length > 3 && <span className="text-[10px]">+{doc.tags.length - 3}</span>}
            </div>
          )}
        </div>
      </div>
      <div className="flex items-center gap-1 shrink-0">
        <Button
          size="sm"
          variant="ghost"
          className="h-9 gap-1.5 text-xs sm:opacity-0 sm:group-hover:opacity-100 transition-all duration-200 hover:bg-primary hover:text-primary-foreground"
          onClick={() => onDownload(doc)}
          disabled={downloading}
        >
          {downloading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Download className="h-3.5 w-3.5" />}
          <span className="hidden sm:inline">Download</span>
        </Button>

        {canManage && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button size="sm" variant="ghost" className="h-9 w-9 p-0 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-40">
              <DropdownMenuItem onClick={() => onEdit?.(doc)} className="cursor-pointer">
                <Edit className="mr-2 h-4 w-4" /> Edit Metadata
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onReplace?.(doc)} className="cursor-pointer">
                <FileEdit className="mr-2 h-4 w-4" /> Replace File
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onHistory?.(doc)} className="cursor-pointer">
                <History className="mr-2 h-4 w-4" /> Version History
              </DropdownMenuItem>
              <Separator className="my-1" />
              <DropdownMenuItem onClick={() => onDelete?.(doc)} className="cursor-pointer text-red-500 focus:text-red-500">
                <Trash2 className="mr-2 h-4 w-4" /> Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Upload dialog
// ─────────────────────────────────────────────────────────────────────────────

interface UploadDialogProps {
  open: boolean
  onClose: () => void
  orgId: string
  categories: DocCategoryResponse[]
  onSuccess: () => void
}

function UploadDialog({ open, onClose, orgId, categories, onSuccess }: UploadDialogProps) {
  const [title, setTitle] = useState("")
  const [categoryCode, setCategoryCode] = useState("")
  const [description, setDescription] = useState("")
  const [tagsInput, setTagsInput] = useState("")
  const [versionLabel, setVersionLabel] = useState("")
  const [file, setFile] = useState<File | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const reset = useCallback(() => {
    setTitle("")
    setCategoryCode("")
    setDescription("")
    setTagsInput("")
    setVersionLabel("")
    setFile(null)
    setError(null)
  }, [])

  const handleClose = useCallback(() => {
    reset()
    onClose()
  }, [reset, onClose])

  const handleSubmit = useCallback(async () => {
    if (!title.trim()) { setError("Title is required"); return }
    if (!categoryCode) { setError("Category is required"); return }
    if (!file) { setError("Please select a file"); return }

    setSubmitting(true)
    setError(null)
    try {
      const fd = new FormData()
      fd.append("org_id", orgId)
      fd.append("title", title.trim())
      fd.append("category_code", categoryCode)
      if (description.trim()) fd.append("description", description.trim())
      fd.append("tags", tagsInput)
      if (versionLabel.trim()) fd.append("version_label", versionLabel.trim())
      fd.append("file", file)
      await uploadOrgDoc(fd)
      handleClose()
      onSuccess()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Upload failed")
    } finally {
      setSubmitting(false)
    }
  }, [title, categoryCode, description, tagsInput, versionLabel, file, orgId, handleClose, onSuccess])

  return (
    <Dialog open={open} onOpenChange={(v) => !v && handleClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-primary/10 p-2.5"><Upload className="h-4 w-4 text-primary" /></div>
            <div>
              <DialogTitle>Upload Document</DialogTitle>
              <DialogDescription>Upload a document to your organisation&apos;s library.</DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />

        <div className="flex flex-col gap-4 py-2 max-h-[60vh] overflow-y-auto pr-1">
          {error && (
            <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500">
              <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
              {error}
            </div>
          )}

          <div className="flex flex-col gap-1.5">
            <Label className="text-xs">Title *</Label>
            <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Document title" maxLength={500} className="h-9 text-sm" autoFocus />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label className="text-xs">Category *</Label>
            <select className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={categoryCode} onChange={(e) => setCategoryCode(e.target.value)}>
              <option value="">Select category…</option>
              {categories.map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
            </select>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label className="text-xs">Description</Label>
            <textarea className="min-h-[64px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-none"
              value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Optional description" />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label className="text-xs">Tags</Label>
              <Input value={tagsInput} onChange={(e) => setTagsInput(e.target.value)} placeholder="iso27001, soc2, gdpr" className="h-9 text-sm" />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label className="text-xs">Version</Label>
              <Input value={versionLabel} onChange={(e) => setVersionLabel(e.target.value)} placeholder="v1.0" className="h-9 text-sm" />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label className="text-xs">File *</Label>
            <input type="file"
              className="block w-full text-sm text-muted-foreground file:mr-3 file:rounded-md file:border file:border-input file:bg-background file:px-3 file:py-1 file:text-xs file:font-medium file:text-foreground"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          </div>
        </div>

        <DialogFooter className="gap-2 sm:gap-2">
          <Button variant="outline" size="sm" onClick={handleClose} disabled={submitting}>Cancel</Button>
          <Button size="sm" onClick={handleSubmit} disabled={submitting}>
            {submitting ? <><Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />Uploading…</> : <><Upload className="mr-2 h-3.5 w-3.5" />Upload</>}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Edit dialog (metadata)
// ─────────────────────────────────────────────────────────────────────────────

interface EditDialogProps {
  open: boolean
  onClose: () => void
  doc: DocumentResponse | null
  categories: DocCategoryResponse[]
  onSuccess: () => void
}

function EditDialog({ open, onClose, doc, categories, onSuccess }: EditDialogProps) {
  const [title, setTitle] = useState("")
  const [categoryCode, setCategoryCode] = useState("")
  const [description, setDescription] = useState("")
  const [tagsInput, setTagsInput] = useState("")
  const [versionLabel, setVersionLabel] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (doc && open) {
      setTitle(doc.title)
      setCategoryCode(doc.category_code)
      setDescription(doc.description ?? "")
      setTagsInput(doc.tags.join(", "))
      setVersionLabel(doc.version_label ?? "")
    }
  }, [doc, open])

  const handleSubmit = useCallback(async () => {
    if (!doc) return
    if (!title.trim()) { setError("Title is required"); return }
    if (!categoryCode) { setError("Category is required"); return }

    setSubmitting(true)
    setError(null)
    try {
      const tags = tagsInput.split(",").map(t => t.trim()).filter(t => t)
      const body: UpdateDocumentRequest = {
        title: title.trim(),
        category_code: categoryCode,
        description: description.trim() || null,
        tags,
        version_label: versionLabel.trim() || null,
      }
      await updateDocument(doc.id, body)
      onSuccess()
      onClose()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Update failed")
    } finally {
      setSubmitting(false)
    }
  }, [doc, title, categoryCode, description, tagsInput, versionLabel, onSuccess, onClose])

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-blue-500/10 p-2.5"><Edit className="h-4 w-4 text-blue-500" /></div>
            <div>
              <DialogTitle>Edit Document Metadata</DialogTitle>
              <DialogDescription>Update the title, category, or other details.</DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />

        <div className="flex flex-col gap-4 py-2">
          {error && (
            <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500">
              <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
              {error}
            </div>
          )}

          <div className="flex flex-col gap-1.5">
            <Label className="text-xs">Title *</Label>
            <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Document title" maxLength={500} className="h-9 text-sm" />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label className="text-xs">Category *</Label>
            <select className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={categoryCode} onChange={(e) => setCategoryCode(e.target.value)}>
              <option value="">Select category…</option>
              {categories.map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
            </select>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label className="text-xs">Description</Label>
            <textarea className="min-h-[64px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm resize-none"
              value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Optional description" />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label className="text-xs">Tags</Label>
              <Input value={tagsInput} onChange={(e) => setTagsInput(e.target.value)} placeholder="iso27001, soc2" className="h-9 text-sm" />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label className="text-xs">Version</Label>
              <Input value={versionLabel} onChange={(e) => setVersionLabel(e.target.value)} placeholder="v1.0" className="h-9 text-sm" />
            </div>
          </div>
        </div>

        <DialogFooter className="gap-2 sm:gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={submitting}>Cancel</Button>
          <Button size="sm" onClick={handleSubmit} disabled={submitting}>
            {submitting ? <><Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />Saving…</> : <><Download className="mr-2 h-3.5 w-3.5 rotate-180" />Save Changes</>}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Replace dialog (file)
// ─────────────────────────────────────────────────────────────────────────────

interface ReplaceDialogProps {
  open: boolean
  onClose: () => void
  doc: DocumentResponse | null
  onSuccess: () => void
}

function ReplaceDialog({ open, onClose, doc, onSuccess }: ReplaceDialogProps) {
  const [file, setFile] = useState<File | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleClose = useCallback(() => {
    setFile(null)
    setError(null)
    onClose()
  }, [onClose])

  const handleSubmit = useCallback(async () => {
    if (!doc || !file) { setError("Please select a file"); return }

    setSubmitting(true)
    setError(null)
    try {
      const fd = new FormData()
      fd.append("file", file)
      await replaceDocumentFile(doc.id, fd)
      onSuccess()
      handleClose()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Replacement failed")
    } finally {
      setSubmitting(false)
    }
  }, [doc, file, onSuccess, handleClose])

  return (
    <Dialog open={open} onOpenChange={(v) => !v && handleClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-amber-500/10 p-2.5"><FileEdit className="h-4 w-4 text-amber-500" /></div>
            <div>
              <DialogTitle>Replace Document File</DialogTitle>
              <DialogDescription>Upload a new version of the file for &quot;{doc?.title}&quot;.</DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />

        <div className="flex flex-col gap-4 py-2">
          {error && (
            <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500">
              <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
              {error}
            </div>
          )}

          <div className="rounded-lg bg-muted/50 p-3 text-xs space-y-2">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Current File:</span>
              <span className="font-medium">{doc?.original_filename}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Current Size:</span>
              <span className="font-medium">{doc ? fmtFileSize(doc.file_size_bytes) : "-"}</span>
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label className="text-xs">New File *</Label>
            <input type="file"
              className="block w-full text-sm text-muted-foreground file:mr-3 file:rounded-md file:border file:border-input file:bg-background file:px-3 file:py-1 file:text-xs file:font-medium file:text-foreground"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          </div>
        </div>

        <DialogFooter className="gap-2 sm:gap-2">
          <Button variant="outline" size="sm" onClick={handleClose} disabled={submitting}>Cancel</Button>
          <Button size="sm" onClick={handleSubmit} disabled={submitting} className="bg-amber-600 hover:bg-amber-700">
            {submitting ? <><Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />Replacing…</> : <><RefreshCw className="mr-2 h-3.5 w-3.5" />Replace File</>}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Delete dialog
// ─────────────────────────────────────────────────────────────────────────────

interface DeleteDialogProps {
  open: boolean
  onClose: () => void
  doc: DocumentResponse | null
  onSuccess: () => void
}

function DeleteDialog({ open, onClose, doc, onSuccess }: DeleteDialogProps) {
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = useCallback(async () => {
    if (!doc) return
    setSubmitting(true)
    setError(null)
    try {
      await deleteDocument(doc.id)
      onSuccess()
      onClose()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Delete failed")
    } finally {
      setSubmitting(false)
    }
  }, [doc, onSuccess, onClose])

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-md border-red-500/20">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-red-500/10 p-2.5"><Trash2 className="h-4 w-4 text-red-500" /></div>
            <div>
              <DialogTitle>Delete Document</DialogTitle>
              <DialogDescription>Are you sure you want to delete &quot;{doc?.title}&quot;? This cannot be undone.</DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {error && (
          <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500">
            <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
            {error}
          </div>
        )}

        <DialogFooter className="gap-2 sm:gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={submitting}>Cancel</Button>
          <Button size="sm" variant="destructive" onClick={handleSubmit} disabled={submitting}>
            {submitting ? <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" /> : <Trash2 className="mr-2 h-3.5 w-3.5" />}
            Delete Document
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// History dialog
// ─────────────────────────────────────────────────────────────────────────────

interface HistoryDialogProps {
  open: boolean
  onClose: () => void
  doc: DocumentResponse | null
  onSuccess: () => void
}

function HistoryDialog({ open, onClose, doc, onSuccess }: HistoryDialogProps) {
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState<DocEventResponse[]>([])
  const [error, setError] = useState<string | null>(null)
  const [reverting, setReverting] = useState<string | null>(null)

  useEffect(() => {
    if (open && doc) {
      setLoading(true)
      setError(null)
      getDocumentHistory(doc.id)
        .then((res) => setHistory(res.items))
        .catch((e) => setError(e instanceof Error ? e.message : "Failed to load history"))
        .finally(() => setLoading(false))
    }
  }, [open, doc])

  const handleRevert = async (eventId: string) => {
    if (!doc) return
    setReverting(eventId)
    setError(null)
    try {
      await revertDocument(doc.id, eventId)
      onSuccess()
      onClose()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Revert failed")
    } finally {
      setReverting(null)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-primary/10 p-2.5"><History className="h-4 w-4 text-primary" /></div>
            <div>
              <DialogTitle>Version History</DialogTitle>
              <DialogDescription>View audit trail and revert to previous versions for &quot;{doc?.title}&quot;.</DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />

        <div className="max-h-[400px] overflow-y-auto pr-2 py-2">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-10 text-muted-foreground">
              <Loader2 className="h-8 w-8 animate-spin mb-4" />
              <p className="text-sm italic">Loading history...</p>
            </div>
          ) : error ? (
            <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500">
              <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
              {error}
            </div>
          ) : history.length === 0 ? (
            <div className="text-center py-10 text-muted-foreground text-sm italic">
              No history found for this document.
            </div>
          ) : (
            <div className="space-y-4">
              {history.map((event) => {
                const isRevertible = event.event_type === "replaced" && event.metadata.previous_storage
                return (
                  <div key={event.id} className="relative pl-6 border-l-2 border-muted pb-4 last:pb-0">
                    <div className="absolute -left-[9px] top-0 h-4 w-4 rounded-full bg-background border-2 border-primary" />
                    <div className="flex flex-col gap-1">
                      <div className="flex justify-between items-start">
                        <span className="text-xs font-semibold capitalize bg-muted px-2 py-0.5 rounded-md">
                          {event.event_type.replace("_", " ")}
                        </span>
                        <span className="text-[10px] text-muted-foreground">{fmtDate(event.created_at)}</span>
                      </div>
                      <div className="text-xs text-foreground mt-1">
                        {event.event_type === "uploaded" && `Initial version uploaded by ${event.actor_display_name || "System"}`}
                        {event.event_type === "replaced" && (
                          <>
                            Replaced by <strong>{event.actor_display_name || "System"}</strong>.
                            {event.metadata.old_filename && (
                              <div className="text-[10px] text-muted-foreground mt-0.5">
                                Prev: {event.metadata.old_filename} ({fmtFileSize(event.metadata.size || 0)})
                              </div>
                            )}
                          </>
                        )}
                        {event.event_type === "deleted" && `Document deleted by ${event.actor_display_name || "System"}`}
                        {event.event_type === "title_updated" && `Title updated to "${event.metadata.new_title}"`}
                        {event.event_type === "description_updated" && "Description updated"}
                      </div>
                      
                      {isRevertible && (
                        <div className="mt-2 text-right">
                          <Button 
                            size="sm" 
                            variant="outline" 
                            className="h-7 text-[10px] gap-1.5"
                            onClick={() => handleRevert(event.id)}
                            disabled={!!reverting}
                          >
                            {reverting === event.id ? (
                              <Loader2 className="h-3 w-3 animate-spin" />
                            ) : (
                              <RefreshCw className="h-3 w-3" />
                            )}
                            Restore this version
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" size="sm" onClick={onClose}>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Main page
// ─────────────────────────────────────────────────────────────────────────────

type Tab = "global" | "org"

export default function PoliciesPage() {
  const { selectedOrgId, orgs, ready } = useOrgWorkspace()
  const { canWrite, hasPlatformAction, isOrgAdmin } = useAccess()

  const [activeTab, setActiveTab] = useState<Tab>("org")
  const [categories, setCategories] = useState<DocCategoryResponse[]>([])
  const [globalDocs, setGlobalDocs] = useState<DocumentResponse[]>([])
  const [orgDocs, setOrgDocs] = useState<DocumentResponse[]>([])
  const [globalTotal, setGlobalTotal] = useState(0)
  const [orgTotal, setOrgTotal] = useState(0)
  const [search, setSearch] = useState("")
  const [categoryFilter, setCategoryFilter] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [downloading, setDownloading] = useState<string | null>(null)

  // Dialog states
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false)
  const [selectedDoc, setSelectedDoc] = useState<DocumentResponse | null>(null)
  const [action, setAction] = useState<"edit" | "replace" | "delete" | "history" | null>(null)

  const canUploadOrg = canWrite("docs") || isOrgAdmin
  const canViewGlobalDocs = hasPlatformAction("docs.view") || hasPlatformAction("docs.manage")

  const loadCategories = useCallback(async () => {
    try {
      const cats = await listDocCategories()
      setCategories(cats)
    } catch {
      // non-fatal
    }
  }, [])

  const loadGlobalDocs = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await listGlobalDocs({
        search: search || undefined,
        category_code: categoryFilter || undefined,
      })
      setGlobalDocs(res.items)
      setGlobalTotal(res.total)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load documents")
    } finally {
      setLoading(false)
    }
  }, [search, categoryFilter])

  const loadOrgDocs = useCallback(async () => {
    if (!selectedOrgId) return
    setLoading(true)
    setError(null)
    try {
      const res = await listOrgDocs(selectedOrgId, {
        search: search || undefined,
        category_code: categoryFilter || undefined,
      })
      setOrgDocs(res.items)
      setOrgTotal(res.total)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load documents")
    } finally {
      setLoading(false)
    }
  }, [selectedOrgId, search, categoryFilter])

  useEffect(() => { if (ready) loadCategories() }, [loadCategories, ready])
  useEffect(() => {
    if (ready && activeTab === "global" && canViewGlobalDocs) {
      loadGlobalDocs()
    }
  }, [activeTab, canViewGlobalDocs, loadGlobalDocs, ready])
  useEffect(() => {
    if (ready && activeTab === "org") {
      loadOrgDocs()
    }
  }, [activeTab, loadOrgDocs, ready])

  const handleDownload = useCallback(async (doc: DocumentResponse) => {
    setDownloading(doc.id)
    try {
      const result = await getDocDownloadUrl(doc.id)
      window.open(result.download_url, "_blank", "noopener,noreferrer")
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to generate download link")
    } finally {
      setDownloading(null)
    }
  }, [])

  const handleSearch = useCallback((e: React.FormEvent) => {
    e.preventDefault()
    if (activeTab === "global") loadGlobalDocs()
    else loadOrgDocs()
  }, [activeTab, loadGlobalDocs, loadOrgDocs])

  const handleRefresh = useCallback(() => {
    if (activeTab === "global") loadGlobalDocs()
    else loadOrgDocs()
  }, [activeTab, loadGlobalDocs, loadOrgDocs])

  const currentOrg = orgs.find((o) => o.id === selectedOrgId)
  const docs = activeTab === "global" ? globalDocs : orgDocs
  const total = activeTab === "global" ? globalTotal : orgTotal

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold tracking-tight font-secondary">Policies &amp; Documents</h1>
          <p className="text-sm text-muted-foreground mt-1">Browse compliance policies, framework guides, templates, and organisation documents.</p>
        </div>
        <div className="flex items-center gap-2 ml-auto sm:ml-0">
          {activeTab === "org" && canUploadOrg && selectedOrgId && (
            <Button size="sm" className="gap-1.5" onClick={() => setUploadDialogOpen(true)}>
              <Plus className="h-3.5 w-3.5" /> Upload
            </Button>
          )}
          <Button size="sm" variant="ghost" className="h-8 w-8 p-0 hidden sm:flex" onClick={handleRefresh} disabled={loading}>
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-3 gap-4">
        {([
          { label: "My Org Docs", value: orgTotal, icon: Building2, iconCls: "text-blue-500", borderCls: "border-l-blue-500", numCls: "text-blue-600 dark:text-blue-400" },
          { label: "Other Documents", value: globalTotal, icon: Globe, iconCls: "text-primary", borderCls: "border-l-primary", numCls: "" },
          { label: "Categories", value: categories.length, icon: FileArchive, iconCls: "text-amber-500", borderCls: "border-l-amber-500", numCls: "text-amber-600 dark:text-amber-400" },
        ] as const).map(({ label, value, icon: Icon, iconCls, borderCls, numCls }) => (
          <div key={label} className={`relative rounded-xl border bg-card border-l-[3px] ${borderCls} px-4 py-3 flex items-center gap-3`}>
            <div className="shrink-0 rounded-lg p-2 bg-muted"><Icon className={`w-4 h-4 ${iconCls}`} /></div>
            <div className="min-w-0">
              <div className={`text-2xl font-bold tabular-nums leading-none ${numCls}`}>{value}</div>
              <div className="text-[11px] text-muted-foreground mt-0.5 truncate">{label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border">
        <button type="button" onClick={() => setActiveTab("org")}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "org" ? "border-primary text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"
          }`}>
          <Building2 className="h-4 w-4" />
          My Organisation
          {currentOrg && <span className="text-muted-foreground hidden sm:inline"> ({currentOrg.name})</span>}
          <span className="ml-1 rounded-full bg-muted px-1.5 py-0.5 text-[11px] text-muted-foreground">{orgTotal}</span>
        </button>
        {canViewGlobalDocs && (
          <button type="button" onClick={() => setActiveTab("global")}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === "global" ? "border-primary text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"
            }`}>
            <Globe className="h-4 w-4" />
            Other Documents
            <span className="ml-1 rounded-full bg-muted px-1.5 py-0.5 text-[11px] text-muted-foreground">{globalTotal}</span>
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="rounded-xl border border-border bg-card px-4 py-3 space-y-3">
        <form onSubmit={handleSearch} className="flex items-center gap-3 flex-wrap">
          <div className="relative flex-1 min-w-[160px] max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <Input className="pl-9 h-9 text-sm" placeholder="Search documents…" value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          <select className="h-9 rounded-md border border-input bg-background px-3 text-sm" value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
            <option value="">All categories</option>
            {categories.map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
          </select>
          {(search || categoryFilter) && (
            <Button type="button" size="sm" variant="ghost" className="h-9 w-9 p-0" onClick={() => { setSearch(""); setCategoryFilter("") }}>
              <X className="h-3.5 w-3.5" />
            </Button>
          )}
          <span className="text-xs text-muted-foreground ml-auto">{total} document{total !== 1 ? "s" : ""}</span>
        </form>
        {categoryFilter && (
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Active:</span>
            <span className="inline-flex items-center gap-1 rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[11px] font-medium text-amber-600 dark:text-amber-400">
              {categories.find(c => c.code === categoryFilter)?.name ?? categoryFilter}
              <button onClick={() => setCategoryFilter("")} className="hover:text-amber-800 dark:hover:text-amber-200"><X className="w-2.5 h-2.5" /></button>
            </span>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-500">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          {error}
          <Button size="sm" variant="ghost" className="ml-auto h-6 px-2" onClick={() => setError(null)}>
            <X className="h-3.5 w-3.5" />
          </Button>
        </div>
      )}

      {/* Org tab — empty state when no org selected */}
      {activeTab === "org" && !selectedOrgId && (
        <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed py-16 text-center text-muted-foreground">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-muted"><Building2 className="h-6 w-6" /></div>
          <p className="text-sm">Select an organisation to view its documents.</p>
        </div>
      )}

      {/* Loading */}
      {loading && (activeTab === "global" || selectedOrgId) && (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      )}

      {/* Results */}
      {!loading && (activeTab === "global" || selectedOrgId) && (
        <>
          {docs.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed py-16 text-center text-muted-foreground">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-muted"><BookOpen className="h-6 w-6" /></div>
              <p className="text-sm">No documents found.</p>
              {activeTab === "org" && canUploadOrg && (
                <Button size="sm" variant="outline" className="gap-1.5 mt-2" onClick={() => setUploadDialogOpen(true)}>
                  <Plus className="h-3.5 w-3.5" /> Upload first document
                </Button>
              )}
            </div>
          ) : (
            <div className="space-y-2">
              {docs.map((doc) => (
                <DocumentRow
                  key={doc.id}
                  doc={doc}
                  onDownload={handleDownload}
                  downloading={downloading === doc.id}
                  canManage={activeTab === "org" && canUploadOrg}
                  onEdit={(d) => { setSelectedDoc(d); setAction("edit") }}
                  onReplace={(d) => { setSelectedDoc(d); setAction("replace") }}
                  onDelete={(d) => { setSelectedDoc(d); setAction("delete") }}
                  onHistory={(d) => { setSelectedDoc(d); setAction("history") }}
                />
              ))}
            </div>
          )}
          {total > docs.length && (
            <p className="text-center text-xs text-muted-foreground">
              Showing {docs.length} of {total} documents
            </p>
          )}
        </>
      )}

      {/* Upload dialog */}
      <UploadDialog
        open={uploadDialogOpen}
        onClose={() => setUploadDialogOpen(false)}
        orgId={selectedOrgId ?? ""}
        categories={categories}
        onSuccess={handleRefresh}
      />

      {/* Edit dialog */}
      <EditDialog
        open={action === "edit"}
        onClose={() => { setAction(null); setSelectedDoc(null) }}
        doc={selectedDoc}
        categories={categories}
        onSuccess={handleRefresh}
      />

      {/* Replace dialog */}
      <ReplaceDialog
        open={action === "replace"}
        onClose={() => { setAction(null); setSelectedDoc(null) }}
        doc={selectedDoc}
        onSuccess={handleRefresh}
      />

      {/* Delete dialog */}
      <DeleteDialog
        open={action === "delete"}
        onClose={() => { setAction(null); setSelectedDoc(null) }}
        doc={selectedDoc}
        onSuccess={handleRefresh}
      />

      {/* History dialog */}
      <HistoryDialog
        open={action === "history"}
        onClose={() => { setAction(null); setSelectedDoc(null) }}
        doc={selectedDoc}
        onSuccess={handleRefresh}
      />
    </div>
  )
}
