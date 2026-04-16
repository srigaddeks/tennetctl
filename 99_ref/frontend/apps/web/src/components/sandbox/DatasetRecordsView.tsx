"use client"

/**
 * DatasetRecordsView — records viewer grouped by asset type with:
 * - AI-generated descriptions at asset type level (not per record)
 * - Asset type filter tags
 * - Expandable JSON per record
 * - Background generation with live progress
 */

import { useState, useEffect, useCallback, useMemo } from "react"
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
  ChevronDown,
  ChevronRight,
  Copy,
  Check,
  FileJson,
  RefreshCw,
  AlertTriangle,
  Brain,
} from "lucide-react"
import {
  getDatasetRecords,
  generateRecordDescriptions,
  getGenerationStatus,
  getAssetTypeDescriptions,
} from "@/lib/api/sandbox"
import type { DatasetDataRecord, DatasetResponse, GenerationStatus } from "@/lib/api/sandbox"

interface Props {
  dataset: DatasetResponse
  orgId: string
  onClose: () => void
}

function MarkdownBlock({ text }: { text: string }) {
  return (
    <div className="text-xs text-muted-foreground whitespace-pre-wrap leading-relaxed">
      {text.split("\n").map((line, i) => {
        if (line.startsWith("## ")) return <h3 key={i} className="font-bold text-foreground text-sm mt-1 mb-1">{line.slice(3)}</h3>
        if (line.startsWith("### ")) return <h4 key={i} className="font-semibold text-foreground mt-2 mb-0.5">{line.slice(4)}</h4>
        if (line.startsWith("- **")) return <p key={i} className="ml-2">{line}</p>
        if (line.startsWith("  - ")) return <p key={i} className="ml-4 text-[10px]">{line.trim()}</p>
        if (line.trim()) return <p key={i}>{line}</p>
        return <br key={i} />
      })}
    </div>
  )
}

export function DatasetRecordsView({ dataset, orgId, onClose }: Props) {
  const [records, setRecords] = useState<DatasetDataRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedRecord, setExpandedRecord] = useState<string | null>(null)
  const [expandedTypeDesc, setExpandedTypeDesc] = useState<string | null>(null)
  const [generating, setGenerating] = useState(false)
  const [genStatus, setGenStatus] = useState<GenerationStatus | null>(null)
  const [generateResult, setGenerateResult] = useState<string | null>(null)
  const [copied, setCopied] = useState<string | null>(null)
  const [typeFilter, setTypeFilter] = useState<string | null>(null)
  const [typeDescs, setTypeDescs] = useState<Record<string, string>>({})

  // Asset type counts for filter tags
  const assetTypeCounts = useMemo(() => {
    const counts = new Map<string, number>()
    for (const r of records) {
      const t = r.record_data._asset_type ? String(r.record_data._asset_type) : "unknown"
      counts.set(t, (counts.get(t) || 0) + 1)
    }
    return Array.from(counts.entries()).sort((a, b) => b[1] - a[1])
  }, [records])

  const filteredRecords = useMemo(() => {
    if (!typeFilter) return records
    return records.filter((r) => String(r.record_data._asset_type || "unknown") === typeFilter)
  }, [records, typeFilter])

  // Group records by asset type for display
  const groupedRecords = useMemo(() => {
    const groups = new Map<string, DatasetDataRecord[]>()
    for (const r of filteredRecords) {
      const t = String(r.record_data._asset_type || "unknown")
      if (!groups.has(t)) groups.set(t, [])
      groups.get(t)!.push(r)
    }
    return Array.from(groups.entries())
  }, [filteredRecords])

  const describedTypes = Object.keys(typeDescs).length

  const loadRecords = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [res, descs] = await Promise.all([
        getDatasetRecords(dataset.id, { limit: 200 }),
        getAssetTypeDescriptions(dataset.id).catch(() => ({})),
      ])
      setRecords(res.records)
      setTypeDescs(descs)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load records")
    } finally {
      setLoading(false)
    }
  }, [dataset.id])

  useEffect(() => { loadRecords() }, [loadRecords])

  // Poll for generation status
  useEffect(() => {
    let timer: ReturnType<typeof setInterval> | null = null

    async function checkStatus() {
      try {
        const s = await getGenerationStatus(dataset.id)
        setGenStatus(s)
        if (s.status === "running") {
          setGenerating(true)
        } else if (s.status === "completed" || s.status === "failed") {
          setGenerating(false)
          if (s.status === "completed") {
            setGenerateResult(`AI generated ${s.updated} asset type descriptions`)
            loadRecords()
          }
          if (timer) { clearInterval(timer); timer = null }
        }
      } catch { /* ignore polling errors */ }
    }

    checkStatus()

    if (generating) {
      timer = setInterval(checkStatus, 3000)
    }

    return () => { if (timer) clearInterval(timer) }
  }, [dataset.id, generating, loadRecords])

  async function handleGenerateAll() {
    setGenerating(true)
    setGenerateResult(null)
    setError(null)
    try {
      const result = await generateRecordDescriptions(orgId, dataset.id)
      setGenStatus(result)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to start description generation")
      setGenerating(false)
    }
  }

  function handleCopy(recordId: string, json: string) {
    navigator.clipboard.writeText(json)
    setCopied(recordId)
    setTimeout(() => setCopied(null), 2000)
  }

  return (
    <Dialog open onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="sm:max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader className="shrink-0">
          <div className="flex items-center gap-2">
            <FileJson className="h-5 w-5 text-indigo-500" />
            <DialogTitle>{dataset.name || dataset.dataset_code}</DialogTitle>
          </div>
          <DialogDescription>
            {records.length} records · {assetTypeCounts.length} asset types · {describedTypes} described
          </DialogDescription>
        </DialogHeader>

        {/* Action bar */}
        <div className="flex items-center gap-2 shrink-0 pb-2 border-b border-border">
          <Button
            size="sm"
            onClick={handleGenerateAll}
            disabled={generating}
            className="gap-1.5 bg-purple-600 hover:bg-purple-700 text-white border-0"
          >
            {generating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Sparkles className="h-3.5 w-3.5" />}
            {generating && genStatus && genStatus.total > 0
              ? `Generating ${genStatus.processed}/${genStatus.total}...`
              : generating
              ? "Starting..."
              : "AI Describe Asset Types"}
          </Button>
          <Button variant="outline" size="sm" onClick={loadRecords} disabled={loading} className="gap-1.5">
            <RefreshCw className="h-3 w-3" /> Refresh
          </Button>
          <span className="text-xs text-muted-foreground ml-auto">
            {describedTypes}/{assetTypeCounts.length} types described
          </span>
        </div>

        {/* Progress bar during generation */}
        {generating && genStatus && genStatus.total > 0 && (
          <div className="shrink-0">
            <div className="h-1.5 rounded-full bg-muted/30 overflow-hidden">
              <div
                className="h-full bg-purple-500 rounded-full transition-all duration-500"
                style={{ width: `${Math.round((genStatus.processed / genStatus.total) * 100)}%` }}
              />
            </div>
            <div className="flex justify-between mt-1">
              <span className="text-[10px] text-muted-foreground">
                {genStatus.updated} described · {genStatus.errors} errors
              </span>
              <span className="text-[10px] text-purple-400 font-medium">
                {Math.round((genStatus.processed / genStatus.total) * 100)}%
              </span>
            </div>
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-500 flex items-center gap-2 shrink-0">
            <AlertTriangle className="h-4 w-4 shrink-0" />{error}
          </div>
        )}

        {generateResult && (
          <div className="rounded-lg border border-green-500/30 bg-green-500/10 px-3 py-2 text-sm text-green-500 shrink-0">
            {generateResult}
          </div>
        )}

        {/* Asset type filter tags */}
        {assetTypeCounts.length > 1 && (
          <div className="flex flex-wrap gap-1.5 shrink-0 pb-2">
            <button
              onClick={() => setTypeFilter(null)}
              className={`rounded-full px-2.5 py-0.5 text-[10px] font-medium border transition-colors ${
                !typeFilter
                  ? "bg-indigo-500/20 border-indigo-500/40 text-indigo-400"
                  : "border-border text-muted-foreground hover:text-foreground hover:border-foreground/30"
              }`}
            >
              All ({records.length})
            </button>
            {assetTypeCounts.map(([type, count]) => (
              <button
                key={type}
                onClick={() => setTypeFilter(typeFilter === type ? null : type)}
                className={`rounded-full px-2.5 py-0.5 text-[10px] font-medium border transition-colors ${
                  typeFilter === type
                    ? "bg-cyan-500/20 border-cyan-500/40 text-cyan-400"
                    : "border-border text-muted-foreground hover:text-foreground hover:border-foreground/30"
                }`}
              >
                {type.replace(/_/g, " ")} ({count})
                {typeDescs[type] && " ✓"}
              </button>
            ))}
          </div>
        )}

        {/* Records grouped by asset type */}
        <div className="flex-1 overflow-y-auto space-y-4 pr-1">
          {loading && (
            <div className="py-8 text-center">
              <Loader2 className="h-5 w-5 animate-spin text-indigo-500 mx-auto mb-2" />
              <p className="text-xs text-muted-foreground">Loading records...</p>
            </div>
          )}

          {!loading && groupedRecords.map(([assetType, recs]) => (
            <div key={assetType} className="space-y-1.5">
              {/* Asset type header with AI description */}
              <div className="rounded-lg border border-border bg-muted/20 overflow-hidden">
                <button
                  onClick={() => setExpandedTypeDesc(expandedTypeDesc === assetType ? null : assetType)}
                  className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-muted/30 transition-colors"
                >
                  <Badge variant="outline" className="text-[10px] font-mono bg-cyan-500/10 text-cyan-500 border-cyan-500/30 shrink-0">
                    {assetType.replace(/_/g, " ")}
                  </Badge>
                  <span className="text-xs text-muted-foreground">{recs.length} records</span>
                  {typeDescs[assetType] ? (
                    <Badge variant="outline" className="text-[9px] bg-purple-500/10 text-purple-400 border-purple-500/30 ml-auto shrink-0">
                      <Brain className="h-2.5 w-2.5 mr-0.5" /> AI described
                    </Badge>
                  ) : (
                    <span className="text-[10px] text-muted-foreground/50 ml-auto">no description</span>
                  )}
                  {typeDescs[assetType] && (
                    expandedTypeDesc === assetType
                      ? <ChevronDown className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                      : <ChevronRight className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                  )}
                </button>
                {expandedTypeDesc === assetType && typeDescs[assetType] && (
                  <div className="border-t border-border px-4 py-3 bg-purple-500/5">
                    <MarkdownBlock text={typeDescs[assetType]} />
                  </div>
                )}
              </div>

              {/* Records for this type */}
              {recs.map((rec) => {
                const isExpanded = expandedRecord === rec.id
                return (
                  <div key={rec.id} className="rounded-lg border border-border bg-card overflow-hidden ml-3">
                    <div className="flex items-center gap-2 px-3 py-2 hover:bg-muted/30 transition-colors">
                      <button
                        onClick={() => setExpandedRecord(isExpanded ? null : rec.id)}
                        className="flex items-center gap-2 flex-1 min-w-0 text-left"
                      >
                        {isExpanded
                          ? <ChevronDown className="h-3 w-3 text-muted-foreground shrink-0" />
                          : <ChevronRight className="h-3 w-3 text-muted-foreground shrink-0" />}
                        <span className="text-[10px] font-mono text-muted-foreground shrink-0">#{rec.record_seq}</span>
                        <span className="text-xs font-medium truncate flex-1">
                          {rec.record_data._external_id
                            ? String(rec.record_data._external_id)
                            : rec.record_data.name
                            ? String(rec.record_data.name)
                            : Object.entries(rec.record_data)
                                .filter(([k]) => !k.startsWith("_"))
                                .slice(0, 2)
                                .map(([k, v]) => `${k}: ${String(v).slice(0, 20)}`)
                                .join(" · ") || `${Object.keys(rec.record_data).length} fields`
                          }
                        </span>
                      </button>
                      <span className="text-[10px] text-muted-foreground shrink-0">
                        {Object.keys(rec.record_data).length} fields
                      </span>
                    </div>

                    {isExpanded && (
                      <div className="border-t border-border px-3 py-2">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-[10px] font-semibold text-muted-foreground flex items-center gap-1">
                            <FileJson className="h-3 w-3" /> JSON
                          </span>
                          <button
                            onClick={() => handleCopy(rec.id, JSON.stringify(rec.record_data, null, 2))}
                            className="text-[10px] text-muted-foreground hover:text-foreground flex items-center gap-0.5 px-1.5 py-0.5 rounded hover:bg-muted"
                          >
                            {copied === rec.id ? <Check className="h-2.5 w-2.5 text-green-500" /> : <Copy className="h-2.5 w-2.5" />}
                            {copied === rec.id ? "Copied!" : "Copy"}
                          </button>
                        </div>
                        <pre className="text-[10px] font-mono text-muted-foreground bg-muted/30 rounded-md p-2 max-h-48 overflow-y-auto whitespace-pre-wrap">
                          {JSON.stringify(rec.record_data, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          ))}
        </div>

        <DialogFooter className="shrink-0 pt-2">
          <Button variant="outline" size="sm" onClick={onClose}>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
