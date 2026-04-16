"use client"

import { useEffect, useState, useCallback } from "react"
import { Button, Input, Label, Separator, Dialog, DialogContent, DialogHeader, DialogFooter, DialogTitle, DialogDescription } from "@kcontrol/ui"
import { Crown, Plus, Pencil, Check, X, Building2, Users, FolderOpen, Layers, Infinity, ChevronDown, ChevronRight, Zap, Star, Shield, Wrench, Package, Gift, Search } from "lucide-react"
import {
  listLicenseProfiles, createLicenseProfile, updateLicenseProfile,
  setLicenseProfileSetting, deleteLicenseProfileSetting,
} from "@/lib/api/admin"
import type { LicenseProfileResponse, CreateLicenseProfileRequest, UpdateLicenseProfileRequest } from "@/lib/types/admin"

// ─────────────────────────────────────────────────────────────────────────────
// Tier metadata
// ─────────────────────────────────────────────────────────────────────────────

const TIER_META: Record<string, {
  label: string; icon: typeof Crown
  color: string; numColor: string; bg: string; border: string; borderL: string
  description: string; order: number
}> = {
  free:       { label: "Free",       icon: Gift,    color: "text-slate-500",   numColor: "text-slate-600",   bg: "bg-slate-500/10",   border: "border-slate-500/20",   borderL: "border-l-slate-500",   description: "Basic access, resource limits apply.",          order: 0 },
  partner:    { label: "Partner",    icon: Package, color: "text-teal-500",    numColor: "text-teal-600",    bg: "bg-teal-500/10",    border: "border-teal-500/20",    borderL: "border-l-teal-500",    description: "Partner or reseller organizations.",            order: 1 },
  pro_trial:  { label: "Pro Trial",  icon: Zap,     color: "text-amber-500",   numColor: "text-amber-600",   bg: "bg-amber-500/10",   border: "border-amber-500/20",   borderL: "border-l-amber-500",   description: "Temporary pro access, manually managed.",       order: 2 },
  pro:        { label: "Pro",        icon: Star,    color: "text-blue-500",    numColor: "text-blue-600",    bg: "bg-blue-500/10",    border: "border-blue-500/20",    borderL: "border-l-blue-500",    description: "Full features, higher limits.",                 order: 3 },
  enterprise: { label: "Enterprise", icon: Shield,  color: "text-purple-500",  numColor: "text-purple-600",  bg: "bg-purple-500/10",  border: "border-purple-500/20",  borderL: "border-l-purple-500",  description: "Enterprise tier with custom entitlements.",     order: 4 },
  internal:   { label: "Internal",   icon: Wrench,  color: "text-red-500",     numColor: "text-red-600",     bg: "bg-red-500/10",     border: "border-red-500/20",     borderL: "border-l-red-500",     description: "Kreesalis internal orgs — no limits enforced.", order: 5 },
}

const SETTING_META: Record<string, { label: string; icon: typeof Users; placeholder: string; tip: string }> = {
  max_users:      { label: "Max Users",      icon: Users,      placeholder: "e.g. 50", tip: "Maximum users allowed in this org" },
  max_workspaces: { label: "Max Workspaces", icon: FolderOpen, placeholder: "e.g. 20", tip: "Maximum workspaces allowed" },
  max_frameworks: { label: "Max Frameworks", icon: Layers,     placeholder: "e.g. 10", tip: "Maximum compliance frameworks" },
}

const ALL_SETTING_KEYS = Object.keys(SETTING_META)
const TIERS_ORDERED = Object.entries(TIER_META).sort((a, b) => a[1].order - b[1].order).map(([t]) => t)

// ─────────────────────────────────────────────────────────────────────────────
// Slugify helper — spaces → hyphens, strip non-alphanum-hyphens
// ─────────────────────────────────────────────────────────────────────────────

function slugify(s: string): string {
  return s.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "").replace(/-+/g, "-").replace(/^-|-$/g, "")
}

// ─────────────────────────────────────────────────────────────────────────────
// Inline setting cell — click to edit, enter to save
// ─────────────────────────────────────────────────────────────────────────────

function SettingCell({ profileCode, settingKey, value, onSaved }: {
  profileCode: string; settingKey: string; value: string | undefined; onSaved: () => void
}) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState("")
  const [saving, setSaving] = useState(false)

  function startEdit() { setDraft(value ?? ""); setEditing(true) }

  async function save() {
    if (draft.trim() === (value ?? "")) { setEditing(false); return }
    setSaving(true)
    try {
      if (draft.trim() === "") {
        await deleteLicenseProfileSetting(profileCode, settingKey).catch(() => {})
      } else {
        await setLicenseProfileSetting(profileCode, settingKey, draft.trim())
      }
      onSaved()
    } catch { /* ignore */ }
    finally { setSaving(false); setEditing(false) }
  }

  if (editing) {
    return (
      <div className="flex items-center gap-1">
        <Input value={draft} onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") save(); if (e.key === "Escape") setEditing(false) }}
          placeholder="blank = no limit" className="h-6 w-24 px-2 text-xs font-mono" autoFocus />
        <button type="button" onClick={save} disabled={saving} className="text-emerald-500 hover:text-emerald-400 transition-colors">
          <Check className="h-3.5 w-3.5" />
        </button>
        <button type="button" onClick={() => setEditing(false)} className="text-muted-foreground/50 hover:text-muted-foreground transition-colors">
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
    )
  }

  return (
    <button type="button" onClick={startEdit} title="Click to edit"
      className="group/cell flex items-center gap-1 text-xs tabular-nums hover:text-foreground transition-colors min-w-[56px] justify-center">
      {value
        ? <span className="font-semibold text-foreground">{value}</span>
        : <span className="text-muted-foreground/30 flex items-center gap-0.5"><Infinity className="h-3 w-3" /></span>
      }
      <Pencil className="h-2.5 w-2.5 opacity-0 group-hover/cell:opacity-30 transition-opacity shrink-0" />
    </button>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Profile row
// ─────────────────────────────────────────────────────────────────────────────

function ProfileRow({ profile, tierMeta, onReload }: {
  profile: LicenseProfileResponse
  tierMeta: typeof TIER_META[string]
  onReload: () => void
}) {
  const [editingName, setEditingName] = useState(false)
  const [nameDraft, setNameDraft] = useState("")
  const [descDraft, setDescDraft] = useState("")
  const [saving, setSaving] = useState(false)
  const TierIcon = tierMeta.icon
  const settingMap = Object.fromEntries(profile.settings.map((s) => [s.key, s.value]))

  async function saveName() {
    setSaving(true)
    try {
      await updateLicenseProfile(profile.code, { name: nameDraft.trim(), description: descDraft.trim() } as UpdateLicenseProfileRequest)
      onReload()
    } catch { /* ignore */ }
    finally { setSaving(false); setEditingName(false) }
  }

  return (
    <div className={`flex items-center gap-4 px-4 py-3 border-b border-border/20 last:border-b-0 border-l-[3px] ${tierMeta.borderL} hover:bg-accent/10 transition-colors group`}>
      <div className={`shrink-0 rounded-lg p-1.5 ${tierMeta.bg}`}>
        <TierIcon className={`h-3.5 w-3.5 ${tierMeta.color}`} />
      </div>

      {/* Name + description */}
      <div className="flex-1 min-w-0">
        {editingName ? (
          <div className="flex items-center gap-2 flex-wrap">
            <Input value={nameDraft} onChange={(e) => setNameDraft(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") saveName(); if (e.key === "Escape") setEditingName(false) }}
              className="h-7 text-sm w-40" autoFocus />
            <Input value={descDraft} onChange={(e) => setDescDraft(e.target.value)}
              placeholder="Description" className="h-7 text-xs w-52" />
            <button type="button" onClick={saveName} disabled={saving} className="text-emerald-500 hover:text-emerald-400"><Check className="h-3.5 w-3.5" /></button>
            <button type="button" onClick={() => setEditingName(false)} className="text-muted-foreground/50 hover:text-muted-foreground"><X className="h-3.5 w-3.5" /></button>
          </div>
        ) : (
          <>
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-foreground">{profile.name}</span>
              <code className="text-[10px] font-mono text-muted-foreground/25 hidden sm:inline">{profile.code}</code>
              {profile.description && <span className="text-xs text-muted-foreground/50 truncate hidden md:inline">— {profile.description}</span>}
            </div>
            <div className="flex items-center gap-1 mt-0.5">
              <Building2 className="h-3 w-3 text-muted-foreground/30" />
              <span className="text-[11px] text-muted-foreground/40">
                {profile.org_count > 0 ? `${profile.org_count} org${profile.org_count !== 1 ? "s" : ""}` : "No orgs assigned"}
              </span>
            </div>
          </>
        )}
      </div>

      {/* Limit cells */}
      <div className="flex items-center gap-6 shrink-0">
        {ALL_SETTING_KEYS.map((key) => (
          <SettingCell key={key} profileCode={profile.code} settingKey={key} value={settingMap[key]} onSaved={onReload} />
        ))}
      </div>

      {/* Edit button */}
      {!editingName && (
        <button type="button"
          onClick={() => { setNameDraft(profile.name); setDescDraft(profile.description ?? ""); setEditingName(true) }}
          title="Edit name/description"
          className="shrink-0 rounded-md p-1.5 text-muted-foreground/20 hover:text-foreground hover:bg-accent transition-all opacity-0 group-hover:opacity-100">
          <Pencil className="h-3 w-3" />
        </button>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Tier section
// ─────────────────────────────────────────────────────────────────────────────

function TierSection({ tier, profiles, onReload, onAddProfile }: {
  tier: string; profiles: LicenseProfileResponse[]; onReload: () => void; onAddProfile: (tier: string) => void
}) {
  const [open, setOpen] = useState(true)
  const meta = TIER_META[tier] ?? { label: tier, icon: Crown, color: "text-muted-foreground", numColor: "text-muted-foreground", bg: "bg-muted/30", border: "border-border", borderL: "border-l-border", description: "", order: 99 }
  const TierIcon = meta.icon
  const totalOrgs = profiles.reduce((n, p) => n + (p.org_count ?? 0), 0)

  return (
    <div>
      <button type="button" onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-2.5 px-2 py-2.5 rounded-lg hover:bg-accent/30 transition-colors text-left">
        <div className={`rounded-lg p-1.5 ${meta.bg} shrink-0`}>
          <TierIcon className={`h-3.5 w-3.5 ${meta.color}`} />
        </div>
        <span className="text-sm font-semibold text-foreground">{meta.label}</span>
        <span className="text-xs text-muted-foreground/50 hidden sm:inline">— {meta.description}</span>
        <div className="ml-auto flex items-center gap-3 text-xs text-muted-foreground/40 shrink-0">
          <span>{profiles.length} profile{profiles.length !== 1 ? "s" : ""}</span>
          {totalOrgs > 0 && <span className="flex items-center gap-0.5"><Building2 className="h-3 w-3" />{totalOrgs}</span>}
        </div>
        {open ? <ChevronDown className="h-3.5 w-3.5 text-muted-foreground/30 shrink-0" /> : <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/30 shrink-0" />}
      </button>

      {open && (
        <div className="ml-4 mb-3 space-y-1">
          <div className="rounded-xl border border-border/40 bg-card/50 overflow-hidden">
            {/* Column headers */}
            <div className="flex items-center gap-4 px-4 py-1.5 border-b border-border/30 bg-muted/20">
              <div className="flex-1 text-[10px] font-medium text-muted-foreground/40 uppercase tracking-wider">Profile</div>
              <div className="flex items-center gap-6 shrink-0">
                {ALL_SETTING_KEYS.map((key) => {
                  const m = SETTING_META[key]
                  const Icon = m.icon
                  return (
                    <div key={key} title={m.tip} className="flex items-center gap-1 text-[10px] font-medium text-muted-foreground/40 uppercase tracking-wider min-w-[56px] justify-center">
                      <Icon className="h-2.5 w-2.5" />{m.label}
                    </div>
                  )
                })}
              </div>
              <div className="w-6 shrink-0" />
            </div>

            {profiles.map((p) => (
              <ProfileRow key={p.code} profile={p} tierMeta={meta} onReload={onReload} />
            ))}

            {profiles.length === 0 && (
              <div className="px-4 py-5 text-center text-xs text-muted-foreground/30">
                No profiles yet for this tier.
              </div>
            )}
          </div>

          <button type="button" onClick={() => onAddProfile(tier)}
            className="flex items-center gap-1.5 text-xs text-muted-foreground/40 hover:text-primary transition-colors px-2 py-0.5">
            <Plus className="h-3 w-3" /> Add {meta.label} profile
          </button>
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Create profile dialog
// ─────────────────────────────────────────────────────────────────────────────

function CreateProfileDialog({ defaultTier, onClose, onCreate }: {
  defaultTier: string | null; onClose: () => void; onCreate: (p: CreateLicenseProfileRequest) => Promise<void>
}) {
  const [code, setCode] = useState("")
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [tier, setTier] = useState(defaultTier ?? "free")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [codeEdited, setCodeEdited] = useState(false)

  const handleNameChange = (v: string) => { setName(v); if (!codeEdited) setCode(slugify(v)) }
  const handleCodeChange = (v: string) => { setCode(v.toLowerCase().replace(/[^a-z0-9-]/g, "-").replace(/-+/g, "-")); setCodeEdited(true) }

  useEffect(() => {
    if (defaultTier !== null) {
      setTier(defaultTier); setCode(""); setName(""); setDescription("")
      setSaving(false); setError(null); setCodeEdited(false)
    }
  }, [defaultTier])

  async function create() {
    if (!name.trim()) { setError("Name is required."); return }
    const finalCode = code.trim() || slugify(name.trim())
    if (!finalCode) { setError("Could not generate a code from the name."); return }
    setSaving(true); setError(null)
    try { await onCreate({ code: finalCode, name: name.trim(), description: description.trim(), tier }) }
    catch (e) { setError(e instanceof Error ? e.message : "Failed"); setSaving(false) }
  }

  return (
    <Dialog open={defaultTier !== null} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-primary/10 p-2.5"><Crown className="h-4 w-4 text-primary" /></div>
            <div>
              <DialogTitle>New License Profile</DialogTitle>
              <DialogDescription>Sets default resource limits for orgs on this tier.</DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />

        <div className="space-y-4">
          {/* Name — primary field */}
          <div className="space-y-1.5">
            <Label className="text-xs">Name</Label>
            <Input value={name} onChange={(e) => handleNameChange(e.target.value)}
              placeholder="Pro Startup" className="h-9 text-sm" autoFocus />
          </div>

          {/* Code — secondary, auto-generated */}
          <div className="space-y-1.5">
            <Label className="text-xs flex items-center gap-1.5">
              Code
              {!codeEdited && name
                ? <span className="text-[10px] text-primary/70 font-normal">(auto-generated)</span>
                : <span className="text-[10px] text-muted-foreground font-normal">(slug)</span>
              }
            </Label>
            <Input value={code} onChange={(e) => handleCodeChange(e.target.value)}
              placeholder={name ? slugify(name) || "my-profile" : "my-profile"}
              className="h-8 text-xs font-mono text-muted-foreground" />
            <p className="text-[10px] text-muted-foreground">Immutable after creation. Must be unique.</p>
          </div>

          {/* Description */}
          <div className="space-y-1.5">
            <Label className="text-xs">Description <span className="text-muted-foreground font-normal">(optional)</span></Label>
            <Input value={description} onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description" className="h-9 text-sm" />
          </div>

          {/* Tier picker */}
          <div className="space-y-1.5">
            <Label className="text-xs">Tier</Label>
            <div className="flex flex-wrap gap-1.5">
              {TIERS_ORDERED.map((value) => {
                const meta = TIER_META[value]
                const Icon = meta.icon
                return (
                  <button key={value} type="button" onClick={() => setTier(value)}
                    className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-all ${
                      tier === value
                        ? `${meta.bg} ${meta.border} ${meta.color}`
                        : "border-border bg-card text-muted-foreground hover:border-foreground/20"
                    }`}>
                    <Icon className="h-3 w-3" />{meta.label}
                  </button>
                )
              })}
            </div>
          </div>
        </div>

        {error && (
          <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500 mt-2">{error}</p>
        )}

        <DialogFooter className="mt-3 gap-2 sm:gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={saving}>Cancel</Button>
          <Button size="sm" onClick={create} disabled={saving}>
            {saving
              ? <span className="flex items-center gap-1.5"><span className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />Creating…</span>
              : "Create Profile"
            }
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Main page
// ─────────────────────────────────────────────────────────────────────────────

export default function LicenseProfilesPage() {
  const [profiles, setProfiles] = useState<LicenseProfileResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [createForTier, setCreateForTier] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [tierFilter, setTierFilter] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true); setError(null)
    try { const data = await listLicenseProfiles(); setProfiles(data.profiles) }
    catch (e) { setError(e instanceof Error ? e.message : "Failed to load") }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  async function handleCreate(payload: CreateLicenseProfileRequest) {
    await createLicenseProfile(payload)
    setCreateForTier(null)
    await load()
  }

  // Derived stats
  const totalOrgs = profiles.reduce((n, p) => n + (p.org_count ?? 0), 0)
  const byTierCount = Object.fromEntries(TIERS_ORDERED.map((t) => [t, profiles.filter((p) => p.tier === t).length]))

  // Filter
  const filtered = profiles.filter((p) => {
    const matchSearch = !search || p.name.toLowerCase().includes(search.toLowerCase()) || p.code.toLowerCase().includes(search.toLowerCase())
    const matchTier = !tierFilter || p.tier === tierFilter
    return matchSearch && matchTier
  })
  const filteredByTier = Object.fromEntries(TIERS_ORDERED.map((t) => [t, filtered.filter((p) => p.tier === t)]))

  // KPI cards
  const kpiCards = [
    { label: "Total Profiles", value: profiles.length, icon: Crown, borderCls: "border-l-amber-500", numCls: "text-amber-600" },
    { label: "Orgs Assigned", value: totalOrgs, icon: Building2, borderCls: "border-l-blue-500", numCls: "text-blue-600" },
    { label: "Tiers Active", value: TIERS_ORDERED.filter((t) => byTierCount[t] > 0).length, icon: Layers, borderCls: "border-l-purple-500", numCls: "text-purple-600" },
    { label: "Unassigned", value: profiles.filter((p) => p.org_count === 0).length, icon: FolderOpen, borderCls: "border-l-slate-500", numCls: "text-slate-600" },
  ]

  return (
    <div className="max-w-6xl space-y-5">
      <CreateProfileDialog defaultTier={createForTier} onClose={() => setCreateForTier(null)} onCreate={handleCreate} />

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="rounded-2xl bg-primary/10 p-3.5 shrink-0">
            <Crown className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-foreground tracking-tight">License Profiles</h2>
            <p className="text-sm text-muted-foreground mt-0.5">
              Define resource limits per tier. Each tier can have multiple profiles — orgs inherit their assigned profile&apos;s limits.
            </p>
          </div>
        </div>
        <Button size="sm" onClick={() => setCreateForTier("free")} className="gap-1.5 shadow-sm shrink-0">
          <Plus className="h-3.5 w-3.5" />New Profile
        </Button>
      </div>

      {/* KPI stat cards */}
      {!loading && !error && (
        <div className="flex gap-3 flex-wrap">
          {kpiCards.map((s) => (
            <div key={s.label}
              className={`relative flex items-center gap-3 rounded-xl border border-l-[3px] ${s.borderCls} bg-card px-4 py-3`}>
              <div className="shrink-0 rounded-lg p-2 bg-muted">
                <s.icon className="h-3.5 w-3.5 text-muted-foreground" />
              </div>
              <div>
                <span className={`text-2xl font-bold tabular-nums leading-none ${s.numCls} block`}>{s.value}</span>
                <span className="text-[11px] text-muted-foreground mt-0.5 block truncate">{s.label}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Filter bar */}
      {!loading && !error && (
        <div className="rounded-xl border border-border bg-card px-4 py-3 flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[180px]">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground/40 pointer-events-none" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search profiles…"
              className="w-full h-8 rounded-lg border border-border bg-background pl-8 pr-3 text-xs outline-none focus:ring-1 focus:ring-ring placeholder:text-muted-foreground/40"
            />
          </div>

          {/* Tier filter chips */}
          <div className="flex items-center gap-1.5 flex-wrap">
            {TIERS_ORDERED.map((t) => {
              const meta = TIER_META[t]
              const Icon = meta.icon
              const count = byTierCount[t] ?? 0
              if (count === 0) return null
              const active = tierFilter === t
              return (
                <button key={t} type="button"
                  onClick={() => setTierFilter(active ? null : t)}
                  className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-[11px] font-medium transition-all ${
                    active
                      ? `${meta.bg} ${meta.border} ${meta.color}`
                      : "border-border bg-card text-muted-foreground hover:border-foreground/20"
                  }`}>
                  <Icon className="h-2.5 w-2.5" />
                  {meta.label}
                  <span className={`ml-0.5 ${active ? meta.color : "text-muted-foreground/50"}`}>{count}</span>
                  {active && <X className="h-2.5 w-2.5 ml-0.5 opacity-60" />}
                </button>
              )
            })}
          </div>

          {/* Active filter summary */}
          {(search || tierFilter) && (
            <button type="button" onClick={() => { setSearch(""); setTierFilter(null) }}
              className="ml-auto flex items-center gap-1 text-[11px] text-muted-foreground/50 hover:text-foreground transition-colors">
              <X className="h-3 w-3" />Clear
            </button>
          )}

          <span className="text-[11px] text-muted-foreground/40 italic shrink-0">
            Click any limit to edit — blank = ∞
          </span>
        </div>
      )}

      {/* Error / loading */}
      {error && <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-500">{error}</div>}
      {loading && <div className="space-y-3">{[1, 2, 3].map((i) => <div key={i} className="h-16 animate-pulse rounded-xl bg-muted" />)}</div>}

      {/* Tier sections */}
      {!loading && !error && (
        <div className="space-y-2">
          {TIERS_ORDERED.map((tier) => {
            const allForTier = profiles.filter((p) => p.tier === tier)
            if (tierFilter && tierFilter !== tier) return null
            if (tierFilter === null && allForTier.length === 0 && !search) return null
            return (
              <TierSection
                key={tier}
                tier={tier}
                profiles={filteredByTier[tier] ?? []}
                onReload={load}
                onAddProfile={setCreateForTier}
              />
            )
          })}
          {filtered.length === 0 && (
            <div className="rounded-xl border border-border bg-card px-4 py-8 text-center text-sm text-muted-foreground/40">
              No profiles match your filters.
            </div>
          )}
        </div>
      )}
    </div>
  )
}
