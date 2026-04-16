"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Button } from "@kcontrol/ui"
import {
  FlaskRound,
  Plug,
  Zap,
  ShieldAlert,
  FileCheck,
  Radio,
  Library,
  ArrowRight,
  CalendarDays,
} from "lucide-react"
import { getSandboxStats } from "@/lib/api/sandbox"
import type { SandboxStats } from "@/lib/api/sandbox"
import { useSandboxOrgWorkspace } from "@/lib/context/SandboxOrgWorkspaceContext"
import { SandboxOrgWorkspaceSwitcher } from "@/components/layout/SandboxOrgWorkspaceSwitcher"

// ── Quick actions ─────────────────────────────────────────────────────────────

const quickActions = [
  {
    icon: <Plug className="h-4 w-4 text-blue-500" />,
    borderCls: "border-l-blue-500",
    title: "Create Connector",
    description: "Connect to cloud APIs, SaaS platforms, or custom data sources to ingest telemetry and configuration data.",
    href: "/sandbox/connectors",
    actionLabel: "Get Started",
  },
  {
    icon: <Zap className="h-4 w-4 text-amber-500" />,
    borderCls: "border-l-amber-500",
    title: "Build Signal",
    description: "Define detection logic that evaluates incoming data against compliance and security rules.",
    href: "/sandbox/signals",
    actionLabel: "Create Signal",
  },
  {
    icon: <Radio className="h-4 w-4 text-purple-500" />,
    borderCls: "border-l-purple-500",
    title: "Start Live Session",
    description: "Run signals against live data streams in real time. Monitor results and tune detection thresholds.",
    href: "/sandbox/live-sessions",
    actionLabel: "Launch Session",
  },
  {
    icon: <Library className="h-4 w-4 text-teal-500" />,
    borderCls: "border-l-teal-500",
    title: "Browse Libraries",
    description: "Explore pre-built control libraries from the community and promote validated controls to production.",
    href: "/sandbox/libraries",
    actionLabel: "Browse",
  },
]

// ── Page ──────────────────────────────────────────────────────────────────────

export default function SandboxPage() {
  const { selectedOrgId, selectedWorkspaceId, ready } = useSandboxOrgWorkspace()
  const [stats, setStats] = useState<SandboxStats | null>(null)
  const [statsLoading, setStatsLoading] = useState(true)

  const today = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  })

  useEffect(() => {
    if (!ready || !selectedOrgId) return
    setStatsLoading(true)
    getSandboxStats(selectedOrgId, selectedWorkspaceId || undefined)
      .then(setStats)
      .catch(() => setStats(null))
      .finally(() => setStatsLoading(false))
  }, [ready, selectedOrgId, selectedWorkspaceId])

  const statCards = [
    { label: "Active Connectors", value: stats?.connector_count ?? 0, icon: Plug, iconCls: "text-blue-500", borderCls: "border-l-blue-500", numCls: "text-blue-600 dark:text-blue-400" },
    { label: "Signals", value: stats?.signal_count ?? 0, icon: Zap, iconCls: "text-amber-500", borderCls: "border-l-amber-500", numCls: "text-amber-600 dark:text-amber-400" },
    { label: "Threat Types", value: stats?.threat_type_count ?? 0, icon: ShieldAlert, iconCls: "text-red-500", borderCls: "border-l-red-500", numCls: "text-red-600 dark:text-red-400" },
    { label: "Active Control Tests", value: stats?.active_policy_count ?? 0, icon: FileCheck, iconCls: "text-green-500", borderCls: "border-l-green-500", numCls: "text-green-600 dark:text-green-400" },
  ]

  return (
    <div className="max-w-5xl space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="rounded-xl bg-primary/10 p-3 shrink-0">
            <FlaskRound className="h-6 w-6 text-primary" />
          </div>
          <div className="flex flex-col gap-1">
            <h2 className="text-2xl font-semibold text-foreground">
              K-Control Sandbox
            </h2>
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <CalendarDays className="h-3 w-3" />
              <span>{today}</span>
            </div>
          </div>
        </div>
        <div className="shrink-0 pt-1">
          <SandboxOrgWorkspaceSwitcher />
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {statCards.map((s) => (
          <div key={s.label} className={`relative flex items-center gap-3 rounded-xl border border-l-[3px] ${s.borderCls} bg-card px-4 py-3`}>
            <div className="shrink-0 rounded-lg p-2 bg-muted">
              <s.icon className={`h-4 w-4 ${s.iconCls}`} />
            </div>
            <div className="min-w-0">
              {statsLoading ? (
                <span className="h-6 w-8 block bg-muted rounded animate-pulse" />
              ) : (
                <span className={`text-2xl font-bold tabular-nums leading-none ${s.numCls}`}>{s.value}</span>
              )}
              <span className="text-[11px] text-muted-foreground mt-0.5 block truncate">{s.label}</span>
            </div>
          </div>
        ))}
      </div>

      {/* How it works */}
      <div className="rounded-xl border border-border bg-muted/20 px-5 py-4">
        <h3 className="text-sm font-semibold text-foreground mb-2">
          How the Sandbox works
        </h3>
        <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <span className="rounded-md border border-border bg-card px-2 py-1 font-medium text-foreground">
            Connector
          </span>
          <ArrowRight className="h-3 w-3" />
          <span className="rounded-md border border-border bg-card px-2 py-1 font-medium text-foreground">
            Dataset
          </span>
          <ArrowRight className="h-3 w-3" />
          <span className="rounded-md border border-amber-500/30 bg-amber-500/10 px-2 py-1 font-medium text-amber-500">
            Signal
          </span>
          <ArrowRight className="h-3 w-3" />
          <span className="rounded-md border border-red-500/30 bg-red-500/10 px-2 py-1 font-medium text-red-500">
            Threat Type
          </span>
          <ArrowRight className="h-3 w-3" />
          <span className="rounded-md border border-green-500/30 bg-green-500/10 px-2 py-1 font-medium text-green-500">
            Control Test
          </span>
          <ArrowRight className="h-3 w-3" />
          <span className="rounded-md border border-purple-500/30 bg-purple-500/10 px-2 py-1 font-medium text-purple-500">
            Sandbox Run
          </span>
          <ArrowRight className="h-3 w-3" />
          <span className="rounded-md border border-primary/30 bg-primary/10 px-2 py-1 font-medium text-primary">
            Promote to Production
          </span>
        </div>
      </div>

      {/* Quick actions */}
      <div>
        <h3 className="text-sm font-semibold text-foreground mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
          {quickActions.map((card) => (
            <div key={card.href}
              className={`flex items-start gap-4 rounded-xl border border-l-[3px] ${card.borderCls} bg-card px-4 py-4 hover:bg-muted/20 transition-colors group`}>
              <div className="shrink-0 rounded-lg p-2 bg-muted mt-0.5">{card.icon}</div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-foreground mb-1">{card.title}</p>
                <p className="text-xs text-muted-foreground leading-relaxed mb-3">{card.description}</p>
                <Button variant="outline" size="sm" asChild className="gap-1.5 h-7 text-xs">
                  <Link href={card.href}>{card.actionLabel}<ArrowRight className="h-3 w-3" /></Link>
                </Button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
