"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import {
  ShieldCheck,
  Flag,
  Users,
  ScrollText,
  UserCog,
  Building2,
  UsersRound,
  Bell,
  Crown,
  ArrowRight,
  Layers,
  Activity,
  Library,
  ShieldAlert,
  CheckSquare,
} from "lucide-react"
import { listFeatureFlags, listAdminUsers, listGroups, listRoles } from "@/lib/api/admin"
import { listOrgs } from "@/lib/api/orgs"

// ── Types ─────────────────────────────────────────────────────────────────────

interface AdminStats {
  totalFlags: number
  activeFlags: number
  orgFlags: number
  totalOrgs: number
  activeOrgs: number
  totalUsers: number
  totalGroups: number
  totalRoles: number
}

// ── Admin card data ───────────────────────────────────────────────────────────

interface AdminCard {
  icon: React.ReactNode
  borderCls: string
  title: string
  description: string
  whyItMatters: string
  actionLabel: string
  href: string
  stat?: { label: string; value: number }
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function AdminPage() {
  const [stats, setStats] = useState<AdminStats | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const [flagsRes, orgsRes, usersRes, groupsRes, rolesRes] = await Promise.all([
          listFeatureFlags().catch(() => null),
          listOrgs().catch(() => []),
          listAdminUsers({ limit: 1 }).catch(() => null),
          listGroups().catch(() => null),
          listRoles().catch(() => null),
        ])
        setStats({
          totalFlags: flagsRes?.flags.length ?? 0,
          activeFlags: flagsRes?.flags.filter((f) => f.env_dev || f.env_staging || f.env_prod).length ?? 0,
          orgFlags: flagsRes?.flags.filter((f) => f.feature_scope === "org").length ?? 0,
          totalOrgs: orgsRes.length,
          activeOrgs: orgsRes.filter((o) => o.is_active).length,
          totalUsers: usersRes?.total ?? 0,
          totalGroups: groupsRes?.groups.length ?? 0,
          totalRoles: rolesRes?.roles.length ?? 0,
        })
      } catch {
        // Non-blocking — just won't show stats
      }
    }
    load()
  }, [])

  const adminCards: AdminCard[] = [
    {
      icon: <Flag className="h-5 w-5 text-primary" />,
      borderCls: "border-l-primary",
      title: "Feature Flags",
      description: "Control which features are enabled across environments (Dev, Staging, Production).",
      whyItMatters: "Toggle features per environment, set org visibility, and gate features by license tier. Changes here affect the entire platform.",
      actionLabel: "Manage Flags",
      href: "/admin/feature-flags",
      stat: stats ? { label: "flags", value: stats.totalFlags } : undefined,
    },
    {
      icon: <Building2 className="h-5 w-5 text-rose-500" />,
      borderCls: "border-l-rose-500",
      title: "Organizations & Licensing",
      description: "Manage all organizations, their workspaces, members, and license tiers.",
      whyItMatters: "Set license tiers (Free, Pro, Trial, Internal), configure resource limits, and manage workspace allocation per org.",
      actionLabel: "Manage Orgs",
      href: "/admin/orgs",
      stat: stats ? { label: "orgs", value: stats.totalOrgs } : undefined,
    },
    {
      icon: <Crown className="h-5 w-5 text-amber-500" />,
      borderCls: "border-l-amber-500",
      title: "License Profiles",
      description: "Define default limits and feature entitlements per license tier.",
      whyItMatters: "Profiles (Free, Pro, Enterprise, Partner) set baseline limits like max_users and max_workspaces. Update a profile once and all orgs on that tier inherit the change. Individual orgs can still have custom overrides.",
      actionLabel: "Manage Profiles",
      href: "/admin/license-profiles",
    },
    {
      icon: <Users className="h-5 w-5 text-purple-500" />,
      borderCls: "border-l-purple-500",
      title: "Roles",
      description: "Define roles and assign feature permissions to them.",
      whyItMatters: "Roles control what users can do. Each role gets specific feature permissions (e.g. 'org_management.create'). Users inherit permissions through group membership.",
      actionLabel: "Manage Roles",
      href: "/admin/roles",
      stat: stats ? { label: "roles", value: stats.totalRoles } : undefined,
    },
    {
      icon: <UsersRound className="h-5 w-5 text-blue-500" />,
      borderCls: "border-l-blue-500",
      title: "Groups",
      description: "Organize users into groups and assign roles to groups.",
      whyItMatters: "The permission chain: User \u2192 Group \u2192 Role \u2192 Permissions. Add a user to a group and they inherit all the roles (and permissions) assigned to that group.",
      actionLabel: "Manage Groups",
      href: "/admin/groups",
      stat: stats ? { label: "groups", value: stats.totalGroups } : undefined,
    },
    {
      icon: <UserCog className="h-5 w-5 text-amber-500" />,
      borderCls: "border-l-amber-500",
      title: "Platform Users",
      description: "View all registered users, their sessions, and account details.",
      whyItMatters: "Search users, view their linked accounts (Google, GitHub, etc.), manage sessions, and check their group memberships.",
      actionLabel: "View Users",
      href: "/admin/users",
      stat: stats ? { label: "users", value: stats.totalUsers } : undefined,
    },
    {
      icon: <ScrollText className="h-5 w-5 text-green-500" />,
      borderCls: "border-l-green-500",
      title: "Audit Log",
      description: "Complete audit trail of every action taken across the platform.",
      whyItMatters: "Track who did what, when, and from where. Every login, permission change, org update, and feature flag toggle is recorded.",
      actionLabel: "View Audit Log",
      href: "/admin/audit",
    },
    {
      icon: <Bell className="h-5 w-5 text-indigo-500" />,
      borderCls: "border-l-indigo-500",
      title: "Notifications",
      description: "Templates, rules, broadcasts, releases, and incidents.",
      whyItMatters: "Create notification templates, set up automated rules, send broadcasts to users, manage release announcements and incident communications.",
      actionLabel: "Manage Notifications",
      href: "/admin/notifications",
    },
    {
      icon: <Library className="h-5 w-5 text-teal-500" />,
      borderCls: "border-l-teal-500",
      title: "Framework Library",
      description: "Manage compliance and governance frameworks, versions, and controls.",
      whyItMatters: "Add, review, and publish frameworks (NIST, ISO, SOC 2, etc.). Each framework contains versioned control sets that map to your organization's compliance posture.",
      actionLabel: "Manage Frameworks",
      href: "/admin/frameworks",
    },
    {
      icon: <ShieldAlert className="h-5 w-5 text-red-500" />,
      borderCls: "border-l-red-500",
      title: "Risk Registry",
      description: "Track, assess, and manage organizational risks across all domains.",
      whyItMatters: "Register risks, assess inherent and residual scores, assign risk levels, and track treatment plans. Risks can be scoped to specific orgs and workspaces.",
      actionLabel: "Manage Risks",
      href: "/admin/risks",
    },
    {
      icon: <CheckSquare className="h-5 w-5 text-cyan-500" />,
      borderCls: "border-l-cyan-500",
      title: "Task Management",
      description: "Track GRC tasks, remediation actions, and compliance activities.",
      whyItMatters: "Create and assign tasks for risk remediation, control implementation, audit findings, and compliance activities. Track priorities, due dates, blockers, and comments.",
      actionLabel: "Manage Tasks",
      href: "/admin/tasks",
    },
  ]

  return (
    <div className="max-w-5xl space-y-8">
      {/* Header */}
      <div className="flex items-start gap-4">
        <div className="rounded-xl bg-primary/10 p-3 shrink-0">
          <ShieldCheck className="h-6 w-6 text-primary" />
        </div>
        <div className="flex flex-col gap-1">
          <h2 className="text-2xl font-semibold text-foreground">
            Super Admin Console
          </h2>
          <p className="text-sm text-muted-foreground">
            Platform-wide administration. Changes here affect all organizations and users.
          </p>
        </div>
      </div>

      {/* Live stats bar */}
      {stats && (
        <div className="flex gap-3 flex-wrap">
          {[
            { label: "Feature Flags", value: stats.totalFlags, icon: Flag, borderCls: "border-l-primary" },
            { label: "Active in Env", value: stats.activeFlags, icon: Activity, borderCls: "border-l-green-500" },
            { label: "Org-Scoped", value: stats.orgFlags, icon: Layers, borderCls: "border-l-blue-500" },
            { label: "Organizations", value: stats.totalOrgs, icon: Building2, borderCls: "border-l-rose-500" },
            { label: "Active Orgs", value: stats.activeOrgs, icon: Crown, borderCls: "border-l-emerald-500" },
            { label: "Users", value: stats.totalUsers, icon: UserCog, borderCls: "border-l-amber-500" },
            { label: "Groups", value: stats.totalGroups, icon: UsersRound, borderCls: "border-l-violet-500" },
            { label: "Roles", value: stats.totalRoles, icon: Users, borderCls: "border-l-purple-500" },
          ].map((s) => (
            <div
              key={s.label}
              className={`rounded-xl border border-l-[3px] ${s.borderCls} bg-card px-4 py-2.5 flex items-center gap-3`}
            >
              <div className="rounded-lg p-1.5 bg-muted">
                <s.icon className="h-3.5 w-3.5 text-muted-foreground" />
              </div>
              <div className="flex flex-col">
                <span className="text-xl font-bold tabular-nums text-foreground leading-none">{s.value}</span>
                <span className="text-[10px] text-muted-foreground">{s.label}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* How it works — only show key concepts */}
      <div className="rounded-xl border border-border bg-muted/20 px-5 py-4">
        <h3 className="text-sm font-semibold text-foreground mb-2">How K-Control access works</h3>
        <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <span className="rounded-md border border-border bg-card px-2 py-1 font-medium text-foreground">User</span>
          <ArrowRight className="h-3 w-3" />
          <span className="rounded-md border border-border bg-card px-2 py-1 font-medium text-foreground">Group</span>
          <ArrowRight className="h-3 w-3" />
          <span className="rounded-md border border-border bg-card px-2 py-1 font-medium text-foreground">Role</span>
          <ArrowRight className="h-3 w-3" />
          <span className="rounded-md border border-primary/30 bg-primary/10 px-2 py-1 font-medium text-primary">Permissions</span>
          <span className="ml-2 text-muted-foreground">|</span>
          <span className="rounded-md border border-border bg-card px-2 py-1 font-medium text-foreground">License Profile</span>
          <ArrowRight className="h-3 w-3" />
          <span className="rounded-md border border-amber-500/30 bg-amber-500/10 px-2 py-1 font-medium text-amber-500">Tier + Limits</span>
          <ArrowRight className="h-3 w-3" />
          <span className="rounded-md border border-border bg-card px-2 py-1 font-medium text-foreground">Org</span>
          <span className="ml-2 text-muted-foreground">|</span>
          <span className="rounded-md border border-border bg-card px-2 py-1 font-medium text-foreground">Feature Flags</span>
          <ArrowRight className="h-3 w-3" />
          <span className="rounded-md border border-purple-500/30 bg-purple-500/10 px-2 py-1 font-medium text-purple-500">Environments</span>
          <span className="text-muted-foreground">+</span>
          <span className="rounded-md border border-amber-500/30 bg-amber-500/10 px-2 py-1 font-medium text-amber-500">Required License</span>
          <span className="text-muted-foreground">+</span>
          <span className="rounded-md border border-green-500/30 bg-green-500/10 px-2 py-1 font-medium text-green-500">Org Visibility</span>
        </div>
      </div>

      {/* Elevated access warning */}
      <div className="rounded-xl border border-l-4 border-amber-500/30 border-l-amber-500 bg-amber-500/5 p-4">
        <p className="text-sm text-amber-700 dark:text-amber-400">
          You have elevated platform access. Changes made here affect all tenants and users.
        </p>
      </div>

      {/* Admin section cards */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {adminCards.map((card) => (
          <Link key={card.href} href={card.href}>
            <div
              className={`rounded-xl border border-l-[3px] ${card.borderCls} bg-card px-4 py-4 flex items-start gap-4 hover:bg-muted/20 transition-colors`}
            >
              <div className="shrink-0 rounded-lg p-2 bg-muted">
                {card.icon}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <p className="text-sm font-semibold">{card.title}</p>
                  {card.stat && (
                    <span className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
                      {card.stat.value} {card.stat.label}
                    </span>
                  )}
                </div>
                <p className="text-xs text-muted-foreground">{card.description}</p>
                <p className="text-xs text-muted-foreground/60 mt-1 leading-relaxed">{card.whyItMatters}</p>
              </div>
              <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0 mt-1" />
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
