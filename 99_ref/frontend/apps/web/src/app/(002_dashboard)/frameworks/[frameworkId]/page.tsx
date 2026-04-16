"use client"

import React, { useEffect, useState, useCallback, useRef } from "react"
import { useParams, useRouter } from "next/navigation"
import {
  Card, CardContent, Button, Input, Badge, Separator,
} from "@kcontrol/ui"
import {
  ChevronDown, ChevronRight, ChevronLeft,
  Layers, ShieldCheck, FlaskConical,
  AlertTriangle, RefreshCw, Plus, Search, Loader2,
  Tag, User, Users, BookOpen, LayoutList, TableProperties,
  MessageSquare, Paperclip, GitBranch, Upload, Download, Send,
  ClipboardCheck, CheckCircle2, Circle, Clock,
  FileText, Zap, GitMerge, Info, ExternalLink,
  Pencil, Save, Filter, Target, X, Sparkles, Trash2, ListTodo, HelpCircle,
} from "lucide-react"
import {
  getFramework, listRequirements, listControls, listVersions,
  createRequirement, createControl, createVersion, publishVersion,
  listControlTests, updateControl, exportControls, importControls,
  exportFrameworkBundle, importFrameworkBundle, submitFrameworkForReview,
  listFrameworkCategories, updateFramework, deleteFramework, getFrameworkDiff,
} from "@/lib/api/grc"
import {
  getAuditReadiness, getFrameworkReports, generateReport,
  getReport, REPORT_TYPE_LABELS, downloadReport,
  type AuditReadinessResponse, type ReportSummaryResponse, type ReportResponse,
} from "@/lib/api/ai"
import { EntitySpreadsheet } from "@/components/spreadsheet/EntitySpreadsheet"
import { controlsColumns } from "@/components/spreadsheet/controlsConfig"
import type { ControlSpreadsheetRow } from "@/components/spreadsheet/controlsConfig"
import {
  suggestTestsForControl,
  applyTestLinkerSuggestionsForControl,
  type TestSuggestion,
} from "@/lib/api/testLinker"
import { listTasks } from "@/lib/api/grc"
import type {
  FrameworkResponse, RequirementResponse, ControlResponse, VersionResponse,
  CreateVersionRequest, TestResponse, TaskResponse,
  UpdateControlRequest, CreateTaskRequest,
  DimensionResponse, UpdateFrameworkRequest, FrameworkBundle, BundleImportResult, BundleImportError,
  FrameworkDiff,
} from "@/lib/types/grc"
import type { OrgMemberResponse } from "@/lib/types/orgs"
import { CommentsSection } from "@/components/comments/CommentsSection"
import { AttachmentsSection } from "@/components/attachments/AttachmentsSection"
import { EditFrameworkDialog, DeleteFrameworkDialog } from "@/components/grc/FrameworkDialogs"
import { useOrgWorkspace } from "@/lib/context/OrgWorkspaceContext"
import { useAccess } from "@/components/providers/AccessProvider"
import { FormFillChat } from "@/components/ai/FormFillChat"
import { TaskCreateSlideOver } from "@/components/tasks/TaskCreateSlideOver"
import { MarkdownRenderer } from "@/components/ui/MarkdownRenderer"
import { LinkTestsDialog } from "@/components/grc/LinkTestsDialog"

// ─────────────────────────────────────────────────────────────────────────────
// Auth helper
// ─────────────────────────────────────────────────────────────────────────────

function getJwtSubject(): string | null {
  try {
    const token = localStorage.getItem("access_token")
    if (!token) return null
    const base64Url = token.split(".")[1]
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/")
    const pad = base64.length % 4
    const padded = pad ? base64 + "=".repeat(4 - pad) : base64
    const payload = JSON.parse(atob(padded))
    return payload.sub || null
  } catch {
    return null
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

const VERSION_STYLES: Record<string, string> = {
  draft: "bg-muted text-muted-foreground",
  published: "bg-green-500/10 text-green-600 border-green-500/30",
  deprecated: "bg-orange-500/10 text-orange-600 border-orange-500/30",
}

const CRITICALITY_COLORS: Record<string, string> = {
  critical: "bg-red-500/10 text-red-500 border-red-500/30",
  high:     "bg-orange-500/10 text-orange-500 border-orange-500/30",
  medium:   "bg-yellow-500/10 text-yellow-600 border-yellow-500/30",
  low:      "bg-green-500/10 text-green-500 border-green-500/30",
}

const CONTROL_TYPE_COLORS: Record<string, string> = {
  preventive:    "bg-blue-500/10 text-blue-500",
  detective:     "bg-purple-500/10 text-purple-500",
  corrective:    "bg-amber-500/10 text-amber-600",
  compensating:  "bg-teal-500/10 text-teal-500",
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

const PAGE_SIZE = 25

// ─────────────────────────────────────────────────────────────────────────────
// Control row expanded panel — details + comments + attachments tabs
// ─────────────────────────────────────────────────────────────────────────────

type ControlDetailTab = "details" | "hierarchy" | "comments" | "attachments"

type OrgGroup = { id: string; name: string; is_locked: boolean }

// ── Test type styles ─────────────────────────────────────────────────────────

const TEST_TYPE_STYLES: Record<string, string> = {
  automated:  "bg-green-500/10 text-green-600 border-green-500/30",
  manual:     "bg-blue-500/10 text-blue-600 border-blue-500/30",
  hybrid:     "bg-purple-500/10 text-purple-600 border-purple-500/30",
}

const TASK_STATUS_STYLES: Record<string, string> = {
  open:        "text-muted-foreground",
  in_progress: "text-blue-500",
  completed:   "text-green-500",
  blocked:     "text-red-500",
}

function TaskStatusIcon({ status }: { status: string }) {
  if (status === "completed") return <CheckCircle2 className="w-3 h-3 text-green-500" />
  if (status === "in_progress") return <Clock className="w-3 h-3 text-blue-500" />
  if (status === "blocked") return <AlertTriangle className="w-3 h-3 text-red-500" />
  return <Circle className="w-3 h-3 text-muted-foreground" />
}

// ── Hierarchy panel: Tests → Tasks ───────────────────────────────────────────


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


function ControlHierarchyPanel({
  control,
  frameworkId,
  defaultOrgId,
  defaultWorkspaceId,
  onTaskCreated,
}: {
  control: ControlResponse
  frameworkId: string
  defaultOrgId: string
  defaultWorkspaceId: string
  onTaskCreated?: () => void
}) {
  const router = useRouter()
  const [tests, setTests] = useState<TestResponse[]>([])
  const [tasks, setTasks] = useState<TaskResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<"tests" | "tasks">("tests")

  // Task slide-over state
  const [taskSlideOver, setTaskSlideOver] = useState<{ open: boolean; typeCode: string; typeName: string } | null>(null)

  // Link test dialog state
  const [linkTestOpen, setLinkTestOpen] = useState(false)
  const [aiSuggestOpen, setAiSuggestOpen] = useState(false)

  const today = new Date().toISOString().split("T")[0]

  const loadData = useCallback((silent = false) => {
    if (!silent) setLoading(true)
    Promise.all([
      listControlTests(frameworkId, control.id).then(r => setTests(r.items ?? [])).catch(() => {}),
      listTasks({ 
        orgId: defaultOrgId, 
        workspaceId: defaultWorkspaceId, 
        entity_type: "control", 
        entity_id: control.id, 
        limit: 50 
      }).then(r => setTasks(r.items ?? [])).catch(() => {}),
    ]).finally(() => { if (!silent) setLoading(false) })
  }, [frameworkId, control.id])

  useEffect(() => { loadData() }, [loadData])

  const evidenceTasks = tasks.filter(t => t.task_type_code === "evidence_collection")
  const remediationTasks = tasks.filter(t => t.task_type_code !== "evidence_collection")

  if (loading) return (
    <div className="space-y-1.5 py-3">
      {[1,2,3].map(i => <div key={i} className="h-7 rounded bg-muted animate-pulse" />)}
    </div>
  )

  return (
    <div className="py-3 text-xs">
      {/* Control meta row */}
      <div className="flex items-center gap-4 pb-2 mb-1 border-b border-border/40 text-muted-foreground">
        {control.category_name && <span>Category: <span className="text-foreground font-medium">{control.category_name}</span></span>}
        <span>Automation: <span className="text-foreground font-medium capitalize">{control.automation_potential}</span></span>
        {control.requirement_code && <span>Group: <span className="text-foreground font-medium">{control.requirement_name ?? control.requirement_code}</span></span>}
      </div>

      {/* Tabs: Tests | Tasks */}
      <div className="flex items-center gap-0 mb-3 border-b border-border/50">
        <button
          type="button"
          onClick={() => setActiveTab("tests")}
          className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium border-b-2 transition-colors -mb-px ${
            activeTab === "tests"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <ClipboardCheck className="w-3 h-3" />
          Tests
          <span className={`ml-1 text-[10px] px-1.5 py-0 rounded-full ${activeTab === "tests" ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"}`}>
            {tests.length}
          </span>
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("tasks")}
          className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium border-b-2 transition-colors -mb-px ${
            activeTab === "tasks"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <ListTodo className="w-3 h-3" />
          Tasks
          <span className={`ml-1 text-[10px] px-1.5 py-0 rounded-full ${activeTab === "tasks" ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"}`}>
            {tasks.length}
          </span>
        </button>
      </div>

      {/* ── Tests Tab ─────────────────────────────────────────────── */}
      {activeTab === "tests" && (
        <div className="space-y-1">
          {tests.length === 0 ? (
            <div className="py-6 text-center">
              <p className="text-muted-foreground mb-3">No tests linked to this control.</p>
              <button
                type="button"
                onClick={() => setLinkTestOpen(true)}
                className="inline-flex items-center gap-1.5 text-[11px] text-emerald-600 hover:text-emerald-500 transition-colors"
              >
                <Layers className="w-3 h-3" /> Link Test
              </button>
            </div>
          ) : (
            <div className="space-y-1">
              {tests.map((test) => (
                <div
                  key={test.id}
                  className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-muted/40 hover:bg-muted/60 transition-colors group"
                >
                  {test.is_platform_managed
                    ? <Zap className="w-3 h-3 text-amber-500 shrink-0" />
                    : <ClipboardCheck className="w-3 h-3 text-blue-500 shrink-0" />
                  }
                  <span className="font-mono text-[11px] text-primary shrink-0">{test.test_code}</span>
                  <span className="truncate font-medium">{test.name ?? test.test_code}</span>
                  <button
                    className="ml-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-primary"
                    onClick={() => router.push(`/tests?highlight=${test.id}`)}
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
              ))}
            </div>
          )}

          {/* Action buttons */}
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
              onClick={() => setAiSuggestOpen((v) => !v)}
              className="flex items-center gap-1.5 text-[11px] text-violet-600 hover:text-violet-500 transition-colors"
            >
              <Sparkles className="w-3 h-3" /> AI Find Tests
            </button>
          </div>
        </div>
      )}

      {/* ── Tasks Tab ─────────────────────────────────────────────── */}
      {activeTab === "tasks" && (
        <div className="space-y-1">
          {evidenceTasks.length === 0 && remediationTasks.length === 0 ? (
            <div className="py-6 text-center">
              <p className="text-muted-foreground mb-3">No tasks attached to this control.</p>
              <div className="flex items-center justify-center gap-3">
                <button
                  type="button"
                  onClick={() => setTaskSlideOver({ open: true, typeCode: "evidence_collection", typeName: "Evidence Collection" })}
                  className="inline-flex items-center gap-1.5 text-[11px] text-sky-600 hover:text-sky-500 transition-colors"
                >
                  <FileText className="w-3 h-3" /> Add Evidence Task
                </button>
                <span className="text-border/50">|</span>
                <button
                  type="button"
                  onClick={() => setTaskSlideOver({ open: true, typeCode: "control_remediation", typeName: "Remediation" })}
                  className="inline-flex items-center gap-1.5 text-[11px] text-orange-600 hover:text-orange-500 transition-colors"
                >
                  <Target className="w-3 h-3" /> Add Remediation Task
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-1">
              {/* Evidence Tasks */}
              {evidenceTasks.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-muted/40 mb-1">
                    <FileText className="w-3 h-3 text-sky-500 shrink-0" />
                    <span className="font-medium text-muted-foreground">Evidence Tasks</span>
                    <span className="ml-auto text-muted-foreground">{evidenceTasks.length}</span>
                  </div>
                  <div className="ml-1 space-y-0.5">
                    {evidenceTasks.map((task) => {
                      const isOverdue = task.due_date && task.due_date < today && !task.is_terminal
                      return (
                        <div key={task.id} className="flex items-center gap-2 px-2 py-1.5 rounded bg-muted/20 text-[11px] group hover:bg-muted/40 transition-colors">
                          <TaskStatusIcon status={task.status_code} />
                          <Chip
                            label={task.priority_code}
                            className={PRIORITY_COLORS[task.priority_code] ?? "bg-muted text-muted-foreground border-border"}
                          />
                          <span className="truncate">{task.title}</span>
                          <button
                            className="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-primary"
                            onClick={() => router.push(`/tasks/${task.id}`)}
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

              {/* Remediation Tasks */}
              {remediationTasks.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-muted/40 mb-1">
                    <GitMerge className="w-3 h-3 text-orange-500 shrink-0" />
                    <span className="font-medium text-muted-foreground">Remediation Tasks</span>
                    <span className="ml-auto text-muted-foreground">{remediationTasks.length}</span>
                  </div>
                  <div className="ml-1 space-y-0.5">
                    {remediationTasks.map((task) => {
                      const isOverdue = task.due_date && task.due_date < today && !task.is_terminal
                      return (
                        <div key={task.id} className="flex items-center gap-2 px-2 py-1.5 rounded bg-muted/20 text-[11px] group hover:bg-muted/40 transition-colors">
                          <TaskStatusIcon status={task.status_code} />
                          <Chip
                            label={task.priority_code}
                            className={PRIORITY_COLORS[task.priority_code] ?? "bg-muted text-muted-foreground border-border"}
                          />
                          <span className="truncate">{task.title}</span>
                          <button
                            className="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-primary"
                            onClick={() => router.push(`/tasks/${task.id}`)}
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

            <span className="text-border/50">|</span>
            <button
              type="button"
              onClick={() => setAiSuggestOpen((v) => !v)}
              className="flex items-center gap-1.5 text-[11px] text-violet-600 hover:text-violet-500 transition-colors"
            >
              <Sparkles className="w-3 h-3" /> AI Find Tests
            </button>
          </div>
        </div>
      )}

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

      {/* Link test dialog */}
      <LinkTestsDialog
        open={linkTestOpen}
        controlId={control.id}
        controlName={control.name}
        frameworkId={frameworkId}
        onClose={() => setLinkTestOpen(false)}
        onLinked={() => loadData(true)}
      />

      {/* Task create slide-over */}
      {taskSlideOver && (
        <TaskCreateSlideOver
          open={taskSlideOver.open}
          onClose={() => setTaskSlideOver(null)}
          onCreated={() => { loadData(true); onTaskCreated?.(); setTaskSlideOver(null) } }
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

// ── Control Details Tab ───────────────────────────────────────────────────────

const CATEGORIES = [
  "access_control","change_management","incident_response","data_protection",
  "network_security","physical_security","risk_management","vendor_management",
  "hr_security","business_continuity","cryptography","logging_monitoring",
  "asset_management","compliance",
]

function ControlDetailsPanel({
  control,
  frameworkId,
  onUpdated,
}: {
  control: ControlResponse
  frameworkId: string
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
    } finally {
      setSaving(false)
    }
  }

  function handleCancelEdit() {
    setEditing(false)
    setSaveError("")
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
          <Input
            value={form.name}
            onChange={e => setForm({ ...form, name: e.target.value })}
            className="h-7 text-xs"
          />
        </div>

        <div>
          <label className="text-[11px] font-medium text-muted-foreground block mb-1">Description</label>
          <textarea
            value={form.description}
            onChange={e => setForm({ ...form, description: e.target.value })}
            rows={2}
            className="w-full rounded-md border border-input bg-background text-xs px-2 py-1.5 resize-none"
          />
        </div>

        <div className="grid grid-cols-3 gap-2">
          <div>
            <label className="text-[11px] font-medium text-muted-foreground block mb-1">Criticality</label>
            <select
              value={form.criticality_code}
              onChange={e => setForm({ ...form, criticality_code: e.target.value })}
              className="w-full h-7 rounded border border-input bg-background text-xs px-1.5"
            >
              {["critical","high","medium","low"].map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="text-[11px] font-medium text-muted-foreground block mb-1">Type</label>
            <select
              value={form.control_type}
              onChange={e => setForm({ ...form, control_type: e.target.value })}
              className="w-full h-7 rounded border border-input bg-background text-xs px-1.5"
            >
              {["preventive","detective","corrective","compensating"].map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="text-[11px] font-medium text-muted-foreground block mb-1">Automation</label>
            <select
              value={form.automation_potential}
              onChange={e => setForm({ ...form, automation_potential: e.target.value })}
              className="w-full h-7 rounded border border-input bg-background text-xs px-1.5"
            >
              {["full","partial","manual"].map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
        </div>

        <div>
          <label className="text-[11px] font-medium text-muted-foreground block mb-1">Guidance</label>
          <textarea
            value={form.guidance}
            onChange={e => setForm({ ...form, guidance: e.target.value })}
            rows={2}
            className="w-full rounded-md border border-input bg-background text-xs px-2 py-1.5 resize-none"
          />
        </div>

        <div>
          <label className="text-[11px] font-medium text-muted-foreground block mb-1">
            Implementation Guidance <span className="font-normal text-muted-foreground/70">(one per line)</span>
          </label>
          <textarea
            value={form.implementation_guidance}
            onChange={e => setForm({ ...form, implementation_guidance: e.target.value })}
            rows={3}
            className="w-full rounded-md border border-input bg-background text-xs px-2 py-1.5 resize-none font-mono"
            placeholder={"Enforce MFA for all admin accounts\nLog all access attempts\nReview access quarterly"}
          />
        </div>

        <div>
          <label className="text-[11px] font-medium text-muted-foreground block mb-1">
            Tags <span className="font-normal text-muted-foreground/70">(comma-separated)</span>
          </label>
          <Input
            value={form.tags}
            onChange={e => setForm({ ...form, tags: e.target.value })}
            placeholder="iam, soc2, access-control"
            className="h-7 text-xs"
          />
        </div>

        {saveError && <p className="text-[11px] text-red-500">{saveError}</p>}

        <div className="flex items-center gap-2 pt-1">
          <Button type="submit" size="sm" className="h-7 text-xs gap-1" disabled={saving}>
            {saving ? <Loader2 className="w-3 h-3 animate-spin" /> : <Save className="w-3 h-3" />}
            Save
          </Button>
          <Button type="button" size="sm" variant="ghost" className="h-7 text-xs" onClick={handleCancelEdit}>
            Cancel
          </Button>
        </div>
      </form>
    )
  }

  // View mode
  return (
    <div className="py-3 space-y-4 text-xs">
      {/* Description */}
      {control.description && (
        <div>
          <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-1">Description</p>
          <p className="text-foreground leading-relaxed">{control.description}</p>
        </div>
      )}

      {/* Guidance */}
      {control.guidance && (
        <div>
          <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-1">Guidance</p>
          <p className="text-foreground leading-relaxed">{control.guidance}</p>
        </div>
      )}

      {/* Implementation guidance bullets */}
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

      {/* Properties grid */}
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
            <Chip
              label={control.automation_potential}
              className={AUTOMATION_COLORS[control.automation_potential] ?? "bg-muted text-muted-foreground border-border"}
            />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Category</span>
            <span className="text-foreground font-medium truncate max-w-[140px] text-right">{control.category_name ?? control.control_category_code}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Criticality</span>
            <Chip
              label={control.criticality_code}
              className={CRITICALITY_COLORS[control.criticality_code] ?? "bg-muted text-muted-foreground border-border"}
            />
          </div>
        </div>
      </div>

      <Separator className="opacity-30" />

      {/* Owner */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 text-muted-foreground min-w-[80px]">
          <User className="w-3 h-3" />
          <span>Owner</span>
        </div>
        {control.owner_user_id ? (
          <span className="font-mono text-[11px] text-foreground">{control.owner_user_id.substring(0, 8)}…</span>
        ) : (
          <span className="text-muted-foreground italic">Not assigned</span>
        )}
      </div>

      {/* Responsible teams */}
      {control.responsible_teams && control.responsible_teams.length > 0 && (
        <div className="flex items-start gap-3">
          <div className="flex items-center gap-1.5 text-muted-foreground min-w-[80px] mt-0.5">
            <Users className="w-3 h-3" />
            <span>Teams</span>
          </div>
          <div className="flex flex-wrap gap-1">
            {control.responsible_teams.map((team, i) => (
              <span key={i} className="inline-flex items-center px-1.5 py-0 rounded text-[10px] bg-blue-500/10 text-blue-600 border border-blue-500/30">
                {team}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Tags */}
      {control.tags && control.tags.length > 0 && (
        <div className="flex items-start gap-3">
          <div className="flex items-center gap-1.5 text-muted-foreground min-w-[80px] mt-0.5">
            <Tag className="w-3 h-3" />
            <span>Tags</span>
          </div>
          <div className="flex flex-wrap gap-1">
            {control.tags.map((tag, i) => (
              <span key={i} className="inline-flex items-center px-1.5 py-0 rounded text-[10px] bg-muted text-muted-foreground border border-border">
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Edit button */}
      <div className="pt-1">
        <Button
          type="button"
          size="sm"
          variant="outline"
          className="h-7 text-xs gap-1.5"
          onClick={() => setEditing(true)}
        >
          <Pencil className="w-3 h-3" /> Edit Control
        </Button>
      </div>
    </div>
  )
}

// ── Control expanded panel ────────────────────────────────────────────────────

function ControlRowExpandedPanel({
  control,
  frameworkId,
  orgMembers,
  orgGroups,
  defaultOrgId,
  defaultWorkspaceId,
  onUpdated,
}: {
  control: ControlResponse
  frameworkId: string
  orgMembers: OrgMemberResponse[]
  orgGroups: OrgGroup[]
  defaultOrgId: string
  defaultWorkspaceId: string
  onUpdated: () => void
}) {
  const [activeTab, setActiveTab] = useState<ControlDetailTab>("hierarchy")
  const currentUserId = getJwtSubject() ?? ""
  const { isWorkspaceAdmin } = useAccess()

  const TABS: { id: ControlDetailTab; label: string; icon: React.ReactNode }[] = [
    { id: "hierarchy", label: "Tests & Tasks", icon: <ClipboardCheck className="w-3 h-3" /> },
    { id: "details", label: "Details", icon: <Info className="w-3 h-3" /> },
    { id: "comments", label: "Comments", icon: <MessageSquare className="w-3 h-3" /> },
    { id: "attachments", label: "Attachments", icon: <Paperclip className="w-3 h-3" /> },
  ]

  return (
    <div className="bg-muted/20 border-t border-border/30 px-4 ml-10">
      {/* Tab bar */}
      <div className="flex items-center gap-0 border-b border-border/50 -mx-4 px-4">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={(e) => { e.stopPropagation(); setActiveTab(tab.id) }}
            className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium border-b-2 transition-colors -mb-px ${
              activeTab === tab.id
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
            role="tab"
          >
            {tab.icon}{tab.label}
          </button>
        ))}
      </div>

      <div className="py-1">
        {activeTab === "details" && (
          <ControlDetailsPanel control={control} frameworkId={frameworkId} onUpdated={onUpdated} />
        )}
        {activeTab === "hierarchy" && (
          <ControlHierarchyPanel control={control} frameworkId={frameworkId} defaultOrgId={defaultOrgId} defaultWorkspaceId={defaultWorkspaceId} onTaskCreated={onUpdated} />
        )}
        {activeTab === "comments" && (
          <div className="py-3">
            <CommentsSection
              entityType="control"
              entityId={control.id}
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
              entityId={control.id}
              currentUserId={currentUserId}
              canUpload
              isWorkspaceAdmin={isWorkspaceAdmin}
              active={activeTab === "attachments"}
            />
          </div>
        )}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Control row — expandable detail
// ─────────────────────────────────────────────────────────────────────────────

function ControlRow({
  control,
  index,
  frameworkId,
  groupLabel,
  orgMembers,
  orgGroups,
  defaultOrgId,
  defaultWorkspaceId,
  onUpdated,
}: {
  control: ControlResponse
  index: number
  frameworkId: string
  groupLabel?: string
  orgMembers: OrgMemberResponse[]
  orgGroups: OrgGroup[]
  defaultOrgId: string
  defaultWorkspaceId: string
  onUpdated: () => void
}) {
  const [open, setOpen] = useState(false)
  const router = useRouter()

  const hasNoTests = (control.test_count ?? 0) === 0
  const displayTags = control.tags?.slice(0, 2) ?? []
  const extraTagCount = (control.tags?.length ?? 0) - 2

  return (
    <div className="border-b border-border/40 last:border-b-0">
      {/* Main row */}
      <div className="flex items-center hover:bg-muted/30 transition-colors">
        <div
          role="button"
          tabIndex={0}
          aria-expanded={open}
          onClick={() => setOpen(!open)}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault()
              setOpen((current) => !current)
            }
          }}
          className="flex items-center gap-3 flex-1 min-w-0 px-4 py-3 text-left"
        >
          {/* Index */}
          <span className="text-[11px] text-muted-foreground tabular-nums w-6 shrink-0 text-right">{index}</span>

          {/* Toggle */}
          <span className="text-muted-foreground shrink-0">
            {open
              ? <ChevronDown className="w-3.5 h-3.5" />
              : <ChevronRight className="w-3.5 h-3.5" />}
          </span>

          {/* Code */}
          <code className="text-[11px] font-mono text-muted-foreground shrink-0 w-20 truncate">
            {control.control_code}
          </code>

          {/* Name */}
          <span className="text-sm font-medium text-foreground truncate">
            {control.name || control.control_code}
          </span>

          {/* View button — right after name */}
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); router.push(`/controls/${frameworkId}/${control.id}`) }}
            className="shrink-0 flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium border border-border/50 text-muted-foreground hover:text-primary hover:border-primary/40 transition-colors"
          >
            <ExternalLink className="w-3 h-3" /> View
          </button>

          {/* Spacer */}
          <span className="flex-1" />

          {/* Owner icon */}
          {control.owner_user_id && (
            <span className="hidden sm:inline shrink-0" title={`Owner: ${control.owner_user_id}`}>
              <User className="w-3 h-3 text-muted-foreground" />
            </span>
          )}

          {/* Tags (up to 2 + overflow) */}
          {displayTags.length > 0 && (
            <div className="hidden md:flex items-center gap-1 shrink-0">
              {displayTags.map((tag, i) => (
                <span key={i} className="inline-flex items-center px-1 py-0 rounded text-[9px] bg-muted text-muted-foreground border border-border/60">
                  {tag}
                </span>
              ))}
              {extraTagCount > 0 && (
                <span className="text-[9px] text-muted-foreground">+{extraTagCount}</span>
              )}
            </div>
          )}

          {/* Requirement group badge */}
          {groupLabel && (
            <span className="hidden sm:inline text-[10px] text-muted-foreground truncate max-w-[100px]">
              {groupLabel}
            </span>
          )}

          {/* Criticality */}
          <Chip
            label={control.criticality_code}
            className={CRITICALITY_COLORS[control.criticality_code] ?? "bg-muted text-muted-foreground border-border"}
          />

          {/* Type */}
          <span className={`hidden md:inline-flex items-center px-1.5 py-0 rounded text-[10px] font-medium ${CONTROL_TYPE_COLORS[control.control_type] ?? "bg-muted text-muted-foreground"}`}>
            {control.control_type}
          </span>

          {/* Automation potential */}
          <Chip
            label={control.automation_potential}
            className={`hidden lg:inline-flex ${AUTOMATION_COLORS[control.automation_potential] ?? "bg-muted text-muted-foreground border-border"}`}
          />

          {/* Tests count — orange/amber with warning if 0 */}
          <span className={`hidden sm:flex items-center gap-1 text-[11px] shrink-0 ${hasNoTests ? "text-amber-500" : "text-muted-foreground"}`}>
            {hasNoTests && <AlertTriangle className="w-3 h-3 text-amber-500" />}
            <FlaskConical className="w-3 h-3" />
            {control.test_count ?? 0}
          </span>
        </div>
      </div>

      {/* Expanded detail */}
      {open && (
        <ControlRowExpandedPanel
          control={control}
          frameworkId={frameworkId}
          orgMembers={orgMembers}
          orgGroups={orgGroups}
          defaultOrgId={defaultOrgId}
          defaultWorkspaceId={defaultWorkspaceId}
          onUpdated={onUpdated}
        />
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Requirement group (for grouped view)
// ─────────────────────────────────────────────────────────────────────────────

function RequirementGroup({
  req,
  controls,
  search,
  startIndex,
  frameworkId,
  orgMembers,
  orgGroups,
  defaultOrgId,
  defaultWorkspaceId,
  onUpdated,
}: {
  req: RequirementResponse | null  // null = "Ungrouped"
  controls: ControlResponse[]
  search: string
  startIndex: number
  frameworkId: string
  orgMembers: OrgMemberResponse[]
  orgGroups: OrgGroup[]
  defaultOrgId: string
  defaultWorkspaceId: string
  onUpdated: () => void
}) {
  const [collapsed, setCollapsed] = useState(false)
  const [visible, setVisible] = useState(PAGE_SIZE)

  const filtered = search
    ? controls.filter((c) =>
        c.name?.toLowerCase().includes(search) ||
        c.control_code.toLowerCase().includes(search))
    : controls

  const shown = filtered.slice(0, visible)

  return (
    <div className="mb-2">
      {/* Group header */}
      <button
        type="button"
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center gap-2 w-full px-4 py-2 text-left bg-muted/40 hover:bg-muted/60 transition-colors rounded-lg group"
      >
        <span className="text-muted-foreground shrink-0">
          {collapsed ? <ChevronRight className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </span>
        {req ? (
          <>
            <BookOpen className="w-3.5 h-3.5 text-purple-500 shrink-0" />
            <span className="text-xs font-semibold text-foreground">
              {req.name || req.requirement_code}
            </span>
            <code className="text-[10px] font-mono text-muted-foreground">{req.requirement_code}</code>
          </>
        ) : (
          <>
            <Layers className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
            <span className="text-xs font-semibold text-muted-foreground">Ungrouped</span>
          </>
        )}
        <span className="ml-auto text-[10px] text-muted-foreground tabular-nums">
          {filtered.length} control{filtered.length !== 1 ? "s" : ""}
        </span>
      </button>

      {/* Controls */}
      {!collapsed && (
        <div className="mt-1 rounded-lg border border-border/50 overflow-hidden">
          {shown.length === 0 ? (
            <p className="px-4 py-3 text-xs text-muted-foreground">No controls.</p>
          ) : (
            <>
              {shown.map((ctrl, idx) => (
                <ControlRow
                  key={ctrl.id}
                  control={ctrl}
                  index={startIndex + idx + 1}
                  frameworkId={frameworkId}
                  groupLabel={req?.name}
                  orgMembers={orgMembers}
                  orgGroups={orgGroups}
                  defaultOrgId={defaultOrgId}
                  defaultWorkspaceId={defaultWorkspaceId}
                  onUpdated={onUpdated}
                />
              ))}
              {visible < filtered.length && (
                <button
                  type="button"
                  onClick={() => setVisible((v) => v + PAGE_SIZE)}
                  className="flex items-center justify-center gap-2 w-full px-4 py-2 text-xs text-primary hover:bg-muted/30 transition-colors border-t border-border/40"
                >
                  <Plus className="w-3 h-3" />
                  Show {Math.min(PAGE_SIZE, filtered.length - visible)} more ({filtered.length - visible} remaining)
                </button>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Add Control Dialog (inline)
// ─────────────────────────────────────────────────────────────────────────────

// ─────────────────────────────────────────────────────────────────────────────
// Searchable combobox for owner / group selection
// ─────────────────────────────────────────────────────────────────────────────

function SearchCombobox({
  placeholder,
  value,
  options,
  getLabel,
  getId,
  onSelect,
  disabled,
}: {
  placeholder: string
  value: string
  options: unknown[]
  getLabel: (o: unknown) => string
  getId: (o: unknown) => string
  onSelect: (id: string) => void
  disabled?: boolean
}) {
  const [query, setQuery] = useState("")
  const [open, setOpen] = useState(false)

  const selected = options.find(o => getId(o) === value)
  const displayValue = selected ? getLabel(selected) : ""

  const filtered = query === ""
    ? options
    : options.filter(o => getLabel(o).toLowerCase().includes(query.toLowerCase()))

  function handleSelect(id: string) {
    onSelect(id)
    setQuery("")
    setOpen(false)
  }

  return (
    <div className="relative">
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
          <button
            type="button"
            className="absolute right-1.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground text-xs leading-none"
            onMouseDown={e => { e.preventDefault(); handleSelect("") }}
          >×</button>
        )}
      </div>
      {open && filtered.length > 0 && (
        <div className="absolute z-50 top-full left-0 right-0 mt-0.5 bg-popover border border-border rounded-md shadow-md max-h-48 overflow-y-auto">
          {filtered.map(o => (
            <button
              key={getId(o)}
              type="button"
              className={`w-full text-left px-3 py-1.5 text-sm hover:bg-accent ${getId(o) === value ? "bg-accent/50 font-medium" : ""}`}
              onMouseDown={e => { e.preventDefault(); handleSelect(getId(o)) }}
            >
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

function AddControlDialog({
  frameworkId,
  frameworkName,
  requirements,
  orgMembers,
  orgGroups,
  orgId,
  workspaceId,
  onCreated,
  onClose,
}: {
  frameworkId: string
  frameworkName?: string
  requirements: RequirementResponse[]
  orgMembers: OrgMemberResponse[]
  orgGroups: OrgGroup[]
  orgId?: string | null
  workspaceId?: string | null
  onCreated: () => void
  onClose: () => void
}) {
  const currentUserId = getJwtSubject()
  const [form, setForm] = useState({
    control_code: "",
    name: "",
    description: "",
    control_category_code: "access_control",
    criticality_code: "medium",
    requirement_id: "",
    owner_user_id: currentUserId ?? "",
    responsible_group_id: "",
    tags: "",
    implementation_guidance: "",
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")

  function handleAIFilled(fields: Record<string, string>) {
    setForm(prev => ({
      ...prev,
      ...(fields.name && { name: fields.name }),
      ...(fields.description && { description: fields.description }),
      ...(fields.control_code && { control_code: fields.control_code }),
      ...(fields.control_category_code && { control_category_code: fields.control_category_code }),
      ...(fields.criticality_code && { criticality_code: fields.criticality_code }),
      ...(fields.implementation_guidance && { implementation_guidance: Array.isArray(fields.implementation_guidance) ? (fields.implementation_guidance as unknown as string[]).join("\n") : fields.implementation_guidance }),
      ...(fields.tags && { tags: Array.isArray(fields.tags) ? (fields.tags as unknown as string[]).join(", ") : fields.tags }),
    }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.control_code || !form.name) { setError("Code and name are required"); return }
    setSaving(true); setError("")
    try {
      await createControl(frameworkId, {
        control_code: form.control_code,
        name: form.name,
        description: form.description || undefined,
        control_category_code: form.control_category_code,
        criticality_code: form.criticality_code,
        control_type: "preventive",
        automation_potential: "manual",
        requirement_id: form.requirement_id || undefined,
        owner_user_id: form.owner_user_id || undefined,
        responsible_teams: form.responsible_group_id ? [form.responsible_group_id] : undefined,
        tags: form.tags ? form.tags.split(",").map((t) => t.trim()).filter(Boolean) : undefined,
        implementation_guidance: form.implementation_guidance
          ? form.implementation_guidance.split("\n").map((l) => l.trim()).filter(Boolean)
          : undefined,
      })
      onCreated()
      onClose()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to create control")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-background rounded-xl border border-border shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-background border-b border-border px-5 py-4 flex items-center justify-between z-10">
          <h2 className="text-base font-semibold">Add Control</h2>
          <button type="button" onClick={onClose} className="text-muted-foreground hover:text-foreground text-lg leading-none">×</button>
        </div>
        <div className="px-5 pt-4">
          <FormFillChat
            entityType="control"
            orgId={orgId}
            workspaceId={workspaceId}
            pageContext={{ framework_id: frameworkId, framework_name: frameworkName }}
            getFormValues={() => ({
              name: form.name || undefined,
              description: form.description || undefined,
              control_code: form.control_code || undefined,
              control_category_code: form.control_category_code,
              criticality_code: form.criticality_code,
              implementation_guidance: form.implementation_guidance || undefined,
              tags: form.tags || undefined,
            })}
            onFilled={handleAIFilled}
          />
        </div>
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1">Code *</label>
              <Input
                placeholder="CC6-01"
                value={form.control_code}
                onChange={(e) => setForm({ ...form, control_code: e.target.value })}
                className="h-8 text-sm"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1">Requirement</label>
              <select
                value={form.requirement_id}
                onChange={(e) => setForm({ ...form, requirement_id: e.target.value })}
                className="w-full h-8 rounded-md border border-input bg-background text-sm px-2"
              >
                <option value="">None (ungrouped)</option>
                {requirements.map((r) => (
                  <option key={r.id} value={r.id}>{r.name || r.requirement_code}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="text-xs font-medium text-muted-foreground block mb-1">Name *</label>
            <Input
              placeholder="Control name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="h-8 text-sm"
            />
          </div>

          <div>
            <label className="text-xs font-medium text-muted-foreground block mb-1">Description</label>
            <textarea
              placeholder="Brief description of this control"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              rows={2}
              className="w-full rounded-md border border-input bg-background text-sm px-3 py-2 resize-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1">
                Owner <span className="text-destructive">*</span>
              </label>
              <SearchCombobox
                placeholder="Search by name or email…"
                value={form.owner_user_id}
                options={orgMembers as unknown[]}
                getId={o => (o as OrgMemberResponse).user_id}
                getLabel={o => {
                  const m = o as OrgMemberResponse
                  const name = m.display_name || ""
                  const email = m.email || ""
                  const you = m.user_id === currentUserId ? " (you)" : ""
                  return name && email ? `${name} — ${email}${you}` : (email || m.user_id) + you
                }}
                onSelect={id => setForm({ ...form, owner_user_id: id })}
              />
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1">
                Responsible Group <span className="text-muted-foreground/60">(optional)</span>
              </label>
              <SearchCombobox
                placeholder="Search groups…"
                value={form.responsible_group_id}
                options={orgGroups as unknown[]}
                getId={o => (o as { id: string }).id}
                getLabel={o => {
                  const g = o as { name: string; is_locked: boolean }
                  return g.is_locked ? `${g.name} 🔒` : g.name
                }}
                onSelect={id => setForm({ ...form, responsible_group_id: id })}
              />
              {form.responsible_group_id && (
                <p className="text-xs text-amber-600 mt-0.5">This group will be locked to this framework control.</p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1">Control Domain</label>
              <select
                value={form.control_category_code}
                onChange={(e) => setForm({ ...form, control_category_code: e.target.value })}
                className="w-full h-8 rounded-md border border-input bg-background text-sm px-2"
              >
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c.replace(/_/g, " ")}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1">Criticality</label>
              <select
                value={form.criticality_code}
                onChange={(e) => setForm({ ...form, criticality_code: e.target.value })}
                className="w-full h-8 rounded-md border border-input bg-background text-sm px-2"
              >
                {["critical","high","medium","low"].map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="text-xs font-medium text-muted-foreground block mb-1">
              Implementation Guidance <span className="font-normal">(one per line)</span>
            </label>
            <textarea
              placeholder={"Enforce MFA for all admin accounts\nLog all access attempts\nReview access quarterly"}
              value={form.implementation_guidance}
              onChange={(e) => setForm({ ...form, implementation_guidance: e.target.value })}
              rows={3}
              className="w-full rounded-md border border-input bg-background text-sm px-3 py-2 resize-none"
            />
          </div>

          <div>
            <label className="text-xs font-medium text-muted-foreground block mb-1">
              Tags <span className="font-normal">(comma-separated)</span>
            </label>
            <Input
              placeholder="iam, soc2, access-control"
              value={form.tags}
              onChange={(e) => setForm({ ...form, tags: e.target.value })}
              className="h-8 text-sm"
            />
          </div>

          {error && <p className="text-xs text-red-500">{error}</p>}

          <div className="flex items-center justify-end gap-2 pt-2">
            <Button type="button" variant="ghost" size="sm" onClick={onClose}>Cancel</Button>
            <Button type="submit" size="sm" disabled={saving}>
              {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : null}
              Add Control
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Add Requirement Dialog
// ─────────────────────────────────────────────────────────────────────────────

function AddRequirementDialog({
  frameworkId,
  requirements,
  orgId,
  workspaceId,
  onCreated,
  onClose,
}: {
  frameworkId: string
  requirements: RequirementResponse[]
  orgId?: string | null
  workspaceId?: string | null
  onCreated: () => void
  onClose: () => void
}) {
  const [form, setForm] = useState({
    requirement_code: "",
    name: "",
    description: "",
    parent_requirement_id: "",
    sort_order: "10",
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")

  function handleAIFilled(fields: Record<string, string>) {
    setForm(prev => ({
      ...prev,
      ...(fields.name && { name: fields.name }),
      ...(fields.description && { description: fields.description }),
      ...(fields.requirement_code && { requirement_code: fields.requirement_code }),
    }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.requirement_code || !form.name) { setError("Code and name are required"); return }
    setSaving(true); setError("")
    try {
      await createRequirement(frameworkId, {
        requirement_code: form.requirement_code,
        name: form.name,
        description: form.description || undefined,
        parent_requirement_id: form.parent_requirement_id || undefined,
        sort_order: parseInt(form.sort_order) || 10,
      })
      onCreated()
      onClose()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to create requirement")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-background rounded-xl border border-border shadow-2xl w-full max-w-md">
        <div className="border-b border-border px-5 py-4 flex items-center justify-between">
          <h2 className="text-base font-semibold">Add Requirement</h2>
          <button type="button" onClick={onClose} className="text-muted-foreground hover:text-foreground text-lg leading-none">×</button>
        </div>
        <div className="px-5 pt-4">
          <FormFillChat
            entityType="requirement"
            orgId={orgId}
            workspaceId={workspaceId}
            pageContext={{ framework_id: frameworkId }}
            getFormValues={() => ({
              name: form.name || undefined,
              description: form.description || undefined,
              requirement_code: form.requirement_code || undefined,
            })}
            onFilled={handleAIFilled}
          />
        </div>
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1">Code *</label>
              <Input
                placeholder="CC6"
                value={form.requirement_code}
                onChange={(e) => setForm({ ...form, requirement_code: e.target.value })}
                className="h-8 text-sm"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1">Sort Order</label>
              <Input
                type="number"
                value={form.sort_order}
                onChange={(e) => setForm({ ...form, sort_order: e.target.value })}
                className="h-8 text-sm"
              />
            </div>
          </div>
          <div>
            <label className="text-xs font-medium text-muted-foreground block mb-1">Name *</label>
            <Input
              placeholder="Access Controls"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="h-8 text-sm"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-muted-foreground block mb-1">Description</label>
            <textarea
              placeholder="Describe this requirement group"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              rows={2}
              className="w-full rounded-md border border-input bg-background text-sm px-3 py-2 resize-none"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-muted-foreground block mb-1">Parent Requirement</label>
            <select
              value={form.parent_requirement_id}
              onChange={(e) => setForm({ ...form, parent_requirement_id: e.target.value })}
              className="w-full h-8 rounded-md border border-input bg-background text-sm px-2"
            >
              <option value="">None (top-level)</option>
              {requirements.map((r) => (
                <option key={r.id} value={r.id}>{r.name || r.requirement_code}</option>
              ))}
            </select>
          </div>

          {error && <p className="text-xs text-red-500">{error}</p>}
          <div className="flex items-center justify-end gap-2 pt-2">
            <Button type="button" variant="ghost" size="sm" onClick={onClose}>Cancel</Button>
            <Button type="submit" size="sm" disabled={saving}>
              {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : null}
              Add Requirement
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Create Version Dialog
// ─────────────────────────────────────────────────────────────────────────────

function CreateVersionDialog({
  frameworkId, open, onCreate, onClose,
}: {
  frameworkId: string
  open: boolean
  onCreate: (frameworkId: string, p: CreateVersionRequest) => Promise<void>
  onClose: () => void
}) {
  const [versionCode, setVersionCode] = useState("")
  const [changeSeverity, setChangeSeverity] = useState("minor")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) { setVersionCode(""); setChangeSeverity("minor"); setSaving(false); setError(null) }
  }, [open])

  async function create() {
    setSaving(true); setError(null)
    try {
      await onCreate(frameworkId, { version_label: versionCode.trim() || undefined, change_severity: changeSeverity })
      onClose()
    } catch (e) { setError(e instanceof Error ? e.message : "Failed to create version"); setSaving(false) }
  }

  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-background rounded-xl border border-border shadow-2xl w-full max-w-sm">
        <div className="border-b border-border px-5 py-4 flex items-center justify-between">
          <h2 className="text-base font-semibold">New Version</h2>
          <button type="button" onClick={onClose} className="text-muted-foreground hover:text-foreground text-lg leading-none">×</button>
        </div>
        <div className="p-5 space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground block">Version Label <span className="text-muted-foreground/60">(optional)</span></label>
            <Input value={versionCode} onChange={(e) => setVersionCode(e.target.value)} placeholder="e.g. v2.0" className="h-9 text-sm font-mono" />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground block">Change Severity</label>
            <select className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={changeSeverity} onChange={(e) => setChangeSeverity(e.target.value)}>
              {["patch", "minor", "major"].map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          {error && <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500">{error}</p>}
          <div className="flex items-center justify-end gap-2 pt-1">
            <Button variant="ghost" size="sm" onClick={onClose} disabled={saving}>Cancel</Button>
            <Button size="sm" onClick={create} disabled={saving}>
              {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : null}
              Create Version
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Versions Panel
// ─────────────────────────────────────────────────────────────────────────────

function VersionsPanel({ frameworkId, onReload }: { frameworkId: string; onReload: () => void }) {
  const [versions, setVersions] = useState<VersionResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [publishing, setPublishing] = useState<string | null>(null)

  const loadVersions = useCallback(async () => {
    setLoading(true)
    try {
      const res = await listVersions(frameworkId)
      setVersions(res.items ?? [])
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
    setPublishing(versionId)
    try {
      await publishVersion(frameworkId, versionId)
      await loadVersions()
      onReload()
    } catch { /* graceful */ }
    finally { setPublishing(null) }
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Versions</p>
        <Button size="sm" variant="ghost" className="h-6 text-xs gap-1" onClick={() => setShowCreate(true)}>
          <Plus className="h-3 w-3" /> Add
        </Button>
      </div>
      {loading ? (
        <div className="h-8 rounded bg-muted animate-pulse" />
      ) : versions.length === 0 ? (
        <p className="text-xs text-muted-foreground">No versions yet.</p>
      ) : (
        <div className="space-y-1">
          {versions.map((v) => (
            <div key={v.id} className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-muted/30 text-xs">
              <GitBranch className="h-3 w-3 text-muted-foreground shrink-0" />
              <code className="font-mono font-medium">{v.version_code}</code>
              <Badge variant="outline" className={`text-[10px] ${VERSION_STYLES[v.lifecycle_state] ?? ""}`}>
                {v.lifecycle_state}
              </Badge>
              <span className="text-muted-foreground">{v.change_severity}</span>
              <span className="text-muted-foreground ml-auto">{v.control_count} ctrl</span>
              {v.lifecycle_state === "draft" && (
                <Button size="sm" variant="ghost" className="h-5 text-[10px] px-1.5" onClick={() => handlePublish(v.id)} disabled={publishing === v.id}>
                  <Upload className="h-2.5 w-2.5 mr-0.5" />
                  {publishing === v.id ? "..." : "Publish"}
                </Button>
              )}
            </div>
          ))}
        </div>
      )}
      <CreateVersionDialog frameworkId={frameworkId} open={showCreate} onCreate={handleCreate} onClose={() => setShowCreate(false)} />
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Stat pill
// ─────────────────────────────────────────────────────────────────────────────

function StatPill({ icon, value, label, valueClassName }: { icon: React.ReactNode; value: number | string; label: string; valueClassName?: string }) {
  return (
    <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-muted/50 border border-border">
      {icon}
      <span className={`text-sm font-bold tabular-nums ${valueClassName ?? ""}`}>{value}</span>
      <span className="text-[10px] text-muted-foreground uppercase tracking-wider">{label}</span>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Filter bar for controls tab
// ─────────────────────────────────────────────────────────────────────────────

type FilterState = {
  criticality: string
  controlType: string
  automation: string
  gapsOnly: boolean
}

// ─────────────────────────────────────────────────────────────────────────────
// Filter Glossary Popover — explains each tag category in plain English
// ─────────────────────────────────────────────────────────────────────────────

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
      { label: "Compensating", desc: "A workaround when the ideal control isn't possible." },
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
  const btnRef = useRef<HTMLButtonElement>(null)
  const panelRef = useRef<HTMLDivElement>(null)
  const [pos, setPos] = useState({ top: 0, left: 0 })

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
        id="filter-glossary-btn"
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

function ControlFilterBar({
  filters,
  onChange,
  gapCount,
}: {
  filters: FilterState
  onChange: (f: FilterState) => void
  gapCount: number
}) {
  return (
    <div className="flex items-center gap-2 flex-wrap text-xs">
      <div className="flex items-center gap-1 text-muted-foreground">
        <Filter className="w-3 h-3" />
        <span>Filter:</span>
        <FilterGlossaryPopover />
      </div>

      {/* Criticality */}
      <div className="flex items-center rounded border border-border/60 overflow-hidden bg-muted/20">
        {["", "critical", "high", "medium", "low"].map(v => (
          <button
            key={v || "all"}
            type="button"
            onClick={() => onChange({ ...filters, criticality: v })}
            className={`px-2 py-1 text-[11px] transition-colors ${
              filters.criticality === v
                ? "bg-background text-foreground font-semibold shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {v === "" ? "All" : v.charAt(0).toUpperCase() + v.slice(1)}
          </button>
        ))}
      </div>

      {/* Type */}
      <div className="flex items-center rounded border border-border/60 overflow-hidden bg-muted/20">
        {["", "preventive", "detective", "corrective", "compensating"].map(v => (
          <button
            key={v || "all"}
            type="button"
            onClick={() => onChange({ ...filters, controlType: v })}
            className={`px-2 py-1 text-[11px] transition-colors ${
              filters.controlType === v
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
            key={v || "all"}
            type="button"
            onClick={() => onChange({ ...filters, automation: v })}
            className={`px-2 py-1 text-[11px] transition-colors ${
              filters.automation === v
                ? "bg-background text-foreground font-semibold shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {v === "" ? "All" : v.charAt(0).toUpperCase() + v.slice(1)}
          </button>
        ))}
      </div>

      {/* Gaps only toggle */}
      <button
        type="button"
        onClick={() => onChange({ ...filters, gapsOnly: !filters.gapsOnly })}
        className={`flex items-center gap-1.5 px-2.5 py-1 rounded border text-[11px] transition-colors ${
          filters.gapsOnly
            ? "border-amber-500/60 bg-amber-500/10 text-amber-600 font-semibold"
            : "border-border/60 bg-muted/20 text-muted-foreground hover:text-foreground"
        }`}
      >
        <AlertTriangle className="w-3 h-3" />
        Gaps only {gapCount > 0 && <span className="ml-0.5">({gapCount})</span>}
      </button>

      {/* Clear all */}
      {(filters.criticality || filters.controlType || filters.automation || filters.gapsOnly) && (
        <button
          type="button"
          onClick={() => onChange({ criticality: "", controlType: "", automation: "", gapsOnly: false })}
          className="flex items-center gap-1 px-2 py-1 text-[11px] text-muted-foreground hover:text-foreground transition-colors"
        >
          <X className="w-3 h-3" /> Clear
        </button>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Spreadsheet inline-edit cell components
// ─────────────────────────────────────────────────────────────────────────────

function SheetCell({ value, editable, onSave, className, children }: {
  value?: string; editable?: boolean; onSave?: (v: string) => void; className?: string; children?: React.ReactNode
}) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(value ?? "")
  const ref = useRef<HTMLInputElement>(null)
  useEffect(() => { if (editing && ref.current) { ref.current.focus(); ref.current.select() } }, [editing])
  // Sync draft when value changes externally
  useEffect(() => { if (!editing) setDraft(value ?? "") }, [value, editing])
  if (children) return <td className={className}>{children}</td>
  if (!editable) return <td className={className}><span className="block truncate">{value ?? "—"}</span></td>
  if (editing) return (
    <td className={`${className} p-0`}>
      <input
        ref={ref}
        value={draft}
        onChange={e => setDraft(e.target.value)}
        onBlur={() => { setEditing(false); if (draft.trim() && draft !== (value ?? "")) onSave?.(draft.trim()) }}
        onKeyDown={e => { if (e.key === "Enter") { e.preventDefault(); (e.target as HTMLInputElement).blur() } if (e.key === "Escape") { setDraft(value ?? ""); setEditing(false) } }}
        className="w-full h-full border-0 outline-none bg-white dark:bg-zinc-900 text-xs px-2 py-1.5 ring-2 ring-primary ring-inset rounded-none"
      />
    </td>
  )
  return (
    <td
      className={`${className} cursor-pointer hover:bg-primary/5`}
      onClick={() => { setDraft(value ?? ""); setEditing(true) }}
    >
      <span className="block truncate">{value || "—"}</span>
    </td>
  )
}

function SheetSelect({ value, options, onSave, className, renderBadge }: {
  value?: string; options: { value: string; label: string }[]; onSave: (v: string) => void; className?: string
  renderBadge?: (val: string) => React.ReactNode
}) {
  const [editing, setEditing] = useState(false)
  const ref = useRef<HTMLSelectElement>(null)
  useEffect(() => { if (editing && ref.current) ref.current.focus() }, [editing])
  if (editing) return (
    <td className={`${className} p-0`}>
      <select
        ref={ref}
        value={value ?? ""}
        onChange={e => { onSave(e.target.value); setEditing(false) }}
        onBlur={() => setEditing(false)}
        className="w-full h-full border-0 outline-none bg-white dark:bg-zinc-900 text-xs px-1.5 py-1.5 ring-2 ring-primary ring-inset rounded-none"
        autoFocus
      >
        <option value="">— select —</option>
        {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </td>
  )
  return (
    <td className={`${className} cursor-pointer hover:bg-primary/5`} onClick={() => setEditing(true)}>
      {value && renderBadge ? renderBadge(value) : <span className="text-muted-foreground/50">—</span>}
    </td>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Main page
// ─────────────────────────────────────────────────────────────────────────────

// ── Simple Report Viewer Modal ──────────────────────────────────────────────

function FrameworkReportViewer({ reportId, onClose }: { reportId: string; onClose: () => void }) {
  const [report, setReport] = useState<ReportResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const pollRef = useRef<NodeJS.Timeout | null>(null)
  const IN_PROGRESS = new Set(["queued", "planning", "collecting", "analyzing", "writing", "formatting"])

  const load = useCallback(async () => {
    try {
      const r = await getReport(reportId)
      setReport(r)
      if (IN_PROGRESS.has(r.status_code)) pollRef.current = setTimeout(load, 3000)
    } catch { /* ignore */ }
    finally { setLoading(false) }
  }, [reportId])

  useEffect(() => { load(); return () => { if (pollRef.current) clearTimeout(pollRef.current) } }, [load])

  useEffect(() => {
    const main = document.querySelector("main")
    if (main) main.style.overflow = "hidden"
    return () => { if (main) main.style.overflow = "" }
  }, [])

  async function handleDownload(fmt: string) {
    try { await downloadReport(reportId, fmt) } catch (e: any) { alert(e.message || "Download failed") }
  }

  const isCompleted = report?.status_code === "completed"

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-6"
      onClick={e => { if (e.target === e.currentTarget) onClose() }}
    >
      <div className="bg-card border border-border rounded-2xl w-full max-w-5xl shadow-2xl flex flex-col overflow-hidden mx-auto" style={{ height: "90vh" }}>
        <div className="flex items-center justify-between border-b border-border px-5 py-3.5 shrink-0">
          <div className="min-w-0">
            <h2 className="text-sm font-semibold truncate">
              {report?.title || REPORT_TYPE_LABELS[report?.report_type ?? ""] || "Report"}
            </h2>
            <span className={`text-[11px] capitalize ${
              report?.status_code === "completed" ? "text-green-500" :
              report?.status_code === "failed" ? "text-red-500" : "text-blue-500"
            }`}>
              {report?.status_code ?? "loading"}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {isCompleted && (
              <button
                onClick={() => handleDownload("pdf")}
                className="flex h-7 items-center gap-1.5 rounded-lg border border-input px-2.5 text-[11px] font-medium text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
              >
                <Download className="w-3 h-3" /> PDF
              </button>
            )}
            <button onClick={onClose} className="text-muted-foreground hover:text-foreground text-lg leading-none p-1">×</button>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-5">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
            </div>
          ) : !isCompleted ? (
            <div className="flex flex-col items-center justify-center py-20 gap-3 text-muted-foreground">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <p className="text-sm">Generating report...</p>
              <p className="text-xs">This may take a minute.</p>
            </div>
          ) : (
            <MarkdownRenderer content={report?.content_markdown ?? ""} />
          )}
        </div>
      </div>
    </div>
  )
}

// ── Framework Tasks Panel ───────────────────────────────────────────────────

function AuditPrepPanel({
  frameworkId,
  frameworkName,
  orgId,
  workspaceId,
  onViewReport,
}: {
  frameworkId: string
  frameworkName: string
  orgId: string
  workspaceId: string
  onViewReport: (reportId: string) => void
}) {
  const [readiness, setReadiness] = useState<AuditReadinessResponse | null>(null)
  const [reports, setReports] = useState<ReportSummaryResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [r, rl] = await Promise.all([
        getAuditReadiness(frameworkId, orgId).catch(() => null),
        getFrameworkReports(frameworkId).catch(() => ({ items: [], total: 0 })),
      ])
      setReadiness(r)
      setReports(rl.items ?? [])
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load audit data")
    } finally {
      setLoading(false)
    }
  }, [frameworkId, orgId])

  useEffect(() => { loadData() }, [loadData])

  async function handleGenerateReport() {
    setGenerating(true)
    setError(null)
    try {
      const report = await generateReport({
        report_type: "framework_compliance",
        title: `${frameworkName || "Framework"} — Audit Readiness Report`,
        org_id: orgId,
        workspace_id: workspaceId || undefined,
        parameters: { framework_id: frameworkId },
      })
      onViewReport(report.id)
      // Refresh reports list
      const rl = await getFrameworkReports(frameworkId)
      setReports(rl.items ?? [])
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to generate report")
    } finally {
      setGenerating(false)
    }
  }

  if (loading) {
    return (
      <Card className="rounded-xl">
        <CardContent className="px-5 py-8 flex flex-col items-center justify-center text-muted-foreground">
          <Loader2 className="h-6 w-6 mb-2 animate-spin text-primary" />
          <p className="text-sm">Loading audit readiness...</p>
        </CardContent>
      </Card>
    )
  }

  const pct = readiness?.readiness_pct ?? 0
  const pctColor = pct >= 90 ? "#10b981" : pct >= 60 ? "#3b82f6" : pct >= 30 ? "#eab308" : "#ef4444"

  return (
    <div className="space-y-4">
      {/* Audit Readiness Card */}
      <div className="rounded-2xl border border-border bg-card p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2.5">
            <div className="rounded-lg bg-primary/10 p-2">
              <ClipboardCheck className="w-4 h-4 text-primary" />
            </div>
            <div>
              <h3 className="text-sm font-semibold tracking-tight">Audit Readiness</h3>
              <p className="text-[11px] text-muted-foreground mt-0.5">Framework compliance overview</p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleGenerateReport}
            disabled={generating}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-primary text-primary-foreground text-[11px] font-semibold hover:bg-primary/90 shadow-lg shadow-primary/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-xl hover:shadow-primary/30 hover:-translate-y-0.5 active:translate-y-0"
          >
            {generating ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                Generate readiness report
              </>
            )}
          </button>
        </div>

        {/* Body */}
        <div className="flex items-center gap-15">
          {/* Circular progress ring */}
          <div className="relative shrink-0" style={{ width: 180, height: 180 }}>
            {/* Glow effect */}
            <div
              className="absolute inset-0 rounded-full opacity-20 blur-xl"
              style={{ backgroundColor: pctColor }}
            />
            <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90 relative">
              {/* Track */}
              <circle cx="50" cy="50" r="42" fill="none" stroke="currentColor" strokeWidth="5" className="text-muted/10" />
              {/* Progress */}
              <circle
                cx="50" cy="50" r="42"
                fill="none"
                stroke={pctColor}
                strokeWidth="5"
                strokeLinecap="round"
                strokeDasharray={`${pct * 2.639} 263.9`}
                className="transition-all duration-1000 ease-out"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center pl-4">
              <span className="text-5xl font-bold tabular-nums leading-none" style={{ color: pctColor }}>
                {Math.round(pct)}
              </span>
              <span className="text-[10px] text-muted-foreground uppercase tracking-[0.2em] font-semibold mt-1">ready</span>
            </div>
          </div>

          {/* Metrics */}
          <div className="flex-1 grid grid-cols-2 gap-3">
            {/* Controls passing */}
            <div className="rounded-lg bg-card/60 border border-border/50 p-2.5">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] text-muted-foreground font-medium">Controls passing</span>
                <div className={`w-1.5 h-1.5 rounded-full ${readiness?.controls_passing.passed === readiness?.controls_passing.total ? "bg-green-500" : "bg-orange-500"}`} />
              </div>
              <div className="flex items-baseline gap-0.5">
                <span className={`text-xl font-bold tabular-nums ${readiness?.controls_passing.passed === readiness?.controls_passing.total ? "text-green-500" : "text-orange-500"}`}>
                  {readiness?.controls_passing.passed ?? 0}
                </span>
                <span className="text-[10px] text-muted-foreground">/ {readiness?.controls_passing.total ?? 0}</span>
              </div>
              {/* Mini progress bar */}
              <div className="mt-1.5 h-0.5 rounded-full bg-muted/50 overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{
                    width: `${readiness?.controls_passing.total ? (readiness.controls_passing.passed / readiness.controls_passing.total * 100) : 0}%`,
                    backgroundColor: readiness?.controls_passing.passed === readiness?.controls_passing.total ? "#10b981" : "#f59e0b",
                  }}
                />
              </div>
            </div>

            {/* Evidence complete */}
            <div className="rounded-lg bg-card/60 border border-border/50 p-2.5">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] text-muted-foreground font-medium">Evidence complete</span>
                <div className={`w-1.5 h-1.5 rounded-full ${readiness?.evidence_complete.complete === readiness?.evidence_complete.total ? "bg-green-500" : readiness && readiness.evidence_complete.total > 0 ? "bg-orange-500" : "bg-muted-foreground/30"}`} />
              </div>
              <div className="flex items-baseline gap-0.5">
                <span className={`text-xl font-bold tabular-nums ${readiness?.evidence_complete.complete === readiness?.evidence_complete.total ? "text-green-500" : readiness && readiness.evidence_complete.total > 0 ? "text-orange-500" : "text-muted-foreground"}`}>
                  {readiness?.evidence_complete.complete ?? 0}
                </span>
                <span className="text-[10px] text-muted-foreground">/ {readiness?.evidence_complete.total ?? 0}</span>
              </div>
              <div className="mt-1.5 h-0.5 rounded-full bg-muted/50 overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{
                    width: `${readiness?.evidence_complete.total ? (readiness.evidence_complete.complete / readiness.evidence_complete.total * 100) : 0}%`,
                    backgroundColor: readiness?.evidence_complete.complete === readiness?.evidence_complete.total ? "#10b981" : "#f59e0b",
                  }}
                />
              </div>
            </div>

            {/* Open gaps */}
            <div className="rounded-lg bg-card/60 border border-border/50 p-2.5">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] text-muted-foreground font-medium">Open gaps</span>
                <div className={`w-1.5 h-1.5 rounded-full ${(readiness?.open_gaps ?? 0) > 0 ? "bg-red-500 animate-pulse" : "bg-green-500"}`} />
              </div>
              <div className="flex items-baseline gap-0.5">
                <span className={`text-xl font-bold tabular-nums ${(readiness?.open_gaps ?? 0) > 0 ? "text-red-500" : "text-green-500"}`}>
                  {readiness?.open_gaps ?? 0}
                </span>
                <span className="text-[10px] text-muted-foreground">gaps</span>
              </div>
            </div>

            {/* Auditor access */}
            <div className="rounded-lg bg-card/60 border border-border/50 p-2.5">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] text-muted-foreground font-medium">Auditor access</span>
                <div className={`w-1.5 h-1.5 rounded-full ${readiness?.auditor_access === "Active" ? "bg-green-500" : "bg-muted-foreground/30"}`} />
              </div>
              <div className="flex items-center gap-1.5">
                <span className={`text-base font-bold ${readiness?.auditor_access === "Active" ? "text-green-500" : "text-muted-foreground"}`}>
                  {readiness?.auditor_access ?? "Inactive"}
                </span>
              </div>
            </div>
          </div>
        </div>

        {error && (
          <div className="mt-4 rounded-lg bg-red-500/10 border border-red-500/20 px-3 py-2">
            <p className="text-xs text-red-500">{error}</p>
          </div>
        )}
      </div>

      {/* Framework Reports List */}
      <div className="rounded-2xl border border-border bg-card p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2.5">
            <div className="rounded-lg bg-blue-500/10 p-2">
              <FileText className="w-4 h-4 text-blue-500" />
            </div>
            <div>
              <h3 className="text-sm font-semibold tracking-tight">Reports</h3>
              <p className="text-[11px] text-muted-foreground mt-0.5">{reports.length} report{reports.length !== 1 ? "s" : ""} generated</p>
            </div>
          </div>
        </div>

        {reports.length === 0 ? (
          <div className="py-10 text-center rounded-xl border border-dashed border-border">
            <FileText className="w-10 h-10 text-muted-foreground/20 mx-auto mb-3" />
            <p className="text-sm font-medium text-muted-foreground">No reports yet</p>
            <p className="text-xs text-muted-foreground/70 mt-1">Generate your first audit readiness report above</p>
          </div>
        ) : (
          <div className="space-y-2">
            {reports.map((r) => {
              const statusDot: Record<string, string> = {
                completed: "bg-green-500",
                failed: "bg-red-500",
                queued: "bg-muted-foreground/30",
                planning: "bg-blue-500 animate-pulse",
                collecting: "bg-blue-500 animate-pulse",
                analyzing: "bg-blue-500 animate-pulse",
                writing: "bg-blue-500 animate-pulse",
                formatting: "bg-blue-500 animate-pulse",
              }
              const statusLabel: Record<string, string> = {
                completed: "Completed",
                failed: "Failed",
                queued: "Queued",
                planning: "Planning",
                collecting: "Collecting",
                analyzing: "Analyzing",
                writing: "Writing",
                formatting: "Formatting",
              }
              return (
                <button
                  key={r.id}
                  type="button"
                  onClick={() => onViewReport(r.id)}
                  className="w-full flex items-center gap-3.5 px-4 py-3.5 rounded-xl border border-border/50 hover:border-border hover:bg-muted/30 transition-all text-left group"
                >
                  <div className={`w-2 h-2 rounded-full shrink-0 ${statusDot[r.status_code] ?? "bg-muted-foreground/30"}`} />
                  <div className="flex-1 min-w-0">
                    <span className="text-[13px] font-medium text-foreground truncate block">
                      {r.title || REPORT_TYPE_LABELS[r.report_type] || r.report_type}
                    </span>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[10px] text-muted-foreground/80">
                        {statusLabel[r.status_code] ?? r.status_code}
                      </span>
                      <span className="text-[10px] text-muted-foreground/30">·</span>
                      <span className="text-[10px] text-muted-foreground/80">
                        {new Date(r.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                      </span>
                      {r.word_count != null && (
                        <>
                          <span className="text-[10px] text-muted-foreground/30">·</span>
                          <span className="text-[10px] text-muted-foreground/80">{r.word_count.toLocaleString()} words</span>
                        </>
                      )}
                    </div>
                  </div>
                  <ExternalLink className="w-4 h-4 text-muted-foreground/0 group-hover:text-muted-foreground transition-all shrink-0 group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                </button>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

function FrameworkTasksPanel({
  frameworkId,
  orgId,
  workspaceId,
}: {
  frameworkId: string
  orgId?: string
  workspaceId?: string
}) {
  const router = useRouter()
  const [tasks, setTasks] = useState<TaskResponse[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)

  const loadTasks = useCallback(async (currentOffset = 0) => {
    if (currentOffset === 0) setLoading(true)
    else setLoadingMore(true)
    
    try {
      const res = await listTasks({
        orgId,
        workspaceId,
        entity_type: "framework",
        entity_id: frameworkId,
        limit: 100,
        offset: currentOffset,
      })
      if (currentOffset === 0) {
        setTasks(res.items ?? [])
      } else {
        setTasks(prev => [...prev, ...(res.items ?? [])])
      }
      setTotal(res.total ?? 0)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }, [frameworkId, orgId, workspaceId])

  useEffect(() => { loadTasks(0) }, [loadTasks])

  if (loading) {
    return (
      <Card className="rounded-xl mt-4">
        <CardContent className="px-5 py-8 flex flex-col items-center justify-center text-muted-foreground">
          <Loader2 className="h-6 w-6 mb-2 animate-spin text-primary" />
          <p className="text-sm">Loading tasks...</p>
        </CardContent>
      </Card>
    )
  }

  if (tasks.length === 0) {
    return (
      <Card className="rounded-xl mt-4">
        <CardContent className="px-5 py-8 flex flex-col items-center justify-center text-muted-foreground">
          <ListTodo className="h-10 w-10 mb-3 opacity-20" />
          <p className="text-sm font-medium">No tasks found</p>
          <p className="text-xs mt-1">There are no framework-level tasks associated with this framework.</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-2 mt-4">
      <div className="flex items-center justify-between mb-4 px-1">
        <div>
          <h3 className="text-sm font-semibold tracking-tight">Framework Tasks</h3>
          <p className="text-xs text-muted-foreground">Tasks assigned directly to this framework.</p>
        </div>
        <div className="text-xs text-muted-foreground">
          {total} {total === 1 ? 'task' : 'tasks'} total
        </div>
      </div>
      
      <div className="rounded-lg border border-border/50 bg-card overflow-hidden">
        <table className="w-full text-left text-xs">
          <thead className="bg-muted/30 border-b border-border/50 text-muted-foreground uppercase tracking-wider">
            <tr>
              <th className="px-4 py-2 font-medium">Task</th>
              <th className="px-4 py-2 font-medium">Type</th>
              <th className="px-4 py-2 font-medium">State</th>
              <th className="px-4 py-2 font-medium">Due</th>
              <th className="px-4 py-2 font-medium w-16 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/30">
            {tasks.map(task => {
              const today = new Date().toISOString().split("T")[0]
              const isOverdue = task.due_date && task.due_date < today && !task.is_terminal
              return (
                <tr key={task.id} className="hover:bg-muted/10 transition-colors group">
                  <td className="px-4 py-2.5">
                    <div className="flex items-center gap-2">
                      <TaskStatusIcon status={task.status_code} />
                      <Chip
                        label={task.priority_code}
                        className={PRIORITY_COLORS[task.priority_code] ?? "bg-muted text-muted-foreground border-border"}
                      />
                      <span className="font-medium truncate max-w-sm">{task.title}</span>
                    </div>
                  </td>
                  <td className="px-4 py-2.5">
                    <span className="text-muted-foreground capitalize">{task.task_type_name ?? task.task_type_code}</span>
                  </td>
                  <td className="px-4 py-2.5">
                    <span className={`capitalize ${TASK_STATUS_STYLES[task.status_code] ?? ""}`}>{task.status_name}</span>
                  </td>
                  <td className="px-4 py-2.5">
                    {task.due_date ? (
                      <span className={`shrink-0 ${isOverdue ? "text-red-500 font-semibold" : "text-muted-foreground"}`}>
                        {new Date(task.due_date).toLocaleDateString()}
                        {isOverdue && " ⚠"}
                      </span>
                    ) : (
                      <span className="text-muted-foreground italic">None</span>
                    )}
                  </td>
                  <td className="px-4 py-2.5 text-right">
                    <button
                      type="button"
                      className="inline-flex items-center gap-1.5 text-sky-600 hover:text-sky-500 transition-colors"
                      onClick={(e) => { e.stopPropagation(); router.push(`/tasks/${task.id}`) }}
                      title="View task"
                    >
                      View
                    </button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {tasks.length < total && (
        <div className="flex justify-center pt-3 pb-2">
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => loadTasks(tasks.length)} 
            disabled={loadingMore}
            className="text-[11px] h-7 gap-1.5"
          >
            {loadingMore && <Loader2 className="w-3 h-3 animate-spin" />}
            Load more tasks ({tasks.length} of {total})
          </Button>
        </div>
      )}
    </div>
  )
}

export default function FrameworkDetailPage() {
  const params = useParams()
  const router = useRouter()
  const frameworkId = params.frameworkId as string
  const { selectedOrgId, selectedWorkspaceId, ready } = useOrgWorkspace()
  const { isWorkspaceAdmin, isSuperAdmin } = useAccess()

  const [framework, setFramework] = useState<FrameworkResponse | null>(null)
  const [requirements, setRequirements] = useState<RequirementResponse[]>([])
  const [controls, setControls] = useState<ControlResponse[]>([])
  const [versions, setVersions] = useState<VersionResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [orgMembers, setOrgMembers] = useState<OrgMemberResponse[]>([])
  const [orgGroups, setOrgGroups] = useState<OrgGroup[]>([])
  const defaultOrgId = selectedOrgId
  const defaultWorkspaceId = selectedWorkspaceId

  // Main tab
  const [mainTab, setMainTab] = useState<"controls" | "tasks" | "versions" | "comments" | "attachments" | "audit_prep">("controls")

  // Report viewer state
  const [viewReportId, setViewReportId] = useState<string | null>(null)

  // View mode: flat list OR grouped by requirements OR spreadsheet
  const [groupByReq, setGroupByReq] = useState(false)
  const [spreadsheetMode, setSpreadsheetMode] = useState(false)

  // Per-control tasks/risks for spreadsheet
  const [sheetTasks, setSheetTasks] = useState<Record<string, TaskResponse[]>>({})
  const [sheetRisks, setSheetRisks] = useState<Record<string, import("@/lib/types/grc").RiskResponse[]>>({})
  const [sheetLoading, setSheetLoading] = useState(false)
  const [expandedSheetRows, setExpandedSheetRows] = useState<Set<string>>(new Set())
  const [sheetSaveError, setSheetSaveError] = useState<string | null>(null)
  // Upload diff preview (controls CSV)
  const [uploadPreview, setUploadPreview] = useState<{ file: File; result: import("@/lib/types/grc").ImportControlsResult } | null>(null)
  const [uploadCommitting, setUploadCommitting] = useState(false)

  // Bundle export/import (full JSON)
  const [bundleExporting, setBundleExporting] = useState(false)
  const [bundlePreview, setBundlePreview] = useState<{ file: File; bundle: FrameworkBundle; result: BundleImportResult } | null>(null)
  const [bundleCommitting, setBundleCommitting] = useState(false)

  // Submit for review
  const [submittingForReview, setSubmittingForReview] = useState(false)

  // Pagination for flat list
  const [flatVisible, setFlatVisible] = useState(PAGE_SIZE)

  // Dialogs
  const [showAddControl, setShowAddControl] = useState(false)
  const [showAddReq, setShowAddReq] = useState(false)
  const [editItem, setEditItem] = useState<FrameworkResponse | null>(null)
  const [deleteItem, setDeleteItem] = useState<FrameworkResponse | null>(null)
  const [categories, setCategories] = useState<DimensionResponse[]>([])
  const [diff, setDiff] = useState<FrameworkDiff | null>(null)

  // Filters
  const [filters, setFilters] = useState<FilterState>({
    criticality: "",
    controlType: "",
    automation: "",
    gapsOnly: false,
  })

  const load = useCallback(async () => {
    setLoading(true); setError(null)
    try {
      const [fw, reqs, vers, ctrlRes, catRes, diffRes] = await Promise.all([
        getFramework(frameworkId),
        listRequirements(frameworkId),
        listVersions(frameworkId),
        listControls(frameworkId),
        listFrameworkCategories(),
        getFrameworkDiff(frameworkId).catch(() => null),
      ])
      setFramework(fw)
      setRequirements(reqs.items ?? [])
      setVersions(vers.items ?? [])
      setControls(ctrlRes.items ?? [])
      setCategories(catRes || [])
      setDiff(diffRes)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load framework")
    } finally {
      setLoading(false)
    }
  }, [frameworkId])

  useEffect(() => { load() }, [load])

  // Load all tasks+risks for all controls when spreadsheet mode activates
  useEffect(() => {
    if (!spreadsheetMode || controls.length === 0) return
    setSheetLoading(true)
    // Fetch all tasks for this framework's controls in one call
    const tasksPromise = listTasks({ entity_type: "control", limit: 2000 }).then(r => {
      const byControl: Record<string, TaskResponse[]> = {}
      for (const t of r.items ?? []) {
        if (t.entity_id) {
          if (!byControl[t.entity_id]) byControl[t.entity_id] = []
          byControl[t.entity_id].push(t)
        }
      }
      setSheetTasks(byControl)
    }).catch(() => {})

    // Fetch risks for each control (parallel, capped at 10 concurrent to avoid flooding)
    const risksPromise = (async () => {
      const byControl: Record<string, import("@/lib/types/grc").RiskResponse[]> = {}
      const { listRisks } = await import("@/lib/api/grc")
      // Batch: fetch risks for each control that has linked_control_count > 0
      // Since we don't have per-control count yet, we fetch for each control in parallel
      await Promise.all(
        controls.map(c =>
          listRisks({ control_id: c.id, limit: 100 }).then(r => {
            if (r.items && r.items.length > 0) byControl[c.id] = r.items
          }).catch(() => {})
        )
      )
      setSheetRisks(byControl)
    })()

    Promise.all([tasksPromise, risksPromise]).finally(() => setSheetLoading(false))
  }, [spreadsheetMode, controls.length])

  // defaultOrgId now comes from OrgWorkspaceContext (selectedOrgId)

  useEffect(() => {
    const scopeOrgId = framework?.scope_org_id
    if (!scopeOrgId) return
    import("@/lib/api/orgs").then(({ listOrgMembers }) =>
      listOrgMembers(scopeOrgId).then(m => setOrgMembers(m)).catch(() => {})
    )
    import("@/lib/api/admin").then(({ listGroups }) =>
      listGroups({ scope_org_id: scopeOrgId }).then(r => setOrgGroups((r.groups ?? []).map(g => ({ id: g.id, name: g.name, is_locked: g.is_locked })))).catch(() => {})
    )
  }, [framework?.scope_org_id])

  const searchLower = search.toLowerCase()

  // Filtered controls — apply search + filter bar
  const filteredControls = controls.filter((c) => {
    if (searchLower && !(
      c.name?.toLowerCase().includes(searchLower) ||
      c.control_code.toLowerCase().includes(searchLower) ||
      c.description?.toLowerCase().includes(searchLower)
    )) return false
    if (filters.criticality && c.criticality_code !== filters.criticality) return false
    if (filters.controlType && c.control_type !== filters.controlType) return false
    if (filters.automation && c.automation_potential !== filters.automation) return false
    if (filters.gapsOnly && (c.test_count ?? 0) > 0) return false
    return true
  })

  async function handleUpdate(id: string, payload: UpdateFrameworkRequest) {
    try {
      await updateFramework(id, payload)
      await load()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to update framework")
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteFramework(id)
      router.push("/frameworks")
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete framework")
    }
  }

  // Gap count (for badge on filter toggle)
  const gapCount = controls.filter(c => (c.test_count ?? 0) === 0).length

  // Coverage stat
  const coveredCount = controls.filter(c => (c.test_count ?? 0) > 0).length
  const coveragePct = controls.length > 0 ? Math.round((coveredCount / controls.length) * 100) : 0
  const coverageColor = coveragePct >= 80 ? "text-green-600" : coveragePct >= 50 ? "text-amber-500" : "text-red-500"

  // Flat view
  const flatVisible_controls = filteredControls.slice(0, flatVisible)

  // Spreadsheet rows (still used by EntitySpreadsheet, kept for export compat)
  const spreadsheetRows: ControlSpreadsheetRow[] = controls.map((c) => {
    const tCount = (sheetTasks[c.id] ?? []).length
    const rCount = (sheetRisks[c.id] ?? []).length
    return {
      id: c.id,
      control_code: c.control_code,
      name: c.name,
      description: c.description ?? "",
      control_type: c.control_type ?? "",
      criticality: c.criticality_code ?? "",
      automation_type: c.automation_potential ?? "",
      owner_name: c.owner_display_name ?? "",
      owner_email: c.owner_email ?? "",
      owner_user_id: c.owner_user_id ?? "",
      requirement_code: c.requirement_code ?? requirements.find(r => r.id === c.requirement_id)?.requirement_code ?? "",
      requirement_id: c.requirement_id ?? "",
      tags: Array.isArray(c.tags) ? c.tags.join(", ") : "",
      framework_code: framework?.framework_code ?? "",
      tasks_count: tCount > 0 ? `${tCount} task${tCount !== 1 ? "s" : ""}` : "",
      risks_count: rCount > 0 ? `${rCount} risk${rCount !== 1 ? "s" : ""}` : "",
    }
  })

  async function handleSpreadsheetSave(row: ControlSpreadsheetRow) {
    if (!row.id) return
    await updateControl(frameworkId, row.id, {
      name: row.name,
      description: row.description || undefined,
      control_type: row.control_type || undefined,
      criticality_code: row.criticality || undefined,
      automation_potential: row.automation_type || undefined,
    })
    await load()
  }

  async function handleSpreadsheetExport(format: "csv" | "json" | "xlsx") {
    const blob = await exportControls(frameworkId, format)
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `controls_${framework?.framework_code ?? frameworkId}_${new Date().toISOString().split("T")[0]}.${format}`
    a.click()
    URL.revokeObjectURL(url)
  }

  async function handleBundleExport() {
    setBundleExporting(true)
    try {
      const blob = await exportFrameworkBundle(frameworkId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `${framework?.framework_code ?? frameworkId}_bundle_${new Date().toISOString().split("T")[0]}.json`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      alert(err instanceof Error ? err.message : "Export failed")
    } finally {
      setBundleExporting(false)
    }
  }

  async function handleBundleFileSelect(file: File) {
    try {
      const text = await file.text()
      const bundle: FrameworkBundle = JSON.parse(text)
      const result = await importFrameworkBundle(bundle, { dryRun: true })
      setBundlePreview({ file, bundle, result })
    } catch (err) {
      alert(err instanceof Error ? err.message : "Invalid bundle file")
    }
  }

  async function handleBundleCommit() {
    if (!bundlePreview) return
    setBundleCommitting(true)
    try {
      await importFrameworkBundle(bundlePreview.bundle, { dryRun: false })
      setBundlePreview(null)
      await load()
    } catch (err) {
      alert(err instanceof Error ? err.message : "Import failed")
    } finally {
      setBundleCommitting(false)
    }
  }

  async function handleSubmitForReview() {
    if (!framework) return
    const isUpdate = framework.approval_status === "approved"
    const action = isUpdate ? "launch a new version" : "admin review"
    if (!confirm(`Submit "${framework.name}" for ${action}? It will be reviewed before appearing in the marketplace.`)) return
    setSubmittingForReview(true)
    try {
      const updated = await submitFrameworkForReview(frameworkId)
      setFramework(updated)
      await load()
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to submit for review")
    } finally {
      setSubmittingForReview(false)
    }
  }

  // Grouped view — build requirement → controls map
  const sortedReqs = [...requirements].sort((a, b) => a.sort_order - b.sort_order)
  const reqMap = new Map<string, RequirementResponse>(sortedReqs.map((r) => [r.id, r]))

  // Group controls by requirement_id
  const grouped = new Map<string | null, ControlResponse[]>()
  for (const ctrl of filteredControls) {
    const key = ctrl.requirement_id ?? null
    if (!grouped.has(key)) grouped.set(key, [])
    grouped.get(key)!.push(ctrl)
  }

  const publishedVersion = versions.find((v) => v.lifecycle_state === "published")

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-5 w-28 rounded bg-muted animate-pulse" />
        <div className="h-8 w-72 rounded bg-muted animate-pulse" />
        <div className="h-14 rounded-xl bg-muted animate-pulse" />
        <div className="space-y-1">
          {[1, 2, 3, 4, 5, 6].map((i) => <div key={i} className="h-11 rounded-lg bg-muted animate-pulse" />)}
        </div>
      </div>
    )
  }

  if (error || !framework) {
    return (
      <div className="space-y-4">
        <Button variant="ghost" size="sm" onClick={() => router.back()} className="gap-2">
          <ChevronLeft className="h-4 w-4" /> Back
        </Button>
        <Card className="rounded-xl">
          <CardContent className="flex flex-col items-center justify-center py-16 gap-3">
            <AlertTriangle className="h-8 w-8 text-red-500" />
            <p className="text-sm font-medium">{error || "Framework not found"}</p>
            <Button size="sm" onClick={load}>Retry</Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Count of groups that have controls (for grouped badge)
  let groupStartIndex = 0

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <Button
            variant="ghost" size="sm"
            onClick={() => router.back()}
            className="gap-1.5 -ml-2 h-7 text-xs text-muted-foreground"
          >
            <ChevronLeft className="h-3.5 w-3.5" /> Frameworks
          </Button>
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl font-bold tracking-tight font-secondary">{framework.name}</h1>
            {isSuperAdmin && (
              <Badge variant="outline" className="text-[10px] font-semibold capitalize">
                {framework.approval_status.replace(/_/g, " ")}
              </Badge>
            )}
          </div>
          <p className="text-xs text-muted-foreground">
            {framework.framework_code}
            {framework.type_name ? ` · ${framework.type_name}` : ""}
            {framework.category_name ? ` · ${framework.category_name}` : ""}
            {framework.publisher_name ? ` · ${framework.publisher_name}` : ""}
          </p>
          {framework.description && (
            <p className="text-xs text-muted-foreground max-w-2xl mt-0.5">{framework.description}</p>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {/* Task Builder */}
          <Button
            size="sm"
            variant="outline"
            className="gap-1.5 text-xs text-violet-600 border-violet-500/30 hover:bg-violet-500/10"
            onClick={() => router.push(`/frameworks/${frameworkId}/task-builder`)}
          >
            <ListTodo className="h-3.5 w-3.5" />
            Task Builder
          </Button>
          {/* Enhance with AI */}
          <Button
            size="sm"
            variant="outline"
            className="gap-1.5 text-xs"
            onClick={() => router.push(`/frameworks?tab=builder&builderTab=enhance&enhance=${frameworkId}`)}
          >
            <Sparkles className="h-3.5 w-3.5 text-amber-500" />
            Enhance with AI
          </Button>
          {/* View toggle */}
          {mainTab === "controls" && (
            <div className="flex items-center rounded-md border border-border bg-muted/30 p-0.5 gap-0.5">
              <button
                type="button"
                title="List view"
                onClick={() => setSpreadsheetMode(false)}
                className={`rounded p-1.5 transition-colors ${!spreadsheetMode ? "bg-muted text-foreground" : "text-muted-foreground hover:text-foreground hover:bg-muted/50"}`}
              >
                <LayoutList className="h-4 w-4" />
              </button>
              <button
                type="button"
                title="Spreadsheet view"
                onClick={() => setSpreadsheetMode(true)}
                className={`rounded p-1.5 transition-colors ${spreadsheetMode ? "bg-muted text-foreground" : "text-muted-foreground hover:text-foreground hover:bg-muted/50"}`}
              >
                <TableProperties className="h-4 w-4" />
              </button>
            </div>
          )}
          {/* Bundle export */}
          {/* 
          <button
            type="button"
            title="Export full framework bundle as JSON"
            onClick={handleBundleExport}
            disabled={bundleExporting}
            className="flex items-center gap-1.5 px-2 py-1.5 rounded text-xs text-muted-foreground hover:text-foreground hover:bg-muted transition-colors border border-border disabled:opacity-50"
          >
            {bundleExporting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Download className="h-3.5 w-3.5" />}
            Export JSON
          </button>
          */}
          {/* Bundle import */}
          {/*
          <label
            title="Import framework bundle JSON — preview before applying"
            className="flex items-center gap-1.5 px-2 py-1.5 rounded text-xs text-muted-foreground hover:text-foreground hover:bg-muted transition-colors border border-border cursor-pointer"
          >
            <Upload className="h-3.5 w-3.5" />
            Import JSON
            <input
              type="file"
              accept=".json"
              className="hidden"
              onChange={async (e) => {
                const file = e.target.files?.[0]
                if (!file) return
                e.target.value = ""
                await handleBundleFileSelect(file)
              }}
            />
          </label>
          */}
          {/* Submit to Library — normal users (draft or rejected) */}
          {!isSuperAdmin && (framework.approval_status === "draft" || framework.approval_status === "rejected") && (
            <Button
              size="sm"
              variant="outline"
              onClick={handleSubmitForReview}
              disabled={submittingForReview}
              className="gap-1.5 text-blue-600 border-blue-500/40 hover:bg-blue-500/10 hover:text-blue-700"
              title="Submit this framework to the platform library for review"
            >
              {submittingForReview ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <BookOpen className="h-3.5 w-3.5" />}
              Submit to Library
            </Button>
          )}
          {/* Submit for review — platform super admins only (draft / rejected) */}
          {isSuperAdmin && (framework.approval_status === "draft" || framework.approval_status === "rejected") && (
            <Button
              size="sm"
              variant="outline"
              onClick={handleSubmitForReview}
              disabled={submittingForReview}
              className="gap-1.5 text-amber-600 border-amber-500/40 hover:bg-amber-500/10 hover:text-amber-700"
              title="Submit this framework for admin review to publish it to the marketplace"
            >
              {submittingForReview ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
              Submit for Review
            </Button>
          )}
          {/* Pending review — platform super admins only */}
          {isSuperAdmin && framework.approval_status === "pending_review" && (
            <span className="flex items-center gap-1.5 px-2 py-1 rounded text-xs text-amber-600 border border-amber-500/30 bg-amber-500/5">
              <CheckCircle2 className="h-3.5 w-3.5" /> Pending Review
            </span>
          )}
          {/* Published — super admins only */}
          {isSuperAdmin && framework.approval_status === "approved" && (
            <span className="flex items-center gap-1.5 px-2 py-1 rounded text-xs text-green-600 border border-green-500/30 bg-green-500/5">
              <CheckCircle2 className="h-3.5 w-3.5" /> Published
            </span>
          )}
          {/* Launch New Version — super admins only (approved with pending changes) */}
          {isSuperAdmin && framework.approval_status === "approved" && (framework.has_pending_changes || (diff && (diff.controls_added > 0 || diff.controls_removed > 0 || diff.controls_modified > 0))) && (
            <Button
              size="sm"
              variant="outline"
              onClick={handleSubmitForReview}
              disabled={submittingForReview}
              className="gap-1.5 text-amber-600 border-amber-500/40 hover:bg-amber-500/10 hover:text-amber-700"
              title="Submit as new version for review"
            >
              {submittingForReview ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <RefreshCw className="h-3.5 w-3.5" />}
              Launch New Version
            </Button>
          )}
          <Button variant="outline" size="sm" onClick={load} className="gap-2">
            <RefreshCw className="h-3.5 w-3.5" /> Refresh
          </Button>
        </div>
      </div>

      {/* Bundle import diff preview */}
      {bundlePreview && (
        <div className="rounded-lg border border-border bg-amber-500/5 px-4 py-3 space-y-3">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Info className="h-4 w-4 text-amber-500 shrink-0" />
              <div>
                <span className="text-sm font-semibold">Preview import: {bundlePreview.file.name}</span>
                <span className="ml-2 text-xs text-muted-foreground">Review changes before applying</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setBundlePreview(null)}
                className="px-2 py-1 text-xs text-muted-foreground hover:text-foreground border border-border rounded transition-colors"
              >
                Cancel
              </button>
              <Button
                size="sm"
                disabled={bundleCommitting || bundlePreview.result.errors.length > 0}
                onClick={handleBundleCommit}
                className="h-7 text-xs gap-1.5"
              >
                {bundleCommitting ? <Loader2 className="h-3 w-3 animate-spin" /> : <Save className="h-3 w-3" />}
                Apply changes
              </Button>
            </div>
          </div>
          {/* Summary chips */}
          <div className="flex items-center gap-2 flex-wrap">
            {bundlePreview.result.framework_created && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-green-500/10 text-green-600 border border-green-500/20">
                + new framework
              </span>
            )}
            {bundlePreview.result.framework_updated && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-blue-500/10 text-blue-600 border border-blue-500/20">
                ~ framework updated
              </span>
            )}
            {bundlePreview.result.requirements_created > 0 && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-green-500/10 text-green-600 border border-green-500/20">
                +{bundlePreview.result.requirements_created} requirements
              </span>
            )}
            {bundlePreview.result.requirements_updated > 0 && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-blue-500/10 text-blue-600 border border-blue-500/20">
                ~{bundlePreview.result.requirements_updated} requirements updated
              </span>
            )}
            {bundlePreview.result.controls_created > 0 && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-green-500/10 text-green-600 border border-green-500/20">
                +{bundlePreview.result.controls_created} controls
              </span>
            )}
            {bundlePreview.result.controls_updated > 0 && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-blue-500/10 text-blue-600 border border-blue-500/20">
                ~{bundlePreview.result.controls_updated} controls updated
              </span>
            )}
            {bundlePreview.result.global_risks_created > 0 && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-green-500/10 text-green-600 border border-green-500/20">
                +{bundlePreview.result.global_risks_created} risks
              </span>
            )}
            {bundlePreview.result.global_risks_updated > 0 && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-blue-500/10 text-blue-600 border border-blue-500/20">
                ~{bundlePreview.result.global_risks_updated} risks updated
              </span>
            )}
            {bundlePreview.result.risk_control_links_created > 0 && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-purple-500/10 text-purple-600 border border-purple-500/20">
                +{bundlePreview.result.risk_control_links_created} risk-control links
              </span>
            )}
            {bundlePreview.result.errors.length === 0 && !bundlePreview.result.framework_created && !bundlePreview.result.framework_updated &&
              bundlePreview.result.requirements_created + bundlePreview.result.requirements_updated +
              bundlePreview.result.controls_created + bundlePreview.result.controls_updated +
              bundlePreview.result.global_risks_created + bundlePreview.result.global_risks_updated === 0 && (
              <span className="text-[11px] text-muted-foreground">No changes — bundle matches current state.</span>
            )}
            {bundlePreview.result.warnings.length > 0 && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-amber-500/10 text-amber-600 border border-amber-500/20">
                {bundlePreview.result.warnings.length} warning{bundlePreview.result.warnings.length !== 1 ? "s" : ""}
              </span>
            )}
            {bundlePreview.result.errors.length > 0 && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-red-500/10 text-red-600 border border-red-500/20">
                {bundlePreview.result.errors.length} error{bundlePreview.result.errors.length !== 1 ? "s" : ""}
              </span>
            )}
          </div>
          {/* Errors */}
          {bundlePreview.result.errors.length > 0 && (
            <div className="space-y-1 max-h-32 overflow-y-auto">
              {bundlePreview.result.errors.map((e: BundleImportError, i: number) => (
                <div key={i} className="flex items-start gap-1.5 text-[11px] text-red-600">
                  <AlertTriangle className="h-3 w-3 shrink-0 mt-0.5" />
                  <span>[{e.section}]{e.key ? ` ${e.key}` : ""}: {e.message}</span>
                </div>
              ))}
            </div>
          )}
          {/* Warnings */}
          {bundlePreview.result.warnings.length > 0 && (
            <div className="space-y-1 max-h-24 overflow-y-auto">
              {bundlePreview.result.warnings.map((w: string, i: number) => (
                <div key={i} className="flex items-start gap-1.5 text-[11px] text-amber-600">
                  <Info className="h-3 w-3 shrink-0 mt-0.5" />
                  <span>{w}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Stats */}
      <div className="flex items-center gap-2 flex-wrap">
        <StatPill icon={<Layers className="w-3 h-3 text-blue-500" />} value={controls.length} label="Controls" />
        <StatPill icon={<BookOpen className="w-3 h-3 text-purple-500" />} value={requirements.length} label="Groups" />
        <StatPill icon={<ShieldCheck className="w-3 h-3 text-green-500" />} value={publishedVersion?.version_code ?? "—"} label="Version" />
        <StatPill icon={<FlaskConical className="w-3 h-3 text-amber-500" />} value={controls.reduce((s, c) => s + (c.test_count ?? 0), 0)} label="Tests" />
        <StatPill
          icon={<Target className="w-3 h-3" />}
          value={`${coveragePct}%`}
          label="Coverage"
          valueClassName={coverageColor}
        />
      </div>

      {/* Main tab bar */}
      <div className="flex items-center gap-0 border-b border-border -mx-1 px-1" role="tablist">
        {([
          { id: "controls", label: "Controls", icon: <ShieldCheck className="h-3 w-3" /> },
          { id: "tasks", label: "Tasks", icon: <ListTodo className="h-3 w-3" /> },
          { id: "versions", label: "Versions", icon: <GitBranch className="h-3 w-3" /> },
          { id: "audit_prep", label: "Audit Prep", icon: <ClipboardCheck className="h-3 w-3" /> },
          { id: "comments", label: "Comments", icon: <MessageSquare className="h-3 w-3" /> },
          { id: "attachments", label: "Attachments", icon: <Paperclip className="h-3 w-3" /> },
        ] as const).map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setMainTab(tab.id)}
            className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium border-b-2 transition-colors -mb-px ${
              mainTab === tab.id
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
            role="tab"
          >
            {tab.icon}{tab.label}
          </button>
        ))}
      </div>

      {/* Versions tab */}
      {mainTab === "versions" && (
        <Card className="rounded-xl">
          <CardContent className="px-5 py-4">
            <VersionsPanel frameworkId={frameworkId} onReload={load} />
          </CardContent>
        </Card>
      )}

      {/* Audit Prep tab */}
      {mainTab === "audit_prep" && defaultOrgId && (
        <AuditPrepPanel
          frameworkId={frameworkId}
          frameworkName={framework?.name ?? ""}
          orgId={defaultOrgId}
          workspaceId={defaultWorkspaceId ?? ""}
          onViewReport={(id) => setViewReportId(id)}
        />
      )}

      {/* Comments tab */}
      {mainTab === "comments" && (
        <CommentsSection
          entityType="framework"
          entityId={frameworkId}
          currentUserId={getJwtSubject() ?? ""}
          isWorkspaceAdmin={isWorkspaceAdmin}
          active={mainTab === "comments"}
        />
      )}

      {/* Attachments tab */}
      {mainTab === "attachments" && (
        <AttachmentsSection
          entityType="framework"
          entityId={frameworkId}
          currentUserId={getJwtSubject() ?? ""}
          canUpload
          isWorkspaceAdmin={isWorkspaceAdmin}
          active={mainTab === "attachments"}
        />
      )}

      {/* Tasks tab */}
      {mainTab === "tasks" && (
        <FrameworkTasksPanel
          frameworkId={frameworkId}
          orgId={defaultOrgId ?? undefined}
          workspaceId={defaultWorkspaceId ?? undefined}
        />
      )}

      {/* Controls tab */}
      {mainTab === "controls" && <>
      <div className="flex items-center gap-3 flex-wrap">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px] max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <Input
            placeholder="Search controls..."
            className="pl-9 h-8 text-sm"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setFlatVisible(PAGE_SIZE) }}
          />
        </div>

        {/* Group toggle */}
        <div className="flex items-center rounded-lg border border-border p-0.5 gap-0.5 bg-muted/30">
          <button
            type="button"
            onClick={() => { setGroupByReq(false); setSpreadsheetMode(false) }}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium transition-colors ${
              !groupByReq && !spreadsheetMode ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <LayoutList className="w-3.5 h-3.5" /> Flat
          </button>
          <button
            type="button"
            onClick={() => { setGroupByReq(true); setSpreadsheetMode(false) }}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium transition-colors ${
              groupByReq && !spreadsheetMode ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" /> By Requirement
          </button>
          <button
            type="button"
            onClick={() => setSpreadsheetMode(true)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium transition-colors ${
              spreadsheetMode ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <TableProperties className="w-3.5 h-3.5" /> Sheet
          </button>
        </div>

        {/* Actions */}
        <button
          type="button"
          onClick={() => setShowAddReq(true)}
          className="inline-flex items-center gap-1 px-2 py-1 text-[11px] text-muted-foreground hover:text-foreground border border-dashed border-border hover:border-border/80 rounded-md transition-colors"
        >
          <Plus className="w-3 h-3" /> Requirement
        </button>
        <Button size="sm" className="h-8 gap-1.5 text-xs" onClick={() => setShowAddControl(true)}>
          <Plus className="w-3.5 h-3.5" /> Control
        </Button>
      </div>

      {/* Filter bar */}
      <ControlFilterBar filters={filters} onChange={f => { setFilters(f); setFlatVisible(PAGE_SIZE) }} gapCount={gapCount} />

      {/* ── Spreadsheet / Hierarchy view ────────────────────────────────── */}
      {spreadsheetMode && (() => {
        const allControlIds = controls.map(c => c.id)
        const hasAnyChildren = allControlIds.some(id => (sheetTasks[id]?.length ?? 0) > 0 || (sheetRisks[id]?.length ?? 0) > 0)
        const allExpanded = allControlIds.every(id => expandedSheetRows.has(id))

        // Build sections: requirements with controls + unlinked
        const unlinkedControls = controls.filter(c => !c.requirement_id || !requirements.find(r => r.id === c.requirement_id))

        // Render a single control row + expanded children
        const renderControlRow = (ctrl: ControlResponse) => {
          const tasks = sheetTasks[ctrl.id] ?? []
          const risks = sheetRisks[ctrl.id] ?? []
          const isExpanded = expandedSheetRows.has(ctrl.id)
          const hasChildren = tasks.length > 0 || risks.length > 0
          const today = new Date().toISOString().split("T")[0]

          const handleFieldSave = async (field: string, value: string) => {
            try {
              setSheetSaveError(null)
              await updateControl(frameworkId, ctrl.id, { [field]: value || undefined } as unknown as UpdateControlRequest)
              await load()
            } catch (e) {
              setSheetSaveError(e instanceof Error ? e.message : "Failed to save — please try again.")
            }
          }

          return (
            <React.Fragment key={ctrl.id}>
              <tr className={`border-b border-border/50 transition-colors group/row ${isExpanded ? "bg-blue-500/[0.03]" : "hover:bg-muted/30"}`}>
                {/* Expand toggle */}
                <td className="px-1.5 py-1.5 w-7 text-center">
                  {hasChildren ? (
                    <button
                      type="button"
                      onClick={() => setExpandedSheetRows(prev => {
                        const next = new Set(prev)
                        if (next.has(ctrl.id)) next.delete(ctrl.id)
                        else next.add(ctrl.id)
                        return next
                      })}
                      className="inline-flex items-center justify-center w-5 h-5 rounded hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
                    >
                      {isExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                    </button>
                  ) : (
                    <span className="inline-block w-5 h-5" />
                  )}
                </td>
                {/* Code */}
                <td className="px-2 py-1.5 font-mono text-[11px] text-primary/70 whitespace-nowrap">{ctrl.control_code}</td>
                {/* Name — editable */}
                <SheetCell value={ctrl.name} editable onSave={v => handleFieldSave("name", v)} className="px-2 py-1.5 text-xs font-medium text-foreground" />
                {/* Description — show truncated */}
                <td className="px-2 py-1.5 text-[11px] text-muted-foreground max-w-[200px]">
                  <span className="block truncate" title={ctrl.description ?? ""}>{ctrl.description || "—"}</span>
                </td>
                {/* Type — select */}
                <SheetSelect
                  value={ctrl.control_type ?? ""}
                  options={[
                    { value: "preventive", label: "Preventive" },
                    { value: "detective", label: "Detective" },
                    { value: "corrective", label: "Corrective" },
                    { value: "compensating", label: "Compensating" },
                  ]}
                  onSave={v => handleFieldSave("control_type", v)}
                  className="px-2 py-1.5"
                  renderBadge={v => (
                    <span className={`inline-flex px-1.5 py-0 rounded text-[10px] font-semibold uppercase tracking-wide border ${CONTROL_TYPE_COLORS[v] ?? "bg-muted text-muted-foreground"}`}>
                      {v}
                    </span>
                  )}
                />
                {/* Criticality — select */}
                <SheetSelect
                  value={ctrl.criticality_code ?? ""}
                  options={[
                    { value: "critical", label: "Critical" },
                    { value: "high", label: "High" },
                    { value: "medium", label: "Medium" },
                    { value: "low", label: "Low" },
                  ]}
                  onSave={v => handleFieldSave("criticality_code", v)}
                  className="px-2 py-1.5"
                  renderBadge={v => (
                    <span className={`inline-flex px-1.5 py-0 rounded text-[10px] font-semibold uppercase tracking-wide border ${CRITICALITY_COLORS[v] ?? "bg-muted text-muted-foreground"}`}>
                      {v}
                    </span>
                  )}
                />
                {/* Automation — select */}
                <SheetSelect
                  value={ctrl.automation_potential ?? ""}
                  options={[
                    { value: "full", label: "Full" },
                    { value: "partial", label: "Partial" },
                    { value: "manual", label: "Manual" },
                  ]}
                  onSave={v => handleFieldSave("automation_potential", v)}
                  className="px-2 py-1.5"
                  renderBadge={v => (
                    <span className={`inline-flex px-1.5 py-0 rounded text-[10px] font-semibold border ${AUTOMATION_COLORS[v] ?? "bg-muted text-muted-foreground"}`}>
                      {v}
                    </span>
                  )}
                />
                {/* Owner */}
                <td className="px-2 py-1.5 text-[11px] text-muted-foreground truncate max-w-[120px]">{ctrl.owner_display_name ?? "—"}</td>
                {/* Tasks count */}
                <td className="px-2 py-1.5 text-center">
                  {sheetLoading ? (
                    <span className="text-[10px] text-muted-foreground/40 animate-pulse">…</span>
                  ) : tasks.length > 0 ? (
                    <button
                      type="button"
                      onClick={() => setExpandedSheetRows(prev => { const next = new Set(prev); next.add(ctrl.id); return next })}
                      className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-semibold bg-blue-500/10 text-blue-600 border border-blue-500/20 hover:bg-blue-500/20 transition-colors"
                    >
                      <ClipboardCheck className="w-2.5 h-2.5" />
                      {tasks.length}
                    </button>
                  ) : (
                    <span className="text-[10px] text-muted-foreground/30">0</span>
                  )}
                </td>
                {/* Risks count */}
                <td className="px-2 py-1.5 text-center">
                  {sheetLoading ? (
                    <span className="text-[10px] text-muted-foreground/40 animate-pulse">…</span>
                  ) : risks.length > 0 ? (
                    <button
                      type="button"
                      onClick={() => setExpandedSheetRows(prev => { const next = new Set(prev); next.add(ctrl.id); return next })}
                      className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-semibold bg-orange-500/10 text-orange-600 border border-orange-500/20 hover:bg-orange-500/20 transition-colors"
                    >
                      <AlertTriangle className="w-2.5 h-2.5" />
                      {risks.length}
                    </button>
                  ) : (
                    <span className="text-[10px] text-muted-foreground/30">0</span>
                  )}
                </td>
              </tr>

              {/* ── Expanded drill-down: Tasks + Risks ──────────────────────── */}
              {isExpanded && (
                <tr className="border-b border-border/40">
                  <td colSpan={11} className="p-0">
                    <div className="bg-gradient-to-b from-muted/10 to-transparent px-6 py-3 ml-7 border-l-2 border-blue-500/20">
                      <div className="space-y-3">
                        {/* Tasks sub-table */}
                        {tasks.length > 0 && (
                          <div>
                            <div className="flex items-center gap-2 mb-1.5">
                              <ClipboardCheck className="w-3.5 h-3.5 text-blue-500" />
                              <span className="text-[11px] font-semibold text-foreground">Tasks</span>
                              <span className="text-[10px] text-muted-foreground">({tasks.length})</span>
                            </div>
                            <div className="rounded-lg border border-border/60 overflow-hidden shadow-sm">
                              <table className="w-full text-xs">
                                <thead>
                                  <tr className="bg-muted/40">
                                    <th className="px-3 py-1.5 text-left font-medium text-muted-foreground text-[10px] uppercase tracking-wider">Title</th>
                                    <th className="px-3 py-1.5 text-left font-medium text-muted-foreground text-[10px] uppercase tracking-wider w-24">Status</th>
                                    <th className="px-3 py-1.5 text-left font-medium text-muted-foreground text-[10px] uppercase tracking-wider w-24">Priority</th>
                                    <th className="px-3 py-1.5 text-left font-medium text-muted-foreground text-[10px] uppercase tracking-wider w-24">Due Date</th>
                                    <th className="px-3 py-1.5 text-left font-medium text-muted-foreground text-[10px] uppercase tracking-wider w-28">Assignee</th>
                                    <th className="px-3 py-1.5 w-8" />
                                  </tr>
                                </thead>
                                <tbody>
                                  {tasks.map((t) => {
                                    const isOverdue = t.due_date && t.due_date < today && !t.is_terminal
                                    return (
                                      <tr key={t.id} className="border-t border-border/30 hover:bg-muted/20 transition-colors">
                                        <td className="px-3 py-1.5">
                                          <div className="flex items-center gap-1.5">
                                            <TaskStatusIcon status={t.status_code} />
                                            <span className="font-medium text-foreground truncate">{t.title}</span>
                                          </div>
                                        </td>
                                        <td className="px-3 py-1.5">
                                          <span className={`inline-flex px-1.5 py-0 rounded text-[10px] font-semibold uppercase tracking-wide ${
                                            t.status_code === "completed" ? "bg-green-500/10 text-green-600" :
                                            t.status_code === "in_progress" ? "bg-blue-500/10 text-blue-600" :
                                            t.status_code === "blocked" ? "bg-red-500/10 text-red-500" :
                                            "bg-muted text-muted-foreground"
                                          }`}>
                                            {t.status_name ?? t.status_code}
                                          </span>
                                        </td>
                                        <td className="px-3 py-1.5">
                                          <Chip label={t.priority_name ?? t.priority_code} className={PRIORITY_COLORS[t.priority_code] ?? "bg-muted text-muted-foreground border-border"} />
                                        </td>
                                        <td className={`px-3 py-1.5 text-[11px] ${isOverdue ? "text-red-500 font-semibold" : "text-muted-foreground"}`}>
                                          {t.due_date ? new Date(t.due_date).toLocaleDateString() : "—"}
                                          {isOverdue && " !"}
                                        </td>
                                        <td className="px-3 py-1.5 text-[11px] text-muted-foreground truncate max-w-[112px]">
                                          {(t as unknown as Record<string, unknown>).assignee_display_name as string ?? "—"}
                                        </td>
                                        <td className="px-3 py-1.5">
                                          <button
                                            type="button"
                                            onClick={() => router.push(`/tasks/${t.id}`)}
                                            className="text-muted-foreground hover:text-primary transition-colors"
                                            title="View task"
                                          >
                                            <ExternalLink className="w-3 h-3" />
                                          </button>
                                        </td>
                                      </tr>
                                    )
                                  })}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        )}

                        {/* Risks sub-table */}
                        {risks.length > 0 && (
                          <div>
                            <div className="flex items-center gap-2 mb-1.5">
                              <AlertTriangle className="w-3.5 h-3.5 text-orange-500" />
                              <span className="text-[11px] font-semibold text-foreground">Risks</span>
                              <span className="text-[10px] text-muted-foreground">({risks.length})</span>
                            </div>
                            <div className="rounded-lg border border-border/60 overflow-hidden shadow-sm">
                              <table className="w-full text-xs">
                                <thead>
                                  <tr className="bg-muted/40">
                                    <th className="px-3 py-1.5 text-left font-medium text-muted-foreground text-[10px] uppercase tracking-wider">Risk Code</th>
                                    <th className="px-3 py-1.5 text-left font-medium text-muted-foreground text-[10px] uppercase tracking-wider">Title</th>
                                    <th className="px-3 py-1.5 text-left font-medium text-muted-foreground text-[10px] uppercase tracking-wider w-24">Level</th>
                                    <th className="px-3 py-1.5 text-left font-medium text-muted-foreground text-[10px] uppercase tracking-wider w-24">Status</th>
                                    <th className="px-3 py-1.5 text-left font-medium text-muted-foreground text-[10px] uppercase tracking-wider w-28">Treatment</th>
                                    <th className="px-3 py-1.5 w-8" />
                                  </tr>
                                </thead>
                                <tbody>
                                  {risks.map((r) => (
                                    <tr key={r.id} className="border-t border-border/30 hover:bg-muted/20 transition-colors">
                                      <td className="px-3 py-1.5 font-mono text-[11px] text-primary/70">{r.risk_code}</td>
                                      <td className="px-3 py-1.5 font-medium text-foreground truncate max-w-[200px]">{r.title}</td>
                                      <td className="px-3 py-1.5">
                                        <span className="inline-flex px-1.5 py-0 rounded text-[10px] font-semibold uppercase tracking-wide border"
                                          style={{ borderColor: `${r.risk_level_color}40`, color: r.risk_level_color, backgroundColor: `${r.risk_level_color}15` }}>
                                          {r.risk_level_name ?? r.risk_level_code}
                                        </span>
                                      </td>
                                      <td className="px-3 py-1.5 text-[11px] text-muted-foreground capitalize">{r.risk_status?.replace(/_/g, " ") ?? "—"}</td>
                                      <td className="px-3 py-1.5 text-[11px] text-muted-foreground capitalize">{r.treatment_type_name ?? r.treatment_type_code ?? "—"}</td>
                                      <td className="px-3 py-1.5">
                                        <button
                                          type="button"
                                          onClick={() => router.push(`/risks/${r.id}`)}
                                          className="text-muted-foreground hover:text-primary transition-colors"
                                          title="View risk"
                                        >
                                          <ExternalLink className="w-3 h-3" />
                                        </button>
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        )}

                        {/* No children message */}
                        {tasks.length === 0 && risks.length === 0 && (
                          <p className="text-[11px] text-muted-foreground py-1">No tasks or risks linked to this control.</p>
                        )}
                      </div>
                    </div>
                  </td>
                </tr>
              )}
            </React.Fragment>
          )
        }

        return (
          <div className="rounded-lg border border-border overflow-hidden shadow-sm">
            {/* ── Sheet toolbar ── */}
            <div className="flex items-center justify-between gap-3 px-3 py-2 border-b border-border bg-muted/30">
              <div className="flex items-center gap-2">
                <Layers className="w-3.5 h-3.5 text-primary/60" />
                <span className="text-[11px] font-medium text-foreground">Requirements → Controls → Tasks & Risks</span>
                {sheetLoading && (
                  <span className="flex items-center gap-1 text-[10px] text-muted-foreground">
                    <Loader2 className="w-3 h-3 animate-spin" /> Loading drill-down data…
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                {hasAnyChildren && !sheetLoading && (
                  <button
                    type="button"
                    onClick={() => {
                      if (allExpanded) setExpandedSheetRows(new Set())
                      else setExpandedSheetRows(new Set(allControlIds))
                    }}
                    className="text-[10px] text-muted-foreground hover:text-foreground transition-colors px-2 py-0.5 rounded border border-border/50 hover:border-border"
                  >
                    {allExpanded ? "Collapse all" : "Expand all"}
                  </button>
                )}
                <span className="text-[10px] text-muted-foreground">
                  {controls.length} control{controls.length !== 1 ? "s" : ""} · {requirements.length} group{requirements.length !== 1 ? "s" : ""}
                </span>
              </div>
            </div>

            {/* ── Sheet save error ── */}
            {sheetSaveError && (
              <div className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive mb-2">
                <span className="flex-1">{sheetSaveError}</span>
                <button onClick={() => setSheetSaveError(null)} className="ml-auto hover:opacity-70 text-destructive font-bold">✕</button>
              </div>
            )}

            {/* ── Sheet table ── */}
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-xs min-w-[900px]">
                <thead className="sticky top-0 z-10">
                  <tr className="bg-muted/60 border-b border-border">
                    <th className="w-7 px-1.5 py-2" />
                    <th className="w-[100px] px-2 py-2 text-left font-semibold text-muted-foreground text-[10px] uppercase tracking-wider whitespace-nowrap border-r border-border/30">Code</th>
                    <th className="min-w-[180px] px-2 py-2 text-left font-semibold text-muted-foreground text-[10px] uppercase tracking-wider border-r border-border/30">Name</th>
                    <th className="w-[160px] px-2 py-2 text-left font-semibold text-muted-foreground text-[10px] uppercase tracking-wider border-r border-border/30">Description</th>
                    <th className="w-[100px] px-2 py-2 text-left font-semibold text-muted-foreground text-[10px] uppercase tracking-wider border-r border-border/30">Type</th>
                    <th className="w-[100px] px-2 py-2 text-left font-semibold text-muted-foreground text-[10px] uppercase tracking-wider border-r border-border/30">Criticality</th>
                    <th className="w-[90px] px-2 py-2 text-left font-semibold text-muted-foreground text-[10px] uppercase tracking-wider border-r border-border/30">Automation</th>
                    <th className="w-[110px] px-2 py-2 text-left font-semibold text-muted-foreground text-[10px] uppercase tracking-wider border-r border-border/30">Owner</th>
                    <th className="w-[60px] px-2 py-2 text-center font-semibold text-muted-foreground text-[10px] uppercase tracking-wider border-r border-border/30">Tasks</th>
                    <th className="w-[60px] px-2 py-2 text-center font-semibold text-muted-foreground text-[10px] uppercase tracking-wider">Risks</th>
                  </tr>
                </thead>
                <tbody>
                  {/* Requirements with controls */}
                  {sortedReqs.map((req) => {
                    const reqControls = filteredControls.filter(c => c.requirement_id === req.id)
                    if (reqControls.length === 0) return null
                    return (
                      <React.Fragment key={req.id}>
                        {/* Requirement group header */}
                        <tr className="bg-purple-500/[0.06] border-b border-border/60">
                          <td colSpan={10} className="px-2 py-2">
                            <div className="flex items-center gap-2">
                              <BookOpen className="w-3.5 h-3.5 text-purple-500 shrink-0" />
                              <span className="font-semibold text-xs text-foreground">{req.requirement_code}</span>
                              <span className="text-xs text-muted-foreground truncate">{req.name}</span>
                              <span className="ml-auto flex items-center gap-1.5 text-[10px] text-muted-foreground shrink-0">
                                <ShieldCheck className="w-3 h-3" />
                                {reqControls.length} control{reqControls.length !== 1 ? "s" : ""}
                              </span>
                            </div>
                          </td>
                        </tr>
                        {/* Controls under this requirement */}
                        {reqControls.map(ctrl => renderControlRow(ctrl))}
                      </React.Fragment>
                    )
                  })}

                  {/* Controls with no requirement */}
                  {unlinkedControls.length > 0 && (
                    <React.Fragment key="__unlinked__">
                      <tr className="bg-muted/30 border-b border-border/60">
                        <td colSpan={10} className="px-2 py-2">
                          <div className="flex items-center gap-2">
                            <Layers className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
                            <span className="font-semibold text-xs text-muted-foreground">Ungrouped Controls</span>
                            <span className="ml-auto text-[10px] text-muted-foreground">{unlinkedControls.length} control{unlinkedControls.length !== 1 ? "s" : ""}</span>
                          </div>
                        </td>
                      </tr>
                      {unlinkedControls.map(ctrl => renderControlRow(ctrl))}
                    </React.Fragment>
                  )}

                  {/* Empty state */}
                  {controls.length === 0 && (
                    <tr>
                      <td colSpan={10} className="px-4 py-12 text-center">
                        <ShieldCheck className="w-6 h-6 text-muted-foreground/40 mx-auto mb-2" />
                        <p className="text-sm text-muted-foreground">No controls in this framework yet.</p>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* ── Sheet footer ── */}
            <div className="flex items-center justify-between px-3 py-1.5 border-t border-border bg-muted/20 text-[10px] text-muted-foreground">
              <span>
                {filteredControls.length} of {controls.length} control{controls.length !== 1 ? "s" : ""} shown
                {expandedSheetRows.size > 0 && <span className="ml-2">· {expandedSheetRows.size} expanded</span>}
              </span>
              <span className="flex items-center gap-1.5">
                <span className={coverageColor}>{coveragePct}% test coverage</span>
                <span>·</span>
                Click any cell to edit
              </span>
            </div>
          </div>
        )
      })()}

      {/* Controls list */}
      {!spreadsheetMode && (filteredControls.length === 0 ? (
        <Card className="rounded-xl">
          <CardContent className="flex flex-col items-center justify-center py-14 gap-3">
            <ShieldCheck className="h-8 w-8 text-muted-foreground" />
            <p className="text-sm font-medium">
              {search || filters.criticality || filters.controlType || filters.automation || filters.gapsOnly
                ? "No controls match your filters"
                : "No controls yet"}
            </p>
            {!search && !filters.criticality && !filters.controlType && !filters.automation && !filters.gapsOnly && (
              <Button size="sm" onClick={() => setShowAddControl(true)} className="gap-2">
                <Plus className="w-3.5 h-3.5" /> Add First Control
              </Button>
            )}
          </CardContent>
        </Card>
      ) : !groupByReq ? (
        /* ── Flat list ── */
        <div className="rounded-xl border border-border overflow-hidden">
          {/* Column header */}
          <div className="flex items-center gap-3 px-4 py-2 bg-muted/40 border-b border-border text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
            <span className="w-6 text-right">#</span>
            <span className="w-4" />
            <span className="w-20">Code</span>
            <span className="flex-1">Name</span>
            <span className="hidden sm:block w-20 text-right">Criticality</span>
            <span className="hidden md:block w-20 text-right">Type</span>
            <span className="hidden lg:block w-20 text-right">Auto</span>
            <span className="hidden sm:flex items-center gap-1 w-12 justify-end">
              <FlaskConical className="w-3 h-3" /> Tests
            </span>
          </div>
          {flatVisible_controls.map((ctrl, idx) => (
            <ControlRow
              key={ctrl.id}
              control={ctrl}
              index={idx + 1}
              frameworkId={frameworkId}
              orgMembers={orgMembers}
              orgGroups={orgGroups}
              defaultOrgId={defaultOrgId}
              defaultWorkspaceId={defaultWorkspaceId}
              onUpdated={load}
            />
          ))}
          {flatVisible < filteredControls.length && (
            <button
              type="button"
              onClick={() => setFlatVisible((v) => v + PAGE_SIZE)}
              className="flex items-center justify-center gap-2 w-full px-4 py-2.5 text-xs text-primary hover:bg-muted/30 transition-colors border-t border-border/40"
            >
              <Plus className="w-3 h-3" />
              Load {Math.min(PAGE_SIZE, filteredControls.length - flatVisible)} more
              <span className="text-muted-foreground">({filteredControls.length - flatVisible} remaining)</span>
            </button>
          )}
          <div className="px-4 py-2 text-center text-[10px] text-muted-foreground border-t border-border/40 bg-muted/20">
            Showing {flatVisible_controls.length} of {filteredControls.length} controls
          </div>
        </div>
      ) : (
        /* ── Grouped by requirement ── */
        <div className="space-y-1">
          {/* Requirements with controls */}
          {sortedReqs.map((req) => {
            const reqControls = grouped.get(req.id) ?? []
            if (reqControls.length === 0 && search) return null
            const start = groupStartIndex
            groupStartIndex += reqControls.length
            return (
              <RequirementGroup
                key={req.id}
                req={req}
                controls={reqControls}
                search={searchLower}
                startIndex={start}
                frameworkId={frameworkId}
                orgMembers={orgMembers}
                orgGroups={orgGroups}
                defaultOrgId={defaultOrgId}
                defaultWorkspaceId={selectedWorkspaceId}
                onUpdated={load}
              />
            )
          })}
          {/* Ungrouped controls */}
          {(grouped.get(null) ?? []).length > 0 && (
            <RequirementGroup
              req={null}
              controls={grouped.get(null) ?? []}
              search={searchLower}
              startIndex={groupStartIndex}
              frameworkId={frameworkId}
              orgMembers={orgMembers}
              orgGroups={orgGroups}
              defaultOrgId={defaultOrgId}
              defaultWorkspaceId={defaultWorkspaceId}
              onUpdated={load}
            />
          )}
        </div>
      ))}
      </>}

      {/* Dialogs */}
      {showAddControl && (
        <AddControlDialog
          frameworkId={frameworkId}
          frameworkName={framework?.name}
          requirements={requirements}
          orgMembers={orgMembers}
          orgGroups={orgGroups}
          orgId={defaultOrgId}
          workspaceId={defaultWorkspaceId}
          onCreated={load}
          onClose={() => setShowAddControl(false)}
        />
      )}
      {showAddReq && (
        <AddRequirementDialog
          frameworkId={frameworkId}
          requirements={requirements}
          orgId={defaultOrgId}
          workspaceId={defaultWorkspaceId}
          onCreated={load}
          onClose={() => setShowAddReq(false)}
        />
      )}
      {editItem && (
        <EditFrameworkDialog
          framework={editItem}
          categories={categories}
          onSave={handleUpdate}
          onClose={() => setEditItem(null)}
        />
      )}
      {deleteItem && (
        <DeleteFrameworkDialog
          framework={deleteItem}
          onConfirm={handleDelete}
          onClose={() => setDeleteItem(null)}
        />
      )}

      {/* Report Viewer Modal */}
      {viewReportId && (
        <FrameworkReportViewer
          reportId={viewReportId}
          onClose={() => setViewReportId(null)}
        />
      )}
    </div>
  )
}
