"use client"

import { useEffect, useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Button,
  Input,
  Label,
  Separator,
  Badge,
} from "@kcontrol/ui"
import {
  Plus,
  Pencil,
  AlertTriangle,
  Loader2,
} from "lucide-react"
import type {
  FrameworkResponse,
  DimensionResponse,
  CreateFrameworkRequest,
  UpdateFrameworkRequest,
} from "@/lib/types/grc"

const PUBLISHER_TYPES = ["official", "partner", "community", "custom"] as const

export function CreateFrameworkDialog({
  open,
  types,
  categories,
  onCreate,
  onClose,
}: {
  open: boolean
  types: DimensionResponse[]
  categories: DimensionResponse[]
  onCreate: (p: CreateFrameworkRequest) => Promise<void>
  onClose: () => void
}) {
  const [code, setCode] = useState("")
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [typeCode, setTypeCode] = useState("")
  const [categoryCode, setCategoryCode] = useState("")
  const [publisherType, setPublisherType] = useState<string>("official")
  const [publisherName, setPublisherName] = useState("")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      setCode(""); setName(""); setDescription("")
      setTypeCode(types[0]?.code ?? ""); setCategoryCode(categories[0]?.code ?? "")
      setPublisherType("official"); setPublisherName("")
      setSaving(false); setError(null)
    }
  }, [open, types, categories])

  async function create() {
    if (!code.trim() || !name.trim()) { setError("Code and Name are required."); return }
    if (!typeCode) { setError("Framework type is required."); return }
    if (!categoryCode) { setError("Category is required."); return }
    setSaving(true); setError(null)
    try {
      await onCreate({
        framework_code: code.trim(),
        name: name.trim(),
        description: description.trim(),
        framework_type_code: typeCode,
        framework_category_code: categoryCode,
        publisher_type: publisherType,
        publisher_name: publisherName.trim() || undefined,
      })
      onClose()
    } catch (e) { setError(e instanceof Error ? e.message : "Failed to create"); setSaving(false) }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-primary/10 p-2.5"><Plus className="h-4 w-4 text-primary" /></div>
            <div>
              <DialogTitle>New Framework</DialogTitle>
              <DialogDescription>Create a new compliance framework in the library.</DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs">Code <span className="text-muted-foreground">(unique identifier)</span></Label>
              <Input value={code} onChange={(e) => setCode(e.target.value)} placeholder="SOC2" className="h-9 text-sm font-mono" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Name</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="SOC 2 Type II" className="h-9 text-sm" />
            </div>
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Description</Label>
            <Input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Framework description..." className="h-9 text-sm" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs">Type</Label>
              <select className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={typeCode} onChange={(e) => setTypeCode(e.target.value)}>
                {types.map((t) => <option key={t.code} value={t.code}>{t.name}</option>)}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Category</Label>
              <select className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={categoryCode} onChange={(e) => setCategoryCode(e.target.value)}>
                {categories.map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs">Publisher Type</Label>
              <select className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={publisherType} onChange={(e) => setPublisherType(e.target.value)}>
                {PUBLISHER_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Publisher Name</Label>
              <Input value={publisherName} onChange={(e) => setPublisherName(e.target.value)} placeholder="AICPA" className="h-9 text-sm" />
            </div>
          </div>
        </div>
        {error && <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500 mt-2">{error}</p>}
        <DialogFooter className="mt-3 gap-2 sm:gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={saving}>Cancel</Button>
          <Button size="sm" onClick={create} disabled={saving}>
            {saving ? <Loader2 className="h-3 w-3 animate-spin mr-1.5" /> : "Create Framework"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export function EditFrameworkDialog({
  framework,
  categories,
  onSave,
  onClose,
}: {
  framework: FrameworkResponse | null
  categories: DimensionResponse[]
  onSave: (id: string, payload: UpdateFrameworkRequest) => Promise<void>
  onClose: () => void
}) {
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [categoryCode, setCategoryCode] = useState("")
  const [marketplaceVisible, setMarketplaceVisible] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (framework) {
      setName(framework.name); setDescription(framework.description ?? "")
      setCategoryCode(framework.framework_category_code)
      setMarketplaceVisible(framework.is_marketplace_visible)
      setSaving(false); setError(null)
    }
  }, [framework])

  if (!framework) return null

  async function save() {
    if (!name.trim()) { setError("Name is required."); return }
    setSaving(true); setError(null)
    try {
      await onSave(framework!.id, {
        name: name.trim(),
        description: description.trim(),
        framework_category_code: categoryCode,
        is_marketplace_visible: marketplaceVisible,
      })
      onClose()
    } catch (e) { setError(e instanceof Error ? e.message : "Failed to save"); setSaving(false) }
  }

  return (
    <Dialog open onOpenChange={(o) => { if (!o) onClose() }}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-primary/10 p-2.5"><Pencil className="h-4 w-4 text-primary" /></div>
            <div>
              <DialogTitle>Edit Framework</DialogTitle>
              <DialogDescription><code className="text-xs font-mono text-foreground/60">{framework.framework_code}</code></DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label className="text-xs">Name</Label>
            <Input value={name} onChange={(e) => setName(e.target.value)} className="h-9 text-sm" />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Description</Label>
            <Input value={description} onChange={(e) => setDescription(e.target.value)} className="h-9 text-sm" />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Category</Label>
            <select className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={categoryCode} onChange={(e) => setCategoryCode(e.target.value)}>
              {categories.map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
            </select>
          </div>
          <div className="flex items-center gap-3">
            <input type="checkbox" id="marketplace" checked={marketplaceVisible} onChange={(e) => setMarketplaceVisible(e.target.checked)}
              className="h-4 w-4 rounded border-input" />
            <Label htmlFor="marketplace" className="text-xs cursor-pointer">Visible in marketplace</Label>
          </div>
        </div>
        {error && <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500 mt-2">{error}</p>}
        <DialogFooter className="mt-3 gap-2 sm:gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={saving}>Cancel</Button>
          <Button size="sm" onClick={save} disabled={saving}>
            {saving ? <Loader2 className="h-3 w-3 animate-spin mr-1.5" /> : "Save Changes"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export function DeleteFrameworkDialog({
  framework,
  onConfirm,
  onClose,
}: {
  framework: FrameworkResponse | null
  onConfirm: (id: string) => Promise<void>
  onClose: () => void
}) {
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!framework) return null

  async function confirm() {
    setDeleting(true); setError(null)
    try {
      await onConfirm(framework!.id)
      onClose()
    } catch (e) { setError(e instanceof Error ? e.message : "Failed to delete"); setDeleting(false) }
  }

  return (
    <Dialog open onOpenChange={(o) => { if (!o) onClose() }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-red-500/10 p-2.5"><AlertTriangle className="h-4 w-4 text-red-500" /></div>
            <div>
              <DialogTitle>Delete Framework</DialogTitle>
              <DialogDescription>This will soft-delete the framework. It can be restored by an administrator.</DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />
        <p className="text-sm">
          Are you sure you want to delete <strong>{framework.name}</strong> (<code className="text-xs font-mono">{framework.framework_code}</code>)?
          All associated versions, requirements, and controls will also be deactivated.
        </p>
        {error && <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500 mt-2">{error}</p>}
        <DialogFooter className="mt-3 gap-2 sm:gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={deleting}>Cancel</Button>
          <Button variant="destructive" size="sm" onClick={confirm} disabled={deleting}>
            {deleting ? <Loader2 className="h-3 w-3 animate-spin mr-1.5" /> : "Delete Framework"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
