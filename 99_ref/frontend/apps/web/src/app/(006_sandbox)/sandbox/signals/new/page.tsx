"use client"

import { useEffect, useState, useRef, useCallback } from "react"
import { useRouter } from "next/navigation"
import {
  Button,
  Badge,
  Label,
} from "@kcontrol/ui"
import {
  ArrowLeft,
  Loader2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ChevronRight,
  ChevronDown,
  Sparkles,
  Send,
  Shield,
  Database,
  Zap,
  Lock,
} from "lucide-react"
import { cn } from "@kcontrol/ui"
import {
  createSpecSession,
  streamSpecGenerate,
  streamSpecRefine,
  approveSpec,
  type SpecSessionResponse,
  type SignalSpec,
  type FeasibilityResult,
  type SpecSseEvent,
} from "@/lib/api/signalPipeline"
import { listDatasets } from "@/lib/api/sandbox"
import type { DatasetResponse } from "@/lib/api/sandbox"
import { useSandboxOrgWorkspace } from "@/lib/context/SandboxOrgWorkspaceContext"

// ── Dataset Explorer ────────────────────────────────────────────────────────────

interface FieldMeta {
  type: string
  example: unknown
  nullable?: boolean
}

function DatasetExplorer({
  schema,
  usedFields,
  missingFields,
}: {
  schema: Record<string, FieldMeta>
  usedFields: Set<string>
  missingFields: Set<string>
}) {
  const fields = Object.entries(schema)

  const getFieldState = (path: string) => {
    if (missingFields.has(path)) return "missing"
    if (usedFields.has(path)) return "used"
    return "unused"
  }

  return (
    <div className="flex flex-col gap-1 font-mono text-xs">
      {fields.length === 0 && (
        <p className="text-muted-foreground p-3 text-center text-xs">
          No dataset selected — choose one to see schema
        </p>
      )}
      {fields.map(([path, meta]) => {
        const state = getFieldState(path)
        return (
          <div
            key={path}
            className={cn(
              "flex items-start gap-2 rounded-md px-2 py-1.5 text-xs transition-colors",
              state === "used" && "bg-green-50 dark:bg-green-950/20",
              state === "missing" && "bg-red-50 dark:bg-red-950/20",
              state === "unused" && "hover:bg-muted/50",
            )}
          >
            <span className="mt-0.5 shrink-0 text-[10px]">
              {state === "used" && <CheckCircle2 className="h-3 w-3 text-green-500" />}
              {state === "missing" && <XCircle className="h-3 w-3 text-red-500" />}
              {state === "unused" && (
                <span className="inline-block h-3 w-3 rounded-full border border-muted-foreground/30" />
              )}
            </span>
            <div className="min-w-0 flex-1">
              <div
                className={cn(
                  "font-medium truncate",
                  state === "used" && "text-green-700 dark:text-green-400",
                  state === "missing" && "text-red-600 dark:text-red-400",
                  state === "unused" && "text-foreground",
                )}
              >
                {path}
              </div>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-muted-foreground text-[10px]">{meta.type}</span>
                {meta.example !== undefined && meta.example !== null && (
                  <span className="text-muted-foreground/70 text-[10px] truncate max-w-[120px]">
                    e.g. {JSON.stringify(meta.example)}
                  </span>
                )}
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

// ── Feasibility Gate ────────────────────────────────────────────────────────────

function FeasibilityGate({
  feasibility,
  onApprove,
  approving,
  approved,
  specReady,
}: {
  feasibility: FeasibilityResult | null
  onApprove: () => void
  approving: boolean
  approved: boolean
  specReady: boolean
}) {
  if (!specReady) {
    return (
      <div className="rounded-lg border border-dashed border-muted-foreground/30 p-4 text-center text-sm text-muted-foreground">
        Describe your signal idea in the chat to get started
      </div>
    )
  }

  if (!feasibility) {
    return (
      <Button disabled className="w-full" variant="outline">
        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        Checking feasibility…
      </Button>
    )
  }

  if (feasibility.status === "infeasible") {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950/20 p-4 space-y-3">
        <div className="flex items-center gap-2 text-red-600 dark:text-red-400 font-semibold text-sm">
          <XCircle className="h-4 w-4 shrink-0" />
          This signal cannot be built with the available dataset data.
        </div>
        {feasibility.missing_fields.length > 0 && (
          <div>
            <p className="text-xs text-red-600/80 dark:text-red-400/80 font-medium mb-1">
              Missing required fields:
            </p>
            <ul className="space-y-1">
              {feasibility.missing_fields.map((f, i) => (
                <li key={i} className="text-xs font-mono text-red-600 dark:text-red-400">
                  • {f.field_path}
                  {f.reason && (
                    <span className="text-red-500/60 ml-1">({f.reason})</span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}
        {feasibility.blocking_issues.length > 0 && (
          <ul className="space-y-1">
            {feasibility.blocking_issues.map((issue, i) => (
              <li key={i} className="text-xs text-red-600/80 dark:text-red-400/80">
                • {issue}
              </li>
            ))}
          </ul>
        )}
        <div className="flex gap-2 pt-1">
          <Button
            variant="outline"
            size="sm"
            className="text-xs border-red-300 text-red-600 hover:bg-red-100"
          >
            Redesign Signal
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="text-xs border-red-300 text-red-600 hover:bg-red-100"
          >
            Change Dataset
          </Button>
        </div>
      </div>
    )
  }

  if (feasibility.status === "partial") {
    return (
      <div className="space-y-3">
        <div className="rounded-lg border border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-950/20 p-3 text-xs text-amber-700 dark:text-amber-400">
          <div className="flex items-center gap-2 font-semibold mb-1">
            <AlertTriangle className="h-3.5 w-3.5" />
            Signal will work with limitations
          </div>
          <p>{feasibility.notes}</p>
        </div>
        <Button
          onClick={onApprove}
          disabled={approving || approved}
          className="w-full bg-amber-500 hover:bg-amber-600 text-white"
        >
          {approving ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Lock className="mr-2 h-4 w-4" />
          )}
          {approved ? "Approved ✓" : "Approve with Limitations"}
        </Button>
      </div>
    )
  }

  if (feasibility.status === "feasible") {
    return (
      <div className="space-y-3">
        <div className="rounded-lg border border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950/20 p-3 text-xs text-green-700 dark:text-green-400 flex items-center gap-2">
          <CheckCircle2 className="h-3.5 w-3.5 shrink-0" />
          <span>All required fields found. Ready to generate.</span>
        </div>
        <Button
          onClick={onApprove}
          disabled={approving || approved}
          className="w-full bg-green-600 hover:bg-green-700 text-white"
        >
          {approving ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Sparkles className="mr-2 h-4 w-4" />
          )}
          {approved ? "Approved ✓" : "Approve & Build ▶"}
        </Button>
      </div>
    )
  }

  return (
    <Button disabled className="w-full" variant="outline">
      Checking…
    </Button>
  )
}

// ── Spec Section ────────────────────────────────────────────────────────────────

function SpecSection({
  label,
  children,
}: {
  label: string
  children: React.ReactNode
}) {
  const [open, setOpen] = useState(true)
  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center justify-between w-full px-3 py-2 bg-muted/50 hover:bg-muted text-xs font-semibold text-foreground"
      >
        {label}
        {open ? (
          <ChevronDown className="h-3.5 w-3.5" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5" />
        )}
      </button>
      {open && <div className="px-3 py-2 text-xs">{children}</div>}
    </div>
  )
}

function SpecDisplay({ spec }: { spec: SignalSpec }) {
  return (
    <div className="space-y-2">
      <SpecSection label="Signal Code">
        <code className="font-mono text-blue-600">{spec.signal_code}</code>
      </SpecSection>
      <SpecSection label="Intent">
        <p className="text-muted-foreground">{spec.intent || spec.description}</p>
      </SpecSection>
      <SpecSection label="Dataset Fields Used">
        <div className="space-y-1.5">
          {spec.dataset_fields_used?.map((f, i) => (
            <div key={i} className="flex items-center gap-2 flex-wrap">
              <span className="font-mono text-green-600">{f.field_path}</span>
              <Badge variant="outline" className="text-[10px] px-1">
                {f.type}
              </Badge>
              {f.required && (
                <Badge className="text-[10px] px-1 bg-blue-50 text-blue-600 border-blue-200">
                  required
                </Badge>
              )}
            </div>
          ))}
        </div>
      </SpecSection>
      <SpecSection label="Detection Logic">
        <p className="text-muted-foreground whitespace-pre-wrap">{spec.detection_logic}</p>
      </SpecSection>
      {(spec.configurable_args?.length ?? 0) > 0 && (
        <SpecSection label={`Configurable Args (${spec.configurable_args.length})`}>
          <div className="space-y-1.5">
            {spec.configurable_args.map((arg, i) => (
              <div key={i} className="flex items-center gap-2">
                <code className="font-mono text-purple-600">{arg.key}</code>
                <span className="text-muted-foreground">
                  = {JSON.stringify(arg.default)}
                </span>
                <Badge variant="outline" className="text-[10px] px-1">
                  {arg.type}
                </Badge>
              </div>
            ))}
          </div>
        </SpecSection>
      )}
      <SpecSection label={`Test Scenarios (${spec.test_scenarios?.length ?? 0})`}>
        <div className="flex flex-wrap gap-1.5">
          {spec.test_scenarios?.map((s, i) => (
            <Badge
              key={i}
              variant="outline"
              className={cn(
                "text-[10px]",
                s.result_expectation === "pass" && "border-green-300 text-green-600",
                s.result_expectation === "fail" && "border-red-300 text-red-600",
                s.result_expectation === "warning" && "border-amber-300 text-amber-600",
              )}
            >
              {s.scenario_name} → {s.result_expectation}
            </Badge>
          ))}
        </div>
      </SpecSection>
      {spec.ssf_mapping && (
        <SpecSection label="SSF Mapping">
          <div className="space-y-1 text-muted-foreground">
            <div>
              <span className="text-foreground font-medium">Standard:</span>{" "}
              {spec.ssf_mapping.standard?.toUpperCase()}
            </div>
            <div>
              <span className="text-foreground font-medium">Event:</span>{" "}
              {spec.ssf_mapping.event_type}
            </div>
            <div>
              <span className="text-foreground font-medium">Severity:</span>{" "}
              {spec.ssf_mapping.signal_severity}
            </div>
          </div>
        </SpecSection>
      )}
    </div>
  )
}

// ── Chat Message ────────────────────────────────────────────────────────────────

interface ChatMessage {
  role: "user" | "assistant" | "system"
  content: string
}

// ── Main Page ───────────────────────────────────────────────────────────────────

export default function SignalSpecBuilderPage() {
  const router = useRouter()
  const { selectedOrgId, selectedWorkspaceId, ready } = useSandboxOrgWorkspace()

  const [datasets, setDatasets] = useState<DatasetResponse[]>([])
  const [selectedDataset, setSelectedDataset] = useState("")
  const [initialPrompt, setInitialPrompt] = useState("")

  const [session, setSession] = useState<SpecSessionResponse | null>(null)
  const [creating, setCreating] = useState(false)

  const [spec, setSpec] = useState<SignalSpec | null>(null)
  const [feasibility, setFeasibility] = useState<FeasibilityResult | null>(null)
  const [schema, setSchema] = useState<Record<string, FieldMeta>>({})
  const [usedFields, setUsedFields] = useState<Set<string>>(new Set())
  const [missingFields, setMissingFields] = useState<Set<string>>(new Set())

  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [chatInput, setChatInput] = useState("")
  const [streaming, setStreaming] = useState(false)
  const [streamPhase, setStreamPhase] = useState("")

  const [approving, setApproving] = useState(false)
  const [approved, setApproved] = useState(false)
  const [approveError, setApproveError] = useState("")

  const stopStream = useRef<(() => void) | null>(null)
  const chatEndRef = useRef<HTMLDivElement>(null)

  // Load datasets
  useEffect(() => {
    if (!ready || !selectedOrgId) return
    listDatasets(selectedOrgId).then((r) => setDatasets(r.items))
  }, [ready, selectedOrgId])

  // Scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [chatMessages])

  // Update used/missing fields when spec changes
  useEffect(() => {
    if (!spec) {
      setUsedFields(new Set())
      setMissingFields(new Set())
      return
    }
    setUsedFields(new Set(spec.dataset_fields_used?.map((f) => f.field_path) ?? []))
    const missing = spec.feasibility?.missing_fields?.map((f) => f.field_path) ?? []
    setMissingFields(new Set(missing))
    setFeasibility(spec.feasibility ?? null)
  }, [spec])

  const handleSseEvent = useCallback((event: SpecSseEvent) => {
    switch (event.type) {
      case "spec_analyzing":
        setStreamPhase(event.data.message)
        break
      case "spec_field_identified":
        setSchema((prev) => ({
          ...prev,
          [event.data.field_path]: { type: event.data.type, example: event.data.example },
        }))
        break
      case "spec_section_ready":
        setStreamPhase(`Building ${event.data.label}…`)
        break
      case "spec_complete":
        setSpec(event.data.spec)
        setStreamPhase("")
        // Build schema from spec fields if schema is empty (get_rich_schema may have failed)
        if (Object.keys(schema).length === 0 && event.data.spec?.dataset_fields_used) {
          const built: Record<string, FieldMeta> = {}
          for (const f of event.data.spec.dataset_fields_used) {
            built[f.field_path] = { type: f.type || "string", example: f.example ?? "" }
          }
          setSchema(built)
        }
        break
      case "spec_refined":
        setSpec(event.data.spec)
        setStreamPhase("")
        break
      case "feasibility_checking":
        setStreamPhase("Checking implementability…")
        break
      case "feasibility_result":
        setFeasibility(event.data as FeasibilityResult)
        setStreamPhase("")
        break
      case "error":
        setChatMessages((m) => [
          ...m,
          { role: "system", content: `Error: ${event.data.message}` },
        ])
        setStreamPhase("")
        break
    }
  }, [])

  const startSession = useCallback(async () => {
    if (!selectedDataset || !initialPrompt.trim()) return
    setCreating(true)
    try {
      const s = await createSpecSession({
        connector_type_code: "generic",
        source_dataset_id: selectedDataset,
        org_id: selectedOrgId,
        workspace_id: selectedWorkspaceId,
      })
      const prompt = initialPrompt.trim()
      setChatMessages([{ role: "user", content: prompt }])
      setSession(s)
      setCreating(false)

      // Small delay to let React render the 3-panel layout before starting SSE
      await new Promise((r) => setTimeout(r, 200))

      setStreaming(true)
      const stop = streamSpecGenerate(
        s.id,
        prompt,
        handleSseEvent,
        () => {
          setStreaming(false)
          setChatMessages((m) => [...m, { role: "assistant", content: "Spec generation complete." }])
        },
        (err) => {
          setStreaming(false)
          setChatMessages((m) => [...m, { role: "system", content: `Error: ${err}` }])
        },
      )
      stopStream.current = stop
    } catch (e: unknown) {
      setChatMessages([{ role: "system", content: `Failed to create session: ${e}` }])
      setCreating(false)
    }
  }, [selectedDataset, initialPrompt, selectedOrgId, selectedWorkspaceId, handleSseEvent])

  const sendMessage = useCallback(async () => {
    if (!session || !chatInput.trim() || streaming) return
    const msg = chatInput.trim()
    setChatInput("")
    setChatMessages((m) => [...m, { role: "user", content: msg }])
    setStreaming(true)
    setApproveError("")

    const isFirstGen = !spec

    if (isFirstGen) {
      const stop = streamSpecGenerate(
        session.id,
        msg,
        handleSseEvent,
        () => {
          setStreaming(false)
          setChatMessages((m) => [
            ...m,
            {
              role: "assistant",
              content:
                "Spec generated. Review the specification and check feasibility.",
            },
          ])
        },
        (err) => {
          setStreaming(false)
          setChatMessages((m) => [
            ...m,
            { role: "system", content: `Stream error: ${err}` },
          ])
        }
      )
      stopStream.current = stop
    } else {
      const stop = streamSpecRefine(
        session.id,
        msg,
        handleSseEvent,
        () => {
          setStreaming(false)
          setChatMessages((m) => [
            ...m,
            { role: "assistant", content: "Spec updated based on your feedback." },
          ])
        },
        (err) => {
          setStreaming(false)
          setChatMessages((m) => [
            ...m,
            { role: "system", content: `Stream error: ${err}` },
          ])
        }
      )
      stopStream.current = stop
    }
  }, [session, chatInput, streaming, spec, handleSseEvent])

  const handleApprove = useCallback(async () => {
    if (!session) return
    setApproving(true)
    setApproveError("")
    try {
      const result = await approveSpec(session.id)
      setApproved(true)
      setChatMessages((m) => [
        ...m,
        {
          role: "system",
          content: `✓ Spec approved! Pipeline queued (job: ${result.job_id}). Redirecting…`,
        },
      ])
      setTimeout(() => router.push("/sandbox/pipeline-queue"), 2000)
    } catch (e: unknown) {
      setApproveError(String(e))
    } finally {
      setApproving(false)
    }
  }, [session, router])

  if (!ready) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-border px-4 py-3 shrink-0">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.back()}
          className="gap-1.5 text-muted-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>
        <div className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-blue-500" />
          <span className="font-semibold">Signal Spec Builder</span>
        </div>
        {session && (
          <Badge variant="outline" className="text-xs">
            Session active
          </Badge>
        )}
        {streaming && (
          <div className="flex items-center gap-1.5 text-xs text-blue-600">
            <Loader2 className="h-3 w-3 animate-spin" />
            {streamPhase || "Streaming…"}
          </div>
        )}
      </div>

      {/* Session setup (before session created) */}
      {!session && (
        <div className="flex items-center justify-center flex-1 p-8">
          <div className="w-full max-w-lg space-y-6">
            <div className="text-center">
              <Sparkles className="h-12 w-12 mx-auto text-blue-500 mb-3" />
              <h2 className="text-xl font-bold">Signal Spec Builder</h2>
              <p className="text-sm text-muted-foreground mt-1">
                Select a dataset to build compliance signals against real collected data
              </p>
            </div>
            <div className="space-y-4 rounded-xl border border-border p-6">
              <div className="space-y-2">
                <Label className="text-sm font-medium">Dataset</Label>
                <select
                  value={selectedDataset}
                  onChange={(e) => setSelectedDataset(e.target.value)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="">Select a dataset…</option>
                  {datasets.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name || d.dataset_code} ({d.row_count} records)
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label className="text-sm font-medium">What signal do you want to build?</Label>
                <textarea
                  value={initialPrompt}
                  onChange={(e) => setInitialPrompt(e.target.value)}
                  rows={4}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring resize-y"
                  placeholder="e.g. Detect GitHub repos that are public and have no branch protection enabled, or detect org members without 2FA..."
                />
                <p className="text-xs text-muted-foreground">
                  Describe the compliance check you want. The AI will analyze your dataset,
                  generate a signal spec, and verify data sufficiency.
                </p>
              </div>
              <Button
                className="w-full"
                disabled={!selectedDataset || !initialPrompt.trim() || creating}
                onClick={startSession}
              >
                {creating ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Sparkles className="mr-2 h-4 w-4" />
                )}
                Generate Signal Spec
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Main 3-panel layout */}
      {session && (
        <div className="flex flex-1 min-h-0 overflow-hidden">
          {/* Left: Dataset Explorer */}
          <div className="w-64 shrink-0 border-r border-border flex flex-col">
            <div className="flex items-center gap-2 px-3 py-2 border-b border-border shrink-0">
              <Database className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                Dataset Schema
              </span>
            </div>
            <div className="flex-1 overflow-y-auto p-2">
              <DatasetExplorer
                schema={schema}
                usedFields={usedFields}
                missingFields={missingFields}
              />
            </div>
            {Object.keys(schema).length > 0 && (
              <div className="border-t border-border p-2 text-xs text-muted-foreground space-y-0.5">
                <div className="flex items-center gap-1.5">
                  <CheckCircle2 className="h-3 w-3 text-green-500" /> used by spec
                </div>
                <div className="flex items-center gap-1.5">
                  <XCircle className="h-3 w-3 text-red-500" /> missing from dataset
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="inline-block h-3 w-3 rounded-full border border-muted-foreground/30" />{" "}
                  available
                </div>
              </div>
            )}
          </div>

          {/* Center: Spec Display + Approve */}
          <div className="flex-1 min-w-0 flex flex-col overflow-hidden border-r border-border">
            <div className="flex items-center gap-2 px-4 py-2 border-b border-border shrink-0">
              <Zap className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                Signal Specification
              </span>
              {spec && (
                <Badge variant="outline" className="text-[10px]">
                  {spec.signal_code}
                </Badge>
              )}
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {!spec && !streaming && (
                <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
                  <Sparkles className="h-10 w-10 mb-3 opacity-30" />
                  <p className="text-sm">Describe your signal idea in the chat →</p>
                  <p className="text-xs mt-1 opacity-60">
                    e.g. "Detect GitHub repos with insufficient branch protection reviewer
                    requirements"
                  </p>
                </div>
              )}

              {streaming && !spec && (
                <div className="flex flex-col items-center justify-center h-full text-center">
                  <Loader2 className="h-8 w-8 animate-spin text-blue-500 mb-3" />
                  <p className="text-sm font-medium">{streamPhase || "Generating spec…"}</p>
                  {Object.keys(schema).length > 0 && (
                    <p className="text-xs text-muted-foreground mt-1">
                      {Object.keys(schema).length} fields discovered
                    </p>
                  )}
                </div>
              )}

              {spec && <SpecDisplay spec={spec} />}
            </div>

            {/* Approve section */}
            <div className="border-t border-border p-4 shrink-0 space-y-2">
              <FeasibilityGate
                feasibility={feasibility}
                onApprove={handleApprove}
                approving={approving}
                approved={approved}
                specReady={!!spec}
              />
              {approveError && (
                <p className="text-xs text-red-600">{approveError}</p>
              )}
            </div>
          </div>

          {/* Right: AI Chat */}
          <div className="w-80 shrink-0 flex flex-col">
            <div className="flex items-center gap-2 px-3 py-2 border-b border-border shrink-0">
              <Sparkles className="h-3.5 w-3.5 text-blue-500" />
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                AI Assistant
              </span>
            </div>

            <div className="flex-1 overflow-y-auto p-3 space-y-3">
              {chatMessages.length === 0 && (
                <p className="text-xs text-muted-foreground text-center pt-4">
                  Describe what you want to detect…
                </p>
              )}
              {chatMessages.map((msg, i) => (
                <div
                  key={i}
                  className={cn(
                    "rounded-lg px-3 py-2 text-xs",
                    msg.role === "user" &&
                      "bg-blue-50 dark:bg-blue-950/20 text-blue-900 dark:text-blue-100 ml-4",
                    msg.role === "assistant" && "bg-muted text-foreground mr-4",
                    msg.role === "system" &&
                      "bg-muted/50 text-muted-foreground text-center italic",
                  )}
                >
                  {msg.content}
                </div>
              ))}
              {streaming && (
                <div className="flex items-center gap-2 text-xs text-blue-600 mr-4">
                  <Loader2 className="h-3 w-3 animate-spin" />
                  <span>{streamPhase || "Thinking…"}</span>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            <div className="border-t border-border p-3 shrink-0 space-y-2">
              <textarea
                value={chatInput}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                  setChatInput(e.target.value)
                }
                placeholder={
                  spec
                    ? "Refine the spec — e.g. make min_review_count configurable…"
                    : "Describe your signal idea…"
                }
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-xs ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring resize-none min-h-[72px]"
                onKeyDown={(e: React.KeyboardEvent<HTMLTextAreaElement>) => {
                  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) sendMessage()
                }}
              />
              <Button
                className="w-full text-xs gap-1.5"
                size="sm"
                disabled={!chatInput.trim() || streaming}
                onClick={sendMessage}
              >
                {streaming ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Send className="h-3.5 w-3.5" />
                )}
                {spec ? "Refine" : "Generate Spec"}
                <span className="text-[10px] opacity-60">⌘↵</span>
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
