"use client"

import { useEffect, useState, useCallback } from "react"
import {
  Button,
  Input,
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
  Download,
  Loader2,
  Search,
  Globe,
  Database,
  Cloud,
  Server,
  Github,
  Star,
  Tag,
  Plug,
  FileJson,
} from "lucide-react"
import {
  listGlobalDatasets,
  pullGlobalDataset,
} from "@/lib/api/sandbox"
import type { GlobalDatasetResponse } from "@/lib/api/sandbox"

const TYPE_ICONS: Record<string, typeof Cloud> = {
  github: Github,
  aws: Cloud,
  azure: Cloud,
  azure_storage: Cloud,
  gcp: Cloud,
  postgres: Database,
  postgresql: Database,
  mysql: Database,
  kubernetes: Server,
  k8s: Server,
}

function getTypeIcon(code: string) {
  return TYPE_ICONS[code?.toLowerCase()] || Plug
}

export function PullGlobalDatasetDialog({
  open,
  orgId,
  workspaceId,
  onPulled,
  onClose,
}: {
  open: boolean
  orgId: string
  workspaceId?: string
  onPulled: (datasetCode: string) => void
  onClose: () => void
}) {
  const [datasets, setDatasets] = useState<GlobalDatasetResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState("")
  const [filterType, setFilterType] = useState("")
  const [error, setError] = useState<string | null>(null)

  const [selected, setSelected] = useState<GlobalDatasetResponse | null>(null)
  const [pulling, setPulling] = useState(false)
  const [pullError, setPullError] = useState<string | null>(null)

  const loadDatasets = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await listGlobalDatasets({
        search: search.trim() || undefined,
        connector_type_code: filterType || undefined,
        publish_status: "published",
        limit: 100,
      })
      setDatasets(res.items)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load library")
    } finally {
      setLoading(false)
    }
  }, [search, filterType])

  useEffect(() => {
    if (open) {
      setSelected(null)
      setPullError(null)
      loadDatasets()
    }
  }, [open, loadDatasets])

  async function handlePull() {
    if (!selected) return
    setPulling(true)
    setPullError(null)
    try {
      const result = await pullGlobalDataset(selected.id, {
        org_id: orgId,
        workspace_id: workspaceId,
      })
      onPulled(result.dataset_code)
      onClose()
    } catch (e) {
      setPullError(e instanceof Error ? e.message : "Failed to pull dataset")
    } finally {
      setPulling(false)
    }
  }

  // Get unique connector types for filter
  const connectorTypes = [...new Set(datasets.map((d) => d.connector_type_code))].sort()

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-blue-500/10 p-2.5">
              <Globe className="h-4 w-4 text-blue-500" />
            </div>
            <div>
              <DialogTitle>Global Dataset Library</DialogTitle>
              <DialogDescription>
                Browse and pull pre-built datasets into your workspace.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {/* Search + filter bar */}
        <div className="flex items-center gap-2 mt-2">
          <div className="relative flex-1">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground pointer-events-none" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search datasets..."
              className="pl-8 h-8 text-sm"
            />
          </div>
          <select
            className="h-8 rounded-md border border-input bg-background px-2.5 text-xs"
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
          >
            <option value="">All Connector Types</option>
            {connectorTypes.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>

        <Separator className="my-2" />

        {/* Dataset list */}
        <div className="flex-1 overflow-y-auto min-h-0 space-y-2 pr-1">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : error ? (
            <div className="text-center py-8">
              <p className="text-sm text-red-500">{error}</p>
              <Button variant="outline" size="sm" onClick={loadDatasets} className="mt-2">Retry</Button>
            </div>
          ) : datasets.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <FileJson className="h-8 w-8 text-muted-foreground/30 mb-3" />
              <p className="text-sm text-muted-foreground">No datasets in the global library yet.</p>
              <p className="text-xs text-muted-foreground mt-1">Publish datasets from sandbox to populate the library.</p>
            </div>
          ) : (
            datasets.map((d) => {
              const TypeIcon = getTypeIcon(d.connector_type_code)
              const isSelected = selected?.id === d.id
              return (
                <button
                  key={d.id}
                  onClick={() => setSelected(isSelected ? null : d)}
                  className={`w-full text-left rounded-lg border p-3 transition-all ${
                    isSelected
                      ? "border-primary bg-primary/5 ring-1 ring-primary/20"
                      : "border-border/50 hover:border-primary/30 hover:bg-muted/30"
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className="h-9 w-9 rounded-lg bg-muted/60 flex items-center justify-center shrink-0 mt-0.5">
                      <TypeIcon className="h-4.5 w-4.5 text-muted-foreground" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h4 className="text-sm font-medium truncate">{d.name || d.global_code}</h4>
                        {d.is_featured && <Star className="h-3 w-3 text-amber-500 shrink-0" />}
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="secondary" className="text-[9px] font-mono">{d.connector_type_code}</Badge>
                        {d.category && <Badge variant="outline" className="text-[9px]">{d.category}</Badge>}
                        <span className="text-[10px] text-muted-foreground">v{d.version_number}</span>
                        <span className="text-[10px] text-muted-foreground">{d.record_count} samples</span>
                        <span className="text-[10px] text-muted-foreground">{d.download_count} pulls</span>
                      </div>
                      {d.description && (
                        <p className="text-xs text-muted-foreground mt-1.5 line-clamp-2">{d.description}</p>
                      )}
                      {d.tags && (
                        <div className="flex items-center gap-1 mt-1.5">
                          <Tag className="h-2.5 w-2.5 text-muted-foreground/50" />
                          <span className="text-[10px] text-muted-foreground">{d.tags}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Expanded preview when selected */}
                  {isSelected && d.sample_payload && d.sample_payload.length > 0 && (
                    <div className="mt-3 rounded-md bg-muted/50 border border-border/30 p-2 max-h-32 overflow-y-auto">
                      <p className="text-[10px] font-medium text-muted-foreground mb-1 uppercase tracking-wide">Sample Record</p>
                      <pre className="text-[10px] text-foreground/80 font-mono whitespace-pre-wrap">
                        {JSON.stringify(d.sample_payload[0], null, 2)}
                      </pre>
                    </div>
                  )}
                </button>
              )
            })
          )}
        </div>

        {pullError && (
          <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500">{pullError}</p>
        )}

        <DialogFooter className="mt-3 gap-2 sm:gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={pulling}>Cancel</Button>
          <Button
            size="sm"
            onClick={handlePull}
            disabled={!selected || pulling}
            className="gap-1.5"
          >
            {pulling ? (
              <>
                <Loader2 className="h-3 w-3 animate-spin" />
                Pulling...
              </>
            ) : (
              <>
                <Download className="h-3 w-3" />
                Pull to Workspace
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
