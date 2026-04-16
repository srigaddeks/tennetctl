"use client"

import { useEffect, useState, useCallback, useMemo } from "react"
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
  ShieldAlert,
  Search,
  Plus,
  Pencil,
  Trash2,
  AlertTriangle,
  Play,
  CheckCircle2,
  XCircle,
  GitBranch,
  RefreshCw,
  ChevronRight,
  ChevronDown,
  Zap,
  Copy,
  X,
  Loader2,
} from "lucide-react"
import {
  listThreatTypes,
  listThreatSeverities,
  listSignals,
  createThreatType,
  updateThreatType,
  deleteThreatType,
  simulateThreat,
} from "@/lib/api/sandbox"
import { copyToClipboard } from "@/lib/utils/sandbox-helpers"
import { useAccess } from "@/components/providers/AccessProvider"
import { useSandboxOrgWorkspace } from "@/lib/context/SandboxOrgWorkspaceContext"
import type {
  ThreatTypeResponse,
  DimensionResponse,
  SignalResponse,
} from "@/lib/api/sandbox"

// ─────────────────────────────────────────────────────────────────────────────
// Severity styles
// ─────────────────────────────────────────────────────────────────────────────

const SEVERITY_STYLES: Record<string, string> = {
  info: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/30",
  low: "bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 border-yellow-500/30",
  medium: "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30",
  high: "bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/30",
  critical: "bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/30",
}

const SEVERITY_DOT: Record<string, string> = {
  info: "bg-blue-500",
  low: "bg-yellow-500",
  medium: "bg-amber-500",
  high: "bg-orange-500",
  critical: "bg-red-500",
}

// border-l color by severity
const SEVERITY_BORDER: Record<string, string> = {
  critical: "border-l-red-500",
  high: "border-l-orange-500",
  medium: "border-l-amber-500",
  low: "border-l-yellow-500",
  info: "border-l-blue-500",
}

// KPI card colors by severity
const SEVERITY_KPI: Record<string, { border: string; num: string; icon: string; bg: string }> = {
  critical: { border: "border-l-red-500", num: "text-red-500", icon: "text-red-500", bg: "bg-red-500/10" },
  high: { border: "border-l-orange-500", num: "text-orange-500", icon: "text-orange-500", bg: "bg-orange-500/10" },
  medium: { border: "border-l-amber-500", num: "text-amber-600 dark:text-amber-400", icon: "text-amber-500", bg: "bg-amber-500/10" },
  low: { border: "border-l-yellow-500", num: "text-yellow-600 dark:text-yellow-400", icon: "text-yellow-500", bg: "bg-yellow-500/10" },
  info: { border: "border-l-blue-500", num: "text-blue-600 dark:text-blue-400", icon: "text-blue-500", bg: "bg-blue-500/10" },
}

function severityBadge(code: string, name?: string) {
  return (
    <Badge
      variant="outline"
      className={`text-[10px] font-semibold ${SEVERITY_STYLES[code] ?? "bg-muted text-muted-foreground"}`}
    >
      <span
        className={`inline-block h-1.5 w-1.5 rounded-full mr-1 ${SEVERITY_DOT[code] ?? "bg-muted-foreground"}`}
      />
      {name || code}
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
// Expression tree helpers
// ─────────────────────────────────────────────────────────────────────────────

interface ExpressionNode {
  operator?: string
  signal_code?: string
  expected_result?: string
  conditions?: ExpressionNode[]
}

const DEFAULT_EXPRESSION: ExpressionNode = {
  operator: "AND",
  conditions: [
    { signal_code: "", expected_result: "fail" },
  ],
}

function countSignals(node: ExpressionNode): number {
  if (node.signal_code !== undefined) return 1
  if (!node.conditions) return 0
  return node.conditions.reduce((sum, c) => sum + countSignals(c), 0)
}

function getOperators(node: ExpressionNode): string[] {
  const ops: string[] = []
  if (node.operator) ops.push(node.operator)
  if (node.conditions) {
    node.conditions.forEach((c) => ops.push(...getOperators(c)))
  }
  return ops
}

function summarizeTree(tree: ExpressionNode | null): string {
  if (!tree) return "No expression defined"
  const signalCount = countSignals(tree)
  const ops = [...new Set(getOperators(tree))]
  return `${signalCount} signal${signalCount !== 1 ? "s" : ""} · ${ops.join("/") || "leaf"}`
}

function extractSignalCodes(node: ExpressionNode): string[] {
  if (node.signal_code) return [node.signal_code]
  if (!node.conditions) return []
  return node.conditions.flatMap(extractSignalCodes)
}

// ─────────────────────────────────────────────────────────────────────────────
// Expression Tree Visual Preview
// ─────────────────────────────────────────────────────────────────────────────

function ExpressionTreePreview({
  node,
  depth = 0,
}: {
  node: ExpressionNode
  depth?: number
}) {
  const [expanded, setExpanded] = useState(depth < 2)

  if (node.signal_code !== undefined) {
    const resultColor =
      node.expected_result === "pass"
        ? "text-green-500"
        : node.expected_result === "fail"
          ? "text-red-500"
          : "text-yellow-500"

    return (
      <div
        className="flex items-center gap-2 py-1 pl-2"
        style={{ marginLeft: depth * 16 }}
      >
        <Zap className="h-3 w-3 text-amber-500 shrink-0" />
        <code className="text-xs font-mono text-foreground">
          {node.signal_code || "(empty)"}
        </code>
        <span className={`text-[10px] font-medium ${resultColor}`}>
          = {node.expected_result || "?"}
        </span>
      </div>
    )
  }

  if (!node.conditions?.length) {
    return (
      <div
        className="text-xs text-muted-foreground italic py-1"
        style={{ marginLeft: depth * 16 }}
      >
        Empty group
      </div>
    )
  }

  return (
    <div style={{ marginLeft: depth * 16 }}>
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 py-1 hover:bg-muted/30 rounded px-1 -ml-1 transition-colors"
      >
        {expanded ? (
          <ChevronDown className="h-3 w-3 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-3 w-3 text-muted-foreground" />
        )}
        <Badge
          variant="outline"
          className={`text-[10px] font-bold ${
            node.operator === "NOT"
              ? "bg-red-500/10 text-red-500 border-red-500/30"
              : "bg-primary/10 text-primary border-primary/30"
          }`}
        >
          {node.operator}
        </Badge>
        <span className="text-[10px] text-muted-foreground">
          ({node.conditions.length} condition
          {node.conditions.length !== 1 ? "s" : ""})
        </span>
      </button>
      {expanded &&
        node.conditions.map((c, i) => (
          <ExpressionTreePreview key={i} node={c} depth={depth + 1} />
        ))}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Expression Tree JSON Editor with Preview
// ─────────────────────────────────────────────────────────────────────────────

function ExpressionTreeEditor({
  value,
  onChange,
  signals,
}: {
  value: ExpressionNode
  onChange: (v: ExpressionNode) => void
  signals: SignalResponse[]
}) {
  const [jsonText, setJsonText] = useState(JSON.stringify(value, null, 2))
  const [parseError, setParseError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<"editor" | "preview">("editor")

  useEffect(() => {
    setJsonText(JSON.stringify(value, null, 2))
  }, [value])

  function handleJsonChange(text: string) {
    setJsonText(text)
    try {
      const parsed = JSON.parse(text)
      setParseError(null)
      onChange(parsed)
    } catch (e) {
      setParseError(e instanceof Error ? e.message : "Invalid JSON")
    }
  }

  return (
    <div className="space-y-2">
      {/* Tab bar */}
      <div className="flex items-center gap-1 border-b border-border">
        <button
          onClick={() => setActiveTab("editor")}
          className={`px-3 py-1.5 text-xs font-medium border-b-2 transition-colors ${
            activeTab === "editor"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          JSON Editor
        </button>
        <button
          onClick={() => setActiveTab("preview")}
          className={`px-3 py-1.5 text-xs font-medium border-b-2 transition-colors ${
            activeTab === "preview"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          Tree Preview
        </button>
      </div>

      {activeTab === "editor" && (
        <div className="space-y-2">
          <div className="relative">
            <div className="absolute left-0 top-0 bottom-0 w-8 bg-muted/40 border-r border-border rounded-l-md flex flex-col items-end pr-1 pt-3 text-[9px] text-muted-foreground font-mono select-none overflow-hidden">
              {jsonText.split("\n").map((_, i) => (
                <div key={i} className="leading-[1.5rem]">
                  {i + 1}
                </div>
              ))}
            </div>
            <textarea
              value={jsonText}
              onChange={(e) => handleJsonChange(e.target.value)}
              rows={12}
              spellCheck={false}
              className={`w-full rounded-md border bg-zinc-100 dark:bg-zinc-950 text-green-700 dark:text-green-400 font-mono text-xs p-3 pl-10 resize-y focus:outline-none focus:ring-2 focus:ring-primary/30 leading-relaxed ${
                parseError ? "border-red-500/50" : "border-border"
              }`}
            />
          </div>
          {parseError && (
            <p className="text-[10px] text-red-500 flex items-center gap-1">
              <XCircle className="h-3 w-3 shrink-0" />
              {parseError}
            </p>
          )}

          {/* Quick-insert helpers */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[10px] text-muted-foreground">
              Quick insert:
            </span>
            {signals.slice(0, 6).map((s) => (
              <button
                key={s.id}
                type="button"
                onClick={() => {
                  try {
                    const parsed = JSON.parse(jsonText)
                    if (!parsed.conditions) parsed.conditions = []
                    parsed.conditions.push({
                      signal_code: s.signal_code,
                      expected_result: "fail",
                    })
                    const newText = JSON.stringify(parsed, null, 2)
                    setJsonText(newText)
                    onChange(parsed)
                    setParseError(null)
                  } catch {
                    // ignore
                  }
                }}
                className="rounded border border-border bg-card px-2 py-0.5 text-[10px] font-mono text-amber-500 hover:border-amber-500/30 transition-colors"
              >
                + {s.signal_code}
              </button>
            ))}
          </div>
        </div>
      )}

      {activeTab === "preview" && (
        <div className="rounded-md border border-border bg-card p-3 min-h-[200px]">
          {parseError ? (
            <p className="text-xs text-red-500 italic">
              Fix JSON errors to see preview
            </p>
          ) : (
            <ExpressionTreePreview node={value} />
          )}
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Create Threat Type Dialog
// ─────────────────────────────────────────────────────────────────────────────

function CreateThreatTypeDialog({
  open,
  orgId,
  workspaceId,
  severities,
  signals,
  onCreate,
  onClose,
}: {
  open: boolean
  orgId: string
  workspaceId: string | null
  severities: DimensionResponse[]
  signals: SignalResponse[]
  onCreate: () => void
  onClose: () => void
}) {
  const [code, setCode] = useState("")
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [severityCode, setSeverityCode] = useState("")
  const [expressionTree, setExpressionTree] =
    useState<ExpressionNode>(DEFAULT_EXPRESSION)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [codeManuallyEdited, setCodeManuallyEdited] = useState(false)

  useEffect(() => {
    if (open) {
      setCode("")
      setName("")
      setDescription("")
      setSeverityCode(severities[0]?.code ?? "")
      setExpressionTree({
        operator: "AND",
        conditions: [{ signal_code: "", expected_result: "fail" }],
      })
      setSaving(false)
      setError(null)
      setCodeManuallyEdited(false)
    }
  }, [open, severities])

  // Auto-generate code from name (only if user hasn't manually edited code)
  useEffect(() => {
    if (!codeManuallyEdited) {
      setCode(
        name
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, "_")
          .replace(/^_|_$/g, "")
      )
    }
  }, [name, codeManuallyEdited])

  async function handleCreate() {
    if (!code.trim()) {
      setError("Threat code is required.")
      return
    }
    if (!severityCode) {
      setError("Severity is required.")
      return
    }
    setSaving(true)
    setError(null)
    try {
      const properties: Record<string, string> = {}
      if (name.trim()) properties.name = name.trim()
      if (description.trim()) properties.description = description.trim()

      await createThreatType({
        org_id: orgId,
        workspace_id: workspaceId || undefined,
        threat_code: code.trim(),
        severity_code: severityCode,
        expression_tree: expressionTree,
        properties,
      })
      onCreate()
      onClose()
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Failed to create threat type"
      )
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-red-500/10 p-2.5">
              <Plus className="h-4 w-4 text-red-500" />
            </div>
            <div>
              <DialogTitle>Create Threat Type</DialogTitle>
              <DialogDescription>
                Define a threat type by composing signals into a boolean
                expression tree.
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
                placeholder="Unauthorized Access Threat"
                className="h-9 text-sm"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">
                Threat Code{" "}
                <span className="text-muted-foreground">(unique)</span>
              </Label>
              <Input
                value={code}
                onChange={(e) => {
                  setCode(e.target.value)
                  setCodeManuallyEdited(true)
                }}
                placeholder="unauthorized_access"
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
              placeholder="Detects unauthorized access attempts across multiple signals..."
              className="h-9 text-sm"
            />
          </div>

          {/* Severity */}
          <div className="space-y-1.5">
            <Label className="text-xs">Severity</Label>
            <div className="flex items-center gap-2 flex-wrap">
              {severities.map((s) => (
                <button
                  key={s.code}
                  type="button"
                  onClick={() => setSeverityCode(s.code)}
                  className={`flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs font-medium transition-all ${
                    severityCode === s.code
                      ? SEVERITY_STYLES[s.code] +
                        " ring-2 ring-offset-1 ring-offset-background"
                      : "border-border bg-card text-muted-foreground hover:border-border/80"
                  }`}
                >
                  <span
                    className={`h-2 w-2 rounded-full ${SEVERITY_DOT[s.code] ?? "bg-muted-foreground"}`}
                  />
                  {s.name}
                </button>
              ))}
            </div>
          </div>

          {/* Expression tree */}
          <div className="space-y-1.5">
            <Label className="text-xs flex items-center gap-1.5">
              <ShieldAlert className="h-3 w-3" />
              Expression Tree
            </Label>
            <ExpressionTreeEditor
              value={expressionTree}
              onChange={setExpressionTree}
              signals={signals}
            />
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
              "Create Threat Type"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Edit Threat Type Dialog
// ─────────────────────────────────────────────────────────────────────────────

function EditThreatTypeDialog({
  threatType,
  orgId,
  severities,
  signals,
  onSave,
  onClose,
}: {
  threatType: ThreatTypeResponse | null
  orgId: string
  severities: DimensionResponse[]
  signals: SignalResponse[]
  onSave: () => void
  onClose: () => void
}) {
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [severityCode, setSeverityCode] = useState("")
  const [expressionTree, setExpressionTree] =
    useState<ExpressionNode>(DEFAULT_EXPRESSION)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (threatType) {
      setName(threatType.name || threatType.properties?.name || "")
      setDescription(
        threatType.description || threatType.properties?.description || ""
      )
      setSeverityCode(threatType.severity_code)
      setExpressionTree(
        threatType.expression_tree ?? {
          operator: "AND",
          conditions: [],
        }
      )
      setSaving(false)
      setError(null)
    }
  }, [threatType])

  if (!threatType) return null

  async function handleSave() {
    setSaving(true)
    setError(null)
    try {
      const properties: Record<string, string> = {}
      if (name.trim()) properties.name = name.trim()
      if (description.trim()) properties.description = description.trim()

      await updateThreatType(threatType!.id, orgId, {
        severity_code: severityCode,
        expression_tree: expressionTree,
        properties,
      })
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
              <DialogTitle>Edit Threat Type</DialogTitle>
              <DialogDescription>
                <code className="text-xs font-mono text-foreground/60">
                  {threatType.threat_code}
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

          <div className="space-y-1.5">
            <Label className="text-xs">Severity</Label>
            <div className="flex items-center gap-2 flex-wrap">
              {severities.map((s) => (
                <button
                  key={s.code}
                  type="button"
                  onClick={() => setSeverityCode(s.code)}
                  className={`flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs font-medium transition-all ${
                    severityCode === s.code
                      ? SEVERITY_STYLES[s.code] +
                        " ring-2 ring-offset-1 ring-offset-background"
                      : "border-border bg-card text-muted-foreground hover:border-border/80"
                  }`}
                >
                  <span
                    className={`h-2 w-2 rounded-full ${SEVERITY_DOT[s.code] ?? "bg-muted-foreground"}`}
                  />
                  {s.name}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs flex items-center gap-1.5">
              <ShieldAlert className="h-3 w-3" />
              Expression Tree
            </Label>
            <ExpressionTreeEditor
              value={expressionTree}
              onChange={setExpressionTree}
              signals={signals}
            />
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
// Delete Threat Type Dialog
// ─────────────────────────────────────────────────────────────────────────────

function DeleteThreatTypeDialog({
  threatType,
  onConfirm,
  onClose,
}: {
  threatType: ThreatTypeResponse | null
  onConfirm: (id: string) => Promise<void>
  onClose: () => void
}) {
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!threatType) return null

  async function confirm() {
    setDeleting(true)
    setError(null)
    try {
      await onConfirm(threatType!.id)
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
              <DialogTitle>Delete Threat Type</DialogTitle>
              <DialogDescription>
                This will deactivate the threat type and any control tests linked to
                it.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />
        <p className="text-sm">
          Are you sure you want to delete{" "}
          <strong>{threatType.name || threatType.threat_code}</strong> (
          <code className="text-xs font-mono">{threatType.threat_code}</code>)?
        </p>
        {error && (
          <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500 mt-2">
            {error}
          </p>
        )}
        <DialogFooter className="mt-3 gap-2 sm:gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onClose}
            disabled={deleting}
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={confirm}
            disabled={deleting}
          >
            {deleting ? (
              <span className="flex items-center gap-1.5">
                <Spinner /> Deleting...
              </span>
            ) : (
              "Delete Threat Type"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Simulate Dialog
// ─────────────────────────────────────────────────────────────────────────────

function SimulateDialog({
  threatType,
  onClose,
}: {
  threatType: ThreatTypeResponse | null
  onClose: () => void
}) {
  const [signalResults, setSignalResults] = useState<Record<string, string>>(
    {}
  )
  const [simulating, setSimulating] = useState(false)
  const [result, setResult] = useState<{
    is_triggered: boolean
    evaluation_trace: any[]
  } | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (threatType?.expression_tree) {
      const codes = extractSignalCodes(threatType.expression_tree)
      const initial: Record<string, string> = {}
      codes.forEach((c) => {
        if (c) initial[c] = "pass"
      })
      setSignalResults(initial)
      setResult(null)
      setError(null)
    }
  }, [threatType])

  if (!threatType) return null

  async function handleSimulate() {
    setSimulating(true)
    setError(null)
    setResult(null)
    try {
      const res = await simulateThreat(threatType!.id, signalResults)
      setResult(res)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Simulation failed")
    } finally {
      setSimulating(false)
    }
  }

  const signalCodes = Object.keys(signalResults)

  return (
    <Dialog open onOpenChange={(o) => { if (!o) onClose() }}>
      <DialogContent className="sm:max-w-xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-purple-500/10 p-2.5">
              <Play className="h-4 w-4 text-purple-500" />
            </div>
            <div>
              <DialogTitle>Simulate Threat Evaluation</DialogTitle>
              <DialogDescription>
                Provide signal results to test whether{" "}
                <code className="font-mono text-foreground/60">
                  {threatType.threat_code}
                </code>{" "}
                would trigger.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />

        <div className="space-y-4">
          {/* Signal result inputs */}
          <div className="space-y-1.5">
            <Label className="text-xs">Signal Results</Label>
            {signalCodes.length === 0 ? (
              <p className="text-xs text-muted-foreground italic">
                No signals found in expression tree.
              </p>
            ) : (
              <div className="space-y-2">
                {signalCodes.map((code) => (
                  <div
                    key={code}
                    className="flex items-center gap-3 rounded-md border border-border bg-card px-3 py-2"
                  >
                    <div className="flex items-center gap-1.5 min-w-0 flex-1">
                      <Zap className="h-3 w-3 text-amber-500 shrink-0" />
                      <code className="text-xs font-mono text-foreground truncate">
                        {code}
                      </code>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      {["pass", "fail", "warning"].map((r) => (
                        <button
                          key={r}
                          type="button"
                          onClick={() =>
                            setSignalResults((prev) => ({
                              ...prev,
                              [code]: r,
                            }))
                          }
                          className={`rounded-md border px-2.5 py-1 text-[10px] font-semibold transition-all ${
                            signalResults[code] === r
                              ? r === "pass"
                                ? "bg-green-500/10 text-green-600 dark:text-green-400 border-green-500/30"
                                : r === "fail"
                                  ? "bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/30"
                                  : "bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 border-yellow-500/30"
                              : "border-border text-muted-foreground hover:border-border/80"
                          }`}
                        >
                          {r}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <Button
            onClick={handleSimulate}
            disabled={simulating || signalCodes.length === 0}
            className="w-full gap-2"
          >
            {simulating ? (
              <>
                <Spinner /> Simulating...
              </>
            ) : (
              <>
                <Play className="h-4 w-4" />
                Run Simulation
              </>
            )}
          </Button>

          {/* Result */}
          {result && (
            <div className="space-y-3">
              <Separator />
              <div
                className={`flex items-center gap-3 rounded-lg border px-4 py-3 ${
                  result.is_triggered
                    ? "border-red-500/30 bg-red-500/10"
                    : "border-green-500/30 bg-green-500/10"
                }`}
              >
                {result.is_triggered ? (
                  <XCircle className="h-5 w-5 text-red-500 shrink-0" />
                ) : (
                  <CheckCircle2 className="h-5 w-5 text-green-500 shrink-0" />
                )}
                <div>
                  <p
                    className={`text-sm font-semibold ${result.is_triggered ? "text-red-500" : "text-green-500"}`}
                  >
                    {result.is_triggered
                      ? "Threat Triggered"
                      : "Threat Not Triggered"}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {result.is_triggered
                      ? "The expression tree evaluated to TRUE with the given signal results."
                      : "The expression tree evaluated to FALSE. No threat detected."}
                  </p>
                </div>
              </div>

              {/* Evaluation trace */}
              {result.evaluation_trace && result.evaluation_trace.length > 0 && (
                <div className="space-y-1.5">
                  <Label className="text-xs">Evaluation Trace</Label>
                  <div className="rounded-md border border-border bg-card divide-y divide-border">
                    {result.evaluation_trace.map((step: any, i: number) => (
                      <div
                        key={i}
                        className="flex items-center gap-2 px-3 py-2"
                      >
                        {step.result === true ||
                        step.result === "true" ||
                        step.result === "pass" ? (
                          <CheckCircle2 className="h-3.5 w-3.5 text-green-500 shrink-0" />
                        ) : (
                          <XCircle className="h-3.5 w-3.5 text-red-500 shrink-0" />
                        )}
                        <span className="text-xs text-foreground flex-1">
                          {step.description || step.node || `Step ${i + 1}`}
                        </span>
                        <code className="text-[10px] font-mono text-muted-foreground">
                          {typeof step.result === "boolean"
                            ? step.result
                              ? "TRUE"
                              : "FALSE"
                            : String(step.result)}
                        </code>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

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
// Threat Type Row
// ─────────────────────────────────────────────────────────────────────────────

function ThreatTypeRow({
  threatType,
  onEdit,
  onSimulate,
  onDelete,
}: {
  threatType: ThreatTypeResponse
  onEdit?: () => void
  onSimulate: () => void
  onDelete?: () => void
}) {
  const severityCode = threatType.severity_code?.toLowerCase() ?? "info"
  const borderCls = SEVERITY_BORDER[severityCode] ?? "border-l-primary"

  return (
    <div
      className={`relative flex items-start gap-3 rounded-xl border border-l-[3px] ${borderCls} bg-card px-4 py-3 group transition-colors hover:border-border/80`}
    >
      {/* Left: icon */}
      <div className="shrink-0 rounded-lg p-2 bg-muted mt-0.5">
        <ShieldAlert className="h-4 w-4 text-muted-foreground" />
      </div>

      {/* Middle: content */}
      <div className="flex-1 min-w-0 space-y-1.5">
        {/* Title row */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-semibold text-foreground truncate">
            {threatType.name || threatType.threat_code}
          </span>
          {severityBadge(severityCode, threatType.severity_name)}
        </div>

        {/* Code + copy */}
        <div className="flex items-center gap-1">
          <code className="text-[11px] font-mono text-muted-foreground">
            {threatType.threat_code}
          </code>
          <button
            onClick={() => copyToClipboard(threatType.threat_code)}
            className="opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-foreground"
            title="Copy code"
          >
            <Copy className="h-3 w-3" />
          </button>
        </div>

        {/* Description */}
        {(threatType.description || threatType.properties?.description) && (
          <p className="text-xs text-muted-foreground line-clamp-1">
            {threatType.description || threatType.properties?.description}
          </p>
        )}

        {/* Expression summary */}
        <div className="rounded-md border border-border bg-muted/20 px-3 py-2">
          <p className="text-[10px] text-muted-foreground font-medium uppercase tracking-wider mb-1">
            Expression
          </p>
          <p className="text-xs text-foreground">
            {summarizeTree(threatType.expression_tree)}
          </p>
          {threatType.expression_tree && (
            <div className="mt-1.5 pt-1.5 border-t border-border/50 max-h-20 overflow-y-auto">
              <ExpressionTreePreview node={threatType.expression_tree} />
            </div>
          )}
        </div>

        {/* Meta row */}
        <div className="flex items-center gap-3 text-[10px] text-muted-foreground pt-0.5">
          <Badge variant="outline" className="text-[10px] bg-muted/40 font-mono">
            <GitBranch className="h-2.5 w-2.5 mr-0.5" />v{threatType.version_number}
          </Badge>
          <span className="ml-auto">{formatDate(threatType.updated_at)}</span>
        </div>
      </div>

      {/* Right: actions (hover) */}
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
          onClick={onSimulate}
          className="rounded-md p-1.5 hover:bg-purple-500/10 transition-colors"
          title="Simulate"
        >
          <Play className="h-3.5 w-3.5 text-purple-500" />
        </button>
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
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Threat Types Page
// ─────────────────────────────────────────────────────────────────────────────

export default function ThreatTypesPage() {
  const { canWrite } = useAccess()
  const canModify = canWrite("sandbox")
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const { selectedOrgId, selectedWorkspaceId, ready: orgReady } = useSandboxOrgWorkspace()

  const [threatTypes, setThreatTypes] = useState<ThreatTypeResponse[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [severities, setSeverities] = useState<DimensionResponse[]>([])
  const [signals, setSignals] = useState<SignalResponse[]>([])
  const [error, setError] = useState<string | null>(null)

  // Filters — persisted in URL so they survive navigation
  const [searchInput, setSearchInput] = useState(() => searchParams.get("q") ?? "")
  const [searchQuery, setSearchQuery] = useState(() => searchParams.get("q") ?? "")
  const [severityFilter, setSeverityFilter] = useState(() => searchParams.get("severity") ?? "")

  // Debounce search
  useEffect(() => {
    const t = setTimeout(() => setSearchQuery(searchInput), 300)
    return () => clearTimeout(t)
  }, [searchInput])

  // Sync filters → URL
  useEffect(() => {
    const params = new URLSearchParams()
    if (searchQuery) params.set("q", searchQuery)
    if (severityFilter) params.set("severity", severityFilter)
    const qs = params.toString()
    router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false })
  }, [searchQuery, severityFilter, pathname, router])

  // Success feedback
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const showSuccess = (msg: string) => {
    setSuccessMessage(msg)
    setTimeout(() => setSuccessMessage(null), 3000)
  }

  // Dialog state
  const [createOpen, setCreateOpen] = useState(false)
  const [editingThreatType, setEditingThreatType] =
    useState<ThreatTypeResponse | null>(null)
  const [deletingThreatType, setDeletingThreatType] =
    useState<ThreatTypeResponse | null>(null)
  const [simulatingThreatType, setSimulatingThreatType] =
    useState<ThreatTypeResponse | null>(null)

  const loadThreatTypes = useCallback(async () => {
    if (!selectedOrgId) return
    setLoading(true)
    setError(null)
    try {
      const res = await listThreatTypes({
        org_id: selectedOrgId,
        workspace_id: selectedWorkspaceId || undefined,
        severity_code: severityFilter || undefined,
        search: searchQuery || undefined,
      })
      setThreatTypes(res.items)
      setTotal(res.total)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load threat types")
    } finally {
      setLoading(false)
    }
  }, [selectedOrgId, selectedWorkspaceId, severityFilter, searchQuery])

  const loadDimensions = useCallback(async () => {
    if (!selectedOrgId) return
    try {
      const [sev, sig] = await Promise.all([
        listThreatSeverities(),
        listSignals({ org_id: selectedOrgId, workspace_id: selectedWorkspaceId || undefined })
          .then((r) => r.items)
          .catch(() => [] as SignalResponse[]),
      ])
      setSeverities(sev)
      setSignals(sig)
    } catch {
      // Non-critical
    }
  }, [selectedOrgId, selectedWorkspaceId])

  useEffect(() => {
    if (orgReady) loadDimensions()
  }, [orgReady, loadDimensions])

  useEffect(() => {
    if (orgReady) loadThreatTypes()
  }, [orgReady, loadThreatTypes])

  async function handleDelete(id: string) {
    if (!selectedOrgId) return
    await deleteThreatType(id, selectedOrgId)
    showSuccess("Threat type deleted")
    await loadThreatTypes()
  }

  // KPI stats derived from loaded list
  const stats = useMemo(() => {
    const bySeverity: Record<string, number> = {}
    for (const tt of threatTypes) {
      const s = tt.severity_code?.toLowerCase() ?? "info"
      bySeverity[s] = (bySeverity[s] ?? 0) + 1
    }
    return bySeverity
  }, [threatTypes])

  // Active filter chips
  const activeFilters: { label: string; onRemove: () => void }[] = []
  if (searchQuery) activeFilters.push({ label: `"${searchQuery}"`, onRemove: () => { setSearchInput(""); setSearchQuery("") } })
  if (severityFilter) {
    const sev = severities.find((s) => s.code === severityFilter)
    activeFilters.push({ label: sev?.name ?? severityFilter, onRemove: () => setSeverityFilter("") })
  }

  const KPI_CARDS = [
    {
      key: "total",
      label: "Total Threat Types",
      value: total,
      borderCls: "border-l-primary",
      numCls: "text-foreground",
      iconCls: "text-muted-foreground",
      bgCls: "bg-muted",
      icon: ShieldAlert,
    },
    ...["critical", "high", "medium", "low", "info"]
      .filter((s) => (stats[s] ?? 0) > 0 || s === "critical" || s === "high")
      .map((s) => {
        const kpi = SEVERITY_KPI[s]
        const Icon = ShieldAlert
        return {
          key: s,
          label: s.charAt(0).toUpperCase() + s.slice(1),
          value: stats[s] ?? 0,
          borderCls: kpi.border,
          numCls: kpi.num,
          iconCls: kpi.icon,
          bgCls: kpi.bg,
          icon: Icon,
        }
      }),
  ]

  return (
    <div className="max-w-5xl space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="rounded-xl bg-red-500/10 p-3 shrink-0">
            <ShieldAlert className="h-6 w-6 text-red-500" />
          </div>
          <div className="flex flex-col gap-1">
            <h2 className="text-2xl font-semibold text-foreground">
              Threat Type Composer
            </h2>
            <p className="text-sm text-muted-foreground">
              Compose signals into threat detection rules using boolean
              expression trees
            </p>
          </div>
        </div>
        {canModify && (
          <Button
            size="sm"
            className="gap-1.5 shrink-0"
            onClick={() => setCreateOpen(true)}
          >
            <Plus className="h-3.5 w-3.5" />
            Create Threat Type
          </Button>
        )}
      </div>

      {/* KPI stat cards */}
      {!loading && threatTypes.length > 0 && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {KPI_CARDS.map(({ key, label, value, borderCls, numCls, iconCls, bgCls, icon: Icon }) => (
            <div
              key={key}
              className={`relative flex items-center gap-3 rounded-xl border border-l-[3px] ${borderCls} bg-card px-4 py-3`}
            >
              <div className={`shrink-0 rounded-lg p-2 ${bgCls}`}>
                <Icon className={`h-4 w-4 ${iconCls}`} />
              </div>
              <div className="min-w-0">
                <p className={`text-2xl font-bold tabular-nums leading-none ${numCls}`}>{value}</p>
                <span className="text-[11px] text-muted-foreground mt-0.5 block truncate">{label}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Filter bar */}
      <div className="rounded-xl border border-border bg-card px-4 py-3 space-y-3">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px] max-w-xs">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search threat types..."
              className="h-9 pl-9 text-sm"
            />
          </div>
          <select
            className="h-9 rounded-md border border-input bg-background px-3 text-sm"
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
          >
            <option value="">All Severities</option>
            {severities.map((s) => (
              <option key={s.code} value={s.code}>
                {s.name}
              </option>
            ))}
          </select>
          <Button
            variant="ghost"
            size="sm"
            onClick={loadThreatTypes}
            className="gap-1.5 text-muted-foreground"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </Button>
          <span className="text-xs text-muted-foreground ml-auto">
            {total} threat type{total !== 1 ? "s" : ""}
          </span>
        </div>

        {/* Active filter chips */}
        {activeFilters.length > 0 && (
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] text-muted-foreground">Active:</span>
            {activeFilters.map((f) => (
              <button
                key={f.label}
                onClick={f.onRemove}
                className="flex items-center gap-1 rounded-md border border-border bg-muted/30 px-2 py-0.5 text-[11px] text-foreground hover:bg-muted/60 transition-colors"
              >
                {f.label}
                <X className="h-3 w-3 text-muted-foreground" />
              </button>
            ))}
          </div>
        )}
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
        <div className="space-y-3">
          {[1, 2, 3, 4].map((n) => (
            <div
              key={n}
              className="rounded-xl border border-l-[3px] border-l-border bg-card p-4 space-y-3 animate-pulse"
            >
              <div className="flex items-center gap-2">
                <div className="h-4 w-32 bg-muted rounded" />
                <div className="h-4 w-16 bg-muted rounded" />
              </div>
              <div className="h-3 w-48 bg-muted rounded" />
              <div className="h-16 w-full bg-muted rounded" />
              <div className="flex gap-3">
                <div className="h-3 w-12 bg-muted rounded" />
                <div className="h-3 w-20 bg-muted rounded" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && threatTypes.length === 0 && (
        <div className="rounded-xl border border-border bg-muted/20 px-5 py-12 text-center">
          <ShieldAlert className="h-10 w-10 text-red-500/30 mx-auto mb-3" />
          <p className="text-sm font-medium text-foreground mb-1">
            No threat types yet
          </p>
          <p className="text-xs text-muted-foreground mb-4">
            Create a threat type to compose multiple signals into a detection
            rule using boolean logic.
          </p>
          {canModify && (
            <Button
              size="sm"
              className="gap-1.5"
              onClick={() => setCreateOpen(true)}
            >
              <Plus className="h-3.5 w-3.5" />
              Create Threat Type
            </Button>
          )}
        </div>
      )}

      {/* Threat type list */}
      {!loading && threatTypes.length > 0 && (
        <div className="space-y-3">
          {threatTypes.map((tt) => (
            <ThreatTypeRow
              key={tt.id}
              threatType={tt}
              onEdit={canModify ? () => setEditingThreatType(tt) : undefined}
              onSimulate={() => setSimulatingThreatType(tt)}
              onDelete={canModify ? () => setDeletingThreatType(tt) : undefined}
            />
          ))}
        </div>
      )}

      {/* Dialogs */}
      <CreateThreatTypeDialog
        open={createOpen}
        orgId={selectedOrgId}
        workspaceId={selectedWorkspaceId || null}
        severities={severities}
        signals={signals}
        onCreate={loadThreatTypes}
        onClose={() => setCreateOpen(false)}
      />
      <EditThreatTypeDialog
        threatType={editingThreatType}
        orgId={selectedOrgId}
        severities={severities}
        signals={signals}
        onSave={loadThreatTypes}
        onClose={() => setEditingThreatType(null)}
      />
      <DeleteThreatTypeDialog
        threatType={deletingThreatType}
        onConfirm={handleDelete}
        onClose={() => setDeletingThreatType(null)}
      />
      <SimulateDialog
        threatType={simulatingThreatType}
        onClose={() => setSimulatingThreatType(null)}
      />
    </div>
  )
}
