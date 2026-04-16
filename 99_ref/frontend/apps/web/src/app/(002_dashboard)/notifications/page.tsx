"use client"

import { useEffect, useState, useCallback } from "react"
import Link from "next/link"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Separator,
} from "@kcontrol/ui"
import {
  Bell,
  BellRing,
  BellOff,
  Mail,
  MailOpen,
  CheckCheck,
  RefreshCw,
  Filter,
  AlertTriangle,
  Info,
  ShieldAlert,
  Megaphone,
  Tag,
  ChevronLeft,
  ChevronRight,
  Circle,
  Settings,
  CheckSquare,
  Square,
  Globe,
  Monitor,
  MessageSquare,
  X,
  FileText,
  CheckCircle2,
  CircleCheck,
  Sparkles,
} from "lucide-react"
import {
  getInbox,
  markInboxRead,
  sendTestWebPush,
  type InboxNotificationItem,
  type InboxResponse,
} from "@/lib/api/notifications"
import { useWebPush } from "@/lib/hooks/useWebPush"

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const CATEGORY_LABELS: Record<string, string> = {
  security: "Security",
  transactional: "Transactional",
  system: "System",
  org: "Organization",
  workspace: "Workspace",
  engagement: "Engagement",
  marketing: "Marketing",
  product_updates: "Product Updates",
}

const CATEGORY_ICONS: Record<string, React.ElementType> = {
  security: ShieldAlert,
  transactional: Mail,
  system: Info,
  org: Tag,
  workspace: Tag,
  engagement: Megaphone,
  marketing: Megaphone,
  product_updates: Bell,
}

const PRIORITY_COLORS: Record<string, string> = {
  critical: "bg-red-100 text-red-700 border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800",
  high: "bg-orange-100 text-orange-700 border-orange-200 dark:bg-orange-900/30 dark:text-orange-400 dark:border-orange-800",
  normal: "bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-900/30 dark:text-blue-400 dark:border-blue-800",
  low: "bg-gray-100 text-gray-600 border-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:border-gray-700",
}

const CHANNEL_LABELS: Record<string, string> = {
  email: "Email",
  in_app: "In-App",
  sms: "SMS",
  web_push: "Web Push",
  webhook: "Webhook",
}

const CHANNEL_ICONS: Record<string, React.ElementType> = {
  email: Mail,
  in_app: Monitor,
  sms: MessageSquare,
  web_push: Globe,
  webhook: Globe,
}

const PAGE_SIZE = 20

// ---------------------------------------------------------------------------
// WebPushBanner — permission-aware strip shown at top of notifications page
// ---------------------------------------------------------------------------

function WebPushBanner() {
  const { state, loading, error, subscribe, unsubscribe } = useWebPush()
  const [testLoading, setTestLoading] = useState(false)
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null)

  if (state === "unsupported") return null

  async function handleTest() {
    setTestLoading(true)
    setTestResult(null)
    try {
      const res = await sendTestWebPush("/notifications")
      setTestResult({ success: true, message: res.message || "Test notification sent — check your browser!" })
    } catch (e) {
      setTestResult({ success: false, message: e instanceof Error ? e.message : "Failed to send test" })
    } finally {
      setTestLoading(false)
    }
  }

  // ── Prompt: ask for permission ──────────────────────────────────────────
  if (state === "prompt") {
    return (
      <div className="flex items-center gap-4 rounded-xl border border-primary/20 bg-primary/5 px-4 py-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10">
          <Bell className="h-4 w-4 text-primary" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-foreground">Enable desktop notifications</p>
          <p className="text-xs text-muted-foreground mt-0.5">
            Get instant browser alerts for security events and updates. Your browser will ask you to confirm.
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {["Real-time", "Deep links", "Secure"].map((f) => (
            <span key={f} className="hidden sm:flex items-center gap-1 text-[11px] text-muted-foreground/70">
              <CircleCheck className="h-3 w-3 text-primary/50" />{f}
            </span>
          ))}
          <Button size="sm" disabled={loading} onClick={subscribe} className="h-8 gap-1.5 ml-2">
            <BellRing className="h-3.5 w-3.5" />
            {loading ? "Requesting…" : "Allow notifications"}
          </Button>
        </div>
        {error && (
          <div className="flex items-center gap-1.5 text-xs text-red-500 shrink-0">
            <AlertTriangle className="h-3.5 w-3.5" />
            {error}
          </div>
        )}
      </div>
    )
  }

  // ── Denied: blocked by browser ─────────────────────────────────────────
  if (state === "denied") {
    return (
      <div className="flex items-start gap-4 rounded-xl border border-amber-500/20 bg-amber-500/5 px-4 py-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-amber-500/10">
          <ShieldAlert className="h-4 w-4 text-amber-500" />
        </div>
        <div className="flex-1">
          <p className="text-sm font-medium text-foreground">
            Notifications blocked
            <span className="ml-2 inline-flex items-center gap-1 rounded-full bg-amber-500/15 px-2 py-0.5 text-[10px] font-semibold text-amber-600 border border-amber-500/20">
              <BellOff className="h-2.5 w-2.5" /> Blocked
            </span>
          </p>
          <p className="text-xs text-muted-foreground mt-0.5">
            Click the lock icon in your address bar → Notifications → Allow, then refresh this page.
          </p>
        </div>
      </div>
    )
  }

  // ── Subscribed: active ─────────────────────────────────────────────────
  return (
    <div className="flex items-center gap-4 rounded-xl border border-emerald-500/20 bg-emerald-500/5 px-4 py-3">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-emerald-500/10">
        <BellRing className="h-4 w-4 text-emerald-500" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium text-foreground">Desktop notifications active</p>
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/15 px-2 py-0.5 text-[10px] font-semibold text-emerald-600 border border-emerald-500/20">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
            Live
          </span>
        </div>
        {testResult && (
          <div className={`mt-1.5 flex items-center gap-1.5 text-xs ${testResult.success ? "text-emerald-600" : "text-red-500"}`}>
            {testResult.success
              ? <CheckCircle2 className="h-3 w-3 shrink-0" />
              : <AlertTriangle className="h-3 w-3 shrink-0" />
            }
            {testResult.message}
          </div>
        )}
        {error && <p className="mt-1 text-xs text-red-500">{error}</p>}
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <Button size="sm" variant="outline" disabled={testLoading} onClick={handleTest} className="h-8 gap-1.5 text-xs">
          <Sparkles className="h-3.5 w-3.5" />
          {testLoading ? "Sending…" : "Send test"}
        </Button>
        <Button size="sm" variant="ghost" disabled={loading} onClick={unsubscribe} className="h-8 gap-1.5 text-xs text-muted-foreground hover:text-red-500 hover:bg-red-500/10">
          <BellOff className="h-3.5 w-3.5" />
          {loading ? "…" : "Disable"}
        </Button>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// FilterPill
// ---------------------------------------------------------------------------
function FilterPill({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: React.ReactNode
}) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
        active
          ? "bg-primary text-primary-foreground border-primary"
          : "bg-muted text-muted-foreground border-transparent hover:bg-muted/80"
      }`}
    >
      {children}
    </button>
  )
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function NotificationsPage() {
  const [data, setData] = useState<InboxResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filterRead, setFilterRead] = useState<boolean | undefined>(undefined)
  const [filterCategory, setFilterCategory] = useState<string | undefined>(undefined)
  const [filterChannel, setFilterChannel] = useState<string | undefined>(undefined)
  const [page, setPage] = useState(0)
  const [markingRead, setMarkingRead] = useState(false)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [detailItem, setDetailItem] = useState<InboxNotificationItem | null>(null)

  // Category counts from current full (unfiltered by category) load
  const [categoryCounts, setCategoryCounts] = useState<Record<string, number>>({})
  const [channelCounts, setChannelCounts] = useState<Record<string, number>>({})

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await getInbox({
        is_read: filterRead,
        category_code: filterCategory,
        channel_code: filterChannel,
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
      })
      setData(res)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load notifications")
    } finally {
      setLoading(false)
    }
  }, [filterRead, filterCategory, filterChannel, page])

  // Load unfiltered counts for filter pill badges (once, and after mark-read)
  const loadCounts = useCallback(async () => {
    try {
      const all = await getInbox({ limit: 200 })
      const catCounts: Record<string, number> = {}
      const chCounts: Record<string, number> = {}
      for (const item of all.items) {
        if (item.category_code) catCounts[item.category_code] = (catCounts[item.category_code] ?? 0) + 1
        chCounts[item.channel_code] = (chCounts[item.channel_code] ?? 0) + 1
      }
      setCategoryCounts(catCounts)
      setChannelCounts(chCounts)
    } catch { /* non-fatal */ }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    loadCounts()
  }, [loadCounts])

  async function openDetail(item: InboxNotificationItem) {
    setDetailItem(item)
    if (!item.is_read) {
      await markInboxRead([item.id])
      await load()
      await loadCounts()
    }
  }

  async function handleMarkRead(ids: string[]) {
    setMarkingRead(true)
    try {
      await markInboxRead(ids)
      await load()
      await loadCounts()
      setSelectedIds(new Set())
    } catch {
      // ignore
    } finally {
      setMarkingRead(false)
    }
  }

  function toggleSelect(id: string) {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function toggleSelectAll() {
    const allIds = data?.items.map((i) => i.id) ?? []
    if (selectedIds.size === allIds.length && allIds.length > 0) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(allIds))
    }
  }

  const unreadItems = data?.items.filter((i) => !i.is_read) ?? []
  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0
  const allSelected = (data?.items.length ?? 0) > 0 && selectedIds.size === (data?.items.length ?? 0)

  // Channels that actually have items
  const activeChannels = Object.entries(channelCounts).filter(([, c]) => c > 0).map(([k]) => k)

  return (
    <div className="flex flex-col gap-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Bell className="h-6 w-6" />
          <div>
            <h1 className="text-2xl font-bold">Notifications</h1>
            <p className="text-sm text-muted-foreground">
              Your received notifications across all channels
            </p>
          </div>
          {data && data.unread_count > 0 && (
            <Badge variant="destructive" className="ml-2">
              {data.unread_count} unread
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          {selectedIds.size > 0 && (
            <Button
              variant="outline"
              size="sm"
              disabled={markingRead}
              onClick={() => handleMarkRead(Array.from(selectedIds))}
            >
              <MailOpen className="h-4 w-4 mr-1" />
              Mark {selectedIds.size} as read
            </Button>
          )}
          {unreadItems.length > 0 && selectedIds.size === 0 && (
            <Button
              variant="outline"
              size="sm"
              disabled={markingRead}
              onClick={() => handleMarkRead([])}
            >
              <CheckCheck className="h-4 w-4 mr-1" />
              Mark all as read
            </Button>
          )}
          <Button variant="ghost" size="sm" onClick={load} disabled={loading} title="Refresh">
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </Button>
          <Button variant="ghost" size="sm" asChild title="Notification preferences">
            <Link href="/settings/notifications">
              <Settings className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>

      {/* Web Push Banner */}
      <WebPushBanner />

      {/* Filters */}
      <Card>
        <CardContent className="pt-4 pb-3">
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-3 flex-wrap">
              <Filter className="h-4 w-4 text-muted-foreground shrink-0" />
              {/* Read/unread filter */}
              <div className="flex gap-1">
                <FilterPill active={filterRead === undefined} onClick={() => { setFilterRead(undefined); setPage(0) }}>All</FilterPill>
                <FilterPill active={filterRead === false} onClick={() => { setFilterRead(false); setPage(0) }}>
                  Unread{data && data.unread_count > 0 ? ` (${data.unread_count})` : ""}
                </FilterPill>
                <FilterPill active={filterRead === true} onClick={() => { setFilterRead(true); setPage(0) }}>Read</FilterPill>
              </div>
              {activeChannels.length > 1 && (
                <>
                  <Separator orientation="vertical" className="h-5" />
                  <div className="flex gap-1 flex-wrap">
                    <FilterPill active={!filterChannel} onClick={() => { setFilterChannel(undefined); setPage(0) }}>
                      All channels
                    </FilterPill>
                    {activeChannels.map((ch) => {
                      const Icon = CHANNEL_ICONS[ch] ?? Mail
                      return (
                        <FilterPill key={ch} active={filterChannel === ch} onClick={() => { setFilterChannel(ch); setPage(0) }}>
                          <span className="flex items-center gap-1">
                            <Icon className="h-3 w-3" />
                            {CHANNEL_LABELS[ch] ?? ch} ({channelCounts[ch]})
                          </span>
                        </FilterPill>
                      )
                    })}
                  </div>
                </>
              )}
            </div>
            {/* Category filter row */}
            <div className="flex items-center gap-1 flex-wrap pl-7">
              <FilterPill active={!filterCategory} onClick={() => { setFilterCategory(undefined); setPage(0) }}>
                All categories
              </FilterPill>
              {Object.entries(CATEGORY_LABELS).map(([code, label]) => {
                const count = categoryCounts[code] ?? 0
                if (count === 0) return null
                return (
                  <FilterPill key={code} active={filterCategory === code} onClick={() => { setFilterCategory(code); setPage(0) }}>
                    {label} ({count})
                  </FilterPill>
                )
              })}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 text-destructive text-sm p-3 rounded-lg border border-destructive/30 bg-destructive/5">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {/* Notification list */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {loading ? "Loading…" : `${data?.total ?? 0} notification${data?.total !== 1 ? "s" : ""}`}
            </CardTitle>
            {/* Select all */}
            {(data?.items.length ?? 0) > 0 && (
              <button
                onClick={toggleSelectAll}
                className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
              >
                {allSelected
                  ? <CheckSquare className="h-3.5 w-3.5 text-primary" />
                  : <Square className="h-3.5 w-3.5" />
                }
                {allSelected ? "Deselect all" : "Select all"}
              </button>
            )}
          </div>
        </CardHeader>
        <CardContent className="pt-0 space-y-1">
          {!loading && (!data?.items || data.items.length === 0) && (
            <div className="text-center py-12 text-muted-foreground">
              <Bell className="h-10 w-10 mx-auto mb-3 opacity-30" />
              <p className="text-sm font-medium">No notifications found</p>
              <p className="text-xs mt-1 opacity-70">
                {filterRead !== undefined || filterCategory || filterChannel
                  ? "Try clearing your filters"
                  : "You're all caught up!"}
              </p>
            </div>
          )}
          {data?.items.map((item) => (
            <NotificationRow
              key={item.id}
              item={item}
              selected={selectedIds.has(item.id)}
              onToggleSelect={() => toggleSelect(item.id)}
              onMarkRead={() => handleMarkRead([item.id])}
              onOpen={() => openDetail(item)}
            />
          ))}
        </CardContent>
      </Card>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-3">
          <Button
            variant="outline"
            size="sm"
            disabled={page === 0}
            onClick={() => setPage((p) => p - 1)}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="text-sm text-muted-foreground">
            Page {page + 1} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= totalPages - 1}
            onClick={() => setPage((p) => p + 1)}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* Detail panel */}
      {detailItem && (
        <NotificationDetailPanel
          item={detailItem}
          onClose={() => setDetailItem(null)}
        />
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Notification detail panel (full email viewer)
// ---------------------------------------------------------------------------

function NotificationDetailPanel({
  item,
  onClose,
}: {
  item: InboxNotificationItem
  onClose: () => void
}) {
  const CategoryIcon = (item.category_code && CATEGORY_ICONS[item.category_code]) || Bell
  const htmlBody = item.rendered_body_html || (item.rendered_body?.trim().startsWith("<") ? item.rendered_body : null)
  const textBody = item.rendered_body_html ? null : item.rendered_body

  return (
    <div className="fixed inset-0 z-50 flex">
      {/* Backdrop */}
      <div className="flex-1 bg-black/40 backdrop-blur-sm" onClick={onClose} />

      {/* Panel */}
      <div className="w-full max-w-2xl bg-background border-l border-border flex flex-col shadow-2xl animate-in slide-in-from-right duration-200">
        {/* Header */}
        <div className="flex items-start justify-between gap-3 px-5 py-4 border-b border-border shrink-0">
          <div className="flex items-start gap-3 min-w-0">
            <div className="shrink-0 rounded-full p-2 bg-muted mt-0.5">
              <CategoryIcon className="h-4 w-4 text-muted-foreground" />
            </div>
            <div className="min-w-0">
              <h2 className="text-sm font-semibold text-foreground leading-snug">
                {item.rendered_subject || item.notification_type_code.replace(/_/g, " ")}
              </h2>
              <div className="flex flex-wrap items-center gap-1.5 mt-1.5">
                {item.category_code && (
                  <Badge variant="outline" className="text-[10px] px-1.5 py-0">
                    {CATEGORY_LABELS[item.category_code] ?? item.category_code}
                  </Badge>
                )}
                <Badge variant="outline" className="text-[10px] px-1.5 py-0">
                  {CHANNEL_LABELS[item.channel_code] ?? item.channel_code}
                </Badge>
                <span className="text-[10px] text-muted-foreground">
                  {formatDate(item.created_at)}
                  {item.completed_at && <> · delivered {formatDate(item.completed_at)}</>}
                </span>
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="shrink-0 p-1.5 rounded-md hover:bg-muted transition-colors"
          >
            <X className="h-4 w-4 text-muted-foreground" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-auto">
          {htmlBody ? (
            <iframe
              srcDoc={htmlBody}
              sandbox="allow-same-origin"
              className="w-full h-full min-h-[500px] border-0 bg-white"
              title="Notification email"
            />
          ) : textBody ? (
            <pre className="p-5 text-sm text-foreground whitespace-pre-wrap font-sans leading-relaxed">
              {textBody}
            </pre>
          ) : (
            <div className="flex flex-col items-center justify-center h-full gap-3 text-muted-foreground p-8">
              <FileText className="h-8 w-8 opacity-40" />
              <p className="text-sm">No content stored for this notification.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Notification row
// ---------------------------------------------------------------------------

function NotificationRow({
  item,
  selected,
  onToggleSelect,
  onMarkRead,
  onOpen,
}: {
  item: InboxNotificationItem
  selected: boolean
  onToggleSelect: () => void
  onMarkRead: () => void
  onOpen: () => void
}) {
  const [expanded, setExpanded] = useState(false)
  const CategoryIcon = (item.category_code && CATEGORY_ICONS[item.category_code]) || Bell
  const priorityClass = PRIORITY_COLORS[item.priority_code] ?? PRIORITY_COLORS.normal
  const bodyText = item.rendered_body ? item.rendered_body.replace(/<[^>]+>/g, " ").trim() : null
  const isLongBody = bodyText && bodyText.length > 150

  return (
    <div
      className={`flex items-start gap-3 p-3 rounded-lg border transition-colors group
        ${!item.is_read ? "bg-primary/5 border-primary/20 hover:bg-primary/8" : "bg-transparent border-transparent hover:bg-muted/50"}
        ${selected ? "ring-2 ring-primary ring-offset-1" : ""}
      `}
    >
      {/* Select checkbox */}
      <button
        className="mt-1 shrink-0"
        onClick={(e) => { e.stopPropagation(); onToggleSelect() }}
        title={selected ? "Deselect" : "Select"}
      >
        {selected
          ? <CheckSquare className="h-3.5 w-3.5 text-primary" />
          : <Square className="h-3.5 w-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
        }
      </button>

      {/* Unread indicator */}
      <div className="mt-1.5 shrink-0">
        {!item.is_read ? (
          <Circle className="h-2 w-2 fill-primary text-primary" />
        ) : (
          <Circle className="h-2 w-2 text-transparent" />
        )}
      </div>

      {/* Category icon */}
      <div className={`shrink-0 rounded-full p-1.5 mt-0.5 ${!item.is_read ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"}`}>
        <CategoryIcon className="h-3.5 w-3.5" />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 cursor-pointer" onClick={onOpen}>
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`font-medium text-sm ${!item.is_read ? "" : "text-muted-foreground"}`}>
            {item.rendered_subject || item.notification_type_code.replace(/_/g, " ")}
          </span>
          {item.priority_code !== "normal" && (
            <Badge variant="outline" className={`text-[10px] px-1.5 py-0 ${priorityClass}`}>
              {item.priority_code}
            </Badge>
          )}
          {item.category_code && (
            <Badge variant="outline" className="text-[10px] px-1.5 py-0 bg-muted/50">
              {CATEGORY_LABELS[item.category_code] ?? item.category_code}
            </Badge>
          )}
          <Badge variant="outline" className="text-[10px] px-1.5 py-0 bg-muted/50">
            {CHANNEL_LABELS[item.channel_code] ?? item.channel_code}
          </Badge>
        </div>
        {bodyText && (
          <div>
            <p
              className={`text-xs text-muted-foreground mt-1 ${expanded ? "" : "line-clamp-2"}`}
            >
              {bodyText}
            </p>
            {isLongBody && (
              <button
                className="text-[10px] text-primary mt-0.5 hover:underline"
                onClick={(e) => { e.stopPropagation(); setExpanded((v) => !v) }}
              >
                {expanded ? "Show less" : "Show more"}
              </button>
            )}
          </div>
        )}
        <p className="text-[10px] text-muted-foreground mt-1">
          {formatDate(item.created_at)}
          {item.completed_at && <> · delivered {formatDate(item.completed_at)}</>}
          {item.is_read && item.read_at && <> · read {formatDate(item.read_at)}</>}
        </p>
      </div>

      {/* Mark read action */}
      {!item.is_read && (
        <button
          className="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded hover:bg-muted"
          title="Mark as read"
          onClick={(e) => { e.stopPropagation(); onMarkRead() }}
        >
          <MailOpen className="h-3.5 w-3.5 text-muted-foreground" />
        </button>
      )}
    </div>
  )
}

function formatDate(iso: string): string {
  try {
    const d = new Date(iso)
    const now = new Date()
    const diffMs = now.getTime() - d.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    if (diffMins < 1) return "just now"
    if (diffMins < 60) return `${diffMins}m ago`
    const diffHours = Math.floor(diffMins / 60)
    if (diffHours < 24) return `${diffHours}h ago`
    const diffDays = Math.floor(diffHours / 24)
    if (diffDays < 7) return `${diffDays}d ago`
    return d.toLocaleDateString()
  } catch {
    return iso
  }
}
