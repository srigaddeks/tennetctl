"use client"

/**
 * DatasetAIPanel — AI-powered dataset analysis panel.
 *
 * Features:
 * - Explain every JSON record (field-by-field with compliance relevance)
 * - Generate varied test data from schema
 * - Analyze dataset quality + suggest improvements
 */

import { useState } from "react"
import {
  Button,
  Badge,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@kcontrol/ui"
import {
  Sparkles,
  Loader2,
  Brain,
  AlertTriangle,
  CheckCircle2,
  Lightbulb,
  Plus,
  ChevronDown,
  ChevronRight,
  Shield,
  Zap,
} from "lucide-react"
import {
  aiExplainRecord,
  aiExplainDataset,
  aiComposeTestData,
  aiEnhanceDataset,
  addDatasetRecords,
} from "@/lib/api/sandbox"
import type {
  ExplainRecordResponse,
  ExplainDatasetResponse,
  ComposeTestDataResponse,
  EnhanceDatasetResponse,
  DatasetDataRecord,
} from "@/lib/api/sandbox"

// ── Explain Record Dialog ────────────────────────────────────────────────────

export function ExplainRecordDialog({
  record,
  assetType,
  connectorType,
  onClose,
}: {
  record: DatasetDataRecord
  assetType?: string
  connectorType?: string
  onClose: () => void
}) {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ExplainRecordResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [expandedField, setExpandedField] = useState<number | null>(null)

  async function handleExplain() {
    setLoading(true)
    setError(null)
    try {
      const r = await aiExplainRecord({
        record_data: record.record_data,
        asset_type_hint: assetType,
        connector_type: connectorType,
      })
      setResult(r)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to explain record")
    } finally {
      setLoading(false)
    }
  }

  const relevanceColor = (r: string) => {
    if (r === "high") return "bg-red-500/20 text-red-500 border-red-500/30"
    if (r === "medium") return "bg-amber-500/20 text-amber-600 border-amber-500/30"
    if (r === "low") return "bg-blue-500/20 text-blue-500 border-blue-500/30"
    return "bg-muted text-muted-foreground"
  }

  return (
    <Dialog open onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-purple-500" />
            <DialogTitle>AI Record Explanation</DialogTitle>
          </div>
          <DialogDescription>
            Understand every field — what it means, its compliance relevance, and what signals could use it.
          </DialogDescription>
        </DialogHeader>

        {!result && !loading && (
          <div className="py-6 text-center">
            <Brain className="h-10 w-10 text-purple-500/30 mx-auto mb-3" />
            <p className="text-sm text-muted-foreground mb-4">
              AI will analyze {Object.keys(record.record_data).length} fields and explain their compliance significance.
            </p>
            <Button onClick={handleExplain} className="gap-1.5 bg-purple-600 hover:bg-purple-700 text-white border-0">
              <Sparkles className="h-3.5 w-3.5" /> Explain with AI
            </Button>
          </div>
        )}

        {loading && (
          <div className="py-8 text-center">
            <Loader2 className="h-6 w-6 animate-spin text-purple-500 mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">Analyzing {Object.keys(record.record_data).length} fields...</p>
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-500 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            {error}
          </div>
        )}

        {result && (
          <div className="space-y-4">
            {/* Summary */}
            <div className="rounded-lg border border-purple-500/20 bg-purple-500/5 p-3">
              <p className="text-sm font-medium text-purple-600 dark:text-purple-400">{result.asset_type}</p>
              <p className="text-xs text-muted-foreground mt-0.5">{result.record_summary}</p>
            </div>

            {/* Field explanations */}
            <div className="space-y-1.5 max-h-72 overflow-y-auto pr-1">
              {result.fields.map((f, i) => (
                <div key={f.field_name} className="rounded border border-border bg-card">
                  <button
                    onClick={() => setExpandedField(expandedField === i ? null : i)}
                    className="flex items-center gap-2 px-3 py-2 w-full text-left hover:bg-muted/30 transition-colors"
                  >
                    {expandedField === i ? <ChevronDown className="h-3 w-3 text-muted-foreground" /> : <ChevronRight className="h-3 w-3 text-muted-foreground" />}
                    <code className="text-xs font-mono flex-1">{f.field_name}</code>
                    <span className="text-[10px] text-muted-foreground">{f.data_type}</span>
                    <Badge variant="outline" className={`text-[9px] ${relevanceColor(f.compliance_relevance)}`}>
                      {f.compliance_relevance}
                    </Badge>
                  </button>
                  {expandedField === i && (
                    <div className="border-t border-border px-3 py-2 space-y-1.5 text-xs">
                      <p className="text-muted-foreground">{f.description}</p>
                      {f.example_signal_uses.length > 0 && (
                        <div>
                          <span className="text-[10px] font-semibold text-purple-500 flex items-center gap-1">
                            <Zap className="h-2.5 w-2.5" /> Signal ideas:
                          </span>
                          <ul className="ml-4 list-disc text-muted-foreground">
                            {f.example_signal_uses.map((u, j) => <li key={j}>{u}</li>)}
                          </ul>
                        </div>
                      )}
                      {f.anomaly_indicators.length > 0 && (
                        <div>
                          <span className="text-[10px] font-semibold text-amber-500 flex items-center gap-1">
                            <AlertTriangle className="h-2.5 w-2.5" /> Anomaly indicators:
                          </span>
                          <ul className="ml-4 list-disc text-muted-foreground">
                            {f.anomaly_indicators.map((a, j) => <li key={j}>{a}</li>)}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Recommended signals */}
            {result.recommended_signals.length > 0 && (
              <div className="space-y-1.5">
                <h4 className="text-xs font-semibold flex items-center gap-1">
                  <Lightbulb className="h-3.5 w-3.5 text-amber-500" /> Recommended Signals
                </h4>
                {result.recommended_signals.map((s, i) => (
                  <div key={i} className="rounded border border-amber-500/20 bg-amber-500/5 px-3 py-2">
                    <p className="text-xs font-medium">{s.signal_name}</p>
                    <p className="text-[10px] text-muted-foreground">{s.description}</p>
                    <div className="flex items-center gap-1 mt-1">
                      {s.fields_used.map((f) => (
                        <span key={f} className="text-[9px] px-1 py-0.5 rounded bg-muted font-mono">{f}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" size="sm" onClick={onClose}>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ── Dataset Quality Analysis Dialog ──────────────────────────────────────────

export function DatasetQualityDialog({
  records,
  datasetId,
  orgId,
  assetType,
  connectorType,
  onRecordsAdded,
  onClose,
}: {
  records: Array<Record<string, unknown>>
  datasetId: string
  orgId: string
  assetType?: string
  connectorType?: string
  onRecordsAdded?: () => void
  onClose: () => void
}) {
  type Tab = "explain" | "enhance" | "compose"
  const [activeTab, setActiveTab] = useState<Tab>("explain")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [explainResult, setExplainResult] = useState<ExplainDatasetResponse | null>(null)
  const [enhanceResult, setEnhanceResult] = useState<EnhanceDatasetResponse | null>(null)
  const [composeResult, setComposeResult] = useState<ComposeTestDataResponse | null>(null)
  const [addingRecords, setAddingRecords] = useState(false)

  async function runExplain() {
    setLoading(true)
    setError(null)
    try {
      const r = await aiExplainDataset({ records, asset_type: assetType, connector_type: connectorType })
      setExplainResult(r)
    } catch (e) { setError(e instanceof Error ? e.message : "Failed") }
    finally { setLoading(false) }
  }

  async function runEnhance() {
    setLoading(true)
    setError(null)
    try {
      const r = await aiEnhanceDataset({ records, asset_type: assetType, connector_type: connectorType })
      setEnhanceResult(r)
    } catch (e) { setError(e instanceof Error ? e.message : "Failed") }
    finally { setLoading(false) }
  }

  async function runCompose() {
    setLoading(true)
    setError(null)
    try {
      const keys = new Set<string>()
      records.forEach((r) => Object.keys(r).forEach((k) => keys.add(k)))
      const r = await aiComposeTestData({
        property_keys: Array.from(keys),
        sample_records: records.slice(0, 3),
        asset_type: assetType || "unknown",
        connector_type: connectorType,
        record_count: 10,
      })
      setComposeResult(r)
    } catch (e) { setError(e instanceof Error ? e.message : "Failed") }
    finally { setLoading(false) }
  }

  async function handleAddGeneratedRecords() {
    if (!composeResult?.generated_records.length) return
    setAddingRecords(true)
    try {
      await addDatasetRecords(orgId, datasetId, { records: composeResult.generated_records })
      onRecordsAdded?.()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add records")
    } finally {
      setAddingRecords(false)
    }
  }

  const qualityColor = (score: number) => {
    if (score >= 80) return "text-green-500"
    if (score >= 50) return "text-amber-500"
    return "text-red-500"
  }

  return (
    <Dialog open onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-3xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-purple-500" />
            <DialogTitle>AI Dataset Assistant</DialogTitle>
          </div>
          <DialogDescription>
            Explain, analyze, and enhance your dataset with AI. {records.length} records loaded.
          </DialogDescription>
        </DialogHeader>

        {/* Tab bar */}
        <div className="flex gap-1 border-b border-border pb-2">
          {([
            { key: "explain" as Tab, label: "Explain Schema", icon: Brain },
            { key: "enhance" as Tab, label: "Quality Analysis", icon: Shield },
            { key: "compose" as Tab, label: "Generate Test Data", icon: Plus },
          ]).map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${activeTab === key ? "bg-purple-500/10 text-purple-500" : "text-muted-foreground hover:text-foreground hover:bg-muted"}`}
            >
              <Icon className="h-3.5 w-3.5" /> {label}
            </button>
          ))}
        </div>

        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-500 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            {error}
          </div>
        )}

        {/* Explain Tab */}
        {activeTab === "explain" && (
          <div className="space-y-3">
            {!explainResult && !loading && (
              <div className="py-6 text-center">
                <Brain className="h-8 w-8 text-purple-500/30 mx-auto mb-2" />
                <p className="text-sm text-muted-foreground mb-3">
                  AI will explain every field and every record in your dataset.
                </p>
                <Button onClick={runExplain} className="gap-1.5 bg-purple-600 hover:bg-purple-700 text-white border-0" size="sm">
                  <Sparkles className="h-3.5 w-3.5" /> Explain Dataset
                </Button>
              </div>
            )}
            {loading && (
              <div className="py-6 text-center">
                <Loader2 className="h-5 w-5 animate-spin text-purple-500 mx-auto mb-2" />
                <p className="text-xs text-muted-foreground">Analyzing {records.length} records...</p>
              </div>
            )}
            {explainResult && (
              <>
                <div className="rounded-lg border border-purple-500/20 bg-purple-500/5 p-3">
                  <p className="text-sm font-medium text-purple-600 dark:text-purple-400">{explainResult.dataset_summary}</p>
                  <p className="text-xs text-muted-foreground mt-1">Quality: <strong>{explainResult.overall_quality}</strong></p>
                </div>

                {/* Schema fields */}
                <div className="space-y-1 max-h-48 overflow-y-auto">
                  <h4 className="text-xs font-semibold">Schema Fields ({explainResult.schema_fields.length})</h4>
                  {explainResult.schema_fields.map((f) => (
                    <div key={f.field_name} className="flex items-center gap-2 text-xs px-2 py-1 rounded bg-muted/30">
                      <code className="font-mono flex-1 truncate">{f.field_name}</code>
                      <span className="text-muted-foreground">{f.data_type}</span>
                      <Badge variant="outline" className="text-[9px]">{f.compliance_relevance}</Badge>
                    </div>
                  ))}
                </div>

                {/* Record explanations */}
                <div className="space-y-1 max-h-48 overflow-y-auto">
                  <h4 className="text-xs font-semibold">Record Analysis</h4>
                  {explainResult.record_explanations.map((r) => (
                    <div key={r.record_index} className="flex items-start gap-2 text-xs px-2 py-1.5 rounded bg-muted/30">
                      <span className="font-mono text-muted-foreground shrink-0">#{r.record_index + 1}</span>
                      <div className="flex-1">
                        <p className="font-medium">{r.summary}</p>
                        <p className="text-muted-foreground">{r.key_observations.join(" • ")}</p>
                      </div>
                      <Badge variant="outline" className="text-[9px] shrink-0">{r.compliance_status}</Badge>
                    </div>
                  ))}
                </div>

                {explainResult.improvement_suggestions.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold flex items-center gap-1 mb-1"><Lightbulb className="h-3 w-3 text-amber-500" /> Suggestions</h4>
                    <ul className="text-xs text-muted-foreground list-disc ml-4 space-y-0.5">
                      {explainResult.improvement_suggestions.map((s, i) => <li key={i}>{s}</li>)}
                    </ul>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* Enhance Tab */}
        {activeTab === "enhance" && (
          <div className="space-y-3">
            {!enhanceResult && !loading && (
              <div className="py-6 text-center">
                <Shield className="h-8 w-8 text-purple-500/30 mx-auto mb-2" />
                <p className="text-sm text-muted-foreground mb-3">
                  AI will find gaps, missing scenarios, and suggest improvements.
                </p>
                <Button onClick={runEnhance} className="gap-1.5 bg-purple-600 hover:bg-purple-700 text-white border-0" size="sm">
                  <Sparkles className="h-3.5 w-3.5" /> Analyze Quality
                </Button>
              </div>
            )}
            {loading && (
              <div className="py-6 text-center">
                <Loader2 className="h-5 w-5 animate-spin text-purple-500 mx-auto mb-2" />
                <p className="text-xs text-muted-foreground">Analyzing quality...</p>
              </div>
            )}
            {enhanceResult && (
              <>
                <div className="flex items-center justify-between rounded-lg border border-border bg-muted/30 p-3">
                  <span className="text-sm font-medium">Quality Score</span>
                  <span className={`text-2xl font-bold ${qualityColor(enhanceResult.quality_score)}`}>{enhanceResult.quality_score}/100</span>
                </div>

                {enhanceResult.strengths.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold flex items-center gap-1 mb-1"><CheckCircle2 className="h-3 w-3 text-green-500" /> Strengths</h4>
                    <ul className="text-xs text-muted-foreground list-disc ml-4">{enhanceResult.strengths.map((s, i) => <li key={i}>{s}</li>)}</ul>
                  </div>
                )}

                {enhanceResult.gaps.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold flex items-center gap-1 mb-1"><AlertTriangle className="h-3 w-3 text-amber-500" /> Gaps</h4>
                    {enhanceResult.gaps.map((g, i) => (
                      <div key={i} className="rounded border border-border px-2 py-1.5 mb-1 text-xs">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className={`text-[9px] ${g.severity === "critical" ? "bg-red-500/20 text-red-500" : g.severity === "high" ? "bg-amber-500/20 text-amber-500" : "bg-muted"}`}>{g.severity}</Badge>
                          <span className="font-medium">{g.gap}</span>
                        </div>
                        <p className="text-muted-foreground mt-0.5">{g.suggestion}</p>
                      </div>
                    ))}
                  </div>
                )}

                {enhanceResult.missing_scenarios.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold flex items-center gap-1 mb-1"><Plus className="h-3 w-3 text-blue-500" /> Missing Scenarios</h4>
                    {enhanceResult.missing_scenarios.map((s, i) => (
                      <div key={i} className="rounded border border-blue-500/20 bg-blue-500/5 px-2 py-1.5 mb-1 text-xs">
                        <span className="font-medium">{s.scenario_name}</span>
                        <span className="ml-2 text-muted-foreground">→ expected: {s.expected_result}</span>
                        <p className="text-muted-foreground">{s.description}</p>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* Compose Tab */}
        {activeTab === "compose" && (
          <div className="space-y-3">
            {!composeResult && !loading && (
              <div className="py-6 text-center">
                <Plus className="h-8 w-8 text-purple-500/30 mx-auto mb-2" />
                <p className="text-sm text-muted-foreground mb-3">
                  AI will generate 10 varied test records covering compliant, non-compliant, and edge cases.
                </p>
                <Button onClick={runCompose} className="gap-1.5 bg-purple-600 hover:bg-purple-700 text-white border-0" size="sm">
                  <Sparkles className="h-3.5 w-3.5" /> Generate Test Data
                </Button>
              </div>
            )}
            {loading && (
              <div className="py-6 text-center">
                <Loader2 className="h-5 w-5 animate-spin text-purple-500 mx-auto mb-2" />
                <p className="text-xs text-muted-foreground">Generating varied test records...</p>
              </div>
            )}
            {composeResult && (
              <>
                <div className="rounded-lg border border-green-500/20 bg-green-500/5 p-3">
                  <p className="text-sm font-medium text-green-600 dark:text-green-400">
                    Generated {composeResult.generated_records.length} test records
                  </p>
                  <p className="text-xs text-muted-foreground">{composeResult.coverage_notes}</p>
                </div>

                <div className="space-y-1 max-h-64 overflow-y-auto pr-1">
                  {composeResult.generated_records.map((r, i) => {
                    const scenario = (r as Record<string, unknown>)._scenario_name as string || `Record ${i + 1}`
                    const expected = (r as Record<string, unknown>)._expected_result as string || "?"
                    const explanation = (r as Record<string, unknown>)._explanation as string || ""
                    return (
                      <div key={i} className="rounded border border-border px-3 py-2 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="font-medium">{scenario}</span>
                          <Badge variant="outline" className={`text-[9px] ${expected === "pass" ? "bg-green-500/20 text-green-500" : expected === "fail" ? "bg-red-500/20 text-red-500" : "bg-amber-500/20 text-amber-500"}`}>{expected}</Badge>
                        </div>
                        {explanation && <p className="text-muted-foreground mt-0.5">{explanation}</p>}
                      </div>
                    )
                  })}
                </div>

                <Button
                  onClick={handleAddGeneratedRecords}
                  disabled={addingRecords}
                  className="gap-1.5 bg-green-600 hover:bg-green-700 text-white border-0"
                  size="sm"
                >
                  {addingRecords ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Plus className="h-3.5 w-3.5" />}
                  Add {composeResult.generated_records.length} Records to Dataset
                </Button>
              </>
            )}
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" size="sm" onClick={onClose}>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
