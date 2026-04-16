"use client"

import { useEffect, useState, useCallback, useRef } from "react"
import { Button, Input, Badge } from "@kcontrol/ui"
import {
  Building2,
  Search,
  Layers,
  ChevronDown,
  ChevronRight,
  Users,
  AlertCircle,
  Trash2,
  Plus,
  Crown,
  Check,
  X,
  Pencil,
  RefreshCw,
  UserMinus,
  Ban,
  Power,
  User,
  Briefcase,
  Handshake,
} from "lucide-react"
import { listOrgs, listOrgMembers, updateOrg, addOrgMember, removeOrgMember } from "@/lib/api/orgs"
import { listWorkspaces, listWorkspaceMembers } from "@/lib/api/workspaces"
import { listAdminUsers, listAuditEvents,
  getEntitySettings, getEntitySettingKeys, setEntitySetting, deleteEntitySetting,
  listLicenseProfiles,
  listGroups, listGroupMembers, addGroupMember, removeGroupMember,
} from "@/lib/api/admin"
import type { OrgResponse, OrgMemberResponse, WorkspaceResponse, WorkspaceMemberResponse } from "@/lib/types/orgs"
import type { SettingResponse, SettingKeyResponse, LicenseProfileResponse, UserSummaryResponse, AuditEventResponse, GroupResponse, GroupMemberResponse } from "@/lib/types/admin"

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" })
}

function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
}

// ── Skeleton ──────────────────────────────────────────────────────────────────

function SkeletonCard() {
  return (
    <div className="rounded-xl border border-l-[3px] border-border bg-card px-4 py-3 animate-pulse">
      <div className="flex items-center gap-3">
        <div className="shrink-0 rounded-lg p-2 bg-muted h-9 w-9" />
        <div className="space-y-1.5 flex-1">
          <div className="h-4 w-40 bg-muted rounded" />
          <div className="h-3 w-56 bg-muted rounded" />
        </div>
      </div>
    </div>
  )
}

// ── User Search Input ─────────────────────────────────────────────────────────

function UserSearchInput({ onSelect, disabled }: { onSelect: (u: UserSummaryResponse) => void; disabled?: boolean }) {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<UserSummaryResponse[]>([])
  const [open, setOpen] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!query.trim()) { setResults([]); setOpen(false); return }
    if (timerRef.current) clearTimeout(timerRef.current)
    timerRef.current = setTimeout(async () => {
      const res = await listAdminUsers({ search: query, limit: 8 }).catch(() => null)
      setResults(res?.users ?? [])
      setOpen(true)
    }, 250)
  }, [query])

  useEffect(() => {
    const handler = (e: MouseEvent) => { if (!ref.current?.contains(e.target as Node)) setOpen(false) }
    document.addEventListener("mousedown", handler)
    return () => document.removeEventListener("mousedown", handler)
  }, [])

  return (
    <div ref={ref} className="relative">
      <div className="relative">
        <Search className="absolute left-2.5 top-2.5 w-3.5 h-3.5 text-muted-foreground" />
        <Input
          className="pl-8 h-8 text-sm"
          placeholder="Search users to add…"
          value={query}
          onChange={e => setQuery(e.target.value)}
          disabled={disabled}
        />
      </div>
      {open && results.length > 0 && (
        <div className="absolute z-50 top-full mt-1 w-full rounded-lg border border-border bg-popover shadow-lg overflow-hidden">
          {results.map(u => (
            <button
              key={u.user_id}
              className="w-full text-left px-3 py-2 text-sm hover:bg-muted transition-colors flex items-center gap-2"
              onClick={() => { onSelect(u); setQuery(""); setOpen(false) }}
            >
              <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center text-xs font-medium text-primary shrink-0">
                {(u.email ?? u.username ?? "?")[0].toUpperCase()}
              </div>
              <div className="min-w-0">
                <div className="font-medium truncate text-xs">{u.display_name ?? u.email ?? u.username}</div>
                {u.email && <div className="text-xs text-muted-foreground truncate">{u.email}</div>}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Details Tab ───────────────────────────────────────────────────────────────

function DetailsTab({ org, onUpdated }: { org: OrgResponse; onUpdated: (o: OrgResponse) => void }) {
  const [editing, setEditing] = useState(false)
  const [editName, setEditName] = useState(org.name)
  const [editDesc, setEditDesc] = useState(org.description ?? "")
  const [saving, setSaving] = useState(false)
  const [toggling, setToggling] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSave = async () => {
    setSaving(true); setError(null)
    try {
      const updated = await updateOrg(org.id, { name: editName, description: editDesc || undefined })
      onUpdated(updated)
      setEditing(false)
    } catch (e) { setError(e instanceof Error ? e.message : "Failed to save") }
    finally { setSaving(false) }
  }

  const handleToggleActive = async () => {
    setToggling(true); setError(null)
    try {
      const updated = await updateOrg(org.id, { is_disabled: org.is_active })
      onUpdated(updated)
    } catch (e) { setError(e instanceof Error ? e.message : "Failed to update status") }
    finally { setToggling(false) }
  }

  return (
    <div className="space-y-4">
      {error && (
        <p className="text-xs text-red-500 flex items-center gap-1"><AlertCircle className="h-3 w-3" />{error}</p>
      )}

      {editing ? (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Name</label>
              <Input value={editName} onChange={e => setEditName(e.target.value)} className="h-8 text-sm" />
            </div>
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">Description</label>
              <Input value={editDesc} onChange={e => setEditDesc(e.target.value)} className="h-8 text-sm" placeholder="Optional description" />
            </div>
          </div>
          <div className="flex gap-2">
            <Button size="sm" onClick={handleSave} disabled={saving} className="h-7 px-3 text-xs">
              <Check className="h-3 w-3 mr-1" />{saving ? "Saving…" : "Save"}
            </Button>
            <Button size="sm" variant="ghost" onClick={() => { setEditing(false); setEditName(org.name); setEditDesc(org.description ?? "") }} className="h-7 px-3 text-xs">
              Cancel
            </Button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-x-6 gap-y-3">
          <div>
            <span className="text-xs text-muted-foreground">Name</span>
            <p className="text-sm font-medium text-foreground">{org.name}</p>
          </div>
          <div>
            <span className="text-xs text-muted-foreground">Slug</span>
            <p className="text-sm font-mono text-foreground">/{org.slug}</p>
          </div>
          <div>
            <span className="text-xs text-muted-foreground">Type</span>
            <p className="text-sm text-foreground flex items-center gap-1.5 mt-0.5">
              <OrgTypeIcon code={org.org_type_code} className="h-3.5 w-3.5" />
              {org.org_type_code}
            </p>
          </div>
          <div>
            <span className="text-xs text-muted-foreground">Status</span>
            <p className={`text-sm font-medium ${org.is_active ? "text-green-500" : "text-muted-foreground"}`}>
              {org.is_active ? "Active" : "Inactive"}
            </p>
          </div>
          <div>
            <span className="text-xs text-muted-foreground">Created</span>
            <p className="text-sm text-foreground">{formatDate(org.created_at)}</p>
          </div>
          <div>
            <span className="text-xs text-muted-foreground">Updated</span>
            <p className="text-sm text-foreground">{formatDate(org.updated_at)}</p>
          </div>
          {org.description && (
            <div className="col-span-2">
              <span className="text-xs text-muted-foreground">Description</span>
              <p className="text-sm text-foreground">{org.description}</p>
            </div>
          )}
          <div className="col-span-2">
            <span className="text-xs text-muted-foreground">Tenant Key</span>
            <code className="block font-mono text-xs text-muted-foreground mt-0.5">{org.tenant_key}</code>
          </div>
        </div>
      )}

      {/* Actions */}
      {!editing && (
        <div className="flex items-center gap-2 pt-1 border-t border-border">
          <Button size="sm" variant="outline" onClick={() => setEditing(true)} className="h-7 px-3 text-xs gap-1">
            <Pencil className="h-3 w-3" />Edit
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={handleToggleActive}
            disabled={toggling}
            className={`h-7 px-3 text-xs gap-1 ${org.is_active ? "hover:text-red-500 hover:border-red-500/40" : "hover:text-green-500 hover:border-green-500/40"}`}
          >
            {org.is_active
              ? <><Ban className="h-3 w-3" />{toggling ? "Disabling…" : "Disable Org"}</>
              : <><Power className="h-3 w-3" />{toggling ? "Enabling…" : "Enable Org"}</>
            }
          </Button>
        </div>
      )}
    </div>
  )
}

// ── Members Tab ───────────────────────────────────────────────────────────────

const ORG_ROLES = ["owner", "admin", "member", "viewer", "billing"]

function MembersTab({ orgId, onCountLoaded }: { orgId: string; onCountLoaded?: (count: number) => void }) {
  const [members, setMembers] = useState<OrgMemberResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [adding, setAdding] = useState(false)
  const [addRole, setAddRole] = useState("member")
  const [removing, setRemoving] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true); setError(null)
    try {
      const res = await listOrgMembers(orgId)
      setMembers(res)
      onCountLoaded?.(res.length)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load members")
    } finally { setLoading(false) }
  }, [orgId])

  useEffect(() => { load() }, [load])

  const handleAdd = async (user: UserSummaryResponse) => {
    setAdding(true); setActionError(null)
    try {
      await addOrgMember(orgId, user.user_id, addRole)
      await load()
    } catch (e) { setActionError(e instanceof Error ? e.message : "Failed to add member") }
    finally { setAdding(false) }
  }

  const handleRemove = async (userId: string) => {
    setRemoving(userId); setActionError(null)
    try {
      await removeOrgMember(orgId, userId)
      setMembers(prev => prev.filter(m => m.user_id !== userId))
      onCountLoaded?.(members.length - 1)
    } catch (e) { setActionError(e instanceof Error ? e.message : "Failed to remove member") }
    finally { setRemoving(null) }
  }

  if (loading) return <div className="h-8 rounded bg-muted animate-pulse" />
  if (error) return <p className="text-xs text-red-500 flex items-center gap-1"><AlertCircle className="h-3 w-3" />{error}</p>

  return (
    <div className="space-y-3">
      {actionError && (
        <p className="text-xs text-red-500 flex items-center gap-1"><AlertCircle className="h-3 w-3" />{actionError}</p>
      )}

      {/* Add member */}
      <div className="flex items-end gap-2">
        <div className="flex-1">
          <UserSearchInput onSelect={handleAdd} disabled={adding} />
        </div>
        <div className="shrink-0">
          <select
            value={addRole}
            onChange={e => setAddRole(e.target.value)}
            className="h-8 rounded-lg border border-border bg-background px-2 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
          >
            {ORG_ROLES.map(r => <option key={r} value={r}>{r}</option>)}
          </select>
        </div>
      </div>

      {members.length === 0 ? (
        <p className="text-sm text-muted-foreground">No members in this organization.</p>
      ) : (
        <div className="space-y-1.5">
          {members.map((member) => (
            <div
              key={member.user_id}
              className="flex items-center justify-between gap-3 rounded-lg border border-border bg-card px-3 py-2 group/mrow"
            >
              <div className="flex items-center gap-2 min-w-0 flex-1">
                <div className="h-6 w-6 rounded-full bg-primary/15 flex items-center justify-center shrink-0">
                  <Users className="h-3 w-3 text-primary" />
                </div>
                <div className="min-w-0">
                  {member.display_name && (
                    <span className="text-sm font-medium text-foreground block truncate">{member.display_name}</span>
                  )}
                  <span className={`font-mono text-xs truncate block ${member.display_name ? "text-muted-foreground" : "text-foreground"}`}>
                    {member.email ?? member.user_id}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <Badge variant="outline" className="text-xs text-muted-foreground">
                  {member.role}
                </Badge>
                <Badge
                  variant="outline"
                  className={`text-xs ${member.is_active ? "text-green-500 border-green-500/30" : "text-muted-foreground"}`}
                >
                  {member.is_active ? "active" : "inactive"}
                </Badge>
                <button
                  onClick={() => handleRemove(member.user_id)}
                  disabled={removing === member.user_id}
                  className="opacity-0 group-hover/mrow:opacity-100 rounded p-1 text-muted-foreground hover:text-red-500 hover:bg-red-500/10 transition-opacity disabled:opacity-50"
                  title="Remove member"
                >
                  <UserMinus className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Workspaces Tab ────────────────────────────────────────────────────────────

function WorkspaceMembersExpand({ orgId, workspaceId }: { orgId: string; workspaceId: string }) {
  const [members, setMembers] = useState<WorkspaceMemberResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    listWorkspaceMembers(orgId, workspaceId)
      .then(res => { if (!cancelled) { setMembers(res); setLoading(false) } })
      .catch(e => { if (!cancelled) { setError(e instanceof Error ? e.message : "Failed"); setLoading(false) } })
    return () => { cancelled = true }
  }, [orgId, workspaceId])

  if (loading) return <div className="h-6 bg-muted rounded animate-pulse mt-1" />
  if (error) return <p className="text-xs text-red-500 mt-1">{error}</p>
  if (members.length === 0) return <p className="text-xs text-muted-foreground mt-1 pl-2">No members.</p>

  return (
    <div className="mt-1.5 pl-2 space-y-1">
      {members.map(m => (
        <div key={m.user_id} className="flex items-center gap-2 text-xs">
          <div className="w-4 h-4 rounded-full bg-primary/15 flex items-center justify-center shrink-0">
            <Users className="h-2.5 w-2.5 text-primary" />
          </div>
          <span className="truncate text-foreground">{m.display_name ?? m.email ?? m.user_id}</span>
          {m.email && m.display_name && <span className="text-muted-foreground truncate">{m.email}</span>}
          <Badge variant="outline" className="text-[10px] text-muted-foreground ml-auto shrink-0">{m.role}</Badge>
        </div>
      ))}
    </div>
  )
}

function WorkspacesTab({ workspaces, orgId }: { workspaces: WorkspaceResponse[]; orgId: string }) {
  const [expandedWs, setExpandedWs] = useState<string | null>(null)

  if (workspaces.length === 0) {
    return <p className="text-sm text-muted-foreground">No workspaces in this organization.</p>
  }

  return (
    <div className="space-y-1.5">
      {workspaces.map((ws) => (
        <div key={ws.id} className="rounded-lg border border-border bg-card overflow-hidden">
          <button
            className="w-full flex items-center gap-3 px-3 py-2 hover:bg-muted/40 transition-colors text-left"
            onClick={() => setExpandedWs(expandedWs === ws.id ? null : ws.id)}
          >
            <span className="text-muted-foreground shrink-0">
              {expandedWs === ws.id ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
            </span>
            <div className="h-5 w-5 rounded-full bg-primary/15 flex items-center justify-center shrink-0">
              <Layers className="h-3 w-3 text-primary" />
            </div>
            <span className="text-sm font-medium text-foreground truncate flex-1">{ws.name}</span>
            <code className="font-mono text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded">/{ws.slug}</code>
            <Badge variant="outline" className="text-xs text-muted-foreground shrink-0">{ws.workspace_type_code}</Badge>
            <span className={`inline-flex items-center gap-1 text-xs font-medium shrink-0 ${ws.is_active ? "text-green-500" : "text-muted-foreground"}`}>
              <span className={`inline-block h-1.5 w-1.5 rounded-full ${ws.is_active ? "bg-green-500" : "bg-muted-foreground"}`} />
              {ws.is_active ? "Active" : "Inactive"}
            </span>
          </button>
          {expandedWs === ws.id && (
            <div className="px-3 pb-3 border-t border-border/50 pt-2">
              <p className="text-xs font-medium text-muted-foreground mb-1">Members</p>
              <WorkspaceMembersExpand orgId={orgId} workspaceId={ws.id} />
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

// ── Settings Tab ──────────────────────────────────────────────────────────────

function SettingsTab({ orgId }: { orgId: string }) {
  const [settings, setSettings] = useState<SettingResponse[]>([])
  const [keys, setKeys] = useState<SettingKeyResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState<string | null>(null)
  const [newKey, setNewKey] = useState("")
  const [newValue, setNewValue] = useState("")

  const loadData = useCallback(async () => {
    setLoading(true); setError(null)
    try {
      const [settingsRes, keysRes] = await Promise.all([
        getEntitySettings("org", orgId),
        getEntitySettingKeys("org", orgId),
      ])
      setSettings(settingsRes); setKeys(keysRes)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load settings")
    } finally { setLoading(false) }
  }, [orgId])

  useEffect(() => { loadData() }, [loadData])

  const settingKeySet = new Set(settings.map(s => s.key))
  const availableKeys = keys.filter(k => !settingKeySet.has(k.code))

  async function handleSetSetting(e: React.FormEvent) {
    e.preventDefault()
    if (!newKey || !newValue) return
    setSaving(true); setError(null)
    try {
      await setEntitySetting("org", orgId, newKey, newValue)
      setNewKey(""); setNewValue("")
      await loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save setting")
    } finally { setSaving(false) }
  }

  async function handleDelete(key: string) {
    setDeleting(key); setError(null)
    try {
      await deleteEntitySetting("org", orgId, key)
      await loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete setting")
    } finally { setDeleting(null) }
  }

  if (loading) return <div className="h-8 rounded bg-muted animate-pulse" />

  return (
    <div className="space-y-4">
      {error && <p className="text-xs text-red-500 flex items-center gap-1"><AlertCircle className="h-3 w-3" />{error}</p>}
      {settings.length === 0 && <p className="text-sm text-muted-foreground">No settings configured for this organization.</p>}
      {settings.length > 0 && (
        <div className="space-y-1.5">
          {settings.map(setting => {
            const keyDef = keys.find(k => k.code === setting.key)
            return (
              <div key={setting.key} className="flex items-center justify-between gap-3 rounded-lg border border-border bg-card px-3 py-2">
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  <div className="min-w-0">
                    <span className="text-sm font-medium text-foreground">{keyDef?.name ?? setting.key}</span>
                    <code className="ml-2 font-mono text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded">{setting.key}</code>
                  </div>
                  <span className="text-sm text-foreground truncate">{setting.value}</span>
                </div>
                <button
                  onClick={() => handleDelete(setting.key)}
                  disabled={deleting === setting.key}
                  className="shrink-0 rounded-lg p-1.5 text-muted-foreground hover:bg-red-500/10 hover:text-red-500 transition-colors disabled:opacity-50"
                >
                  <Trash2 className={`h-3.5 w-3.5 ${deleting === setting.key ? "animate-pulse" : ""}`} />
                </button>
              </div>
            )
          })}
        </div>
      )}
      {availableKeys.length > 0 && (
        <form onSubmit={handleSetSetting} className="flex items-end gap-2 pt-1">
          <div className="flex-1 space-y-1">
            <label className="text-xs font-medium text-foreground">Key</label>
            <select value={newKey} onChange={e => setNewKey(e.target.value)}
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50">
              <option value="">Select a setting key...</option>
              {availableKeys.map(k => <option key={k.code} value={k.code}>{k.name} ({k.code})</option>)}
            </select>
          </div>
          <div className="flex-1 space-y-1">
            <label className="text-xs font-medium text-foreground">Value</label>
            <Input value={newValue} onChange={e => setNewValue(e.target.value)} placeholder="Enter value" />
          </div>
          <Button type="submit" size="sm" variant="outline" disabled={saving || !newKey || !newValue} className="shrink-0">
            <Plus className="h-3.5 w-3.5 mr-1.5" />{saving ? "Saving..." : "Set"}
          </Button>
        </form>
      )}
      {availableKeys.length === 0 && settings.length > 0 && keys.length > 0 && (
        <p className="text-xs text-muted-foreground pt-1">All available setting keys are configured.</p>
      )}
    </div>
  )
}

// ── License Tab ──────────────────────────────────────────────────────────────

const TIER_META: Record<string, { label: string; color: string; bgColor: string; borderColor: string }> = {
  free:       { label: "Free",       color: "text-muted-foreground", bgColor: "bg-muted",          borderColor: "border-border" },
  pro:        { label: "Pro",        color: "text-primary",          bgColor: "bg-primary/10",      borderColor: "border-primary/40" },
  pro_trial:  { label: "Pro Trial",  color: "text-amber-500",        bgColor: "bg-amber-500/10",    borderColor: "border-amber-500/40" },
  enterprise: { label: "Enterprise", color: "text-blue-500",         bgColor: "bg-blue-500/10",     borderColor: "border-blue-500/40" },
  partner:    { label: "Partner",    color: "text-green-500",        bgColor: "bg-green-500/10",    borderColor: "border-green-500/40" },
  internal:   { label: "Internal",   color: "text-purple-500",       bgColor: "bg-purple-500/10",   borderColor: "border-purple-500/40" },
}

function LicenseTab({ orgId }: { orgId: string }) {
  const [settings, setSettings] = useState<SettingResponse[]>([])
  const [keys, setKeys] = useState<SettingKeyResponse[]>([])
  const [profiles, setProfiles] = useState<LicenseProfileResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState<Record<string, boolean>>({})
  const [editing, setEditing] = useState<Record<string, string>>({})
  const [error, setError] = useState<string | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true
    async function load() {
      try {
        const [s, k, p] = await Promise.all([
          getEntitySettings("org", orgId),
          getEntitySettingKeys("org", orgId),
          listLicenseProfiles().then(r => r.profiles).catch(() => []),
        ])
        if (mounted) { setSettings(s); setKeys(k); setProfiles(p) }
      } catch (e) {
        if (mounted) setError(e instanceof Error ? e.message : "Failed to load")
      } finally {
        if (mounted) setLoading(false)
      }
    }
    load()
    return () => { mounted = false }
  }, [orgId])

  if (loading) return <div className="h-16 animate-pulse rounded bg-muted" />
  if (error) return <p className="text-xs text-red-500">{error}</p>

  const settingMap = Object.fromEntries(settings.map(s => [s.key, s.value]))
  const currentTier = settingMap["license_tier"] ?? "free"
  const currentProfileCode = settingMap["license_profile"] ?? ""
  const currentProfile = profiles.find(p => p.code === currentProfileCode) ?? null
  const profileDefaults = Object.fromEntries((currentProfile?.settings ?? []).map(s => [s.key, s.value]))
  const allLimitKeys = keys.filter(k => k.code.startsWith("max_") || k.code === "license_expires_at").sort((a, b) => a.sort_order - b.sort_order)

  async function saveSetting(key: string, value?: string) {
    const val = value ?? editing[key]
    if (val === undefined) return
    const keyDef = keys.find(k => k.code === key)
    if (keyDef?.data_type === "integer") {
      const num = Number(val)
      if (!Number.isInteger(num) || num < 0) return
    }
    setSaving(p => ({ ...p, [key]: true })); setSaveError(null)
    try {
      await setEntitySetting("org", orgId, key, val)
      setSettings(prev => {
        const idx = prev.findIndex(s => s.key === key)
        if (idx >= 0) { const n = [...prev]; n[idx] = { key, value: val }; return n }
        return [...prev, { key, value: val }]
      })
      setEditing(p => { const n = { ...p }; delete n[key]; return n })
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Failed to save setting")
    } finally { setSaving(p => ({ ...p, [key]: false })) }
  }

  async function clearSetting(key: string) {
    setSaving(p => ({ ...p, [key]: true })); setSaveError(null)
    try {
      await deleteEntitySetting("org", orgId, key)
      setSettings(prev => prev.filter(s => s.key !== key))
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Failed to clear setting")
    } finally { setSaving(p => ({ ...p, [key]: false })) }
  }

  async function assignProfile(profileCode: string) {
    setSaving(p => ({ ...p, license_profile: true, license_tier: true })); setSaveError(null)
    const profile = profiles.find(p => p.code === profileCode)
    try {
      await setEntitySetting("org", orgId, "license_profile", profileCode)
      if (profile) await setEntitySetting("org", orgId, "license_tier", profile.tier)
      setSettings(prev => {
        let next = [...prev]
        const pi = next.findIndex(s => s.key === "license_profile")
        if (pi >= 0) next[pi] = { key: "license_profile", value: profileCode }
        else next.push({ key: "license_profile", value: profileCode })
        if (profile) {
          const ti = next.findIndex(s => s.key === "license_tier")
          if (ti >= 0) next[ti] = { key: "license_tier", value: profile.tier }
          else next.push({ key: "license_tier", value: profile.tier })
        }
        return next
      })
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Failed to assign profile")
    } finally { setSaving(p => ({ ...p, license_profile: false, license_tier: false })) }
  }

  const tierMeta = TIER_META[currentTier] ?? TIER_META.free

  return (
    <div className="space-y-5">
      {saveError && <p className="text-xs text-red-500 flex items-center gap-1"><AlertCircle className="h-3 w-3" />{saveError}</p>}
      <div className="space-y-2">
        <label className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">License Profile</label>
        <div className="flex flex-wrap gap-2">
          {profiles.filter(p => p.is_active).map(p => {
            const tm = TIER_META[p.tier] ?? TIER_META.free
            const isSelected = currentProfileCode === p.code
            return (
              <button key={p.code} type="button" disabled={saving["license_profile"]} onClick={() => assignProfile(p.code)}
                className={`inline-flex items-center gap-1.5 rounded-xl border px-3 py-2 text-left transition-all disabled:opacity-50 ${
                  isSelected ? "border-primary bg-primary/5 ring-1 ring-primary" : `${tm.borderColor} ${tm.bgColor} hover:ring-1 hover:ring-primary/30`
                }`}>
                <Crown className={`h-3.5 w-3.5 shrink-0 ${isSelected ? "text-primary" : tm.color}`} />
                <div className="min-w-0">
                  <span className={`text-xs font-semibold block ${isSelected ? "text-primary" : "text-foreground"}`}>{p.name}</span>
                  <span className="text-[10px] text-muted-foreground block">{tm.label} tier</span>
                </div>
              </button>
            )
          })}
        </div>
        {!currentProfileCode && <p className="text-xs text-muted-foreground">No profile assigned.</p>}
      </div>
      <div className="flex items-center gap-3 rounded-xl border border-border bg-muted/20 px-4 py-2.5">
        <span className="text-xs text-muted-foreground">Current Tier:</span>
        <span className={`inline-flex items-center gap-1 rounded-full border ${tierMeta.borderColor} ${tierMeta.bgColor} px-2 py-0.5 text-xs font-semibold ${tierMeta.color}`}>
          {(currentTier === "pro" || currentTier === "pro_trial" || currentTier === "enterprise") && <Crown className="h-3 w-3" />}
          {tierMeta.label}
        </span>
        {currentProfile && (
          <><span className="text-xs text-muted-foreground">from profile</span>
          <code className="text-xs font-mono text-foreground bg-muted px-1.5 py-0.5 rounded">{currentProfile.name}</code></>
        )}
      </div>
      <div className="space-y-2">
        <label className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
          Limits & Configuration
          {currentProfile && <span className="font-normal normal-case tracking-normal ml-1 text-muted-foreground">— profile defaults in gray, org overrides in bold</span>}
        </label>
        <div className="rounded-xl border border-border bg-muted/20 divide-y divide-border overflow-hidden">
          {allLimitKeys.map(k => {
            const orgValue = settingMap[k.code] ?? ""
            const profileValue = profileDefaults[k.code] ?? ""
            const effectiveValue = orgValue || profileValue
            const isOverridden = !!orgValue && !!profileValue && orgValue !== profileValue
            const isEditing = editing[k.code] !== undefined
            const editVal = editing[k.code] ?? orgValue
            return (
              <div key={k.code} className="flex items-center gap-3 px-3 py-2 hover:bg-accent/30 transition-colors group/limrow">
                <div className="w-36 shrink-0"><span className="text-xs font-medium text-foreground">{k.name}</span></div>
                {isEditing ? (
                  <div className="flex items-center gap-1 flex-1">
                    <Input value={editVal} onChange={e => setEditing(p => ({ ...p, [k.code]: e.target.value }))}
                      className="h-7 text-xs flex-1 font-mono"
                      type={k.data_type === "integer" ? "number" : "text"}
                      min={k.data_type === "integer" ? "0" : undefined}
                      placeholder={profileValue ? `Profile default: ${profileValue}` : "value"} />
                    <button onClick={() => saveSetting(k.code)} disabled={saving[k.code]} className="rounded p-1 text-green-500 hover:bg-green-500/10 disabled:opacity-50"><Check className="h-3.5 w-3.5" /></button>
                    <button onClick={() => setEditing(p => { const n = { ...p }; delete n[k.code]; return n })} className="rounded p-1 text-muted-foreground hover:bg-muted"><X className="h-3.5 w-3.5" /></button>
                  </div>
                ) : (
                  <div className="flex items-center gap-1.5 flex-1">
                    {effectiveValue
                      ? <span className={`text-xs font-mono ${orgValue ? "text-foreground font-semibold" : "text-muted-foreground"}`}>{effectiveValue}</span>
                      : <span className="text-xs text-muted-foreground italic">no limit</span>
                    }
                    {isOverridden && <span className="text-[10px] text-amber-500 border border-amber-500/30 bg-amber-500/5 rounded px-1">overridden (profile: {profileValue})</span>}
                    {!orgValue && profileValue && <span className="text-[10px] text-muted-foreground border border-border rounded px-1">from profile</span>}
                    <div className="ml-auto flex items-center gap-0.5 opacity-0 group-hover/limrow:opacity-100 transition-opacity">
                      <button onClick={() => setEditing(p => ({ ...p, [k.code]: orgValue }))} className="rounded p-1 text-muted-foreground hover:text-foreground hover:bg-muted"><Pencil className="h-3 w-3" /></button>
                      {orgValue && <button onClick={() => clearSetting(k.code)} disabled={saving[k.code]} className="rounded p-1 text-muted-foreground hover:text-destructive hover:bg-destructive/10 disabled:opacity-50" title="Remove override"><X className="h-3 w-3" /></button>}
                    </div>
                  </div>
                )}
              </div>
            )
          })}
          {allLimitKeys.length === 0 && (
            <p className="px-3 py-4 text-xs text-muted-foreground text-center">No limit settings available yet.</p>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Audit Tab ─────────────────────────────────────────────────────────────────

function AuditTab({ orgId }: { orgId: string }) {
  const [events, setEvents] = useState<AuditEventResponse[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [offset, setOffset] = useState(0)
  const limit = 20

  const load = useCallback(async (off: number) => {
    setLoading(true); setError(null)
    try {
      const res = await listAuditEvents({ entity_type: "org", entity_id: orgId, limit, offset: off })
      setEvents(res.events)
      setTotal(res.total)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load audit events")
    } finally { setLoading(false) }
  }, [orgId])

  useEffect(() => { load(0) }, [load])

  if (loading) return <div className="space-y-2">{[...Array(4)].map((_, i) => <div key={i} className="h-8 bg-muted rounded animate-pulse" />)}</div>
  if (error) return <p className="text-xs text-red-500 flex items-center gap-1"><AlertCircle className="h-3 w-3" />{error}</p>
  if (events.length === 0) return <p className="text-sm text-muted-foreground">No audit events for this organization.</p>

  return (
    <div className="space-y-2">
      <div className="space-y-1">
        {events.map(ev => (
          <div key={ev.id} className="flex items-start gap-3 rounded-lg border border-border bg-card px-3 py-2 text-xs">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                <code className="font-mono text-foreground font-medium">{ev.event_type}</code>
                <Badge variant="outline" className="text-[10px] text-muted-foreground">{ev.entity_type}</Badge>
              </div>
              {ev.actor_id && (
                <p className="text-muted-foreground mt-0.5 truncate">by {ev.actor_id.slice(0, 8)}…</p>
              )}
            </div>
            <span className="text-muted-foreground shrink-0 tabular-nums">{formatDateTime(ev.occurred_at)}</span>
          </div>
        ))}
      </div>
      {total > limit && (
        <div className="flex items-center justify-between pt-1">
          <span className="text-xs text-muted-foreground">{offset + 1}–{Math.min(offset + limit, total)} of {total}</span>
          <div className="flex gap-1">
            <Button size="sm" variant="outline" className="h-6 px-2 text-xs" disabled={offset === 0} onClick={() => { const o = Math.max(0, offset - limit); setOffset(o); load(o) }}>Prev</Button>
            <Button size="sm" variant="outline" className="h-6 px-2 text-xs" disabled={offset + limit >= total} onClick={() => { const o = offset + limit; setOffset(o); load(o) }}>Next</Button>
          </div>
        </div>
      )}
    </div>
  )
}

// ── Groups Tab ────────────────────────────────────────────────────────────────

function GroupsTab({ orgId }: { orgId: string }) {
  const [groups, setGroups] = useState<GroupResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedGroup, setExpandedGroup] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true); setError(null)
    try {
      const res = await listGroups()
      setGroups(res.groups.filter(g => g.scope_org_id === orgId))
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load groups")
    } finally { setLoading(false) }
  }, [orgId])

  useEffect(() => { load() }, [load])

  if (loading) return <div className="space-y-2">{[...Array(3)].map((_, i) => <div key={i} className="h-10 bg-muted rounded animate-pulse" />)}</div>
  if (error) return <p className="text-xs text-red-500 flex items-center gap-1"><AlertCircle className="h-3 w-3" />{error}</p>

  const systemGroups = groups.filter(g => g.is_system)
  const customGroups = groups.filter(g => !g.is_system)

  return (
    <div className="space-y-4">
      <div>
        <div className="flex items-center gap-2 mb-2">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-amber-500/80">System Groups</span>
          <span className="text-[10px] text-muted-foreground/50">· auto-managed, read-only</span>
        </div>
        {systemGroups.length === 0 ? (
          <p className="text-xs text-muted-foreground/50">No system groups for this org.</p>
        ) : (
          <div className="space-y-1.5">
            {systemGroups.map(g => (
              <GroupMemberPanel key={g.id} group={g} readonly onChanged={load} expanded={expandedGroup === g.id} onToggle={() => setExpandedGroup(prev => prev === g.id ? null : g.id)} />
            ))}
          </div>
        )}
      </div>

      <div>
        <div className="flex items-center gap-2 mb-2">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-primary/70">Custom Groups</span>
        </div>
        {customGroups.length === 0 ? (
          <p className="text-xs text-muted-foreground/50">No custom groups for this org.</p>
        ) : (
          <div className="space-y-1.5">
            {customGroups.map(g => (
              <GroupMemberPanel key={g.id} group={g} readonly={false} onChanged={load} expanded={expandedGroup === g.id} onToggle={() => setExpandedGroup(prev => prev === g.id ? null : g.id)} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function GroupMemberPanel({
  group, readonly, onChanged, expanded, onToggle,
}: {
  group: GroupResponse
  readonly: boolean
  onChanged: () => void
  expanded: boolean
  onToggle: () => void
}) {
  const [members, setMembers] = useState<GroupMemberResponse[]>([])
  const [total, setTotal] = useState(0)
  const [loadingMembers, setLoadingMembers] = useState(false)
  const [adding, setAdding] = useState(false)
  const [removing, setRemoving] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  const loadMembers = useCallback(async () => {
    setLoadingMembers(true)
    try {
      const res = await listGroupMembers(group.id, 50, 0)
      setMembers(res.members)
      setTotal(res.total)
    } catch { /* ignore */ }
    finally { setLoadingMembers(false) }
  }, [group.id])

  useEffect(() => {
    if (expanded) loadMembers()
  }, [expanded, loadMembers])

  const handleAdd = async (user: UserSummaryResponse) => {
    setAdding(true); setActionError(null)
    try {
      await addGroupMember(group.id, user.user_id)
      await loadMembers()
      onChanged()
    } catch (e) { setActionError(e instanceof Error ? e.message : "Failed to add member") }
    finally { setAdding(false) }
  }

  const handleRemove = async (userId: string) => {
    setRemoving(userId); setActionError(null)
    try {
      await removeGroupMember(group.id, userId)
      setMembers(prev => prev.filter(m => m.user_id !== userId))
      onChanged()
    } catch (e) { setActionError(e instanceof Error ? e.message : "Failed to remove member") }
    finally { setRemoving(null) }
  }

  return (
    <div className={`rounded-lg border overflow-hidden ${readonly ? "border-amber-500/20 bg-amber-500/5" : "border-border bg-card"}`}>
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-2 px-3 py-2.5 text-left hover:bg-muted/30 transition-colors"
      >
        <span className="text-muted-foreground shrink-0">
          {expanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
        </span>
        <div className="flex-1 min-w-0 flex items-center gap-2">
          <span className="text-sm font-medium text-foreground truncate">{group.name}</span>
          <code className="font-mono text-[10px] text-muted-foreground/60 truncate">{group.code}</code>
          {readonly && (
            <Badge variant="outline" className="text-[10px] text-amber-500 border-amber-500/30 gap-1 shrink-0">
              <Ban className="h-2.5 w-2.5" />system
            </Badge>
          )}
          <Badge variant="outline" className="text-[10px] text-muted-foreground shrink-0">{group.role_level_code}</Badge>
        </div>
        <Badge variant="outline" className="text-[10px] text-muted-foreground shrink-0">
          <Users className="h-2.5 w-2.5 mr-1" />{group.member_count}
        </Badge>
      </button>

      {expanded && (
        <div className="border-t border-border/50 px-3 py-3 space-y-2">
          {actionError && (
            <p className="text-xs text-red-500 flex items-center gap-1"><AlertCircle className="h-3 w-3" />{actionError}</p>
          )}

          {!readonly && (
            <UserSearchInput onSelect={handleAdd} disabled={adding} />
          )}

          {loadingMembers ? (
            <div className="h-6 bg-muted rounded animate-pulse" />
          ) : members.length === 0 ? (
            <p className="text-xs text-muted-foreground/50 text-center py-1">No members in this group.</p>
          ) : (
            <div className="space-y-1">
              {members.map(m => (
                <div key={m.user_id} className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-muted/30 group/gm">
                  <div className="w-5 h-5 rounded-full bg-primary/15 flex items-center justify-center shrink-0">
                    <User className="h-2.5 w-2.5 text-primary" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <span className="text-xs font-medium text-foreground truncate block">{m.display_name ?? m.email ?? m.user_id}</span>
                    {m.email && <span className="text-[10px] text-muted-foreground font-mono truncate block">{m.email}</span>}
                  </div>
                  {!readonly && (
                    <button
                      onClick={() => handleRemove(m.user_id)}
                      disabled={removing === m.user_id}
                      className="opacity-0 group-hover/gm:opacity-100 rounded p-1 text-muted-foreground hover:text-red-500 hover:bg-red-500/10 transition-opacity disabled:opacity-50"
                      title="Remove from group"
                    >
                      <UserMinus className="h-3 w-3" />
                    </button>
                  )}
                </div>
              ))}
              {total > members.length && (
                <p className="text-[10px] text-muted-foreground/50 text-center">+{total - members.length} more</p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Org Type ──────────────────────────────────────────────────────────────────

const ORG_TYPE_META: Record<string, { icon: React.FC<{ className?: string }>; color: string; bgColor: string; borderAccent: string }> = {
  personal:   { icon: User,       color: "text-violet-500",  bgColor: "bg-violet-500/10",  borderAccent: "border-l-violet-500" },
  company:    { icon: Building2,  color: "text-blue-500",    bgColor: "bg-blue-500/10",    borderAccent: "border-l-blue-500" },
  partner:    { icon: Handshake,  color: "text-emerald-500", bgColor: "bg-emerald-500/10", borderAccent: "border-l-emerald-500" },
  enterprise: { icon: Briefcase,  color: "text-amber-500",   bgColor: "bg-amber-500/10",   borderAccent: "border-l-amber-500" },
}

function OrgTypeIcon({ code, className }: { code: string; className?: string }) {
  const meta = ORG_TYPE_META[code] ?? { icon: Building2, color: "text-primary", bgColor: "bg-primary/10", borderAccent: "border-l-primary" }
  const Icon = meta.icon
  return <Icon className={`${meta.color} ${className ?? "h-3.5 w-3.5"}`} />
}

// ── License Badge ─────────────────────────────────────────────────────────────

function LicenseBadge({ tier }: { tier: string }) {
  const meta = TIER_META[tier] ?? TIER_META.free
  return (
    <Badge variant="outline" className={`text-[10px] ${meta.color} ${meta.bgColor} border-0 gap-0.5`}>
      {(tier === "pro" || tier === "pro_trial") && <Crown className="h-2.5 w-2.5" />}
      {meta.label}
    </Badge>
  )
}

// ── Org Row ───────────────────────────────────────────────────────────────────

type OrgTab = "details" | "members" | "workspaces" | "groups" | "license" | "settings" | "audit"

interface OrgRowProps {
  org: OrgResponse
  workspaces: WorkspaceResponse[]
  licenseTier: string
  onOrgUpdated: (o: OrgResponse) => void
}

function OrgRow({ org, workspaces, licenseTier, onOrgUpdated }: OrgRowProps) {
  const [expanded, setExpanded] = useState(false)
  const [activeTab, setActiveTab] = useState<OrgTab>("details")
  const [memberCount, setMemberCount] = useState<number | null>(null)

  const typeMeta = ORG_TYPE_META[org.org_type_code]
  const borderCls = org.is_active
    ? (typeMeta?.borderAccent ?? "border-l-primary")
    : "border-l-red-500"

  const tabs: { key: OrgTab; label: string }[] = [
    { key: "details", label: "Details" },
    { key: "members", label: memberCount !== null ? `Members (${memberCount})` : "Members" },
    { key: "workspaces", label: `Workspaces (${workspaces.length})` },
    { key: "groups", label: "Groups" },
    { key: "license", label: "License" },
    { key: "settings", label: "Settings" },
    { key: "audit", label: "Audit" },
  ]

  return (
    <div className={`rounded-xl border border-l-[3px] ${borderCls} border-border bg-card overflow-hidden`}>
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-muted/40 transition-colors text-left"
      >
        <span className="text-muted-foreground shrink-0">
          {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        </span>
        <div className={`shrink-0 rounded-lg p-2 ${org.is_active ? (typeMeta?.bgColor ?? "bg-primary/10") : "bg-muted"}`}>
          {org.is_active
            ? <OrgTypeIcon code={org.org_type_code} className="h-4 w-4" />
            : <Building2 className="h-4 w-4 text-muted-foreground" />
          }
        </div>
        <div className="flex-1 min-w-0 flex flex-wrap items-center gap-2">
          <span className={`font-semibold text-sm ${org.is_active ? "text-foreground" : "text-muted-foreground line-through"}`}>{org.name}</span>
          <code className="font-mono text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded">/{org.slug}</code>
          <Badge variant="outline" className="text-xs text-muted-foreground">{org.org_type_code}</Badge>
          <LicenseBadge tier={licenseTier} />
          {!org.is_active && <Badge variant="outline" className="text-xs text-red-500 border-red-500/30">Inactive</Badge>}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {memberCount !== null && (
            <Badge variant="outline" className="text-xs text-muted-foreground">
              <Users className="h-3 w-3 mr-1" />{memberCount}
            </Badge>
          )}
          <Badge variant="outline" className="text-xs text-muted-foreground">
            <Layers className="h-3 w-3 mr-1" />{workspaces.length}
          </Badge>
        </div>
      </button>

      {expanded && (
        <div className="border-t border-border">
          <div className="flex border-b border-border bg-muted/30 overflow-x-auto">
            {tabs.map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-4 py-2 text-xs font-medium whitespace-nowrap transition-colors ${
                  activeTab === tab.key
                    ? "border-b-2 border-primary text-primary bg-background"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
          <div className="p-4">
            {activeTab === "details" && <DetailsTab org={org} onUpdated={onOrgUpdated} />}
            {activeTab === "members" && <MembersTab orgId={org.id} onCountLoaded={setMemberCount} />}
            {activeTab === "workspaces" && <WorkspacesTab workspaces={workspaces} orgId={org.id} />}
            {activeTab === "groups" && <GroupsTab orgId={org.id} />}
            {activeTab === "license" && <LicenseTab orgId={org.id} />}
            {activeTab === "settings" && <SettingsTab orgId={org.id} />}
            {activeTab === "audit" && <AuditTab orgId={org.id} />}
          </div>
        </div>
      )}
    </div>
  )
}

// ── KPI Stat Card ─────────────────────────────────────────────────────────────

interface StatCardProps {
  icon: React.FC<{ className?: string }>
  label: string
  value: number | string
  borderCls: string
  iconCls: string
  numCls: string
}

function StatCard({ icon: Icon, label, value, borderCls, iconCls, numCls }: StatCardProps) {
  return (
    <div className={`relative flex items-center gap-3 rounded-xl border border-l-[3px] ${borderCls} bg-card px-4 py-3`}>
      <div className={`shrink-0 rounded-lg p-2 bg-muted`}>
        <Icon className={`h-4 w-4 ${iconCls}`} />
      </div>
      <div className="min-w-0">
        <span className={`text-2xl font-bold tabular-nums leading-none ${numCls}`}>{value}</span>
        <span className="text-[11px] text-muted-foreground mt-0.5 block truncate">{label}</span>
      </div>
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function OrgsPage() {
  const [orgs, setOrgs] = useState<OrgResponse[]>([])
  const [workspacesMap, setWorkspacesMap] = useState<Record<string, WorkspaceResponse[]>>({})
  const [licenseTiers, setLicenseTiers] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [filterStatus, setFilterStatus] = useState<"all" | "active" | "inactive">("all")
  const [filterTier, setFilterTier] = useState<string>("all")
  const [filterType, setFilterType] = useState<string>("all")

  const load = useCallback(async () => {
    setLoading(true); setError(null)
    try {
      const orgList = await listOrgs()
      setOrgs(orgList)
      const [wsResults, tierResults] = await Promise.all([
        Promise.all(orgList.map(org => listWorkspaces(org.id).catch(() => [] as WorkspaceResponse[]))),
        Promise.all(orgList.map(org =>
          getEntitySettings("org", org.id)
            .then(s => ({ orgId: org.id, tier: s.find(x => x.key === "license_tier")?.value ?? "free" }))
            .catch(() => ({ orgId: org.id, tier: "free" }))
        )),
      ])
      const wsMap: Record<string, WorkspaceResponse[]> = {}
      orgList.forEach((org, i) => { wsMap[org.id] = wsResults[i] })
      setWorkspacesMap(wsMap)
      const tierMap: Record<string, string> = {}
      tierResults.forEach(({ orgId, tier }) => { tierMap[orgId] = tier })
      setLicenseTiers(tierMap)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load organizations")
    } finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const handleOrgUpdated = useCallback((updated: OrgResponse) => {
    setOrgs(prev => prev.map(o => o.id === updated.id ? updated : o))
  }, [])

  const totalOrgs = orgs.length
  const activeOrgs = orgs.filter(o => o.is_active).length
  const totalWorkspaces = Object.values(workspacesMap).reduce((sum, wsList) => sum + wsList.length, 0)
  const tierCounts = Object.values(licenseTiers).reduce((acc, t) => { acc[t] = (acc[t] ?? 0) + 1; return acc }, {} as Record<string, number>)
  const orgTypes = [...new Set(orgs.map(o => o.org_type_code))].sort()

  const filtered = orgs.filter(o => {
    if (search.trim() && !o.name.toLowerCase().includes(search.toLowerCase()) && !o.slug.toLowerCase().includes(search.toLowerCase())) return false
    if (filterStatus === "active" && !o.is_active) return false
    if (filterStatus === "inactive" && o.is_active) return false
    if (filterTier !== "all" && (licenseTiers[o.id] ?? "free") !== filterTier) return false
    if (filterType !== "all" && o.org_type_code !== filterType) return false
    return true
  })

  const activeChips: { label: string; onRemove: () => void }[] = []
  if (search.trim()) activeChips.push({ label: `"${search}"`, onRemove: () => setSearch("") })
  if (filterStatus !== "all") activeChips.push({ label: filterStatus === "active" ? "Active" : "Inactive", onRemove: () => setFilterStatus("all") })
  if (filterTier !== "all") activeChips.push({ label: TIER_META[filterTier]?.label ?? filterTier, onRemove: () => setFilterTier("all") })
  if (filterType !== "all") activeChips.push({ label: filterType, onRemove: () => setFilterType("all") })

  return (
    <div className="max-w-5xl space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="rounded-xl bg-primary/10 p-3 shrink-0">
            <Building2 className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h2 className="text-2xl font-semibold text-foreground">Organizations</h2>
            <p className="text-sm text-muted-foreground mt-0.5">All organizations across the platform.</p>
          </div>
        </div>
        <Button size="sm" variant="outline" onClick={load} disabled={loading} className="h-8 px-3 gap-1.5 shrink-0">
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {/* KPI Stats */}
      {!loading && !error && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          <StatCard
            icon={Building2}
            label="Total Orgs"
            value={totalOrgs}
            borderCls="border-primary/40"
            iconCls="text-primary"
            numCls="text-foreground"
          />
          <StatCard
            icon={Building2}
            label="Active"
            value={activeOrgs}
            borderCls="border-green-500/40"
            iconCls="text-green-500"
            numCls="text-green-500"
          />
          <StatCard
            icon={Layers}
            label="Workspaces"
            value={totalWorkspaces}
            borderCls="border-blue-500/40"
            iconCls="text-blue-500"
            numCls="text-foreground"
          />
          <StatCard
            icon={Building2}
            label="Free"
            value={tierCounts["free"] ?? 0}
            borderCls="border-border"
            iconCls="text-muted-foreground"
            numCls="text-muted-foreground"
          />
          <StatCard
            icon={Crown}
            label="Pro"
            value={tierCounts["pro"] ?? 0}
            borderCls="border-primary/40"
            iconCls="text-primary"
            numCls="text-primary"
          />
          <StatCard
            icon={Crown}
            label="Trial"
            value={tierCounts["pro_trial"] ?? 0}
            borderCls="border-amber-500/40"
            iconCls="text-amber-500"
            numCls="text-amber-500"
          />
        </div>
      )}

      {/* Filter Bar */}
      {!loading && !error && (
        <div className="rounded-xl border border-border bg-card px-4 py-3 space-y-2.5">
          <div className="flex items-center gap-2 flex-wrap">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground/40 pointer-events-none" />
              <input
                type="text"
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Search name or slug…"
                className="h-8 w-52 rounded-lg border border-border bg-background pl-9 pr-3 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 transition-colors"
              />
              {search && (
                <button type="button" onClick={() => setSearch("")}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground/40 hover:text-foreground">
                  <X className="h-3 w-3" />
                </button>
              )}
            </div>
            <select
              value={filterStatus}
              onChange={e => setFilterStatus(e.target.value as "all" | "active" | "inactive")}
              className="h-8 rounded-lg border border-border bg-background px-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
            >
              <option value="all">All statuses</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
            <select
              value={filterTier}
              onChange={e => setFilterTier(e.target.value)}
              className="h-8 rounded-lg border border-border bg-background px-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
            >
              <option value="all">All tiers</option>
              {["free", "pro_trial", "pro", "enterprise", "partner", "internal"].map(t => (
                <option key={t} value={t}>{TIER_META[t]?.label ?? t}</option>
              ))}
            </select>
            {orgTypes.length > 1 && (
              <select
                value={filterType}
                onChange={e => setFilterType(e.target.value)}
                className="h-8 rounded-lg border border-border bg-background px-3 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
              >
                <option value="all">All types</option>
                {orgTypes.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            )}
            <span className="ml-auto text-xs text-muted-foreground/60">
              <span className="font-semibold text-foreground">{filtered.length}</span> of {totalOrgs}
            </span>
          </div>

          {/* Active filter chips */}
          {activeChips.length > 0 && (
            <div className="flex items-center gap-1.5 flex-wrap">
              {activeChips.map(chip => (
                <span
                  key={chip.label}
                  className="inline-flex items-center gap-1 rounded-full border border-primary/30 bg-primary/10 px-2 py-0.5 text-[11px] font-medium text-primary"
                >
                  {chip.label}
                  <button type="button" onClick={chip.onRemove} className="ml-0.5 rounded-full hover:bg-primary/20 p-0.5 transition-colors">
                    <X className="h-2.5 w-2.5" />
                  </button>
                </span>
              ))}
              <button
                type="button"
                onClick={() => { setSearch(""); setFilterStatus("all"); setFilterTier("all"); setFilterType("all") }}
                className="text-[11px] text-muted-foreground/50 hover:text-red-500 transition-colors flex items-center gap-0.5 ml-1"
              >
                <X className="h-3 w-3" />Clear all
              </button>
            </div>
          )}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-500 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />{error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="space-y-3">
          {[1, 2, 3, 4].map(i => <SkeletonCard key={i} />)}
        </div>
      )}

      {/* Org rows */}
      {!loading && !error && (
        <>
          {filtered.length === 0 ? (
            <div className="rounded-xl border border-dashed border-border bg-card px-6 py-12 text-center">
              <Building2 className="mx-auto h-8 w-8 text-muted-foreground mb-3" />
              <p className="text-sm text-muted-foreground">
                {search ? `No organizations match "${search}".` : "No organizations found."}
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {filtered.map(org => (
                <OrgRow
                  key={org.id}
                  org={org}
                  workspaces={workspacesMap[org.id] ?? []}
                  licenseTier={licenseTiers[org.id] ?? "free"}
                  onOrgUpdated={handleOrgUpdated}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
