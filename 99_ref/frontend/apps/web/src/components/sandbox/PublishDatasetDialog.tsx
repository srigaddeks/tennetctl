"use client"

import { useEffect, useState } from "react"
import {
  Button,
  Input,
  Label,
  Separator,
  Badge,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@kcontrol/ui"
import { Globe, Loader2, Tag, FileJson } from "lucide-react"
import { publishGlobalDataset } from "@/lib/api/sandbox"
import type { DatasetResponse } from "@/lib/api/sandbox"

function slugify(val: string): string {
  return val.toLowerCase().replace(/[^a-z0-9-_]/g, "_").replace(/__+/g, "_").replace(/^_|_$/g, "")
}

const CATEGORIES = [
  { value: "access_control", label: "Access Control" },
  { value: "encryption", label: "Encryption" },
  { value: "network", label: "Network Security" },
  { value: "identity", label: "Identity & Auth" },
  { value: "compliance", label: "Compliance" },
  { value: "logging", label: "Logging & Monitoring" },
  { value: "configuration", label: "Configuration" },
  { value: "vulnerability", label: "Vulnerability Management" },
  { value: "data_protection", label: "Data Protection" },
  { value: "custom", label: "Custom" },
]

export function PublishDatasetDialog({
  dataset,
  orgId,
  onPublished,
  onClose,
}: {
  dataset: DatasetResponse | null
  orgId: string
  onPublished: () => void
  onClose: () => void
}) {
  const [globalCode, setGlobalCode] = useState("")
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [category, setCategory] = useState("")
  const [tags, setTags] = useState("")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (dataset) {
      const displayName = dataset.name || dataset.dataset_code
      setName(displayName)
      setGlobalCode(slugify(displayName))
      setDescription(dataset.description || "")
      setCategory("")
      setTags("")
      setSaving(false)
      setError(null)
    }
  }, [dataset])

  if (!dataset) return null

  async function handlePublish() {
    if (!globalCode.trim() || !name.trim()) {
      setError("Code and name are required")
      return
    }
    setSaving(true)
    setError(null)
    try {
      const props: Record<string, string> = { name: name.trim() }
      if (description.trim()) props.description = description.trim()
      if (category) props.category = category
      if (tags.trim()) props.tags = tags.trim()

      await publishGlobalDataset(orgId, {
        source_dataset_id: dataset!.id,
        global_code: globalCode.trim(),
        properties: props,
      })
      onPublished()
      onClose()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to publish")
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open onOpenChange={(o) => { if (!o) onClose() }}>
      <DialogContent className="sm:max-w-lg max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-emerald-500/10 p-2.5">
              <Globe className="h-4 w-4 text-emerald-500" />
            </div>
            <div>
              <DialogTitle>Publish to Global Library</DialogTitle>
              <DialogDescription>
                Make this dataset available to all organizations and workspaces.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />

        {/* Source info */}
        <div className="rounded-lg border border-border/50 bg-muted/30 p-3 space-y-1.5">
          <div className="flex items-center gap-2">
            <FileJson className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Source Dataset</span>
          </div>
          <p className="text-sm font-medium">{dataset.name || dataset.dataset_code}</p>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Badge variant="secondary" className="text-[9px]">{dataset.dataset_source_code}</Badge>
            <span>{dataset.row_count ?? 0} records</span>
            <span>v{dataset.version_number}</span>
          </div>
        </div>

        <div className="space-y-4 mt-2">
          {/* Global code */}
          <div className="space-y-1.5">
            <Label className="text-xs font-medium">
              Global Code <span className="text-red-500">*</span>
            </Label>
            <Input
              value={globalCode}
              onChange={(e) => setGlobalCode(slugify(e.target.value))}
              placeholder="e.g. github_branch_protection"
              className="h-9 text-sm font-mono"
            />
            <p className="text-[10px] text-muted-foreground">
              Unique identifier. Lowercase, underscores allowed. Used across all versions.
            </p>
          </div>

          {/* Name */}
          <div className="space-y-1.5">
            <Label className="text-xs font-medium">
              Display Name <span className="text-red-500">*</span>
            </Label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="GitHub Branch Protection Rules"
              className="h-9 text-sm"
            />
          </div>

          {/* Description */}
          <div className="space-y-1.5">
            <Label className="text-xs">Description</Label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What this dataset contains and how to use it..."
              className="w-full min-h-[80px] rounded-md border border-input bg-background px-3 py-2 text-sm resize-y focus:outline-none focus:ring-2 focus:ring-primary/30"
            />
          </div>

          {/* Category */}
          <div className="space-y-1.5">
            <Label className="text-xs">Category</Label>
            <select
              className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              <option value="">Select category...</option>
              {CATEGORIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
            </select>
          </div>

          {/* Tags */}
          <div className="space-y-1.5">
            <Label className="text-xs flex items-center gap-1.5">
              <Tag className="h-3 w-3" />
              Tags
            </Label>
            <Input
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="security, github, branch-protection"
              className="h-9 text-sm"
            />
            <p className="text-[10px] text-muted-foreground">Comma-separated. Helps with search and discovery.</p>
          </div>
        </div>

        {error && (
          <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2.5 text-xs text-red-500 mt-2">{error}</p>
        )}

        <DialogFooter className="mt-3 gap-2 sm:gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={saving}>Cancel</Button>
          <Button
            size="sm"
            onClick={handlePublish}
            disabled={saving || !globalCode.trim() || !name.trim()}
            className="gap-1.5 bg-emerald-600 hover:bg-emerald-700"
          >
            {saving ? (
              <>
                <Loader2 className="h-3 w-3 animate-spin" />
                Publishing...
              </>
            ) : (
              <>
                <Globe className="h-3 w-3" />
                Publish to Library
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
