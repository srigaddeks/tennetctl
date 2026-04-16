"use client"

import React, { useEffect, useState, useCallback, useMemo } from "react"
import { useRouter } from "next/navigation"
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@kcontrol/ui"
import {
  Layers,
  Search,
  Plus,
  ChevronDown,
  ChevronRight,
  Pencil,
  Trash2,
  AlertTriangle,
  X,
  Download,
  Zap,
  ClipboardList,
  Sparkles,
  CheckCircle2,
  Loader2,
  Circle,
  Clock,
  FileText,
  GitMerge,
  Info,
  ExternalLink,
  ClipboardCheck,
  TableProperties,
  List,
  Target,
  HelpCircle,
  Filter,
} from "lucide-react"
import {
  listFrameworks,
  listAllControls,
  createControl,
  updateControl,
  deleteControl,
  listControlCategories,
  listControlCriticalities,
  listRequirements,
  listTestExecutions,
  listControlTests,
  listTasks,
  exportControls,
  importControls,
  getControlsImportTemplate,
} from "@/lib/api/grc"
import {
  suggestTestsForControl,
  applyTestLinkerSuggestionsForControl,
  type TestSuggestion,
} from "@/lib/api/testLinker"
import type {
  ControlResponse,
  FrameworkResponse,
  RequirementResponse,
  DimensionResponse,
  CreateControlRequest,
  UpdateControlRequest,
  TestExecutionResponse,
  TestResponse,
  TaskResponse,
} from "@/lib/types/grc"
import { ReadOnlyBanner } from "@/components/layout/ReadOnlyBanner"
import { useAccess } from "@/components/providers/AccessProvider"
import { useOrgWorkspace } from "@/lib/context/OrgWorkspaceContext"
import { TaskCreateSlideOver } from "@/components/tasks/TaskCreateSlideOver"
import { FormFillChat } from "@/components/ai/FormFillChat"
import { EntitySpreadsheet } from "@/components/spreadsheet/EntitySpreadsheet"
import { ImportResultDialog } from "@/components/spreadsheet/ImportResultDialog"
import type { ImportResult } from "@/components/spreadsheet/ImportResultDialog"
import { controlsColumns } from "@/components/spreadsheet/controlsConfig"
import type { ControlSpreadsheetRow } from "@/components/spreadsheet/controlsConfig"
import { LinkTestsDialog } from "@/components/grc/LinkTestsDialog"

// ── Helpers ──────────────────────────────────────────────────────────────────

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

const CONTROL_TYPES = ["preventive", "detective", "corrective", "compensating"] as const
const AUTOMATION_LEVELS = ["full", "partial", "manual"] as const

/** Normalise result_status from TestExecution into a display status */
function execHealthStatus(exec: TestExecutionResponse | undefined): "Pass" | "Fail" | "Partial" | null {
  if (!exec) return null
  const s = exec.result_status?.toLowerCase()
  if (s === "pass" || s === "passed") return "Pass"
  if (s === "fail" || s === "failed") return "Fail"
  if (s === "partial") return "Partial"
  return null
}

/** Left border colour driven by the latest execution result, fallback to criticality */
function getBorderColor(c: ControlResponse, exec: TestExecutionResponse | undefined): string {
  const h = execHealthStatus(exec)
  if (h === "Fail") return "border-l-red-500"
  if (h === "Partial") return "border-l-amber-500"
  if (h === "Pass") return "border-l-green-500"
  // no execution yet — use criticality as fallback
  if (c.criticality_code === "critical") return "border-l-red-500"
  if (c.criticality_code === "high") return "border-l-orange-500"
  if (c.criticality_code === "medium") return "border-l-amber-500"
  return "border-l-slate-500"
}

function getHealthBadge(status: "Pass" | "Fail" | "Partial") {
  if (status === "Pass") return "bg-green-500/10 text-green-500 border-green-500/30"
  if (status === "Fail") return "bg-red-500/10 text-red-500 border-red-500/30"
  return "bg-amber-500/10 text-amber-500 border-amber-500/30"
}

function getCriticalityBadge(code: string) {
  if (code === "critical") return "bg-red-500/10 text-red-500 border-red-500/30"
  if (code === "high") return "bg-orange-500/10 text-orange-500 border-orange-500/30"
  if (code === "medium") return "bg-amber-500/10 text-amber-500 border-amber-500/30"
  return "bg-green-500/10 text-green-500 border-green-500/30"
}

function formatExecTime(iso: string): string {
  const d = new Date(iso)
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffDays = Math.floor(diffMs / 86400000)
  if (diffDays === 0) {
    return `Today ${d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`
  }
  if (diffDays === 1) return "Yesterday"
  if (diffDays < 7) return `${diffDays}d ago`
  return d.toLocaleDateString([], { month: "short", day: "numeric" })
}

// ── Task helpers ──────────────────────────────────────────────────────────────

const PRIORITY_COLORS: Record<string, string> = {
  critical: "bg-red-500/10 text-red-500 border-red-500/30",
  high: "bg-orange-500/10 text-orange-500 border-orange-500/30",
  medium: "bg-amber-500/10 text-amber-500 border-amber-500/30",
  low: "bg-green-500/10 text-green-500 border-green-500/30",
}

const TASK_STATUS_STYLES: Record<string, string> = {
  open: "text-muted-foreground",
  in_progress: "text-blue-500",
  completed: "text-green-500",
  blocked: "text-red-500",
}

const TEST_TYPE_STYLES: Record<string, string> = {
  automated: "bg-emerald-500/10 text-emerald-500 border-emerald-500/30",
  manual: "bg-sky-500/10 text-sky-500 border-sky-500/30",
  hybrid: "bg-violet-500/10 text-violet-500 border-violet-500/30",
}

function Chip({ label, className }: { label: string; className?: string }) {
  return (
    <span className={`inline-flex items-center rounded border px-1.5 py-0 text-[10px] font-semibold uppercase ${className ?? ""}`}>
      {label}
    </span>
  )
}

function TaskStatusIcon({ status }: { status: string }) {
  if (status === "completed") return <CheckCircle2 className="w-3 h-3 text-green-500" />
  if (status === "in_progress") return <Clock className="w-3 h-3 text-blue-500" />
  if (status === "blocked") return <AlertTriangle className="w-3 h-3 text-red-500" />
  return <Circle className="w-3 h-3 text-muted-foreground" />
}

function FrequencyBadge({ frequency }: { frequency?: string | null }) {
  if (!frequency || frequency === "none") return null
  return (
    <span className="inline-flex items-center px-1.5 py-0 rounded text-[10px] font-medium border bg-violet-500/10 text-violet-500 border-violet-500/30 shrink-0">
      {frequency}
    </span>
  )
}

// ── Filter Glossary Popover ─────────────────────────────────────────────────────

const FILTER_GLOSSARY = [
  {
    title: "Criticality",
    color: "text-red-400",
    icon: "🔴",
    description: "How bad it is if this control fails.",
    items: [
      { label: "Critical", desc: "Must not fail. Severe impact on security or compliance." },
      { label: "High", desc: "Very important. Failure puts major obligations at risk." },
      { label: "Medium", desc: "Standard importance. Failure causes moderate disruption." },
      { label: "Low", desc: "Nice to have. Minimal impact if skipped." },
    ],
  },
  {
    title: "Control Type",
    color: "text-purple-400",
    icon: "🛡",
    description: "When does this control act — before, during, or after a problem?",
    items: [
      { label: "Preventive", desc: "Stops issues before they happen. (e.g. requiring MFA)" },
      { label: "Detective", desc: "Spots issues after they happen. (e.g. audit logs, alerts)" },
      { label: "Corrective", desc: "Fixes the damage after an issue. (e.g. restoring a backup)" },
      { label: "Compensating", desc: "A workaround when the ideal control isn’t possible." },
    ],
  },
  {
    title: "Automation",
    color: "text-cyan-400",
    icon: "⚡",
    description: "How much human effort does this control need?",
    items: [
      { label: "Full", desc: "Runs automatically, no human touch needed." },
      { label: "Partial", desc: "System does the hard work, a person reviews or approves." },
      { label: "Manual", desc: "A person must complete this control every time." },
    ],
  },
  {
    title: "Gaps Only",
    color: "text-amber-400",
    icon: "⚠️",
    description: "Show only controls that are missing tests or have failing tests — your compliance blind spots.",
    items: [],
  },
]

function FilterGlossaryPopover() {
  const [open, setOpen] = useState(false)
  const btnRef = React.useRef<HTMLButtonElement>(null)
  const panelRef = React.useRef<HTMLDivElement>(null)
  const [pos, setPos] = React.useState({ top: 0, left: 0 })

  function handleOpen() {
    if (btnRef.current) {
      const rect = btnRef.current.getBoundingClientRect()
      setPos({ top: rect.bottom + 6, left: rect.left })
    }
    setOpen(v => !v)
  }

  // Close on click outside; reposition on scroll so it stays anchored to the button
  useEffect(() => {
    if (!open) return
    function onMouseDown(e: MouseEvent) {
      if (
        panelRef.current && !panelRef.current.contains(e.target as Node) &&
        btnRef.current && !btnRef.current.contains(e.target as Node)
      ) {
        setOpen(false)
      }
    }
    function onScroll() {
      if (btnRef.current) {
        const rect = btnRef.current.getBoundingClientRect()
        setPos({ top: rect.bottom + 6, left: rect.left })
      }
    }
    document.addEventListener("mousedown", onMouseDown)
    window.addEventListener("scroll", onScroll, true)
    return () => {
      document.removeEventListener("mousedown", onMouseDown)
      window.removeEventListener("scroll", onScroll, true)
    }
  }, [open])

  return (
    <div className="relative">
      <button
        ref={btnRef}
        type="button"
        id="filter-glossary-btn-controls"
        aria-label="Explain filter categories"
        onClick={handleOpen}
        className="flex items-center justify-center w-5 h-5 rounded-full text-muted-foreground/60 hover:text-muted-foreground hover:bg-muted/50 transition-colors"
      >
        <HelpCircle className="w-3.5 h-3.5" />
      </button>

      {open && (
        <div
          ref={panelRef}
          className="fixed z-50 w-80 rounded-xl border border-border bg-card shadow-xl p-4 space-y-4 animate-in fade-in slide-in-from-top-1"
          style={{ top: pos.top, left: pos.left }}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold tracking-wide uppercase text-foreground">What do these filters mean?</span>
            <button type="button" onClick={() => setOpen(false)} className="text-muted-foreground hover:text-foreground">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="space-y-3">
            {FILTER_GLOSSARY.map(group => (
              <div key={group.title}>
                <div className="flex items-center gap-1.5 mb-1">
                  <span>{group.icon}</span>
                  <span className={`text-[11px] font-bold uppercase tracking-wide ${group.color}`}>{group.title}</span>
                </div>
                <p className="text-[11px] text-muted-foreground mb-1.5 leading-relaxed">{group.description}</p>
                {group.items.length > 0 && (
                  <div className="space-y-0.5 pl-2 border-l border-border/50">
                    {group.items.map(item => (
                      <div key={item.label} className="flex gap-1.5">
                        <span className="text-[10px] font-semibold text-foreground shrink-0 w-20">{item.label}</span>
                        <span className="text-[10px] text-muted-foreground leading-relaxed">{item.desc}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
          <p className="text-[10px] text-muted-foreground/60 border-t border-border pt-2">
            Click any filter button to narrow your control list. Combine filters to find exactly what you need.
          </p>
        </div>
      )}
    </div>
  )
}

// ── AI Suggest Tests for Control ─────────────────────────────────────────────

const LINK_TYPE_STYLES: Record<string, string> = {
  covers: "bg-green-500/10 text-green-600 border-green-500/30",
  partially_covers: "bg-amber-500/10 text-amber-600 border-amber-500/30",
  related: "bg-sky-500/10 text-sky-600 border-sky-500/30",
}

function AiSuggestTestsPanel({
  controlId,
  orgId,
  workspaceId,
  onLinked,
  onClose,
}: {
  controlId: string
  orgId?: string
  workspaceId?: string
  onLinked: () => void
  onClose: () => void
}) {
  const [loading, setLoading] = useState(true)
  const [suggestions, setSuggestions] = useState<TestSuggestion[]>([])
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [applying, setApplying] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [applyMsg, setApplyMsg] = useState<string | null>(null)

  useEffect(() => {
    suggestTestsForControl({
      control_id: controlId,
      org_id: orgId,
      workspace_id: workspaceId,
    })
      .then((s) => {
        setSuggestions(s)
        setSelected(new Set(s.map((x) => x.test_id)))
      })
      .catch((e) => setError(e instanceof Error ? e.message : "AI suggestion failed"))
      .finally(() => setLoading(false))
  }, [controlId, orgId, workspaceId])

  async function handleApply() {
    const approved = suggestions.filter((s) => selected.has(s.test_id))
    if (!approved.length) return
    setApplying(true)
    setError(null)
    try {
      const r = await applyTestLinkerSuggestionsForControl({ control_id: controlId, suggestions: approved })
      setApplyMsg(
        `Submitted ${r.created} mapping${r.created !== 1 ? "s" : ""} for approval${r.skipped ? ` (${r.skipped} already existed)` : ""}`,
      )
      setSuggestions([])
      setSelected(new Set())
      onLinked()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to apply")
    } finally {
      setApplying(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-3 text-xs text-muted-foreground">
        <Loader2 className="h-3 w-3 animate-spin text-violet-500" />
        Finding relevant control tests…
      </div>
    )
  }

  return (
    <div className="mt-2 border border-violet-500/20 rounded-lg bg-violet-500/5 p-3 space-y-2">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-semibold text-violet-600 flex items-center gap-1">
          <Sparkles className="h-3 w-3" /> AI Suggestions
        </span>
        <button className="text-[11px] text-muted-foreground hover:text-foreground" onClick={onClose}>
          <X className="h-3.5 w-3.5" />
        </button>
      </div>

      {error && (
        <div className="text-xs text-destructive flex items-center gap-1.5">
          <AlertTriangle className="h-3 w-3 shrink-0" /> {error}
        </div>
      )}

      {applyMsg && (
        <div className="text-xs text-green-600 flex items-center gap-1.5">
          <CheckCircle2 className="h-3 w-3 shrink-0" /> {applyMsg}
        </div>
      )}

      {!applyMsg && (
        <p className="text-[10px] text-muted-foreground">
          AI-suggested links are submitted as pending mappings and need approval before they become active.
        </p>
      )}

      {suggestions.length === 0 && !error && !applyMsg && (
        <p className="text-xs text-muted-foreground">No relevant control tests found.</p>
      )}

      {suggestions.length > 0 && (
        <>
          <div className="space-y-1.5 max-h-60 overflow-y-auto">
            {suggestions.map((s) => {
              const isSel = selected.has(s.test_id)
              return (
                <div
                  key={s.test_id}
                  className={`flex items-start gap-2 px-2 py-1.5 rounded-md cursor-pointer transition-colors ${isSel ? "bg-violet-500/10" : "hover:bg-muted/40"}`}
                  onClick={() => setSelected((prev) => {
                    const n = new Set(prev)
                    n.has(s.test_id) ? n.delete(s.test_id) : n.add(s.test_id)
                    return n
                  })}
                >
                  <div className={`mt-0.5 h-3.5 w-3.5 rounded border shrink-0 flex items-center justify-center ${isSel ? "border-violet-500 bg-violet-500" : "border-border"}`}>
                    {isSel && <CheckCircle2 className="h-2.5 w-2.5 text-white" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="text-[11px] font-mono text-primary">{s.test_code}</span>
                      <span className={`text-[9px] px-1 rounded border font-semibold ${LINK_TYPE_STYLES[s.link_type] ?? ""}`}>
                        {s.link_type.replace("_", " ")}
                      </span>
                      <span className="text-[10px] text-muted-foreground ml-auto">{Math.round(s.confidence * 100)}%</span>
                    </div>
                    <p className="text-[10px] text-muted-foreground mt-0.5 leading-relaxed">{s.rationale}</p>
                  </div>
                </div>
              )
            })}
          </div>

          <div className="flex items-center gap-2 pt-1">
            <span className="text-[11px] text-muted-foreground flex-1">{selected.size} of {suggestions.length} selected</span>
            <button className="text-[11px] underline text-muted-foreground" onClick={() => setSelected(new Set(suggestions.map(s => s.test_id)))}>All</button>
            <button className="text-[11px] underline text-muted-foreground" onClick={() => setSelected(new Set())}>None</button>
            <button
              className="flex items-center gap-1 text-[11px] font-semibold text-white bg-violet-600 hover:bg-violet-700 px-2.5 py-1 rounded-md disabled:opacity-50 transition-colors"
              disabled={selected.size === 0 || applying}
              onClick={handleApply}
            >
              {applying ? <Loader2 className="h-2.5 w-2.5 animate-spin" /> : <Sparkles className="h-2.5 w-2.5" />}
              Submit {selected.size}
            </button>
          </div>
        </>
      )}
    </div>
  )
}

// ── Control Hierarchy Panel (Tests → Tasks → Add Task) ──────────────────────

function ControlHierarchyPanel({
  control,
  frameworkId,
  defaultOrgId,
  defaultWorkspaceId,
}: {
  control: ControlResponse
  frameworkId: string
  defaultOrgId: string
  defaultWorkspaceId: string
}) {
  const router = useRouter()
  const [tests, setTests] = useState<TestResponse[]>([])
  const [tasks, setTasks] = useState<TaskResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedTests, setExpandedTests] = useState<Set<string>>(new Set())

  const [taskSlideOver, setTaskSlideOver] = useState<{ open: boolean; typeCode: string; typeName: string } | null>(null)
  const [aiSuggestOpen, setAiSuggestOpen] = useState(false)
  const [linkTestOpen, setLinkTestOpen] = useState(false)

  const today = new Date().toISOString().split("T")[0]

  const loadData = useCallback((silent = false) => {
    if (!silent) setLoading(true)
    Promise.all([
      listControlTests(frameworkId, control.id).then(r => setTests(r.items ?? [])).catch(() => { }),
      listTasks({ entity_type: "control", entity_id: control.id, limit: 50 }).then(r => setTasks(r.items ?? [])).catch(() => { }),
    ]).finally(() => { if (!silent) setLoading(false) })
  }, [frameworkId, control.id])

  useEffect(() => { loadData() }, [loadData])

  const evidenceTasks = tasks.filter(t => t.task_type_code === "evidence_collection")
  const remediationTasks = tasks.filter(t => t.task_type_code !== "evidence_collection")

  if (loading) return (
    <div className="space-y-1.5 py-3 px-4">
      {[1, 2, 3].map(i => <div key={i} className="h-7 rounded bg-muted animate-pulse" />)}
    </div>
  )

  return (
    <div className="py-3 px-4 space-y-1 text-xs border-t border-border/40 bg-muted/10">
      {/* Control meta row */}
      <div className="flex items-center gap-4 pb-2 mb-1 border-b border-border/40 text-muted-foreground">
        {control.category_name && <span>Category: <span className="text-foreground font-medium">{control.category_name}</span></span>}
        <span>Automation: <span className="text-foreground font-medium capitalize">{control.automation_potential}</span></span>
        {control.requirement_code && <span>Group: <span className="text-foreground font-medium">{control.requirement_name ?? control.requirement_code}</span></span>}
      </div>

      {tests.length === 0 && tasks.length === 0 ? (
        <p className="text-muted-foreground py-2">No tests or tasks attached to this control.</p>
      ) : (
        <div className="space-y-1">
          {tests.map((test, idx) => {
            const expanded = expandedTests.has(test.id)
            const isLast = idx === tests.length - 1 && remediationTasks.length === 0
            return (
              <div key={test.id}>
                <div
                  className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-muted/40 hover:bg-muted/60 cursor-pointer transition-colors group"
                  onClick={() => setExpandedTests(prev => {
                    const n = new Set(prev)
                    n.has(test.id) ? n.delete(test.id) : n.add(test.id)
                    return n
                  })}
                >
                  <span className="w-4 shrink-0 text-border">{isLast ? "└─" : "├─"}</span>
                  {expanded
                    ? <ChevronDown className="w-3 h-3 text-muted-foreground shrink-0" />
                    : <ChevronRight className="w-3 h-3 text-muted-foreground shrink-0" />
                  }
                  {test.is_platform_managed
                    ? <Zap className="w-3 h-3 text-amber-500 shrink-0" />
                    : <ClipboardCheck className="w-3 h-3 text-blue-500 shrink-0" />
                  }
                  <span className="font-mono text-[11px] text-primary shrink-0">{test.test_code}</span>
                  <span className="truncate font-medium">{test.name ?? test.test_code}</span>
                  <button
                    className="ml-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-primary"
                    onClick={(e) => { e.stopPropagation(); router.push(`/tests?highlight=${test.id}`) }}
                    title="View test details"
                  >
                    <Info className="w-3 h-3" />
                  </button>
                  <Badge variant="outline" className={`ml-auto shrink-0 text-[10px] px-1.5 py-0 ${TEST_TYPE_STYLES[test.test_type_code] ?? ""}`}>
                    {test.test_type_name ?? test.test_type_code}
                  </Badge>
                  {test.integration_type && test.integration_type !== "none" && (
                    <span className="inline-flex items-center px-1.5 py-0 rounded text-[10px] font-medium border bg-gray-500/10 text-gray-500 border-gray-500/30 shrink-0">
                      {test.integration_type}
                    </span>
                  )}
                  <FrequencyBadge frequency={test.monitoring_frequency} />
                </div>
              </div>
            )
          })}

          {/* Evidence tasks */}
          {evidenceTasks.length > 0 && (
            <div>
              <div className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-muted/40 mt-1">
                <span className="w-4 shrink-0 text-border">├─</span>
                <FileText className="w-3 h-3 text-sky-500 shrink-0" />
                <span className="font-medium text-muted-foreground">Evidence Tasks</span>
                <span className="ml-auto text-muted-foreground">{evidenceTasks.length}</span>
              </div>
              <div className="ml-8 mt-0.5 space-y-0.5">
                {evidenceTasks.map((task) => {
                  const isOverdue = task.due_date && task.due_date < today && !task.is_terminal
                  return (
                    <div key={task.id} className="flex items-center gap-2 px-2 py-1 rounded bg-muted/20 text-[11px] group hover:bg-muted/40 transition-colors">
                      <span className="w-4 shrink-0 text-border/60">│  └─</span>
                      <TaskStatusIcon status={task.status_code} />
                      <Chip label={task.priority_code} className={PRIORITY_COLORS[task.priority_code] ?? "bg-muted text-muted-foreground border-border"} />
                      <span className="truncate">{task.title}</span>
                      <button
                        className="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-primary"
                        onClick={() => router.push(`/tasks?highlight=${task.id}`)}
                        title="View task"
                      >
                        <ExternalLink className="w-3 h-3" />
                      </button>
                      <span className={`ml-auto shrink-0 capitalize ${TASK_STATUS_STYLES[task.status_code] ?? ""}`}>{task.status_name}</span>
                      {task.due_date && (
                        <span className={`shrink-0 ${isOverdue ? "text-red-500 font-semibold" : "text-muted-foreground"}`}>
                          {new Date(task.due_date).toLocaleDateString()}
                          {isOverdue && " ⚠"}
                        </span>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Remediation tasks */}
          {remediationTasks.length > 0 && (
            <div>
              <div className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-muted/40 mt-1">
                <span className="w-4 shrink-0 text-border">└─</span>
                <GitMerge className="w-3 h-3 text-orange-500 shrink-0" />
                <span className="font-medium text-muted-foreground">Remediation Tasks</span>
                <span className="ml-auto text-muted-foreground">{remediationTasks.length}</span>
              </div>
              <div className="ml-8 mt-0.5 space-y-0.5">
                {remediationTasks.map((task) => {
                  const isOverdue = task.due_date && task.due_date < today && !task.is_terminal
                  return (
                    <div key={task.id} className="flex items-center gap-2 px-2 py-1 rounded bg-muted/20 text-[11px] group hover:bg-muted/40 transition-colors">
                      <span className="w-4 shrink-0 text-border/60">│  └─</span>
                      <TaskStatusIcon status={task.status_code} />
                      <Chip label={task.priority_code} className={PRIORITY_COLORS[task.priority_code] ?? "bg-muted text-muted-foreground border-border"} />
                      <span className="truncate">{task.title}</span>
                      <button
                        className="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-primary"
                        onClick={() => router.push(`/tasks?highlight=${task.id}`)}
                        title="View task"
                      >
                        <ExternalLink className="w-3 h-3" />
                      </button>
                      <span className={`ml-auto shrink-0 capitalize ${TASK_STATUS_STYLES[task.status_code] ?? ""}`}>{task.status_name}</span>
                      {task.due_date && (
                        <span className={`shrink-0 ${isOverdue ? "text-red-500 font-semibold" : "text-muted-foreground"}`}>
                          {new Date(task.due_date).toLocaleDateString()}
                          {isOverdue && " ⚠"}
                        </span>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Add task buttons */}
      <div className="pt-2 border-t border-border/30 mt-2 flex items-center gap-3 flex-wrap">
        <button
          type="button"
          onClick={() => setTaskSlideOver({ open: true, typeCode: "evidence_collection", typeName: "Evidence Collection" })}
          className="flex items-center gap-1.5 text-[11px] text-sky-600 hover:text-sky-500 transition-colors"
        >
          <FileText className="w-3 h-3" /> Add Evidence Task
        </button>
        <span className="text-border/50">|</span>
        <button
          type="button"
          onClick={() => setTaskSlideOver({ open: true, typeCode: "control_remediation", typeName: "Remediation" })}
          className="flex items-center gap-1.5 text-[11px] text-orange-600 hover:text-orange-500 transition-colors"
        >
          <Target className="w-3 h-3" /> Add Remediation Task
        </button>
        <span className="text-border/50">|</span>
        <button
          type="button"
          onClick={() => setLinkTestOpen(true)}
          className="flex items-center gap-1.5 text-[11px] text-emerald-600 hover:text-emerald-500 transition-colors"
        >
          <Layers className="w-3 h-3" /> Link Test
        </button>
        <span className="text-border/50">|</span>
        <button
          type="button"
          onClick={() => setAiSuggestOpen((v) => !v)}
          className="flex items-center gap-1.5 text-[11px] text-violet-600 hover:text-violet-500 transition-colors"
        >
          <Sparkles className="w-3 h-3" /> AI Find Tests
        </button>
      </div>

      {/* AI Suggest Tests panel */}
      {aiSuggestOpen && (
        <AiSuggestTestsPanel
          controlId={control.id}
          orgId={defaultOrgId}
          workspaceId={defaultWorkspaceId}
          onLinked={() => loadData(true)}
          onClose={() => setAiSuggestOpen(false)}
        />
      )}

      {/* Task create slide-over */}
      {taskSlideOver && (
        <TaskCreateSlideOver
          open={taskSlideOver.open}
          onClose={() => setTaskSlideOver(null)}
          onCreated={() => { loadData(true); setTaskSlideOver(null) }}
          taskTypeCode={taskSlideOver.typeCode}
          taskTypeName={taskSlideOver.typeName}
          entityType="control"
          entityId={control.id}
          entityTitle={control.name}
          orgId={defaultOrgId}
          workspaceId={defaultWorkspaceId}
        />
      )}
    </div>
  )
}

// ── Create Control Dialog ────────────────────────────────────────────────────

function slugifyControl(text: string): string {
  return text.toUpperCase().replace(/\s+/g, "_").replace(/[^A-Z0-9_\-\.]/g, "").replace(/^[^A-Z0-9]+/, "").replace(/[^A-Z0-9]+$/, "").slice(0, 32) || ""
}

function CreateControlDialog({
  open, frameworks, categories, criticalities, onCreate, onClose,
}: {
  open: boolean
  frameworks: FrameworkResponse[]
  categories: DimensionResponse[]
  criticalities: DimensionResponse[]
  onCreate: (frameworkId: string, payload: CreateControlRequest) => Promise<void>
  onClose: () => void
}) {
  const [frameworkId, setFrameworkId] = useState("")
  const [requirements, setRequirements] = useState<RequirementResponse[]>([])
  const [requirementId, setRequirementId] = useState("")
  const [name, setName] = useState("")
  const [code, setCode] = useState("")
  const [codeEdited, setCodeEdited] = useState(false)
  const [description, setDescription] = useState("")
  const [categoryCode, setCategoryCode] = useState("")
  const [criticalityCode, setCriticalityCode] = useState("")
  const [automationPotential, setAutomationPotential] = useState<string>("manual")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loadingReqs, setLoadingReqs] = useState(false)

  useEffect(() => {
    if (open) {
      setFrameworkId(frameworks[0]?.id ?? ""); setRequirementId(""); setCode(""); setName("")
      setCodeEdited(false)
      setDescription(""); setCategoryCode(categories[0]?.code ?? "")
      setCriticalityCode(criticalities[0]?.code ?? "")
      setAutomationPotential("manual")
      setSaving(false); setError(null); setRequirements([])
    }
  }, [open, frameworks, categories, criticalities])

  useEffect(() => {
    if (!frameworkId) { setRequirements([]); return }
    setLoadingReqs(true)
    listRequirements(frameworkId)
      .then((res) => { setRequirements(res.items ?? []); setRequirementId(res.items?.[0]?.id ?? "") })
      .catch(() => setRequirements([]))
      .finally(() => setLoadingReqs(false))
  }, [frameworkId])

  function handleNameChange(v: string) {
    setName(v)
    if (!codeEdited) setCode(slugifyControl(v))
  }

  async function create() {
    if (!name.trim()) { setError("Name is required."); return }
    if (!frameworkId) { setError("Select a framework."); return }
    if (!requirementId) { setError("Select a requirement."); return }
    setSaving(true); setError(null)
    const currentUserId = getJwtSubject()
    try {
      await onCreate(frameworkId, {
        control_code: code.trim() || slugifyControl(name),
        requirement_id: requirementId,
        control_category_code: categoryCode,
        criticality_code: criticalityCode,
        control_type: "preventive",
        automation_potential: automationPotential,
        name: name.trim(),
        description: description.trim() || undefined,
        owner_user_id: currentUserId ?? undefined,
      })
      onClose()
    } catch (e) { setError(e instanceof Error ? e.message : "Failed to create control"); setSaving(false) }
  }

  function handleAIFilled(fields: Record<string, string>) {
    if (fields.name) { setName(fields.name); if (!codeEdited) setCode(slugifyControl(fields.name)) }
    if (fields.description) setDescription(fields.description)
    if (fields.control_category_code && categories.some((c) => c.code === fields.control_category_code)) setCategoryCode(fields.control_category_code)
    if (fields.criticality_code && criticalities.some((c) => c.code === fields.criticality_code)) setCriticalityCode(fields.criticality_code)
    if (fields.automation_potential && ["full", "partial", "manual"].includes(fields.automation_potential)) setAutomationPotential(fields.automation_potential)
  }

  const selectedFramework = frameworks.find((f) => f.id === frameworkId)

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-primary/10 p-2.5"><Plus className="h-4 w-4 text-primary" /></div>
            <div>
              <DialogTitle>New Control</DialogTitle>
              <DialogDescription>Add a control to a framework requirement.</DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <FormFillChat
          entityType="control"
          onFilled={handleAIFilled}
          getFormValues={() => ({ name, description, control_code: code, control_category_code: categoryCode, criticality_code: criticalityCode, automation_potential: automationPotential })}
          placeholder="e.g. enforce MFA for all admin users"
          pageContext={selectedFramework ? { framework_id: selectedFramework.id, framework_name: selectedFramework.name } : undefined}
        />
        <Separator className="my-2" />
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs">Framework</Label>
              <select className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={frameworkId} onChange={(e) => setFrameworkId(e.target.value)}>
                <option value="">Select framework...</option>
                {frameworks.map((fw) => <option key={fw.id} value={fw.id}>{fw.name || fw.framework_code}</option>)}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Requirement</Label>
              <select className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={requirementId} onChange={(e) => setRequirementId(e.target.value)} disabled={loadingReqs}>
                <option value="">{loadingReqs ? "Loading..." : "Select requirement..."}</option>
                {requirements.map((r) => <option key={r.id} value={r.id}>{r.requirement_code} - {r.name}</option>)}
              </select>
            </div>
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Name</Label>
            <Input value={name} onChange={(e) => handleNameChange(e.target.value)} placeholder="Access Control Policy" className="h-9 text-sm" autoFocus />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Code <span className="text-muted-foreground text-[10px]">auto-generated · editable</span></Label>
            <Input value={code} onChange={(e) => { setCode(e.target.value.toUpperCase().replace(/[^A-Z0-9_\-\.]/g, "")); setCodeEdited(true) }} placeholder="ACCESS_CONTROL_POLICY" className="h-9 text-sm font-mono" />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Description <span className="text-muted-foreground text-[10px]">optional</span></Label>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Control description..."
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm min-h-[60px] resize-y" />
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs">Category</Label>
              <select className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={categoryCode} onChange={(e) => setCategoryCode(e.target.value)}>
                {categories.map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Criticality</Label>
              <select className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={criticalityCode} onChange={(e) => setCriticalityCode(e.target.value)}>
                {criticalities.map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Automation</Label>
              <select className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={automationPotential} onChange={(e) => setAutomationPotential(e.target.value)}>
                {AUTOMATION_LEVELS.map((a) => <option key={a} value={a}>{a}</option>)}
              </select>
            </div>
          </div>
        </div>
        {error && <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500 mt-2">{error}</p>}
        <DialogFooter className="mt-3 gap-2 sm:gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={saving}>Cancel</Button>
          <Button size="sm" onClick={create} disabled={saving}>
            {saving ? <span className="flex items-center gap-1.5"><span className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />Creating...</span> : "Create Control"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ── Edit Control Dialog ──────────────────────────────────────────────────────

function EditControlDialog({
  control, categories, criticalities, onSave, onClose,
}: {
  control: ControlResponse | null
  categories: DimensionResponse[]
  criticalities: DimensionResponse[]
  onSave: (frameworkId: string, controlId: string, payload: UpdateControlRequest) => Promise<void>
  onClose: () => void
}) {
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [categoryCode, setCategoryCode] = useState("")
  const [criticalityCode, setCriticalityCode] = useState("")
  const [controlType, setControlType] = useState("")
  const [automationPotential, setAutomationPotential] = useState("")
  const [guidance, setGuidance] = useState("")
  const [implNotes, setImplNotes] = useState("")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (control) {
      setName(control.name); setDescription(control.description ?? "")
      setCategoryCode(control.control_category_code)
      setCriticalityCode(control.criticality_code)
      setControlType(control.control_type)
      setAutomationPotential(control.automation_potential)
      setGuidance(control.guidance ?? "")
      setImplNotes(control.implementation_notes ?? "")
      setSaving(false); setError(null)
    }
  }, [control])

  if (!control) return null

  async function save() {
    if (!name.trim()) { setError("Name is required."); return }
    setSaving(true); setError(null)
    try {
      await onSave(control!.framework_id, control!.id, {
        name: name.trim(),
        description: description.trim(),
        control_category_code: categoryCode,
        criticality_code: criticalityCode,
        control_type: controlType,
        automation_potential: automationPotential,
        guidance: guidance.trim() || undefined,
        implementation_notes: implNotes.trim() || undefined,
      })
      onClose()
    } catch (e) { setError(e instanceof Error ? e.message : "Failed to save"); setSaving(false) }
  }

  function handleAIFilled(fields: Record<string, string>) {
    if (fields.name) setName(fields.name)
    if (fields.description) setDescription(fields.description)
    if (fields.control_category_code && categories.some((c) => c.code === fields.control_category_code)) setCategoryCode(fields.control_category_code)
    if (fields.criticality_code && criticalities.some((c) => c.code === fields.criticality_code)) setCriticalityCode(fields.criticality_code)
    if (fields.control_type) setControlType(fields.control_type)
    if (fields.automation_potential && ["full", "partial", "manual"].includes(fields.automation_potential)) setAutomationPotential(fields.automation_potential)
    if (fields.guidance) setGuidance(fields.guidance)
    if (fields.implementation_notes) setImplNotes(fields.implementation_notes)
  }

  return (
    <Dialog open onOpenChange={(o) => { if (!o) onClose() }}>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-primary/10 p-2.5"><Pencil className="h-4 w-4 text-primary" /></div>
            <div>
              <DialogTitle>Edit Control</DialogTitle>
              <DialogDescription><code className="text-xs font-mono text-foreground/60">{control.control_code}</code> in {control.framework_name}</DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <FormFillChat
          entityType="control"
          orgId={null}
          workspaceId={null}
          pageContext={{ control_id: control.id, control_name: control.name }}
          getFormValues={() => ({ name, description, control_category_code: categoryCode, criticality_code: criticalityCode, control_type: controlType, automation_potential: automationPotential })}
          onFilled={handleAIFilled}
        />
        <Separator className="my-2" />
        <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-1">
          <div className="space-y-1.5">
            <Label className="text-xs">Name</Label>
            <Input value={name} onChange={(e) => setName(e.target.value)} className="h-9 text-sm" />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Description</Label>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm min-h-[60px] resize-y" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs">Category</Label>
              <select className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={categoryCode} onChange={(e) => setCategoryCode(e.target.value)}>
                {categories.map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Criticality</Label>
              <select className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={criticalityCode} onChange={(e) => setCriticalityCode(e.target.value)}>
                {criticalities.map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs">Control Type</Label>
              <select className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={controlType} onChange={(e) => setControlType(e.target.value)}>
                {CONTROL_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Automation Potential</Label>
              <select className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={automationPotential} onChange={(e) => setAutomationPotential(e.target.value)}>
                {AUTOMATION_LEVELS.map((a) => <option key={a} value={a}>{a}</option>)}
              </select>
            </div>
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Guidance</Label>
            <textarea value={guidance} onChange={(e) => setGuidance(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm min-h-[50px] resize-y" />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Implementation Notes</Label>
            <textarea value={implNotes} onChange={(e) => setImplNotes(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm min-h-[50px] resize-y" />
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

// ── Delete Confirmation ──────────────────────────────────────────────────────

function DeleteControlDialog({
  control, onConfirm, onClose,
}: {
  control: ControlResponse | null
  onConfirm: (frameworkId: string, controlId: string) => Promise<void>
  onClose: () => void
}) {
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!control) return null

  async function confirm() {
    setDeleting(true); setError(null)
    try {
      await onConfirm(control!.framework_id, control!.id)
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
              <DialogTitle>Delete Control</DialogTitle>
              <DialogDescription>This will soft-delete the control and its test mappings.</DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />
        <p className="text-sm">
          Are you sure you want to delete <strong>{control.name}</strong> (<code className="text-xs font-mono">{control.control_code}</code>)?
        </p>
        {error && <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500 mt-2">{error}</p>}
        <DialogFooter className="mt-3 gap-2 sm:gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={deleting}>Cancel</Button>
          <Button variant="destructive" size="sm" onClick={confirm} disabled={deleting}>
            {deleting ? "Deleting..." : "Delete Control"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ── Framework Group Header ───────────────────────────────────────────────────

function FrameworkGroupHeader({
  framework,
  controls,
  latestExecutions,
  collapsed,
  onToggle,
}: {
  framework: FrameworkResponse
  controls: ControlResponse[]
  latestExecutions: Map<string, TestExecutionResponse>
  collapsed: boolean
  onToggle: () => void
}) {
  const passing = controls.filter((c) => execHealthStatus(latestExecutions.get(c.id)) === "Pass").length
  const failing = controls.filter((c) => execHealthStatus(latestExecutions.get(c.id)) === "Fail").length
  const partial = controls.filter((c) => execHealthStatus(latestExecutions.get(c.id)) === "Partial").length
  // controls with no execution yet
  const noRun = controls.filter((c) => !latestExecutions.has(c.id)).length
  const total = controls.length
  const pct = total > 0 ? Math.round((passing / total) * 100) : 0

  const passPct = total > 0 ? (passing / total) * 100 : 0
  const failPct = total > 0 ? (failing / total) * 100 : 0
  const partialPct = total > 0 ? (partial / total) * 100 : 0

  return (
    <button
      type="button"
      onClick={onToggle}
      className="w-full flex items-center gap-2 px-4 py-2 bg-blue-500/5 border-b border-border hover:bg-blue-500/8 transition-colors text-left"
    >
      {collapsed
        ? <ChevronRight className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
        : <ChevronDown className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
      }
      <span className="text-sm">🛡</span>
      <span className="text-[10px] font-bold tracking-widest uppercase text-blue-400">
        {framework.name || framework.framework_code}
      </span>
      <span className="text-[10px] text-muted-foreground">{total} controls</span>
      {/* Mini segmented progress bar — green=pass, red=fail, amber=partial, grey=not run */}
      <div className="flex gap-[2px] h-[4px] w-20 rounded-sm overflow-hidden ml-1 bg-muted">
        {passPct > 0 && <div style={{ width: `${passPct}%` }} className="bg-green-500" />}
        {failPct > 0 && <div style={{ width: `${failPct}%` }} className="bg-red-500" />}
        {partialPct > 0 && <div style={{ width: `${partialPct}%` }} className="bg-amber-500" />}
        {noRun > 0 && <div style={{ width: `${(noRun / total) * 100}%` }} className="bg-muted-foreground/30" />}
      </div>
      <span className={`text-[11px] font-semibold ml-1 ${pct >= 70 ? "text-green-400" : pct >= 40 ? "text-blue-400" : "text-amber-400"}`}>
        {pct}%
      </span>
      <span className="ml-auto text-[11px] text-muted-foreground">
        {framework.framework_code}
      </span>
    </button>
  )
}

// ── Control Table Row ────────────────────────────────────────────────────────

function ControlTableRow({
  ctrl,
  latestExec,
  setEditItem,
  setDeleteItem,
  colSpan,
  onNavigate,
  isExpanded,
  onToggleExpand,
  defaultOrgId,
  defaultWorkspaceId,
}: {
  ctrl: ControlResponse
  latestExec: TestExecutionResponse | undefined
  setEditItem: (c: ControlResponse) => void
  setDeleteItem: (c: ControlResponse) => void
  colSpan: number
  onNavigate: (ctrl: ControlResponse) => void
  isExpanded: boolean
  onToggleExpand: () => void
  defaultOrgId: string
  defaultWorkspaceId: string
}) {
  const health = execHealthStatus(latestExec)
  const borderColor = getBorderColor(ctrl, latestExec)

  // Evidence: use real evidence_summary from the execution, fall back to automation label
  const evidenceText = latestExec?.evidence_summary
    ? latestExec.evidence_summary
    : latestExec
      ? "No evidence attached"
      : ctrl.automation_potential === "full"
        ? "Auto collected"
        : ctrl.automation_potential === "partial"
          ? "Partial auto"
          : "Manual required"
  const evidenceClass = latestExec?.evidence_summary
    ? "text-muted-foreground"
    : !latestExec && ctrl.automation_potential === "manual"
      ? "text-red-400"
      : "text-muted-foreground"

  // Last run: from real executed_at
  const lastRun = latestExec?.executed_at ? formatExecTime(latestExec.executed_at) : "—"
  const lastRunClass = latestExec ? (health === "Fail" ? "text-red-400" : "text-muted-foreground") : "text-muted-foreground"

  return (
    <>
      <tr
        className={`border-b border-border cursor-pointer hover:bg-accent/30 transition-colors border-l-[3px] ${borderColor} ${isExpanded ? "bg-accent/20" : ""}`}
        onClick={onToggleExpand}
      >
        <td className="px-4 py-2.5">
          <div className="flex items-center gap-1.5">
            {isExpanded ? <ChevronDown className="w-3 h-3 text-muted-foreground shrink-0" /> : <ChevronRight className="w-3 h-3 text-muted-foreground shrink-0" />}
            <span className="font-mono text-xs text-blue-400 underline underline-offset-2">{ctrl.control_code}</span>
          </div>
        </td>
        <td className="px-4 py-2.5 max-w-[220px]">
          <div className="font-medium text-sm truncate">{ctrl.name || ctrl.control_code}</div>
          <div className="text-[10px] text-muted-foreground truncate">
            {[ctrl.category_name ?? ctrl.control_category_code, ...(ctrl.tags ?? [])].filter(Boolean).join(" · ")}
          </div>
        </td>
        <td className="px-4 py-2.5">
          <span className="text-[11px] text-muted-foreground">
            {ctrl.test_count ?? 0} test{(ctrl.test_count ?? 0) !== 1 ? "s" : ""}
          </span>
        </td>
        <td className="px-4 py-2.5">
          {health ? (
            <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-[10px] font-semibold ${getHealthBadge(health)}`}>
              {health}
            </span>
          ) : (
            <span className="text-[11px] text-muted-foreground">Not run</span>
          )}
        </td>
        <td className="px-4 py-2.5 max-w-[160px]">
          <span className={`text-[11px] truncate block ${evidenceClass}`}>{evidenceText}</span>
        </td>
        <td className="px-4 py-2.5">
          <span className={`text-[11px] ${lastRunClass}`}>{lastRun}</span>
        </td>
        <td className="px-4 py-2.5">
          {ctrl.criticality_code && ctrl.criticality_code !== "low" ? (
            <span className={`inline-flex items-center rounded-md border px-1.5 py-0.5 text-[9px] font-semibold ${getCriticalityBadge(ctrl.criticality_code)}`}>
              {ctrl.criticality_code}
            </span>
          ) : (
            <span className="text-[11px] text-muted-foreground">—</span>
          )}
        </td>
        <td className="px-4 py-2.5" onClick={(e) => e.stopPropagation()}>
          <div className="flex items-center gap-1">
            {health === "Fail" ? (
              <button
                type="button"
                onClick={() => onNavigate(ctrl)}
                className="rounded px-2 py-1 text-[10px] font-semibold bg-red-500/10 text-red-400 border border-red-500/30 hover:bg-red-500/20 transition-colors"
              >
                Fix →
              </button>
            ) : (
              <button
                type="button"
                onClick={() => onNavigate(ctrl)}
                className="rounded px-2 py-1 text-[10px] font-semibold text-muted-foreground border border-border hover:text-foreground hover:border-foreground/30 transition-colors"
              >
                View →
              </button>
            )}
            <button
              type="button"
              title="Edit"
              onClick={() => setEditItem(ctrl)}
              className="rounded p-1 text-muted-foreground hover:text-foreground hover:bg-accent transition-all"
            >
              <Pencil className="h-3 w-3" />
            </button>
            <button
              type="button"
              title="Delete"
              onClick={() => setDeleteItem(ctrl)}
              className="rounded p-1 text-muted-foreground hover:text-red-500 hover:bg-red-500/10 transition-all"
            >
              <Trash2 className="h-3 w-3" />
            </button>
          </div>
        </td>
      </tr>
      {isExpanded && (
        <tr>
          <td colSpan={colSpan} className="p-0">
            <ControlHierarchyPanel
              control={ctrl}
              frameworkId={ctrl.framework_id}
              defaultOrgId={defaultOrgId}
              defaultWorkspaceId={defaultWorkspaceId}
            />
          </td>
        </tr>
      )}
    </>
  )
}

// ── Health Overview Tab ──────────────────────────────────────────────────────

function HealthOverview({
  controls,
  frameworks,
  latestExecutions,
}: {
  controls: ControlResponse[]
  frameworks: FrameworkResponse[]
  latestExecutions: Map<string, TestExecutionResponse>
}) {
  const totalTests = controls.reduce((sum, c) => sum + (c.test_count ?? 0), 0)
  const fullAuto = controls.filter((c) => c.automation_potential === "full").length
  const partialAuto = controls.filter((c) => c.automation_potential === "partial").length
  const manual = controls.filter((c) => c.automation_potential === "manual").length

  const failingCount = controls.filter((c) => execHealthStatus(latestExecutions.get(c.id)) === "Fail").length
  const partialCount = controls.filter((c) => execHealthStatus(latestExecutions.get(c.id)) === "Partial").length

  return (
    <div className="space-y-4">
      {/* Health stat cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: "Total Tests", value: totalTests, sub: `${controls.length} controls`, iconCls: "text-primary", borderCls: "border-l-primary", numCls: "text-foreground" },
          { label: "Failing Controls", value: failingCount, sub: "Action needed", iconCls: "text-red-500", borderCls: "border-l-red-500", numCls: "text-red-600" },
          { label: "Partial / Evidence Gap", value: partialCount, sub: "Needs attention", iconCls: "text-amber-500", borderCls: "border-l-amber-500", numCls: "text-amber-600" },
          { label: "Fully Automated", value: fullAuto, sub: `${controls.length > 0 ? Math.round((fullAuto / controls.length) * 100) : 0}% of controls`, iconCls: "text-green-500", borderCls: "border-l-green-500", numCls: "text-green-600" },
        ].map(({ label, value, sub, borderCls, numCls }) => (
          <div key={label} className={`relative rounded-xl border bg-card border-l-[3px] ${borderCls} px-4 py-3`}>
            <div className={`text-2xl font-bold tabular-nums leading-none ${numCls}`}>{value}</div>
            <div className="text-[11px] text-muted-foreground mt-0.5">{label}</div>
            <div className="text-[10px] text-muted-foreground/70">{sub}</div>
            {label === "Failing Controls" && value > 0 && (
              <div className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-red-500 animate-pulse" />
            )}
          </div>
        ))}
      </div>

      {/* Test type breakdown + By framework */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Automation breakdown */}
        <Card className="rounded-xl">
          <CardContent className="pt-4 pb-4 px-4">
            <p className="text-sm font-semibold mb-3">Automation Breakdown</p>
            <div className="flex gap-3 mb-4">
              <div className="flex-1 bg-muted/50 border border-border rounded-lg p-3 text-center">
                <p className="text-[9px] uppercase tracking-widest text-muted-foreground mb-1">Fully Auto</p>
                <p className="text-2xl font-bold text-cyan-400">{fullAuto}</p>
                <p className="text-[10px] text-muted-foreground mt-1">{controls.length > 0 ? Math.round((fullAuto / controls.length) * 100) : 0}%</p>
              </div>
              <div className="flex-1 bg-muted/50 border border-border rounded-lg p-3 text-center">
                <p className="text-[9px] uppercase tracking-widest text-muted-foreground mb-1">Partial</p>
                <p className="text-2xl font-bold text-indigo-400">{partialAuto}</p>
                <p className="text-[10px] text-muted-foreground mt-1">{controls.length > 0 ? Math.round((partialAuto / controls.length) * 100) : 0}%</p>
              </div>
              <div className="flex-1 bg-muted/50 border border-border rounded-lg p-3 text-center">
                <p className="text-[9px] uppercase tracking-widest text-muted-foreground mb-1">Manual</p>
                <p className="text-2xl font-bold text-slate-400">{manual}</p>
                <p className="text-[10px] text-muted-foreground mt-1">{controls.length > 0 ? Math.round((manual / controls.length) * 100) : 0}%</p>
              </div>
            </div>
            <div className="space-y-2">
              <div>
                <div className="flex justify-between text-[11px] mb-1">
                  <span className="text-cyan-400">Fully Automated</span>
                  <span className="text-muted-foreground">{fullAuto} controls</span>
                </div>
                <div className="flex gap-[2px] h-[7px] rounded overflow-hidden bg-muted">
                  {controls.length > 0 && <div style={{ width: `${(fullAuto / controls.length) * 100}%` }} className="bg-green-500 rounded-l" />}
                </div>
              </div>
              <div>
                <div className="flex justify-between text-[11px] mb-1">
                  <span className="text-indigo-400">Partial Auto</span>
                  <span className="text-muted-foreground">{partialAuto} controls</span>
                </div>
                <div className="flex gap-[2px] h-[7px] rounded overflow-hidden bg-muted">
                  {controls.length > 0 && <div style={{ width: `${(partialAuto / controls.length) * 100}%` }} className="bg-blue-500 rounded-l" />}
                </div>
              </div>
              <div>
                <div className="flex justify-between text-[11px] mb-1">
                  <span className="text-slate-400">Manual</span>
                  <span className="text-muted-foreground">{manual} controls</span>
                </div>
                <div className="flex gap-[2px] h-[7px] rounded overflow-hidden bg-muted">
                  {controls.length > 0 && <div style={{ width: `${(manual / controls.length) * 100}%` }} className="bg-slate-500 rounded-l" />}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* By Framework */}
        <Card className="rounded-xl">
          <CardContent className="pt-4 pb-4 px-4">
            <p className="text-sm font-semibold mb-3">By Framework</p>
            <div className="space-y-3">
              {frameworks.map((fw) => {
                const fwControls = controls.filter((c) => c.framework_id === fw.id)
                const fwPassing = fwControls.filter((c) => execHealthStatus(latestExecutions.get(c.id)) === "Pass").length
                const fwPct = fwControls.length > 0 ? Math.round((fwPassing / fwControls.length) * 100) : 0
                return (
                  <div key={fw.id}>
                    <div className="flex justify-between text-[11px] mb-1">
                      <span className="text-muted-foreground">{fw.name || fw.framework_code}</span>
                      <span className={`font-semibold ${fwPct >= 70 ? "text-green-400" : fwPct >= 40 ? "text-blue-400" : "text-amber-400"}`}>{fwPct}%</span>
                    </div>
                    <div className="h-[6px] rounded overflow-hidden bg-muted">
                      <div
                        style={{ width: `${fwPct}%` }}
                        className={`h-full rounded ${fwPct >= 70 ? "bg-green-500" : fwPct >= 40 ? "bg-blue-500" : "bg-amber-500"}`}
                      />
                    </div>
                    <p className="text-[10px] text-muted-foreground mt-0.5">{fwControls.length} controls</p>
                  </div>
                )
              })}
              {frameworks.length === 0 && (
                <p className="text-xs text-muted-foreground">No frameworks loaded.</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function ControlsPage() {
  const router = useRouter()
  const { ready, selectedOrgId, selectedWorkspaceId } = useOrgWorkspace()
  const { canWrite } = useAccess()
  const canCreateControl = canWrite("control_management")

  const [controls, setControls] = useState<ControlResponse[]>([])
  const [frameworks, setFrameworks] = useState<FrameworkResponse[]>([])
  const [categories, setCategories] = useState<DimensionResponse[]>([])
  const [criticalities, setCriticalities] = useState<DimensionResponse[]>([])
  // Map<controlId, latest TestExecution> — fetched from real API
  const [latestExecutions, setLatestExecutions] = useState<Map<string, TestExecutionResponse>>(new Map())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filter / UI state
  const [search, setSearch] = useState("")
  const [quickFilter, setQuickFilter] = useState<"all" | "failing" | "partial" | "remediable" | "critical" | "high" | "medium" | "low">("all")
  const [filterFramework, setFilterFramework] = useState("")
  const [filterCriticality, setFilterCriticality] = useState("")
  const [filterControlType, setFilterControlType] = useState("")
  const [filterAutomation, setFilterAutomation] = useState("")
  const [activeTab, setActiveTab] = useState<"list" | "health">("list")
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set())
  const [expandedControlId, setExpandedControlId] = useState<string | null>(null)

  // View mode
  const [viewMode, setViewMode] = useState<"list" | "spreadsheet">("list")

  // Import result dialog
  const [importResult, setImportResult] = useState<ImportResult | null>(null)
  const [importResultOpen, setImportResultOpen] = useState(false)
  const [pendingImportFile, setPendingImportFile] = useState<{ file: File; frameworkId: string } | null>(null)

  // CRUD dialogs
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [editItem, setEditItem] = useState<ControlResponse | null>(null)
  const [deleteItem, setDeleteItem] = useState<ControlResponse | null>(null)

  const load = useCallback(async () => {
    if (!selectedOrgId) return
    setLoading(true); setError(null)
    try {
      const [catRes, critRes] = await Promise.all([listControlCategories(), listControlCriticalities()])
      setCategories(Array.isArray(catRes) ? catRes : [])
      setCriticalities(Array.isArray(critRes) ? critRes : [])

      const fwRes = await listFrameworks({ scope_org_id: selectedOrgId, scope_workspace_id: selectedWorkspaceId || undefined })
      const fws = fwRes.items ?? []
      setFrameworks(fws)
      const ctrlRes = await listAllControls({ scope_org_id: selectedOrgId, scope_workspace_id: selectedWorkspaceId || undefined, limit: 500 })
      setControls(ctrlRes.items ?? [])

      // Fetch latest test execution per control from the real API.
      // We request a large limit to get all recent executions in one call,
      // then keep only the most recent per control_id.
      try {
        const execRes = await listTestExecutions({ limit: 200 })
        const execMap = new Map<string, TestExecutionResponse>()
        // Sort oldest-first so later (newer) items overwrite earlier ones
        const sorted = [...(execRes.items ?? [])].sort(
          (a, b) => new Date(a.executed_at).getTime() - new Date(b.executed_at).getTime()
        )
        for (const exec of sorted) {
          if (exec.control_id) execMap.set(exec.control_id, exec)
        }
        setLatestExecutions(execMap)
      } catch {
        // Non-fatal: executions may not be available; table degrades gracefully
        setLatestExecutions(new Map())
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load controls")
    } finally { setLoading(false) }
  }, [selectedOrgId, selectedWorkspaceId])

  useEffect(() => { if (ready && selectedOrgId) load() }, [load, ready, selectedOrgId])

  const filtered = useMemo(() => {
    return controls.filter((c) => {
      if (search && !c.name?.toLowerCase().includes(search.toLowerCase()) && !c.control_code.toLowerCase().includes(search.toLowerCase())) return false
      if (filterFramework && c.framework_id !== filterFramework) return false
      if (filterCriticality && c.criticality_code !== filterCriticality) return false
      if (filterControlType && c.control_type !== filterControlType) return false
      if (filterAutomation && c.automation_potential !== filterAutomation) return false
      // quickFilter by execution health status
      if (quickFilter === "failing") {
        if (execHealthStatus(latestExecutions.get(c.id)) !== "Fail") return false
      } else if (quickFilter === "partial") {
        const h = execHealthStatus(latestExecutions.get(c.id))
        if (h !== "Partial" && h !== null) return false
      } else if (quickFilter === "remediable") {
        if (c.automation_potential !== "partial") return false
      } else if (quickFilter !== "all") {
        if (c.criticality_code !== quickFilter) return false
      }
      return true
    })
  }, [controls, search, quickFilter, filterFramework, filterCriticality, filterControlType, filterAutomation, latestExecutions])

  // Stats derived from real test execution results
  const totalCount = controls.length
  const passingCount = controls.filter((c) => execHealthStatus(latestExecutions.get(c.id)) === "Pass").length
  const failingCount = controls.filter((c) => execHealthStatus(latestExecutions.get(c.id)) === "Fail").length
  const partialOrNoRunCount = controls.filter((c) => {
    const h = execHealthStatus(latestExecutions.get(c.id))
    return h === "Partial" || h === null
  }).length

  async function handleCreate(frameworkId: string, payload: CreateControlRequest) {
    await createControl(frameworkId, payload)
    await load()
  }

  async function handleUpdate(frameworkId: string, controlId: string, payload: UpdateControlRequest) {
    await updateControl(frameworkId, controlId, payload)
    await load()
  }

  async function handleDelete(frameworkId: string, controlId: string) {
    await deleteControl(frameworkId, controlId)
    await load()
  }

  function handleNavigateToControl(ctrl: ControlResponse) {
    router.push(`/controls/${ctrl.framework_id}/${ctrl.id}`)
  }

  // ── Spreadsheet helpers ──────────────────────────────────────────────────

  // Convert filtered ControlResponse[] to spreadsheet rows (respects active search + filters)
  const spreadsheetRows = useMemo<ControlSpreadsheetRow[]>(() => 
    filtered.map((c) => ({
      id: c.id,
      control_code: c.control_code,
      name: c.name ?? "",
      description: c.description ?? "",
      control_type: c.control_type ?? "",
      criticality: c.criticality_code ?? "",
      automation_type: c.automation_potential ?? "",
      owner_name: c.owner_display_name ?? c.owner_email ?? "",
      owner_user_id: c.owner_user_id ?? "",
      requirement_code: c.requirement_code ?? "",
      requirement_id: c.requirement_id ?? "",
      tags: Array.isArray(c.tags) ? c.tags.join(", ") : (c.tags ?? ""),
      framework_code: c.framework_code ?? frameworks.find((f) => f.id === c.framework_id)?.framework_code ?? "",
      tasks_count: String(c.test_count ?? ""),
      risks_count: "",
    })),
    [filtered, frameworks]
  )

  // Spreadsheet selection tracking
  const [selectedControlIds, setSelectedControlIds] = useState<string[]>([])

  const handleSelectionChange = useCallback((indices: number[]) => {
    const ids = indices.map(idx => spreadsheetRows[idx]?.id).filter(Boolean) as string[]
    setSelectedControlIds(prev => {
      if (prev.length === ids.length && prev.every((val, i) => val === ids[i])) return prev
      return ids
    })
  }, [spreadsheetRows])

  const handleBuildTasks = () => {
    if (selectedControlIds.length === 0) return
    // Navigate to task builder with selected control IDs
    // Assuming the task builder is at /frameworks/[frameworkId]/task-builder
    // We pick the framework of the first selected control
    const firstId = selectedControlIds[0]
    const ctrl = controls.find(c => c.id === firstId)
    if (ctrl?.framework_id) {
      const q = new URLSearchParams()
      selectedControlIds.forEach(id => q.append("control_id", id))
      router.push(`/frameworks/${ctrl.framework_id}/task-builder?${q.toString()}`)
    }
  }

  // Group filtered controls by framework, then by requirement
  const groupedByFramework = useMemo(() => {
    const map = new Map<string, { framework: FrameworkResponse; byReq: Map<string, { reqCode: string; reqName: string; controls: ControlResponse[] }> }>()
    for (const ctrl of filtered) {
      const fwId = ctrl.framework_id ?? "__unknown__"
      if (!map.has(fwId)) {
        const fw = frameworks.find((f) => f.id === fwId) ?? {
          id: fwId, framework_code: fwId, name: ctrl.framework_name ?? fwId,
        } as FrameworkResponse
        map.set(fwId, { framework: fw, byReq: new Map() })
      }
      const reqKey = ctrl.requirement_id ?? "__no_req__"
      const byReq = map.get(fwId)!.byReq
      if (!byReq.has(reqKey)) {
        byReq.set(reqKey, {
          reqCode: ctrl.requirement_code ?? "",
          reqName: ctrl.requirement_name ?? ctrl.requirement_code ?? "No Requirement",
          controls: [],
        })
      }
      byReq.get(reqKey)!.controls.push(ctrl)
    }
    return [...map.values()].map(({ framework, byReq }) => ({
      framework,
      requirements: [...byReq.values()],
    }))
  }, [filtered, frameworks])

  // The first framework ID is used as a fallback for import/export when there is
  // only one framework, or the user hasn't picked one.
  const defaultFrameworkId = frameworks[0]?.id ?? ""

  async function handleSpreadsheetSave(row: ControlSpreadsheetRow, _index: number) {
    const existing = controls.find((c) => c.id === row.id)
    if (!existing) return
    await updateControl(existing.framework_id, existing.id, {
      name: row.name,
      description: row.description || undefined,
      control_type: (row.control_type as "preventive" | "detective" | "corrective" | "compensating") || undefined,
      criticality_code: (row.criticality as string) || undefined,
      automation_potential: (row.automation_type as "full" | "partial" | "manual") || undefined,
      tags: row.tags ? row.tags.split(",").map((t) => t.trim()).filter(Boolean) : undefined,
    })
    await load()
  }

  async function handleSpreadsheetExport(format: "csv" | "json" | "xlsx") {
    const fwId = defaultFrameworkId
    if (!fwId) return
    const blob = await exportControls(fwId, format)
    const ext = format === "xlsx" ? "xlsx" : format === "json" ? "json" : "csv"
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `controls_export_${new Date().toISOString().split("T")[0]}.${ext}`
    a.click()
    URL.revokeObjectURL(url)
  }

  async function handleSpreadsheetImport(file: File, dryRun: boolean) {
    const fwId = defaultFrameworkId
    if (!fwId) return
    const result = await importControls(fwId, file, dryRun)
    const importResult: ImportResult = {
      created: result.created,
      updated: result.updated,
      skipped: result.skipped,
      warnings: result.warnings,
      errors: result.errors,
      dry_run: dryRun,
    }
    setImportResult(importResult)
    setImportResultOpen(true)
    if (dryRun) {
      setPendingImportFile({ file, frameworkId: fwId })
    } else {
      await load()
    }
  }

  async function handleImportCommit() {
    if (!pendingImportFile) return
    const result = await importControls(pendingImportFile.frameworkId, pendingImportFile.file, false)
    const commitResult: ImportResult = {
      created: result.created,
      updated: result.updated,
      skipped: result.skipped,
      warnings: result.warnings,
      errors: result.errors,
      dry_run: false,
    }
    setImportResult(commitResult)
    setPendingImportFile(null)
    await load()
  }

  async function handleDownloadTemplate(format: "csv" | "xlsx") {
    const blob = await getControlsImportTemplate(format)
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `controls_template.${format}`
    a.click()
    URL.revokeObjectURL(url)
  }

  // ─────────────────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 rounded-md bg-muted animate-pulse" />
        <div className="grid grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => <div key={i} className="h-20 rounded-xl bg-muted animate-pulse" />)}
        </div>
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => <div key={i} className="h-12 rounded-xl bg-muted animate-pulse" />)}
        </div>
      </div>
    )
  }

  const TABLE_COLS = 8

  return (
    <div className="space-y-5">
      {/* Page header */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold tracking-tight font-secondary">Controls</h1>
          <p className="text-sm text-muted-foreground mt-0.5">Control library across all frameworks</p>
        </div>
        <div className="flex items-center gap-2 ml-auto">
          <ReadOnlyBanner />
          {canCreateControl && (
            <Button size="sm" className="h-8 gap-1.5 text-xs" onClick={() => setShowCreateDialog(true)}>
              <Plus className="h-3.5 w-3.5" /> New Control
            </Button>
          )}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-500 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          {error}
          <Button variant="ghost" size="sm" className="ml-auto h-6 text-xs" onClick={load}>Retry</Button>
        </div>
      )}

      {/* 4 stat cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: "Total Controls", value: totalCount, icon: Layers, iconCls: "text-primary", borderCls: "border-l-primary", numCls: "text-foreground", sub: `${frameworks.length} framework${frameworks.length !== 1 ? "s" : ""}`, onClick: undefined },
          { label: "Passing", value: passingCount, icon: CheckCircle2, iconCls: "text-green-500", borderCls: "border-l-green-500", numCls: "text-green-600", sub: "All tests green", onClick: () => setQuickFilter(quickFilter === "all" ? "all" : "all") },
          { label: "Failing", value: failingCount, icon: AlertTriangle, iconCls: "text-red-500", borderCls: "border-l-red-500", numCls: "text-red-600", sub: failingCount > 0 ? "Action needed" : "None", onClick: () => setQuickFilter(quickFilter === "failing" ? "all" : "failing") },
          { label: "Needs Evidence", value: partialOrNoRunCount, icon: ClipboardList, iconCls: "text-amber-500", borderCls: "border-l-amber-500", numCls: "text-amber-600", sub: "Evidence gap / not run", onClick: () => setQuickFilter(quickFilter === "partial" ? "all" : "partial") },
        ].map(({ label, value, icon: Icon, iconCls, borderCls, numCls, sub, onClick }) => (
          <div
            key={label}
            className={`relative rounded-xl border bg-card border-l-[3px] ${borderCls} px-4 py-3 flex items-center gap-3 ${onClick ? "cursor-pointer hover:bg-muted/30 transition-colors" : ""}`}
            onClick={onClick}
          >
            <div className="shrink-0 rounded-lg p-2 bg-muted">
              <Icon className={`w-4 h-4 ${iconCls}`} />
            </div>
            <div className="min-w-0">
              <div className={`text-2xl font-bold tabular-nums leading-none ${numCls}`}>{value}</div>
              <div className="text-[11px] text-muted-foreground mt-0.5 truncate">{label}</div>
              <div className="text-[10px] text-muted-foreground/70 truncate">{sub}</div>
            </div>
            {label === "Failing" && value > 0 && (
              <div className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-red-500 animate-pulse" />
            )}
          </div>
        ))}
      </div>

      {/* Tabs + view toggle */}
      <div className="flex items-center justify-between border-b border-border">
        <div className="flex items-center gap-0">
          {([["list", "Controls List"], ["health", "Health Overview"]] as const).map(([id, label]) => (
            <button
              key={id}
              type="button"
              onClick={() => { setActiveTab(id); setViewMode("list") }}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px ${activeTab === id
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
            >
              {label}
            </button>
          ))}
        </div>
        {activeTab === "list" && (
          <div className="flex items-center gap-1 pr-1 pb-px">
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
      </div>

      {activeTab === "health" && (
        <HealthOverview controls={controls} frameworks={frameworks} latestExecutions={latestExecutions} />
      )}

      {activeTab === "list" && viewMode === "spreadsheet" && (
        <div className="space-y-3">
          <div className="flex items-center justify-between gap-4 px-1">
            <div className="flex items-center gap-2">
              {selectedControlIds.length > 0 && (
                <Button
                  size="sm"
                  className="bg-violet-600 hover:bg-violet-700 text-white gap-2 shadow-lg animate-in fade-in slide-in-from-left-2"
                  onClick={handleBuildTasks}
                >
                  <Sparkles className="h-4 w-4" />
                  Build Tasks for {selectedControlIds.length} Control{selectedControlIds.length !== 1 ? "s" : ""}
                </Button>
              )}
            </div>
            <div className="text-xs text-muted-foreground tabular-nums">
              {selectedControlIds.length > 0 ? `${selectedControlIds.length} selected` : `${controls.length} total controls`}
            </div>
          </div>
          <EntitySpreadsheet
            columns={controlsColumns}
            rows={spreadsheetRows}
            onSave={handleSpreadsheetSave}
            onDelete={async (row) => {
              const ctrl = controls.find(c => c.id === row.id)
              if (ctrl) setDeleteItem(ctrl)
            }}
            onSelectionChange={handleSelectionChange}
            loading={loading}
            keyField="id"
            totalCount={controls.length}
            hideAddButton={true}
          />
        </div>
      )}

      {activeTab === "list" && viewMode === "list" && (
        <div className="space-y-3">
          {/* Alert banners */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div
              className={`p-3 rounded-lg border transition-colors cursor-pointer ${quickFilter === "failing" ? "border-red-500 bg-red-500/10" : "border-red-500/20 bg-red-500/5 hover:bg-red-500/8"}`}
              onClick={() => setQuickFilter(quickFilter === "failing" ? "all" : "failing")}
            >
              <div className="flex items-center gap-1.5 mb-1">
                <Zap className="h-3 w-3 text-red-400" />
                <span className="text-[10px] font-bold tracking-widest uppercase text-red-400">Action needed</span>
              </div>
              <p className="text-xs text-muted-foreground whitespace-nowrap overflow-hidden text-ellipsis">
                {failingCount} failing control{failingCount !== 1 ? "s" : ""} have open issues
                {failingCount > 0 && <span className="text-red-400"> · {Math.max(1, Math.ceil(failingCount * 0.4))} SLA at risk</span>}
              </p>
            </div>
            <div
              className={`p-3 rounded-lg border transition-colors cursor-pointer ${quickFilter === "partial" ? "border-amber-500 bg-amber-500/10" : "border-amber-500/15 bg-amber-500/5 hover:bg-amber-500/8"}`}
              onClick={() => setQuickFilter(quickFilter === "partial" ? "all" : "partial")}
            >
              <div className="flex items-center gap-1.5 mb-1">
                <ClipboardList className="h-3 w-3 text-amber-400" />
                <span className="text-[10px] font-bold tracking-widest uppercase text-amber-400">Evidence overdue</span>
              </div>
              <p className="text-xs text-muted-foreground whitespace-nowrap overflow-hidden text-ellipsis">
                {controls.filter((c) => {
                  const exec = latestExecutions.get(c.id)
                  return exec && !exec.evidence_summary
                }).length} tests missing evidence
              </p>
            </div>
            <div
              className={`p-3 rounded-lg border transition-colors cursor-pointer ${quickFilter === "remediable" ? "border-indigo-500 bg-indigo-500/10" : "border-indigo-500/20 bg-indigo-500/5 hover:bg-indigo-500/8"}`}
              onClick={() => setQuickFilter(quickFilter === "remediable" ? "all" : "remediable")}
            >
              <div className="flex items-center gap-1.5 mb-1">
                <Sparkles className="h-3 w-3 text-indigo-400" />
                <span className="text-[10px] font-bold tracking-widest uppercase text-indigo-400">Kue suggestion</span>
              </div>
              <p className="text-xs text-muted-foreground whitespace-nowrap overflow-hidden text-ellipsis">
                {controls.filter((c) => c.automation_potential === "partial").length} controls can be auto-remediated · click to view
              </p>
            </div>
          </div>

          <Card className="rounded-xl overflow-hidden">
            {/* Card header */}
            <div className="flex items-center gap-3 px-4 py-3 border-b border-border">
              <span className="text-sm font-semibold">Controls</span>
            </div>

            {/* Filter row */}
            <div className="flex flex-col gap-2.5 px-4 py-3 border-b border-border">
              {/* Row 1: search + framework */}
              <div className="flex flex-col sm:flex-row sm:items-center gap-2">
                <div className="relative w-full sm:w-64">
                  <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground" />
                  <Input
                    placeholder="Search controls by name, ID…"
                    className="pl-7 h-8 sm:h-7 text-xs w-full"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                  />
                </div>
                <div className="w-full sm:w-auto min-w-[140px] max-w-full sm:max-w-[280px] flex items-center gap-2 flex-shrink-0">
                  <Select
                    value={filterFramework || "all"}
                    onValueChange={(val) => setFilterFramework(val === "all" ? "" : val)}
                  >
                    <SelectTrigger className="h-8 sm:h-7 text-[11px] font-medium w-full overflow-hidden">
                      <SelectValue placeholder="All Frameworks" />
                    </SelectTrigger>
                    <SelectContent className="max-w-[90vw] sm:max-w-md">
                      <SelectItem value="all" className="text-[11px]">All Frameworks</SelectItem>
                      {frameworks.map((fw) => (
                        <SelectItem key={fw.id} value={fw.id} className="text-[11px]">
                          {fw.name || fw.framework_code}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                {(search || quickFilter !== "all" || filterFramework || filterCriticality || filterControlType || filterAutomation) && (
                  <button
                    type="button"
                    onClick={() => { setSearch(""); setQuickFilter("all"); setFilterFramework(""); setFilterCriticality(""); setFilterControlType(""); setFilterAutomation("") }}
                    className="flex items-center gap-1 px-2 py-1 text-[11px] text-muted-foreground hover:text-foreground transition-colors border border-border rounded-md flex-shrink-0"
                    title="Clear all filters"
                  >
                    <X className="h-3 w-3" /> Clear all
                  </button>
                )}
              </div>

              {/* Row 2: filter pill groups */}
              <div className="flex items-center gap-2 flex-wrap text-xs">
                <div className="flex items-center gap-1 text-muted-foreground">
                  <Filter className="w-3 h-3" />
                  <span className="text-[11px]">Filter:</span>
                  <FilterGlossaryPopover />
                </div>

                {/* Criticality */}
                <div className="flex items-center rounded border border-border/60 overflow-hidden bg-muted/20">
                  {["", "critical", "high", "medium", "low"].map(v => (
                    <button
                      key={v || "crit-all"}
                      type="button"
                      onClick={() => setFilterCriticality(v)}
                      className={`px-2 py-1 text-[11px] transition-colors whitespace-nowrap ${
                        filterCriticality === v
                          ? "bg-background text-foreground font-semibold shadow-sm"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      {v === "" ? "All" : v.charAt(0).toUpperCase() + v.slice(1)}
                    </button>
                  ))}
                </div>

                {/* Control Type */}
                <div className="flex items-center rounded border border-border/60 overflow-hidden bg-muted/20">
                  {["", "preventive", "detective", "corrective", "compensating"].map(v => (
                    <button
                      key={v || "type-all"}
                      type="button"
                      onClick={() => setFilterControlType(v)}
                      className={`px-2 py-1 text-[11px] transition-colors whitespace-nowrap ${
                        filterControlType === v
                          ? "bg-background text-foreground font-semibold shadow-sm"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      {v === "" ? "All" : v.charAt(0).toUpperCase() + v.slice(1)}
                    </button>
                  ))}
                </div>

                {/* Automation */}
                <div className="flex items-center rounded border border-border/60 overflow-hidden bg-muted/20">
                  {["", "full", "partial", "manual"].map(v => (
                    <button
                      key={v || "auto-all"}
                      type="button"
                      onClick={() => setFilterAutomation(v)}
                      className={`px-2 py-1 text-[11px] transition-colors whitespace-nowrap ${
                        filterAutomation === v
                          ? "bg-background text-foreground font-semibold shadow-sm"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      {v === "" ? "All" : v.charAt(0).toUpperCase() + v.slice(1)}
                    </button>
                  ))}
                </div>

                {/* Quick health chips */}
                <div className="flex items-center gap-1.5 ml-1">
                  {(["all", "failing", "partial", "remediable"] as const).map((f) => (
                    <button
                      key={f}
                      type="button"
                      onClick={() => setQuickFilter(f)}
                      className={`whitespace-nowrap rounded-full px-2.5 py-0.5 text-[11px] font-medium border transition-colors ${
                        quickFilter === f
                          ? "bg-primary text-primary-foreground border-primary"
                          : "border-border text-muted-foreground hover:text-foreground hover:border-foreground/30"
                      }`}
                    >
                      {f === "all" ? "All" : f === "failing" ? "Failing" : f === "partial" ? "Needs evidence" : "Remediable"}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Controls grouped by framework → requirement */}
            {filtered.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-muted">
                  <Layers className="h-6 w-6 text-muted-foreground" />
                </div>
                <p className="text-sm font-medium">No controls found</p>
                <p className="text-xs text-muted-foreground">
                  {controls.length === 0 ? "Create your first control within a framework." : "Try adjusting your filters."}
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                {groupedByFramework.map(({ framework, requirements }) => {
                  const allFwControls = requirements.flatMap((r) => r.controls)
                  const isCollapsed = collapsedGroups.has(framework.id)
                  return (
                    <div key={framework.id}>
                      <FrameworkGroupHeader
                        framework={framework}
                        controls={allFwControls}
                        latestExecutions={latestExecutions}
                        collapsed={isCollapsed}
                        onToggle={() => {
                          const next = new Set(collapsedGroups)
                          isCollapsed ? next.delete(framework.id) : next.add(framework.id)
                          setCollapsedGroups(next)
                        }}
                      />
                      {!isCollapsed && (
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b border-border">
                              <th className="px-4 py-2 text-left text-[10px] uppercase tracking-wider text-muted-foreground font-medium">Control ID</th>
                              <th className="px-4 py-2 text-left text-[10px] uppercase tracking-wider text-muted-foreground font-medium">Name</th>
                              <th className="px-4 py-2 text-left text-[10px] uppercase tracking-wider text-muted-foreground font-medium">Tests</th>
                              <th className="px-4 py-2 text-left text-[10px] uppercase tracking-wider text-muted-foreground font-medium">Health</th>
                              <th className="px-4 py-2 text-left text-[10px] uppercase tracking-wider text-muted-foreground font-medium">Evidence</th>
                              <th className="px-4 py-2 text-left text-[10px] uppercase tracking-wider text-muted-foreground font-medium">Last Run</th>
                              <th className="px-4 py-2 text-left text-[10px] uppercase tracking-wider text-muted-foreground font-medium">Issues</th>
                              <th className="px-4 py-2" />
                            </tr>
                          </thead>
                          <tbody>
                            {requirements.map(({ reqCode, reqName, controls: reqControls }) => (
                              <React.Fragment key={`req-${reqCode}`}>
                                {/* Requirement sub-header */}
                                <tr className="border-b border-border/60 bg-muted/20">
                                  <td colSpan={TABLE_COLS} className="px-4 py-1.5">
                                    <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                                      {reqCode ? `${reqCode} — ` : ""}{reqName}
                                    </span>
                                    <span className="ml-2 text-[10px] text-muted-foreground/60">{reqControls.length} control{reqControls.length !== 1 ? "s" : ""}</span>
                                  </td>
                                </tr>
                                {reqControls.map((ctrl) => (
                                  <ControlTableRow
                                    key={ctrl.id}
                                    ctrl={ctrl}
                                    latestExec={latestExecutions.get(ctrl.id)}
                                    setEditItem={setEditItem}
                                    setDeleteItem={setDeleteItem}
                                    colSpan={TABLE_COLS}
                                    onNavigate={handleNavigateToControl}
                                    isExpanded={expandedControlId === ctrl.id}
                                    onToggleExpand={() => setExpandedControlId(expandedControlId === ctrl.id ? null : ctrl.id)}
                                    defaultOrgId={selectedOrgId || ""}
                                    defaultWorkspaceId={selectedWorkspaceId || ""}
                                  />
                                ))}
                              </React.Fragment>
                            ))}
                          </tbody>
                        </table>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </Card>
        </div>
      )}

      {/* Dialogs */}
      <CreateControlDialog open={showCreateDialog} frameworks={frameworks} categories={categories} criticalities={criticalities} onCreate={handleCreate} onClose={() => setShowCreateDialog(false)} />
      <EditControlDialog control={editItem} categories={categories} criticalities={criticalities} onSave={handleUpdate} onClose={() => setEditItem(null)} />
      <DeleteControlDialog control={deleteItem} onConfirm={handleDelete} onClose={() => setDeleteItem(null)} />
      <ImportResultDialog
        open={importResultOpen}
        onClose={() => { setImportResultOpen(false); setImportResult(null) }}
        result={importResult}
        title="Controls Import Results"
        onCommit={pendingImportFile ? handleImportCommit : undefined}
      />
    </div>
  )
}
