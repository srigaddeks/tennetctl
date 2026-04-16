"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@kcontrol/ui"
import { Flag, Building2, FlaskConical, FolderOpen, Folder, ChevronDown, ChevronRight, ShieldCheck, Info, Lock, Crown } from "lucide-react"
import { listOrgAvailableFlags, getEntitySettings, setEntitySetting, deleteEntitySetting } from "@/lib/api/admin"
import { CURRENT_ENV, CURRENT_ENV_LABEL } from "@/lib/config"
import { listOrgs } from "@/lib/api/orgs"
import { fetchUserProperties } from "@/lib/api/auth"
import type { OrgAvailableFlagResponse, FeatureCategoryResponse } from "@/lib/types/admin"
import type { OrgResponse } from "@/lib/types/orgs"

// ── Helpers ───────────────────────────────────────────────────────────────────

function parseEnabledFeatures(raw: string | undefined): Set<string> {
  if (!raw) return new Set()
  try {
    const arr = JSON.parse(raw)
    if (Array.isArray(arr)) return new Set(arr as string[])
  } catch {}
  return new Set()
}

function serializeEnabledFeatures(set: Set<string>): string {
  return JSON.stringify([...set])
}

function Tip({ text, children }: { text: string; children: React.ReactNode }) {
  return (
    <span className="group/tip relative inline-flex">
      {children}
      <span className="pointer-events-none absolute bottom-full left-1/2 z-50 mb-1.5 -translate-x-1/2 whitespace-nowrap rounded-md border border-border bg-popover px-2.5 py-1 text-xs text-popover-foreground shadow-md opacity-0 transition-opacity group-hover/tip:opacity-100 max-w-xs text-center">
        {text}
      </span>
    </span>
  )
}

// ── Toggle Row ────────────────────────────────────────────────────────────────

const TIER_RANK: Record<string, number> = { free: 0, partner: 1, pro_trial: 2, pro: 3, enterprise: 4, internal: 5 }

function meetsLicenseRequirement(orgTier: string, required: string | null): boolean {
  if (!required) return true
  return (TIER_RANK[orgTier] ?? 0) >= (TIER_RANK[required] ?? 0)
}

function FlagToggleRow({
  flag,
  enabled,
  onToggle,
  saving,
  orgTier,
}: {
  flag: OrgAvailableFlagResponse
  enabled: boolean
  onToggle: (code: string, enabled: boolean) => void
  saving: boolean
  orgTier: string
}) {
  const isLocked = flag.org_visibility === "locked"
  const tierBlocked = !meetsLicenseRequirement(orgTier, flag.required_license)

  return (
    <div className={`flex items-center gap-4 px-4 py-3 hover:bg-accent/30 transition-colors ${enabled ? "" : "opacity-60"}`}>
      <div className="flex flex-col gap-1 min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-foreground leading-tight">{flag.name}</span>
          {flag.permissions.length > 0 && (
            <Tip text={`Permissions: ${flag.permissions.map((p) => p.permission_action_code).join(", ")}`}>
              <span className="inline-flex items-center gap-0.5 text-muted-foreground cursor-help">
                <ShieldCheck className="h-3 w-3" />
                <span className="text-[10px]">{flag.permissions.length}</span>
              </span>
            </Tip>
          )}
          {isLocked && (
            <Tip text={`This feature is ${enabled ? "enabled" : "disabled"} by your platform administrator and cannot be changed at the org level`}>
              <span className="inline-flex items-center gap-0.5 rounded-full border border-amber-500/40 bg-amber-500/10 px-1.5 py-0 text-[10px] font-medium text-amber-600 dark:text-amber-400 cursor-help">
                <Lock className="h-2.5 w-2.5" />
                {enabled ? "Enabled" : "Disabled"} by admin
              </span>
            </Tip>
          )}
          {flag.required_license && (
            <Tip text={tierBlocked ? `Requires ${flag.required_license} tier — your org is on ${orgTier}. Upgrade to enable.` : `This feature requires ${flag.required_license} tier or higher`}>
              <span className={`inline-flex items-center gap-0.5 rounded-full border px-1.5 py-0 text-[10px] font-semibold cursor-help ${tierBlocked ? "border-red-500/40 bg-red-500/5 text-red-500" : "border-purple-500/40 bg-purple-500/5 text-purple-500"}`}>
                <Crown className="h-2.5 w-2.5" />
                {flag.required_license}{tierBlocked ? " required" : ""}
              </span>
            </Tip>
          )}
        </div>
        <Tip text={flag.code}>
          <span className="text-xs text-muted-foreground cursor-help">{flag.description}</span>
        </Tip>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <span className="text-xs text-muted-foreground">{enabled ? "Enabled" : "Disabled"}</span>
        {isLocked || tierBlocked ? (
          <Tip text={tierBlocked ? `Upgrade to ${flag.required_license} to enable this feature` : "Managed by platform admin"}>
            <span
              className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full cursor-not-allowed opacity-50 ${
                enabled ? "bg-primary" : "bg-muted border border-border"
              }`}
            >
              <span className={`pointer-events-none inline-block h-4 w-4 rounded-full bg-white shadow-sm ${enabled ? "translate-x-6" : "translate-x-1"}`} />
            </span>
          </Tip>
        ) : (
          <button
            type="button"
            role="switch"
            aria-checked={enabled}
            disabled={saving}
            onClick={() => onToggle(flag.code, !enabled)}
            className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:opacity-50 disabled:cursor-not-allowed ${
              enabled ? "bg-primary" : "bg-muted border border-border"
            }`}
          >
            <span className={`pointer-events-none inline-block h-4 w-4 rounded-full bg-white shadow-sm transition-transform ${enabled ? "translate-x-6" : "translate-x-1"}`} />
          </button>
        )}
      </div>
    </div>
  )
}

// ── Category Group ────────────────────────────────────────────────────────────

function CategoryGroup({
  category,
  flags,
  enabledFeatures,
  onToggle,
  saving,
  orgTier,
}: {
  category: FeatureCategoryResponse | null
  flags: OrgAvailableFlagResponse[]
  enabledFeatures: Set<string>
  onToggle: (code: string, enabled: boolean) => void
  saving: boolean
  orgTier: string
}) {
  const [open, setOpen] = useState(true)
  const label = category?.name ?? "Other"
  const enabledCount = flags.filter((f) => enabledFeatures.has(f.code)).length
  const lockedCount = flags.filter((f) => f.org_visibility === "locked").length

  return (
    <div className="space-y-1">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-2 rounded-xl px-3 py-2 hover:bg-muted/50 transition-colors text-left"
      >
        {open ? <FolderOpen className="h-4 w-4 text-primary shrink-0" /> : <Folder className="h-4 w-4 text-muted-foreground shrink-0" />}
        <span className="text-sm font-semibold text-foreground">{label}</span>
        {category?.description && (
          <Tip text={category.description}>
            <Info className="h-3 w-3 text-muted-foreground cursor-help" />
          </Tip>
        )}
        <div className="ml-auto flex items-center gap-2 shrink-0">
          <span className="text-xs text-muted-foreground">{enabledCount}/{flags.length} enabled</span>
          {lockedCount > 0 && (
            <span className="inline-flex items-center gap-0.5 text-[10px] text-amber-500">
              <Lock className="h-3 w-3" />{lockedCount}
            </span>
          )}
          {open ? <ChevronDown className="h-4 w-4 text-muted-foreground" /> : <ChevronRight className="h-4 w-4 text-muted-foreground" />}
        </div>
      </button>

      {open && (
        <Card className="rounded-xl border-border bg-card overflow-hidden ml-4">
          <div className="divide-y divide-border">
            {flags.map((flag) => (
              <FlagToggleRow
                key={flag.code}
                flag={flag}
                enabled={enabledFeatures.has(flag.code)}
                onToggle={onToggle}
                saving={saving}
                orgTier={orgTier}
              />
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function OrgFeaturesPage() {
  const [orgs, setOrgs] = useState<OrgResponse[]>([])
  const [selectedOrgId, setSelectedOrgId] = useState<string>("")
  const [flags, setFlags] = useState<OrgAvailableFlagResponse[]>([])
  const [categories, setCategories] = useState<FeatureCategoryResponse[]>([])
  const [enabledFeatures, setEnabledFeatures] = useState<Set<string>>(new Set())
  const [orgLicenseTier, setOrgLicenseTier] = useState<string>("free")
  const [saving, setSaving] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [permissionDenied, setPermissionDenied] = useState(false)

  // Load orgs, flags (with visibility pre-resolved from backend), and user's default org
  useEffect(() => {
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const [orgsRes, flagsRes, props] = await Promise.all([
          listOrgs(),
          listOrgAvailableFlags(),  // Single API call — no N+1, no platform permission needed
          fetchUserProperties(),
        ])
        setOrgs(orgsRes)
        setCategories(flagsRes.categories)
        // Only show flags enabled in current environment
        setFlags(flagsRes.flags.filter((f) => f[`env_${CURRENT_ENV}`]))
        const defaultOrgId = props["default_org_id"] ?? ""
        const firstOrgId = orgsRes[0]?.id ?? ""
        setSelectedOrgId(defaultOrgId || firstOrgId)
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load")
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  // Load enabled features for selected org
  useEffect(() => {
    if (!selectedOrgId) return
    let mounted = true
    async function loadOrgSettings() {
      try {
        const settings = await getEntitySettings("org", selectedOrgId)
        const raw = settings.find((s) => s.key === "enabled_features")?.value
        const tier = settings.find((s) => s.key === "license_tier")?.value ?? "free"
        if (mounted) {
          setEnabledFeatures(parseEnabledFeatures(raw))
          setOrgLicenseTier(tier)
          setPermissionDenied(false)
        }
      } catch (e) {
        if (mounted) {
          setEnabledFeatures(new Set())
          setOrgLicenseTier("free")
          // If 403, the user doesn't have org admin permissions
          const msg = e instanceof Error ? e.message : ""
          setPermissionDenied(msg.includes("403") || msg.toLowerCase().includes("permission") || msg.toLowerCase().includes("forbidden"))
        }
      }
    }
    loadOrgSettings()
    return () => { mounted = false }
  }, [selectedOrgId])

  async function handleToggle(flagCode: string, nowEnabled: boolean) {
    if (!selectedOrgId) return
    const flag = flags.find((f) => f.code === flagCode)
    if (flag?.org_visibility === "locked") return
    if (!meetsLicenseRequirement(orgLicenseTier, flag?.required_license ?? null)) return

    setSaving(true)
    setSaveError(null)
    const prev = new Set(enabledFeatures)
    const next = new Set(enabledFeatures)
    if (nowEnabled) next.add(flagCode)
    else next.delete(flagCode)
    setEnabledFeatures(next)
    try {
      if (next.size === 0) {
        await deleteEntitySetting("org", selectedOrgId, "enabled_features")
      } else {
        await setEntitySetting("org", selectedOrgId, "enabled_features", serializeEnabledFeatures(next))
      }
    } catch (e) {
      setEnabledFeatures(prev)
      setSaveError(e instanceof Error ? e.message : "Failed to save")
    } finally {
      setSaving(false)
    }
  }

  const selectedOrg = orgs.find((o) => o.id === selectedOrgId)
  const lockedCount = flags.filter((f) => f.org_visibility === "locked").length

  // Group by category
  const groupedByCategory = categories
    .map((cat) => ({ category: cat, flags: flags.filter((f) => f.category_code === cat.code) }))
    .filter((g) => g.flags.length > 0)
  const uncategorized = flags.filter((f) => !categories.some((c) => c.code === f.category_code))

  return (
    <div className="max-w-3xl space-y-5">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold text-foreground">Features</h1>
        <p className="text-sm text-muted-foreground">
          Enable or disable features for your organization.
        </p>
      </div>

      <div className={`flex items-center gap-3 rounded-xl border-2 px-4 py-2.5 ${
        CURRENT_ENV === "prod" ? "border-green-500/40 bg-green-500/10" :
        CURRENT_ENV === "staging" ? "border-amber-500/40 bg-amber-500/10" :
        "border-blue-500/40 bg-blue-500/10"
      }`}>
        <FlaskConical className={`h-4 w-4 shrink-0 ${
          CURRENT_ENV === "prod" ? "text-green-500" :
          CURRENT_ENV === "staging" ? "text-amber-500" :
          "text-blue-500"
        }`} />
        <div>
          <p className={`text-sm font-semibold ${
            CURRENT_ENV === "prod" ? "text-green-500" :
            CURRENT_ENV === "staging" ? "text-amber-500" :
            "text-blue-500"
          }`}>{CURRENT_ENV_LABEL} Environment</p>
          <p className="text-xs text-muted-foreground">Features shown here are available in the {CURRENT_ENV_LABEL.toLowerCase()} environment.</p>
        </div>
      </div>

      {orgs.length > 1 && (
        <div className="flex items-center gap-3">
          <Building2 className="h-4 w-4 text-muted-foreground shrink-0" />
          <select
            value={selectedOrgId}
            onChange={(e) => setSelectedOrgId(e.target.value)}
            className="flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
          >
            {orgs.map((o) => (<option key={o.id} value={o.id}>{o.name}</option>))}
          </select>
        </div>
      )}

      {selectedOrg && (
        <div className="flex items-center gap-2 rounded-xl border border-border bg-muted/30 px-4 py-2.5">
          <Building2 className="h-4 w-4 text-muted-foreground shrink-0" />
          <div className="min-w-0">
            <p className="text-sm font-medium text-foreground truncate">{selectedOrg.name}</p>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-xs text-muted-foreground capitalize">{selectedOrg.org_type_code.replace(/_/g, " ")}</span>
              <Tip text={`License tier: ${orgLicenseTier}. Some features may require a higher tier.`}>
                <span className={`inline-flex items-center gap-0.5 rounded-full border px-1.5 py-0 text-[10px] font-semibold cursor-help ${
                  orgLicenseTier === "pro" ? "border-primary/40 bg-primary/10 text-primary" :
                  orgLicenseTier === "pro_trial" ? "border-amber-500/40 bg-amber-500/10 text-amber-500" :
                  orgLicenseTier === "internal" ? "border-purple-500/40 bg-purple-500/10 text-purple-500" :
                  "border-border bg-muted text-muted-foreground"
                }`}>
                  {(orgLicenseTier === "pro" || orgLicenseTier === "pro_trial") && <Crown className="h-2.5 w-2.5" />}
                  {orgLicenseTier === "pro_trial" ? "Pro Trial" : orgLicenseTier.charAt(0).toUpperCase() + orgLicenseTier.slice(1)}
                </span>
              </Tip>
            </div>
          </div>
          <div className="ml-auto flex items-center gap-3 text-xs text-muted-foreground">
            <span>{enabledFeatures.size} of {flags.length} enabled</span>
            {lockedCount > 0 && (
              <Tip text={`${lockedCount} feature${lockedCount !== 1 ? "s" : ""} managed by platform admin`}>
                <span className="inline-flex items-center gap-0.5 text-amber-500 cursor-help"><Lock className="h-3 w-3" />{lockedCount} locked</span>
              </Tip>
            )}
          </div>
        </div>
      )}

      {permissionDenied && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 px-4 py-3">
          <p className="text-sm text-amber-700 dark:text-amber-400 font-medium">You don&apos;t have permission to manage features for this organization.</p>
          <p className="text-xs text-muted-foreground mt-1">Contact your organization owner or admin to get access.</p>
        </div>
      )}
      {saveError && <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-500">{saveError}</div>}
      {error && <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-500">{error}</div>}
      {loading && <div className="space-y-2">{[1, 2, 3].map((i) => <div key={i} className="h-14 animate-pulse rounded-xl bg-muted" />)}</div>}

      {!loading && !error && (
        <>
          {flags.length === 0 ? (
            <div className="rounded-xl border border-dashed border-border bg-card px-6 py-12 text-center">
              <Flag className="mx-auto h-8 w-8 text-muted-foreground mb-3" />
              <p className="text-sm text-muted-foreground">No features are available for your organization yet.</p>
              <p className="text-xs text-muted-foreground mt-1">Your platform administrator hasn't made any features configurable at the organization level.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {groupedByCategory.map(({ category, flags: catFlags }) => (
                <CategoryGroup key={category.code} category={category} flags={catFlags} enabledFeatures={enabledFeatures} onToggle={handleToggle} saving={saving} orgTier={orgLicenseTier} />
              ))}
              {uncategorized.length > 0 && (
                <CategoryGroup category={null} flags={uncategorized} enabledFeatures={enabledFeatures} onToggle={handleToggle} saving={saving} orgTier={orgLicenseTier} />
              )}
            </div>
          )}
        </>
      )}

      {!loading && !error && (
        <div className="space-y-2">
          {lockedCount > 0 && (
            <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 px-4 py-3">
              <p className="text-xs text-muted-foreground">
                <Lock className="inline h-3 w-3 text-amber-500 mr-1" />
                <strong className="text-foreground">{lockedCount} feature{lockedCount !== 1 ? "s" : ""}</strong> {lockedCount !== 1 ? "are" : "is"} managed by your platform administrator.
              </p>
            </div>
          )}
          <div className="rounded-xl border border-border bg-muted/20 px-4 py-3">
            <p className="text-xs text-muted-foreground">
              <strong className="text-foreground">Platform features</strong> are controlled globally by super admins and are not shown here.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
