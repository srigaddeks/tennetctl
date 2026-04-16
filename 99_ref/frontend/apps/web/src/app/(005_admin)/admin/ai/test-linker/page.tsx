"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { useSearchParams } from "next/navigation"
import {
  CheckCircle2,
  Loader2,
  Play,
  RefreshCw,
  Search,
  Sparkles,
  ThumbsDown,
  ThumbsUp,
} from "lucide-react"
import { Button, Card, CardContent, Input } from "@kcontrol/ui"
import { listAllControls, listFrameworks, listTests } from "@/lib/api/grc"
import { listOrgs } from "@/lib/api/orgs"
import { listWorkspaces } from "@/lib/api/workspaces"
import {
  bulkApproveTestControlMappings,
  bulkRejectTestControlMappings,
  enqueueBulkTestLink,
  getTestLinkerJobStatus,
  listPendingTestControlMappings,
  type PendingTestControlMapping,
  type TestLinkerJobStatusResponse,
} from "@/lib/api/testLinker"
import type { ControlResponse, FrameworkResponse, TestResponse } from "@/lib/types/grc"
import type { OrgResponse, WorkspaceResponse } from "@/lib/types/orgs"

const STATUS_META: Record<string, { label: string; color: string }> = {
  queued: { label: "Queued", color: "text-amber-500" },
  running: { label: "Running", color: "text-blue-500" },
  completed: { label: "Completed", color: "text-green-500" },
  failed: { label: "Failed", color: "text-red-500" },
  cancelled: { label: "Cancelled", color: "text-muted-foreground" },
}

function MultiSelectList<T extends { id: string }>({
  items,
  selected,
  onToggle,
  getLabel,
  getMeta,
  emptyLabel,
}: {
  items: T[]
  selected: Set<string>
  onToggle: (id: string) => void
  getLabel: (item: T) => string
  getMeta?: (item: T) => string | null
  emptyLabel: string
}) {
  if (items.length === 0) {
    return <div className="rounded-lg border border-dashed border-border px-3 py-6 text-center text-xs text-muted-foreground">{emptyLabel}</div>
  }

  return (
    <div className="max-h-60 overflow-y-auto rounded-lg border border-border divide-y divide-border">
      {items.map((item) => {
        const active = selected.has(item.id)
        return (
          <button
            key={item.id}
            type="button"
            onClick={() => onToggle(item.id)}
            className={`flex w-full items-start gap-3 px-3 py-2.5 text-left transition-colors ${active ? "bg-primary/5" : "hover:bg-muted/40"}`}
          >
            <div className={`mt-0.5 h-4 w-4 rounded border flex items-center justify-center ${active ? "border-primary bg-primary text-primary-foreground" : "border-border"}`}>
              {active && <CheckCircle2 className="h-3 w-3" />}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{getLabel(item)}</p>
              {getMeta?.(item) && <p className="truncate text-[11px] text-muted-foreground">{getMeta(item)}</p>}
            </div>
          </button>
        )
      })}
    </div>
  )
}

export default function TestLinkerAdminPage() {
  const searchParams = useSearchParams()
  const [orgs, setOrgs] = useState<OrgResponse[]>([])
  const [workspaces, setWorkspaces] = useState<WorkspaceResponse[]>([])
  const [frameworks, setFrameworks] = useState<FrameworkResponse[]>([])
  const [tests, setTests] = useState<TestResponse[]>([])
  const [controls, setControls] = useState<ControlResponse[]>([])

  const [selectedOrgId, setSelectedOrgId] = useState("")
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState("")
  const [controlScope, setControlScope] = useState<"all" | "framework" | "specific">("all")
  const [testScope, setTestScope] = useState<"all" | "specific">("all")
  const [selectedFrameworkId, setSelectedFrameworkId] = useState("")
  const [selectedControlIds, setSelectedControlIds] = useState<Set<string>>(new Set())
  const [selectedTestIds, setSelectedTestIds] = useState<Set<string>>(new Set())
  const [controlSearch, setControlSearch] = useState("")
  const [testSearch, setTestSearch] = useState("")
  const [priority, setPriority] = useState("normal")
  const [dryRun, setDryRun] = useState(false)

  const [loadingOrgs, setLoadingOrgs] = useState(true)
  const [loadingWs, setLoadingWs] = useState(false)
  const [loadingFw, setLoadingFw] = useState(false)
  const [loadingTests, setLoadingTests] = useState(false)
  const [loadingControls, setLoadingControls] = useState(false)

  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [jobs, setJobs] = useState<TestLinkerJobStatusResponse[]>([])
  const [activeJobId, setActiveJobId] = useState<string | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const [reviewItems, setReviewItems] = useState<PendingTestControlMapping[]>([])
  const [loadingReview, setLoadingReview] = useState(false)
  const [reviewError, setReviewError] = useState<string | null>(null)
  const [processing, setProcessing] = useState(false)
  const [decisions, setDecisions] = useState<Record<string, "approve" | "reject" | null>>({})
  const [rejectReason, setRejectReason] = useState("")
  const [doneSummary, setDoneSummary] = useState<{ approved: number; rejected: number } | null>(null)

  useEffect(() => {
    listOrgs()
      .then((data) => setOrgs(data))
      .catch(() => {})
      .finally(() => setLoadingOrgs(false))
  }, [])

  useEffect(() => {
    const orgId = searchParams.get("org_id")
    const workspaceId = searchParams.get("workspace_id")
    if (orgId) setSelectedOrgId(orgId)
    if (workspaceId) setSelectedWorkspaceId(workspaceId)
  }, [searchParams])

  useEffect(() => {
    if (!selectedOrgId) {
      setWorkspaces([])
      setFrameworks([])
      setTests([])
      setControls([])
      setSelectedWorkspaceId("")
      setSelectedFrameworkId("")
      return
    }

    setLoadingWs(true)
    setLoadingTests(true)
    setLoadingControls(true)
    if (selectedOrgId !== searchParams.get("org_id")) {
      setSelectedWorkspaceId("")
    }
    setSelectedFrameworkId("")
    setSelectedControlIds(new Set())
    setSelectedTestIds(new Set())

    listWorkspaces(selectedOrgId)
      .then((data) => setWorkspaces(data))
      .catch(() => {})
      .finally(() => setLoadingWs(false))

    listTests({ scope_org_id: selectedOrgId, limit: 200 })
      .then((res) => setTests(res.items ?? []))
      .catch(() => {})
      .finally(() => setLoadingTests(false))

    listAllControls({ deployed_org_id: selectedOrgId, limit: 200 })
      .then((res) => setControls(res.items ?? []))
      .catch(() => {})
      .finally(() => setLoadingControls(false))
  }, [searchParams, selectedOrgId])

  useEffect(() => {
    if (!selectedOrgId) {
      setFrameworks([])
      return
    }

    setLoadingFw(true)
    listFrameworks({
      deployed_org_id: selectedOrgId,
      deployed_workspace_id: selectedWorkspaceId || undefined,
    })
      .then((res) => {
        const items = res.items ?? []
        setFrameworks(items)
        if (selectedFrameworkId && !items.some((framework) => framework.id === selectedFrameworkId)) {
          setSelectedFrameworkId("")
        }
      })
      .catch(() => {})
      .finally(() => setLoadingFw(false))
  }, [selectedFrameworkId, selectedOrgId, selectedWorkspaceId])

  useEffect(() => {
    if (!selectedOrgId) return
    setLoadingTests(true)
    setLoadingControls(true)

    listTests({
      scope_org_id: selectedOrgId,
      scope_workspace_id: selectedWorkspaceId || undefined,
      limit: 200,
    })
      .then((res) => setTests(res.items ?? []))
      .catch(() => {})
      .finally(() => setLoadingTests(false))

    listAllControls({
      deployed_org_id: selectedOrgId,
      deployed_workspace_id: selectedWorkspaceId || undefined,
      framework_id: controlScope === "framework" && selectedFrameworkId ? selectedFrameworkId : undefined,
      limit: 200,
    })
      .then((res) => setControls(res.items))
      .catch(() => {})
      .finally(() => setLoadingControls(false))
  }, [selectedOrgId, selectedWorkspaceId, controlScope, selectedFrameworkId])

  const filteredTests = useMemo(() => {
    const query = testSearch.trim().toLowerCase()
    return tests.filter((test) => {
      if (!query) return true
      return (
        (test.name || "").toLowerCase().includes(query) ||
        test.test_code.toLowerCase().includes(query)
      )
    })
  }, [tests, testSearch])

  const filteredControls = useMemo(() => {
    const query = controlSearch.trim().toLowerCase()
    return controls.filter((control) => {
      if (controlScope === "framework" && selectedFrameworkId && control.framework_id !== selectedFrameworkId) {
        return false
      }
      if (!query) return true
      return (
        (control.name || "").toLowerCase().includes(query) ||
        control.control_code.toLowerCase().includes(query) ||
        (control.framework_code || "").toLowerCase().includes(query)
      )
    })
  }, [controls, controlScope, selectedFrameworkId, controlSearch])

  const refreshJob = useCallback(async (jobId: string) => {
    try {
      const status = await getTestLinkerJobStatus(jobId)
      setJobs((prev) => {
        const idx = prev.findIndex((item) => item.job_id === jobId)
        if (idx >= 0) {
          const next = [...prev]
          next[idx] = status
          return next
        }
        return [status, ...prev]
      })
      if (["completed", "failed", "cancelled"].includes(status.status_code)) {
        setActiveJobId(null)
        if (status.status_code === "completed") {
          setLoadingReview(true)
          setReviewError(null)
          const pending = await listPendingTestControlMappings({
            org_id: selectedOrgId || undefined,
            workspace_id: selectedWorkspaceId || undefined,
            framework_id: controlScope === "framework" ? selectedFrameworkId || undefined : undefined,
            control_ids: controlScope === "specific" ? [...selectedControlIds] : undefined,
            test_ids: testScope === "specific" ? [...selectedTestIds] : undefined,
            created_after: status.created_at,
            mine_only: true,
            limit: 500,
          })
          setReviewItems(pending.items)
          setDecisions(
            pending.items.reduce<Record<string, "approve" | "reject" | null>>((acc, item) => {
              acc[item.id] = "approve"
              return acc
            }, {}),
          )
          setDoneSummary(null)
          setLoadingReview(false)
        }
      }
    } catch (error) {
      setReviewError(error instanceof Error ? error.message : "Failed to refresh job")
    }
  }, [controlScope, selectedControlIds, selectedFrameworkId, selectedOrgId, selectedTestIds, selectedWorkspaceId, testScope])

  useEffect(() => {
    if (!activeJobId) {
      if (pollRef.current) clearInterval(pollRef.current)
      return
    }
    pollRef.current = setInterval(() => refreshJob(activeJobId), 3000)
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [activeJobId, refreshJob])

  const toggleControl = (id: string) => {
    setSelectedControlIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleTest = (id: string) => {
    setSelectedTestIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const handleSubmit = useCallback(async () => {
    if (!selectedOrgId) return
    setSubmitting(true)
    setSubmitError(null)
    setReviewItems([])
    setReviewError(null)
    setDoneSummary(null)
    try {
      const res = await enqueueBulkTestLink({
        org_id: selectedOrgId,
        workspace_id: selectedWorkspaceId || null,
        framework_id: controlScope === "framework" ? selectedFrameworkId || null : null,
        control_ids: controlScope === "specific" ? [...selectedControlIds] : undefined,
        test_ids: testScope === "specific" ? [...selectedTestIds] : undefined,
        priority_code: priority,
        dry_run: dryRun,
      })
      const job: TestLinkerJobStatusResponse = {
        job_id: res.job_id,
        status_code: res.status,
        job_type: "test_linker_bulk_link",
        progress_pct: 0,
        output_json: null,
        error_message: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      setJobs((prev) => [job, ...prev])
      setActiveJobId(res.job_id)
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : "Failed to enqueue job")
    } finally {
      setSubmitting(false)
    }
  }, [controlScope, dryRun, priority, selectedControlIds, selectedFrameworkId, selectedOrgId, selectedTestIds, selectedWorkspaceId, testScope])

  const handleApplyReview = useCallback(async () => {
    const approveIds = reviewItems.filter((item) => decisions[item.id] === "approve").map((item) => item.id)
    const rejectIds = reviewItems.filter((item) => decisions[item.id] === "reject").map((item) => item.id)
    setProcessing(true)
    setReviewError(null)
    try {
      let approved = 0
      let rejected = 0
      if (approveIds.length > 0) {
        const res = await bulkApproveTestControlMappings(approveIds)
        approved = res.updated
      }
      if (rejectIds.length > 0) {
        const res = await bulkRejectTestControlMappings(rejectIds, rejectReason || undefined)
        rejected = res.updated
      }
      setDoneSummary({ approved, rejected })
    } catch (error) {
      setReviewError(error instanceof Error ? error.message : "Failed to process review decisions")
    } finally {
      setProcessing(false)
    }
  }, [decisions, rejectReason, reviewItems])

  const canSubmit =
    !!selectedOrgId &&
    !submitting &&
    (controlScope !== "framework" || !!selectedFrameworkId) &&
    (controlScope !== "specific" || selectedControlIds.size > 0) &&
    (testScope !== "specific" || selectedTestIds.size > 0)

  const latestJob = jobs[0] ?? null

  return (
    <div className="space-y-6">
      <div className="flex items-start gap-3">
        <div className="rounded-lg bg-primary/10 p-2">
          <Sparkles className="h-5 w-5 text-primary" />
        </div>
        <div>
          <h1 className="text-xl font-semibold">Control Test Linker</h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            Bulk-match control tests to controls with AI, then approve or reject the proposed mappings.
          </p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="border-border/60">
          <CardContent className="space-y-4 p-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Configuration</p>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Organisation</label>
              {loadingOrgs ? (
                <div className="flex items-center gap-2 text-xs text-muted-foreground"><Loader2 className="h-3 w-3 animate-spin" /> Loading…</div>
              ) : (
                <select className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" value={selectedOrgId} onChange={(event) => setSelectedOrgId(event.target.value)}>
                  <option value="">Select an organisation…</option>
                  {orgs.map((org) => <option key={org.id} value={org.id}>{org.name}</option>)}
                </select>
              )}
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Workspace</label>
              {loadingWs ? (
                <div className="flex items-center gap-2 text-xs text-muted-foreground"><Loader2 className="h-3 w-3 animate-spin" /> Loading…</div>
              ) : (
                <select className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" value={selectedWorkspaceId} onChange={(event) => setSelectedWorkspaceId(event.target.value)} disabled={!selectedOrgId}>
                  <option value="">All workspaces / org scope</option>
                  {workspaces.map((workspace) => <option key={workspace.id} value={workspace.id}>{workspace.name}</option>)}
                </select>
              )}
            </div>

            <div className="space-y-2">
              <label className="text-xs font-medium text-muted-foreground">Test scope</label>
              <div className="flex gap-2">
                <Button size="sm" variant={testScope === "all" ? "default" : "outline"} onClick={() => setTestScope("all")}>All workspace tests</Button>
                <Button size="sm" variant={testScope === "specific" ? "default" : "outline"} onClick={() => setTestScope("specific")}>Specific tests</Button>
              </div>
              {testScope === "specific" && (
                <div className="space-y-2">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
                    <Input className="pl-8 h-9 text-sm" value={testSearch} onChange={(event) => setTestSearch(event.target.value)} placeholder="Filter tests…" />
                  </div>
                  {loadingTests ? (
                    <div className="flex items-center gap-2 text-xs text-muted-foreground"><Loader2 className="h-3 w-3 animate-spin" /> Loading tests…</div>
                  ) : (
                    <MultiSelectList
                      items={filteredTests}
                      selected={selectedTestIds}
                      onToggle={toggleTest}
                      getLabel={(test) => test.name || test.test_code}
                      getMeta={(test) => test.test_code}
                      emptyLabel="No tests available in this scope."
                    />
                  )}
                </div>
              )}
            </div>

            <div className="space-y-2">
              <label className="text-xs font-medium text-muted-foreground">Control scope</label>
              <div className="flex gap-2 flex-wrap">
                <Button size="sm" variant={controlScope === "all" ? "default" : "outline"} onClick={() => setControlScope("all")}>All controls</Button>
                <Button size="sm" variant={controlScope === "framework" ? "default" : "outline"} onClick={() => setControlScope("framework")}>Framework controls</Button>
                <Button size="sm" variant={controlScope === "specific" ? "default" : "outline"} onClick={() => setControlScope("specific")}>Specific controls</Button>
              </div>

              {controlScope === "framework" && (
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">Framework</label>
                  {loadingFw ? (
                    <div className="flex items-center gap-2 text-xs text-muted-foreground"><Loader2 className="h-3 w-3 animate-spin" /> Loading…</div>
                  ) : (
                    <select className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" value={selectedFrameworkId} onChange={(event) => setSelectedFrameworkId(event.target.value)}>
                      <option value="">Select a framework…</option>
                      {frameworks.map((framework) => (
                        <option key={framework.id} value={framework.id}>
                          {framework.framework_code} - {framework.name}
                        </option>
                      ))}
                    </select>
                  )}
                </div>
              )}

              {controlScope === "specific" && (
                <div className="space-y-2">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
                    <Input className="pl-8 h-9 text-sm" value={controlSearch} onChange={(event) => setControlSearch(event.target.value)} placeholder="Filter controls…" />
                  </div>
                  {loadingControls ? (
                    <div className="flex items-center gap-2 text-xs text-muted-foreground"><Loader2 className="h-3 w-3 animate-spin" /> Loading controls…</div>
                  ) : (
                    <MultiSelectList
                      items={filteredControls}
                      selected={selectedControlIds}
                      onToggle={toggleControl}
                      getLabel={(control) => control.name || control.control_code}
                      getMeta={(control) => `${control.control_code}${control.framework_code ? ` · ${control.framework_code}` : ""}`}
                      emptyLabel="No controls available in this scope."
                    />
                  )}
                </div>
              )}
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Priority</label>
                <select className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" value={priority} onChange={(event) => setPriority(event.target.value)}>
                  <option value="low">Low</option>
                  <option value="normal">Normal</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>
              <label className="flex items-center gap-3 rounded-lg border border-border px-3 py-2">
                <div className={`relative h-5 w-9 rounded-full transition-colors ${dryRun ? "bg-primary" : "bg-muted"}`} onClick={() => setDryRun((value) => !value)}>
                  <span className={`absolute left-0.5 top-0.5 h-4 w-4 rounded-full bg-white shadow transition-transform ${dryRun ? "translate-x-4" : ""}`} />
                </div>
                <div>
                  <p className="text-sm font-medium">Dry run</p>
                  <p className="text-[11px] text-muted-foreground">Preview proposals only</p>
                </div>
              </label>
            </div>

            <div className="rounded-lg border border-primary/20 bg-primary/5 p-3 text-xs text-muted-foreground">
              <p className="mb-1 font-medium text-primary">How it works</p>
              <ul className="list-inside list-disc space-y-0.5">
                <li>AI evaluates the selected control scope against the selected control tests.</li>
                <li>Proposed mappings are created as pending approvals, not live links.</li>
                <li>You approve or reject the batch after the job finishes.</li>
                <li>Existing mappings are skipped automatically.</li>
              </ul>
            </div>

            {submitError && <p className="rounded bg-red-500/10 px-3 py-2 text-xs text-red-500">{submitError}</p>}

            <Button className="w-full gap-2" disabled={!canSubmit} onClick={handleSubmit}>
              {submitting ? <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Starting…</> : <><Play className="h-3.5 w-3.5" /> Run AI Linking</>}
            </Button>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card className="border-border/60">
            <CardContent className="space-y-4 p-5">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Job Status</p>
                {latestJob && (
                  <button className="text-muted-foreground hover:text-foreground" onClick={() => refreshJob(latestJob.job_id)}>
                    <RefreshCw className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>

              {!latestJob ? (
                <div className="rounded-lg border border-dashed border-border px-3 py-8 text-center text-sm text-muted-foreground">
                  No bulk AI link job started yet.
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className={`text-sm font-medium ${(STATUS_META[latestJob.status_code] ?? STATUS_META.cancelled).color}`}>
                      {(STATUS_META[latestJob.status_code] ?? { label: latestJob.status_code }).label}
                    </span>
                    <span className="text-[10px] font-mono text-muted-foreground">{latestJob.job_id.slice(0, 8)}…</span>
                  </div>
                  {latestJob.progress_pct !== null && latestJob.status_code !== "completed" && (
                    <div className="space-y-1">
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>Progress</span>
                        <span>{latestJob.progress_pct}%</span>
                      </div>
                      <div className="h-1.5 rounded-full bg-muted/50">
                        <div className="h-1.5 rounded-full bg-primary transition-all" style={{ width: `${latestJob.progress_pct}%` }} />
                      </div>
                    </div>
                  )}
                  {latestJob.output_json && latestJob.status_code === "completed" && (
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      {[
                        { label: "Controls checked", value: latestJob.output_json.total_controls },
                        { label: "Tests evaluated", value: latestJob.output_json.total_tests },
                        { label: "Proposals created", value: latestJob.output_json.mappings_created },
                        { label: "Skipped", value: latestJob.output_json.mappings_skipped },
                      ].map((item) => (
                        <div key={item.label} className="rounded bg-muted/30 p-2">
                          <p className="text-muted-foreground">{item.label}</p>
                          <p className="text-sm font-semibold">{String(item.value ?? "—")}</p>
                        </div>
                      ))}
                    </div>
                  )}
                  {latestJob.error_message && <p className="rounded bg-red-500/10 px-3 py-2 text-xs text-red-500">{latestJob.error_message}</p>}
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="border-border/60">
            <CardContent className="space-y-4 p-5">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Approval Review</p>
                <span className="text-xs text-muted-foreground">{reviewItems.length} pending</span>
              </div>

              {loadingReview ? (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" /> Loading pending mappings…
                </div>
              ) : doneSummary ? (
                <div className="space-y-2 text-center">
                  <CheckCircle2 className="mx-auto h-8 w-8 text-green-500" />
                  <p className="font-medium">Review complete</p>
                  <p className="text-sm text-muted-foreground">
                    <span className="text-green-600">{doneSummary.approved} approved</span>
                    {doneSummary.rejected > 0 && <> · <span className="text-red-500">{doneSummary.rejected} rejected</span></>}
                  </p>
                </div>
              ) : reviewItems.length === 0 ? (
                <div className="rounded-lg border border-dashed border-border px-3 py-8 text-center text-sm text-muted-foreground">
                  Run a job to load new proposals for review.
                </div>
              ) : (
                <>
                  <div className="flex items-center gap-3 text-xs">
                    <button className="flex items-center gap-1 text-green-600" onClick={() => setDecisions(Object.fromEntries(reviewItems.map((item) => [item.id, "approve"])))}>
                      <ThumbsUp className="h-3 w-3" /> Approve all
                    </button>
                    <button className="flex items-center gap-1 text-red-500" onClick={() => setDecisions(Object.fromEntries(reviewItems.map((item) => [item.id, "reject"])))}>
                      <ThumbsDown className="h-3 w-3" /> Reject all
                    </button>
                  </div>

                  <div className="max-h-80 space-y-2 overflow-y-auto pr-1">
                    {reviewItems.map((item) => {
                      const decision = decisions[item.id]
                      const confidence = item.ai_confidence !== null ? Math.round(item.ai_confidence * 100) : null
                      return (
                        <div key={item.id} className={`rounded-lg border p-3 ${decision === "approve" ? "border-green-500/30 bg-green-500/5" : decision === "reject" ? "border-red-500/30 bg-red-500/5" : "border-border/60"}`}>
                          <div className="flex items-start gap-3">
                            <div className="min-w-0 flex-1">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="text-[10px] font-mono text-primary">{item.test_code}</span>
                                <span className="text-xs text-muted-foreground">→</span>
                                <span className="text-[10px] font-mono text-muted-foreground">{item.control_code}</span>
                                <span className="rounded border px-1.5 py-0.5 text-[10px] font-semibold">{item.link_type}</span>
                                {confidence !== null && <span className="ml-auto text-[10px] font-semibold text-muted-foreground">{confidence}%</span>}
                              </div>
                              <p className="mt-1 text-sm font-medium truncate">{item.test_name || item.test_code}</p>
                              <p className="text-xs text-muted-foreground truncate">{item.control_name || item.control_code}{item.framework_code ? ` · ${item.framework_code}` : ""}</p>
                              {item.ai_rationale && <p className="mt-1 text-[11px] leading-relaxed text-muted-foreground">{item.ai_rationale}</p>}
                            </div>
                            <div className="flex gap-1">
                              <button className={`rounded p-1.5 ${decision === "approve" ? "bg-green-500/20 text-green-600" : "text-muted-foreground hover:bg-green-500/10 hover:text-green-600"}`} onClick={() => setDecisions((prev) => ({ ...prev, [item.id]: "approve" }))}>
                                <ThumbsUp className="h-3.5 w-3.5" />
                              </button>
                              <button className={`rounded p-1.5 ${decision === "reject" ? "bg-red-500/20 text-red-500" : "text-muted-foreground hover:bg-red-500/10 hover:text-red-500"}`} onClick={() => setDecisions((prev) => ({ ...prev, [item.id]: "reject" }))}>
                                <ThumbsDown className="h-3.5 w-3.5" />
                              </button>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>

                  {Object.values(decisions).some((value) => value === "reject") && (
                    <div className="space-y-1.5">
                      <label className="text-xs font-medium text-muted-foreground">Reject reason</label>
                      <Input value={rejectReason} onChange={(event) => setRejectReason(event.target.value)} placeholder="Optional reason for rejected mappings" />
                    </div>
                  )}

                  {reviewError && <p className="rounded bg-red-500/10 px-3 py-2 text-xs text-red-500">{reviewError}</p>}

                  <Button className="w-full gap-2" disabled={processing || Object.values(decisions).every((value) => value === null)} onClick={handleApplyReview}>
                    {processing ? <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Applying…</> : <><CheckCircle2 className="h-3.5 w-3.5" /> Apply Review Decisions</>}
                  </Button>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
