"use client"

import { useEffect, useState, useMemo, useCallback } from "react"
import {
  Button,
  Input,
  Label,
  Separator,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
} from "@kcontrol/ui"
import {
  Flag,
  Plus,
  X,
  ChevronDown,
  ChevronRight,
  FolderOpen,
  Folder,
  FolderPlus,
  AlertTriangle,
  Info,
  Pencil,
  Crown,
  Search,
  Globe,
  Building2,
  Package,
  Lock,
  Unlock,
  Eye,
  EyeOff,
  Settings2,
  Zap,
  Archive,
  Clock,
  XCircle,
} from "lucide-react"
import {
  listFeatureFlags,
  createFeatureFlag,
  createFeatureCategory,
  updateFeatureFlag,
  setEntitySetting,
  deleteEntitySetting,
  listPermissionActionTypes,
  addPermissionToFlag,
  removePermissionFromFlag,
} from "@/lib/api/admin"
import type {
  FeatureFlagListResponse,
  FeatureFlagResponse,
  FeatureCategoryResponse,
  CreateFeatureFlagRequest,
  UpdateFeatureFlagRequest,
} from "@/lib/types/admin"

// ─────────────────────────────────────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────────────────────────────────────

type OrgAccess = "hidden" | "locked" | "unlocked"

const SCOPE_META = {
  platform: { label: "Platform", icon: Globe },
  org:      { label: "Org",      icon: Building2 },
  product:  { label: "Product",  icon: Package },
} as const

const LIFECYCLE_META: Record<string, { label: string; icon: typeof Zap; color: string; bg: string }> = {
  planned:    { label: "Planned",    icon: Clock,     color: "text-blue-500",  bg: "bg-blue-500/10 border-blue-500/20" },
  active:     { label: "Active",     icon: Zap,       color: "text-emerald-500", bg: "bg-emerald-500/10 border-emerald-500/20" },
  deprecated: { label: "Deprecated", icon: Archive,   color: "text-amber-500", bg: "bg-amber-500/10 border-amber-500/20" },
  retired:    { label: "Retired",    icon: XCircle,   color: "text-muted-foreground", bg: "bg-muted/40 border-border" },
}

const ENV_META = {
  dev:     { label: "Dev",  field: "env_dev"     as const, color: "text-blue-600 dark:text-blue-400", bg: "bg-blue-500/15 border-blue-500/25", dot: "bg-blue-500" },
  staging: { label: "Stg",  field: "env_staging" as const, color: "text-amber-600 dark:text-amber-400", bg: "bg-amber-500/15 border-amber-500/25", dot: "bg-amber-500" },
  prod:    { label: "Prd",  field: "env_prod"    as const, color: "text-emerald-600 dark:text-emerald-400", bg: "bg-emerald-500/15 border-emerald-500/25", dot: "bg-emerald-500" },
} as const

const ACCESS_META: Record<OrgAccess, { label: string; icon: typeof Globe; color: string; bg: string; tip: string }> = {
  hidden:   { label: "Global Admin", icon: Globe,  color: "text-primary",     bg: "bg-primary/10 border-primary/20",           tip: "Super admins only. Not visible to org admins." },
  locked:   { label: "Org Viewed",   icon: Eye,    color: "text-amber-500",   bg: "bg-amber-500/10 border-amber-500/20",       tip: "Org admins can see this but cannot change it." },
  unlocked: { label: "Org Managed",  icon: Unlock, color: "text-emerald-500", bg: "bg-emerald-500/10 border-emerald-500/20",   tip: "Org admins can toggle this for their org." },
}

// ─────────────────────────────────────────────────────────────────────────────
// Reusable Tag
// ─────────────────────────────────────────────────────────────────────────────

function Tag({
  label, style, onClick, title, icon: Icon, active,
}: {
  label: string; style: string; onClick?: () => void; title?: string; icon?: typeof Globe; active?: boolean
}) {
  const ring = active ? " ring-2 ring-primary/40 ring-offset-1 ring-offset-background" : ""
  const cls = `inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium border whitespace-nowrap transition-all ${style}${ring}`
  if (onClick) {
    return (
      <button type="button" onClick={onClick} title={title} className={`${cls} cursor-pointer hover:shadow-sm hover:brightness-110`}>
        {Icon && <Icon className="h-3 w-3 shrink-0" />}{label}
      </button>
    )
  }
  return <span title={title} className={cls}>{Icon && <Icon className="h-3 w-3 shrink-0" />}{label}</span>
}

// ─────────────────────────────────────────────────────────────────────────────
// Confirm dialog
// ─────────────────────────────────────────────────────────────────────────────

interface ConfirmAction {
  title: string; body: string; detail: string
  variant: "info" | "warning" | "danger"; confirmLabel: string
  onConfirm: () => Promise<void>
}

function ConfirmDialog({ action, onClose }: { action: ConfirmAction | null; onClose: () => void }) {
  const [running, setRunning] = useState(false)
  if (!action) return null
  const colorsMap = {
    info:    { icon: Info,          iconColor: "text-primary",   bg: "bg-primary/10", border: "border-primary/30" },
    warning: { icon: AlertTriangle, iconColor: "text-amber-500", bg: "bg-amber-500/10", border: "border-amber-500/30" },
    danger:  { icon: AlertTriangle, iconColor: "text-red-500",   bg: "bg-red-500/10", border: "border-red-500/30" },
  }
  const colors = colorsMap[action.variant] ?? colorsMap.info
  const Icon = colors.icon
  async function confirm() {
    setRunning(true)
    try { await action?.onConfirm() } catch { /* reload will show */ }
    setRunning(false); onClose()
  }
  return (
    <Dialog open onOpenChange={(o) => { if (!o) onClose() }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-3 mb-1">
            <div className={`rounded-xl p-2.5 ${colors.bg}`}><Icon className={`h-5 w-5 ${colors.iconColor}`} /></div>
            <DialogTitle>{action.title}</DialogTitle>
          </div>
          <DialogDescription>{action.body}</DialogDescription>
        </DialogHeader>
        <div className={`rounded-xl border ${colors.border} ${colors.bg} px-4 py-3`}>
          <p className="text-sm font-medium text-foreground">{action.detail}</p>
        </div>
        <DialogFooter className="gap-2 mt-2 sm:gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={running}>Cancel</Button>
          <Button size="sm" onClick={confirm} disabled={running}
            className={action.variant === "danger" ? "bg-red-500 hover:bg-red-600 text-white" : ""}>
            {running ? "Working…" : action.confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Inline picker — shows options on click, saves on select
// ─────────────────────────────────────────────────────────────────────────────

function InlinePicker<T extends string>({
  current, options, onPick, disabled,
}: {
  current: T
  options: { value: T; label: string; icon?: typeof Globe; style: string; tip?: string }[]
  onPick: (value: T) => void
  disabled?: boolean
}) {
  const [open, setOpen] = useState(false)
  const cur = options.find((o) => o.value === current) ?? options[0]

  if (open && !disabled) {
    return (
      <div className="flex items-center gap-1">
        {options.map((o) => (
          <Tag key={o.value} label={o.label} icon={o.icon} style={o.style}
            active={o.value === current} title={o.tip}
            onClick={() => { setOpen(false); onPick(o.value) }} />
        ))}
        <button type="button" onClick={() => setOpen(false)}
          className="ml-0.5 text-muted-foreground/50 hover:text-foreground transition-colors">
          <X className="h-3 w-3" />
        </button>
      </div>
    )
  }

  return (
    <Tag label={cur.label} icon={cur.icon} style={cur.style}
      title={`${cur.tip ?? cur.label} — click to change`}
      onClick={() => !disabled && setOpen(true)} />
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Environment tags — show enabled envs, click to expand picker
// ─────────────────────────────────────────────────────────────────────────────

function EnvTags({ flag, onToggle }: {
  flag: FeatureFlagResponse
  onToggle: (flag: FeatureFlagResponse, env: "dev" | "staging" | "prod") => void
}) {
  const [expanded, setExpanded] = useState(false)

  if (expanded) {
    return (
      <div className="flex items-center gap-1">
        {(["dev", "staging", "prod"] as const).map((env) => {
          const meta = ENV_META[env]
          const isOn = flag[meta.field]
          return (
            <button key={env} type="button"
              onClick={() => { setExpanded(false); onToggle(flag, env) }}
              title={isOn ? `Disable in ${meta.label}` : `Enable in ${meta.label}`}
              className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium border transition-all cursor-pointer ${
                isOn ? meta.bg + " " + meta.color : "bg-muted/30 border-border/50 text-muted-foreground/40 hover:text-muted-foreground"
              }`}>
              <span className={`h-1.5 w-1.5 rounded-full ${isOn ? meta.dot : "bg-muted-foreground/30"}`} />
              {meta.label}
            </button>
          )
        })}
        <button type="button" onClick={() => setExpanded(false)}
          className="ml-0.5 text-muted-foreground/50 hover:text-foreground transition-colors">
          <X className="h-3 w-3" />
        </button>
      </div>
    )
  }

  // Collapsed: show enabled environments
  const enabled = (["dev", "staging", "prod"] as const).filter((e) => flag[ENV_META[e].field])

  if (enabled.length === 0) {
    return (
      <button type="button" onClick={() => setExpanded(true)}
        title="Not deployed. Click to enable in an environment."
        className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium border bg-muted/30 border-border/50 text-muted-foreground/40 cursor-pointer hover:text-muted-foreground hover:border-border transition-all">
        <EyeOff className="h-3 w-3" /> None
      </button>
    )
  }

  // Show only the highest environment reached
  const highest = enabled[enabled.length - 1]
  const meta = ENV_META[highest]
  const tip = highest === "prod" ? "Enabled in Dev + Stg + Prd — click to change"
    : highest === "staging" ? "Enabled in Dev + Stg — click to change"
    : "Enabled in Dev only — click to change"

  return (
    <button type="button" onClick={() => setExpanded(true)} title={tip}
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium border cursor-pointer transition-all hover:brightness-110 ${meta.bg} ${meta.color}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${meta.dot}`} />
      {meta.label}
    </button>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Access tag — drives feature_scope + org_visibility
// ─────────────────────────────────────────────────────────────────────────────

function AccessTag({ flag, onDone }: { flag: FeatureFlagResponse; onDone: () => void }) {
  const [saving, setSaving] = useState(false)

  const current: OrgAccess = flag.org_visibility === "unlocked" ? "unlocked"
    : flag.org_visibility === "locked" ? "locked" : "hidden"

  async function handlePick(next: OrgAccess) {
    if (next === current) return
    setSaving(true)
    try {
      if (next === "hidden") {
        await updateFeatureFlag(flag.code, { feature_scope: "platform" } as UpdateFeatureFlagRequest)
        await deleteEntitySetting("feature", flag.code, "org_visibility").catch(() => {})
      } else {
        await updateFeatureFlag(flag.code, { feature_scope: "org" } as UpdateFeatureFlagRequest)
        await setEntitySetting("feature", flag.code, "org_visibility", next)
      }
      onDone()
    } catch { /* swallow */ }
    finally { setSaving(false) }
  }

  const options = Object.entries(ACCESS_META).map(([value, meta]) => ({
    value: value as OrgAccess, label: meta.label, icon: meta.icon, style: meta.bg + " " + meta.color, tip: meta.tip,
  }))

  return (
    <div className={saving ? "opacity-40 pointer-events-none" : ""}>
      <InlinePicker current={current} options={options} onPick={handlePick} disabled={saving} />
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// License tag — set/clear required_license entity setting inline
// ─────────────────────────────────────────────────────────────────────────────

type LicenseTier = "none" | "free" | "pro_trial" | "pro" | "enterprise" | "internal"

const LICENSE_META: Record<LicenseTier, { label: string; style: string; tip: string }> = {
  none:       { label: "No min",    style: "bg-muted/40 border-border text-muted-foreground",                     tip: "No license requirement — available to all tiers." },
  free:       { label: "Free+",     style: "bg-gray-500/10 border-gray-500/20 text-gray-600 dark:text-gray-400",  tip: "Available on Free tier and above." },
  pro_trial:  { label: "Trial+",    style: "bg-blue-500/10 border-blue-500/20 text-blue-600 dark:text-blue-400",  tip: "Requires Pro Trial tier or above." },
  pro:        { label: "Pro+",      style: "bg-violet-500/10 border-violet-500/20 text-violet-600 dark:text-violet-400", tip: "Requires Pro tier or above." },
  enterprise: { label: "Enterprise",style: "bg-purple-500/10 border-purple-500/20 text-purple-600 dark:text-purple-400", tip: "Requires Enterprise tier." },
  internal:   { label: "Internal",  style: "bg-amber-500/10 border-amber-500/20 text-amber-600 dark:text-amber-400",   tip: "Internal use only." },
}

function LicenseTag({ flag, onDone }: { flag: FeatureFlagResponse; onDone: () => void }) {
  const [saving, setSaving] = useState(false)

  const current: LicenseTier = (flag.required_license as LicenseTier) ?? "none"

  async function handlePick(next: LicenseTier) {
    if (next === current) return
    setSaving(true)
    try {
      if (next === "none") {
        await deleteEntitySetting("feature", flag.code, "required_license").catch(() => {})
      } else {
        await setEntitySetting("feature", flag.code, "required_license", next)
      }
      onDone()
    } catch { /* swallow */ }
    finally { setSaving(false) }
  }

  const options = Object.entries(LICENSE_META).map(([value, meta]) => ({
    value: value as LicenseTier, label: meta.label, style: meta.style, tip: meta.tip,
  }))

  return (
    <div className={saving ? "opacity-40 pointer-events-none" : ""}>
      <InlinePicker current={current} options={options} onPick={handlePick} disabled={saving} />
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Lifecycle tag — click to cycle
// ─────────────────────────────────────────────────────────────────────────────

function LifecycleTag({ flag, onDone }: { flag: FeatureFlagResponse; onDone: () => void }) {
  const [saving, setSaving] = useState(false)

  async function handlePick(next: string) {
    if (next === flag.lifecycle_state) return
    setSaving(true)
    try {
      await updateFeatureFlag(flag.code, { lifecycle_state: next } as UpdateFeatureFlagRequest)
      onDone()
    } catch { /* swallow */ }
    finally { setSaving(false) }
  }

  const options = Object.entries(LIFECYCLE_META).map(([value, meta]) => ({
    value, label: meta.label, icon: meta.icon, style: meta.bg + " " + meta.color,
  }))

  return (
    <div className={saving ? "opacity-40 pointer-events-none" : ""}>
      <InlinePicker current={flag.lifecycle_state} options={options} onPick={handlePick} disabled={saving} />
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Inline permission chips — show existing perms, click + to add, × to remove
// ─────────────────────────────────────────────────────────────────────────────

const ALL_ACTION_CODES = ["view", "create", "update", "delete", "enable", "disable", "assign", "revoke", "execute", "promote"]

const ACTION_COLORS: Record<string, string> = {
  view:    "bg-sky-500/10 border-sky-500/20 text-sky-600 dark:text-sky-400",
  create:  "bg-emerald-500/10 border-emerald-500/20 text-emerald-600 dark:text-emerald-400",
  update:  "bg-amber-500/10 border-amber-500/20 text-amber-600 dark:text-amber-400",
  delete:  "bg-red-500/10 border-red-500/20 text-red-600 dark:text-red-400",
  enable:  "bg-teal-500/10 border-teal-500/20 text-teal-600 dark:text-teal-400",
  disable: "bg-orange-500/10 border-orange-500/20 text-orange-600 dark:text-orange-400",
  assign:  "bg-violet-500/10 border-violet-500/20 text-violet-600 dark:text-violet-400",
  revoke:  "bg-rose-500/10 border-rose-500/20 text-rose-600 dark:text-rose-400",
  execute: "bg-cyan-500/10 border-cyan-500/20 text-cyan-600 dark:text-cyan-400",
  promote: "bg-purple-500/10 border-purple-500/20 text-purple-600 dark:text-purple-400",
}

function PermissionChips({
  flag, onReload,
}: {
  flag: FeatureFlagResponse
  onReload: () => void
}) {
  const [adding, setAdding] = useState(false)
  const [busy, setBusy] = useState<string | null>(null)

  const existingActions = new Set(flag.permissions.map((p) => p.permission_action_code))
  const available = ALL_ACTION_CODES.filter((a) => !existingActions.has(a))

  async function handleRemove(actionCode: string) {
    setBusy(actionCode)
    try {
      await removePermissionFromFlag(flag.code, actionCode)
      onReload()
    } catch { /* swallow */ }
    finally { setBusy(null) }
  }

  async function handleAdd(actionCode: string) {
    setBusy(actionCode)
    setAdding(false)
    try {
      await addPermissionToFlag(flag.code, actionCode)
      onReload()
    } catch { /* swallow */ }
    finally { setBusy(null) }
  }

  return (
    <div className="flex items-center flex-wrap gap-1">
      {flag.permissions.map((p) => {
        const ac = p.permission_action_code
        const color = ACTION_COLORS[ac] ?? "bg-muted/40 border-border text-muted-foreground"
        const isBusy = busy === ac
        return (
          <span key={ac}
            className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium border transition-all ${color} ${isBusy ? "opacity-40" : ""}`}>
            {ac}
            <button type="button" onClick={() => handleRemove(ac)} disabled={isBusy}
              className="ml-0.5 rounded-full hover:bg-black/10 dark:hover:bg-white/10 p-0.5 transition-colors"
              title={`Remove ${ac} permission`}>
              <X className="h-2.5 w-2.5" />
            </button>
          </span>
        )
      })}

      {/* Add button */}
      {adding ? (
        <div className="flex items-center gap-1 flex-wrap">
          {available.map((ac) => {
            const color = ACTION_COLORS[ac] ?? "bg-muted/40 border-border text-muted-foreground"
            return (
              <button key={ac} type="button" onClick={() => handleAdd(ac)}
                className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium border border-dashed transition-all cursor-pointer hover:opacity-80 ${color}`}>
                <Plus className="h-2.5 w-2.5" />{ac}
              </button>
            )
          })}
          <button type="button" onClick={() => setAdding(false)}
            className="rounded-full p-0.5 text-muted-foreground/50 hover:text-foreground transition-colors">
            <X className="h-3 w-3" />
          </button>
        </div>
      ) : available.length > 0 ? (
        <button type="button" onClick={() => setAdding(true)}
          className="inline-flex items-center gap-0.5 rounded-full border border-dashed border-border/50 px-1.5 py-0.5 text-[10px] text-muted-foreground/40 hover:text-foreground hover:border-border transition-all"
          title="Add permission">
          <Plus className="h-2.5 w-2.5" />
        </button>
      ) : null}

      {flag.permissions.length === 0 && !adding && (
        <span className="text-[10px] text-muted-foreground/30 italic">no permissions</span>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Flag row
// ─────────────────────────────────────────────────────────────────────────────

function FlagRow({
  flag, onToggleEnv, onEdit, onReload,
}: {
  flag: FeatureFlagResponse
  onToggleEnv: (flag: FeatureFlagResponse, env: "dev" | "staging" | "prod") => void
  onEdit: (flag: FeatureFlagResponse) => void
  onReload: () => void
}) {
  const scope = SCOPE_META[flag.feature_scope as keyof typeof SCOPE_META] ?? SCOPE_META.platform
  const ScopeIcon = scope.icon

  // Border accent: scope-based for disabled flags, green when prod-enabled
  const borderCls = flag.env_prod
    ? "border-l-green-500"
    : flag.env_staging
    ? "border-l-amber-500"
    : flag.env_dev
    ? "border-l-blue-500"
    : flag.feature_scope === "org"
    ? "border-l-blue-500"
    : flag.feature_scope === "product"
    ? "border-l-violet-500"
    : "border-l-slate-400"

  return (
    <div className={`grid grid-cols-[auto_1fr_auto] items-start gap-x-3 gap-y-0.5 px-4 py-2.5 border-b border-l-[3px] ${borderCls} border-b-border/20 last:border-b-0 hover:bg-accent/10 transition-colors group`}>

      {/* Col 1: scope icon */}
      <div className="row-span-3 shrink-0 rounded-lg bg-muted/40 p-1.5 self-start mt-0.5" title={`${scope.label} scope`}>
        <ScopeIcon className="h-3.5 w-3.5 text-muted-foreground" />
      </div>

      {/* Row 1 col 2: name + code */}
      <div className="flex items-center gap-2 min-w-0">
        <span className="text-sm font-medium text-foreground truncate">{flag.name}</span>
        <code className="text-[10px] font-mono text-muted-foreground/25 hidden md:inline shrink-0">{flag.code}</code>
      </div>

      {/* Row 1 col 3: tags + edit */}
      <div className="flex items-center gap-1.5 shrink-0">
        <LifecycleTag flag={flag} onDone={onReload} />
        <span className="w-px h-3.5 bg-border/40" />
        <EnvTags flag={flag} onToggle={onToggleEnv} />
        <span className="w-px h-3.5 bg-border/40" />
        <AccessTag flag={flag} onDone={onReload} />
        <span className="w-px h-3.5 bg-border/40" />
        <LicenseTag flag={flag} onDone={onReload} />
        <button type="button" onClick={() => onEdit(flag)} title="Edit flag"
          className="ml-1 shrink-0 rounded-md p-1 text-muted-foreground/20 hover:text-foreground hover:bg-accent transition-all opacity-0 group-hover:opacity-100">
          <Pencil className="h-3 w-3" />
        </button>
      </div>

      {/* Row 2 col 2+3: description */}
      {flag.description && (
        <p className="col-span-2 text-xs text-muted-foreground/60 truncate -mt-0.5">{flag.description}</p>
      )}

      {/* Row 3 col 2+3: permissions */}
      <div className="col-span-2 mt-1">
        <PermissionChips flag={flag} onReload={onReload} />
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Category section
// ─────────────────────────────────────────────────────────────────────────────

function CategorySection({
  category, flags, onToggleEnv, onEdit, onReload,
}: {
  category: FeatureCategoryResponse | null
  flags: FeatureFlagResponse[]
  onToggleEnv: (flag: FeatureFlagResponse, env: "dev" | "staging" | "prod") => void
  onEdit: (flag: FeatureFlagResponse) => void
  onReload: () => void
}) {
  const [open, setOpen] = useState(true)
  const label = category?.name ?? "Uncategorized"
  const devOn = flags.filter((f) => f.env_dev).length
  const stagOn = flags.filter((f) => f.env_staging).length
  const prdOn = flags.filter((f) => f.env_prod).length

  return (
    <div>
      <button type="button" onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-2 px-2 py-2 rounded-lg hover:bg-accent/30 transition-colors text-left">
        {open
          ? <FolderOpen className="h-4 w-4 text-primary shrink-0" />
          : <Folder className="h-4 w-4 text-muted-foreground shrink-0" />}
        <span className="text-sm font-semibold text-foreground">{label}</span>
        {category?.description && (
          <span className="text-xs text-muted-foreground/60 hidden sm:inline">— {category.description}</span>
        )}
        <span className="ml-auto text-xs text-muted-foreground tabular-nums">{flags.length}</span>
        <span className="hidden sm:flex items-center gap-1.5 text-[10px] tabular-nums">
          <span className={devOn > 0 ? "text-blue-500 font-medium" : "text-muted-foreground/30"}>{devOn}d</span>
          <span className={stagOn > 0 ? "text-amber-500 font-medium" : "text-muted-foreground/30"}>{stagOn}s</span>
          <span className={prdOn > 0 ? "text-emerald-500 font-medium" : "text-muted-foreground/30"}>{prdOn}p</span>
        </span>
        {open ? <ChevronDown className="h-3.5 w-3.5 text-muted-foreground/50" /> : <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/50" />}
      </button>

      {open && (
        <div className="rounded-xl border border-border/40 bg-card/50 overflow-hidden ml-4 mb-3">
          {flags.map((flag) => (
            <FlagRow key={flag.code} flag={flag} onToggleEnv={onToggleEnv} onEdit={onEdit} onReload={onReload} />
          ))}
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Edit flag dialog
// ─────────────────────────────────────────────────────────────────────────────

function EditFlagDialog({
  flag, categories, onSave, onClose,
}: {
  flag: FeatureFlagResponse | null
  categories: FeatureCategoryResponse[]
  onSave: (code: string, payload: UpdateFeatureFlagRequest) => Promise<void>
  onClose: () => void
}) {
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [categoryCode, setCategoryCode] = useState("")
  const [featureScope, setFeatureScope] = useState("platform")
  const [lifecycleState, setLifecycleState] = useState("planned")
  const [selectedActions, setSelectedActions] = useState<Set<string>>(new Set())
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (flag) {
      setName(flag.name); setDescription(flag.description)
      setCategoryCode(flag.category_code); setFeatureScope(flag.feature_scope)
      setLifecycleState(flag.lifecycle_state); setError(null)
      setSelectedActions(new Set(flag.permissions.map((p) => p.permission_action_code)))
    }
  }, [flag])

  function toggleAction(ac: string) {
    setSelectedActions((prev) => {
      const next = new Set(prev)
      if (next.has(ac)) next.delete(ac); else next.add(ac)
      return next
    })
  }

  function applyPreset(actions: string[]) {
    setSelectedActions(new Set(actions))
  }

  if (!flag) return null

  function pill(current: string, value: string, setter: (v: string) => void, label?: string) {
    return (
      <button key={value} type="button" onClick={() => setter(value)}
        className={`rounded-full border px-3 py-1 text-xs font-medium transition-all ${
          current === value
            ? "border-primary bg-primary text-white"
            : "border-border bg-card text-muted-foreground hover:border-primary/50 hover:text-foreground"
        }`}>
        {label ?? value}
      </button>
    )
  }

  async function save() {
    setSaving(true); setError(null)
    try {
      const permPayload = Array.from(selectedActions).map((ac) => ({
        permission_action_code: ac,
        name: `${name} ${ac.charAt(0).toUpperCase() + ac.slice(1)}`,
        description: `${ac} permission for ${name}`,
      }))
      await onSave(flag!.code, {
        name, description, category_code: categoryCode, feature_scope: featureScope,
        lifecycle_state: lifecycleState,
        access_mode: selectedActions.size > 0 ? "permissioned" : "authenticated",
        permissions: permPayload,
      })
      onClose()
    } catch (e) { setError(e instanceof Error ? e.message : "Failed to save"); setSaving(false) }
  }

  return (
    <Dialog open onOpenChange={(o) => { if (!o) onClose() }}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-primary/10 p-2.5"><Settings2 className="h-4 w-4 text-primary" /></div>
            <div>
              <DialogTitle>Edit Feature Flag</DialogTitle>
              <DialogDescription><code className="text-xs font-mono text-foreground/60">{flag.code}</code></DialogDescription>
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
            <div className="flex flex-wrap gap-1.5">
              {categories.map((c) => pill(categoryCode, c.code, setCategoryCode, c.name))}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label className="text-xs">Scope</Label>
              <div className="flex flex-wrap gap-1.5">
                {(["platform", "org", "product"] as const).map((s) =>
                  pill(featureScope, s, setFeatureScope, SCOPE_META[s].label)
                )}
              </div>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Lifecycle</Label>
              <div className="flex flex-wrap gap-1.5">
                {(["planned", "active", "deprecated", "retired"] as const).map((s) =>
                  pill(lifecycleState, s, setLifecycleState)
                )}
              </div>
            </div>
          </div>

          {/* Permissions */}
          <div className="space-y-2 rounded-xl border border-border/40 bg-muted/20 p-3">
            <div className="flex items-center justify-between">
              <Label className="text-xs font-semibold">Permissions</Label>
              <span className="text-[10px] text-muted-foreground">{selectedActions.size} selected</span>
            </div>
            <div className="flex flex-wrap gap-1">
              {PERMISSION_PRESETS.map((preset) => {
                const isActive = preset.actions.length === selectedActions.size &&
                  preset.actions.every((a) => selectedActions.has(a))
                return (
                  <button key={preset.label} type="button" onClick={() => applyPreset(preset.actions)}
                    title={preset.tip}
                    className={`rounded-full border px-2 py-0.5 text-[10px] font-medium transition-all ${
                      isActive
                        ? "border-primary bg-primary text-white"
                        : "border-border bg-card text-muted-foreground hover:border-primary/40 hover:text-foreground"
                    }`}>
                    {preset.label}
                  </button>
                )
              })}
            </div>
            <Separator className="my-1" />
            <div className="flex flex-wrap gap-1.5">
              {ALL_ACTION_CODES.map((ac) => {
                const color = ACTION_COLORS[ac] ?? "bg-muted/40 border-border text-muted-foreground"
                const selected = selectedActions.has(ac)
                return (
                  <button key={ac} type="button" onClick={() => toggleAction(ac)}
                    className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium border transition-all ${
                      selected ? color : "bg-muted/20 border-border/30 text-muted-foreground/40 hover:border-border hover:text-muted-foreground"
                    }`}>
                    {selected && <span className="h-1.5 w-1.5 rounded-full bg-current opacity-70" />}
                    {ac}
                  </button>
                )
              })}
            </div>
          </div>
        </div>
        {error && <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500 mt-2">{error}</p>}
        <DialogFooter className="mt-3 gap-2 sm:gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={saving}>Cancel</Button>
          <Button size="sm" onClick={save} disabled={saving}>
            {saving ? <span className="flex items-center gap-1.5"><span className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />Saving…</span> : "Save Changes"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Create flag dialog
// ─────────────────────────────────────────────────────────────────────────────

// Permission presets for quick seeding
const PERMISSION_PRESETS: { label: string; actions: string[]; tip: string }[] = [
  { label: "None",      actions: [],                                           tip: "No permissions — flag is on/off only" },
  { label: "View only", actions: ["view"],                                     tip: "Read-only access" },
  { label: "Read/Write",actions: ["view", "create", "update"],                 tip: "Standard CRUD without delete" },
  { label: "Full CRUD", actions: ["view", "create", "update", "delete"],       tip: "Full create, read, update, delete" },
  { label: "Admin",     actions: ["view", "create", "update", "delete", "assign", "revoke"], tip: "Full CRUD + assignment controls" },
]

function CreateFlagDialog({
  open, categories, onCreate, onClose,
}: {
  open: boolean
  categories: FeatureCategoryResponse[]
  onCreate: (p: CreateFeatureFlagRequest) => Promise<void>
  onClose: () => void
}) {
  const [code, setCode] = useState("")
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [categoryCode, setCategoryCode] = useState(categories[0]?.code ?? "")
  const [featureScope, setFeatureScope] = useState("platform")
  const [selectedActions, setSelectedActions] = useState<Set<string>>(new Set(["view"]))
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [codeEdited, setCodeEdited] = useState(false)

  const toSnakeCase = (s: string) => s.toLowerCase().replace(/\s+/g, "_").replace(/[^a-z0-9_]/g, "").replace(/_+/g, "_").replace(/^_|_$/g, "")

  const handleNameChange = (v: string) => { setName(v); if (!codeEdited) setCode(toSnakeCase(v)) }
  const handleCodeChange = (v: string) => { setCode(v.toLowerCase().replace(/[^a-z0-9_]/g, "_")); setCodeEdited(true) }

  useEffect(() => {
    if (open) {
      setCode(""); setName(""); setDescription("")
      setCategoryCode(categories[0]?.code ?? ""); setFeatureScope("platform")
      setSelectedActions(new Set(["view"]))
      setSaving(false); setError(null); setCodeEdited(false)
    }
  }, [open, categories])

  function pill(current: string, value: string, setter: (v: string) => void, label?: string) {
    return (
      <button key={value} type="button" onClick={() => setter(value)}
        className={`rounded-full border px-3 py-1 text-xs font-medium transition-all ${
          current === value
            ? "border-primary bg-primary text-white"
            : "border-border bg-card text-muted-foreground hover:border-primary/50 hover:text-foreground"
        }`}>
        {label ?? value}
      </button>
    )
  }

  function toggleAction(ac: string) {
    setSelectedActions((prev) => {
      const next = new Set(prev)
      if (next.has(ac)) next.delete(ac); else next.add(ac)
      return next
    })
  }

  function applyPreset(actions: string[]) {
    setSelectedActions(new Set(actions))
  }

  async function create() {
    if (!code.trim() || !name.trim()) { setError("Code and Name are required."); return }
    setSaving(true); setError(null)
    try {
      await onCreate({
        code: code.trim(), name: name.trim(), description: description.trim(),
        category_code: categoryCode, feature_scope: featureScope,
        access_mode: selectedActions.size > 0 ? "permissioned" : "authenticated",
        lifecycle_state: "planned",
        env_dev: true, env_staging: false, env_prod: false,
        permissions: Array.from(selectedActions),
      })
      onClose()
    } catch (e) { setError(e instanceof Error ? e.message : "Failed"); setSaving(false) }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-primary/10 p-2.5"><Plus className="h-4 w-4 text-primary" /></div>
            <div>
              <DialogTitle>New Feature Flag</DialogTitle>
              <DialogDescription>Starts enabled in Dev. Promote to Staging and Production when ready.</DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />
        <div className="space-y-4">
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label className="text-xs">Name</Label>
              <Input value={name} onChange={(e) => handleNameChange(e.target.value)} placeholder="My Feature" className="h-9 text-sm" autoFocus />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs flex items-center gap-1.5">
                Code <span className="text-muted-foreground">(snake_case)</span>
                {!codeEdited && name && <span className="text-[10px] text-primary/70 font-normal">(auto-generated)</span>}
              </Label>
              <Input value={code} onChange={(e) => handleCodeChange(e.target.value)} placeholder="my_feature" className="h-9 text-sm font-mono" />
              <p className="text-[10px] text-muted-foreground">Cannot be changed after creation. Must be unique.</p>
            </div>
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Description</Label>
            <Input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="What does this feature do?" className="h-9 text-sm" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label className="text-xs">Category</Label>
              <div className="flex flex-wrap gap-1.5">
                {categories.map((c) => pill(categoryCode, c.code, setCategoryCode, c.name))}
              </div>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Scope</Label>
              <div className="flex flex-wrap gap-1.5">
                {(["platform", "org", "product"] as const).map((s) =>
                  pill(featureScope, s, setFeatureScope, SCOPE_META[s].label)
                )}
              </div>
            </div>
          </div>

          {/* Permissions */}
          <div className="space-y-2 rounded-xl border border-border/40 bg-muted/20 p-3">
            <div className="flex items-center justify-between">
              <Label className="text-xs font-semibold">Permissions</Label>
              <span className="text-[10px] text-muted-foreground">{selectedActions.size} selected</span>
            </div>
            {/* Presets */}
            <div className="flex flex-wrap gap-1">
              {PERMISSION_PRESETS.map((preset) => {
                const isActive = preset.actions.length === selectedActions.size &&
                  preset.actions.every((a) => selectedActions.has(a))
                return (
                  <button key={preset.label} type="button" onClick={() => applyPreset(preset.actions)}
                    title={preset.tip}
                    className={`rounded-full border px-2 py-0.5 text-[10px] font-medium transition-all ${
                      isActive
                        ? "border-primary bg-primary text-white"
                        : "border-border bg-card text-muted-foreground hover:border-primary/40 hover:text-foreground"
                    }`}>
                    {preset.label}
                  </button>
                )
              })}
            </div>
            <Separator className="my-1" />
            {/* Individual toggles */}
            <div className="flex flex-wrap gap-1.5">
              {ALL_ACTION_CODES.map((ac) => {
                const color = ACTION_COLORS[ac] ?? "bg-muted/40 border-border text-muted-foreground"
                const selected = selectedActions.has(ac)
                return (
                  <button key={ac} type="button" onClick={() => toggleAction(ac)}
                    className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium border transition-all ${
                      selected ? color : "bg-muted/20 border-border/30 text-muted-foreground/40 hover:border-border hover:text-muted-foreground"
                    }`}>
                    {selected && <span className="h-1.5 w-1.5 rounded-full bg-current opacity-70" />}
                    {ac}
                  </button>
                )
              })}
            </div>
            {selectedActions.size === 0 && (
              <p className="text-[10px] text-amber-500/80">No permissions selected — flag will use authenticated access mode.</p>
            )}
          </div>
        </div>
        {error && <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500 mt-2">{error}</p>}
        <DialogFooter className="mt-3 gap-2 sm:gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={saving}>Cancel</Button>
          <Button size="sm" onClick={create} disabled={saving}>
            {saving ? <span className="flex items-center gap-1.5"><span className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />Creating…</span> : "Create Flag"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Create category dialog
// ─────────────────────────────────────────────────────────────────────────────

function CreateCategoryDialog({
  open, onCreate, onClose,
}: {
  open: boolean
  onCreate: (p: { code: string; name: string; description: string; sort_order: number }) => Promise<void>
  onClose: () => void
}) {
  const [name, setName] = useState("")
  const [code, setCode] = useState("")
  const [codeEdited, setCodeEdited] = useState(false)
  const [description, setDescription] = useState("")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const toSnakeCase = (s: string) => s.toLowerCase().replace(/\s+/g, "_").replace(/[^a-z0-9_]/g, "").replace(/_+/g, "_").replace(/^_|_$/g, "")

  useEffect(() => {
    if (open) { setName(""); setCode(""); setCodeEdited(false); setDescription(""); setSaving(false); setError(null) }
  }, [open])

  function handleNameChange(v: string) {
    setName(v)
    if (!codeEdited) setCode(toSnakeCase(v))
  }

  async function create() {
    if (!name.trim()) { setError("Name is required."); return }
    const finalCode = code.trim() || toSnakeCase(name)
    setSaving(true); setError(null)
    try {
      await onCreate({ code: finalCode, name: name.trim(), description: description.trim(), sort_order: 100 })
      onClose()
    } catch (e) { setError(e instanceof Error ? e.message : "Failed"); setSaving(false) }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-primary/10 p-2.5"><FolderPlus className="h-4 w-4 text-primary" /></div>
            <div>
              <DialogTitle>New Category</DialogTitle>
              <DialogDescription>Categories group related feature flags together.</DialogDescription>
            </div>
          </div>
        </DialogHeader>
        <Separator className="my-2" />
        <div className="space-y-3">
          <div className="space-y-1.5">
            <Label className="text-xs">Name</Label>
            <Input value={name} onChange={(e) => handleNameChange(e.target.value)} placeholder="Compliance" className="h-9 text-sm" autoFocus />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs flex items-center gap-1.5">
              Code <span className="text-muted-foreground">(snake_case)</span>
              {!codeEdited && name && <span className="text-[10px] text-primary/70 font-normal">(auto-generated)</span>}
            </Label>
            <Input value={code} onChange={(e) => { setCode(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, "_")); setCodeEdited(true) }} placeholder="compliance" className="h-9 text-sm font-mono" />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Description</Label>
            <Input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Optional description" className="h-9 text-sm" />
          </div>
        </div>
        {error && <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-500 mt-2">{error}</p>}
        <DialogFooter className="mt-3 gap-2 sm:gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={saving}>Cancel</Button>
          <Button size="sm" onClick={create} disabled={saving}>
            {saving ? "Creating…" : "Create Category"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Main page
// ─────────────────────────────────────────────────────────────────────────────

export default function FeatureFlagsPage() {
  const [data, setData] = useState<FeatureFlagListResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [scopeFilter, setScopeFilter] = useState<"all" | "platform" | "org" | "product">("all")
  const [confirmAction, setConfirmAction] = useState<ConfirmAction | null>(null)
  const [editingFlag, setEditingFlag] = useState<FeatureFlagResponse | null>(null)
  const [showCreateFlag, setShowCreateFlag] = useState(false)
  const [showCreateCat, setShowCreateCat] = useState(false)

  const load = useCallback(async () => {
    setLoading(true); setError(null)
    try { setData(await listFeatureFlags()) }
    catch (e) { setError(e instanceof Error ? e.message : "Failed to load") }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  function handleToggleEnv(flag: FeatureFlagResponse, env: "dev" | "staging" | "prod") {
    const isOn = flag[`env_${env}`]
    const envLabel = env === "dev" ? "Development" : env === "staging" ? "Staging" : "Production"
    setConfirmAction({
      title: `${isOn ? "Disable" : "Enable"} in ${envLabel}?`,
      body: `"${flag.name}" will be ${isOn ? "disabled" : "enabled"} in ${envLabel}.`,
      detail: env === "prod" && !isOn
        ? "This will go live to all production users immediately."
        : env === "prod" && isOn
        ? "This will immediately stop working in production."
        : `This only affects ${envLabel}.`,
      variant: env === "prod" ? (isOn ? "danger" : "warning") : "info",
      confirmLabel: `${isOn ? "Disable" : "Enable"} in ${envLabel}`,
      onConfirm: async () => {
        await updateFeatureFlag(flag.code, { [`env_${env}`]: !isOn } as UpdateFeatureFlagRequest)
        await load()
      },
    })
  }

  async function handleEditSave(code: string, payload: UpdateFeatureFlagRequest) {
    await updateFeatureFlag(code, payload)
    setEditingFlag(null); await load()
  }

  async function handleCreateFlag(payload: CreateFeatureFlagRequest) {
    await createFeatureFlag(payload)
    setShowCreateFlag(false); await load()
  }

  async function handleCreateCategory(payload: { code: string; name: string; description: string; sort_order: number }) {
    await createFeatureCategory(payload)
    setShowCreateCat(false); await load()
  }

  const allFlags = data?.flags ?? []
  const categories = data?.categories ?? []

  const stats = useMemo(() => ({
    total: allFlags.length,
    platform: allFlags.filter((f) => f.feature_scope === "platform").length,
    org:      allFlags.filter((f) => f.feature_scope === "org").length,
    product:  allFlags.filter((f) => f.feature_scope === "product").length,
    dev:      allFlags.filter((f) => f.env_dev).length,
    staging:  allFlags.filter((f) => f.env_staging).length,
    prod:     allFlags.filter((f) => f.env_prod).length,
  }), [allFlags])

  const filtered = useMemo(() => {
    let flags = scopeFilter === "all" ? allFlags : allFlags.filter((f) => f.feature_scope === scopeFilter)
    if (search.trim()) {
      const q = search.toLowerCase()
      flags = flags.filter((f) =>
        f.name.toLowerCase().includes(q) || f.code.toLowerCase().includes(q) || (f.description ?? "").toLowerCase().includes(q)
      )
    }
    return flags
  }, [allFlags, scopeFilter, search])

  const grouped = categories
    .map((cat) => ({ category: cat, flags: filtered.filter((f) => f.category_code === cat.code) }))
    .filter((g) => g.flags.length > 0)
  const uncategorized = filtered.filter((f) => !categories.some((c) => c.code === f.category_code))

  return (
    <div className="max-w-7xl space-y-5">
      {/* Dialogs */}
      <ConfirmDialog action={confirmAction} onClose={() => setConfirmAction(null)} />
      <EditFlagDialog flag={editingFlag} categories={categories} onSave={handleEditSave} onClose={() => setEditingFlag(null)} />
      <CreateFlagDialog open={showCreateFlag} categories={categories} onCreate={handleCreateFlag} onClose={() => setShowCreateFlag(false)} />
      <CreateCategoryDialog open={showCreateCat} onCreate={handleCreateCategory} onClose={() => setShowCreateCat(false)} />

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="rounded-2xl bg-primary/10 p-3.5 shrink-0">
            <Flag className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-foreground tracking-tight">Feature Flags</h2>
            <p className="text-sm text-muted-foreground mt-0.5">
              Control features across environments. Click any tag to change it.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Button size="sm" variant="outline" onClick={() => setShowCreateCat(true)} className="gap-1.5">
            <FolderPlus className="h-3.5 w-3.5" />Category
          </Button>
          <Button size="sm" onClick={() => setShowCreateFlag(true)} className="gap-1.5 shadow-sm">
            <Plus className="h-3.5 w-3.5" />Flag
          </Button>
        </div>
      </div>

      {/* KPI stat cards */}
      {!loading && !error && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
          {(([
            { label: "Total",    value: stats.total,    numCls: "text-foreground",   borderCls: "border-l-primary",      icon: Flag },
            { label: "Platform", value: stats.platform, numCls: "text-violet-500",   borderCls: "border-l-violet-500",   icon: Globe },
            { label: "Org",      value: stats.org,      numCls: "text-blue-500",     borderCls: "border-l-blue-500",     icon: Building2 },
            { label: "Product",  value: stats.product,  numCls: "text-indigo-500",   borderCls: "border-l-indigo-500",   icon: Package },
            { label: "Dev",      value: stats.dev,      numCls: "text-blue-500",     borderCls: "border-l-blue-500",     icon: Zap },
            { label: "Staging",  value: stats.staging,  numCls: "text-amber-500",    borderCls: "border-l-amber-500",    icon: Clock },
            { label: "Prod",     value: stats.prod,     numCls: "text-emerald-500",  borderCls: "border-l-emerald-500",  icon: Zap },
          ]) as { label: string; value: number; numCls: string; borderCls: string; icon: typeof Flag }[]).map(({ label, value, numCls, borderCls, icon: Icon }) => (
            <div key={label} className={`relative flex items-center gap-3 rounded-xl border border-l-[3px] ${borderCls} bg-card px-4 py-3`}>
              <div className="shrink-0 rounded-lg p-2 bg-muted">
                <Icon className="h-4 w-4 text-muted-foreground" />
              </div>
              <div className="min-w-0">
                <span className={`text-2xl font-bold tabular-nums leading-none ${numCls}`}>{value}</span>
                <span className="text-[11px] text-muted-foreground mt-0.5 block truncate">{label}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Legend */}
      {!loading && !error && (
        <div className="flex items-center gap-3 flex-wrap text-[11px] text-muted-foreground/60 px-1">
          <span className="font-medium text-muted-foreground">Each flag:</span>
          <span className="flex items-center gap-1.5">
            {Object.entries(LIFECYCLE_META).map(([k, v]) => {
              const Icon = v.icon
              return <span key={k} className={`inline-flex items-center gap-0.5 ${v.color}`}><Icon className="h-2.5 w-2.5" />{v.label}</span>
            })}
            <span className="text-muted-foreground/40 ml-0.5">lifecycle</span>
          </span>
          <span className="w-px h-3 bg-border/40" />
          <span className="flex items-center gap-1.5">
            {Object.entries(ENV_META).map(([k, v]) => (
              <span key={k} className={`inline-flex items-center gap-0.5 ${v.color}`}>
                <span className={`h-1.5 w-1.5 rounded-full ${v.dot}`} />{v.label}
              </span>
            ))}
            <span className="text-muted-foreground/40 ml-0.5">highest env (Prd implies Dev+Stg)</span>
          </span>
          <span className="w-px h-3 bg-border/40" />
          <span className="flex items-center gap-1.5">
            {Object.entries(ACCESS_META).map(([k, v]) => {
              const Icon = v.icon
              return <span key={k} className={`inline-flex items-center gap-0.5 ${v.color}`} title={v.tip}><Icon className="h-2.5 w-2.5" />{v.label}</span>
            })}
            <span className="text-muted-foreground/40 ml-0.5">org access</span>
          </span>
          <span className="w-px h-3 bg-border/40" />
          <span className="flex items-center gap-1.5">
            {(["none", "pro", "enterprise"] as const).map((k) => {
              const v = LICENSE_META[k]
              return <span key={k} className={`inline-flex items-center gap-0.5 rounded-full border px-1.5 py-0.5 text-[10px] font-medium ${v.style}`}><Crown className="h-2.5 w-2.5" />{v.label}</span>
            })}
            <span className="text-muted-foreground/40 ml-0.5">min license</span>
          </span>
          <span className="text-muted-foreground/30 italic">— click any tag to change</span>
        </div>
      )}

      {/* Filter bar */}
      {!loading && !error && (
        <div className="rounded-xl border border-border bg-card px-4 py-3 flex items-center gap-3 flex-wrap">
          {/* Scope filter pills */}
          {(["all", "platform", "org", "product"] as const).map((s) => {
            const active = scopeFilter === s
            const count = s === "all" ? stats.total : stats[s]
            const meta = s !== "all" ? SCOPE_META[s] : null
            const SIcon = meta?.icon
            return (
              <button key={s} type="button" onClick={() => setScopeFilter(s)}
                className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-all ${
                  active ? "border-primary bg-primary text-white shadow-sm" : "border-border bg-background text-muted-foreground hover:border-foreground/20 hover:text-foreground"
                }`}>
                {SIcon && <SIcon className="h-3 w-3" />}
                {s === "all" ? "All" : meta!.label}
                <span className={`tabular-nums ${active ? "text-white/70" : "text-muted-foreground/50"}`}>{count}</span>
              </button>
            )
          })}

          {/* Active filter chips */}
          {scopeFilter !== "all" && (
            <button type="button" onClick={() => setScopeFilter("all")}
              className="inline-flex items-center gap-1 rounded-full bg-primary/10 border border-primary/20 text-primary px-2 py-0.5 text-[11px] font-medium hover:bg-primary/20 transition-colors">
              scope: {scopeFilter}
              <X className="h-2.5 w-2.5 ml-0.5" />
            </button>
          )}
          {search && (
            <button type="button" onClick={() => setSearch("")}
              className="inline-flex items-center gap-1 rounded-full bg-primary/10 border border-primary/20 text-primary px-2 py-0.5 text-[11px] font-medium hover:bg-primary/20 transition-colors">
              "{search}"
              <X className="h-2.5 w-2.5 ml-0.5" />
            </button>
          )}

          {/* Search */}
          <div className="ml-auto relative w-56">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground/50 pointer-events-none" />
            <Input value={search} onChange={(e) => setSearch(e.target.value)}
              placeholder="Search…" className="h-7 pl-7 text-xs" />
            {search && (
              <button type="button" onClick={() => setSearch("")}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
                <X className="h-3 w-3" />
              </button>
            )}
          </div>
        </div>
      )}

      {/* Error / loading */}
      {error && <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-500">{error}</div>}
      {loading && <div className="space-y-3">{[1, 2, 3].map((i) => <div key={i} className="h-14 animate-pulse rounded-xl bg-muted" />)}</div>}

      {/* Flag list */}
      {!loading && !error && data && (
        <div className="space-y-2">
          {grouped.map(({ category, flags }) => (
            <CategorySection key={category.code} category={category} flags={flags}
              onToggleEnv={handleToggleEnv} onEdit={setEditingFlag} onReload={load} />
          ))}
          {uncategorized.length > 0 && (
            <CategorySection category={null} flags={uncategorized}
              onToggleEnv={handleToggleEnv} onEdit={setEditingFlag} onReload={load} />
          )}
          {filtered.length === 0 && (
            <div className="rounded-xl border border-dashed border-border px-6 py-12 text-center">
              <Flag className="mx-auto h-8 w-8 text-muted-foreground mb-3" />
              <p className="text-sm text-muted-foreground">No flags match your filters.</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}