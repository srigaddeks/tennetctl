"use client"

import { useEffect, useState, useCallback } from "react"
import { useParams, useRouter } from "next/navigation"
import {
  Card, CardContent, Button, Input, Badge, Separator,
} from "@kcontrol/ui"
import {
  ChevronRight, ChevronDown,
  Shield, AlertTriangle, CheckCircle2, Clock,
  Upload, Plus, ExternalLink, FileText,
  MessageSquare, Paperclip, ListTodo, History,
  Layers, Users, Tag, User, Info,
  ClipboardCheck, Zap, GitMerge, Target,
  Circle, Pencil, Save, Loader2, BarChart3,
  ShieldAlert, X, Sparkles,
} from "lucide-react"
import { CommentsSection } from "@/components/comments/CommentsSection"
import { AttachmentsSection } from "@/components/attachments/AttachmentsSection"
import { TaskCreateSlideOver } from "@/components/tasks/TaskCreateSlideOver"
import {
  getControl, listControlTests, listTestExecutions, listTasks, updateControl,
  listControlRisks, assignRiskToControl, unassignRiskFromControl, listRisks,
  listPromotedTests,
} from "@/lib/api/grc"
import type {
  ControlResponse, TestResponse, TestExecutionResponse, TaskResponse,
  UpdateControlRequest, RiskControlMappingResponse, RiskResponse,
} from "@/lib/types/grc"
import { useAccess } from "@/components/providers/AccessProvider"
import { useOrgWorkspace } from "@/lib/context/OrgWorkspaceContext"
import { useCopilotEntityNames } from "@/lib/context/CopilotContext"
import { AIEnhancePopover } from "@/components/ai/AIEnhancePopover"
import { LinkTestsDialog } from "@/components/grc/LinkTestsDialog"
import {
  suggestTestsForControl,
  applyTestLinkerSuggestionsForControl,
  type TestSuggestion,
} from "@/lib/api/testLinker"

// ── Auth helper ───────────────────────────────────────────────────────────────

function getJwtSubject(): string | null {
  try {
    const token = localStorage.getItem("access_token")
    if (!token) return null
    const payload = JSON.parse(atob(token.split(".")[1]))
    return payload.sub || null
  } catch { return null }
}

// ── Style maps ────────────────────────────────────────────────────────────────

const CRITICALITY_COLORS: Record<string, string> = {
  critical: "bg-red-500/10 text-red-500 border-red-500/30",
  high:     "bg-orange-500/10 text-orange-500 border-orange-500/30",
  medium:   "bg-yellow-500/10 text-yellow-600 border-yellow-500/30",
  low:      "bg-green-500/10 text-green-500 border-green-500/30",
}

const CONTROL_TYPE_COLORS: Record<string, string> = {
  preventive:   "bg-blue-500/10 text-blue-500",
  detective:    "bg-purple-500/10 text-purple-500",
  corrective:   "bg-amber-500/10 text-amber-600",
  compensating: "bg-teal-500/10 text-teal-500",
}

const AUTOMATION_COLORS: Record<string, string> = {
  full:    "bg-green-500/10 text-green-600 border-green-500/30",
  partial: "bg-blue-500/10 text-blue-600 border-blue-500/30",
  manual:  "bg-gray-500/10 text-gray-500 border-gray-500/30",
}

const PRIORITY_COLORS: Record<string, string> = {
  critical: "bg-red-500/10 text-red-500 border-red-500/30",
  high:     "bg-orange-500/10 text-orange-500 border-orange-500/30",
  medium:   "bg-yellow-500/10 text-yellow-600 border-yellow-500/30",
  low:      "bg-green-500/10 text-green-500 border-green-500/30",
}

const MONITORING_FREQ_COLORS: Record<string, string> = {
  realtime: "bg-green-500/10 text-green-600 border-green-500/30",
  hourly:   "bg-cyan-500/10 text-cyan-600 border-cyan-500/30",
  daily:    "bg-blue-500/10 text-blue-600 border-blue-500/30",
  weekly:   "bg-purple-500/10 text-purple-600 border-purple-500/30",
  monthly:  "bg-gray-500/10 text-gray-500 border-gray-500/30",
  manual:   "bg-gray-500/10 text-gray-500 border-gray-500/30",
}

const TEST_TYPE_STYLES: Record<string, string> = {
  automated: "bg-green-500/10 text-green-600 border-green-500/30",
  manual:    "bg-blue-500/10 text-blue-600 border-blue-500/30",
  hybrid:    "bg-purple-500/10 text-purple-600 border-purple-500/30",
}

const TASK_STATUS_STYLES: Record<string, string> = {
  open:        "text-muted-foreground",
  in_progress: "text-blue-500",
  completed:   "text-green-500",
  blocked:     "text-red-500",
}

// ── Small helpers ─────────────────────────────────────────────────────────────

function Chip({ label, className }: { label: string; className?: string }) {
  return (
    <span className={`inline-flex items-center px-1.5 py-0 rounded text-[10px] font-semibold uppercase tracking-wide border ${className}`}>
      {label}
    </span>
  )
}

function FrequencyBadge({ frequency }: { frequency: string }) {
  const colorClass = MONITORING_FREQ_COLORS[frequency?.toLowerCase()] ?? "bg-gray-500/10 text-gray-500 border-gray-500/30"
  return (
    <span className={`inline-flex items-center px-1.5 py-0 rounded text-[10px] font-semibold border ${colorClass}`}>
      {frequency}
    </span>
  )
}

function TaskStatusIcon({ status }: { status: string }) {
  if (status === "completed") return <CheckCircle2 className="w-3 h-3 text-green-500" />
  if (status === "in_progress") return <Clock className="w-3 h-3 text-blue-500" />
  if (status === "blocked") return <AlertTriangle className="w-3 h-3 text-red-500" />
  return <Circle className="w-3 h-3 text-muted-foreground" />
}

function execHealth(exec: TestExecutionResponse | undefined): "pass" | "fail" | "partial" | null {
  if (!exec) return null
  const s = exec.result_status?.toLowerCase()
  if (s === "pass" || s === "passed") return "pass"
  if (s === "fail" || s === "failed") return "fail"
  if (s === "partial") return "partial"
  return null
}

function formatTime(iso: string): string {
  const d = new Date(iso)
  const now = new Date()
  const diffDays = Math.floor((now.getTime() - d.getTime()) / 86400000)
  if (diffDays === 0) return `Today ${d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`
  if (diffDays === 1) return "Yesterday"
  if (diffDays < 7) return `${diffDays}d ago`
  return d.toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" })
}

function HealthBadge({ status }: { status: "pass" | "fail" | "partial" | null }) {
  if (!status) return <span className="text-[11px] text-muted-foreground">Not run</span>
  const cfg = {
    pass:    "bg-green-500/10 text-green-400 border-green-500/30",
    fail:    "bg-red-500/10 text-red-400 border-red-500/30",
    partial: "bg-amber-500/10 text-amber-400 border-amber-500/30",
  }[status]
  return (
    <span className={`inline-flex items-center rounded border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${cfg}`}>
      {status}
    </span>
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
          <div className="space-y-1.5 max-h-60 overflow-y-auto pr-1">
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

// ── Tests Panel ─────────────────────────────────────────────────────────────

function ControlTestsPanel({
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
  const [execMap, setExecMap] = useState<Map<string, TestExecutionResponse>>(new Map())
  const [loading, setLoading] = useState(true)
  const [expandedTests, setExpandedTests] = useState<Set<string>>(new Set())
  const [linkTestOpen, setLinkTestOpen] = useState(false)
  const [aiSuggestOpen, setAiSuggestOpen] = useState(false)
  const { selectedOrgId } = useOrgWorkspace()
  const [promotedMap, setPromotedMap] = useState<Map<string, string>>(new Map())

  const loadData = useCallback(() => {
    setLoading(true)

    // Fetch promoted tests to resolve standard IDs to promoted IDs for navigation
    if (selectedOrgId) {
      listPromotedTests({ orgId: selectedOrgId, limit: 500 }).then(res => {
        const map = new Map<string, string>()
        res.items.forEach(p => {
          if (p.control_test_id) map.set(p.control_test_id, p.id)
        })
        setPromotedMap(map)
      }).catch(() => {})
    }

    listControlTests(frameworkId, control.id).then(async (r) => {
      const testList = r.items ?? []
      setTests(testList)
      if (testList.length > 0) {
        try {
          const execRes = await listTestExecutions({ control_id: control.id, limit: 200 })
          const allExecs = execRes.items ?? []
          const map = new Map<string, TestExecutionResponse>()
          const sorted = [...allExecs].sort(
            (a, b) => new Date(a.executed_at).getTime() - new Date(b.executed_at).getTime()
          )
          for (const exec of sorted) {
            if (exec.test_code) map.set(exec.test_code, exec)
          }
          setExecMap(map)
        } catch { /* ignore */ }
      }
    }).finally(() => setLoading(false))
  }, [frameworkId, control.id, selectedOrgId])

  useEffect(() => { loadData() }, [loadData])

  if (loading) return (
    <div className="space-y-1.5 py-3">
      {[1, 2, 3].map(i => <div key={i} className="h-7 rounded bg-muted animate-pulse" />)}
    </div>
  )

  return (
    <div className="py-3 space-y-1 text-xs">
      <div className="flex items-center gap-4 pb-2 mb-1 border-b border-border/40 text-muted-foreground">
        {control.category_name && (
          <span>Category: <span className="text-foreground font-medium">{control.category_name}</span></span>
        )}
        <span>Automation: <span className="text-foreground font-medium capitalize">{control.automation_potential}</span></span>
      </div>

      {tests.length === 0 ? (
        <p className="text-muted-foreground py-8 text-center italic">No tests linked to this control.</p>
      ) : (
        <div className="space-y-1">
          {tests.map((test, idx) => {
            const expanded = expandedTests.has(test.id)
            const isLast = idx === tests.length - 1
            const health = execHealth(execMap.get(test.test_code))
            const exec = execMap.get(test.test_code)
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
                    className="ml-1 shrink-0 text-muted-foreground hover:text-primary transition-colors p-1 rounded-full hover:bg-primary/10"
                    onClick={(e) => {
                      e.stopPropagation()
                      const targetId = promotedMap.get(test.id) || test.id
                      router.push(`/tests/${targetId}/live`)
                    }}
                    title="View live test detail"
                  >
                    <Info className="w-3.5 h-3.5" />
                  </button>
                  <Badge variant="outline" className={`ml-auto shrink-0 text-[10px] px-1.5 py-0 ${TEST_TYPE_STYLES[test.test_type_code] ?? ""}`}>
                    {test.test_type_name ?? test.test_type_code}
                  </Badge>
                  <FrequencyBadge frequency={test.monitoring_frequency} />
                </div>

                {expanded && (
                  <div className="ml-10 mt-0.5 mb-1 px-3 py-2 rounded-lg bg-muted/20 border border-border/30 space-y-1.5">
                    <div className="flex items-center gap-3">
                      <HealthBadge status={health} />
                      {exec?.executed_at && (
                        <span className="text-[11px] text-muted-foreground">
                          Last run: <span className={health === "fail" ? "text-red-400" : "text-foreground/70"}>{formatTime(exec.executed_at)}</span>
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Test Buttons */}
      <div className="pt-2 border-t border-border/30 mt-2 flex items-center gap-3">
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

      {aiSuggestOpen && (
        <AiSuggestTestsPanel
          controlId={control.id}
          orgId={defaultOrgId}
          workspaceId={defaultWorkspaceId}
          onLinked={() => loadData()}
          onClose={() => setAiSuggestOpen(false)}
        />
      )}

      {linkTestOpen && (
        <LinkTestsDialog
          open={linkTestOpen}
          controlId={control.id}
          controlName={control.name}
          frameworkId={frameworkId}
          onClose={() => setLinkTestOpen(false)}
          onLinked={() => loadData()}
        />
      )}
    </div>
  )
}

// ── Tasks Panel ─────────────────────────────────────────────────────────────

function ControlTasksPanel({
  control,
  defaultOrgId,
  defaultWorkspaceId,
  onTaskCreated,
}: {
  control: ControlResponse
  defaultOrgId: string
  defaultWorkspaceId: string
  onTaskCreated?: () => void
}) {
  const router = useRouter()
  const [tasks, setTasks] = useState<TaskResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [taskSlideOver, setTaskSlideOver] = useState<{ open: boolean; typeCode: string; typeName: string } | null>(null)

  const today = new Date().toISOString().split("T")[0]

  const loadData = useCallback(() => {
    setLoading(true)
    listTasks({ entity_type: "control", entity_id: control.id, limit: 50 }).then(r => {
      setTasks(r.items ?? [])
    }).catch(() => {}).finally(() => setLoading(false))
  }, [control.id])

  useEffect(() => { loadData() }, [loadData])

  const evidenceTasks = tasks.filter(t => t.task_type_code === "evidence_collection")
  const remediationTasks = tasks.filter(t => t.task_type_code !== "evidence_collection")

  if (loading) return (
    <div className="space-y-1.5 py-3">
      {[1, 2, 3].map(i => <div key={i} className="h-7 rounded bg-muted animate-pulse" />)}
    </div>
  )

  return (
    <div className="py-3 space-y-1 text-xs">
      <div className="flex items-center gap-4 pb-2 mb-1 border-b border-border/40 text-muted-foreground">
        <span>Group: <span className="text-foreground font-medium">{control.requirement_name ?? control.requirement_code}</span></span>
      </div>

      {tasks.length === 0 ? (
        <p className="text-muted-foreground py-8 text-center italic">No tasks created for this control.</p>
      ) : (
        <div className="space-y-1">
          {evidenceTasks.length > 0 && (
            <div>
              <div className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-muted/40">
                <FileText className="w-3 h-3 text-sky-500 shrink-0" />
                <span className="font-medium text-muted-foreground">Evidence Tasks</span>
                <span className="ml-auto text-muted-foreground">{evidenceTasks.length}</span>
              </div>
              <div className="mt-0.5 space-y-0.5">
                {evidenceTasks.map((task) => {
                  const isOverdue = task.due_date && task.due_date < today && !task.is_terminal
                  return (
                    <div key={task.id} className="flex items-center gap-2 px-2 py-1 rounded bg-muted/20 text-[11px] group hover:bg-muted/40 transition-colors">
                      <TaskStatusIcon status={task.status_code} />
                      <Chip label={task.priority_code} className={PRIORITY_COLORS[task.priority_code] ?? "bg-muted text-muted-foreground"} />
                      <span className="truncate">{task.title}</span>
                      <button 
                        onClick={() => router.push(`/tasks/${task.id}`)} 
                        className="ml-auto flex items-center gap-1.5 px-2 py-1 rounded text-[10px] font-semibold text-primary border border-primary/30 hover:bg-primary/10 bg-primary/5 transition-all shrink-0"
                        title="View task detail"
                      >
                        <ExternalLink className="w-3 h-3" /> View
                      </button>
                      <span className={`capitalize ${TASK_STATUS_STYLES[task.status_code] ?? ""}`}>{task.status_name}</span>
                      {task.due_date && <span className={isOverdue ? "text-red-500 font-semibold" : "text-muted-foreground"}>{new Date(task.due_date).toLocaleDateString()}</span>}
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {remediationTasks.length > 0 && (
            <div>
              <div className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-muted/40 mt-1">
                <GitMerge className="w-3 h-3 text-orange-500 shrink-0" />
                <span className="font-medium text-muted-foreground">Remediation Tasks</span>
                <span className="ml-auto text-muted-foreground">{remediationTasks.length}</span>
              </div>
              <div className="mt-0.5 space-y-0.5">
                {remediationTasks.map((task) => {
                  const isOverdue = task.due_date && task.due_date < today && !task.is_terminal
                  return (
                    <div key={task.id} className="flex items-center gap-2 px-2 py-1 rounded bg-muted/20 text-[11px] group hover:bg-muted/40 transition-colors">
                      <TaskStatusIcon status={task.status_code} />
                      <Chip label={task.priority_code} className={PRIORITY_COLORS[task.priority_code] ?? "bg-muted text-muted-foreground"} />
                      <span className="truncate">{task.title}</span>
                      <button 
                        onClick={() => router.push(`/tasks/${task.id}`)} 
                        className="ml-auto flex items-center gap-1.5 px-2 py-1 rounded text-[10px] font-semibold text-primary border border-primary/30 hover:bg-primary/10 bg-primary/5 transition-all shrink-0"
                        title="View task detail"
                      >
                        <ExternalLink className="w-3 h-3" /> View
                      </button>
                      <span className={`capitalize ${TASK_STATUS_STYLES[task.status_code] ?? ""}`}>{task.status_name}</span>
                      {task.due_date && <span className={isOverdue ? "text-red-500 font-semibold" : "text-muted-foreground"}>{new Date(task.due_date).toLocaleDateString()}</span>}
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Task Buttons */}
      <div className="pt-2 border-t border-border/30 mt-2 flex items-center gap-3">
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
      </div>

      {taskSlideOver && (
        <TaskCreateSlideOver
          open={taskSlideOver.open}
          onClose={() => setTaskSlideOver(null)}
          onCreated={() => { loadData(); onTaskCreated?.(); setTaskSlideOver(null) }}
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

// ── Control details panel (edit + view, matches frameworks page) ──────────────

const CATEGORIES = [
  "access_control","change_management","incident_response","data_protection",
  "network_security","physical_security","risk_management","vendor_management",
  "hr_security","business_continuity","cryptography","logging_monitoring",
  "asset_management","compliance",
]

function ControlDetailsPanel({
  control,
  frameworkId,
  orgId,
  workspaceId,
  onUpdated,
}: {
  control: ControlResponse
  frameworkId: string
  orgId?: string | null
  workspaceId?: string | null
  onUpdated: () => void
}) {
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({
    name: control.name ?? "",
    description: control.description ?? "",
    criticality_code: control.criticality_code ?? "medium",
    control_type: control.control_type ?? "preventive",
    automation_potential: control.automation_potential ?? "manual",
    guidance: control.guidance ?? "",
    implementation_guidance: (control.implementation_guidance ?? []).join("\n"),
    tags: (control.tags ?? []).join(", "),
  })
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState("")

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true); setSaveError("")
    try {
      const payload: UpdateControlRequest = {
        name: form.name || undefined,
        description: form.description || undefined,
        criticality_code: form.criticality_code || undefined,
        control_type: form.control_type || undefined,
        automation_potential: form.automation_potential || undefined,
        guidance: form.guidance || undefined,
        implementation_guidance: form.implementation_guidance
          ? form.implementation_guidance.split("\n").map(l => l.trim()).filter(Boolean)
          : [],
        tags: form.tags
          ? form.tags.split(",").map(t => t.trim()).filter(Boolean)
          : [],
      }
      await updateControl(frameworkId, control.id, payload)
      setEditing(false)
      onUpdated()
    } catch (err: unknown) {
      setSaveError(err instanceof Error ? err.message : "Failed to save changes")
    } finally { setSaving(false) }
  }

  function handleCancelEdit() {
    setEditing(false); setSaveError("")
    setForm({
      name: control.name ?? "",
      description: control.description ?? "",
      criticality_code: control.criticality_code ?? "medium",
      control_type: control.control_type ?? "preventive",
      automation_potential: control.automation_potential ?? "manual",
      guidance: control.guidance ?? "",
      implementation_guidance: (control.implementation_guidance ?? []).join("\n"),
      tags: (control.tags ?? []).join(", "),
    })
  }

  if (editing) {
    return (
      <form onSubmit={handleSave} className="py-3 space-y-3 text-xs">
        <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Edit Control</p>
        <div>
          <label className="text-[11px] font-medium text-muted-foreground block mb-1">Name</label>
          <Input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} className="h-7 text-xs" />
        </div>
        <div>
          <div className="flex items-center gap-1.5 mb-1">
            <label className="text-[11px] font-medium text-muted-foreground">Description</label>
            <AIEnhancePopover
              entityType="control"
              entityId={control.id}
              fieldName="description"
              fieldLabel="Description"
              currentValue={form.description}
              orgId={orgId ?? null}
              workspaceId={workspaceId ?? null}
              entityContext={{ control_code: control.control_code, control_name: control.name, framework_id: frameworkId }}
              onApply={(v) => setForm(f => ({ ...f, description: v as string }))}
              popoverSide="right"
            />
          </div>
          <textarea value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} rows={2}
            className="w-full rounded-md border border-input bg-background text-xs px-2 py-1.5 resize-none" />
        </div>
        <div className="grid grid-cols-3 gap-2">
          <div>
            <label className="text-[11px] font-medium text-muted-foreground block mb-1">Criticality</label>
            <select value={form.criticality_code} onChange={e => setForm({ ...form, criticality_code: e.target.value })}
              className="w-full h-7 rounded border border-input bg-background text-xs px-1.5">
              {["critical","high","medium","low"].map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="text-[11px] font-medium text-muted-foreground block mb-1">Type</label>
            <select value={form.control_type} onChange={e => setForm({ ...form, control_type: e.target.value })}
              className="w-full h-7 rounded border border-input bg-background text-xs px-1.5">
              {["preventive","detective","corrective","compensating"].map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="text-[11px] font-medium text-muted-foreground block mb-1">Automation</label>
            <select value={form.automation_potential} onChange={e => setForm({ ...form, automation_potential: e.target.value })}
              className="w-full h-7 rounded border border-input bg-background text-xs px-1.5">
              {["full","partial","manual"].map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
        </div>
        <div>
          <div className="flex items-center gap-1.5 mb-1">
            <label className="text-[11px] font-medium text-muted-foreground">Guidance</label>
            <AIEnhancePopover
              entityType="control"
              entityId={control.id}
              fieldName="guidance"
              fieldLabel="Guidance"
              currentValue={form.guidance}
              orgId={orgId ?? null}
              workspaceId={workspaceId ?? null}
              entityContext={{ control_code: control.control_code, control_name: control.name, framework_id: frameworkId }}
              onApply={(v) => setForm(f => ({ ...f, guidance: v as string }))}
              popoverSide="right"
            />
          </div>
          <textarea value={form.guidance} onChange={e => setForm({ ...form, guidance: e.target.value })} rows={2}
            className="w-full rounded-md border border-input bg-background text-xs px-2 py-1.5 resize-none" />
        </div>
        <div>
          <div className="flex items-center gap-1.5 mb-1 flex-wrap">
            <label className="text-[11px] font-medium text-muted-foreground">Implementation Guidance</label>
            <span className="text-[11px] font-normal text-muted-foreground/70">(one per line)</span>
            <AIEnhancePopover
              entityType="control"
              entityId={control.id}
              fieldName="implementation_guidance"
              fieldLabel="Implementation Guidance"
              currentValue={form.implementation_guidance.split("\n").filter(Boolean)}
              isArrayField
              orgId={orgId ?? null}
              workspaceId={workspaceId ?? null}
              entityContext={{ control_code: control.control_code, control_name: control.name, framework_id: frameworkId }}
              onApply={(v) => {
                const lines = Array.isArray(v) ? v : (v as string).split("\n").filter(Boolean)
                setForm(f => ({ ...f, implementation_guidance: lines.join("\n") }))
              }}
              popoverSide="right"
            />
          </div>
          <textarea value={form.implementation_guidance} onChange={e => setForm({ ...form, implementation_guidance: e.target.value })}
            rows={3} className="w-full rounded-md border border-input bg-background text-xs px-2 py-1.5 resize-none font-mono"
            placeholder={"Enforce MFA for all admin accounts\nLog all access attempts\nReview access quarterly"} />
        </div>
        <div>
          <label className="text-[11px] font-medium text-muted-foreground block mb-1">
            Tags <span className="font-normal text-muted-foreground/70">(comma-separated)</span>
          </label>
          <Input value={form.tags} onChange={e => setForm({ ...form, tags: e.target.value })}
            placeholder="iam, soc2, access-control" className="h-7 text-xs" />
        </div>
        {saveError && <p className="text-[11px] text-red-500">{saveError}</p>}
        <div className="flex items-center gap-2 pt-1">
          <Button type="submit" size="sm" className="h-7 text-xs gap-1" disabled={saving}>
            {saving ? <Loader2 className="w-3 h-3 animate-spin" /> : <Save className="w-3 h-3" />} Save
          </Button>
          <Button type="button" size="sm" variant="ghost" className="h-7 text-xs" onClick={handleCancelEdit}>Cancel</Button>
        </div>
      </form>
    )
  }

  return (
    <div className="py-3 space-y-4 text-xs">
      {control.description && (
        <div>
          <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-1">Description</p>
          <p className="text-foreground leading-relaxed">{control.description}</p>
        </div>
      )}
      {control.guidance && (
        <div>
          <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-1">Guidance</p>
          <p className="text-foreground leading-relaxed">{control.guidance}</p>
        </div>
      )}
      {control.implementation_guidance && control.implementation_guidance.length > 0 && (
        <div>
          <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-1">Implementation Guidance</p>
          <ul className="space-y-1">
            {control.implementation_guidance.map((item, i) => (
              <li key={i} className="flex items-start gap-2 text-foreground">
                <span className="mt-0.5 w-1.5 h-1.5 rounded-full bg-primary/60 shrink-0" />
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}
      <div>
        <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">Properties</p>
        <div className="grid grid-cols-2 gap-x-4 gap-y-2">
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Control Type</span>
            <span className={`inline-flex items-center px-1.5 py-0 rounded text-[10px] font-medium ${CONTROL_TYPE_COLORS[control.control_type] ?? "bg-muted text-muted-foreground"}`}>
              {control.control_type}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Automation</span>
            <Chip label={control.automation_potential} className={AUTOMATION_COLORS[control.automation_potential] ?? "bg-muted text-muted-foreground border-border"} />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Category</span>
            <span className="text-foreground font-medium truncate max-w-[140px] text-right">{control.category_name ?? control.control_category_code}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Criticality</span>
            <Chip label={control.criticality_code} className={CRITICALITY_COLORS[control.criticality_code] ?? "bg-muted text-muted-foreground border-border"} />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Framework</span>
            <span className="text-foreground font-medium truncate max-w-[140px] text-right">{control.framework_name ?? control.framework_code}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Version</span>
            <span className="text-foreground font-medium">v{control.version}</span>
          </div>
        </div>
      </div>
      <Separator className="opacity-30" />
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 text-muted-foreground min-w-[80px]">
          <User className="w-3 h-3" />
          <span>Owner</span>
        </div>
        {control.owner_display_name ?? control.owner_email ? (
          <span className="text-foreground font-medium text-[11px]">{control.owner_display_name ?? control.owner_email}</span>
        ) : (
          <span className="text-muted-foreground italic">Not assigned</span>
        )}
      </div>
      {control.responsible_teams && control.responsible_teams.length > 0 && (
        <div className="flex items-start gap-3">
          <div className="flex items-center gap-1.5 text-muted-foreground min-w-[80px] mt-0.5">
            <Users className="w-3 h-3" />
            <span>Teams</span>
          </div>
          <div className="flex flex-wrap gap-1">
            {control.responsible_teams.map((team, i) => (
              <span key={i} className="inline-flex items-center px-1.5 py-0 rounded text-[10px] bg-blue-500/10 text-blue-600 border border-blue-500/30">{team}</span>
            ))}
          </div>
        </div>
      )}
      {control.tags && control.tags.length > 0 && (
        <div className="flex items-start gap-3">
          <div className="flex items-center gap-1.5 text-muted-foreground min-w-[80px] mt-0.5">
            <Tag className="w-3 h-3" />
            <span>Tags</span>
          </div>
          <div className="flex flex-wrap gap-1">
            {control.tags.map((tag, i) => (
              <span key={i} className="inline-flex items-center px-1.5 py-0 rounded text-[10px] bg-muted text-muted-foreground border border-border">{tag}</span>
            ))}
          </div>
        </div>
      )}
      <div className="pt-1">
        <Button type="button" size="sm" variant="outline" className="h-7 text-xs gap-1.5" onClick={() => setEditing(true)}>
          <Pencil className="w-3 h-3" /> Edit Control
        </Button>
      </div>
    </div>
  )
}

// ── Execution history tab ─────────────────────────────────────────────────────

function HistoryPanel({ executions }: { executions: TestExecutionResponse[] }) {
  return (
    <div className="py-3 text-xs">
      {executions.length === 0 ? (
        <p className="text-muted-foreground py-4 text-center">No executions recorded yet.</p>
      ) : (
        <div className="space-y-1.5">
          {[...executions]
            .sort((a, b) => new Date(b.executed_at).getTime() - new Date(a.executed_at).getTime())
            .slice(0, 20)
            .map((exec) => {
              const h = execHealth(exec)
              return (
                <div key={exec.id} className="flex items-center gap-3 py-1.5 border-b border-border/50 last:border-0">
                  <HealthBadge status={h} />
                  <span className="font-mono text-[11px] text-muted-foreground">{exec.test_code ?? "—"}</span>
                  <span className="text-muted-foreground truncate flex-1">{exec.test_name ?? "Unknown test"}</span>
                  <span className="text-[11px] text-muted-foreground shrink-0">{formatTime(exec.executed_at)}</span>
                </div>
              )
            })}
        </div>
      )}
    </div>
  )
}

// ── Control Risks Panel ───────────────────────────────────────────────────────

const RISK_LEVEL_BADGE: Record<string, string> = {
  critical: "bg-red-500/10 text-red-500 border-red-500/30",
  high:     "bg-orange-500/10 text-orange-500 border-orange-500/30",
  medium:   "bg-yellow-500/10 text-yellow-600 border-yellow-500/30",
  low:      "bg-green-500/10 text-green-500 border-green-500/30",
}

const LINK_TYPE_BADGE: Record<string, string> = {
  mitigating:   "bg-green-500/10 text-green-600 border-green-500/30",
  compensating: "bg-blue-500/10 text-blue-500 border-blue-500/30",
  related:      "bg-muted text-muted-foreground border-border",
}

function ControlRisksPanel({ controlId, orgId, workspaceId }: {
  controlId: string; orgId: string; workspaceId: string
}) {
  const router = useRouter()
  const [mappings, setMappings] = useState<RiskControlMappingResponse[]>([])
  const [risks, setRisks] = useState<RiskResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [assigning, setAssigning] = useState(false)
  const [showAssign, setShowAssign] = useState(false)
  const [form, setForm] = useState({ risk_id: "", link_type: "mitigating", notes: "" })
  const [assignError, setAssignError] = useState("")
  const [removing, setRemoving] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [ms, rs] = await Promise.all([
        listControlRisks(controlId, orgId),
        listRisks({ org_id: orgId, workspace_id: workspaceId, limit: 200 }),
      ])
      setMappings(ms)
      setRisks(rs.items ?? [])
    } finally { setLoading(false) }
  }, [controlId, orgId, workspaceId])

  useEffect(() => { load() }, [load])

  const linkedRiskIds = new Set(mappings.map(m => m.risk_id))
  const available = risks.filter(r => !linkedRiskIds.has(r.id))

  async function handleAssign(e: React.FormEvent) {
    e.preventDefault()
    if (!form.risk_id) { setAssignError("Select a risk"); return }
    setAssigning(true); setAssignError("")
    try {
      await assignRiskToControl(controlId, orgId, {
        risk_id: form.risk_id,
        link_type: form.link_type,
        notes: form.notes || undefined,
      })
      setShowAssign(false)
      setForm({ risk_id: "", link_type: "mitigating", notes: "" })
      await load()
    } catch (err) {
      setAssignError(err instanceof Error ? err.message : "Failed to assign")
    } finally { setAssigning(false) }
  }

  async function handleRemove(mapping: RiskControlMappingResponse) {
    setRemoving(mapping.id)
    try {
      await unassignRiskFromControl(mapping.risk_id, mapping.id)
      await load()
    } finally { setRemoving(null) }
  }

  if (loading) {
    return <div className="py-6 text-center text-xs text-muted-foreground">Loading…</div>
  }

  return (
    <div className="py-3 space-y-3 text-xs">
      {/* Assign form */}
      {showAssign ? (
        <form onSubmit={handleAssign} className="rounded-lg border border-border bg-muted/30 p-3 space-y-2">
          <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Assign Risk</p>
          <select
            value={form.risk_id}
            onChange={e => setForm(f => ({ ...f, risk_id: e.target.value }))}
            className="w-full h-7 rounded border border-input bg-background text-xs px-1.5"
          >
            <option value="">— Select a risk —</option>
            {available.map(r => (
              <option key={r.id} value={r.id}>{r.risk_code} — {r.title}</option>
            ))}
          </select>
          <div className="flex items-center gap-2">
            <select
              value={form.link_type}
              onChange={e => setForm(f => ({ ...f, link_type: e.target.value }))}
              className="h-7 rounded border border-input bg-background text-xs px-1.5"
            >
              <option value="mitigating">Mitigating</option>
              <option value="compensating">Compensating</option>
              <option value="related">Related</option>
            </select>
            <input
              placeholder="Notes (optional)"
              value={form.notes}
              onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
              className="flex-1 h-7 rounded border border-input bg-background text-xs px-2"
            />
          </div>
          {assignError && <p className="text-[11px] text-red-500">{assignError}</p>}
          <div className="flex items-center gap-2">
            <button type="submit" disabled={assigning}
              className="flex items-center gap-1 h-7 px-3 rounded-lg bg-primary text-primary-foreground text-xs font-medium disabled:opacity-50">
              {assigning ? <Loader2 className="w-3 h-3 animate-spin" /> : null} Assign
            </button>
            <button type="button" onClick={() => setShowAssign(false)}
              className="h-7 px-3 rounded-lg border border-border text-xs text-muted-foreground hover:text-foreground">
              Cancel
            </button>
          </div>
        </form>
      ) : (
        <button
          type="button"
          onClick={() => setShowAssign(true)}
          className="flex items-center gap-1.5 h-7 px-3 rounded-lg border border-border text-xs text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
        >
          <Plus className="w-3 h-3" /> Assign Risk
        </button>
      )}

      {/* Linked risks list */}
      {mappings.length === 0 ? (
        <p className="text-xs text-muted-foreground py-2 text-center">No risks linked to this control.</p>
      ) : (
        <div className="space-y-1">
          {mappings.map((m, idx) => {
            const isLast = idx === mappings.length - 1
            const risk = risks.find(r => r.id === m.risk_id)
            const levelKey = risk?.risk_level_code?.toLowerCase() ?? ""
            return (
              <div key={m.id}
                className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-muted/40 hover:bg-muted/60 transition-colors group">
                <span className="w-4 shrink-0 text-border text-[10px]">{isLast ? "└─" : "├─"}</span>
                <ShieldAlert className="w-3 h-3 shrink-0 text-muted-foreground" />
                <span className="font-mono text-[10px] text-muted-foreground shrink-0">{m.risk_code ?? risk?.risk_code ?? "—"}</span>
                <span className="truncate font-medium">{m.risk_title ?? risk?.title ?? m.risk_id}</span>
                {levelKey && (
                  <span className={`inline-flex items-center rounded border px-1 py-0 text-[9px] font-semibold uppercase tracking-wide shrink-0 ${RISK_LEVEL_BADGE[levelKey] ?? "bg-muted text-muted-foreground border-border"}`}>
                    {levelKey}
                  </span>
                )}
                <span className={`inline-flex items-center rounded border px-1 py-0 text-[9px] font-semibold uppercase tracking-wide shrink-0 ${LINK_TYPE_BADGE[m.link_type] ?? "bg-muted text-muted-foreground border-border"}`}>
                  {m.link_type}
                </span>
                 <button
                   className="ml-auto flex items-center gap-1.5 px-2 py-1 rounded text-[10px] font-semibold text-primary border border-primary/30 hover:bg-primary/10 bg-primary/5 transition-all shrink-0"
                   onClick={() => router.push(`/risks/${m.risk_id}`)}
                   title="View risk detail"
                 >
                   <ExternalLink className="w-3 h-3" /> View
                 </button>
                <button
                  className="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-red-500"
                  onClick={() => handleRemove(m)}
                  disabled={removing === m.id}
                  title="Remove link"
                >
                  {removing === m.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <X className="w-3 h-3" />}
                </button>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

type DetailTab = "tests" | "tasks" | "details" | "risks" | "comments" | "attachments" | "history"

export default function ControlDetailPage() {
  const { frameworkId, controlId } = useParams<{ frameworkId: string; controlId: string }>()
  const router = useRouter()
  const { isWorkspaceAdmin } = useAccess()
  const { selectedOrgId, selectedWorkspaceId } = useOrgWorkspace()
  const currentUserId = typeof window !== "undefined" ? (getJwtSubject() ?? "") : ""

  const [control, setControl] = useState<ControlResponse | null>(null)
  const [executions, setExecutions] = useState<TestExecutionResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<DetailTab>("tests")

  // Register human-readable names so copilot never shows raw UUIDs
  useCopilotEntityNames({
    framework_name: control?.framework_name ?? control?.framework_code ?? undefined,
    control_code: control?.control_code ?? undefined,
    control_name: control?.name ?? undefined,
  })

  const load = useCallback(async () => {
    if (!frameworkId || !controlId) return
    setLoading(true); setError(null)
    try {
      const ctrl = await getControl(frameworkId, controlId)
      setControl(ctrl)
      // Load executions for history tab
      const execRes = await listTestExecutions({ control_id: controlId, limit: 200 })
      setExecutions(execRes.items ?? [])
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load control")
    } finally { setLoading(false) }
  }, [frameworkId, controlId])

  useEffect(() => { load() }, [load])

  const TABS: { id: DetailTab; label: string; icon: React.ReactNode }[] = [
    { id: "tests",       label: "Tests",         icon: <ClipboardCheck className="w-3.5 h-3.5" /> },
    { id: "tasks",       label: "Tasks",         icon: <ListTodo className="w-3.5 h-3.5" /> },
    { id: "details",     label: "Details",       icon: <Info className="w-3.5 h-3.5" /> },
    { id: "risks",       label: "Risks",         icon: <ShieldAlert className="w-3.5 h-3.5" /> },
    { id: "comments",    label: "Comments",      icon: <MessageSquare className="w-3.5 h-3.5" /> },
    { id: "attachments", label: "Attachments",   icon: <Paperclip className="w-3.5 h-3.5" /> },
    { id: "history",     label: "History",       icon: <History className="w-3.5 h-3.5" /> },
  ]

  if (loading) {
    return (
      <div className="space-y-3">
        <div className="h-6 w-64 rounded bg-muted animate-pulse" />
        <div className="h-24 rounded-xl bg-muted animate-pulse" />
        <div className="h-64 rounded-xl bg-muted animate-pulse" />
      </div>
    )
  }

  if (error || !control) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-3">
        <AlertTriangle className="h-8 w-8 text-red-400" />
        <p className="text-sm text-muted-foreground">{error ?? "Control not found"}</p>
        <Button variant="outline" size="sm" onClick={() => router.back()}>Go back</Button>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Breadcrumb + nav */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <button
            type="button"
            onClick={() => router.push(`/frameworks/${frameworkId}`)}
            className="text-blue-400 hover:text-blue-300 transition-colors"
          >
            {control.framework_name ?? control.framework_code ?? "Framework"}
          </button>
          <ChevronRight className="h-3.5 w-3.5" />
          <span className="font-mono text-foreground">{control.control_code}</span>
          <span className="text-muted-foreground/50">—</span>
          <span className="text-foreground truncate max-w-[240px]">{control.name}</span>
        </div>
      </div>

      {/* Control header card — same style as framework page's control row expanded header */}
      <Card className="rounded-xl">
        <CardContent className="pt-4 pb-4 px-5">
          <div className="flex items-start gap-3 flex-wrap">
            {/* Code + badges row */}
            <div className="flex-1 min-w-0 space-y-1.5">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-mono text-sm font-bold text-primary">{control.control_code}</span>
                {control.framework_code && (
                  <span className="inline-flex items-center rounded border border-blue-500/30 bg-blue-500/10 px-1.5 py-0 text-[10px] font-bold text-blue-400">
                    {control.framework_code}
                  </span>
                )}
                <Chip
                  label={control.criticality_code}
                  className={CRITICALITY_COLORS[control.criticality_code] ?? "bg-muted text-muted-foreground border-border"}
                />
                <span className={`inline-flex items-center px-1.5 py-0 rounded text-[10px] font-medium ${CONTROL_TYPE_COLORS[control.control_type] ?? "bg-muted text-muted-foreground"}`}>
                  {control.control_type}
                </span>
                <Chip
                  label={control.automation_potential}
                  className={AUTOMATION_COLORS[control.automation_potential] ?? "bg-muted text-muted-foreground border-border"}
                />
                {control.owner_display_name && (
                  <span className="text-[11px] text-muted-foreground flex items-center gap-1">
                    <User className="h-3 w-3" /> {control.owner_display_name}
                  </span>
                )}
              </div>
              <h1 className="text-lg font-bold tracking-tight">{control.name}</h1>
              {control.requirement_name && (
                <p className="text-[11px] text-muted-foreground">{control.requirement_name}</p>
              )}
            </div>

            {/* Test count badge */}
            <div className="shrink-0 flex items-center gap-1.5 text-[11px] text-muted-foreground">
              <ClipboardCheck className="h-3.5 w-3.5" />
              <span>{control.test_count ?? 0} tests</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabs — exact same style as framework page's ControlRowExpandedPanel */}
      <div className="flex items-center gap-0 border-b border-border">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px ${
              activeTab === tab.id
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div>
        {activeTab === "tests" && (
          <ControlTestsPanel
            control={control}
            frameworkId={frameworkId}
            defaultOrgId={selectedOrgId ?? ""}
            defaultWorkspaceId={selectedWorkspaceId ?? ""}
          />
        )}
        {activeTab === "tasks" && (
          <ControlTasksPanel
            control={control}
            defaultOrgId={selectedOrgId ?? ""}
            defaultWorkspaceId={selectedWorkspaceId ?? ""}
            onTaskCreated={load}
          />
        )}
        {activeTab === "details" && (
          <ControlDetailsPanel control={control} frameworkId={frameworkId} orgId={selectedOrgId} workspaceId={selectedWorkspaceId} onUpdated={load} />
        )}
        {activeTab === "risks" && (
          <ControlRisksPanel controlId={controlId} orgId={selectedOrgId} workspaceId={selectedWorkspaceId} />
        )}
        {activeTab === "comments" && (
          <div className="py-3">
            <CommentsSection
              entityType="control"
              entityId={controlId}
              currentUserId={currentUserId}
              isWorkspaceAdmin={isWorkspaceAdmin}
              active={activeTab === "comments"}
            />
          </div>
        )}
        {activeTab === "attachments" && (
          <div className="py-3">
            <AttachmentsSection
              entityType="control"
              entityId={controlId}
              currentUserId={currentUserId}
              canUpload
              isWorkspaceAdmin={isWorkspaceAdmin}
              active={activeTab === "attachments"}
            />
          </div>
        )}
        {activeTab === "history" && (
          <HistoryPanel executions={executions} />
        )}
      </div>
    </div>
  )
}
