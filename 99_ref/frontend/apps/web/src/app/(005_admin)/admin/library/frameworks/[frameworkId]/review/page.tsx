"use client"

import { useEffect, useState, useCallback, use, useMemo } from "react"
import { useRouter } from "next/navigation"
import {
  Button,
  Badge,
  Separator,
} from "@kcontrol/ui"
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  Clock,
  FileText,
  AlertCircle,
  RefreshCw,
  User,
  Calendar,
  Layers,
  GitBranch,
  ShieldCheck,
  ChevronDown,
  ChevronRight,
  PlusCircle,
  MinusCircle,
} from "lucide-react"
import {
  listFrameworks,
  getFrameworkDiff,
  approveFramework,
  rejectFramework,
  getReviewSelection,
  getReviewDiff,
  listRequirements,
  listControls,
  ReviewDiff,
} from "@/lib/api/grc"
import type { FrameworkResponse, FrameworkDiff, ReviewSelectionResponse, RequirementResponse, ControlResponse } from "@/lib/types/grc"
import { FrameworkDiffViewer } from "@/components/grc/FrameworkDiffViewer"

// ── Helpers ───────────────────────────────────────────────────────────────────

function approvalStatusBadge(status: string) {
  switch (status) {
    case "draft":
      return (
        <Badge variant="outline" className="text-xs font-medium bg-muted text-muted-foreground border-border">
          <FileText className="h-3.5 w-3.5 mr-1.5" />
          Draft
        </Badge>
      )
    case "pending_review":
      return (
        <Badge variant="outline" className="text-xs font-medium bg-amber-500/10 text-amber-600 border-amber-500/20">
          <Clock className="h-3.5 w-3.5 mr-1.5" />
          Pending Review
        </Badge>
      )
    case "approved":
      return (
        <Badge variant="outline" className="text-xs font-medium bg-green-500/10 text-green-600 border-green-500/20">
          <CheckCircle2 className="h-3.5 w-3.5 mr-1.5" />
          Approved
        </Badge>
      )
    case "rejected":
      return (
        <Badge variant="outline" className="text-xs font-medium bg-red-500/10 text-red-600 border-red-500/20">
          <XCircle className="h-3.5 w-3.5 mr-1.5" />
          Rejected
        </Badge>
      )
    default:
      return (
        <Badge variant="outline" className="text-xs text-muted-foreground">
          {status}
        </Badge>
      )
  }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

// ── Loading Skeleton ──────────────────────────────────────────────────────────

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="h-8 w-8 rounded-md bg-muted animate-pulse" />
        <div className="h-7 w-64 rounded-md bg-muted animate-pulse" />
        <div className="h-6 w-24 rounded-full bg-muted animate-pulse" />
      </div>
      <div className="h-24 rounded-xl bg-muted animate-pulse" />
      <div className="h-96 rounded-xl bg-muted animate-pulse" />
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function FrameworkReviewPage({
  params,
}: {
  params: Promise<{ frameworkId: string }>
}) {
  const router = useRouter()
  const { frameworkId } = use(params)

  const [framework, setFramework] = useState<FrameworkResponse | null>(null)
  const [diff, setDiff] = useState<FrameworkDiff | null>(null)
  const [reviewSelection, setReviewSelection] = useState<ReviewSelectionResponse | null>(null)
  const [reviewDiff, setReviewDiff] = useState<ReviewDiff | null>(null)
  const [requirements, setRequirements] = useState<RequirementResponse[]>([])
  const [controls, setControls] = useState<ControlResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Reject state
  const [showRejectForm, setShowRejectForm] = useState(false)
  const [rejectReason, setRejectReason] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  // Expanded state for hierarchy
  const [expandedReqs, setExpandedReqs] = useState<Set<string>>(() => new Set())

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [fwRes, diffRes, reviewRes, reviewDiffRes, reqRes, ctrlRes] = await Promise.allSettled([
        listFrameworks(),
        getFrameworkDiff(frameworkId),
        getReviewSelection(frameworkId),
        getReviewDiff(frameworkId),
        listRequirements(frameworkId),
        listControls(frameworkId),
      ])

      if (fwRes.status === "fulfilled") {
        const fw = fwRes.value.items.find((f) => f.id === frameworkId)
        setFramework(fw ?? null)
        if (!fw) setError("Framework not found")
      } else {
        setError("Failed to load framework details")
      }

      if (diffRes.status === "fulfilled") {
        setDiff(diffRes.value)
      }

      if (reviewRes.status === "fulfilled") {
        setReviewSelection(reviewRes.value)
      }

      if (reviewDiffRes.status === "fulfilled") {
        setReviewDiff(reviewDiffRes.value)
      }

      if (reqRes.status === "fulfilled") {
        setRequirements(reqRes.value.items ?? [])
      }

      if (ctrlRes.status === "fulfilled") {
        setControls(ctrlRes.value.items ?? [])
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load")
    } finally {
      setLoading(false)
    }
  }, [frameworkId])

  useEffect(() => { load() }, [load])

  const toggleReqExpanded = (reqId: string) => {
    setExpandedReqs((prev) => {
      const next = new Set(prev)
      if (next.has(reqId)) next.delete(reqId)
      else next.add(reqId)
      return next
    })
  }

  // Build hierarchy for submitted items
  const submittedRequirements = reviewSelection?.requirement_ids
    .map((reqId) => requirements.find((r) => r.id === reqId))
    .filter(Boolean) as RequirementResponse[]

  const submittedControls = reviewSelection?.control_ids
    .map((ctrlId) => controls.find((c) => c.id === ctrlId))
    .filter(Boolean) as ControlResponse[]

  const unassignedSubmittedControls = submittedControls?.filter(
    (c) => !c.requirement_id || !submittedRequirements?.find((r) => r.id === c.requirement_id)
  ) ?? []

  // Build list of controls to publish - ONLY use explicitly submitted control IDs
  const controlsToPublish = useMemo(() => {
    if (!reviewSelection) return []
    
    // Only use explicitly submitted control IDs, NOT controls from requirements
    if (reviewSelection.control_ids && reviewSelection.control_ids.length > 0) {
      return reviewSelection.control_ids
    }
    
    // If no explicit controls but has requirements, return empty (admin should reject)
    return []
  }, [reviewSelection])

  const handleApprove = async () => {
    if (!framework) return
    console.log("DEBUG: Approve clicked, controlsToPublish =", controlsToPublish)
    console.log("DEBUG: reviewSelection =", reviewSelection)
    if (!confirm(`Approve and publish "${framework.name}" to the marketplace?`)) return
    setSubmitting(true)
    setActionError(null)
    try {
      console.log("DEBUG: Calling approveFramework with", controlsToPublish)
      await approveFramework(frameworkId, controlsToPublish)
      router.push("/admin/library/frameworks")
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Failed to approve")
      setSubmitting(false)
    }
  }

  const handleReject = async () => {
    if (!framework) return
    setSubmitting(true)
    setActionError(null)
    try {
      await rejectFramework(frameworkId, rejectReason.trim() || undefined)
      router.push("/admin/library/frameworks")
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Failed to reject")
      setSubmitting(false)
    }
  }

  if (loading) return <LoadingSkeleton />

  if (error || !framework) {
    return (
      <div className="space-y-4">
        <Button variant="ghost" size="sm" onClick={() => router.back()} className="gap-1.5">
          <ArrowLeft className="h-3.5 w-3.5" />
          Back
        </Button>
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 flex items-center gap-3">
          <AlertCircle className="h-4 w-4 text-destructive shrink-0" />
          <p className="text-sm text-destructive">{error ?? "Framework not found"}</p>
        </div>
      </div>
    )
  }

  const canReview = framework.approval_status === "pending_review" || (framework.approval_status === "approved" && framework.has_pending_changes)

  return (
    <div className="space-y-6 pb-32">
      {/* Top bar */}
      <div className="flex items-center gap-3 flex-wrap">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push("/admin/library/frameworks")}
          className="gap-1.5 shrink-0"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back
        </Button>
        <Separator orientation="vertical" className="h-5" />
        <div className="flex items-center gap-2 flex-wrap flex-1">
          <h1 className="text-xl font-bold tracking-tight font-secondary">{framework.name}</h1>
          {approvalStatusBadge(framework.approval_status)}
        </div>
      </div>

      {/* Framework metadata */}
      <div className="rounded-xl border border-border bg-muted/20 px-5 py-4 space-y-3">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-0.5">
              Framework Code
            </p>
            <p className="font-mono text-xs">{framework.framework_code}</p>
          </div>
          <div>
            <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-0.5">
              Category
            </p>
            <p className="text-xs">{framework.category_name || framework.framework_category_code}</p>
          </div>
          <div className="flex items-start gap-1.5">
            <Layers className="h-3.5 w-3.5 text-muted-foreground mt-0.5 shrink-0" />
            <div>
              <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-0.5">
                Controls
              </p>
              <p className="text-xs">{framework.control_count ?? 0}</p>
            </div>
          </div>
          <div className="flex items-start gap-1.5">
            <GitBranch className="h-3.5 w-3.5 text-muted-foreground mt-0.5 shrink-0" />
            <div>
              <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-0.5">
                Version
              </p>
              <p className="text-xs">{framework.latest_version_code ?? "—"}</p>
            </div>
          </div>
        </div>

        <Separator />

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="flex items-start gap-1.5">
            <User className="h-3.5 w-3.5 text-muted-foreground mt-0.5 shrink-0" />
            <div>
              <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-0.5">
                Publisher
              </p>
              <p className="text-xs">{framework.publisher_name ?? "—"}</p>
            </div>
          </div>
          <div className="flex items-start gap-1.5">
            <Calendar className="h-3.5 w-3.5 text-muted-foreground mt-0.5 shrink-0" />
            <div>
              <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-0.5">
                Submitted
              </p>
              <p className="text-xs">{formatDate(framework.updated_at)}</p>
            </div>
          </div>
        </div>

        {framework.description && (
          <>
            <Separator />
            <p className="text-sm text-muted-foreground">{framework.description}</p>
          </>
        )}
      </div>

      {/* Submitted items section - Hierarchy View */}
      {reviewSelection && (reviewSelection.requirement_ids.length > 0 || reviewSelection.control_ids.length > 0) && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 px-5 py-4 space-y-4">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-amber-500" />
            <h2 className="text-sm font-semibold">Submitted for Review</h2>
            {reviewSelection.notes && (
              <span className="text-xs text-muted-foreground">- {reviewSelection.notes}</span>
            )}
          </div>

          <div className="space-y-2">
            {/* Submitted Requirements with Controls */}
            {submittedRequirements?.map((req) => {
              const reqControls = submittedControls?.filter((c) => c.requirement_id === req.id) ?? []
              const isExpanded = expandedReqs.has(req.id)

              return (
                <div key={req.id} className="border rounded-lg overflow-hidden">
                  <div
                    className="flex items-center gap-2 px-3 py-2.5 bg-amber-500/10 hover:bg-amber-500/20 cursor-pointer"
                    onClick={() => toggleReqExpanded(req.id)}
                  >
                    {isExpanded ? (
                      <ChevronDown className="h-4 w-4 text-amber-500" />
                    ) : (
                      <ChevronRight className="h-4 w-4 text-amber-500" />
                    )}
                    <FileText className="h-4 w-4 text-amber-500" />
                    <span className="font-mono text-xs font-medium">{req.requirement_code}</span>
                    <span className="text-sm truncate flex-1">{req.name}</span>
                    <span className="text-[10px] text-muted-foreground bg-background px-1.5 py-0.5 rounded">
                      {reqControls.length} controls
                    </span>
                  </div>

                  {isExpanded && reqControls.length > 0 && (
                    <div className="bg-background divide-y">
                      {reqControls.map((ctrl) => (
                        <div key={ctrl.id} className="flex items-center gap-3 px-4 py-2">
                          <ShieldCheck className="h-4 w-4 text-muted-foreground shrink-0" />
                          <span className="font-mono text-xs">{ctrl.control_code}</span>
                          <span className="text-sm truncate flex-1">{ctrl.name}</span>
                          {ctrl.criticality_code && (
                            <span
                              className={`text-[10px] px-1.5 py-0.5 rounded border ${
                                ctrl.criticality_code === "critical"
                                  ? "border-red-500 text-red-500"
                                  : ctrl.criticality_code === "high"
                                  ? "border-orange-500 text-orange-500"
                                  : "border-muted-foreground text-muted-foreground"
                              }`}
                            >
                              {ctrl.criticality_code}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}

            {/* Unassigned Controls */}
            {unassignedSubmittedControls.length > 0 && (
              <div className="space-y-2">
                <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                  Unassigned Controls ({unassignedSubmittedControls.length})
                </p>
                <div className="border rounded-lg overflow-hidden">
                  {unassignedSubmittedControls.map((ctrl) => (
                    <div key={ctrl.id} className="flex items-center gap-3 px-3 py-2 bg-blue-500/5">
                      <ShieldCheck className="h-4 w-4 text-blue-500 shrink-0" />
                      <span className="font-mono text-xs">{ctrl.control_code}</span>
                      <span className="text-sm truncate flex-1">{ctrl.name}</span>
                      {ctrl.criticality_code && (
                        <span
                          className={`text-[10px] px-1.5 py-0.5 rounded border ${
                            ctrl.criticality_code === "critical"
                              ? "border-red-500 text-red-500"
                              : ctrl.criticality_code === "high"
                              ? "border-orange-500 text-orange-500"
                              : "border-muted-foreground text-muted-foreground"
                          }`}
                        >
                          {ctrl.criticality_code}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Review Diff - Changes from previous version */}
      {reviewDiff && reviewDiff.has_previous_version && (
        <div className="rounded-xl border border-blue-500/30 bg-blue-500/5 px-5 py-4 space-y-4">
          <div className="flex items-center gap-2">
            <GitBranch className="h-4 w-4 text-blue-500" />
            <h2 className="text-sm font-semibold">Changes from Previous Version</h2>
            <span className="text-xs text-muted-foreground">({reviewDiff.previous_version_code})</span>
          </div>

          <div className="flex items-center gap-3 text-xs">
            {reviewDiff.added_count > 0 && (
              <span className="flex items-center gap-1 px-2 py-1 rounded-full bg-green-500/15 text-green-600 border border-green-500/20">
                <PlusCircle className="h-3 w-3" />
                {reviewDiff.added_count} added
              </span>
            )}
            {reviewDiff.removed_count > 0 && (
              <span className="flex items-center gap-1 px-2 py-1 rounded-full bg-red-500/15 text-red-600 border border-red-500/20">
                <MinusCircle className="h-3 w-3" />
                {reviewDiff.removed_count} removed
              </span>
            )}
            {reviewDiff.added_count === 0 && reviewDiff.removed_count === 0 && (
              <span className="text-muted-foreground">No control changes</span>
            )}
          </div>

          {reviewDiff.added.length > 0 && (
            <div className="space-y-2">
              <p className="text-[11px] font-semibold text-green-600 uppercase tracking-wider">Added Controls</p>
              <div className="space-y-1">
                {reviewDiff.added.map((c) => (
                  <div key={c.id} className="flex items-center gap-2 px-3 py-2 rounded-md bg-green-500/10 border border-green-500/20">
                    <PlusCircle className="h-3 w-3 text-green-500 shrink-0" />
                    <span className="font-mono text-xs text-green-700 shrink-0">{c.control_code}</span>
                    {c.name && <span className="text-xs text-muted-foreground truncate">{c.name}</span>}
                    {c.criticality_code && (
                      <span className={`text-[10px] px-1.5 py-0.5 rounded border ml-auto ${
                        c.criticality_code === "critical" ? "border-red-500 text-red-500" :
                        c.criticality_code === "high" ? "border-orange-500 text-orange-500" : "border-muted-foreground text-muted-foreground"
                      }`}>{c.criticality_code}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {reviewDiff.removed.length > 0 && (
            <div className="space-y-2">
              <p className="text-[11px] font-semibold text-red-600 uppercase tracking-wider">Removed Controls</p>
              <div className="space-y-1">
                {reviewDiff.removed.map((c) => (
                  <div key={c.id} className="flex items-center gap-2 px-3 py-2 rounded-md bg-red-500/10 border border-red-500/20">
                    <MinusCircle className="h-3 w-3 text-red-500 shrink-0" />
                    <span className="font-mono text-xs text-red-700 shrink-0 line-through">{c.control_code}</span>
                    {c.name && <span className="text-xs text-muted-foreground truncate line-through">{c.name}</span>}
                    {c.criticality_code && (
                      <span className={`text-[10px] px-1.5 py-0.5 rounded border ml-auto ${
                        c.criticality_code === "critical" ? "border-red-500 text-red-500" :
                        c.criticality_code === "high" ? "border-orange-500 text-orange-500" : "border-muted-foreground text-muted-foreground"
                      }`}>{c.criticality_code}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* No previous version message */}
      {reviewDiff && !reviewDiff.has_previous_version && (
        <div className="rounded-xl border border-border bg-muted/10 px-5 py-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <GitBranch className="h-4 w-4" />
            <span>This is the first published version - no previous version to compare</span>
          </div>
        </div>
      )}

      {/* Diff viewer */}
      {diff ? (
        <div className="space-y-3">
          <h2 className="text-sm font-semibold">Control Changes</h2>
          <FrameworkDiffViewer diff={diff} />
        </div>
      ) : (
        <div className="rounded-xl border border-border bg-muted/10 px-5 py-8 text-center">
          <GitBranch className="h-8 w-8 text-muted-foreground/40 mx-auto mb-2" />
          <p className="text-sm text-muted-foreground">
            No diff available — this may be an initial version of the framework.
          </p>
        </div>
      )}

      {/* Sticky bottom action bar */}
      {canReview && (
        <div className="fixed bottom-0 left-0 right-0 z-50 border-t border-border bg-background/95 backdrop-blur-sm px-6 py-4">
          <div className="max-w-screen-xl mx-auto">
            {/* Action error */}
            {actionError && (
              <div className="mb-3 rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-2.5 flex items-center gap-3">
                <AlertCircle className="h-4 w-4 text-destructive shrink-0" />
                <p className="text-sm text-destructive flex-1">{actionError}</p>
                <button
                  className="text-xs underline text-destructive"
                  onClick={() => setActionError(null)}
                >
                  Dismiss
                </button>
              </div>
            )}

            {/* Reject reason textarea */}
            {showRejectForm && (
              <div className="mb-3 space-y-1.5">
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Rejection reason (optional)
                </label>
                <textarea
                  rows={3}
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  placeholder="Describe why this framework is being rejected..."
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none"
                />
              </div>
            )}

            <div className="flex items-center gap-3 justify-end">
              {!showRejectForm ? (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowRejectForm(true)}
                    disabled={submitting}
                    className="gap-1.5 text-destructive border-destructive/30 hover:bg-destructive/10 hover:text-destructive"
                  >
                    <XCircle className="h-3.5 w-3.5" />
                    Reject
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleApprove}
                    disabled={submitting}
                    className="gap-1.5"
                  >
                    {submitting ? (
                      <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <CheckCircle2 className="h-3.5 w-3.5" />
                    )}
                    Approve &amp; Publish
                  </Button>
                </>
              ) : (
                <>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setShowRejectForm(false)
                      setRejectReason("")
                    }}
                    disabled={submitting}
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={handleReject}
                    disabled={submitting}
                    className="gap-1.5"
                  >
                    {submitting ? (
                      <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <XCircle className="h-3.5 w-3.5" />
                    )}
                    Confirm Rejection
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
