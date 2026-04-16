"use client"

import { useState, useEffect, useRef } from "react"
import { useSearchParams } from "next/navigation"
import { useOrgWorkspace } from "@/lib/context/OrgWorkspaceContext"
import {
  createBuilderSession,
  listBuilderSessions,
  getBuilderSession,
  patchBuilderSession,
  enqueueBuilderHierarchy,
  enqueueBuilderControls,
  enqueueFrameworkCreation,
  enqueueBuilderEnhanceDiff,
  applyBuilderEnhancements,
  enqueueGapAnalysis,
  getBuilderSessionJob,
  getBuilderJob,
  uploadBuilderAttachment,
  type BuilderSession,
  type BuildJobStatus,
  type GapAnalysisReport,
} from "@/lib/api/ai"
import { listFrameworks } from "@/lib/api/grc"
import type { FrameworkResponse } from "@/lib/types/grc"
import type { HierarchyNode, ChangeProposal } from "@/components/grc/FrameworkHierarchyTree"
import type { ProgressEvent } from "@/components/grc/BuildProgressFeed"

// ── Types ──────────────────────────────────────────────────────────────────────

export type PagePhase =
  | "idle"
  | "phase1_streaming"
  | "phase1_review"
  | "phase2_streaming"
  | "phase2_review"
  | "creating"
  | "enhance_applying"
  | "enhance_complete"
  | "complete"
  | "failed"

export type ActiveTab = "build" | "enhance" | "gap"

export type Phase2Stats = {
  control_count: number
  risk_count: number
  risk_mapping_count: number
  unmapped_control_count: number
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useBuilder() {
  const searchParams = useSearchParams()
  const { selectedOrgId, selectedWorkspaceId, ready } = useOrgWorkspace()

  // ── Tab / phase state ──────────────────────────────────────────────────────
  const [activeTab, setActiveTab] = useState<ActiveTab>("build")
  const [phase, setPhase] = useState<PagePhase>("idle")

  // ── Session state ──────────────────────────────────────────────────────────
  const [sessions, setSessions] = useState<BuilderSession[]>([])
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null)

  // ── Build form state ───────────────────────────────────────────────────────
  const [frameworkName, setFrameworkName] = useState("")
  const [frameworkType, setFrameworkType] = useState("it_cyber")
  const [categoryCode, setCategoryCode] = useState("security")
  const [userContext, setUserContext] = useState("")
  const [attachmentIds, setAttachmentIds] = useState<string[]>([])
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([])
  const [dragOver, setDragOver] = useState(false)

  // ── Hierarchy state ────────────────────────────────────────────────────────
  const [hierarchyNodes, setHierarchyNodes] = useState<HierarchyNode[]>([])
  const [selectedCode, setSelectedCode] = useState<string | null>(null)
  const [nodeOverrides, setNodeOverrides] = useState<Record<string, string>>({})

  // ── Progress feed state ────────────────────────────────────────────────────
  const [feedEvents, setFeedEvents] = useState<ProgressEvent[]>([])
  const [isStreaming, setIsStreaming] = useState(false)

  // ── Phase stats ────────────────────────────────────────────────────────────
  const [phase1Stats, setPhase1Stats] = useState<{ requirement_count: number } | null>(null)
  const [phase2Stats, setPhase2Stats] = useState<Phase2Stats | null>(null)
  const [resultFrameworkId, setResultFrameworkId] = useState<string | null>(null)
  const [buildCreateApproved, setBuildCreateApproved] = useState(false)

  // ── Enhance tab state ──────────────────────────────────────────────────────
  const [proposals, setProposals] = useState<ChangeProposal[]>([])
  const [enhanceFrameworkId, setEnhanceFrameworkId] = useState<string | null>(null)
  const [enhanceContext, setEnhanceContext] = useState("")
  const [enhanceApplyApproved, setEnhanceApplyApproved] = useState(false)
  const [enhanceAppliedCount, setEnhanceAppliedCount] = useState<number | null>(null)
  const [enhanceApplyStats, setEnhanceApplyStats] = useState<{
    requested_count: number
    applied_count: number
    failed_count: number
  } | null>(null)
  const [availableFrameworks, setAvailableFrameworks] = useState<FrameworkResponse[]>([])
  const [loadingFrameworks, setLoadingFrameworks] = useState(false)
  const [enhanceUserContext, setEnhanceUserContext] = useState("")
  const [enhanceUploadedFiles, setEnhanceUploadedFiles] = useState<File[]>([])
  const [enhanceDragOver, setEnhanceDragOver] = useState(false)
  const [enhanceUploading, setEnhanceUploading] = useState(false)

  // ── Gap analysis state ─────────────────────────────────────────────────────
  const [gapFrameworkId, setGapFrameworkId] = useState<string | null>(null)
  const [gapReport, setGapReport] = useState<GapAnalysisReport | null>(null)
  const [gapPolling, setGapPolling] = useState(false)
  const [gapUserContext, setGapUserContext] = useState("")
  const [gapUploadedFiles, setGapUploadedFiles] = useState<File[]>([])
  const [gapDragOver, setGapDragOver] = useState(false)
  const [gapUploading, setGapUploading] = useState(false)
  const [gapJobId, setGapJobId] = useState<string | null>(null)

  // ── Cherry-pick selection (controls/requirements to include in commit) ────
  // Set of codes (req + control) the user wants to include. Initialised with
  // ALL codes when entering phase2_review so everything is checked by default.
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set())

  // ── refs ───────────────────────────────────────────────────────────────────
  const pollingRef = useRef<NodeJS.Timeout | null>(null)
  const pollingActiveRef = useRef<boolean>(false)
  const abortRef = useRef<AbortController | null>(null)
  const hydratedSessionRef = useRef<string | null>(null)
  const activeSessionIdRef = useRef<string | null>(null)
  const sessionsRef = useRef<BuilderSession[]>([])

  // ── Toast proxy ────────────────────────────────────────────────────────────
  const toast = {
    error: (msg: string) => console.error("[toast]", msg),
    success: (msg: string) => console.info("[toast]", msg),
  }

  // ── Sync refs ──────────────────────────────────────────────────────────────
  useEffect(() => {
    activeSessionIdRef.current = activeSessionId
  }, [activeSessionId])

  useEffect(() => {
    sessionsRef.current = sessions
  }, [sessions])

  // ── Initial load ───────────────────────────────────────────────────────────
  useEffect(() => {
    if (ready && selectedOrgId && selectedWorkspaceId) {
      void loadSessions()
    }
  }, [ready, selectedOrgId, selectedWorkspaceId])

  useEffect(() => {
    if (activeTab === "enhance" || activeTab === "gap") {
      if (availableFrameworks.length === 0) fetchFrameworks()
    }
  }, [activeTab])

  useEffect(() => {
    return () => {
      abortRef.current?.abort()
      if (pollingRef.current) clearInterval(pollingRef.current)
    }
  }, [])

  // ── URL synchronization ────────────────────────────────────────────────────
  useEffect(() => {
    const tab = searchParams.get("builderTab") ?? searchParams.get("tab")
    if (tab === "build" || tab === "enhance" || tab === "gap") {
      setActiveTab(tab as ActiveTab)
    }

    const enhance = searchParams.get("enhance")
    if (enhance) {
      setActiveTab("enhance")
      setEnhanceFrameworkId(enhance)
    }

    // Gap analysis URL sync
    const gapFramework = searchParams.get("gapFramework")
    if (gapFramework) {
      setActiveTab("gap")
      setGapFrameworkId(gapFramework)
    }
  }, [searchParams])

  useEffect(() => {
    const sessionId = searchParams.get("session")
    if (!sessionId) return
    if (hydratedSessionRef.current === sessionId) return

    let cancelled = false
    void (async () => {
      try {
        // Read sessions from ref — avoids making `sessions` a reactive dep
        const existing = sessionsRef.current.find((s) => s.id === sessionId)
        const session = existing ?? (await getBuilderSession(sessionId))
        if (cancelled) return
        hydratedSessionRef.current = sessionId
        await hydrateFromSession(session)
        if (!existing) {
          setSessions((prev) => [session, ...prev.filter((s) => s.id !== session.id)])
        }
      } catch (err) {
        if (!cancelled) {
          console.error("Failed to hydrate builder session from URL", err)
        }
      }
    })()

    return () => {
      cancelled = true
    }
  // Only re-run when the URL changes, NOT on every sessions state update
  }, [searchParams])

  // ── Actions ────────────────────────────────────────────────────────────────

  async function loadSessions() {
    if (!selectedOrgId || !selectedWorkspaceId) return
    try {
      const res = await listBuilderSessions({
        org_id: selectedOrgId,
        workspace_id: selectedWorkspaceId,
        limit: 20
      })
      setSessions(res.items)
      // Only auto-resume if the URL explicitly references a session (?session=...).
      // Default navigation to /frameworks/builder/ always starts with a fresh form.
      if (!activeSessionIdRef.current && searchParams.get("session")) {
        const activeStatuses = new Set([
          "phase1_streaming", "phase2_streaming", "creating",
          "phase1_review", "phase2_review",
        ])
        const inProgress = res.items.find(s => activeStatuses.has(s.status))
        if (inProgress) await hydrateFromSession(inProgress)
      }
    } catch (err) {
      console.error("Failed to load builder sessions", err)
    }
  }

  async function fetchFrameworks() {
    if (!selectedOrgId) return
    setLoadingFrameworks(true)
    try {
      const res = await listFrameworks({
        scope_org_id: selectedOrgId,
        ...(selectedWorkspaceId ? { scope_workspace_id: selectedWorkspaceId } : {}),
      })
      setAvailableFrameworks((res.items ?? []).filter(f => f.scope_org_id && f.scope_workspace_id))
    } catch {
      toast.error("Failed to load frameworks")
    } finally {
      setLoadingFrameworks(false)
    }
  }

  async function hydrateFromSession(session: BuilderSession) {
    setActiveSessionId(session.id)
    // If session is phase1_review but already has controls, skip to phase2_review
    const hasControls = Array.isArray(session.proposed_controls) && session.proposed_controls.length > 0
    const mappedPhase = session.status === "phase1_review" && hasControls && session.session_type === "create"
      ? "phase2_review" as PagePhase
      : mapSessionStatusToPhase(session.status, session.session_type)
    setPhase(mappedPhase)
    setBuildCreateApproved(false)
    setEnhanceApplyApproved(false)

    const isEnhanceSession = session.session_type === "enhance"
    const isGapSession = session.session_type === "gap"
    setActiveTab(isEnhanceSession ? "enhance" : isGapSession ? "gap" : "build")
    setFrameworkName(session.framework_name ?? "")
    setFrameworkType(session.framework_type_code ?? "custom")
    setCategoryCode(session.framework_category_code ?? "security")
    setUserContext(session.user_context ?? "")
    setAttachmentIds(session.attachment_ids ?? [])
    setNodeOverrides(session.node_overrides ?? {})
    setResultFrameworkId(session.result_framework_id ?? null)

    // Restore persisted activity log so past build events survive navigation
    const persistedLog = Array.isArray(session.activity_log) ? session.activity_log : []
    setFeedEvents(persistedLog as ProgressEvent[])

    if (isEnhanceSession) {
      setEnhanceFrameworkId(session.framework_id)
      setProposals(parseSessionProposals(session.enhance_diff))
      setHierarchyNodes([])
      setPhase1Stats(null)
      setPhase2Stats(null)
    } else if (isGapSession) {
      // Gap analysis session - restore gap framework ID
      setGapFrameworkId(session.framework_id)
      // Check if there's a completed report in activity log
      const completedEvent = session.activity_log?.find(
        (e: any) => e.event === "gap_analysis_complete"
      )
      if (completedEvent?.report) {
        setGapReport(completedEvent.report as unknown as GapAnalysisReport)
      }
    } else {
      const nodes = buildHierarchyNodesFromSession(session.proposed_hierarchy, session.proposed_controls)
      const riskCoverage = computeRiskCoverageStats(session.proposed_controls, session.proposed_risk_mappings)
      setHierarchyNodes(nodes)
      setProposals([])
      setPhase1Stats(nodes.length > 0 ? { requirement_count: nodes.length } : null)
      setPhase2Stats({
        control_count: Array.isArray(session.proposed_controls) ? session.proposed_controls.length : 0,
        risk_count: Array.isArray(session.proposed_risks) ? session.proposed_risks.length : 0,
        risk_mapping_count: riskCoverage.risk_mapping_count,
        unmapped_control_count: riskCoverage.unmapped_control_count,
      })
      // Init cherry-pick: all codes selected by default when hydrating a phase2+ session
      if (Array.isArray(session.proposed_controls) && session.proposed_controls.length > 0) {
        const allCodes = new Set<string>()
        for (const n of nodes) {
          allCodes.add(n.code)
          for (const c of n.controls ?? []) allCodes.add(c.code)
        }
        setSelectedItems(allCodes)
      }
    }

    // Resume polling for any in-progress background jobs
    const needsPolling =
      (session.status === "creating") ||
      (session.status === "phase1_streaming" && !!session.job_id) ||
      (session.status === "phase2_streaming" && !!session.job_id) ||
      (isGapSession && session.job_id && session.status !== "complete" && session.status !== "completed")
    if (needsPolling && !pollingActiveRef.current) {
      setIsStreaming(true)
      if (isGapSession && session.job_id) {
        setGapFrameworkId(session.framework_id)
        setGapJobId(session.job_id)
        setGapPolling(true)
        // If job is already complete, get the report; otherwise poll
        if (session.status === "complete" || session.status === "completed") {
          try {
            const job = await getBuilderJob(session.job_id)
            if (job.stats) {
              setGapReport(job.stats as unknown as GapAnalysisReport)
            }
          } catch (e) {
            console.error("Failed to fetch gap report:", e)
          }
          setGapPolling(false)
        } else {
          pollGapJob(session.job_id)
        }
      } else {
        startPollingJob(session.id)
      }
    }
  }

  function resetBuildState() {
    setPhase("idle")
    setActiveTab("build")
    setActiveSessionId(null)
    setHierarchyNodes([])
    setSelectedCode(null)
    setNodeOverrides({})
    setFeedEvents([])
    setIsStreaming(false)
    setPhase1Stats(null)
    setPhase2Stats(null)
    setResultFrameworkId(null)
    setBuildCreateApproved(false)
    setFrameworkName("")
    setFrameworkType("custom")
    setCategoryCode("security")
    setUserContext("")
    setUploadedFiles([])
    setAttachmentIds([])
    setProposals([])
    setEnhanceFrameworkId(null)
    setEnhanceContext("")
    setEnhanceApplyApproved(false)
    setEnhanceAppliedCount(null)
    setEnhanceApplyStats(null)
    setEnhanceUserContext("")
    setEnhanceUploadedFiles([])
    setGapFrameworkId(null)
    setGapReport(null)
    setGapJobId(null)
    setGapPolling(false)
    setGapUserContext("")
    setGapUploadedFiles([])
    abortRef.current?.abort()
    if (pollingRef.current) clearInterval(pollingRef.current)
  }

  async function handleProposeStructure() {
    if (!frameworkName.trim()) {
      toast.error("Framework name is required")
      return
    }
    setFeedEvents([])
    setHierarchyNodes([])
    setPhase1Stats(null)
    setPhase2Stats(null)
    setResultFrameworkId(null)
    setBuildCreateApproved(false)

    try {
      let sessionId = activeSessionId
      if (!sessionId) {
        if (!selectedOrgId || !selectedWorkspaceId) {
          toast.error("Organization and workspace scope required")
          return
        }

        // Upload any staged files to get attachment IDs before creating session
        let resolvedAttachmentIds = [...attachmentIds]
        if (uploadedFiles.length > 0) {
          const uploaded = await uploadFilesForSession(uploadedFiles)
          resolvedAttachmentIds = [...resolvedAttachmentIds, ...uploaded]
          setAttachmentIds(resolvedAttachmentIds)
          setUploadedFiles([])
        }

        const session = await createBuilderSession({
          session_type: "create",
          framework_name: frameworkName.trim(),
          framework_type_code: frameworkType,
          framework_category_code: categoryCode,
          user_context: userContext.trim() || undefined,
          attachment_ids: resolvedAttachmentIds.length > 0 ? resolvedAttachmentIds : undefined,
          scope_org_id: selectedOrgId,
          scope_workspace_id: selectedWorkspaceId,
        })
        sessionId = session.id
        setActiveSessionId(sessionId)
        setSessions(prev => [session, ...prev])
      } else {
        await patchBuilderSession(sessionId, {
          framework_name: frameworkName.trim(),
          framework_type_code: frameworkType,
          framework_category_code: categoryCode,
          user_context: userContext.trim() || undefined,
          attachment_ids: attachmentIds.length > 0 ? attachmentIds : undefined,
        })
      }

      setPhase("phase1_streaming")
      setIsStreaming(true)

      // Enqueue as async background job — survives navigation
      const job = await enqueueBuilderHierarchy(sessionId)
      toast.success("Hierarchy generation started — you can navigate away safely")
      startPollingJob(sessionId, job)
    } catch (err: any) {
      toast.error(`Build failed: ${err.message}`)
      setPhase("failed")
      setIsStreaming(false)
    }
  }

  async function handleGenerateControls() {
    if (!activeSessionId) return
    setBuildCreateApproved(false)
    setPhase("phase2_streaming")
    setIsStreaming(true)
    setPhase2Stats(null)
    setFeedEvents([])

    try {
      if (Object.keys(nodeOverrides).length > 0) {
        await patchBuilderSession(activeSessionId, { node_overrides: nodeOverrides })
      }
      // Enqueue as async background job — survives navigation
      const job = await enqueueBuilderControls(activeSessionId)
      toast.success("Control generation started — you can navigate away safely")
      startPollingJob(activeSessionId, job)
    } catch (err: any) {
      toast.error(`Control generation failed: ${err.message}`)
      setPhase("phase1_review")
      setIsStreaming(false)
    }
  }

  async function handleCreateFramework() {
    if (!activeSessionId) return
    try {
      setPhase("creating")
      setFeedEvents([])
      const job = await enqueueFrameworkCreation(activeSessionId)
      toast.success("Build job enqueued! Cataloging framework…")
      startPollingJob(activeSessionId, job)
    } catch (err: any) {
      toast.error(`Creation failed: ${err.message}`)
      setPhase("failed")
    }
  }

  async function uploadFilesForSession(files: File[]): Promise<string[]> {
    if (files.length === 0) return []
    setEnhanceUploading(true)
    try {
      const results = await Promise.allSettled(files.map(f => uploadBuilderAttachment(f)))
      const ids: string[] = []
      for (const r of results) {
        if (r.status === "fulfilled" && r.value.status_code === "ready") {
          ids.push(r.value.id)
        } else if (r.status === "rejected") {
          console.error("[builder] file upload failed:", r.reason)
        }
      }
      return ids
    } finally {
      setEnhanceUploading(false)
    }
  }

  async function handleAnalyzeEnhance() {
    if (!enhanceFrameworkId) {
      toast.error("Select a framework to enhance")
      return
    }
    setActiveTab("enhance")
    setPhase("phase1_streaming")
    setEnhanceAppliedCount(null)
    setEnhanceApplyStats(null)
    setProposals([])
    setFeedEvents([])
    setIsStreaming(true)
    setEnhanceApplyApproved(false)

    try {
      if (!selectedOrgId || !selectedWorkspaceId) {
        toast.error("Organization and workspace scope required")
        setPhase("idle")
        return
      }

      // Upload any staged files before creating session
      const uploadedAttachmentIds = await uploadFilesForSession(enhanceUploadedFiles)

      const session = await createBuilderSession({
        session_type: "enhance",
        framework_id: enhanceFrameworkId,
        user_context: enhanceUserContext.trim() || undefined,
        attachment_ids: uploadedAttachmentIds.length > 0 ? uploadedAttachmentIds : undefined,
        scope_org_id: selectedOrgId,
        scope_workspace_id: selectedWorkspaceId,
      })
      setActiveSessionId(session.id)
      setSessions(prev => [session, ...prev])

      // Enqueue as background job — survives navigation, no SSE dependency
      const job = await enqueueBuilderEnhanceDiff(session.id)
      startPollingJob(session.id, job)
    } catch (err: any) {
      toast.error(`Enhance failed: ${err.message}`)
      setPhase("idle")
      setIsStreaming(false)
    }
  }

  async function handleApplyEnhancements(accepted: ChangeProposal[]) {
    if (!activeSessionId) return
    if (!enhanceApplyApproved) {
      toast.error("Approve the accepted enhancement set before applying")
      return
    }
    if (accepted.length === 0) {
      toast.error("Select at least one enhancement to apply")
      return
    }
    try {
      setPhase("enhance_applying")
      setEnhanceAppliedCount(null)
      setEnhanceApplyStats(null)
      setFeedEvents([])
      const job = await applyBuilderEnhancements(activeSessionId, accepted)
      toast.success(`Applying ${accepted.length} changes…`)
      startPollingJob(activeSessionId, job)
    } catch (err: any) {
      toast.error(`Apply failed: ${err.message}`)
      setPhase("failed")
    }
  }

  async function handleRunGapAnalysis() {
    if (!gapFrameworkId) {
      toast.error("Select a framework for gap analysis")
      return
    }
    setGapPolling(true)
    setGapReport(null)
    setGapJobId(null)
    try {
      // Upload any staged files (audit reports, test results, etc.)
      let attachmentIds: string[] = []
      if (gapUploadedFiles.length > 0) {
        setGapUploading(true)
        attachmentIds = await uploadFilesForSession(gapUploadedFiles)
        setGapUploading(false)
      }
      const job = await enqueueGapAnalysis(gapFrameworkId, {
        user_context: gapUserContext.trim() || undefined,
        attachment_ids: attachmentIds.length > 0 ? attachmentIds : undefined,
      })
      setGapJobId(job.job_id)
      pollGapJob(job.job_id)
    } catch (err: any) {
      toast.error(`Gap analysis failed: ${err.message}`)
      setGapPolling(false)
      setGapUploading(false)
    }
  }

  // ── Resume gap analysis on mount ─────────────────────────────────────────
  useEffect(() => {
    const gapJob = searchParams.get("gapJob")
    if (gapJob && !gapPolling && !gapReport) {
      setGapJobId(gapJob)
      setGapPolling(true)
      pollGapJob(gapJob)
    }
  }, [])

  // ── Polling (Internal) ─────────────────────────────────────────────────────

  async function startPollingJob(sessionId: string, initialJob?: BuildJobStatus) {
    // If a new job is explicitly provided, force-stop any existing poll loop so
    // we switch to polling the new job_id immediately.
    if (initialJob) {
      pollingActiveRef.current = false
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
        pollingRef.current = null
      }
    }
    if (pollingActiveRef.current) return   // guard: never start a second poll loop
    if (pollingRef.current) clearInterval(pollingRef.current)
    let currentJobId = initialJob?.job_id
    if (!currentJobId) {
      try {
        const job = await getBuilderSessionJob(sessionId)
        currentJobId = job.job_id
      } catch {
        return
      }
    }
    if (!currentJobId) return

    pollingActiveRef.current = true

    const stopPolling = () => {
      pollingActiveRef.current = false
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
        pollingRef.current = null
      }
    }

    const poll = async () => {
      try {
        const job = await getBuilderJob(currentJobId!)
        handleJobEvent(job, sessionId)
        if (job.status === "completed" || job.status === "failed") {
          stopPolling()
          // Only refresh the sidebar list — do NOT call hydrateFromSession (would restart polling)
          await syncSessionState(sessionId)
        }
      } catch {
        stopPolling()
      }
    }
    void poll()
    pollingRef.current = setInterval(poll, 2500)
  }

  function handleCancelApply() {
    // Stop any in-flight SSE stream
    abortRef.current?.abort()
    // Stop the job-status polling loop
    pollingActiveRef.current = false
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
    // Revert UI back to the enhance review state so user can retry
    setPhase("phase2_review")
    setIsStreaming(false)
    setFeedEvents([])
  }

  function handleJobEvent(job: BuildJobStatus, sessionId: string) {
    if (activeSessionIdRef.current !== sessionId) return
    // Merge job creation_log with existing SSE events (keep SSE history, append/replace job events)
    if (job.creation_log && job.creation_log.length > 0) {
      setFeedEvents(prev => {
        const sseEvents = prev.filter(e => !(e as any).__job)
        const jobEvents = (job.creation_log as ProgressEvent[]).map(e => ({ ...e, __job: true }))
        return [...sseEvents, ...jobEvents]
      })
    }
    if (job.status === "completed") {
      if (job.job_type === "framework_apply_changes") {
        setPhase("enhance_complete")
        const stats = job.stats as any
        setEnhanceAppliedCount(stats?.applied_count ?? null)
        setEnhanceApplyStats(stats ?? null)
        if (job.framework_id) setResultFrameworkId(job.framework_id)
      } else if (job.job_type === "framework_enhance_diff") {
        // Diff proposals are now saved to session — fetch session and move to review
        void syncAndHydrateSession(sessionId).then(() => {
          setIsStreaming(false)
          setPhase("phase2_review")
        })
      } else if (job.job_type === "framework_hierarchy") {
        // Phase 1 complete — session now has proposed_hierarchy, hydrate and move to review
        void syncAndHydrateSession(sessionId).then(() => {
          setIsStreaming(false)
        })
      } else if (job.job_type === "framework_controls") {
        // Phase 2 complete — session now has proposed_controls/risks, hydrate and move to review
        void syncAndHydrateSession(sessionId).then(() => {
          setIsStreaming(false)
        })
      } else {
        setPhase("complete")
        if (job.framework_id) setResultFrameworkId(job.framework_id)
      }
      // syncSessionState will refresh the sidebar list (called from the poll loop)
    } else if (job.status === "failed") {
      setPhase("failed")
      if (job.error_message) {
        setFeedEvents(prev => [...prev, { event: "creation_error", stage: "job", message: job.error_message } as ProgressEvent])
      }
      // syncSessionState will refresh the sidebar list (called from the poll loop)
    }
  }

  async function pollGapJob(jobId: string) {
    const poll = async () => {
      try {
        const job = await getBuilderJob(jobId)
        // Show live progress events from creation_log in the activity panel
        if (job.creation_log && job.creation_log.length > 0) {
          setFeedEvents(
            (job.creation_log as ProgressEvent[]).map(e => ({ ...e, __job: true }))
          )
        }
        if (job.status === "completed") {
          setGapReport((job.stats as unknown as GapAnalysisReport | null) ?? null)
          setGapPolling(false)
          return true
        }
        if (job.status === "failed") {
          toast.error(`Gap analysis failed: ${job.error_message || "Unknown error"}`)
          setGapPolling(false)
          return true
        }
      } catch {
        setGapPolling(false)
        return true
      }
      return false
    }
    const finished = await poll()
    if (!finished) {
      const interval = setInterval(async () => {
        if (await poll()) clearInterval(interval)
      }, 2000)
    }
  }

  async function syncSessionState(sessionId: string) {
    try {
      const latest = await getBuilderSession(sessionId)
      // Always refresh the sidebar session list
      setSessions((prev) => [latest, ...prev.filter((s) => s.id !== latest.id)])
      // Only do a full UI hydration when the user explicitly selected/navigated to
      // this session — NOT after job completion, to avoid restarting the poll loop.
    } catch (err) {
      console.error("Failed to refresh builder session state", err)
    }
  }

  async function syncAndHydrateSession(sessionId: string) {
    try {
      const latest = await getBuilderSession(sessionId)
      setSessions((prev) => [latest, ...prev.filter((s) => s.id !== latest.id)])
      if (activeSessionIdRef.current === sessionId) await hydrateFromSession(latest)
    } catch (err) {
      console.error("Failed to refresh builder session state", err)
    }
  }

  return {
    // State
    ready,
    selectedOrgId,
    selectedWorkspaceId,
    activeTab,
    setActiveTab,
    phase,
    setPhase,
    sessions,
    activeSessionId,
    setActiveSessionId,
    frameworkName,
    setFrameworkName,
    frameworkType,
    setFrameworkType,
    categoryCode,
    setCategoryCode,
    userContext,
    setUserContext,
    attachmentIds,
    setAttachmentIds,
    uploadedFiles,
    setUploadedFiles,
    dragOver,
    setDragOver,
    hierarchyNodes,
    setHierarchyNodes,
    selectedCode,
    setSelectedCode,
    nodeOverrides,
    setNodeOverrides,
    feedEvents,
    setFeedEvents,
    isStreaming,
    phase1Stats,
    phase2Stats,
    resultFrameworkId,
    buildCreateApproved,
    setBuildCreateApproved,
    proposals,
    setProposals,
    enhanceFrameworkId,
    setEnhanceFrameworkId,
    enhanceContext,
    setEnhanceContext,
    enhanceApplyApproved,
    setEnhanceApplyApproved,
    enhanceAppliedCount,
    enhanceApplyStats,
    availableFrameworks,
    loadingFrameworks,
    enhanceUserContext,
    setEnhanceUserContext,
    enhanceUploadedFiles,
    setEnhanceUploadedFiles,
    enhanceDragOver,
    setEnhanceDragOver,
    enhanceUploading,
    gapFrameworkId,
    setGapFrameworkId,
    gapReport,
    gapPolling,
    gapUserContext,
    setGapUserContext,
    gapUploadedFiles,
    setGapUploadedFiles,
    gapDragOver,
    setGapDragOver,
    gapUploading,
    gapJobId,

    // Actions
    loadSessions,
    resetBuildState,
    handleProposeStructure,
    handleGenerateControls,
    handleCreateFramework,
    handleAnalyzeEnhance,
    handleApplyEnhancements,
    handleCancelApply,
    handleRunGapAnalysis,
    hydrateFromSession,
    acceptAllProposals: () => {
      setEnhanceApplyApproved(false)
      setProposals(prev => prev.map(p => ({ ...p, accepted: true })))
    },
    rejectAllProposals: () => {
      setEnhanceApplyApproved(false)
      setProposals(prev => prev.map(p => ({ ...p, accepted: false })))
    },
    toggleProposal: (index: number, accepted: boolean) => {
      setEnhanceApplyApproved(false)
      setProposals(prev => prev.map((p, i) => i === index ? { ...p, accepted } : p))
    },

    // Cherry-pick selection with cascading:
    // - Unchecking a requirement unchecks all its descendants + their controls
    // - Checking a control auto-checks its parent requirement chain upward
    selectedItems,
    toggleItem: (code: string) => {
      setSelectedItems(prev => {
        const next = new Set(prev)
        const adding = !next.has(code)

        // Check if this code is a control (exists on some node's controls list)
        const isControl = hierarchyNodes.some(n => n.controls?.some(c => c.code === code))

        if (isControl) {
          if (adding) {
            // Select the control
            next.add(code)
            // Auto-select the parent requirement and all ancestors
            const ownerNode = hierarchyNodes.find(n => n.controls?.some(c => c.code === code))
            if (ownerNode) {
              next.add(ownerNode.code)
              // Walk up the parent chain
              let parentCode = ownerNode.parent_code
              while (parentCode) {
                next.add(parentCode)
                const parent = hierarchyNodes.find(n => n.code === parentCode)
                parentCode = parent?.parent_code ?? null
              }
            }
          } else {
            next.delete(code)
          }
        } else {
          // It's a requirement node — cascade to all descendants + their controls
          const codesToToggle = new Set<string>([code])
          const addDescendants = (parentCode: string) => {
            for (const n of hierarchyNodes) {
              if (n.parent_code === parentCode) {
                codesToToggle.add(n.code)
                for (const c of n.controls ?? []) codesToToggle.add(c.code)
                addDescendants(n.code)
              }
            }
          }
          addDescendants(code)
          // Also add controls directly on this node
          const thisNode = hierarchyNodes.find(n => n.code === code)
          if (thisNode) {
            for (const c of thisNode.controls ?? []) codesToToggle.add(c.code)
          }
          for (const c of codesToToggle) {
            if (adding) next.add(c)
            else next.delete(c)
          }
        }

        return next
      })
    },

    // Inline edit handlers — mutate local hierarchy state
    editNode: (code: string, field: "name" | "description", value: string) => {
      setHierarchyNodes(prev => prev.map(n =>
        n.code === code ? { ...n, [field]: value } : n
      ))
    },
    editControl: (code: string, field: "name" | "description" | "guidance" | "implementation_guidance", value: string | string[]) => {
      setHierarchyNodes(prev => prev.map(n => ({
        ...n,
        controls: n.controls?.map(c =>
          c.code === code ? { ...c, [field]: value } : c
        )
      })))
    },
  }
}

// ── Shared Helpers ──────────────────────────────────────────────────────────

function mapSessionStatusToPhase(
  status: string,
  sessionType: "create" | "enhance" | "gap",
): PagePhase {
  if (status === "failed") return "failed"
  if (status === "creating") return sessionType === "enhance" ? "enhance_applying" : "creating"
  if (status === "complete" || status === "completed") {
    return sessionType === "enhance" ? "enhance_complete" : "complete"
  }
  if (status === "phase2_review") return "phase2_review"
  if (status === "phase1_review") return sessionType === "enhance" ? "phase2_review" : "phase1_review"
  // Streaming statuses now mean a background job is running — resume polling
  if (status === "phase2_streaming") return "phase2_streaming"
  if (status === "phase1_streaming") return "phase1_streaming"
  return "idle"
}

function parseSessionProposals(raw: unknown[] | null): ChangeProposal[] {
  if (!Array.isArray(raw)) return []
  return raw
    .filter((item): item is Record<string, unknown> => !!item && typeof item === "object")
    .map((item) => ({
      change_type: String(item.change_type ?? ""),
      entity_type: String(item.entity_type ?? ""),
      entity_id: item.entity_id === null || typeof item.entity_id === "string" ? item.entity_id : null,
      entity_code: String(item.entity_code ?? ""),
      field: String(item.field ?? ""),
      current_value: item.current_value,
      proposed_value: item.proposed_value,
      reason: String(item.reason ?? ""),
      accepted: item.accepted === false ? false : true,
    }))
    .filter((item) => item.change_type.length > 0)
}

function normalizeCode(value: unknown): string {
  return String(value ?? "").trim().toUpperCase()
}

function computeRiskCoverageStats(
  controls: unknown[] | null | undefined,
  mappings: unknown[] | null | undefined,
): Pick<Phase2Stats, "risk_mapping_count" | "unmapped_control_count"> {
  const controlCodes = new Set<string>()
  if (Array.isArray(controls)) {
    for (const control of controls) {
      if (!control || typeof control !== "object") continue
      const code = normalizeCode((control as Record<string, unknown>).control_code)
      if (code) controlCodes.add(code)
    }
  }

  const mappedControlCodes = new Set<string>()
  let mappingCount = 0
  if (Array.isArray(mappings)) {
    for (const mapping of mappings) {
      if (!mapping || typeof mapping !== "object") continue
      const controlCode = normalizeCode((mapping as Record<string, unknown>).control_code)
      const riskCode = normalizeCode((mapping as Record<string, unknown>).risk_code)
      if (!controlCode || !riskCode) continue
      mappingCount += 1
      mappedControlCodes.add(controlCode)
    }
  }

  let unmapped = 0
  for (const controlCode of controlCodes) {
    if (!mappedControlCodes.has(controlCode)) unmapped += 1
  }

  return {
    risk_mapping_count: mappingCount,
    unmapped_control_count: unmapped,
  }
}

function buildHierarchyNodesFromSession(
  hierarchy: Record<string, unknown> | null,
  controls: unknown[] | null,
): HierarchyNode[] {
  if (!hierarchy) return []

  const requirements = Array.isArray(hierarchy.requirements)
    ? (hierarchy.requirements as any[])
    : []

  const controlMap = new Map<string, HierarchyNode["controls"]>()
  if (Array.isArray(controls)) {
    for (const raw of controls as any[]) {
      const reqCode = raw.requirement_code
      const ctrlCode = raw.control_code ?? raw.code
      if (!reqCode || !ctrlCode || !raw.name) continue
      const list = controlMap.get(reqCode) ?? []
      list.push({
        code: ctrlCode,
        name: raw.name,
        description: raw.description ?? undefined,
        guidance: raw.guidance ?? undefined,
        implementation_guidance: Array.isArray(raw.implementation_guidance) ? raw.implementation_guidance : undefined,
        requirement_code: reqCode,
        criticality: String(raw.criticality ?? raw.criticality_code ?? "medium").toLowerCase() as any,
        control_type: raw.control_type ?? "preventive",
        automation_potential: raw.automation_potential ?? "manual",
      })
      controlMap.set(reqCode, list)
    }
  }

  // Flat hierarchy: all requirements are top-level, no nesting.
  // If LLM produced nested children, promote them to top-level.
  const out: HierarchyNode[] = []
  const allReqs: any[] = []
  for (const node of requirements) {
    allReqs.push(node)
    for (const child of node.children ?? []) {
      allReqs.push(child)
    }
  }

  allReqs
    .sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0))
    .forEach((node, index) => {
      out.push({
        code: node.code,
        name: node.name,
        description: node.description ?? "",
        parent_code: null,
        depth: 0,
        sort_order: node.sort_order ?? index,
        controls: controlMap.get(node.code) ?? [],
      })
    })

  return out
}
