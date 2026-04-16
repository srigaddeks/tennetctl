"use client"

import { useEffect, useState, useCallback } from "react"
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
  Library,
  Search,
  Plus,
  ChevronDown,
  ChevronRight,
  Upload,
  Copy,
  Trash2,
  AlertTriangle,
  FileCheck,
  ArrowUpFromLine,
  GripVertical,
  X,
  RefreshCw,
  Sparkles,
  BookOpen,
  Filter,
} from "lucide-react"
import {
  listLibraries,
  listLibraryTypes,
  createLibrary,
  publishLibrary,
  cloneLibrary,
  deleteLibrary,
  listLibraryPolicies,
  addPolicyToLibrary,
  removePolicyFromLibrary,
  promoteLibrary,
} from "@/lib/api/sandbox"
import type {
  LibraryResponse,
  LibraryPolicyResponse,
  DimensionResponse,
} from "@/lib/api/sandbox"
import { useSandboxOrgWorkspace } from "@/lib/context/SandboxOrgWorkspaceContext"
import { AssetSelectorDialog } from "@/components/grc/AssetSelectorDialog"

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

const TYPE_STYLES: Record<string, { bg: string; text: string; border: string }> = {
  asset_security:  { bg: "bg-blue-500/10",   text: "text-blue-500",   border: "border-blue-500/30" },
  compliance:      { bg: "bg-green-500/10",  text: "text-green-500",  border: "border-green-500/30" },
  operational:     { bg: "bg-amber-500/10",  text: "text-amber-500",  border: "border-amber-500/30" },
  custom:          { bg: "bg-purple-500/10", text: "text-purple-500", border: "border-purple-500/30" },
}

function typeStyle(code: string) {
  return TYPE_STYLES[code] ?? { bg: "bg-muted", text: "text-muted-foreground", border: "border-border" }
}

function fmtDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
}

const RECOMMENDED_LIBRARIES = [
  { code: "aws_cis_benchmark", name: "AWS CIS Benchmark", type: "compliance", description: "Center for Internet Security AWS Foundations Benchmark controls for cloud-native compliance." },
  { code: "azure_security_baseline", name: "Azure Security Baseline", type: "asset_security", description: "Microsoft Azure security configuration baseline control tests for identity, networking, and data." },
  { code: "k8s_pod_security", name: "Kubernetes Pod Security", type: "operational", description: "Runtime pod security standards for container workload protection and admission control." },
]

// ─────────────────────────────────────────────────────────────────────────────
// Create Library Dialog
// ─────────────────────────────────────────────────────────────────────────────

function CreateLibraryDialog({
  open, types, onCreate, onClose,
}: {
  open: boolean
  types: DimensionResponse[]
  onCreate: (p: { library_code: string; library_type_code: string; properties?: Record<string, string> }) => Promise<void>
  onClose: () => void
}) {
  const [code, setCode] = useState("")
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [typeCode, setTypeCode] = useState("")
  const [targetAsset, setTargetAsset] = useState("")
  const [frameworks, setFrameworks] = useState("")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      setCode(""); setName(""); setDescription("")
      setTypeCode(types[0]?.code ?? ""); setTargetAsset(""); setFrameworks("")
      setSaving(false); setError(null)
    }
  }, [open, types])

  function slugify(s: string) {
    return s.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "")
  }

  function handleNameChange(v: string) {
    setName(v)
    if (!code || code === slugify(name)) {
      setCode(slugify(v))
    }
  }

  async function create() {
    if (!code.trim() || !name.trim()) { setError("Code and Name are required."); return }
    if (!typeCode) { setError("Library type is required."); return }
    setSaving(true); setError(null)
    try {
      const props: Record<string, string> = { name: name.trim() }
      if (description.trim()) props.description = description.trim()
      if (targetAsset.trim()) props.target_asset_type = targetAsset.trim()
      if (frameworks.trim()) props.compliance_frameworks = frameworks.trim()
      await onCreate({ library_code: code.trim(), library_type_code: typeCode, properties: props })
      onClose()
    } catch (e) { setError(e instanceof Error ? e.message : "Failed to create"); setSaving(false) }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-teal-500/10 p-2.5"><Plus className="h-4 w-4 text-teal-500" /></div>
            <div>
              <DialogTitle>New Library</DialogTitle>
              <DialogDescription>Create a new control test library to group related control tests.</DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs">Name</Label>
              <Input value={name} onChange={(e) => handleNameChange(e.target.value)} placeholder="AWS CIS Benchmark" className="h-9 text-sm" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Code <span className="text-muted-foreground">(auto-slug)</span></Label>
              <Input value={code} onChange={(e) => setCode(e.target.value)} placeholder="aws_cis_benchmark" className="h-9 text-sm font-mono" />
            </div>
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Description</Label>
            <Input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Library description..." className="h-9 text-sm" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs">Library Type</Label>
              <select className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={typeCode} onChange={(e) => setTypeCode(e.target.value)}>
                {types.map((t) => <option key={t.code} value={t.code}>{t.name}</option>)}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Target Asset Type</Label>
              <Input value={targetAsset} onChange={(e) => setTargetAsset(e.target.value)} placeholder="aws_account, k8s_cluster..." className="h-9 text-sm" />
            </div>
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Compliance Frameworks <span className="text-muted-foreground">(comma-separated tags)</span></Label>
            <Input value={frameworks} onChange={(e) => setFrameworks(e.target.value)} placeholder="SOC2, ISO27001, NIST" className="h-9 text-sm" />
          </div>
        </div>
        {error && <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500 mt-2">{error}</p>}
        <DialogFooter className="mt-3 gap-2 sm:gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={saving}>Cancel</Button>
          <Button size="sm" onClick={create} disabled={saving}>
            {saving ? <span className="flex items-center gap-1.5"><span className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />Creating...</span> : "Create Library"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Delete Library Dialog
// ─────────────────────────────────────────────────────────────────────────────

function DeleteLibraryDialog({
  library, onConfirm, onClose,
}: {
  library: LibraryResponse | null
  onConfirm: (id: string) => Promise<void>
  onClose: () => void
}) {
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!library) return null

  async function confirm() {
    setDeleting(true); setError(null)
    try {
      await onConfirm(library!.id)
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
              <DialogTitle>Delete Library</DialogTitle>
              <DialogDescription>This will deactivate the library and remove all control test associations.</DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />
        <p className="text-sm">
          Are you sure you want to delete <strong>{library.name || library.library_code}</strong>{" "}
          (<code className="text-xs font-mono">{library.library_code}</code>)?
        </p>
        {error && <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500 mt-2">{error}</p>}
        <DialogFooter className="mt-3 gap-2 sm:gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={deleting}>Cancel</Button>
          <Button variant="destructive" size="sm" onClick={confirm} disabled={deleting}>
            {deleting ? <span className="flex items-center gap-1.5"><span className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />Deleting...</span> : "Delete Library"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Add Control Test Dialog
// ─────────────────────────────────────────────────────────────────────────────

function AddPolicyDialog({
  open, libraryId, onAdd, onClose,
}: {
  open: boolean
  libraryId: string
  onAdd: (libraryId: string, policyId: string, sortOrder: number) => Promise<void>
  onClose: () => void
}) {
  const [policyId, setPolicyId] = useState("")
  const [sortOrder, setSortOrder] = useState("0")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) { setPolicyId(""); setSortOrder("0"); setSaving(false); setError(null) }
  }, [open])

  async function add() {
    if (!policyId.trim()) { setError("Control test ID is required."); return }
    setSaving(true); setError(null)
    try {
      await onAdd(libraryId, policyId.trim(), parseInt(sortOrder, 10) || 0)
      onClose()
    } catch (e) { setError(e instanceof Error ? e.message : "Failed to add control test"); setSaving(false) }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>Add Control Test</DialogTitle>
          <DialogDescription>Add an existing control test to this library.</DialogDescription>
        </DialogHeader>
        <Separator className="my-2" />
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label className="text-xs">Control Test ID</Label>
            <Input value={policyId} onChange={(e) => setPolicyId(e.target.value)} placeholder="Enter control test UUID" className="h-9 text-sm font-mono" />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Sort Order</Label>
            <Input type="number" value={sortOrder} onChange={(e) => setSortOrder(e.target.value)} className="h-9 text-sm" />
          </div>
        </div>
        {error && <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500 mt-2">{error}</p>}
        <DialogFooter className="mt-3 gap-2 sm:gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={saving}>Cancel</Button>
          <Button size="sm" onClick={add} disabled={saving}>
            {saving ? "Adding..." : "Add Control Test"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Library Detail (expandable policies list)
// ─────────────────────────────────────────────────────────────────────────────

function LibraryPoliciesPanel({
  libraryId, isPublished, orgId, onReload,
}: {
  libraryId: string
  isPublished: boolean
  orgId: string
  onReload: () => void
}) {
  const [policies, setPolicies] = useState<LibraryPolicyResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [showAddPolicy, setShowAddPolicy] = useState(false)
  const [removing, setRemoving] = useState<string | null>(null)

  const loadPolicies = useCallback(async () => {
    setLoading(true)
    try {
      const res = await listLibraryPolicies(libraryId)
      setPolicies(res)
    } catch { /* graceful */ }
    finally { setLoading(false) }
  }, [libraryId])

  useEffect(() => { loadPolicies() }, [loadPolicies])

  async function handleAdd(_libId: string, policyId: string, sortOrder: number) {
    await addPolicyToLibrary(orgId, libraryId, { policy_id: policyId, sort_order: sortOrder })
    await loadPolicies()
    onReload()
  }

  async function handleRemove(policyId: string) {
    setRemoving(policyId)
    try {
      await removePolicyFromLibrary(orgId, libraryId, policyId)
      await loadPolicies()
      onReload()
    } catch { /* graceful */ }
    finally { setRemoving(null) }
  }

  return (
    <div className="space-y-2 pt-2">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Included Control Tests</p>
        {!isPublished && (
          <Button size="sm" variant="ghost" className="h-6 text-xs gap-1" onClick={() => setShowAddPolicy(true)}>
            <Plus className="h-3 w-3" /> Add Control Test
          </Button>
        )}
      </div>
      {loading ? (
        <div className="space-y-1.5">
          {[1, 2, 3].map((i) => <div key={i} className="h-8 rounded bg-muted animate-pulse" />)}
        </div>
      ) : policies.length === 0 ? (
        <div className="rounded-lg border border-dashed border-border bg-muted/10 px-4 py-6 text-center">
          <FileCheck className="h-5 w-5 text-muted-foreground mx-auto mb-2" />
          <p className="text-xs text-muted-foreground">No control tests yet. Add control tests to build this library.</p>
        </div>
      ) : (
        <div className="space-y-1">
          {policies.sort((a, b) => a.sort_order - b.sort_order).map((p) => (
            <div key={p.policy_id} className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-muted/30 text-xs group">
              <GripVertical className="h-3 w-3 text-muted-foreground/40 shrink-0" />
              <span className="text-muted-foreground w-5 text-right shrink-0">{p.sort_order}</span>
              <FileCheck className="h-3 w-3 text-green-500 shrink-0" />
              <span className="font-medium truncate">{p.policy_name || p.policy_code}</span>
              <code className="text-[10px] font-mono text-muted-foreground">{p.policy_code}</code>
              {!isPublished && (
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-5 w-5 p-0 ml-auto opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-red-500"
                  onClick={() => handleRemove(p.policy_id)}
                  disabled={removing === p.policy_id}
                >
                  <X className="h-3 w-3" />
                </Button>
              )}
            </div>
          ))}
        </div>
      )}
      <AddPolicyDialog
        open={showAddPolicy}
        libraryId={libraryId}
        onAdd={handleAdd}
        onClose={() => setShowAddPolicy(false)}
      />
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Library Row
// ─────────────────────────────────────────────────────────────────────────────

function libraryBorderCls(lib: LibraryResponse) {
  if (!lib.is_active) return "border-l-slate-400"
  if (lib.is_published) return "border-l-green-500"
  return "border-l-amber-500"
}

function LibraryRow({
  lib, orgId, onPublish, onClone, onPromote, onDelete, onReload,
}: {
  lib: LibraryResponse
  orgId: string
  onPublish: (id: string) => Promise<void>
  onClone: (id: string) => Promise<void>
  onPromote: (id: string) => Promise<void>
  onDelete: (lib: LibraryResponse) => void
  onReload: () => void
}) {
  const [expanded, setExpanded] = useState(false)
  const [publishing, setPublishing] = useState(false)
  const [cloning, setCloning] = useState(false)
  const [promoting, setPromoting] = useState(false)

  const ts = typeStyle(lib.library_type_code)
  const borderCls = libraryBorderCls(lib)

  async function handlePublish() {
    setPublishing(true)
    try { await onPublish(lib.id) } catch { /* */ }
    finally { setPublishing(false) }
  }

  async function handleClone() {
    setCloning(true)
    try { await onClone(lib.id) } catch { /* */ }
    finally { setCloning(false) }
  }

  async function handlePromote() {
    setPromoting(true)
    try { await onPromote(lib.id) } catch { /* */ }
    finally { setPromoting(false) }
  }

  return (
    <div className={`relative rounded-xl border border-l-[3px] ${borderCls} bg-card hover:border-teal-500/30 transition-colors overflow-hidden`}>
      <div className="px-4 pt-4 pb-3 space-y-3">
        {/* Header row */}
        <div className="flex items-start gap-3">
          <div className={`rounded-lg p-2 shrink-0 ${ts.bg}`}>
            <Library className={`h-4 w-4 ${ts.text}`} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-semibold text-foreground truncate">{lib.name || lib.library_code}</span>
              {lib.is_published ? (
                <Badge variant="outline" className="text-[10px] font-semibold bg-green-500/10 text-green-500 border-green-500/30">Published</Badge>
              ) : (
                <Badge variant="outline" className="text-[10px] font-semibold bg-muted text-muted-foreground">Draft</Badge>
              )}
            </div>
            <code className="text-[10px] font-mono text-muted-foreground">{lib.library_code}</code>
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="rounded-md p-1 hover:bg-muted transition-colors shrink-0"
          >
            {expanded ? <ChevronDown className="h-4 w-4 text-muted-foreground" /> : <ChevronRight className="h-4 w-4 text-muted-foreground" />}
          </button>
        </div>

        {/* Meta row */}
        <div className="flex items-center gap-3 flex-wrap text-xs text-muted-foreground">
          <Badge variant="outline" className={`text-[10px] font-semibold ${ts.bg} ${ts.text} ${ts.border}`}>
            {lib.library_type_name || lib.library_type_code.replace(/_/g, " ")}
          </Badge>
          <span className="flex items-center gap-1">
            <FileCheck className="h-3 w-3" /> {lib.policy_count} {lib.policy_count === 1 ? "control test" : "control tests"}
          </span>
          <span>v{lib.version_number}</span>
          <span className="ml-auto">{fmtDate(lib.created_at)}</span>
        </div>

        {lib.description && (
          <p className="text-xs text-muted-foreground leading-relaxed">{lib.description}</p>
        )}

        {/* Tags */}
        {(lib.properties?.compliance_frameworks || lib.properties?.target_asset_type) && (
          <div className="flex items-center gap-1.5 flex-wrap">
            {lib.properties?.target_asset_type && (
              <span className="rounded-md border border-border bg-muted/50 px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground">
                {lib.properties.target_asset_type}
              </span>
            )}
            {lib.properties?.compliance_frameworks?.split(",").map((fw) => (
              <span key={fw.trim()} className="rounded-md border border-border bg-muted/50 px-1.5 py-0.5 text-[10px] text-muted-foreground">
                {fw.trim()}
              </span>
            ))}
          </div>
        )}

        {/* Action buttons */}
        <div className="flex items-center gap-1.5 flex-wrap pt-1">
          <Button size="sm" variant="ghost" className="h-7 text-xs gap-1" onClick={() => setExpanded(!expanded)}>
            <BookOpen className="h-3 w-3" /> {expanded ? "Hide" : "View"} Control Tests
          </Button>
          {!lib.is_published && (
            <Button size="sm" variant="ghost" className="h-7 text-xs gap-1" onClick={handlePublish} disabled={publishing}>
              <Upload className="h-3 w-3" /> {publishing ? "..." : "Publish"}
            </Button>
          )}
          <Button size="sm" variant="ghost" className="h-7 text-xs gap-1" onClick={handleClone} disabled={cloning}>
            <Copy className="h-3 w-3" /> {cloning ? "..." : "Clone"}
          </Button>
          {lib.is_published && (
            <Button size="sm" variant="ghost" className="h-7 text-xs gap-1 text-teal-500 hover:text-teal-400" onClick={handlePromote} disabled={promoting}>
              <ArrowUpFromLine className="h-3 w-3" /> {promoting ? "..." : "Promote to GRC"}
            </Button>
          )}
          <Button size="sm" variant="ghost" className="h-7 text-xs gap-1 text-muted-foreground hover:text-red-500 ml-auto" onClick={() => onDelete(lib)}>
            <Trash2 className="h-3 w-3" />
          </Button>
        </div>

        {/* Expanded: policies list */}
        {expanded && (
          <>
            <Separator />
            <LibraryPoliciesPanel libraryId={lib.id} isPublished={lib.is_published} orgId={orgId} onReload={onReload} />
          </>
        )}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Page
// ─────────────────────────────────────────────────────────────────────────────

export default function LibrariesPage() {
  const { selectedOrgId, selectedWorkspaceId, ready: orgReady } = useSandboxOrgWorkspace()
  const [libraries, setLibraries] = useState<LibraryResponse[]>([])
  const [types, setTypes] = useState<DimensionResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Success feedback
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const showSuccess = (msg: string) => {
    setSuccessMessage(msg)
    setTimeout(() => setSuccessMessage(null), 3000)
  }

  // Filters (debounced search)
  const [searchInput, setSearchInput] = useState("")
  const [search, setSearch] = useState("")
  useEffect(() => {
    const timer = setTimeout(() => setSearch(searchInput), 300)
    return () => clearTimeout(timer)
  }, [searchInput])

  const [filterType, setFilterType] = useState("")
  const [filterPublished, setFilterPublished] = useState<string>("")

  // Dialogs
  const [showCreate, setShowCreate] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<LibraryResponse | null>(null)

  // Promote with asset
  const [promoteTarget, setPromoteTarget] = useState<string | null>(null)
  const [promoteAssetOpen, setPromoteAssetOpen] = useState(false)

  const loadData = useCallback(async () => {
    if (!selectedOrgId) return
    setLoading(true); setError(null)
    try {
      const [libRes, typeRes] = await Promise.all([
        listLibraries({
          org_id: selectedOrgId,
          workspace_id: selectedWorkspaceId || undefined,
          library_type_code: filterType || undefined,
          is_published: filterPublished === "" ? undefined : filterPublished === "true",
          search: search || undefined,
        }),
        listLibraryTypes(),
      ])
      setLibraries(libRes.items ?? [])
      setTypes(typeRes)
    } catch (e) { setError(e instanceof Error ? e.message : "Failed to load libraries") }
    finally { setLoading(false) }
  }, [selectedOrgId, selectedWorkspaceId, filterType, filterPublished, search])

  useEffect(() => { if (orgReady) loadData() }, [orgReady, loadData])

  async function handleCreate(payload: { library_code: string; library_type_code: string; properties?: Record<string, string> }) {
    if (!selectedOrgId) return
    await createLibrary(selectedOrgId, payload)
    showSuccess("Library created successfully")
    await loadData()
  }

  async function handlePublish(id: string) {
    if (!selectedOrgId) return
    await publishLibrary(selectedOrgId, id)
    showSuccess("Library published")
    await loadData()
  }

  async function handleClone(id: string) {
    if (!selectedOrgId) return
    await cloneLibrary(selectedOrgId, id)
    showSuccess("Library cloned")
    await loadData()
  }

  async function handlePromote(id: string) {
    setPromoteTarget(id)
    setPromoteAssetOpen(true)
  }

  async function handlePromoteWithAsset(connectorId: string) {
    if (!promoteTarget) return
    try {
      await promoteLibrary(promoteTarget, { linked_asset_id: connectorId, workspace_id: selectedWorkspaceId ?? undefined })
      setPromoteAssetOpen(false)
      setPromoteTarget(null)
      showSuccess("Library promoted to Control Tests")
      await loadData()
    } catch (e) {
      showSuccess("Promotion failed: " + (e instanceof Error ? e.message : "Unknown error"))
    }
  }

  async function handleDelete(id: string) {
    if (!selectedOrgId) return
    await deleteLibrary(selectedOrgId, id)
    setDeleteTarget(null)
    showSuccess("Library deleted")
    await loadData()
  }

  // Stats
  const totalLibs = libraries.length
  const publishedCount = libraries.filter((l) => l.is_published).length
  const draftCount = totalLibs - publishedCount
  const totalPolicies = libraries.reduce((sum, l) => sum + l.policy_count, 0)

  // Active filter chips
  const activeFilters: { key: string; label: string; onRemove: () => void }[] = []
  if (filterType) {
    const typeName = types.find((t) => t.code === filterType)?.name ?? filterType
    activeFilters.push({ key: "type", label: `Type: ${typeName}`, onRemove: () => setFilterType("") })
  }
  if (filterPublished !== "") {
    activeFilters.push({ key: "status", label: filterPublished === "true" ? "Published" : "Draft", onRemove: () => setFilterPublished("") })
  }
  if (search) {
    activeFilters.push({ key: "search", label: `"${search}"`, onRemove: () => { setSearch(""); setSearchInput("") } })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="rounded-xl bg-teal-500/10 p-3 shrink-0">
            <Library className="h-6 w-6 text-teal-500" />
          </div>
          <div className="flex flex-col gap-1">
            <h2 className="text-2xl font-semibold text-foreground">Control Test Libraries</h2>
            <p className="text-sm text-muted-foreground">
              Group control tests into reusable libraries for organized compliance testing.
            </p>
          </div>
        </div>
        <Button size="sm" className="gap-1.5 shrink-0" onClick={() => setShowCreate(true)}>
          <Plus className="h-3.5 w-3.5" /> Create Library
        </Button>
      </div>

      {/* KPI stat cards */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {[
          { label: "Total Libraries", value: totalLibs,       icon: Library,    iconBg: "bg-teal-500/10",  iconColor: "text-teal-500",  numCls: "text-foreground",   borderCls: "border-l-primary" },
          { label: "Published",        value: publishedCount, icon: Upload,     iconBg: "bg-green-500/10", iconColor: "text-green-500", numCls: "text-green-500",   borderCls: "border-l-green-500" },
          { label: "Draft",            value: draftCount,     icon: FileCheck,  iconBg: "bg-muted",        iconColor: "text-muted-foreground", numCls: "text-amber-500", borderCls: "border-l-amber-500" },
          { label: "Total Control Tests", value: totalPolicies,  icon: BookOpen,   iconBg: "bg-blue-500/10",  iconColor: "text-blue-500",  numCls: "text-blue-500",    borderCls: "border-l-blue-500" },
        ].map((s) => (
          <div key={s.label} className={`relative flex items-center gap-3 rounded-xl border border-l-[3px] ${s.borderCls} bg-card px-4 py-3`}>
            <div className={`shrink-0 rounded-lg p-2 ${s.iconBg}`}>
              <s.icon className={`h-4 w-4 ${s.iconColor}`} />
            </div>
            <div className="flex flex-col min-w-0">
              <span className={`text-2xl font-bold tabular-nums leading-none ${s.numCls}`}>{s.value}</span>
              <span className="text-[11px] text-muted-foreground mt-0.5 block truncate">{s.label}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Recommended libraries banner */}
      {libraries.length === 0 && !loading && (
        <div className="rounded-xl border border-teal-500/20 bg-teal-500/5 px-5 py-4 space-y-3">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-teal-500" />
            <h3 className="text-sm font-semibold text-foreground">Recommended for your environment</h3>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
            {RECOMMENDED_LIBRARIES.map((rec) => {
              const rs = typeStyle(rec.type)
              return (
                <div key={rec.code} className="rounded-lg border border-border bg-card px-3 py-2.5 space-y-1.5">
                  <div className="flex items-center gap-2">
                    <Library className={`h-3.5 w-3.5 ${rs.text}`} />
                    <span className="text-xs font-semibold text-foreground">{rec.name}</span>
                  </div>
                  <p className="text-[11px] text-muted-foreground leading-relaxed">{rec.description}</p>
                  <Badge variant="outline" className={`text-[10px] font-semibold ${rs.bg} ${rs.text} ${rs.border}`}>
                    {rec.type.replace(/_/g, " ")}
                  </Badge>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Filter bar */}
      <div className="rounded-xl border border-border bg-card px-4 py-3 space-y-3">
        <div className="flex items-center gap-3 flex-wrap">
          <div className="relative flex-1 min-w-[200px] max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search libraries..."
              className="h-9 pl-9 text-sm"
            />
          </div>
          <div className="flex items-center gap-1.5">
            <Filter className="h-3.5 w-3.5 text-muted-foreground" />
            <select
              className="h-9 rounded-md border border-input bg-background px-3 text-sm"
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
            >
              <option value="">All Types</option>
              {types.map((t) => <option key={t.code} value={t.code}>{t.name}</option>)}
            </select>
          </div>
          <select
            className="h-9 rounded-md border border-input bg-background px-3 text-sm"
            value={filterPublished}
            onChange={(e) => setFilterPublished(e.target.value)}
          >
            <option value="">All Status</option>
            <option value="true">Published</option>
            <option value="false">Draft</option>
          </select>
          <Button size="sm" variant="ghost" className="h-9 gap-1" onClick={loadData}>
            <RefreshCw className="h-3.5 w-3.5" /> Refresh
          </Button>
        </div>
        {/* Active filter chips */}
        {activeFilters.length > 0 && (
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[11px] text-muted-foreground">Active filters:</span>
            {activeFilters.map((f) => (
              <span key={f.key} className="inline-flex items-center gap-1 rounded-md border border-border bg-muted/50 px-2 py-0.5 text-[11px] font-medium text-foreground">
                {f.label}
                <button onClick={f.onRemove} className="text-muted-foreground hover:text-foreground transition-colors">
                  <X className="h-2.5 w-2.5" />
                </button>
              </span>
            ))}
            <button
              onClick={() => { setFilterType(""); setFilterPublished(""); setSearch(""); setSearchInput("") }}
              className="text-[11px] text-muted-foreground hover:text-foreground underline underline-offset-2 transition-colors"
            >
              Clear all
            </button>
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
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-500">
          {error}
        </div>
      )}

      {/* Loading skeleton */}
      {loading && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="rounded-xl border border-l-[3px] border-l-primary border-border bg-card p-5 space-y-3 animate-pulse">
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-lg bg-muted" />
                <div className="space-y-1 flex-1">
                  <div className="h-4 w-2/3 rounded bg-muted" />
                  <div className="h-2.5 w-1/3 rounded bg-muted" />
                </div>
              </div>
              <div className="h-3 w-full rounded bg-muted" />
              <div className="h-3 w-3/4 rounded bg-muted" />
            </div>
          ))}
        </div>
      )}

      {/* Library rows */}
      {!loading && libraries.length > 0 && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {libraries.map((lib) => (
            <LibraryRow
              key={lib.id}
              lib={lib}
              orgId={selectedOrgId || ""}
              onPublish={handlePublish}
              onClone={handleClone}
              onPromote={handlePromote}
              onDelete={setDeleteTarget}
              onReload={loadData}
            />
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && libraries.length === 0 && (
        <div className="rounded-xl border border-dashed border-border bg-muted/10 px-5 py-12 text-center space-y-3">
          <Library className="h-8 w-8 text-muted-foreground mx-auto" />
          <p className="text-sm text-muted-foreground">No libraries found. Create your first library to start organizing control tests.</p>
          <Button size="sm" variant="outline" className="gap-1.5" onClick={() => setShowCreate(true)}>
            <Plus className="h-3.5 w-3.5" /> Create Library
          </Button>
        </div>
      )}

      {/* Dialogs */}
      <CreateLibraryDialog open={showCreate} types={types} onCreate={handleCreate} onClose={() => setShowCreate(false)} />
      <DeleteLibraryDialog library={deleteTarget} onConfirm={handleDelete} onClose={() => setDeleteTarget(null)} />

      {/* Promote — asset selector */}
      {promoteAssetOpen && selectedOrgId && (
        <AssetSelectorDialog
          open={promoteAssetOpen}
          orgId={selectedOrgId}
          currentAssetId={null}
          onSelect={handlePromoteWithAsset}
          onClose={() => { setPromoteAssetOpen(false); setPromoteTarget(null) }}
        />
      )}
    </div>
  )
}
