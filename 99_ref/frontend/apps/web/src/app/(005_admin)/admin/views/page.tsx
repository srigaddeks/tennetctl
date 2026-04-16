"use client"

import { useEffect, useState, useCallback } from "react"
import { Button } from "@kcontrol/ui"
import {
  Eye, RefreshCw, Plus, X, ShieldCheck, Search, Wrench, BarChart3,
  Building2, Layers, Globe, Shield, Lock, Pencil, Trash2, Check,
  GripVertical, AlertTriangle,
} from "lucide-react"
import {
  listViews, listRoleViewAssignments, assignViewToRole, revokeViewFromRole,
  createView, updateView, deleteView, addViewRoute, removeViewRoute,
} from "@/lib/api/views"
import { listRoles } from "@/lib/api/admin"
import type { PortalViewResponse, ViewRouteResponse } from "@/lib/types/views"
import type { RoleResponse } from "@/lib/types/admin"

// ── Constants ─────────────────────────────────────────────────────────────────

const ICON_OPTIONS = [
  "ShieldCheck", "Search", "Wrench", "BarChart3", "Building2",
  "Eye", "Layers", "Globe", "Shield", "Lock",
]

const ICON_MAP: Record<string, React.ReactNode> = {
  ShieldCheck: <ShieldCheck className="w-4 h-4" />,
  Search: <Search className="w-4 h-4" />,
  Wrench: <Wrench className="w-4 h-4" />,
  BarChart3: <BarChart3 className="w-4 h-4" />,
  Building2: <Building2 className="w-4 h-4" />,
  Eye: <Eye className="w-4 h-4" />,
  Layers: <Layers className="w-4 h-4" />,
  Globe: <Globe className="w-4 h-4" />,
  Shield: <Shield className="w-4 h-4" />,
  Lock: <Lock className="w-4 h-4" />,
}

const ROUTE_SUGGESTIONS = [
  "/*", "/dashboard", "/frameworks", "/controls", "/tests", "/risks",
  "/tasks", "/workspaces", "/sandbox", "/settings", "/feedback", "/policies",
]

type Tab = "details" | "routes" | "roles"

// ── Unified View Modal ────────────────────────────────────────────────────────

function ViewModal({
  initial,
  roles,
  assignments,
  onSave,
  onClose,
  onAssign,
  onRevoke,
}: {
  initial?: PortalViewResponse | null
  roles: RoleResponse[]
  assignments: Array<{ role_id: string; view_code: string }>
  onSave: (view: PortalViewResponse) => void
  onClose: () => void
  onAssign: (roleId: string, viewCode: string) => Promise<void>
  onRevoke: (roleId: string, viewCode: string) => Promise<void>
}) {
  const isEdit = !!initial
  const [tab, setTab] = useState<Tab>("details")

  // Details state
  const [code, setCode] = useState(initial?.code ?? "")
  const [codeEdited, setCodeEdited] = useState(isEdit)
  const [name, setName] = useState(initial?.name ?? "")
  const [description, setDescription] = useState(initial?.description ?? "")

  const toSnakeCase = (s: string) => s.toLowerCase().replace(/\s+/g, "_").replace(/[^a-z0-9_]/g, "").replace(/_+/g, "_").replace(/^_|_$/g, "")
  const handleNameChange = (v: string) => { setName(v); if (!codeEdited) setCode(toSnakeCase(v)) }
  const handleCodeChange = (v: string) => { setCode(v.toLowerCase().replace(/[^a-z0-9_]/g, "_")); setCodeEdited(true) }
  const [color, setColor] = useState(initial?.color ?? "#2878ff")
  const [icon, setIcon] = useState(initial?.icon ?? "Eye")
  const [sortOrder, setSortOrder] = useState(initial?.sort_order ?? 50)
  const [defaultRoute, setDefaultRoute] = useState(initial?.default_route ?? "/dashboard")
  const [isActive, setIsActive] = useState(initial?.is_active ?? true)
  const [saving, setSaving] = useState(false)
  const [detailError, setDetailError] = useState<string | null>(null)

  // Saved view (for routes/roles tab — only meaningful after creation or when editing)
  const [savedView, setSavedView] = useState<PortalViewResponse | null>(initial ?? null)

  // Routes state
  const [routePrefix, setRoutePrefix] = useState("")
  const [isReadOnly, setIsReadOnly] = useState(false)
  const [sidebarLabel, setSidebarLabel] = useState("")
  const [sidebarSection, setSidebarSection] = useState("")
  const [addingRoute, setAddingRoute] = useState(false)
  const [showAddRoute, setShowAddRoute] = useState(false)
  const [removingRoute, setRemovingRoute] = useState<string | null>(null)
  const [routeError, setRouteError] = useState<string | null>(null)

  // Roles state
  const [assigning, setAssigning] = useState<string | null>(null)
  const [revoking, setRevoking] = useState<string | null>(null)
  const [roleError, setRoleError] = useState<string | null>(null)

  const currentRoutes = savedView?.routes ?? []
  const assignedRoleIds = new Set(
    assignments.filter(a => a.view_code === (savedView?.code ?? "")).map(a => a.role_id)
  )
  const assignedRoles = roles.filter(r => assignedRoleIds.has(r.id))
  const availableRoles = roles.filter(r => !assignedRoleIds.has(r.id))

  const handleSaveDetails = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true); setDetailError(null)
    try {
      let result: PortalViewResponse
      if (isEdit) {
        result = await updateView(initial!.code, {
          name, description: description || null, color, icon,
          sort_order: sortOrder, is_active: isActive,
          default_route: defaultRoute || null,
        }) as PortalViewResponse
        result = { ...result, routes: savedView?.routes ?? initial!.routes }
      } else {
        result = await createView({
          code, name, description: description || null, color, icon,
          sort_order: sortOrder, default_route: defaultRoute || null,
        }) as PortalViewResponse
        result = { ...result, routes: [] }
      }
      setSavedView(result)
      onSave(result)
      if (!isEdit) setTab("routes") // after create, move to routes tab
    } catch (e) { setDetailError((e as Error).message) }
    finally { setSaving(false) }
  }

  const handleAddRoute = async () => {
    if (!savedView) return
    const prefix = routePrefix.startsWith("/") ? routePrefix : `/${routePrefix}`
    setAddingRoute(true); setRouteError(null)
    try {
      const route = await addViewRoute(savedView.code, {
        route_prefix: prefix,
        is_read_only: isReadOnly,
        sort_order: (currentRoutes.length + 1) * 10,
        sidebar_label: sidebarLabel || null,
        sidebar_section: sidebarSection || null,
        sidebar_icon: null,
      })
      const updated = { ...savedView, routes: [...currentRoutes.filter(r => r.route_prefix !== route.route_prefix), route] }
      setSavedView(updated)
      onSave(updated)
      setRoutePrefix(""); setSidebarLabel(""); setSidebarSection(""); setIsReadOnly(false)
      setShowAddRoute(false)
    } catch (e) { setRouteError((e as Error).message) }
    finally { setAddingRoute(false) }
  }

  const handleRemoveRoute = async (prefix: string) => {
    if (!savedView) return
    setRemovingRoute(prefix); setRouteError(null)
    try {
      await removeViewRoute(savedView.code, prefix)
      const updated = { ...savedView, routes: currentRoutes.filter(r => r.route_prefix !== prefix) }
      setSavedView(updated)
      onSave(updated)
    } catch (e) { setRouteError((e as Error).message) }
    finally { setRemovingRoute(null) }
  }

  const handleAssign = async (roleId: string) => {
    if (!savedView) return
    setAssigning(roleId); setRoleError(null)
    try { await onAssign(roleId, savedView.code) }
    catch (e) { setRoleError((e as Error).message) }
    finally { setAssigning(null) }
  }

  const handleRevoke = async (roleId: string) => {
    if (!savedView) return
    setRevoking(roleId); setRoleError(null)
    try { await onRevoke(roleId, savedView.code) }
    catch (e) { setRoleError((e as Error).message) }
    finally { setRevoking(null) }
  }

  const sortedRoutes = [...currentRoutes].sort((a, b) => a.sort_order - b.sort_order)
  const accentColor = color ?? "#888"

  const tabs: { id: Tab; label: string; disabled?: boolean }[] = [
    { id: "details", label: "Details" },
    { id: "routes", label: `Routes (${sortedRoutes.length})`, disabled: !savedView && !isEdit },
    { id: "roles", label: `Roles (${assignedRoles.length})`, disabled: !savedView && !isEdit },
  ]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="w-full max-w-xl max-h-[90vh] flex flex-col overflow-hidden rounded-xl border border-border bg-card shadow-lg">
        {/* Modal header */}
        <div className="flex items-center justify-between px-5 pt-5 pb-3 shrink-0 border-l-[3px]" style={{ borderLeftColor: accentColor }}>
          <div>
            <h2 className="font-semibold text-base">{isEdit ? `Edit: ${initial!.name}` : "Create Portal View"}</h2>
            {isEdit && <p className="text-[11px] text-muted-foreground font-mono">{initial!.code}</p>}
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground p-1 rounded hover:bg-muted">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-border px-5 shrink-0">
          {tabs.map(t => (
            <button
              key={t.id}
              onClick={() => !t.disabled && setTab(t.id)}
              disabled={t.disabled}
              className={`text-xs font-medium px-3 py-2 border-b-2 transition-colors ${
                tab === t.id
                  ? "border-primary text-primary"
                  : t.disabled
                    ? "border-transparent text-muted-foreground/40 cursor-not-allowed"
                    : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="flex-1 overflow-y-auto px-5 py-4">

          {/* ── DETAILS TAB ── */}
          {tab === "details" && (
            <form onSubmit={handleSaveDetails} className="space-y-4" id="details-form">
              {detailError && (
                <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">{detailError}</div>
              )}

              <div>
                <label className="text-xs text-muted-foreground mb-1 block">Name <span className="text-destructive">*</span></label>
                <input
                  className="w-full h-8 px-3 rounded border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                  value={name} onChange={e => handleNameChange(e.target.value)} required placeholder="e.g. Security Ops" autoFocus
                />
              </div>

              {!isEdit && (
                <div>
                  <label className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
                    Code <span className="text-destructive">*</span>
                    {!codeEdited && name && <span className="text-[10px] text-primary/70 font-normal">(auto-generated)</span>}
                  </label>
                  <input
                    className="w-full h-8 px-3 rounded border border-border bg-background text-sm font-mono focus:outline-none focus:ring-1 focus:ring-primary"
                    value={code}
                    onChange={e => handleCodeChange(e.target.value)}
                    placeholder="e.g. security_ops"
                    required
                  />
                  <p className="text-[10px] text-muted-foreground mt-1">Cannot be changed after creation.</p>
                </div>
              )}

              <div>
                <label className="text-xs text-muted-foreground mb-1 block">Default Landing Route</label>
                <input
                  className="w-full h-8 px-3 rounded border border-border bg-background text-sm font-mono focus:outline-none focus:ring-1 focus:ring-primary"
                  value={defaultRoute} onChange={e => setDefaultRoute(e.target.value)} placeholder="/dashboard"
                />
              </div>

              <div>
                <label className="text-xs text-muted-foreground mb-1 block">Description</label>
                <input
                  className="w-full h-8 px-3 rounded border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                  value={description} onChange={e => setDescription(e.target.value)} placeholder="What this view is for..."
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-muted-foreground mb-1 block">Accent Color</label>
                  <div className="flex items-center gap-2">
                    <input type="color" value={color} onChange={e => setColor(e.target.value)} className="h-8 w-10 rounded border border-border cursor-pointer" />
                    <input
                      className="flex-1 h-8 px-3 rounded border border-border bg-background text-sm font-mono focus:outline-none focus:ring-1 focus:ring-primary"
                      value={color} onChange={e => setColor(e.target.value)}
                    />
                  </div>
                </div>
                <div>
                  <label className="text-xs text-muted-foreground mb-1 block">Sort Order</label>
                  <input
                    type="number"
                    className="w-full h-8 px-3 rounded border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                    value={sortOrder} onChange={e => setSortOrder(Number(e.target.value))} min={0}
                  />
                </div>
              </div>

              <div>
                <label className="text-xs text-muted-foreground mb-1 block">Icon</label>
                <div className="flex flex-wrap gap-1.5">
                  {ICON_OPTIONS.map(ic => (
                    <button
                      key={ic} type="button" onClick={() => setIcon(ic)} title={ic}
                      style={icon === ic ? { borderColor: color, color } : {}}
                      className={`p-2 rounded-lg border transition-colors ${icon === ic ? "bg-primary/10" : "border-border hover:bg-muted/50"}`}
                    >
                      {ICON_MAP[ic] ?? <Eye className="w-4 h-4" />}
                    </button>
                  ))}
                </div>
              </div>

              {isEdit && (
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={isActive} onChange={e => setIsActive(e.target.checked)} className="rounded" />
                  <span className="text-sm">Active (visible to users)</span>
                </label>
              )}
            </form>
          )}

          {/* ── ROUTES TAB ── */}
          {tab === "routes" && savedView && (
            <div className="space-y-3">
              {routeError && <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">{routeError}</div>}

              {sortedRoutes.length === 0 && !showAddRoute && (
                <p className="text-sm text-muted-foreground italic py-2">No routes yet. Add one below.</p>
              )}

              {sortedRoutes.map(r => (
                <div key={r.route_prefix} className="group flex items-center gap-2 rounded-lg border border-border bg-muted/20 px-3 py-2">
                  <GripVertical className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
                  <span className="font-mono text-sm flex-1">{r.route_prefix}</span>
                  {r.sidebar_label && <span className="text-xs text-muted-foreground">{r.sidebar_label}</span>}
                  {r.sidebar_section && <span className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded">{r.sidebar_section}</span>}
                  {r.is_read_only && <span className="text-[10px] font-semibold text-amber-600 bg-amber-500/10 border border-amber-500/20 rounded px-1.5 py-0.5">RO</span>}
                  <button
                    onClick={() => handleRemoveRoute(r.route_prefix)}
                    disabled={removingRoute === r.route_prefix}
                    className="opacity-0 group-hover:opacity-100 p-1 text-muted-foreground hover:text-destructive transition-all rounded"
                  >
                    {removingRoute === r.route_prefix ? <RefreshCw className="w-3 h-3 animate-spin" /> : <X className="w-3 h-3" />}
                  </button>
                </div>
              ))}

              {showAddRoute ? (
                <div className="rounded-lg border border-border bg-muted/20 p-3 space-y-3">
                  <p className="text-xs font-medium text-muted-foreground">Add Route</p>
                  <div className="flex flex-wrap gap-1">
                    {ROUTE_SUGGESTIONS.filter(s => !currentRoutes.some(r => r.route_prefix === s)).map(s => (
                      <button key={s} type="button" onClick={() => setRoutePrefix(s)}
                        className={`text-[10px] font-mono px-2 py-0.5 rounded border transition-colors ${routePrefix === s ? "border-primary bg-primary/10 text-primary" : "border-border hover:bg-muted"}`}>
                        {s}
                      </button>
                    ))}
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-[10px] text-muted-foreground mb-1 block">Route prefix <span className="text-destructive">*</span></label>
                      <input
                        autoFocus
                        className="w-full h-8 px-2 rounded border border-border bg-background text-xs font-mono focus:outline-none focus:ring-1 focus:ring-primary"
                        placeholder="/route-prefix"
                        value={routePrefix}
                        onChange={e => setRoutePrefix(e.target.value)}
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-muted-foreground mb-1 block">Sidebar label</label>
                      <input
                        className="w-full h-8 px-2 rounded border border-border bg-background text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                        placeholder="e.g. Controls"
                        value={sidebarLabel}
                        onChange={e => setSidebarLabel(e.target.value)}
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-[10px] text-muted-foreground mb-1 block">Sidebar section</label>
                      <input
                        className="w-full h-8 px-2 rounded border border-border bg-background text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                        placeholder="e.g. Compliance"
                        value={sidebarSection}
                        onChange={e => setSidebarSection(e.target.value)}
                      />
                    </div>
                    <div className="flex items-end pb-1">
                      <label className="flex items-center gap-2 text-xs cursor-pointer">
                        <input type="checkbox" checked={isReadOnly} onChange={e => setIsReadOnly(e.target.checked)} />
                        Read-only
                      </label>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={handleAddRoute} disabled={addingRoute || !routePrefix.trim()}
                      className="flex items-center gap-1 text-xs px-3 py-1.5 rounded bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                    >
                      <Check className="w-3 h-3" /> {addingRoute ? "Adding…" : "Add Route"}
                    </button>
                    <button onClick={() => { setShowAddRoute(false); setRoutePrefix(""); setSidebarLabel(""); setSidebarSection(""); setIsReadOnly(false) }}
                      className="text-xs px-3 py-1.5 rounded border border-border hover:bg-muted">
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <button onClick={() => setShowAddRoute(true)}
                  className="flex items-center gap-1.5 text-sm text-primary hover:underline">
                  <Plus className="w-3.5 h-3.5" /> Add route
                </button>
              )}
            </div>
          )}

          {/* ── ROLES TAB ── */}
          {tab === "roles" && savedView && (
            <div className="space-y-4">
              {roleError && <div className="text-xs text-destructive bg-destructive/10 rounded-lg px-3 py-2">{roleError}</div>}

              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">Assigned Roles ({assignedRoles.length})</p>
                {assignedRoles.length === 0 ? (
                  <p className="text-sm text-muted-foreground italic">No roles assigned yet.</p>
                ) : (
                  <div className="flex flex-wrap gap-1.5">
                    {assignedRoles.map(role => (
                      <span
                        key={role.id}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border"
                        style={{ backgroundColor: `${accentColor}15`, borderColor: `${accentColor}40`, color: accentColor }}
                      >
                        {role.name}
                        <button type="button" onClick={() => handleRevoke(role.id)} disabled={revoking === role.id}
                          className="ml-0.5 opacity-60 hover:opacity-100 transition-opacity">
                          {revoking === role.id ? <RefreshCw className="w-3 h-3 animate-spin" /> : <X className="w-3 h-3" />}
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {availableRoles.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">Assign Role</p>
                  <div className="max-h-52 overflow-y-auto rounded-lg border border-border bg-muted/20 divide-y divide-border">
                    {availableRoles.map(role => (
                      <button key={role.id} type="button" onClick={() => handleAssign(role.id)} disabled={assigning === role.id}
                        className="w-full text-left px-3 py-2 text-sm hover:bg-accent transition-colors flex items-center justify-between gap-2">
                        <span>{role.name}</span>
                        <div className="flex items-center gap-2 shrink-0">
                          <span className="text-[10px] text-muted-foreground">{role.role_level_code}</span>
                          {assigning === role.id
                            ? <RefreshCw className="w-3 h-3 animate-spin text-primary" />
                            : <Plus className="w-3 h-3 text-primary opacity-0 group-hover:opacity-100" />}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {availableRoles.length === 0 && (
                <p className="text-xs text-muted-foreground italic">All roles are already assigned to this view.</p>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between gap-2 px-5 py-3 border-t border-border shrink-0">
          <div className="text-[10px] text-muted-foreground">
            {!isEdit && !savedView && "Save details first, then add routes and roles."}
            {savedView && tab !== "details" && (
              <span className="text-green-600">✓ Saved — configure {tab === "routes" ? "routes" : "roles"} above</span>
            )}
          </div>
          <div className="flex gap-2">
            <Button type="button" variant="ghost" onClick={onClose} className="h-8 px-4 text-sm">
              {savedView ? "Close" : "Cancel"}
            </Button>
            {tab === "details" && (
              <Button
                type="submit"
                form="details-form"
                disabled={saving}
                className="h-8 px-4 text-sm"
              >
                {saving
                  ? (isEdit ? "Saving…" : "Creating…")
                  : (isEdit ? "Save Changes" : "Create & Continue")}
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// ── View Card ─────────────────────────────────────────────────────────────────

function ViewCard({
  view,
  roles,
  assignments,
  onUpdate,
  onDelete,
  onAssign,
  onRevoke,
}: {
  view: PortalViewResponse
  roles: RoleResponse[]
  assignments: Array<{ role_id: string; view_code: string }>
  onUpdate: (v: PortalViewResponse) => void
  onDelete: (code: string) => void
  onAssign: (roleId: string, viewCode: string) => Promise<void>
  onRevoke: (roleId: string, viewCode: string) => Promise<void>
}) {
  const [editing, setEditing] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [opError, setOpError] = useState<string | null>(null)

  const assignedRoleIds = new Set(assignments.filter(a => a.view_code === view.code).map(a => a.role_id))
  const assignedRoles = roles.filter(r => assignedRoleIds.has(r.id))
  const color = view.color ?? "#888"
  const sorted = [...view.routes].sort((a, b) => a.sort_order - b.sort_order)

  const handleDelete = async () => {
    setDeleting(true); setOpError(null)
    try { await deleteView(view.code); onDelete(view.code) }
    catch (e) { setOpError((e as Error).message); setDeleting(false); setConfirmDelete(false) }
  }

  return (
    <>
      {editing && (
        <ViewModal
          initial={view}
          roles={roles}
          assignments={assignments}
          onSave={v => onUpdate(v)}
          onClose={() => setEditing(false)}
          onAssign={onAssign}
          onRevoke={onRevoke}
        />
      )}

      <div className={`rounded-xl border border-border bg-card overflow-hidden ${!view.is_active ? "opacity-60" : ""}`}>
        <div className="px-4 py-3 flex items-center gap-3 border-l-[3px]" style={{ borderLeftColor: color }}>
          <span style={{ color }}>{ICON_MAP[view.icon ?? ""] ?? <Eye className="w-4 h-4" />}</span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-sm font-semibold">{view.name}</h3>
              <span className="inline-flex items-center rounded border border-border bg-muted px-1.5 py-0.5 text-[10px] font-mono shrink-0">{view.code}</span>
              {!view.is_active && <span className="inline-flex items-center rounded border border-border bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">Inactive</span>}
              {view.default_route && (
                <span className="text-[10px] font-mono text-muted-foreground">→ {view.default_route}</span>
              )}
            </div>
            {view.description && <p className="text-[11px] text-muted-foreground mt-0.5 truncate">{view.description}</p>}
          </div>
          <div className="flex items-center gap-1 shrink-0">
            <button onClick={() => setEditing(true)} className="p-1.5 rounded hover:bg-muted text-muted-foreground hover:text-foreground transition-colors" title="Edit view">
              <Pencil className="w-3.5 h-3.5" />
            </button>
            {!confirmDelete ? (
              <button onClick={() => setConfirmDelete(true)} className="p-1.5 rounded hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors" title="Delete view">
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            ) : (
              <div className="flex items-center gap-1 text-xs">
                <button onClick={handleDelete} disabled={deleting}
                  className="px-2 py-0.5 rounded bg-destructive text-destructive-foreground text-[10px] hover:bg-destructive/90">
                  {deleting ? "…" : "Delete?"}
                </button>
                <button onClick={() => setConfirmDelete(false)} className="px-2 py-0.5 rounded border text-[10px] hover:bg-muted">No</button>
              </div>
            )}
          </div>
        </div>

        <div className="px-4 py-3 space-y-3">
          {opError && <p className="text-xs text-destructive">{opError}</p>}

          {/* Routes */}
          <div>
            <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
              Routes ({sorted.length})
            </p>
            <div className="flex flex-wrap gap-1">
              {sorted.length === 0 && <span className="text-xs text-muted-foreground italic">No routes</span>}
              {sorted.map(r => (
                <span key={r.route_prefix}
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-mono bg-muted border border-border">
                  {r.route_prefix}
                  {r.is_read_only && <span className="text-[8px] font-sans font-semibold text-muted-foreground">RO</span>}
                </span>
              ))}
            </div>
          </div>

          {/* Roles */}
          <div>
            <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
              Assigned Roles ({assignedRoles.length})
            </p>
            {assignedRoles.length === 0 ? (
              <p className="text-xs text-muted-foreground italic">No roles assigned</p>
            ) : (
              <div className="flex flex-wrap gap-1">
                {assignedRoles.map(role => (
                  <span key={role.id}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium border"
                    style={{ backgroundColor: `${color}10`, borderColor: `${color}30`, color }}
                  >
                    {role.name}
                  </span>
                ))}
              </div>
            )}
          </div>

          <button
            onClick={() => setEditing(true)}
            className="text-[10px] text-primary hover:underline flex items-center gap-1"
          >
            <Pencil className="w-3 h-3" /> Edit routes & roles
          </button>
        </div>
      </div>
    </>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function ViewsAdminPage() {
  const [views, setViews] = useState<PortalViewResponse[]>([])
  const [roles, setRoles] = useState<RoleResponse[]>([])
  const [assignments, setAssignments] = useState<Array<{ role_id: string; view_code: string }>>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreate, setShowCreate] = useState(false)

  const load = useCallback(async () => {
    setLoading(true); setError(null)
    try {
      const [viewRes, roleRes, assignRes] = await Promise.all([
        listViews(), listRoles(), listRoleViewAssignments(),
      ])
      setViews(viewRes.views)
      setRoles(roleRes.roles)
      setAssignments(assignRes.assignments)
    } catch (e) { setError((e as Error).message) }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const handleUpdate = useCallback((updated: PortalViewResponse) => {
    setViews(prev => prev.map(v => v.code === updated.code ? updated : v))
  }, [])

  const handleCreated = useCallback((created: PortalViewResponse) => {
    setViews(prev => {
      const exists = prev.some(v => v.code === created.code)
      return exists ? prev.map(v => v.code === created.code ? created : v) : [...prev, created]
    })
  }, [])

  const handleDelete = useCallback((code: string) => {
    setViews(prev => prev.filter(v => v.code !== code))
  }, [])

  const handleAssign = useCallback(async (roleId: string, viewCode: string) => {
    await assignViewToRole(roleId, viewCode)
    setAssignments(prev => [...prev, { role_id: roleId, view_code: viewCode }])
  }, [])

  const handleRevoke = useCallback(async (roleId: string, viewCode: string) => {
    await revokeViewFromRole(roleId, viewCode)
    setAssignments(prev => prev.filter(a => !(a.role_id === roleId && a.view_code === viewCode)))
  }, [])

  const sorted = [...views].sort((a, b) => a.sort_order - b.sort_order)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight font-secondary">Portal Views</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Manage role-based portal views. Assign views to roles — users see all views from their roles.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={load} title="Refresh">
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          </Button>
          <Button size="sm" className="h-8 px-3" onClick={() => setShowCreate(true)}>
            <Plus className="w-3.5 h-3.5 mr-1" /> New View
          </Button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-destructive/20 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertTriangle className="w-4 h-4 shrink-0" /> {error}
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5].map(i => <div key={i} className="h-48 rounded-xl bg-muted animate-pulse" />)}
        </div>
      ) : (
        <>
          {sorted.length === 0 && (
            <div className="text-center py-12 text-muted-foreground text-sm">
              No portal views yet. Create one to get started.
            </div>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {sorted.map(view => (
              <ViewCard
                key={view.code}
                view={view}
                roles={roles}
                assignments={assignments}
                onUpdate={handleUpdate}
                onDelete={handleDelete}
                onAssign={handleAssign}
                onRevoke={handleRevoke}
              />
            ))}
          </div>
        </>
      )}

      {showCreate && (
        <ViewModal
          roles={roles}
          assignments={assignments}
          onSave={handleCreated}
          onClose={() => setShowCreate(false)}
          onAssign={handleAssign}
          onRevoke={handleRevoke}
        />
      )}
    </div>
  )
}
