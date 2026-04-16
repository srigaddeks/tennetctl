// ═══════════════════════════════════════════════════════════════════════════════
// Shared utilities for K-Control Sandbox pages
// ═══════════════════════════════════════════════════════════════════════════════

// ── Date formatting ──────────────────────────────────────────────────────────

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  })
}

export function formatDatetime(dateStr: string): string {
  return new Date(dateStr).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

export function timeAgo(dateStr: string): string {
  const seconds = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000)
  if (seconds < 60) return "just now"
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  return `${Math.floor(seconds / 86400)}d ago`
}

// ── Number / byte formatting ─────────────────────────────────────────────────

export function formatBytes(bytes: number | null): string {
  if (!bytes) return "--"
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
}

export function formatNumber(n: number | null): string {
  if (n === null || n === undefined) return "--"
  return n.toLocaleString()
}

// ── Slug generation ──────────────────────────────────────────────────────────

export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .substring(0, 100)
}

// ── Clipboard ────────────────────────────────────────────────────────────────

export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
      return true
    } else {
      // Fallback for older browsers
      const textArea = document.createElement("textarea")
      textArea.value = text
      textArea.style.position = "fixed"
      textArea.style.left = "-9999px"
      document.body.appendChild(textArea)
      textArea.select()
      const result = document.execCommand("copy")
      document.body.removeChild(textArea)
      return result
    }
  } catch (err) {
    console.error("Failed to copy:", err)
    return false
  }
}

// ── Status / severity style maps ─────────────────────────────────────────────

export const SIGNAL_STATUS_STYLES: Record<string, string> = {
  draft: "bg-zinc-500/10 text-zinc-500",
  testing: "bg-blue-500/10 text-blue-600 dark:text-blue-400",
  validated: "bg-green-500/10 text-green-600 dark:text-green-400",
  promoted: "bg-purple-500/10 text-purple-600 dark:text-purple-400",
  archived: "bg-zinc-500/10 text-zinc-400",
}

export const SEVERITY_STYLES: Record<string, string> = {
  info: "bg-blue-500/10 text-blue-600 dark:text-blue-400",
  low: "bg-green-500/10 text-green-600 dark:text-green-400",
  medium: "bg-yellow-500/10 text-yellow-600 dark:text-yellow-400",
  high: "bg-orange-500/10 text-orange-600 dark:text-orange-400",
  critical: "bg-red-500/10 text-red-600 dark:text-red-400",
}

export const RESULT_STYLES: Record<string, string> = {
  pass: "bg-green-500/10 text-green-600 dark:text-green-400",
  fail: "bg-red-500/10 text-red-600 dark:text-red-400",
  warning: "bg-yellow-500/10 text-yellow-600 dark:text-yellow-400",
  error: "bg-zinc-500/10 text-zinc-500",
}

export const SESSION_STATUS_STYLES: Record<string, string> = {
  starting: "bg-blue-500/10 text-blue-600 dark:text-blue-400",
  active: "bg-green-500/10 text-green-600 dark:text-green-400",
  paused: "bg-yellow-500/10 text-yellow-600 dark:text-yellow-400",
  completed: "bg-zinc-500/10 text-zinc-500",
  expired: "bg-orange-500/10 text-orange-500",
  error: "bg-red-500/10 text-red-600",
}

export const CONNECTOR_CATEGORY_ICONS: Record<string, string> = {
  cloud_infrastructure: "Cloud",
  identity_provider: "Shield",
  source_control: "GitBranch",
  project_management: "Kanban",
  database: "Database",
  container_orchestration: "Container",
  logging_monitoring: "Activity",
  itsm: "Headphones",
  communication: "MessageSquare",
  custom: "Puzzle",
}
