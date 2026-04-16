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
  Layers,
  Plus,
  Search,
  AlertTriangle,
  RefreshCw,
  Shield,
  FlaskConical,
  X,
  Download,
  Pencil,
  Trash2,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  ChevronDown,
  Tag,
  Users,
  User,
} from "lucide-react"
import {
  listAllControls,
  createControl,
  updateControl,
  deleteControl,
  listFrameworks,
  listControlCategories,
  listControlCriticalities,
  listRequirements,
} from "@/lib/api/grc"
import type {
  ControlResponse,
  CreateControlRequest,
  UpdateControlRequest,
  DimensionResponse,
  RequirementResponse,
} from "@/lib/types/grc"
import { CommentsSection } from "@/components/comments/CommentsSection"
import { AttachmentsSection } from "@/components/attachments/AttachmentsSection"
import type { OrgMemberResponse } from "@/lib/types/orgs"

// -- Constants ----------------------------------------------------------------

const CRITICALITY_META: Record<string, { label: string; color: string }> = {
  critical: { label: "Critical", color: "text-red-600 bg-red-500/10 border-red-500/20" },
  high:     { label: "High",     color: "text-orange-600 bg-orange-500/10 border-orange-500/20" },
  medium:   { label: "Medium",   color: "text-yellow-600 bg-yellow-500/10 border-yellow-500/20" },
  low:      { label: "Low",      color: "text-blue-600 bg-blue-500/10 border-blue-500/20" },
  info:     { label: "Info",     color: "text-muted-foreground bg-muted border-border" },
}

const AUTOMATION_POTENTIAL_META: Record<string, { label: string; color: string }> = {
  full:    { label: "Full",    color: "text-emerald-600 bg-emerald-500/10 border-emerald-500/20" },
  partial: { label: "Partial", color: "text-yellow-600 bg-yellow-500/10 border-yellow-500/20" },
  manual:  { label: "Manual",  color: "text-muted-foreground bg-muted border-border" },
}

const PAGE_SIZE = 50
type SortField = "name" | "criticality_code" | "framework_name" | "created_at" | "test_count"
type SortDir = "asc" | "desc"

// -- Helpers ------------------------------------------------------------------

function slugify(name: string): string {
  return name
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
}

function CriticalityBadge({ code }: { code: string }) {
  const meta = CRITICALITY_META[code] ?? { label: code, color: "text-muted-foreground bg-muted border-border" }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full border text-xs font-medium ${meta.color}`}>
      {meta.label}
    </span>
  )
}

function AutomationBadge({ potential }: { potential: string }) {
  const meta = AUTOMATION_POTENTIAL_META[potential] ?? { label: potential, color: "text-muted-foreground bg-muted border-border" }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full border text-xs font-medium ${meta.color}`}>
      {meta.label}
    </span>
  )
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
}

function SortIcon({ field, sortBy, sortDir }: { field: SortField; sortBy: SortField; sortDir: SortDir }) {
  if (field !== sortBy) return null
  return sortDir === "asc" ? <ChevronUp className="w-3 h-3 inline ml-0.5" /> : <ChevronDown className="w-3 h-3 inline ml-0.5" />
}

type OrgGroup = { id: string; name: string; is_locked: boolean }

// -- Row left-border color by status ------------------------------------------

function controlBorderCls(control: ControlResponse): string {
  // Use lifecycle_state if present, otherwise fall back to a heuristic
  const state = (control as { lifecycle_state?: string }).lifecycle_state
  if (state === "effective" || state === "active") return "border-l-green-500"
  if (state === "draft") return "border-l-amber-500"
  if (state === "deprecated") return "border-l-red-500"
  // Fallback: criticality hint
  if (control.criticality_code === "critical" || control.criticality_code === "high") return "border-l-primary"
  return "border-l-primary"
}

// -- SearchCombobox -----------------------------------------------------------

function SearchCombobox<T>({
  placeholder, value, options, getLabel, getId, onSelect, disabled,
}: {
  placeholder: string; value: string; options: T[]
  getLabel: (o: T) => string; getId: (o: T) => string
  onSelect: (id: string) => void; disabled?: boolean
}) {
  const [query, setQuery] = useState("")
  const [open, setOpen] = useState(false)
  const selected = options.find(o => getId(o) === value)
  const displayValue = selected ? getLabel(selected) : ""
  const filtered = query === "" ? options : options.filter(o => getLabel(o).toLowerCase().includes(query.toLowerCase()))

  function handleSelect(id: string) { onSelect(id); setQuery(""); setOpen(false) }

  return (
    <div className="relative">
      <input
        type="text"
        className="w-full h-8 rounded-md border border-input bg-background text-sm px-2 pr-7"
        placeholder={open ? "Search..." : (displayValue || placeholder)}
        value={open ? query : displayValue}
        onFocus={() => { setOpen(true); setQuery("") }}
        onChange={e => { setQuery(e.target.value); setOpen(true) }}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        disabled={disabled}
      />
      {value && (
        <button type="button" className="absolute right-1.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground text-xs"
          onMouseDown={e => { e.preventDefault(); handleSelect("") }}>×</button>
      )}
      {open && filtered.length > 0 && (
        <div className="absolute z-50 top-full left-0 right-0 mt-0.5 bg-popover border border-border rounded-md shadow-md max-h-48 overflow-y-auto">
          {filtered.map(o => (
            <button key={getId(o)} type="button"
              className={`w-full text-left px-3 py-1.5 text-sm hover:bg-accent ${getId(o) === value ? "bg-accent/50 font-medium" : ""}`}
              onMouseDown={e => { e.preventDefault(); handleSelect(getId(o)) }}>
              {getLabel(o)}
            </button>
          ))}
        </div>
      )}
      {open && filtered.length === 0 && (
        <div className="absolute z-50 top-full left-0 right-0 mt-0.5 bg-popover border border-border rounded-md shadow-md px-3 py-2 text-sm text-muted-foreground">
          No results
        </div>
      )}
    </div>
  )
}

// -- Skeleton -----------------------------------------------------------------

function Skeleton() {
  return (
    <div className="rounded-xl border border-l-[3px] border-l-muted border-border bg-card p-4 animate-pulse space-y-2">
      <div className="flex items-center gap-3">
        <div className="h-4 w-40 bg-muted rounded" />
        <div className="h-4 w-20 bg-muted rounded" />
      </div>
      <div className="h-3 w-56 bg-muted rounded" />
    </div>
  )
}

// -- Helpers ------------------------------------------------------------------

function getJwtSubject(): string | null {
  try {
    const token = localStorage.getItem("access_token")
    if (!token) return null
    const payload = JSON.parse(atob(token.split(".")[1]))
    return payload.sub || null
  } catch { return null }
}

// -- Detail Side Panel --------------------------------------------------------

function ControlDetailPanel({
  control,
  orgMembers,
  orgGroups,
  onEdit,
  onDelete,
  onClose,
}: {
  control: ControlResponse
  orgMembers: OrgMemberResponse[]
  orgGroups: OrgGroup[]
  onEdit: (c: ControlResponse) => void
  onDelete: (c: ControlResponse) => void
  onClose: () => void
}) {
  const [detailTab, setDetailTab] = useState<"details" | "comments" | "attachments">("details")

  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-[480px] bg-background border-l border-border shadow-xl z-40 flex flex-col">
      <div className="flex items-center justify-between px-5 py-4 border-b border-border shrink-0">
        <div className="flex items-center gap-2 min-w-0">
          <Layers className="w-4 h-4 text-primary shrink-0" />
          <div className="min-w-0">
            <span className="font-semibold text-sm truncate block">{control.name}</span>
            <span className="font-mono text-xs text-muted-foreground">{control.control_code}</span>
          </div>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <Button variant="ghost" size="sm" className="h-8 px-2" onClick={() => onEdit(control)}>
            <Pencil className="w-3.5 h-3.5" />
          </Button>
          <Button variant="ghost" size="sm" className="h-8 px-2 text-destructive hover:text-destructive" onClick={() => onDelete(control)}>
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
          <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>

      <div className="flex border-b border-border px-4 bg-muted/20" role="tablist">
        {(["details", "comments", "attachments"] as const).map((tab) => (
          <button
            key={tab}
            role="tab"
            aria-selected={detailTab === tab}
            onClick={() => setDetailTab(tab)}
            className={`px-3 py-2.5 text-xs font-medium border-b-2 transition-colors whitespace-nowrap capitalize
              ${detailTab === tab
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {detailTab === "details" && (
      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        <div className="flex items-center gap-2 flex-wrap">
          <CriticalityBadge code={control.criticality_code} />
          <span className="inline-flex items-center gap-1">
            <AutomationBadge potential={control.automation_potential} />
            <span className="text-xs text-muted-foreground">automation</span>
          </span>
        </div>

        {control.description && (
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">Description</p>
            <p className="text-sm text-foreground">{control.description}</p>
          </div>
        )}

        {control.guidance && (
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">Guidance</p>
            <p className="text-sm text-foreground">{control.guidance}</p>
          </div>
        )}

        {control.implementation_notes && (
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">Implementation Notes</p>
            <p className="text-sm text-foreground">{control.implementation_notes}</p>
          </div>
        )}

        {control.implementation_guidance && control.implementation_guidance.length > 0 && (
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">Implementation Guidance</p>
            <ul className="list-disc list-inside text-xs text-muted-foreground space-y-0.5">
              {control.implementation_guidance.map((g, i) => <li key={i}>{g}</li>)}
            </ul>
          </div>
        )}

        <div className="grid grid-cols-2 gap-x-4 gap-y-3 text-xs">
          <div>
            <p className="text-muted-foreground mb-0.5">Control Code</p>
            <p className="font-mono text-foreground">{control.control_code}</p>
          </div>
          <div>
            <p className="text-muted-foreground mb-0.5">Framework</p>
            <p className="text-foreground">{control.framework_name}</p>
          </div>
          <div>
            <p className="text-muted-foreground mb-0.5">Requirement</p>
            <p className="font-mono text-foreground">{control.requirement_code ?? "—"}</p>
          </div>
          <div>
            <p className="text-muted-foreground mb-0.5">Control Domain</p>
            <p className="text-foreground">{control.category_name}</p>
          </div>
          <div>
            <p className="text-muted-foreground mb-0.5">Automation</p>
            <div className="flex items-center gap-1">
              <AutomationBadge potential={control.automation_potential} />
              <span className="text-muted-foreground/60 text-xs">(from tests)</span>
            </div>
          </div>
          <div>
            <p className="text-muted-foreground mb-0.5">Tests Linked</p>
            <p className="font-semibold text-foreground">{control.test_count}</p>
          </div>
          <div>
            <p className="text-muted-foreground mb-0.5">Version</p>
            <p className="font-mono text-foreground">v{control.version}</p>
          </div>
          {control.owner_user_id && (
            <div className="col-span-2">
              <p className="text-muted-foreground mb-0.5 flex items-center gap-1"><User className="w-3 h-3" /> Owner</p>
              <p className="text-foreground">
                {(() => {
                  const m = orgMembers.find(x => x.user_id === control.owner_user_id)
                  return m ? (m.display_name || m.email || m.user_id) : control.owner_user_id
                })()}
              </p>
            </div>
          )}
          {control.responsible_teams && control.responsible_teams.length > 0 && (
            <div className="col-span-2">
              <p className="text-muted-foreground mb-0.5 flex items-center gap-1"><Users className="w-3 h-3" /> Responsible Teams</p>
              <div className="flex flex-wrap gap-1 mt-0.5">
                {control.responsible_teams.map(t => {
                  const grp = orgGroups.find(g => g.id === t)
                  return <span key={t} className="px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-600 text-xs border border-blue-500/20">{grp ? grp.name : t}</span>
                })}
              </div>
            </div>
          )}
          {control.tags && control.tags.length > 0 && (
            <div className="col-span-2">
              <p className="text-muted-foreground mb-0.5 flex items-center gap-1"><Tag className="w-3 h-3" /> Tags</p>
              <div className="flex flex-wrap gap-1 mt-0.5">
                {control.tags.map(t => (
                  <span key={t} className="px-1.5 py-0.5 rounded bg-muted text-xs text-muted-foreground">{t}</span>
                ))}
              </div>
            </div>
          )}
          <div>
            <p className="text-muted-foreground mb-0.5">Created</p>
            <p className="text-foreground">{formatDate(control.created_at)}</p>
          </div>
        </div>

        {/* Linked tests count */}
        <div>
          <p className="text-xs font-medium text-muted-foreground mb-2">Linked Tests</p>
          <div className="flex items-center gap-2 text-xs text-foreground">
            <FlaskConical className="w-3.5 h-3.5 text-muted-foreground" />
            <span className="font-semibold">{control.test_count}</span>
            <span className="text-muted-foreground">tests linked to this control</span>
          </div>
        </div>
      </div>
      )}

      {detailTab === "comments" && (
      <div className="flex-1 overflow-y-auto p-5">
        <CommentsSection entityType="control" entityId={control.id} currentUserId={getJwtSubject() ?? ""} />
      </div>
      )}

      {detailTab === "attachments" && (
      <div className="flex-1 overflow-y-auto p-5">
        <AttachmentsSection entityType="control" entityId={control.id} currentUserId={getJwtSubject() ?? ""} />
      </div>
      )}
    </div>
  )
}

// -- Create / Edit Dialog -----------------------------------------------------

function ControlDialog({
  mode,
  control,
  frameworks,
  categories,
  criticalities,
  orgMembers,
  orgGroups,
  onSaved,
  onClose,
}: {
  mode: "create" | "edit"
  control?: ControlResponse
  frameworks: { id: string; name: string; framework_code: string }[]
  categories: DimensionResponse[]
  criticalities: DimensionResponse[]
  orgMembers: OrgMemberResponse[]
  orgGroups: OrgGroup[]
  onSaved: (c: ControlResponse) => void
  onClose: () => void
}) {
  const [frameworkId, setFrameworkId] = useState(control?.framework_id ?? frameworks[0]?.id ?? "")
  const [name, setName] = useState(control?.name ?? "")
  const [desc, setDesc] = useState(control?.description ?? "")
  const [categoryCode, setCategoryCode] = useState(control?.control_category_code ?? categories[0]?.code ?? "")
  const [critCode, setCritCode] = useState(control?.criticality_code ?? criticalities[0]?.code ?? "")
  const [controlType, setControlType] = useState(control?.control_type ?? "preventive")
  const [automationPotential, setAutomationPotential] = useState(control?.automation_potential ?? "manual")
  const [requirementId, setRequirementId] = useState(control?.requirement_id ?? "")
  const [requirements, setRequirements] = useState<RequirementResponse[]>([])
  const [guidance, setGuidance] = useState(control?.guidance ?? "")
  const [implementationNotes, setImplementationNotes] = useState(control?.implementation_notes ?? "")
  const [implGuidance, setImplGuidance] = useState((control?.implementation_guidance ?? []).join("\n"))
  const [ownerUserId, setOwnerUserId] = useState(control?.owner_user_id ?? "")
  const [responsibleGroupId, setResponsibleGroupId] = useState(control?.responsible_teams?.[0] ?? "")
  const [tags, setTags] = useState((control?.tags ?? []).join(", "))
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Auto-generated code from name (create mode only)
  const autoCode = useMemo(() => slugify(name), [name])
  // In edit mode, show the existing control_code
  const displayCode = mode === "edit" ? (control?.control_code ?? "") : autoCode

  // Load requirements when framework selected
  useEffect(() => {
    if (!frameworkId) { setRequirements([]); return }
    listRequirements(frameworkId).then(res => setRequirements(res.items ?? [])).catch(() => setRequirements([]))
  }, [frameworkId])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!frameworkId && mode === "create") { setError("Select a framework"); return }
    setSaving(true)
    setError(null)
    try {
      const parsedGuidance = implGuidance.split("\n").map(l => l.trim()).filter(Boolean)
      const parsedTags = tags.split(",").map(t => t.trim()).filter(Boolean)
      let result: ControlResponse
      if (mode === "create") {
        const payload: CreateControlRequest = {
          control_code: autoCode || name.slice(0, 50),
          control_category_code: categoryCode,
          criticality_code: critCode,
          control_type: controlType,
          automation_potential: automationPotential,
          requirement_id: requirementId || undefined,
          name,
          description: desc || undefined,
          guidance: guidance || undefined,
          implementation_notes: implementationNotes || undefined,
          implementation_guidance: parsedGuidance.length ? parsedGuidance : undefined,
          owner_user_id: ownerUserId || undefined,
          responsible_teams: responsibleGroupId ? [responsibleGroupId] : undefined,
          tags: parsedTags.length ? parsedTags : undefined,
        }
        result = await createControl(frameworkId, payload)
      } else {
        const payload: UpdateControlRequest = {
          name,
          description: desc || undefined,
          control_category_code: categoryCode,
          criticality_code: critCode,
          control_type: controlType,
          automation_potential: automationPotential,
          requirement_id: requirementId || undefined,
          guidance: guidance || undefined,
          implementation_notes: implementationNotes || undefined,
          implementation_guidance: parsedGuidance.length ? parsedGuidance : undefined,
          owner_user_id: ownerUserId || undefined,
          responsible_teams: responsibleGroupId ? [responsibleGroupId] : undefined,
          tags: parsedTags.length ? parsedTags : undefined,
        }
        result = await updateControl(control!.framework_id, control!.id, payload)
      }
      onSaved(result)
      onClose()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{mode === "create" ? "Create Control" : "Edit Control"}</DialogTitle>
          <DialogDescription>
            {mode === "create" ? "Add a new control to a framework." : "Update control details."}
          </DialogDescription>
        </DialogHeader>

        {error && <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-3">
          {mode === "create" && (
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">Framework <span className="text-destructive">*</span></Label>
              <select
                value={frameworkId}
                onChange={e => { setFrameworkId(e.target.value); setRequirementId("") }}
                className="w-full h-8 px-2 rounded border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                required
              >
                <option value="">— Select framework —</option>
                {frameworks.map(f => <option key={f.id} value={f.id}>{f.name} ({f.framework_code})</option>)}
              </select>
            </div>
          )}

          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Name <span className="text-destructive">*</span></Label>
            <Input value={name} onChange={e => setName(e.target.value)} placeholder="Control name" required className="h-8 text-sm" />
            {mode === "create" && name.trim() && (
              <p className="text-[11px] text-muted-foreground mt-1 font-mono">
                Code: <span className="text-foreground">{displayCode || "—"}</span>
              </p>
            )}
            {mode === "edit" && (
              <p className="text-[11px] text-muted-foreground mt-1 font-mono">
                Code: <span className="text-foreground">{displayCode}</span>
              </p>
            )}
          </div>

          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Description</Label>
            <textarea
              value={desc}
              onChange={e => setDesc(e.target.value)}
              placeholder="Brief description of this control"
              rows={2}
              className="w-full rounded-md border border-input bg-background text-sm px-3 py-2 resize-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">Control Domain <span className="text-destructive">*</span></Label>
              <select
                value={categoryCode}
                onChange={e => setCategoryCode(e.target.value)}
                className="w-full h-8 px-2 rounded border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                required
              >
                {categories.map(c => <option key={c.code} value={c.code}>{c.name}</option>)}
              </select>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">Criticality <span className="text-destructive">*</span></Label>
              <select
                value={critCode}
                onChange={e => setCritCode(e.target.value)}
                className="w-full h-8 px-2 rounded border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                required
              >
                {criticalities.map(c => <option key={c.code} value={c.code}>{c.name}</option>)}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">Control Type</Label>
              <select
                value={controlType}
                onChange={e => setControlType(e.target.value)}
                className="w-full h-8 px-2 rounded border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="preventive">Preventive</option>
                <option value="detective">Detective</option>
                <option value="corrective">Corrective</option>
                <option value="compensating">Compensating</option>
              </select>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">Automation Potential</Label>
              <select
                value={automationPotential}
                onChange={e => setAutomationPotential(e.target.value)}
                className="w-full h-8 px-2 rounded border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="manual">Manual</option>
                <option value="partial">Partial</option>
                <option value="full">Full</option>
              </select>
            </div>
          </div>

          {requirements.length > 0 && (
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">Framework Requirement <span className="text-muted-foreground/60">(optional)</span></Label>
              <select
                value={requirementId}
                onChange={e => setRequirementId(e.target.value)}
                className="w-full h-8 px-2 rounded border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="">— No specific requirement —</option>
                {requirements.map(r => <option key={r.id} value={r.id}>{r.requirement_code} – {r.name}</option>)}
              </select>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">Owner</Label>
              <SearchCombobox<OrgMemberResponse>
                placeholder="Search by name or email…"
                value={ownerUserId}
                options={orgMembers}
                getId={m => m.user_id}
                getLabel={m => m.display_name ? `${m.display_name} — ${m.email || ""}` : (m.email || m.user_id)}
                onSelect={id => setOwnerUserId(id)}
              />
            </div>
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">Responsible Group</Label>
              <SearchCombobox<OrgGroup>
                placeholder="Search groups…"
                value={responsibleGroupId}
                options={orgGroups}
                getId={g => g.id}
                getLabel={g => g.is_locked ? `${g.name} 🔒` : g.name}
                onSelect={id => setResponsibleGroupId(id)}
              />
            </div>
          </div>

          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Guidance</Label>
            <Input value={guidance} onChange={e => setGuidance(e.target.value)} placeholder="High-level guidance" className="h-8 text-sm" />
          </div>

          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Implementation Notes</Label>
            <Input value={implementationNotes} onChange={e => setImplementationNotes(e.target.value)} placeholder="Technical implementation notes" className="h-8 text-sm" />
          </div>

          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Implementation Guidance <span className="font-normal">(one per line)</span></Label>
            <textarea
              value={implGuidance}
              onChange={e => setImplGuidance(e.target.value)}
              placeholder={"Enforce MFA for all admin accounts\nLog all access attempts\nReview access quarterly"}
              rows={3}
              className="w-full rounded-md border border-input bg-background text-sm px-3 py-2 resize-none"
            />
          </div>

          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Tags <span className="font-normal">(comma-separated)</span></Label>
            <Input value={tags} onChange={e => setTags(e.target.value)} placeholder="iam, soc2, access-control" className="h-8 text-sm" />
          </div>

          <DialogFooter>
            <Button type="button" variant="ghost" onClick={onClose} className="h-9 px-4">Cancel</Button>
            <Button type="submit" disabled={saving} className="h-9">
              {saving ? (mode === "create" ? "Creating..." : "Saving...") : (mode === "create" ? "Create Control" : "Save Changes")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// -- Delete Confirm -----------------------------------------------------------

function DeleteConfirmDialog({
  control,
  onConfirm,
  onClose,
}: {
  control: ControlResponse
  onConfirm: () => Promise<void>
  onClose: () => void
}) {
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleDelete = async () => {
    setDeleting(true)
    try {
      await onConfirm()
      onClose()
    } catch (e) {
      setError((e as Error).message)
      setDeleting(false)
    }
  }

  return (
    <Dialog open onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Delete Control</DialogTitle>
          <DialogDescription>
            Are you sure you want to delete <strong>{control.name}</strong>? This action cannot be undone.
          </DialogDescription>
        </DialogHeader>
        {error && <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">{error}</div>}
        <DialogFooter>
          <Button type="button" variant="ghost" onClick={onClose} className="h-9 px-4">Cancel</Button>
          <Button variant="destructive" onClick={handleDelete} disabled={deleting} className="h-9">
            {deleting ? "Deleting..." : "Delete"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// -- Main Page ----------------------------------------------------------------

export default function AdminControlsPage() {
  const [controls, setControls] = useState<ControlResponse[]>([])
  const [frameworks, setFrameworks] = useState<{ id: string; name: string; framework_code: string }[]>([])
  const [categories, setCategories] = useState<DimensionResponse[]>([])
  const [criticalities, setCriticalities] = useState<DimensionResponse[]>([])
  const [orgMembers, setOrgMembers] = useState<OrgMemberResponse[]>([])
  const [orgGroups, setOrgGroups] = useState<OrgGroup[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // dialogs
  const [showCreate, setShowCreate] = useState(false)
  const [editTarget, setEditTarget] = useState<ControlResponse | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<ControlResponse | null>(null)
  const [detailTarget, setDetailTarget] = useState<ControlResponse | null>(null)

  // filters
  const [search, setSearch] = useState("")
  const [filterFramework, setFilterFramework] = useState("")
  const [filterCategory, setFilterCategory] = useState("")
  const [filterCriticality, setFilterCriticality] = useState("")
  const [filterAutomation, setFilterAutomation] = useState("")
  const [showAll, setShowAll] = useState(false)

  // Track published framework IDs for filtering
  const [publishedFrameworkIds, setPublishedFrameworkIds] = useState<Set<string>>(new Set())

  // sort + pagination
  const [sortBy, setSortBy] = useState<SortField>("name")
  const [sortDir, setSortDir] = useState<SortDir>("asc")
  const [page, setPage] = useState(0)

  const load = useCallback(async (quiet = false) => {
    if (quiet) setRefreshing(true); else setLoading(true)
    setError(null)
    try {
      const [fwRes, catsRes, critsRes, controlsRes] = await Promise.all([
        listFrameworks(),
        listControlCategories(),
        listControlCriticalities(),
        listAllControls({ limit: 500 }),
      ])
      const fwList = fwRes.items
      setFrameworks(fwList.map(f => ({ id: f.id, name: f.name ?? f.framework_code, framework_code: f.framework_code })))
      setPublishedFrameworkIds(new Set(fwList.filter(f => f.is_marketplace_visible).map(f => f.id)))
      setCategories(catsRes)
      setCriticalities(critsRes)
      setControls(controlsRes.items)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  // Load org members + groups for owner/team dropdowns (best-effort, non-blocking)
  useEffect(() => {
    import("@/lib/api/admin").then(({ listGroups }) => {
      listGroups().then(r => setOrgGroups((r.groups ?? []).map((g: { id: string; name: string; is_locked: boolean }) => ({ id: g.id, name: g.name, is_locked: g.is_locked })))).catch(() => {})
    }).catch(() => {})
    import("@/lib/api/orgs").then(({ listOrgs, listOrgMembers }) => {
      listOrgs().then(orgs => {
        const firstOrg = orgs[0]
        if (firstOrg) listOrgMembers(firstOrg.id).then(m => setOrgMembers(m)).catch(() => {})
      }).catch(() => {})
    }).catch(() => {})
  }, [])

  const handleSaved = useCallback((control: ControlResponse) => {
    setControls(prev => {
      const idx = prev.findIndex(c => c.id === control.id)
      if (idx >= 0) {
        const next = [...prev]
        next[idx] = control
        return next
      }
      return [control, ...prev]
    })
  }, [])

  const handleDelete = useCallback(async (control: ControlResponse) => {
    await deleteControl(control.framework_id, control.id)
    setControls(prev => prev.filter(c => c.id !== control.id))
    if (detailTarget?.id === control.id) setDetailTarget(null)
  }, [detailTarget])

  const handleSort = (field: SortField) => {
    if (sortBy === field) setSortDir(d => d === "asc" ? "desc" : "asc")
    else { setSortBy(field); setSortDir("asc") }
    setPage(0)
  }

  const filtered = useMemo(() => {
    let items = controls.filter(c => {
      // Default: show only controls from published frameworks
      if (!showAll && !publishedFrameworkIds.has(c.framework_id)) return false
      if (search.trim()) {
        const q = search.toLowerCase()
        if (!c.name.toLowerCase().includes(q) && !c.control_code.toLowerCase().includes(q)) return false
      }
      if (filterFramework && c.framework_id !== filterFramework) return false
      if (filterCategory && c.control_category_code !== filterCategory) return false
      if (filterCriticality && c.criticality_code !== filterCriticality) return false
      if (filterAutomation && c.automation_potential !== filterAutomation) return false
      return true
    })

    const CRIT_ORDER: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3, info: 4 }
    items = [...items].sort((a, b) => {
      let av: string | number = ""
      let bv: string | number = ""
      if (sortBy === "name") { av = a.name; bv = b.name }
      else if (sortBy === "criticality_code") { av = CRIT_ORDER[a.criticality_code] ?? 99; bv = CRIT_ORDER[b.criticality_code] ?? 99 }
      else if (sortBy === "framework_name") { av = a.framework_name ?? ""; bv = b.framework_name ?? "" }
      else if (sortBy === "created_at") { av = a.created_at; bv = b.created_at }
      else if (sortBy === "test_count") { av = a.test_count ?? 0; bv = b.test_count ?? 0 }
      if (typeof av === "number" && typeof bv === "number") {
        return sortDir === "asc" ? av - bv : bv - av
      }
      const cmp = String(av).localeCompare(String(bv))
      return sortDir === "asc" ? cmp : -cmp
    })

    return items
  }, [controls, search, filterFramework, filterCategory, filterCriticality, filterAutomation, sortBy, sortDir, showAll, publishedFrameworkIds])

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE)
  const paginated = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)
  const hasFilters = !!(search.trim() || filterFramework || filterCategory || filterCriticality || filterAutomation)

  const clearFilters = () => {
    setSearch(""); setFilterFramework(""); setFilterCategory("")
    setFilterCriticality(""); setFilterAutomation(""); setPage(0)
  }

  const exportCsv = () => {
    const rows = [
      ["code", "name", "framework", "category", "criticality", "control_type", "automation_potential", "test_count", "created_at"],
      ...filtered.map(c => [
        c.control_code,
        c.name,
        c.framework_name ?? "",
        c.category_name,
        c.criticality_code,
        c.control_type,
        c.automation_potential,
        String(c.test_count ?? 0),
        c.created_at,
      ]),
    ]
    const csv = rows.map(row => row.map(v => `"${String(v).replace(/"/g, '""')}"`).join(",")).join("\n")
    const blob = new Blob([csv], { type: "text/csv" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "controls.csv"
    a.click()
    URL.revokeObjectURL(url)
  }

  const criticalCount = controls.filter(c => c.criticality_code === "critical").length
  const totalTests = controls.reduce((s, c) => s + (c.test_count ?? 0), 0)

  // KPI card colors
  const kpiCards = [
    { label: "Total Controls",    value: controls.length, icon: Layers,      borderCls: "border-l-primary",   numCls: "text-foreground" },
    { label: "Critical Controls", value: criticalCount,   icon: Shield,      borderCls: "border-l-red-500",   numCls: "text-red-600" },
    { label: "Tests Linked",      value: totalTests,      icon: FlaskConical, borderCls: "border-l-blue-500", numCls: "text-blue-600" },
  ]

  return (
    <div className={`p-6 space-y-6 ${detailTarget ? "mr-[480px]" : ""} max-w-5xl transition-all`}>
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold">{showAll ? "All Controls" : "Published Controls"}</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {showAll
              ? "Controls across all frameworks and workspaces."
              : "Controls from published frameworks only."
            }{" "}
            <button onClick={() => { setShowAll(!showAll); setPage(0) }} className="text-primary hover:underline font-medium">
              {showAll ? "Show Published Only" : "Show All Controls"}
            </button>
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Button variant="ghost" size="sm" className="h-8 px-2" onClick={exportCsv} title="Export CSV">
            <Download className="w-3.5 h-3.5 mr-1" /> Export
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0"
            onClick={() => load(true)}
            disabled={refreshing}
            title="Refresh"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
          </Button>
          <Button onClick={() => setShowCreate(true)} size="sm" className="h-8 px-3 shrink-0">
            <Plus className="w-3.5 h-3.5 mr-1" /> Add Control
          </Button>
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-3 gap-3">
        {kpiCards.map(s => (
          <div key={s.label} className={`relative flex items-center gap-3 rounded-xl border border-l-[3px] ${s.borderCls} bg-card px-4 py-3`}>
            <div className="shrink-0 rounded-lg p-2 bg-muted">
              <s.icon className="w-4 h-4 text-muted-foreground" />
            </div>
            <div className="min-w-0">
              <span className={`text-2xl font-bold tabular-nums leading-none ${s.numCls}`}>{s.value}</span>
              <span className="text-[11px] text-muted-foreground mt-0.5 block truncate">{s.label}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Filter bar */}
      <div className="rounded-xl border border-border bg-card px-4 py-3 flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-muted-foreground" />
          <Input
            className="pl-9 h-9"
            placeholder="Search controls by name or code..."
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(0) }}
          />
        </div>
        <select
          value={filterFramework}
          onChange={e => { setFilterFramework(e.target.value); setPage(0) }}
          className="h-9 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
        >
          <option value="">All Frameworks</option>
          {frameworks.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
        </select>
        {categories.length > 0 && (
          <select
            value={filterCategory}
            onChange={e => { setFilterCategory(e.target.value); setPage(0) }}
            className="h-9 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="">All Domains</option>
            {categories.map(c => <option key={c.code} value={c.code}>{c.name}</option>)}
          </select>
        )}
        {criticalities.length > 0 && (
          <select
            value={filterCriticality}
            onChange={e => { setFilterCriticality(e.target.value); setPage(0) }}
            className="h-9 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="">All Criticalities</option>
            {criticalities.map(c => <option key={c.code} value={c.code}>{c.name}</option>)}
          </select>
        )}
        <select
          value={filterAutomation}
          onChange={e => { setFilterAutomation(e.target.value); setPage(0) }}
          className="h-9 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
        >
          <option value="">All Test Coverage</option>
          <option value="full">Full</option>
          <option value="partial">Partial</option>
          <option value="manual">Manual</option>
        </select>

        {/* Active filter chips */}
        {search.trim() && (
          <button
            onClick={() => { setSearch(""); setPage(0) }}
            className="inline-flex items-center gap-1 h-7 px-2.5 rounded-full bg-primary/10 text-primary text-xs font-medium hover:bg-primary/20 transition-colors"
          >
            &ldquo;{search}&rdquo; <X className="w-3 h-3" />
          </button>
        )}
        {filterFramework && (
          <button
            onClick={() => { setFilterFramework(""); setPage(0) }}
            className="inline-flex items-center gap-1 h-7 px-2.5 rounded-full bg-primary/10 text-primary text-xs font-medium hover:bg-primary/20 transition-colors"
          >
            {frameworks.find(f => f.id === filterFramework)?.name ?? filterFramework} <X className="w-3 h-3" />
          </button>
        )}
        {filterCategory && (
          <button
            onClick={() => { setFilterCategory(""); setPage(0) }}
            className="inline-flex items-center gap-1 h-7 px-2.5 rounded-full bg-primary/10 text-primary text-xs font-medium hover:bg-primary/20 transition-colors"
          >
            {categories.find(c => c.code === filterCategory)?.name ?? filterCategory} <X className="w-3 h-3" />
          </button>
        )}
        {filterCriticality && (
          <button
            onClick={() => { setFilterCriticality(""); setPage(0) }}
            className="inline-flex items-center gap-1 h-7 px-2.5 rounded-full bg-primary/10 text-primary text-xs font-medium hover:bg-primary/20 transition-colors"
          >
            {criticalities.find(c => c.code === filterCriticality)?.name ?? filterCriticality} <X className="w-3 h-3" />
          </button>
        )}
        {filterAutomation && (
          <button
            onClick={() => { setFilterAutomation(""); setPage(0) }}
            className="inline-flex items-center gap-1 h-7 px-2.5 rounded-full bg-primary/10 text-primary text-xs font-medium hover:bg-primary/20 transition-colors"
          >
            {filterAutomation} coverage <X className="w-3 h-3" />
          </button>
        )}
        {hasFilters && (
          <Button variant="ghost" size="sm" className="h-9 px-2 text-muted-foreground ml-auto" onClick={clearFilters}>
            Clear all
          </Button>
        )}
      </div>

      {/* Sort + count */}
      {!loading && !error && (
        <div className="flex items-center gap-4 text-xs text-muted-foreground flex-wrap">
          <span>Showing {filtered.length} of {controls.length} controls{hasFilters ? " (filtered)" : ""}</span>
          <span className="text-muted-foreground/50">|</span>
          <span>Sort by:</span>
          {(["name", "criticality_code", "framework_name", "test_count", "created_at"] as SortField[]).map(f => (
            <button
              key={f}
              className={`hover:text-foreground transition-colors ${sortBy === f ? "text-foreground font-medium" : ""}`}
              onClick={() => handleSort(f)}
            >
              {f === "criticality_code" ? "Criticality" : f === "framework_name" ? "Framework" : f === "test_count" ? "Tests" : f === "created_at" ? "Created" : "Name"}
              <SortIcon field={f} sortBy={sortBy} sortDir={sortDir} />
            </button>
          ))}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertTriangle className="w-4 h-4 shrink-0" /> {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => <Skeleton key={i} />)}
        </div>
      )}

      {/* List */}
      {!loading && !error && (
        <div className="space-y-1">
          {paginated.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              {hasFilters ? "No controls match your filters." : "No controls yet. Add your first control to get started."}
            </p>
          ) : (
            paginated.map(control => {
              const borderCls = controlBorderCls(control)
              return (
                <div
                  key={control.id}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl border border-l-[3px] ${borderCls} transition-colors cursor-pointer
                    ${detailTarget?.id === control.id ? "border-primary/20 bg-primary/5" : "border-border bg-card hover:border-border/80 hover:bg-muted/30"}`}
                  onClick={() => setDetailTarget(prev => prev?.id === control.id ? null : control)}
                >
                  <Layers className="w-4 h-4 shrink-0 text-primary" />

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap min-w-0">
                      <span className="font-medium text-sm truncate">{control.name}</span>
                      <span className="font-mono text-xs text-muted-foreground hidden sm:inline">{control.control_code}</span>
                    </div>
                    <div className="flex items-center gap-2 mt-0.5">
                      <CriticalityBadge code={control.criticality_code} />
                      {control.version > 1 && (
                        <span className="font-mono text-[10px] text-muted-foreground border border-border/50 rounded px-1 hidden md:inline">v{control.version}</span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-4 shrink-0 text-xs text-muted-foreground">
                    <span className="hidden xl:inline text-[10px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-600 border border-blue-500/20 font-medium truncate max-w-[140px]">{control.framework_name}</span>
                    <span className="hidden lg:inline">{control.category_name}</span>
                    <AutomationBadge potential={control.automation_potential} />
                    <span className="hidden md:flex items-center gap-1">
                      <FlaskConical className="w-3 h-3" />
                      {control.test_count}
                    </span>
                    <span className="hidden sm:inline">{formatDate(control.created_at)}</span>
                  </div>

                  <div className="flex items-center gap-1 shrink-0" onClick={e => e.stopPropagation()}>
                    <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => setEditTarget(control)} title="Edit">
                      <Pencil className="w-3 h-3" />
                    </Button>
                    <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-destructive hover:text-destructive" onClick={() => setDeleteTarget(control)} title="Delete">
                      <Trash2 className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
              )
            })
          )}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-2">
          <span className="text-xs text-muted-foreground">
            Page {page + 1} of {totalPages} ({filtered.length} total)
          </span>
          <div className="flex items-center gap-1">
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0" disabled={page === 0} onClick={() => setPage(p => p - 1)}>
              <ChevronLeft className="w-4 h-4" />
            </Button>
            {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
              const pageNum = totalPages <= 7 ? i : (page < 4 ? i : (page > totalPages - 4 ? totalPages - 7 + i : page - 3 + i))
              return (
                <Button
                  key={pageNum}
                  variant={pageNum === page ? "default" : "ghost"}
                  size="sm"
                  className="h-8 w-8 p-0 text-xs"
                  onClick={() => setPage(pageNum)}
                >
                  {pageNum + 1}
                </Button>
              )
            })}
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0" disabled={page >= totalPages - 1} onClick={() => setPage(p => p + 1)}>
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Detail panel */}
      {detailTarget && (
        <>
          <div className="fixed inset-0 z-30" onClick={() => setDetailTarget(null)} />
          <ControlDetailPanel
            control={detailTarget}
            orgMembers={orgMembers}
            orgGroups={orgGroups}
            onEdit={c => { setDetailTarget(null); setEditTarget(c) }}
            onDelete={c => { setDetailTarget(null); setDeleteTarget(c) }}
            onClose={() => setDetailTarget(null)}
          />
        </>
      )}

      {/* Dialogs */}
      {showCreate && (
        <ControlDialog
          mode="create"
          frameworks={frameworks}
          categories={categories}
          criticalities={criticalities}
          orgMembers={orgMembers}
          orgGroups={orgGroups}
          onSaved={c => { handleSaved(c); setShowCreate(false) }}
          onClose={() => setShowCreate(false)}
        />
      )}
      {editTarget && (
        <ControlDialog
          mode="edit"
          control={editTarget}
          frameworks={frameworks}
          categories={categories}
          criticalities={criticalities}
          orgMembers={orgMembers}
          orgGroups={orgGroups}
          onSaved={c => { handleSaved(c); setEditTarget(null) }}
          onClose={() => setEditTarget(null)}
        />
      )}
      {deleteTarget && (
        <DeleteConfirmDialog
          control={deleteTarget}
          onConfirm={() => handleDelete(deleteTarget)}
          onClose={() => setDeleteTarget(null)}
        />
      )}
    </div>
  )
}
