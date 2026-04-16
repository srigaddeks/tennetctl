"use client"

import { useEffect, useState } from "react"
import {
  Button,
  Input,
  Badge,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@kcontrol/ui"
import { Search, Github, Cloud, Database, Server, ExternalLink, Check, AlertTriangle } from "lucide-react"
import { listConnectors } from "@/lib/api/sandbox"
import type { ConnectorInstanceResponse } from "@/lib/api/sandbox"

// ── Helpers ───────────────────────────────────────────────────────────────────

function ConnectorIcon({ typeCode, className = "h-4 w-4" }: { typeCode: string; className?: string }) {
  if (typeCode.startsWith("github")) return <Github className={className} />
  if (typeCode.startsWith("azure")) return <Cloud className={className} />
  if (typeCode.startsWith("aws")) return <Cloud className={className} />
  if (typeCode.startsWith("postgres") || typeCode.startsWith("mysql")) return <Database className={className} />
  return <Server className={className} />
}

function connectorTypePill(typeCode: string): string {
  if (typeCode.startsWith("github")) return "bg-gray-900 text-white"
  if (typeCode.startsWith("azure")) return "bg-blue-600 text-white"
  if (typeCode.startsWith("aws")) return "bg-orange-500 text-white"
  return "bg-slate-100 text-slate-700"
}

// ── Props ─────────────────────────────────────────────────────────────────────

interface AssetSelectorDialogProps {
  open: boolean
  orgId: string
  currentAssetId?: string | null
  onSelect: (connectorId: string) => void
  onClose: () => void
}

// ── Component ─────────────────────────────────────────────────────────────────

export function AssetSelectorDialog({
  open,
  orgId,
  currentAssetId,
  onSelect,
  onClose,
}: AssetSelectorDialogProps) {
  const [connectors, setConnectors] = useState<ConnectorInstanceResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [selected, setSelected] = useState<string | null>(currentAssetId ?? null)

  useEffect(() => {
    if (!open || !orgId) return
    setLoading(true)
    setError(null)
    listConnectors({ org_id: orgId })
      .then((res) => setConnectors(res.items))
      .catch((e) => setError(e.message || "Failed to load connectors"))
      .finally(() => setLoading(false))
  }, [open, orgId])

  // Reset selection when dialog opens
  useEffect(() => {
    if (open) setSelected(currentAssetId ?? null)
  }, [open, currentAssetId])

  const filtered = connectors.filter((c) => {
    if (!search) return true
    const q = search.toLowerCase()
    return (
      (c.name || "").toLowerCase().includes(q) ||
      c.connector_type_code.toLowerCase().includes(q) ||
      c.instance_code.toLowerCase().includes(q)
    )
  })

  function handleConfirm() {
    if (selected) onSelect(selected)
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Link Asset</DialogTitle>
          <DialogDescription>
            Select a connector to link as the asset for this control test. The test will run against this
            connector&apos;s data.
          </DialogDescription>
        </DialogHeader>

        {/* Search */}
        <div className="relative mt-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search connectors..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>

        {/* Connector list */}
        <div className="max-h-72 overflow-y-auto space-y-1.5 mt-2 pr-1">
          {loading && (
            <div className="text-sm text-muted-foreground text-center py-8">Loading connectors...</div>
          )}
          {error && (
            <div className="flex items-center gap-2 text-sm text-destructive py-4 px-3 bg-destructive/5 rounded-lg">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              {error}
            </div>
          )}
          {!loading && !error && filtered.length === 0 && (
            <div className="text-sm text-muted-foreground text-center py-8">
              {connectors.length === 0 ? (
                <span>
                  No connectors found.{" "}
                  <a
                    href="/sandbox/connectors"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary inline-flex items-center gap-1 hover:underline"
                  >
                    Create one in Sandbox <ExternalLink className="h-3 w-3" />
                  </a>
                </span>
              ) : (
                "No connectors match your search."
              )}
            </div>
          )}
          {filtered.map((connector) => {
            const isSelected = selected === connector.id
            return (
              <button
                key={connector.id}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg border text-left transition-colors ${
                  isSelected
                    ? "border-primary/60 bg-primary/5"
                    : "border-border hover:border-primary/30 hover:bg-muted/30"
                }`}
                onClick={() => setSelected(connector.id)}
              >
                <div
                  className={`flex items-center justify-center h-8 w-8 rounded-md shrink-0 ${connectorTypePill(connector.connector_type_code)}`}
                >
                  <ConnectorIcon typeCode={connector.connector_type_code} className="h-4 w-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium truncate">
                      {connector.name || connector.instance_code}
                    </span>
                    {connector.is_draft && (
                      <Badge variant="outline" className="text-[10px] px-1.5 py-0 shrink-0">
                        draft
                      </Badge>
                    )}
                  </div>
                  <p className="text-[11px] text-muted-foreground font-mono truncate">
                    {connector.connector_type_code}
                    {connector.name ? ` · ${connector.instance_code}` : ""}
                  </p>
                </div>
                {isSelected && <Check className="h-4 w-4 text-primary shrink-0" />}
              </button>
            )
          })}
        </div>

        {connectors.length > 0 && (
          <p className="text-[11px] text-muted-foreground text-right -mt-1">
            {connectors.length} connector{connectors.length !== 1 ? "s" : ""} available.{" "}
            <a
              href="/sandbox/connectors"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary inline-flex items-center gap-0.5 hover:underline"
            >
              Add new <ExternalLink className="h-3 w-3" />
            </a>
          </p>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleConfirm} disabled={!selected || selected === currentAssetId}>
            {selected && selected !== currentAssetId ? "Link Asset" : "No Change"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
