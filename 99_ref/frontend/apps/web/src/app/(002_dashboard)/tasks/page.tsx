"use client"

import { useEffect, useState, useMemo, useCallback } from "react"
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
  CheckSquare,
  Plus,
  Search,
  RefreshCw,
  AlertTriangle,
  MessageSquare,
  Link2,
  Pencil,
  Trash2,
  UserPlus,
  GitBranch,
  X,
  Calendar,
  User2,
  LayoutList,
  Columns,
  ChevronUp,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Clock,
  ArrowUpDown,
  Copy,
  CheckCircle2,
  Circle,
  Timer,
  ShieldAlert,
  Ban,
  FileSearch,
  Wrench,
  Download,
  SquareCheck,
  Square,
  ListChecks,
  SlidersHorizontal,
  ExternalLink,
  TableProperties,
  List,
} from "lucide-react"
import { useRouter } from "next/navigation"
import {
  listTasks,
  getTaskSummary,
  listTaskTypes,
  listTaskPriorities,
  listTaskStatuses,
  createTask,
  updateTask,
  deleteTask,
  cloneTask,
  getTask,
  listAssignments,
  addAssignment,
  removeAssignment,
  listTaskEvents,
  addTaskEvent,
  listDependencies,
  addDependency,
  removeDependency,
  exportTasksCsv,
  bulkUpdateTasks,
  exportTasks,
  importTasks,
} from "@/lib/api/grc"
import { EntitySpreadsheet } from "@/components/spreadsheet/EntitySpreadsheet"
import { ExportImportToolbar } from "@/components/spreadsheet/ExportImportToolbar"
import { ImportResultDialog } from "@/components/spreadsheet/ImportResultDialog"
import type { ImportResult } from "@/components/spreadsheet/ImportResultDialog"
import { tasksColumns } from "@/components/spreadsheet/tasksConfig"
import type { TaskSpreadsheetRow } from "@/components/spreadsheet/tasksConfig"
import { CommentsSection } from "@/components/comments/CommentsSection"
import { AttachmentsSection } from "@/components/attachments/AttachmentsSection"
import { getCommentCount } from "@/lib/api/comments"
import { getAttachmentCount } from "@/lib/api/attachments"
import { getEvidenceBatchVerdicts } from "@/lib/api/ai"
import type {
  TaskResponse,
  DimensionResponse,
  TaskStatusResponse,
  TaskAssignmentResponse,
  TaskEventResponse,
  TaskDependencyResponse,
  TaskDependencyListResponse,
  CreateTaskRequest,
  UpdateTaskRequest,
  TaskListFilters,
  TaskSummaryResponse,
} from "@/lib/types/grc"
import { useOrgWorkspace } from "@/lib/context/OrgWorkspaceContext"
import { OrgWorkspaceSwitcher } from "@/components/layout/OrgWorkspaceSwitcher"
import { ReadOnlyBanner } from "@/components/layout/ReadOnlyBanner"
import { useAccess } from "@/components/providers/AccessProvider"
import { FormFillChat } from "@/components/ai/FormFillChat"

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

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "—"
  try {
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    })
  } catch {
    return dateStr
  }
}

function formatDateTime(dateStr: string | null | undefined): string {
  if (!dateStr) return "—"
  try {
    return new Date(dateStr).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  } catch {
    return dateStr
  }
}

function formatRelativeTime(dateStr: string | null | undefined): string {
  if (!dateStr) return "—"
  try {
    const diff = Date.now() - new Date(dateStr).getTime()
    if (diff < 60_000) return "just now"
    if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`
    if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`
    if (diff < 7 * 86_400_000) return `${Math.floor(diff / 86_400_000)}d ago`
    return formatDate(dateStr)
  } catch {
    return dateStr
  }
}

function isOverdue(task: TaskResponse): boolean {
  if (!task.due_date || task.is_terminal) return false
  return new Date(task.due_date) < new Date()
}

function overdueDays(task: TaskResponse): number {
  if (!task.due_date) return 0
  return Math.floor((Date.now() - new Date(task.due_date).getTime()) / 86_400_000)
}

function truncateId(id: string): string {
  return id.slice(0, 8) + "..."
}

function parseAssigneeEmails(raw: string): { emails: string[]; invalid: string[] } {
  const candidates = raw
    .split(",")
    .map((token) => token.trim().toLowerCase())
    .filter((token) => token.length > 0)
  const seen = new Set<string>()
  const emails: string[] = []
  const invalid: string[] = []
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  for (const token of candidates) {
    if (!emailPattern.test(token)) {
      invalid.push(token)
      continue
    }
    if (seen.has(token)) continue
    seen.add(token)
    emails.push(token)
  }
  return { emails, invalid }
}

// ─────────────────────────────────────────────────────────────────────────────
// Constants / Styling Maps
// ─────────────────────────────────────────────────────────────────────────────

const PRIORITY_META: Record<string, { label: string; cls: string; border: string; dot: string }> = {
  critical: { label: "Critical", cls: "text-red-500 bg-red-500/10 border-red-500/20", border: "border-l-red-500", dot: "bg-red-500" },
  high:     { label: "High",     cls: "text-orange-500 bg-orange-500/10 border-orange-500/20", border: "border-l-orange-500", dot: "bg-orange-500" },
  medium:   { label: "Medium",   cls: "text-amber-500 bg-amber-500/10 border-amber-500/20", border: "border-l-amber-500", dot: "bg-amber-500" },
  low:      { label: "Low",      cls: "text-green-500 bg-green-500/10 border-green-500/20", border: "border-l-green-500", dot: "bg-green-500" },
}

const STATUS_META: Record<string, { label: string; cls: string; headerCls: string; iconColor: string }> = {
  open: {
    label: "Open",
    cls: "text-slate-400 bg-slate-500/10 border-slate-500/20",
    headerCls: "bg-slate-500/10 border-slate-500/20 text-slate-500",
    iconColor: "text-slate-400",
  },
  in_progress: {
    label: "In Progress",
    cls: "text-blue-500 bg-blue-500/10 border-blue-500/20",
    headerCls: "bg-blue-500/10 border-blue-500/20 text-blue-600",
    iconColor: "text-blue-500",
  },
  pending_verification: {
    label: "Pending Review",
    cls: "text-purple-500 bg-purple-500/10 border-purple-500/20",
    headerCls: "bg-purple-500/10 border-purple-500/20 text-purple-600",
    iconColor: "text-purple-500",
  },
  resolved: {
    label: "Resolved",
    cls: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20",
    headerCls: "bg-emerald-500/10 border-emerald-500/20 text-emerald-600",
    iconColor: "text-emerald-500",
  },
  cancelled: {
    label: "Cancelled",
    cls: "text-gray-400 bg-gray-500/10 border-gray-500/20",
    headerCls: "bg-gray-500/10 border-gray-500/20 text-gray-500",
    iconColor: "text-gray-400",
  },
  blocked: {
    label: "Blocked",
    cls: "text-red-600 bg-red-600/10 border-red-600/20",
    headerCls: "bg-red-600/10 border-red-600/20 text-red-700",
    iconColor: "text-red-600",
  },
}

const TASK_TYPE_ICONS: Record<string, React.ReactNode> = {
  evidence_collection: <FileSearch className="h-3.5 w-3.5 text-sky-500" />,
  control_remediation: <Wrench className="h-3.5 w-3.5 text-orange-500" />,
  risk_mitigation:     <ShieldAlert className="h-3.5 w-3.5 text-red-500" />,
  general:             <SquareCheck className="h-3.5 w-3.5 text-gray-400" />,
}

const TASK_TYPE_BG: Record<string, string> = {
  evidence_collection: "bg-sky-500/10",
  control_remediation: "bg-orange-500/10",
  risk_mitigation:     "bg-red-500/10",
  general:             "bg-gray-500/10",
}

const BOARD_COLUMNS = ["open", "in_progress", "pending_verification", "resolved", "cancelled"]

const EVENT_LABELS: Record<string, string> = {
  created: "Task created",
  status_changed: "Status changed",
  reassigned: "Reassigned",
  priority_changed: "Priority changed",
  due_date_changed: "Due date updated",
  comment_added: "Comment",
}

// ─────────────────────────────────────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────────────────────────────────────

function PriorityBadge({ code }: { code: string }) {
  const meta = PRIORITY_META[code] ?? { label: code, cls: "text-muted-foreground bg-muted border-border", dot: "bg-muted-foreground" }
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-semibold border ${meta.cls}`}>
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${meta.dot}`} />
      {meta.label}
    </span>
  )
}

function StatusBadge({ code, name }: { code: string; name: string }) {
  const meta = STATUS_META[code] ?? { label: name, cls: "text-muted-foreground bg-muted border-border", iconColor: "" }
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold border ${meta.cls}`}>
      {meta.label || name}
    </span>
  )
}

function TypeBadge({ code, name }: { code: string; name: string }) {
  const icon = TASK_TYPE_ICONS[code]
  const bg = TASK_TYPE_BG[code] ?? "bg-muted/50"
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium border border-border/50 text-muted-foreground ${bg}`}>
      {icon}
      {name}
    </span>
  )
}

const EVIDENCE_VERDICT_BADGE: Record<string, { dot: string; label: string; badge: string }> = {
  ALL_MET:     { dot: "bg-emerald-500", label: "All Met",       badge: "text-emerald-400 bg-emerald-500/10 border-emerald-500/25" },
  PARTIALLY_MET: { dot: "bg-amber-500",  label: "Partial",      badge: "text-amber-400 bg-amber-500/10 border-amber-500/25" },
  NOT_MET:     { dot: "bg-red-500",     label: "Not Met",       badge: "text-red-400 bg-red-500/10 border-red-500/25" },
  INCONCLUSIVE: { dot: "bg-slate-500",  label: "Inconclusive",  badge: "text-slate-400 bg-slate-500/10 border-slate-500/25" },
}

function EvidenceVerdictBadge({ verdict }: { verdict?: string }) {
  if (!verdict) return <span className="text-[10px] text-muted-foreground/40">—</span>
  const vm = EVIDENCE_VERDICT_BADGE[verdict]
  if (!vm) return <span className="text-[10px] text-muted-foreground/40">—</span>
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-[10px] font-semibold ${vm.badge}`}>
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${vm.dot}`} />
      {vm.label}
    </span>
  )
}

function CopyableId({ id }: { id: string }) {
  const [copied, setCopied] = useState(false)
  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(id).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    })
  }, [id])
  return (
    <button
      onClick={handleCopy}
      className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
      title={id}
    >
      <span className="font-mono">{truncateId(id)}</span>
      {copied ? <CheckCircle2 className="h-3 w-3 text-green-500" /> : <Copy className="h-3 w-3" />}
    </button>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Summary Stat Cards
// ─────────────────────────────────────────────────────────────────────────────

interface SummaryBarProps {
  summary: TaskSummaryResponse | null
  activeFilter: string | null
  onFilterClick: (filter: string | null) => void
}

function SummaryBar({ summary, activeFilter, onFilterClick }: SummaryBarProps) {
  type StatItem = {
    key: string
    label: string
    count: number
    icon: React.ReactNode
    iconBg: string
    borderColor: string
    countColor: string
    pulse?: boolean
    noFilter?: boolean
  }

  const stats: StatItem[] = [
    {
      key: "open",
      label: "Open",
      count: summary?.open_count ?? 0,
      icon: <Circle className="h-5 w-5 text-slate-400" />,
      iconBg: "bg-slate-500/10",
      borderColor: "border-l-slate-400",
      countColor: "text-foreground",
    },
    {
      key: "in_progress",
      label: "In Progress",
      count: summary?.in_progress_count ?? 0,
      icon: <Timer className="h-5 w-5 text-blue-500" />,
      iconBg: "bg-blue-500/10",
      borderColor: "border-l-blue-500",
      countColor: "text-blue-500",
    },
    {
      key: "overdue",
      label: "Overdue",
      count: summary?.overdue_count ?? 0,
      icon: <AlertTriangle className="h-5 w-5 text-red-500" />,
      iconBg: "bg-red-500/10",
      borderColor: "border-l-red-500",
      countColor: "text-red-500",
      pulse: (summary?.overdue_count ?? 0) > 0,
    },
    {
      key: "pending_verification",
      label: "Pending Review",
      count: summary?.pending_verification_count ?? 0,
      icon: <ShieldAlert className="h-5 w-5 text-purple-500" />,
      iconBg: "bg-purple-500/10",
      borderColor: "border-l-purple-500",
      countColor: "text-purple-500",
    },
    {
      key: "resolved",
      label: "Resolved",
      count: summary?.resolved_count ?? 0,
      icon: <CheckCircle2 className="h-5 w-5 text-emerald-500" />,
      iconBg: "bg-emerald-500/10",
      borderColor: "border-l-emerald-500",
      countColor: "text-emerald-500",
    },
    {
      key: "resolved_this_week",
      label: "This Week",
      count: summary?.resolved_this_week_count ?? 0,
      icon: <CheckCircle2 className="h-5 w-5 text-green-400" />,
      iconBg: "bg-green-500/10",
      borderColor: "border-l-green-400",
      countColor: "text-green-400",
      noFilter: true,
    },
  ]

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      {stats.map((s) => {
        const isActive = !s.noFilter && activeFilter === s.key
        return (
          <button
            key={s.key}
            onClick={() => { if (!s.noFilter) onFilterClick(isActive ? null : s.key) }}
            className={`relative flex flex-col gap-2 p-4 rounded-xl border-l-4 bg-card border border-border transition-all text-left
              ${s.noFilter ? "cursor-default" : "cursor-pointer hover:shadow-md hover:-translate-y-0.5"}
              ${s.borderColor}
              ${isActive ? "ring-2 ring-primary/30 shadow-md bg-primary/5" : ""}
            `}
          >
            {s.pulse && (
              <span className="absolute top-2 right-2 flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500" />
              </span>
            )}
            <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${s.iconBg}`}>
              {s.icon}
            </div>
            <div>
              <p className={`text-2xl font-bold tabular-nums leading-none ${s.countColor}`}>{s.count}</p>
              <p className="text-xs text-muted-foreground mt-1 font-medium">{s.label}</p>
            </div>
          </button>
        )
      })}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Task Detail Panel (slide-over)
// ─────────────────────────────────────────────────────────────────────────────

interface TaskDetailPanelProps {
  task: TaskResponse
  onClose: () => void
  onEdit: (task: TaskResponse) => void
  onClone: (task: TaskResponse) => void
  onRefresh: () => void
}

function TaskDetailPanel({ task, onClose, onEdit, onClone, onRefresh }: TaskDetailPanelProps) {
  const [events, setEvents] = useState<TaskEventResponse[]>([])
  const [assignments, setAssignments] = useState<TaskAssignmentResponse[]>([])
  const [loadingEvents, setLoadingEvents] = useState(true)
  const [commentText, setCommentText] = useState("")
  const [submittingComment, setSubmittingComment] = useState(false)
  const [detailTab, setDetailTab] = useState<"details" | "comments" | "attachments">("details")
  const [addAssigneeUserId, setAddAssigneeUserId] = useState("")
  const [showAddAssignee, setShowAddAssignee] = useState(false)
  const [commentCount, setCommentCount] = useState<number | null>(null)
  const [attachmentCount, setAttachmentCount] = useState<number | null>(null)
  const { isWorkspaceAdmin } = useAccess()
  const router = useRouter()

  const loadPanel = useCallback(async () => {
    setLoadingEvents(true)
    try {
      const [evts, assigns, ccnt, acnt] = await Promise.all([
        listTaskEvents(task.id),
        listAssignments(task.id),
        getCommentCount("task", task.id).catch(() => null),
        getAttachmentCount("task", task.id).catch(() => null),
      ])
      setEvents(evts)
      setAssignments(assigns)
      if (ccnt !== null) setCommentCount(ccnt)
      if (acnt !== null) setAttachmentCount(acnt)
    } catch {
      // silently ignore
    } finally {
      setLoadingEvents(false)
    }
  }, [task.id])

  useEffect(() => { loadPanel() }, [loadPanel])

  const handleComment = useCallback(async () => {
    if (!commentText.trim()) return
    setSubmittingComment(true)
    try {
      await addTaskEvent(task.id, commentText.trim())
      setCommentText("")
      await loadPanel()
    } catch {
      // ignore
    } finally {
      setSubmittingComment(false)
    }
  }, [commentText, task.id, loadPanel])

  const handleAddAssignee = useCallback(async () => {
    if (!addAssigneeUserId.trim()) return
    try {
      await addAssignment(task.id, { user_id: addAssigneeUserId.trim(), role: "co_assignee" })
      setAddAssigneeUserId("")
      setShowAddAssignee(false)
      await loadPanel()
      onRefresh()
    } catch {
      // ignore
    }
  }, [addAssigneeUserId, task.id, loadPanel, onRefresh])

  const handleRemoveAssignee = useCallback(async (assignmentId: string) => {
    try {
      await removeAssignment(task.id, assignmentId)
      await loadPanel()
      onRefresh()
    } catch {
      // ignore
    }
  }, [task.id, loadPanel, onRefresh])

  const overdueTask = isOverdue(task)
  const criteriaLines = task.acceptance_criteria
    ? task.acceptance_criteria.split("\n").filter((l) => l.trim().length > 0)
    : []
  const [checkedCriteria, setCheckedCriteria] = useState<Set<number>>(new Set())
  const criteriaProgress = criteriaLines.length > 0
    ? Math.round((checkedCriteria.size / criteriaLines.length) * 100)
    : 0

  const priorityMeta = PRIORITY_META[task.priority_code]
  const statusMeta = STATUS_META[task.status_code]

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm" onClick={onClose} />

      {/* Panel */}
      <div className="fixed top-0 right-0 bottom-0 z-50 w-full sm:w-[500px] bg-background border-l border-border shadow-2xl flex flex-col overflow-hidden">

        {/* Colored top accent based on priority */}
        <div className={`h-1 w-full shrink-0 ${
          task.priority_code === "critical" ? "bg-red-500" :
          task.priority_code === "high" ? "bg-orange-500" :
          task.priority_code === "medium" ? "bg-amber-500" : "bg-green-500"
        }`} />

        {/* Header */}
        <div className="flex items-start justify-between gap-3 px-5 pt-4 pb-4 border-b border-border">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1.5">
              <div className={`w-6 h-6 rounded-md flex items-center justify-center ${TASK_TYPE_BG[task.task_type_code] ?? "bg-muted"}`}>
                {TASK_TYPE_ICONS[task.task_type_code] ?? <SquareCheck className="h-3.5 w-3.5 text-muted-foreground" />}
              </div>
              <span className="text-xs text-muted-foreground font-medium">{task.task_type_name}</span>
              <span className="font-mono text-[10px] text-muted-foreground border border-border/50 rounded px-1.5 py-0.5">v{task.version ?? 1}</span>
            </div>
            <h2 className="text-base font-bold leading-snug text-foreground line-clamp-2">{task.title}</h2>
            <div className="flex flex-wrap items-center gap-1.5 mt-2">
              <StatusBadge code={task.status_code} name={task.status_name} />
              <PriorityBadge code={task.priority_code} />
              {overdueTask && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold border border-red-500/30 bg-red-500/10 text-red-500">
                  <AlertTriangle className="h-3 w-3" /> Overdue
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-1 shrink-0">
            <Button size="sm" variant="outline" onClick={() => { onClose(); router.push(`/tasks/${task.id}`) }} title="Open full page">
              <ExternalLink className="h-3.5 w-3.5" />
            </Button>
            <Button size="sm" variant="outline" onClick={() => onEdit(task)}>
              <Pencil className="h-3.5 w-3.5 mr-1" /> Edit
            </Button>
            <Button size="sm" variant="ghost" onClick={() => { onClone(task); onClose() }} title="Clone task">
              <Copy className="h-3.5 w-3.5" />
            </Button>
            <button onClick={onClose} className="p-1.5 rounded hover:bg-muted transition-colors">
              <X className="h-4 w-4 text-muted-foreground" />
            </button>
          </div>
        </div>

        {/* Tab bar */}
        <div className="flex border-b border-border px-5 shrink-0 bg-muted/20">
          {(["details", "comments", "attachments"] as const).map((tab) => {
            let label = "Details"
            if (tab === "comments") label = commentCount !== null ? `Comments (${commentCount})` : "Comments"
            if (tab === "attachments") label = attachmentCount !== null ? `Attachments (${attachmentCount})` : "Attachments"
            return (
              <button
                key={tab}
                onClick={() => setDetailTab(tab)}
                className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-colors
                  ${detailTab === tab
                    ? "border-primary text-primary"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                  }`}
              >
                {label}
              </button>
            )
          })}
        </div>

        {/* Scrollable body */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-5">

          {/* Comments tab */}
          {detailTab === "comments" && (
            <CommentsSection
              entityType="task"
              entityId={task.id}
              currentUserId={getJwtSubject() ?? ""}
              isWorkspaceAdmin={isWorkspaceAdmin}
            />
          )}

          {/* Attachments tab */}
          {detailTab === "attachments" && (
            <AttachmentsSection
              entityType="task"
              entityId={task.id}
              currentUserId={getJwtSubject() ?? ""}
              canUpload={true}
              isWorkspaceAdmin={isWorkspaceAdmin}
            />
          )}

          {/* Details tab */}
          {detailTab === "details" && <>

          {/* Key properties grid */}
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-lg bg-muted/40 p-3 border border-border/50">
              <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1">Assignee</p>
              {task.assignee_user_id
                ? <CopyableId id={task.assignee_user_id} />
                : <span className="text-xs text-muted-foreground">Unassigned</span>}
            </div>
            <div className="rounded-lg bg-muted/40 p-3 border border-border/50">
              <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1">Reporter</p>
              {task.reporter_user_id
                ? <CopyableId id={task.reporter_user_id} />
                : <span className="text-xs text-muted-foreground">—</span>}
            </div>
            <div className={`rounded-lg p-3 border ${overdueTask ? "bg-red-500/5 border-red-500/20" : "bg-muted/40 border-border/50"}`}>
              <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1">Due Date</p>
              <div className="flex items-center gap-1">
                {overdueTask && <AlertTriangle className="h-3 w-3 text-red-500 shrink-0" />}
                <span className={`text-xs font-medium ${overdueTask ? "text-red-500" : ""}`}>{formatDate(task.due_date)}</span>
              </div>
              {overdueTask && (
                <p className="text-[10px] text-red-400 mt-0.5">{overdueDays(task)}d overdue</p>
              )}
            </div>
            <div className="rounded-lg bg-muted/40 p-3 border border-border/50">
              <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1">Start Date</p>
              <span className="text-xs">{formatDate(task.start_date)}</span>
            </div>
            {(task.estimated_hours !== null || task.actual_hours !== null) && (
              <>
                <div className="rounded-lg bg-muted/40 p-3 border border-border/50">
                  <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1">Est. Hours</p>
                  <span className="text-xs">{task.estimated_hours !== null ? `${task.estimated_hours}h` : "—"}</span>
                </div>
                <div className="rounded-lg bg-muted/40 p-3 border border-border/50">
                  <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1">Actual Hours</p>
                  <span className="text-xs">{task.actual_hours !== null ? `${task.actual_hours}h` : "—"}</span>
                </div>
              </>
            )}
          </div>

          {/* Linked entity */}
          {task.entity_type && (
            <div className="rounded-lg border border-blue-500/20 bg-blue-500/5 p-3">
              <div className="flex items-center gap-1.5 flex-wrap">
                <Link2 className="h-3.5 w-3.5 text-blue-400 shrink-0" />
                <span className="text-xs font-semibold text-blue-400 capitalize">{task.entity_type.replace(/_/g, " ")}</span>
                {task.entity_name ? (
                  <span className="text-xs font-bold text-foreground px-1">{task.entity_name}</span>
                ) : task.entity_id && <CopyableId id={task.entity_id} />}
                {task.entity_type === "control" && (
                  <a href="/controls" className="text-xs text-blue-400 hover:underline flex items-center gap-0.5 ml-auto">
                    View Controls <ExternalLink className="h-3 w-3" />
                  </a>
                )}
                {task.entity_type === "risk" && (
                  <a href="/risks" className="text-xs text-blue-400 hover:underline flex items-center gap-0.5 ml-auto">
                    View Risks <ExternalLink className="h-3 w-3" />
                  </a>
                )}
              </div>
            </div>
          )}

          <Separator className="opacity-40" />

          {/* Description */}
          {task.description && (
            <div>
              <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">Description</p>
              <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">{task.description}</p>
            </div>
          )}

          {/* Acceptance Criteria — rich checklist with progress ring */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Acceptance Criteria</p>
              {criteriaLines.length > 0 && (
                <div className="flex items-center gap-2">
                  <span className="text-[11px] text-muted-foreground tabular-nums">{checkedCriteria.size}/{criteriaLines.length}</span>
                  {/* Mini progress ring */}
                  <svg className="w-6 h-6 -rotate-90" viewBox="0 0 24 24">
                    <circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" strokeWidth="2.5" className="text-border" />
                    <circle
                      cx="12" cy="12" r="9" fill="none" stroke="currentColor" strokeWidth="2.5"
                      className="text-emerald-500 transition-all duration-500"
                      strokeDasharray={`${2 * Math.PI * 9}`}
                      strokeDashoffset={`${2 * Math.PI * 9 * (1 - criteriaProgress / 100)}`}
                      strokeLinecap="round"
                    />
                  </svg>
                </div>
              )}
            </div>
            {criteriaLines.length > 0 ? (
              <div className="space-y-1.5">
                {/* Progress bar */}
                <div className="w-full bg-muted rounded-full h-1 mb-3">
                  <div
                    className="bg-emerald-500 h-1 rounded-full transition-all duration-300"
                    style={{ width: `${criteriaProgress}%` }}
                  />
                </div>
                {criteriaLines.map((line, i) => {
                  const checked = checkedCriteria.has(i)
                  return (
                    <div
                      key={i}
                      className="flex items-start gap-2.5 p-2 rounded-lg cursor-pointer hover:bg-muted/40 transition-colors group"
                      onClick={() => setCheckedCriteria((prev) => {
                        const next = new Set(prev)
                        if (checked) next.delete(i)
                        else next.add(i)
                        return next
                      })}
                    >
                      <div className={`mt-0.5 shrink-0 w-4 h-4 rounded border-2 flex items-center justify-center transition-all duration-150 ${
                        checked
                          ? "bg-emerald-500 border-emerald-500"
                          : "border-border group-hover:border-emerald-400"
                      }`}>
                        {checked && (
                          <svg className="w-2.5 h-2.5 text-white" viewBox="0 0 12 12" fill="none">
                            <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                        )}
                      </div>
                      <span className={`text-sm leading-snug transition-colors ${checked ? "line-through text-muted-foreground/60" : "text-foreground"}`}>{line}</span>
                    </div>
                  )
                })}

                {/* AI placeholder */}
                <div className="mt-3 rounded-lg border border-dashed border-purple-500/30 bg-purple-500/5 p-2.5 flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] text-purple-400 font-semibold">AI JUSTIFICATION</span>
                    <span className="inline-flex items-center px-1.5 py-0 rounded text-[9px] font-bold uppercase border border-purple-500/30 bg-purple-500/10 text-purple-400">Soon</span>
                  </div>
                  <span className="text-[10px] text-muted-foreground">Auto-evaluate criteria with AI</span>
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No acceptance criteria defined</p>
            )}
          </div>

          {/* Evidence & AI Analysis — evidence_collection tasks only */}
          {task.task_type_code === "evidence_collection" && (
            <>
              <Separator className="opacity-40" />
              <div className="rounded-xl border border-sky-500/20 bg-sky-500/5 p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-lg bg-sky-500/15 flex items-center justify-center">
                      <FileSearch className="h-4 w-4 text-sky-400" />
                    </div>
                    <p className="text-sm font-semibold text-sky-400">Evidence &amp; AI Analysis</p>
                  </div>
                  <button
                    disabled
                    title="AI analysis coming soon"
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-purple-500/30 bg-purple-500/5 text-purple-400/60 text-[11px] font-semibold cursor-not-allowed opacity-60"
                  >
                    <svg className="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M12 3l1.9 5.8H20l-4.9 3.6 1.9 5.8L12 14.6l-5 3.6 1.9-5.8L4 9h6.1z" />
                    </svg>
                    Run AI Analysis
                  </button>
                </div>
                <p className="text-xs text-sky-300/60">
                  No evidence attached yet. Upload files in the Attachments tab.
                </p>
              </div>
            </>
          )}

          {/* Remediation Plan */}
          {task.task_type_code === "control_remediation" && (
            <div>
              <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">Remediation Plan</p>
              {task.remediation_plan ? (
                <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap bg-orange-500/5 border border-orange-500/20 rounded-lg p-3">{task.remediation_plan}</p>
              ) : (
                <p className="text-sm text-muted-foreground">Not defined</p>
              )}
            </div>
          )}

          {/* Resolution Notes */}
          {task.resolution_notes && (
            <div>
              <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-2">Resolution Notes</p>
              <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap bg-emerald-500/5 border border-emerald-500/20 rounded-lg p-3">{task.resolution_notes}</p>
            </div>
          )}

          <Separator className="opacity-40" />

          {/* Co-assignees */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                Co-Assignees ({task.co_assignee_count})
              </p>
              <Button size="sm" variant="ghost" className="h-6 text-xs" onClick={() => setShowAddAssignee(!showAddAssignee)}>
                <UserPlus className="h-3.5 w-3.5 mr-1" /> Add
              </Button>
            </div>
            {showAddAssignee && (
              <div className="flex gap-2 mb-2">
                <Input
                  className="h-7 text-xs"
                  placeholder="User ID"
                  value={addAssigneeUserId}
                  onChange={(e) => setAddAssigneeUserId(e.target.value)}
                />
                <Button size="sm" className="h-7 text-xs" onClick={handleAddAssignee}>Add</Button>
              </div>
            )}
            {assignments.length === 0 ? (
              <p className="text-xs text-muted-foreground">No co-assignees</p>
            ) : (
              <div className="space-y-1">
                {assignments.map((a) => (
                  <div key={a.id} className="flex items-center justify-between">
                    <CopyableId id={a.user_id} />
                    <button
                      onClick={() => handleRemoveAssignee(a.id)}
                      className="text-xs text-muted-foreground hover:text-destructive"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <Separator className="opacity-40" />

          {/* Activity */}
          <div>
            <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-3">Activity</p>
            {loadingEvents ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <RefreshCw className="h-3.5 w-3.5 animate-spin" /> Loading…
              </div>
            ) : events.length === 0 ? (
              <p className="text-sm text-muted-foreground">No activity yet</p>
            ) : (
              <div className="relative pl-4">
                {/* Timeline line */}
                <div className="absolute left-1.5 top-1.5 bottom-1.5 w-px bg-border/60" />
                <div className="space-y-3">
                  {events.map((ev) => (
                    <div key={ev.id} className="flex gap-3 relative">
                      <div className="absolute -left-2.5 top-1 w-3 h-3 rounded-full border-2 border-background bg-border shrink-0" />
                      <div className="flex-1 min-w-0 pl-2">
                        {ev.event_type === "comment_added" ? (
                          <div className="bg-muted/50 rounded-lg p-2.5 text-sm border border-border/50">
                            <p className="text-foreground leading-relaxed">{ev.comment}</p>
                          </div>
                        ) : (
                          <p className="text-sm text-foreground">
                            <span className="font-medium">{EVENT_LABELS[ev.event_type] ?? ev.event_type}</span>
                            {ev.old_value && ev.new_value && (
                              <span className="text-muted-foreground"> {ev.old_value} → {ev.new_value}</span>
                            )}
                            {ev.comment && <span className="text-muted-foreground"> — {ev.comment}</span>}
                          </p>
                        )}
                        <div className="flex items-center gap-2 mt-1">
                          {ev.actor_id && (
                            <span className="text-xs text-muted-foreground font-mono">{truncateId(ev.actor_id)}</span>
                          )}
                          <span className="text-xs text-muted-foreground" title={formatDateTime(ev.occurred_at)}>
                            {formatRelativeTime(ev.occurred_at)}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Comment input */}
          <div className="space-y-2">
            <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Add Comment</p>
            <textarea
              className="w-full rounded-lg border border-border bg-background text-sm px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-ring min-h-[72px]"
              placeholder="Write a comment…"
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
            />
            <Button
              size="sm"
              disabled={!commentText.trim() || submittingComment}
              onClick={handleComment}
            >
              {submittingComment ? <RefreshCw className="h-3.5 w-3.5 animate-spin mr-1" /> : null}
              Add Comment
            </Button>
          </div>

          </>}
        </div>
      </div>
    </>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Resolution Dialog
// ─────────────────────────────────────────────────────────────────────────────

interface ResolutionDialogProps {
  open: boolean
  onClose: () => void
  onConfirm: (notes: string) => void
  loading: boolean
}

function ResolutionDialog({ open, onClose, onConfirm, loading }: ResolutionDialogProps) {
  const [notes, setNotes] = useState("")
  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Resolve Task</DialogTitle>
          <DialogDescription>
            Please confirm you have completed this task and provide resolution notes.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-2">
          <Label htmlFor="resolution-notes">Resolution Notes <span className="text-red-500">*</span></Label>
          <textarea
            id="resolution-notes"
            className="w-full rounded-lg border border-border bg-background text-sm px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-ring min-h-[96px]"
            placeholder="Describe what was done to resolve this task…"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={loading}>Cancel</Button>
          <Button
            disabled={!notes.trim() || loading}
            onClick={() => onConfirm(notes.trim())}
          >
            {loading ? <RefreshCw className="h-3.5 w-3.5 animate-spin mr-1" /> : null}
            Confirm Resolved
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Create Task Dialog — org/workspace from context
// ─────────────────────────────────────────────────────────────────────────────

interface CreateDialogProps {
  open: boolean
  onClose: () => void
  onCreated: () => void
  taskTypes: DimensionResponse[]
  defaultOrgId?: string
  defaultWorkspaceId?: string
}

const EMPTY_CREATE: CreateTaskRequest = {
  task_type_code: "",
  priority_code: "medium",
  org_id: "",
  title: "",
}

function CreateTaskDialog({ open, onClose, onCreated, taskTypes, defaultOrgId, defaultWorkspaceId }: CreateDialogProps) {
  const { orgs, workspaces: contextWorkspaces } = useOrgWorkspace()
  const [form, setForm] = useState<CreateTaskRequest>(() => ({
    ...EMPTY_CREATE,
    org_id: defaultOrgId ?? "",
    workspace_id: defaultWorkspaceId ?? "",
  }))
  const [criteriaItems, setCriteriaItems] = useState<string[]>([""])
  const [assigneeEmail, setAssigneeEmail] = useState("")
  const [showGrcLink, setShowGrcLink] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // When dialog opens, sync org/workspace from context
  useEffect(() => {
    if (open) {
      setForm((prev) => ({
        ...prev,
        org_id: defaultOrgId ?? prev.org_id,
        workspace_id: defaultWorkspaceId ?? prev.workspace_id,
      }))
    }
  }, [open, defaultOrgId, defaultWorkspaceId])

  const orgName = orgs.find((o) => o.id === (defaultOrgId ?? form.org_id))?.name
  const wsName = contextWorkspaces.find((w) => w.id === (defaultWorkspaceId ?? form.workspace_id))?.name

  const set = useCallback(<K extends keyof CreateTaskRequest>(k: K, v: CreateTaskRequest[K]) => {
    setForm((prev) => ({ ...prev, [k]: v }))
  }, [])

  const handleSubmit = useCallback(async () => {
    const orgId = defaultOrgId ?? form.org_id
    const wsId = defaultWorkspaceId ?? form.workspace_id
    if (!form.title.trim() || !form.task_type_code || !orgId.trim()) {
      setError("Title and Task Type are required.")
      return
    }
    if (!wsId?.trim()) {
      setError("No workspace selected — use the workspace switcher at the top.")
      return
    }
    setLoading(true)
    setError(null)
    try {
      const parsedAssignees = parseAssigneeEmails(assigneeEmail)
      if (parsedAssignees.invalid.length > 0) {
        setError(`Invalid email(s): ${parsedAssignees.invalid.join(", ")}`)
        setLoading(false)
        return
      }
      const criteriaText = criteriaItems.filter(l => l.trim()).join("\n") || undefined
      const payload: CreateTaskRequest = {
        ...form,
        title: form.title.trim(),
        org_id: orgId.trim(),
        description: form.description?.trim() || undefined,
        workspace_id: wsId!.trim(),
        entity_type: showGrcLink ? form.entity_type?.trim() || undefined : undefined,
        entity_id: showGrcLink ? form.entity_id?.trim() || undefined : undefined,
        acceptance_criteria: criteriaText,
        remediation_plan: form.task_type_code === "control_remediation" ? form.remediation_plan?.trim() || undefined : undefined,
      }
      let created = await createTask(payload)
      if (parsedAssignees.emails.length > 0) {
        const assignments = await Promise.all(
          parsedAssignees.emails.map((email) => addAssignment(created.id, { email, role: "co_assignee" })),
        )
        const primaryAssigneeId = assignments[0]?.user_id
        if (primaryAssigneeId) {
          created = await updateTask(created.id, { assignee_user_id: primaryAssigneeId })
        }
      }
      setForm({ ...EMPTY_CREATE, org_id: orgId, workspace_id: wsId ?? "" })
      setCriteriaItems([""])
      setAssigneeEmail("")
      setShowGrcLink(false)
      onCreated()
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create task")
    } finally {
      setLoading(false)
    }
  }, [form, criteriaItems, assigneeEmail, showGrcLink, defaultOrgId, defaultWorkspaceId, onCreated, onClose])

  function handleAIFilled(fields: Record<string, string>) {
    if (fields.title) set("title", fields.title)
    if (fields.description) set("description", fields.description)
    if (fields.task_type_code && taskTypes.some((t) => t.code === fields.task_type_code)) set("task_type_code", fields.task_type_code)
    if (fields.priority_code && ["critical", "high", "medium", "low"].includes(fields.priority_code)) set("priority_code", fields.priority_code)
    if (fields.acceptance_criteria) {
      const lines = fields.acceptance_criteria.split("\n").filter(l => l.trim())
      setCriteriaItems(lines.length > 0 ? lines : [""])
    }
    if (fields.remediation_plan) set("remediation_plan", fields.remediation_plan)
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) { setForm({ ...EMPTY_CREATE, org_id: defaultOrgId ?? "", workspace_id: defaultWorkspaceId ?? "" }); setError(null); onClose() } }}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-primary/10 flex items-center justify-center">
              <Plus className="h-4 w-4 text-primary" />
            </div>
            New Task
          </DialogTitle>
          <DialogDescription>Create a new GRC task.</DialogDescription>
        </DialogHeader>
        <FormFillChat
          entityType="task"
          orgId={defaultOrgId}
          workspaceId={defaultWorkspaceId}
          pageContext={{ org_id: defaultOrgId, workspace_id: defaultWorkspaceId }}
          getFormValues={() => ({ title: form.title, description: form.description, task_type_code: form.task_type_code, priority_code: form.priority_code })}
          onFilled={handleAIFilled}
          placeholder="e.g. review firewall rules for SOC 2 — link to the right control"
        />

        {/* Context info chip */}
        {(orgName || wsName) && (
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-muted/50 border border-border/60 text-xs text-muted-foreground">
            <span className="font-medium text-foreground">Creating in:</span>
            {orgName && <span className="px-2 py-0.5 rounded-full bg-background border border-border">{orgName}</span>}
            {wsName && (
              <>
                <span>/</span>
                <span className="px-2 py-0.5 rounded-full bg-background border border-border">{wsName}</span>
              </>
            )}
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          {/* Title — full width */}
          <div className="col-span-2 space-y-1.5">
            <Label htmlFor="c-title">Title <span className="text-red-500">*</span></Label>
            <Input id="c-title" placeholder="Task title" value={form.title} onChange={(e) => set("title", e.target.value)} />
          </div>

          {/* Description — full width */}
          <div className="col-span-2 space-y-1.5">
            <Label htmlFor="c-desc">Description</Label>
            <textarea
              id="c-desc"
              className="w-full rounded-lg border border-border bg-background text-sm px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-ring min-h-[72px]"
              placeholder="Optional description…"
              value={form.description ?? ""}
              onChange={(e) => set("description", e.target.value)}
            />
          </div>

          {/* Task Type */}
          <div className="space-y-1.5">
            <Label htmlFor="c-type">Task Type <span className="text-red-500">*</span></Label>
            <select
              id="c-type"
              className="w-full rounded-lg border border-border bg-background text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-ring"
              value={form.task_type_code}
              onChange={(e) => set("task_type_code", e.target.value)}
            >
              <option value="">Select type…</option>
              {taskTypes.map((t) => <option key={t.code} value={t.code}>{t.name}</option>)}
            </select>
          </div>

          {/* Priority */}
          <div className="space-y-1.5">
            <Label htmlFor="c-priority">Priority</Label>
            <select
              id="c-priority"
              className="w-full rounded-lg border border-border bg-background text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-ring"
              value={form.priority_code}
              onChange={(e) => set("priority_code", e.target.value)}
            >
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          {/* Assignee */}
          <div className="col-span-2 space-y-1.5">
            <Label htmlFor="c-assignee">Assignee Emails</Label>
            <Input
              id="c-assignee"
              placeholder="alice@company.com, bob@company.com"
              value={assigneeEmail}
              onChange={(e) => setAssigneeEmail(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">Use one email or multiple emails separated by commas.</p>
          </div>

          {/* Due Date */}
          <div className="space-y-1.5">
            <Label htmlFor="c-due">Due Date</Label>
            <Input id="c-due" type="date" value={form.due_date ?? ""} onChange={(e) => set("due_date", e.target.value)} />
          </div>

          {/* Acceptance Criteria — full width */}
          <div className="col-span-2 space-y-2">
            <div className="flex items-center justify-between">
              <Label>Acceptance Criteria</Label>
              <button
                type="button"
                onClick={() => setCriteriaItems(prev => [...prev, ""])}
                className="flex items-center gap-1 text-xs text-primary hover:text-primary/80 transition-colors"
              >
                <Plus className="h-3 w-3" /> Add item
              </button>
            </div>
            <div className="space-y-2">
              {criteriaItems.map((item, i) => (
                <div key={i} className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded border border-border shrink-0" />
                  <Input
                    placeholder={`Criteria ${i + 1}…`}
                    value={item}
                    onChange={e => {
                      const next = [...criteriaItems]
                      next[i] = e.target.value
                      setCriteriaItems(next)
                    }}
                    className="flex-1"
                  />
                  {criteriaItems.length > 1 && (
                    <button
                      type="button"
                      onClick={() => setCriteriaItems(prev => prev.filter((_, j) => j !== i))}
                      className="p-1 text-muted-foreground hover:text-destructive transition-colors shrink-0"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Remediation Plan — control_remediation only */}
          {form.task_type_code === "control_remediation" && (
            <div className="col-span-2 space-y-1.5">
              <Label htmlFor="c-rem">Remediation Plan</Label>
              <textarea
                id="c-rem"
                className="w-full rounded-lg border border-border bg-background text-sm px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-ring min-h-[72px]"
                placeholder="Describe the remediation steps…"
                value={form.remediation_plan ?? ""}
                onChange={(e) => set("remediation_plan", e.target.value)}
              />
            </div>
          )}

          {/* GRC Link — collapsible */}
          <div className="col-span-2">
            <button
              type="button"
              onClick={() => setShowGrcLink(!showGrcLink)}
              className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              <Link2 className="h-3.5 w-3.5" />
              GRC Entity Link
              {showGrcLink ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
            </button>
            {showGrcLink && (
              <div className="grid grid-cols-2 gap-4 mt-3">
                <div className="space-y-1.5">
                  <Label htmlFor="c-etype">Entity Type</Label>
                  <select
                    id="c-etype"
                    className="w-full rounded-lg border border-border bg-background text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-ring"
                    value={form.entity_type ?? ""}
                    onChange={(e) => set("entity_type", e.target.value || undefined)}
                  >
                    <option value="">None</option>
                    <option value="control">Control</option>
                    <option value="risk">Risk</option>
                    <option value="framework">Framework</option>
                    <option value="test">Test</option>
                  </select>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="c-eid">Entity ID</Label>
                  <Input id="c-eid" placeholder="UUID" value={form.entity_id ?? ""} onChange={(e) => set("entity_id", e.target.value)} />
                </div>
              </div>
            )}
          </div>
        </div>

        {error && (
          <div className="rounded-lg bg-red-500/10 border border-red-500/20 px-3 py-2 text-sm text-red-500 mt-2">
            {error}
          </div>
        )}

        <DialogFooter className="mt-4">
          <Button variant="outline" onClick={onClose} disabled={loading}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={loading}>
            {loading ? <RefreshCw className="h-3.5 w-3.5 animate-spin mr-1" /> : <Plus className="h-3.5 w-3.5 mr-1" />}
            Create Task
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Edit Task Dialog
// ─────────────────────────────────────────────────────────────────────────────

const STATUS_TRANSITIONS: Record<string, string[]> = {
  open: ["in_progress", "cancelled"],
  in_progress: ["pending_verification", "open", "cancelled"],
  pending_verification: ["resolved", "in_progress"],
  resolved: [],
  cancelled: [],
  overdue: ["in_progress", "cancelled"],
}

interface EditDialogProps {
  open: boolean
  task: TaskResponse | null
  onClose: () => void
  onUpdated: (updated: TaskResponse) => void
  statuses: TaskStatusResponse[]
}

function EditTaskDialog({ open, task, onClose, onUpdated, statuses }: EditDialogProps) {
  const [form, setForm] = useState<UpdateTaskRequest>({})
  const [criteriaItems, setCriteriaItems] = useState<string[]>([""])
  const [assigneeEmail, setAssigneeEmail] = useState("")
  const [showResolution, setShowResolution] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (task) {
      setForm({
        title: task.title,
        description: task.description ?? "",
        priority_code: task.priority_code,
        status_code: task.status_code,
        due_date: task.due_date ?? "",
        resolution_notes: task.resolution_notes ?? "",
        remediation_plan: task.remediation_plan ?? "",
      })
      setAssigneeEmail("")
      const lines = task.acceptance_criteria
        ? task.acceptance_criteria.split("\n").filter(l => l.trim())
        : []
      setCriteriaItems(lines.length > 0 ? lines : [""])
      setShowResolution(task.status_code === "resolved")
    }
  }, [task])

  const set = useCallback(<K extends keyof UpdateTaskRequest>(k: K, v: UpdateTaskRequest[K]) => {
    setForm((prev) => {
      const next = { ...prev, [k]: v }
      if (k === "status_code") {
        setShowResolution(v === "resolved")
      }
      return next
    })
  }, [])

  const handleSubmit = useCallback(async () => {
    if (!task) return
    if (form.status_code === "resolved" && !form.resolution_notes?.trim()) {
      setError("Resolution notes are required when resolving a task.")
      return
    }
    setLoading(true)
    setError(null)
    try {
      const parsedAssignees = parseAssigneeEmails(assigneeEmail)
      if (parsedAssignees.invalid.length > 0) {
        setError(`Invalid email(s): ${parsedAssignees.invalid.join(", ")}`)
        setLoading(false)
        return
      }
      const criteriaText = criteriaItems.filter(l => l.trim()).join("\n") || undefined
      const payload: UpdateTaskRequest = {
        title: form.title?.trim() || undefined,
        description: form.description?.trim() || undefined,
        priority_code: form.priority_code || undefined,
        status_code: form.status_code || undefined,
        assignee_user_id: parsedAssignees.emails.length > 0 ? undefined : (task.assignee_user_id ?? undefined),
        due_date: form.due_date?.trim() || undefined,
        acceptance_criteria: criteriaText,
        resolution_notes: form.resolution_notes?.trim() || undefined,
        remediation_plan: form.remediation_plan?.trim() || undefined,
      }
      let updated = await updateTask(task.id, payload)
      if (parsedAssignees.emails.length > 0) {
        const assignments = await Promise.all(
          parsedAssignees.emails.map((email) => addAssignment(task.id, { email, role: "co_assignee" })),
        )
        const primaryAssigneeId = assignments[0]?.user_id
        if (primaryAssigneeId) {
          updated = await updateTask(task.id, { assignee_user_id: primaryAssigneeId })
        }
      }
      onUpdated(updated)
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update task")
    } finally {
      setLoading(false)
    }
  }, [task, form, criteriaItems, assigneeEmail, onUpdated, onClose])

  function handleAIFilled(fields: Record<string, string>) {
    if (fields.title) setForm((prev) => ({ ...prev, title: fields.title }))
    if (fields.description) setForm((prev) => ({ ...prev, description: fields.description }))
    if (fields.priority_code && ["critical", "high", "medium", "low"].includes(fields.priority_code)) setForm((prev) => ({ ...prev, priority_code: fields.priority_code }))
    if (fields.acceptance_criteria) setCriteriaItems(fields.acceptance_criteria.split("\n").filter(l => l.trim()))
    if (fields.remediation_plan) setForm((prev) => ({ ...prev, remediation_plan: fields.remediation_plan }))
  }

  if (!task) return null

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) { setError(null); onClose() } }}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit Task</DialogTitle>
          <DialogDescription className="truncate">{task.title}</DialogDescription>
        </DialogHeader>

        <FormFillChat
          entityType="task"
          orgId={null}
          workspaceId={null}
          pageContext={{ entity_id: task.entity_id ?? undefined, entity_type: task.entity_type ?? undefined }}
          getFormValues={() => ({ title: form.title ?? "", description: form.description ?? "", priority_code: form.priority_code ?? "", acceptance_criteria: criteriaItems.filter(l => l.trim()).join("\n"), remediation_plan: form.remediation_plan ?? "" })}
          onFilled={handleAIFilled}
        />

        <div className="grid grid-cols-2 gap-4">
          <div className="col-span-2 space-y-1.5">
            <Label>Title</Label>
            <Input value={form.title ?? ""} onChange={(e) => set("title", e.target.value)} />
          </div>

          <div className="col-span-2 space-y-1.5">
            <Label>Description</Label>
            <textarea
              className="w-full rounded-lg border border-border bg-background text-sm px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-ring min-h-[72px]"
              value={form.description ?? ""}
              onChange={(e) => set("description", e.target.value)}
            />
          </div>

          <div className="space-y-1.5">
            <Label>Status</Label>
            <select
              className="w-full rounded-lg border border-border bg-background text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-ring"
              value={form.status_code ?? ""}
              onChange={(e) => set("status_code", e.target.value)}
            >
              {statuses
                .filter((s) => {
                  const current = task.status_code
                  const allowed = STATUS_TRANSITIONS[current] ?? []
                  return s.code === current || allowed.includes(s.code)
                })
                .map((s) => <option key={s.code} value={s.code}>{s.name}</option>)}
            </select>
            <p className="text-xs text-muted-foreground">Only valid next states are shown</p>
          </div>

          <div className="space-y-1.5">
            <Label>Priority</Label>
            <select
              className="w-full rounded-lg border border-border bg-background text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-ring"
              value={form.priority_code ?? ""}
              onChange={(e) => set("priority_code", e.target.value)}
            >
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          <div className="col-span-2 space-y-1.5">
            <Label>Assignee Emails</Label>
            <Input
              placeholder={task.assignee_user_id ? "alice@company.com, bob@company.com" : "alice@company.com, bob@company.com"}
              value={assigneeEmail}
              onChange={(e) => setAssigneeEmail(e.target.value)}
            />
            {task.assignee_user_id && !assigneeEmail && (
              <p className="text-xs text-muted-foreground">Currently assigned. Add one or more emails (comma separated) to assign additional users and set the first as primary.</p>
            )}
            {!task.assignee_user_id && (
              <p className="text-xs text-muted-foreground">Use one email or multiple emails separated by commas.</p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label>Due Date</Label>
            <Input type="date" value={form.due_date ?? ""} onChange={(e) => set("due_date", e.target.value)} />
          </div>

          <div className="col-span-2 space-y-2">
            <div className="flex items-center justify-between">
              <Label>Acceptance Criteria</Label>
              <button
                type="button"
                onClick={() => setCriteriaItems(prev => [...prev, ""])}
                className="flex items-center gap-1 text-xs text-primary hover:text-primary/80 transition-colors"
              >
                <Plus className="h-3 w-3" /> Add item
              </button>
            </div>
            <div className="space-y-2">
              {criteriaItems.map((item, i) => (
                <div key={i} className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded border border-border shrink-0" />
                  <Input
                    placeholder={`Criteria ${i + 1}…`}
                    value={item}
                    onChange={e => {
                      const next = [...criteriaItems]
                      next[i] = e.target.value
                      setCriteriaItems(next)
                    }}
                    className="flex-1"
                  />
                  {criteriaItems.length > 1 && (
                    <button
                      type="button"
                      onClick={() => setCriteriaItems(prev => prev.filter((_, j) => j !== i))}
                      className="p-1 text-muted-foreground hover:text-destructive transition-colors shrink-0"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {task.task_type_code === "control_remediation" && (
            <div className="col-span-2 space-y-1.5">
              <Label>Remediation Plan</Label>
              <textarea
                className="w-full rounded-lg border border-border bg-background text-sm px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-ring min-h-[72px]"
                value={form.remediation_plan ?? ""}
                onChange={(e) => set("remediation_plan", e.target.value)}
              />
            </div>
          )}

          {showResolution && (
            <div className="col-span-2 space-y-1.5">
              <Label>
                Resolution Notes <span className="text-red-500">*</span>
                <span className="text-xs text-muted-foreground ml-1">(required when resolving)</span>
              </Label>
              <textarea
                className="w-full rounded-lg border border-border bg-background text-sm px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-ring min-h-[72px]"
                placeholder="Describe what was done to resolve this task…"
                value={form.resolution_notes ?? ""}
                onChange={(e) => set("resolution_notes", e.target.value)}
              />
            </div>
          )}
        </div>

        {error && (
          <div className="rounded-lg bg-red-500/10 border border-red-500/20 px-3 py-2 text-sm text-red-500 mt-2">
            {error}
          </div>
        )}

        <DialogFooter className="mt-4">
          <Button variant="outline" onClick={onClose} disabled={loading}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={loading}>
            {loading ? <RefreshCw className="h-3.5 w-3.5 animate-spin mr-1" /> : null}
            Save Changes
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Board View
// ─────────────────────────────────────────────────────────────────────────────

interface BoardViewProps {
  tasks: TaskResponse[]
  onSelect: (task: TaskResponse) => void
  onEdit: (task: TaskResponse) => void
  onDelete: (task: TaskResponse) => void
  onClone: (task: TaskResponse) => void
}

function BoardView({ tasks, onSelect, onEdit, onDelete, onClone }: BoardViewProps) {
  const columns = useMemo(() => {
    return BOARD_COLUMNS.map((statusCode) => ({
      statusCode,
      meta: STATUS_META[statusCode] ?? { label: statusCode, headerCls: "bg-muted border-border text-muted-foreground", iconColor: "" },
      tasks: tasks.filter((t) => t.status_code === statusCode),
    }))
  }, [tasks])

  return (
    <div className="flex gap-4 overflow-x-auto pb-4">
      {columns.map((col) => (
        <div key={col.statusCode} className="flex flex-col shrink-0 w-72">
          <div className={`flex items-center justify-between px-3 py-2.5 rounded-t-xl border ${col.meta.headerCls} mb-0`}>
            <span className="text-xs font-bold tracking-wide">{col.meta.label}</span>
            <span className={`px-2 py-0.5 rounded-full text-[11px] font-bold border ${col.meta.headerCls}`}>{col.tasks.length}</span>
          </div>
          <div className="flex flex-col gap-2 min-h-[120px] rounded-b-xl border-x border-b border-border bg-muted/20 p-2">
            {col.tasks.length === 0 ? (
              <div className="flex-1 flex items-center justify-center py-8 text-xs text-muted-foreground/50">
                No tasks
              </div>
            ) : (
              col.tasks.map((t) => {
                const over = isOverdue(t)
                const pm = PRIORITY_META[t.priority_code]
                return (
                  <div
                    key={t.id}
                    onClick={() => onSelect(t)}
                    className={`bg-card border border-border rounded-lg p-3 cursor-pointer hover:shadow-md hover:border-primary/30 transition-all border-l-[3px] ${pm?.border ?? "border-l-border"}`}
                  >
                    <p className="text-sm font-medium text-foreground line-clamp-2 mb-2 leading-snug">{t.title}</p>
                    <div className="flex flex-wrap gap-1 mb-2">
                      <PriorityBadge code={t.priority_code} />
                    </div>
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        <span className={over ? "text-red-500 font-medium" : ""}>{formatDate(t.due_date)}</span>
                        {over && <AlertTriangle className="h-3 w-3 text-red-500" />}
                      </div>
                      <div className="flex items-center gap-1.5">
                        {t.blocker_count > 0 && (
                          <span className="flex items-center gap-0.5 text-orange-500">
                            <GitBranch className="h-3 w-3" />{t.blocker_count}
                          </span>
                        )}
                        {t.assignee_user_id && <User2 className="h-3 w-3" />}
                      </div>
                    </div>
                    <div className="flex justify-end gap-1 mt-2 border-t border-border/40 pt-2">
                      <button
                        onClick={(e) => { e.stopPropagation(); onEdit(t) }}
                        className="p-1 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                        title="Edit"
                      >
                        <Pencil className="h-3 w-3" />
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); onClone(t) }}
                        className="p-1 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                        title="Clone"
                      >
                        <Copy className="h-3 w-3" />
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); onDelete(t) }}
                        className="p-1 rounded hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors"
                        title="Delete"
                      >
                        <Trash2 className="h-3 w-3" />
                      </button>
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Page
// ─────────────────────────────────────────────────────────────────────────────

export default function TasksPage() {
  const { selectedOrgId, selectedWorkspaceId, ready } = useOrgWorkspace()
  const { isWorkspaceAdmin, canWrite } = useAccess()
  const canCreateTask = canWrite("task_management")

  // Data
  const [tasks, setTasks] = useState<TaskResponse[]>([])
  const [totalTasks, setTotalTasks] = useState(0)
  const [summary, setSummary] = useState<TaskSummaryResponse | null>(null)
  const [taskTypes, setTaskTypes] = useState<DimensionResponse[]>([])
  const [statuses, setStatuses] = useState<TaskStatusResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Current user
  const [currentUserId, setCurrentUserId] = useState<string | null>(null)

  // Filters
  const [filters, setFilters] = useState<TaskListFilters & { orgId?: string; workspaceId?: string }>({})
  const [searchText, setSearchText] = useState("")
  const [myTasksOn, setMyTasksOn] = useState(false)
  const [summaryFilter, setSummaryFilter] = useState<string | null>(null)
  const [sortBy, setSortBy] = useState("created_at")
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc")
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false)

  // Pagination
  const PAGE_SIZE = 50
  const [page, setPage] = useState(0)

  // Bulk select
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [bulkLoading, setBulkLoading] = useState(false)
  const [bulkStatusCode, setBulkStatusCode] = useState("")
  const [bulkPriority, setBulkPriority] = useState("")
  const [exportLoading, setExportLoading] = useState(false)

  // View
  const [viewMode, setViewMode] = useState<"list" | "board" | "spreadsheet">("list")

  // Import result dialog
  const [importResult, setImportResult] = useState<ImportResult | null>(null)
  const [importResultOpen, setImportResultOpen] = useState(false)

  // Dialogs / panel
  const [showCreate, setShowCreate] = useState(false)
  const [editTask, setEditTask] = useState<TaskResponse | null>(null)
  const [detailTask, setDetailTask] = useState<TaskResponse | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<TaskResponse | null>(null)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => { setCurrentUserId(getJwtSubject()) }, [])

  useEffect(() => {
    Promise.all([listTaskTypes(), listTaskStatuses()]).then(([types, sts]) => {
      setTaskTypes(types)
      setStatuses(sts)
    }).catch(() => {})
  }, [])

  const effectiveFilters = useMemo(() => {
    const f: TaskListFilters & { orgId?: string; workspaceId?: string } = {
      ...filters,
      sort_by: sortBy,
      sort_dir: sortDir,
      limit: PAGE_SIZE,
      offset: page * PAGE_SIZE,
      orgId: selectedOrgId || undefined,
      workspaceId: selectedWorkspaceId || undefined,
    }
    if (myTasksOn && currentUserId) f.assignee_user_id = currentUserId
    if (summaryFilter === "overdue") {
      f.is_overdue = true
      f.status_code = undefined
    } else if (summaryFilter) {
      f.status_code = summaryFilter
      f.is_overdue = undefined
    }
    return f
  }, [filters, sortBy, sortDir, myTasksOn, currentUserId, summaryFilter, page, selectedOrgId, selectedWorkspaceId])

  const loadTasks = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [taskData, summaryData] = await Promise.all([
        listTasks(effectiveFilters),
        getTaskSummary(effectiveFilters.orgId, effectiveFilters.workspaceId),
      ])
      setTasks(taskData.items)
      setTotalTasks(taskData.total)
      setSummary(summaryData)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load tasks")
    } finally {
      setLoading(false)
    }
  }, [effectiveFilters])

  useEffect(() => { if (ready) loadTasks() }, [loadTasks, ready])

  // Evidence verdicts for badge display on task rows
  // Reset on every task list change so stale verdicts from a previous filter don't persist
  const [evidenceVerdicts, setEvidenceVerdicts] = useState<Record<string, string>>({})
  useEffect(() => {
    setEvidenceVerdicts({})
    if (tasks.length === 0) return
    getEvidenceBatchVerdicts(tasks.map(t => t.id)).then(res => {
      setEvidenceVerdicts(res.verdicts)
    }).catch(() => {})
  }, [tasks])

  const displayedTasks = useMemo(() => {
    if (!searchText.trim()) return tasks
    const q = searchText.toLowerCase()
    return tasks.filter((t) =>
      t.title.toLowerCase().includes(q) ||
      (t.description?.toLowerCase().includes(q) ?? false)
    )
  }, [tasks, searchText])

  const updateFilters = useCallback((updater: (prev: TaskListFilters & { orgId?: string; workspaceId?: string }) => TaskListFilters & { orgId?: string; workspaceId?: string }) => {
    setFilters(updater)
    setPage(0)
    setSelectedIds(new Set())
  }, [])

  const handleSummaryFilter = useCallback((key: string | null) => {
    setSummaryFilter(key)
    setPage(0)
    setSelectedIds(new Set())
  }, [])

  const handleDeleteConfirmed = useCallback(async () => {
    if (!deleteConfirm) return
    setDeleting(true)
    try {
      await deleteTask(deleteConfirm.id)
      setDeleteConfirm(null)
      if (detailTask?.id === deleteConfirm.id) setDetailTask(null)
      await loadTasks()
    } catch {
      // ignore
    } finally {
      setDeleting(false)
    }
  }, [deleteConfirm, detailTask, loadTasks])

  const handleClone = useCallback(async (task: TaskResponse) => {
    try {
      await cloneTask(task.id)
      await loadTasks()
    } catch {
      // ignore
    }
  }, [loadTasks])

  const handleCreated = useCallback(() => { loadTasks() }, [loadTasks])

  const handleUpdated = useCallback(async (updatedTask?: TaskResponse) => {
    if (updatedTask && detailTask?.id === updatedTask.id) setDetailTask(updatedTask)
    await loadTasks()
    if (!updatedTask && detailTask) {
      getTask(detailTask.id).then((t) => setDetailTask(t)).catch(() => {})
    }
  }, [loadTasks, detailTask])

  const toggleSortDir = useCallback(() => { setSortDir((d) => (d === "asc" ? "desc" : "asc")) }, [])

  const handleExport = useCallback(async () => {
    setExportLoading(true)
    try {
      const blob = await exportTasksCsv(effectiveFilters)
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `tasks_export_${new Date().toISOString().slice(0, 10)}.csv`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch {
      // ignore
    } finally {
      setExportLoading(false)
    }
  }, [effectiveFilters])

  // Spreadsheet rows — built from displayedTasks so active filters carry into spreadsheet view
  const spreadsheetRows = useMemo<TaskSpreadsheetRow[]>(() => 
    displayedTasks.map((t) => ({
      id: t.id,
      title: t.title,
      description: t.description ?? "",
      status: t.status_code ?? "",
      priority: t.priority_code ?? "",
      due_date: t.due_date ? t.due_date.slice(0, 10) : "",
      assignee_name: t.assignee_user_id ?? "",
      assignee_user_id: t.assignee_user_id ?? "",
      entity_type: t.entity_type ?? "",
      entity_id: t.entity_id ?? "",
    })),
    [displayedTasks]
  )

  async function handleSpreadsheetExport(format: "csv" | "json" | "xlsx") {
    const blob = await exportTasks(
      { orgId: selectedOrgId || undefined, workspaceId: selectedWorkspaceId || undefined },
      format,
    )
    const ext = format
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `tasks_export_${new Date().toISOString().split("T")[0]}.${ext}`
    a.click()
    URL.revokeObjectURL(url)
  }

  async function handleSpreadsheetImport(file: File, dryRun: boolean) {
    const result = await importTasks(
      file,
      { orgId: selectedOrgId || undefined, workspaceId: selectedWorkspaceId || undefined },
      dryRun,
    )
    const importRes: ImportResult = {
      created: result.created,
      updated: result.updated,
      skipped: result.skipped,
      warnings: result.warnings ?? [],
      errors: result.errors ?? [],
      dry_run: dryRun,
    }
    setImportResult(importRes)
    setImportResultOpen(true)
    if (!dryRun) await loadTasks()
  }

  async function handleSpreadsheetSave(row: TaskSpreadsheetRow) {
    if (!row.id) return
    await updateTask(row.id, {
      title: row.title,
      description: row.description || undefined,
      status_code: row.status || undefined,
      priority_code: row.priority || undefined,
      due_date: row.due_date || undefined,
    })
    await loadTasks()
  }

  async function handleImportCommit() {
    if (!importResult) return
    setImportResultOpen(false)
    setImportResult(null)
  }

  async function handleDownloadTemplate(format: "csv" | "xlsx") {
    const { getTasksImportTemplate } = await import("@/lib/api/grc")
    const blob = await getTasksImportTemplate(format)
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `tasks_template.${format}`
    a.click()
    URL.revokeObjectURL(url)
  }

  const allPageSelected = useMemo(() =>
    displayedTasks.length > 0 && displayedTasks.every((t) => selectedIds.has(t.id)),
    [displayedTasks, selectedIds]
  )
  const someSelected = selectedIds.size > 0

  const toggleSelectAll = useCallback(() => {
    if (allPageSelected) setSelectedIds(new Set())
    else setSelectedIds(new Set(displayedTasks.map((t) => t.id)))
  }, [allPageSelected, displayedTasks])

  const toggleSelectOne = useCallback((id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  const handleBulkUpdate = useCallback(async () => {
    if (!someSelected) return
    if (!bulkStatusCode && !bulkPriority) return
    setBulkLoading(true)
    try {
      await bulkUpdateTasks({
        task_ids: Array.from(selectedIds),
        status_code: bulkStatusCode || undefined,
        priority_code: bulkPriority || undefined,
      })
      setSelectedIds(new Set())
      setBulkStatusCode("")
      setBulkPriority("")
      await loadTasks()
    } catch {
      // ignore
    } finally {
      setBulkLoading(false)
    }
  }, [someSelected, bulkStatusCode, bulkPriority, selectedIds, loadTasks])

  const totalPages = Math.max(1, Math.ceil(totalTasks / PAGE_SIZE))

  if (loading && tasks.length === 0) {
    return (
      <div className="flex flex-col gap-5 p-6 max-w-screen-2xl mx-auto">
        <div className="h-8 w-48 rounded-lg bg-muted animate-pulse" />
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {[1,2,3,4,5,6].map((i) => <div key={i} className="h-24 rounded-xl bg-muted animate-pulse" />)}
        </div>
        <div className="h-14 w-full rounded-xl bg-muted animate-pulse" />
        <div className="space-y-2">
          {[1,2,3,4,5,6].map((i) => <div key={i} className="h-14 rounded-xl bg-muted animate-pulse" />)}
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-5 p-6 max-w-screen-2xl mx-auto">

      {/* Page header */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
            <CheckSquare className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-foreground tracking-tight">Tasks</h1>
            <p className="text-sm text-muted-foreground">GRC tasks, remediations &amp; work items</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <OrgWorkspaceSwitcher />
          <ReadOnlyBanner />
          <Button variant="outline" size="sm" onClick={loadTasks} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-1.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          {canCreateTask && (
            <Button size="sm" onClick={() => setShowCreate(true)} className="gap-1.5">
              <Plus className="h-4 w-4" />
              New Task
            </Button>
          )}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-500 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {/* Summary Stat Cards */}
      <SummaryBar summary={summary} activeFilter={summaryFilter} onFilterClick={handleSummaryFilter} />

      {/* Active filter chip */}
      {summaryFilter && (
        <div className="flex items-center gap-2 text-sm">
          <span className="text-muted-foreground text-xs">Filtered by:</span>
          <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${
            summaryFilter === "overdue"
              ? "bg-red-500/10 border-red-500/30 text-red-500"
              : STATUS_META[summaryFilter]?.cls ?? "bg-muted border-border text-muted-foreground"
          }`}>
            {summaryFilter === "overdue" ? "Overdue" : STATUS_META[summaryFilter]?.label ?? summaryFilter}
            <button onClick={() => setSummaryFilter(null)} className="hover:opacity-70 transition-opacity">
              <X className="h-3 w-3" />
            </button>
          </span>
        </div>
      )}

      {/* Filter Bar */}
      <Card className="rounded-xl">
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-3">
            {/* Search */}
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                className="pl-9 h-9"
                placeholder="Search tasks…"
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
              />
            </div>

            {/* Status filter */}
            {!summaryFilter && (
              <select
                className="rounded-lg border border-border bg-background text-sm px-3 py-2 h-9 focus:outline-none focus:ring-2 focus:ring-ring"
                value={filters.status_code ?? ""}
                onChange={(e) => updateFilters((f) => ({ ...f, status_code: e.target.value || undefined }))}
              >
                <option value="">All Statuses</option>
                {statuses.map((s) => <option key={s.code} value={s.code}>{s.name}</option>)}
                <option value="overdue">Overdue</option>
              </select>
            )}

            {/* Priority */}
            <select
              className="rounded-lg border border-border bg-background text-sm px-3 py-2 h-9 focus:outline-none focus:ring-2 focus:ring-ring"
              value={filters.priority_code ?? ""}
              onChange={(e) => updateFilters((f) => ({ ...f, priority_code: e.target.value || undefined }))}
            >
              <option value="">All Priorities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>

            {/* Task Type */}
            <select
              className="rounded-lg border border-border bg-background text-sm px-3 py-2 h-9 focus:outline-none focus:ring-2 focus:ring-ring"
              value={filters.task_type_code ?? ""}
              onChange={(e) => updateFilters((f) => ({ ...f, task_type_code: e.target.value || undefined }))}
            >
              <option value="">All Types</option>
              {taskTypes.map((t) => <option key={t.code} value={t.code}>{t.name}</option>)}
            </select>

            {/* My Tasks toggle */}
            <Button
              size="sm"
              variant={myTasksOn ? "default" : "outline"}
              className="h-9"
              onClick={() => { setMyTasksOn(!myTasksOn); setPage(0) }}
            >
              <User2 className="h-3.5 w-3.5 mr-1.5" />
              My Tasks
            </Button>

            <Separator orientation="vertical" className="h-6" />

            {/* Sort */}
            <div className="flex items-center gap-1">
              <select
                className="rounded-lg border border-border bg-background text-sm px-3 py-2 h-9 focus:outline-none focus:ring-2 focus:ring-ring"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
              >
                <option value="created_at">Created</option>
                <option value="due_date">Due Date</option>
                <option value="priority_code">Priority</option>
                <option value="updated_at">Updated</option>
              </select>
              <button
                onClick={toggleSortDir}
                className="h-9 w-9 flex items-center justify-center rounded-lg border border-border bg-background hover:bg-muted transition-colors"
                title={sortDir === "asc" ? "Ascending" : "Descending"}
              >
                {sortDir === "asc" ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </button>
            </div>

            <Separator orientation="vertical" className="h-6" />

            {/* View toggle */}
            <div className="flex rounded-lg border border-border overflow-hidden">
              <button
                onClick={() => setViewMode("list")}
                className={`flex items-center gap-1.5 px-3 py-2 text-sm transition-colors ${viewMode === "list" ? "bg-primary text-primary-foreground" : "bg-background text-muted-foreground hover:bg-muted"}`}
              >
                <LayoutList className="h-3.5 w-3.5" /> List
              </button>
              <button
                onClick={() => setViewMode("board")}
                className={`flex items-center gap-1.5 px-3 py-2 text-sm transition-colors ${viewMode === "board" ? "bg-primary text-primary-foreground" : "bg-background text-muted-foreground hover:bg-muted"}`}
              >
                <Columns className="h-3.5 w-3.5" /> Board
              </button>
              <button
                onClick={() => setViewMode("spreadsheet")}
                className={`flex items-center gap-1.5 px-3 py-2 text-sm transition-colors ${viewMode === "spreadsheet" ? "bg-primary text-primary-foreground" : "bg-background text-muted-foreground hover:bg-muted"}`}
              >
                <TableProperties className="h-3.5 w-3.5" /> Sheet
              </button>
            </div>

            {/* Export CSV */}
            <Button size="sm" variant="outline" className="h-9" onClick={handleExport} disabled={exportLoading} title="Export current view as CSV">
              {exportLoading ? <RefreshCw className="h-3.5 w-3.5 mr-1.5 animate-spin" /> : <Download className="h-3.5 w-3.5 mr-1.5" />}
              Export
            </Button>

            {/* Advanced Filters */}
            <Button
              size="sm"
              variant={showAdvancedFilters ? "secondary" : "outline"}
              className="h-9"
              onClick={() => setShowAdvancedFilters((v) => !v)}
            >
              <SlidersHorizontal className="h-3.5 w-3.5 mr-1.5" />
              Advanced
              {showAdvancedFilters ? <ChevronUp className="h-3 w-3 ml-1" /> : <ChevronDown className="h-3 w-3 ml-1" />}
            </Button>

            {/* Clear filters */}
            {(summaryFilter || filters.status_code || filters.priority_code || filters.task_type_code || myTasksOn || filters.due_date_from || filters.due_date_to || filters.entity_type || filters.reporter_user_id) && (
              <Button
                size="sm" variant="ghost" className="h-9 text-muted-foreground"
                onClick={() => { setSummaryFilter(null); setFilters({}); setMyTasksOn(false); setPage(0); setSelectedIds(new Set()) }}
              >
                <X className="h-3.5 w-3.5 mr-1" /> Clear
              </Button>
            )}
          </div>

          {/* Advanced Filters */}
          {showAdvancedFilters && (
            <div className="mt-3 pt-3 border-t border-border flex flex-wrap items-end gap-3">
              <div className="flex flex-col gap-1">
                <label className="text-xs text-muted-foreground font-medium">Due From</label>
                <input
                  type="date"
                  className="rounded-lg border border-border bg-background text-sm px-3 py-2 h-9 focus:outline-none focus:ring-2 focus:ring-ring"
                  value={filters.due_date_from ?? ""}
                  onChange={(e) => updateFilters((f) => ({ ...f, due_date_from: e.target.value || undefined }))}
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs text-muted-foreground font-medium">Due To</label>
                <input
                  type="date"
                  className="rounded-lg border border-border bg-background text-sm px-3 py-2 h-9 focus:outline-none focus:ring-2 focus:ring-ring"
                  value={filters.due_date_to ?? ""}
                  onChange={(e) => updateFilters((f) => ({ ...f, due_date_to: e.target.value || undefined }))}
                />
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs text-muted-foreground font-medium">Entity Type</label>
                <select
                  className="rounded-lg border border-border bg-background text-sm px-3 py-2 h-9 focus:outline-none focus:ring-2 focus:ring-ring"
                  value={filters.entity_type ?? ""}
                  onChange={(e) => updateFilters((f) => ({ ...f, entity_type: e.target.value || undefined }))}
                >
                  <option value="">Any Entity</option>
                  <option value="control">Control</option>
                  <option value="risk">Risk</option>
                  <option value="framework">Framework</option>
                  <option value="test">Test</option>
                </select>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs text-muted-foreground font-medium">Reporter ID</label>
                <input
                  type="text"
                  className="rounded-lg border border-border bg-background text-sm px-3 py-2 h-9 w-64 focus:outline-none focus:ring-2 focus:ring-ring"
                  placeholder="User UUID…"
                  value={filters.reporter_user_id ?? ""}
                  onChange={(e) => updateFilters((f) => ({ ...f, reporter_user_id: e.target.value || undefined }))}
                />
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Main content */}
      {loading ? (
        <div className="flex items-center justify-center py-16 text-muted-foreground gap-2">
          <RefreshCw className="h-5 w-5 animate-spin" />
          <span>Loading tasks…</span>
        </div>
      ) : displayedTasks.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="w-16 h-16 rounded-2xl bg-muted/50 flex items-center justify-center mb-4">
            <CheckSquare className="h-8 w-8 text-muted-foreground/40" />
          </div>
          <p className="text-muted-foreground font-semibold">No tasks found</p>
          <p className="text-sm text-muted-foreground/60 mt-1 max-w-xs">Try adjusting your filters, or create tasks from the Risk Registry or Framework detail pages</p>
        </div>
      ) : viewMode === "spreadsheet" ? (
        <>
          <EntitySpreadsheet
            columns={tasksColumns}
            rows={spreadsheetRows}
            onSave={handleSpreadsheetSave}
            onDelete={async (row) => {
              const t = tasks.find((t) => t.id === row.id)
              if (t) setDeleteConfirm(t)
            }}
            loading={loading}
            keyField="id"
            totalCount={tasks.length}
            exportButton={
              <ExportImportToolbar
                entityName="Tasks"
                onExport={handleSpreadsheetExport}
                onImport={handleSpreadsheetImport}
                onDownloadTemplate={handleDownloadTemplate}
              />
            }
          />
          {importResult && (
            <ImportResultDialog
              open={importResultOpen}
              onClose={() => { setImportResultOpen(false); setImportResult(null) }}
              result={importResult}
              onCommit={handleImportCommit}
            />
          )}
        </>
      ) : viewMode === "board" ? (
        <BoardView
          tasks={displayedTasks}
          onSelect={setDetailTask}
          onEdit={setEditTask}
          onDelete={setDeleteConfirm}
          onClone={handleClone}
        />
      ) : (
        /* List View */
        <>
          {/* Bulk action toolbar */}
          {someSelected && (
            <div className="flex flex-wrap items-center gap-2 px-4 py-2.5 rounded-xl bg-primary/5 border border-primary/20">
              <ListChecks className="h-4 w-4 text-primary shrink-0" />
              <span className="text-sm font-semibold text-primary">{selectedIds.size} selected</span>
              <Separator orientation="vertical" className="h-5" />
              <select
                className="rounded border border-border bg-background text-xs px-2 py-1 focus:outline-none focus:ring-1 focus:ring-ring"
                value={bulkStatusCode}
                onChange={(e) => setBulkStatusCode(e.target.value)}
              >
                <option value="">Change status…</option>
                {statuses.map((s) => <option key={s.code} value={s.code}>{s.name}</option>)}
              </select>
              <select
                className="rounded border border-border bg-background text-xs px-2 py-1 focus:outline-none focus:ring-1 focus:ring-ring"
                value={bulkPriority}
                onChange={(e) => setBulkPriority(e.target.value)}
              >
                <option value="">Change priority…</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
              <Button size="sm" className="h-7 text-xs" disabled={(!bulkStatusCode && !bulkPriority) || bulkLoading} onClick={handleBulkUpdate}>
                {bulkLoading ? <RefreshCw className="h-3 w-3 animate-spin mr-1" /> : null}
                Apply
              </Button>
              <Button size="sm" variant="ghost" className="h-7 text-xs text-muted-foreground" onClick={() => setSelectedIds(new Set())}>
                <X className="h-3 w-3 mr-1" /> Clear
              </Button>
            </div>
          )}

          <Card className="rounded-xl overflow-hidden">
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border bg-muted/40">
                      <th className="px-4 py-3 w-8">
                        <button
                          onClick={toggleSelectAll}
                          className="flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors"
                          title={allPageSelected ? "Deselect all" : "Select all on page"}
                        >
                          {allPageSelected
                            ? <CheckSquare className="h-4 w-4 text-primary" />
                            : <Square className="h-4 w-4" />}
                        </button>
                      </th>
                      <th className="text-left px-4 py-3 text-[11px] font-bold text-muted-foreground uppercase tracking-wider">Title</th>
                      <th className="text-left px-4 py-3 text-[11px] font-bold text-muted-foreground uppercase tracking-wider hidden md:table-cell">Type</th>
                      <th className="text-left px-4 py-3 text-[11px] font-bold text-muted-foreground uppercase tracking-wider hidden sm:table-cell">Priority</th>
                      <th className="text-left px-4 py-3 text-[11px] font-bold text-muted-foreground uppercase tracking-wider">Status</th>
                      <th className="text-left px-4 py-3 text-[11px] font-bold text-muted-foreground uppercase tracking-wider hidden md:table-cell">Evidence</th>
                      <th className="text-left px-4 py-3 text-[11px] font-bold text-muted-foreground uppercase tracking-wider hidden lg:table-cell">Assignee</th>
                      <th className="text-left px-4 py-3 text-[11px] font-bold text-muted-foreground uppercase tracking-wider hidden lg:table-cell">
                        <div className="flex items-center gap-1 cursor-pointer" onClick={() => { setSortBy("due_date"); toggleSortDir() }}>
                          Due Date <ArrowUpDown className="h-3 w-3" />
                        </div>
                      </th>
                      <th className="text-right px-4 py-3 text-[11px] font-bold text-muted-foreground uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/60">
                    {displayedTasks.map((task) => {
                      const over = isOverdue(task)
                      const selected = selectedIds.has(task.id)
                      const pm = PRIORITY_META[task.priority_code]
                      return (
                        <tr
                          key={task.id}
                          className={`hover:bg-muted/30 cursor-pointer transition-colors border-l-[3px] ${pm?.border ?? "border-l-transparent"} ${selected ? "bg-primary/5" : ""}`}
                          onClick={() => setDetailTask(task)}
                        >
                          <td className="px-4 py-3.5" onClick={(e) => { e.stopPropagation(); toggleSelectOne(task.id) }}>
                            <div className="flex items-center justify-center">
                              {selected
                                ? <CheckSquare className="h-4 w-4 text-primary" />
                                : <Square className="h-4 w-4 text-muted-foreground/40 hover:text-muted-foreground" />}
                            </div>
                          </td>
                          <td className="px-4 py-3.5 max-w-xs">
                            <div className="flex items-start gap-2">
                              <div className={`mt-0.5 w-5 h-5 rounded-md flex items-center justify-center shrink-0 ${TASK_TYPE_BG[task.task_type_code] ?? "bg-muted"}`}>
                                {TASK_TYPE_ICONS[task.task_type_code] ?? <SquareCheck className="h-3 w-3 text-muted-foreground" />}
                              </div>
                              <div className="min-w-0">
                                <p className="font-semibold text-foreground line-clamp-1 leading-snug">
                                  {task.title}
                                  {task.version > 1 && (
                                    <span className="ml-1.5 font-mono text-[10px] text-muted-foreground border border-border/50 rounded px-1 py-0 align-middle">v{task.version}</span>
                                  )}
                                </p>
                                {task.description && (
                                  <p className="text-xs text-muted-foreground line-clamp-1 mt-0.5">{task.description}</p>
                                )}
                                {(task.blocker_count > 0 || task.comment_count > 0) && (
                                  <div className="flex items-center gap-2 mt-1">
                                    {task.blocker_count > 0 && (
                                      <span className="flex items-center gap-0.5 text-[11px] text-orange-500 font-medium">
                                        <GitBranch className="h-3 w-3" /> {task.blocker_count} blockers
                                      </span>
                                    )}
                                    {task.comment_count > 0 && (
                                      <span className="flex items-center gap-0.5 text-[11px] text-muted-foreground">
                                        <MessageSquare className="h-3 w-3" /> {task.comment_count}
                                      </span>
                                    )}
                                  </div>
                                )}
                              </div>
                            </div>
                          </td>
                          <td className="px-4 py-3.5 hidden md:table-cell">
                            <TypeBadge code={task.task_type_code} name={task.task_type_name} />
                          </td>
                          <td className="px-4 py-3.5 hidden sm:table-cell">
                            <PriorityBadge code={task.priority_code} />
                          </td>
                          <td className="px-4 py-3.5">
                            <StatusBadge code={task.status_code} name={task.status_name} />
                          </td>
                          <td className="px-4 py-3.5 hidden md:table-cell">
                            <EvidenceVerdictBadge verdict={evidenceVerdicts[task.id]} />
                          </td>
                          <td className="px-4 py-3.5 hidden lg:table-cell">
                            {task.assignee_user_id ? (
                              <div className="flex items-center gap-1.5">
                                <div className="w-6 h-6 rounded-full bg-muted flex items-center justify-center shrink-0">
                                  <User2 className="h-3 w-3 text-muted-foreground" />
                                </div>
                                <CopyableId id={task.assignee_user_id} />
                              </div>
                            ) : (
                              <span className="text-xs text-muted-foreground/60">Unassigned</span>
                            )}
                          </td>
                          <td className="px-4 py-3.5 hidden lg:table-cell">
                            {task.due_date ? (
                              <div className={`flex flex-col ${over ? "text-red-500" : "text-muted-foreground"}`}>
                                <span className={`text-xs font-medium ${over ? "text-red-500" : ""}`}>
                                  {formatDate(task.due_date)}
                                </span>
                                {over && (
                                  <span className="flex items-center gap-0.5 text-[10px] text-red-400 font-semibold">
                                    <AlertTriangle className="h-2.5 w-2.5" /> {overdueDays(task)}d overdue
                                  </span>
                                )}
                              </div>
                            ) : (
                              <span className="text-xs text-muted-foreground/60">—</span>
                            )}
                          </td>
                          <td className="px-4 py-3.5">
                            <div className="flex items-center justify-end gap-1" onClick={(e) => e.stopPropagation()}>
                              <button
                                onClick={() => setEditTask(task)}
                                className="p-1.5 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                                title="Edit"
                              >
                                <Pencil className="h-3.5 w-3.5" />
                              </button>
                              <button
                                onClick={() => handleClone(task)}
                                className="p-1.5 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                                title="Clone"
                              >
                                <Copy className="h-3.5 w-3.5" />
                              </button>
                              <button
                                onClick={() => setDeleteConfirm(task)}
                                className="p-1.5 rounded-lg hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors"
                                title="Delete"
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>

              {/* Pagination footer */}
              <div className="flex items-center justify-between px-4 py-3 border-t border-border bg-muted/20">
                <span className="text-xs text-muted-foreground">
                  {totalTasks === 0
                    ? "No tasks"
                    : `${page * PAGE_SIZE + 1}–${Math.min((page + 1) * PAGE_SIZE, totalTasks)} of ${totalTasks} tasks`}
                </span>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => setPage(0)} disabled={page === 0}
                    className="p-1.5 rounded-lg hover:bg-muted disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    title="First page"
                  >
                    <ChevronLeft className="h-3.5 w-3.5" />
                  </button>
                  <button
                    onClick={() => setPage((p) => Math.max(0, p - 1))} disabled={page === 0}
                    className="p-1.5 rounded-lg hover:bg-muted disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    title="Previous page"
                  >
                    <ChevronLeft className="h-3.5 w-3.5" />
                  </button>
                  <span className="text-xs text-muted-foreground px-3 py-1 rounded-lg bg-muted/50 tabular-nums">
                    {page + 1} / {totalPages}
                  </span>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))} disabled={page >= totalPages - 1}
                    className="p-1.5 rounded-lg hover:bg-muted disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    title="Next page"
                  >
                    <ChevronRight className="h-3.5 w-3.5" />
                  </button>
                  <button
                    onClick={() => setPage(totalPages - 1)} disabled={page >= totalPages - 1}
                    className="p-1.5 rounded-lg hover:bg-muted disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    title="Last page"
                  >
                    <ChevronRight className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {/* Task Detail Panel */}
      {detailTask && (
        <TaskDetailPanel
          task={detailTask}
          onClose={() => setDetailTask(null)}
          onEdit={(t) => { setDetailTask(null); setEditTask(t) }}
          onClone={handleClone}
          onRefresh={loadTasks}
        />
      )}

      {/* Create Dialog */}
      <CreateTaskDialog
        open={showCreate}
        onClose={() => setShowCreate(false)}
        onCreated={handleCreated}
        taskTypes={taskTypes}
        defaultOrgId={selectedOrgId || undefined}
        defaultWorkspaceId={selectedWorkspaceId || undefined}
      />

      {/* Edit Dialog */}
      <EditTaskDialog
        open={!!editTask}
        task={editTask}
        onClose={() => setEditTask(null)}
        onUpdated={(updated) => handleUpdated(updated)}
        statuses={statuses}
      />

      {/* Delete Confirm */}
      <Dialog open={!!deleteConfirm} onOpenChange={(v) => { if (!v) setDeleteConfirm(null) }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Delete Task</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete <span className="font-semibold">&ldquo;{deleteConfirm?.title}&rdquo;</span>? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteConfirm(null)} disabled={deleting}>Cancel</Button>
            <Button variant="destructive" onClick={handleDeleteConfirmed} disabled={deleting}>
              {deleting ? <RefreshCw className="h-3.5 w-3.5 animate-spin mr-1" /> : <Trash2 className="h-3.5 w-3.5 mr-1" />}
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
