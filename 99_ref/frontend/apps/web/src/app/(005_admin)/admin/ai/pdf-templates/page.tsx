"use client"

import { useEffect, useState, useCallback } from "react"
import {
  FileType, Plus, Pencil, Trash2, Loader2, Check, X, Star, Upload,
} from "lucide-react"
import { Card, CardContent, Button, Input } from "@kcontrol/ui"
import {
  listPdfTemplates, createPdfTemplate, updatePdfTemplate, deletePdfTemplate,
  setPdfTemplateDefault, uploadPdfShell,
  type PdfTemplateResponse, type CreatePdfTemplateRequest, type UpdatePdfTemplateRequest,
} from "@/lib/api/pdfTemplates"

const REPORT_TYPES = [
  { value: "evidence_report", label: "Evidence Report" },
  { value: "framework_compliance", label: "Framework Compliance" },
  { value: "control_status", label: "Control Status" },
  { value: "risk_summary", label: "Risk Summary" },
  { value: "task_health", label: "Task Health" },
  { value: "audit_trail", label: "Audit Trail" },
  { value: "executive_summary", label: "Executive Summary" },
  { value: "gap_analysis", label: "Gap Analysis" },
  { value: "vendor_assessment", label: "Vendor Assessment" },
]

const COVER_STYLES = [
  { value: "dark_navy", label: "Dark Navy", description: "Deep navy full-bleed cover" },
  { value: "light_minimal", label: "Light Minimal", description: "White cover with accent line" },
  { value: "gradient_accent", label: "Gradient Accent", description: "Gradient header band" },
] as const

type CoverStyle = typeof COVER_STYLES[number]["value"]

const EMPTY_FORM: CreatePdfTemplateRequest = {
  name: "",
  description: "",
  cover_style: "dark_navy",
  primary_color: "#1e2a45",
  secondary_color: "#c9a96e",
  header_text: "",
  footer_text: "",
  prepared_by: "",
  doc_ref_prefix: "",
  classification_label: "",
  applicable_report_types: [],
  is_default: false,
}

export default function PdfTemplatesAdminPage() {
  const [templates, setTemplates] = useState<PdfTemplateResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [editTarget, setEditTarget] = useState<PdfTemplateResponse | null>(null)
  const [form, setForm] = useState<CreatePdfTemplateRequest>(EMPTY_FORM)
  const [saving, setSaving] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<PdfTemplateResponse | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<number | null>(null)
  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await listPdfTemplates({ limit: 200 })
      setTemplates(res.items)
    } catch { /* ignore */ }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  function openCreate() {
    setEditTarget(null)
    setForm(EMPTY_FORM)
    setDrawerOpen(true)
  }

  function openEdit(t: PdfTemplateResponse) {
    setEditTarget(t)
    setForm({
      name: t.name,
      description: t.description ?? "",
      cover_style: t.cover_style,
      primary_color: t.primary_color,
      secondary_color: t.secondary_color,
      header_text: t.header_text ?? "",
      footer_text: t.footer_text ?? "",
      prepared_by: t.prepared_by ?? "",
      doc_ref_prefix: t.doc_ref_prefix ?? "",
      classification_label: t.classification_label ?? "",
      applicable_report_types: t.applicable_report_types,
      is_default: t.is_default,
    })
    setDrawerOpen(true)
  }

  function closeDrawer() {
    setDrawerOpen(false)
    setEditTarget(null)
  }

  async function handleSave() {
    if (!form.name.trim()) return
    setSaving(true)
    try {
      const payload = {
        ...form,
        description: form.description || undefined,
        header_text: form.header_text || undefined,
        footer_text: form.footer_text || undefined,
        prepared_by: form.prepared_by || undefined,
        doc_ref_prefix: form.doc_ref_prefix || undefined,
        classification_label: form.classification_label || undefined,
      }
      if (editTarget) {
        const updated = await updatePdfTemplate(editTarget.id, payload as UpdatePdfTemplateRequest)
        setTemplates(prev => prev.map(t => t.id === updated.id ? updated : t))
      } else {
        const created = await createPdfTemplate(payload)
        setTemplates(prev => [created, ...prev])
      }
      closeDrawer()
    } catch { /* TODO: toast error */ }
    finally { setSaving(false) }
  }

  async function handleDelete() {
    if (!deleteTarget) return
    setDeleting(true)
    try {
      await deletePdfTemplate(deleteTarget.id)
      setTemplates(prev => prev.filter(t => t.id !== deleteTarget.id))
      setDeleteTarget(null)
    } catch { /* TODO: toast error */ }
    finally { setDeleting(false) }
  }

  async function handleSetDefault(t: PdfTemplateResponse) {
    try {
      const updated = await setPdfTemplateDefault(t.id)
      setTemplates(prev => prev.map(x =>
        x.id === updated.id ? updated :
        (x.applicable_report_types.length === 0 && updated.applicable_report_types.length === 0)
          ? { ...x, is_default: false }
          : x
      ))
    } catch { /* TODO: toast error */ }
  }

  async function handleUploadShell(templateId: string, file: File) {
    setUploadProgress(0)
    try {
      const updated = await uploadPdfShell(templateId, file, setUploadProgress)
      setTemplates(prev => prev.map(t => t.id === updated.id ? updated : t))
    } catch { /* TODO: toast error */ }
    finally { setUploadProgress(null) }
  }

  function toggleReportType(type: string) {
    setForm(f => ({
      ...f,
      applicable_report_types: f.applicable_report_types?.includes(type)
        ? f.applicable_report_types.filter(t => t !== type)
        : [...(f.applicable_report_types ?? []), type],
    }))
  }

  return (
    <div className="max-w-5xl space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-start gap-4">
          <div className="rounded-xl bg-indigo-500/15 p-3 shrink-0">
            <FileType className="h-6 w-6 text-indigo-400" />
          </div>
          <div>
            <h2 className="text-2xl font-semibold text-foreground">PDF Templates</h2>
            <p className="text-sm text-muted-foreground mt-1">
              Define branded PDF layouts for AI report exports. Set defaults per report type.
            </p>
          </div>
        </div>
        <Button onClick={openCreate} className="gap-2">
          <Plus className="w-4 h-4" /> New Template
        </Button>
      </div>

      {loading ? (
        <div className="flex items-center gap-2 text-sm text-muted-foreground py-8">
          <Loader2 className="w-4 h-4 animate-spin" /> Loading templates…
        </div>
      ) : templates.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground text-sm">
            No PDF templates yet. Create one to customise report exports.
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {templates.map(t => (
            <Card key={t.id} className="border border-border">
              <CardContent className="py-4 px-5 flex items-start justify-between gap-4">
                <div className="flex items-start gap-3 min-w-0">
                  {/* Colour swatch */}
                  <div
                    className="w-8 h-8 rounded-md shrink-0 border border-border mt-0.5"
                    style={{ background: t.primary_color }}
                  />
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium text-sm text-foreground">{t.name}</span>
                      {t.is_default && (
                        <span className="text-[10px] font-semibold bg-amber-500/15 text-amber-500 px-1.5 py-0.5 rounded-full">
                          DEFAULT
                        </span>
                      )}
                      <span className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                        {COVER_STYLES.find(s => s.value === t.cover_style)?.label ?? t.cover_style}
                      </span>
                    </div>
                    {t.description && (
                      <p className="text-xs text-muted-foreground mt-0.5">{t.description}</p>
                    )}
                    <div className="flex flex-wrap gap-1 mt-1.5">
                      {t.applicable_report_types.length === 0 ? (
                        <span className="text-[10px] text-muted-foreground italic">All report types</span>
                      ) : t.applicable_report_types.map(rt => (
                        <span key={rt} className="text-[10px] bg-indigo-500/10 text-indigo-400 px-1.5 py-0.5 rounded">
                          {REPORT_TYPES.find(r => r.value === rt)?.label ?? rt}
                        </span>
                      ))}
                    </div>
                    {t.shell_file_name && (
                      <p className="text-[10px] text-muted-foreground mt-1">
                        Shell: {t.shell_file_name}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  {!t.is_default && (
                    <Button
                      variant="ghost" size="sm"
                      onClick={() => handleSetDefault(t)}
                      title="Set as default"
                      className="h-8 w-8 p-0 text-muted-foreground hover:text-amber-500"
                    >
                      <Star className="w-4 h-4" />
                    </Button>
                  )}
                  <label title="Upload PDF shell" className="cursor-pointer">
                    <Button
                      variant="ghost" size="sm" asChild
                      className="h-8 w-8 p-0 text-muted-foreground"
                    >
                      <span>
                        <Upload className="w-4 h-4" />
                      </span>
                    </Button>
                    <input
                      type="file" accept=".pdf" className="hidden"
                      onChange={e => {
                        const file = e.target.files?.[0]
                        if (file) handleUploadShell(t.id, file)
                        e.target.value = ""
                      }}
                    />
                  </label>
                  <Button
                    variant="ghost" size="sm"
                    onClick={() => openEdit(t)}
                    className="h-8 w-8 p-0 text-muted-foreground"
                  >
                    <Pencil className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="ghost" size="sm"
                    onClick={() => setDeleteTarget(t)}
                    className="h-8 w-8 p-0 text-muted-foreground hover:text-destructive"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {uploadProgress !== null && (
        <div className="fixed bottom-6 right-6 bg-background border border-border rounded-lg px-4 py-3 shadow-lg flex items-center gap-3 text-sm">
          <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
          Uploading shell PDF… {uploadProgress}%
        </div>
      )}

      {/* Create / Edit Drawer */}
      {drawerOpen && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div className="absolute inset-0 bg-black/40" onClick={closeDrawer} />
          <div className="relative z-10 w-full max-w-xl bg-background border-l border-border shadow-2xl overflow-y-auto flex flex-col">
            <div className="flex items-center justify-between px-6 py-4 border-b border-border">
              <h3 className="font-semibold text-base">
                {editTarget ? "Edit Template" : "New PDF Template"}
              </h3>
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={closeDrawer}>
                <X className="w-4 h-4" />
              </Button>
            </div>

            <div className="flex-1 px-6 py-5 space-y-5">
              {/* Name */}
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Name *</label>
                <Input
                  value={form.name}
                  onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                  placeholder="e.g. Kreesalis Standard"
                />
              </div>

              {/* Description */}
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Description</label>
                <Input
                  value={form.description ?? ""}
                  onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                  placeholder="Optional description"
                />
              </div>

              {/* Cover Style */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Cover Style</label>
                <div className="grid grid-cols-3 gap-2">
                  {COVER_STYLES.map(s => (
                    <button
                      key={s.value}
                      type="button"
                      onClick={() => setForm(f => ({ ...f, cover_style: s.value as CoverStyle }))}
                      className={`rounded-lg border p-3 text-left transition-colors ${
                        form.cover_style === s.value
                          ? "border-indigo-500 bg-indigo-500/10"
                          : "border-border hover:border-muted-foreground"
                      }`}
                    >
                      <p className="text-xs font-medium">{s.label}</p>
                      <p className="text-[10px] text-muted-foreground mt-0.5">{s.description}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Colors */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Primary Colour</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="color"
                      value={form.primary_color}
                      onChange={e => setForm(f => ({ ...f, primary_color: e.target.value }))}
                      className="h-9 w-12 rounded border border-input cursor-pointer bg-background p-1"
                    />
                    <Input
                      value={form.primary_color}
                      onChange={e => setForm(f => ({ ...f, primary_color: e.target.value }))}
                      className="font-mono text-xs"
                      maxLength={7}
                    />
                  </div>
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Secondary Colour</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="color"
                      value={form.secondary_color}
                      onChange={e => setForm(f => ({ ...f, secondary_color: e.target.value }))}
                      className="h-9 w-12 rounded border border-input cursor-pointer bg-background p-1"
                    />
                    <Input
                      value={form.secondary_color}
                      onChange={e => setForm(f => ({ ...f, secondary_color: e.target.value }))}
                      className="font-mono text-xs"
                      maxLength={7}
                    />
                  </div>
                </div>
              </div>

              {/* Text overrides */}
              <div className="space-y-3">
                <label className="text-sm font-medium">Text Overrides</label>
                <div className="space-y-2">
                  <div>
                    <label className="text-xs text-muted-foreground">Running Header</label>
                    <Input
                      value={form.header_text ?? ""}
                      onChange={e => setForm(f => ({ ...f, header_text: e.target.value }))}
                      placeholder="Defaults to report title"
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground">Running Footer</label>
                    <Input
                      value={form.footer_text ?? ""}
                      onChange={e => setForm(f => ({ ...f, footer_text: e.target.value }))}
                      placeholder="Defaults to © Kreesalis · Confidential"
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground">Prepared By</label>
                    <Input
                      value={form.prepared_by ?? ""}
                      onChange={e => setForm(f => ({ ...f, prepared_by: e.target.value }))}
                      placeholder="e.g. Kreesalis Security Team"
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground">Document Reference Prefix</label>
                    <Input
                      value={form.doc_ref_prefix ?? ""}
                      onChange={e => setForm(f => ({ ...f, doc_ref_prefix: e.target.value }))}
                      placeholder="e.g. KSR-2026"
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground">Classification Label</label>
                    <Input
                      value={form.classification_label ?? ""}
                      onChange={e => setForm(f => ({ ...f, classification_label: e.target.value }))}
                      placeholder="Defaults to CONFIDENTIAL"
                      className="mt-1"
                    />
                  </div>
                </div>
              </div>

              {/* Applicable report types */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Applicable Report Types</label>
                <p className="text-xs text-muted-foreground">
                  Leave all unchecked to apply to all report types.
                </p>
                <div className="grid grid-cols-2 gap-1.5">
                  {REPORT_TYPES.map(rt => {
                    const checked = form.applicable_report_types?.includes(rt.value) ?? false
                    return (
                      <button
                        key={rt.value}
                        type="button"
                        onClick={() => toggleReportType(rt.value)}
                        className={`flex items-center gap-2 rounded-md border px-3 py-2 text-left text-xs transition-colors ${
                          checked
                            ? "border-indigo-500 bg-indigo-500/10 text-indigo-300"
                            : "border-border text-muted-foreground hover:border-muted-foreground"
                        }`}
                      >
                        <div className={`w-3.5 h-3.5 rounded border shrink-0 flex items-center justify-center ${
                          checked ? "bg-indigo-500 border-indigo-500" : "border-border"
                        }`}>
                          {checked && <Check className="w-2.5 h-2.5 text-white" />}
                        </div>
                        {rt.label}
                      </button>
                    )
                  })}
                </div>
              </div>

              {/* Set as default */}
              <label className="flex items-center gap-3 cursor-pointer select-none">
                <div
                  onClick={() => setForm(f => ({ ...f, is_default: !f.is_default }))}
                  className={`w-9 h-5 rounded-full transition-colors relative shrink-0 ${
                    form.is_default ? "bg-indigo-500" : "bg-muted"
                  }`}
                >
                  <div className={`absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-transform ${
                    form.is_default ? "translate-x-4" : "translate-x-0.5"
                  }`} />
                </div>
                <span className="text-sm">Set as default template</span>
              </label>
            </div>

            <div className="px-6 py-4 border-t border-border flex justify-end gap-2">
              <Button variant="outline" onClick={closeDrawer} disabled={saving}>Cancel</Button>
              <Button onClick={handleSave} disabled={saving || !form.name.trim()}>
                {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                {editTarget ? "Save Changes" : "Create Template"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Delete confirmation */}
      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/50" onClick={() => setDeleteTarget(null)} />
          <div className="relative z-10 bg-background border border-border rounded-xl shadow-2xl p-6 w-full max-w-sm space-y-4">
            <h3 className="font-semibold">Delete Template</h3>
            <p className="text-sm text-muted-foreground">
              Delete <span className="font-medium text-foreground">{deleteTarget.name}</span>? This cannot be undone.
            </p>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setDeleteTarget(null)} disabled={deleting}>
                Cancel
              </Button>
              <Button variant="destructive" onClick={handleDelete} disabled={deleting}>
                {deleting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                Delete
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
