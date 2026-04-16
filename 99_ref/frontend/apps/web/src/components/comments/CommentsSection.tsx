"use client"

import { useEffect, useState, useCallback, useRef, useMemo } from "react"
import { Button } from "@kcontrol/ui"
import {
  RefreshCw,
  MessageSquare,
  MoreHorizontal,
  Pencil,
  Trash2,
  Pin,
  PinOff,
  CheckCircle,
  XCircle,
  History,
  Reply,
  ChevronDown,
  ChevronRight,
  X,
  Link,
  EyeOff,
  Eye,
  Search,
  ArrowUpDown,
  Lock,
  Bold,
  Italic,
  Code,
  List,
  Quote,
} from "lucide-react"
import {
  listComments,
  createComment,
  updateComment,
  deleteComment,
  pinComment,
  unpinComment,
  resolveComment,
  unresolveComment,
  getCommentHistory,
  addReaction,
  removeReaction,
} from "@/lib/api/comments"
import type { CommentRecord, CommentEditRecord } from "@/lib/types/comments"
import { AIEnhancePopover } from "@/components/ai/AIEnhancePopover"

// ─────────────────────────────────────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────────────────────────────────────

const REACTION_EMOJI_TO_CODE: Record<string, string> = {
  "👍": "thumbs_up",
  "👎": "thumbs_down",
  "❤️": "heart",
  "😂": "laugh",
  "🎉": "tada",
  "👀": "eyes",
  "🚀": "rocket",
  "😕": "confused",
}
const REACTION_CODE_TO_EMOJI: Record<string, string> = Object.fromEntries(
  Object.entries(REACTION_EMOJI_TO_CODE).map(([e, c]) => [c, e])
)
const REACTIONS = Object.keys(REACTION_EMOJI_TO_CODE)
const MAX_COMMENT_LENGTH = 50_000
const WARN_COMMENT_LENGTH = 45_000

// ─────────────────────────────────────────────────────────────────────────────
// @mention extraction — backend expects @[Display Name](user_uuid)
// ─────────────────────────────────────────────────────────────────────────────

function extractMentionIds(content: string): string[] {
  const mentionRegex = /@\[([^\]]+)\]\(([0-9a-f-]{36})\)/g
  const ids: string[] = []
  let match
  while ((match = mentionRegex.exec(content)) !== null) {
    if (!ids.includes(match[2])) ids.push(match[2])
  }
  return ids
}

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

function timeAgo(dateStr: string): string {
  try {
    const diff = Date.now() - new Date(dateStr).getTime()
    if (diff < 60_000) return "just now"
    if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`
    if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`
    if (diff < 7 * 86_400_000) return `${Math.floor(diff / 86_400_000)}d ago`
    return new Date(dateStr).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
  } catch {
    return dateStr
  }
}

function fullDateTime(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleString("en-US", {
      weekday: "short",
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

function authorInitials(comment: CommentRecord): string {
  const name = comment.author_display_name || comment.author_email || "?"
  return name.slice(0, 2).toUpperCase()
}

function authorLabel(comment: CommentRecord): string {
  return comment.author_display_name || comment.author_email || "Unknown"
}

function renderContent(content: string): React.ReactNode {
  // Highlight @mentions — supports both @[Display Name](uuid) and simple @handle
  const mentionRegex = /(@\[([^\]]+)\]\([0-9a-f-]{36}\)|@[\w\-]+)/g
  const parts: React.ReactNode[] = []
  let lastIndex = 0
  let match
  while ((match = mentionRegex.exec(content)) !== null) {
    if (match.index > lastIndex) {
      parts.push(<span key={`text-${lastIndex}`}>{content.slice(lastIndex, match.index)}</span>)
    }
    // Extract display name from @[Name](uuid), or use the simple @handle
    const displayName = match[2] ? `@${match[2]}` : match[0]
    parts.push(
      <span
        key={`mention-${match.index}`}
        className="inline-flex items-center rounded px-1 py-0.5 text-[11px] font-semibold bg-blue-500/15 text-blue-600 dark:text-blue-300 border border-blue-500/20"
      >
        {displayName}
      </span>
    )
    lastIndex = match.index + match[0].length
  }
  if (lastIndex < content.length) {
    parts.push(<span key={`text-${lastIndex}`}>{content.slice(lastIndex)}</span>)
  }
  return parts.length > 0 ? parts : content
}

function copyToClipboard(text: string): void {
  try {
    navigator.clipboard.writeText(text).catch(() => {
      const el = document.createElement("textarea")
      el.value = text
      el.style.position = "fixed"
      el.style.opacity = "0"
      document.body.appendChild(el)
      el.select()
      document.execCommand("copy")
      document.body.removeChild(el)
    })
  } catch {
    // ignore
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Character Counter
// ─────────────────────────────────────────────────────────────────────────────

function CharCounter({ length }: { length: number }) {
  if (length === 0) return null
  const isWarn = length > WARN_COMMENT_LENGTH
  const isOver = length > MAX_COMMENT_LENGTH
  return (
    <span
      className={`text-xs tabular-nums ${
        isOver ? "text-destructive font-semibold" : isWarn ? "text-amber-600" : "text-muted-foreground"
      }`}
      aria-live="polite"
    >
      {length.toLocaleString()} / {MAX_COMMENT_LENGTH.toLocaleString()}
    </span>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Avatar
// ─────────────────────────────────────────────────────────────────────────────

function CommentAvatar({ comment, size = "md" }: { comment: CommentRecord; size?: "sm" | "md" }) {
  const sz = size === "sm" ? "h-6 w-6 text-[10px]" : "h-8 w-8 text-xs"
  const isExternal = comment.author_is_external
  const colors = isExternal
    ? "bg-amber-500/15 border-amber-500/20 text-amber-600"
    : "bg-primary/15 border-primary/20 text-primary"
  return (
    <div className="relative shrink-0">
      <div
        className={`${sz} rounded-full ${colors} border flex items-center justify-center font-semibold`}
        aria-label={`Avatar for ${authorLabel(comment)}`}
      >
        {authorInitials(comment)}
      </div>
      {isExternal && (
        <span className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full bg-amber-500 border-2 border-background" title="External Auditor" />
      )}
    </div>
  )
}

function AuthorBadge({ comment }: { comment: CommentRecord }) {
  if (!comment.author_grc_role_code) return null
  const roleLabels: Record<string, string> = {
    grc_lead: "GRC Lead",
    grc_sme: "SME",
    grc_engineer: "Engineer",
    grc_ciso: "CISO",
    grc_lead_auditor: "Lead Auditor",
    grc_staff_auditor: "Staff Auditor",
    grc_vendor: "Vendor",
  }
  const label = roleLabels[comment.author_grc_role_code] || comment.author_grc_role_code
  const isExternal = comment.author_is_external
  return (
    <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-bold ${
      isExternal
        ? "bg-amber-500/10 text-amber-600 border border-amber-500/20"
        : "bg-primary/10 text-primary border border-primary/20"
    }`}>
      {label}
    </span>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Reaction Bar
// ─────────────────────────────────────────────────────────────────────────────

interface ReactionBarProps {
  comment: CommentRecord
  currentUserId: string
  onReacted: () => void
}

function ReactionBar({ comment, currentUserId, onReacted }: ReactionBarProps) {
  const [showPicker, setShowPicker] = useState(false)
  const [optimistic, setOptimistic] = useState<Map<string, boolean>>(new Map())
  const [reactionInFlight, setReactionInFlight] = useState(false)
  const pickerRef = useRef<HTMLDivElement>(null)

  // Close picker on outside click
  useEffect(() => {
    if (!showPicker) return
    const handler = (e: MouseEvent) => {
      if (pickerRef.current && !pickerRef.current.contains(e.target as Node)) {
        setShowPicker(false)
      }
    }
    document.addEventListener("mousedown", handler)
    return () => document.removeEventListener("mousedown", handler)
  }, [showPicker])

  const handleToggle = useCallback(async (emoji: string) => {
    if (reactionInFlight) return
    const code = REACTION_EMOJI_TO_CODE[emoji] ?? emoji
    const existing = comment.reactions.find((r) => r.reaction_code === code)
    const hasReacted = optimistic.has(emoji)
      ? optimistic.get(emoji)!
      : (existing?.reacted_by_me ?? false)

    // Optimistic update
    setOptimistic((prev) => {
      const next = new Map(prev)
      next.set(emoji, !hasReacted)
      return next
    })
    setShowPicker(false)
    setReactionInFlight(true)

    try {
      if (hasReacted) {
        await removeReaction(comment.id, code)
      } else {
        await addReaction(comment.id, code)
      }
      onReacted()
    } catch {
      // Revert
      setOptimistic((prev) => {
        const next = new Map(prev)
        next.delete(emoji)
        return next
      })
    } finally {
      setReactionInFlight(false)
    }
  }, [comment, optimistic, onReacted, reactionInFlight])

  // Merge API reactions with optimistic state
  // Server returns codes (thumbs_up), optimistic state uses emojis (👍) — normalize to emojis
  const merged = useMemo(() => {
    const m = new Map<string, { count: number; reacted: boolean }>()
    for (const r of comment.reactions) {
      const emoji = REACTION_CODE_TO_EMOJI[r.reaction_code] ?? r.reaction_code
      const reacted = optimistic.has(emoji) ? optimistic.get(emoji)! : r.reacted_by_me
      const countDelta = optimistic.has(emoji)
        ? (reacted !== r.reacted_by_me ? (reacted ? 1 : -1) : 0)
        : 0
      m.set(emoji, { count: Math.max(0, r.count + countDelta), reacted })
    }
    // Add emojis that were added optimistically but not yet in server data
    for (const [emoji, reacted] of optimistic.entries()) {
      if (!m.has(emoji) && reacted) {
        m.set(emoji, { count: 1, reacted: true })
      }
    }
    return m
  }, [comment.reactions, optimistic])

  return (
    <div className="flex items-center gap-1 flex-wrap relative">
      {Array.from(merged.entries())
        .filter(([, v]) => v.count > 0)
        .map(([emoji, { count, reacted }]) => {
          const reactionLabel = `React with ${emoji} (${count} reaction${count !== 1 ? "s" : ""})`
          return (
            <button
              key={emoji}
              onClick={() => handleToggle(emoji)}
              disabled={reactionInFlight}
              aria-label={reactionLabel}
              aria-pressed={reacted}
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs transition-colors disabled:opacity-50
                ${reacted
                  ? "bg-blue-500/15 border-blue-500/30 text-blue-700 dark:text-blue-300"
                  : "bg-muted border-border hover:bg-muted/80 text-foreground"
                }`}
            >
              {emoji} <span className="tabular-nums">{count}</span>
            </button>
          )
        })}

      <div className="relative" ref={pickerRef}>
        <button
          onClick={() => setShowPicker((v) => !v)}
          className="inline-flex items-center gap-0.5 px-2 py-0.5 rounded-full border border-dashed border-border text-xs text-muted-foreground hover:border-border hover:bg-muted transition-colors"
          aria-label="Add reaction"
          aria-expanded={showPicker}
          aria-haspopup="true"
        >
          + React
        </button>
        {showPicker && (
          <div
            className="absolute left-0 bottom-full mb-1 z-50 bg-popover border border-border rounded-lg shadow-lg p-2 flex flex-wrap gap-1 w-48"
            role="dialog"
            aria-label="Reaction picker"
          >
            {REACTIONS.map((emoji) => {
              const alreadyReacted = merged.get(emoji)?.reacted ?? false
              return (
                <button
                  key={emoji}
                  onClick={() => handleToggle(emoji)}
                  disabled={reactionInFlight}
                  aria-label={`React with ${emoji}`}
                  aria-pressed={alreadyReacted}
                  className={`text-base p-1 rounded hover:bg-muted transition-colors disabled:opacity-50 ${alreadyReacted ? "ring-1 ring-blue-500" : ""}`}
                >
                  {emoji}
                </button>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Edit History Dialog
// ─────────────────────────────────────────────────────────────────────────────

function HistoryDialog({ commentId, onClose }: { commentId: string; onClose: () => void }) {
  const [history, setHistory] = useState<CommentEditRecord[]>([])
  const [loading, setLoading] = useState(true)
  const closeButtonRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    closeButtonRef.current?.focus()
  }, [])

  useEffect(() => {
    setLoading(true)
    getCommentHistory(commentId)
      .then(setHistory)
      .catch(() => setHistory([]))
      .finally(() => setLoading(false))
  }, [commentId])

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose()
    }
    document.addEventListener("keydown", handler)
    return () => document.removeEventListener("keydown", handler)
  }, [onClose])

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/40 backdrop-blur-sm"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Edit history"
    >
      <div
        className="bg-background border border-border rounded-xl shadow-2xl max-w-lg w-full mx-4 max-h-[70vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <h3 className="font-semibold text-sm">Edit History</h3>
          <button
            ref={closeButtonRef}
            onClick={onClose}
            className="p-1 rounded hover:bg-muted transition-colors"
            aria-label="Close edit history"
          >
            <X className="h-4 w-4 text-muted-foreground" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
          {loading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground" aria-live="polite">
              <RefreshCw className="h-3.5 w-3.5 animate-spin" aria-hidden="true" /> Loading history...
            </div>
          ) : history.length === 0 ? (
            <p className="text-sm text-muted-foreground">No edit history available.</p>
          ) : (
            history.map((h) => (
              <div key={h.id} className="space-y-1">
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span className="font-mono">{h.edited_by.slice(0, 8)}…</span>
                  <span>•</span>
                  <span title={fullDateTime(h.edited_at)}>{timeAgo(h.edited_at)}</span>
                </div>
                <pre className="whitespace-pre-wrap font-sans text-sm bg-muted/50 rounded-lg px-3 py-2 border border-border">
                  {h.previous_content}
                </pre>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Comment Action Menu
// ─────────────────────────────────────────────────────────────────────────────

interface CommentMenuProps {
  comment: CommentRecord
  isAuthor: boolean
  isAdmin: boolean
  onEdit: () => void
  onDelete: () => void
  onPin: () => void
  onResolve: () => void
  onHistory: () => void
  onCopyLink: () => void
}

function CommentMenu({ comment, isAuthor, isAdmin, onEdit, onDelete, onPin, onResolve, onHistory, onCopyLink }: CommentMenuProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener("mousedown", handler)
    return () => document.removeEventListener("mousedown", handler)
  }, [open])

  // Close on Escape
  useEffect(() => {
    if (!open) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false)
    }
    document.addEventListener("keydown", handler)
    return () => document.removeEventListener("keydown", handler)
  }, [open])

  const items = [
    ...(isAuthor ? [{ label: "Edit", icon: <Pencil className="h-3.5 w-3.5" />, action: onEdit }] : []),
    ...(comment.is_edited ? [{ label: "View History", icon: <History className="h-3.5 w-3.5" />, action: onHistory }] : []),
    { label: "Copy link", icon: <Link className="h-3.5 w-3.5" />, action: onCopyLink },
    ...(isAdmin ? [
      {
        label: comment.pinned ? "Unpin" : "Pin",
        icon: comment.pinned ? <PinOff className="h-3.5 w-3.5" /> : <Pin className="h-3.5 w-3.5" />,
        action: onPin,
      },
      {
        label: comment.resolved ? "Unresolve" : "Resolve",
        icon: comment.resolved ? <XCircle className="h-3.5 w-3.5" /> : <CheckCircle className="h-3.5 w-3.5" />,
        action: onResolve,
      },
    ] : []),
    ...((isAuthor || isAdmin) ? [{ label: "Delete", icon: <Trash2 className="h-3.5 w-3.5" />, action: onDelete, danger: true }] : []),
  ]

  if (items.length === 0) return null

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((v) => !v)}
        className="p-1 rounded hover:bg-muted transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100"
        aria-label="More actions"
        aria-expanded={open}
        aria-haspopup="menu"
      >
        <MoreHorizontal className="h-4 w-4 text-muted-foreground" />
      </button>
      {open && (
        <div
          className="absolute right-0 top-full mt-1 z-50 bg-popover border border-border rounded-lg shadow-lg py-1 min-w-[160px]"
          role="menu"
          aria-label="Comment actions"
        >
          {items.map((item) => (
            <button
              key={item.label}
              role="menuitem"
              onClick={() => { item.action(); setOpen(false) }}
              className={`w-full flex items-center gap-2 px-3 py-1.5 text-sm hover:bg-muted transition-colors
                ${item.danger ? "text-destructive hover:text-destructive" : "text-foreground"}`}
            >
              {item.icon}
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Single Comment Item
// ─────────────────────────────────────────────────────────────────────────────

interface CommentItemProps {
  comment: CommentRecord
  currentUserId: string
  isWorkspaceAdmin: boolean
  depth: number
  onRefresh: () => void
  onReplyClick?: (commentId: string) => void
  showResolved: boolean
  parentAuthorName?: string
}

function CommentItem({
  comment,
  currentUserId,
  isWorkspaceAdmin,
  depth,
  onRefresh,
  onReplyClick,
  showResolved,
  parentAuthorName,
}: CommentItemProps) {
  const [editing, setEditing] = useState(false)
  const [editContent, setEditContent] = useState(comment.content)
  const [saving, setSaving] = useState(false)
  const [showHistory, setShowHistory] = useState(false)
  const [showReplies, setShowReplies] = useState(true)
  const [deleteConfirm, setDeleteConfirm] = useState(false)
  const [copyFeedback, setCopyFeedback] = useState(false)
  const editRef = useRef<HTMLTextAreaElement>(null)

  const isAuthor = comment.author_user_id === currentUserId

  // Focus textarea when entering edit mode
  useEffect(() => {
    if (editing) {
      editRef.current?.focus()
      const len = editContent.length
      editRef.current?.setSelectionRange(len, len)
    }
  }, [editing, editContent.length])

  const handleSaveEdit = useCallback(async () => {
    if (!editContent.trim() || editContent === comment.content || editContent.length > MAX_COMMENT_LENGTH) {
      setEditing(false)
      return
    }
    setSaving(true)
    try {
      await updateComment(comment.id, { content: editContent.trim() })
      setEditing(false)
      onRefresh()
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Failed to save edit")
    } finally {
      setSaving(false)
    }
  }, [editContent, comment.id, comment.content, onRefresh])

  const handleCancelEdit = useCallback(() => {
    setEditing(false)
    setEditContent(comment.content)
  }, [comment.content])

  const [actionError, setActionError] = useState<string | null>(null)

  const handleDelete = useCallback(async () => {
    setActionError(null)
    try {
      await deleteComment(comment.id)
      setDeleteConfirm(false)
      onRefresh()
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Failed to delete comment")
    }
  }, [comment.id, onRefresh])

  const handlePin = useCallback(async () => {
    setActionError(null)
    try {
      if (comment.pinned) await unpinComment(comment.id)
      else await pinComment(comment.id)
      onRefresh()
    } catch (e) {
      setActionError(e instanceof Error ? e.message : `Failed to ${comment.pinned ? "unpin" : "pin"} comment`)
    }
  }, [comment.id, comment.pinned, onRefresh])

  const handleResolve = useCallback(async () => {
    setActionError(null)
    try {
      if (comment.resolved) await unresolveComment(comment.id)
      else await resolveComment(comment.id)
      onRefresh()
    } catch (e) {
      setActionError(e instanceof Error ? e.message : `Failed to ${comment.resolved ? "unresolve" : "resolve"} comment`)
    }
  }, [comment.id, comment.resolved, onRefresh])

  const handleCopyLink = useCallback(() => {
    setActionError(null)
    try {
      const url = `${window.location.href.split("#")[0]}#comment-${comment.id}`
      copyToClipboard(url)
      setCopyFeedback(true)
      const timer = setTimeout(() => setCopyFeedback(false), 2000)
      return () => clearTimeout(timer)
    } catch (e) {
      setActionError("Failed to copy link")
    }
  }, [comment.id])

  // Skip resolved comments when toggle is off
  if (comment.resolved && !showResolved && !comment.pinned) return null

  if (comment.is_deleted) {
    return (
      <div className={`flex gap-3 ${depth > 0 ? "ml-6 border-l-2 border-muted-foreground/20 pl-4" : ""}`}>
        <div className="h-8 w-8 rounded-full bg-muted border border-border shrink-0" aria-hidden="true" />
        <p className="text-sm text-muted-foreground italic self-center">This comment was deleted.</p>
      </div>
    )
  }

  const editCharOver = editContent.length > MAX_COMMENT_LENGTH
  const editCharWarn = editContent.length > WARN_COMMENT_LENGTH

  return (
    <div
      id={`comment-${comment.id}`}
      className={`${depth > 0 ? "ml-6 border-l-2 border-muted-foreground/20 pl-4" : ""}`}
    >
      <div
        className={`group relative rounded-xl p-3 transition-colors
          ${comment.visibility === "internal" ? "bg-amber-50/50 dark:bg-amber-950/20 border-l-2 border-amber-400" : ""}
          ${comment.pinned ? "bg-amber-500/5 border border-amber-500/20" : ""}
          ${comment.resolved && !comment.pinned ? "bg-emerald-500/5 border border-emerald-500/20 opacity-75" : ""}
          ${!comment.pinned && !comment.resolved && comment.visibility !== "internal" ? "hover:bg-muted/30" : ""}
        `}
      >
        {/* Reply-to label */}
        {depth > 0 && parentAuthorName && (
          <div className="flex items-center gap-1 text-[11px] text-muted-foreground mb-1.5">
            <Reply className="h-3 w-3" aria-hidden="true" />
            <span>Reply to <span className="font-medium text-foreground/70">{parentAuthorName}</span></span>
          </div>
        )}

        {/* Header */}
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="flex items-center gap-2 min-w-0">
            <CommentAvatar comment={comment} size={depth > 0 ? "sm" : "md"} />
            <div className="min-w-0">
              <div className="flex items-center gap-1.5 flex-wrap">
                <span className="text-sm font-semibold text-foreground">{authorLabel(comment)}</span>
                <AuthorBadge comment={comment} />
                {comment.visibility === "internal" && (
                  <span className="inline-flex items-center gap-0.5 text-[10px] text-amber-700 dark:text-amber-400 bg-amber-500/10 rounded px-1 py-0.5 border border-amber-500/20">
                    <Lock className="h-2.5 w-2.5" aria-hidden="true" /> Internal
                  </span>
                )}
                {comment.pinned && (
                  <span className="inline-flex items-center gap-0.5 text-[10px] text-amber-600 bg-amber-500/10 rounded px-1 py-0.5 border border-amber-500/20">
                    <Pin className="h-2.5 w-2.5" aria-hidden="true" /> Pinned
                  </span>
                )}
                {comment.resolved && (
                  <span className="inline-flex items-center gap-0.5 text-[10px] text-emerald-600 bg-emerald-500/10 rounded px-1 py-0.5 border border-emerald-500/20">
                    <CheckCircle className="h-2.5 w-2.5" aria-hidden="true" /> Resolved
                  </span>
                )}
              </div>
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <span title={fullDateTime(comment.created_at)}>{timeAgo(comment.created_at)}</span>
                {comment.is_edited && <span className="italic">(edited)</span>}
                {copyFeedback && (
                  <span className="text-emerald-600 font-medium" aria-live="polite">Link copied!</span>
                )}
              </div>
            </div>
          </div>
          <CommentMenu
            comment={comment}
            isAuthor={isAuthor}
            isAdmin={isWorkspaceAdmin}
            onEdit={() => { setEditing(true); setEditContent(comment.content) }}
            onDelete={() => setDeleteConfirm(true)}
            onPin={handlePin}
            onResolve={handleResolve}
            onHistory={() => setShowHistory(true)}
            onCopyLink={handleCopyLink}
          />
        </div>

        {/* Content */}
        {editing ? (
          <div className="space-y-2">
            <div className="relative">
              <textarea
                ref={editRef}
                id={`edit-comment-${comment.id}`}
                className={`w-full rounded-lg border bg-background text-sm px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-ring min-h-[72px] ${
                  editCharOver ? "border-destructive focus:ring-destructive" : "border-border"
                }`}
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                aria-label="Edit comment"
                aria-describedby={`edit-counter-${comment.id}`}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleSaveEdit()
                  if (e.key === "Escape") handleCancelEdit()
                }}
              />
            </div>
            <div className="flex items-center justify-between gap-2">
              <span id={`edit-counter-${comment.id}`}>
                <CharCounter length={editContent.length} />
              </span>
              <div className="flex items-center gap-2">
                <AIEnhancePopover
                  entityType={comment.entity_type}
                  entityId={comment.entity_id}
                  fieldName="comment_body"
                  fieldLabel="Comment"
                  currentValue={editContent}
                  orgId={null}
                  workspaceId={null}
                  entityContext={{ entity_type: comment.entity_type, entity_id: comment.entity_id }}
                  onApply={(v) => setEditContent(v as string)}
                  popoverSide="left"
                  placeholder="e.g. Make it more concise, add context, improve clarity…"
                />
                <Button size="sm" variant="ghost" onClick={handleCancelEdit}>Cancel</Button>
                <Button
                  size="sm"
                  disabled={saving || !editContent.trim() || editCharOver}
                  onClick={handleSaveEdit}
                  aria-label="Save edit"
                >
                  {saving ? <RefreshCw className="h-3 w-3 animate-spin mr-1" aria-hidden="true" /> : null}
                  Save
                </Button>
              </div>
            </div>
          </div>
        ) : comment.rendered_html ? (
          <div
            className="prose prose-sm dark:prose-invert max-w-none text-foreground leading-relaxed"
            dangerouslySetInnerHTML={{ __html: comment.rendered_html }}
          />
        ) : (
          <pre className="whitespace-pre-wrap font-sans text-sm text-foreground leading-relaxed">
            {renderContent(comment.content)}
          </pre>
        )}

        {/* Delete confirm */}
        {deleteConfirm && (
          <div className="mt-2 flex items-center gap-2 text-sm" role="alert">
            <span className="text-muted-foreground">Delete this comment?</span>
            <button
              onClick={handleDelete}
              className="text-destructive font-medium hover:underline"
              aria-label="Confirm delete comment"
            >
              Delete
            </button>
            <button
              onClick={() => setDeleteConfirm(false)}
              className="text-muted-foreground hover:underline"
              aria-label="Cancel delete"
            >
              Cancel
            </button>
          </div>
        )}

        {/* Action error */}
        {actionError && (
          <div className="mt-2 flex items-center gap-2 text-xs text-destructive" role="alert" aria-live="polite">
            <span>{actionError}</span>
            <button onClick={() => setActionError(null)} className="underline hover:no-underline" aria-label="Dismiss error">Dismiss</button>
          </div>
        )}

        {/* Reaction bar + Reply */}
        {!editing && (
          <div className="mt-2 flex items-center justify-between gap-2 flex-wrap">
            <ReactionBar comment={comment} currentUserId={currentUserId} onReacted={onRefresh} />
            {depth === 0 && onReplyClick && (
              <button
                onClick={() => onReplyClick(comment.id)}
                className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
                aria-label={`Reply to ${authorLabel(comment)}`}
              >
                <Reply className="h-3.5 w-3.5" aria-hidden="true" />
                Reply
              </button>
            )}
          </div>
        )}
      </div>

      {/* Replies */}
      {depth === 0 && comment.replies && comment.replies.length > 0 && (
        <div className="mt-2 space-y-2">
          <button
            onClick={() => setShowReplies((v) => !v)}
            className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors mb-1 ml-6"
            aria-expanded={showReplies}
            aria-label={`${showReplies ? "Hide" : "Show"} ${comment.replies.length} ${comment.replies.length === 1 ? "reply" : "replies"}`}
          >
            {showReplies
              ? <ChevronDown className="h-3 w-3" aria-hidden="true" />
              : <ChevronRight className="h-3 w-3" aria-hidden="true" />}
            {comment.replies.length} {comment.replies.length === 1 ? "reply" : "replies"}
          </button>
          {showReplies && (
            <div className="space-y-2">
              {comment.replies.map((reply) => (
                <CommentItem
                  key={reply.id}
                  comment={reply}
                  currentUserId={currentUserId}
                  isWorkspaceAdmin={isWorkspaceAdmin}
                  depth={1}
                  onRefresh={onRefresh}
                  showResolved={showResolved}
                  parentAuthorName={authorLabel(comment)}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* History dialog */}
      {showHistory && <HistoryDialog commentId={comment.id} onClose={() => setShowHistory(false)} />}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Reply Composer
// ─────────────────────────────────────────────────────────────────────────────

interface ReplyComposerProps {
  parentId: string
  entityType: string
  entityId: string
  onCreated: () => void
  onCancel: () => void
}

function ReplyComposer({ parentId, entityType, entityId, onCreated, onCancel }: ReplyComposerProps) {
  const [content, setContent] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    textareaRef.current?.focus()
  }, [])

  const handleSubmit = useCallback(async () => {
    if (!content.trim() || content.length > MAX_COMMENT_LENGTH) return
    setSubmitting(true)
    setError(null)
    try {
      const mentionIds = extractMentionIds(content)
      await createComment({
        entity_type: entityType,
        entity_id: entityId,
        content: content.trim(),
        content_format: "markdown",
        parent_comment_id: parentId,
        ...(mentionIds.length > 0 ? { mention_user_ids: mentionIds } : {}),
      })
      setContent("")
      onCreated()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to post reply")
    } finally {
      setSubmitting(false)
    }
  }, [content, entityType, entityId, parentId, onCreated])

  const charOver = content.length > MAX_COMMENT_LENGTH

  return (
    <div className="ml-10 mt-2 space-y-2">
      <FormattingToolbar
        textareaRef={textareaRef}
        onContentChange={setContent}
        content={content}
      />
      <textarea
        ref={textareaRef}
        className={`w-full rounded-lg border bg-background text-sm px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-ring min-h-[60px] ${
          charOver ? "border-destructive" : "border-border"
        }`}
        placeholder="Write a reply... (Markdown supported)"
        value={content}
        onChange={(e) => setContent(e.target.value)}
        aria-label="Write a reply"
        aria-describedby="reply-char-counter"
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleSubmit()
          if (e.key === "Escape") onCancel()
        }}
      />
      <div className="flex items-center justify-between gap-2">
        <span id="reply-char-counter">
          <CharCounter length={content.length} />
        </span>
        <div className="flex items-center gap-2">
          <AIEnhancePopover
            entityType={entityType}
            entityId={entityId}
            fieldName="comment_body"
            fieldLabel="Reply"
            currentValue={content}
            orgId={null}
            workspaceId={null}
            entityContext={{ entity_type: entityType, entity_id: entityId }}
            onApply={(v) => setContent(v as string)}
            popoverSide="left"
            placeholder="e.g. Make it more concise, add context, improve clarity…"
          />
          <Button size="sm" variant="ghost" onClick={onCancel}>Cancel</Button>
          <Button size="sm" disabled={!content.trim() || submitting || charOver} onClick={handleSubmit}>
            {submitting ? <RefreshCw className="h-3 w-3 animate-spin mr-1" aria-hidden="true" /> : null}
            Reply
          </Button>
        </div>
      </div>
      {error && (
        <p className="text-xs text-destructive" role="alert" aria-live="polite">{error}</p>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Formatting Toolbar
// ─────────────────────────────────────────────────────────────────────────────

interface FormattingToolbarProps {
  textareaRef: React.RefObject<HTMLTextAreaElement | null>
  onContentChange: (newContent: string) => void
  content: string
}

function FormattingToolbar({ textareaRef, onContentChange, content }: FormattingToolbarProps) {
  const wrapSelection = useCallback((before: string, after: string) => {
    const textarea = textareaRef.current
    if (!textarea) return
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const selected = content.slice(start, end)
    const replacement = `${before}${selected || "text"}${after}`
    const newContent = content.slice(0, start) + replacement + content.slice(end)
    onContentChange(newContent)
    // Restore focus after state update
    requestAnimationFrame(() => {
      textarea.focus()
      const newStart = start + before.length
      const newEnd = newStart + (selected || "text").length
      textarea.setSelectionRange(newStart, newEnd)
    })
  }, [textareaRef, content, onContentChange])

  const prefixLines = useCallback((prefix: string) => {
    const textarea = textareaRef.current
    if (!textarea) return
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const selected = content.slice(start, end)
    const lines = selected.split("\n")
    const prefixed = lines.map((line) => `${prefix}${line}`).join("\n")
    const newContent = content.slice(0, start) + prefixed + content.slice(end)
    onContentChange(newContent)
    requestAnimationFrame(() => {
      textarea.focus()
    })
  }, [textareaRef, content, onContentChange])

  const tools = [
    { label: "Bold", icon: <Bold className="h-3.5 w-3.5" />, action: () => wrapSelection("**", "**") },
    { label: "Italic", icon: <Italic className="h-3.5 w-3.5" />, action: () => wrapSelection("*", "*") },
    { label: "Code", icon: <Code className="h-3.5 w-3.5" />, action: () => wrapSelection("`", "`") },
    { label: "Link", icon: <Link className="h-3.5 w-3.5" />, action: () => wrapSelection("[", "](url)") },
    { label: "List", icon: <List className="h-3.5 w-3.5" />, action: () => prefixLines("- ") },
    { label: "Quote", icon: <Quote className="h-3.5 w-3.5" />, action: () => prefixLines("> ") },
  ]

  return (
    <div className="flex items-center gap-0.5 border-b border-border pb-1.5 mb-1.5">
      {tools.map((tool) => (
        <button
          key={tool.label}
          type="button"
          onClick={tool.action}
          className="p-1 rounded hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
          aria-label={tool.label}
          title={tool.label}
        >
          {tool.icon}
        </button>
      ))}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Visibility Toggle
// ─────────────────────────────────────────────────────────────────────────────

interface VisibilityToggleProps {
  visibility: "internal" | "external"
  onChange: (v: "internal" | "external") => void
  isAdmin: boolean
}

function VisibilityToggle({ visibility, onChange, isAdmin }: VisibilityToggleProps) {
  if (!isAdmin) return null
  return (
    <button
      type="button"
      onClick={() => onChange(visibility === "external" ? "internal" : "external")}
      className={`inline-flex items-center gap-1 text-xs px-2 py-1 rounded border transition-colors ${
        visibility === "internal"
          ? "bg-amber-500/10 border-amber-500/30 text-amber-700 dark:text-amber-400"
          : "border-border text-muted-foreground hover:bg-muted"
      }`}
      aria-label={visibility === "internal" ? "Switch to external visibility" : "Switch to internal visibility"}
      title={visibility === "internal" ? "Internal: only visible to team members with manage permission" : "External: visible to all with entity access"}
    >
      {visibility === "internal" ? (
        <><Lock className="h-3 w-3" /> Internal</>
      ) : (
        <><Eye className="h-3 w-3" /> External</>
      )}
    </button>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Composer
// ─────────────────────────────────────────────────────────────────────────────

interface MainComposerProps {
  entityType: string
  entityId: string
  onCreated: () => void
  isWorkspaceAdmin?: boolean
}

function MainComposer({ entityType, entityId, onCreated, isWorkspaceAdmin = false }: MainComposerProps) {
  const [content, setContent] = useState("")
  const [focused, setFocused] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [visibility, setVisibility] = useState<"internal" | "external">("external")
  const composerTextareaRef = useRef<HTMLTextAreaElement>(null)

  const charOver = content.length > MAX_COMMENT_LENGTH

  const handleSubmit = useCallback(async () => {
    if (!content.trim() || charOver) return
    setSubmitting(true)
    setError(null)
    try {
      const mentionIds = extractMentionIds(content)
      await createComment({
        entity_type: entityType,
        entity_id: entityId,
        content: content.trim(),
        content_format: "markdown",
        visibility,
        ...(mentionIds.length > 0 ? { mention_user_ids: mentionIds } : {}),
      })
      setContent("")
      setFocused(false)
      setVisibility("external")
      onCreated()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to post comment")
    } finally {
      setSubmitting(false)
    }
  }, [content, entityType, entityId, onCreated, charOver, visibility])

  return (
    <div className="border-t border-border pt-4 space-y-2">
      {focused && (
        <FormattingToolbar
          textareaRef={composerTextareaRef}
          onContentChange={setContent}
          content={content}
        />
      )}
      <textarea
        ref={composerTextareaRef}
        id="main-comment-composer"
        className={`w-full rounded-lg border bg-background text-sm px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-ring transition-all ${
          charOver ? "border-destructive focus:ring-destructive" : "border-border"
        }`}
        style={{ minHeight: focused ? "96px" : "44px" }}
        placeholder="Write a comment... (Markdown supported, Ctrl+Enter to submit)"
        value={content}
        onChange={(e) => setContent(e.target.value)}
        onFocus={() => setFocused(true)}
        aria-label="Write a comment"
        aria-describedby="main-comment-counter main-comment-error"
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleSubmit()
          if (e.key === "Escape") { setFocused(false); setContent(""); setError(null) }
        }}
      />
      {error && (
        <p id="main-comment-error" className="text-xs text-destructive" role="alert" aria-live="polite">
          {error}
        </p>
      )}
      {(focused || content) && (
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span id="main-comment-counter">
              <CharCounter length={content.length} />
            </span>
            <VisibilityToggle
              visibility={visibility}
              onChange={setVisibility}
              isAdmin={isWorkspaceAdmin}
            />
          </div>
          <div className="flex items-center gap-2">
            <AIEnhancePopover
              entityType={entityType}
              entityId={entityId}
              fieldName="comment_body"
              fieldLabel="Comment"
              currentValue={content}
              orgId={null}
              workspaceId={null}
              entityContext={{ entity_type: entityType, entity_id: entityId }}
              onApply={(v) => setContent(v as string)}
              popoverSide="left"
              placeholder="e.g. Make it more concise, add context, improve clarity…"
            />
            <Button
              size="sm"
              variant="ghost"
              onClick={() => { setFocused(false); setContent(""); setError(null); setVisibility("external") }}
              aria-label="Cancel comment"
            >
              Cancel
            </Button>
            <Button
              size="sm"
              disabled={!content.trim() || submitting || charOver}
              onClick={handleSubmit}
              aria-label="Submit comment"
            >
              {submitting ? <RefreshCw className="h-3 w-3 animate-spin mr-1" aria-hidden="true" /> : null}
              Comment
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Loading Skeleton
// ─────────────────────────────────────────────────────────────────────────────

function CommentSkeleton() {
  return (
    <div className="flex gap-3 animate-pulse" aria-hidden="true">
      <div className="h-8 w-8 rounded-full bg-muted shrink-0" />
      <div className="flex-1 space-y-2">
        <div className="h-3 w-24 bg-muted rounded" />
        <div className="h-4 w-full bg-muted rounded" />
        <div className="h-4 w-3/4 bg-muted rounded" />
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// CommentsSection — Public Component
// ─────────────────────────────────────────────────────────────────────────────

interface CommentsSectionProps {
  entityType: string
  entityId: string
  currentUserId: string
  isWorkspaceAdmin?: boolean
  /** If true, do not auto-fetch on mount. Caller triggers the first load by passing active=true. */
  active?: boolean
  className?: string
  orgId?: string | null
  workspaceId?: string | null
}

export function CommentsSection({
  entityType,
  entityId,
  currentUserId,
  isWorkspaceAdmin = false,
  active = true,
  className = "",
  orgId: _orgId,
  workspaceId: _workspaceId,
}: CommentsSectionProps) {
  const [comments, setComments] = useState<CommentRecord[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [hasNext, setHasNext] = useState(false)
  const [loading, setLoading] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [replyingTo, setReplyingTo] = useState<string | null>(null)
  const [showResolved, setShowResolved] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [sortOrder, setSortOrder] = useState<"newest" | "oldest">("newest")
  const autoRefreshRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const hasLoadedRef = useRef(false)

  const load = useCallback(async (quiet = false) => {
    if (!quiet) setLoading(true)
    setError(null)
    try {
      const res = await listComments(entityType, entityId, 1, 25)
      setComments(res.items)
      setTotal(res.total)
      setHasNext(res.next_cursor !== null)
      setPage(1)
    } catch (e) {
      setError((e as Error).message || "Failed to load comments")
    } finally {
      setLoading(false)
    }
  }, [entityType, entityId])

  const loadMore = useCallback(async () => {
    setLoadingMore(true)
    try {
      const nextPage = page + 1
      const res = await listComments(entityType, entityId, nextPage, 25)
      setComments((prev) => [...prev, ...res.items])
      setHasNext(res.next_cursor !== null)
      setPage(nextPage)
    } catch {
      // ignore — load more is non-critical
    } finally {
      setLoadingMore(false)
    }
  }, [entityType, entityId, page])

  // Only load when active (lazy tab loading)
  useEffect(() => {
    if (!active) return
    if (!hasLoadedRef.current) {
      hasLoadedRef.current = true
      load()
    }
  }, [active, load])

  // Auto-refresh every 30 seconds and on window focus — only when active
  useEffect(() => {
    if (!active) return
    autoRefreshRef.current = setInterval(() => load(true), 30_000)
    const onFocus = () => load(true)
    window.addEventListener("focus", onFocus)
    return () => {
      if (autoRefreshRef.current) clearInterval(autoRefreshRef.current)
      window.removeEventListener("focus", onFocus)
    }
  }, [active, load])

  const pinnedComments = useMemo(
    () => comments.filter((c) => c.pinned && !c.is_deleted),
    [comments]
  )

  const filteredRegularComments = useMemo(() => {
    let result = comments.filter((c) => !c.pinned || c.is_deleted)
    // Client-side search filter
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      result = result.filter(
        (c) =>
          c.content.toLowerCase().includes(q) ||
          authorLabel(c).toLowerCase().includes(q)
      )
    }
    // Sort order
    if (sortOrder === "oldest") {
      result = [...result].sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
    } else {
      result = [...result].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    }
    return result
  }, [comments, searchQuery, sortOrder])

  const resolvedCount = useMemo(
    () => comments.filter((c) => c.resolved && !c.is_deleted).length,
    [comments]
  )

  const handleReplyClick = useCallback((id: string) => {
    setReplyingTo((prev) => prev === id ? null : id)
  }, [])

  const handleCreated = useCallback(() => {
    setReplyingTo(null)
    load(true)
  }, [load])

  return (
    <div className={`space-y-4 ${className}`} aria-label="Comments section">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <MessageSquare className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
          <span className="text-sm font-semibold text-foreground">
            {loading ? "Comments" : `Comments (${total})`}
          </span>
          {resolvedCount > 0 && !loading && (
            <span className="text-[11px] text-muted-foreground">
              • {resolvedCount} resolved
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          {resolvedCount > 0 && (
            <button
              onClick={() => setShowResolved((v) => !v)}
              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground px-2 py-1 rounded transition-colors hover:bg-muted"
              aria-pressed={showResolved}
              aria-label={showResolved ? "Hide resolved comments" : "Show resolved comments"}
            >
              {showResolved
                ? <><EyeOff className="h-3 w-3" aria-hidden="true" /> Hide resolved</>
                : <><Eye className="h-3 w-3" aria-hidden="true" /> Show resolved</>}
            </button>
          )}
          <button
            onClick={() => load(true)}
            className="p-1.5 rounded hover:bg-muted transition-colors"
            aria-label="Refresh comments"
          >
            <RefreshCw
              className={`h-3.5 w-3.5 text-muted-foreground ${loading ? "animate-spin" : ""}`}
              aria-hidden="true"
            />
          </button>
        </div>
      </div>

      {/* Search & sort bar */}
      {!loading && comments.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          <div className="relative flex-1 min-w-[140px]">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" aria-hidden="true" />
            <input
              type="text"
              className="w-full h-8 pl-8 pr-3 text-xs rounded-lg border border-border bg-background focus:outline-none focus:ring-1 focus:ring-ring"
              placeholder="Search comments..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              aria-label="Search comments"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-0.5 rounded hover:bg-muted"
                aria-label="Clear search"
              >
                <X className="h-3 w-3 text-muted-foreground" aria-hidden="true" />
              </button>
            )}
          </div>
          <button
            onClick={() => setSortOrder((v) => v === "newest" ? "oldest" : "newest")}
            className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground px-2 py-1.5 rounded border border-border hover:bg-muted transition-colors"
            aria-label={`Sort: ${sortOrder === "newest" ? "Newest first" : "Oldest first"}. Click to toggle.`}
          >
            <ArrowUpDown className="h-3 w-3" aria-hidden="true" />
            {sortOrder === "newest" ? "Newest first" : "Oldest first"}
          </button>
        </div>
      )}

      {/* Live region for loading state */}
      <div aria-live="polite" aria-atomic="true" className="sr-only">
        {loading ? "Loading comments..." : ""}
      </div>

      {/* Error */}
      {error && (
        <div
          className="flex items-center gap-2 rounded-lg border border-destructive/20 bg-destructive/10 px-3 py-2 text-sm text-destructive"
          role="alert"
          aria-live="assertive"
        >
          {error}
          <button
            onClick={() => load()}
            className="ml-auto text-xs underline hover:no-underline"
            aria-label="Retry loading comments"
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading */}
      {loading ? (
        <div className="space-y-4" aria-label="Loading comments">
          {[1, 2, 3].map((i) => <CommentSkeleton key={i} />)}
        </div>
      ) : (
        <>
          {/* Pinned comments */}
          {pinnedComments.length > 0 && (
            <div className="space-y-2" aria-label="Pinned comments">
              <div className="flex items-center gap-1.5 text-xs font-medium text-amber-600">
                <Pin className="h-3 w-3" aria-hidden="true" />
                Pinned
              </div>
              {pinnedComments.map((c) => (
                <div key={c.id}>
                  <CommentItem
                    comment={c}
                    currentUserId={currentUserId}
                    isWorkspaceAdmin={isWorkspaceAdmin}
                    depth={0}
                    onRefresh={() => load(true)}
                    onReplyClick={handleReplyClick}
                    showResolved={showResolved}
                  />
                  {replyingTo === c.id && (
                    <ReplyComposer
                      parentId={c.id}
                      entityType={entityType}
                      entityId={entityId}
                      onCreated={handleCreated}
                      onCancel={() => setReplyingTo(null)}
                    />
                  )}
                </div>
              ))}
              <div className="border-b border-border" />
            </div>
          )}

          {/* Regular comments */}
          {filteredRegularComments.length === 0 && pinnedComments.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 gap-2 text-center">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-muted" aria-hidden="true">
                <MessageSquare className="h-5 w-5 text-muted-foreground" />
              </div>
              <p className="text-sm font-medium text-foreground">No comments yet</p>
              <p className="text-xs text-muted-foreground">Be the first to comment.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredRegularComments.map((c) => (
                <div key={c.id}>
                  <CommentItem
                    comment={c}
                    currentUserId={currentUserId}
                    isWorkspaceAdmin={isWorkspaceAdmin}
                    depth={0}
                    onRefresh={() => load(true)}
                    onReplyClick={handleReplyClick}
                    showResolved={showResolved}
                  />
                  {replyingTo === c.id && (
                    <ReplyComposer
                      parentId={c.id}
                      entityType={entityType}
                      entityId={entityId}
                      onCreated={handleCreated}
                      onCancel={() => setReplyingTo(null)}
                    />
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Load more */}
          {hasNext && (
            <div className="pt-2 border-t border-border">
              <Button
                variant="ghost"
                size="sm"
                className="w-full text-xs"
                disabled={loadingMore}
                onClick={loadMore}
                aria-label="Load more comments"
              >
                {loadingMore
                  ? <RefreshCw className="h-3 w-3 animate-spin mr-1" aria-hidden="true" />
                  : null}
                Load more comments
              </Button>
            </div>
          )}
        </>
      )}

      {/* Composer */}
      <MainComposer entityType={entityType} entityId={entityId} onCreated={() => load(true)} isWorkspaceAdmin={isWorkspaceAdmin} />
    </div>
  )
}

export default CommentsSection
