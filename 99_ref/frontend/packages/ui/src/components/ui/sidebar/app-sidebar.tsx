"use client"

import * as React from "react"
import {
  LayoutDashboard,
  Layers,
  Settings,
  User2,
  LogOut,
  ShieldCheck,
  KeyRound,
  Bell,
  Lock,
  Flag,
  Users,
  ScrollText,
  UserCog,
  Building2,
  UsersRound,
  ChevronLeft,
  ShieldAlert,
  ToggleLeft,
  Crown,
  Mail,
  Library,
  CheckSquare,
  FlaskConical,
  MessageSquare,
  Paperclip,
  Plug,
  Database,
  Zap,
  FileCheck,
  Play,
  Radio,
  ArrowUpFromLine,
  Share2,
  FlaskRound,
  Eye,
  Sun,
  Moon,
  MessageSquarePlus,
  BookOpen,
  Sparkles,
  Brain,
  FileCode2,
  BarChart3,
  ClipboardCheck,
  Boxes,
  ListTodo,
  Bot,
  Cpu,
  Wrench,
  Check,
  FileType,
  GitMerge,
  Activity,
  AlertCircle,
  ClipboardList,
  Globe,
} from "lucide-react"

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuBadge,
  SidebarMenuItem,
  SidebarMenuSkeleton,
  SidebarFooter,
  SidebarRail,
} from "./sidebar"

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../dropdown-menu"

import { Logo } from "../logo"
import { useTheme } from "next-themes"
import { cn } from "../../../lib/utils"
import { useBrowserPathname } from "./use-browser-pathname"

/** Badge counts for sidebar navigation items */
export interface SidebarBadgeCounts {
  // Compliance
  frameworks?: number
  controls?: number
  controlTests?: number
  // Risk & governance
  risks?: number
  openRisks?: number
  criticalRisks?: number
  tasks?: number
  openTasks?: number
  overdueTasks?: number
  // Notifications
  unreadNotifications?: number
  // Feedback
  feedbackTickets?: number
  // Compliance score (0-100)
  complianceScore?: number
  compliancePassingCount?: number
  complianceTotalCount?: number
}

export interface SidebarViewDefinition {
  id: string
  label: string
  color: string
  icon?: string | null
  description?: string
}

export interface AppSidebarProps {
  userName?: string
  userEmail?: string
  isSuperAdmin?: boolean
  variant?: "dashboard" | "settings" | "admin" | "sandbox" | "agent_sandbox"
  currentOrgId?: string
  currentOrgName?: string
  onSignOut?: () => void
  /** When set, only sidebar items whose URL matches one of these prefixes are shown (view-based filtering) */
  allowedRoutes?: string[]
  /** View badge label shown under the logo (e.g. "External Auditor") */
  viewLabel?: string
  /** View badge color */
  viewColor?: string
  /** View switching */
  availableViews?: SidebarViewDefinition[]
  activeViewId?: string
  onViewSelect?: (id: string) => void
  /** Badge counts for sidebar items */
  badgeCounts?: SidebarBadgeCounts
  /** Custom link component (e.g. Next.js Link) */
  linkComponent?: React.ComponentType<{ href: string; children: React.ReactNode; className?: string; target?: string; rel?: string;[key: string]: any }>
  /** Optional controlled path for non-browser hosts */
  currentPath?: string
  /** When true, show skeleton placeholders instead of nav items (prevents flash while access/views load) */
  loading?: boolean
  /** Visibility toggle for the auditor workspace entry */
  showAuditorWorkspace?: boolean
}

const navigateItems: { title: string; url: string; icon: typeof LayoutDashboard; badgeKey?: keyof SidebarBadgeCounts }[] = [
  { title: "Dashboard", url: "/dashboard", icon: LayoutDashboard },
]

const monitoringItems = [
  { title: "Live Monitoring", url: "/monitoring", icon: Activity, badgeKey: undefined },
  { title: "Control Tests", url: "/tests", icon: FlaskConical, badgeKey: "controlTests" as const },
  { title: "Asset Inventory", url: "/assets", icon: Boxes, badgeKey: undefined },
  { title: "Issues", url: "/issues", icon: AlertCircle, badgeKey: undefined },
]

const complianceItems = [
  { title: "Frameworks", url: "/frameworks", icon: Library, badgeKey: "frameworks" as const },
  { title: "Controls", url: "/controls", icon: Layers, badgeKey: "controls" as const },
  { title: "Tasks", url: "/tasks", icon: CheckSquare, badgeKey: "openTasks" as const },
]

const riskAndGovernanceItems = [
  { title: "Risk Registry", url: "/risks", icon: ShieldAlert, badgeKey: "risks" as const },
  { title: "Policies & Docs", url: "/policies", icon: BookOpen, badgeKey: undefined },
  { title: "Reports", url: "/reports", icon: BarChart3, badgeKey: undefined },
]

const auditItems = [
  { title: "Audit Management", url: "/audit-workspace/grc", icon: ShieldCheck },
  { title: "Auditor Workspace", url: "/audit-workspace/auditor", icon: FileCheck },
  // { title: "Fulfillment Queue", url: "/audit-workspace/engineering", icon: Wrench },
  { title: "Compliance Insights", url: "/audit-workspace/executive", icon: BarChart3 },
]

const workspaceItems = [
  { title: "Workspaces", url: "/workspaces", icon: Layers },
]

const settingsItems = [
  { title: "Profile", url: "/settings/profile", icon: User2 },
  { title: "Security", url: "/settings/security", icon: Lock },
  { title: "Manage Notifications", url: "/settings/notifications", icon: Bell },
  { title: "API Keys", url: "/settings/api-keys", icon: KeyRound },
]

const orgSettingsItems = [
  { title: "Overview", url: "/settings/org/profile", icon: Building2 },
  { title: "Workspaces", url: "/settings/org/workspaces", icon: Layers },
  { title: "Documents", url: "/settings/org/docs", icon: BookOpen },
]

const orgAccessControlItems = [
  { title: "Users", url: "/settings/org/users", icon: UserCog },
]

const orgConfigurationItems = [
  { title: "Invitations", url: "/settings/org/invitations", icon: Mail },
  { title: "Audit Log", url: "/settings/org/audit", icon: ScrollText },
]

const adminIdentityItems = [
  { title: "Overview", url: "/admin", icon: ShieldCheck },
  { title: "Users", url: "/admin/users", icon: UserCog },
  { title: "Groups", url: "/admin/groups", icon: UsersRound },
  { title: "Roles", url: "/admin/roles", icon: ShieldAlert },
  { title: "Organizations", url: "/admin/orgs", icon: Building2 },
]

const adminPlatformItems = [
  { title: "Feature Flags", url: "/admin/feature-flags", icon: Flag },
  { title: "License Profiles", url: "/admin/license-profiles", icon: Crown },
  { title: "Portal Views", url: "/admin/views", icon: Eye },
  { title: "Notifications", url: "/admin/notifications", icon: Bell },
]

const adminContentItems: { title: string; url: string; icon: typeof ShieldCheck; badgeKey?: keyof SidebarBadgeCounts }[] = [
  { title: "Feedback & Support", url: "/admin/feedback", icon: MessageSquarePlus, badgeKey: "feedbackTickets" },
  { title: "Comments", url: "/admin/comments", icon: MessageSquare },
  { title: "Attachments", url: "/admin/attachments", icon: Paperclip },
  { title: "Document Library", url: "/admin/docs", icon: BookOpen },
]

const adminAuditItems = [
  { title: "Audit Log", url: "/admin/audit", icon: ScrollText },
]

const adminGrcPlatformItems = [
  { title: "Framework Library", url: "/admin/frameworks", icon: Library },
  { title: "Controls Library", url: "/admin/controls", icon: Layers },
  { title: "Control Test Library", url: "/admin/control-test-library", icon: FlaskConical },
  { title: "Dataset Library", url: "/admin/dataset-library", icon: Database },
  { title: "Risk Registry Library", url: "/admin/risk-library", icon: ShieldAlert },
  { title: "Assessments", url: "/admin/assessments", icon: ClipboardCheck },
  { title: "Task Management", url: "/admin/tasks", icon: CheckSquare },
  { title: "Questionnaires", url: "/admin/questionnaires", icon: ClipboardList },
]

const adminLibraryItems = [
  { title: "Frameworks", url: "/admin/library/frameworks", icon: Library },
  { title: "Framework Builder", url: "/admin/library/frameworks/builder", icon: Sparkles },
]

const adminAiPlatformItems = [
  { title: "Overview", url: "/admin/ai", icon: Sparkles },
  { title: "Agent Configs", url: "/admin/ai/agent-configs", icon: Brain },
  { title: "Prompts", url: "/admin/ai/prompts", icon: FileCode2 },
  { title: "Approvals", url: "/admin/ai/approvals", icon: MessageSquare },
  { title: "Reporting", url: "/admin/ai/reporting", icon: BarChart3 },
  { title: "Job Queue", url: "/admin/ai/jobs", icon: ListTodo },
  { title: "PDF Templates", url: "/admin/ai/pdf-templates", icon: FileType },
  { title: "Risk Advisor", url: "/admin/ai/risk-advisor", icon: GitMerge },
  { title: "Test Linker", url: "/admin/ai/test-linker", icon: FlaskConical },
]

const sandboxDataSourceItems = [
  { title: "Connectors", url: "/sandbox/connectors", icon: Plug },
  { title: "Datasets", url: "/sandbox/datasets", icon: Database },
]

const sandboxSignalItems = [
  { title: "Signals", url: "/sandbox/signals", icon: Zap },
  { title: "Threat Types", url: "/sandbox/threat-types", icon: ShieldAlert },
  { title: "Control Tests", url: "/sandbox/policies", icon: FileCheck },
  { title: "Pipeline Queue", url: "/sandbox/pipeline-queue", icon: BarChart3 },
]

const sandboxTestingItems = [
  { title: "Sandbox Runs", url: "/sandbox/runs", icon: Play },
  { title: "Live Sessions", url: "/sandbox/live-sessions", icon: Radio },
]

const sandboxLibraryItems = [
  { title: "Global Library", url: "/sandbox/global-library", icon: Globe },
  { title: "Control Libraries", url: "/sandbox/libraries", icon: Library },
  { title: "Promotions", url: "/sandbox/promotions", icon: ArrowUpFromLine },
]

const sandboxIntegrationItems = [
  { title: "SSF Streams", url: "/sandbox/ssf-streams", icon: Share2 },
]

function normalizePath(path: string): string {
  if (!path) return "/"
  return path.length > 1 && path.endsWith("/") ? path.slice(0, -1) : path
}

function isPathMatch(pathname: string, url: string): boolean {
  const currentPath = normalizePath(pathname)
  const targetPath = normalizePath(url)

  return currentPath === targetPath || currentPath.startsWith(`${targetPath}/`)
}

function getActiveUrl(pathname: string, urls: string[]): string | null {
  const matchingUrls = urls
    .map((url) => normalizePath(url))
    .filter((url) => isPathMatch(pathname, url))
    .sort((left, right) => right.length - left.length)

  return matchingUrls[0] ?? null
}

function ComplianceScoreWidget({ score, passing, total }: { score: number; passing: number; total: number }) {
  const radius = 20
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference
  const color = score >= 80 ? "#22c55e" : score >= 60 ? "#eab308" : "#ef4444"

  return (
    <div className="flex items-center gap-3 mt-2 px-1 py-2 rounded-lg bg-sidebar-accent/30">
      <div className="relative shrink-0">
        <svg width="48" height="48" viewBox="0 0 48 48" className="-rotate-90">
          <circle cx="24" cy="24" r={radius} fill="none" stroke="currentColor" strokeWidth="4" className="text-sidebar-border" />
          <circle cx="24" cy="24" r={radius} fill="none" stroke={color} strokeWidth="4" strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={offset} className="transition-all duration-700" />
        </svg>
        <span className="absolute inset-0 flex items-center justify-center text-[11px] font-bold" style={{ color }}>{score}%</span>
      </div>
      <div className="flex flex-col min-w-0">
        <span className="text-[10px] font-medium uppercase tracking-wider text-sidebar-foreground/60">Compliance Score</span>
        <span className="text-xs text-sidebar-foreground/80">{passing} / {total} passing</span>
      </div>
    </div>
  )
}

function ThemeToggleRow() {
  const [mounted, setMounted] = React.useState(false)
  const { resolvedTheme, setTheme } = useTheme()
  React.useEffect(() => { setMounted(true) }, [])
  const isDark = mounted && resolvedTheme === "dark"
  return (
    <div className="flex items-center justify-between px-2 py-1.5">
      <div className="flex items-center gap-2.5 text-sm text-muted-foreground">
        {isDark ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
        <span>{isDark ? "Dark" : "Light"} mode</span>
      </div>
      <button
        type="button"
        aria-label="Toggle theme"
        onClick={() => setTheme(isDark ? "light" : "dark")}
        className="relative inline-flex h-5 w-10 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent bg-muted transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        <span
          className={`pointer-events-none relative z-10 h-4 w-4 rounded-full bg-foreground shadow-sm ring-0 transition-transform duration-200 ${isDark ? "translate-x-5" : "translate-x-0"}`}
        />
      </button>
    </div>
  )
}

/** Skeleton placeholder for the dashboard sidebar — matches group structure */
function SidebarContentSkeleton() {
  return (
    <>
      {/* Dashboard */}
      <SidebarGroup>
        <SidebarGroupContent>
          <SidebarMenu>
            <SidebarMenuItem><SidebarMenuSkeleton showIcon /></SidebarMenuItem>
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>
      {/* Monitoring */}
      <SidebarGroup>
        <SidebarGroupLabel className="opacity-50">
          <span className="inline-block h-3 w-16 rounded bg-sidebar-accent/40 animate-pulse" />
        </SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            {[...Array(4)].map((_, i) => (
              <SidebarMenuItem key={`mon-${i}`}><SidebarMenuSkeleton showIcon /></SidebarMenuItem>
            ))}
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>
      {/* Compliance */}
      <SidebarGroup>
        <SidebarGroupLabel className="opacity-50">
          <span className="inline-block h-3 w-20 rounded bg-sidebar-accent/40 animate-pulse" />
        </SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            {[...Array(3)].map((_, i) => (
              <SidebarMenuItem key={`comp-${i}`}><SidebarMenuSkeleton showIcon /></SidebarMenuItem>
            ))}
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>
      {/* Risk & Governance */}
      <SidebarGroup>
        <SidebarGroupLabel className="opacity-50">
          <span className="inline-block h-3 w-28 rounded bg-sidebar-accent/40 animate-pulse" />
        </SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            {[...Array(3)].map((_, i) => (
              <SidebarMenuItem key={`risk-${i}`}><SidebarMenuSkeleton showIcon /></SidebarMenuItem>
            ))}
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>
      {/* Audit Workspace */}
      <SidebarGroup>
        <SidebarGroupLabel className="opacity-50">
          <span className="inline-block h-3 w-24 rounded bg-sidebar-accent/40 animate-pulse" />
        </SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            {[...Array(3)].map((_, i) => (
              <SidebarMenuItem key={`audit-${i}`}><SidebarMenuSkeleton showIcon /></SidebarMenuItem>
            ))}
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>
    </>
  )
}

export function AppSidebar({
  userName,
  userEmail,
  isSuperAdmin,
  variant = "dashboard",
  currentOrgId,
  currentOrgName,
  onSignOut,
  allowedRoutes,
  viewLabel,
  viewColor,
  availableViews,
  activeViewId,
  onViewSelect,
  badgeCounts,
  linkComponent: LinkComp = "a" as any,
  currentPath,
  loading = false,
  showAuditorWorkspace = true,
}: AppSidebarProps) {
  const pathname = useBrowserPathname(currentPath)
  const displayLabel = userName || userEmail || "My Account"
  const initials = userName
    ? userName.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()
    : "?"

  // View-based route filter — when allowedRoutes is set, only show items whose URL matches
  const isItemAllowed = (url: string) => {
    if (!allowedRoutes) return true
    return allowedRoutes.some(prefix => prefix === "/*" || url === prefix || url.startsWith(prefix + "/"))
  }

  const filterItems = <T extends { url: string }>(items: T[]) => items.filter(i => isItemAllowed(i.url))
  const visibleAuditItems = React.useMemo(
    () => auditItems.filter((item) => item.url !== "/audit-workspace/auditor" || showAuditorWorkspace),
    [showAuditorWorkspace],
  )
  const activeUrl = React.useMemo(() => {
    const urls =
      variant === "dashboard"
        ? [
          ...filterItems(navigateItems).map((item) => item.url),
          ...filterItems(monitoringItems).map((item) => item.url),
          ...filterItems(complianceItems).map((item) => item.url),
          ...filterItems(riskAndGovernanceItems).map((item) => item.url),
          ...filterItems(visibleAuditItems).map((item) => item.url),
          ...(isItemAllowed("/sandbox") ? ["/sandbox"] : []),
        ]
        : variant === "settings"
          ? [
            ...settingsItems
              .filter((item) => item.url !== "/settings/api-keys" || !!isSuperAdmin)
              .map((item) => item.url),
            ...(currentOrgId
              ? [
                ...orgSettingsItems.map((item) => item.url),
                ...orgAccessControlItems.map((item) => item.url),
                ...orgConfigurationItems.map((item) => item.url),
              ]
              : []),
          ]
          : variant === "admin"
            ? [
              ...adminIdentityItems.map((item) => item.url),
              ...adminPlatformItems.map((item) => item.url),
              ...adminGrcPlatformItems.map((item) => item.url),
              ...adminLibraryItems.map((item) => item.url),
              ...adminContentItems.map((item) => item.url),
              ...adminAuditItems.map((item) => item.url),
              ...adminAiPlatformItems.map((item) => item.url),
              "/sandbox",
            ]
            : [
              "/sandbox",
              ...sandboxDataSourceItems.map((item) => item.url),
              ...sandboxSignalItems.map((item) => item.url),
              ...sandboxTestingItems.map((item) => item.url),
              ...sandboxLibraryItems.map((item) => item.url),
              ...sandboxIntegrationItems.map((item) => item.url),
              "/feedback",
            ]

    return getActiveUrl(pathname ?? "/", urls)
  }, [currentOrgId, isSuperAdmin, pathname, variant, allowedRoutes, visibleAuditItems])

  const isSidebarItemActive = React.useCallback(
    (url: string) => activeUrl === normalizePath(url),
    [activeUrl],
  )

  return (
    <Sidebar variant="sidebar" collapsible="offcanvas">
      {/* Logo header */}
      <SidebarHeader className="px-4 py-3 border-b border-sidebar-border">
        <Logo className="h-6" />
        {viewLabel && (
          <span
            className="inline-flex items-center gap-1.5 mt-1.5 px-2.5 py-1 rounded-md text-[10px] font-semibold"
            style={{
              backgroundColor: viewColor ? `${viewColor}15` : undefined,
              color: viewColor ?? undefined,
              border: viewColor ? `1px solid ${viewColor}30` : undefined,
            }}
          >
            {viewLabel}
          </span>
        )}
        {variant === "dashboard" && (
          <ComplianceScoreWidget
            score={badgeCounts?.complianceScore ?? 0}
            passing={badgeCounts?.compliancePassingCount ?? 0}
            total={badgeCounts?.complianceTotalCount ?? 0}
          />
        )}
      </SidebarHeader>

      <SidebarContent>
        {/* ── DASHBOARD variant ─────────────────────────────────────── */}
        {variant === "dashboard" && loading && <SidebarContentSkeleton />}
        {variant === "dashboard" && !loading && (
          <>
            {filterItems(navigateItems).length > 0 && (
              <SidebarGroup>
                <SidebarGroupContent>
                  <SidebarMenu>
                    {filterItems(navigateItems).map((item) => (
                      <SidebarMenuItem key={item.title}>
                        <SidebarMenuButton asChild isActive={isSidebarItemActive(item.url)}>
                          <LinkComp
                            href={item.url}
                            aria-current={isSidebarItemActive(item.url) ? "page" : undefined}
                            target={item.url === "/sandbox" ? "_blank" : undefined}
                            rel={item.url === "/sandbox" ? "noopener noreferrer" : undefined}
                          >
                            <item.icon />
                            <span>{item.title}</span>
                          </LinkComp>
                        </SidebarMenuButton>
                        {item.badgeKey && badgeCounts?.[item.badgeKey] != null && badgeCounts[item.badgeKey]! > 0 && (
                          <SidebarMenuBadge>{badgeCounts[item.badgeKey]}</SidebarMenuBadge>
                        )}
                      </SidebarMenuItem>
                    ))}
                  </SidebarMenu>
                </SidebarGroupContent>
              </SidebarGroup>
            )}

            {filterItems(monitoringItems).length > 0 && (
              <SidebarGroup>
                <SidebarGroupLabel>Monitoring</SidebarGroupLabel>
                <SidebarGroupContent>
                  <SidebarMenu>
                    {filterItems(monitoringItems).map((item) => (
                      <SidebarMenuItem key={item.title}>
                        <SidebarMenuButton asChild isActive={isSidebarItemActive(item.url)}>
                          <LinkComp href={item.url} aria-current={isSidebarItemActive(item.url) ? "page" : undefined}>
                            <item.icon />
                            <span>{item.title}</span>
                          </LinkComp>
                        </SidebarMenuButton>
                        {item.badgeKey && badgeCounts?.[item.badgeKey] != null && badgeCounts[item.badgeKey]! > 0 && (
                          <SidebarMenuBadge>{badgeCounts[item.badgeKey]}</SidebarMenuBadge>
                        )}
                      </SidebarMenuItem>
                    ))}
                  </SidebarMenu>
                </SidebarGroupContent>
              </SidebarGroup>
            )}

            {filterItems(complianceItems).length > 0 && (
              <SidebarGroup>
                <SidebarGroupLabel>Compliance</SidebarGroupLabel>
                <SidebarGroupContent>
                  <SidebarMenu>
                    {filterItems(complianceItems).map((item) => (
                      <SidebarMenuItem key={item.title}>
                        <SidebarMenuButton asChild isActive={isSidebarItemActive(item.url)}>
                          <LinkComp href={item.url} aria-current={isSidebarItemActive(item.url) ? "page" : undefined}>
                            <item.icon />
                            <span>{item.title}</span>
                          </LinkComp>
                        </SidebarMenuButton>
                        {item.badgeKey && badgeCounts?.[item.badgeKey] != null && badgeCounts[item.badgeKey]! > 0 && (
                          <SidebarMenuBadge>{badgeCounts[item.badgeKey]}</SidebarMenuBadge>
                        )}
                      </SidebarMenuItem>
                    ))}
                  </SidebarMenu>
                </SidebarGroupContent>
              </SidebarGroup>
            )}

            {filterItems(riskAndGovernanceItems).length > 0 && (
              <SidebarGroup>
                <SidebarGroupLabel>Risk &amp; Governance</SidebarGroupLabel>
                <SidebarGroupContent>
                  <SidebarMenu>
                    {filterItems(riskAndGovernanceItems).map((item) => (
                      <SidebarMenuItem key={item.title}>
                        <SidebarMenuButton asChild isActive={isSidebarItemActive(item.url)}>
                          <LinkComp href={item.url} aria-current={isSidebarItemActive(item.url) ? "page" : undefined}>
                            <item.icon />
                            <span>{item.title}</span>
                          </LinkComp>
                        </SidebarMenuButton>
                        {item.badgeKey && badgeCounts?.[item.badgeKey] != null && badgeCounts[item.badgeKey]! > 0 && (
                          <SidebarMenuBadge>{badgeCounts[item.badgeKey]}</SidebarMenuBadge>
                        )}
                      </SidebarMenuItem>
                    ))}
                  </SidebarMenu>
                </SidebarGroupContent>
              </SidebarGroup>
            )}

            {filterItems(visibleAuditItems).length > 0 && (
              <SidebarGroup>
                <SidebarGroupLabel>Audit Workspace</SidebarGroupLabel>
                <SidebarGroupContent>
                  <SidebarMenu>
                    {filterItems(visibleAuditItems).map((item) => (
                      <SidebarMenuItem key={item.title}>
                        <SidebarMenuButton asChild isActive={isSidebarItemActive(item.url)}>
                          <LinkComp href={item.url} aria-current={isSidebarItemActive(item.url) ? "page" : undefined}>
                            <item.icon />
                            <span>{item.title}</span>
                          </LinkComp>
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                    ))}
                  </SidebarMenu>
                </SidebarGroupContent>
              </SidebarGroup>
            )}

            {/* <SidebarGroup>
              <SidebarGroupLabel>Intelligence</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {isItemAllowed("/copilot") && (
                    <SidebarMenuItem>
                      <SidebarMenuButton asChild>
                        <LinkComp href="/copilot">
                          <Sparkles />
                          <span>AI Copilot</span>
                        </LinkComp>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  )}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup> */}

            {isSuperAdmin && (
              <SidebarGroup>
                <SidebarGroupLabel>Projects</SidebarGroupLabel>
                <SidebarGroupContent>
                  <SidebarMenu>
                    <SidebarMenuItem>
                      <SidebarMenuButton asChild isActive={isSidebarItemActive("/sandbox")}>
                        <LinkComp
                          href="/sandbox"
                          aria-current={isSidebarItemActive("/sandbox") ? "page" : undefined}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          <FlaskRound />
                          <span>K-Control Sandbox</span>
                        </LinkComp>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                    {/* <SidebarMenuItem>
                    <SidebarMenuButton asChild>
                      <a href="/agent-sandbox">
                        <Bot />
                        <span>Agent Sandbox</span>
                      </a>
                    </SidebarMenuButton>
                  </SidebarMenuItem> */}
                  </SidebarMenu>
                </SidebarGroupContent>
              </SidebarGroup>
            )}


          </>
        )}

        {/* ── SETTINGS variant ──────────────────────────────────────── */}
        {variant === "settings" && (
          <>
            <SidebarGroup>
              <SidebarGroupContent>
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild>
                      <LinkComp href="/dashboard">
                        <ChevronLeft />
                        <span>Back to K-Control</span>
                      </LinkComp>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            <SidebarGroup>
              <SidebarGroupLabel>Account</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {settingsItems
                    .filter((item) => item.url !== "/settings/api-keys" || !!isSuperAdmin)
                    .map((item) => (
                      <SidebarMenuItem key={item.title}>
                        <SidebarMenuButton asChild isActive={isSidebarItemActive(item.url)}>
                          <LinkComp href={item.url} aria-current={isSidebarItemActive(item.url) ? "page" : undefined}>
                            <item.icon />
                            <span>{item.title}</span>
                          </LinkComp>
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                    ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            {currentOrgId && (
              <>
                <SidebarGroup>
                  <SidebarGroupLabel className="truncate flex items-center gap-1.5">
                    <Building2 className="h-3 w-3 shrink-0 opacity-60" />
                    <span className="truncate">{currentOrgName ?? "Organization"}</span>
                  </SidebarGroupLabel>
                  <SidebarGroupContent>
                    <SidebarMenu>
                      {orgSettingsItems.map((item) => (
                        <SidebarMenuItem key={item.title}>
                          <SidebarMenuButton asChild isActive={isSidebarItemActive(item.url)}>
                            <LinkComp href={item.url} aria-current={isSidebarItemActive(item.url) ? "page" : undefined}>
                              <item.icon />
                              <span>{item.title}</span>
                            </LinkComp>
                          </SidebarMenuButton>
                        </SidebarMenuItem>
                      ))}
                    </SidebarMenu>
                  </SidebarGroupContent>
                </SidebarGroup>

                <SidebarGroup>
                  <SidebarGroupLabel>Access Control</SidebarGroupLabel>
                  <SidebarGroupContent>
                    <SidebarMenu>
                      {orgAccessControlItems.map((item) => (
                        <SidebarMenuItem key={item.title}>
                          <SidebarMenuButton asChild isActive={isSidebarItemActive(item.url)}>
                            <LinkComp href={item.url} aria-current={isSidebarItemActive(item.url) ? "page" : undefined}>
                              <item.icon />
                              <span>{item.title}</span>
                            </LinkComp>
                          </SidebarMenuButton>
                        </SidebarMenuItem>
                      ))}
                    </SidebarMenu>
                  </SidebarGroupContent>
                </SidebarGroup>

                <SidebarGroup>
                  <SidebarGroupLabel>Configuration</SidebarGroupLabel>
                  <SidebarGroupContent>
                    <SidebarMenu>
                      {orgConfigurationItems.map((item) => (
                        <SidebarMenuItem key={item.title}>
                          <SidebarMenuButton asChild isActive={isSidebarItemActive(item.url)}>
                            <LinkComp href={item.url} aria-current={isSidebarItemActive(item.url) ? "page" : undefined}>
                              <item.icon />
                              <span>{item.title}</span>
                            </LinkComp>
                          </SidebarMenuButton>
                        </SidebarMenuItem>
                      ))}
                    </SidebarMenu>
                  </SidebarGroupContent>
                </SidebarGroup>
              </>
            )}
          </>
        )}

        {/* ── ADMIN variant ─────────────────────────────────────────── */}
        {variant === "admin" && (
          <>
            <SidebarGroup>
              <SidebarGroupContent>
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild>
                      <LinkComp href="/dashboard">
                        <ChevronLeft />
                        <span>Back to K-Control</span>
                      </LinkComp>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            <SidebarGroup>
              <SidebarGroupLabel>Identity &amp; Access</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {adminIdentityItems.map((item) => (
                    <SidebarMenuItem key={item.title}>
                      <SidebarMenuButton asChild isActive={isSidebarItemActive(item.url)}>
                        <LinkComp href={item.url} aria-current={isSidebarItemActive(item.url) ? "page" : undefined}>
                          <item.icon />
                          <span>{item.title}</span>
                        </LinkComp>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            <SidebarGroup>
              <SidebarGroupLabel>Platform</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {adminPlatformItems.map((item) => (
                    <SidebarMenuItem key={item.title}>
                      <SidebarMenuButton asChild isActive={isSidebarItemActive(item.url)}>
                        <LinkComp href={item.url} aria-current={isSidebarItemActive(item.url) ? "page" : undefined}>
                          <item.icon />
                          <span>{item.title}</span>
                        </LinkComp>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            <SidebarGroup>
              <SidebarGroupLabel>GRC Platform</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {adminGrcPlatformItems.map((item) => (
                    <SidebarMenuItem key={item.title}>
                      <SidebarMenuButton asChild isActive={isSidebarItemActive(item.url)}>
                        <LinkComp href={item.url} aria-current={isSidebarItemActive(item.url) ? "page" : undefined}>
                          <item.icon />
                          <span>{item.title}</span>
                        </LinkComp>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            <SidebarGroup>
              <SidebarGroupLabel>Library</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {adminLibraryItems.map((item) => (
                    <SidebarMenuItem key={item.title}>
                      <SidebarMenuButton asChild isActive={isSidebarItemActive(item.url)}>
                        <LinkComp href={item.url} aria-current={isSidebarItemActive(item.url) ? "page" : undefined}>
                          <item.icon />
                          <span>{item.title}</span>
                        </LinkComp>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            <SidebarGroup>
              <SidebarGroupLabel>Content</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {adminContentItems.map((item) => (
                    <SidebarMenuItem key={item.title}>
                      <SidebarMenuButton asChild isActive={isSidebarItemActive(item.url)}>
                        <LinkComp href={item.url} aria-current={isSidebarItemActive(item.url) ? "page" : undefined}>
                          <item.icon />
                          <span>{item.title}</span>
                        </LinkComp>
                      </SidebarMenuButton>
                      {item.badgeKey && badgeCounts?.[item.badgeKey] != null && badgeCounts[item.badgeKey]! > 0 && (
                        <SidebarMenuBadge>{badgeCounts[item.badgeKey]}</SidebarMenuBadge>
                      )}
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            <SidebarGroup>
              <SidebarGroupLabel>Audit</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {adminAuditItems.map((item) => (
                    <SidebarMenuItem key={item.title}>
                      <SidebarMenuButton asChild isActive={isSidebarItemActive(item.url)}>
                        <LinkComp href={item.url} aria-current={isSidebarItemActive(item.url) ? "page" : undefined}>
                          <item.icon />
                          <span>{item.title}</span>
                        </LinkComp>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            <SidebarGroup>
              <SidebarGroupLabel>AI Platform</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {adminAiPlatformItems.map((item) => (
                    <SidebarMenuItem key={item.title}>
                      <SidebarMenuButton asChild isActive={isSidebarItemActive(item.url)}>
                        <LinkComp href={item.url} aria-current={isSidebarItemActive(item.url) ? "page" : undefined}>
                          <item.icon />
                          <span>{item.title}</span>
                        </LinkComp>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            <SidebarGroup>
              <SidebarGroupLabel>Products</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild isActive={isSidebarItemActive("/sandbox")}>
                      <LinkComp
                        href="/sandbox"
                        aria-current={isSidebarItemActive("/sandbox") ? "page" : undefined}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <FlaskRound />
                        <span>K-Control Sandbox</span>
                      </LinkComp>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </>
        )}

        {/* ── SANDBOX variant ────────────────────────────────────────── */}
        {variant === "sandbox" && (
          <>
            <SidebarGroup>
              <SidebarGroupContent>
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild>
                      <LinkComp href="/dashboard">
                        <ChevronLeft />
                        <span>K-Control</span>
                      </LinkComp>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            <SidebarGroup>
              <SidebarGroupContent>
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild isActive={isSidebarItemActive("/sandbox")}>
                      <LinkComp href="/sandbox" aria-current={isSidebarItemActive("/sandbox") ? "page" : undefined}>
                        <FlaskRound />
                        <span>Overview</span>
                      </LinkComp>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            <SidebarGroup>
              <SidebarGroupLabel>Assets</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {sandboxDataSourceItems.map((item) => (
                    <SidebarMenuItem key={item.title}>
                      <SidebarMenuButton asChild isActive={isSidebarItemActive(item.url)}>
                        <LinkComp href={item.url} aria-current={isSidebarItemActive(item.url) ? "page" : undefined}>
                          <item.icon />
                          <span>{item.title}</span>
                        </LinkComp>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            <SidebarGroup>
              <SidebarGroupLabel>Signal Engineering</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {sandboxSignalItems.map((item) => (
                    <SidebarMenuItem key={item.title}>
                      <SidebarMenuButton asChild isActive={isSidebarItemActive(item.url)}>
                        <LinkComp href={item.url} aria-current={isSidebarItemActive(item.url) ? "page" : undefined}>
                          <item.icon />
                          <span>{item.title}</span>
                        </LinkComp>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            <SidebarGroup>
              <SidebarGroupLabel>Testing</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {sandboxTestingItems.map((item) => (
                    <SidebarMenuItem key={item.title}>
                      <SidebarMenuButton asChild isActive={isSidebarItemActive(item.url)}>
                        <LinkComp href={item.url} aria-current={isSidebarItemActive(item.url) ? "page" : undefined}>
                          <item.icon />
                          <span>{item.title}</span>
                        </LinkComp>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            <SidebarGroup>
              <SidebarGroupLabel>Libraries</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {sandboxLibraryItems.map((item) => (
                    <SidebarMenuItem key={item.title}>
                      <SidebarMenuButton asChild isActive={isSidebarItemActive(item.url)}>
                        <LinkComp href={item.url} aria-current={isSidebarItemActive(item.url) ? "page" : undefined}>
                          <item.icon />
                          <span>{item.title}</span>
                        </LinkComp>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            <SidebarGroup>
              <SidebarGroupLabel>Integration</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {sandboxIntegrationItems.map((item) => (
                    <SidebarMenuItem key={item.title}>
                      <SidebarMenuButton asChild isActive={isSidebarItemActive(item.url)}>
                        <LinkComp href={item.url} aria-current={isSidebarItemActive(item.url) ? "page" : undefined}>
                          <item.icon />
                          <span>{item.title}</span>
                        </LinkComp>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            <SidebarGroup>
              <SidebarGroupContent>
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild isActive={isSidebarItemActive("/feedback")}>
                      <LinkComp href="/feedback" aria-current={isSidebarItemActive("/feedback") ? "page" : undefined}>
                        <MessageSquarePlus />
                        <span>Feedback &amp; Support</span>
                      </LinkComp>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </>
        )}

        {variant === "agent_sandbox" && (
          <>
            {/* Back to K-Control */}
            <SidebarGroup>
              <SidebarGroupContent>
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild>
                      <a href="/dashboard">
                        <ChevronLeft />
                        <span>K-Control</span>
                      </a>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            {/* Overview */}
            <SidebarGroup>
              <SidebarGroupContent>
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild>
                      <a href="/agent-sandbox">
                        <Bot />
                        <span>Overview</span>
                      </a>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            {/* Platform Agents */}
            <SidebarGroup>
              <SidebarGroupLabel>Platform Agents</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild>
                      <a href="/agent-sandbox/playground">
                        <Play />
                        <span>Playground</span>
                      </a>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild>
                      <a href="/agent-sandbox/registry">
                        <Layers />
                        <span>Agent Registry</span>
                      </a>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            {/* Agent Builder */}
            <SidebarGroup>
              <SidebarGroupLabel>Agent Builder</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild>
                      <a href="/agent-sandbox/agents">
                        <Cpu />
                        <span>Custom Agents</span>
                      </a>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild>
                      <a href="/agent-sandbox/tools">
                        <Wrench />
                        <span>Agent Tools</span>
                      </a>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            {/* Testing */}
            <SidebarGroup>
              <SidebarGroupLabel>Testing</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild>
                      <a href="/agent-sandbox/scenarios">
                        <ClipboardCheck />
                        <span>Test Scenarios</span>
                      </a>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild>
                      <a href="/agent-sandbox/runs">
                        <Cpu />
                        <span>Agent Runs</span>
                      </a>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            {/* Feedback */}
            <SidebarGroup>
              <SidebarGroupContent>
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild>
                      <a href="/feedback">
                        <MessageSquarePlus />
                        <span>Feedback &amp; Support</span>
                      </a>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </>
        )}
      </SidebarContent>

      <SidebarFooter className="border-t border-sidebar-border">
        <SidebarMenu>
          <SidebarMenuItem>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <SidebarMenuButton size="lg">
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold select-none">
                    {initials}
                  </span>
                  <span className="flex flex-col items-start min-w-0 flex-1 overflow-hidden">
                    <span className="truncate text-sm font-semibold leading-tight">{displayLabel}</span>
                    <span className="truncate text-[10px] font-medium leading-tight opacity-50 flex items-center gap-1.5 mt-0.5" style={{ color: viewColor }}>
                      {viewColor && <span className="h-1 w-1 rounded-full shrink-0" style={{ backgroundColor: viewColor }} />}
                      {viewLabel || "K-Control User"}
                    </span>
                  </span>
                  <User2 className="ml-auto h-4 w-4 opacity-40" />
                </SidebarMenuButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                side="top"
                align="end"
                sideOffset={8}
                className="w-56 p-1.5"
              >
                {/* Identity */}
                <div className="px-2 py-2 mb-0.5 flex flex-col gap-1">
                  <span className="text-sm font-semibold text-foreground truncate leading-tight block">{displayLabel}</span>
                  <span className="text-[10px] font-medium text-muted-foreground/60 truncate leading-tight flex items-center gap-1.5" style={{ color: viewColor }}>
                    {viewColor && <span className="h-1 w-1 rounded-full shrink-0" style={{ backgroundColor: viewColor }} />}
                    {viewLabel || "Standard Access"}
                  </span>
                  {userEmail && (
                    <span className="text-[10px] text-muted-foreground/40 font-mono truncate leading-tight block mt-0.5">{userEmail}</span>
                  )}
                </div>
                <DropdownMenuSeparator />

                {/* View Switching */}
                {availableViews && availableViews.length > 1 && (
                  <>
                    <div className="px-2 py-1.5">
                      <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground/50 mb-1 px-1">
                        Switch View
                      </p>
                      <div className="grid gap-1">
                        {availableViews.map((view) => {
                          const isActive = view.id === activeViewId
                          return (
                            <DropdownMenuItem
                              key={view.id}
                              onSelect={() => onViewSelect?.(view.id)}
                              className={cn(
                                "gap-2.5 px-2 py-1.5 cursor-pointer rounded-md transition-all",
                                isActive ? "bg-sidebar-accent/50 text-foreground" : "text-muted-foreground hover:text-foreground hover:bg-sidebar-accent/30"
                              )}
                            >
                              <div
                                className="h-1.5 w-1.5 rounded-full shrink-0"
                                style={{
                                  backgroundColor: view.color,
                                  boxShadow: isActive ? `0 0 8px ${view.color}88` : 'none'
                                }}
                              />
                              <span className={cn("flex-1 truncate", isActive ? "font-bold" : "font-medium")}>
                                {view.label}
                              </span>
                              {isActive && <Check className="h-3 w-3 text-foreground/40" />}
                            </DropdownMenuItem>
                          )
                        })}
                      </div>
                    </div>
                    <DropdownMenuSeparator />
                  </>
                )}

                <DropdownMenuItem asChild className="gap-2.5 px-2 py-1.5 mt-0.5 cursor-pointer">
                  <LinkComp href="/settings/profile">
                    <Settings className="h-4 w-4 text-muted-foreground" />
                    <span>Settings</span>
                  </LinkComp>
                </DropdownMenuItem>

                {isSuperAdmin && (
                  <DropdownMenuItem asChild className="gap-2.5 px-2 py-1.5 cursor-pointer">
                    <LinkComp href="/admin">
                      <ShieldCheck className="h-4 w-4 text-primary" />
                      <span>Super Admin</span>
                    </LinkComp>
                  </DropdownMenuItem>
                )}

                <DropdownMenuSeparator className="mt-0.5" />
                <ThemeToggleRow />
                <DropdownMenuSeparator className="mt-0.5" />

                <DropdownMenuItem
                  className="gap-2.5 px-2 py-1.5 mt-0.5 cursor-pointer text-destructive focus:text-destructive focus:bg-destructive/10"
                  onSelect={onSignOut}
                >
                  <LogOut className="h-4 w-4" />
                  <span>Sign out</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  )
}
