"use client"

import { useEffect, useState, useCallback, useMemo } from "react"
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
  ShieldAlert,
  Plus,
  Search,
  Globe,
  Library,
  CheckCircle,
  X,
  Pencil,
  Trash2,
  ChevronRight,
  ArrowUpDown,
  Eye,
  EyeOff,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  Link2,
  Flame,
  Tag,
} from "lucide-react"
import { fetchWithAuth } from "@/lib/api/apiClient"
import { useAccess } from "@/components/providers/AccessProvider"

// ── Types ─────────────────────────────────────────────────────────────────────

interface GlobalRiskResponse {
  id: string
  tenant_key: string
  risk_code: string
  risk_category_code: string
  risk_category_name: string | null
  risk_level_code: string | null
  risk_level_name: string | null
  risk_level_color: string | null
  inherent_likelihood: number | null
  inherent_impact: number | null
  inherent_risk_score: number | null
  is_active: boolean
  created_at: string
  updated_at: string
  created_by: string | null
  title: string | null
  description: string | null
  short_description: string | null
  mitigation_guidance: string | null
  detection_guidance: string | null
  linked_control_count: number
  version: number
}

interface LinkedControl {
  id: string
  control_code: string
  title: string | null
  framework_name: string | null
}

interface CreateGlobalRiskRequest {
  risk_code: string
  risk_category_code: string
  risk_level_code?: string
  inherent_likelihood?: number
  inherent_impact?: number
  title: string
  description?: string
  short_description?: string
  mitigation_guidance?: string
  detection_guidance?: string
}

interface UpdateGlobalRiskRequest {
  risk_category_code?: string
  risk_level_code?: string
  inherent_likelihood?: number
  inherent_impact?: number
  title?: string
  description?: string
  mitigation_guidance?: string
  detection_guidance?: string
}

// ── API Layer ─────────────────────────────────────────────────────────────────

async function apiCall<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetchWithAuth(path, init)
  if (res.status === 204) return undefined as T
  const data = await res.json()
  if (!res.ok) throw new Error(data?.detail ?? data?.error?.message ?? "Request failed")
  return data as T
}

async function listGlobalRisks(params?: Record<string, string>): Promise<{ items: GlobalRiskResponse[]; total: number }> {
  const qs = params ? "?" + new URLSearchParams(params).toString() : ""
  return apiCall(`/api/v1/fr/global-risks${qs}`)
}

async function createGlobalRisk(body: CreateGlobalRiskRequest): Promise<GlobalRiskResponse> {
  return apiCall("/api/v1/fr/global-risks", {
    method: "POST",
    body: JSON.stringify(body),
  })
}

async function updateGlobalRisk(id: string, body: UpdateGlobalRiskRequest): Promise<GlobalRiskResponse> {
  return apiCall(`/api/v1/fr/global-risks/${id}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  })
}

async function deleteGlobalRisk(id: string): Promise<void> {
  return apiCall(`/api/v1/fr/global-risks/${id}`, { method: "DELETE" })
}

async function listLinkedControls(id: string): Promise<LinkedControl[]> {
  return apiCall(`/api/v1/fr/global-risks/${id}/controls`)
}

// ── Constants ─────────────────────────────────────────────────────────────────

const RISK_SCORE_META = (score: number): { label: string; color: string; borderCls: string; numCls: string } => {
  if (score >= 16) return { label: "Critical", color: "text-red-600 bg-red-500/10 border-red-500/30",    borderCls: "border-l-red-500",    numCls: "text-red-600" }
  if (score >= 11) return { label: "High",     color: "text-orange-600 bg-orange-500/10 border-orange-500/30", borderCls: "border-l-orange-500", numCls: "text-orange-600" }
  if (score >= 6)  return { label: "Medium",   color: "text-yellow-600 bg-yellow-500/10 border-yellow-500/30", borderCls: "border-l-amber-500",  numCls: "text-yellow-600" }
  return               { label: "Low",      color: "text-emerald-600 bg-emerald-500/10 border-emerald-500/30", borderCls: "border-l-yellow-500", numCls: "text-emerald-600" }
}

const SEVERITY_BORDER: Record<string, string> = {
  critical: "border-l-red-500",
  high:     "border-l-orange-500",
  medium:   "border-l-amber-500",
  low:      "border-l-yellow-500",
}

function severityBorderCls(levelCode: string | null, score: number | null): string {
  if (levelCode && SEVERITY_BORDER[levelCode]) return SEVERITY_BORDER[levelCode]
  if (score !== null) return RISK_SCORE_META(score).borderCls
  return "border-l-primary"
}

const RISK_CATEGORIES = [
  { code: "operational",    name: "Operational" },
  { code: "financial",      name: "Financial" },
  { code: "compliance",     name: "Compliance" },
  { code: "strategic",      name: "Strategic" },
  { code: "reputational",   name: "Reputational" },
  { code: "technology",     name: "Technology" },
  { code: "cyber",          name: "Cyber Security" },
  { code: "third_party",    name: "Third Party" },
  { code: "data_privacy",   name: "Data Privacy" },
  { code: "environmental",  name: "Environmental" },
]

const RISK_LEVELS = [
  { code: "critical", name: "Critical", color: "#ef4444" },
  { code: "high",     name: "High",     color: "#f97316" },
  { code: "medium",   name: "Medium",   color: "#eab308" },
  { code: "low",      name: "Low",      color: "#22c55e" },
]

const LEVEL_FILTER_OPTIONS = [
  { value: "",         label: "All Levels" },
  { value: "critical", label: "Critical" },
  { value: "high",     label: "High" },
  { value: "medium",   label: "Medium" },
  { value: "low",      label: "Low" },
]

type SortField = "risk_code" | "title" | "risk_category_name" | "inherent_risk_score" | "created_at"
type SortDir = "asc" | "desc"

// ── Helpers ───────────────────────────────────────────────────────────────────

function slugify(name: string): string {
  return name
    .toUpperCase()
    .replace(/[^A-Z0-9\s]/g, "")
    .trim()
    .replace(/\s+/g, "-")
    .slice(0, 32)
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
}

function ScorePill({ score }: { score: number }) {
  const meta = RISK_SCORE_META(score)
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full border text-xs font-semibold ${meta.color}`}>
      {score}
    </span>
  )
}

function RiskLevelDot({ color, name }: { color: string; name: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
      <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
      {name}
    </span>
  )
}

function SortIcon({ field, sortBy, sortDir }: { field: SortField; sortBy: SortField; sortDir: SortDir }) {
  if (field !== sortBy) return null
  return sortDir === "asc" ? <ChevronUp className="w-3 h-3 inline ml-0.5" /> : <ChevronDown className="w-3 h-3 inline ml-0.5" />
}

function Skeleton() {
  return (
    <div className="rounded-xl border border-border bg-card p-4 animate-pulse space-y-2">
      <div className="flex items-center gap-3">
        <div className="h-4 w-28 bg-muted rounded" />
        <div className="h-4 w-40 bg-muted rounded" />
        <div className="h-4 w-20 bg-muted rounded ml-auto" />
      </div>
      <div className="h-3 w-56 bg-muted rounded" />
    </div>
  )
}

function ScoreBar({ likelihood, impact, score }: { likelihood: number; impact: number; score: number }) {
  const meta = RISK_SCORE_META(score)
  const pct = Math.round((score / 25) * 100)
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>Inherent Risk Score</span>
        <span className={`font-semibold ${meta.color.split(" ")[0]}`}>{score} / 25 — {meta.label}</span>
      </div>
      <div className="h-2 rounded-full bg-muted overflow-hidden">
        <div
          className="h-full rounded-full transition-all"
          style={{
            width: `${pct}%`,
            backgroundColor: score >= 16 ? "#ef4444" : score >= 11 ? "#f97316" : score >= 6 ? "#eab308" : "#22c55e",
          }}
        />
      </div>
      <div className="flex gap-4 text-xs text-muted-foreground">
        <span>Likelihood: <span className="text-foreground font-medium">{likelihood}</span>/5</span>
        <span>Impact: <span className="text-foreground font-medium">{impact}</span>/5</span>
      </div>
    </div>
  )
}

// ── Delete Dialog ─────────────────────────────────────────────────────────────

function DeleteDialog({
  risk,
  onConfirm,
  onClose,
  saving,
}: {
  risk: GlobalRiskResponse
  onConfirm: () => void
  onClose: () => void
  saving: boolean
}) {
  return (
    <Dialog open onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Delete Risk</DialogTitle>
          <DialogDescription>
            This will permanently delete <span className="font-semibold text-foreground">{risk.risk_code}</span>
            {risk.title ? ` — ${risk.title}` : ""}. This action cannot be undone.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button type="button" variant="ghost" onClick={onClose} className="h-9 px-4">Cancel</Button>
          <Button
            type="button"
            disabled={saving}
            className="h-9 bg-destructive text-destructive-foreground hover:bg-destructive/90"
            onClick={onConfirm}
          >
            {saving ? "Deleting..." : "Delete Risk"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ── Create / Edit Dialog ──────────────────────────────────────────────────────

function RiskFormDialog({
  initial,
  onSave,
  onClose,
}: {
  initial?: GlobalRiskResponse
  onSave: (data: CreateGlobalRiskRequest | UpdateGlobalRiskRequest) => Promise<void>
  onClose: () => void
}) {
  const isEdit = !!initial
  const [title, setTitle] = useState(initial?.title ?? "")
  const [shortDesc, setShortDesc] = useState(initial?.short_description ?? "")
  const [description, setDescription] = useState(initial?.description ?? "")
  const [categoryCode, setCategoryCode] = useState(initial?.risk_category_code ?? "")
  const [levelCode, setLevelCode] = useState(initial?.risk_level_code ?? "")
  const [likelihood, setLikelihood] = useState<string>(initial?.inherent_likelihood?.toString() ?? "")
  const [impact, setImpact] = useState<string>(initial?.inherent_impact?.toString() ?? "")
  const [mitigationGuidance, setMitigationGuidance] = useState(initial?.mitigation_guidance ?? "")
  const [detectionGuidance, setDetectionGuidance] = useState(initial?.detection_guidance ?? "")
  const [codeManuallyEdited, setCodeManuallyEdited] = useState(false)
  const [manualCode, setManualCode] = useState("")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Auto-generate risk_code from title (create only)
  const autoCode = useMemo(() => {
    if (isEdit) return ""
    return slugify(title)
  }, [title, isEdit])

  const displayCode = isEdit ? (initial?.risk_code ?? "") : (codeManuallyEdited ? manualCode : autoCode)

  const computedScore = useMemo(() => {
    const l = parseInt(likelihood)
    const i = parseInt(impact)
    if (!isNaN(l) && !isNaN(i) && l >= 1 && l <= 5 && i >= 1 && i <= 5) return l * i
    return null
  }, [likelihood, impact])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim()) { setError("Title is required."); return }
    if (!categoryCode) { setError("Category is required."); return }
    if (!isEdit && !displayCode.trim()) { setError("Title must produce a valid risk code."); return }
    setSaving(true)
    setError(null)
    try {
      const payload = isEdit
        ? {
            risk_category_code: categoryCode || undefined,
            risk_level_code: levelCode || undefined,
            inherent_likelihood: likelihood ? parseInt(likelihood) : undefined,
            inherent_impact: impact ? parseInt(impact) : undefined,
            title: title || undefined,
            description: description || undefined,
            mitigation_guidance: mitigationGuidance || undefined,
            detection_guidance: detectionGuidance || undefined,
          } as UpdateGlobalRiskRequest
        : {
            risk_code: displayCode,
            risk_category_code: categoryCode,
            risk_level_code: levelCode || undefined,
            inherent_likelihood: likelihood ? parseInt(likelihood) : undefined,
            inherent_impact: impact ? parseInt(impact) : undefined,
            title,
            description: description || undefined,
            short_description: shortDesc || undefined,
            mitigation_guidance: mitigationGuidance || undefined,
            detection_guidance: detectionGuidance || undefined,
          } as CreateGlobalRiskRequest
      await onSave(payload)
      onClose()
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit Risk" : "Create Global Risk"}</DialogTitle>
          <DialogDescription>
            {isEdit
              ? "Update the details of this global risk."
              : "Define a new platform-level risk for the global risk registry."}
          </DialogDescription>
        </DialogHeader>

        {error && (
          <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">{error}</div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Title */}
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">
              Title <span className="text-destructive">*</span>
            </Label>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Unauthorized Access to Sensitive Data"
              className="h-8 text-sm"
              maxLength={200}
            />
            {!isEdit && (
              <div className="mt-1 flex items-center gap-2">
                <span className="text-xs text-muted-foreground font-mono">code: </span>
                <Input
                  value={displayCode}
                  onChange={(e) => { setCodeManuallyEdited(true); setManualCode(e.target.value.toUpperCase().replace(/[^A-Z0-9-]/g, "")) }}
                  className="h-6 text-xs font-mono flex-1 max-w-[240px] px-2"
                  placeholder="AUTO-GENERATED"
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
            )}
          </div>

          {/* Category + Level */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">
                Category <span className="text-destructive">*</span>
              </Label>
              <select
                value={categoryCode}
                onChange={(e) => setCategoryCode(e.target.value)}
                className="w-full h-8 px-2 rounded border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="">Select category...</option>
                {RISK_CATEGORIES.map((c) => (
                  <option key={c.code} value={c.code}>{c.name}</option>
                ))}
              </select>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">Risk Level</Label>
              <select
                value={levelCode}
                onChange={(e) => setLevelCode(e.target.value)}
                className="w-full h-8 px-2 rounded border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="">None</option>
                {RISK_LEVELS.map((l) => (
                  <option key={l.code} value={l.code}>{l.name}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Likelihood + Impact + Score */}
          <div className="grid grid-cols-3 gap-3 items-end">
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">Likelihood (1–5)</Label>
              <Input
                type="number"
                value={likelihood}
                onChange={(e) => setLikelihood(e.target.value)}
                placeholder="1–5"
                min={1}
                max={5}
                className="h-8 text-sm"
              />
            </div>
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">Impact (1–5)</Label>
              <Input
                type="number"
                value={impact}
                onChange={(e) => setImpact(e.target.value)}
                placeholder="1–5"
                min={1}
                max={5}
                className="h-8 text-sm"
              />
            </div>
            <div className="flex items-center gap-2 pb-0.5">
              <span className="text-xs text-muted-foreground">Score:</span>
              {computedScore !== null ? (
                <ScorePill score={computedScore} />
              ) : (
                <span className="text-xs text-muted-foreground italic">—</span>
              )}
            </div>
          </div>

          {/* Short description (create only) */}
          {!isEdit && (
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">Short Description</Label>
              <Input
                value={shortDesc}
                onChange={(e) => setShortDesc(e.target.value)}
                placeholder="One-line summary for list views"
                className="h-8 text-sm"
                maxLength={300}
              />
            </div>
          )}

          {/* Description */}
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Description</Label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              placeholder="Full description of the risk, its causes, and business context..."
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary resize-none"
            />
          </div>

          {/* Mitigation guidance */}
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Mitigation Guidance</Label>
            <textarea
              value={mitigationGuidance}
              onChange={(e) => setMitigationGuidance(e.target.value)}
              rows={3}
              placeholder="Recommended controls, safeguards, and mitigating actions..."
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary resize-none"
            />
          </div>

          {/* Detection guidance */}
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Detection Guidance</Label>
            <textarea
              value={detectionGuidance}
              onChange={(e) => setDetectionGuidance(e.target.value)}
              rows={2}
              placeholder="Indicators of compromise, monitoring signals, detection methods..."
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary resize-none"
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="ghost" onClick={onClose} className="h-9 px-4">Cancel</Button>
            <Button type="submit" disabled={saving} className="h-9">
              {saving ? (isEdit ? "Saving..." : "Creating...") : (isEdit ? "Save Changes" : "Create Risk")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ── Detail Panel ──────────────────────────────────────────────────────────────

function RiskDetailPanel({
  risk: initialRisk,
  onEdit,
  onDelete,
  onClose,
  onUpdated,
}: {
  risk: GlobalRiskResponse
  onEdit: (r: GlobalRiskResponse) => void
  onDelete: (r: GlobalRiskResponse) => void
  onClose: () => void
  onUpdated: (r: GlobalRiskResponse) => void
}) {
  const [tab, setTab] = useState<"details" | "controls">("details")
  const [risk, setRisk] = useState(initialRisk)
  const [linkedControls, setLinkedControls] = useState<LinkedControl[]>([])
  const [loadingControls, setLoadingControls] = useState(false)

  useEffect(() => { setRisk(initialRisk) }, [initialRisk])

  const loadLinkedControls = useCallback(async () => {
    setLoadingControls(true)
    try {
      const res = await listLinkedControls(risk.id)
      setLinkedControls(res)
    } catch {
      setLinkedControls([])
    } finally {
      setLoadingControls(false)
    }
  }, [risk.id])

  useEffect(() => {
    if (tab === "controls") loadLinkedControls()
  }, [tab, loadLinkedControls])

  // onUpdated kept to satisfy prop contract (parent passes it)
  void onUpdated

  const tabs: { key: "details" | "controls"; label: string }[] = [
    { key: "details",  label: "Details" },
    { key: "controls", label: `Controls${risk.linked_control_count > 0 ? ` (${risk.linked_control_count})` : ""}` },
  ]

  return (
    <div className="flex flex-col h-full">
      {/* Panel header */}
      <div className="flex items-start gap-3 px-5 pt-5 pb-4 border-b border-border flex-shrink-0">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="font-mono text-xs font-semibold text-primary bg-primary/10 px-2 py-0.5 rounded">
              {risk.risk_code}
            </span>
            {risk.is_active ? (
              <span className="inline-flex items-center gap-1 text-xs text-emerald-600">
                <Eye className="w-3 h-3" /> Active
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                <EyeOff className="w-3 h-3" /> Inactive
              </span>
            )}
          </div>
          <h2 className="text-sm font-semibold text-foreground leading-snug line-clamp-2">
            {risk.title ?? <span className="text-muted-foreground italic">No title</span>}
          </h2>
        </div>
        <div className="flex items-center gap-1 flex-shrink-0">
          <Button
            size="sm"
            variant="ghost"
            onClick={() => onEdit(risk)}
            className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground"
            title="Edit"
          >
            <Pencil className="w-3.5 h-3.5" />
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => onDelete(risk)}
            className="h-7 w-7 p-0 text-muted-foreground hover:text-destructive"
            title="Delete"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={onClose}
            className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border px-5 flex-shrink-0">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-3 py-2.5 text-xs font-medium border-b-2 transition-colors ${
              tab === t.key
                ? "border-primary text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto px-5 py-4 space-y-5">
        {tab === "details" && (
          <>
            {/* Meta grid */}
            <div className="grid grid-cols-2 gap-x-4 gap-y-3 text-xs">
              <div>
                <p className="text-muted-foreground mb-0.5">Category</p>
                <p className="text-foreground font-medium">{risk.risk_category_name ?? risk.risk_category_code}</p>
              </div>
              <div>
                <p className="text-muted-foreground mb-0.5">Risk Level</p>
                {risk.risk_level_name ? (
                  <RiskLevelDot
                    color={risk.risk_level_color ?? "#888"}
                    name={risk.risk_level_name}
                  />
                ) : (
                  <span className="text-muted-foreground italic">Not set</span>
                )}
              </div>
              <div>
                <p className="text-muted-foreground mb-0.5">Version</p>
                <p className="text-foreground font-medium">v{risk.version}</p>
              </div>
              <div>
                <p className="text-muted-foreground mb-0.5">Created</p>
                <p className="text-foreground font-medium">{formatDate(risk.created_at)}</p>
              </div>
              <div>
                <p className="text-muted-foreground mb-0.5">Linked Controls</p>
                <p className="text-foreground font-medium">{risk.linked_control_count}</p>
              </div>
              <div>
                <p className="text-muted-foreground mb-0.5">Active</p>
                <p className={risk.is_active ? "text-emerald-600 font-medium" : "text-muted-foreground font-medium"}>
                  {risk.is_active ? "Yes" : "No"}
                </p>
              </div>
            </div>

            {/* Score bar */}
            {risk.inherent_likelihood && risk.inherent_impact && risk.inherent_risk_score && (
              <div className="rounded-lg border border-border bg-muted/20 p-3">
                <ScoreBar
                  likelihood={risk.inherent_likelihood}
                  impact={risk.inherent_impact}
                  score={risk.inherent_risk_score}
                />
              </div>
            )}

            {/* Short description */}
            {risk.short_description && (
              <div>
                <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide mb-1">Summary</p>
                <p className="text-sm text-foreground">{risk.short_description}</p>
              </div>
            )}

            {/* Description */}
            {risk.description && (
              <div>
                <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide mb-1">Description</p>
                <p className="text-sm text-foreground whitespace-pre-wrap leading-relaxed">{risk.description}</p>
              </div>
            )}

            {/* Mitigation guidance */}
            {risk.mitigation_guidance && (
              <div>
                <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide mb-1 flex items-center gap-1">
                  <CheckCircle className="w-3 h-3 text-emerald-500" /> Mitigation Guidance
                </p>
                <p className="text-sm text-foreground whitespace-pre-wrap leading-relaxed">{risk.mitigation_guidance}</p>
              </div>
            )}

            {/* Detection guidance */}
            {risk.detection_guidance && (
              <div>
                <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide mb-1 flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3 text-yellow-500" /> Detection Guidance
                </p>
                <p className="text-sm text-foreground whitespace-pre-wrap leading-relaxed">{risk.detection_guidance}</p>
              </div>
            )}

            {!risk.description && !risk.short_description && !risk.mitigation_guidance && !risk.detection_guidance && (
              <p className="text-xs text-muted-foreground italic">No additional details provided.</p>
            )}
          </>
        )}

        {tab === "controls" && (
          <>
            {loadingControls ? (
              <div className="space-y-2">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-10 rounded-md bg-muted animate-pulse" />
                ))}
              </div>
            ) : linkedControls.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-10 text-center gap-2">
                <Link2 className="w-8 h-8 text-muted-foreground/40" />
                <p className="text-sm text-muted-foreground">No controls linked to this risk</p>
                <p className="text-xs text-muted-foreground">Link controls via the Risk Registry in a workspace.</p>
              </div>
            ) : (
              <div className="space-y-1.5">
                {linkedControls.map((ctrl) => (
                  <div
                    key={ctrl.id}
                    className="flex items-center gap-3 px-3 py-2.5 rounded-md border border-border bg-card hover:bg-muted/30 transition-colors"
                  >
                    <span className="font-mono text-xs font-semibold text-primary bg-primary/10 px-1.5 py-0.5 rounded flex-shrink-0">
                      {ctrl.control_code}
                    </span>
                    <span className="text-sm text-foreground truncate flex-1">{ctrl.title ?? "—"}</span>
                    {ctrl.framework_name && (
                      <span className="text-xs text-muted-foreground flex-shrink-0">{ctrl.framework_name}</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function RiskRegistryLibraryPage() {
  const { isSuperAdmin } = useAccess()

  const [risks, setRisks] = useState<GlobalRiskResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [total, setTotal] = useState(0)

  const [search, setSearch] = useState("")
  const [categoryFilter, setCategoryFilter] = useState("")
  const [levelFilter, setLevelFilter] = useState("")
  const [sortBy, setSortBy] = useState<SortField>("created_at")
  const [sortDir, setSortDir] = useState<SortDir>("desc")

  const [selectedRisk, setSelectedRisk] = useState<GlobalRiskResponse | null>(null)
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [editRisk, setEditRisk] = useState<GlobalRiskResponse | null>(null)
  const [deleteRisk, setDeleteRiskState] = useState<GlobalRiskResponse | null>(null)
  const [deleting, setDeleting] = useState(false)

  const loadRisks = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params: Record<string, string> = {}
      if (search.trim())  params.search = search.trim()
      if (categoryFilter) params.category = categoryFilter
      if (levelFilter)    params.level = levelFilter
      params.sort_by  = sortBy
      params.sort_dir = sortDir
      params.limit    = "200"
      const data = await listGlobalRisks(params)
      setRisks(data.items ?? [])
      setTotal(data.total ?? (data.items?.length ?? 0))
    } catch (err) {
      setError((err as Error).message)
      setRisks([])
    } finally {
      setLoading(false)
    }
  }, [search, categoryFilter, levelFilter, sortBy, sortDir])

  useEffect(() => { loadRisks() }, [loadRisks])

  const stats = useMemo(() => {
    const criticalCount  = risks.filter((r) => r.risk_level_code === "critical" || (r.inherent_risk_score !== null && r.inherent_risk_score >= 16)).length
    const highCount      = risks.filter((r) => r.risk_level_code === "high"     || (r.inherent_risk_score !== null && r.inherent_risk_score >= 11 && r.inherent_risk_score < 16 && r.risk_level_code !== "critical")).length
    const categoriesSet  = new Set(risks.map((r) => r.risk_category_code))
    return { criticalCount, highCount, categoriesCount: categoriesSet.size }
  }, [risks])

  const toggleSort = (field: SortField) => {
    if (sortBy === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"))
    } else {
      setSortBy(field)
      setSortDir("asc")
    }
  }

  const handleCreate = async (body: CreateGlobalRiskRequest | UpdateGlobalRiskRequest) => {
    const created = await createGlobalRisk(body as CreateGlobalRiskRequest)
    setRisks((prev) => [created, ...prev])
    setTotal((t) => t + 1)
  }

  const handleUpdate = async (body: CreateGlobalRiskRequest | UpdateGlobalRiskRequest) => {
    if (!editRisk) return
    const updated = await updateGlobalRisk(editRisk.id, body as UpdateGlobalRiskRequest)
    setRisks((prev) => prev.map((r) => (r.id === updated.id ? updated : r)))
    if (selectedRisk?.id === updated.id) setSelectedRisk(updated)
  }

  const handleDelete = async () => {
    if (!deleteRisk) return
    setDeleting(true)
    try {
      await deleteGlobalRisk(deleteRisk.id)
      setRisks((prev) => prev.filter((r) => r.id !== deleteRisk.id))
      setTotal((t) => Math.max(0, t - 1))
      if (selectedRisk?.id === deleteRisk.id) setSelectedRisk(null)
      setDeleteRiskState(null)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setDeleting(false)
    }
  }

  const handleUpdated = (updated: GlobalRiskResponse) => {
    setRisks((prev) => prev.map((r) => (r.id === updated.id ? updated : r)))
    if (selectedRisk?.id === updated.id) setSelectedRisk(updated)
  }

  const sortedFilteredRisks = useMemo(() => risks, [risks])

  const hasFilters = !!(search || categoryFilter || levelFilter)

  // KPI stat cards
  const statCards = [
    {
      label: "Total Risks",
      value: loading ? "—" : total,
      icon: Library,
      borderCls: "border-l-primary",
      numCls: "text-foreground",
      iconBg: "bg-primary/10",
      iconColor: "text-primary",
    },
    {
      label: "Critical",
      value: loading ? "—" : stats.criticalCount,
      icon: Flame,
      borderCls: "border-l-red-500",
      numCls: "text-red-600",
      iconBg: "bg-red-500/10",
      iconColor: "text-red-600",
    },
    {
      label: "High",
      value: loading ? "—" : stats.highCount,
      icon: AlertTriangle,
      borderCls: "border-l-orange-500",
      numCls: "text-orange-600",
      iconBg: "bg-orange-500/10",
      iconColor: "text-orange-600",
    },
    {
      label: "Categories",
      value: loading ? "—" : stats.categoriesCount,
      icon: Tag,
      borderCls: "border-l-blue-500",
      numCls: "text-blue-600",
      iconBg: "bg-blue-500/10",
      iconColor: "text-blue-600",
    },
  ]

  return (
    <>
      {/* Dialogs */}
      {showCreateDialog && (
        <RiskFormDialog
          onSave={handleCreate}
          onClose={() => setShowCreateDialog(false)}
        />
      )}
      {editRisk && (
        <RiskFormDialog
          initial={editRisk}
          onSave={handleUpdate}
          onClose={() => setEditRisk(null)}
        />
      )}
      {deleteRisk && (
        <DeleteDialog
          risk={deleteRisk}
          onConfirm={handleDelete}
          onClose={() => setDeleteRiskState(null)}
          saving={deleting}
        />
      )}

      <div className="flex flex-col h-full min-h-0">
        {/* Page header */}
        <div className="flex items-start justify-between gap-4 px-6 pt-6 pb-4 flex-shrink-0">
          <div>
            <h1 className="text-xl font-semibold flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-primary" />
              Risk Registry Library
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Global risk catalog — publish platform-level risks deployable to any workspace
            </p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Button
              size="sm"
              variant="ghost"
              onClick={loadRisks}
              className="h-8 w-8 p-0 text-muted-foreground"
              title="Refresh"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </Button>
            {isSuperAdmin && (
              <Button size="sm" className="h-9 gap-1.5 text-sm" onClick={() => setShowCreateDialog(true)}>
                <Plus className="w-4 h-4" /> New Risk
              </Button>
            )}
          </div>
        </div>

        {/* KPI stat cards */}
        <div className="grid grid-cols-4 gap-3 px-6 pb-4 flex-shrink-0">
          {statCards.map((s) => (
            <div
              key={s.label}
              className={`relative flex items-center gap-3 rounded-xl border border-l-[3px] ${s.borderCls} bg-card px-4 py-3`}
            >
              <div className={`shrink-0 rounded-lg p-2 ${s.iconBg}`}>
                <s.icon className={`w-4 h-4 ${s.iconColor}`} />
              </div>
              <div className="min-w-0">
                <span className={`text-2xl font-bold tabular-nums leading-none ${s.numCls}`}>{s.value}</span>
                <span className="text-[11px] text-muted-foreground mt-0.5 block truncate">{s.label}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Filter bar */}
        <div className="px-6 pb-3 flex-shrink-0">
          <div className="rounded-xl border border-border bg-card px-4 py-3 flex items-center gap-2 flex-wrap">
            <div className="relative flex-1 min-w-[200px] max-w-xs">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
              <Input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search risks..."
                className="pl-8 h-8 text-sm"
              />
            </div>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="h-8 px-2 rounded border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary min-w-[140px]"
            >
              <option value="">All Categories</option>
              {RISK_CATEGORIES.map((c) => (
                <option key={c.code} value={c.code}>{c.name}</option>
              ))}
            </select>
            <select
              value={levelFilter}
              onChange={(e) => setLevelFilter(e.target.value)}
              className="h-8 px-2 rounded border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary min-w-[120px]"
            >
              {LEVEL_FILTER_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>

            {/* Active filter chips */}
            {search && (
              <span className="inline-flex items-center gap-1 rounded-full border border-primary/20 bg-primary/10 px-2.5 py-0.5 text-xs text-primary font-medium">
                &quot;{search}&quot;
                <button onClick={() => setSearch("")} className="ml-0.5 hover:opacity-70">
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}
            {categoryFilter && (
              <span className="inline-flex items-center gap-1 rounded-full border border-primary/20 bg-primary/10 px-2.5 py-0.5 text-xs text-primary font-medium">
                {RISK_CATEGORIES.find((c) => c.code === categoryFilter)?.name ?? categoryFilter}
                <button onClick={() => setCategoryFilter("")} className="ml-0.5 hover:opacity-70">
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}
            {levelFilter && (
              <span className="inline-flex items-center gap-1 rounded-full border border-primary/20 bg-primary/10 px-2.5 py-0.5 text-xs text-primary font-medium">
                {LEVEL_FILTER_OPTIONS.find((o) => o.value === levelFilter)?.label ?? levelFilter}
                <button onClick={() => setLevelFilter("")} className="ml-0.5 hover:opacity-70">
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}
            {hasFilters && (
              <button
                onClick={() => { setSearch(""); setCategoryFilter(""); setLevelFilter("") }}
                className="text-xs text-muted-foreground hover:text-foreground ml-auto"
              >
                Clear all
              </button>
            )}
          </div>
        </div>

        {/* Main content: split list + detail */}
        <div className="flex flex-1 min-h-0 border-t border-border">
          {/* Left: list */}
          <div className={`flex flex-col min-h-0 overflow-hidden transition-all ${selectedRisk ? "w-[55%]" : "w-full"}`}>
            {/* Column headers */}
            <div className="flex items-center gap-3 px-4 py-2 border-b border-border bg-muted/30 text-xs text-muted-foreground flex-shrink-0">
              <button
                onClick={() => toggleSort("risk_code")}
                className="flex items-center gap-0.5 hover:text-foreground w-28 flex-shrink-0 font-medium"
              >
                Code <SortIcon field="risk_code" sortBy={sortBy} sortDir={sortDir} />
                {sortBy !== "risk_code" && <ArrowUpDown className="w-3 h-3 opacity-40 ml-0.5" />}
              </button>
              <button
                onClick={() => toggleSort("title")}
                className="flex-1 flex items-center gap-0.5 hover:text-foreground font-medium"
              >
                Title <SortIcon field="title" sortBy={sortBy} sortDir={sortDir} />
                {sortBy !== "title" && <ArrowUpDown className="w-3 h-3 opacity-40 ml-0.5" />}
              </button>
              {!selectedRisk && (
                <>
                  <button
                    onClick={() => toggleSort("risk_category_name")}
                    className="w-28 flex items-center gap-0.5 hover:text-foreground font-medium flex-shrink-0"
                  >
                    Category <SortIcon field="risk_category_name" sortBy={sortBy} sortDir={sortDir} />
                  </button>
                  <div className="w-24 flex-shrink-0 font-medium">Level</div>
                </>
              )}
              <button
                onClick={() => toggleSort("inherent_risk_score")}
                className="w-14 flex items-center gap-0.5 hover:text-foreground font-medium flex-shrink-0"
              >
                Score <SortIcon field="inherent_risk_score" sortBy={sortBy} sortDir={sortDir} />
              </button>
              <div className="w-4 flex-shrink-0" />
            </div>

            {/* List body */}
            <div className="flex-1 overflow-y-auto">
              {error && (
                <div className="m-4 text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2 flex items-center gap-2">
                  <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
                  {error}
                </div>
              )}

              {loading ? (
                <div className="p-4 space-y-2">
                  {[1, 2, 3, 4, 5].map((i) => <Skeleton key={i} />)}
                </div>
              ) : sortedFilteredRisks.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
                  <ShieldAlert className="w-10 h-10 text-muted-foreground/30" />
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">No risks found</p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {search || categoryFilter || levelFilter
                        ? "Try adjusting your filters"
                        : "Create a global risk to get started"}
                    </p>
                  </div>
                  {isSuperAdmin && !hasFilters && (
                    <Button size="sm" className="h-8 gap-1.5 text-xs" onClick={() => setShowCreateDialog(true)}>
                      <Plus className="w-3.5 h-3.5" /> New Risk
                    </Button>
                  )}
                </div>
              ) : (
                sortedFilteredRisks.map((risk) => {
                  const bCls = severityBorderCls(risk.risk_level_code, risk.inherent_risk_score)
                  return (
                    <div
                      key={risk.id}
                      onClick={() => setSelectedRisk((prev) => (prev?.id === risk.id ? null : risk))}
                      className={`flex items-center gap-3 pl-3 pr-4 py-3 border-b border-border border-l-[3px] ${bCls} cursor-pointer hover:bg-muted/40 transition-colors ${
                        selectedRisk?.id === risk.id ? "bg-muted/60" : ""
                      }`}
                    >
                      {/* Code */}
                      <span className="font-mono text-xs font-semibold text-primary bg-primary/10 px-1.5 py-0.5 rounded w-28 flex-shrink-0 truncate">
                        {risk.risk_code}
                      </span>

                      {/* Title + short desc */}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-foreground truncate">
                          {risk.title ?? <span className="text-muted-foreground italic">No title</span>}
                        </p>
                        {!selectedRisk && risk.short_description && (
                          <p className="text-xs text-muted-foreground truncate">{risk.short_description}</p>
                        )}
                      </div>

                      {/* Category + Level */}
                      {!selectedRisk && (
                        <>
                          <span className="text-xs text-muted-foreground w-28 flex-shrink-0 truncate">
                            {risk.risk_category_name ?? risk.risk_category_code}
                          </span>
                          <div className="w-24 flex-shrink-0">
                            {risk.risk_level_name ? (
                              <RiskLevelDot
                                color={risk.risk_level_color ?? "#888"}
                                name={risk.risk_level_name}
                              />
                            ) : (
                              <span className="text-xs text-muted-foreground">—</span>
                            )}
                          </div>
                        </>
                      )}

                      {/* Score */}
                      <div className="w-14 flex-shrink-0">
                        {risk.inherent_risk_score ? (
                          <ScorePill score={risk.inherent_risk_score} />
                        ) : (
                          <span className="text-xs text-muted-foreground">—</span>
                        )}
                      </div>

                      {/* Chevron */}
                      <ChevronRight
                        className={`w-4 h-4 flex-shrink-0 text-muted-foreground transition-transform ${
                          selectedRisk?.id === risk.id ? "rotate-90" : ""
                        }`}
                      />
                    </div>
                  )
                })
              )}
            </div>

            {/* Footer count */}
            {!loading && sortedFilteredRisks.length > 0 && (
              <div className="px-4 py-2 border-t border-border bg-muted/20 text-xs text-muted-foreground flex-shrink-0">
                Showing {sortedFilteredRisks.length}{total > sortedFilteredRisks.length ? ` of ${total}` : ""} risk{sortedFilteredRisks.length !== 1 ? "s" : ""}
              </div>
            )}
          </div>

          {/* Right: detail panel */}
          {selectedRisk && (
            <div className="w-[45%] flex-shrink-0 border-l border-border flex flex-col min-h-0 overflow-hidden">
              <RiskDetailPanel
                key={selectedRisk.id}
                risk={selectedRisk}
                onEdit={(r) => setEditRisk(r)}
                onDelete={(r) => setDeleteRiskState(r)}
                onClose={() => setSelectedRisk(null)}
                onUpdated={handleUpdated}
              />
            </div>
          )}
        </div>
      </div>
    </>
  )
}
