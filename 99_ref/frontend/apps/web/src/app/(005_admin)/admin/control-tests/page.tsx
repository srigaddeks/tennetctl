"use client"

import { useEffect, useState, useCallback, useMemo } from "react"
import {
  Button,
  Input,
  Label,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
} from "@kcontrol/ui"
import {
  FlaskConical,
  Plus,
  Search,
  AlertTriangle,
  RefreshCw,
  Layers,
  X,
  Bot,
  User,
  Download,
  Pencil,
  Trash2,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  ChevronDown,
  CheckCircle2,
  XCircle,
  Clock,
  SkipForward,
} from "lucide-react"
import {
  listTests,
  createTest,
  updateTest,
  deleteTest,
  listTestTypes,
  listTestMappings,
  createTestMapping,
  deleteTestMapping,
} from "@/lib/api/grc"
import type {
  TestResponse,
  CreateTestRequest,
  UpdateTestRequest,
  DimensionResponse,
  TestControlMappingResponse,
} from "@/lib/types/grc"

// ── Constants ─────────────────────────────────────────────────────────────────

const FREQUENCY_META: Record<string, { label: string; color: string }> = {
  continuous:  { label: "Continuous",  color: "text-emerald-600 bg-emerald-500/10 border-emerald-500/20" },
  daily:       { label: "Daily",       color: "text-blue-600 bg-blue-500/10 border-blue-500/20" },
  weekly:      { label: "Weekly",      color: "text-yellow-600 bg-yellow-500/10 border-yellow-500/20" },
  monthly:     { label: "Monthly",     color: "text-orange-600 bg-orange-500/10 border-orange-500/20" },
  quarterly:   { label: "Quarterly",   color: "text-red-600 bg-red-500/10 border-red-500/20" },
  annually:    { label: "Annually",    color: "text-muted-foreground bg-muted border-border" },
  on_demand:   { label: "On Demand",   color: "text-muted-foreground bg-muted border-border" },
}

const PAGE_SIZE = 50
type SortField = "name" | "test_type_name" | "monitoring_frequency" | "created_at" | "mapped_control_count"
type SortDir = "asc" | "desc"

/**
 * Derive a display status for a test based on available fields.
 * - passed:  active + platform managed (automated, running)
 * - failed:  not active (inactive/disabled)
 * - pending: active + manual (awaiting manual collection)
 * - skipped: (reserved, no current mapping — treated as pending fallback)
 */
function testDisplayStatus(test: TestResponse): "passed" | "failed" | "pending" | "skipped" {
  if (!test.is_active) return "failed"
  if (test.is_platform_managed) return "passed"
  return "pending"
}

function testBorderCls(test: TestResponse): string {
  switch (testDisplayStatus(test)) {
    case "passed":  return "border-l-green-500"
    case "failed":  return "border-l-red-500"
    case "pending": return "border-l-amber-500"
    case "skipped": return "border-l-slate-400"
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function slugify(name: string) {
  return name.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "")
}

function FrequencyBadge({ freq }: { freq: string }) {
  const meta = FREQUENCY_META[freq] ?? { label: freq, color: "text-muted-foreground bg-muted border-border" }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full border text-xs font-medium ${meta.color}`}>
      {meta.label}
    </span>
  )
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
}

function SortIcon({ field, sortBy, sortDir }: { field: SortField; sortBy: SortField; sortDir: SortDir }) {
  if (field !== sortBy) return null
  return sortDir === "asc" ? <ChevronUp className="w-3 h-3 inline ml-0.5" /> : <ChevronDown className="w-3 h-3 inline ml-0.5" />
}

// ── Status badge ─────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: "passed" | "failed" | "pending" | "skipped" }) {
  if (status === "passed") {
    return (
      <span className="inline-flex items-center gap-1 rounded-md border border-green-500/20 bg-green-500/10 px-2 py-0.5 text-xs font-medium text-green-600">
        <CheckCircle2 className="h-2.5 w-2.5" /> Active
      </span>
    )
  }
  if (status === "failed") {
    return (
      <span className="inline-flex items-center gap-1 rounded-md border border-red-500/20 bg-red-500/10 px-2 py-0.5 text-xs font-medium text-red-600">
        <XCircle className="h-2.5 w-2.5" /> Inactive
      </span>
    )
  }
  if (status === "skipped") {
    return (
      <span className="inline-flex items-center gap-1 rounded-md border border-border bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
        <SkipForward className="h-2.5 w-2.5" /> Skipped
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-md border border-amber-500/20 bg-amber-500/10 px-2 py-0.5 text-xs font-medium text-amber-600">
      <Clock className="h-2.5 w-2.5" /> Manual
    </span>
  )
}

// ── Skeleton ──────────────────────────────────────────────────────────────────

function Skeleton() {
  return (
    <div className="rounded-xl border border-l-[3px] border-l-primary border-border bg-card px-4 py-3 animate-pulse space-y-2">
      <div className="flex items-center gap-3">
        <div className="h-4 w-44 bg-muted rounded" />
        <div className="h-4 w-24 bg-muted rounded" />
      </div>
      <div className="h-3 w-60 bg-muted rounded" />
    </div>
  )
}

// ── KPI Stat Cards ────────────────────────────────────────────────────────────

interface KpiCardsProps {
  tests: TestResponse[]
  loading: boolean
}

function KpiCards({ tests, loading }: KpiCardsProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="relative flex items-center gap-3 rounded-xl border border-border bg-card px-4 py-3 animate-pulse">
            <div className="shrink-0 rounded-lg p-2 bg-muted h-8 w-8" />
            <div className="flex flex-col gap-1">
              <div className="h-5 w-10 rounded bg-muted" />
              <div className="h-2.5 w-16 rounded bg-muted" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  const passedCount  = tests.filter(t => testDisplayStatus(t) === "passed").length
  const failedCount  = tests.filter(t => testDisplayStatus(t) === "failed").length
  const pendingCount = tests.filter(t => testDisplayStatus(t) === "pending").length

  const cards = [
    {
      label:     "Total Tests",
      value:     tests.length,
      borderCls: "border-l-violet-500",
      numCls:    "text-foreground",
      bgCls:     "bg-violet-500/10",
      icon:      <FlaskConical className="h-4 w-4 text-violet-500" />,
    },
    {
      label:     "Passed",
      value:     passedCount,
      borderCls: "border-l-green-500",
      numCls:    "text-green-600",
      bgCls:     "bg-green-500/10",
      icon:      <CheckCircle2 className="h-4 w-4 text-green-500" />,
    },
    {
      label:     "Failed",
      value:     failedCount,
      borderCls: "border-l-red-500",
      numCls:    "text-red-600",
      bgCls:     "bg-red-500/10",
      icon:      <XCircle className="h-4 w-4 text-red-500" />,
    },
    {
      label:     "Pending",
      value:     pendingCount,
      borderCls: "border-l-amber-500",
      numCls:    "text-amber-600",
      bgCls:     "bg-amber-500/10",
      icon:      <Clock className="h-4 w-4 text-amber-500" />,
    },
  ]

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {cards.map((c) => (
        <div key={c.label} className={`relative flex items-center gap-3 rounded-xl border border-l-[3px] ${c.borderCls} bg-card px-4 py-3`}>
          <div className={`shrink-0 rounded-lg p-2 ${c.bgCls}`}>
            {c.icon}
          </div>
          <div className="min-w-0">
            <div className={`text-2xl font-bold tabular-nums leading-none ${c.numCls}`}>{c.value}</div>
            <span className="text-[11px] text-muted-foreground mt-0.5 block truncate">{c.label}</span>
          </div>
        </div>
      ))}
    </div>
  )
}

// ── Detail Side Panel ─────────────────────────────────────────────────────────

function TestDetailPanel({
  test,
  onEdit,
  onDelete,
  onClose,
}: {
  test: TestResponse
  onEdit: (t: TestResponse) => void
  onDelete: (t: TestResponse) => void
  onClose: () => void
}) {
  const [tab, setTab] = useState<"details" | "controls">("details")
  const [mappings, setMappings] = useState<TestControlMappingResponse[]>([])
  const [loadingMappings, setLoadingMappings] = useState(false)
  const [newControlId, setNewControlId] = useState("")
  const [addingMapping, setAddingMapping] = useState(false)
  const [addError, setAddError] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const loadMappings = async () => {
    setLoadingMappings(true)
    listTestMappings(test.id)
      .then(data => setMappings(data.items ?? []))
      .catch(() => setMappings([]))
      .finally(() => setLoadingMappings(false))
  }

  useEffect(() => {
    if (tab === "controls") loadMappings()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, test.id])

  const handleAddMapping = async () => {
    if (!newControlId.trim()) return
    setAddingMapping(true)
    setAddError(null)
    try {
      const m = await createTestMapping(test.id, { control_id: newControlId.trim() })
      setMappings(prev => [...prev, m])
      setNewControlId("")
    } catch (e) {
      setAddError(e instanceof Error ? e.message : "Failed to add mapping")
    } finally {
      setAddingMapping(false)
    }
  }

  const handleRemoveMapping = async (mappingId: string) => {
    setDeletingId(mappingId)
    try {
      await deleteTestMapping(test.id, mappingId)
      setMappings(prev => prev.filter(m => m.id !== mappingId))
    } catch {
      // ignore
    } finally {
      setDeletingId(null)
    }
  }

  let parsedRule: object | null = null
  if (test.evaluation_rule) {
    try { parsedRule = JSON.parse(test.evaluation_rule) } catch { parsedRule = null }
  }

  const status = testDisplayStatus(test)

  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-[480px] bg-background border-l border-border shadow-xl z-40 flex flex-col">
      <div className="flex items-center justify-between px-5 py-4 border-b border-border shrink-0">
        <div className="flex items-center gap-2 min-w-0">
          <FlaskConical className="w-4 h-4 text-primary shrink-0" />
          <span className="font-semibold text-sm truncate">{test.name}</span>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <Button variant="ghost" size="sm" className="h-8 px-2" onClick={() => onEdit(test)}>
            <Pencil className="w-3.5 h-3.5" />
          </Button>
          <Button variant="ghost" size="sm" className="h-8 px-2 text-destructive hover:text-destructive" onClick={() => onDelete(test)}>
            <Trash2 className="w-3.5 h-3.5" />
          </Button>
          <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border px-5 shrink-0">
        {(["details", "controls"] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-3 py-2.5 text-xs font-medium border-b-2 transition-colors
              ${tab === t ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"}`}
          >
            {t === "details" ? "Details" : `Controls${mappings.length > 0 ? ` (${mappings.length})` : ""}`}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-5 space-y-5">

        {/* Details tab */}
        {tab === "details" && <>
          <div className="flex items-center gap-2 flex-wrap">
            <StatusBadge status={status} />
            <FrequencyBadge freq={test.monitoring_frequency} />
            {test.is_platform_managed && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-medium text-blue-600 bg-blue-500/10 border-blue-500/20">
                <Bot className="w-3 h-3" /> Platform Managed
              </span>
            )}
          </div>

          {test.description && (
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-1">Description</p>
              <p className="text-sm text-foreground">{test.description}</p>
            </div>
          )}

          {test.integration_guide && (
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-1">Integration Guide</p>
              <p className="text-sm text-foreground">{test.integration_guide}</p>
            </div>
          )}

          {test.evaluation_rule && (
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-1">Evaluation Rule</p>
              {parsedRule ? (
                <pre className="text-xs text-muted-foreground bg-muted rounded p-2 overflow-auto max-h-40">
                  {JSON.stringify(parsedRule, null, 2)}
                </pre>
              ) : (
                <pre className="text-xs text-muted-foreground bg-muted rounded p-2 overflow-auto max-h-40">
                  {test.evaluation_rule}
                </pre>
              )}
            </div>
          )}

          <div className="grid grid-cols-2 gap-x-4 gap-y-3 text-xs">
            <div>
              <p className="text-muted-foreground mb-0.5">Test Code</p>
              <p className="font-mono text-foreground">{test.test_code}</p>
            </div>
            <div>
              <p className="text-muted-foreground mb-0.5">Type</p>
              <p className="text-foreground">{test.test_type_name}</p>
            </div>
            <div>
              <p className="text-muted-foreground mb-0.5">Integration</p>
              <p className="text-foreground capitalize">{test.integration_type}</p>
            </div>
            <div>
              <p className="text-muted-foreground mb-0.5">Frequency</p>
              <FrequencyBadge freq={test.monitoring_frequency} />
            </div>
            {test.signal_type && (
              <div>
                <p className="text-muted-foreground mb-0.5">Signal Type</p>
                <p className="text-foreground capitalize">{test.signal_type}</p>
              </div>
            )}
            <div>
              <p className="text-muted-foreground mb-0.5">Managed By</p>
              <p className="flex items-center gap-1 text-foreground">
                {test.is_platform_managed
                  ? <><Bot className="w-3 h-3" /> Platform</>
                  : <><User className="w-3 h-3" /> Manual</>}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground mb-0.5">Controls Mapped</p>
              <p className="font-semibold text-foreground">{test.mapped_control_count}</p>
            </div>
            <div>
              <p className="text-muted-foreground mb-0.5">Created</p>
              <p className="text-foreground">{formatDate(test.created_at)}</p>
            </div>
          </div>
        </>}

        {/* Controls tab */}
        {tab === "controls" && <>
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-2">Mapped Controls</p>
            <div className="flex gap-2">
              <input
                value={newControlId}
                onChange={e => { setNewControlId(e.target.value); setAddError(null) }}
                onKeyDown={e => e.key === "Enter" && handleAddMapping()}
                placeholder="Paste control UUID to link..."
                className="flex-1 h-8 px-2 rounded border border-border bg-background text-xs font-mono focus:outline-none focus:ring-1 focus:ring-primary"
              />
              <Button size="sm" variant="outline" className="h-8 text-xs shrink-0" disabled={!newControlId.trim() || addingMapping} onClick={handleAddMapping}>
                {addingMapping ? "Adding…" : "Link"}
              </Button>
            </div>
            {addError && (
              <p className="text-[11px] text-destructive mt-1.5 flex items-center gap-1">
                <AlertTriangle className="w-3 h-3 shrink-0" />{addError}
              </p>
            )}
          </div>
          {loadingMappings ? (
            <div className="text-xs text-muted-foreground">Loading…</div>
          ) : mappings.length === 0 ? (
            <div className="text-xs text-muted-foreground text-center py-6 border border-dashed border-border rounded-lg">
              No controls linked to this test yet.
            </div>
          ) : (
            <div className="space-y-1.5">
              {mappings.map(m => (
                <div key={m.id} className="flex items-center gap-2.5 text-xs px-3 py-2.5 rounded-lg bg-muted/40 border border-border/50">
                  <Layers className="w-3 h-3 text-muted-foreground shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      {m.control_code && (
                        <span className="font-mono text-[11px] text-primary shrink-0">{m.control_code}</span>
                      )}
                      {m.control_name && (
                        <span className="text-foreground font-medium truncate">{m.control_name}</span>
                      )}
                      {!m.control_code && !m.control_name && (
                        <span className="font-mono text-muted-foreground truncate">{m.control_id}</span>
                      )}
                    </div>
                    {m.framework_code && (
                      <p className="text-[10px] text-muted-foreground mt-0.5">{m.framework_code}</p>
                    )}
                  </div>
                  {m.is_primary && (
                    <span className="text-[9px] uppercase tracking-wider font-semibold text-primary bg-primary/10 border border-primary/20 rounded px-1.5 py-0.5 shrink-0">
                      Primary
                    </span>
                  )}
                  <button
                    disabled={deletingId === m.id}
                    onClick={() => handleRemoveMapping(m.id)}
                    className="text-muted-foreground hover:text-destructive transition-colors disabled:opacity-50 shrink-0"
                    title="Unlink control"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </>}

      </div>
    </div>
  )
}

// ── Create / Edit Dialog ──────────────────────────────────────────────────────

function TestDialog({
  mode,
  test,
  testTypes,
  onSaved,
  onClose,
}: {
  mode: "create" | "edit"
  test?: TestResponse
  testTypes: DimensionResponse[]
  onSaved: (t: TestResponse) => void
  onClose: () => void
}) {
  const [name, setName]                         = useState(test?.name ?? "")
  const [codeManuallyEdited, setCodeManuallyEdited] = useState(mode === "edit")
  const [codeOverride, setCodeOverride]         = useState(test?.test_code ?? "")
  const [desc, setDesc]                         = useState(test?.description ?? "")
  const [testTypeCode, setTestTypeCode]         = useState(test?.test_type_code ?? testTypes[0]?.code ?? "")
  const [integrationType, setIntegrationType]   = useState(test?.integration_type ?? "api")
  const [frequency, setFrequency]               = useState(test?.monitoring_frequency ?? "monthly")
  const [isPlatformManaged, setIsPlatformManaged] = useState(test?.is_platform_managed ?? false)
  const [signalType, setSignalType]             = useState(test?.signal_type ?? "")
  const [integrationGuide, setIntegrationGuide] = useState(test?.integration_guide ?? "")
  const [evaluationRule, setEvaluationRule]     = useState(test?.evaluation_rule ?? "")
  const [saving, setSaving]                     = useState(false)
  const [error, setError]                       = useState<string | null>(null)

  // Auto-slug code from name (create mode only, unless manually edited)
  const autoCode = mode === "create" && !codeManuallyEdited ? slugify(name) : codeOverride
  const displayCode = mode === "create" ? autoCode : test?.test_code ?? ""

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      let result: TestResponse
      if (mode === "create") {
        const payload: CreateTestRequest = {
          test_code: autoCode,
          test_type_code: testTypeCode,
          integration_type: integrationType,
          monitoring_frequency: frequency,
          is_platform_managed: isPlatformManaged,
          name,
          description: desc || undefined,
          signal_type: signalType || undefined,
          integration_guide: integrationGuide || undefined,
          evaluation_rule: evaluationRule || undefined,
        }
        result = await createTest(payload)
      } else {
        const payload: UpdateTestRequest = {
          name,
          description: desc || undefined,
          test_type_code: testTypeCode,
          integration_type: integrationType,
          monitoring_frequency: frequency,
          is_platform_managed: isPlatformManaged,
          signal_type: signalType || undefined,
          integration_guide: integrationGuide || undefined,
          evaluation_rule: evaluationRule || undefined,
        }
        result = await updateTest(test!.id, payload)
      }
      onSaved(result)
      onClose()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{mode === "create" ? "Create Control Test" : "Edit Control Test"}</DialogTitle>
          <DialogDescription>
            {mode === "create" ? "Define a new test for evaluating control effectiveness." : "Update test details."}
          </DialogDescription>
        </DialogHeader>

        {error && <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Name <span className="text-destructive">*</span></Label>
            <Input
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="Test name"
              required
              className="h-8 text-sm"
            />
            {mode === "create" && (
              <div className="mt-1.5 space-y-1">
                <p className="text-xs text-muted-foreground">
                  Code: <span className="font-mono">{displayCode || "auto-generated from name"}</span>
                </p>
                {!codeManuallyEdited ? (
                  <button
                    type="button"
                    className="text-xs text-primary underline underline-offset-2"
                    onClick={() => { setCodeManuallyEdited(true); setCodeOverride(autoCode) }}
                  >
                    Edit code manually
                  </button>
                ) : (
                  <div className="flex items-center gap-2">
                    <Input
                      value={codeOverride}
                      onChange={e => setCodeOverride(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, "_"))}
                      placeholder="test_code"
                      className="h-7 text-xs font-mono flex-1"
                    />
                    <button
                      type="button"
                      className="text-xs text-muted-foreground hover:text-foreground"
                      onClick={() => { setCodeManuallyEdited(false); setCodeOverride("") }}
                    >
                      Reset
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Description</Label>
            <Input value={desc} onChange={e => setDesc(e.target.value)} placeholder="What this test verifies" className="h-8 text-sm" />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">Test Type <span className="text-destructive">*</span></Label>
              <select
                value={testTypeCode}
                onChange={e => setTestTypeCode(e.target.value)}
                className="w-full h-8 px-2 rounded border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                required
              >
                {testTypes.map(t => <option key={t.code} value={t.code}>{t.name}</option>)}
              </select>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">Integration Type</Label>
              <select
                value={integrationType}
                onChange={e => setIntegrationType(e.target.value)}
                className="w-full h-8 px-2 rounded border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="api">API</option>
                <option value="webhook">Webhook</option>
                <option value="agent">Agent</option>
                <option value="manual">Manual</option>
                <option value="file_upload">File Upload</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">Frequency</Label>
              <select
                value={frequency}
                onChange={e => setFrequency(e.target.value)}
                className="w-full h-8 px-2 rounded border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
              >
                {Object.entries(FREQUENCY_META).map(([k, v]) => (
                  <option key={k} value={k}>{v.label}</option>
                ))}
              </select>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground mb-1 block">Signal Type</Label>
              <Input value={signalType} onChange={e => setSignalType(e.target.value)} placeholder="e.g. boolean, score" className="h-8 text-sm" />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="platform-managed"
              checked={isPlatformManaged}
              onChange={e => setIsPlatformManaged(e.target.checked)}
              className="h-4 w-4 rounded border-border"
            />
            <Label htmlFor="platform-managed" className="text-sm cursor-pointer">Platform managed (automated collection)</Label>
          </div>

          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Integration Guide</Label>
            <Input value={integrationGuide} onChange={e => setIntegrationGuide(e.target.value)} placeholder="Setup instructions for this test" className="h-8 text-sm" />
          </div>

          <div>
            <Label className="text-xs text-muted-foreground mb-1 block">Evaluation Rule (JSON)</Label>
            <Input value={evaluationRule} onChange={e => setEvaluationRule(e.target.value)} placeholder='{"type": "threshold", "value": 95}' className="h-8 text-sm font-mono" />
          </div>

          <DialogFooter>
            <Button type="button" variant="ghost" onClick={onClose} className="h-9 px-4">Cancel</Button>
            <Button type="submit" disabled={saving} className="h-9">
              {saving ? (mode === "create" ? "Creating..." : "Saving...") : (mode === "create" ? "Create Test" : "Save Changes")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ── Delete Confirm ────────────────────────────────────────────────────────────

function DeleteConfirmDialog({
  test,
  onConfirm,
  onClose,
}: {
  test: TestResponse
  onConfirm: () => Promise<void>
  onClose: () => void
}) {
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleDelete = async () => {
    setDeleting(true)
    try {
      await onConfirm()
      onClose()
    } catch (e) {
      setError((e as Error).message)
      setDeleting(false)
    }
  }

  return (
    <Dialog open onOpenChange={(open) => { if (!open) onClose() }}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Delete Control Test</DialogTitle>
          <DialogDescription>
            Are you sure you want to delete <strong>{test.name}</strong>? This action cannot be undone.
          </DialogDescription>
        </DialogHeader>
        {error && <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">{error}</div>}
        <DialogFooter>
          <Button type="button" variant="ghost" onClick={onClose} className="h-9 px-4">Cancel</Button>
          <Button variant="destructive" onClick={handleDelete} disabled={deleting} className="h-9">
            {deleting ? "Deleting..." : "Delete"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ── Active filter chips ───────────────────────────────────────────────────────

interface ActiveChip {
  label: string
  color: "blue" | "green" | "amber" | "red" | "violet" | "default"
  onDismiss: () => void
}

function ActiveFilterChips({ chips, onClearAll }: { chips: ActiveChip[]; onClearAll: () => void }) {
  if (chips.length === 0) return null

  const colorMap: Record<ActiveChip["color"], string> = {
    blue:    "border-blue-500/30 bg-blue-500/10 text-blue-700 dark:text-blue-400",
    green:   "border-green-500/30 bg-green-500/10 text-green-700 dark:text-green-400",
    amber:   "border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-400",
    red:     "border-red-500/30 bg-red-500/10 text-red-700 dark:text-red-400",
    violet:  "border-violet-500/30 bg-violet-500/10 text-violet-700 dark:text-violet-400",
    default: "border-border bg-muted text-foreground",
  }

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {chips.map((chip) => (
        <span
          key={chip.label}
          className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium ${colorMap[chip.color]}`}
        >
          {chip.label}
          <button onClick={chip.onDismiss} className="opacity-60 hover:opacity-100 transition-opacity">
            <X className="h-2.5 w-2.5" />
          </button>
        </span>
      ))}
      {chips.length > 1 && (
        <button
          onClick={onClearAll}
          className="text-xs text-muted-foreground hover:text-foreground transition-colors underline underline-offset-2"
        >
          Clear all
        </button>
      )}
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function AdminControlTestsPage() {
  const [tests, setTests]         = useState<TestResponse[]>([])
  const [testTypes, setTestTypes] = useState<DimensionResponse[]>([])
  const [loading, setLoading]     = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError]         = useState<string | null>(null)

  // dialogs
  const [showCreate, setShowCreate]       = useState(false)
  const [editTarget, setEditTarget]       = useState<TestResponse | null>(null)
  const [deleteTarget, setDeleteTarget]   = useState<TestResponse | null>(null)
  const [detailTarget, setDetailTarget]   = useState<TestResponse | null>(null)

  // filters
  const [search, setSearch]               = useState("")
  const [filterType, setFilterType]       = useState("")
  const [filterFrequency, setFilterFrequency] = useState("")
  const [filterManaged, setFilterManaged] = useState("")

  // sort + pagination
  const [sortBy, setSortBy]   = useState<SortField>("name")
  const [sortDir, setSortDir] = useState<SortDir>("asc")
  const [page, setPage]       = useState(0)

  const load = useCallback(async (quiet = false) => {
    if (quiet) setRefreshing(true); else setLoading(true)
    setError(null)
    try {
      const [testsRes, typesRes] = await Promise.all([
        listTests(),
        listTestTypes(),
      ])
      setTests(testsRes.items)
      setTestTypes(typesRes)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const handleSaved = useCallback((test: TestResponse) => {
    setTests(prev => {
      const idx = prev.findIndex(t => t.id === test.id)
      if (idx >= 0) {
        const next = [...prev]
        next[idx] = test
        return next
      }
      return [test, ...prev]
    })
  }, [])

  const handleDelete = useCallback(async (test: TestResponse) => {
    await deleteTest(test.id)
    setTests(prev => prev.filter(t => t.id !== test.id))
    if (detailTarget?.id === test.id) setDetailTarget(null)
  }, [detailTarget])

  const handleSort = (field: SortField) => {
    if (sortBy === field) setSortDir(d => d === "asc" ? "desc" : "asc")
    else { setSortBy(field); setSortDir("asc") }
    setPage(0)
  }

  const filtered = useMemo(() => {
    let items = tests.filter(t => {
      if (search.trim()) {
        const q = search.toLowerCase()
        if (!t.name.toLowerCase().includes(q) && !t.test_code.toLowerCase().includes(q)) return false
      }
      if (filterType && t.test_type_code !== filterType) return false
      if (filterFrequency && t.monitoring_frequency !== filterFrequency) return false
      if (filterManaged === "automated" && !t.is_platform_managed) return false
      if (filterManaged === "manual" && t.is_platform_managed) return false
      return true
    })

    items = [...items].sort((a, b) => {
      let av: string | number = ""
      let bv: string | number = ""
      if (sortBy === "name") { av = a.name; bv = b.name }
      else if (sortBy === "test_type_name") { av = a.test_type_name; bv = b.test_type_name }
      else if (sortBy === "monitoring_frequency") { av = a.monitoring_frequency; bv = b.monitoring_frequency }
      else if (sortBy === "created_at") { av = a.created_at; bv = b.created_at }
      else if (sortBy === "mapped_control_count") { av = a.mapped_control_count ?? 0; bv = b.mapped_control_count ?? 0 }
      if (typeof av === "number" && typeof bv === "number") {
        return sortDir === "asc" ? av - bv : bv - av
      }
      const cmp = String(av).localeCompare(String(bv))
      return sortDir === "asc" ? cmp : -cmp
    })

    return items
  }, [tests, search, filterType, filterFrequency, filterManaged, sortBy, sortDir])

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE)
  const paginated  = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)
  const hasFilters = !!(search.trim() || filterType || filterFrequency || filterManaged)

  const clearFilters = () => {
    setSearch(""); setFilterType(""); setFilterFrequency(""); setFilterManaged(""); setPage(0)
  }

  const exportCsv = () => {
    const rows = [
      ["code", "name", "test_type", "integration", "frequency", "platform_managed", "controls_mapped", "created_at"],
      ...filtered.map(t => [
        t.test_code,
        t.name,
        t.test_type_name,
        t.integration_type,
        t.monitoring_frequency,
        t.is_platform_managed ? "yes" : "no",
        String(t.mapped_control_count ?? 0),
        t.created_at,
      ]),
    ]
    const csv = rows.map(row => row.map(v => `"${String(v).replace(/"/g, '""')}"`).join(",")).join("\n")
    const blob = new Blob([csv], { type: "text/csv" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "control-tests.csv"
    a.click()
    URL.revokeObjectURL(url)
  }

  // Active filter chips
  const activeChips: ActiveChip[] = []
  if (search.trim()) activeChips.push({ label: `"${search}"`, color: "violet", onDismiss: () => { setSearch(""); setPage(0) } })
  if (filterType) activeChips.push({ label: testTypes.find(t => t.code === filterType)?.name ?? filterType, color: "blue", onDismiss: () => { setFilterType(""); setPage(0) } })
  if (filterFrequency) activeChips.push({ label: FREQUENCY_META[filterFrequency]?.label ?? filterFrequency, color: "amber", onDismiss: () => { setFilterFrequency(""); setPage(0) } })
  if (filterManaged) activeChips.push({ label: filterManaged === "automated" ? "Automated Only" : "Manual Only", color: filterManaged === "automated" ? "green" : "default", onDismiss: () => { setFilterManaged(""); setPage(0) } })

  return (
    <div className={`p-6 space-y-6 ${detailTarget ? "mr-[480px]" : ""} max-w-5xl transition-all`}>

      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold">Control Tests</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Define and manage tests for evaluating compliance control effectiveness
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Button variant="ghost" size="sm" className="h-8 px-2" onClick={exportCsv} title="Export CSV">
            <Download className="w-3.5 h-3.5 mr-1" /> Export
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0"
            onClick={() => load(true)}
            disabled={refreshing}
            title="Refresh"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
          </Button>
          <Button onClick={() => setShowCreate(true)} size="sm" className="h-8 px-3 shrink-0">
            <Plus className="w-3.5 h-3.5 mr-1" /> Create Test
          </Button>
        </div>
      </div>

      {/* ── KPI Stat Cards ──────────────────────────────────────────────── */}
      <KpiCards tests={tests} loading={loading} />

      {/* ── Filter bar ──────────────────────────────────────────────────── */}
      <div className="rounded-xl border border-border bg-card px-4 py-3 space-y-3">
        <div className="flex flex-wrap gap-2 items-center">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-muted-foreground" />
            <Input
              className="pl-9 h-9"
              placeholder="Search tests by name or code..."
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(0) }}
            />
          </div>
          {testTypes.length > 0 && (
            <select
              value={filterType}
              onChange={e => { setFilterType(e.target.value); setPage(0) }}
              className="h-9 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
            >
              <option value="">All Test Types</option>
              {testTypes.map(t => <option key={t.code} value={t.code}>{t.name}</option>)}
            </select>
          )}
          <select
            value={filterFrequency}
            onChange={e => { setFilterFrequency(e.target.value); setPage(0) }}
            className="h-9 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="">All Frequencies</option>
            {Object.entries(FREQUENCY_META).map(([k, v]) => (
              <option key={k} value={k}>{v.label}</option>
            ))}
          </select>
          <select
            value={filterManaged}
            onChange={e => { setFilterManaged(e.target.value); setPage(0) }}
            className="h-9 px-3 rounded-lg border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="">All Modes</option>
            <option value="automated">Automated Only</option>
            <option value="manual">Manual Only</option>
          </select>
          {hasFilters && (
            <Button variant="ghost" size="sm" className="h-9 px-2 gap-1 text-muted-foreground" onClick={clearFilters}>
              <X className="w-3.5 h-3.5" />
              Clear all
            </Button>
          )}
        </div>

        <ActiveFilterChips chips={activeChips} onClearAll={clearFilters} />
      </div>

      {/* ── Sort + count ────────────────────────────────────────────────── */}
      {!loading && !error && (
        <div className="flex items-center gap-4 text-xs text-muted-foreground flex-wrap">
          <span>Showing {filtered.length} of {tests.length} tests{hasFilters ? " (filtered)" : ""}</span>
          <span className="text-muted-foreground/50">|</span>
          <span>Sort by:</span>
          {(["name", "test_type_name", "monitoring_frequency", "mapped_control_count", "created_at"] as SortField[]).map(f => (
            <button
              key={f}
              className={`hover:text-foreground transition-colors ${sortBy === f ? "text-foreground font-medium" : ""}`}
              onClick={() => handleSort(f)}
            >
              {f === "test_type_name" ? "Type" : f === "monitoring_frequency" ? "Frequency" : f === "mapped_control_count" ? "Controls" : f === "created_at" ? "Created" : "Name"}
              <SortIcon field={f} sortBy={sortBy} sortDir={sortDir} />
            </button>
          ))}
        </div>
      )}

      {/* ── Error ───────────────────────────────────────────────────────── */}
      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertTriangle className="w-4 h-4 shrink-0" /> {error}
        </div>
      )}

      {/* ── Loading ─────────────────────────────────────────────────────── */}
      {loading && (
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => <Skeleton key={i} />)}
        </div>
      )}

      {/* ── List ────────────────────────────────────────────────────────── */}
      {!loading && !error && (
        <div className="space-y-1">
          {paginated.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              {hasFilters ? "No tests match your filters." : "No control tests yet. Create your first test to get started."}
            </p>
          ) : (
            paginated.map(test => {
              const borderCls = testBorderCls(test)
              const status    = testDisplayStatus(test)
              return (
                <div
                  key={test.id}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl border border-l-[3px] ${borderCls} transition-colors cursor-pointer
                    ${detailTarget?.id === test.id ? "border-primary/20 bg-primary/5" : "border-border bg-card hover:border-border/80 hover:bg-muted/30"}`}
                  onClick={() => setDetailTarget(prev => prev?.id === test.id ? null : test)}
                >
                  <FlaskConical className="w-4 h-4 shrink-0 text-primary" />

                  <div className="flex-1 min-w-0 flex items-center gap-2 flex-wrap">
                    <span className="font-medium text-sm truncate">{test.name}</span>
                    <span className="font-mono text-xs text-muted-foreground hidden sm:inline">{test.test_code}</span>
                    <StatusBadge status={status} />
                    <FrequencyBadge freq={test.monitoring_frequency} />
                    {test.is_platform_managed && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-medium text-blue-600 bg-blue-500/10 border-blue-500/20">
                        <Bot className="w-3 h-3" /> Automated
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-4 shrink-0 text-xs text-muted-foreground">
                    <span className="hidden lg:inline">{test.test_type_name}</span>
                    <span className="hidden md:flex items-center gap-1">
                      <Layers className="w-3 h-3" />
                      {test.mapped_control_count}
                    </span>
                    <span className="hidden sm:inline">{formatDate(test.created_at)}</span>
                  </div>

                  <div className="flex items-center gap-1 shrink-0" onClick={e => e.stopPropagation()}>
                    <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => setEditTarget(test)} title="Edit">
                      <Pencil className="w-3 h-3" />
                    </Button>
                    <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-destructive hover:text-destructive" onClick={() => setDeleteTarget(test)} title="Delete">
                      <Trash2 className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
              )
            })
          )}
        </div>
      )}

      {/* ── Pagination ──────────────────────────────────────────────────── */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-2">
          <span className="text-xs text-muted-foreground">
            Page {page + 1} of {totalPages} ({filtered.length} total)
          </span>
          <div className="flex items-center gap-1">
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0" disabled={page === 0} onClick={() => setPage(p => p - 1)}>
              <ChevronLeft className="w-4 h-4" />
            </Button>
            {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
              const pageNum = totalPages <= 7 ? i : (page < 4 ? i : (page > totalPages - 4 ? totalPages - 7 + i : page - 3 + i))
              return (
                <Button
                  key={pageNum}
                  variant={pageNum === page ? "default" : "ghost"}
                  size="sm"
                  className="h-8 w-8 p-0 text-xs"
                  onClick={() => setPage(pageNum)}
                >
                  {pageNum + 1}
                </Button>
              )
            })}
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0" disabled={page >= totalPages - 1} onClick={() => setPage(p => p + 1)}>
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}

      {/* ── Detail panel ────────────────────────────────────────────────── */}
      {detailTarget && (
        <>
          <div className="fixed inset-0 z-30" onClick={() => setDetailTarget(null)} />
          <TestDetailPanel
            test={detailTarget}
            onEdit={t => { setDetailTarget(null); setEditTarget(t) }}
            onDelete={t => { setDetailTarget(null); setDeleteTarget(t) }}
            onClose={() => setDetailTarget(null)}
          />
        </>
      )}

      {/* ── Dialogs ─────────────────────────────────────────────────────── */}
      {showCreate && (
        <TestDialog
          mode="create"
          testTypes={testTypes}
          onSaved={t => { handleSaved(t); setShowCreate(false) }}
          onClose={() => setShowCreate(false)}
        />
      )}
      {editTarget && (
        <TestDialog
          mode="edit"
          test={editTarget}
          testTypes={testTypes}
          onSaved={t => { handleSaved(t); setEditTarget(null) }}
          onClose={() => setEditTarget(null)}
        />
      )}
      {deleteTarget && (
        <DeleteConfirmDialog
          test={deleteTarget}
          onConfirm={() => handleDelete(deleteTarget)}
          onClose={() => setDeleteTarget(null)}
        />
      )}
    </div>
  )
}
