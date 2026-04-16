"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
} from "@kcontrol/ui"
import {
  Building2,
  Layers,
  ChevronRight,
  Library,
  ShieldAlert,
  CheckSquare,
  Settings,
  Sparkles,
  ArrowRight,
  Plus,
  Rocket,
} from "lucide-react"
import { fetchUserProperties } from "@/lib/api/auth"
import { listOrgs } from "@/lib/api/orgs"
import { listWorkspaces } from "@/lib/api/workspaces"
import { getEntitySettings } from "@/lib/api/admin"
import { listFrameworks, listRisks, listTasks } from "@/lib/api/grc"
import type { OrgResponse, WorkspaceResponse } from "@/lib/types/orgs"
import type { FrameworkResponse, RiskResponse, TaskResponse } from "@/lib/types/grc"
import { useOrgWorkspace } from "@/lib/context/OrgWorkspaceContext"
import { OrgWorkspaceSwitcher } from "@/components/layout/OrgWorkspaceSwitcher"
import { ReadOnlyBanner } from "@/components/layout/ReadOnlyBanner"

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface DashboardData {
  firstName: string
  defaultOrg: OrgResponse | null
  defaultWorkspace: WorkspaceResponse | null
  allWorkspaces: WorkspaceResponse[]
  licenseTier: string
  frameworkCount: number
  approvedFrameworks: number
  totalControls: number
  riskCount: number
  criticalHighRisks: number
  openRisks: number
  taskCount: number
  openTasks: number
  overdueTasks: number
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function QuickActionRow({
  icon,
  iconBg,
  label,
  href,
}: {
  icon: React.ReactNode
  iconBg: string
  label: string
  href: string
}) {
  return (
    <Link href={href} className="group/item">
      <div className="flex h-11 items-center gap-3 rounded-xl px-2.5 transition-all hover:bg-muted/50 group/row">
        <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${iconBg}`}>
          {icon}
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-semibold text-foreground group-hover/row:text-primary transition-colors truncate">
            {label}
          </div>
        </div>
        <div className="flex h-6 w-6 items-center justify-center rounded-md text-muted-foreground/30 transition-all group-hover/row:translate-x-0.5 group-hover/row:text-primary">
          <ChevronRight className="h-4 w-4" />
        </div>
      </div>
    </Link>
  )
}

function StatCard({
  icon,
  borderCls,
  numCls,
  value,
  label,
  href,
}: {
  icon: React.ReactNode
  borderCls: string
  numCls?: string
  value: number
  label: string
  href: string
}) {
  return (
    <Link href={href}>
      <div className={`relative rounded-xl border bg-card border-l-[3px] ${borderCls} px-4 py-3 flex items-center gap-3 hover:bg-muted/20 transition-colors cursor-pointer`}>
        <div className="shrink-0 rounded-lg p-2 bg-muted">{icon}</div>
        <div className="min-w-0">
          <p className={`text-2xl font-bold tabular-nums leading-none ${numCls ?? ""}`}>{value}</p>
          <p className="text-[11px] text-muted-foreground mt-0.5 truncate">{label}</p>
        </div>
      </div>
    </Link>
  )
}

// ---------------------------------------------------------------------------
// Onboarding Nudge — shown when all stats are zero
// ---------------------------------------------------------------------------

function OnboardingNudge() {
  return (
    <div className="relative group overflow-hidden rounded-3xl border border-primary/20 bg-card p-1 shadow-2xl transition-all hover:shadow-primary/5">
      {/* Premium Glassmorphism Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/[0.08] via-background to-blue-500/[0.08] opacity-100" />
      <div className="absolute -top-12 -right-12 lg:-top-24 lg:-right-24 h-48 w-48 lg:h-64 lg:w-64 rounded-full bg-primary/5 lg:bg-primary/10 blur-[60px] lg:blur-[80px]" />
      <div className="absolute -bottom-12 -left-12 lg:-bottom-24 lg:-left-24 h-48 w-48 lg:h-64 lg:w-64 rounded-full bg-blue-500/5 lg:bg-blue-500/10 blur-[60px] lg:blur-[80px]" />

      <div className="relative flex flex-col lg:flex-row items-stretch gap-0 overflow-hidden rounded-[22px] bg-background/40 backdrop-blur-sm">
        {/* Left Content: Value Prop */}
        <div className="flex flex-col justify-center p-6 sm:p-8 lg:p-12 lg:w-3/5 space-y-4 lg:space-y-6 text-center lg:text-left">
          <div className="space-y-3 lg:space-y-4">
            <div className="inline-flex items-center lg:mx-0 mx-auto gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-[10px] font-black uppercase tracking-widest text-primary">
              <Rocket className="h-3 w-3" />
              Getting Started
            </div>
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight text-foreground font-secondary leading-tight">
              Build your compliance <span className="text-primary">command center.</span>
            </h2>
            <p className="text-sm sm:text-base text-muted-foreground leading-relaxed max-w-md italic lg:mx-0 mx-auto">
              "The journey of a thousand controls begins with a single framework."
            </p>
            <p className="hidden sm:block text-xs sm:text-sm text-muted-foreground/80 leading-relaxed max-w-lg lg:mx-0 mx-auto">
              Unlock the full power of K-Control by initializing your workspace. Whether you're importing a library or using our AI, we've got you covered.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-4 pt-2">
            <Button className="w-full sm:w-auto gap-2 h-11 sm:h-12 px-8 rounded-2xl font-bold text-sm shadow-xl shadow-primary/20 transition-all hover:scale-[1.02] active:scale-95 group/btn" asChild>
              <Link href="/frameworks">
                Start Building Now
                <ArrowRight className="h-4 w-4 transition-transform group-hover/btn:translate-x-1" />
              </Link>
            </Button>
            <div className="flex -space-x-2">
              {[Library, Sparkles, Plus].map((Icon, i) => (
                <div key={i} className="h-8 w-8 rounded-full border-2 border-background bg-muted flex items-center justify-center">
                  <Icon className="h-3.5 w-3.5 text-muted-foreground" />
                </div>
              ))}
              <div className="h-8 px-3 rounded-full border-2 border-background bg-muted flex items-center justify-center text-[9px] font-bold text-muted-foreground">
                3 Pathways
              </div>
            </div>
          </div>
        </div>

        {/* Right Content: Visual/Steps Preview */}
        <div className="hidden lg:flex lg:w-2/5 relative bg-primary/5 border-l border-primary/10 p-8 flex-col justify-center gap-4">
          <div className="space-y-4">
            {[
              { title: "Standard Library", desc: "ISO, SOC2, NIST", icon: Library },
              { title: "AI Custom Build", desc: "Automated & Smart", icon: Sparkles, active: true },
              { title: "Manual Entry", desc: "Complete Control", icon: Plus },
            ].map((s, i) => (
              <div
                key={i}
                className={`flex items-center gap-4 p-4 rounded-2xl border transition-all ${s.active
                    ? "bg-background border-primary shadow-lg shadow-primary/5 scale-105 z-10"
                    : "bg-background/20 border-border/50 scale-95 opacity-60"
                  }`}
              >
                <div className={`h-10 w-10 rounded-xl flex items-center justify-center ${s.active ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}>
                  <s.icon className="h-5 w-5" />
                </div>
                <div>
                  <div className="text-sm font-bold">{s.title}</div>
                  <div className="text-[10px] uppercase font-bold tracking-tight text-muted-foreground opacity-70">{s.desc}</div>
                </div>
                {s.active && <div className="ml-auto h-2 w-2 rounded-full bg-primary animate-ping" />}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function DashboardPage() {
  const { selectedOrgId, selectedWorkspaceId, orgs: contextOrgs, workspaces: contextWorkspaces, ready } = useOrgWorkspace()
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!ready || !selectedOrgId) return

    async function load() {
      try {
        const orgId = selectedOrgId!
        const wsId = selectedWorkspaceId || null
        const props = await fetchUserProperties()

        let defaultOrg: OrgResponse | null = null
        let defaultWorkspace: WorkspaceResponse | null = null
        let allWorkspaces: WorkspaceResponse[] = contextWorkspaces
        let licenseTier = "free"

        const orgs = contextOrgs.length > 0 ? contextOrgs : await listOrgs().catch(() => [])
        if (allWorkspaces.length === 0) {
          allWorkspaces = await listWorkspaces(orgId).catch(() => [] as WorkspaceResponse[])
        }
        const orgSettings = await getEntitySettings("org", orgId).catch(() => [] as { key: string; value: string }[])
        defaultOrg = orgs.find((o) => o.id === orgId) ?? null
        defaultWorkspace = wsId
          ? allWorkspaces.find((w) => w.id === wsId) ?? null
          : allWorkspaces[0] ?? null
        licenseTier = orgSettings.find((s) => s.key === "license_tier")?.value ?? "free"

        // Load GRC stats scoped to selected org/workspace
        let frameworks: FrameworkResponse[] = []
        let risks: RiskResponse[] = []
        let tasks: TaskResponse[] = []
        try {
          const filters = { org_id: orgId, workspace_id: wsId || undefined }
          const [fwRes, riskRes, taskRes] = await Promise.all([
            listFrameworks({ scope_org_id: orgId, ...(wsId ? { scope_workspace_id: wsId } : {}) }).catch(() => ({ items: [] })),
            listRisks(filters).catch(() => ({ items: [] })),
            listTasks({ orgId, workspaceId: wsId || undefined }).catch(() => ({ items: [] })),
          ])
          frameworks = fwRes.items ?? []
          risks = riskRes.items ?? []
          tasks = taskRes.items ?? []
        } catch {
          // non-blocking
        }

        setData({
          firstName: props["first_name"] || props["display_name"] || "",
          defaultOrg,
          defaultWorkspace,
          allWorkspaces,
          licenseTier,
          frameworkCount: frameworks.length,
          approvedFrameworks: frameworks.filter((f) => f.approval_status === "approved").length,
          totalControls: frameworks.reduce((sum, f) => sum + (f.control_count ?? 0), 0),
          riskCount: risks.length,
          criticalHighRisks: risks.filter((r) => r.risk_level_code === "critical" || r.risk_level_code === "high").length,
          openRisks: risks.filter((r) => !["accepted", "closed"].includes(r.risk_status)).length,
          taskCount: tasks.length,
          openTasks: tasks.filter((t) => t.status_code === "open" || t.status_code === "in_progress").length,
          overdueTasks: tasks.filter((t) => t.status_code === "overdue" || (t.due_date && new Date(t.due_date) < new Date() && !["resolved", "cancelled"].includes(t.status_code))).length,
        })
      } catch {
        setData({
          firstName: "", defaultOrg: null, defaultWorkspace: null, allWorkspaces: [], licenseTier: "free",
          frameworkCount: 0, approvedFrameworks: 0, totalControls: 0,
          riskCount: 0, criticalHighRisks: 0, openRisks: 0,
          taskCount: 0, openTasks: 0, overdueTasks: 0,
        })
      } finally {
        setLoading(false)
      }
    }
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, selectedOrgId, selectedWorkspaceId])

  const today = new Date()
  const formattedDate = today.toLocaleDateString("en-GB", {
    weekday: "long", day: "numeric", month: "long", year: "numeric",
  })
  const greeting = () => {
    const h = today.getHours()
    if (h < 12) return "Good morning"
    if (h < 17) return "Good afternoon"
    return "Good evening"
  }

  if (loading) {
    return (
      <div className="space-y-8">
        <div className="space-y-2">
          <div className="h-3 w-40 rounded-md bg-muted animate-pulse" />
          <div className="h-8 w-64 rounded-md bg-muted animate-pulse" />
        </div>
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => <div key={i} className="h-20 rounded-xl bg-muted animate-pulse" />)}
        </div>
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
          {[1, 2, 3].map((i) => <div key={i} className="h-28 rounded-2xl bg-muted animate-pulse" />)}
        </div>
      </div>
    )
  }

  const d = data!
  const isWorkspaceEmpty = d.frameworkCount === 0 && d.totalControls === 0 && d.riskCount === 0 && d.taskCount === 0

  return (
    <div className="space-y-8">
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div className="space-y-1">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
              {formattedDate}
            </p>
            <h1 className="text-3xl font-bold tracking-tight text-foreground font-secondary">
              {greeting()}{d.firstName ? `, ${d.firstName}` : ""}
            </h1>
            <p className="text-sm text-muted-foreground">
              {isWorkspaceEmpty ? "Let's get your workspace set up." : "Your compliance posture at a glance."}
            </p>
          </div>
          <OrgWorkspaceSwitcher />
          <ReadOnlyBanner />
        </div>
        <div className="mt-4 h-px w-full bg-gradient-to-r from-primary/50 via-primary/20 to-transparent" />
      </div>

      {isWorkspaceEmpty ? (
        <OnboardingNudge />
      ) : (
        <>
          {/* ── GRC Stats ──────────────────────────────────────────────────── */}
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <StatCard
              icon={<Library className="h-4 w-4 text-primary" />}
              borderCls="border-l-primary"
              value={d.frameworkCount}
              label="Frameworks"
              href="/frameworks"
            />
            <StatCard
              icon={<Layers className="h-4 w-4 text-blue-500" />}
              borderCls="border-l-blue-500"
              numCls="text-blue-600 dark:text-blue-400"
              value={d.totalControls}
              label="Controls"
              href="/frameworks"
            />
            <StatCard
              icon={<ShieldAlert className="h-4 w-4 text-red-500" />}
              borderCls="border-l-red-500"
              numCls={d.openRisks > 0 ? "text-red-600 dark:text-red-400" : ""}
              value={d.openRisks}
              label="Open Risks"
              href="/risks"
            />
            <StatCard
              icon={<CheckSquare className="h-4 w-4 text-amber-500" />}
              borderCls="border-l-amber-500"
              numCls={d.openTasks > 0 ? "text-amber-600 dark:text-amber-400" : ""}
              value={d.openTasks}
              label="Open Tasks"
              href="/tasks"
            />
          </div>

          {/* ── Main content ───────────────────────────────────────────────── */}
          <div className="grid gap-4 lg:grid-cols-3">
            {/* Risk Overview */}
            <Card className="rounded-2xl border-border bg-card">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base font-semibold flex items-center gap-2">
                    <ShieldAlert className="h-4 w-4 text-red-500" />
                    Risk Overview
                  </CardTitle>
                  <Button variant="ghost" size="sm" className="h-7 text-xs" asChild>
                    <Link href="/risks">View all</Link>
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-3 pt-0">
                <div className="grid grid-cols-3 gap-3">
                  <div className="text-center p-3 rounded-lg bg-muted/50 border border-border/50">
                    <p className="text-xl font-bold tabular-nums">{d.riskCount}</p>
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wider mt-0.5">Total</p>
                  </div>
                  <div className="text-center p-3 rounded-lg bg-red-500/5 border border-red-500/20">
                    <p className="text-xl font-bold tabular-nums text-red-500">{d.criticalHighRisks}</p>
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wider mt-0.5">Crit/High</p>
                  </div>
                  <div className="text-center p-3 rounded-lg bg-amber-500/5 border border-amber-500/20">
                    <p className="text-xl font-bold tabular-nums text-amber-500">{d.openRisks}</p>
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wider mt-0.5">Open</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Task Overview */}
            <Card className="rounded-2xl border-border bg-card">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base font-semibold flex items-center gap-2">
                    <CheckSquare className="h-4 w-4 text-primary" />
                    Task Overview
                  </CardTitle>
                  <Button variant="ghost" size="sm" className="h-7 text-xs" asChild>
                    <Link href="/tasks">View all</Link>
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-3 pt-0">
                <div className="grid grid-cols-3 gap-3">
                  <div className="text-center p-3 rounded-lg bg-muted/50 border border-border/50">
                    <p className="text-xl font-bold tabular-nums">{d.taskCount}</p>
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wider mt-0.5">Total</p>
                  </div>
                  <div className="text-center p-3 rounded-lg bg-blue-500/5 border border-blue-500/20">
                    <p className="text-xl font-bold tabular-nums text-blue-500">{d.openTasks}</p>
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wider mt-0.5">Open</p>
                  </div>
                  <div className="text-center p-3 rounded-lg bg-red-500/5 border border-red-500/20">
                    <p className="text-xl font-bold tabular-nums text-red-500">{d.overdueTasks}</p>
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wider mt-0.5">Overdue</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card className="rounded-2xl border-border bg-card">
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-semibold">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-0.5 px-3 pb-3 pt-0">
                <QuickActionRow
                  icon={<Library className="h-3.5 w-3.5 text-primary" />}
                  iconBg="bg-primary/10"
                  label="Browse Frameworks"
                  href="/frameworks"
                />
                <QuickActionRow
                  icon={<ShieldAlert className="h-3.5 w-3.5 text-red-500" />}
                  iconBg="bg-red-500/10"
                  label="Risk Registry"
                  href="/risks"
                />
                <QuickActionRow
                  icon={<CheckSquare className="h-3.5 w-3.5 text-amber-500" />}
                  iconBg="bg-amber-500/10"
                  label="My Tasks"
                  href="/tasks"
                />
                <QuickActionRow
                  icon={<Building2 className="h-3.5 w-3.5 text-purple-500" />}
                  iconBg="bg-purple-500/10"
                  label="Manage Organization"
                  href={d.defaultOrg ? `/workspaces/${d.defaultOrg.id}` : "/workspaces"}
                />
                <QuickActionRow
                  icon={<Settings className="h-3.5 w-3.5 text-green-500" />}
                  iconBg="bg-green-500/10"
                  label="Settings"
                  href="/settings/profile"
                />
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  )
}
