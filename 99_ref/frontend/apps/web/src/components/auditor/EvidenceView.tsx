"use client"

import * as React from "react"
import {
  AlertTriangle,
  Download,
  FileIcon,
  HardDrive,
  Loader2,
  ShieldCheck,
} from "lucide-react"

import {
  Badge,
  Button,
  Card,
  CardContent,
} from "@kcontrol/ui"
import { toast } from "sonner"

import {
  getDownloadUrl,
  listEngagementAttachments,
} from "@/lib/api/attachments"
import type { AttachmentRecord } from "@/lib/types/attachments"
import { engagementsApi, type Engagement } from "@/lib/api/engagements"

interface EvidenceViewProps {
  orgId?: string
  workspaceId?: string
  engagementId?: string
  engagementName?: string
  engagementFrameworkId?: string
  engagements?: Engagement[]
}

interface EvidenceItem extends AttachmentRecord {
  source_engagement_id?: string
  source_engagement_name?: string
  linked_task_id?: string
  linked_task_title?: string
}

const ATTACHMENTS_PAGE_SIZE = 100
const ENGAGEMENT_CONCURRENCY = 3

function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 Bytes"
  const units = ["Bytes", "KB", "MB", "GB", "TB"]
  const index = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    units.length - 1,
  )
  return `${(bytes / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${units[index]}`
}

function formatEntityType(entityType: string): string {
  const labels: Record<string, string> = {
    control: "Controls",
    task: "Tasks",
    engagement: "Engagement",
    finding: "Findings",
    report: "Reports",
    risk: "Risks",
  }

  return labels[entityType] ?? entityType.replace(/_/g, " ").replace(/\b\w/g, (m) => m.toUpperCase())
}

function getVirusBadge(status: AttachmentRecord["virus_scan_status"]) {
  switch (status) {
    case "clean":
      return { label: "Clean", className: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" }
    case "pending":
      return { label: "Scanning", className: "bg-amber-500/10 text-amber-400 border-amber-500/20" }
    case "infected":
      return { label: "Infected", className: "bg-red-500/10 text-red-400 border-red-500/20" }
    case "error":
      return { label: "Scan Error", className: "bg-orange-500/10 text-orange-400 border-orange-500/20" }
    default:
      return { label: "Skipped", className: "bg-muted/40 text-muted-foreground border-border/60" }
  }
}

function formatTimestamp(value: string): string {
  return new Date(value).toLocaleString([], {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

async function listAllEngagementAttachments(engagementId: string): Promise<AttachmentRecord[]> {
  const allItems: AttachmentRecord[] = []
  let page = 1
  let total = 0

  do {
    const response = await listEngagementAttachments(engagementId, page, ATTACHMENTS_PAGE_SIZE)
    allItems.push(...(response.items ?? []))
    total = response.total ?? allItems.length
    page += 1
  } while (allItems.length < total)

  return allItems
}

async function mapWithConcurrency<T, R>(
  items: T[],
  limit: number,
  mapper: (item: T) => Promise<R>,
): Promise<R[]> {
  const results: R[] = []

  for (let index = 0; index < items.length; index += limit) {
    const batch = items.slice(index, index + limit)
    const batchResults = await Promise.all(batch.map(mapper))
    results.push(...batchResults)
  }

  return results
}

export function EvidenceView({
  orgId,
  workspaceId,
  engagementId,
  engagementName,
  engagementFrameworkId,
  engagements = [],
}: EvidenceViewProps) {
  const [attachments, setAttachments] = React.useState<EvidenceItem[]>([])
  const [total, setTotal] = React.useState(0)
  const [isLoading, setIsLoading] = React.useState(false)
  const [activeFilter, setActiveFilter] = React.useState("all")
  const [isPageVisible, setIsPageVisible] = React.useState(true)

  const engagementOptions = React.useMemo(() => {
    return engagements.filter((engagement) => !!engagement.id && !!engagement.framework_id)
  }, [engagements])

  const loadEvidence = React.useCallback(async () => {
    const scopedTargets = engagementId
      ? engagementOptions.filter(
          (engagement) =>
            engagement.id === engagementId &&
            engagement.framework_id === engagementFrameworkId,
        )
      : engagementOptions

    if (!orgId || scopedTargets.length === 0) {
      setAttachments([])
      setTotal(0)
      setIsLoading(false)
      return
    }

    setIsLoading(true)
    try {
      const results = await mapWithConcurrency(
        scopedTargets,
        ENGAGEMENT_CONCURRENCY,
        async (engagement) => {
          const tasksResult = await engagementsApi.listEngagementTasks(engagement.id)

          const taskTitleById = new Map(
            (tasksResult.items ?? []).map((task) => [task.id, task.title] as const),
          )
          const attachmentItems = await listAllEngagementAttachments(engagement.id)

          return {
            engagement,
            taskTitleById,
            attachmentItems,
          }
        },
      )

      const byId = new Map<string, EvidenceItem>()
      let combinedTotal = 0

      for (const result of results) {
        const taskAttachments = result.attachmentItems.filter(
          (item) => item.entity_type === "task",
        )

        combinedTotal += taskAttachments.length

        for (const item of taskAttachments) {
          if (byId.has(item.id)) continue
          byId.set(item.id, {
            ...item,
            source_engagement_id: result.engagement.id,
            source_engagement_name: result.engagement.engagement_name,
            linked_task_id: item.entity_id,
            linked_task_title: result.taskTitleById.get(item.entity_id),
          })
        }
      }

      const sorted = Array.from(byId.values()).sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
      )
      setAttachments(sorted)
      setTotal(engagementId ? combinedTotal : sorted.length)
    } catch (error) {
      console.error("Failed to load evidence:", error)
      toast.error((error as Error).message || "Failed to load evidence")
    } finally {
      setIsLoading(false)
    }
  }, [engagementFrameworkId, engagementId, engagementOptions, orgId, workspaceId])

  React.useEffect(() => {
    const handleVisibilityChange = () => {
      setIsPageVisible(document.visibilityState === "visible")
    }

    handleVisibilityChange()
    document.addEventListener("visibilitychange", handleVisibilityChange)

    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange)
    }
  }, [])

  React.useEffect(() => {
    loadEvidence()
  }, [loadEvidence])

  React.useEffect(() => {
    if (!orgId || !engagementId || !isPageVisible) return

    const interval = window.setInterval(() => {
      loadEvidence()
    }, 120000)

    return () => window.clearInterval(interval)
  }, [engagementId, isPageVisible, loadEvidence, orgId])

  React.useEffect(() => {
    if (activeFilter === "all") return
    if (attachments.some((attachment) => attachment.entity_type === activeFilter)) return
    setActiveFilter("all")
  }, [activeFilter, attachments])

  const filterOptions = React.useMemo(() => {
    return Array.from(new Set(attachments.map((attachment) => attachment.entity_type))).sort()
  }, [attachments])

  const filteredEvidence = React.useMemo(() => {
    return attachments.filter((attachment) => {
      const matchesFilter = activeFilter === "all" || attachment.entity_type === activeFilter
      if (!matchesFilter) return false
      return true
    })
  }, [activeFilter, attachments])

  const stats = React.useMemo(() => {
    const totalBytes = attachments.reduce((sum, attachment) => sum + attachment.file_size_bytes, 0)
    const auditorReady = attachments.filter((attachment) => attachment.auditor_access).length
    const pendingScan = attachments.filter((attachment) => attachment.virus_scan_status === "pending").length

    return {
      totalBytes,
      auditorReady,
      pendingScan,
    }
  }, [attachments])

  const handleDownload = React.useCallback(async (attachment: AttachmentRecord) => {
    try {
      const data = await getDownloadUrl(attachment.id)
      window.open(data.url, "_blank", "noopener,noreferrer")
    } catch (error) {
      toast.error((error as Error).message || "Failed to get download URL")
    }
  }, [])

  if (!orgId || engagementOptions.length === 0) {
    return (
      <div className="rounded-3xl border border-dashed border-border/60 bg-card/70 px-6 py-20 text-center">
        <ShieldCheck className="mx-auto mb-4 h-12 w-12 text-muted-foreground/30" />
        <h3 className="text-lg font-black uppercase tracking-tight text-foreground">
          No engagement frameworks available
        </h3>
        <p className="mx-auto mt-2 max-w-xl text-sm text-muted-foreground">
          This tab reads live task attachments from the frameworks attached to your loaded engagements.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="border-border/60 bg-card/85 shadow-sm">
          <CardContent className="p-4">
            <p className="text-[10px] font-black uppercase tracking-[0.25em] text-muted-foreground">Stored Evidence</p>
            <p className="mt-2 text-2xl font-black text-foreground">{total}</p>
            <p className="mt-1 text-xs text-muted-foreground">{formatFileSize(stats.totalBytes)} total footprint</p>
          </CardContent>
        </Card>
        <Card className="border-border/60 bg-card/85 shadow-sm">
          <CardContent className="p-4">
            <p className="text-[10px] font-black uppercase tracking-[0.25em] text-muted-foreground">Auditor Ready</p>
            <p className="mt-2 text-2xl font-black text-teal-600 dark:text-teal-400">{stats.auditorReady}</p>
            <p className="mt-1 text-xs text-muted-foreground">Published for auditor review</p>
          </CardContent>
        </Card>
        <Card className="border-border/60 bg-card/85 shadow-sm">
          <CardContent className="p-4">
            <p className="text-[10px] font-black uppercase tracking-[0.25em] text-muted-foreground">Scanning Queue</p>
            <p className="mt-2 text-2xl font-black text-amber-600 dark:text-amber-400">{stats.pendingScan}</p>
            <p className="mt-1 text-xs text-muted-foreground">Files still awaiting malware scan completion</p>
          </CardContent>
        </Card>
      </div>

      <div className="flex flex-wrap gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setActiveFilter("all")}
          className={`h-9 rounded-xl border-border/60 px-4 ${
            activeFilter === "all"
              ? "border-primary/30 bg-primary/15 text-primary"
              : "bg-card/70 text-muted-foreground hover:bg-muted hover:text-foreground"
          }`}
        >
          All Evidence
        </Button>
        {filterOptions.map((entityType) => (
          <Button
            key={entityType}
            variant="outline"
            size="sm"
            onClick={() => setActiveFilter(entityType)}
            className={`h-9 rounded-xl border-border/60 px-4 ${
              activeFilter === entityType
                ? "bg-indigo-500/10 text-indigo-300 border-indigo-500/20"
                : "bg-card/70 text-muted-foreground hover:bg-muted hover:text-foreground"
            }`}
          >
            {formatEntityType(entityType)}
          </Button>
        ))}
      </div>

      {isLoading && attachments.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-3xl border border-border/60 bg-card/70 py-20">
          <Loader2 className="mb-4 h-10 w-10 animate-spin text-teal-500" />
          <p className="text-sm font-medium text-muted-foreground">Loading live task evidence for this framework scope...</p>
        </div>
      ) : filteredEvidence.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-3xl border border-border/60 bg-card/70 py-20 text-center">
          <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-muted">
            <HardDrive className="h-8 w-8 text-muted-foreground/50" />
          </div>
          <h3 className="text-lg font-semibold text-foreground">No evidence found</h3>
          <p className="mt-1 max-w-sm text-sm text-muted-foreground">
            {`No task attachments have been uploaded for ${engagementName || "the current framework scope"} yet.`}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {filteredEvidence.map((attachment) => {
            const virusBadge = getVirusBadge(attachment.virus_scan_status)

            return (
              <Card
                key={attachment.id}
                className="group overflow-hidden rounded-3xl border border-border/60 bg-card/90 shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-md"
              >
                <CardContent className="p-0">
                  <div className="space-y-5 p-5">
                    <div className="flex items-start gap-4">
                      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-border/60 bg-gradient-to-br from-muted to-muted/40 text-muted-foreground transition-colors group-hover:text-primary">
                        <FileIcon className="h-6 w-6" />
                      </div>
                      <div className="min-w-0 flex-1 space-y-3">
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge variant="outline" className={`h-6 border px-2.5 text-[10px] font-semibold ${virusBadge.className}`}>
                            {virusBadge.label}
                          </Badge>
                          {attachment.auditor_access && (
                            <Badge variant="outline" className="h-6 border-teal-500/20 bg-teal-500/10 px-2.5 text-[10px] font-semibold text-teal-600 dark:text-teal-400">
                              Auditor Ready
                            </Badge>
                          )}
                          {!engagementId && attachment.source_engagement_name && (
                            <Badge variant="outline" className="h-6 border-indigo-500/20 bg-indigo-500/10 px-2.5 text-[10px] font-semibold text-indigo-700 dark:text-indigo-300">
                              {attachment.source_engagement_name}
                            </Badge>
                          )}
                        </div>

                        <div className="space-y-1.5">
                          <h3
                            className="truncate text-base font-semibold text-foreground transition-colors group-hover:text-primary"
                            title={attachment.original_filename}
                          >
                            {attachment.original_filename}
                          </h3>
                          <p className="line-clamp-2 text-sm text-muted-foreground">
                            {attachment.description || "No description provided for this evidence file."}
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="grid gap-3 rounded-2xl border border-border/60 bg-muted/20 p-3 sm:grid-cols-2">
                      <div className="space-y-1">
                        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">
                          Evidence Type
                        </p>
                        <p className="text-sm font-semibold text-foreground">
                          {formatEntityType(attachment.entity_type)}
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">
                          File Size
                        </p>
                        <p className="text-sm font-semibold text-foreground">
                          {formatFileSize(attachment.file_size_bytes)}
                        </p>
                      </div>
                      <div className="space-y-1 sm:col-span-2">
                        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">
                          Linked Task
                        </p>
                        <p className="line-clamp-2 text-sm font-medium text-foreground/85">
                          {attachment.linked_task_title || "Task title unavailable"}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between border-t border-border/60 bg-muted/20 px-5 py-3">
                    <div className="min-w-0">
                      <p className="text-[11px] text-muted-foreground">
                        {formatTimestamp(attachment.created_at)}
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      {attachment.virus_scan_status === "infected" && (
                        <AlertTriangle className="h-4 w-4 text-red-400" />
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDownload(attachment)}
                        disabled={attachment.virus_scan_status === "infected"}
                        className="h-9 rounded-xl px-3 text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-40"
                      >
                        <Download className="mr-1.5 h-4 w-4" />
                        Download
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
