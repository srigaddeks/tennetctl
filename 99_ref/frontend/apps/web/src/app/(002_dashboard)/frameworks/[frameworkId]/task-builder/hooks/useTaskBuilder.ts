"use client"

import { useState, useEffect, useRef } from "react"
import { useSearchParams } from "next/navigation"
import { useOrgWorkspace } from "@/lib/context/OrgWorkspaceContext"
import {
  createTaskBuilderSession,
  listTaskBuilderSessions,
  getTaskBuilderSession,
  patchTaskBuilderSession,
  enqueueTaskBuilderPreview,
  enqueueTaskBuilderApply,
  getTaskBuilderSessionJob,
  getTaskBuilderJob,
  uploadTaskBuilderFile,
  type TaskBuilderSession,
  type TaskBuilderJobStatus,
  type TaskGroup,
  type GeneratedTask,
  type TaskBuilderAttachment,
} from "@/lib/api/taskBuilder"
import type { ProgressEvent } from "@/components/grc/BuildProgressFeed"

// ── Types ────────────────────────────────────────────────────────────────────

export type TaskBuilderPhase =
  | "idle"
  | "generating"
  | "reviewing"
  | "applying"
  | "complete"
  | "failed"

export type SelectedTask = GeneratedTask & { _selected: boolean }
export type SelectedGroup = Omit<TaskGroup, "tasks"> & { tasks: SelectedTask[] }

// ── Hook ─────────────────────────────────────────────────────────────────────

export function useTaskBuilder(frameworkId: string) {
  const searchParams = useSearchParams()
  const { selectedOrgId, selectedWorkspaceId, ready } = useOrgWorkspace()

  // ── Phase / session state ──────────────────────────────────────────────────
  const [phase, setPhase] = useState<TaskBuilderPhase>("idle")
  const [sessions, setSessions] = useState<TaskBuilderSession[]>([])
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null)

  // ── Configure form state ──────────────────────────────────────────────────
  const [userContext, setUserContext] = useState("")
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([])
  const [attachments, setAttachments] = useState<TaskBuilderAttachment[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [dragOver, setDragOver] = useState(false)

  // ── Preview state ──────────────────────────────────────────────────────────
  const [groups, setGroups] = useState<SelectedGroup[]>([])

  // ── Apply result ───────────────────────────────────────────────────────────
  const [applyResult, setApplyResult] = useState<{ created: number; skipped: number } | null>(null)

  // ── Progress feed ──────────────────────────────────────────────────────────
  const [feedEvents, setFeedEvents] = useState<ProgressEvent[]>([])
  const [isStreaming, setIsStreaming] = useState(false)

  // ── Error state ────────────────────────────────────────────────────────────
  const [error, setError] = useState<string | null>(null)

  // ── Refs ────────────────────────────────────────────────────────────────────
  const pollingRef = useRef<NodeJS.Timeout | null>(null)
  const pollingActiveRef = useRef(false)
  const activeSessionIdRef = useRef<string | null>(null)
  const hydratedSessionRef = useRef<string | null>(null)
  const sessionsRef = useRef<TaskBuilderSession[]>([])

  // ── Sync refs ──────────────────────────────────────────────────────────────
  useEffect(() => { activeSessionIdRef.current = activeSessionId }, [activeSessionId])
  useEffect(() => { sessionsRef.current = sessions }, [sessions])
  useEffect(() => { return () => { if (pollingRef.current) clearInterval(pollingRef.current) } }, [])

  // ── Initial load ──────────────────────────────────────────────────────────
  useEffect(() => {
    if (ready && selectedOrgId && selectedWorkspaceId) void loadSessions()
  }, [ready, selectedOrgId, selectedWorkspaceId])

  // ── URL session hydration ──────────────────────────────────────────────────
  useEffect(() => {
    const sessionId = searchParams.get("session")
    if (!sessionId) return
    if (hydratedSessionRef.current === sessionId) return
    let cancelled = false
    void (async () => {
      try {
        const existing = sessionsRef.current.find(s => s.id === sessionId)
        const session = existing ?? await getTaskBuilderSession(sessionId)
        if (cancelled) return
        hydratedSessionRef.current = sessionId
        hydrateFromSession(session)
        if (!existing) {
          setSessions(prev => [session, ...prev.filter(s => s.id !== session.id)])
        }
      } catch (err) {
        if (!cancelled) console.error("Failed to hydrate task builder session", err)
      }
    })()
    return () => { cancelled = true }
  }, [searchParams])

  // ── Computed ───────────────────────────────────────────────────────────────
  const totalSelected = groups.reduce((sum, g) => sum + g.tasks.filter(t => t._selected).length, 0)
  const totalTasks = groups.reduce((sum, g) => sum + g.tasks.length, 0)

  // ── Actions ────────────────────────────────────────────────────────────────

  async function loadSessions() {
    if (!selectedOrgId || !selectedWorkspaceId) return
    try {
      const res = await listTaskBuilderSessions({
        framework_id: frameworkId,
        scope_org_id: selectedOrgId,
        scope_workspace_id: selectedWorkspaceId,
        limit: 20,
      })
      setSessions(res.items)
    } catch (err) {
      console.error("Failed to load task builder sessions", err)
    }
  }

  function hydrateFromSession(session: TaskBuilderSession) {
    setActiveSessionId(session.id)
    setUserContext(session.user_context || "")
    setError(session.error_message || null)

    // Restore activity log
    const log = Array.isArray(session.activity_log) ? session.activity_log : []
    setFeedEvents(log as ProgressEvent[])

    // Map status to phase
    const statusMap: Record<string, TaskBuilderPhase> = {
      idle: "idle",
      generating: "generating",
      reviewing: "reviewing",
      applying: "applying",
      complete: "complete",
      failed: "failed",
    }
    const mappedPhase = statusMap[session.status] ?? "idle"
    setPhase(mappedPhase)

    // Restore proposed tasks
    if (session.proposed_tasks && session.proposed_tasks.length > 0) {
      setGroups(
        session.proposed_tasks.map((g): SelectedGroup => ({
          ...g,
          tasks: g.tasks.map((t): SelectedTask => ({ ...t, _selected: true })),
        }))
      )
    } else {
      setGroups([])
    }

    // Restore apply result
    setApplyResult(session.apply_result ?? null)

    // Resume polling if job in flight
    const needsPolling = session.status === "generating" || session.status === "applying"
    if (needsPolling && session.job_id && !pollingActiveRef.current) {
      setIsStreaming(true)
      startPollingJob(session.id, undefined, session.job_id)
    }
  }

  function resetState() {
    setPhase("idle")
    setActiveSessionId(null)
    setGroups([])
    setFeedEvents([])
    setIsStreaming(false)
    setApplyResult(null)
    setError(null)
    setUserContext("")
    setUploadedFiles([])
    setAttachments([])
    setUploadError(null)
    if (pollingRef.current) clearInterval(pollingRef.current)
    pollingActiveRef.current = false
  }

  async function handleFileDrop(files: File[]) {
    if (!selectedOrgId || !selectedWorkspaceId) return
    setUploadError(null)
    setUploading(true)
    const newFiles = files.filter(
      f => !uploadedFiles.some(existing => existing.name === f.name && existing.size === f.size)
    )
    if (newFiles.length === 0) { setUploading(false); return }
    try {
      const results = await Promise.all(
        newFiles.map(f => uploadTaskBuilderFile(f, selectedOrgId!, selectedWorkspaceId!))
      )
      setUploadedFiles(prev => [...prev, ...newFiles])
      setAttachments(prev => [...prev, ...results])
    } catch (e) {
      setUploadError(e instanceof Error ? e.message : "Upload failed")
    } finally {
      setUploading(false)
    }
  }

  function removeFile(index: number) {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index))
    setAttachments(prev => prev.filter((_, i) => i !== index))
  }

  // ── Generate (async via job) ───────────────────────────────────────────────

  async function handleGenerate(overrideControlIds?: string[]) {
    if (!selectedOrgId || !selectedWorkspaceId) return
    setError(null)
    setFeedEvents([])
    setGroups([])
    setApplyResult(null)

    // Pre-selected controls from URL or override
    const urlControlIds = searchParams.getAll("control_id")
    const controlIds = overrideControlIds ?? (urlControlIds.length > 0 ? urlControlIds : undefined)

    try {
      let sessionId = activeSessionId
      if (!sessionId) {
        const session = await createTaskBuilderSession({
          framework_id: frameworkId,
          scope_org_id: selectedOrgId,
          scope_workspace_id: selectedWorkspaceId,
          user_context: userContext.trim() || undefined,
          attachment_ids: attachments.length > 0 ? attachments.map(a => a.id) : undefined,
          control_ids: controlIds,
        })
        sessionId = session.id
        setActiveSessionId(sessionId)
        setSessions(prev => [session, ...prev])
      } else {
        await patchTaskBuilderSession(sessionId, {
          user_context: userContext.trim() || undefined,
          attachment_ids: attachments.length > 0 ? attachments.map(a => a.id) : undefined,
          control_ids: controlIds,
        })
      }

      setPhase("generating")
      setIsStreaming(true)

      const job = await enqueueTaskBuilderPreview(sessionId)
      startPollingJob(sessionId, job)
    } catch (err: any) {
      setError(err.message || "Generation failed")
      setPhase("failed")
      setIsStreaming(false)
    }
  }

  // ── Auto-generate if control IDs present ──
  useEffect(() => {
    if (phase === "idle" && ready && selectedOrgId && selectedWorkspaceId) {
      const urlControlIds = searchParams.getAll("control_id")
      if (urlControlIds.length > 0) {
        void handleGenerate(urlControlIds)
      }
    }
  }, [phase, ready, selectedOrgId, selectedWorkspaceId, searchParams])

  // ── Apply (async via job) ──────────────────────────────────────────────────

  async function handleApply() {
    if (!activeSessionId) return
    setError(null)
    setFeedEvents([])

    try {
      // Build filtered task groups (only selected)
      const filteredGroups: TaskGroup[] = groups
        .map(g => ({
          control_id: g.control_id,
          control_code: g.control_code,
          tasks: g.tasks.filter(t => t._selected).map(({ _selected, ...t }) => t),
        }))
        .filter(g => g.tasks.length > 0)

      if (filteredGroups.length === 0) {
        setError("Select at least one task to create")
        return
      }

      setPhase("applying")
      setIsStreaming(true)

      const job = await enqueueTaskBuilderApply(activeSessionId, filteredGroups)
      startPollingJob(activeSessionId, job)
    } catch (err: any) {
      setError(err.message || "Apply failed")
      setPhase("failed")
      setIsStreaming(false)
    }
  }

  // ── Task selection helpers ─────────────────────────────────────────────────

  function toggleTask(groupIdx: number, taskIdx: number) {
    setGroups(prev =>
      prev.map((g, gi): SelectedGroup =>
        gi !== groupIdx ? g : {
          ...g,
          tasks: g.tasks.map((t, ti): SelectedTask =>
            ti !== taskIdx ? t : { ...t, _selected: !t._selected }
          ),
        }
      )
    )
  }

  function editTask(groupIdx: number, taskIdx: number, field: keyof GeneratedTask, value: string) {
    setGroups(prev =>
      prev.map((g, gi): SelectedGroup =>
        gi !== groupIdx ? g : {
          ...g,
          tasks: g.tasks.map((t, ti): SelectedTask =>
            ti !== taskIdx ? t : { ...t, [field]: value }
          ),
        }
      )
    )
  }

  function toggleGroupAll(groupIdx: number, selected: boolean) {
    setGroups(prev =>
      prev.map((g, gi): SelectedGroup =>
        gi !== groupIdx ? g : {
          ...g,
          tasks: g.tasks.map((t): SelectedTask => ({ ...t, _selected: selected })),
        }
      )
    )
  }

  function selectAll(selected: boolean) {
    setGroups(prev =>
      prev.map((g): SelectedGroup => ({
        ...g,
        tasks: g.tasks.map((t): SelectedTask => ({ ...t, _selected: selected })),
      }))
    )
  }

  function handleSpreadsheetSelectionChange(indices: number[]) {
    const selectedSet = new Set(indices)
    let currentIdx = 0
    setGroups(prev =>
      prev.map((group): SelectedGroup => ({
        ...group,
        tasks: group.tasks.map((task): SelectedTask => {
          const isSelected = selectedSet.has(currentIdx)
          currentIdx++
          return { ...task, _selected: isSelected }
        }),
      }))
    )
  }

  // ── Polling ────────────────────────────────────────────────────────────────

  async function startPollingJob(sessionId: string, initialJob?: TaskBuilderJobStatus, knownJobId?: string) {
    if (initialJob || knownJobId) {
      pollingActiveRef.current = false
      if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null }
    }
    if (pollingActiveRef.current) return
    if (pollingRef.current) clearInterval(pollingRef.current)

    let currentJobId = initialJob?.job_id || knownJobId
    if (!currentJobId) {
      try {
        const job = await getTaskBuilderSessionJob(sessionId)
        currentJobId = job.job_id
      } catch (err) {
        console.error("Failed to fetch session job for polling", err)
        return 
      }
    }
    if (!currentJobId) return

    pollingActiveRef.current = true
    let consecutiveErrors = 0

    const stopPolling = () => {
      pollingActiveRef.current = false
      if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null }
    }

    const poll = async () => {
      try {
        const job = await getTaskBuilderJob(currentJobId!)
        consecutiveErrors = 0
        handleJobEvent(job, sessionId)
        if (job.status === "completed" || job.status === "failed") {
          stopPolling()
          await syncSessionState(sessionId)
        }
      } catch (err) {
        consecutiveErrors++
        console.warn(`Polling error (${consecutiveErrors}):`, err)
        if (consecutiveErrors >= 5) {
          stopPolling()
          setError("Connection lost while polling job status. Please refresh.")
        }
      }
    }
    void poll()
    pollingRef.current = setInterval(poll, 3000)
  }

  function handleJobEvent(job: TaskBuilderJobStatus, sessionId: string) {
    if (activeSessionIdRef.current !== sessionId) return

    // Merge job creation_log into feed events
    if (job.creation_log && job.creation_log.length > 0) {
      setFeedEvents(
        (job.creation_log as ProgressEvent[]).map(e => ({ ...e, __job: true }))
      )
    }

    if (job.status === "completed") {
      if (job.job_type === "task_builder_preview") {
        // Preview done — fetch session and hydrate groups
        void syncAndHydrateSession(sessionId).then(() => {
          setIsStreaming(false)
        })
      } else if (job.job_type === "task_builder_apply") {
        // Apply done
        const stats = job.stats as Record<string, number> | null
        setApplyResult(stats ? { created: stats.created ?? 0, skipped: stats.skipped ?? 0 } : null)
        setPhase("complete")
        setIsStreaming(false)
      }
    } else if (job.status === "failed") {
      setPhase("failed")
      if (job.error_message) {
        setFeedEvents(prev => [...prev, { event: "error", stage: "job", message: job.error_message } as ProgressEvent])
      }
      setIsStreaming(false)
    }
  }

  async function syncSessionState(sessionId: string) {
    try {
      const session = await getTaskBuilderSession(sessionId)
      setSessions(prev => prev.map(s => s.id === session.id ? session : s))
    } catch {}
  }

  async function syncAndHydrateSession(sessionId: string) {
    try {
      const session = await getTaskBuilderSession(sessionId)
      setSessions(prev => prev.map(s => s.id === session.id ? session : s))
      hydrateFromSession(session)
    } catch (err) {
      console.error("Failed to hydrate session", err)
    }
  }

  return {
    // State
    phase,
    sessions,
    activeSessionId,
    userContext,
    setUserContext,
    uploadedFiles,
    attachments,
    uploading,
    uploadError,
    dragOver,
    setDragOver,
    groups,
    totalSelected,
    totalTasks,
    applyResult,
    feedEvents,
    isStreaming,
    error,

    // Actions
    handleFileDrop,
    removeFile,
    handleGenerate,
    handleApply,
    toggleTask,
    editTask,
    toggleGroupAll,
    selectAll,
    handleSpreadsheetSelectionChange,
    resetState,
    hydrateFromSession,
    loadSessions,
  }
}