"use client"

import { useEffect, useState, useCallback, useRef } from "react"
import { useRouter, useSearchParams, usePathname } from "next/navigation"
import {
  Button,
  Input,
  Label,
  Badge,
  Separator,
  Switch,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@kcontrol/ui"
import {
  FileCheck,
  Plus,
  Search,
  Pencil,
  Trash2,
  FlaskRound,
  Bell,
  FileText,
  ShieldAlert,
  X,
  ChevronDown,
  Timer,
  ToggleLeft,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Loader2,
  GitBranch,
  Copy,
  ArrowUpFromLine,
  Globe,
} from "lucide-react"
import { copyToClipboard } from "@/lib/utils/sandbox-helpers"
import { useAccess } from "@/components/providers/AccessProvider"
import { useSandboxOrgWorkspace } from "@/lib/context/SandboxOrgWorkspaceContext"
import {
  listPolicies,
  listThreatTypes,
  listPolicyActionTypes,
  listConnectorTypes,
  createPolicy,
  enablePolicy,
  disablePolicy,
  testPolicy,
  deletePolicy,
  promotePolicy,
  listSignals,
  publishGlobalControlTest,
} from "@/lib/api/sandbox"
import { AssetSelectorDialog } from "@/components/grc/AssetSelectorDialog"
import type {
  PolicyResponse,
  PolicyActionConfig,
  PolicyTestResult,
  ThreatTypeResponse,
  DimensionResponse,
} from "@/lib/api/sandbox"

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

const SEVERITY_STYLES: Record<string, string> = {
  critical: "bg-red-500/10 text-red-500 border-red-500/30",
  high: "bg-orange-500/10 text-orange-500 border-orange-500/30",
  medium: "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30",
  low: "bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 border-yellow-500/30",
  info: "bg-muted text-muted-foreground",
}

const ACTION_ICONS: Record<string, typeof Bell> = {
  notification: Bell,
  evidence_capture: FileText,
  alert: AlertTriangle,
  quarantine: ShieldAlert,
  block: XCircle,
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  })
}

// ─────────────────────────────────────────────────────────────────────────────
// Create Control Test Dialog
// ─────────────────────────────────────────────────────────────────────────────

function CreatePolicyDialog({
  open,
  orgId,
  workspaceId,
  threatTypes,
  actionTypes,
  connectorTypes,
  onCreate,
  onClose,
}: {
  open: boolean
  orgId: string
  workspaceId: string | null
  threatTypes: ThreatTypeResponse[]
  actionTypes: DimensionResponse[]
  connectorTypes: DimensionResponse[]
  onCreate: () => void
  onClose: () => void
}) {
  const [code, setCode] = useState("")
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [threatTypeId, setThreatTypeId] = useState("")
  const [containerCode, setContainerCode] = useState("")
  const containerSelectRef = useRef<HTMLSelectElement>(null)
  const [cooldownMinutes, setCooldownMinutes] = useState(0)
  const [isEnabled, setIsEnabled] = useState(true)
  const [actions, setActions] = useState<PolicyActionConfig[]>([])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [codeManuallyEdited, setCodeManuallyEdited] = useState(false)

  useEffect(() => {
    if (open) {
      setCode("")
      setName("")
      setDescription("")
      setThreatTypeId(threatTypes[0]?.id ?? "")
      setContainerCode("")
      setCooldownMinutes(0)
      setIsEnabled(true)
      setActions([])
      setSaving(false)
      setError(null)
      setCodeManuallyEdited(false)
    }
  }, [open, threatTypes])

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

  function addAction() {
    setActions((prev) => [
      ...prev,
      { action_type_code: actionTypes[0]?.code ?? "", config: {} },
    ])
  }

  function removeAction(idx: number) {
    setActions((prev) => prev.filter((_, i) => i !== idx))
  }

  function updateAction(idx: number, field: string, value: unknown) {
    setActions((prev) =>
      prev.map((a, i) => (i === idx ? { ...a, [field]: value } : a)),
    )
  }

  function updateActionConfig(idx: number, configStr: string) {
    try {
      const parsed = JSON.parse(configStr)
      updateAction(idx, "config", parsed)
    } catch {
      // allow invalid JSON while typing
    }
  }

  async function submit() {
    if (!threatTypeId) {
      setError("Threat type is required.")
      return
    }

    if (actions.length === 0) {
      setError("At least one action is required.")
      return
    }
    if (!code.trim()) {
      setError("Control test code is required.")
      return
    }
    setSaving(true)
    setError(null)
    try {
      const effectiveContainerCode = containerCode || containerSelectRef.current?.value || ""
      const selectedContainer = connectorTypes.find((item) => item.code === effectiveContainerCode)
      const props: Record<string, string> = {}
      if (name.trim()) props.name = name.trim()
      if (description.trim()) props.description = description.trim()
      if (selectedContainer) {
        props.policy_container_code = selectedContainer.code
        props.policy_container_name = selectedContainer.name
      }
      // Map action_type_code → action_type for backend compatibility
      const mappedActions = actions.map((a) => ({
        action_type: a.action_type_code,
        config: a.config || {},
      })) as unknown as typeof actions
      await createPolicy({
        org_id: orgId,
        workspace_id: workspaceId || undefined,
        policy_code: code.trim(),
        threat_type_id: threatTypeId,
        actions: mappedActions,
        cooldown_minutes: cooldownMinutes,
        is_enabled: isEnabled,
        properties: Object.keys(props).length > 0 ? props : undefined,
      })
      onCreate()
      onClose()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create control test")
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-green-500/10 p-2.5">
              <Plus className="h-4 w-4 text-green-500" />
            </div>
            <div>
              <DialogTitle>Create Control Test</DialogTitle>
              <DialogDescription>
                Define enforcement rules that bind threat types to automated responses.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />
        <div className="space-y-4">
          {/* Name + Code */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs">Name</Label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="MFA Enforcement"
                className="h-9 text-sm"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">
                Control Test Code <span className="text-muted-foreground">(unique)</span>
              </Label>
              <Input
                value={code}
                onChange={(e) => {
                  setCode(e.target.value)
                  setCodeManuallyEdited(true)
                }}
                placeholder="mfa_enforce"
                className="h-9 text-sm font-mono"
              />
            </div>
          </div>

          {/* Threat type */}
          <div className="space-y-1.5">
            <Label className="text-xs">Threat Type</Label>
            <select
              className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
              value={threatTypeId}
              onChange={(e) => setThreatTypeId(e.target.value)}
            >
              {threatTypes.length === 0 && (
                <option value="">No threat types available</option>
              )}
              {threatTypes.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name || t.threat_code} ({t.severity_name})
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs">Policy Container</Label>
            <select
              ref={containerSelectRef}
              className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
              value={containerCode}
              onChange={(e) => setContainerCode(e.target.value)}
            >
              <option value="">Select a platform container</option>
              {connectorTypes.map((connectorType) => (
                <option key={connectorType.code} value={connectorType.code}>
                  {connectorType.name}
                </option>
              ))}
            </select>
            <p className="text-[11px] text-muted-foreground">
              Promoted policies stay grouped inside this container in Control Tests.
            </p>
          </div>

          {/* Cooldown + Enabled */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs">Cooldown (minutes)</Label>
              <Input
                type="number"
                min={0}
                value={cooldownMinutes}
                onChange={(e) => setCooldownMinutes(Number(e.target.value))}
                className="h-9 text-sm"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Enabled on Create</Label>
              <div className="flex items-center gap-2 h-9">
                <Switch isSelected={isEnabled} onChange={setIsEnabled} />
                <span className="text-xs text-muted-foreground">
                  {isEnabled ? "Enabled" : "Disabled"}
                </span>
              </div>
            </div>
          </div>

          {/* Actions builder */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label className="text-xs">Actions</Label>
              <Button variant="outline" size="sm" onClick={addAction} className="h-7 text-xs gap-1">
                <Plus className="h-3 w-3" /> Add Action
              </Button>
            </div>
            {actions.length === 0 && (
              <div className="rounded-lg border border-dashed border-border px-4 py-3 text-center">
                <p className="text-xs text-muted-foreground">
                  No actions configured. Add at least one action.
                </p>
              </div>
            )}
            {actions.map((action, idx) => (
              <div
                key={idx}
                className="rounded-lg border border-border bg-muted/10 p-3 space-y-2"
              >
                <div className="flex items-center gap-2">
                  <select
                    className="h-8 flex-1 rounded-md border border-input bg-background px-2 text-xs"
                    value={action.action_type_code}
                    onChange={(e) => updateAction(idx, "action_type_code", e.target.value)}
                  >
                    {actionTypes.map((at) => (
                      <option key={at.code} value={at.code}>
                        {at.name}
                      </option>
                    ))}
                  </select>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0 text-muted-foreground hover:text-red-500"
                    onClick={() => removeAction(idx)}
                  >
                    <X className="h-3.5 w-3.5" />
                  </Button>
                </div>
                <div className="space-y-1">
                  <Label className="text-[10px] text-muted-foreground">
                    Config (JSON)
                  </Label>
                  <Input
                    defaultValue={JSON.stringify(action.config)}
                    onChange={(e) => updateActionConfig(idx, e.target.value)}
                    placeholder='{"channel": "#alerts"}'
                    className="h-8 text-xs font-mono"
                  />
                </div>
              </div>
            ))}
          </div>

          {error && (
            <div className="rounded-lg border border-red-500/30 bg-red-500/5 px-3 py-2">
              <p className="text-xs text-red-500">{error}</p>
            </div>
          )}
        </div>
        <DialogFooter className="mt-4">
          <Button variant="outline" size="sm" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button size="sm" onClick={submit} disabled={saving} className="gap-1.5">
            {saving && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            Create Control Test
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Test (Dry-Run) Dialog
// ─────────────────────────────────────────────────────────────────────────────

function TestPolicyDialog({
  open,
  policy,
  onClose,
}: {
  open: boolean
  policy: PolicyResponse | null
  onClose: () => void
}) {
  const { selectedOrgId } = useSandboxOrgWorkspace()
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<PolicyTestResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open && policy) {
      setLoading(true)
      setResult(null)
      setError(null)
      testPolicy(selectedOrgId!, policy.id)
        .then(setResult)
        .catch((e) => setError(e instanceof Error ? e.message : "Test failed"))
        .finally(() => setLoading(false))
    }
  }, [open, policy])

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-amber-500/10 p-2.5">
              <FlaskRound className="h-4 w-4 text-amber-500" />
            </div>
            <div>
              <DialogTitle>Dry-Run: {policy?.name || policy?.policy_code}</DialogTitle>
              <DialogDescription>
                Simulated control test execution showing what actions would fire.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />

        {loading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            <span className="ml-2 text-sm text-muted-foreground">Running simulation...</span>
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/5 px-4 py-3">
            <p className="text-sm text-red-500">{error}</p>
          </div>
        )}

        {result && (
          <div className="space-y-4">
            {/* Would fire indicator */}
            <div
              className={`flex items-center gap-3 rounded-xl px-4 py-3 ${
                result.would_fire
                  ? "border border-green-500/30 bg-green-500/5"
                  : "border border-yellow-500/30 bg-yellow-500/5"
              }`}
            >
              {result.would_fire ? (
                <CheckCircle2 className="h-5 w-5 text-green-500" />
              ) : (
                <AlertTriangle className="h-5 w-5 text-yellow-500" />
              )}
              <div>
                <p className="text-sm font-medium text-foreground">
                  {result.would_fire
                    ? "Control test would fire"
                    : "Control test would NOT fire"}
                </p>
                <p className="text-xs text-muted-foreground">
                  {result.would_fire
                    ? "All conditions met. The following actions would execute."
                    : "Conditions not met in current context. No actions triggered."}
                </p>
              </div>
            </div>

            {/* Simulated actions */}
            {result.actions_simulated.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Simulated Actions
                </h4>
                {result.actions_simulated.map((a, i) => {
                  const Icon = ACTION_ICONS[a.action_type_code] ?? FileCheck
                  return (
                    <div
                      key={i}
                      className="flex items-start gap-3 rounded-lg border border-border bg-muted/10 px-3 py-2.5"
                    >
                      <div className="rounded-lg bg-muted/30 p-1.5 mt-0.5">
                        <Icon className="h-3.5 w-3.5 text-muted-foreground" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-foreground">
                          {a.action_type_name || a.action_type_code}
                        </p>
                        {Object.keys(a.config).length > 0 && (
                          <pre className="text-[10px] text-muted-foreground font-mono mt-1 overflow-x-auto">
                            {JSON.stringify(a.config, null, 2)}
                          </pre>
                        )}
                      </div>
                      <Badge
                        variant="outline"
                        className="text-[10px] bg-green-500/10 text-green-500 border-green-500/30 shrink-0"
                      >
                        simulated
                      </Badge>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}

        <DialogFooter className="mt-4">
          <Button variant="outline" size="sm" onClick={onClose}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Publish to Global Library Confirmation Dialog
// ─────────────────────────────────────────────────────────────────────────────

function PublishGlobalConfirmDialog({
  open,
  policy,
  onConfirm,
  onClose,
}: {
  open: boolean
  policy: PolicyResponse | null
  onConfirm: () => void
  onClose: () => void
}) {
  const [publishing, setPublishing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) { setPublishing(false); setError(null) }
  }, [open])

  async function confirm() {
    setPublishing(true)
    setError(null)
    try {
      await onConfirm()
      onClose()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Publish failed")
      setPublishing(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-amber-500/10 p-2.5">
              <Globe className="h-4 w-4 text-amber-500" />
            </div>
            <div>
              <DialogTitle>Publish to Global Library</DialogTitle>
              <DialogDescription>
                This will publish the control test to the global library where it becomes available across all workspaces.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 px-4 py-3 mt-2">
          <div className="flex items-start gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="text-sm font-medium text-amber-600 dark:text-amber-400">Warning</p>
              <ul className="text-xs text-amber-600/90 dark:text-amber-400/90 space-y-1 list-disc list-inside">
                <li>This action cannot be easily undone</li>
                <li>The control test will be visible to all workspaces</li>
                <li>Associated signals and threat definitions will be included</li>
              </ul>
            </div>
          </div>
        </div>

        {policy && (
          <div className="rounded-lg border border-border bg-muted/10 px-3 py-2 mt-2">
            <p className="text-xs text-muted-foreground">Publishing:</p>
            <p className="text-sm font-mono font-semibold text-foreground">
              {policy.name || policy.policy_code}
            </p>
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/5 px-3 py-2 mt-2">
            <p className="text-xs text-red-500">{error}</p>
          </div>
        )}

        <DialogFooter className="mt-4">
          <Button variant="outline" size="sm" onClick={onClose} disabled={publishing}>
            Cancel
          </Button>
          <Button
            size="sm"
            onClick={confirm}
            disabled={publishing}
            className="gap-1.5 bg-amber-500 hover:bg-amber-600 text-white"
          >
            {publishing && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            Confirm & Publish
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Delete Confirmation Dialog
// ─────────────────────────────────────────────────────────────────────────────

function DeleteDialog({
  open,
  orgId,
  policy,
  onConfirm,
  onClose,
}: {
  open: boolean
  orgId: string
  policy: PolicyResponse | null
  onConfirm: () => void
  onClose: () => void
}) {
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) { setDeleting(false); setError(null) }
  }, [open])

  async function confirm() {
    if (!policy) return
    setDeleting(true)
    setError(null)
    try {
      await deletePolicy(policy.id, orgId)
      onConfirm()
      onClose()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete")
      setDeleting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-red-500/10 p-2.5">
              <Trash2 className="h-4 w-4 text-red-500" />
            </div>
            <div>
              <DialogTitle>Delete Control Test</DialogTitle>
              <DialogDescription>
                This will permanently delete{" "}
                <span className="font-mono font-semibold text-foreground">
                  {policy?.name || policy?.policy_code}
                </span>
                . This action cannot be undone.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>
        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/5 px-3 py-2 mt-2">
            <p className="text-xs text-red-500">{error}</p>
          </div>
        )}
        <DialogFooter className="mt-4">
          <Button variant="outline" size="sm" onClick={onClose} disabled={deleting}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={confirm}
            disabled={deleting}
            className="gap-1.5"
          >
            {deleting && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
            Delete
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Control Test Row
// ─────────────────────────────────────────────────────────────────────────────

function PolicyRow({
  policy,
  connectorTypeMap,
  threatTypes,
  onToggle,
  onTest,
  onDelete,
  onPromote,
  onPublishToGlobal,
}: {
  policy: PolicyResponse
  connectorTypeMap: Record<string, string>
  threatTypes: ThreatTypeResponse[]
  onToggle: (p: PolicyResponse) => void
  onTest: (p: PolicyResponse) => void
  onDelete?: (p: PolicyResponse) => void
  onPromote?: (p: PolicyResponse) => void
  onPublishToGlobal?: (p: PolicyResponse) => void
}) {
  const threat = threatTypes.find((t) => t.id === policy.threat_type_id)
  const severityCode = threat?.severity_name?.toLowerCase() ?? "info"
  const borderCls = policy.is_enabled ? "border-l-green-500" : "border-l-slate-400"
  const containerName =
    policy.properties?.policy_container_name ||
    (policy.properties?.policy_container_code
      ? connectorTypeMap[policy.properties.policy_container_code] || policy.properties.policy_container_code
      : null)

  return (
    <div
      className={`relative flex items-start gap-3 rounded-xl border border-l-[3px] ${borderCls} bg-card px-4 py-3 group transition-colors hover:border-border/80`}
    >
      {/* Left: icon */}
      <div className="shrink-0 rounded-lg p-2 bg-muted mt-0.5">
        <FileCheck className="h-4 w-4 text-muted-foreground" />
      </div>

      {/* Middle: content */}
      <div className="flex-1 min-w-0 space-y-1.5">
        {/* Title row */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-semibold text-foreground truncate">
            {policy.name || policy.policy_code}
          </span>
          {containerName && (
            <Badge
              variant="outline"
              className="text-[10px] shrink-0 bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border-cyan-500/30"
            >
              {containerName}
            </Badge>
          )}
          <Badge
            variant="outline"
            className={`text-[10px] shrink-0 ${
              policy.is_enabled
                ? "bg-green-500/10 text-green-500 border-green-500/30"
                : "bg-muted text-muted-foreground"
            }`}
          >
            {policy.is_enabled ? "Enabled" : "Disabled"}
          </Badge>
        </div>

        {/* Code + copy */}
        <div className="flex items-center gap-1">
          <code className="text-[11px] font-mono text-muted-foreground">
            {policy.policy_code}
          </code>
          <button
            onClick={(e) => { e.stopPropagation(); copyToClipboard(policy.policy_code) }}
            className="text-muted-foreground hover:text-foreground transition-colors"
            title="Copy code"
          >
            <Copy className="h-3 w-3" />
          </button>
        </div>

        {/* Threat type */}
        {threat && (
          <div className="flex items-center gap-2">
            <ShieldAlert className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
            <span className="text-xs text-muted-foreground truncate">
              {threat.name || threat.threat_code}
            </span>
            <Badge
              variant="outline"
              className={`text-[10px] ${SEVERITY_STYLES[severityCode] ?? SEVERITY_STYLES.info}`}
            >
              {threat.severity_name}
            </Badge>
          </div>
        )}

        {/* Actions preview */}
        <div className="flex flex-wrap gap-1.5">
          {policy.actions.map((a, i) => {
            const Icon = ACTION_ICONS[a.action_type_code] ?? FileCheck
            return (
              <div
                key={i}
                className="flex items-center gap-1 rounded-md border border-border bg-muted/20 px-2 py-1"
              >
                <Icon className="h-3 w-3 text-muted-foreground" />
                <span className="text-[10px] text-muted-foreground">
                  {a.action_type_name || a.action_type_code}
                </span>
              </div>
            )
          })}
          {policy.actions.length === 0 && (
            <span className="text-[10px] text-muted-foreground italic">No actions</span>
          )}
        </div>

        {/* Meta row */}
        <div className="flex items-center gap-3 text-[10px] text-muted-foreground pt-0.5">
          {policy.cooldown_minutes > 0 && (
            <div className="flex items-center gap-1">
              <Timer className="h-3 w-3" />
              <span>{policy.cooldown_minutes} min cooldown</span>
            </div>
          )}
          <div className="flex items-center gap-1">
            <GitBranch className="h-3 w-3" />
            <span>v{policy.version_number}</span>
          </div>
          <span className="ml-auto">{formatDate(policy.created_at)}</span>
        </div>
      </div>

      {/* Right: toggle + actions */}
      <div className="flex flex-col items-end gap-2 shrink-0">
        <Switch
          isSelected={policy.is_enabled}
          onChange={() => onToggle(policy)}
          className="shrink-0"
        />
        <div className="flex items-center gap-1">
          <button
            onClick={() => onTest(policy)}
            className="rounded-md p-1.5 hover:bg-amber-500/10 transition-colors"
            title="Dry-run test"
          >
            <FlaskRound className="h-3.5 w-3.5 text-amber-500" />
          </button>
          {onPromote && (
            <button
              onClick={() => onPromote(policy)}
              className="rounded-md p-1.5 hover:bg-cyan-500/10 transition-colors"
              title="Deploy to Workspace"
            >
              <ArrowUpFromLine className="h-3.5 w-3.5 text-cyan-500" />
            </button>
          )}
          {onPublishToGlobal && (
            <button
              onClick={() => onPublishToGlobal(policy)}
              className="rounded-md p-1.5 hover:bg-emerald-500/10 transition-colors"
              title="Publish to Global Library"
            >
              <Globe className="h-3.5 w-3.5 text-emerald-500" />
            </button>
          )}
          {onDelete && (
            <button
              onClick={() => onDelete(policy)}
              className="rounded-md p-1.5 hover:bg-red-500/10 transition-colors"
              title="Delete"
            >
              <Trash2 className="h-3.5 w-3.5 text-red-500" />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Page
// ─────────────────────────────────────────────────────────────────────────────

export default function PoliciesPage() {
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()

  const [policies, setPolicies] = useState<PolicyResponse[]>([])
  const [threatTypes, setThreatTypes] = useState<ThreatTypeResponse[]>([])
  const [actionTypes, setActionTypes] = useState<DimensionResponse[]>([])
  const [connectorTypes, setConnectorTypes] = useState<DimensionResponse[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Success feedback
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const showSuccess = (msg: string) => {
    setSuccessMessage(msg)
    setTimeout(() => setSuccessMessage(null), 3000)
  }

  // Filters — persisted in URL so they survive navigation
  const [searchInput, setSearchInput] = useState(() => searchParams.get("q") ?? "")
  const [searchQuery, setSearchQuery] = useState(() => searchParams.get("q") ?? "")
  const [filterThreatId, setFilterThreatId] = useState<string>(() => searchParams.get("threat") ?? "")
  const [filterEnabled, setFilterEnabled] = useState<string>(() => searchParams.get("enabled") ?? "")

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => setSearchQuery(searchInput), 300)
    return () => clearTimeout(timer)
  }, [searchInput])

  // Sync filters → URL
  useEffect(() => {
    const params = new URLSearchParams()
    if (searchQuery) params.set("q", searchQuery)
    if (filterThreatId) params.set("threat", filterThreatId)
    if (filterEnabled) params.set("enabled", filterEnabled)
    const qs = params.toString()
    router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false })
  }, [searchQuery, filterThreatId, filterEnabled, pathname, router])

  const { canWrite } = useAccess()
  const canModify = canWrite("sandbox")
  const { selectedOrgId, selectedWorkspaceId, ready: orgReady } = useSandboxOrgWorkspace()

  // Dialogs
  const [showCreate, setShowCreate] = useState(false)
  const [testTarget, setTestTarget] = useState<PolicyResponse | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<PolicyResponse | null>(null)
  const [publishTarget, setPublishTarget] = useState<PolicyResponse | null>(null)

  // Promote state
  const [promoteTarget, setPromoteTarget] = useState<PolicyResponse | null>(null)
  const [promoting, setPromoting] = useState(false)
  const [promoteError, setPromoteError] = useState<string | null>(null)

  async function handlePromoteWithAsset(connectorId: string) {
    if (!promoteTarget || !selectedOrgId) return
    setPromoting(true)
    setPromoteError(null)
    try {
      await promotePolicy(selectedOrgId, promoteTarget.id, { linked_asset_id: connectorId, workspace_id: selectedWorkspaceId ?? undefined })
      setPromoteTarget(null)
      showSuccess("Control test promoted successfully")
    } catch (e) {
      setPromoteError(e instanceof Error ? e.message : "Promotion failed")
    } finally {
      setPromoting(false)
    }
  }

  // Publish to Global Library
  async function handlePublishToGlobal(policy: PolicyResponse) {
    if (!selectedOrgId) return
    try {
      // Find the threat type to get the signal codes from expression tree
      const threat = threatTypes.find((t) => t.id === policy.threat_type_id)
      if (!threat) { setError("Threat type not found"); return }

      // Extract signal codes from expression tree
      const extractSignalCodes = (tree: any): string[] => {
        if (!tree) return []
        if (tree.signal_code) return [tree.signal_code]
        if (tree.conditions) return tree.conditions.flatMap(extractSignalCodes)
        return []
      }
      const signalCodes = extractSignalCodes(threat.expression_tree)
      if (signalCodes.length === 0) { setError("No signals in threat type expression"); return }

      // Get the signal IDs by listing signals and matching codes
      const signalsResp = await listSignals({ org_id: selectedOrgId })
      const matchedSignal = signalsResp.items.find((s: any) => signalCodes.includes(s.signal_code))
      if (!matchedSignal) { setError("Source signal not found"); return }

      const policyName = policy.name || policy.policy_code
      const globalCode = policyName.toLowerCase().replace(/[^a-z0-9]/g, "_").replace(/__+/g, "_").replace(/^_|_$/g, "")

      await publishGlobalControlTest(selectedOrgId, {
        source_signal_id: matchedSignal.id,
        global_code: globalCode,
        properties: {
          name: policyName,
          description: policy.description || "",
          category: "compliance",
        },
      })
      showSuccess(`"${policyName}" published to Global Library`)
      await fetchData()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Publish to Global Library failed")
    }
  }

  function handlePublishToGlobalRequest(policy: PolicyResponse) {
    setPublishTarget(policy)
  }

  const fetchData = useCallback(async () => {
    if (!selectedOrgId) return
    setLoading(true)
    setError(null)
    try {
      const params: Record<string, any> = { org_id: selectedOrgId }
      if (selectedWorkspaceId) params.workspace_id = selectedWorkspaceId
      if (filterThreatId) params.threat_type_id = filterThreatId
      if (filterEnabled === "true") params.is_enabled = true
      if (filterEnabled === "false") params.is_enabled = false
      if (searchQuery) params.search = searchQuery

      const [pRes, tRes, aRes, cRes] = await Promise.all([
        listPolicies(params),
        listThreatTypes({ org_id: selectedOrgId, workspace_id: selectedWorkspaceId || undefined }),
        listPolicyActionTypes(),
        listConnectorTypes(),
      ])
      setPolicies(pRes.items)
      setTotal(pRes.total)
      setThreatTypes(tRes.items)
      setActionTypes(aRes)
      setConnectorTypes(cRes)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load data")
    } finally {
      setLoading(false)
    }
  }, [selectedOrgId, selectedWorkspaceId, filterThreatId, filterEnabled, searchQuery])

  useEffect(() => {
    if (orgReady) fetchData()
  }, [orgReady, fetchData])

  async function handleToggle(policy: PolicyResponse) {
    if (!selectedOrgId) return
    try {
      if (policy.is_enabled) {
        await disablePolicy(policy.id, selectedOrgId)
        showSuccess("Control test disabled")
      } else {
        await enablePolicy(policy.id, selectedOrgId)
        showSuccess("Control test enabled")
      }
      await fetchData()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to toggle control test")
    }
  }

  // Filtered results (client-side search over what API returned)
  const filteredPolicies = policies.filter((p) => {
    if (!searchQuery) return true
    const q = searchQuery.toLowerCase()
    return (
      p.policy_code.toLowerCase().includes(q) ||
      (p.name && p.name.toLowerCase().includes(q)) ||
      (p.description && p.description.toLowerCase().includes(q)) ||
      (p.properties?.policy_container_name && p.properties.policy_container_name.toLowerCase().includes(q)) ||
      (p.properties?.policy_container_code && p.properties.policy_container_code.toLowerCase().includes(q))
    )
  })

  const connectorTypeMap = connectorTypes.reduce<Record<string, string>>((acc, item) => {
    acc[item.code] = item.name
    return acc
  }, {})

  const enabledCount = policies.filter((p) => p.is_enabled).length
  const disabledCount = policies.filter((p) => !p.is_enabled).length

  // Active filter chips
  const activeFilters: { label: string; onRemove: () => void }[] = []
  if (searchQuery) activeFilters.push({ label: `"${searchQuery}"`, onRemove: () => { setSearchInput(""); setSearchQuery("") } })
  if (filterThreatId) {
    const tt = threatTypes.find((t) => t.id === filterThreatId)
    activeFilters.push({ label: tt ? (tt.name || tt.threat_code) : filterThreatId, onRemove: () => setFilterThreatId("") })
  }
  if (filterEnabled) {
    activeFilters.push({ label: filterEnabled === "true" ? "Enabled" : "Disabled", onRemove: () => setFilterEnabled("") })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="rounded-xl bg-green-500/10 p-3 shrink-0">
            <FileCheck className="h-6 w-6 text-green-500" />
          </div>
          <div className="flex flex-col gap-1">
            <h2 className="text-2xl font-semibold text-foreground">Control Test Engine</h2>
            <p className="text-sm text-muted-foreground">
              Define enforcement rules that bind threat types to automated responses.
            </p>
          </div>
        </div>
        {canModify && (
          <Button size="sm" className="gap-1.5 shrink-0" onClick={() => setShowCreate(true)}>
            <Plus className="h-3.5 w-3.5" /> Create Control Test
          </Button>
        )}
      </div>

      {/* KPI stat cards */}
      {!loading && policies.length > 0 && (
        <div className="grid grid-cols-3 gap-3">
          <div className="relative flex items-center gap-3 rounded-xl border border-l-[3px] border-l-primary bg-card px-4 py-3">
            <div className="shrink-0 rounded-lg p-2 bg-muted">
              <FileCheck className="h-4 w-4 text-muted-foreground" />
            </div>
            <div className="min-w-0">
              <p className="text-2xl font-bold tabular-nums leading-none text-foreground">{total}</p>
              <span className="text-[11px] text-muted-foreground mt-0.5 block truncate">Total Control Tests</span>
            </div>
          </div>
          <div className="relative flex items-center gap-3 rounded-xl border border-l-[3px] border-l-green-500 bg-card px-4 py-3">
            <div className="shrink-0 rounded-lg p-2 bg-green-500/10">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
            </div>
            <div className="min-w-0">
              <p className="text-2xl font-bold tabular-nums leading-none text-green-500">{enabledCount}</p>
              <span className="text-[11px] text-muted-foreground mt-0.5 block truncate">Enabled</span>
            </div>
          </div>
          <div className="relative flex items-center gap-3 rounded-xl border border-l-[3px] border-l-slate-400 bg-card px-4 py-3">
            <div className="shrink-0 rounded-lg p-2 bg-muted">
              <XCircle className="h-4 w-4 text-muted-foreground" />
            </div>
            <div className="min-w-0">
              <p className="text-2xl font-bold tabular-nums leading-none text-muted-foreground">{disabledCount}</p>
              <span className="text-[11px] text-muted-foreground mt-0.5 block truncate">Disabled</span>
            </div>
          </div>
        </div>
      )}

      {/* Filter bar */}
      <div className="rounded-xl border border-border bg-card px-4 py-3 space-y-3">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px] max-w-xs">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              placeholder="Search control tests..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="h-9 pl-9 text-sm"
            />
          </div>

          <select
            className="h-9 rounded-md border border-input bg-background px-3 text-sm text-foreground"
            value={filterThreatId}
            onChange={(e) => setFilterThreatId(e.target.value)}
          >
            <option value="">All Threat Types</option>
            {threatTypes.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name || t.threat_code}
              </option>
            ))}
          </select>

          <select
            className="h-9 rounded-md border border-input bg-background px-3 text-sm text-foreground"
            value={filterEnabled}
            onChange={(e) => setFilterEnabled(e.target.value)}
          >
            <option value="">All Status</option>
            <option value="true">Enabled</option>
            <option value="false">Disabled</option>
          </select>

          <Button variant="ghost" size="sm" className="h-9 gap-1.5" onClick={fetchData}>
            <RefreshCw className="h-3.5 w-3.5" /> Refresh
          </Button>

          {total > 0 && (
            <span className="text-xs text-muted-foreground ml-auto">
              {filteredPolicies.length} of {total} control tests
            </span>
          )}
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
        <div className="rounded-xl border border-red-500/30 bg-red-500/5 px-4 py-3">
          <p className="text-sm text-red-500">{error}</p>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          <span className="ml-2 text-sm text-muted-foreground">Loading control tests...</span>
        </div>
      )}

      {/* Empty state */}
      {!loading && filteredPolicies.length === 0 && (
        <div className="rounded-xl border border-border bg-muted/20 px-5 py-12 text-center">
          <FileCheck className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
          <p className="text-sm font-medium text-foreground mb-1">No control tests found</p>
          <p className="text-xs text-muted-foreground mb-4">
            {searchQuery || filterThreatId || filterEnabled
              ? "Try adjusting your filters."
              : "Create your first control test to automate threat responses."}
          </p>
          {!searchQuery && !filterThreatId && !filterEnabled && canModify && (
            <Button size="sm" className="gap-1.5" onClick={() => setShowCreate(true)}>
              <Plus className="h-3.5 w-3.5" /> Create Control Test
            </Button>
          )}
        </div>
      )}

      {/* Control test list */}
      {!loading && filteredPolicies.length > 0 && (
        <div className="space-y-3">
          {filteredPolicies.map((policy) => (
            <PolicyRow
              key={policy.id}
              policy={policy}
              connectorTypeMap={connectorTypeMap}
              threatTypes={threatTypes}
              onToggle={handleToggle}
              onTest={setTestTarget}
              onDelete={canModify ? setDeleteTarget : undefined}
              onPromote={canModify ? setPromoteTarget : undefined}
              onPublishToGlobal={canModify && policy.is_enabled ? handlePublishToGlobalRequest : undefined}
            />
          ))}
        </div>
      )}

      {/* Dialogs */}
      <CreatePolicyDialog
        open={showCreate}
        orgId={selectedOrgId}
        workspaceId={selectedWorkspaceId || null}
        threatTypes={threatTypes}
        actionTypes={actionTypes}
        connectorTypes={connectorTypes}
        onCreate={() => { showSuccess("Control test created successfully"); fetchData() }}
        onClose={() => setShowCreate(false)}
      />
      <TestPolicyDialog
        open={!!testTarget}
        policy={testTarget}
        onClose={() => setTestTarget(null)}
      />
      <DeleteDialog
        open={!!deleteTarget}
        orgId={selectedOrgId}
        policy={deleteTarget}
        onConfirm={() => { showSuccess("Control test deleted"); fetchData() }}
        onClose={() => setDeleteTarget(null)}
      />

      {/* Deploy to Workspace */}
      {!!promoteTarget && selectedOrgId && (
        <AssetSelectorDialog
          open={!!promoteTarget}
          orgId={selectedOrgId}
          currentAssetId={null}
          onSelect={handlePromoteWithAsset}
          onClose={() => { setPromoteTarget(null); setPromoteError(null) }}
        />
      )}
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

      {/* Publish to Global Library Confirmation */}
      <PublishGlobalConfirmDialog
        open={!!publishTarget}
        policy={publishTarget}
        onConfirm={() => handlePublishToGlobal(publishTarget!)}
        onClose={() => setPublishTarget(null)}
      />
    </div>
  )
}
