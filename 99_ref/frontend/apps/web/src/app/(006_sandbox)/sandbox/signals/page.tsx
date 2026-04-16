"use client"

import { useEffect, useState, useCallback } from "react"
import { useRouter, useSearchParams, usePathname } from "next/navigation"
import {
  Button,
  Input,
  Label,
  Badge,
  Separator,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@kcontrol/ui"
import {
  Zap,
  Search,
  Plus,
  Sparkles,
  Pencil,
  Trash2,
  ShieldCheck,
  AlertTriangle,
  Clock,
  Cpu,
  Hash,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2,
  Code2,
  RefreshCw,
  Copy,
  Check,
  GitBranch,
  ArrowUpFromLine,
  FlaskConical,
  Play,
  Activity,
  Globe,
} from "lucide-react"
import {
  listSignals,
  listSignalStatuses,
  listConnectorTypes,
  listDatasets,
  createSignal,
  publishGlobalControlTest,
  updateSignal,
  deleteSignal,
  generateSignal,
  validateSignal,
  promoteSignal,
  runSignalTestSuite,
  executeSignalLive,
} from "@/lib/api/sandbox"
import type {
  SignalResponse,
  SignalListResponse,
  GenerateSignalResponse,
  DimensionResponse,
  DatasetResponse,
  TestSuiteResponse,
  ExecuteLiveResponse,
} from "@/lib/api/sandbox"
import { SignalArgsForm } from "@/components/sandbox/SignalArgsForm"
import type { ArgDefinition } from "@/components/sandbox/SignalArgsForm"
import { SignalTestResults } from "@/components/sandbox/SignalTestResults"
import { copyToClipboard } from "@/lib/utils/sandbox-helpers"
import { useSandboxOrgWorkspace } from "@/lib/context/SandboxOrgWorkspaceContext"
import { useAccess } from "@/components/providers/AccessProvider"
import { AssetSelectorDialog } from "@/components/grc/AssetSelectorDialog"

// ─────────────────────────────────────────────────────────────────────────────
// Status badge styles
// ─────────────────────────────────────────────────────────────────────────────

const STATUS_STYLES: Record<string, string> = {
  draft: "bg-muted text-muted-foreground",
  testing: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/30",
  validated: "bg-green-500/10 text-green-600 dark:text-green-400 border-green-500/30",
  promoted: "bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/30",
  archived: "bg-muted/60 text-muted-foreground/60",
}

function statusBadge(code: string, name?: string) {
  return (
    <Badge
      variant="outline"
      className={`text-[10px] font-semibold ${STATUS_STYLES[code] ?? "bg-muted text-muted-foreground"}`}
    >
      {name || code.replace(/_/g, " ")}
    </Badge>
  )
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  })
}

function truncateHash(hash: string | null) {
  if (!hash) return null
  return hash.length > 12 ? `${hash.slice(0, 12)}...` : hash
}

// ─────────────────────────────────────────────────────────────────────────────
// Spinner
// ─────────────────────────────────────────────────────────────────────────────

function Spinner({ className = "h-3 w-3" }: { className?: string }) {
  return (
    <span
      className={`${className} animate-spin rounded-full border-2 border-current border-t-transparent inline-block`}
    />
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Create Signal Dialog
// ─────────────────────────────────────────────────────────────────────────────

function CreateSignalDialog({
  open,
  orgId,
  workspaceId,
  connectorTypes,
  onCreate,
  onClose,
}: {
  open: boolean
  orgId: string | null
  workspaceId: string | null
  connectorTypes: DimensionResponse[]
  onCreate: () => void
  onClose: () => void
}) {
  const [code, setCode] = useState("")
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [pythonCode, setPythonCode] = useState(
    `def evaluate(data: dict) -> str:\n    """Return 'pass', 'fail', or 'warning'."""\n    return "pass"\n`
  )
  const [selectedConnectors, setSelectedConnectors] = useState<string[]>([])
  const [timeoutMs, setTimeoutMs] = useState("5000")
  const [maxMemoryMb, setMaxMemoryMb] = useState("128")
  const [caepEventType, setCaepEventType] = useState("")
  const [riscEventType, setRiscEventType] = useState("")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      setCode("")
      setName("")
      setDescription("")
      setPythonCode(
        `def evaluate(data: dict) -> str:\n    """Return 'pass', 'fail', or 'warning'."""\n    return "pass"\n`
      )
      setSelectedConnectors([])
      setTimeoutMs("5000")
      setMaxMemoryMb("128")
      setCaepEventType("")
      setRiscEventType("")
      setSaving(false)
      setError(null)
    }
  }, [open])

  // Auto-generate code from name
  useEffect(() => {
    if (name && !code) {
      setCode(
        name
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, "_")
          .replace(/^_|_$/g, "")
      )
    }
  }, [name, code])

  function toggleConnector(c: string) {
    setSelectedConnectors((prev) =>
      prev.includes(c) ? prev.filter((x) => x !== c) : [...prev, c]
    )
  }

  async function handleCreate() {
    if (!code.trim()) {
      setError("Signal code is required.")
      return
    }
    if (!orgId) {
      setError("Select an organization before creating a signal.")
      return
    }
    setSaving(true)
    setError(null)
    try {
      const properties: Record<string, string> = {}
      if (name.trim()) properties.name = name.trim()
      if (description.trim()) properties.description = description.trim()
      if (pythonCode.trim()) properties.python_source = pythonCode.trim()
      if (selectedConnectors.length > 0)
        properties.connector_types = selectedConnectors.join(",")
      if (caepEventType.trim())
        properties.caep_event_type = caepEventType.trim()
      if (riscEventType.trim())
        properties.risc_event_type = riscEventType.trim()
      properties.timeout_ms = timeoutMs
      properties.max_memory_mb = maxMemoryMb

      await createSignal({
        signal_code: code.trim(),
        properties,
        org_id: orgId,
        workspace_id: workspaceId ?? undefined,
      })
      onCreate()
      onClose()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create signal")
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-amber-500/10 p-2.5">
              <Plus className="h-4 w-4 text-amber-500" />
            </div>
            <div>
              <DialogTitle>Create Signal</DialogTitle>
              <DialogDescription>
                Define a new compliance detection signal with Python evaluation
                logic.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />

        <div className="space-y-4">
          {/* Name + Code */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs">
                Name{" "}
                <span className="text-muted-foreground">(display name)</span>
              </Label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="MFA Enforcement Check"
                className="h-9 text-sm"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">
                Code{" "}
                <span className="text-muted-foreground">
                  (unique identifier)
                </span>
              </Label>
              <Input
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="mfa_enforcement_check"
                className="h-9 text-sm font-mono"
              />
            </div>
          </div>

          {/* Description */}
          <div className="space-y-1.5">
            <Label className="text-xs">Description</Label>
            <Input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Checks that MFA is enabled for all admin accounts..."
              className="h-9 text-sm"
            />
          </div>

          {/* Python Code */}
          <div className="space-y-1.5">
            <Label className="text-xs flex items-center gap-1.5">
              <Code2 className="h-3 w-3" />
              Python Evaluation Code
            </Label>
            <div className="relative">
              <div className="absolute left-0 top-0 bottom-0 w-10 bg-muted/40 border-r border-border rounded-l-md flex flex-col items-end pr-1.5 pt-3 text-[10px] text-muted-foreground font-mono select-none overflow-hidden">
                {pythonCode.split("\n").map((_, i) => (
                  <div key={i} className="leading-[1.625rem]">
                    {i + 1}
                  </div>
                ))}
              </div>
              <textarea
                value={pythonCode}
                onChange={(e) => setPythonCode(e.target.value)}
                rows={10}
                spellCheck={false}
                className="w-full rounded-md border border-border bg-zinc-100 dark:bg-zinc-950 text-green-700 dark:text-green-400 font-mono text-sm p-3 pl-12 resize-y focus:outline-none focus:ring-2 focus:ring-primary/30 leading-relaxed"
              />
            </div>
          </div>

          {/* Connector types */}
          <div className="space-y-1.5">
            <Label className="text-xs">Connector Types</Label>
            <div className="flex flex-wrap gap-1.5">
              {connectorTypes.map((ct) => (
                <button
                  key={ct.code}
                  type="button"
                  onClick={() => toggleConnector(ct.code)}
                  className={`rounded-md border px-2.5 py-1 text-xs font-medium transition-colors ${
                    selectedConnectors.includes(ct.code)
                      ? "border-primary bg-primary/10 text-primary"
                      : "border-border bg-card text-muted-foreground hover:border-primary/30"
                  }`}
                >
                  {ct.name}
                </button>
              ))}
            </div>
          </div>

          {/* Timeout + Memory */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs flex items-center gap-1">
                <Clock className="h-3 w-3" /> Timeout (ms)
              </Label>
              <Input
                type="number"
                value={timeoutMs}
                onChange={(e) => setTimeoutMs(e.target.value)}
                className="h-9 text-sm font-mono"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs flex items-center gap-1">
                <Cpu className="h-3 w-3" /> Max Memory (MB)
              </Label>
              <Input
                type="number"
                value={maxMemoryMb}
                onChange={(e) => setMaxMemoryMb(e.target.value)}
                className="h-9 text-sm font-mono"
              />
            </div>
          </div>

          {/* Event type mappings */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs">CAEP Event Type</Label>
              <Input
                value={caepEventType}
                onChange={(e) => setCaepEventType(e.target.value)}
                placeholder="session-revoked"
                className="h-9 text-sm"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">RISC Event Type</Label>
              <Input
                value={riscEventType}
                onChange={(e) => setRiscEventType(e.target.value)}
                placeholder="credential-compromise"
                className="h-9 text-sm"
              />
            </div>
          </div>
        </div>

        {error && (
          <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500 mt-2">
            {error}
          </p>
        )}

        <DialogFooter className="mt-3 gap-2 sm:gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button size="sm" onClick={handleCreate} disabled={saving}>
            {saving ? (
              <span className="flex items-center gap-1.5">
                <Spinner /> Creating...
              </span>
            ) : (
              "Create Signal"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// AI Generate Signal Dialog
// ─────────────────────────────────────────────────────────────────────────────

function AIGenerateDialog({
  open,
  orgId,
  workspaceId,
  connectorTypes,
  datasets,
  onSaved,
  onClose,
}: {
  open: boolean
  orgId: string | null
  workspaceId: string | null
  connectorTypes: DimensionResponse[]
  datasets: DatasetResponse[]
  onSaved: () => void
  onClose: () => void
}) {
  const [prompt, setPrompt] = useState("")
  const [connectorTypeCode, setConnectorTypeCode] = useState("")
  const [sampleDatasetId, setSampleDatasetId] = useState("")
  const [generating, setGenerating] = useState(false)
  const [iterationLabel, setIterationLabel] = useState("")
  const [result, setResult] = useState<GenerateSignalResponse | null>(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (open) {
      setPrompt("")
      setConnectorTypeCode(connectorTypes[0]?.code ?? "")
      setSampleDatasetId("")
      setGenerating(false)
      setIterationLabel("")
      setResult(null)
      setSaving(false)
      setError(null)
      setCopied(false)
    }
  }, [open, connectorTypes])

  async function handleGenerate() {
    if (!prompt.trim()) {
      setError("Please describe what you want to check.")
      return
    }
    if (!connectorTypeCode) {
      setError("Please select a connector type.")
      return
    }
    setGenerating(true)
    setError(null)
    setResult(null)

    // Simulate iteration updates for UX
    const iterationInterval = setInterval(() => {
      setIterationLabel((prev) => {
        const match = prev.match(/(\d+)/)
        const current = match ? parseInt(match[1]) : 0
        if (current >= 5) return prev
        return `Generating... (iteration ${current + 1}/5)`
      })
    }, 2000)
    setIterationLabel("Generating... (iteration 1/5)")

    try {
      const res = await generateSignal({
        prompt: prompt.trim(),
        connector_type_code: connectorTypeCode,
        sample_dataset_id: sampleDatasetId || undefined,
      })
      setResult(res)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Generation failed")
    } finally {
      clearInterval(iterationInterval)
      setGenerating(false)
      setIterationLabel("")
    }
  }

  async function handleSave() {
    if (!result) return
    if (!orgId) {
      setError("Select an organization before saving the generated signal.")
      return
    }
    setSaving(true)
    setError(null)
    try {
      const code = result.signal_name_suggestion
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "_")
        .replace(/^_|_$/g, "")

      const properties: Record<string, string> = {
        python_source: result.generated_code,
        connector_types: connectorTypeCode,
      }
      if (result.signal_name_suggestion)
        properties.name = result.signal_name_suggestion
      if (result.signal_description_suggestion)
        properties.description = result.signal_description_suggestion
      if (result.caep_event_type)
        properties.caep_event_type = result.caep_event_type
      if (result.risc_event_type)
        properties.risc_event_type = result.risc_event_type
      if (result.custom_event_type)
        properties.custom_event_type = result.custom_event_type

      await createSignal({
        signal_code: code,
        properties,
        org_id: orgId,
        workspace_id: workspaceId ?? undefined,
      })
      onSaved()
      onClose()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save signal")
      setSaving(false)
    }
  }

  function copyCode() {
    if (!result) return
    navigator.clipboard.writeText(result.generated_code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-gradient-to-br from-purple-500/20 to-pink-500/20 p-2.5">
              <Sparkles className="h-4 w-4 text-purple-500" />
            </div>
            <div>
              <DialogTitle>AI Signal Generator</DialogTitle>
              <DialogDescription>
                Describe what you want to check in plain English and let AI
                generate the Python detection code.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />

        {/* Input area */}
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label className="text-xs font-medium">
              What do you want to check?
            </Label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={4}
              placeholder="Check that all S3 buckets have encryption enabled and public access is blocked. Flag any bucket that has versioning disabled or doesn't have a lifecycle policy configured."
              className="w-full rounded-md border border-border bg-background text-sm p-3 resize-y focus:outline-none focus:ring-2 focus:ring-primary/30 placeholder:text-muted-foreground/50"
              disabled={generating}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs">Connector Type</Label>
              <select
                className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
                value={connectorTypeCode}
                onChange={(e) => setConnectorTypeCode(e.target.value)}
                disabled={generating}
              >
                {connectorTypes.map((ct) => (
                  <option key={ct.code} value={ct.code}>
                    {ct.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">
                Sample Dataset{" "}
                <span className="text-muted-foreground">(optional)</span>
              </Label>
              <select
                className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
                value={sampleDatasetId}
                onChange={(e) => setSampleDatasetId(e.target.value)}
                disabled={generating}
              >
                <option value="">None</option>
                {datasets.map((ds) => (
                  <option key={ds.id} value={ds.id}>
                    {ds.name || ds.dataset_code}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {!result && (
            <Button
              onClick={handleGenerate}
              disabled={generating || !prompt.trim()}
              className="w-full gap-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white"
            >
              {generating ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  {iterationLabel}
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  Generate Signal
                </>
              )}
            </Button>
          )}
        </div>

        {/* Result */}
        {result && (
          <div className="space-y-4 mt-2">
            <Separator />

            {/* Status indicators */}
            <div className="flex items-center gap-3 flex-wrap">
              <div className="flex items-center gap-1.5">
                {result.compile_status === "success" ? (
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                ) : (
                  <XCircle className="h-4 w-4 text-red-500" />
                )}
                <span className="text-xs font-medium">
                  Compile:{" "}
                  <span
                    className={
                      result.compile_status === "success"
                        ? "text-green-500"
                        : "text-red-500"
                    }
                  >
                    {result.compile_status}
                  </span>
                </span>
              </div>

              {result.test_result && (
                <div className="flex items-center gap-1.5">
                  {result.test_result === "pass" ? (
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                  ) : result.test_result === "warning" ? (
                    <AlertCircle className="h-4 w-4 text-yellow-500" />
                  ) : (
                    <XCircle className="h-4 w-4 text-red-500" />
                  )}
                  <span className="text-xs font-medium">
                    Test: {result.test_result}
                  </span>
                </div>
              )}

              <Badge variant="outline" className="text-[10px]">
                {result.iterations_used} iteration
                {result.iterations_used !== 1 ? "s" : ""}
              </Badge>

              {result.caep_event_type && (
                <Badge
                  variant="outline"
                  className="text-[10px] bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/30"
                >
                  CAEP: {result.caep_event_type}
                </Badge>
              )}
              {result.risc_event_type && (
                <Badge
                  variant="outline"
                  className="text-[10px] bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/30"
                >
                  RISC: {result.risc_event_type}
                </Badge>
              )}
            </div>

            {/* Suggested name/description */}
            {result.signal_name_suggestion && (
              <div className="rounded-lg border border-border bg-muted/20 px-4 py-3 space-y-1">
                <p className="text-sm font-medium text-foreground">
                  {result.signal_name_suggestion}
                </p>
                {result.signal_description_suggestion && (
                  <p className="text-xs text-muted-foreground">
                    {result.signal_description_suggestion}
                  </p>
                )}
              </div>
            )}

            {/* Generated code */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label className="text-xs flex items-center gap-1.5">
                  <Code2 className="h-3 w-3" />
                  Generated Python Code
                </Label>
                <button
                  onClick={copyCode}
                  className="flex items-center gap-1 text-[10px] text-muted-foreground hover:text-foreground transition-colors"
                >
                  {copied ? (
                    <Check className="h-3 w-3 text-green-500" />
                  ) : (
                    <Copy className="h-3 w-3" />
                  )}
                  {copied ? "Copied" : "Copy"}
                </button>
              </div>
              <div className="relative rounded-md border border-border bg-zinc-100 dark:bg-zinc-950 overflow-hidden">
                <div className="absolute left-0 top-0 bottom-0 w-10 bg-zinc-200 dark:bg-zinc-900 border-r border-zinc-300 dark:border-zinc-800 flex flex-col items-end pr-1.5 pt-3 text-[10px] text-zinc-400 dark:text-zinc-600 font-mono select-none overflow-hidden">
                  {result.generated_code.split("\n").map((_, i) => (
                    <div key={i} className="leading-[1.625rem]">
                      {i + 1}
                    </div>
                  ))}
                </div>
                <pre className="text-sm font-mono text-green-700 dark:text-green-400 p-3 pl-12 overflow-x-auto leading-relaxed whitespace-pre">
                  {result.generated_code}
                </pre>
              </div>
            </div>

            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleGenerate}
                disabled={generating}
                className="gap-1.5"
              >
                <RefreshCw className="h-3 w-3" />
                Regenerate
              </Button>
              <Button
                size="sm"
                onClick={handleSave}
                disabled={saving}
                className="gap-1.5 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white"
              >
                {saving ? (
                  <span className="flex items-center gap-1.5">
                    <Spinner /> Saving...
                  </span>
                ) : (
                  <>
                    <Zap className="h-3 w-3" />
                    Save as Signal
                  </>
                )}
              </Button>
            </div>
          </div>
        )}

        {error && (
          <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500 mt-2">
            {error}
          </p>
        )}
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Edit Signal Dialog
// ─────────────────────────────────────────────────────────────────────────────

function EditSignalDialog({
  signal,
  orgId,
  connectorTypes,
  onSave,
  onClose,
}: {
  signal: SignalResponse | null
  orgId: string | null
  connectorTypes: DimensionResponse[]
  onSave: () => void
  onClose: () => void
}) {
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [pythonCode, setPythonCode] = useState("")
  const [selectedConnectors, setSelectedConnectors] = useState<string[]>([])
  const [timeoutMs, setTimeoutMs] = useState("5000")
  const [maxMemoryMb, setMaxMemoryMb] = useState("128")
  const [caepEventType, setCaepEventType] = useState("")
  const [riscEventType, setRiscEventType] = useState("")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (signal) {
      setName(signal.name || signal.properties?.name || "")
      setDescription(
        signal.description || signal.properties?.description || ""
      )
      setPythonCode(signal.properties?.python_source || signal.properties?.python_code || "")
      setSelectedConnectors(
        signal.properties?.connector_types
          ? signal.properties.connector_types.split(",")
          : []
      )
      setTimeoutMs(String(signal.timeout_ms))
      setMaxMemoryMb(String(signal.max_memory_mb))
      setCaepEventType(signal.properties?.caep_event_type || "")
      setRiscEventType(signal.properties?.risc_event_type || "")
      setSaving(false)
      setError(null)
    }
  }, [signal])

  if (!signal) return null

  function toggleConnector(c: string) {
    setSelectedConnectors((prev) =>
      prev.includes(c) ? prev.filter((x) => x !== c) : [...prev, c]
    )
  }

  async function handleSave() {
    if (!orgId) {
      setError("Select an organization before saving the signal.")
      return
    }
    setSaving(true)
    setError(null)
    try {
      const properties: Record<string, string> = {}
      if (name.trim()) properties.name = name.trim()
      if (description.trim()) properties.description = description.trim()
      if (pythonCode.trim()) properties.python_source = pythonCode.trim()
      if (selectedConnectors.length > 0)
        properties.connector_types = selectedConnectors.join(",")
      if (caepEventType.trim())
        properties.caep_event_type = caepEventType.trim()
      if (riscEventType.trim())
        properties.risc_event_type = riscEventType.trim()
      properties.timeout_ms = timeoutMs
      properties.max_memory_mb = maxMemoryMb

      await updateSignal(signal!.id, { properties }, orgId)
      onSave()
      onClose()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save")
      setSaving(false)
    }
  }

  return (
    <Dialog open onOpenChange={(o) => { if (!o) onClose() }}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-primary/10 p-2.5">
              <Pencil className="h-4 w-4 text-primary" />
            </div>
            <div>
              <DialogTitle>Edit Signal</DialogTitle>
              <DialogDescription>
                <code className="text-xs font-mono text-foreground/60">
                  {signal.signal_code}
                </code>
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs">Name</Label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="h-9 text-sm"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Description</Label>
              <Input
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="h-9 text-sm"
              />
            </div>
          </div>

          {/* Python Code */}
          <div className="space-y-1.5">
            <Label className="text-xs flex items-center gap-1.5">
              <Code2 className="h-3 w-3" />
              Python Evaluation Code
            </Label>
            <div className="relative">
              <div className="absolute left-0 top-0 bottom-0 w-10 bg-muted/40 border-r border-border rounded-l-md flex flex-col items-end pr-1.5 pt-3 text-[10px] text-muted-foreground font-mono select-none overflow-hidden">
                {pythonCode.split("\n").map((_, i) => (
                  <div key={i} className="leading-[1.625rem]">
                    {i + 1}
                  </div>
                ))}
              </div>
              <textarea
                value={pythonCode}
                onChange={(e) => setPythonCode(e.target.value)}
                rows={10}
                spellCheck={false}
                className="w-full rounded-md border border-border bg-zinc-100 dark:bg-zinc-950 text-green-700 dark:text-green-400 font-mono text-sm p-3 pl-12 resize-y focus:outline-none focus:ring-2 focus:ring-primary/30 leading-relaxed"
              />
            </div>
          </div>

          {/* Connector types */}
          <div className="space-y-1.5">
            <Label className="text-xs">Connector Types</Label>
            <div className="flex flex-wrap gap-1.5">
              {connectorTypes.map((ct) => (
                <button
                  key={ct.code}
                  type="button"
                  onClick={() => toggleConnector(ct.code)}
                  className={`rounded-md border px-2.5 py-1 text-xs font-medium transition-colors ${
                    selectedConnectors.includes(ct.code)
                      ? "border-primary bg-primary/10 text-primary"
                      : "border-border bg-card text-muted-foreground hover:border-primary/30"
                  }`}
                >
                  {ct.name}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs flex items-center gap-1">
                <Clock className="h-3 w-3" /> Timeout (ms)
              </Label>
              <Input
                type="number"
                value={timeoutMs}
                onChange={(e) => setTimeoutMs(e.target.value)}
                className="h-9 text-sm font-mono"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs flex items-center gap-1">
                <Cpu className="h-3 w-3" /> Max Memory (MB)
              </Label>
              <Input
                type="number"
                value={maxMemoryMb}
                onChange={(e) => setMaxMemoryMb(e.target.value)}
                className="h-9 text-sm font-mono"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs">CAEP Event Type</Label>
              <Input
                value={caepEventType}
                onChange={(e) => setCaepEventType(e.target.value)}
                className="h-9 text-sm"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">RISC Event Type</Label>
              <Input
                value={riscEventType}
                onChange={(e) => setRiscEventType(e.target.value)}
                className="h-9 text-sm"
              />
            </div>
          </div>
        </div>

        {error && (
          <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500 mt-2">
            {error}
          </p>
        )}

        <DialogFooter className="mt-3 gap-2 sm:gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button size="sm" onClick={handleSave} disabled={saving}>
            {saving ? (
              <span className="flex items-center gap-1.5">
                <Spinner /> Saving...
              </span>
            ) : (
              "Save Changes"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Delete Signal Dialog
// ─────────────────────────────────────────────────────────────────────────────

function DeleteSignalDialog({
  signal,
  onConfirm,
  onClose,
}: {
  signal: SignalResponse | null
  onConfirm: (id: string) => Promise<void>
  onClose: () => void
}) {
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!signal) return null

  async function confirm() {
    setDeleting(true)
    setError(null)
    try {
      await onConfirm(signal!.id)
      onClose()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete")
      setDeleting(false)
    }
  }

  return (
    <Dialog open onOpenChange={(o) => { if (!o) onClose() }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-red-500/10 p-2.5">
              <AlertTriangle className="h-4 w-4 text-red-500" />
            </div>
            <div>
              <DialogTitle>Delete Signal</DialogTitle>
              <DialogDescription>
                This will deactivate the signal. It can be restored by an
                administrator.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />
        <p className="text-sm">
          Are you sure you want to delete{" "}
          <strong>{signal.name || signal.signal_code}</strong> (
          <code className="text-xs font-mono">{signal.signal_code}</code>)?
        </p>
        {error && (
          <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500 mt-2">
            {error}
          </p>
        )}
        <DialogFooter className="mt-3 gap-2 sm:gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={deleting}>
            Cancel
          </Button>
          <Button variant="destructive" size="sm" onClick={confirm} disabled={deleting}>
            {deleting ? (
              <span className="flex items-center gap-1.5">
                <Spinner /> Deleting...
              </span>
            ) : (
              "Delete Signal"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Test Suite Dialog
// ─────────────────────────────────────────────────────────────────────────────

function TestSuiteDialog({
  signal,
  orgId,
  datasets,
  onClose,
}: {
  signal: SignalResponse
  orgId: string
  datasets: DatasetResponse[]
  onClose: () => void
}) {
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<TestSuiteResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [testDatasetId, setTestDatasetId] = useState("")

  async function handleRun() {
    setRunning(true)
    setError(null)
    setResult(null)
    try {
      const r = await runSignalTestSuite(signal.id, orgId, testDatasetId || undefined)
      setResult(r)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Test suite failed")
    } finally {
      setRunning(false)
    }
  }

  const resultColorClass = (r: string | null) => {
    if (r === "pass") return "text-green-600 dark:text-green-400"
    if (r === "fail") return "text-red-500"
    if (r === "warning") return "text-amber-500"
    if (r === "error") return "text-red-400"
    return "text-muted-foreground"
  }

  return (
    <Dialog open onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <FlaskConical className="h-4 w-4 text-blue-500" />
            <DialogTitle>Test Suite — {signal.name || signal.signal_code}</DialogTitle>
          </div>
          <DialogDescription>
            Run expected-vs-actual comparisons across all test cases.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">Test Dataset (optional override)</label>
            <select
              className="w-full h-8 rounded-md border border-input bg-background px-2 text-sm"
              value={testDatasetId}
              onChange={(e) => setTestDatasetId(e.target.value)}
              disabled={running}
            >
              <option value="">Use signal's default test dataset</option>
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
          </div>

          {error && (
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-500 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              {error}
            </div>
          )}

          {result && (
            <div className="space-y-3">
              {/* Summary bar */}
              <div className="rounded-lg border border-border bg-muted/30 p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">
                    {result.passed}/{result.total_cases} passed
                  </span>
                  <span className={`text-sm font-semibold ${result.pass_rate >= 0.8 ? "text-green-600" : result.pass_rate >= 0.5 ? "text-amber-500" : "text-red-500"}`}>
                    {Math.round(result.pass_rate * 100)}%
                  </span>
                </div>
                <div className="flex gap-3 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1"><CheckCircle2 className="h-3 w-3 text-green-500" />{result.passed} passed</span>
                  <span className="flex items-center gap-1"><XCircle className="h-3 w-3 text-red-500" />{result.failed} failed</span>
                  {result.errored > 0 && <span className="flex items-center gap-1"><AlertCircle className="h-3 w-3 text-amber-500" />{result.errored} errors</span>}
                </div>
              </div>

              {/* Per-case results */}
              <div className="space-y-1.5 max-h-64 overflow-y-auto pr-1">
                {result.results.map((r, i) => (
                  <div
                    key={r.case_id ?? i}
                    className={`rounded border px-3 py-2 flex items-center justify-between gap-2 text-xs ${r.passed ? "border-green-500/20 bg-green-500/5" : "border-red-500/20 bg-red-500/5"}`}
                  >
                    <div className="min-w-0">
                      <span className="font-medium truncate block">{r.scenario_name || r.case_id || `Case ${i + 1}`}</span>
                      {r.error && <span className="text-red-400 block truncate">{r.error}</span>}
                    </div>
                    <div className="shrink-0 flex items-center gap-2 text-right">
                      <span className="text-muted-foreground">expected: <strong>{r.expected}</strong></span>
                      <span className={`font-semibold ${resultColorClass(r.actual)}`}>{r.actual ?? "—"}</span>
                      <span className="text-muted-foreground">{r.execution_time_ms}ms</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <DialogFooter className="gap-2">
          <Button variant="outline" size="sm" onClick={onClose}>Close</Button>
          <Button size="sm" onClick={handleRun} disabled={running} className="gap-1.5">
            {running ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
            Run Tests
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Execute Live Dialog
// ─────────────────────────────────────────────────────────────────────────────

function ExecuteLiveDialog({
  signal,
  orgId,
  onClose,
}: {
  signal: SignalResponse
  orgId: string
  onClose: () => void
}) {
  const argsSchema: ArgDefinition[] = signal.properties?.signal_args_schema
    ? (() => { try { return JSON.parse(signal.properties.signal_args_schema) } catch { return [] } })()
    : []

  const [args, setArgs] = useState<Record<string, unknown>>(() => {
    const defaults: Record<string, unknown> = {}
    for (const a of argsSchema) {
      if (a.default !== undefined) defaults[a.key] = a.default
    }
    return defaults
  })
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<ExecuteLiveResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function handleRun() {
    setRunning(true)
    setError(null)
    setResult(null)
    try {
      const r = await executeSignalLive(signal.id, orgId, { configurable_args: args })
      setResult(r)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Live execution failed")
    } finally {
      setRunning(false)
    }
  }

  const resultCode = result?.result_code
  const resultColorClass = resultCode === "pass" ? "text-green-600 dark:text-green-400"
    : resultCode === "fail" ? "text-red-500"
    : resultCode === "warning" ? "text-amber-500"
    : "text-muted-foreground"

  return (
    <Dialog open onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-emerald-500" />
            <DialogTitle>Live Execute — {signal.name || signal.signal_code}</DialogTitle>
          </div>
          <DialogDescription>
            Run this signal against the latest collected asset properties.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <SignalArgsForm
            schema={argsSchema}
            values={args}
            onChange={setArgs}
            disabled={running}
          />

          {error && (
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-500 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              {error}
            </div>
          )}

          {result && (
            <div className="rounded-lg border border-border bg-muted/30 p-3 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Result</span>
                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                  <span>{result.dataset_row_count} rows</span>
                  <span>{result.execution_time_ms}ms</span>
                  <span className={`font-semibold text-sm ${resultColorClass}`}>{result.result_code?.toUpperCase() ?? result.status.toUpperCase()}</span>
                </div>
              </div>
              {result.result_summary && (
                <p className="text-sm text-muted-foreground">{result.result_summary}</p>
              )}
              {result.result_details.length > 0 && (
                <div className="space-y-1 max-h-48 overflow-y-auto pr-1">
                  {result.result_details.map((d, i) => (
                    <div key={i} className="text-xs bg-background rounded border border-border px-2 py-1 font-mono">
                      {JSON.stringify(d)}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        <DialogFooter className="gap-2">
          <Button variant="outline" size="sm" onClick={onClose}>Close</Button>
          <Button size="sm" onClick={handleRun} disabled={running} className="gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white border-0">
            {running ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Activity className="h-3.5 w-3.5" />}
            Execute Live
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Signal Card
// ─────────────────────────────────────────────────────────────────────────────

function SignalCard({
  signal,
  onEdit,
  onValidate,
  onDelete,
  onPromote,
  onTestSuite,
  onExecuteLive,
}: {
  signal: SignalResponse
  onEdit?: () => void
  onValidate: () => void
  onDelete?: () => void
  onPromote?: () => void
  onTestSuite?: () => void
  onExecuteLive?: () => void
}) {
  const connectorTypes = signal.properties?.connector_types
    ? signal.properties.connector_types.split(",")
    : []

  const statusCode = signal.signal_status_code?.toLowerCase()
  const rowBorderCls = statusCode === "active" ? "border-l-green-500"
    : statusCode === "draft" ? "border-l-amber-500"
    : statusCode === "deprecated" ? "border-l-red-500"
    : "border-l-primary"

  return (
    <div className={`rounded-xl border border-l-[3px] ${rowBorderCls} bg-card hover:bg-muted/20 transition-colors group`}>
      <div className="p-4 space-y-3">
        {/* Header row */}
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-0.5">
              <h3 className="text-sm font-semibold text-foreground truncate">
                {signal.name || signal.signal_code}
              </h3>
              {statusBadge(signal.signal_status_code, signal.signal_status_name)}
            </div>
            <div className="flex items-center gap-1">
              <code className="text-[11px] font-mono text-muted-foreground">
                {signal.signal_code}
              </code>
              <button onClick={() => copyToClipboard(signal.signal_code)} className="opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-foreground" title="Copy code">
                <Copy className="h-3 w-3" />
              </button>
            </div>
          </div>
          <div className="flex items-center gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
            {onEdit && (
              <button
                onClick={onEdit}
                className="rounded-md p-1.5 hover:bg-muted transition-colors"
                title="Edit"
              >
                <Pencil className="h-3.5 w-3.5 text-muted-foreground" />
              </button>
            )}
            <button
              onClick={onValidate}
              className="rounded-md p-1.5 hover:bg-muted transition-colors"
              title="Validate"
            >
              <ShieldCheck className="h-3.5 w-3.5 text-muted-foreground" />
            </button>
            {onTestSuite && (
              <button
                onClick={onTestSuite}
                className="rounded-md p-1.5 hover:bg-blue-500/10 transition-colors"
                title="Run Test Suite"
              >
                <FlaskConical className="h-3.5 w-3.5 text-blue-500" />
              </button>
            )}
            {onExecuteLive && (
              <button
                onClick={onExecuteLive}
                className="rounded-md p-1.5 hover:bg-emerald-500/10 transition-colors"
                title="Execute Live"
              >
                <Activity className="h-3.5 w-3.5 text-emerald-500" />
              </button>
            )}
            {onPromote && (
              <button
                onClick={onPromote}
                className="rounded-md p-1.5 hover:bg-cyan-500/10 transition-colors"
                title="Promote to Control Test"
              >
                <ArrowUpFromLine className="h-3.5 w-3.5 text-cyan-500" />
              </button>
            )}
            {onDelete && (
              <button
                onClick={onDelete}
                className="rounded-md p-1.5 hover:bg-red-500/10 transition-colors"
                title="Delete"
              >
                <Trash2 className="h-3.5 w-3.5 text-red-500" />
              </button>
            )}
          </div>
        </div>

        {/* Description */}
        {(signal.description || signal.properties?.description) && (
          <p className="text-xs text-muted-foreground line-clamp-2">
            {signal.description || signal.properties?.description}
          </p>
        )}

        {/* Badges row */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <Badge
            variant="outline"
            className="text-[10px] bg-muted/40 font-mono"
          >
            <GitBranch className="h-2.5 w-2.5 mr-0.5" />v
            {signal.version_number}
          </Badge>

          {connectorTypes.map((ct) => (
            <Badge
              key={ct}
              variant="outline"
              className="text-[10px] bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/30"
            >
              {ct}
            </Badge>
          ))}

          {signal.properties?.caep_event_type && (
            <Badge
              variant="outline"
              className="text-[10px] bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border-cyan-500/30"
            >
              CAEP: {signal.properties.caep_event_type}
            </Badge>
          )}
          {signal.properties?.risc_event_type && (
            <Badge
              variant="outline"
              className="text-[10px] bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/30"
            >
              RISC: {signal.properties.risc_event_type}
            </Badge>
          )}
        </div>

        {/* Meta row */}
        <div className="flex items-center gap-3 text-[10px] text-muted-foreground pt-1 border-t border-border/50">
          {signal.python_hash && (
            <span className="flex items-center gap-1 font-mono">
              <Hash className="h-2.5 w-2.5" />
              {truncateHash(signal.python_hash)}
            </span>
          )}
          <span className="flex items-center gap-1">
            <Clock className="h-2.5 w-2.5" />
            {signal.timeout_ms}ms
          </span>
          <span className="flex items-center gap-1">
            <Cpu className="h-2.5 w-2.5" />
            {signal.max_memory_mb}MB
          </span>
          <span className="ml-auto">{formatDate(signal.updated_at)}</span>
        </div>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Signals Page
// ─────────────────────────────────────────────────────────────────────────────

export default function SignalsPage() {
  const { selectedOrgId, selectedWorkspaceId, ready } = useSandboxOrgWorkspace()
  const { canWrite } = useAccess()
  const canModify = canWrite("sandbox")
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()

  const [signals, setSignals] = useState<SignalResponse[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [statuses, setStatuses] = useState<DimensionResponse[]>([])
  const [connectorTypes, setConnectorTypes] = useState<DimensionResponse[]>([])
  const [datasets, setDatasets] = useState<DatasetResponse[]>([])
  const [error, setError] = useState<string | null>(null)

  // Filters — persisted in URL so they survive navigation
  const [searchInput, setSearchInput] = useState(() => searchParams.get("q") ?? "")
  const [searchQuery, setSearchQuery] = useState(() => searchParams.get("q") ?? "")
  const [statusFilter, setStatusFilter] = useState(() => searchParams.get("status") ?? "")

  // Debounce search input → searchQuery
  useEffect(() => {
    const t = setTimeout(() => setSearchQuery(searchInput), 300)
    return () => clearTimeout(t)
  }, [searchInput])

  // Sync filters → URL
  useEffect(() => {
    const params = new URLSearchParams()
    if (searchQuery) params.set("q", searchQuery)
    if (statusFilter) params.set("status", statusFilter)
    const qs = params.toString()
    router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false })
  }, [searchQuery, statusFilter, pathname, router])

  // Success feedback
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const showSuccess = (msg: string) => {
    setSuccessMessage(msg)
    setTimeout(() => setSuccessMessage(null), 3000)
  }

  // Dialog state
  const [createOpen, setCreateOpen] = useState(false)
  const [aiGenerateOpen, setAiGenerateOpen] = useState(false)
  const [editingSignal, setEditingSignal] = useState<SignalResponse | null>(null)
  const [deletingSignal, setDeletingSignal] = useState<SignalResponse | null>(null)
  const [validating, setValidating] = useState<string | null>(null)

  // Test Suite + Execute Live state
  const [testSuiteSignal, setTestSuiteSignal] = useState<SignalResponse | null>(null)
  const [executeLiveSignal, setExecuteLiveSignal] = useState<SignalResponse | null>(null)

  // Promote state
  const [promotingSignal, setPromotingSignal] = useState<SignalResponse | null>(null)
  const [promoteAssetDialogOpen, setPromoteAssetDialogOpen] = useState(false)
  const [promoting, setPromoting] = useState(false)
  const [promoteError, setPromoteError] = useState<string | null>(null)

  // Publish to Global Library
  async function handlePublishToLibrary(signal: SignalResponse) {
    if (!selectedOrgId) return
    try {
      const signalName = signal.name || signal.properties?.name || signal.signal_code
      const globalCode = signalName.toLowerCase().replace(/[^a-z0-9]/g, "_").replace(/__+/g, "_").replace(/^_|_$/g, "")
      await publishGlobalControlTest(selectedOrgId, {
        source_signal_id: signal.id,
        global_code: globalCode,
        properties: {
          name: signalName,
          description: signal.description || signal.properties?.description || "",
          category: "compliance",
        },
      })
      showSuccess("Signal published to Global Control Test Library")
    } catch (e) {
      setPromoteError(e instanceof Error ? e.message : "Publish failed")
    }
  }

  async function handlePromoteWithAsset(connectorId: string) {
    if (!promotingSignal) return
    setPromoting(true)
    setPromoteError(null)
    try {
      await promoteSignal(promotingSignal.id, { linked_asset_id: connectorId, workspace_id: selectedWorkspaceId ?? undefined })
      setPromoteAssetDialogOpen(false)
      setPromotingSignal(null)
      showSuccess(`Signal promoted to Control Test`)
      await loadSignals()
    } catch (e) {
      setPromoteError(e instanceof Error ? e.message : "Promotion failed")
    } finally {
      setPromoting(false)
    }
  }

  const loadSignals = useCallback(async () => {
    if (!selectedOrgId) return
    setLoading(true)
    setError(null)
    try {
      const res = await listSignals({
        org_id: selectedOrgId,
        workspace_id: selectedWorkspaceId ?? undefined,
        signal_status_code: statusFilter || undefined,
        search: searchQuery || undefined,
      })
      setSignals(res.items)
      setTotal(res.total)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load signals")
    } finally {
      setLoading(false)
    }
  }, [selectedOrgId, selectedWorkspaceId, statusFilter, searchQuery])

  const loadDimensions = useCallback(async () => {
    if (!selectedOrgId) return
    try {
      const [s, ct, ds] = await Promise.all([
        listSignalStatuses(),
        listConnectorTypes(),
        listDatasets(selectedOrgId).catch(() => ({ items: [], total: 0 })),
      ])
      setStatuses(s)
      setConnectorTypes(ct)
      setDatasets(ds.items)
    } catch {
      // Non-critical
    }
  }, [selectedOrgId])

  useEffect(() => {
    if (ready) loadDimensions()
  }, [loadDimensions, ready])

  useEffect(() => {
    if (ready) loadSignals()
  }, [loadSignals, ready])

  async function handleValidate(id: string) {
    setValidating(id)
    try {
      await validateSignal(id)
      await loadSignals()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Validation failed")
    } finally {
      setValidating(null)
    }
  }

  async function handleDelete(id: string) {
    if (!selectedOrgId) {
      setError("Select an organization before deleting a signal.")
      return
    }
    await deleteSignal(selectedOrgId, id)
    showSuccess("Signal deleted")
    await loadSignals()
  }

  return (
    <div className="w-full space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="rounded-xl bg-amber-500/10 p-3 shrink-0">
            <Zap className="h-6 w-6 text-amber-500" />
          </div>
          <div className="flex flex-col gap-1">
            <h2 className="text-2xl font-semibold text-foreground">
              Signal Builder
            </h2>
            <p className="text-sm text-muted-foreground">
              Build and test Python-based compliance detection signals
            </p>
          </div>
        </div>
        {canModify && (
          <div className="flex flex-wrap items-center gap-2 shrink-0">
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5"
              onClick={() => setCreateOpen(true)}
            >
              <Plus className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Create Signal</span>
              <span className="sm:hidden">Create</span>
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="gap-1.5 border-blue-300 text-blue-600 hover:bg-blue-50"
              onClick={() => router.push("/sandbox/signals/new")}
            >
              <GitBranch className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Spec Builder</span>
              <span className="sm:hidden">Spec</span>
            </Button>
            <Button
              size="sm"
              className="gap-1.5 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white border-0"
              onClick={() => setAiGenerateOpen(true)}
            >
              <Sparkles className="h-3.5 w-3.5" />
              AI Generate
            </Button>
          </div>
        )}
      </div>

      {/* Filter bar */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-3">
        <div className="flex flex-wrap items-center gap-2 flex-1">
          <div className="relative flex-1 min-w-[180px] max-w-xs">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search signals..."
              className="h-9 pl-9 text-sm"
            />
          </div>
          <select
            className="h-9 rounded-md border border-input bg-background px-3 text-sm"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Statuses</option>
            {statuses.map((s) => (
              <option key={s.code} value={s.code}>
                {s.name}
              </option>
            ))}
          </select>
          <Button
            variant="ghost"
            size="sm"
            onClick={loadSignals}
            className="gap-1.5 text-muted-foreground"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </Button>
        </div>
        <span className="text-xs text-muted-foreground sm:ml-auto">
          {total} signal{total !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Success feedback */}
      {successMessage && (
        <div className="rounded-lg border border-green-500/30 bg-green-500/10 px-4 py-3 text-sm text-green-600 dark:text-green-400">
          {successMessage}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-500 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          {error}
          <button
            onClick={() => setError(null)}
            className="ml-auto text-red-400 hover:text-red-300"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((n) => (
            <div
              key={n}
              className="rounded-2xl border border-border bg-card p-4 space-y-3 animate-pulse"
            >
              <div className="flex items-center gap-2">
                <div className="h-4 w-32 bg-muted rounded" />
                <div className="h-4 w-16 bg-muted rounded" />
              </div>
              <div className="h-3 w-48 bg-muted rounded" />
              <div className="flex gap-1.5">
                <div className="h-5 w-12 bg-muted rounded" />
                <div className="h-5 w-16 bg-muted rounded" />
              </div>
              <div className="flex gap-3">
                <div className="h-3 w-20 bg-muted rounded" />
                <div className="h-3 w-16 bg-muted rounded" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && signals.length === 0 && (
        <div className="rounded-xl border border-border bg-muted/20 px-5 py-12 text-center">
          <Zap className="h-10 w-10 text-amber-500/30 mx-auto mb-3" />
          <p className="text-sm font-medium text-foreground mb-1">
            No signals yet
          </p>
          <p className="text-xs text-muted-foreground mb-4">
            Create your first signal manually or use AI to generate one from a
            plain-English description.
          </p>
          {canModify && (
            <div className="flex items-center justify-center gap-2">
              <Button
                variant="outline"
                size="sm"
                className="gap-1.5"
                onClick={() => setCreateOpen(true)}
              >
                <Plus className="h-3.5 w-3.5" />
                Create Signal
              </Button>
              <Button
                size="sm"
                className="gap-1.5 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white border-0"
                onClick={() => setAiGenerateOpen(true)}
              >
                <Sparkles className="h-3.5 w-3.5" />
                AI Generate
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Signal grid — 3 per row */}
      {!loading && signals.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {signals.map((s) => (
            <SignalCard
              key={s.id}
              signal={s}
              onEdit={canModify ? () => setEditingSignal(s) : undefined}
              onValidate={() => handleValidate(s.id)}
              onDelete={canModify ? () => setDeletingSignal(s) : undefined}
              onPromote={canModify && s.signal_status_code === "validated" ? () => { setPromotingSignal(s); setPromoteAssetDialogOpen(true) } : undefined}
              onTestSuite={selectedOrgId ? () => setTestSuiteSignal(s) : undefined}
              onExecuteLive={selectedOrgId ? () => setExecuteLiveSignal(s) : undefined}
            />
          ))}
        </div>
      )}

      {/* Dialogs */}
      <CreateSignalDialog
        open={createOpen}
        orgId={selectedOrgId ?? null}
        workspaceId={selectedWorkspaceId ?? null}
        connectorTypes={connectorTypes}
        onCreate={loadSignals}
        onClose={() => setCreateOpen(false)}
      />
      <AIGenerateDialog
        open={aiGenerateOpen}
        orgId={selectedOrgId ?? null}
        workspaceId={selectedWorkspaceId ?? null}
        connectorTypes={connectorTypes}
        datasets={datasets}
        onSaved={loadSignals}
        onClose={() => setAiGenerateOpen(false)}
      />
      <EditSignalDialog
        signal={editingSignal}
        orgId={selectedOrgId ?? null}
        connectorTypes={connectorTypes}
        onSave={loadSignals}
        onClose={() => setEditingSignal(null)}
      />
      <DeleteSignalDialog
        signal={deletingSignal}
        onConfirm={handleDelete}
        onClose={() => setDeletingSignal(null)}
      />

      {/* Test Suite Dialog */}
      {testSuiteSignal && selectedOrgId && (
        <SignalTestResults
          signal={testSuiteSignal}
          orgId={selectedOrgId}
          onClose={() => setTestSuiteSignal(null)}
        />
      )}

      {/* Execute Live Dialog */}
      {executeLiveSignal && selectedOrgId && (
        <ExecuteLiveDialog
          signal={executeLiveSignal}
          orgId={selectedOrgId}
          onClose={() => setExecuteLiveSignal(null)}
        />
      )}

      {/* Promote to Control Test — asset selector */}
      {promoteAssetDialogOpen && selectedOrgId && (
        <AssetSelectorDialog
          open={promoteAssetDialogOpen}
          orgId={selectedOrgId}
          currentAssetId={null}
          onSelect={handlePromoteWithAsset}
          onClose={() => { setPromoteAssetDialogOpen(false); setPromotingSignal(null); setPromoteError(null) }}
        />
      )}

      {/* Promote error dialog */}
      {promoteError && (
        <Dialog open={!!promoteError} onOpenChange={(v) => !v && setPromoteError(null)}>
          <DialogContent className="max-w-sm">
            <DialogHeader>
              <DialogTitle>Promotion Failed</DialogTitle>
              <DialogDescription>{promoteError}</DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button onClick={() => setPromoteError(null)}>OK</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  )
}
