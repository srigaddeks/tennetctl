"use client"

/**
 * DatasetBuilder — guided wizard for creating datasets from connector assets.
 *
 * Flow: Pick Connector → Pick Asset Type → Preview Samples → Name & Create
 *
 * Each dataset is scoped to ONE connector + ONE asset type.
 * Users can add 100s of JSON samples manually after creation.
 */

import { useState, useEffect, useCallback } from "react"
import {
  Button,
  Input,
  Label,
  Badge,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@kcontrol/ui"
import {
  Database,
  ChevronRight,
  ChevronLeft,
  ChevronDown,
  Loader2,
  AlertTriangle,
  CheckCircle2,
  Eye,
  Copy,
  Server,
  Layers,
  FileJson,
  Sparkles,
} from "lucide-react"
import {
  listConnectors,
  getConnectorAssetTypes,
  getAssetSamples,
  createDataset,
  addDatasetRecords,
  composeDataset,
  smartComposeDataset,
  smartPreviewDataset,
} from "@/lib/api/sandbox"
import type {
  ConnectorInstanceResponse,
  AssetTypeInfo,
  AssetSampleRecord,
  DatasetResponse,
  SmartPreviewResponse,
} from "@/lib/api/sandbox"

interface Props {
  open: boolean
  orgId: string
  workspaceId?: string
  defaultConnectorId?: string
  onCreated: (datasetId: string, name: string) => void
  onClose: () => void
}

type Step = "connector" | "asset_type" | "preview" | "create"

export function DatasetBuilder({ open, orgId, workspaceId, defaultConnectorId, onCreated, onClose }: Props) {
  const [step, setStep] = useState<Step>("connector")

  // Step 1: Connector
  const [connectors, setConnectors] = useState<ConnectorInstanceResponse[]>([])
  const [connectorsLoading, setConnectorsLoading] = useState(false)
  const [selectedConnector, setSelectedConnector] = useState<ConnectorInstanceResponse | null>(null)

  // Step 2: Asset Type
  const [assetTypes, setAssetTypes] = useState<AssetTypeInfo[]>([])
  const [assetTypesLoading, setAssetTypesLoading] = useState(false)
  const [selectedAssetType, setSelectedAssetType] = useState<AssetTypeInfo | null>(null)

  // Step 3: Preview
  const [samples, setSamples] = useState<AssetSampleRecord[]>([])
  const [totalCount, setTotalCount] = useState(0)
  const [propertyKeys, setPropertyKeys] = useState<string[]>([])
  const [samplesLoading, setSamplesLoading] = useState(false)
  const [expandedSample, setExpandedSample] = useState<number | null>(0)

  // Step 4: Create
  const [datasetName, setDatasetName] = useState("")
  const [datasetDescription, setDatasetDescription] = useState("")
  const [includeAllAssets, setIncludeAllAssets] = useState(true)
  const [creating, setCreating] = useState(false)

  // Smart preview
  const [smartPreview, setSmartPreview] = useState<SmartPreviewResponse | null>(null)
  const [smartPreviewLoading, setSmartPreviewLoading] = useState(false)
  const [smartPreviewExpanded, setSmartPreviewExpanded] = useState<number | null>(0)
  const [smartTypeFilter, setSmartTypeFilter] = useState("")

  const [error, setError] = useState<string | null>(null)

  // Load connectors on open
  useEffect(() => {
    if (!open || !orgId) return
    setConnectorsLoading(true)
    listConnectors({ org_id: orgId })
      .then((res) => {
        setConnectors(res.items)
        // Auto-select connector if defaultConnectorId is provided
        if (defaultConnectorId) {
          const match = res.items.find((c) => c.id === defaultConnectorId)
          if (match) {
            setSelectedConnector(match)
            setStep("asset_type")
          }
        }
      })
      .catch(() => setError("Failed to load connectors"))
      .finally(() => setConnectorsLoading(false))
  }, [open, orgId, defaultConnectorId])

  // Load asset types when connector selected
  const loadAssetTypes = useCallback(async (connId: string) => {
    setAssetTypesLoading(true)
    setError(null)
    try {
      const res = await getConnectorAssetTypes(orgId, connId)
      setAssetTypes(res.asset_types)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load asset types")
    } finally {
      setAssetTypesLoading(false)
    }
  }, [orgId])

  // Auto-load asset types when connector auto-selected from URL
  useEffect(() => {
    if (selectedConnector && step === "asset_type" && assetTypes.length === 0 && !assetTypesLoading) {
      loadAssetTypes(selectedConnector.id)
    }
  }, [selectedConnector, step, assetTypes.length, assetTypesLoading, loadAssetTypes])

  // "Smart Dataset" — load preview with diversity-maximising samples
  async function selectAllAssets() {
    if (!selectedConnector || assetTypes.length === 0) return
    const allType: AssetTypeInfo = {
      asset_type_code: "__all__",
      asset_count: assetTypes.reduce((s, t) => s + t.asset_count, 0),
      sample_property_keys: [...new Set(assetTypes.flatMap((t) => t.sample_property_keys))],
    }
    setSelectedAssetType(allType)
    const connName = selectedConnector.name || selectedConnector.connector_type_code || "connector"
    setDatasetName(`${connName} — Smart Dataset`)
    setStep("preview")
    setSmartPreviewLoading(true)
    setSmartPreview(null)
    setError(null)
    try {
      const preview = await smartPreviewDataset(orgId, {
        connector_instance_id: selectedConnector.id,
        samples_per_type: 10,
      })
      setSmartPreview(preview)
      setDatasetDescription(preview.composition_summary)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load preview")
    } finally {
      setSmartPreviewLoading(false)
    }
  }

  // Load samples when asset type selected
  const loadSamples = useCallback(async (connId: string, assetType: string) => {
    setSamplesLoading(true)
    setError(null)
    try {
      const res = await getAssetSamples(orgId, connId, assetType, 10)
      setSamples(res.samples)
      setTotalCount(res.total_count)
      setPropertyKeys(res.property_keys)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load samples")
    } finally {
      setSamplesLoading(false)
    }
  }, [orgId])

  function selectConnector(conn: ConnectorInstanceResponse) {
    setSelectedConnector(conn)
    setSelectedAssetType(null)
    setSamples([])
    setStep("asset_type")
    loadAssetTypes(conn.id)
  }

  function selectAssetType(at: AssetTypeInfo) {
    setSelectedAssetType(at)
    setStep("preview")
    if (selectedConnector) {
      loadSamples(selectedConnector.id, at.asset_type_code)
      // Auto-name the dataset
      const connName = selectedConnector.name || selectedConnector.connector_type_code || "connector"
      setDatasetName(`${connName} — ${at.asset_type_code.replace(/_/g, " ")}`)
    }
  }

  function goToCreate() {
    setStep("create")
  }

  async function handleCreate() {
    if (!selectedConnector || !selectedAssetType || !datasetName.trim()) return
    setCreating(true)
    setError(null)
    try {
      if (selectedAssetType.asset_type_code === "__all__") {
        // Smart compose — diversity-maximising sample across all asset types
        await smartComposeDataset(orgId, {
          connector_instance_id: selectedConnector.id,
          name: datasetName.trim(),
          description: datasetDescription.trim() || undefined,
          workspace_id: workspaceId || undefined,
          samples_per_type: 10,
        })
        onCreated("", datasetName.trim())
        return
      }

      // Single asset type — create the dataset
      const ds: DatasetResponse = await createDataset(orgId, {
        dataset_source_code: "connector_pull",
        connector_instance_id: selectedConnector.id,
        properties: {
          name: datasetName.trim(),
          description: datasetDescription.trim() || `${selectedAssetType.asset_type_code} assets from ${selectedConnector.name || selectedConnector.id}`,
          asset_type_code: selectedAssetType.asset_type_code,
        },
      })

      // Add all sample records as initial data
      if (includeAllAssets && samples.length > 0) {
        const records = samples.map((s) => ({
          ...s.properties,
          _asset_id: s.asset_id,
          _asset_external_id: s.asset_external_id,
          _asset_type: selectedAssetType.asset_type_code,
        }))
        await addDatasetRecords(orgId, ds.id, {
          records,
          connector_instance_id: selectedConnector.id,
        }).catch(() => {
          // Non-critical if records fail
        })
      }

      onCreated(ds.id, datasetName.trim())
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create dataset")
    } finally {
      setCreating(false)
    }
  }

  function reset() {
    setStep("connector")
    setSelectedConnector(null)
    setSelectedAssetType(null)
    setSamples([])
    setPropertyKeys([])
    setTotalCount(0)
    setDatasetName("")
    setDatasetDescription("")
    setError(null)
  }

  function handleClose() {
    reset()
    onClose()
  }

  const stepNumber = step === "connector" ? 1 : step === "asset_type" ? 2 : step === "preview" ? 3 : 4

  return (
    <Dialog open={open} onOpenChange={(v) => !v && handleClose()}>
      <DialogContent className="sm:max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <Database className="h-5 w-5 text-indigo-500" />
            <DialogTitle>Dataset Builder</DialogTitle>
          </div>
          <DialogDescription>
            Create a focused dataset from collected assets. Each dataset = one connector + one asset type.
          </DialogDescription>
        </DialogHeader>

        {/* Step indicator */}
        <div className="flex items-center gap-1 py-2">
          {["Connector", "Asset Type", "Preview", "Create"].map((label, i) => (
            <div key={label} className="flex items-center gap-1">
              {i > 0 && <ChevronRight className="h-3 w-3 text-muted-foreground" />}
              <span className={`text-xs px-2 py-0.5 rounded-full ${i + 1 === stepNumber ? "bg-indigo-500/20 text-indigo-500 font-semibold" : i + 1 < stepNumber ? "bg-green-500/20 text-green-500" : "bg-muted text-muted-foreground"}`}>
                {i + 1}. {label}
              </span>
            </div>
          ))}
        </div>

        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-500 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            {error}
          </div>
        )}

        {/* Step 1: Pick Connector */}
        {step === "connector" && (
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">
              Select the connector whose collected assets you want to build a dataset from.
            </p>
            {connectorsLoading ? (
              <div className="flex items-center gap-2 py-8 justify-center text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" /> Loading connectors...
              </div>
            ) : connectors.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground text-sm">
                No connectors found. Create a connector and run a collection first.
              </div>
            ) : (
              <div className="grid gap-2">
                {connectors.map((conn) => (
                  <button
                    key={conn.id}
                    onClick={() => selectConnector(conn)}
                    className="flex items-center gap-3 rounded-lg border border-border bg-card hover:bg-muted/40 px-4 py-3 text-left transition-colors group"
                  >
                    <div className="rounded-lg bg-indigo-500/10 p-2 shrink-0">
                      <Server className="h-4 w-4 text-indigo-500" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium truncate">{conn.name || conn.connector_type_code}</span>
                        <Badge variant="outline" className="text-[10px]">{conn.connector_type_code}</Badge>
                      </div>
                      <p className="text-xs text-muted-foreground truncate">{conn.id}</p>
                    </div>
                    <ChevronRight className="h-4 w-4 text-muted-foreground group-hover:text-foreground transition-colors" />
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Step 2: Pick Asset Type */}
        {step === "asset_type" && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <button onClick={() => { setStep("connector"); setSelectedConnector(null) }} className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1">
                <ChevronLeft className="h-3 w-3" /> Back
              </button>
              <Badge variant="outline" className="text-xs">
                <Server className="h-3 w-3 mr-1" />{selectedConnector?.name || selectedConnector?.connector_type_code}
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground">
              Pick an asset type, or select all assets from this connector.
            </p>
            {!assetTypesLoading && assetTypes.length > 1 && (
              <button
                onClick={selectAllAssets}
                className="w-full flex items-center gap-3 rounded-xl border-2 border-dashed border-green-500/40 bg-green-500/5 px-4 py-3 hover:bg-green-500/10 transition-colors text-left mb-2"
              >
                <div className="rounded-lg bg-green-500/10 p-2">
                  <Sparkles className="h-4 w-4 text-green-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-green-500">Smart Dataset</span>
                    <Badge className="bg-green-500/10 text-green-500 border-green-500/30 text-[10px]">
                      AI-curated samples
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {assetTypes.map((t) => `${t.asset_type_code.replace(/_/g, " ")} (${t.asset_count})`).join(", ")}
                  </p>
                </div>
                <ChevronRight className="h-4 w-4 text-green-500 shrink-0" />
              </button>
            )}
            {assetTypesLoading ? (
              <div className="flex items-center gap-2 py-8 justify-center text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" /> Loading asset types...
              </div>
            ) : assetTypes.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground text-sm">
                No assets found. Run a collection on this connector first.
              </div>
            ) : (
              <div className="grid gap-2">
                {assetTypes.map((at) => (
                  <button
                    key={at.asset_type_code}
                    onClick={() => selectAssetType(at)}
                    className="flex items-center gap-3 rounded-lg border border-border bg-card hover:bg-muted/40 px-4 py-3 text-left transition-colors group"
                  >
                    <div className="rounded-lg bg-cyan-500/10 p-2 shrink-0">
                      <Layers className="h-4 w-4 text-cyan-500" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">{at.asset_type_code.replace(/_/g, " ")}</span>
                        <Badge variant="outline" className="text-[10px] bg-cyan-500/10 text-cyan-500 border-cyan-500/30">
                          {at.asset_count} assets
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground truncate">
                        {at.sample_property_keys.slice(0, 6).join(", ")}{at.sample_property_keys.length > 6 ? ` +${at.sample_property_keys.length - 6} more` : ""}
                      </p>
                    </div>
                    <ChevronRight className="h-4 w-4 text-muted-foreground group-hover:text-foreground transition-colors" />
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Step 3: Preview Samples */}
        {step === "preview" && selectedAssetType?.asset_type_code === "__all__" && (
          /* ── Smart Preview ──────────────────────────────────────── */
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <button onClick={() => { setStep("asset_type"); setSmartPreview(null) }} className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1">
                <ChevronLeft className="h-3 w-3" /> Back
              </button>
              <Badge variant="outline" className="text-xs">
                <Server className="h-3 w-3 mr-1" />{selectedConnector?.name}
              </Badge>
              <Badge className="text-xs bg-green-500/10 text-green-500 border-green-500/30">
                <Sparkles className="h-3 w-3 mr-1" />Smart Dataset
              </Badge>
            </div>

            {smartPreviewLoading ? (
              <div className="flex items-center gap-2 py-8 justify-center text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" /> Analyzing assets for optimal diversity...
              </div>
            ) : smartPreview ? (
              <>
                {/* Summary */}
                <div className="rounded-lg border border-green-500/20 bg-green-500/5 p-3">
                  <p className="text-xs text-green-600 dark:text-green-400 font-medium">{smartPreview.composition_summary}</p>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {Object.entries(smartPreview.by_type).map(([type, count]) => (
                      <button
                        key={type}
                        onClick={() => setSmartTypeFilter(smartTypeFilter === type ? "" : type)}
                        className={`text-[10px] px-2 py-0.5 rounded-md border font-medium transition-colors ${
                          smartTypeFilter === type
                            ? "bg-green-500/10 text-green-500 border-green-500/30"
                            : "bg-muted border-border text-muted-foreground hover:text-foreground"
                        }`}
                      >
                        {type.replace(/_/g, " ")} ({count})
                      </button>
                    ))}
                  </div>
                </div>

                {/* Records */}
                <div className="space-y-1 max-h-[300px] overflow-y-auto pr-1">
                  {smartPreview.records
                    .filter((r) => !smartTypeFilter || r._asset_type === smartTypeFilter)
                    .map((record, i) => (
                    <div key={i} className="rounded border border-border bg-card">
                      <button
                        onClick={() => setSmartPreviewExpanded(smartPreviewExpanded === i ? null : i)}
                        className="flex items-center gap-2 px-3 py-1.5 w-full text-left hover:bg-muted/30 transition-colors"
                      >
                        {smartPreviewExpanded === i
                          ? <ChevronDown className="h-3 w-3 text-muted-foreground shrink-0" />
                          : <ChevronRight className="h-3 w-3 text-muted-foreground shrink-0" />}
                        <Badge variant="outline" className="text-[9px] shrink-0">{String(record._asset_type).replace(/_/g, " ")}</Badge>
                        <span className="text-[11px] font-mono truncate flex-1">{String(record._external_id || "")}</span>
                        <span className="text-[9px] text-muted-foreground shrink-0">{String(record._diversity_group || "").slice(0, 40)}</span>
                      </button>
                      {smartPreviewExpanded === i && (
                        <div className="border-t border-border">
                          <pre className="px-3 py-2 text-[10px] font-mono text-green-400 bg-[#0d1117] whitespace-pre-wrap max-h-48 overflow-y-auto">
                            {JSON.stringify(record, null, 2)}
                          </pre>
                          <div className="px-3 py-1 flex justify-end">
                            <button
                              onClick={() => navigator.clipboard.writeText(JSON.stringify(record, null, 2))}
                              className="text-[10px] text-muted-foreground hover:text-foreground flex items-center gap-1"
                            >
                              <Copy className="h-2.5 w-2.5" /> Copy JSON
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {/* Copy All */}
                <div className="flex justify-end">
                  <button
                    onClick={() => navigator.clipboard.writeText(JSON.stringify(smartPreview.records, null, 2))}
                    className="text-[10px] text-muted-foreground hover:text-foreground flex items-center gap-1"
                  >
                    <Copy className="h-3 w-3" /> Copy all {smartPreview.total} records as JSON
                  </button>
                </div>
              </>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-4">No preview available</p>
            )}
          </div>
        )}

        {step === "preview" && selectedAssetType?.asset_type_code !== "__all__" && (
          /* ── Single-type Preview ─────────────────────────────── */
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <button onClick={() => setStep("asset_type")} className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1">
                <ChevronLeft className="h-3 w-3" /> Back
              </button>
              <Badge variant="outline" className="text-xs">
                <Server className="h-3 w-3 mr-1" />{selectedConnector?.name}
              </Badge>
              <Badge variant="outline" className="text-xs bg-cyan-500/10 text-cyan-500 border-cyan-500/30">
                <Layers className="h-3 w-3 mr-1" />{selectedAssetType?.asset_type_code}
              </Badge>
            </div>

            {samplesLoading ? (
              <div className="flex items-center gap-2 py-8 justify-center text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" /> Loading samples...
              </div>
            ) : (
              <>
                <div className="rounded-lg border border-border bg-muted/30 p-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">{totalCount} total assets</span>
                    <span className="text-xs text-muted-foreground">{propertyKeys.length} properties per asset</span>
                  </div>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {propertyKeys.slice(0, 15).map((k) => (
                      <span key={k} className="text-[10px] px-1.5 py-0.5 rounded bg-muted border border-border font-mono">{k}</span>
                    ))}
                    {propertyKeys.length > 15 && (
                      <span className="text-[10px] px-1.5 py-0.5 text-muted-foreground">+{propertyKeys.length - 15} more</span>
                    )}
                  </div>
                </div>

                {/* Sample records */}
                <div className="space-y-1.5 max-h-64 overflow-y-auto pr-1">
                  {samples.map((s, i) => (
                    <div key={s.asset_id} className="rounded border border-border bg-card">
                      <button
                        onClick={() => setExpandedSample(expandedSample === i ? null : i)}
                        className="flex items-center gap-2 px-3 py-2 w-full text-left hover:bg-muted/30 transition-colors"
                      >
                        <Eye className="h-3 w-3 text-muted-foreground shrink-0" />
                        <span className="text-xs font-mono truncate flex-1">
                          {s.asset_external_id || s.asset_id.slice(0, 12)}
                        </span>
                        <span className="text-[10px] text-muted-foreground">{Object.keys(s.properties).length} props</span>
                      </button>
                      {expandedSample === i && (
                        <div className="border-t border-border px-3 py-2">
                          <pre className="text-[10px] font-mono text-muted-foreground whitespace-pre-wrap max-h-40 overflow-y-auto">
                            {JSON.stringify(s.properties, null, 2)}
                          </pre>
                          <button
                            onClick={() => navigator.clipboard.writeText(JSON.stringify(s.properties, null, 2))}
                            className="mt-1 text-[10px] text-indigo-500 hover:text-indigo-400 flex items-center gap-1"
                          >
                            <Copy className="h-2.5 w-2.5" /> Copy JSON
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {samples.length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No collected assets found for this type. Run a collection first.
                  </p>
                )}
              </>
            )}
          </div>
        )}

        {/* Step 4: Name & Create */}
        {step === "create" && (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <button onClick={() => setStep("preview")} className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1">
                <ChevronLeft className="h-3 w-3" /> Back
              </button>
            </div>

            <div className="rounded-lg border border-green-500/20 bg-green-500/5 p-3 flex items-center gap-3">
              <CheckCircle2 className="h-5 w-5 text-green-500 shrink-0" />
              <div>
                <p className="text-sm font-medium text-green-600 dark:text-green-400">Ready to create</p>
                <p className="text-xs text-muted-foreground">
                  {selectedAssetType?.asset_type_code === "__all__"
                    ? `Smart sampling: diverse, edge-case coverage across ${assetTypes.length} asset types from ${selectedConnector?.name}`
                    : `${totalCount} ${selectedAssetType?.asset_type_code.replace(/_/g, " ")} assets from ${selectedConnector?.name}`}
                </p>
              </div>
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs font-medium">Dataset Name</Label>
              <Input
                className="h-9 text-sm"
                value={datasetName}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setDatasetName(e.target.value)}
                placeholder="e.g. GitHub Repos - March 2026"
                disabled={creating}
              />
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs font-medium text-muted-foreground">Description (optional)</Label>
              <Input
                className="h-9 text-sm"
                value={datasetDescription}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setDatasetDescription(e.target.value)}
                placeholder="What this dataset is for..."
                disabled={creating}
              />
            </div>

            {selectedAssetType?.asset_type_code !== "__all__" && (
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="include-all"
                  checked={includeAllAssets}
                  onChange={(e) => setIncludeAllAssets(e.target.checked)}
                  className="rounded border-border"
                  disabled={creating}
                />
                <label htmlFor="include-all" className="text-xs text-muted-foreground cursor-pointer">
                  Include {samples.length > 0 ? samples.length : totalCount} sample records in the dataset
                </label>
              </div>
            )}
          </div>
        )}

        <DialogFooter className="gap-2 pt-2">
          <Button variant="outline" size="sm" onClick={handleClose} disabled={creating}>
            Cancel
          </Button>
          {step === "preview" && (
            <Button size="sm" onClick={goToCreate} className="gap-1.5" disabled={
              selectedAssetType?.asset_type_code === "__all__"
                ? !smartPreview || smartPreview.total === 0
                : samples.length === 0 && totalCount === 0
            }>
              <FileJson className="h-3.5 w-3.5" />
              Continue to Create
            </Button>
          )}
          {step === "create" && (
            <Button
              size="sm"
              onClick={handleCreate}
              disabled={creating || !datasetName.trim()}
              className="gap-1.5 bg-indigo-600 hover:bg-indigo-700 text-white border-0"
            >
              {creating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Database className="h-3.5 w-3.5" />}
              Create Dataset
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
