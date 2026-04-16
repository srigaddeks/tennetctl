"use client"

import { useEffect, useState, useMemo } from "react"
import { useParams, useRouter } from "next/navigation"
import { Button, Badge, Separator } from "@kcontrol/ui"
import {
  ChevronLeft,
  Sparkles,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  X,
  ChevronDown,
  ChevronRight,
  ListTodo,
  Check,
  Upload,
  FileText,
  RotateCcw,
  TableProperties,
  LayoutGrid,
  History,
  Activity,
  Zap,
  Info,
  Database,
  Cpu,
  Boxes,
  Compass,
  ShieldCheck,
  ArrowRight,
} from "lucide-react"
import { getFramework, listControls } from "@/lib/api/grc"
import type { GeneratedTask } from "@/lib/api/taskBuilder"
import { useOrgWorkspace } from "@/lib/context/OrgWorkspaceContext"
import { OrgWorkspaceSwitcher } from "@/components/layout/OrgWorkspaceSwitcher"
import { BuildProgressFeed } from "@/components/grc/BuildProgressFeed"
import { EntitySpreadsheet, type SpreadsheetColumn } from "@/components/spreadsheet/EntitySpreadsheet"
import type { FrameworkResponse } from "@/lib/types/grc"
import { useTaskBuilder, type SelectedTask, type SelectedGroup } from "./hooks/useTaskBuilder"
import { cn } from "@/lib/utils"

// ── Helpers ───────────────────────────────────────────────────────────────────

function relativeTime(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return "just now"
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

const STATUS_LABELS: Record<string, string> = {
  idle: "Idle",
  generating: "Generating…",
  reviewing: "Ready to review",
  applying: "Applying…",
  complete: "Complete",
  failed: "Failed",
}

const STATUS_COLORS: Record<string, string> = {
  idle: "text-muted-foreground",
  generating: "text-blue-500",
  reviewing: "text-blue-600",
  applying: "text-amber-600",
  complete: "text-green-600",
  failed: "text-red-500",
}

// ── Components ────────────────────────────────────────────────────────────────

function StepCircle({ step, label, active, done }: { step: number; label: string; active: boolean; done: boolean }) {
  return (
    <div className={cn(
      "flex items-center gap-2 transition-all duration-300",
      active || done ? "opacity-100" : "opacity-30"
    )}>
       <div className={cn(
         "w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold transition-all duration-300",
         active ? "bg-primary text-primary-foreground shadow-sm shadow-primary/20" : 
         done ? "bg-green-600 text-white" :
         "bg-muted text-muted-foreground border border-border"
       )}>
         {done ? <Check className="h-3 w-3 stroke-[3px]" /> : step}
       </div>
       <span className={cn(
         "text-xs font-semibold transition-colors duration-300 whitespace-nowrap",
         active ? "text-foreground" : done ? "text-green-600" : "text-muted-foreground"
       )}>
         {label}
       </span>
    </div>
  )
}

function TaskRow({
  task,
  onToggle,
  onEdit,
}: {
  task: SelectedTask
  onToggle: () => void
  onEdit: (field: keyof GeneratedTask, value: string) => void
}) {
  const [expanded, setExpanded] = useState(false)
  const [editingTitle, setEditingTitle] = useState(false)
  const [titleDraft, setTitleDraft] = useState(task.title)

  return (
    <div className={cn(
      "border rounded-xl transition-all duration-200",
      task._selected ? "border-primary/20 bg-card hover:border-primary/40" : "border-border/30 bg-muted/10 opacity-60"
    )}>
      <div className="flex items-center gap-3 px-5 py-4">
        <button
          onClick={onToggle}
          className={cn(
            "h-5 w-5 rounded-md border-2 transition-all flex items-center justify-center shrink-0",
            task._selected ? "border-primary bg-primary text-primary-foreground shadow-sm shadow-primary/20" : "border-muted-foreground/30 bg-background hover:border-muted-foreground/50"
          )}
        >
          {task._selected && <Check className="h-3 w-3 stroke-[3px]" />}
        </button>
 
        <div className="flex-1 min-w-0">
          {editingTitle ? (
            <input
              className="w-full text-sm bg-background border border-primary rounded-lg px-3 py-1.5 focus:outline-none focus:ring-4 focus:ring-primary/10 shadow-inner"
              value={titleDraft}
              autoFocus
              onChange={(e) => setTitleDraft(e.target.value)}
              onBlur={() => { onEdit("title", titleDraft); setEditingTitle(false) }}
              onKeyDown={(e) => { if (e.key === "Enter") { onEdit("title", titleDraft); setEditingTitle(false) } }}
            />
          ) : (
            <button
              className="group/btn text-sm font-semibold text-left hover:text-primary transition-colors truncate block w-full tracking-tight"
              onClick={() => setEditingTitle(true)}
            >
              {task.title}
            </button>
          )}
        </div>
 
        <div className="flex items-center gap-3 shrink-0">
          <Badge variant="outline" className={cn(
            "text-[9px] font-black uppercase tracking-widest px-2 h-5 rounded-full border-2 translate-y-[1px]",
            task.task_type_code === "evidence_collection" ? "bg-blue-500/10 text-blue-600 border-blue-500/20" :
            task.task_type_code === "control_remediation" ? "bg-indigo-500/10 text-indigo-600 border-indigo-500/20" :
            task.task_type_code === "risk_mitigation" ? "bg-violet-500/10 text-violet-600 border-violet-500/20" :
            "bg-muted/50 text-muted-foreground border-border/30"
          )}>
            {task.task_type_code === "evidence_collection" ? "Evidence" : 
             task.task_type_code === "control_remediation" ? "Remediation" : 
             task.task_type_code === "risk_mitigation" ? "Mitigation" : 
             (task.task_type_code as string)?.replace(/_/g, " ") || "General"}
          </Badge>

          <Badge variant="outline" className={cn(
            "text-[9px] font-black uppercase tracking-widest px-2 h-5 rounded-full border-2",
            task.priority_code === "critical" ? "bg-red-500/10 text-red-600 border-red-500/20" :
            task.priority_code === "high" ? "bg-orange-500/10 text-orange-600 border-orange-500/20" :
            "bg-muted/50 text-muted-foreground border-border/30"
          )}>
            {task.priority_code}
          </Badge>
 
          <button
            onClick={() => setExpanded(v => !v)}
            className="p-1.5 rounded-lg hover:bg-muted text-muted-foreground transition-all duration-300"
          >
            <ChevronDown className={cn("h-4 w-4 transition-transform duration-300", expanded ? "rotate-0" : "-rotate-90")} />
          </button>
        </div>
      </div>

      {expanded && (
        <div className="px-11 pb-4 space-y-3 animate-in fade-in slide-in-from-top-1 duration-200">
          <Separator className="opacity-50" />
          {task.description && (
            <div>
              <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mb-1">Description</p>
              <p className="text-xs text-muted-foreground leading-relaxed">{task.description}</p>
            </div>
          )}
          {task.acceptance_criteria && (
            <div>
              <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mb-1">Acceptance Criteria</p>
              <p className="text-xs text-foreground font-medium leading-relaxed">{task.acceptance_criteria}</p>
            </div>
          )}
          {task.remediation_plan && (
            <div className="bg-primary/[0.03] p-3 rounded-lg border border-primary/10">
              <p className="text-[10px] font-bold uppercase tracking-widest text-primary/60 mb-1">Implementation Plan</p>
              <p className="text-xs text-primary font-medium leading-relaxed italic">{task.remediation_plan}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function ControlGroup({
  group,
  controlName,
  onToggleTask,
  onEditTask,
  onToggleAll,
}: {
  group: SelectedGroup
  controlName?: string
  onToggleTask: (taskIdx: number) => void
  onEditTask: (taskIdx: number, field: keyof GeneratedTask, value: string) => void
  onToggleAll: (selected: boolean) => void
}) {
  const [open, setOpen] = useState(true)
  const allSelected = group.tasks.every(t => t._selected)
  const selectedCount = group.tasks.filter(t => t._selected).length

  return (
    <div className="border border-border/50 rounded-2xl overflow-hidden bg-card shadow-sm hover:shadow-md transition-shadow">
      <div
        className="w-full flex items-center gap-3 px-5 py-3 bg-muted/40 hover:bg-muted/60 transition-colors text-left cursor-pointer border-b border-border/10"
        onClick={() => setOpen(v => !v)}
      >
        <div className={cn("p-1.5 rounded-lg transition-all duration-500", open ? "rotate-0 text-primary" : "-rotate-90 text-muted-foreground")}>
            <ChevronDown className="h-4 w-4" />
        </div>
        <div className="flex flex-col min-w-0">
          <span className="font-mono text-xs font-bold text-primary tracking-tight">{group.control_code}</span>
          {controlName && <span className="text-[10px] text-muted-foreground font-medium truncate">{controlName}</span>}
        </div>
        <span className="text-[11px] font-medium text-muted-foreground flex-1 ml-2">{selectedCount} of {group.tasks.length} tasks ready</span>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 text-[10px] font-bold uppercase tracking-widest text-muted-foreground hover:text-primary px-2"
          onClick={(e) => { e.stopPropagation(); onToggleAll(!allSelected) }}
        >
          {allSelected ? "Deselect All" : "Select All"}
        </Button>
      </div>

      {open && (
        <div className="p-4 space-y-2 bg-card">
          {group.tasks.map((task, i) => (
            <TaskRow
              key={i}
              task={task}
              onToggle={() => onToggleTask(i)}
              onEdit={(field, value) => onEditTask(i, field, value)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

const builderColumns: SpreadsheetColumn<any>[] = [
  { key: "control_code", label: "Control", type: "readonly", width: 120 },
  { key: "control_name", label: "Control Name", type: "readonly", width: 220 },
  { key: "title", label: "Task Title", type: "text", required: true, width: 220 },
  { key: "description", label: "Description", type: "textarea", width: 280 },
  {
    key: "task_type_code",
    label: "Type",
    type: "select",
    width: 140,
    options: [
      { value: "evidence_collection", label: "Evidence" },
      { value: "control_remediation", label: "Remediation" },
    ],
  },
  {
    key: "priority_code",
    label: "Priority",
    type: "select",
    width: 120,
    options: [
      { value: "critical", label: "Critical" },
      { value: "high", label: "High" },
      { value: "medium", label: "Medium" },
      { value: "low", label: "Low" },
    ],
  },
  { key: "due_days_from_now", label: "Days", type: "number", width: 80 },
  { key: "acceptance_criteria", label: "Acceptance Criteria", type: "textarea", width: 280 },
  { key: "remediation_plan", label: "Remediation Plan", type: "textarea", width: 280 },
]

const GRC_INSIGHTS = [
  { title: "STRATEGIC REMEDIATION", text: "Targeted remediation tasks reduce risk faster than shotgun approaches. Focus on Critical assets first." },
  { title: "EVIDENCE INTEGRITY", text: "Always ensure evidence includes the system name and timestamp to pass SOC 2 Type II strict scrutiny." },
  { title: "MFA BASELINE", text: "Privileged accounts (Admin, DB Root) should always have MFA active—prioritize these tasks today." },
  { title: "FRAMEWORK DRIFT", text: "AI helps detect if your implemented tasks still meet the latest framework release requirements." },
]

// ── Main Page ────────────────────────────────────────────────────────────────

export default function TaskBuilderPage() {
  const params = useParams()
  const router = useRouter()
  const frameworkId = params.frameworkId as string
  const { selectedWorkspaceId } = useOrgWorkspace()

  const [framework, setFramework] = useState<FrameworkResponse | null>(null)
  const [frameworkLoading, setFrameworkLoading] = useState(true)
  const [controlsMap, setControlsMap] = useState<Map<string, string>>(new Map())

  const tb = useTaskBuilder(frameworkId)

  useEffect(() => {
    if (!frameworkId) return
    let isMounted = true
    setFrameworkLoading(true)

    Promise.all([
      getFramework(frameworkId)
        .then(res => { if(isMounted) setFramework(res) })
        .catch(() => {}),
      listControls(frameworkId, { limit: 500 })
        .then(res => {
          if (!isMounted) return
          const m = new Map<string, string>()
          res.items.forEach(c => m.set(c.control_code, c.name))
          setControlsMap(m)
        })
        .catch(() => {})
    ]).finally(() => {
      if(isMounted) setFrameworkLoading(false)
    })
    
    return () => { isMounted = false }
  }, [frameworkId])

  const frameworkName = framework?.name || framework?.framework_code || frameworkId

  const [reviewMode, setReviewMode] = useState<"grid" | "spreadsheet">("grid")
  const [historyOpen, setHistoryOpen] = useState(false)
  const [insightIndex, setInsightIndex] = useState(0)

  // Rotate through insights during wait
  useEffect(() => {
    if (tb.phase === "generating") {
      const timer = setInterval(() => {
        setInsightIndex(prev => (prev + 1) % GRC_INSIGHTS.length)
      }, 10000)
      return () => clearInterval(timer)
    }
  }, [tb.phase])

  // Flattened tasks for spreadsheet view
  const flattenedTasks = useMemo(() => {
    const list: any[] = []
    tb.groups.forEach((g, gi) => {
      g.tasks.forEach((t, ti) => {
        list.push({
          ...t,
          id: `${g.control_id}_${ti}`,
          control_code: g.control_code,
          control_name: controlsMap.get(g.control_code) || "",
          groupIdx: gi,
          taskIdx: ti,
        })
      })
    })
    return list
  }, [tb.groups, controlsMap])

  const selectedIndices = useMemo(() => {
    const indices: number[] = []
    let currentIdx = 0
    tb.groups.forEach(g => {
      g.tasks.forEach(t => {
        if (t._selected) indices.push(currentIdx)
        currentIdx++
      })
    })
    return indices
  }, [tb.groups])

  const step =
    tb.phase === "idle" ? "configure" :
    tb.phase === "generating" ? "generating" :
    tb.phase === "reviewing" ? "preview" :
    tb.phase === "applying" ? "applying" :
    tb.phase === "complete" ? "done" :
    tb.phase === "failed" ? "failed" :
    "configure"

  return (
    <div className="relative flex h-[calc(100vh-64px)] w-full overflow-hidden bg-background">
      
      {/* ── Subtle background decor (Onboarding style) ── */}
      <div aria-hidden className="absolute inset-0 isolate contain-strict -z-10 opacity-30 pointer-events-none">
        <div className="bg-[radial-gradient(circle_at_50%_0%,--theme(--color-primary/.1)_0,transparent_60%)] absolute top-0 left-0 w-full h-[600px]" />
      </div>

      <div className={cn(
        "flex-1 flex flex-col min-w-0 transition-all duration-300 ease-in-out",
        historyOpen ? "mr-[320px]" : "mr-0"
      )}>
        <header className="h-14 px-4 border-b border-border bg-background/90 backdrop-blur-md flex items-center justify-between shrink-0 z-30">
          <div className="flex items-center gap-3">
            <button
              className="p-1.5 rounded-lg hover:bg-muted transition-colors text-muted-foreground"
              onClick={() => router.back()}
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-primary/15 flex items-center justify-center text-primary">
                <Sparkles className="h-4 w-4" />
              </div>
              <div className="flex flex-col -space-y-0.5">
                <h1 className="text-sm font-bold tracking-tight text-foreground">AI Task Builder</h1>
                <p className="text-[10px] font-medium text-muted-foreground truncate max-w-[150px]">
                   {frameworkLoading ? "Onboarding..." : frameworkName}
                </p>
              </div>
            </div>

            <Separator orientation="vertical" className="h-5 mx-2" />
            
            <Button
               variant={historyOpen ? "secondary" : "ghost"}
               size="sm"
               onClick={() => setHistoryOpen(!historyOpen)}
               className={cn(
                 "h-8 gap-2 rounded-xl text-[11px] font-bold uppercase tracking-widest px-3 border border-transparent shadow-sm transition-all",
                 historyOpen ? "bg-primary text-primary-foreground border-primary/20" : "hover:bg-muted"
               )}
            >
              <Activity className="h-3.5 w-3.5" />
              Timeline
              {tb.sessions.length > 0 && (
                <Badge variant="secondary" className="ml-1 h-4 px-1.5 min-w-[18px] text-[9px] bg-primary/20 text-primary border-none">{tb.sessions.length}</Badge>
              )}
            </Button>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="hidden lg:flex items-center gap-4">
                <StepCircle step={1} label="Scope" active={step === "configure"} done={["generating", "preview", "applying", "done"].includes(step)} />
                <ArrowRight className="h-3 w-3 text-muted-foreground/30" />
                <StepCircle step={2} label="Build" active={step === "generating"} done={["preview", "applying", "done"].includes(step)} />
                <ArrowRight className="h-3 w-3 text-muted-foreground/30" />
                <StepCircle step={3} label="Review" active={step === "preview" || step === "applying"} done={step === "done"} />
                <ArrowRight className="h-3 w-3 text-muted-foreground/30" />
                <StepCircle step={4} label="Done" active={step === "done"} done={false} />
            </div>
            
            <Separator orientation="vertical" className="h-6 mx-2" />
            <OrgWorkspaceSwitcher />
          </div>
        </header>

        <main className="flex-1 overflow-y-auto px-6 py-8">
          <div className="max-w-5xl mx-auto w-full h-full">
            
            {step === "configure" && (
              <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-500">
                <div className="text-center space-y-2 mb-10">
                    <h2 className="text-3xl font-bold tracking-tight">Configure Build Context</h2>
                    <p className="text-muted-foreground text-sm max-w-lg mx-auto">
                        Provide custom instructions and reference documents to generate specific evidence tasks for your framework controls.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
                    {/* Context Card */}
                    <div className="group flex flex-col p-6 rounded-2xl border border-border/60 bg-card shadow-sm hover:shadow-md transition-all duration-300">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary group-hover:scale-105 transition-transform">
                                <Boxes className="h-5 w-5" />
                            </div>
                            <div className="flex flex-col">
                                <h3 className="text-base font-bold text-foreground">Generation Instructions</h3>
                                <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Custom Instructions</p>
                            </div>
                        </div>
                        <textarea
                          className="flex-1 w-full rounded-2xl border border-border/50 bg-muted/20 px-5 py-4 text-sm resize-none focus:outline-none focus:ring-4 focus:ring-primary/10 min-h-[220px] shadow-inner font-medium text-foreground leading-relaxed premium-scrollbar transition-all"
                          placeholder="e.g. 'Create tasks for collecting policy documents, architecture diagrams, and configuration files...'"
                          value={tb.userContext}
                          onChange={(e) => tb.setUserContext(e.target.value)}
                        />
                        <div className="mt-4 flex items-center gap-2 text-[10px] font-bold text-muted-foreground/60 uppercase tracking-widest">
                            <Info className="h-3 w-3" />
                            The AI uses this to customize the type of tasks it generates for you
                        </div>
                    </div>

                    {/* File Card */}
                    <div className="group flex flex-col p-6 rounded-2xl border border-border/60 bg-card shadow-sm hover:shadow-md transition-all duration-300">
                         <div className="flex items-center gap-3 mb-6">
                            <div className="h-10 w-10 rounded-xl bg-amber-500/10 flex items-center justify-center text-amber-600 group-hover:scale-105 transition-transform">
                                <Database className="h-5 w-5" />
                            </div>
                            <div className="flex flex-col">
                                <h3 className="text-base font-bold text-foreground">Reference Documents</h3>
                                <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Supporting Files</p>
                            </div>
                        </div>

                        <div
                          className={cn(
                            "flex-1 flex flex-col rounded-2xl border-2 border-dashed transition-all duration-300 min-h-[220px] overflow-hidden",
                            tb.dragOver ? "border-primary bg-primary/[0.03] scale-[0.99] shadow-inner" : "border-muted-foreground/20 bg-muted/10 hover:border-muted-foreground/40 hover:bg-muted/20"
                          )}
                          onDragOver={(e) => { e.preventDefault(); tb.setDragOver(true) }}
                          onDragLeave={() => tb.setDragOver(false)}
                          onDrop={(e) => { e.preventDefault(); tb.setDragOver(false); const files = Array.from(e.dataTransfer.files); if (files.length > 0) tb.handleFileDrop(files) }}
                        >
                            {tb.uploadedFiles.length === 0 ? (
                                <label className="flex-1 flex flex-col items-center justify-center gap-4 cursor-pointer p-8 group/upload">
                                    <div className="p-4 rounded-2xl bg-background border border-border shadow-sm group-hover/upload:scale-110 group-hover/upload:border-primary/30 transition-all duration-500">
                                        <Upload className="h-6 w-6 text-muted-foreground group-hover/upload:text-primary transition-colors" />
                                    </div>
                                    <div className="text-center">
                                        <p className="text-sm font-bold tracking-tight">Drop reference documents or <span className="text-primary hover:underline">browse</span></p>
                                        <p className="text-[10px] text-muted-foreground/70 font-bold uppercase tracking-widest mt-1">PDF, DOCX, CSV, MD</p>
                                    </div>
                                    <input type="file" multiple accept=".pdf,.docx,.txt,.csv,.json,.md" className="hidden" onChange={(e) => { const files = Array.from(e.target.files || []); if (files.length > 0) tb.handleFileDrop(files); e.target.value = "" }} />
                                </label>
                            ) : (
                                <div className="p-5 space-y-2.5 overflow-y-auto premium-scrollbar h-full bg-muted/5">
                                    {tb.uploadedFiles.map((file, i) => (
                                        <div key={i} className="flex items-center gap-3 rounded-xl bg-background border border-border/80 p-3 shadow-sm animate-in fade-in slide-in-from-top-2">
                                            <div className="p-2 rounded-lg bg-primary/5">
                                              <FileText className="h-4 w-4 text-primary" />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="text-xs font-bold truncate tracking-tight">{file.name}</p>
                                                <p className={cn("text-[9px] font-black uppercase tracking-widest", tb.attachments[i]?.ingest_status === "complete" ? "text-green-600" : "text-primary animate-pulse")}>
                                                    {tb.attachments[i]?.ingest_status || "UPLOADING..."}
                                                </p>
                                            </div>
                                            <button className="p-2 hover:bg-red-500/10 text-muted-foreground hover:text-red-500 rounded-lg transition-colors" onClick={() => tb.removeFile(i)}>
                                                <X className="h-4 w-4" />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                        <div className="mt-4 flex items-center gap-2 text-[10px] font-bold text-muted-foreground/60 uppercase tracking-widest">
                            <Database className="h-3 w-3" />
                            Referenced for specific control wording
                        </div>
                    </div>
                </div>

                <div className="flex items-center justify-center pt-10">
                    <Button
                        size="lg"
                        className="h-16 px-20 rounded-2xl gap-4 font-black text-lg shadow-2xl shadow-primary/30 bg-primary hover:bg-primary/90 text-primary-foreground border-none transition-all hover:scale-[1.02] active:scale-[0.98] group"
                        disabled={tb.uploading || !frameworkId}
                        onClick={() => tb.handleGenerate()}
                    >
                        <Sparkles className="h-6 w-6 group-hover:animate-spin-slow transition-transform" />
                        Generate Control Tasks
                    </Button>
                </div>
              </div>
            )}

            {(step === "generating" || step === "failed") && (
              <div className="flex flex-col items-center justify-center min-h-[80%] space-y-12 animate-in fade-in zoom-in-95 duration-500">
                <div className="text-center space-y-4">
                    <div className="relative inline-block mb-4">
                        <div className="absolute inset-0 bg-primary/20 blur-[50px] rounded-full animate-pulse" />
                        <div className="relative w-24 h-24 rounded-3xl bg-card border border-border shadow-2xl flex items-center justify-center">
                            <Loader2 className={cn("h-12 w-12 text-primary", step === "generating" && "animate-spin")} />
                        </div>
                    </div>
                    <h2 className="text-4xl font-bold tracking-tighter">
                        {step === "failed" ? "Task Generation Failed" : "Generating Evidence Tasks"}
                    </h2>
                    <p className="text-muted-foreground text-base max-w-lg mx-auto leading-relaxed font-medium">
                        {step === "failed" 
                          ? "The system encountered an unexpected issue. Review the log below."
                          : "Structuring evidence collection tasks based on your instructions and mapping them to framework controls."
                        }
                    </p>
                </div>

                <div className="w-full max-w-5xl grid grid-cols-1 md:grid-cols-12 gap-8">
                    <div className="md:col-span-7 space-y-4">
                        <div className="flex items-center gap-2 px-2">
                                <Activity className="h-3.5 w-3.5 text-primary" />
                                <span className="text-[11px] font-bold uppercase tracking-widest text-muted-foreground">Activity Log</span>
                        </div>
                        <div className="bg-card/50 rounded-2xl border border-border overflow-hidden shadow-sm backdrop-blur-sm">
                            <BuildProgressFeed events={tb.feedEvents} isStreaming={tb.isStreaming} className="h-[350px]" />
                        </div>
                    </div>

                    <div className="md:col-span-5">
                        {/* Featured Nudge Style Insight */}
                        <div className="h-full p-8 rounded-2xl border border-primary/20 bg-primary/[0.03] backdrop-blur-md flex flex-col justify-between group shadow-sm">
                            <div className="space-y-6">
                                <div className="h-11 w-11 rounded-xl bg-background border border-primary/20 shadow-sm flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
                                    <Info className="h-5 w-5" />
                                </div>
                                <div className="space-y-3">
                                    <h4 className="text-[12px] font-bold text-primary uppercase tracking-[0.2em]">{GRC_INSIGHTS[insightIndex]?.title}</h4>
                                    <p className="text-sm text-foreground/80 leading-relaxed font-medium italic">
                                        "{GRC_INSIGHTS[insightIndex]?.text}"
                                    </p>
                                </div>
                            </div>
                            <div className="flex gap-2 pt-10">
                                {GRC_INSIGHTS.map((_, i) => (
                                    <div key={i} className={cn("h-1.5 rounded-full transition-all duration-700", i === insightIndex ? "w-10 bg-primary" : "w-3 bg-primary/20")} />
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                {step === "failed" && (
                  <div className="flex flex-col items-center gap-5 pt-4">
                    <div className="flex gap-4">
                      <Button variant="outline" className="rounded-xl px-10 h-12" onClick={() => tb.resetState()}>Discard Draft</Button>
                      <Button className="rounded-xl px-12 h-12 bg-[#4e5d72]" onClick={() => tb.handleGenerate()}>Retry Build</Button>
                    </div>
                    {tb.error && (
                      <div className="text-[11px] font-bold text-red-500 bg-red-500/10 px-6 py-3 rounded-xl border border-red-500/20 shadow-sm">
                        ENGINE_EXCEPTION_LOG: {tb.error}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {(step === "preview" || step === "applying") && (
              <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500 h-full flex flex-col">
                <div className="flex items-center gap-6 p-5 rounded-2xl border border-border/80 bg-card shadow-sm backdrop-blur-sm">
                  <div className="h-12 w-12 rounded-xl bg-green-500/10 flex items-center justify-center text-green-600 shrink-0">
                    <ShieldCheck className="h-6 w-6" />
                  </div>
                  <div className="flex-1">
                    <p className="text-base font-bold text-foreground">{tb.totalSelected} Tasks Selected</p>
                    <p className="text-xs text-muted-foreground font-medium">Mapped from {tb.totalTasks} framework controls</p>
                  </div>
                  
                  <Separator orientation="vertical" className="h-10 mx-2" />
                  
                  <div className="flex items-center gap-3 mr-4">
                        <button className="text-[11px] font-bold text-muted-foreground hover:text-primary transition-colors uppercase tracking-widest" onClick={() => tb.selectAll(true)}>Select All</button>
                        <span className="w-1 h-1 rounded-full bg-muted-foreground/30" />
                        <button className="text-[11px] font-bold text-muted-foreground hover:text-primary transition-colors uppercase tracking-widest" onClick={() => tb.selectAll(false)}>Clear</button>
                  </div>

                  <div className="flex items-center p-1 bg-muted/50 rounded-xl border border-border shadow-inner">
                    <button onClick={() => setReviewMode("grid")} className={cn("p-2.5 rounded-lg transition-all", reviewMode === "grid" ? "bg-background text-primary shadow-sm" : "text-muted-foreground hover:text-foreground")}>
                      <LayoutGrid className="h-4.5 w-4.5" />
                    </button>
                    <button onClick={() => setReviewMode("spreadsheet")} className={cn("p-2.5 rounded-lg transition-all", reviewMode === "spreadsheet" ? "bg-background text-primary shadow-sm" : "text-muted-foreground hover:text-foreground")}>
                      <TableProperties className="h-4.5 w-4.5" />
                    </button>
                  </div>
                </div>

                <div className="flex-1 min-h-[400px]">
                    {reviewMode === "grid" ? (
                    <div className="grid grid-cols-1 gap-4 overflow-y-auto premium-scrollbar pr-1 max-h-[calc(100vh-400px)]">
                        {tb.groups.map((group, gi) => (
                        <ControlGroup
                            key={group.control_id}
                            group={group}
                            controlName={controlsMap.get(group.control_code)}
                            onToggleTask={(ti) => tb.toggleTask(gi, ti)}
                            onEditTask={(ti, field, val) => tb.editTask(gi, ti, field, val)}
                            onToggleAll={(sel) => tb.toggleGroupAll(gi, sel)}
                        />
                        ))}
                    </div>
                    ) : (
                    <div className="rounded-2xl overflow-hidden border border-border shadow-sm bg-card h-full">
                        <EntitySpreadsheet
                            columns={builderColumns}
                            rows={flattenedTasks}
                            initialSelectedIndices={selectedIndices}
                            onSelectionChange={tb.handleSpreadsheetSelectionChange}
                            onSave={async (row, index) => {
                                const task = flattenedTasks[index]
                                if (task) {
                                    Object.keys(row).forEach((k) => {
                                        if (k !== "control_code") { tb.editTask(task.groupIdx, task.taskIdx, k as any, row[k] as string) }
                                    })
                                }
                            }}
                            keyField="id"
                        />
                    </div>
                    )}
                </div>

                {tb.error && (
                  <div className="text-sm font-bold text-red-500 bg-red-500/5 p-4 rounded-xl border border-red-500/20 mb-4 animate-in shake duration-500">
                    {tb.error}
                  </div>
                )}

                {step === "applying" && tb.feedEvents.length > 0 && (
                  <div className="p-6 rounded-2xl border border-border/80 bg-card shadow-lg animate-in fade-in slide-in-from-bottom-4">
                      <div className="flex items-center justify-between mb-4">
                        <p className="text-[11px] font-bold uppercase tracking-widest text-muted-foreground">Saving Evidence Tasks...</p>
                        <Loader2 className="h-4 w-4 animate-spin text-primary" />
                      </div>
                      <BuildProgressFeed events={tb.feedEvents} isStreaming={tb.isStreaming} className="max-h-[150px]" />
                  </div>
                )}

                <div className="flex items-center justify-between py-8 border-t border-border/50 mt-auto">
                  <div className="flex gap-4">
                     <Button variant="outline" className="rounded-xl px-10 h-14 font-bold border-border/80" onClick={() => tb.resetState()}>Back to Scope</Button>
                     {!selectedWorkspaceId && (
                        <div className="flex items-center gap-3 px-5 rounded-xl bg-amber-500/10 border border-amber-500/20 animate-pulse">
                           <AlertTriangle className="h-4 w-4 text-amber-600" />
                           <p className="text-[11px] font-bold text-amber-700 uppercase tracking-tight">Assign Target Workspace</p>
                        </div>
                     )}
                  </div>
                  
                  <Button
                    size="lg"
                    className="h-16 px-16 rounded-2xl font-black text-lg bg-primary hover:bg-primary/90 text-primary-foreground shadow-2xl shadow-primary/20 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50"
                    disabled={tb.totalSelected === 0 || step === "applying" || !selectedWorkspaceId}
                    onClick={tb.handleApply}
                  >
                    {step === "applying" ? (
                      <><Loader2 className="h-6 w-6 animate-spin mr-3" /> Save Selected Tasks...</>
                    ) : (
                      <>Save {tb.totalSelected} Tasks</>
                    )}
                  </Button>
                </div>
              </div>
            )}

            {step === "done" && tb.applyResult && (
              <div className="max-w-xl mx-auto py-16 animate-in fade-in zoom-in-95 duration-500">
                <div className="rounded-[3rem] border border-border bg-card p-16 flex flex-col items-center text-center gap-10 shadow-2xl relative overflow-hidden backdrop-blur-sm">
                  <div aria-hidden className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,--theme(--color-green-500/.1)_0,transparent_60%)] pointer-events-none" />
                  
                  <div className="relative">
                     <div className="absolute inset-0 bg-green-500/30 blur-[40px] rounded-full animate-pulse" />
                     <div className="relative w-24 h-24 rounded-full bg-green-600 flex items-center justify-center text-white border-8 border-background shadow-xl">
                        <CheckCircle2 className="h-12 w-12 stroke-[3px]" />
                     </div>
                  </div>
                  
                  <div className="space-y-4">
                    <h2 className="text-4xl font-bold tracking-tighter">Evidence Tasks Created</h2>
                    <p className="text-sm text-muted-foreground leading-relaxed max-w-sm mx-auto font-medium">
                      Evidence collection tasks for <strong>{frameworkName}</strong> have been structured and saved as <strong>{tb.applyResult.created} active items</strong>.
                    </p>
                    <div className="mt-4 inline-flex items-center px-4 py-1.5 rounded-full bg-green-500/10 text-green-600 border border-green-500/20 font-bold text-[11px] uppercase tracking-[0.1em]">
                       Generation Complete
                    </div>
                  </div>
                  
                  <div className="flex gap-4 w-full pt-6">
                    <Button className="flex-1 h-14 rounded-2xl font-bold bg-foreground text-background hover:opacity-90 transition-all active:scale-[0.98]" onClick={() => router.push("/tasks")}>
                       View Task List
                    </Button>
                    <Button variant="outline" className="flex-1 h-14 rounded-2xl font-bold border-border/80" onClick={() => tb.resetState()}>Start New Set</Button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>

      {/* ── Retractable Session Timeline ── */}
      <aside className={cn(
        "fixed right-0 top-[56px] bottom-0 w-[320px] bg-card/95 backdrop-blur-xl border-l border-border transform transition-transform duration-500 ease-in-out z-40 shadow-2xl",
        historyOpen ? "translate-x-0" : "translate-x-full"
      )}>
        <div className="flex flex-col h-full uppercase tracking-tighter font-secondary">
          <div className="h-14 px-6 border-b border-border flex items-center justify-between shrink-0 bg-muted/10">
            <div className="flex items-center gap-2">
              <History className="h-4 w-4 text-primary" />
              <span className="text-[11px] font-bold uppercase tracking-[0.2em] text-foreground">Timeline History</span>
            </div>
            <button onClick={() => setHistoryOpen(false)} className="p-2 rounded-lg hover:bg-muted transition-colors text-muted-foreground hover:text-foreground">
              <X className="h-4.5 w-4.5" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-6 space-y-5 premium-scrollbar">
            {tb.sessions.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-32 text-center px-8 opacity-30">
                <div className="w-20 h-20 rounded-full border-2 border-dashed border-muted-foreground/30 flex items-center justify-center mb-6">
                    <Compass className="h-8 w-8 text-muted-foreground/50 stroke-[1.5]" />
                </div>
                <p className="text-[11px] font-black text-muted-foreground uppercase tracking-[0.25em]">No Iterations Recorded</p>
              </div>
            ) : (
              tb.sessions.map(session => {
                const isActive = session.id === tb.activeSessionId
                const taskCount = session.proposed_tasks
                  ? session.proposed_tasks.reduce((sum, g) => sum + (g.tasks?.length ?? 0), 0)
                  : 0
                return (
                  <button
                    key={session.id}
                    className={cn(
                      "w-full text-left rounded-[1.5rem] border p-5 transition-all group relative overflow-hidden",
                      isActive
                        ? "border-primary bg-primary/[0.08] shadow-xl shadow-primary/10 ring-1 ring-primary/20 scale-[1.02]"
                        : "border-border/60 bg-muted/10 hover:border-primary/30 hover:bg-muted/20 hover:scale-[1.01]"
                    )}
                    onClick={() => tb.hydrateFromSession(session)}
                  >
                    <div className="flex items-center justify-between mb-4">
                       <Badge variant="outline" className={cn("text-[9px] font-black uppercase tracking-widest px-2.5 py-0.5 rounded-full border shadow-sm", isActive ? "border-primary/40 bg-primary/20 text-primary" : STATUS_COLORS[session.status] ?? "text-muted-foreground bg-muted border-border")}>
                        {STATUS_LABELS[session.status] || session.status}
                      </Badge>
                      <span className="text-[10px] font-bold text-muted-foreground/50">
                        {relativeTime(session.created_at)}
                      </span>
                    </div>
 
                    <p className={cn("text-[13px] font-black tracking-tight mb-2 leading-tight", isActive ? "text-primary" : "text-foreground")}>Generated Draft</p>
                    <div className="flex items-center gap-2 mb-3">
                        <Badge variant="secondary" className={cn("h-5 px-2 text-[10px] font-bold border", isActive ? "bg-primary/20 text-primary border-primary/20" : "bg-muted text-muted-foreground border-border/50")}>
                            <Activity className="h-3 w-3 mr-1.5 opacity-50" />
                            {session.status === 'generating' ? 'Drafting...' : `${taskCount} Tasks`}
                        </Badge>
                        {taskCount > 0 && session.status !== 'generating' && (
                          <Badge variant="outline" className="h-5 px-2 text-[9px] font-black uppercase tracking-tighter bg-emerald-500/10 text-emerald-600 border-emerald-500/20">
                            Ready
                          </Badge>
                        )}
                    </div>
 
                    {session.user_context && (
                      <div className="mt-2 block opacity-80">
                        <p className={cn("text-[11px] line-clamp-2 italic font-medium border-l-2 pl-3 py-0.5", isActive ? "border-primary/40" : "border-border/50")}>
                          "{session.user_context}"
                        </p>
                      </div>
                    )}
                  </button>
                )
              })
            )}
          </div>

          <div className="p-5 border-t border-border bg-muted/10">
             <div className="p-4 rounded-xl border border-border/80 bg-background flex items-center gap-4 group hover:border-primary/30 transition-all transition-colors cursor-default shadow-sm font-primary">
                <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary group-hover:scale-105 transition-transform">
                    <ShieldCheck className="h-5 w-5" />
                </div>
                <div>
                    <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-foreground">Draft History</p>
                    <p className="text-[9px] font-bold text-muted-foreground uppercase">Saved Versions</p>
                </div>
             </div>
          </div>
        </div>
      </aside>
    </div>
  )
}