"use client"

import { useEffect, useState, useCallback } from "react"
import {
  Button,
  Input,
  Label,
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
  Trash2,
  Pencil,
  Eye,
  EyeOff,
  Layers,
} from "lucide-react"
import {
  listDocCategories,
  listGlobalDocs,
  listOrgDocs,
  getDocDownloadUrl,
  uploadGlobalDoc,
  deleteDocument,
  updateDocument,
} from "@/lib/api/docs"

import type { DocCategoryResponse, DocumentResponse } from "@/lib/api/docs"
import { listOrgs } from "@/lib/api/orgs"
import type { OrgResponse } from "@/lib/types/orgs"

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

const SCOPE_COLORS: Record<string, string> = {
  global: "bg-blue-500/10 text-blue-600 border-blue-500/20",
  org: "bg-purple-500/10 text-purple-600 border-purple-500/20",
}

// border-l-[3px] color by category
function docBorderCls(categoryCode: string): string {
  const map: Record<string, string> = {
    policy:      "border-l-primary",
    procedure:   "border-l-blue-500",
    standard:    "border-l-purple-500",
    guideline:   "border-l-green-500",
    template:    "border-l-amber-500",
    regulation:  "border-l-red-500",
  }
  return map[categoryCode?.toLowerCase()] ?? "border-l-primary"
}

// KPI stat helpers
function statBorderCls(label: string): string {
  if (label === "Global Docs") return "border-l-blue-500"
  if (label === "Org Docs") return "border-l-purple-500"
  if (label === "Categories") return "border-l-amber-500"
  return "border-l-primary"
}
function statNumCls(_label: string): string {
  return "text-foreground"
}

// Active filter chip
function FilterChip({ label, onRemove }: { label: string; onRemove: () => void }) {
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-primary/10 border border-primary/20 text-xs text-primary font-medium">
      {label}
      <button type="button" onClick={onRemove} className="ml-0.5 hover:text-primary/70">
        <X className="w-3 h-3" />
      </button>
    </span>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Upload dialog (global)
// ─────────────────────────────────────────────────────────────────────────────

interface UploadGlobalDialogProps {
  open: boolean
  onClose: () => void
  categories: DocCategoryResponse[]
  onSuccess: () => void
}

function UploadGlobalDialog({ open, onClose, categories, onSuccess }: UploadGlobalDialogProps) {
  const [title, setTitle] = useState("")
  const [categoryCode, setCategoryCode] = useState("")
  const [description, setDescription] = useState("")
  const [tagsInput, setTagsInput] = useState("")
  const [versionLabel, setVersionLabel] = useState("")
  const [file, setFile] = useState<File | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const reset = useCallback(() => {
    setTitle(""); setCategoryCode(""); setDescription("")
    setTagsInput(""); setVersionLabel(""); setFile(null); setError(null)
  }, [])

  const handleClose = useCallback(() => { reset(); onClose() }, [reset, onClose])

  const handleSubmit = useCallback(async () => {
    if (!title.trim()) { setError("Title is required"); return }
    if (!categoryCode) { setError("Category is required"); return }
    if (!file) { setError("Please select a file"); return }
    setSubmitting(true)
    setError(null)
    try {
      const fd = new FormData()
      fd.append("title", title.trim())
      fd.append("category_code", categoryCode)
      if (description.trim()) fd.append("description", description.trim())
      fd.append("tags", tagsInput)
      if (versionLabel.trim()) fd.append("version_label", versionLabel.trim())
      fd.append("file", file)
      await uploadGlobalDoc(fd)
      handleClose()
      onSuccess()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Upload failed")
    } finally {
      setSubmitting(false)
    }
  }, [title, categoryCode, description, tagsInput, versionLabel, file, handleClose, onSuccess])

  return (
    <Dialog open={open} onOpenChange={(v) => !v && handleClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Upload Global Document</DialogTitle>
          <DialogDescription>
            Upload a document to the global library. Visible to all authenticated users.
          </DialogDescription>
        </DialogHeader>
        <div className="flex flex-col gap-4 py-2">
          {error && (
            <div className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              <AlertTriangle className="h-4 w-4 shrink-0" />{error}
            </div>
          )}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="g-title">Title *</Label>
            <Input id="g-title" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Document title" maxLength={500} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="g-category">Category *</Label>
            <select id="g-category" className="h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm" value={categoryCode} onChange={(e) => setCategoryCode(e.target.value)}>
              <option value="">Select category…</option>
              {categories.map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
            </select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="g-desc">Description</Label>
            <textarea id="g-desc" className="min-h-[64px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm resize-none" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Optional description" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="g-tags">Tags</Label>
              <Input id="g-tags" value={tagsInput} onChange={(e) => setTagsInput(e.target.value)} placeholder="iso27001, soc2" />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="g-version">Version</Label>
              <Input id="g-version" value={versionLabel} onChange={(e) => setVersionLabel(e.target.value)} placeholder="v1.0" />
            </div>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="g-file">File *</Label>
            <input id="g-file" type="file" className="block w-full text-sm text-muted-foreground file:mr-3 file:rounded-md file:border file:border-input file:bg-background file:px-3 file:py-1 file:text-xs file:font-medium file:text-foreground" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={submitting}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={submitting}>
            {submitting ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Uploading…</> : <><Upload className="mr-2 h-4 w-4" />Upload</>}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Edit metadata dialog
// ─────────────────────────────────────────────────────────────────────────────

interface EditDialogProps {
  open: boolean
  doc: DocumentResponse | null
  categories: DocCategoryResponse[]
  onClose: () => void
  onSuccess: () => void
}

function EditDialog({ open, doc, categories, onClose, onSuccess }: EditDialogProps) {
  const [title, setTitle] = useState(doc?.title ?? "")
  const [categoryCode, setCategoryCode] = useState(doc?.category_code ?? "")
  const [description, setDescription] = useState(doc?.description ?? "")
  const [tagsInput, setTagsInput] = useState(doc?.tags.join(", ") ?? "")
  const [versionLabel, setVersionLabel] = useState(doc?.version_label ?? "")
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (doc) {
      setTitle(doc.title)
      setCategoryCode(doc.category_code)
      setDescription(doc.description ?? "")
      setTagsInput(doc.tags.join(", "))
      setVersionLabel(doc.version_label ?? "")
      setError(null)
    }
  }, [doc])

  const handleSubmit = useCallback(async () => {
    if (!doc) return
    if (!title.trim()) { setError("Title is required"); return }
    setSubmitting(true)
    setError(null)
    try {
      await updateDocument(doc.id, {
        title: title.trim(),
        description: description.trim() || null,
        tags: tagsInput.split(",").map((t) => t.trim()).filter(Boolean),
        version_label: versionLabel.trim() || null,
        category_code: categoryCode || null,
      })
      onClose()
      onSuccess()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Update failed")
    } finally {
      setSubmitting(false)
    }
  }, [doc, title, description, tagsInput, versionLabel, categoryCode, onClose, onSuccess])

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Edit Document</DialogTitle>
          <DialogDescription>Update document metadata.</DialogDescription>
        </DialogHeader>
        <div className="flex flex-col gap-4 py-2">
          {error && (
            <div className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              <AlertTriangle className="h-4 w-4 shrink-0" />{error}
            </div>
          )}
          <div className="flex flex-col gap-1.5">
            <Label>Title *</Label>
            <Input value={title} onChange={(e) => setTitle(e.target.value)} maxLength={500} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Category</Label>
            <select className="h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm" value={categoryCode} onChange={(e) => setCategoryCode(e.target.value)}>
              <option value="">Select category…</option>
              {categories.map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
            </select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Description</Label>
            <textarea className="min-h-[64px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm resize-none" value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label>Tags</Label>
              <Input value={tagsInput} onChange={(e) => setTagsInput(e.target.value)} placeholder="tag1, tag2" />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label>Version</Label>
              <Input value={versionLabel} onChange={(e) => setVersionLabel(e.target.value)} placeholder="v1.0" />
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={submitting}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={submitting}>
            {submitting ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Saving…</> : "Save"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Document row
// ─────────────────────────────────────────────────────────────────────────────

function DocRow({
  doc,
  togglingId,
  deletingId,
  onEdit,
  onDownload,
  onToggleVisibility,
  onDelete,
}: {
  doc: DocumentResponse
  togglingId: string | null
  deletingId: string | null
  onEdit: (doc: DocumentResponse) => void
  onDownload: (doc: DocumentResponse) => void
  onToggleVisibility: (doc: DocumentResponse) => void
  onDelete: (doc: DocumentResponse) => void
}) {
  const borderCls = docBorderCls(doc.category_code ?? "")

  return (
    <div className={`flex items-center gap-3 px-4 py-3 rounded-xl border border-l-[3px] ${borderCls} border-border bg-card hover:bg-muted/30 transition-colors`}>
      {/* Icon */}
      <div className="shrink-0 rounded-lg p-2 bg-muted">
        <FileText className="w-3.5 h-3.5 text-muted-foreground" />
      </div>

      {/* Title + meta */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-medium text-sm truncate max-w-[280px]">{doc.title}</span>
          <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium ${SCOPE_COLORS[doc.scope] ?? ""}`}>
            {doc.scope === "global" ? <Globe className="h-3 w-3" /> : <Building2 className="h-3 w-3" />}
            {doc.scope}
          </span>
          {doc.version_label && (
            <span className="font-mono text-[10px] text-muted-foreground border border-border/50 rounded px-1">{doc.version_label}</span>
          )}
        </div>
        <div className="flex items-center gap-3 mt-0.5 text-[11px] text-muted-foreground flex-wrap">
          <span>{doc.category_name ?? doc.category_code}</span>
          <span>{fmtFileSize(doc.file_size_bytes)}</span>
          <span>{fmtDate(doc.created_at)}</span>
          {doc.tags.length > 0 && (
            <span className="flex gap-1">
              {doc.tags.slice(0, 3).map(tag => (
                <span key={tag} className="px-1.5 py-0 rounded border border-border/60 text-[10px]">{tag}</span>
              ))}
              {doc.tags.length > 3 && <span>+{doc.tags.length - 3}</span>}
            </span>
          )}
        </div>
      </div>

      {/* Visibility toggle */}
      <button
        type="button"
        onClick={() => onToggleVisibility(doc)}
        disabled={togglingId === doc.id}
        title={doc.is_visible ? "Visible to users — click to hide" : "Hidden from users — click to show"}
        className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[11px] font-medium transition-colors shrink-0 ${
          doc.is_visible
            ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/20 hover:bg-emerald-500/20"
            : "bg-muted text-muted-foreground border-border hover:bg-muted/80"
        }`}
      >
        {togglingId === doc.id ? (
          <Loader2 className="h-3 w-3 animate-spin" />
        ) : doc.is_visible ? (
          <Eye className="h-3 w-3" />
        ) : (
          <EyeOff className="h-3 w-3" />
        )}
        {doc.is_visible ? "visible" : "hidden"}
      </button>

      {/* Actions */}
      <div className="flex items-center gap-1 shrink-0">
        <Button size="sm" variant="ghost" className="h-7 w-7 p-0" onClick={() => onDownload(doc)} title="Download">
          <Download className="h-3.5 w-3.5" />
        </Button>
        <Button size="sm" variant="ghost" className="h-7 w-7 p-0" onClick={() => onEdit(doc)} title="Edit">
          <Pencil className="h-3.5 w-3.5" />
        </Button>
        <Button
          size="sm"
          variant="ghost"
          className="h-7 w-7 p-0 text-destructive hover:text-destructive"
          onClick={() => onDelete(doc)}
          disabled={deletingId === doc.id}
          title="Delete"
        >
          {deletingId === doc.id ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Trash2 className="h-3.5 w-3.5" />
          )}
        </Button>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Main admin page
// ─────────────────────────────────────────────────────────────────────────────

type ScopeFilter = "all" | "global" | "org"

export default function AdminDocsPage() {
  const [categories, setCategories] = useState<DocCategoryResponse[]>([])
  const [orgs, setOrgs] = useState<OrgResponse[]>([])
  const [docs, setDocs] = useState<DocumentResponse[]>([])
  const [total, setTotal] = useState(0)
  const [search, setSearch] = useState("")
  const [categoryFilter, setCategoryFilter] = useState("")
  const [scopeFilter, setScopeFilter] = useState<ScopeFilter>("all")
  const [selectedOrgId, setSelectedOrgId] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false)
  const [editDoc, setEditDoc] = useState<DocumentResponse | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [togglingId, setTogglingId] = useState<string | null>(null)

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const results: DocumentResponse[] = []
      let resultTotal = 0

      if (scopeFilter === "global" || scopeFilter === "all") {
        const g = await listGlobalDocs({
          search: search || undefined,
          category_code: categoryFilter || undefined,
          per_page: 100,
          include_all: true,
        })
        results.push(...g.items)
        resultTotal += g.total
      }

      if (scopeFilter === "org" || scopeFilter === "all") {
        const orgList = selectedOrgId ? [{ id: selectedOrgId }] : orgs
        for (const org of orgList.slice(0, 10)) {
          const o = await listOrgDocs(org.id, {
            search: search || undefined,
            category_code: categoryFilter || undefined,
            per_page: 50,
            include_all: true,
          })
          results.push(...o.items)
          resultTotal += o.total
        }
      }

      setDocs(results)
      setTotal(resultTotal)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load documents")
    } finally {
      setLoading(false)
    }
  }, [search, categoryFilter, scopeFilter, selectedOrgId, orgs])

  useEffect(() => {
    const init = async () => {
      try {
        const [cats, orgList] = await Promise.all([listDocCategories(), listOrgs()])
        setCategories(cats)
        setOrgs(orgList)
      } catch {
        // non-fatal
      }
    }
    init()
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleDelete = useCallback(async (doc: DocumentResponse) => {
    if (!confirm(`Delete "${doc.title}"? This action cannot be undone.`)) return
    setDeletingId(doc.id)
    try {
      await deleteDocument(doc.id)
      setDocs((prev) => prev.filter((d) => d.id !== doc.id))
      setTotal((prev) => prev - 1)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Delete failed")
    } finally {
      setDeletingId(null)
    }
  }, [])

  const handleToggleVisibility = useCallback(async (doc: DocumentResponse) => {
    setTogglingId(doc.id)
    try {
      const updated = await updateDocument(doc.id, { is_visible: !doc.is_visible })
      setDocs((prev) => prev.map((d) => d.id === doc.id ? updated : d))
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to toggle visibility")
    } finally {
      setTogglingId(null)
    }
  }, [])

  const handleDownload = useCallback(async (doc: DocumentResponse) => {
    try {
      const result = await getDocDownloadUrl(doc.id)
      window.open(result.download_url, "_blank", "noopener,noreferrer")
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Download failed")
    }
  }, [])

  const categoryFilterName = categories.find(c => c.code === categoryFilter)?.name ?? categoryFilter
  const selectedOrgName = orgs.find(o => o.id === selectedOrgId)?.name ?? "Org"
  const hasFilters = search || categoryFilter || scopeFilter !== "all" || selectedOrgId

  const statCards = [
    { label: "Total Documents", value: total,                                          icon: FileText  },
    { label: "Global Docs",     value: docs.filter((d) => d.scope === "global").length, icon: Globe     },
    { label: "Org Docs",        value: docs.filter((d) => d.scope === "org").length,    icon: Building2 },
    { label: "Categories",      value: categories.length,                               icon: Layers    },
  ]

  return (
    <div className="flex flex-col gap-6 p-6 max-w-5xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold flex items-center gap-2">
            <BookOpen className="h-5 w-5" />
            Document Library
          </h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Manage all global and org-scoped documents across the platform.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button size="sm" className="gap-1.5" onClick={() => setUploadDialogOpen(true)}>
            <Plus className="h-4 w-4" />
            Upload Global Doc
          </Button>
          <Button size="sm" variant="ghost" className="h-8 w-8 p-0" onClick={loadData} disabled={loading} title="Refresh">
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {/* KPI Stat Cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {statCards.map((stat) => {
          const borderCls = statBorderCls(stat.label)
          const numCls = statNumCls(stat.label)
          return (
            <div key={stat.label} className={`relative flex items-center gap-3 rounded-xl border border-l-[3px] ${borderCls} bg-card px-4 py-3`}>
              <div className="shrink-0 rounded-lg p-2 bg-muted">
                <stat.icon className="w-4 h-4 text-muted-foreground" />
              </div>
              <div className="min-w-0">
                <div className={`text-2xl font-bold tabular-nums leading-none ${numCls}`}>{stat.value}</div>
                <span className="text-[11px] text-muted-foreground mt-0.5 block truncate">{stat.label}</span>
              </div>
            </div>
          )
        })}
      </div>

      {/* Filter bar */}
      <div className="rounded-xl border border-border bg-card px-4 py-3 space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative flex-1 min-w-[200px] max-w-sm">
            <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="pl-8 h-9"
              placeholder="Search documents…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <select
            className="h-9 rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
            value={scopeFilter}
            onChange={(e) => setScopeFilter(e.target.value as ScopeFilter)}
          >
            <option value="all">All scopes</option>
            <option value="global">Global only</option>
            <option value="org">Org only</option>
          </select>
          <select
            className="h-9 rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
          >
            <option value="">All categories</option>
            {categories.map((c) => (
              <option key={c.code} value={c.code}>{c.name}</option>
            ))}
          </select>
          {(scopeFilter === "org" || scopeFilter === "all") && (
            <select
              className="h-9 rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              value={selectedOrgId}
              onChange={(e) => setSelectedOrgId(e.target.value)}
            >
              <option value="">All orgs</option>
              {orgs.map((o) => (
                <option key={o.id} value={o.id}>{o.name}</option>
              ))}
            </select>
          )}
          <Button size="sm" variant="outline" onClick={loadData} className="h-9">Search</Button>
        </div>

        {/* Active chips */}
        {hasFilters && (
          <div className="flex items-center gap-2 flex-wrap">
            {search && <FilterChip label={`"${search}"`} onRemove={() => setSearch("")} />}
            {categoryFilter && <FilterChip label={categoryFilterName} onRemove={() => setCategoryFilter("")} />}
            {scopeFilter !== "all" && <FilterChip label={scopeFilter === "global" ? "Global only" : "Org only"} onRemove={() => setScopeFilter("all")} />}
            {selectedOrgId && <FilterChip label={selectedOrgName} onRemove={() => setSelectedOrgId("")} />}
            <button
              type="button"
              className="text-xs text-muted-foreground hover:text-foreground ml-1"
              onClick={() => { setSearch(""); setCategoryFilter(""); setScopeFilter("all"); setSelectedOrgId("") }}
            >
              Clear all
            </button>
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertTriangle className="h-4 w-4 shrink-0" />{error}
          <Button size="sm" variant="ghost" className="ml-auto h-6 px-2" onClick={() => setError(null)}>
            <X className="h-3.5 w-3.5" />
          </Button>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      )}

      {/* Empty state */}
      {!loading && docs.length === 0 && (
        <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed py-16 text-center text-muted-foreground">
          <BookOpen className="h-8 w-8" />
          <p className="text-sm">No documents found.</p>
          <Button size="sm" variant="outline" className="gap-1.5" onClick={() => setUploadDialogOpen(true)}>
            <Plus className="h-4 w-4" />Upload first document
          </Button>
        </div>
      )}

      {/* Document rows */}
      {!loading && docs.length > 0 && (
        <div className="space-y-2">
          {docs.map((doc) => (
            <DocRow
              key={doc.id}
              doc={doc}
              togglingId={togglingId}
              deletingId={deletingId}
              onEdit={setEditDoc}
              onDownload={handleDownload}
              onToggleVisibility={handleToggleVisibility}
              onDelete={handleDelete}
            />
          ))}
          {total > docs.length && (
            <p className="text-center text-xs text-muted-foreground pt-2">
              Showing {docs.length} of {total} documents
            </p>
          )}
        </div>
      )}

      {/* Dialogs */}
      <UploadGlobalDialog
        open={uploadDialogOpen}
        onClose={() => setUploadDialogOpen(false)}
        categories={categories}
        onSuccess={loadData}
      />
      <EditDialog
        open={editDoc !== null}
        doc={editDoc}
        categories={categories}
        onClose={() => setEditDoc(null)}
        onSuccess={loadData}
      />
    </div>
  )
}
