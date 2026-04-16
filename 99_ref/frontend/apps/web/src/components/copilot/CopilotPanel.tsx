"use client"

import {
  useState, useEffect, useRef, useCallback,
  type KeyboardEvent, type DragEvent,
} from "react"
import { useRouter } from "next/navigation"
import {
  X, Send, Plus, Loader2, Bot, User, Sparkles,
  ChevronDown, Check, XCircle, Wrench, CheckCircle2,
  AlertCircle, Database, Search, Paperclip, History,
  FileText, Image, File as FileIcon, Trash2, ExternalLink,
  LayoutGrid, Shield, Eye, ChevronUp, Clock,
  BarChart3, ArrowRight, Edit, Zap, GitBranch, ClipboardList,
  Copy, CheckCheck,
} from "lucide-react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import rehypeHighlight from "rehype-highlight"
import {
  listConversations, createConversation, listMessages, streamMessage,
  approveAction, rejectApproval, getApproval,
  uploadAttachment, listAttachments, deleteAttachment,
  getReport, REPORT_TYPE_LABELS,
  type ConversationResponse, type MessageResponse, type ApprovalResponse,
  type AttachmentResponse, type ReportResponse,
} from "@/lib/api/ai"
import { type CopilotPageContext } from "@/lib/hooks/useCopilotPageContext"
import { ApprovalModal } from "./ApprovalModal"
import { useCopilot, MIN_WIDTH, MAX_WIDTH } from "@/lib/context/CopilotContext"

// ── Types ──────────────────────────────────────────────────────────────────────

interface StreamEvent { type: string; data: Record<string, unknown> }

interface ToolCallEvent {
  tool_name: string
  tool_category: "insight" | "navigation" | "hierarchy" | "action" | "write" | "form_fill"
  input_summary: string
  output_summary?: string
  status: "running" | "done" | "error"
}

interface PendingNavigation {
  path: string
  label: string
  entityType: string
}

interface PendingPageNavigation {
  path: string
  label: string
}

interface PendingReport {
  report_id: string
  report_type: string
  title: string | null
  status: string
}

interface PendingFormFill {
  fields: Record<string, unknown>
  explanation: string
}

interface AttachedFile {
  id: string
  name: string
  size: number
  type: string
  file: File
  // local preview URL for images
  previewUrl?: string
}

// Maps optimistic message id → attachments that were sent with it
type MessageAttachmentMap = Record<string, AttachmentResponse[]>

// ── Helpers ────────────────────────────────────────────────────────────────────

function formatRelative(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  if (diff < 60_000) return "just now"
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`
  return new Date(iso).toLocaleDateString([], { month: "short", day: "numeric" })
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`
}

function getFileIcon(type: string) {
  if (type.startsWith("image/")) return Image
  if (type === "application/pdf" || type.includes("document")) return FileText
  return FileIcon
}

function getContextLabel(ctx: CopilotPageContext): string {
  // Most-specific wins: control > risk > task > framework > workspace
  // Show human-readable name when available — never show raw UUIDs
  if (ctx.control_id) {
    const label = ctx.control_code ? `${ctx.control_code}${ctx.control_name ? ` — ${ctx.control_name}` : ""}` : "Control"
    return label
  }
  if (ctx.risk_id) return ctx.risk_title ?? "Risk"
  if (ctx.task_id) return ctx.task_title ? `Task: ${ctx.task_title.slice(0, 40)}` : "Task"
  if (ctx.framework_id) return ctx.framework_name ?? "Framework"
  if (ctx.workspace_id) return ctx.workspace_name ? `Workspace: ${ctx.workspace_name}` : "Workspace"
  return "Dashboard"
}

// ── NavigationCard ────────────────────────────────────────────────────────────

const ENTITY_ICONS: Record<string, React.ElementType> = {
  framework: LayoutGrid,
  control: Shield,
  risk: AlertCircle,
  task: CheckCircle2,
}

function NavigationCard({
  nav,
  onNavigate,
}: {
  nav: PendingNavigation
  onNavigate: () => void
}) {
  const Icon = ENTITY_ICONS[nav.entityType] ?? ExternalLink
  const typeLabel = nav.entityType.charAt(0).toUpperCase() + nav.entityType.slice(1)
  return (
    <button
      onClick={onNavigate}
      className="flex items-center gap-3 w-full text-left px-3 py-2.5 rounded-xl border border-violet-500/30 bg-violet-500/5 hover:bg-violet-500/10 hover:border-violet-500/50 transition-colors group"
    >
      <div className="w-8 h-8 rounded-lg bg-violet-500/15 flex items-center justify-center shrink-0">
        <Icon className="w-4 h-4 text-violet-400" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-foreground/80 truncate">{nav.label}</p>
        <p className="text-[10px] text-violet-400/60">Open {typeLabel} →</p>
      </div>
      <ExternalLink className="w-3 h-3 text-violet-400/40 group-hover:text-violet-400 shrink-0 transition-colors" />
    </button>
  )
}

// ── PageNavigationCard ────────────────────────────────────────────────────────

const PAGE_ROUTES: Record<string, string> = {
  dashboard: "/dashboard",
  frameworks: "/frameworks",
  marketplace: "/frameworks?tab=marketplace",
  risks: "/risks",
  tasks: "/tasks",
  reports: "/reports",
  copilot: "/copilot",
  sandbox: "/sandbox",
  sandbox_connectors: "/sandbox/connectors",
  sandbox_signals: "/sandbox/signals",
  sandbox_libraries: "/sandbox/libraries",
  settings_profile: "/settings/profile",
  settings_security: "/settings/security",
  settings_notifications: "/settings/notifications",
  settings_api_keys: "/settings/api-keys",
  settings_features: "/settings/features",
  admin_overview: "/admin",
  admin_users: "/admin/users",
  admin_roles: "/admin/roles",
  admin_orgs: "/admin/orgs",
  admin_features: "/admin/features",
  admin_library_frameworks: "/admin/library/frameworks",
}

function PageNavigationCard({
  nav,
  onNavigate,
}: {
  nav: PendingPageNavigation
  onNavigate: () => void
}) {
  return (
    <button
      onClick={onNavigate}
      className="flex items-center gap-3 w-full text-left px-3 py-2.5 rounded-xl border border-violet-500/30 bg-violet-500/5 hover:bg-violet-500/10 hover:border-violet-500/50 transition-colors group"
    >
      <div className="w-8 h-8 rounded-lg bg-violet-500/15 flex items-center justify-center shrink-0">
        <ExternalLink className="w-4 h-4 text-violet-400" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-foreground/80 truncate">{nav.label}</p>
        <p className="text-[10px] text-violet-400/60">Go to page →</p>
      </div>
      <ArrowRight className="w-3 h-3 text-violet-400/40 group-hover:text-violet-400 shrink-0 transition-colors" />
    </button>
  )
}

// ── FormFillCard ──────────────────────────────────────────────────────────────

function FormFillCard({
  fill,
  onDismiss,
}: {
  fill: PendingFormFill
  onDismiss: () => void
}) {
  const [copied, setCopied] = useState(false)
  const entries = Object.entries(fill.fields).filter(([, v]) => v !== null && v !== undefined && v !== "")

  function handleCopy() {
    const text = entries.map(([k, v]) => `${k}: ${String(v)}`).join("\n")
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  return (
    <div className="rounded-xl border border-sky-500/25 bg-sky-500/5 overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 border-b border-sky-500/15">
        <div className="flex items-center gap-2">
          <ClipboardList className="w-3.5 h-3.5 text-sky-400" />
          <span className="text-xs font-semibold text-sky-400">Form fill suggestion</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={handleCopy}
            className="p-1 rounded hover:bg-sky-500/10 text-sky-400/60 hover:text-sky-400 transition-colors"
            aria-label="Copy fields"
          >
            {copied ? <CheckCheck className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
          </button>
          <button
            onClick={onDismiss}
            className="p-1 rounded hover:bg-sky-500/10 text-sky-400/60 hover:text-sky-400 transition-colors"
            aria-label="Dismiss"
          >
            <X className="w-3 h-3" />
          </button>
        </div>
      </div>
      {fill.explanation && (
        <p className="px-3 pt-2 text-[11px] text-muted-foreground">{fill.explanation}</p>
      )}
      <div className="px-3 py-2 space-y-1">
        {entries.map(([key, value]) => (
          <div key={key} className="flex items-start gap-2 text-xs">
            <span className="font-mono text-sky-400/70 shrink-0 min-w-[120px] truncate">{key}</span>
            <span className="text-foreground/80 break-all">{String(value)}</span>
          </div>
        ))}
        {entries.length === 0 && (
          <p className="text-xs text-muted-foreground/50 italic">No fields suggested</p>
        )}
      </div>
    </div>
  )
}

// ── ReportCard ────────────────────────────────────────────────────────────────

const REPORT_STATUS_CONFIG: Record<string, { label: string; color: string; spinning: boolean }> = {
  queued:     { label: "Queued",          color: "text-slate-400",   spinning: false },
  planning:   { label: "Planning",        color: "text-blue-400",    spinning: true  },
  collecting: { label: "Collecting data", color: "text-blue-400",    spinning: true  },
  analyzing:  { label: "Analyzing",       color: "text-purple-400",  spinning: true  },
  writing:    { label: "Writing",         color: "text-amber-400",   spinning: true  },
  formatting: { label: "Formatting",      color: "text-amber-400",   spinning: true  },
  completed:  { label: "Completed",       color: "text-emerald-400", spinning: false },
  failed:     { label: "Failed",          color: "text-red-400",     spinning: false },
}
const IN_PROGRESS = new Set(["queued", "planning", "collecting", "analyzing", "writing", "formatting"])

function ReportCard({ report: initial }: { report: PendingReport }) {
  const [report, setReport] = useState<PendingReport>(initial)
  const [expanded, setExpanded] = useState(false)
  const [fullReport, setFullReport] = useState<ReportResponse | null>(null)
  const pollRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const router = useRouter()

  useEffect(() => {
    if (!IN_PROGRESS.has(report.status)) return
    const poll = async () => {
      try {
        const r = await getReport(report.report_id)
        setReport(prev => ({ ...prev, status: r.status_code, title: r.title ?? prev.title }))
        if (r.status_code === "completed") setFullReport(r)
        if (IN_PROGRESS.has(r.status_code)) {
          pollRef.current = setTimeout(poll, 4000)
        }
      } catch { /* ignore */ }
    }
    pollRef.current = setTimeout(poll, 3000)
    return () => { if (pollRef.current) clearTimeout(pollRef.current) }
  }, [report.report_id, report.status])

  const sc = REPORT_STATUS_CONFIG[report.status] ?? REPORT_STATUS_CONFIG.queued
  const label = report.title || REPORT_TYPE_LABELS[report.report_type] || report.report_type

  return (
    <div className="rounded-xl border border-purple-500/25 bg-purple-500/5 overflow-hidden">
      <div className="flex items-center gap-3 px-3 py-2.5">
        <div className="w-7 h-7 rounded-lg bg-purple-500/15 flex items-center justify-center shrink-0">
          <BarChart3 className="w-3.5 h-3.5 text-purple-400" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-foreground/80 truncate">{label}</p>
          <span className={`flex items-center gap-1 text-[10px] ${sc.color}`}>
            {sc.spinning
              ? <Loader2 className="w-2.5 h-2.5 animate-spin" />
              : report.status === "completed"
              ? <Check className="w-2.5 h-2.5" />
              : report.status === "failed"
              ? <XCircle className="w-2.5 h-2.5" />
              : <Clock className="w-2.5 h-2.5" />
            }
            {sc.label}
          </span>
        </div>
        {report.status === "completed" && (
          <div className="flex items-center gap-1 shrink-0">
            <button
              onClick={() => setExpanded(e => !e)}
              className="flex items-center gap-1 px-2 py-1 rounded-md bg-purple-500/15 hover:bg-purple-500/25 text-[10px] text-purple-300 transition-colors"
            >
              <Eye className="w-3 h-3" />
              {expanded ? "Hide" : "View"}
            </button>
            <button
              onClick={() => router.push("/reports")}
              className="p-1 rounded-md hover:bg-white/5 text-white/30 hover:text-white/60 transition-colors"
              title="Open Reports page"
            >
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>
      {expanded && fullReport?.content_markdown && (
        <div className="border-t border-purple-500/15 px-3 py-3 max-h-96 overflow-y-auto">
          <pre className="text-[11px] text-foreground/70 whitespace-pre-wrap font-sans leading-relaxed">
            {fullReport.content_markdown}
          </pre>
        </div>
      )}
    </div>
  )
}

// ── ToolCallPill ──────────────────────────────────────────────────────────────

const CATEGORY_ICONS: Record<ToolCallEvent["tool_category"], React.ElementType> = {
  insight: Database,
  navigation: Search,
  hierarchy: GitBranch,
  action: Zap,
  write: Edit,
  form_fill: ClipboardList,
}

function ToolCallPill({ call }: { call: ToolCallEvent }) {
  const Icon = CATEGORY_ICONS[call.tool_category] ?? Search
  const label = call.tool_name.replace(/^grc_/, "").replace(/_/g, " ")

  return (
    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[11px] font-medium my-0.5
      border-violet-500/20 bg-violet-500/5 text-violet-400">
      <Icon className="w-2.5 h-2.5 shrink-0" />
      <span className="font-mono">{label}</span>
      {call.input_summary && (
        <span className="text-violet-300/50 truncate max-w-[120px]">{call.input_summary}</span>
      )}
      {call.status === "running" && <Loader2 className="w-2.5 h-2.5 animate-spin shrink-0" />}
      {call.status === "done" && <CheckCircle2 className="w-2.5 h-2.5 text-emerald-400 shrink-0" />}
      {call.status === "error" && <AlertCircle className="w-2.5 h-2.5 text-red-400 shrink-0" />}
      {call.status === "done" && call.output_summary && (
        <span className="text-emerald-400/60 truncate max-w-[80px]">{call.output_summary}</span>
      )}
    </div>
  )
}

// ── MessageBubble ─────────────────────────────────────────────────────────────

function MessageBubble({
  msg,
  sentAttachments,
  onApprove,
  onReject,
  onSelectAttachment,
}: {
  msg: MessageResponse
  sentAttachments?: AttachmentResponse[]
  onApprove: (id: string) => Promise<void>
  onReject: (id: string, reason: string) => Promise<void>
  onSelectAttachment: (att: AttachmentResponse) => void
}) {
  const isUser = msg.role_code === "user"

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"} group`}>
      {/* Avatar */}
      <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5
        ${isUser ? "bg-primary" : "bg-gradient-to-br from-violet-500/30 to-purple-500/20"}`}>
        {isUser
          ? <User className="w-3.5 h-3.5 text-primary-foreground" />
          : <Sparkles className="w-3.5 h-3.5 text-violet-400" />}
      </div>

      {/* Content */}
      <div className={`flex-1 min-w-0 flex flex-col gap-1.5 ${isUser ? "items-end" : "items-start"}`}>
        {/* Attachment chips (user messages only) */}
        {isUser && sentAttachments && sentAttachments.length > 0 && (
          <div className="flex flex-wrap gap-1.5 max-w-[85%] justify-end mt-1">
            {sentAttachments.map(att => (
              <SentAttachmentChip key={att.id} att={att} onSelect={() => onSelectAttachment(att)} />
            ))}
          </div>
        )}
        {isUser ? (
          <div className="max-w-[85%] bg-primary text-primary-foreground rounded-2xl rounded-tr-sm px-3.5 py-2.5 text-sm leading-relaxed">
            <p className="whitespace-pre-wrap break-words">{msg.content}</p>
          </div>
        ) : (
          <div className="copilot-md w-full text-sm leading-relaxed text-foreground/90 py-0.5">
            <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]} components={{ p: ({ children }) => <div className="mb-1 last:mb-0">{children}</div> }}>
              {msg.content}
            </ReactMarkdown>
          </div>
        )}
        <span className="text-[10px] text-muted-foreground/30 opacity-0 group-hover:opacity-100 transition-opacity px-1">
          {formatRelative(msg.created_at)}
        </span>
      </div>
    </div>
  )
}

// ── ThinkingIndicator ─────────────────────────────────────────────────────────

const THINKING_PHRASES = [
  "Thinking…", "Reasoning…", "Analyzing…", "Processing…", "Examining…",
  "Considering…", "Evaluating…", "Reflecting…", "Deliberating…", "Contemplating…",
  "Synthesizing…", "Investigating…", "Calculating…", "Formulating…", "Sifting data…",
  "Connecting dots…", "Reading context…", "Cross-referencing…", "Interpreting…", "Working…",
]

function ThinkingIndicator() {
  const [phraseIdx, setPhraseIdx] = useState(0)
  const [visible, setVisible] = useState(true)

  useEffect(() => {
    const fade = setInterval(() => {
      setVisible(false)
      setTimeout(() => {
        setPhraseIdx(i => (i + 1) % THINKING_PHRASES.length)
        setVisible(true)
      }, 300)
    }, 1800)
    return () => clearInterval(fade)
  }, [])

  return (
    <div className="flex items-center gap-2">
      <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-bounce [animation-delay:0ms]" />
      <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-bounce [animation-delay:120ms]" />
      <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-bounce [animation-delay:240ms]" />
      <span
        className="text-xs text-violet-400/70 font-mono transition-opacity duration-300 ml-1"
        style={{ opacity: visible ? 1 : 0 }}
      >
        {THINKING_PHRASES[phraseIdx]}
      </span>
    </div>
  )
}

// ── StreamingBubble ───────────────────────────────────────────────────────────

function StreamingBubble({ content, toolCalls }: { content: string; toolCalls: ToolCallEvent[] }) {
  return (
    <div className="flex gap-3">
      <div className="w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5
        bg-gradient-to-br from-violet-500/30 to-purple-500/20">
        <Sparkles className="w-3.5 h-3.5 text-violet-400" />
      </div>
      <div className="flex-1 min-w-0 space-y-1.5 py-0.5">
        {toolCalls.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {toolCalls.map((call, i) => (
              <ToolCallPill key={`${call.tool_name}-${i}`} call={call} />
            ))}
          </div>
        )}
        {content ? (
          <div className="copilot-md text-sm leading-relaxed text-foreground/90">
            <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]} components={{ p: ({ children }) => <div className="mb-1 last:mb-0">{children}</div> }}>
              {content}
            </ReactMarkdown>
          </div>
        ) : toolCalls.length === 0 ? (
          <ThinkingIndicator />
        ) : null}
      </div>
    </div>
  )
}

// ── HistoryDrawer ─────────────────────────────────────────────────────────────

function HistoryDrawer({
  conversations,
  activeId,
  onSelect,
  onNew,
  onClose,
}: {
  conversations: ConversationResponse[]
  activeId: string | null
  onSelect: (id: string) => void
  onNew: () => void
  onClose: () => void
}) {
  return (
    <div className="absolute inset-0 z-20 bg-background flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border/50 shrink-0">
        <p className="text-sm font-semibold">Conversation history</p>
        <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-muted/60 text-muted-foreground">
          <X className="w-4 h-4" />
        </button>
      </div>
      <div className="p-2.5 border-b border-border/50">
        <button
          onClick={() => { onNew(); onClose() }}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-xl bg-primary/8 hover:bg-primary/15 text-primary text-xs font-semibold transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          New conversation
        </button>
      </div>
      <div className="flex-1 overflow-y-auto py-2 px-2 space-y-0.5">
        {conversations.length === 0 ? (
          <p className="text-[11px] text-muted-foreground/50 text-center py-8">No conversations yet</p>
        ) : (
          conversations.map(c => (
            <button
              key={c.id}
              onClick={() => { onSelect(c.id); onClose() }}
              className={`w-full text-left px-3 py-2.5 rounded-xl text-xs transition-colors
                ${activeId === c.id
                  ? "bg-violet-500/10 text-violet-400"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted/50"}`}
            >
              <p className="font-medium truncate">{c.title ?? "Untitled conversation"}</p>
              <p className="text-[10px] opacity-50 mt-0.5">{formatRelative(c.updated_at)}</p>
            </button>
          ))
        )}
      </div>
    </div>
  )
}

// ── AttachmentPreviewModal ────────────────────────────────────────────────────

function AttachmentPreviewModal({
  file,
  onClose,
}: {
  file: AttachedFile | AttachmentResponse
  onClose: () => void
}) {
  useEffect(() => {
    const handler = (e: globalThis.KeyboardEvent) => { if (e.key === "Escape") onClose() }
    document.addEventListener("keydown", handler)
    return () => document.removeEventListener("keydown", handler)
  }, [onClose])

  const isAttachedFile = "file" in file
  const name = isAttachedFile ? file.name : file.filename
  const size = isAttachedFile ? file.size : file.file_size_bytes
  const type = isAttachedFile ? file.type : file.content_type
  const previewUrl = isAttachedFile ? file.previewUrl : undefined
  const isImage = type.startsWith("image/")

  return (
    <div 
      className="absolute inset-0 z-[100] flex flex-col bg-background animate-in fade-in slide-in-from-right-8 duration-500 overflow-hidden" 
      onClick={onClose}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-5 border-b border-border/40 bg-background/50 backdrop-blur-md shrink-0">
        <div className="flex items-center gap-4 min-w-0">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-violet-500/20 to-purple-500/10 flex items-center justify-center border border-violet-500/10 shrink-0">
            {isImage ? <Image className="w-5 h-5 text-violet-400" /> : <FileText className="w-5 h-5 text-violet-400" />}
          </div>
          <div className="flex-1 min-w-0 mr-4">
            <h3 className="text-sm font-bold text-foreground truncate">{name}</h3>
            <span className="text-[10px] text-muted-foreground/60 font-semibold tracking-wider uppercase">
              {formatBytes(size)} • {isImage ? "IMAGE" : type.includes("/") ? type.split('/')[1].toUpperCase() : "FILE"}
            </span>
          </div>
        </div>
        <button 
          onClick={(e) => { e.stopPropagation(); onClose() }} 
          className="w-10 h-10 rounded-full bg-muted/50 hover:bg-muted text-muted-foreground hover:text-foreground flex items-center justify-center transition-all hover:rotate-90"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Content Area */}
      <div className="flex-1 min-h-0 overflow-y-auto p-4 flex flex-col items-center justify-center bg-zinc-950/2" onClick={e => e.stopPropagation()}>
        {isImage && previewUrl ? (
          <div className="relative w-full h-full flex items-center justify-center">
            <img 
              src={previewUrl} 
              alt={name} 
              className="max-w-full max-h-full object-contain rounded-xl shadow-2xl animate-in zoom-in-95 duration-700" 
            />
          </div>
        ) : isImage && !previewUrl ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-4 py-32 opacity-30 text-center">
            <Image className="w-12 h-12 text-muted-foreground" />
            <p className="text-xs font-mono">No live preview for this file</p>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center gap-6 py-20 text-center px-4">
            <div className="w-24 h-24 rounded-[2.5rem] bg-violet-500/5 flex items-center justify-center border border-violet-500/10 shadow-xl">
              <FileIcon className="w-12 h-12 text-violet-400/40" />
            </div>
            <div className="space-y-1">
              <p className="text-base font-bold text-foreground">{name}</p>
              <p className="text-xs text-muted-foreground">{formatBytes(size)} • {type}</p>
            </div>
            {!isAttachedFile && (
              <div className="mt-4 space-y-3">
                <div className="flex gap-4 p-4 rounded-2xl bg-muted/30 border border-border/40">
                  <div className="flex flex-col items-center gap-1">
                    <span className="text-[9px] uppercase font-bold text-muted-foreground/40">Vector</span>
                    <AttachmentStatusBadge status={file.ingest_status} chunkCount={file.chunk_count} />
                  </div>
                  <div className="w-px h-8 bg-border/40" />
                  <div className="flex flex-col items-center gap-1">
                    <span className="text-[9px] uppercase font-bold text-muted-foreground/40">Graph Index</span>
                    <PageIndexStatusBadge status={file.pageindex_status} />
                  </div>
                </div>
                {(file.error_message || file.pageindex_error) && (
                  <div className="max-w-xl rounded-2xl border border-red-500/20 bg-red-500/5 px-4 py-3 text-left">
                    {file.error_message && (
                      <p className="text-xs text-red-300">{file.error_message}</p>
                    )}
                    {file.pageindex_error && (
                      <p className="text-xs text-amber-300 mt-1">{file.pageindex_error}</p>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

    </div>
  )
}

// ── AttachmentStatusBadge ─────────────────────────────────────────────────────

function AttachmentStatusBadge({
  status,
  chunkCount,
}: {
  status: AttachmentResponse["ingest_status"]
  chunkCount: number
}) {
  if (status === "ready") {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400 font-medium">
        <CheckCircle2 className="w-3 h-3" />
        {chunkCount > 0 ? `${chunkCount} chunks` : "Ready"}
      </span>
    )
  }
  if (status === "ingesting" || status === "pending") {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] text-violet-400 font-medium">
        <Loader2 className="w-3 h-3 animate-spin" />
        Processing…
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1 text-[10px] text-red-400 font-medium">
      <XCircle className="w-3 h-3" />
      Failed
    </span>
  )
}

// ── PageIndexStatusBadge ──────────────────────────────────────────────────────

function PageIndexStatusBadge({
  status,
}: {
  status: AttachmentResponse["pageindex_status"]
}) {
  if (status === "ready") {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] text-sky-400 font-medium">
        <CheckCircle2 className="w-3 h-3" />
        TOC indexed
      </span>
    )
  }
  if (status === "indexing") {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] text-sky-400/70 font-medium">
        <Loader2 className="w-3 h-3 animate-spin" />
        Indexing…
      </span>
    )
  }
  if (status === "failed") {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] text-amber-400 font-medium">
        <AlertCircle className="w-3 h-3" />
        Index failed
      </span>
    )
  }
  // none — not a supported type or feature disabled
  return (
    <span className="inline-flex items-center gap-1 text-[10px] text-muted-foreground/40 font-medium">
      <span>—</span>
    </span>
  )
}

// ── AttachmentChip (pre-send, in input area) ──────────────────────────────────

function AttachmentChip({ file, onSelect }: { file: AttachedFile; onSelect: () => void }) {
  const Icon = getFileIcon(file.type)
  const isImage = file.type.startsWith("image/")

  return (
    <div 
      onClick={onSelect}
      className="relative group w-16 h-16 rounded-2xl border border-border/60 bg-muted/40 overflow-visible transition-all hover:border-violet-500/50 shadow-sm animate-in fade-in zoom-in duration-300 cursor-pointer"
    >
      {isImage && file.previewUrl ? (
        /* eslint-disable-next-line @next/next/no-img-element */
        <img src={file.previewUrl} alt={file.name} className="w-full h-full object-cover rounded-[inherit] transition-transform duration-500 group-hover:scale-105" />
      ) : (
        <div className="w-full h-full flex flex-col items-center justify-center p-2 gap-1 text-center">
          <Icon className="w-5 h-5 text-violet-400" />
          <span className="text-[8px] font-medium text-foreground/60 truncate w-full">{file.name}</span>
        </div>
      )}
      
      {/* Handled by parent to avoid multi-modal issues */}
    </div>
  )
}

// ── SentAttachmentChip (in-chat, after send) ──────────────────────────────────

function SentAttachmentChip({ att, onSelect }: { att: AttachmentResponse; onSelect: () => void }) {
  const isImage = att.content_type.startsWith("image/")
  const Icon = isImage ? Image : (att.content_type === "application/pdf" || att.content_type.includes("document")) ? FileText : FileIcon

  return (
    <button
      onClick={onSelect}
      className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl border border-border/60 bg-background hover:bg-muted/40 hover:border-border text-[11px] transition-all group animate-in fade-in slide-in-from-left-2 duration-200"
      title="Review attachment"
    >
      <Icon className="w-3.5 h-3.5 shrink-0 text-violet-400/80" />
      <div className="flex-1 min-w-0 pr-1 text-left">
        <p className="truncate max-w-[140px] font-medium text-foreground/80 group-hover:text-foreground transition-colors">{att.filename}</p>
      </div>
      <div className="flex items-center gap-1.5 shrink-0">
        {att.pageindex_status === "ready" && <span className="text-[9px] font-bold text-sky-400/40">TOC</span>}
        {att.ingest_status === "ready" 
          ? <CheckCircle2 className="w-2.5 h-2.5 text-emerald-500/40" /> 
          : att.ingest_status === "failed"
          ? <XCircle className="w-2.5 h-2.5 text-red-500/40" />
          : <Loader2 className="w-2.5 h-2.5 text-muted-foreground/40 animate-spin" />}
        <Eye className="w-3 h-3 text-muted-foreground/40 group-hover:text-violet-400 opacity-0 group-hover:opacity-100 transition-opacity" />
      </div>
    </button>
  )
}

// ── ConversationAttachmentsPanel ──────────────────────────────────────────────

function ConversationAttachmentsPanel({
  conversationId,
  onDeleted,
  onSelect,
}: {
  conversationId: string
  onDeleted: () => void
  onSelect: (att: AttachmentResponse) => void
}) {
  const [attachments, setAttachments] = useState<AttachmentResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    listAttachments(conversationId)
      .then(r => setAttachments(r.items))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [conversationId])

  async function handleDelete(att: AttachmentResponse) {
    setDeletingId(att.id)
    try {
      await deleteAttachment(conversationId, att.id)
      setAttachments(prev => prev.filter(a => a.id !== att.id))
      onDeleted()
    } catch { /* ignore */ }
    finally { setDeletingId(null) }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-10">
        <Loader2 className="w-5 h-5 animate-spin text-muted-foreground/20" />
      </div>
    )
  }

  if (attachments.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-10 opacity-30">
         <Paperclip className="w-8 h-8 mb-2" />
         <p className="text-[11px] font-medium uppercase tracking-widest">No attachments</p>
      </div>
    )
  }

  return (
    <div className="space-y-1 pt-1 pr-2">
      {attachments.map(att => {
        const isImage = att.content_type.startsWith("image/")
        const Icon = isImage ? Image : (att.content_type === "application/pdf" || att.content_type.includes("document")) ? FileText : FileIcon
        return (
          <div key={att.id} className="flex items-center gap-3 px-3 py-2.5 rounded-2xl hover:bg-muted/40 group cursor-pointer transition-all border border-transparent hover:border-border/40" onClick={() => onSelect(att)}>
            <div className="w-9 h-9 rounded-xl bg-violet-500/5 flex items-center justify-center border border-violet-500/5 shrink-0 group-hover:bg-violet-500/10 transition-colors">
              <Icon className="w-4 h-4 text-violet-400/80" />
            </div>
            <div className="flex-1 min-w-0 mr-2">
              <p className="text-xs font-bold truncate text-foreground/80 group-hover:text-foreground transition-colors leading-tight">{att.filename}</p>
              <div className="flex items-center gap-2 mt-1 translate-y-[-1px]">
                <span className="text-[9px] font-bold text-muted-foreground/40 uppercase tracking-tighter">{formatBytes(att.file_size_bytes)}</span>
                <AttachmentStatusBadge status={att.ingest_status} chunkCount={att.chunk_count} />
                {att.pageindex_status !== "none" && (
                  <PageIndexStatusBadge status={att.pageindex_status} />
                )}
              </div>
            </div>
            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all shrink-0">
              <button
                onClick={(e) => { e.stopPropagation(); onSelect(att) }}
                className="p-1.5 rounded-lg text-muted-foreground/30 hover:text-violet-400 hover:bg-violet-500/10 transition-all"
                title="Preview"
              >
                <Eye className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); handleDelete(att) }}
                disabled={deletingId === att.id}
                className="p-1.5 rounded-lg text-muted-foreground/20 hover:text-red-400 hover:bg-red-500/10 transition-all disabled:opacity-50"
                title="Delete"
              >
                {deletingId === att.id ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Trash2 className="w-3.5 h-3.5" />
                )}
              </button>
            </div>
          </div>
        )
      })}
    </div>
  )
}

// ── ResizeHandle ──────────────────────────────────────────────────────────────

function ResizeHandle({ onResize }: { onResize: (delta: number) => void }) {
  const dragging = useRef(false)
  const lastX = useRef(0)
  // Keep a stable ref to the latest onResize so the mousemove handler
  // never captures a stale closure over `width`.
  const onResizeRef = useRef(onResize)
  onResizeRef.current = onResize

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    dragging.current = true
    lastX.current = e.clientX
    document.body.style.cursor = "col-resize"
    document.body.style.userSelect = "none"

    const move = (ev: MouseEvent) => {
      if (!dragging.current) return
      const delta = lastX.current - ev.clientX
      lastX.current = ev.clientX
      onResizeRef.current(delta)
    }
    const up = () => {
      dragging.current = false
      document.removeEventListener("mousemove", move)
      document.removeEventListener("mouseup", up)
      document.body.style.cursor = ""
      document.body.style.userSelect = ""
    }
    document.addEventListener("mousemove", move)
    document.addEventListener("mouseup", up)
  }, []) // stable — no deps needed since we use refs

  return (
    <div
      onMouseDown={onMouseDown}
      className="absolute left-0 top-0 bottom-0 w-1.5 cursor-col-resize z-30 group"
    >
      {/* Wider invisible hit area + visible hover indicator */}
      <div className="absolute -left-2 top-0 bottom-0 w-5 group-hover:bg-violet-500/10 transition-colors" />
      <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-transparent group-hover:bg-violet-500/40 group-active:bg-violet-500/60 transition-colors rounded-full" />
    </div>
  )
}

// ── EmptyState ────────────────────────────────────────────────────────────────

function EmptyState({
  pageContext,
  onPrompt,
  onNew,
  loading,
}: {
  pageContext: CopilotPageContext
  onPrompt: (p: string) => void
  onNew: () => void
  loading: boolean
}) {
  const contextLabel = getContextLabel(pageContext)
  // Suggestions are enriched with actual entity names wherever available
  const controlRef = pageContext.control_code ?? "this control"
  const frameworkRef = pageContext.framework_name ?? "this framework"
  const riskRef = pageContext.risk_title ?? "this risk"
  const taskRef = pageContext.task_title ? `"${pageContext.task_title.slice(0, 40)}"` : "this task"

  const suggestions = pageContext.control_id
    ? [
        `What is the health of ${controlRef}? Any overdue tasks or failing tests?`,
        `Which risks are linked to ${controlRef} and how critical are they?`,
        `Does ${controlRef} have an owner and responsible teams assigned?`,
      ]
    : pageContext.risk_id
    ? [
        `Summarize ${riskRef} — what is the severity and treatment status?`,
        `Which controls are mapped to ${riskRef}?`,
        `What tasks are open to address ${riskRef}?`,
      ]
    : pageContext.task_id
    ? [
        `Summarize the task ${taskRef} — what needs to be done?`,
        `What control or risk does ${taskRef} relate to?`,
        `What is the priority and due date of ${taskRef}?`,
      ]
    : pageContext.framework_id
    ? [
        `What is the compliance health of ${frameworkRef}? How many controls are passing?`,
        `Which controls in ${frameworkRef} have the most overdue tasks or missing tests?`,
        `Show me the riskiest controls in ${frameworkRef} by linked risk count`,
      ]
    : [
        "What are my top open risks across all frameworks?",
        "Which controls have missing evidence or overdue tasks right now?",
        "Show me frameworks with the most compliance gaps",
      ]

  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-5 px-6 py-10 text-center">
      <div>
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-500/20 to-purple-600/10 flex items-center justify-center ring-1 ring-violet-500/20">
          <Sparkles className="w-8 h-8 text-violet-400" />
        </div>
      </div>
      <div className="space-y-1">
        <p className="font-semibold text-foreground">AI Copilot</p>
        <p className="text-xs text-muted-foreground">
          {contextLabel !== "Dashboard"
            ? `Viewing: ${contextLabel}`
            : "Ask anything about your GRC posture, frameworks, risks, or tasks."}
        </p>
      </div>
      <div className="w-full space-y-1.5">
        {suggestions.map(s => (
          <button
            key={s}
            onClick={() => onPrompt(s)}
            className="w-full text-left text-xs px-3.5 py-2.5 rounded-xl border border-border/50 hover:border-violet-500/30 bg-muted/20 hover:bg-violet-500/5 text-muted-foreground hover:text-foreground transition-all"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  )
}

// ── Main CopilotPanel ─────────────────────────────────────────────────────────

// ── Session storage helpers ────────────────────────────────────────────────────

const SS_CONV_ID = "kcontrol:copilot:activeConvId"
const SS_CTX_HISTORY = "kcontrol:copilot:ctxHistory"
const MAX_CTX_HISTORY = 5

function ssGet(key: string): string | null {
  try { return sessionStorage.getItem(key) } catch { return null }
}
function ssSet(key: string, val: string) {
  try { sessionStorage.setItem(key, val) } catch { /* ignore */ }
}
function ssDel(key: string) {
  try { sessionStorage.removeItem(key) } catch { /* ignore */ }
}

export function CopilotPanel({ pageContext }: { pageContext: CopilotPageContext }) {
  const { isOpen, close, width, setWidth } = useCopilot()
  const router = useRouter()

  const [conversations, setConversations] = useState<ConversationResponse[]>([])
  const [activeConvId, setActiveConvId] = useState<string | null>(() => ssGet(SS_CONV_ID))
  const [messages, setMessages] = useState<MessageResponse[]>([])
  const [approvalQueue, setApprovalQueue] = useState<ApprovalResponse[]>([])
  const [streamContent, setStreamContent] = useState("")
  const [streamToolCalls, setStreamToolCalls] = useState<ToolCallEvent[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [loadingMsgs, setLoadingMsgs] = useState(false)
  const [showHistory, setShowHistory] = useState(false)
  const [attachments, setAttachments] = useState<AttachedFile[]>([])
  const [previewAttachment, setPreviewAttachment] = useState<AttachedFile | AttachmentResponse | null>(null)
  const [uploadingFiles, setUploadingFiles] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const [msgAttachments, setMsgAttachments] = useState<MessageAttachmentMap>({})
  const [showAttachmentsPanel, setShowAttachmentsPanel] = useState(false)
  const [pendingNavigation, setPendingNavigation] = useState<PendingNavigation | null>(null)
  const [pendingPageNavigation, setPendingPageNavigation] = useState<PendingPageNavigation | null>(null)
  const [pendingReports, setPendingReports] = useState<PendingReport[]>([])
  const [pendingFormFills, setPendingFormFills] = useState<PendingFormFill[]>([])
  const [streamError, setStreamError] = useState<string | null>(null)
  const [approvalResult, setApprovalResult] = useState<{ success: boolean; message: string } | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Persist activeConvId to sessionStorage
  const setActiveConvIdPersisted = useCallback((id: string | null) => {
    setActiveConvId(id)
    if (id) ssSet(SS_CONV_ID, id)
    else ssDel(SS_CONV_ID)
  }, [])

  // Track page context history (last 5 unique routes) in sessionStorage
  useEffect(() => {
    if (!pageContext.route) return
    try {
      const raw = ssGet(SS_CTX_HISTORY)
      const history: CopilotPageContext[] = raw ? JSON.parse(raw) : []
      // Only add if route changed from last entry
      if (history.length === 0 || history[history.length - 1].route !== pageContext.route) {
        const updated = [...history, pageContext].slice(-MAX_CTX_HISTORY)
        ssSet(SS_CTX_HISTORY, JSON.stringify(updated))
      } else {
        // Update last entry in place (org/workspace may have changed)
        history[history.length - 1] = pageContext
        ssSet(SS_CTX_HISTORY, JSON.stringify(history))
      }
    } catch { /* ignore */ }
  }, [pageContext])

  const loadConversations = useCallback(async () => {
    try {
      const res = await listConversations(false, 50, 0)
      setConversations(res.items)
    } catch { /* ignore */ }
  }, [])

  useEffect(() => {
    if (isOpen) loadConversations()
  }, [isOpen, loadConversations])

  const loadMessages = useCallback(async (convId: string) => {
    setLoadingMsgs(true)
    try {
      const msgs = await listMessages(convId, 100)
      const sortedMsgs = msgs.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
      setMessages(sortedMsgs)
      return sortedMsgs
    } catch { /* ignore */ }
    finally { setLoadingMsgs(false) }
  }, [])

  // Load messages when activeConvId changes (e.g. restored from sessionStorage on mount)
  const prevConvId = useRef<string | null>(null)
  useEffect(() => {
    if (activeConvId && activeConvId !== prevConvId.current) {
      prevConvId.current = activeConvId
      setMessages([])
      setApprovalQueue([])
      setPendingNavigation(null)
      setPendingPageNavigation(null)
      setPendingReports([])
      setPendingFormFills([])
      loadMessages(activeConvId)
    }
  }, [activeConvId, loadMessages])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, streamContent, streamToolCalls])

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current
    if (!ta) return
    ta.style.height = "auto"
    ta.style.height = `${Math.min(ta.scrollHeight, 120)}px`
  }, [input])

  const handleResize = useCallback((delta: number) => {
    // Use functional update so we never depend on a stale `width` value
    setWidth((prev: number) => prev + delta)
  }, [setWidth])

  function moveAttachmentsToSavedMessage(
    loadedMessages: MessageResponse[] | void,
    optimisticMessageId: string,
    messageText: string,
    uploaded: AttachmentResponse[],
  ) {
    if (!loadedMessages || uploaded.length === 0) return

    const savedUserMessage = [...loadedMessages].reverse().find(msg =>
      msg.role_code === "user" && msg.content === messageText
    )
    if (!savedUserMessage || savedUserMessage.id === optimisticMessageId) return

    setMsgAttachments(prev => {
      const next = { ...prev }
      delete next[optimisticMessageId]
      next[savedUserMessage.id] = uploaded
      return next
    })
  }

  async function handleNewConversation() {
    setLoading(true)
    try {
      const conv = await createConversation({
        agent_type_code: "copilot",
        org_id: pageContext.org_id ?? undefined,
        workspace_id: pageContext.workspace_id ?? undefined,
        page_context: pageContext as unknown as Record<string, unknown>,
      })
      setConversations(prev => [conv, ...prev])
      setActiveConvIdPersisted(conv.id)
      setMessages([])
    } catch { /* ignore */ }
    finally { setLoading(false) }
  }

  async function handleSend(promptOverride?: string) {
    const rawText = (promptOverride ?? input).trim()
    // Allow sending with only attachments (no text) — use a default prompt
    const text = rawText || (attachments.length > 0 ? "I've attached a file. Please analyze it and summarize what it contains." : "")
    if (!text || isStreaming) return

    let convId = activeConvId
    if (!convId) {
      try {
        const conv = await createConversation({
          agent_type_code: "copilot",
          title: text.slice(0, 80),
          org_id: pageContext.org_id ?? undefined,
          workspace_id: pageContext.workspace_id ?? undefined,
          page_context: pageContext as unknown as Record<string, unknown>,
        })
        setConversations(prev => [conv, ...prev])
        setActiveConvIdPersisted(conv.id)
        convId = conv.id
      } catch { return }
    }

    setInput("")
    setIsStreaming(true)
    setStreamContent("")
    setStreamToolCalls([])
    setStreamError(null)

    // Upload any pending attachments to the conversation before streaming
    const pendingAttachments = attachments.slice()
    setAttachments([])
    const optimisticId = `opt_${Date.now()}`
    let uploadedAttachments: AttachmentResponse[] = []
    if (pendingAttachments.length > 0) {
      setUploadingFiles(true)
      const results = await Promise.allSettled(
        pendingAttachments.map(a => uploadAttachment(convId!, a.file))
      )
      const failedAttachments: AttachedFile[] = []
      const failedMessages: string[] = []

      results.forEach((result, index) => {
        const pendingAttachment = pendingAttachments[index]
        if (result.status === "rejected") {
          failedAttachments.push(pendingAttachment)
          failedMessages.push(
            `${pendingAttachment.name}: ${result.reason instanceof Error ? result.reason.message : "Upload failed"}`
          )
          return
        }

        if (result.value.ingest_status === "failed") {
          failedAttachments.push(pendingAttachment)
          failedMessages.push(
            `${pendingAttachment.name}: ${result.value.error_message || "Document ingest failed"}`
          )
          return
        }

        uploadedAttachments.push(result.value)
      })

      setUploadingFiles(false)
      // Keep failed attachments in the tray so they can be retried or removed.
      setAttachments(failedAttachments)
      // Revoke previews only for files that uploaded successfully.
      pendingAttachments
        .filter(a => !failedAttachments.some(f => f.id === a.id))
        .forEach(a => { if (a.previewUrl) URL.revokeObjectURL(a.previewUrl) })

      if (failedMessages.length > 0) {
        setStreamError(failedMessages.join(" "))
      }
      if (uploadedAttachments.length === 0 && failedMessages.length > 0) {
        setIsStreaming(false)
        if (rawText) setInput(rawText)
        return
      }
    }
    if (uploadedAttachments.length > 0) {
      setMsgAttachments(prev => ({ ...prev, [optimisticId]: uploadedAttachments }))
    }

    const optimistic: MessageResponse = {
      id: optimisticId,
      conversation_id: convId,
      role_code: "user",
      content: text,
      token_count: null, model_id: null,
      created_at: new Date().toISOString(),
    }
    setMessages(prev => [...prev, optimistic])

    try {
      const res = await streamMessage(convId, {
        content: text,
        page_context: pageContext as unknown as Record<string, unknown>,
      })
      if (!res.body) { setIsStreaming(false); return }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ""
      let accumulated = ""
      let gotMessageEnd = false

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const parts = buffer.split("\n\n")
        buffer = parts.pop() ?? ""

        for (const part of parts) {
          const lines = part.split("\n")
          const eventLine = lines.find(l => l.startsWith("event:"))
          const dataLine = lines.find(l => l.startsWith("data:"))
          if (!eventLine || !dataLine) continue
          const eventType = eventLine.replace("event:", "").trim()
          let eventData: Record<string, unknown> = {}
          try { eventData = JSON.parse(dataLine.replace("data:", "").trim()) } catch { continue }

          switch (eventType) {
            case "content_delta":
              accumulated += (eventData.delta as string) ?? (eventData.text as string) ?? ""
              setStreamContent(accumulated)
              break
            case "tool_call_start":
              setStreamToolCalls(prev => [...prev, {
                tool_name: eventData.tool_name as string,
                tool_category: (eventData.tool_category as ToolCallEvent["tool_category"]) ?? "navigation",
                input_summary: (eventData.input_summary as string) ?? "",
                status: "running",
              }])
              break
            case "tool_call_result":
              setStreamToolCalls(prev => prev.map(tc =>
                tc.tool_name === (eventData.tool_name as string)
                  ? { ...tc, status: eventData.is_successful ? "done" : "error", output_summary: eventData.output_summary as string }
                  : tc
              ))
              break
            case "session_named":
              setConversations(prev => prev.map(c =>
                c.id === (eventData.conversation_id as string) ? { ...c, title: eventData.title as string } : c
              ))
              break
            case "navigate": {
              // Build URL from structured data — never trust AI-generated URL strings
              const entityType = eventData.entity_type as string
              const entityId = eventData.entity_id as string
              const frameworkId = eventData.framework_id as string | undefined
              const label = (eventData.label as string) || entityType
              let path: string | null = null
              if (entityType === "framework" && entityId) {
                path = `/frameworks/${entityId}`
              } else if (entityType === "control" && entityId && frameworkId) {
                path = `/controls/${frameworkId}/${entityId}`
              } else if (entityType === "task" && entityId) {
                path = `/tasks/${entityId}`
              } else if (entityType === "risk" && entityId) {
                path = `/risks/${entityId}`
              }
              // Don't auto-navigate — show a clickable card in the chat instead
              if (path) {
                setPendingNavigation({ path, label, entityType })
              }
              break
            }
            case "navigate_page": {
              const page = eventData.page as string
              const label = (eventData.label as string) || page
              const path = PAGE_ROUTES[page]
              if (path) {
                setPendingPageNavigation({ path, label })
              }
              break
            }
            case "report_queued":
              setPendingReports(prev => [...prev, {
                report_id: eventData.report_id as string,
                report_type: eventData.report_type as string,
                title: eventData.title as string | null,
                status: eventData.status as string,
              }])
              break
            case "form_fill_proposed":
              setPendingFormFills(prev => [...prev, {
                fields: (eventData.fields as Record<string, unknown>) ?? {},
                explanation: (eventData.explanation as string) ?? "",
              }])
              break
            case "error":
              setStreamError((eventData.message as string) || "The agent encountered an error. Please try again.")
              setIsStreaming(false)
              break
            case "approval_created": {
              // Fetch the full approval record from the API — the SSE payload is a partial
              // shape that doesn't satisfy ApprovalResponse. Fetching ensures type safety
              // and gives us the authoritative server-side state.
              const approvalId = eventData.id as string
              if (approvalId) {
                getApproval(approvalId)
                  .then(full => setApprovalQueue(prev => [...prev, full]))
                  .catch(() => {/* non-fatal — approval missed, user can find it in approvals page */})
              }
              break
            }
            case "message_end":
              gotMessageEnd = true
              moveAttachmentsToSavedMessage(
                await loadMessages(convId!),
                optimisticId,
                text,
                uploadedAttachments,
              )
              setStreamContent("")
              setStreamToolCalls([])
              setIsStreaming(false)
              loadConversations()
              break
          }
        }
      }

      // Fallback: stream closed without message_end (mock SSE or error)
      if (!gotMessageEnd) {
        moveAttachmentsToSavedMessage(
          await loadMessages(convId!),
          optimisticId,
          text,
          uploadedAttachments,
        )
        setStreamContent("")
        setStreamToolCalls([])
        loadConversations()
      }
    } catch (err) {
      setStreamError("Connection lost. The response may have timed out — please try again.")
      moveAttachmentsToSavedMessage(
        await loadMessages(convId!),
        optimisticId,
        text,
        uploadedAttachments,
      )
      setStreamContent("")
      setStreamToolCalls([])
    }
    finally { setIsStreaming(false) }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  async function handleFileSelect(files: FileList | File[] | null) {
    if (!files) return
    const MAX_FILE_SIZE = 100 * 1024 * 1024 // 100 MB, matches backend storage cap
    const allFiles = Array.from(files)
    const fileArray = allFiles.filter(f => f.size <= MAX_FILE_SIZE)
    const skippedFiles = allFiles.filter(f => f.size > MAX_FILE_SIZE)

    if (skippedFiles.length > 0) {
      setStreamError(
        skippedFiles.map(f => `${f.name}: exceeds 100 MB upload limit`).join(" ")
      )
    } else {
      setStreamError(null)
    }

    if (fileArray.length === 0) return

    const newAttachments: AttachedFile[] = []

    for (const f of fileArray) {
      const id = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`
      const isPasted = !f.name || f.name === "image.png" || f.name === "file" || !f.type
      const finalName = isPasted ? (f.name && f.name.includes(".") ? f.name : `image-${id.slice(-4)}.png`) : f.name
      const finalType = f.type || (isPasted ? "image/png" : "application/octet-stream")
      const finalFile = f.type ? f : new globalThis.File([f], finalName, { type: finalType })

      let previewUrl: string | undefined
      if (finalType.startsWith("image/")) {
        // Use FileReader for more robust Base64 previews (works better with some clipboard sources)
        try {
          previewUrl = await new Promise<string>((resolve, reject) => {
            const reader = new FileReader()
            reader.onload = () => resolve(reader.result as string)
            reader.onerror = reject
            reader.readAsDataURL(finalFile)
          })
        } catch (err) {
          console.error("Preview failed", err)
          previewUrl = URL.createObjectURL(finalFile)
        }
      }

      newAttachments.push({
        id: `${id}-${finalName}`,
        name: finalName,
        size: f.size,
        type: finalType,
        file: finalFile,
        previewUrl,
      })
    }

    setAttachments(prev => [...prev, ...newAttachments].slice(0, 10))
  }

  const handlePaste = useCallback((e: React.ClipboardEvent) => {
    const clipboardData = e.clipboardData
    if (!clipboardData) return

    const files: File[] = []
    let hasImage = false
    for (let i = 0; i < clipboardData.items.length; i++) {
      const item = clipboardData.items[i]
      if (item.kind === "file") {
        const file = item.getAsFile()
        if (file) {
          files.push(file)
          if (file.type.startsWith("image/")) hasImage = true
        }
      }
    }

    if (files.length > 0) {
      if (hasImage) e.preventDefault()
      void handleFileSelect(files)
    }
  }, [handleFileSelect])

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setIsDragging(false)
    handleFileSelect(e.dataTransfer.files)
  }

  const handleApprove = useCallback(async (id: string) => {
    try {
      const result = await approveAction(id)
      setApprovalQueue(prev => prev.filter(a => a.id !== id))
      if (result.execution_result) {
        const res = result.execution_result as Record<string, unknown>
        const name = (res.name ?? res.title ?? res.code ?? "") as string
        setApprovalResult({ success: true, message: name ? `Done — ${name} created.` : "Action completed successfully." })
      } else {
        setApprovalResult({ success: true, message: "Action completed successfully." })
      }
    } catch (err) {
      setApprovalResult({ success: false, message: err instanceof Error ? err.message : "Action failed." })
    }
    setTimeout(() => setApprovalResult(null), 5000)
  }, [])

  const handleReject = useCallback(async (id: string, reason: string) => {
    try {
      await rejectApproval(id, reason)
      setApprovalQueue(prev => prev.filter(a => a.id !== id))
    } catch { /* ignore */ }
  }, [])

  if (!isOpen) return null

  return (
    <>
      {previewAttachment && (
        <AttachmentPreviewModal 
          file={previewAttachment} 
          onClose={() => setPreviewAttachment(null)} 
        />
      )}

      {approvalQueue.length > 0 && (
        <ApprovalModal
          approval={approvalQueue[0]}
          queueLength={approvalQueue.length}
          onApprove={handleApprove}
          onReject={handleReject}
        />
      )}

      <div
        className="relative flex h-full bg-background border-l border-border/60 flex-col shrink-0 overflow-hidden"
        style={{ width }}
        onDragOver={e => { e.preventDefault(); setIsDragging(true) }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
      >
        <ResizeHandle onResize={handleResize} />

        {/* Drag overlay */}
        {isDragging && (
          <div className="absolute inset-0 z-50 bg-violet-500/10 border-2 border-dashed border-violet-500/40 rounded-none flex items-center justify-center">
            <div className="text-center">
              <Paperclip className="w-8 h-8 text-violet-400 mx-auto mb-2" />
              <p className="text-sm font-medium text-violet-400">Drop files to attach</p>
            </div>
          </div>
        )}

        {/* History drawer overlay */}
        {showHistory && (
          <HistoryDrawer
            conversations={conversations}
            activeId={activeConvId}
            onSelect={id => { setActiveConvIdPersisted(id); setShowHistory(false) }}
            onNew={() => { handleNewConversation(); setShowHistory(false) }}
            onClose={() => setShowHistory(false)}
          />
        )}

        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border/50 shrink-0 bg-background/80 backdrop-blur-sm">
          <div className="flex items-center gap-2.5">
            <div>
              <div className="w-7 h-7 rounded-xl bg-gradient-to-br from-violet-500/25 to-purple-600/15 flex items-center justify-center ring-1 ring-violet-500/20">
                <Sparkles className="w-3.5 h-3.5 text-violet-400" />
              </div>
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-semibold text-foreground leading-none">AI Copilot</span>
              {/* Context pill */}
              <span className="text-[10px] text-violet-400/70 leading-none mt-0.5">
                {getContextLabel(pageContext)} context
              </span>
            </div>
          </div>
          <div className="flex items-center gap-1">
            {activeConvId && (
              <button
                onClick={() => setShowAttachmentsPanel(v => !v)}
                className={`p-1.5 rounded-lg transition-colors ${showAttachmentsPanel ? "bg-violet-500/15 text-violet-400" : "hover:bg-muted/60 text-muted-foreground hover:text-foreground"}`}
                title="Conversation attachments"
              >
                <Paperclip className="w-3.5 h-3.5" />
              </button>
            )}
            <button
              onClick={() => setShowHistory(v => !v)}
              className="p-1.5 rounded-lg hover:bg-muted/60 text-muted-foreground hover:text-foreground transition-colors"
              title="Conversation history"
            >
              <History className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => { setActiveConvIdPersisted(null); setMessages([]); setPendingNavigation(null); setPendingPageNavigation(null); setPendingReports([]); setPendingFormFills([]); setStreamError(null); setApprovalResult(null); setShowAttachmentsPanel(false) }}
              className="p-1.5 rounded-lg hover:bg-muted/60 text-muted-foreground hover:text-foreground transition-colors"
              title="New conversation"
            >
              <Plus className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={close}
              className="p-1.5 rounded-lg hover:bg-muted/60 text-muted-foreground hover:text-foreground transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Attachments panel */}
        {showAttachmentsPanel && activeConvId && (
          <div className="border-b border-border/50 bg-muted/10">
            <div className="px-4 pt-3 pb-1 flex items-center justify-between">
              <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Conversation Attachments</span>
              <button
                onClick={() => setShowAttachmentsPanel(false)}
                className="p-1 rounded text-muted-foreground/50 hover:text-foreground transition-colors"
              >
                <ChevronUp className="w-3 h-3" />
              </button>
            </div>
            <div className="px-3 pb-3">
              <ConversationAttachmentsPanel
                conversationId={activeConvId}
                onDeleted={() => {
                  loadConversations()
                  loadMessages(activeConvId)
                }}
                onSelect={setPreviewAttachment}
              />
            </div>
          </div>
        )}

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto min-h-0">
          {activeConvId === null ? (
            <EmptyState
              pageContext={pageContext}
              onPrompt={p => { setInput(p); textareaRef.current?.focus() }}
              onNew={handleNewConversation}
              loading={loading}
            />
          ) : loadingMsgs ? (
            <div className="flex-1 flex items-center justify-center h-full">
              <Loader2 className="w-5 h-5 animate-spin text-muted-foreground/40" />
            </div>
          ) : (
            <div className="px-4 py-4 space-y-5">
              {messages.map(msg => (
                <MessageBubble
                  key={msg.id}
                  msg={msg}
                  sentAttachments={msgAttachments[msg.id]}
                  onApprove={handleApprove}
                  onReject={handleReject}
                  onSelectAttachment={setPreviewAttachment}
                />
              ))}
              {isStreaming && (
                <StreamingBubble content={streamContent} toolCalls={streamToolCalls} />
              )}
              {!isStreaming && streamError && (
                <div className="flex gap-3">
                  <div className="w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5
                    bg-red-500/10">
                    <AlertCircle className="w-3.5 h-3.5 text-red-400" />
                  </div>
                  <div className="flex-1 min-w-0 py-1">
                    <p className="text-xs text-red-400">{streamError}</p>
                  </div>
                </div>
              )}
              {approvalResult && (
                <div className="flex gap-3">
                  <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${approvalResult.success ? "bg-emerald-500/10" : "bg-red-500/10"}`}>
                    {approvalResult.success
                      ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      : <AlertCircle className="w-3.5 h-3.5 text-red-400" />}
                  </div>
                  <div className="flex-1 min-w-0 py-1">
                    <p className={`text-xs ${approvalResult.success ? "text-emerald-400" : "text-red-400"}`}>{approvalResult.message}</p>
                  </div>
                </div>
              )}
              {pendingNavigation && (
                <div className="flex gap-3">
                  <div className="w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5
                    bg-gradient-to-br from-violet-500/30 to-purple-500/20">
                    <Sparkles className="w-3.5 h-3.5 text-violet-400" />
                  </div>
                  <div className="flex-1 min-w-0 py-0.5">
                    <NavigationCard
                      nav={pendingNavigation}
                      onNavigate={() => {
                        router.push(pendingNavigation.path)
                        setPendingNavigation(null)
                      }}
                    />
                  </div>
                </div>
              )}
              {pendingPageNavigation && (
                <div className="flex gap-3">
                  <div className="w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5
                    bg-gradient-to-br from-violet-500/30 to-purple-500/20">
                    <Sparkles className="w-3.5 h-3.5 text-violet-400" />
                  </div>
                  <div className="flex-1 min-w-0 py-0.5">
                    <PageNavigationCard
                      nav={pendingPageNavigation}
                      onNavigate={() => {
                        if (pendingPageNavigation.path.startsWith("/sandbox")) {
                          window.open(pendingPageNavigation.path, "_blank", "noopener,noreferrer")
                        } else {
                          router.push(pendingPageNavigation.path)
                        }
                        setPendingPageNavigation(null)
                      }}
                    />
                  </div>
                </div>
              )}
              {pendingReports.map(r => (
                <div key={r.report_id} className="flex gap-3">
                  <div className="w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5
                    bg-gradient-to-br from-purple-500/30 to-violet-500/20">
                    <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                  </div>
                  <div className="flex-1 min-w-0 py-0.5">
                    <ReportCard report={r} />
                  </div>
                </div>
              ))}
              {pendingFormFills.map((fill, i) => (
                <div key={i} className="flex gap-3">
                  <div className="w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5
                    bg-gradient-to-br from-sky-500/30 to-blue-500/20">
                    <Sparkles className="w-3.5 h-3.5 text-sky-400" />
                  </div>
                  <div className="flex-1 min-w-0 py-0.5">
                    <FormFillCard
                      fill={fill}
                      onDismiss={() => setPendingFormFills(prev => prev.filter((_, j) => j !== i))}
                    />
                  </div>
                </div>
              ))}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        {/* Input area */}
        <div className="shrink-0 border-t border-border/50 bg-background/80 backdrop-blur-sm">
          {/* Attachments row */}
          {attachments.length > 0 && (
            <div className="flex flex-wrap gap-2.5 px-3 pt-2.5">
              {attachments.map(f => (
                <div key={f.id} className="relative">
                  <AttachmentChip
                    file={f}
                    onSelect={() => setPreviewAttachment(f)}
                  />
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      if (f.previewUrl) URL.revokeObjectURL(f.previewUrl)
                      setAttachments(prev => prev.filter(a => a.id !== f.id))
                    }}
                    className="absolute -top-2 -left-2 w-6 h-6 rounded-full bg-muted/90 border border-border/60 text-muted-foreground hover:bg-red-500 hover:text-white flex items-center justify-center shadow-lg transition-all z-20 hover:scale-110"
                    title="Remove"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="p-3 space-y-2">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              onPaste={handlePaste}
              placeholder="Ask anything… (Enter to send, Shift+Enter for newline)"
              disabled={isStreaming}
              rows={1}
              className="w-full bg-transparent text-sm resize-none focus:outline-none disabled:opacity-50 placeholder:text-muted-foreground/50 text-foreground leading-relaxed"
              style={{ minHeight: "1.5rem", maxHeight: "7.5rem" }}
            />
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1">
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".pdf,.docx,.xlsx,.xls,.txt,.md,.csv,.json,.html,.png,.jpg,.jpeg,.gif,.webp,.svg"
                  className="hidden"
                  onChange={e => { handleFileSelect(e.target.files); e.target.value = '' }}
                />
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="p-1.5 rounded-lg text-muted-foreground/50 hover:text-muted-foreground hover:bg-muted/60 transition-colors"
                  title="Attach file"
                >
                  <Paperclip className="w-3.5 h-3.5" />
                </button>
                {uploadingFiles ? (
                  <span className="text-[10px] text-violet-400/70 flex items-center gap-1">
                    <Loader2 className="w-2.5 h-2.5 animate-spin" />
                    Uploading files…
                  </span>
                ) : (
                  <span className="text-[10px] text-muted-foreground/50">
                    {getContextLabel(pageContext)} context active
                  </span>
                )}
              </div>
              <button
                type="button"
                onClick={() => handleSend()}
                disabled={(!input.trim() && attachments.length === 0) || isStreaming}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-primary text-primary-foreground text-xs font-semibold disabled:opacity-30 hover:opacity-90 transition-opacity"
              >
                {isStreaming
                  ? <Loader2 className="w-3 h-3 animate-spin" />
                  : <Send className="w-3 h-3" />}
                {isStreaming ? "Thinking…" : "Send"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
