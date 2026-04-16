"use client"

import { useEffect, useState, useCallback } from "react"
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
  BookOpen,
  Download,
  Upload,
  Search,
  RefreshCw,
  AlertTriangle,
  Loader2,
  FileText,
  X,
  Plus,
  Filter,
  Trash2,
  Pencil,
  ShieldCheck,
  ClipboardList,
  Book,
  FileCode,
  Info,
  CheckCircle2,
  Box,
  GraduationCap,
  MoreHorizontal,
  ArrowRight,
  Archive,
} from "lucide-react"
import {
  listDocCategories,
  listOrgDocs,
  getDocDownloadUrl,
  uploadOrgDoc,
  deleteDocument,
  updateDocument,
} from "@/lib/api/docs"
import type { DocCategoryResponse, DocumentResponse } from "@/lib/api/docs"
import { useOrgWorkspace } from "@/lib/context/OrgWorkspaceContext"
import { useAccess } from "@/components/providers/AccessProvider"

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

const CATEGORY_MAP: Record<string, { icon: any; color: string }> = {
  policy: { icon: ShieldCheck, color: "text-blue-500 bg-blue-500/10" },
  procedure: { icon: ClipboardList, color: "text-indigo-500 bg-indigo-500/10" },
  framework_guide: { icon: Book, color: "text-emerald-500 bg-emerald-500/10" },
  template: { icon: FileCode, color: "text-amber-500 bg-amber-500/10" },
  reference: { icon: Info, color: "text-slate-500 bg-slate-500/10" },
  compliance: { icon: CheckCircle2, color: "text-green-500 bg-green-500/10" },
  sandbox: { icon: Box, color: "text-purple-500 bg-purple-500/10" },
  training: { icon: GraduationCap, color: "text-rose-500 bg-rose-500/10" },
  other: { icon: MoreHorizontal, color: "text-muted-foreground bg-muted" },
}

function CategoryIcon({ code, className = "h-4 w-4" }: { code: string; className?: string }) {
  const { icon: Icon, color } = CATEGORY_MAP[code] || CATEGORY_MAP.other
  return <Icon className={`${className} ${color} p-1 rounded-md`} />
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
          <DialogTitle>Upload Document</DialogTitle>
          <DialogDescription>
            Upload a document to your organisation&apos;s library.
          </DialogDescription>
        </DialogHeader>
        <div className="flex flex-col gap-4 py-2">
          {error && (
            <div className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              <AlertTriangle className="h-4 w-4 shrink-0" />{error}
            </div>
          )}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="s-title">Title *</Label>
            <Input id="s-title" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Document title" maxLength={500} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="s-category">Category *</Label>
            <select id="s-category" className="h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm" value={categoryCode} onChange={(e) => setCategoryCode(e.target.value)}>
              <option value="">Select category…</option>
              {categories.map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
            </select>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="s-desc">Description</Label>
            <textarea id="s-desc" className="min-h-[64px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm resize-none" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Optional description" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="s-tags">Tags</Label>
              <Input id="s-tags" value={tagsInput} onChange={(e) => setTagsInput(e.target.value)} placeholder="iso27001, soc2" />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="s-version">Version</Label>
              <Input id="s-version" value={versionLabel} onChange={(e) => setVersionLabel(e.target.value)} placeholder="v1.0" />
            </div>
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="s-file">File *</Label>
            <input id="s-file" type="file" className="block w-full text-sm text-muted-foreground file:mr-3 file:rounded-md file:border file:border-input file:bg-background file:px-3 file:py-1 file:text-xs file:font-medium file:text-foreground" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
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
// Main settings org docs page
// ─────────────────────────────────────────────────────────────────────────────

export default function OrgDocsSettingsPage() {
  const { selectedOrgId } = useOrgWorkspace()
  const { canWrite, isOrgAdmin } = useAccess()

  const [categories, setCategories] = useState<DocCategoryResponse[]>([])
  const [docs, setDocs] = useState<DocumentResponse[]>([])
  const [total, setTotal] = useState(0)
  const [search, setSearch] = useState("")
  const [categoryFilter, setCategoryFilter] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const canUpload = canWrite("docs") || isOrgAdmin
  const canManageDocs = canWrite("docs")

  const loadData = useCallback(async () => {
    if (!selectedOrgId) return
    setLoading(true)
    setError(null)
    try {
      const res = await listOrgDocs(selectedOrgId, {
        search: search || undefined,
        category_code: categoryFilter || undefined,
      })
      setDocs(res.items)
      setTotal(res.total)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load documents")
    } finally {
      setLoading(false)
    }
  }, [selectedOrgId, search, categoryFilter])

  useEffect(() => {
    listDocCategories().then(setCategories).catch(() => {})
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

  const handleDownload = useCallback(async (doc: DocumentResponse) => {
    try {
      const result = await getDocDownloadUrl(doc.id)
      window.open(result.download_url, "_blank", "noopener,noreferrer")
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Download failed")
    }
  }, [])

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <BookOpen className="h-5 w-5" />
            Organisation Documents
          </h2>
          <p className="text-sm text-muted-foreground mt-0.5">
            Manage documents belonging to this organisation.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {canUpload && selectedOrgId && (
            <Button size="sm" className="gap-1.5" onClick={() => setUploadDialogOpen(true)}>
              <Plus className="h-4 w-4" />Upload
            </Button>
          )}
          <Button size="sm" variant="outline" onClick={loadData} disabled={loading}>
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {!selectedOrgId && (
        <div className="flex flex-col gap-8 animate-in fade-in slide-in-from-bottom-2 duration-500">
          <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 px-4 py-4 backdrop-blur-sm shadow-sm flex items-start gap-4">
            <div className="p-2 rounded-lg bg-amber-500/20 text-amber-600 dark:text-amber-400">
              <AlertTriangle className="h-5 w-5" />
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-amber-900 dark:text-amber-300">Organisation Context Required</h3>
              <p className="text-xs text-amber-800/80 dark:text-amber-400/80 mt-1">
                Select an organisation from the switcher to manage its compliance documents and library.
              </p>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Document Infrastructure</h3>
              <Badge variant="outline" className="text-[10px]">Ready</Badge>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {categories.map((cat) => {
                const { icon: Icon, color } = CATEGORY_MAP[cat.code] || CATEGORY_MAP.other
                return (
                  <Card key={cat.code} className="group hover:border-primary/30 transition-all duration-300 hover:shadow-md bg-card/50">
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        <div className={`p-2 rounded-xl ${color} transition-transform group-hover:scale-110`}>
                          <Icon className="h-5 w-5" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="text-sm font-semibold group-hover:text-primary transition-colors">{cat.name}</h4>
                          <p className="text-xs text-muted-foreground mt-1 line-clamp-2 leading-relaxed">
                            {cat.description || "No description provided."}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          </div>

          <div className="rounded-xl border border-dashed border-border bg-muted/30 p-8 text-center">
            <Archive className="mx-auto h-8 w-8 text-muted-foreground/50 mb-3" />
            <h4 className="text-sm font-medium">Ready to build your library?</h4>
            <p className="text-xs text-muted-foreground mt-1 max-w-xs mx-auto">
              Once an organisation is selected, you can upload policies, evidence, and procedures to maintain compliance records.
            </p>
          </div>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input className="pl-8" placeholder="Search…" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <select
          className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm"
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
        >
          <option value="">All categories</option>
          {categories.map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
        </select>
        <Button size="sm" variant="outline" onClick={loadData}>Search</Button>
        {(search || categoryFilter) && (
          <Button size="sm" variant="ghost" onClick={() => { setSearch(""); setCategoryFilter("") }}>
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertTriangle className="h-4 w-4 shrink-0" />{error}
          <Button size="sm" variant="ghost" className="ml-auto h-6 px-2" onClick={() => setError(null)}>
            <X className="h-3.5 w-3.5" />
          </Button>
        </div>
      )}

      {selectedOrgId && (
        loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : docs.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed py-16 text-center text-muted-foreground">
            <BookOpen className="h-8 w-8" />
            <p className="text-sm">No documents found.</p>
            {canUpload && (
              <Button size="sm" variant="outline" className="gap-1.5" onClick={() => setUploadDialogOpen(true)}>
                <Plus className="h-4 w-4" />Upload first document
              </Button>
            )}
          </div>
        ) : (
          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border bg-muted/40">
                      <th className="px-4 py-3 text-left font-medium text-muted-foreground">Document</th>
                      <th className="px-4 py-3 text-left font-medium text-muted-foreground">Category</th>
                      <th className="px-4 py-3 text-left font-medium text-muted-foreground">Size</th>
                      <th className="px-4 py-3 text-left font-medium text-muted-foreground">Uploaded</th>
                      <th className="px-4 py-3 text-right font-medium text-muted-foreground">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {docs.map((doc, idx) => (
                      <tr key={doc.id} className={`border-b border-border last:border-0 ${idx % 2 === 0 ? "" : "bg-muted/20"}`}>
                        <td className="px-4 py-3">
                          <div className="flex items-start gap-2">
                            <FileText className="h-4 w-4 text-muted-foreground mt-0.5 shrink-0" />
                            <div>
                              <p className="font-medium">{doc.title}</p>
                              <p className="text-[11px] text-muted-foreground">{doc.original_filename}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <CategoryIcon code={doc.category_code} />
                            <span className="text-muted-foreground text-[12px]">{doc.category_name ?? doc.category_code}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-muted-foreground text-[12px] font-mono">{fmtFileSize(doc.file_size_bytes)}</td>
                        <td className="px-4 py-3 text-muted-foreground text-[12px]">{fmtDate(doc.created_at)}</td>
                        <td className="px-4 py-3">
                          <div className="flex items-center justify-end gap-1">
                            <Button size="sm" variant="ghost" className="h-7 w-7 p-0" onClick={() => handleDownload(doc)} title="Download">
                              <Download className="h-3.5 w-3.5" />
                            </Button>
                            {canManageDocs && (
                              <Button
                                size="sm"
                                variant="ghost"
                                className="h-7 w-7 p-0 text-destructive hover:text-destructive"
                                onClick={() => handleDelete(doc)}
                                disabled={deletingId === doc.id}
                                title="Delete"
                              >
                                {deletingId === doc.id ? (
                                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                ) : (
                                  <Trash2 className="h-3.5 w-3.5" />
                                )}
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {total > docs.length && (
                <div className="border-t border-border px-4 py-3 text-center text-xs text-muted-foreground">
                  Showing {docs.length} of {total} documents
                </div>
              )}
            </CardContent>
          </Card>
        )
      )}

      <UploadDialog
        open={uploadDialogOpen}
        onClose={() => setUploadDialogOpen(false)}
        orgId={selectedOrgId}
        categories={categories}
        onSuccess={loadData}
      />
    </div>
  )
}
