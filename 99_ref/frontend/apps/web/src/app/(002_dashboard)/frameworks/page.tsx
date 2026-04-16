"use client"

import Link from "next/link"
import { useEffect, useState, useCallback, useMemo } from "react"
import { useRouter, useSearchParams } from "next/navigation"
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
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@kcontrol/ui"
import {
  Library,
  Search,
  Plus,
  Rocket,
  Sparkles,
  ChevronDown,
  ChevronRight,
  Layers,
  ShieldCheck,
  BookOpen,
  Pencil,
  Trash2,
  GitBranch,
  Upload,
  AlertTriangle,
  FileText,
  X,
  ExternalLink,
  MessageSquare,
  Paperclip,
  RefreshCw,
  ArrowUpDown,
  Download,
  RotateCcw,
  Clock,
  SlidersHorizontal,
  TableProperties,
  List,
  Send,
  CheckCircle2,
  XCircle,
  ArrowRight,
  PlusCircle,
  MinusCircle,
  Loader2,
  GitCompare,
  Bell,
  HeartPulse,
  Lock,
  Zap,
  Globe,
  ArrowUpRight,
  ListTodo,
} from "lucide-react"
import {
  listFrameworks,
  listFrameworkTypes,
  listFrameworkCategories,
  createFramework,
  updateFramework,
  deleteFramework,
  listVersions,
  createVersion,
  publishVersion,
  deprecateVersion,
  restoreVersion,
  listRequirements,
  createRequirement,
  listControls,
  exportFrameworkBundle,
  importFrameworkBundle,
  submitFrameworkForReview,
  listDeployments,
  deployFramework,
  updateDeployment,
  deleteDeployment,
  getUpgradeDiff,
  listTestExecutions,
} from "@/lib/api/grc"
import type {
  FrameworkResponse,
  FrameworkDeploymentResponse,
  VersionResponse,
  RequirementResponse,
  ControlResponse,
  DimensionResponse,
  CreateFrameworkRequest,
  UpdateFrameworkRequest,
  CreateVersionRequest,
  CreateRequirementRequest,
  BundleImportResult,
  TestExecutionResponse,
} from "@/lib/types/grc"

// ── Upgrade Diff Dialog ──────────────────────────────────────────────────────

type UpgradeDiff = {
  from_version_code: string
  to_version_id: string
  to_version_code?: string | null
  release_notes?: string | null
  change_severity?: string | null
  change_summary?: string | null
  added: Array<{ id: string; control_code: string; name: string | null; criticality_code?: string | null }>
  removed: Array<{ id: string; control_code: string; name: string | null; criticality_code?: string | null }>
  added_count: number
  removed_count: number
}

type ImportedFrameworkSuccess = {
  frameworkId: string
  frameworkName: string
}

const SEVERITY_STYLES: Record<string, string> = {
  breaking: "bg-red-500/10 text-red-600 border-red-500/30",
  major: "bg-orange-500/10 text-orange-600 border-orange-500/30",
  minor: "bg-blue-500/10 text-blue-600 border-blue-500/30",
  patch: "bg-green-500/10 text-green-600 border-green-500/30",
}

function UpgradeDiffDialog({
  deployment,
  diff,
  loading,
  error,
  onConfirm,
  onClose,
  confirming,
}: {
  deployment: FrameworkDeploymentResponse
  diff: UpgradeDiff | null
  loading: boolean
  error: string | null
  onConfirm: () => void
  onClose: () => void
  confirming: boolean
}) {
  const noChanges = diff && diff.added_count === 0 && diff.removed_count === 0
  const severityLabel = diff?.change_severity || deployment.latest_change_severity
  const releaseNotes = diff?.release_notes || deployment.latest_release_notes
  const changeSummary = diff?.change_summary || deployment.latest_change_summary

  return (
    <Dialog open onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <GitCompare className="h-4 w-4 text-blue-500" />
            Framework Update Available
          </DialogTitle>
          <DialogDescription>
            Review what changes before pulling this update.
          </DialogDescription>
        </DialogHeader>

        {/* Version badge row */}
        <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50 border">
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold truncate">{deployment.framework_name || deployment.framework_code}</p>
            {deployment.publisher_name && (
              <p className="text-xs text-muted-foreground">by {deployment.publisher_name}</p>
            )}
          </div>
          <div className="flex items-center gap-2 shrink-0 text-sm font-mono">
            <span className="px-2 py-0.5 rounded bg-muted text-muted-foreground text-xs">
              {deployment.deployed_version_code?.replace(/^v/, '') ?? "?"}
            </span>
            <ArrowRight className="h-3.5 w-3.5 text-blue-500" />
            <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-600 border border-blue-500/20 text-xs font-semibold">
              {(diff?.to_version_code || deployment.latest_version_code?.replace(/^v/, '')) ?? "new"}
            </span>
          </div>
        </div>

        {/* Severity badge */}
        {severityLabel && (
          <div className="flex items-center gap-2">
            <Badge variant="outline" className={`text-[10px] font-semibold ${SEVERITY_STYLES[severityLabel] ?? "bg-muted text-muted-foreground"}`}>
              {severityLabel}
            </Badge>
            {changeSummary && (
              <p className="text-xs text-muted-foreground truncate">{changeSummary}</p>
            )}
          </div>
        )}

        {/* Release notes */}
        {releaseNotes && (
          <div className="rounded-lg border border-border bg-muted/30 p-3">
            <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1">Release Notes</p>
            <p className="text-xs text-foreground leading-relaxed whitespace-pre-wrap">{releaseNotes}</p>
          </div>
        )}

        {/* Diff body */}
        {loading ? (
          <div className="flex items-center justify-center py-8 gap-2 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span className="text-sm">Loading changes…</span>
          </div>
        ) : error ? (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-500 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0" /> {error}
          </div>
        ) : noChanges ? (
          <div className="flex flex-col items-center justify-center py-8 gap-2 text-center">
            <CheckCircle2 className="h-7 w-7 text-green-500" />
            <p className="text-sm font-medium">No control changes</p>
            <p className="text-xs text-muted-foreground">The new version has the same controls. Metadata or descriptions may have been updated.</p>
          </div>
        ) : diff ? (
          <div className="space-y-3 max-h-64 overflow-y-auto pr-1">
            {/* Summary chips */}
            <div className="flex items-center gap-2 text-xs">
              {diff.added_count > 0 && (
                <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-green-500/10 text-green-600 border border-green-500/20">
                  <PlusCircle className="h-3 w-3" /> {diff.added_count} added
                </span>
              )}
              {diff.removed_count > 0 && (
                <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-red-500/10 text-red-600 border border-red-500/20">
                  <MinusCircle className="h-3 w-3" /> {diff.removed_count} removed
                </span>
              )}
            </div>

            {/* Added controls */}
            {diff.added.length > 0 && (
              <div>
                <p className="text-[10px] font-semibold text-green-600 uppercase tracking-wider mb-1.5">Added Controls</p>
                <div className="space-y-1">
                  {diff.added.map((c) => (
                    <div key={c.id} className="flex items-center gap-2 px-2.5 py-1.5 rounded-md bg-green-500/5 border border-green-500/15">
                      <PlusCircle className="h-3 w-3 text-green-500 shrink-0" />
                      <span className="font-mono text-xs text-green-700 dark:text-green-400 shrink-0">{c.control_code}</span>
                      {c.name && <span className="text-xs text-muted-foreground truncate">{c.name}</span>}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Removed controls */}
            {diff.removed.length > 0 && (
              <div>
                <p className="text-[10px] font-semibold text-red-600 uppercase tracking-wider mb-1.5">Removed Controls</p>
                <div className="space-y-1">
                  {diff.removed.map((c) => (
                    <div key={c.id} className="flex items-center gap-2 px-2.5 py-1.5 rounded-md bg-red-500/5 border border-red-500/15">
                      <MinusCircle className="h-3 w-3 text-red-500 shrink-0" />
                      <span className="font-mono text-xs text-red-700 dark:text-red-400 shrink-0 line-through">{c.control_code}</span>
                      {c.name && <span className="text-xs text-muted-foreground truncate line-through">{c.name}</span>}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : null}

        <DialogFooter>
          <Button variant="outline" size="sm" onClick={onClose} disabled={confirming}>Cancel</Button>
          <Button
            size="sm"
            disabled={loading || !!error || confirming}
            onClick={onConfirm}
            className="gap-1.5"
          >
            {confirming ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Download className="h-3.5 w-3.5" />}
            {confirming ? "Updating…" : "Pull Update"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function ImportSuccessDialog({
  success,
  onClose,
  onViewFramework,
}: {
  success: ImportedFrameworkSuccess | null
  onClose: () => void
  onViewFramework: () => void
}) {
  return (
    <Dialog open={Boolean(success)} onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full border border-green-500/20 bg-green-500/10">
            <CheckCircle2 className="h-7 w-7 text-green-600" />
          </div>
          <DialogTitle className="text-center">Framework Successfully Imported</DialogTitle>
          <DialogDescription className="text-center">
            {success
              ? `${success.frameworkName} is ready for onboarding.`
              : "The framework is ready for onboarding."}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="mt-2 gap-2 sm:gap-2">
          <Button variant="outline" onClick={onClose}>OK</Button>
          <Button onClick={onViewFramework} className="gap-1.5">
            View Framework
            <ArrowUpRight className="h-3.5 w-3.5" />
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
import { CommentsSection } from "@/components/comments/CommentsSection"
import { AttachmentsSection } from "@/components/attachments/AttachmentsSection"
import { OrgWorkspaceSwitcher } from "@/components/layout/OrgWorkspaceSwitcher"
import { ReadOnlyBanner } from "@/components/layout/ReadOnlyBanner"
import { useOrgWorkspace } from "@/lib/context/OrgWorkspaceContext"
import { useAccess } from "@/components/providers/AccessProvider"
import { AIEnhancePopover } from "@/components/ai/AIEnhancePopover"
import { FormFillChat } from "@/components/ai/FormFillChat"
import { ExportImportToolbar } from "@/components/spreadsheet/ExportImportToolbar"
import { ImportResultDialog } from "@/components/spreadsheet/ImportResultDialog"
import { EntitySpreadsheet } from "@/components/spreadsheet/EntitySpreadsheet"
import { frameworksColumns } from "@/components/spreadsheet/frameworksConfig"
import type { FrameworkSpreadsheetRow } from "@/components/spreadsheet/frameworksConfig"
import { FrameworkBuilderShell } from "./builder/components/FrameworkBuilderShell"
import { SubmitForReviewModal } from "@/components/grc/SubmitForReviewModal"

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

// ── Helpers ─────────────────────────────────────────────────────────────────

const VERSION_STYLES: Record<string, string> = {
  draft: "bg-muted text-muted-foreground",
  published: "bg-green-500/10 text-green-600 border-green-500/30",
  deprecated: "bg-orange-500/10 text-orange-600 border-orange-500/30",
}

type FrameworkGroupBy = "none" | "status" | "category" | "type" | "deployment" | "size" | "updated"

type FrameworkAssuranceSummary = {
  totalControls: number
  testedControls: number
  passedControls: number
  partialControls: number
  failedControls: number
  untestedControls: number
  lastTestedAt: string | null
}

const ASSURANCE_PAGE_SIZE = 200
const ASSURANCE_FRAMEWORK_CONCURRENCY = 3
const ASSURANCE_EXECUTION_CONCURRENCY = 6

function execHealthStatus(exec: TestExecutionResponse | undefined): "pass" | "fail" | "partial" | null {
  if (!exec) return null
  const s = exec.result_status?.toLowerCase()
  if (s === "pass" || s === "passed") return "pass"
  if (s === "fail" || s === "failed") return "fail"
  if (s === "partial") return "partial"
  return null
}

function formatFrameworkRecency(iso: string): string {
  const updated = new Date(iso)
  const now = new Date()
  const diffDays = Math.floor((now.getTime() - updated.getTime()) / 86400000)
  if (diffDays <= 7) return "Updated last 7 days"
  if (diffDays <= 30) return "Updated last 30 days"
  if (diffDays <= 90) return "Updated last 90 days"
  return "Older than 90 days"
}

function getFrameworkSizeLabel(controlCount: number): string {
  if (controlCount >= 50) return "Enterprise"
  if (controlCount >= 26) return "Large"
  if (controlCount >= 11) return "Medium"
  return "Small"
}

function getFrameworkStatusLabel(framework: FrameworkResponse): string {
  if (framework.approval_status === "approved") return "Published"
  if (framework.approval_status === "pending_review") return "Pending Review"
  if (framework.approval_status === "rejected") return "Rejected"
  if (framework.approval_status === "deprecated") return "Deprecated"
  return "Draft"
}

function getDeploymentLabel(isDeployed: boolean): string {
  return isDeployed ? "Deployed" : "Not Deployed"
}

async function mapWithConcurrency<T, R>(
  items: T[],
  limit: number,
  mapper: (item: T, index: number) => Promise<R>,
): Promise<R[]> {
  if (items.length === 0) return []

  const results = new Array<R>(items.length)
  let cursor = 0

  async function worker() {
    while (cursor < items.length) {
      const current = cursor
      cursor += 1
      results[current] = await mapper(items[current], current)
    }
  }

  await Promise.all(
    Array.from({ length: Math.min(limit, items.length) }, () => worker()),
  )

  return results
}

// ── Framework Creation Entry Dialog ──────────────────────────────────────────

function FrameworkCreationEntryDialog({
  open,
  onClose,
  onSelectLibrary,
  onSelectAI,
  onSelectManual,
}: {
  open: boolean
  onClose: () => void
  onSelectLibrary: () => void
  onSelectAI: () => void
  onSelectManual: () => void
}) {
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-3xl border-border bg-background shadow-2xl p-0 overflow-hidden">
        <div className="p-8 md:p-10">
          <DialogHeader className="mb-10 text-left">
            <div className="flex items-center gap-4">
              <div className="h-10 w-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center shrink-0">
                <Plus className="h-5 w-5 text-primary" />
              </div>
              <div className="space-y-1">
                <DialogTitle className="text-2xl font-bold tracking-tight">Initialize Framework</DialogTitle>
                <DialogDescription className="text-sm font-medium">Select your architectural pathway to build a robust compliance structure.</DialogDescription>
              </div>
            </div>
          </DialogHeader>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {/* Library Option */}
            <button
              onClick={onSelectLibrary}
              className="group flex flex-col p-6 rounded-2xl border border-border bg-card hover:border-blue-500/40 hover:bg-blue-500/[0.02] transition-all duration-300 text-left shadow-sm hover:shadow-md"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="h-10 w-10 rounded-lg bg-blue-500/10 flex items-center justify-center border border-blue-500/10">
                  <Library className="h-5 w-5 text-blue-500" />
                </div>
                <Badge variant="outline" className="text-[9px] font-black uppercase tracking-wider bg-blue-500/5 text-blue-500 border-blue-500/20 px-2">
                  Standard
                </Badge>
              </div>
              <h3 className="text-base font-bold mb-1.5 text-foreground leading-tight">Standard Library</h3>
              <p className="text-xs text-muted-foreground leading-relaxed flex-1">
                Import from global regulations like ISO 27001, SOC2, or NIST.
              </p>
              <div className="mt-6 flex items-center text-[10px] font-black uppercase tracking-widest text-blue-600 gap-1.5 opacity-60 group-hover:opacity-100 transition-opacity">
                Browse Catalog <ChevronRight className="h-3 w-3" />
              </div>
            </button>

            {/* AI Builder Option */}
            <button
              onClick={onSelectAI}
              className="group flex flex-col p-6 rounded-2xl border border-primary/20 bg-primary/[0.02] hover:border-primary hover:bg-primary/[0.04] transition-all duration-300 text-left shadow-sm hover:shadow-md ring-1 ring-primary/5"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="h-10 w-10 rounded-lg bg-primary/20 flex items-center justify-center border border-primary/20">
                  <Sparkles className="h-5 w-5 text-primary" />
                </div>
                <Badge className="text-[9px] font-black uppercase tracking-wider bg-primary text-primary-foreground px-2">
                  Recommend
                </Badge>
              </div>
              <h3 className="text-base font-bold mb-1.5 text-foreground leading-tight">AI Custom Build</h3>
              <p className="text-xs text-muted-foreground leading-relaxed flex-1">
                Generate a custom framework from your docs or environment.
              </p>
              <div className="mt-6 flex items-center text-[10px] font-black uppercase tracking-widest text-primary gap-1.5 opacity-60 group-hover:opacity-100 transition-opacity">
                Start Builder <Sparkles className="h-3 w-3" />
              </div>
            </button>

            {/* Manual Option */}
            <button
              onClick={onSelectManual}
              className="group flex flex-col p-6 rounded-2xl border border-border bg-card hover:border-foreground/20 hover:bg-muted/10 transition-all duration-300 text-left shadow-sm hover:shadow-md"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="h-10 w-10 rounded-lg bg-muted flex items-center justify-center border border-border">
                  <Plus className="h-5 w-5 text-muted-foreground" />
                </div>
              </div>
              <h3 className="text-base font-bold mb-1.5 text-foreground leading-tight">Manual Create</h3>
              <p className="text-xs text-muted-foreground leading-relaxed flex-1">
                Start with a blank slate and define your requirements manually.
              </p>
              <div className="mt-6 flex items-center text-[10px] font-black uppercase tracking-widest text-muted-foreground gap-1.5 opacity-60 group-hover:opacity-100 transition-opacity">
                Create Blank <ArrowRight className="h-3 w-3" />
              </div>
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

function FrameworkAssuranceBar({
  summary,
  loading,
}: {
  summary?: FrameworkAssuranceSummary
  loading: boolean
}) {
  if (loading) {
    return (
      <div className="space-y-2">
        <div className="h-1.5 rounded-full bg-muted/60 animate-pulse" />
        <div className="h-3 w-28 rounded bg-muted/60 animate-pulse" />
      </div>
    )
  }

  if (!summary || summary.totalControls === 0) {
    return (
      <div className="space-y-2">
        <div className="h-1.5 rounded-full bg-muted/40" />
        <p className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground/60">
          No controls to assess
        </p>
      </div>
    )
  }

  const passPct = (summary.passedControls / summary.totalControls) * 100
  const attentionPct = ((summary.failedControls + summary.partialControls) / summary.totalControls) * 100
  const untestedPct = (summary.untestedControls / summary.totalControls) * 100

  return (
    <div className="space-y-2">
      <div className="flex h-1.5 overflow-hidden rounded-full bg-muted/40 ring-1 ring-white/5">
        <div className="bg-green-500/90" style={{ width: `${passPct}%` }} />
        <div className="bg-amber-500/90" style={{ width: `${attentionPct}%` }} />
        <div className="bg-muted-foreground/30" style={{ width: `${untestedPct}%` }} />
      </div>
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground/75">
        <span className="text-green-500">{summary.passedControls} passed</span>
        <span className="text-amber-500">{summary.failedControls + summary.partialControls} attention</span>
        <span>{summary.untestedControls} untested</span>
      </div>
    </div>
  )
}

// ── Create Framework Dialog ─────────────────────────────────────────────────

function slugify(text: string): string {
  return text.toLowerCase().replace(/\s+/g, "_").replace(/[^a-z0-9_\-]/g, "").replace(/^[^a-z0-9]+/, "").replace(/[^a-z0-9]+$/, "").slice(0, 64) || ""
}

function CreateFrameworkDialog({
  open, types, categories, onCreate, onClose,
}: {
  open: boolean
  types: DimensionResponse[]
  categories: DimensionResponse[]
  onCreate: (p: CreateFrameworkRequest) => Promise<void>
  onClose: () => void
}) {
  const [name, setName] = useState("")
  const [code, setCode] = useState("")
  const [codeEdited, setCodeEdited] = useState(false)
  const [description, setDescription] = useState("")
  const [typeCode, setTypeCode] = useState("")
  const [categoryCode, setCategoryCode] = useState("")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      setName(""); setCode(""); setCodeEdited(false); setDescription("")
      setTypeCode(types[0]?.code ?? ""); setCategoryCode(categories[0]?.code ?? "")
      setSaving(false); setError(null)
    }
  }, [open, types, categories])

  function handleNameChange(v: string) {
    setName(v)
    if (!codeEdited) setCode(slugify(v))
  }

  async function create() {
    if (!name.trim()) { setError("Name is required."); return }
    if (!code.trim()) { setError("Code is required."); return }
    setSaving(true); setError(null)
    try {
      await onCreate({
        framework_code: code.trim(),
        name: name.trim(),
        description: description.trim() || undefined,
        framework_type_code: typeCode,
        framework_category_code: categoryCode,
        publisher_type: "custom",
      })
      onClose()
    } catch (e) { setError(e instanceof Error ? e.message : "Failed to create"); setSaving(false) }
  }

  function handleAIFilled(fields: Record<string, string>) {
    if (fields.name) { setName(fields.name); if (!codeEdited) setCode(slugify(fields.name)) }
    if (fields.description) setDescription(fields.description)
    if (fields.framework_type_code && types.some((t) => t.code === fields.framework_type_code)) setTypeCode(fields.framework_type_code)
    if (fields.framework_category_code && categories.some((c) => c.code === fields.framework_category_code)) setCategoryCode(fields.framework_category_code)
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-primary/10 p-2.5"><Plus className="h-4 w-4 text-primary" /></div>
            <div>
              <DialogTitle>New Framework</DialogTitle>
              <DialogDescription>Create a new compliance framework.</DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <FormFillChat
          entityType="framework"
          onFilled={handleAIFilled}
          getFormValues={() => ({ name, description, framework_type_code: typeCode, framework_category_code: categoryCode })}
          placeholder="e.g. HIPAA Security Rule for a healthcare company"
        />
        <Separator className="my-2" />
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label className="text-xs">Name</Label>
            <Input value={name} onChange={(e) => handleNameChange(e.target.value)} placeholder="HIPAA Security Rule" className="h-9 text-sm" autoFocus />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Code <span className="text-muted-foreground text-[10px]">auto-generated · editable</span></Label>
            <Input value={code} onChange={(e) => { setCode(e.target.value.toLowerCase().replace(/[^a-z0-9_\-]/g, "_")); setCodeEdited(true) }} placeholder="hipaa_security_rule" className="h-9 text-sm font-mono" />
          </div>
          <div className="space-y-1.5">
            <div className="flex items-center gap-1.5">
              <Label className="text-xs">Description <span className="text-muted-foreground text-[10px]">optional</span></Label>
              {name.trim() && (
                <AIEnhancePopover
                  entityType="framework"
                  entityId={null}
                  fieldName="description"
                  fieldLabel="Description"
                  currentValue={description}
                  orgId={null}
                  workspaceId={null}
                  entityContext={{ framework_code: code, framework_name: name }}
                  onApply={(v) => setDescription(v as string)}
                  popoverSide="right"
                />
              )}
            </div>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full rounded-md border border-input bg-background text-sm px-3 py-2 resize-none focus:outline-none focus:ring-1 focus:ring-ring"
              placeholder="Brief description of this framework…"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs">Type</Label>
              <select className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={typeCode} onChange={(e) => setTypeCode(e.target.value)}>
                {types.map((t) => <option key={t.code} value={t.code}>{t.name}</option>)}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Category</Label>
              <select className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={categoryCode} onChange={(e) => setCategoryCode(e.target.value)}>
                {categories.map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
              </select>
            </div>
          </div>
        </div>
        {error && <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500 mt-2">{error}</p>}
        <DialogFooter className="mt-3 gap-2 sm:gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={saving}>Cancel</Button>
          <Button size="sm" onClick={create} disabled={saving}>
            {saving ? <span className="flex items-center gap-1.5"><span className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />Creating...</span> : "Create Framework"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ── Edit Framework Dialog ───────────────────────────────────────────────────

function EditFrameworkDialog({
  framework, categories, onSave, onClose,
}: {
  framework: FrameworkResponse | null
  categories: DimensionResponse[]
  onSave: (id: string, payload: UpdateFrameworkRequest) => Promise<void>
  onClose: () => void
}) {
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [categoryCode, setCategoryCode] = useState("")
  const [marketplaceVisible, setMarketplaceVisible] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (framework) {
      setName(framework.name); setDescription(framework.description ?? "")
      setCategoryCode(framework.framework_category_code)
      setMarketplaceVisible(framework.is_marketplace_visible)
      setSaving(false); setError(null)
    }
  }, [framework])

  if (!framework) return null

  async function save() {
    if (!name.trim()) { setError("Name is required."); return }
    setSaving(true); setError(null)
    try {
      await onSave(framework!.id, {
        name: name.trim(),
        description: description.trim(),
        framework_category_code: categoryCode,
        is_marketplace_visible: marketplaceVisible,
      })
      onClose()
    } catch (e) { setError(e instanceof Error ? e.message : "Failed to save"); setSaving(false) }
  }

  function handleAIFilled(fields: Record<string, string>) {
    if (fields.name) setName(fields.name)
    if (fields.description) setDescription(fields.description)
    if (fields.framework_category_code && categories.some((c) => c.code === fields.framework_category_code)) setCategoryCode(fields.framework_category_code)
  }

  return (
    <Dialog open onOpenChange={(o) => { if (!o) onClose() }}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-primary/10 p-2.5"><Pencil className="h-4 w-4 text-primary" /></div>
            <div>
              <DialogTitle>Edit Framework</DialogTitle>
              <DialogDescription><code className="text-xs font-mono text-foreground/60">{framework.framework_code}</code></DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <FormFillChat
          entityType="framework"
          orgId={null}
          workspaceId={null}
          pageContext={{ framework_id: framework.id, framework_name: framework.name }}
          getFormValues={() => ({ name, description, framework_category_code: categoryCode })}
          onFilled={handleAIFilled}
        />
        <Separator className="my-2" />
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label className="text-xs">Name</Label>
            <Input value={name} onChange={(e) => setName(e.target.value)} className="h-9 text-sm" />
          </div>
          <div className="space-y-1.5">
            <div className="flex items-center gap-1.5">
              <Label className="text-xs">Description</Label>
              <AIEnhancePopover
                entityType="framework"
                entityId={framework.id}
                fieldName="description"
                fieldLabel="Description"
                currentValue={description}
                orgId={null}
                workspaceId={null}
                entityContext={{ framework_code: framework.framework_code, framework_name: name }}
                onApply={(v) => setDescription(v as string)}
                popoverSide="right"
              />
            </div>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full rounded-md border border-input bg-background text-sm px-3 py-2 resize-none focus:outline-none focus:ring-1 focus:ring-ring"
              placeholder="Brief description of this framework…"
            />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Category</Label>
            <select className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={categoryCode} onChange={(e) => setCategoryCode(e.target.value)}>
              {categories.map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
            </select>
          </div>
          <div className="flex items-center gap-3">
            <input type="checkbox" id="marketplace" checked={marketplaceVisible} onChange={(e) => setMarketplaceVisible(e.target.checked)}
              className="h-4 w-4 rounded border-input" />
            <Label htmlFor="marketplace" className="text-xs cursor-pointer">Visible in marketplace</Label>
          </div>
        </div>
        {error && <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500 mt-2">{error}</p>}
        <DialogFooter className="mt-3 gap-2 sm:gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={saving}>Cancel</Button>
          <Button size="sm" onClick={save} disabled={saving}>
            {saving ? <span className="flex items-center gap-1.5"><span className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />Saving...</span> : "Save Changes"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ── Delete Confirmation Dialog ──────────────────────────────────────────────

function DeleteDialog({
  framework, onConfirm, onClose,
}: {
  framework: FrameworkResponse | null
  onConfirm: (id: string) => Promise<void>
  onClose: () => void
}) {
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!framework) return null

  async function confirm() {
    setDeleting(true); setError(null)
    try {
      await onConfirm(framework!.id)
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
              <DialogTitle>Delete Framework</DialogTitle>
              <DialogDescription>This will soft-delete the framework. It can be restored by an administrator.</DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />
        <p className="text-sm">
          Are you sure you want to delete <strong>{framework.name}</strong> (<code className="text-xs font-mono">{framework.framework_code}</code>)?
          All associated versions, requirements, and controls will also be deactivated.
        </p>
        {error && <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500 mt-2">{error}</p>}
        <DialogFooter className="mt-3 gap-2 sm:gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={deleting}>Cancel</Button>
          <Button variant="destructive" size="sm" onClick={confirm} disabled={deleting}>
            {deleting ? <span className="flex items-center gap-1.5"><span className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />Deleting...</span> : "Delete Framework"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ── Create Version Dialog ───────────────────────────────────────────────────

function CreateVersionDialog({
  frameworkId, open, onCreate, onClose,
}: {
  frameworkId: string
  open: boolean
  onCreate: (frameworkId: string, p: CreateVersionRequest) => Promise<void>
  onClose: () => void
}) {
  const [changeSeverity, setChangeSeverity] = useState("minor")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) { setChangeSeverity("minor"); setSaving(false); setError(null) }
  }, [open])

  async function create() {
    setSaving(true); setError(null)
    try {
      await onCreate(frameworkId, { change_severity: changeSeverity })
      onClose()
    } catch (e) { setError(e instanceof Error ? e.message : "Failed to create version"); setSaving(false) }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>New Version</DialogTitle>
          <DialogDescription>A new version number will be assigned automatically.</DialogDescription>
        </DialogHeader>
        <Separator className="my-2" />
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label className="text-xs">Change Severity</Label>
            <select className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={changeSeverity} onChange={(e) => setChangeSeverity(e.target.value)}>
              {["patch", "minor", "major", "breaking"].map((s) => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
            </select>
          </div>
        </div>
        {error && <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500 mt-2">{error}</p>}
        <DialogFooter className="mt-3 gap-2 sm:gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={saving}>Cancel</Button>
          <Button size="sm" onClick={create} disabled={saving}>
            {saving ? "Creating..." : "Create Version"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ── Create Requirement Dialog ───────────────────────────────────────────────

function CreateRequirementDialog({
  frameworkId, open, onCreate, onClose,
}: {
  frameworkId: string
  open: boolean
  onCreate: (frameworkId: string, p: CreateRequirementRequest) => Promise<void>
  onClose: () => void
}) {
  const [reqCode, setReqCode] = useState("")
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [sortOrder, setSortOrder] = useState("0")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) { setReqCode(""); setName(""); setDescription(""); setSortOrder("0"); setSaving(false); setError(null) }
  }, [open])

  async function create() {
    if (!reqCode.trim() || !name.trim()) { setError("Code and Name are required."); return }
    setSaving(true); setError(null)
    try {
      await onCreate(frameworkId, {
        requirement_code: reqCode.trim(),
        name: name.trim(),
        description: description.trim() || undefined,
        sort_order: parseInt(sortOrder, 10) || 0,
      })
      onClose()
    } catch (e) { setError(e instanceof Error ? e.message : "Failed to create requirement"); setSaving(false) }
  }

  function handleAIFilled(fields: Record<string, string>) {
    if (fields.requirement_code) setReqCode(fields.requirement_code)
    if (fields.name) setName(fields.name)
    if (fields.description) setDescription(fields.description)
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>New Requirement</DialogTitle>
          <DialogDescription>Add a requirement to this framework.</DialogDescription>
        </DialogHeader>
        <FormFillChat
          entityType="requirement"
          orgId={null}
          workspaceId={null}
          getFormValues={() => ({ name, description, requirement_code: reqCode })}
          onFilled={handleAIFilled}
        />
        <Separator className="my-2" />
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs">Requirement Code</Label>
              <Input value={reqCode} onChange={(e) => setReqCode(e.target.value)} placeholder="CC1.1" className="h-9 text-sm font-mono" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Sort Order</Label>
              <Input type="number" value={sortOrder} onChange={(e) => setSortOrder(e.target.value)} className="h-9 text-sm" />
            </div>
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Name</Label>
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Control Environment" className="h-9 text-sm" />
          </div>
          <div className="space-y-1.5">
            <div className="flex items-center gap-1.5">
              <Label className="text-xs">Description</Label>
              {name.trim() && (
                <AIEnhancePopover
                  entityType="requirement"
                  entityId={null}
                  fieldName="description"
                  fieldLabel="Description"
                  currentValue={description}
                  orgId={null}
                  workspaceId={null}
                  entityContext={{ requirement_code: reqCode, requirement_name: name, framework_id: frameworkId }}
                  onApply={(v) => setDescription(v as string)}
                  popoverSide="right"
                />
              )}
            </div>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full rounded-md border border-input bg-background text-sm px-3 py-2 resize-none focus:outline-none focus:ring-1 focus:ring-ring"
              placeholder="Requirement description…"
            />
          </div>
        </div>
        {error && <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500 mt-2">{error}</p>}
        <DialogFooter className="mt-3 gap-2 sm:gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={saving}>Cancel</Button>
          <Button size="sm" onClick={create} disabled={saving}>
            {saving ? "Creating..." : "Add Requirement"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ── Versions Panel ──────────────────────────────────────────────────────────

function VersionsPanel({ frameworkId, onReload }: { frameworkId: string; onReload: () => void }) {
  const [versions, setVersions] = useState<VersionResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [actioning, setActioning] = useState<string | null>(null)

  const loadVersions = useCallback(async () => {
    setLoading(true)
    try {
      const res = await listVersions(frameworkId)
      // Show newest first
      setVersions((res.items ?? []).sort((a, b) => Number(b.version_code) - Number(a.version_code)))
    } catch { /* graceful */ }
    finally { setLoading(false) }
  }, [frameworkId])

  useEffect(() => { loadVersions() }, [loadVersions])

  async function handleCreate(fwId: string, payload: CreateVersionRequest) {
    await createVersion(fwId, payload)
    await loadVersions()
    onReload()
  }

  async function handlePublish(versionId: string) {
    setActioning(versionId)
    try { await publishVersion(frameworkId, versionId); await loadVersions(); onReload() }
    catch { /* graceful */ }
    finally { setActioning(null) }
  }

  async function handleDeprecate(versionId: string) {
    setActioning(versionId)
    try { await deprecateVersion(frameworkId, versionId); await loadVersions(); onReload() }
    catch { /* graceful */ }
    finally { setActioning(null) }
  }

  async function handleRestore(versionId: string) {
    setActioning(versionId)
    try { await restoreVersion(frameworkId, versionId); await loadVersions(); onReload() }
    catch { /* graceful */ }
    finally { setActioning(null) }
  }

  const hasDraft = versions.some(v => v.lifecycle_state === "draft")

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
          <Clock className="h-3 w-3" /> Version History
        </p>
        {!hasDraft && (
          <Button size="sm" variant="ghost" className="h-6 text-xs gap-1" onClick={() => setShowCreate(true)}>
            <Plus className="h-3 w-3" /> New Version
          </Button>
        )}
      </div>
      {loading ? (
        <div className="h-8 rounded bg-muted animate-pulse" />
      ) : versions.length === 0 ? (
        <p className="text-xs text-muted-foreground">No versions yet. Create one to start tracking changes.</p>
      ) : (
        <div className="space-y-1">
          {versions.map((v) => (
            <div key={v.id} className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-muted/30 text-xs group">
              <GitBranch className="h-3 w-3 text-muted-foreground shrink-0" />
              <span className="font-mono font-semibold tabular-nums">{v.version_code.replace(/^v/, '')}</span>
              <Badge variant="outline" className={`text-[10px] ${VERSION_STYLES[v.lifecycle_state] ?? ""}`}>
                {v.lifecycle_state}
              </Badge>
              <span className="text-muted-foreground capitalize">{v.change_severity}</span>
              <span className="text-muted-foreground ml-auto">{v.control_count} controls</span>
              <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                {v.lifecycle_state === "draft" && (
                  <Button size="sm" variant="ghost" className="h-5 text-[10px] px-1.5 text-green-600 hover:text-green-600 hover:bg-green-500/10"
                    onClick={() => handlePublish(v.id)} disabled={actioning === v.id} title="Publish">
                    <Upload className="h-2.5 w-2.5 mr-0.5" />
                    {actioning === v.id ? "..." : "Publish"}
                  </Button>
                )}
                {v.lifecycle_state === "published" && (
                  <Button size="sm" variant="ghost" className="h-5 text-[10px] px-1.5 text-muted-foreground hover:text-foreground"
                    onClick={() => handleDeprecate(v.id)} disabled={actioning === v.id} title="Deprecate">
                    {actioning === v.id ? "..." : "Deprecate"}
                  </Button>
                )}
                {(v.lifecycle_state === "deprecated" || v.lifecycle_state === "archived") && (
                  <Button size="sm" variant="ghost" className="h-5 text-[10px] px-1.5 text-blue-500 hover:text-blue-500 hover:bg-blue-500/10"
                    onClick={() => handleRestore(v.id)} disabled={actioning === v.id} title="Restore as new version">
                    <RotateCcw className="h-2.5 w-2.5 mr-0.5" />
                    {actioning === v.id ? "..." : "Restore"}
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
      <CreateVersionDialog frameworkId={frameworkId} open={showCreate} onCreate={handleCreate} onClose={() => setShowCreate(false)} />
    </div>
  )
}

// ── Controls Panel ──────────────────────────────────────────────────────────

function ControlsPanel({ frameworkId }: { frameworkId: string }) {
  const router = useRouter()
  const [controls, setControls] = useState<ControlResponse[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    listControls(frameworkId).then(r => setControls(r.items ?? [])).catch(() => { }).finally(() => setLoading(false))
  }, [frameworkId])

  if (loading) return <div className="h-8 rounded bg-muted animate-pulse" />
  if (controls.length === 0) return <p className="text-xs text-muted-foreground">No controls yet.</p>

  return (
    <div className="space-y-1">
      {controls.map((c) => (
        <button
          key={c.id}
          type="button"
          onClick={(e) => { e.stopPropagation(); router.push(`/frameworks/${frameworkId}`) }}
          className="flex items-center gap-2 w-full px-2 py-1.5 rounded-lg bg-muted/30 hover:bg-muted/60 text-xs text-left transition-colors"
        >
          <ShieldCheck className="h-3 w-3 text-muted-foreground shrink-0" />
          <code className="font-mono font-medium text-primary shrink-0">{c.control_code}</code>
          <span className="truncate">{c.name ?? c.control_code}</span>
          {c.criticality_code && (
            <span className="ml-auto shrink-0 text-muted-foreground">{c.criticality_code}</span>
          )}
          <ExternalLink className="h-3 w-3 text-muted-foreground shrink-0" />
        </button>
      ))}
    </div>
  )
}

// ── Requirements Panel ──────────────────────────────────────────────────────

function RequirementsPanel({ frameworkId }: { frameworkId: string }) {
  const [requirements, setRequirements] = useState<RequirementResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)

  const loadReqs = useCallback(async () => {
    setLoading(true)
    try {
      const res = await listRequirements(frameworkId)
      setRequirements(res.items ?? [])
    } catch { /* graceful */ }
    finally { setLoading(false) }
  }, [frameworkId])

  useEffect(() => { loadReqs() }, [loadReqs])

  async function handleCreate(fwId: string, payload: CreateRequirementRequest) {
    await createRequirement(fwId, payload)
    await loadReqs()
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Requirements</p>
        <Button size="sm" variant="ghost" className="h-6 text-xs gap-1" onClick={() => setShowCreate(true)}>
          <Plus className="h-3 w-3" /> Add
        </Button>
      </div>
      {loading ? (
        <div className="h-8 rounded bg-muted animate-pulse" />
      ) : requirements.length === 0 ? (
        <p className="text-xs text-muted-foreground">No requirements yet.</p>
      ) : (
        <div className="space-y-1">
          {requirements.map((r) => (
            <div key={r.id} className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-muted/30 text-xs">
              <FileText className="h-3 w-3 text-muted-foreground shrink-0" />
              <code className="font-mono font-medium">{r.requirement_code}</code>
              <span className="truncate">{r.name}</span>
              <span className="text-muted-foreground ml-auto">#{r.sort_order}</span>
            </div>
          ))}
        </div>
      )}
      <CreateRequirementDialog frameworkId={frameworkId} open={showCreate} onCreate={handleCreate} onClose={() => setShowCreate(false)} />
    </div>
  )
}

// ── Framework Expanded Panel (info + tabs: Requirements, Versions, Comments, Attachments) ──

type FrameworkTab = "controls" | "versions" | "comments" | "attachments"

function FrameworkExpandedPanel({ fw, onReload }: { fw: FrameworkResponse; onReload: () => void }) {
  const [activeTab, setActiveTab] = useState<FrameworkTab>("controls")
  const currentUserId = getJwtSubject() ?? ""
  const { isWorkspaceAdmin } = useAccess()

  const TABS: { id: FrameworkTab; label: string; icon: React.ReactNode }[] = [
    { id: "controls", label: "Controls", icon: <ShieldCheck className="h-3 w-3" /> },
    { id: "versions", label: "Versions", icon: <GitBranch className="h-3 w-3" /> },
    { id: "comments", label: "Comments", icon: <MessageSquare className="h-3 w-3" /> },
    { id: "attachments", label: "Attachments", icon: <Paperclip className="h-3 w-3" /> },
  ]

  return (
    <>
      {/* Meta row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-3 mb-4">
        {[
          { label: "Publisher", value: fw.publisher_name || "—" },
          { label: "Type", value: fw.publisher_type || "—" },
          { label: "Created", value: new Date(fw.created_at).toLocaleDateString() },
          { label: "Controls", value: String(fw.control_count ?? 0) },
        ].map(({ label, value }) => (
          <div key={label} className="rounded-lg bg-muted/40 border border-border px-3 py-2">
            <div className="text-[10px] text-muted-foreground mb-0.5">{label}</div>
            <div className="text-xs font-medium text-foreground">{value}</div>
          </div>
        ))}
      </div>
      {fw.description && (
        <div className="rounded-lg bg-muted/40 border border-border px-3 py-2 text-xs mb-4">
          <div className="text-[10px] text-muted-foreground mb-1">Description</div>
          <p className="text-foreground leading-relaxed">{fw.description}</p>
        </div>
      )}

      {/* Tab bar */}
      <div className="flex items-center gap-0 border-b border-border mb-4 -mx-4 px-4" role="tablist">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={(e) => { e.stopPropagation(); setActiveTab(tab.id) }}
            className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium border-b-2 transition-colors -mb-px ${activeTab === tab.id
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            aria-selected={activeTab === tab.id}
            role="tab"
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === "controls" && <ControlsPanel frameworkId={fw.id} />}
      {activeTab === "versions" && <VersionsPanel frameworkId={fw.id} onReload={onReload} />}
      {activeTab === "comments" && (
        <CommentsSection
          entityType="framework"
          entityId={fw.id}
          currentUserId={currentUserId}
          isWorkspaceAdmin={isWorkspaceAdmin}
          active={activeTab === "comments"}
        />
      )}
      {activeTab === "attachments" && (
        <AttachmentsSection
          entityType="framework"
          entityId={fw.id}
          currentUserId={currentUserId}
          canUpload
          isWorkspaceAdmin={isWorkspaceAdmin}
          active={activeTab === "attachments"}
        />
      )}
    </>
  )
}

// ── Marketplace / Deployments Panel ─────────────────────────────────────────

function MarketplacePanel({
  marketplaceFrameworks,
  deployments,
  onDeploy,
  onReviewUpgrade,
  onRemove,
  totalCount,
}: {
  marketplaceFrameworks: FrameworkResponse[]
  deployments: FrameworkDeploymentResponse[]
  onDeploy: (framework: FrameworkResponse) => Promise<void>
  onReviewUpgrade: (d: FrameworkDeploymentResponse) => void
  onRemove: (d: FrameworkDeploymentResponse) => Promise<void>
  totalCount: number
}) {
  const router = useRouter()
  const [search, setSearch] = useState("")
  const [deploying, setDeploying] = useState<string | null>(null)

  const deployedMap = new Map(
    deployments.map((d) => [d.source_framework_id || d.framework_id, d]),
  )

  const filtered = marketplaceFrameworks.filter((fw) => {
    if (search && !fw.name?.toLowerCase().includes(search.toLowerCase()) && !fw.framework_code.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  const updatesCount = new Set(
    deployments.filter((d) => d.has_update).map((d) => d.source_framework_id || d.framework_id)
  ).size

  const deploymentsWithUpdates = deployments.filter((d) => d.has_update)

  return (
    <div className="space-y-4">
      {/* Framework Updates Summary Section - only show if marketplace has frameworks AND deployments have updates
      {marketplaceFrameworks.length > 0 && deploymentsWithUpdates.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Bell className="h-4 w-4 text-amber-500" />
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Framework Updates ({updatesCount})
            </h3>
          </div>
          <div className="space-y-1.5">
            {deploymentsWithUpdates.map((d) => (
              <Card key={d.id} className="rounded-xl border-amber-500/30 bg-amber-500/5">
                <CardContent className="px-4 py-2.5">
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-amber-500/10">
                      <RefreshCw className="h-3.5 w-3.5 text-amber-500" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-semibold truncate">{d.framework_name || d.framework_code}</p>
                        <div className="flex items-center gap-1 text-xs font-mono">
                          <span className="text-muted-foreground">{d.deployed_version_code?.replace(/^v/, '') ?? "?"}</span>
                          <ArrowRight className="h-3 w-3 text-amber-500" />
                          <span className="text-amber-600 font-semibold">{d.latest_version_code?.replace(/^v/, '') ?? "new"}</span>
                        </div>
                        {d.latest_change_severity && (
                          <Badge variant="outline" className={`text-[9px] font-semibold ${SEVERITY_STYLES[d.latest_change_severity] ?? "bg-muted text-muted-foreground"}`}>
                            {d.latest_change_severity}
                          </Badge>
                        )}
                      </div>
                      {d.latest_change_summary && (
                        <p className="text-xs text-muted-foreground mt-0.5 truncate">{d.latest_change_summary}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-1.5 shrink-0">
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-7 text-xs gap-1"
                        onClick={() => onReviewUpgrade(d)}
                      >
                        <GitCompare className="h-3 w-3" /> View Changes
                      </Button>
                      <Button
                        size="sm"
                        className="h-7 text-xs gap-1 bg-amber-500 hover:bg-amber-600 text-white"
                        onClick={() => onReviewUpgrade(d)}
                      >
                        <Download className="h-3 w-3" /> Pull Update
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
      */}

      {/* Marketplace catalog */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Framework Library ({totalCount})
          </h3>
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <Input placeholder="Search library..." className="pl-8 h-8 text-xs w-56" value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
        </div>
        {filtered.length === 0 ? (
          <Card className="rounded-xl">
            <CardContent className="flex flex-col items-center justify-center py-12 gap-2">
              <Library className="h-8 w-8 text-muted-foreground" />
              <p className="text-sm font-medium">No marketplace frameworks</p>
              <p className="text-xs text-muted-foreground">Approved frameworks will appear here once published.</p>
            </CardContent>
          </Card>
        ) : (
          filtered.map((fw) => {
            const deployed = deployedMap.get(fw.id)
            return (
              <Card 
                key={fw.id} 
                className={`rounded-xl ${deployed?.has_update ? "border-amber-500/30" : ""} hover:shadow-md cursor-pointer transition-shadow`}
                onClick={() => router.push(`/framework_library/${fw.id}`)}
              >
                <CardContent className="px-4 py-3">
                  <div className="flex items-center gap-4">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-500/10">
                      <BookOpen className="h-4 w-4 text-blue-500" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-semibold truncate">{fw.name || fw.framework_code}</p>
                        {deployed && (
                          <Badge variant="outline" className="text-[10px] font-semibold bg-green-500/10 text-green-600 border-green-500/30">deployed</Badge>
                        )}
                        {deployed?.has_update && (
                          <Badge variant="outline" className="text-[10px] font-semibold bg-amber-500/10 text-amber-600 border-amber-500/30">
                            v{deployed.latest_version_code?.replace(/^v/, '') ?? "new"} available
                          </Badge>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {fw.publisher_name ? `${fw.publisher_name} · ` : ""}
                        {fw.category_name ?? fw.framework_category_code}
                        {fw.latest_version_code ? ` · ${fw.latest_version_code.replace(/^v/, '')}` : ""}
                        {` · ${fw.control_count ?? 0} controls`}
                      </p>
                      {fw.description && (
                        <p className="text-xs text-muted-foreground mt-1">{fw.description}</p>
                      )}
                    </div>
                    <div className="shrink-0">
                      {deployed ? (
                        deployed.has_update ? (
                          <div className="flex items-center gap-1.5">
                            <Button
                              size="sm"
                              variant="outline"
                              className="h-7 text-xs gap-1"
                              onClick={(e) => { e.stopPropagation(); onReviewUpgrade(deployed); }}
                            >
                              <GitCompare className="h-3 w-3" /> View Changes
                            </Button>
                            <Button
                              size="sm"
                              className="h-7 text-xs gap-1 bg-amber-500 hover:bg-amber-600 text-white"
                              onClick={(e) => { e.stopPropagation(); onReviewUpgrade(deployed); }}
                            >
                              <Download className="h-3 w-3" /> Pull Update
                            </Button>
                          </div>
                        ) : (
                          <Button size="sm" variant="outline" className="h-7 text-xs" disabled>
                            <ShieldCheck className="h-3 w-3 mr-1" /> Deployed
                          </Button>
                        )
                      ) : fw.latest_version_code ? (
                        <Button
                          size="sm"
                          className="h-7 text-xs gap-1"
                          disabled={deploying === fw.id}
                          onClick={async (e) => {
                            e.stopPropagation()
                            setDeploying(fw.id)
                            try { await onDeploy(fw) } catch { } finally { setDeploying(null) }
                          }}
                        >
                          <Download className="h-3 w-3" /> Deploy
                        </Button>
                      ) : (
                        <Button size="sm" variant="outline" className="h-7 text-xs" disabled>No version</Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })
        )}
      </div>
    </div>
  )
}

// ── Page ────────────────────────────────────────────────────────────────────

export default function FrameworksPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { selectedOrgId, selectedWorkspaceId, ready } = useOrgWorkspace()
  const { canWrite, isSuperAdmin } = useAccess()
  const canCreateFramework = canWrite("framework_management")
  const canSubmitForReview = isSuperAdmin
  const [activeTab, setActiveTab] = useState<"frameworks" | "marketplace" | "builder">("frameworks")
  const [frameworks, setFrameworks] = useState<FrameworkResponse[]>([])
  const [marketplaceCatalog, setMarketplaceCatalog] = useState<FrameworkResponse[]>([])
  const [marketplaceTotal, setMarketplaceTotal] = useState<number>(0)
  const [types, setTypes] = useState<DimensionResponse[]>([])
  const [categories, setCategories] = useState<DimensionResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [filterCategory, setFilterCategory] = useState("")
  const [filterType, setFilterType] = useState("")
  const [sortBy, setSortBy] = useState<"name" | "controls" | "created">("name")
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc")
  const [groupBy, setGroupBy] = useState<FrameworkGroupBy>("status")
  const [refreshing, setRefreshing] = useState(false)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [showCreationEntry, setShowCreationEntry] = useState(false)
  const [showCreate, setShowCreate] = useState(false)
  const [hasInteracted, setHasInteracted] = useState(false)
  const showHighlight = !loading && frameworks.length === 0 && !showCreationEntry && !showCreate && !hasInteracted && activeTab === "frameworks"
  const [editItem, setEditItem] = useState<FrameworkResponse | null>(null)
  const [deleteItem, setDeleteItem] = useState<FrameworkResponse | null>(null)
  const [bundleImportResult, setBundleImportResult] = useState<BundleImportResult | null>(null)
  const [showBundleImportDialog, setShowBundleImportDialog] = useState(false)
  const [viewMode, setViewMode] = useState<"list" | "spreadsheet">("list")
  // Deployments
  const [deployments, setDeployments] = useState<FrameworkDeploymentResponse[]>([])
  const updatesCount = useMemo(() => {
    const uniqueFrameworksWithUpdates = new Set(
      deployments.filter((d) => d.has_update).map((d) => d.source_framework_id || d.framework_id)
    )
    return uniqueFrameworksWithUpdates.size
  }, [deployments])
  // Upgrade diff dialog
  const [upgradeTarget, setUpgradeTarget] = useState<FrameworkDeploymentResponse | null>(null)
  const [upgradeDiff, setUpgradeDiff] = useState<UpgradeDiff | null>(null)
  const [upgradeDiffLoading, setUpgradeDiffLoading] = useState(false)
  const [upgradeDiffError, setUpgradeDiffError] = useState<string | null>(null)
  const [upgradeConfirming, setUpgradeConfirming] = useState(false)
  const [quickInstallingId, setQuickInstallingId] = useState<string | null>(null)
  const [importSuccess, setImportSuccess] = useState<ImportedFrameworkSuccess | null>(null)
  const [frameworkAssurance, setFrameworkAssurance] = useState<Record<string, FrameworkAssuranceSummary>>({})
  const [assuranceLoadingIds, setAssuranceLoadingIds] = useState<Set<string>>(new Set())
  // Submit for review modal
  const [submitReviewItem, setSubmitReviewItem] = useState<FrameworkResponse | null>(null)

  const setPrimaryTab = useCallback((tab: "frameworks" | "marketplace" | "builder", extraParams?: Record<string, string | null>) => {
    const params = new URLSearchParams(searchParams.toString())
    params.set("tab", tab)
    if (extraParams) {
      for (const [key, value] of Object.entries(extraParams)) {
        if (value) params.set(key, value)
        else params.delete(key)
      }
    }
    const qs = params.toString()
    router.replace(qs ? `/frameworks?${qs}` : "/frameworks", { scroll: false })
  }, [router, searchParams])

  const openBuilderTab = useCallback((builderTab: "build" | "enhance" | "gap", options?: { enhanceFrameworkId?: string | null; gapFrameworkId?: string | null; gapJobId?: string | null }) => {
    const params = new URLSearchParams(searchParams.toString())
    params.set("tab", "builder")
    params.set("builderTab", builderTab)
    if (options?.enhanceFrameworkId) params.set("enhance", options.enhanceFrameworkId)
    else params.delete("enhance")
    if (options?.gapFrameworkId) params.set("gapFramework", options.gapFrameworkId)
    else params.delete("gapFramework")
    if (options?.gapJobId) params.set("gapJob", options.gapJobId)
    else params.delete("gapJob")
    const qs = params.toString()
    router.replace(qs ? `/frameworks?${qs}` : "/frameworks", { scroll: false })
  }, [router, searchParams])

  const load = useCallback(async (quiet = false) => {
    if (!selectedOrgId) return
    if (quiet) setRefreshing(true); else setLoading(true)
    setError(null)
    try {
      const [typeRes, catRes] = await Promise.all([listFrameworkTypes(), listFrameworkCategories()])

      // Filter out sensitive categories for non-admins
      const hiddenCodes = ["risk", "control", "risk_library", "control_library"]
      const filterMetadata = (items: DimensionResponse[]) =>
        isSuperAdmin ? items : items.filter(i => !hiddenCodes.includes(i.code.toLowerCase()))

      setTypes(Array.isArray(typeRes) ? filterMetadata(typeRes) : [])
      setCategories(Array.isArray(catRes) ? filterMetadata(catRes) : [])

      const [fwRes, marketRes, depRes] = await Promise.all([
        listFrameworks({ scope_org_id: selectedOrgId, scope_workspace_id: selectedWorkspaceId || undefined }),
        listFrameworks({
          scope_org_id: selectedOrgId,
          ...(selectedWorkspaceId ? { scope_workspace_id: selectedWorkspaceId } : {}),
          is_marketplace_visible: true,
          approval_status: "approved",
        }),
        listDeployments(selectedOrgId, selectedWorkspaceId || undefined),
      ])

      const finalMarketCatalog = (marketRes.items ?? []).filter(fw => {
        if (isSuperAdmin) return true
        const cat = fw.framework_category_code?.toLowerCase() || ""
        const type = fw.framework_type_code?.toLowerCase() || ""
        return !hiddenCodes.includes(cat) && !hiddenCodes.includes(type)
      })

      setFrameworks(fwRes.items ?? [])
      setMarketplaceCatalog(finalMarketCatalog)
      setMarketplaceTotal(marketRes.total ?? finalMarketCatalog.length)
      setDeployments((depRes.items ?? []) as unknown as FrameworkDeploymentResponse[])
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load frameworks")
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [selectedOrgId, selectedWorkspaceId])

  useEffect(() => { if (ready && selectedOrgId) load() }, [load, ready, selectedOrgId])

  useEffect(() => {
    const tab = searchParams.get("tab")
    if (tab === "frameworks" || tab === "marketplace" || tab === "builder") {
      setActiveTab(tab)
      return
    }
    setActiveTab("frameworks")
  }, [searchParams])

  const loadFrameworkAssurance = useCallback(async (frameworkList: FrameworkResponse[]) => {
    if (frameworkList.length === 0) {
      setFrameworkAssurance({})
      setAssuranceLoadingIds(new Set())
      return
    }

    setAssuranceLoadingIds(new Set(frameworkList.map((fw) => fw.id)))

    const fetchLatestExecutionForControl = async (controlId: string) => {
      let offset = 0
      let total = 0
      let latest: TestExecutionResponse | undefined

      do {
        const execRes = await listTestExecutions({ control_id: controlId, limit: ASSURANCE_PAGE_SIZE, offset })
        const items = execRes.items ?? []
        for (const exec of items) {
          if (!latest || new Date(exec.executed_at).getTime() > new Date(latest.executed_at).getTime()) {
            latest = exec
          }
        }
        total = execRes.total ?? offset + items.length
        offset += ASSURANCE_PAGE_SIZE
      } while (offset < total)

      return latest
    }

    const entries = await mapWithConcurrency(
      frameworkList,
      ASSURANCE_FRAMEWORK_CONCURRENCY,
      async (fw) => {
        try {
          const controls: ControlResponse[] = []
          let offset = 0
          let total = 0

          do {
            const res = await listControls(fw.id, { limit: ASSURANCE_PAGE_SIZE, offset })
            controls.push(...(res.items ?? []))
            total = res.total ?? controls.length
            offset += ASSURANCE_PAGE_SIZE
          } while (offset < total)

          const testedControls = controls.filter((control) => (control.test_count ?? 0) > 0)

          const executionResults = await mapWithConcurrency(
            testedControls,
            ASSURANCE_EXECUTION_CONCURRENCY,
            async (control) => {
              try {
                return await fetchLatestExecutionForControl(control.id)
              } catch {
                return undefined
              }
            },
          )

          let passedControls = 0
          let partialControls = 0
          let failedControls = 0
          let testedCount = 0
          let lastTestedAt: string | null = null

          executionResults.forEach((exec) => {
            if (!exec) return
            testedCount += 1
            if (!lastTestedAt || new Date(exec.executed_at).getTime() > new Date(lastTestedAt).getTime()) {
              lastTestedAt = exec.executed_at
            }
            const status = execHealthStatus(exec)
            if (status === "pass") passedControls += 1
            else if (status === "fail") failedControls += 1
            else if (status === "partial") partialControls += 1
          })

          const controlsWithTestsButNoExecution = testedControls.length - testedCount
          const untestedControls = Math.max(controls.length - testedControls.length, 0)

          return [
            fw.id,
            {
              totalControls: controls.length,
              testedControls: testedControls.length,
              passedControls,
              partialControls: partialControls + Math.max(controlsWithTestsButNoExecution, 0),
              failedControls,
              untestedControls,
              lastTestedAt,
            } satisfies FrameworkAssuranceSummary,
          ] as const
        } catch {
          return [
            fw.id,
            {
              totalControls: fw.control_count ?? 0,
              testedControls: 0,
              passedControls: 0,
              partialControls: 0,
              failedControls: 0,
              untestedControls: fw.control_count ?? 0,
              lastTestedAt: null,
            } satisfies FrameworkAssuranceSummary,
          ] as const
        }
      },
    )

    setFrameworkAssurance(Object.fromEntries(entries))
    setAssuranceLoadingIds(new Set())
  }, [])

  const filtered = useMemo(() => {
    const base = frameworks.filter((fw) => {
      if (search && !fw.name?.toLowerCase().includes(search.toLowerCase()) && !fw.framework_code.toLowerCase().includes(search.toLowerCase())) return false
      if (filterCategory && fw.framework_category_code !== filterCategory) return false
      if (filterType && fw.framework_type_code !== filterType) return false
      return true
    })
    return [...base].sort((a, b) => {
      let cmp = 0
      if (sortBy === "name") cmp = (a.name ?? "").localeCompare(b.name ?? "")
      else if (sortBy === "controls") cmp = (a.control_count ?? 0) - (b.control_count ?? 0)
      else cmp = a.created_at.localeCompare(b.created_at)
      return sortDir === "asc" ? cmp : -cmp
    })
  }, [frameworks, search, filterCategory, filterType, sortBy, sortDir])

  useEffect(() => {
    if (activeTab !== "frameworks") return
    void loadFrameworkAssurance(filtered)
  }, [activeTab, filtered, loadFrameworkAssurance])

  const deployedFrameworkIds = useMemo(
    () => new Set(deployments.map((deployment) => deployment.source_framework_id || deployment.framework_id)),
    [deployments],
  )

  const groupedFrameworks = useMemo(() => {
    const groups = new Map<string, FrameworkResponse[]>()

    const getGroupLabel = (framework: FrameworkResponse) => {
      if (groupBy === "status" && isSuperAdmin) return getFrameworkStatusLabel(framework)
      if (groupBy === "category") return framework.category_name || framework.framework_category_code || "Uncategorized"
      if (groupBy === "type") return framework.type_name || framework.framework_type_code || "Unspecified type"
      if (groupBy === "deployment") return getDeploymentLabel(deployedFrameworkIds.has(framework.id))
      if (groupBy === "size") return getFrameworkSizeLabel(framework.control_count ?? 0)
      if (groupBy === "updated") return formatFrameworkRecency(framework.updated_at)
      return "All Frameworks"
    }

    filtered.forEach((framework) => {
      const label = getGroupLabel(framework)
      if (!groups.has(label)) groups.set(label, [])
      groups.get(label)!.push(framework)
    })

    return Array.from(groups.entries()).map(([label, items]) => ({ label, items }))
  }, [deployedFrameworkIds, filtered, groupBy])

  const publishedCount = marketplaceCatalog.length
  const totalControls = frameworks.reduce((sum, f) => sum + (f.control_count ?? 0), 0)

  const marketplaceFrameworks = marketplaceCatalog

  const libraryTop3 = useMemo(() => {
    // Top 3 marketplace frameworks NOT already deployed, sorted by most controls
    return marketplaceCatalog
      .filter(fw => !deployments.some(d => d.framework_id === fw.id || d.source_framework_id === fw.id))
      .sort((a, b) => (b.control_count ?? 0) - (a.control_count ?? 0))
      .slice(0, 3)
  }, [marketplaceCatalog, deployments])

  async function handleCreate(payload: CreateFrameworkRequest) {
    await createFramework({ ...payload, scope_org_id: selectedOrgId, scope_workspace_id: selectedWorkspaceId })
    await load()
  }

  async function handleUpdate(id: string, payload: UpdateFrameworkRequest) {
    await updateFramework(id, payload)
    await load()
  }

  async function handleDelete(id: string) {
    await deleteFramework(id)
    await load()
  }

  const handleBundleExport = async (frameworkId: string, frameworkCode: string) => {
    try {
      const blob = await exportFrameworkBundle(frameworkId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `framework-bundle-${frameworkCode}.json`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error("Bundle export failed", err)
    }
  }

  const handleBundleImport = async (file: File, dryRun: boolean) => {
    try {
      const text = await file.text()
      const bundle = JSON.parse(text)
      const result = await importFrameworkBundle(bundle, {
        scopeOrgId: selectedOrgId ?? undefined,
        scopeWorkspaceId: selectedWorkspaceId ?? undefined,
        dryRun: dryRun,
      })
      setBundleImportResult(result)
      setShowBundleImportDialog(true)
      if (!dryRun && !result.errors?.length) {
        load()
      }
    } catch (err) {
      console.error("Bundle import failed", err)
    }
  }

  // Marketplace handlers
  async function handleDeploy(fw: FrameworkResponse) {
    if (!selectedOrgId || !selectedWorkspaceId) {
      const message = "Select an organization and workspace before installing a framework"
      setError(message)
      throw new Error(message)
    }
    setError(null)
    try {
      const versionsRes = await listVersions(fw.id, {
        scope_org_id: selectedOrgId,
        scope_workspace_id: selectedWorkspaceId,
      })
      const published = (versionsRes.items ?? []).filter((v: VersionResponse) => v.lifecycle_state === "published")
      const latest = published[0]
      if (!latest) throw new Error("No published version available")
      const deployment = await deployFramework({
        org_id: selectedOrgId,
        framework_id: fw.id,
        version_id: latest.id,
        workspace_id: selectedWorkspaceId,
      })
      setImportSuccess({
        frameworkId: deployment.framework_id,
        frameworkName: deployment.framework_name ?? fw.name ?? fw.framework_code,
      })
      await load(true)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to install framework")
      throw e
    }
  }

  async function handleRemoveDeployment(d: FrameworkDeploymentResponse) {
    await deleteDeployment(d.id)
    await load(true)
  }

  function handleReviewUpgrade(d: FrameworkDeploymentResponse) {
    setUpgradeTarget(d)
    setUpgradeDiff(null)
    setUpgradeDiffError(null)
    setUpgradeDiffLoading(true)
    getUpgradeDiff(d.id, d.latest_version_id!)
      .then(r => setUpgradeDiff(r as UpgradeDiff))
      .catch(e => setUpgradeDiffError(e instanceof Error ? e.message : "Failed to load diff"))
      .finally(() => setUpgradeDiffLoading(false))
  }

  async function handleConfirmUpgrade() {
    if (!upgradeTarget?.latest_version_id) return
    setUpgradeConfirming(true)
    try {
      await updateDeployment(upgradeTarget.id, { version_id: upgradeTarget.latest_version_id })
      setUpgradeTarget(null)
      await load(true)
    } catch (e) {
      setUpgradeDiffError(e instanceof Error ? e.message : "Upgrade failed")
    } finally {
      setUpgradeConfirming(false)
    }
  }

  function handleViewImportedFramework() {
    if (!importSuccess?.frameworkId) return
    const frameworkId = importSuccess.frameworkId
    setImportSuccess(null)
    router.push(`/frameworks/${frameworkId}`)
  }


  const frameworkSpreadsheetRows = useMemo<FrameworkSpreadsheetRow[]>(() => 
    filtered.map((fw) => ({
      id: fw.id,
      framework_code: fw.framework_code,
      name: fw.name ?? "",
      description: fw.description ?? "",
      framework_type_code: fw.framework_type_code ?? "",
      framework_category_code: fw.framework_category_code ?? "",
      publisher_type: fw.publisher_type ?? "",
      control_count: String(frameworkAssurance[fw.id]?.totalControls ?? (fw.working_control_count || fw.control_count) ?? 0),
      is_marketplace_visible: String(fw.is_marketplace_visible ?? false),
      version: fw.latest_version_code ?? "",
    })),
    [filtered, frameworkAssurance]
  )

  // ── Loading skeleton ────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 rounded-md bg-muted animate-pulse" />
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => <div key={i} className="h-20 rounded-xl bg-muted animate-pulse" />)}
        </div>
        <div className="h-9 w-64 rounded-md bg-muted animate-pulse" />
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => <div key={i} className="h-16 rounded-xl bg-muted animate-pulse" />)}
        </div>
      </div>
    )
  }

  async function handleFrameworkSpreadsheetSave(row: FrameworkSpreadsheetRow) {
    if (!row.id) {
      // Create new framework
      if (!row.framework_code || !row.name) {
        setError("Code and Name are required for new frameworks")
        return
      }
      try {
        await createFramework({
          framework_code: row.framework_code,
          name: row.name,
          description: row.description || undefined,
          framework_type_code: row.framework_type_code || "standard",
          framework_category_code: row.framework_category_code || "security",
          scope_org_id: selectedOrgId,
          scope_workspace_id: selectedWorkspaceId,
        })
        await load()
      } catch (e: any) {
        setError(e.message || "Failed to create framework")
      }
      return
    }
    await updateFramework(row.id, {
      name: row.name || undefined,
      description: row.description || undefined,
    })
    await load()
  }

  function renderFrameworkCard(fw: FrameworkResponse) {
    const catCode = fw.framework_category_code?.toLowerCase()
    const fwBorderCls = catCode === "security" ? "border-l-blue-500"
      : catCode === "privacy" ? "border-l-purple-500"
        : catCode === "financial" ? "border-l-green-500"
          : catCode === "healthcare" ? "border-l-rose-500"
            : catCode === "regulatory" ? "border-l-amber-500"
              : "border-l-primary"
    const fwIconCls = catCode === "security" ? "text-blue-500"
      : catCode === "privacy" ? "text-purple-500"
        : catCode === "financial" ? "text-green-500"
          : catCode === "healthcare" ? "text-rose-500"
            : catCode === "regulatory" ? "text-amber-500"
              : "text-primary"
    const isExpanded = expandedId === fw.id
    const assurance = frameworkAssurance[fw.id]
    const assuranceLoading = assuranceLoadingIds.has(fw.id)
    const displayControlCount = activeTab === "frameworks" ? (assurance?.totalControls ?? (fw.working_control_count || fw.control_count)) : fw.control_count;

    return (
      <div
        key={fw.id}
        className={`rounded-xl border border-l-[3px] ${fwBorderCls} bg-card transition-all cursor-pointer group ${isExpanded ? "bg-primary/5 border-primary/20 shadow-md ring-1 ring-primary/10" : "hover:bg-muted/30 border-border"}`}
      >
        <div className="px-4 py-3 flex flex-col gap-4 sm:flex-row sm:items-start" onClick={() => router.push(`/frameworks/${fw.id}`)}>
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-muted">
            <BookOpen className={`h-4 w-4 ${fwIconCls}`} />
          </div>
          <div className="min-w-0 flex-1 space-y-2">
            <div className="flex items-center gap-2 flex-wrap">
              <p className="text-sm font-semibold">{fw.name || fw.framework_code}</p>
              {/* Status badges — role based visibility */}
              {fw.approval_status === "approved" ? (
                isSuperAdmin ? (
                  <Badge variant="outline" className="text-[10px] font-semibold bg-green-500/10 text-green-600 border-green-500/30">
                    <CheckCircle2 className="h-2.5 w-2.5 mr-1" />published
                  </Badge>
                ) : (
                  <Badge variant="outline" className="text-[10px] font-semibold bg-blue-500/10 text-blue-600 border-blue-500/30">
                    <Library className="h-2.5 w-2.5 mr-1" />library
                  </Badge>
                )
              ) : (
                <>
                  {fw.approval_status === "pending_review" ? (
                    <Badge variant="outline" className="text-[10px] font-semibold bg-amber-500/10 text-amber-600 border-amber-500/30">
                      <Clock className="h-2.5 w-2.5 mr-1" />pending review
                    </Badge>
                  ) : fw.approval_status === "rejected" ? (
                    <Badge variant="outline" className="text-[10px] font-semibold bg-red-500/10 text-red-600 border-red-500/30">
                      <XCircle className="h-2.5 w-2.5 mr-1" />rejected
                    </Badge>
                  ) : fw.approval_status === "draft" ? (
                    <Badge variant="outline" className="text-[10px] font-semibold bg-muted text-muted-foreground border-border">
                      draft
                    </Badge>
                  ) : null}
                </>
              )}

              {/* Deployed badge — visible to all */}
              {deployedFrameworkIds.has(fw.id) && (
                <Badge variant="outline" className="text-[10px] font-semibold bg-blue-500/10 text-blue-600 border-blue-500/30">
                  deployed
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-1.5 mt-0.5 text-[10px] text-muted-foreground flex-wrap uppercase font-bold tracking-wider opacity-60">
              <span className="font-mono">{fw.framework_code}</span>
              <span>·</span>
              <span>{fw.type_name ?? fw.framework_type_code}</span>
              <span>·</span>
              <span>{fw.category_name ?? fw.framework_category_code}</span>
            </div>
            <div className="max-w-full sm:max-w-md">
              <div className="mb-1 flex items-center justify-between gap-3">
                <span className="text-[10px] font-bold uppercase tracking-[0.18em] text-muted-foreground/65">
                  Assurance Coverage
                </span>
                <span className="text-[10px] font-semibold text-muted-foreground/75">
                  {assurance?.testedControls ?? 0}/{assurance?.totalControls ?? displayControlCount ?? 0} tested
                </span>
              </div>
              <FrameworkAssuranceBar summary={assurance} loading={assuranceLoading} />
            </div>
          </div>
          <div className="flex items-center gap-4 text-xs text-muted-foreground shrink-0 sm:pr-2">
            <div className="text-center group-hover:scale-105 transition-transform duration-300">
              <p className="text-sm font-bold tabular-nums text-foreground">{displayControlCount ?? 0}</p>
              <p className="text-[10px] uppercase font-bold tracking-tight opacity-50">Controls</p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-1 opacity-100 transition-opacity shrink-0 sm:opacity-0 sm:group-hover:opacity-100">
            <Link href={`/frameworks/${fw.id}`} title="View" onClick={(e) => e.stopPropagation()}
              className="rounded-md p-1.5 text-muted-foreground hover:text-primary hover:bg-primary/10 transition-all">
              <ExternalLink className="h-3.5 w-3.5" />
            </Link>
            {/* Submit — available to anyone who can edit the framework */}
            {(fw.approval_status === "draft" || fw.approval_status === "rejected") && (
              <button
                type="button"
                title={isSuperAdmin ? "Submit for Review" : "Submit to Library"}
                onClick={(e) => {
                  e.stopPropagation();
                  e.preventDefault();
                  setSubmitReviewItem(fw);
                }}
                className={`rounded-md p-1.5 transition-all ${isSuperAdmin ? "text-muted-foreground hover:text-amber-500 hover:bg-amber-500/10" : "text-muted-foreground hover:text-blue-500 hover:bg-blue-500/10"}`}
              >
                {isSuperAdmin ? <Send className="h-3.5 w-3.5" /> : <BookOpen className="h-3.5 w-3.5" />}
              </button>
            )}
            {/* 
            <button type="button" title="Export Bundle" onClick={(e) => { e.stopPropagation(); handleBundleExport(fw.id, fw.framework_code) }}
              className="rounded-md p-1.5 text-muted-foreground hover:text-blue-500 hover:bg-blue-500/10 transition-all">
              <TableProperties className="h-3.5 w-3.5" />
            </button>
            */}
            <button type="button" title="Enhance with AI" onClick={(e) => { e.stopPropagation(); openBuilderTab("enhance", { enhanceFrameworkId: fw.id }) }}
              className="rounded-md p-1.5 text-muted-foreground hover:text-amber-500 hover:bg-amber-500/10 transition-all">
              <Sparkles className="h-3.5 w-3.5" />
            </button>
            <button type="button" title="Task Builder — bulk generate tasks for this framework" onClick={(e) => { e.stopPropagation(); router.push(`/frameworks/${fw.id}/task-builder`) }}
              className="rounded-md p-1.5 text-muted-foreground hover:text-violet-500 hover:bg-violet-500/10 transition-all">
              <ListTodo className="h-3.5 w-3.5" />
            </button>
            <button type="button" title="Edit" onClick={(e) => { e.stopPropagation(); setEditItem(fw) }}
              className="rounded-md p-1.5 text-muted-foreground hover:text-foreground hover:bg-accent transition-all">
              <Pencil className="h-3.5 w-3.5" />
            </button>
            <button type="button" title="Delete" onClick={(e) => { e.stopPropagation(); setDeleteItem(fw) }}
              className="rounded-md p-1.5 text-muted-foreground hover:text-red-500 hover:bg-red-500/10 transition-all">
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); setExpandedId(isExpanded ? null : fw.id) }}
            className="rounded-md p-0.5 text-muted-foreground hover:text-foreground hover:bg-accent transition-all shrink-0 self-end sm:self-center"
          >
            {isExpanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </button>
        </div>
        {isExpanded && (
          <div className="px-4 pb-4 border-t border-border/50">
            <FrameworkExpandedPanel fw={fw} onReload={load} />
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-6" onPointerDownCapture={() => { if (!hasInteracted) setHasInteracted(true) }}>
      {/* Header */}
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="min-w-0">
          <h1 className="text-2xl font-bold tracking-tight font-secondary">Frameworks</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Manage your frameworks, browse the library, and build new ones with AI from one place
          </p>
        </div>
        <div className="w-full xl:w-auto">
          <OrgWorkspaceSwitcher />
        </div>
      </div>
      <ReadOnlyBanner />
      <div className="flex w-full flex-wrap items-center gap-2 xl:w-auto xl:justify-end">
        {/* View toggle — shown only on frameworks tab */}
        {activeTab === "frameworks" && (
          <div className="flex items-center rounded-md border border-border bg-muted/30 p-0.5 gap-0.5">
            <button
              type="button"
              title="List view"
              onClick={() => setViewMode("list")}
              className={`rounded p-1.5 transition-colors ${viewMode === "list" ? "bg-muted text-foreground" : "text-muted-foreground hover:text-foreground hover:bg-muted/50"}`}
            >
              <List className="h-4 w-4" />
            </button>
            <button
              type="button"
              title="Spreadsheet view"
              onClick={() => setViewMode("spreadsheet")}
              className={`rounded p-1.5 transition-colors ${viewMode === "spreadsheet" ? "bg-muted text-foreground" : "text-muted-foreground hover:text-foreground hover:bg-muted/50"}`}
            >
              <TableProperties className="h-4 w-4" />
            </button>
          </div>
        )}
        <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={() => load(true)} disabled={refreshing} title="Refresh">
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
        </Button>
        {(activeTab === "frameworks" || activeTab === "builder") && canCreateFramework && (
          <div className="relative group/onboard">
            {showHighlight && (
              <>
                <div className="absolute -inset-1 rounded-[1.2rem] bg-primary/40 blur-md animate-pulse pointer-events-none" />
                {/* Floating Guide Bubble — Mature Glassmorphism */}
                <div className="absolute top-[calc(100%+20px)] right-0 z-[60] w-80 hidden sm:block animate-in fade-in zoom-in-95 slide-in-from-top-4 duration-1000 ease-out">
                  <div className="relative rounded-[1.5rem] border border-primary/20 bg-background/60 backdrop-blur-xl p-5 shadow-[0_30px_60px_-12px_rgba(0,0,0,0.6),0_0_40px_-10px_rgba(var(--primary),0.15)] ring-1 ring-white/10 overflow-hidden group/bubble">
                    <div className="absolute -top-12 -right-12 h-32 w-32 rounded-full bg-primary/10 blur-[50px] animate-pulse" />
                    <div className="absolute -bottom-12 -left-12 h-32 w-32 rounded-full bg-blue-500/5 blur-[50px]" />
                    <div className="absolute inset-0 bg-gradient-to-br from-white/[0.07] via-transparent to-transparent pointer-events-none" />
                    <div className="absolute -top-1.5 right-12 h-3.5 w-3.5 rotate-45 border-l border-t border-primary/20 bg-background/60 backdrop-blur-xl shrink-0" />
                    <div className="flex items-start gap-4 relative z-10">
                      <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary/10 text-primary border border-primary/20 shadow-xl shadow-primary/5 shrink-0 group-hover/bubble:scale-105 transition-transform">
                        <Sparkles className="h-5 w-5" />
                      </div>
                      <div className="space-y-1.5 pt-0.5">
                        <div className="flex items-center gap-2">
                          <p className="text-[10px] font-black text-foreground/70 leading-none tracking-[0.2em] uppercase">Guided Setup</p>
                          <div className="h-1 w-1 rounded-full bg-primary animate-ping" />
                        </div>
                        <p className="text-sm font-extrabold text-foreground leading-[1.3] tracking-tight">
                          Start building your first <br /> compliance framework
                        </p>
                        <p className="text-[10px] text-muted-foreground font-semibold leading-none flex items-center gap-1.5 pt-0.5">
                          Click to launch the initialization wizard
                          <ArrowRight className="h-2.5 w-2.5 opacity-0 -translate-x-2 group-hover/bubble:opacity-100 group-hover/bubble:translate-x-0 transition-all" />
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </>
            )}
            <Button
              size="sm"
              onClick={() => {
                setShowCreationEntry(true)
              }}
              className={`w-full gap-2 rounded-xl px-4 py-5 font-bold tracking-tight sm:w-auto relative transition-all ${showHighlight
                ? "bg-primary text-primary-foreground shadow-[0_0_20px_rgba(var(--primary),0.3)] ring-4 ring-primary/20 scale-105"
                : "shadow-xl shadow-primary/20"
                }`}
            >
              <Plus className={`h-4 w-4 ${showHighlight ? "animate-bounce" : ""}`} />
              New Framework
            </Button>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="-mx-1 overflow-x-auto scrollbar-none border-b border-border">
        <div className="flex min-w-max gap-1 px-1">
          <button
            type="button"
            onClick={() => setPrimaryTab("frameworks")}
            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${activeTab === "frameworks" ? "border-primary text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"}`}
          >
            My Frameworks
          </button>
          <button
            type="button"
            onClick={() => setPrimaryTab("marketplace")}
            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px flex items-center gap-2 ${activeTab === "marketplace" ? "border-primary text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"}`}
          >
            Framework Library
            {marketplaceTotal > 0 && (
              <span className="flex h-4 w-4 items-center justify-center rounded-full bg-blue-500 text-[10px] text-white font-bold">{marketplaceTotal}</span>
            )}
          </button>
          <button
            type="button"
            onClick={() => openBuilderTab("build")}
            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px flex items-center gap-2 ${activeTab === "builder" ? "border-primary text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"}`}
          >
            <Sparkles className="h-4 w-4" />
            Framework Builder
          </button>
        </div>
      </div>

      {/* Upgrade diff dialog */}
      {upgradeTarget && (
        <UpgradeDiffDialog
          deployment={upgradeTarget}
          diff={upgradeDiff}
          loading={upgradeDiffLoading}
          error={upgradeDiffError}
          onConfirm={handleConfirmUpgrade}
          onClose={() => setUpgradeTarget(null)}
          confirming={upgradeConfirming}
        />
      )}


      {/* Shared Dialogs */}
      <CreateFrameworkDialog open={showCreate} types={types} categories={categories} onCreate={handleCreate} onClose={() => setShowCreate(false)} />
      <FrameworkCreationEntryDialog
        open={showCreationEntry}
        onClose={() => setShowCreationEntry(false)}
        onSelectLibrary={() => {
          setShowCreationEntry(false)
          setPrimaryTab("marketplace")
        }}
        onSelectAI={() => {
          setShowCreationEntry(false)
          openBuilderTab("build")
        }}
        onSelectManual={() => {
          setShowCreationEntry(false)
          setShowCreate(true)
        }}
      />
      <EditFrameworkDialog framework={editItem} categories={categories} onSave={handleUpdate} onClose={() => setEditItem(null)} />
      <DeleteDialog framework={deleteItem} onConfirm={handleDelete} onClose={() => setDeleteItem(null)} />
      <ImportSuccessDialog
        success={importSuccess}
        onClose={() => setImportSuccess(null)}
        onViewFramework={handleViewImportedFramework}
      />
      <ImportResultDialog
        open={showBundleImportDialog}
        onClose={() => setShowBundleImportDialog(false)}
        result={bundleImportResult ? {
          created: (bundleImportResult.requirements_created ?? 0) + (bundleImportResult.controls_created ?? 0),
          updated: (bundleImportResult.requirements_updated ?? 0) + (bundleImportResult.controls_updated ?? 0),
          skipped: 0,
          warnings: bundleImportResult.warnings ?? [],
          errors: bundleImportResult.errors ?? [],
          dry_run: bundleImportResult.dry_run,
        } : null}
        onCommit={async () => setShowBundleImportDialog(false)}
      />

      {/* Marketplace tab */}
      {activeTab === "marketplace" && (
        <MarketplacePanel
          marketplaceFrameworks={marketplaceFrameworks}
          deployments={deployments}
          onDeploy={handleDeploy}
          onReviewUpgrade={handleReviewUpgrade}
          onRemove={handleRemoveDeployment}
          totalCount={marketplaceTotal}
        />
      )}

      {activeTab === "builder" && (
        <FrameworkBuilderShell embedded />
      )}

      {/* Frameworks tab content starts below */}
      {activeTab === "frameworks" && <>


        {/* Error */}
        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-500 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            {error}
            <Button variant="ghost" size="sm" className="ml-auto h-6 text-xs" onClick={() => load()}>Retry</Button>
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {[
            { label: "Total Frameworks", value: frameworks.length, icon: Library, iconCls: "text-primary", borderCls: "border-l-primary", numCls: "text-foreground" },
            isSuperAdmin && { label: "Published", value: publishedCount, icon: ShieldCheck, iconCls: "text-green-500", borderCls: "border-l-green-500", numCls: "text-green-600" },
            { label: "Total Controls", value: totalControls, icon: Layers, iconCls: "text-blue-500", borderCls: "border-l-blue-500", numCls: "text-blue-600" },
          ].filter(Boolean).map((stat) => (
            stat && (
              <div key={stat.label} className={`relative rounded-xl border bg-card border-l-[3px] ${stat.borderCls} px-4 py-3 flex items-center gap-3`}>
                <div className="shrink-0 rounded-lg p-2 bg-muted">
                  <stat.icon className={`w-4 h-4 ${stat.iconCls}`} />
                </div>
                <div className="min-w-0">
                  <div className={`text-2xl font-bold tabular-nums leading-none ${stat.numCls}`}>{stat.value}</div>
                  <div className="text-[11px] text-muted-foreground mt-0.5 truncate">{stat.label}</div>
                </div>
              </div>
            )
          ))}
        </div>

        {/* Filters */}
        <div className="rounded-xl border border-border bg-card px-4 py-3 space-y-2.5">
          <div className="flex flex-col gap-3 xl:flex-row xl:items-center">
            <div className="flex w-full items-center gap-2 xl:min-w-[260px] xl:flex-1">
              {/* Mobile Filter Button */}
              <div className="lg:hidden">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="sm" className="h-8 w-8 p-0">
                      <SlidersHorizontal className="h-3.5 w-3.5" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start" className="w-56">
                    <DropdownMenuLabel>Filter Frameworks</DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <div className="p-2 space-y-3">
                      <div className="space-y-1">
                        <Label className="text-[10px] uppercase font-bold text-muted-foreground">Category</Label>
                        <select className="h-8 w-full rounded-md border border-input bg-background px-2 text-xs" value={filterCategory} onChange={(e) => setFilterCategory(e.target.value)}>
                          <option value="">All Categories</option>
                          {categories.map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
                        </select>
                      </div>
                      {/* 
                    <div className="space-y-1">
                      <Label className="text-[10px] uppercase font-bold text-muted-foreground">Type</Label>
                      <select className="h-8 w-full rounded-md border border-input bg-background px-2 text-xs" value={filterType} onChange={(e) => setFilterType(e.target.value)}>
                        <option value="">All Types</option>
                        {types.map((t) => <option key={t.code} value={t.code}>{t.name}</option>)}
                      </select>
                    </div>
                    */}
                      <div className="space-y-1">
                        <Label className="text-[10px] uppercase font-bold text-muted-foreground">Sort By</Label>
                        <select className="h-8 w-full rounded-md border border-input bg-background px-2 text-xs" value={sortBy} onChange={(e) => setSortBy(e.target.value as typeof sortBy)}>
                          <option value="name">Name</option>
                          <option value="controls">Controls</option>
                          <option value="created">Created</option>
                        </select>
                      </div>
                      <div className="space-y-1">
                        <Label className="text-[10px] uppercase font-bold text-muted-foreground">Group By</Label>
                        <select className="h-8 w-full rounded-md border border-input bg-background px-2 text-xs" value={groupBy} onChange={(e) => setGroupBy(e.target.value as FrameworkGroupBy)}>
                          <option value="none">None</option>
                          {isSuperAdmin && <option value="status">Status</option>}
                          <option value="category">Category</option>
                          <option value="type">Type</option>
                          <option value="deployment">Deployment</option>
                          <option value="size">Size</option>
                          <option value="updated">Updated</option>
                        </select>
                      </div>
                    </div>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
                <Input placeholder="Search frameworks..." className="pl-9 h-8 text-sm" value={search} onChange={(e) => setSearch(e.target.value)} />
              </div>
            </div>
            <div className="hidden lg:flex flex-wrap items-center gap-2">
              <select className="h-8 min-w-[140px] rounded-md border border-input bg-background px-2 text-xs" value={filterCategory} onChange={(e) => setFilterCategory(e.target.value)}>
                <option value="">All Categories</option>
                {categories.map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
              </select>
              {/* 
            <select className="h-8 min-w-[140px] rounded-md border border-input bg-background px-2 text-xs" value={filterType} onChange={(e) => setFilterType(e.target.value)}>
              <option value="">All Types</option>
              {types.map((t) => <option key={t.code} value={t.code}>{t.name}</option>)}
            </select>
            */}
              <select className="h-8 min-w-[110px] rounded-md border border-input bg-background px-2 text-xs" value={sortBy} onChange={(e) => setSortBy(e.target.value as typeof sortBy)}>
                <option value="name">Name</option>
                <option value="controls">Controls</option>
                <option value="created">Created</option>
              </select>
              <select className="h-8 min-w-[150px] rounded-md border border-input bg-background px-2 text-xs" value={groupBy} onChange={(e) => setGroupBy(e.target.value as FrameworkGroupBy)}>
                <option value="none">No Grouping</option>
                {isSuperAdmin && <option value="status">Group: Status</option>}
                <option value="category">Group: Category</option>
                <option value="type">Group: Type</option>
                <option value="deployment">Group: Deployment</option>
                <option value="size">Group: Size</option>
                <option value="updated">Group: Updated</option>
              </select>
            </div>
            <div className="flex w-full flex-wrap items-center justify-end gap-1 xl:ml-auto xl:w-auto xl:shrink-0">
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={() => setSortDir(d => d === "asc" ? "desc" : "asc")} title={sortDir === "asc" ? "Ascending" : "Descending"}>
                <ArrowUpDown className="w-3.5 h-3.5" />
              </Button>
              {/* 
            <Button variant="ghost" size="sm" className="h-8 gap-1.5 text-xs px-2" title="Export CSV" onClick={() => {
              const headers = ["Code", "Name", "Type", "Category", "Published", "Controls", "Active"]
              const rows = filtered.map(fw => [fw.framework_code, fw.name ?? "", fw.framework_type_code ?? "", fw.framework_category_code ?? "", fw.is_marketplace_visible ? "Yes" : "No", fw.control_count ?? 0, fw.is_active ? "Yes" : "No"])
              const csv = [headers, ...rows].map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(",")).join("\n")
              const blob = new Blob([csv], { type: "text/csv" })
              const url = URL.createObjectURL(blob)
              const a = document.createElement("a"); a.href = url; a.download = `frameworks_export_${new Date().toISOString().split("T")[0]}.csv`; a.click()
              URL.revokeObjectURL(url)
            }}>
              <Download className="h-3.5 w-3.5" />
            </Button>
            <ExportImportToolbar
              entityName="Framework Bundle"
              onExport={async () => {
                // Bundle export is per-framework — show a note
              }}
              onImport={handleBundleImport}
              loading={loading}
            /> 
            */}
            </div>
          </div>
          {(search || filterCategory || filterType) && (
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-[10px] text-muted-foreground font-medium">Filtered by:</span>
              {search && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-primary/10 text-primary border border-primary/20">
                  &ldquo;{search}&rdquo;
                  <button onClick={() => setSearch("")} className="hover:text-primary/70"><X className="w-2.5 h-2.5" /></button>
                </span>
              )}
              {filterCategory && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-blue-500/10 text-blue-600 border border-blue-500/20">
                  {categories.find(c => c.code === filterCategory)?.name ?? filterCategory}
                  <button onClick={() => setFilterCategory("")} className="hover:text-blue-400"><X className="w-2.5 h-2.5" /></button>
                </span>
              )}
              {filterType && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-purple-500/10 text-purple-600 border border-purple-500/20">
                  {types.find(t => t.code === filterType)?.name ?? filterType}
                  <button onClick={() => setFilterType("")} className="hover:text-purple-400"><X className="w-2.5 h-2.5" /></button>
                </span>
              )}
              <button className="text-[11px] text-muted-foreground hover:text-foreground ml-1 underline"
                onClick={() => { setSearch(""); setFilterCategory(""); setFilterType("") }}>
                clear all
              </button>
            </div>
          )}
          {groupBy !== "none" && (
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-[10px] text-muted-foreground font-medium">Grouped by:</span>
              <span className="inline-flex items-center gap-1 rounded-full border border-primary/20 bg-primary/10 px-2 py-0.5 text-[11px] font-medium capitalize text-primary">
                {groupBy}
              </span>
            </div>
          )}
        </div>

        {/* Spreadsheet View */}
        {viewMode === "spreadsheet" && (
          <EntitySpreadsheet
            columns={isSuperAdmin ? frameworksColumns : frameworksColumns.filter(c => c.key !== "is_marketplace_visible")}
            rows={frameworkSpreadsheetRows}
            onSave={handleFrameworkSpreadsheetSave}
            onDelete={async (row) => {
              if (row.id) setDeleteItem(row as unknown as FrameworkResponse)
            }}
            loading={loading}
            keyField="id"
            readOnly={!canCreateFramework}
          />
        )}

        {/* Framework Content Grid */}
        {viewMode === "list" && (
          <div className="grid grid-cols-1 gap-6 xl:grid-cols-3 xl:gap-8">
            <div className="space-y-4 xl:col-span-2">
              <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-widest px-1 mb-2">
                Active Frameworks
              </h3>

              {filtered.length === 0 ? (
                frameworks.length === 0 ? (
                  /* ── Clean, minimal empty state ── */
                  <Card className="rounded-2xl border-dashed bg-muted/5">
                    <CardContent className="flex flex-col items-center justify-center py-24 gap-4">
                      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-muted/20">
                        <Library className="h-7 w-7 text-muted-foreground/50" />
                      </div>
                      <div className="text-center max-w-sm space-y-1.5">
                        <p className="text-base font-bold text-foreground">No frameworks yet</p>
                        <p className="text-xs text-muted-foreground leading-relaxed">
                          Start by creating your first framework to organize your <br /> requirements and track compliance progress.
                        </p>
                      </div>
                      {(activeTab === "frameworks" || activeTab === "builder") && canCreateFramework && (
                        <Button onClick={() => setShowCreationEntry(true)} variant="outline" size="sm" className="mt-2 h-9 px-6 rounded-xl font-bold bg-background">
                          Initialize Workspace
                        </Button>
                      )}
                    </CardContent>
                  </Card>
                ) : (
                  /* ── Filtered empty state ── */
                  <Card className="rounded-xl">
                    <CardContent className="flex flex-col items-center justify-center py-16 gap-3">
                      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-muted">
                        <Search className="h-6 w-6 text-muted-foreground" />
                      </div>
                      <p className="text-sm font-medium">No matching frameworks</p>
                      <p className="text-xs text-muted-foreground">Try adjusting your search or filters.</p>
                      <Button variant="ghost" size="sm" className="mt-1 gap-1.5 text-xs" onClick={() => { setSearch(""); setFilterCategory(""); setFilterType("") }}>
                        <X className="h-3 w-3" /> Clear Filters
                      </Button>
                    </CardContent>
                  </Card>
                )
              ) : (
                <div className="space-y-4">
                  {(groupBy === "none" ? [{ label: "All Frameworks", items: filtered }] : groupedFrameworks).map((group) => (
                    <div key={group.label} className="space-y-2.5">
                      {groupBy !== "none" && (
                        <div className="flex items-center justify-between px-1">
                          <div>
                            <h4 className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground/80">
                              {group.label}
                            </h4>
                            <p className="mt-0.5 text-[10px] text-muted-foreground/60">
                              {group.items.length} framework{group.items.length > 1 ? "s" : ""}
                            </p>
                          </div>
                        </div>
                      )}
                      {group.items.map((fw) => renderFrameworkCard(fw))}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Right Column: Library Sidebar */}
            <div className="space-y-5 xl:sticky xl:top-4 xl:self-start">
              <div className="flex items-center justify-between px-1">
                <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-widest">
                  Framework Library ({marketplaceTotal})
                </h3>
                <button
                  onClick={() => setPrimaryTab("marketplace")}
                  className="text-[10px] font-bold text-primary hover:underline transition-all flex items-center gap-1"
                >
                  Browse all <ArrowRight className="h-3 w-3" />
                </button>
              </div>

              <div className="rounded-2xl border border-border bg-muted/20 p-4 space-y-4 shadow-inner">
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/50">
                  Available to add
                </p>

                <div className="space-y-4">
                  {libraryTop3.length === 0 ? (
                    <div className="rounded-xl border border-dashed border-border p-8 text-center bg-card/50">
                      <p className="text-[10px] text-muted-foreground font-medium uppercase">Library empty</p>
                    </div>
                  ) : (
                    libraryTop3.map(fw => {
                      const code = fw.framework_code.toLowerCase()
                      const isHealthcare = code.includes("hipaa") || code.includes("hitrust")
                      const isPrivacy = code.includes("gdpr") || code.includes("ccpa") || code.includes("privacy") || code.includes("dpdp")
                      const isResilience = code.includes("dora") || code.includes("nist")

                      const Icon = isHealthcare ? HeartPulse : isPrivacy ? Lock : isResilience ? ShieldCheck : Library
                      const iconColor = isHealthcare ? "text-sky-400" : isPrivacy ? "text-indigo-400" : isResilience ? "text-amber-400" : "text-primary"
                      const iconBg = isHealthcare ? "bg-sky-500/10" : isPrivacy ? "bg-indigo-500/10" : isResilience ? "bg-amber-500/10" : "bg-primary/10"

                      return (
                        <Card key={fw.id} className="border-border bg-background shadow-sm hover:shadow-md hover:border-primary/20 transition-all duration-300 group">
                          <CardContent className="p-4">
                            <div className="flex items-start gap-3">
                              <div className={`h-8 w-8 rounded-lg ${iconBg} flex items-center justify-center shrink-0 border border-white/5`}>
                                <Icon className={`h-4 w-4 ${iconColor}`} />
                              </div>
                              <div className="flex-1 min-w-0">
                                <h4 className="text-sm font-bold truncate group-hover:text-primary transition-colors">{fw.name || fw.framework_code}</h4>
                                <p className="text-[10px] text-muted-foreground truncate leading-relaxed">
                                  {fw.category_name ?? fw.framework_category_code}
                                </p>
                              </div>
                            </div>

                            <div className="mt-4 flex items-center justify-between text-[10px] font-bold">
                              <div className="flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-muted/60 text-muted-foreground">
                                <Layers className="h-2.5 w-2.5" />
                                {fw.control_count ?? 0} controls
                              </div>
                              <span className="text-muted-foreground/40 tabular-nums">
                                {fw.latest_version_code?.replace(/^v/, '') ?? "v1.0"}
                              </span>
                            </div>

                            <Button
                              className="w-full mt-3 h-8 text-[11px] font-bold rounded-lg gap-1.5 shadow-xl shadow-primary/10"
                              disabled={quickInstallingId === fw.id}
                              onClick={async () => {
                                setQuickInstallingId(fw.id)
                                try {
                                  await handleDeploy(fw)
                                } catch {
                                  // Error is already surfaced through page state.
                                } finally {
                                  setQuickInstallingId(null)
                                }
                              }}
                            >
                              {quickInstallingId === fw.id
                                ? <Loader2 className="h-3 w-3 animate-spin" />
                                : <Plus className="h-3 w-3" />}
                              {quickInstallingId === fw.id ? "Installing..." : "Start Onboarding"}
                            </Button>
                          </CardContent>
                        </Card>
                      )
                    })
                  )}
                </div>
              </div>
              <div className="p-4 rounded-xl border border-dashed border-border bg-primary/5">
                <p className="text-[11px] text-primary/70 font-medium leading-relaxed">
                  Can&apos;t find what you need? Our **AI Builder** can generate custom frameworks from your documents in minutes.
                </p>
                <Button
                  variant="link"
                  size="sm"
                  className="h-auto p-0 text-[11px] font-bold text-primary mt-2 flex items-center gap-1"
                  onClick={() => openBuilderTab("build")}
                >
                  Try AI Builder <Sparkles className="h-3 w-3" />
                </Button>
              </div>
            </div>
          </div>
        )}

      </> /* end frameworks tab */}

      {/* Global Dialogs - kept outside tab conditions to ensure they stay in DOM and work correctly after deployment */}
      <CreateFrameworkDialog open={showCreate} types={types} categories={categories} onCreate={handleCreate} onClose={() => setShowCreate(false)} />
      <FrameworkCreationEntryDialog
        open={showCreationEntry}
        onClose={() => setShowCreationEntry(false)}
        onSelectLibrary={() => {
          setShowCreationEntry(false)
          setPrimaryTab("marketplace")
        }}
        onSelectAI={() => {
          setShowCreationEntry(false)
          openBuilderTab("build")
        }}
        onSelectManual={() => {
          setShowCreationEntry(false)
          setShowCreate(true)
        }}
      />
      <EditFrameworkDialog framework={editItem} categories={categories} onSave={handleUpdate} onClose={() => setEditItem(null)} />
      <DeleteDialog framework={deleteItem} onConfirm={handleDelete} onClose={() => setDeleteItem(null)} />
      <ImportSuccessDialog
        success={importSuccess}
        onClose={() => setImportSuccess(null)}
        onViewFramework={handleViewImportedFramework}
      />
      <ImportResultDialog
        open={showBundleImportDialog}
        onClose={() => setShowBundleImportDialog(false)}
        result={bundleImportResult ? {
          created: (bundleImportResult.requirements_created ?? 0) + (bundleImportResult.controls_created ?? 0),
          updated: (bundleImportResult.requirements_updated ?? 0) + (bundleImportResult.controls_updated ?? 0),
          skipped: 0,
          warnings: bundleImportResult.warnings ?? [],
          errors: bundleImportResult.errors ?? [],
          dry_run: bundleImportResult.dry_run,
        } : null}
        onCommit={async () => setShowBundleImportDialog(false)}
      />
      <SubmitForReviewModal
        open={!!submitReviewItem}
        framework={submitReviewItem}
        onClose={() => setSubmitReviewItem(null)}
        onSuccess={() => load()}
      />
    </div>
  )
}
