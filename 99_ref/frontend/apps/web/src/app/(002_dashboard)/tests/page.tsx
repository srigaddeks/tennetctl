"use client"

import { useEffect, useState, useCallback, useMemo, Suspense } from "react"
import { useSearchParams } from "next/navigation"
import {
  Button,
  Input,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@kcontrol/ui"
import {
  FlaskConical,
  Search,
  AlertTriangle,
  RefreshCw,
  Layers,
  Link2,
  Activity,
  ArrowRight,
  Github,
  Cloud,
  Database,
  Server,
  CheckCircle2,
  X,
  Globe,
  Download,
  Shield,
  Sparkles,
  Zap,
  Plug,
} from "lucide-react"
import { OrgWorkspaceSwitcher } from "@/components/layout/OrgWorkspaceSwitcher"
import { ReadOnlyBanner } from "@/components/layout/ReadOnlyBanner"
import { useAccess } from "@/components/providers/AccessProvider"
import { useOrgWorkspace } from "@/lib/context/OrgWorkspaceContext"
import { ControlTestCard } from "@/components/grc/ControlTestCard"
import { AssetSelectorDialog } from "@/components/grc/AssetSelectorDialog"
import { LinkControlsDialog } from "@/components/grc/LinkControlsDialog"
import { GlobalLibraryDialog } from "@/components/grc/GlobalLibraryDialog"
import { ConnectorIcon, getConnectorLabel } from "@/components/common/ConnectorIcon"
import {
  listPromotedTests,
  updatePromotedTest,
  deletePromotedTest,
  getPromotedTestHistory,
  listFrameworks,
} from "@/lib/api/grc"
import {
  listGlobalControlTests,
  listDeployedGlobalTestIds,
  deployGlobalControlTest,
  triggerCollection,
} from "@/lib/api/sandbox"
import {
  enqueueBulkTestLink,
  getTestLinkerJobStatus,
  listPendingTestControlMappings,
  bulkApproveTestControlMappings,
  bulkRejectTestControlMappings,
} from "@/lib/api/testLinker"
import type { PendingTestControlMapping } from "@/lib/api/testLinker"
import type { GlobalControlTestResponse } from "@/lib/api/sandbox"
import type { PromotedTestResponse } from "@/lib/types/grc"
import type { ExecutePromotedTestResponse } from "@/lib/api/grc"

// ── Helpers ───────────────────────────────────────────────────────────────────

function containerForTest(test: PromotedTestResponse): { code: string; label: string } {
  if (test.policy_container_code) {
    return {
      code: test.policy_container_code,
      label: test.policy_container_name || getConnectorLabel(test.policy_container_code),
    }
  }
  if (test.connector_type_code) {
    return {
      code: test.connector_type_code,
      label: getConnectorLabel(test.connector_type_code),
    }
  }
  if (test.source_signal_id && test.signal_type) {
    return {
      code: test.signal_type,
      label: getConnectorLabel(test.signal_type),
    }
  }
  return {
    code: "unassigned",
    label: "Unassigned",
  }
}


// ── Stats strip ───────────────────────────────────────────────────────────────

function StatsStrip({ tests }: { tests: PromotedTestResponse[] }) {
  const total = tests.length
  const linked = tests.filter((t) => !!t.linked_asset_id).length
  const unlinked = total - linked
  const automated = tests.filter((t) => t.test_type_code === "automated").length
  const connectorTypes = [
    ...new Set(
      tests
        .map((test) => containerForTest(test).code)
        .filter((code) => code !== "unassigned")
    ),
  ]

  return (
    <div className="flex items-stretch gap-3 flex-wrap">
      {[
        { label: "Total Tests", value: total, valueClass: "text-foreground", accent: "border-l-primary" },
        { label: "Automated", value: automated, valueClass: "text-violet-600 dark:text-violet-400", accent: "border-l-violet-500" },
        { label: "Asset Linked", value: linked, valueClass: "text-green-600 dark:text-green-400", accent: "border-l-green-500" },
        {
          label: "No Asset",
          value: unlinked,
          valueClass: unlinked > 0 ? "text-amber-600 dark:text-amber-400" : "text-muted-foreground",
          accent: unlinked > 0 ? "border-l-amber-500" : "border-l-border",
        },
      ].map((s) => (
        <div
          key={s.label}
          className={`flex flex-col gap-0.5 rounded-xl border border-l-[3px] ${s.accent} bg-card px-4 py-3 min-w-[90px]`}
        >
          <span className={`text-2xl font-bold tabular-nums leading-none ${s.valueClass}`}>{s.value}</span>
          <span className="text-[11px] text-muted-foreground mt-0.5">{s.label}</span>
        </div>
      ))}

      {/* Platform containers */}
      {connectorTypes.length > 0 && (
        <div className="flex items-center gap-2 ml-2 flex-wrap">
          <span className="text-[11px] text-muted-foreground">Platforms:</span>
          {connectorTypes.map((ct) => (
            <div
              key={ct}
              className="flex items-center gap-1.5 rounded-lg border border-border bg-muted/40 px-2.5 py-1 text-[11px] font-medium text-foreground"
            >
              <ConnectorIcon typeCode={ct} className="h-3 w-3 text-muted-foreground" />
              {getConnectorLabel(ct)}
              <CheckCircle2 className="h-3 w-3 text-green-500" />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Global Library Browse Dialog ──────────────────────────────────────────────


// ── Auto-Link with AI Modal ──────────────────────────────────────────────────

function AutoLinkTestsModal({
  open,
  orgId,
  workspaceId,
  onClose,
}: {
  open: boolean
  orgId: string
  workspaceId: string | null
  onClose: () => void
}) {
  const [step, setStep] = useState<"configure" | "running" | "review">("configure")
  const [frameworks, setFrameworks] = useState<{ id: string; framework_code: string; name: string; control_count: number }[]>([])
  const [selectedFrameworkId, setSelectedFrameworkId] = useState("")
  const [loadingFw, setLoadingFw] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [jobId, setJobId] = useState<string | null>(null)
  const [jobStatus, setJobStatus] = useState<string | null>(null)
  const [jobError, setJobError] = useState<string | null>(null)
  const [pending, setPending] = useState<PendingTestControlMapping[]>([])
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [approving, setApproving] = useState(false)

  useEffect(() => {
    if (!open) return
    setStep("configure")
    setJobId(null)
    setJobStatus(null)
    setJobError(null)
    setPending([])
    setSelected(new Set())
    setSelectedFrameworkId("")
    let cancelled = false
    async function loadFw() {
      setLoadingFw(true)
      try {
        const res = await listFrameworks({ deployed_org_id: orgId, deployed_workspace_id: workspaceId ?? undefined })
        if (!cancelled) setFrameworks(res.items.map(f => ({
          id: f.id,
          framework_code: f.framework_code,
          name: f.name ?? f.framework_code,
          control_count: f.control_count ?? 0,
        })))
      } catch { /* ignore */ }
      finally { if (!cancelled) setLoadingFw(false) }
    }
    loadFw()
    return () => { cancelled = true }
  }, [open, orgId, workspaceId])

  const handleRun = useCallback(async () => {
    setSubmitting(true)
    setJobError(null)
    try {
      const res = await enqueueBulkTestLink({
        framework_id: selectedFrameworkId || null,
        org_id: orgId,
        workspace_id: workspaceId,
      })
      setJobId(res.job_id)
      setJobStatus("queued")
      setStep("running")
    } catch (e) {
      setJobError(e instanceof Error ? e.message : "Failed to start job")
    } finally {
      setSubmitting(false)
    }
  }, [selectedFrameworkId, orgId, workspaceId])

  // Poll job status
  useEffect(() => {
    if (step !== "running" || !jobId) return
    let cancelled = false
    let failCount = 0
    const poll = setInterval(async () => {
      try {
        const s = await getTestLinkerJobStatus(jobId)
        if (cancelled) return
        failCount = 0
        setJobStatus(s.status_code)
        if (s.status_code === "completed") {
          clearInterval(poll)
          const res = await listPendingTestControlMappings({
            org_id: orgId,
            workspace_id: workspaceId ?? undefined,
            limit: 500,
          })
          setPending(res.items)
          setSelected(new Set(res.items.filter(m => m.approval_status === "pending").map(m => m.id)))
          setStep("review")
        } else if (s.status_code === "failed") {
          clearInterval(poll)
          setJobError(s.error_message || "Job failed")
          setStep("configure")
        }
      } catch (e) {
        failCount++
        if (failCount >= 3) {
          clearInterval(poll)
          if (!cancelled) {
            setJobError(e instanceof Error ? e.message : "Failed to check job status")
            setStep("configure")
          }
        }
      }
    }, 3000)
    return () => { cancelled = true; clearInterval(poll) }
  }, [step, jobId, orgId, workspaceId])

  const pendingItems = pending.filter(m => m.approval_status === "pending")

  const handleApproveSelected = useCallback(async () => {
    if (selected.size === 0) return
    setApproving(true)
    try {
      await bulkApproveTestControlMappings([...selected])
      setPending(prev => prev.map(m => selected.has(m.id) ? { ...m, approval_status: "approved" as const } : m))
      setSelected(new Set())
    } catch { /* ignore */ }
    finally { setApproving(false) }
  }, [selected])

  const handleRejectRemaining = useCallback(async () => {
    const rejectIds = pendingItems.filter(m => !selected.has(m.id)).map(m => m.id)
    if (rejectIds.length === 0) return
    try {
      await bulkRejectTestControlMappings(rejectIds)
      setPending(prev => prev.map(m => rejectIds.includes(m.id) ? { ...m, approval_status: "rejected" as const } : m))
    } catch { /* ignore */ }
  }, [pendingItems, selected])

  const toggleSelected = (id: string) => setSelected(prev => {
    const next = new Set(prev)
    if (next.has(id)) next.delete(id); else next.add(id)
    return next
  })

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-full bg-primary/10 flex items-center justify-center">
              <Link2 className="h-4 w-4 text-primary" />
            </div>
            <div>
              <DialogTitle>Auto-Link with AI</DialogTitle>
              <DialogDescription className="text-xs">
                AI will propose test-to-control links for your review
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {step === "configure" && (
          <div className="space-y-4 pt-2">
            <div>
              <label className="text-xs font-medium text-muted-foreground flex items-center gap-2">
                Framework <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground/60">optional</span>
              </label>
              <select
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                value={selectedFrameworkId}
                onChange={e => setSelectedFrameworkId(e.target.value)}
              >
                <option value="">All frameworks (evaluate every control)</option>
                {frameworks.map(f => (
                  <option key={f.id} value={f.id}>
                    {f.framework_code} — {f.name} ({f.control_count} controls)
                  </option>
                ))}
              </select>
            </div>
            <div className="rounded-lg border border-primary/20 bg-primary/5 p-4 space-y-2">
              <p className="text-xs font-semibold text-primary flex items-center gap-1.5">
                <Sparkles className="h-3.5 w-3.5" /> How it works
              </p>
              <ul className="text-xs text-muted-foreground space-y-1 list-disc pl-4">
                <li>AI evaluates every control test against controls in this workspace</li>
                <li>Proposed links land in a review queue — nothing is created yet</li>
                <li>You approve or reject each proposal before it takes effect</li>
                <li>Only approved links are written to the control test mappings</li>
              </ul>
            </div>
            {jobError && (
              <p className="text-xs text-destructive flex items-center gap-1.5">
                <AlertTriangle className="h-3.5 w-3.5" /> {jobError}
              </p>
            )}
            <div className="flex justify-between items-center pt-2">
              <Button variant="ghost" size="sm" onClick={onClose}>Cancel</Button>
              <Button size="sm" className="gap-1.5" onClick={handleRun} disabled={submitting}>
                {submitting ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <ArrowRight className="h-3.5 w-3.5" />}
                {submitting ? "Starting…" : "Run Analysis"}
              </Button>
            </div>
          </div>
        )}

        {step === "running" && (
          <div className="flex flex-col items-center gap-4 py-8">
            <RefreshCw className="h-8 w-8 text-primary animate-spin" />
            <div className="text-center">
              <p className="text-sm font-medium">Analyzing test-control relationships…</p>
              <p className="text-xs text-muted-foreground mt-1">
                {jobStatus === "queued" ? "Queued — waiting for worker…" : "Processing — this may take a minute"}
              </p>
            </div>
            {jobError && (
              <p className="text-xs text-destructive flex items-center gap-1.5">
                <AlertTriangle className="h-3.5 w-3.5" /> {jobError}
              </p>
            )}
          </div>
        )}

        {step === "review" && (
          <div className="space-y-3 pt-2 max-h-[400px] overflow-y-auto">
            {pendingItems.length === 0 ? (
              <div className="text-center py-8">
                <CheckCircle2 className="h-8 w-8 mx-auto text-green-500 mb-2" />
                <p className="text-sm font-medium">All proposals reviewed</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {pending.filter(m => m.approval_status === "approved").length} approved, {pending.filter(m => m.approval_status === "rejected").length} rejected
                </p>
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between">
                  <p className="text-xs text-muted-foreground">{pendingItems.length} proposal{pendingItems.length !== 1 ? "s" : ""} to review</p>
                  <div className="flex items-center gap-2">
                    <Button variant="ghost" size="sm" className="text-xs h-7" onClick={() => setSelected(new Set(pendingItems.map(m => m.id)))}>Select all</Button>
                    <Button variant="ghost" size="sm" className="text-xs h-7" onClick={() => setSelected(new Set())}>None</Button>
                  </div>
                </div>
                {pendingItems.map(m => (
                  <label key={m.id} className="flex items-start gap-3 rounded-lg border border-border p-3 cursor-pointer hover:bg-muted/30 transition-colors">
                    <input
                      type="checkbox"
                      className="mt-0.5 h-4 w-4 rounded border-primary/20 accent-primary"
                      checked={selected.has(m.id)}
                      onChange={() => toggleSelected(m.id)}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold text-foreground truncate">{m.test_name || m.test_code}</span>
                        <ArrowRight className="h-3 w-3 text-muted-foreground shrink-0" />
                        <span className="text-xs text-muted-foreground truncate">{m.control_name || m.control_code}</span>
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                          m.link_type === "covers" ? "bg-green-500/10 text-green-600" :
                          m.link_type === "partially_covers" ? "bg-amber-500/10 text-amber-600" :
                          "bg-blue-500/10 text-blue-600"
                        }`}>{m.link_type?.replace("_", " ")}</span>
                        {m.ai_confidence != null && (
                          <span className="text-[10px] text-muted-foreground">{Math.round(m.ai_confidence * 100)}% confidence</span>
                        )}
                      </div>
                      {m.ai_rationale && <p className="text-[10px] text-muted-foreground mt-1 line-clamp-2">{m.ai_rationale}</p>}
                    </div>
                  </label>
                ))}
              </>
            )}
            <div className="flex justify-between items-center pt-2 border-t border-border">
              {pendingItems.length > 0 ? (
                <>
                  <Button variant="ghost" size="sm" className="text-xs text-destructive" onClick={handleRejectRemaining}>
                    Reject unselected ({pendingItems.length - selected.size})
                  </Button>
                  <Button size="sm" className="gap-1.5" onClick={handleApproveSelected} disabled={selected.size === 0 || approving}>
                    {approving ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <CheckCircle2 className="h-3.5 w-3.5" />}
                    Approve {selected.size} link{selected.size !== 1 ? "s" : ""}
                  </Button>
                </>
              ) : (
                <Button size="sm" className="ml-auto" onClick={onClose}>Done</Button>
              )}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function TestsPage() {
  const searchParams = useSearchParams()
  const { selectedOrgId, selectedWorkspaceId } = useOrgWorkspace()
  const { canWrite } = useAccess()
  const canEdit = canWrite("grc") || canWrite("sandbox")

  const [tests, setTests] = useState<PromotedTestResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [search, setSearch] = useState("")
  const [filterAsset, setFilterAsset] = useState<"all" | "linked" | "unlinked">("all")
  const [filterType, setFilterType] = useState("")
  const [filterConnector, setFilterConnector] = useState("")

  const [histories, setHistories] = useState<Record<string, PromotedTestResponse[]>>({})
  const [assetDialogTestId, setAssetDialogTestId] = useState<string | null>(null)
  const [assetDialogCurrentId, setAssetDialogCurrentId] = useState<string | null>(null)
  const [deleteConfirm, setDeleteConfirm] = useState<PromotedTestResponse | null>(null)
  const [linkControlsTest, setLinkControlsTest] = useState<PromotedTestResponse | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [runningTestId, setRunningTestId] = useState<string | null>(null)
  const [testResults, setTestResults] = useState<Record<string, ExecutePromotedTestResponse>>({})
  const [globalLibraryOpen, setGlobalLibraryOpen] = useState(false)
  const [showAutoLink, setShowAutoLink] = useState(false)

  // Auto-open global library dialog when browse_library=1 in URL
  useEffect(() => {
    if (searchParams.get("browse_library") === "1" && selectedOrgId) {
      setGlobalLibraryOpen(true)
    }
  }, [searchParams, selectedOrgId])

  async function handleRunTest(testId: string) {
    const test = tests.find((t) => t.id === testId)
    const orgId = selectedOrgId ?? test?.org_id
    if (!test?.linked_asset_id || !orgId) return
    setRunningTestId(testId)
    try {
      // Trigger live collection on the linked connector — backend auto-runs all
      // promoted tests linked to it after collection completes.
      await triggerCollection(orgId, test.linked_asset_id)
      setTestResults((prev) => ({
        ...prev,
        [testId]: {
          test_id: testId,
          test_code: test.test_code,
          result_status: "pending",
          summary: "Collection triggered — results will appear on the Live page",
          details: [],
          metadata: {},
          execution_id: null,
          executed_at: new Date().toISOString(),
          task_created: false,
          task_id: null,
        },
      }))
    } catch (e) {
      setTestResults((prev) => ({
        ...prev,
        [testId]: {
          test_id: testId,
          test_code: test.test_code,
          result_status: "error",
          summary: e instanceof Error ? e.message : "Failed to trigger collection",
          details: [],
          metadata: {},
          execution_id: null,
          executed_at: new Date().toISOString(),
          task_created: false,
          task_id: null,
        },
      }))
    } finally {
      setRunningTestId(null)
    }
  }

  const load = useCallback(async () => {
    if (!selectedOrgId) return
    setLoading(true)
    setError(null)
    try {
      const res = await listPromotedTests({ orgId: selectedOrgId, isActive: true })
      setTests(res.items)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load tests")
    } finally {
      setLoading(false)
    }
  }, [selectedOrgId, selectedWorkspaceId])

  useEffect(() => { load() }, [load])

  async function handleLoadHistory(testId: string) {
    try {
      const history = await getPromotedTestHistory(testId)
      setHistories((prev) => ({ ...prev, [testId]: history }))
    } catch { /* ignore */ }
  }

  function handleLinkAsset(testId: string) {
    const test = tests.find((t) => t.id === testId)
    setAssetDialogTestId(testId)
    setAssetDialogCurrentId(test?.linked_asset_id ?? null)
  }

  async function handleAssetSelect(connectorId: string) {
    if (!assetDialogTestId) return
    try {
      await updatePromotedTest(assetDialogTestId, { linked_asset_id: connectorId })
      await load()
    } catch { /* ignore */ } finally {
      setAssetDialogTestId(null)
    }
  }

  async function handleDelete(test: PromotedTestResponse) {
    setDeleting(true)
    try {
      await deletePromotedTest(test.id)
      setDeleteConfirm(null)
      await load()
    } finally {
      setDeleting(false)
    }
  }

  const connectorTypes = useMemo(
    () =>
      [
        ...new Set(
          tests
            .map((test) => containerForTest(test).code)
            .filter((code) => code !== "unassigned")
        ),
      ],
    [tests]
  )

  const filtered = useMemo(() => {
    let list = tests
    if (search) {
      const q = search.toLowerCase()
      list = list.filter(
        (t) =>
          (t.name || "").toLowerCase().includes(q) ||
          t.test_code.toLowerCase().includes(q) ||
          (t.connector_name || "").toLowerCase().includes(q) ||
          (t.connector_type_code || "").toLowerCase().includes(q) ||
          (t.policy_container_name || "").toLowerCase().includes(q) ||
          (t.policy_container_code || "").toLowerCase().includes(q)
      )
    }
    if (filterAsset === "linked") list = list.filter((t) => !!t.linked_asset_id)
    if (filterAsset === "unlinked") list = list.filter((t) => !t.linked_asset_id)
    if (filterType) list = list.filter((t) => t.test_type_code === filterType)
    if (filterConnector) list = list.filter((t) => containerForTest(t).code === filterConnector)
    return list
  }, [tests, search, filterAsset, filterType, filterConnector])

  const groupedTests = useMemo(() => {
    const groups = new Map<string, { code: string; label: string; tests: PromotedTestResponse[] }>()
    for (const test of filtered) {
      const container = containerForTest(test)
      const existing = groups.get(container.code)
      if (existing) {
        existing.tests.push(test)
      } else {
        groups.set(container.code, { ...container, tests: [test] })
      }
    }
    return [...groups.values()].sort((a, b) => {
      if (a.code === "unassigned") return 1
      if (b.code === "unassigned") return -1
      return a.label.localeCompare(b.label)
    })
  }, [filtered])

  const unlinkedCount = tests.filter((t) => !t.linked_asset_id).length
  const automatedCount = tests.filter((t) => t.test_type_code === "automated").length
  const linkedCount = tests.filter((t) => !!t.linked_asset_id).length
  const hasFilters = !!(search || filterAsset !== "all" || filterType || filterConnector)

  function clearFilters() {
    setSearch("")
    setFilterAsset("all")
    setFilterType("")
    setFilterConnector("")
  }

  return (
    <div className="flex-1 min-h-0 flex flex-col bg-background">

      {/* ── Header ──────────────────────────────────────────────────────────── */}
      <div className="flex items-start justify-between gap-4 px-6 pt-6 pb-4 border-b border-border">
        <div className="flex items-start gap-4 min-w-0 w-full">
          <div className="h-9 w-9 rounded-lg bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
            <Shield className="h-5 w-5 text-primary" />
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-xl font-semibold leading-tight">Control Tests</h1>
            <p className="text-xs text-muted-foreground mt-0.5">
              Automated tests promoted from Sandbox, each linked to a live data source
            </p>
          </div>
          <div className="flex items-center gap-2">
            {selectedOrgId && (
              <Button
                variant="outline"
                size="sm"
                className="gap-1.5 text-violet-600 border-violet-500/30 bg-violet-500/5 hover:bg-violet-500 hover:text-white transition-all"
                onClick={() => setShowAutoLink(true)}
              >
                <Sparkles className="h-3.5 w-3.5" />
                Auto-Link with AI
              </Button>
            )}
            {selectedOrgId && (
              <Button
                variant="outline"
                size="sm"
                className="gap-1.5 text-primary border-primary/20 bg-primary/5 hover:bg-primary hover:text-white transition-all"
                onClick={() => setGlobalLibraryOpen(true)}
              >
                <Globe className="h-3.5 w-3.5" />
                Browse Library
              </Button>
            )}
            <OrgWorkspaceSwitcher />
          </div>
        </div>
      </div>

      <div className="flex-1 min-h-0 px-6 py-6 overflow-y-auto space-y-6">
        <ReadOnlyBanner />

        {!selectedOrgId ? (
          <div className="text-center py-20 text-muted-foreground">
            <FlaskConical className="h-10 w-10 mx-auto mb-3 opacity-20" />
            <p className="text-sm font-medium">Select an organisation to view control tests.</p>
          </div>
        ) : (
          <>
            {/* ── Stats ────────────────────────────────────────────────────────── */}
            {tests.length > 0 && (
              <div className="grid gap-4 xl:grid-cols-4 md:grid-cols-2">
                <div className="rounded-xl border border-l-[3px] border-l-primary bg-card/50 shadow-sm p-5">
                  <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground">Total Tests</p>
                  <div className="mt-3 flex items-end gap-2">
                    <span className="text-3xl font-bold tabular-nums text-foreground">{tests.length}</span>
                  </div>
                  <p className="mt-2 text-[11px] text-muted-foreground">Active in environment</p>
                </div>
                <div className="rounded-xl border border-l-[3px] border-l-violet-500 bg-card/50 shadow-sm p-5">
                  <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground">Automated</p>
                  <div className="mt-3 flex items-end gap-2">
                    <span className="text-3xl font-bold tabular-nums text-violet-500">{automatedCount}</span>
                  </div>
                  <p className="mt-2 text-[11px] text-muted-foreground">Continuous monitoring</p>
                </div>
                <div className="rounded-xl border border-l-[3px] border-l-emerald-500 bg-card/50 shadow-sm p-5">
                  <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground">Linked</p>
                  <div className="mt-3 flex items-end gap-2">
                    <span className="text-3xl font-bold tabular-nums text-emerald-500">{linkedCount}</span>
                  </div>
                  <p className="mt-2 text-[11px] text-muted-foreground">Data source connection</p>
                </div>
                <div className="rounded-xl border border-l-[3px] border-l-amber-500 bg-card/50 shadow-sm p-5">
                  <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground">No Asset</p>
                  <div className="mt-3 flex items-end gap-2">
                    <span className="text-3xl font-bold tabular-nums text-amber-500">{unlinkedCount}</span>
                  </div>
                  <p className="mt-2 text-[11px] text-muted-foreground text-amber-500/80">Pending link verification</p>
                </div>
              </div>
            )}

            {/* ── Unlinked warning banner ───────────────────────────────────────── */}
            {unlinkedCount > 0 && (
              <div className="flex items-center gap-4 rounded-xl border border-amber-500/20 bg-amber-500/5 px-5 py-4 shadow-sm">
                <div className="h-10 w-10 rounded-full bg-amber-500/10 flex items-center justify-center shrink-0">
                  <AlertTriangle className="h-5 w-5 text-amber-500" />
                </div>
                <div className="flex-1 min-w-0 text-left">
                  <p className="text-sm font-bold text-foreground leading-none mb-1">
                    {unlinkedCount} test{unlinkedCount !== 1 ? "s" : ""} disconnected
                  </p>
                  <p className="text-[11px] text-muted-foreground">
                    Link a data source to enable automated execution and live session monitoring.
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="shrink-0 h-9 font-bold border-amber-500/30 text-amber-600 hover:bg-amber-500/10"
                  onClick={() => setFilterAsset("unlinked")}
                >
                  <Link2 className="h-3.5 w-3.5 mr-2" />
                  Link Sources
                </Button>
              </div>
            )}

            {/* ── Filter bar ───────────────────────────────────────────────────── */}
            <div className="flex items-center gap-3 flex-wrap">
              <div className="relative flex-1 min-w-[300px]">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
                <Input
                  placeholder="Search tests or data sources…"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-10 h-11 rounded-xl border-border/70 bg-background/80"
                />
              </div>
              <div className="flex items-center gap-2">
                <select
                  value={filterAsset}
                  onChange={(e) => setFilterAsset(e.target.value as "all" | "linked" | "unlinked")}
                  className="h-11 rounded-xl border border-border/70 bg-background/80 px-4 text-sm font-medium focus:ring-2 focus:ring-primary/20 outline-none transition-all"
                >
                  <option value="all">All Status</option>
                  <option value="linked">Asset Linked</option>
                  <option value="unlinked">No Asset</option>
                </select>
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  className="h-11 rounded-xl border border-border/70 bg-background/80 px-4 text-sm font-medium focus:ring-2 focus:ring-primary/20 outline-none transition-all"
                >
                  <option value="">All Types</option>
                  <option value="automated">Automated</option>
                  <option value="manual">On-Demand</option>
                </select>
                {connectorTypes.length > 0 && (
                  <select
                    value={filterConnector}
                    onChange={(e) => setFilterConnector(e.target.value)}
                    className="h-11 rounded-xl border border-border/70 bg-background/80 px-4 text-sm font-medium focus:ring-2 focus:ring-primary/20 outline-none transition-all"
                  >
                    <option value="">All Connectors</option>
                    {connectorTypes.map((ct) => (
                      <option key={ct} value={ct}>{getConnectorLabel(ct)}</option>
                    ))}
                  </select>
                )}
                <Button variant="outline" size="icon" onClick={load} className="h-11 w-11 rounded-xl shrink-0 border-border/70 bg-background/80">
                  <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                </Button>
                {hasFilters && (
                  <Button variant="ghost" size="sm" onClick={clearFilters} className="h-11 px-4 text-muted-foreground font-bold hover:text-primary transition-colors">
                    <X className="h-4 w-4 mr-2" />
                    Reset
                  </Button>
                )}
              </div>
            </div>

          {/* ── Loading skeletons ─────────────────────────────────────────────── */}
          {loading && (
            <div className="flex flex-col gap-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="rounded-xl border border-border bg-card h-20 animate-pulse" />
              ))}
            </div>
          )}

          {/* ── Error ────────────────────────────────────────────────────────── */}
          {!loading && error && (
            <div className="flex items-center gap-2 text-sm text-destructive py-4 px-4 bg-destructive/5 rounded-xl border border-destructive/20">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              {error}
            </div>
          )}

          {/* ── Empty state ───────────────────────────────────────────────────── */}
          {!loading && !error && filtered.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20 text-center gap-4">
              {hasFilters ? (
                <>
                  <Layers className="h-10 w-10 text-muted-foreground/30" />
                  <div>
                    <p className="text-base font-semibold text-foreground">No tests match your filters</p>
                    <p className="text-sm text-muted-foreground mt-1">Try broadening your search or clearing filters.</p>
                  </div>
                  <Button variant="outline" size="sm" onClick={clearFilters} className="gap-1.5">
                    <X className="h-3.5 w-3.5" />
                    Clear Filters
                  </Button>
                </>
              ) : (
                <>
                  {/* Empty state with a flow diagram suggestion */}
                  <div className="flex items-center gap-3 text-muted-foreground/30">
                    <FlaskConical className="h-10 w-10" />
                    <ArrowRight className="h-5 w-5" />
                    <Activity className="h-10 w-10" />
                    <ArrowRight className="h-5 w-5" />
                    <Server className="h-10 w-10" />
                  </div>
                  <div>
                    <p className="text-base font-semibold text-foreground">No control tests yet</p>
                    <p className="text-sm text-muted-foreground mt-1 max-w-sm">
                      Deploy pre-built control tests from the Global Library, or promote from the Sandbox.
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="default"
                      size="sm"
                      className="gap-1.5"
                      onClick={() => setGlobalLibraryOpen(true)}
                    >
                      <Globe className="h-4 w-4" />
                      Browse Global Library
                    </Button>
                    <Button variant="outline" size="sm" className="gap-1.5" asChild>
                      <a href="/sandbox/signals">
                        <FlaskConical className="h-4 w-4" />
                        Go to Sandbox
                      </a>
                    </Button>
                  </div>
                </>
              )}
            </div>
          )}

          {/* ── Test list ─────────────────────────────────────────────────────── */}
          {!loading && !error && filtered.length > 0 && (
            <div className="flex flex-col gap-4">
              {groupedTests.map((group) => (
                <section key={group.code} className="rounded-2xl border border-border bg-card overflow-hidden">
                  <div className="flex items-center justify-between gap-3 border-b border-border bg-muted/20 px-4 py-3">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="rounded-xl border border-border bg-background p-2">
                        <ConnectorIcon typeCode={group.code === "unassigned" ? "" : group.code} className="h-4 w-4 text-muted-foreground" />
                      </div>
                      <div className="min-w-0">
                        <h2 className="text-sm font-semibold text-foreground truncate">{group.label}</h2>
                        <p className="text-[11px] text-muted-foreground">
                          {group.code === "unassigned"
                            ? "Tests without a mapped policy container yet."
                            : "Policies and automated tests grouped by platform container."}
                        </p>
                      </div>
                    </div>
                    <div className="rounded-full border border-border bg-background px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
                      {group.tests.length} test{group.tests.length !== 1 ? "s" : ""}
                    </div>
                  </div>

                  <div className="flex flex-col gap-2 p-3">
                    {group.tests.map((test) => (
                      <ControlTestCard
                        key={test.id}
                        test={test}
                        versionHistory={histories[test.id]}
                        onLinkAsset={canEdit ? handleLinkAsset : undefined}
                        onDelete={canEdit ? (id) => setDeleteConfirm(tests.find((t) => t.id === id) ?? null) : undefined}
                        onLoadHistory={handleLoadHistory}
                        onLinkControls={canEdit && test.control_test_id ? (id) => setLinkControlsTest(tests.find((t) => t.id === id) ?? null) : undefined}
                        onRun={handleRunTest}
                        isRunning={runningTestId === test.id}
                        lastResult={testResults[test.id] ? {
                          result_status: testResults[test.id].result_status,
                          summary: testResults[test.id].summary,
                          executed_at: testResults[test.id].executed_at,
                          task_created: testResults[test.id].task_created,
                        } : undefined}
                      />
                    ))}
                  </div>
                </section>
              ))}

              <p className="text-xs text-muted-foreground text-right pt-1">
                {filtered.length} test{filtered.length !== 1 ? "s" : ""} across {groupedTests.length} container{groupedTests.length !== 1 ? "s" : ""}
                {hasFilters && ` · filtered from ${tests.length}`}
              </p>
            </div>
          )}

          {/* ── Asset selector ────────────────────────────────────────────────── */}
          {assetDialogTestId && (
            <AssetSelectorDialog
              open={!!assetDialogTestId}
              orgId={selectedOrgId}
              currentAssetId={assetDialogCurrentId}
              onSelect={handleAssetSelect}
              onClose={() => setAssetDialogTestId(null)}
            />
          )}

          {/* ── Link controls ─────────────────────────────────────────────────── */}
          {linkControlsTest && linkControlsTest.control_test_id && (
            <LinkControlsDialog
              open={!!linkControlsTest}
              testId={linkControlsTest.control_test_id}
              testName={linkControlsTest.name || linkControlsTest.test_code}
              orgId={selectedOrgId}
              workspaceId={selectedWorkspaceId}
              onClose={() => setLinkControlsTest(null)}
            />
          )}

          {/* ── Delete confirm ────────────────────────────────────────────────── */}
          <Dialog open={!!deleteConfirm} onOpenChange={(v) => !v && setDeleteConfirm(null)}>
            <DialogContent className="max-w-sm">
              <DialogHeader>
                <DialogTitle>Remove Control Test</DialogTitle>
                <DialogDescription>
                  Remove &ldquo;{deleteConfirm?.name || deleteConfirm?.test_code}&rdquo; from active tests?
                  Version history is preserved.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <Button variant="outline" onClick={() => setDeleteConfirm(null)}>Cancel</Button>
                <Button
                  variant="destructive"
                  disabled={deleting}
                  onClick={() => deleteConfirm && handleDelete(deleteConfirm)}
                >
                  {deleting ? "Removing…" : "Remove"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
          {/* ── Auto-Link with AI ──────────────────────────────────────── */}
          {showAutoLink && selectedOrgId && (
            <AutoLinkTestsModal
              open={showAutoLink}
              orgId={selectedOrgId}
              workspaceId={selectedWorkspaceId}
              onClose={() => setShowAutoLink(false)}
            />
          )}

          {/* ── Global Library Dialog ────────────────────────────────────── */}
          {globalLibraryOpen && selectedOrgId && (
            <GlobalLibraryDialog
              open={globalLibraryOpen}
              orgId={selectedOrgId}
              workspaceId={selectedWorkspaceId}
              connectorInstanceId={searchParams.get("connector")}
              lockedConnectorType={searchParams.get("connector_type")}
              onDeployed={load}
              onClose={() => setGlobalLibraryOpen(false)}
            />
          )}
        </>
      )}
      </div>
    </div>
  )
}
