"use client"

import * as React from "react"
import {
  ShieldCheck,
  Calendar,
  Plus,
  BarChart3,
  CheckCircle2,
  Clock,
  Search,
  Mail,
  Building2,
  AlertCircle,
  Loader2,
  Users,
  MessageSquare,
  FileCheck,
  ChevronRight,
  Layers,
  ClipboardList,
  Inbox,
  LayoutDashboard,
  UserCheck,
  Paperclip,
  CheckSquare,
  Settings,
  ChevronDown,
} from "lucide-react"
import { toast } from "sonner"

import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Badge,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Input,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  Label,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@kcontrol/ui"

import { useOrgWorkspace } from "@/lib/context/OrgWorkspaceContext"
import { useView } from "@/lib/context/ViewContext"
import { useAccess } from "@/components/providers/AccessProvider"
import { engagementsApi, type Engagement } from "@/lib/api/engagements"
import { dashboardApi, type GrcDashboardResponse } from "@/lib/api/dashboard"
import { useRouter } from "next/navigation"
import { listDeployments, listFrameworks, listVersions, deployFramework } from "@/lib/api/grc"
import type { FrameworkResponse } from "@/lib/types/grc"
import { FrameworksView } from "@/components/auditor/FrameworksView"
import { ControlsView } from "@/components/auditor/ControlsView"
import { FindingsView } from "@/components/auditor/FindingsView"
import { TasksView } from "@/components/auditor/TasksView"
import { EvidenceView } from "@/components/auditor/EvidenceView"
import { ReportsView } from "@/components/auditor/ReportsView"
import { GrcTeamPanel } from "@/components/grc/GrcTeamPanel"
import { getGrcTeam } from "@/lib/api/grcRoles"
import { generateReport } from "@/lib/api/ai"
import { MessagesTab } from "@/components/auditor/MessagesTab"

// New GRC Components
import { GrcEngagementTabs } from "@/components/grc/GrcEngagementTabs"
import { EngagementRequests } from "@/components/grc/EngagementRequests"

// ─── Shared Helpers ─────────────────────────────────────────────────────────

const statusVariants: Record<string, "success" | "warning" | "info" | "muted" | "secondary"> = {
  setup: "secondary",
  active: "info",
  review: "warning",
  completed: "success",
  closed: "muted",
}

function fmt(date?: string | null): string {
  if (!date) return "—"
  return new Date(date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
}

function HelpIcon({ title }: { title: string }) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button className="text-muted-foreground/30 hover:text-primary transition-colors">
          <HelpCircle className="h-3 w-3" />
        </button>
      </TooltipTrigger>
      <TooltipContent side="top" className="max-w-[200px] text-[11px] font-medium leading-relaxed p-3 bg-zinc-900 border-none shadow-2xl">
        <p>{title}</p>
      </TooltipContent>
    </Tooltip>
  )
}

function HelpCircle({ className }: { className?: string }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <circle cx="12" cy="12" r="10" />
      <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
      <line x1="12" y1="12.01" x2="12" y2="12.01" />
    </svg>
  )
}

function TrustScoreGauge({ score }: { score: number }) {
  const radius = 45
  const circ = 2 * Math.PI * radius
  const offset = circ - (Math.max(5, score) / 100) * circ
  const color = score > 80 ? "#6366f1" : score > 50 ? "#f97316" : "#ef4444"

  return (
    <div className="relative flex flex-col items-center justify-center">
      <svg className="h-32 w-32 -rotate-90">
        <circle cx="64" cy="64" r={radius} fill="transparent" stroke="currentColor" strokeWidth="8" className="text-muted/10" />
        <circle
          cx="64" cy="64" r={radius} fill="transparent" stroke={color} strokeWidth="8"
          strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-2xl font-black tracking-tighter tabular-nums">{Math.round(score)}%</span>
      </div>
    </div>
  )
}

function SimpleProgress({ value, color = "bg-primary" }: { value: number, color?: string }) {
  return (
    <div className="w-full bg-muted/20 rounded-full h-1.5 overflow-hidden">
      <div className={`${color} h-full transition-all duration-1000`} style={{ width: `${value}%` }} />
    </div>
  )
}

function StatItem({ icon: Icon, label, value, sub, colorClass = "text-muted-foreground" }: any) {
  return (
    <div className="p-6 flex flex-col justify-center">
      <div className={`flex items-center gap-2 ${colorClass} mb-4 opacity-70`}>
        <Icon className="h-3.5 w-3.5" />
        <span className="text-[10px] font-black uppercase tracking-widest">{label}</span>
      </div>
      <div className="text-4xl font-black tracking-tighter tabular-nums">{value}</div>
      <p className="text-[10px] text-muted-foreground mt-2 font-bold uppercase tracking-tighter">
        {sub}
      </p>
    </div>
  )
}

// ─── Engagement Card ──────────────────────────────────────────────────────────

interface EngagementCardProps {
  eng: Engagement
  onSelect: (eng: Engagement) => void
  onInvite: (eng: Engagement) => void
}

function EngagementCard({ eng, onSelect, onInvite }: EngagementCardProps) {
  const total = eng.total_controls_count || 0
  const verified = eng.verified_controls_count || 0
  const pct = total > 0 ? Math.round((verified / total) * 100) : 0

  return (
    <Card
      className="hover:shadow-lg transition-all cursor-pointer border-l-4 group bg-card/40 backdrop-blur-sm border-muted/20 hover:border-indigo-500/50"
      style={{ borderLeftColor: "#6366f1" }}
      onClick={() => onSelect(eng)}
    >
      <CardHeader className="flex flex-row items-start justify-between pb-3">
        <div className="space-y-1 flex-1 min-w-0">
          <CardTitle className="text-sm font-black uppercase tracking-tight truncate group-hover:text-indigo-400 transition-colors">{eng.engagement_name}</CardTitle>
          <div className="text-[10px] text-muted-foreground flex items-center gap-1.5 font-bold uppercase tracking-widest opacity-60">
            <Building2 className="h-3 w-3 shrink-0" />
            <span className="truncate">{eng.auditor_firm || "Unknown Firm"}</span>
          </div>
        </div>
        <div className="flex items-center gap-1 shrink-0 ml-2">
          <Badge variant={statusVariants[eng.status_code] ?? "secondary"} className="uppercase text-[8px] h-4 font-black tracking-widest border-none">
            {eng.status_name}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4 text-[10px] font-bold uppercase tracking-tighter">
          <div>
            <p className="opacity-40 mb-1">Audit Period</p>
            <p className="font-black truncate">{fmt(eng.audit_period_start)} → {fmt(eng.audit_period_end)}</p>
          </div>
          <div className="text-right">
            <p className="opacity-40 mb-1">Verified</p>
            <p className="font-black text-indigo-500">{verified} / {total}</p>
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between text-[9px] font-black uppercase tracking-widest mb-1.5 opacity-40">
            <span>Readiness Vector</span>
            <span>{pct}%</span>
          </div>
          <SimpleProgress value={pct} color="bg-indigo-500" />
        </div>

        <div className="flex items-center justify-between pt-1">
          <div className="flex gap-2">
            {eng.open_requests_count > 0 && (
              <Badge className="h-5 px-1.5 text-[8px] font-black uppercase tracking-widest bg-amber-500/10 text-amber-500 border-none">
                {eng.open_requests_count} PENDING REQ.
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-all">
            <Button
              variant="outline"
              size="sm"
              className="h-7 px-3 text-[9px] font-black uppercase tracking-[0.15em] rounded-lg border-muted/30 hover:border-indigo-500/40 hover:text-indigo-500"
              onClick={(e) => { e.stopPropagation(); onInvite(eng) }}
            >
              Invite
            </Button>
            <Button variant="ghost" size="sm" className="h-7 w-7 p-0 rounded-lg">
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// ─── Create Engagement Form State ─────────────────────────────────────────────

interface CreateEngagementForm {
  engagement_type: "readiness" | "audit"
  engagement_name: string
  engagement_code: string
  auditor_firm: string
  framework_deployment_id: string
  status_code: string
  scope_description: string
  audit_period_start: string
  audit_period_end: string
  target_completion_date: string
  lead_grc_sme: string
}

const INITIAL_CREATE_FORM: CreateEngagementForm = {
  engagement_type: "readiness",
  engagement_name: "",
  engagement_code: "",
  auditor_firm: "",
  framework_deployment_id: "",
  status_code: "setup",
  scope_description: "",
  audit_period_start: "",
  audit_period_end: "",
  target_completion_date: "",
  lead_grc_sme: "",
}

// ─── Main Page Component ─────────────────────────────────────────────────────

export default function GrcPortalPage() {
  const router = useRouter()
  const { activeViewDef } = useView()
  const { selectedOrgId, selectedWorkspaceId } = useOrgWorkspace()
  const { access } = useAccess()
  const accentColor = activeViewDef?.color ?? "#6366f1"

  // Navigation State
  const [selectedEngagement, setSelectedEngagement] = React.useState<Engagement | null>(null)
  const [portfolioTab, setPortfolioTab] = React.useState("dashboard")
  const [engagementTab, setEngagementTab] = React.useState("overview")

  // Data State
  const [dbData, setDbData] = React.useState<GrcDashboardResponse | null>(null)
  const [engagements, setEngagements] = React.useState<Engagement[]>([])
  const [team, setTeam] = React.useState<any[]>([])
  const [isLoading, setIsLoading] = React.useState(true)
  const [searchQuery, setSearchQuery] = React.useState("")

  // Create & Invite Dialog State
  const [isCreateOpen, setIsCreateOpen] = React.useState(false)
  const [createForm, setCreateForm] = React.useState<CreateEngagementForm>(INITIAL_CREATE_FORM)
  const [createLoading, setCreateLoading] = React.useState(false)
  const [createError, setCreateError] = React.useState<string | null>(null)
  const [deployments, setDeployments] = React.useState<FrameworkResponse[]>([])
  
  const [isInviteOpen, setIsInviteOpen] = React.useState(false)
  const [invitingEng, setInvitingEng] = React.useState<Engagement | null>(null)
  const [inviteEmail, setInviteEmail] = React.useState("")
  const [isInviting, setIsInviting] = React.useState(false)

  // Edit Engagement State
  const [isEditOpen, setIsEditOpen] = React.useState(false)
  const [editForm, setEditForm] = React.useState<Partial<Engagement>>({})
  const [isUpdating, setIsUpdating] = React.useState(false)

  // Messaging / Link handling
  const [selectedMessageEntity, setSelectedMessageEntity] = React.useState<{ type: string; id: string; title?: string } | undefined>()

  // ── Data Loading ──────────────────────────────────────────────────────────

  const fetchData = React.useCallback(async () => {
    if (!selectedOrgId) return
    setIsLoading(true)
    try {
      const [db, engs, deps, team] = await Promise.all([
        dashboardApi.getGrc(selectedOrgId).catch(() => null),
        engagementsApi.list(selectedOrgId).catch(() => []),
        listFrameworks({ is_active: true, scope_org_id: selectedOrgId }).catch(() => ({ items: [], total: 0 })),
        getGrcTeam(selectedOrgId).catch(() => ({ internal: [], auditors: [], vendors: [], total: 0 })),
      ])

      setDbData(db)
      setEngagements(engs)
      setDeployments(deps.items || [])
      setTeam([...(team?.internal || []), ...(team?.auditors || [])])
      
      // Sync selected engagement if it exists
      if (selectedEngagement) {
        const fresh = engs.find(e => e.id === selectedEngagement.id)
        if (fresh) setSelectedEngagement(fresh)
      }
    } catch (e) {
      console.error("Failed to load GRC data", e)
    } finally {
      setIsLoading(false)
    }
  }, [selectedOrgId, selectedEngagement?.id])

  React.useEffect(() => { fetchData() }, [fetchData])

  // Auto-populate creator as Lead Practitioner
  React.useEffect(() => {
    if (isCreateOpen && !createForm.lead_grc_sme && access?.user_id && team.length > 0) {
      const currentUser = team.find(m => m.user_id === access.user_id)
      if (currentUser) {
        const name = currentUser.display_name || currentUser.email
        if (name) {
          setCreateForm(prev => ({ ...prev, lead_grc_sme: name }))
        }
      }
    }
  }, [isCreateOpen, access?.user_id, team, createForm.lead_grc_sme])


  // ── Handlers ──────────────────────────────────────────────────────────────

  const handleSelectEngagement = (eng: Engagement | null) => {
    setSelectedEngagement(eng)
    if (eng) {
      setEngagementTab("overview")
    }
  }

  const handleCreate = async () => {
    if (!selectedOrgId) return
    if (!createForm.engagement_name.trim() || !createForm.framework_deployment_id) {
      setCreateError("Missing required fields.")
      return
    }

    setCreateLoading(true)
    setCreateError(null)
    try {
      const selectedFramework = deployments.find(f => f.id === createForm.framework_deployment_id)
      if (!selectedFramework) throw new Error("Please select a framework standard.")
      
      const frameworkId = selectedFramework.id
      let targetVersionId = ""
      const vers = await listVersions(frameworkId)
      if (vers.items && vers.items.length > 0) {
        const published = vers.items.find(v => v.lifecycle_state === 'published')
        targetVersionId = published ? published.id : vers.items[0].id
      }
      if (!targetVersionId) throw new Error("No published versions found.")

      let deploymentId = ""
      const existingDeps = await listDeployments(selectedOrgId)
      const match = existingDeps.items.find(d => d.framework_id === frameworkId && d.deployed_version_id === targetVersionId)
      if (match) {
        deploymentId = match.id
      } else {
        const newDep = await deployFramework({ org_id: selectedOrgId, framework_id: frameworkId, version_id: targetVersionId })
        deploymentId = newDep.id
      }

      await engagementsApi.create(selectedOrgId, {
        ...createForm,
        engagement_name: createForm.engagement_name.trim(),
        engagement_code: createForm.engagement_name.toLowerCase().replace(/[^a-z0-9]+/g, '_').slice(0, 30),
        framework_id: frameworkId,
        framework_deployment_id: deploymentId,
        auditor_firm: createForm.auditor_firm.trim() || (createForm.engagement_type === "readiness" ? "Internal" : ""),
      } as any)

      setIsCreateOpen(false)
      setCreateForm(INITIAL_CREATE_FORM)
      await fetchData()
      toast.success("Engagement launched successfully")
    } catch (err: any) {
      setCreateError(err.message || "Operation failed.")
    } finally {
      setCreateLoading(false)
    }
  }

  const handleInvite = async () => {
    if (!invitingEng || !inviteEmail.trim()) return
    setIsInviting(true)
    try {
      await engagementsApi.inviteAuditor(invitingEng.id, inviteEmail.trim())
      toast.success(`Access dispatched to ${inviteEmail}`)
      setIsInviteOpen(false)
      setInviteEmail("")
    } catch (e: any) {
      toast.error(e.message || "Invitation failure.")
    } finally {
      setIsInviting(false)
    }
  }

  const handleUpdateEngagement = async () => {
    if (!selectedEngagement) return
    setIsUpdating(true)
    try {
      await engagementsApi.update(selectedEngagement.id, editForm)
      toast.success("Engagement intelligence updated")
      setIsEditOpen(false)
      await fetchData()
    } catch (e: any) {
      toast.error(e.message || "Update failed")
    } finally {
      setIsUpdating(false)
    }
  }

  const handleMessageLink = (entity: { type: string; id: string; title?: string }) => {

    setSelectedMessageEntity(entity)
    setEngagementTab("messages")
  }

  // ── Derived State ─────────────────────────────────────────────────────────

  const topEngagement = React.useMemo(() => {
    if (!engagements.length) return null
    return engagements.reduce((best, cur) => {
      const bestPct = best.total_controls_count ? (best.verified_controls_count / best.total_controls_count) : 0
      const curPct = cur.total_controls_count ? (cur.verified_controls_count / cur.total_controls_count) : 0
      return curPct > bestPct ? cur : best
    })
  }, [engagements])

  const tabCounts = React.useMemo(() => ({
    requests: selectedEngagement?.open_requests_count || 0,
    findings: 0, // Placeholder
    tasks: 0, // Placeholder
    messages: 0, // Placeholder
  }), [selectedEngagement])

  // ── Render Views ──────────────────────────────────────────────────────────

  const renderPortfolioContent = () => {
    if (isLoading && !engagements.length) {
      return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
          <Loader2 className="h-10 w-10 animate-spin text-indigo-500" />
          <p className="text-[10px] font-black uppercase tracking-[0.2em] opacity-40">Compiling Risk Vectors...</p>
        </div>
      )
    }

    return (
      <div className="space-y-6 animate-in fade-in duration-700">
        <div className="flex items-center justify-between border-b border-muted/10 pb-6">
          <div className="space-y-0.5">
            <h1 className="text-2xl font-black tracking-tighter flex items-center gap-3 lowercase">
              <ShieldCheck className="h-7 w-7 text-indigo-500" />
              GRC COMMAND CENTER
            </h1>
            <p className="text-muted-foreground text-[10px] font-black uppercase tracking-[0.25em] opacity-60">
              Operational Intelligence & Strategic Risk Oversight
            </p>
          </div>
          <div className="flex items-center gap-3">
             <Button
                className="h-9 rounded-xl bg-indigo-600 px-4 text-[10px] font-black uppercase tracking-[0.2em] shadow-sm hover:bg-indigo-700"
                onClick={() => setIsCreateOpen(true)}
              >
                <Plus className="h-3.5 w-3.5" />
                Launch Engagement
              </Button>
            <Button variant="ghost" size="sm" className="h-9 px-4 rounded-xl font-black text-[10px] uppercase tracking-widest gap-2 hover:bg-muted/50" onClick={fetchData}>
              <BarChart3 className="h-3.5 w-3.5" />
              Refresh Data
            </Button>
          </div>
        </div>

        <Tabs value={portfolioTab} onValueChange={setPortfolioTab} className="space-y-6">
          <TabsList className="bg-muted/20 p-1 h-10 items-center rounded-xl backdrop-blur-sm border border-muted/10 w-fit">
            <TabsTrigger value="dashboard" className="gap-2 px-6 h-8 rounded-lg text-[10px] font-black uppercase tracking-widest data-[state=active]:bg-background data-[state=active]:shadow-sm">
              <LayoutDashboard className="h-3 w-3" />
              Dashboard
            </TabsTrigger>
            <TabsTrigger value="engagements" className="gap-2 px-6 h-8 rounded-lg text-[10px] font-black uppercase tracking-widest data-[state=active]:bg-background data-[state=active]:shadow-sm">
              <Layers className="h-3 w-3" />
              Engagements
            </TabsTrigger>
            <TabsTrigger value="frameworks" className="gap-2 px-6 h-8 rounded-lg text-[10px] font-black uppercase tracking-widest data-[state=active]:bg-background data-[state=active]:shadow-sm">
              <ClipboardList className="h-3 w-3" />
              Standards
            </TabsTrigger>
          </TabsList>

          <TabsContent value="dashboard" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
              <Card className="lg:col-span-3 border-none bg-gradient-to-br from-indigo-500/10 to-purple-500/10 flex flex-col items-center justify-center py-6 relative overflow-hidden group">
                <TrustScoreGauge score={dbData?.trust_score ?? 0} />
                <div className="text-center px-4 mt-3">
                  <div className="flex items-center justify-center gap-1.5 mb-1">
                    <p className="text-[10px] font-black uppercase tracking-[0.2em] text-indigo-500/60">Portfolio Health</p>
                    <HelpIcon title="Aggregate readiness and security posture across all frameworks." />
                  </div>
                  <p className="text-[11px] text-muted-foreground leading-tight italic max-w-[180px] mx-auto">Consolidated compliance maturity.</p>
                </div>
              </Card>

              <Card className="lg:col-span-9 bg-card/40 backdrop-blur-sm border-muted/20 overflow-hidden">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 h-full divide-y sm:divide-y-0 sm:divide-x divide-muted/10">
                  <StatItem icon={CheckCircle2} label="Pass Rate" value={`${Math.round(dbData?.test_stats.pass_rate ?? 0)}%`} sub={`${dbData?.test_stats.total_tests ?? 0} total controls`} colorClass="text-emerald-500" />
                  <StatItem icon={Clock} label="Org. Findings" value={dbData?.task_forecast.total_pending ?? 0} sub={`${dbData?.task_forecast.overdue ?? 0} strictly overdue`} colorClass="text-amber-500" />
                  <StatItem icon={Calendar} label="Due This Week" value={dbData?.task_forecast.due_this_week ?? 0} sub="Critical timelines" colorClass="text-sky-500" />
                  
                  <div className="p-6 flex flex-col justify-center bg-indigo-500/[0.02]">
                    <div className="flex items-center gap-2 text-indigo-500 mb-4 font-black">
                      <FileCheck className="h-3.5 w-3.5" />
                      <span className="text-[10px] uppercase tracking-widest">Priority Segment</span>
                    </div>
                    <div className="text-2xl font-black tracking-tight truncate mb-1 leading-none uppercase">{topEngagement?.engagement_name ?? "No Active Track"}</div>
                    <div className="flex items-center gap-2 mt-2">
                       <SimpleProgress value={topEngagement ? Math.round((topEngagement.verified_controls_count / (topEngagement.total_controls_count || 1)) * 100) : 0} color="bg-indigo-500" />
                       <span className="text-[10px] font-black text-muted-foreground tabular-nums">
                        {topEngagement ? Math.round((topEngagement.verified_controls_count / (topEngagement.total_controls_count || 1)) * 100) : 0}%
                       </span>
                    </div>
                  </div>
                </div>
              </Card>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              <Card className="lg:col-span-8 bg-card/30 backdrop-blur-sm border-muted/20 overflow-hidden flex flex-col min-h-[400px]">
                <CardHeader className="py-4 px-6 border-b border-muted/10 flex flex-row items-center justify-between">
                  <CardTitle className="text-[11px] font-black uppercase tracking-[0.25em] text-muted-foreground flex items-center gap-2.5">
                    <Layers className="h-4 w-4" />
                    Operational Segments
                  </CardTitle>
                </CardHeader>
                <div className="divide-y divide-muted/10 overflow-y-auto max-h-[500px]">
                  {engagements.map(eng => (
                    <div key={eng.id} className="p-5 flex items-center justify-between hover:bg-muted/5 transition-all group cursor-pointer" onClick={() => handleSelectEngagement(eng)}>
                      <div className="space-y-1.5 flex-1 min-w-0 pr-10">
                        <div className="flex items-center gap-3">
                          <p className="font-black text-sm uppercase tracking-tight truncate group-hover:text-indigo-400 transition-colors">{eng.engagement_name}</p>
                          <Badge variant={statusVariants[eng.status_code] ?? "secondary"} className="h-4 text-[8px] font-black uppercase tracking-widest border-none">{eng.status_name}</Badge>
                        </div>
                        <div className="flex items-center gap-4 text-[10px] font-bold text-muted-foreground/50 uppercase tracking-widest">
                          <span className="truncate flex items-center gap-1.5"><Building2 className="h-3 w-3 opacity-30" /> {eng.auditor_firm || "Internal"}</span>
                          <span className="flex items-center gap-1.5"><UserCheck className="h-3 w-3 opacity-30" /> {eng.verified_controls_count} / {eng.total_controls_count} Controls</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-10">
                        <div className="w-32 hidden md:block">
                          <div className="flex items-center justify-between text-[8px] font-black uppercase tracking-[0.2em] mb-1.5 opacity-40">
                             <span>Vector</span>
                             <span>{Math.round((eng.verified_controls_count / (eng.total_controls_count || 1)) * 100)}%</span>
                          </div>
                          <SimpleProgress value={(eng.verified_controls_count / (eng.total_controls_count || 1)) * 100} color="bg-indigo-500" />
                        </div>
                        <ChevronRight className="h-4 w-4 text-muted-foreground/30 group-hover:text-indigo-500 transition-colors" />
                      </div>
                    </div>
                  ))}
                  {engagements.length === 0 && (
                    <div className="py-20 flex flex-col items-center justify-center opacity-20">
                      <Inbox className="h-10 w-10 mb-2" />
                      <p className="text-[10px] font-black uppercase tracking-widest">Zero Engagements Found</p>
                    </div>
                  )}
                </div>
              </Card>

              <Card className="lg:col-span-4 bg-card/30 backdrop-blur-sm border-muted/20 overflow-hidden flex flex-col">
                 <CardHeader className="py-4 px-6 border-b border-muted/10">
                   <CardTitle className="text-[11px] font-black uppercase tracking-[0.25em] text-muted-foreground flex items-center gap-2.5">
                     <Inbox className="h-4 w-4" />
                     Global Activity
                   </CardTitle>
                 </CardHeader>
                 <div className="p-6 space-y-6 overflow-y-auto max-h-[500px]">
                    {dbData?.recent_activity?.map((act, i) => (
                      <div key={i} className="flex gap-4">
                        <div className="flex flex-col items-center shrink-0">
                          <div className="h-7 w-7 rounded-lg bg-indigo-500/5 flex items-center justify-center border border-indigo-500/10">
                             <div className="h-1 w-1 rounded-full bg-indigo-500" />
                          </div>
                          {i < dbData.recent_activity.length - 1 && <div className="w-px flex-1 bg-muted/10 mt-2" />}
                        </div>
                        <div className="min-w-0 pb-2">
                           <p className="text-[11px] leading-relaxed">
                             <span className="font-black text-foreground">{act.actor_name}</span>
                             <span className="mx-1 text-muted-foreground opacity-60">triggered</span>
                             <span className="font-black text-indigo-400 capitalize">{act.event_type.replace(/_/g, ' ')}</span>
                           </p>
                           <p className="text-[9px] font-bold text-muted-foreground/40 mt-1 uppercase tracking-tighter">{fmt(act.occurred_at)} · {act.entity_type}</p>
                        </div>
                      </div>
                    ))}
                    {(!dbData?.recent_activity || dbData.recent_activity.length === 0) && (
                      <p className="text-[10px] font-black uppercase tracking-widest opacity-20 text-center py-20">No recent interactions</p>
                    )}
                 </div>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="engagements" className="space-y-6">
            <div className="relative max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground/30" />
              <Input
                placeholder="SEARCH PORTFOLIO..."
                className="pl-10 h-10 border-muted/20 bg-muted/5 placeholder:text-[10px] placeholder:font-black"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              {engagements.filter(e => e.engagement_name.toLowerCase().includes(searchQuery.toLowerCase())).map(eng => (
                <EngagementCard 
                  key={eng.id} 
                  eng={eng} 
                  onSelect={handleSelectEngagement}
                  onInvite={(e) => { setInvitingEng(e); setIsInviteOpen(true); }}
                />
              ))}
            </div>
          </TabsContent>

          <TabsContent value="frameworks">
             <FrameworksView colorScheme="indigo" hideImportTemplate={false} />
          </TabsContent>
        </Tabs>
      </div>
    )
  }

  const renderEngagementContent = () => {
    if (!selectedEngagement) return null

    const verified = selectedEngagement.verified_controls_count || 0
    const total = selectedEngagement.total_controls_count || 1
    const progress = Math.round((verified / total) * 100)

    return (
      <div className="flex flex-col gap-6 animate-in slide-in-from-right-4 duration-500">
        {/* Context Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-muted/20 p-6 rounded-3xl border border-muted/10">
          <div className="flex items-center gap-5">
            <Button variant="ghost" size="icon" onClick={() => handleSelectEngagement(null)} className="h-11 w-11 rounded-2xl bg-background/50 border border-muted/10 hover:bg-indigo-500/10 hover:text-indigo-500 shadow-sm transition-all group">
              <ChevronRight className="h-5 w-5 rotate-180 group-hover:-translate-x-0.5 transition-transform" />
            </Button>
            <div>
              <div className="flex items-center gap-3">
                 <h2 className="text-2xl font-black tracking-tight uppercase leading-none">{selectedEngagement.engagement_name}</h2>
                 <Badge variant={statusVariants[selectedEngagement.status_code] ?? "secondary"} className="h-5 text-[8px] font-black tracking-[0.2em] border-none uppercase">{selectedEngagement.status_name}</Badge>
              </div>
              <div className="flex flex-wrap items-center gap-3 mt-1.5 overflow-hidden">
                <span className="text-[10px] text-indigo-500 font-black uppercase tracking-widest">{selectedEngagement.auditor_firm || "Internal READINESS"}</span>
                <span className="text-muted-foreground opacity-20 text-xs">|</span>
                <span className="text-[10px] font-bold text-muted-foreground/60 uppercase tracking-widest">{selectedEngagement.engagement_code}</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-8">
              <div className="text-right">
                <p className="text-[10px] font-black text-muted-foreground uppercase tracking-widest opacity-40 mb-1.5 text-right">Maturity Vector</p>
                <div className="flex items-center gap-3">
                  <span className="text-xl font-black italic tabular-nums leading-none">{progress}%</span>
                  <div className="w-32">
                    <SimpleProgress value={progress} color="bg-indigo-500 shadow-[0_0_10px_rgba(99,102,241,0.4)]" />
                  </div>
                </div>
              </div>
              <div className="h-10 w-10 flex items-center justify-center rounded-2xl bg-indigo-500/10 text-indigo-500 border border-indigo-500/20">
                <ShieldCheck className="h-5 w-5" />
              </div>
            </div>
            <Button
              variant="outline"
              size="icon"
              className="h-10 w-10 rounded-xl border-muted/20 hover:bg-indigo-500/10 hover:text-indigo-500 transition-all"
              onClick={() => {
                setEditForm({
                  engagement_name: selectedEngagement.engagement_name,
                  auditor_firm: selectedEngagement.auditor_firm,
                  lead_grc_sme: selectedEngagement.lead_grc_sme,
                  scope_description: selectedEngagement.scope_description,
                  audit_period_start: selectedEngagement.audit_period_start,
                  audit_period_end: selectedEngagement.audit_period_end,
                  target_completion_date: selectedEngagement.target_completion_date,
                })
                setIsEditOpen(true)
              }}
            >
              <Settings className="h-4 w-4" />
            </Button>
          </div>
        </div>


        <GrcEngagementTabs 
          activeTab={engagementTab}
          onTabChange={setEngagementTab}
          tabCounts={tabCounts}
          isLoading={isLoading}
        />

        <div className="mt-2 min-h-[50vh]">
          {engagementTab === "overview" && (
            <div className="grid gap-6 lg:grid-cols-12">
              <div className="lg:col-span-8 space-y-6">
                <div className="grid gap-4 sm:grid-cols-2">
                   <Card className="bg-card/40 border-muted/20 p-6 flex items-center gap-5">
                      <div className="h-12 w-12 rounded-2xl bg-emerald-500/10 flex items-center justify-center text-emerald-500"><CheckCircle2 className="h-6 w-6" /></div>
                      <div>
                         <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground opacity-40">Verified Intel</p>
                         <p className="text-2xl font-black">{verified} <span className="text-xs text-muted-foreground opacity-40 font-bold">/ {total}</span></p>
                      </div>
                   </Card>
                   <Card className="bg-card/40 border-muted/20 p-6 flex items-center gap-5">
                      <div className="h-12 w-12 rounded-2xl bg-amber-500/10 flex items-center justify-center text-amber-500"><Inbox className="h-6 w-6" /></div>
                      <div>
                         <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground opacity-40">Open Requests</p>
                         <p className="text-2xl font-black">{tabCounts.requests}</p>
                      </div>
                   </Card>
                </div>

                <Card className="bg-card/40 border-muted/20">
                    <CardHeader className="border-b border-muted/10 pb-4"><CardTitle className="text-xs font-black uppercase tracking-widest text-muted-foreground opacity-60">Engagement Perimeter</CardTitle></CardHeader>
                    <CardContent className="grid gap-6 md:grid-cols-2 pt-6">
                       <div className="space-y-1.5">
                          <p className="text-[10px] font-black uppercase text-muted-foreground/30 flex items-center gap-2"><Calendar className="h-3 w-3" /> Audit Window</p>
                          <p className="text-sm font-black tabular-nums">{fmt(selectedEngagement.audit_period_start)} <span className="opacity-20 font-bold mx-1">→</span> {fmt(selectedEngagement.audit_period_end)}</p>
                       </div>
                       <div className="space-y-1.5">
                          <p className="text-[10px] font-black uppercase text-muted-foreground/30 flex items-center gap-2"><Clock className="h-3 w-3" /> Target Dispatch</p>
                          <p className="text-sm font-black tabular-nums">{fmt(selectedEngagement.target_completion_date)}</p>
                       </div>
                       <div className="space-y-1.5">
                          <p className="text-[10px] font-black uppercase text-muted-foreground/30 flex items-center gap-2"><Users className="h-3 w-3" /> Lead Practitioner</p>
                          <p className="text-sm font-black">{selectedEngagement.lead_grc_sme || "Pending Assignment"}</p>
                       </div>
                       <div className="space-y-1.5">
                          <p className="text-[10px] font-black uppercase text-muted-foreground/30 flex items-center gap-2"><Building2 className="h-3 w-3" /> External Entity</p>
                          <p className="text-sm font-black truncate">{selectedEngagement.auditor_firm || "Direct Implementation"}</p>
                       </div>
                       <div className="md:col-span-2 space-y-1.5">
                          <p className="text-[10px] font-black uppercase text-muted-foreground/30">Strategic Scope</p>
                          <p className="text-[11px] font-medium leading-relaxed italic text-muted-foreground/80 bg-muted/10 p-4 rounded-xl border border-muted/10">
                            {selectedEngagement.scope_description || "No scope definition provided for this vector."}
                          </p>
                       </div>
                    </CardContent>
                </Card>
              </div>

              <div className="lg:col-span-4 space-y-6">
                <Card className="bg-card/40 border-muted/20">
                  <CardHeader className="border-b border-muted/10 pb-4"><CardTitle className="text-xs font-black uppercase tracking-widest text-muted-foreground opacity-60 flex items-center gap-2"><BarChart3 className="h-3.5 w-3.5 text-indigo-500" /> Quick Flow</CardTitle></CardHeader>
                  <CardContent className="space-y-3 pt-6">
                    <Button variant="outline" className="w-full justify-between rounded-xl h-11 text-[10px] font-black uppercase tracking-widest border-muted/20 hover:border-indigo-500/30 group" onClick={() => setEngagementTab("controls")}>
                      Manage Controls
                      <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/30 group-hover:text-indigo-500 transition-colors" />
                    </Button>
                    <Button variant="outline" className="w-full justify-between rounded-xl h-11 text-[10px] font-black uppercase tracking-widest border-muted/20 hover:border-indigo-500/30 group" onClick={() => setEngagementTab("requests")}>
                      Fulfill Requests
                      <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/30 group-hover:text-indigo-500 transition-colors" />
                    </Button>
                    <Button variant="outline" className="w-full justify-between rounded-xl h-11 text-[10px] font-black uppercase tracking-widest border-muted/20 hover:border-indigo-500/30 group" onClick={() => setEngagementTab("findings")}>
                      Engagement Findings
                      <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/30 group-hover:text-indigo-500 transition-colors" />
                    </Button>
                    <Button variant="outline" className="w-full justify-between rounded-xl h-11 text-[10px] font-black uppercase tracking-widest border-muted/20 hover:border-indigo-500/30 group" onClick={() => setEngagementTab("reports")}>
                      Audit Reports
                      <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/30 group-hover:text-indigo-500 transition-colors" />
                    </Button>
                  </CardContent>
                </Card>
                
                <div className="bg-indigo-500/5 rounded-2xl border border-indigo-500/10 p-5 space-y-4">
                   <p className="text-[10px] font-black uppercase tracking-widest text-indigo-500">Lifecycle Operations</p>
                   <div className="grid gap-2">
                     {selectedEngagement.status_code === 'setup' && (
                       <Button className="w-full h-10 bg-indigo-600 font-black text-[10px] uppercase tracking-[0.2em]" onClick={() => updateStatus('active')}>Start Engagement</Button>
                     )}
                     {selectedEngagement.status_code === 'active' && (
                       <Button className="w-full h-10 bg-amber-600 font-black text-[10px] uppercase tracking-[0.2em]" onClick={() => updateStatus('review')}>Submit for Review</Button>
                     )}
                   </div>
                </div>
              </div>
            </div>
          )}

          {engagementTab === "controls" && (
            <div className="space-y-6">
               <ControlsView 
                  orgId={selectedOrgId} 
                  workspaceId={selectedWorkspaceId} 
                  engagementId={selectedEngagement?.id}
                />
            </div>
          )}

          {engagementTab === "requests" && (
             <EngagementRequests engagementId={selectedEngagement.id} />
          )}

          {engagementTab === "findings" && (
             <FindingsView 
                orgId={selectedOrgId} 
                workspaceId={selectedWorkspaceId} 
                engagementId={selectedEngagement?.id}
              />
          )}

          {engagementTab === "tasks" && (
             <TasksView 
                orgId={selectedOrgId} 
                workspaceId={selectedWorkspaceId} 
                engagementId={selectedEngagement?.id}
              />
          )}

          {engagementTab === "reports" && (
             <ReportsView 
                orgId={selectedOrgId} 
                workspaceId={selectedWorkspaceId} 
                engagementId={selectedEngagement?.id}
                engagementName={selectedEngagement?.engagement_name}
                engagementFrameworkId={selectedEngagement?.framework_id}
                engagements={engagements}
              />
          )}

          {engagementTab === "team" && selectedOrgId && (
            <GrcTeamPanel 
              orgId={selectedOrgId} 
              workspaceId={selectedWorkspaceId || undefined} 
              engagementId={selectedEngagement?.id} 
            />
          )}

          {engagementTab === "messages" && (
            <MessagesTab
              engagementId={selectedEngagement.id}
              selectedEntity={selectedMessageEntity}
              onEntitySelect={setSelectedMessageEntity}
              engagements={engagements}
            />
          )}
        </div>
      </div>
    )
  }

  async function updateStatus(code: string) {
    if (!selectedEngagement) return
    try {
      await engagementsApi.update(selectedEngagement.id, { status_code: code })
      toast.success(`Engagement status transitioned to ${code}`)
      fetchData()
    } catch (e: any) {
      toast.error(e.message)
    }
  }

  return (
    <TooltipProvider delayDuration={0}>
      <div className="flex-1 space-y-6 pb-12">
        {selectedEngagement ? renderEngagementContent() : renderPortfolioContent()}

        {/* Create Engagement Dialog */}
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogContent className="sm:max-w-[550px] bg-card border-none shadow-2xl p-0 overflow-hidden">
            <DialogHeader className="p-6 pb-2 bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border-b border-muted/10">
              <DialogTitle className="text-2xl font-black uppercase tracking-tight">Launch Engagement</DialogTitle>
              <DialogDescription className="text-[10px] font-bold uppercase tracking-widest opacity-60">Inititate A New Strategic Audit Segment</DialogDescription>
            </DialogHeader>

            <div className="p-6 space-y-5 max-h-[70vh] overflow-y-auto scrollbar-none">
                {createError && <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-[11px] font-bold uppercase flex items-center gap-2"><AlertCircle className="h-4 w-4" />{createError}</div>}
                <div className="space-y-1.5">
                  <Label className="text-[10px] font-black uppercase tracking-widest opacity-40">Engagement Identity</Label>
                  <Input 
                    placeholder="e.g. FY26 SOC2 Strategic Review"
                    className="h-11 rounded-xl border-muted/20" 
                    value={createForm.engagement_name} 
                    onChange={(e) => setCreateForm(prev => ({ ...prev, engagement_name: e.target.value }))} 
                  />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-[10px] font-black uppercase tracking-widest opacity-40">Framework Standard</Label>
                  <Select value={createForm.framework_deployment_id} onValueChange={(val) => setCreateForm(prev => ({ ...prev, framework_deployment_id: val }))}>
                    <SelectTrigger className="h-11 rounded-xl border-muted/20"><SelectValue placeholder="Select Standard" /></SelectTrigger>
                    <SelectContent>
                      {deployments.map(fw => <SelectItem key={fw.id} value={fw.id}>{fw.name || fw.framework_code}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                   <div className="space-y-1.5">
                    <Label className="text-[10px] font-black uppercase tracking-widest opacity-40">Entity / Firm</Label>
                    <Input placeholder="e.g. Deloitte" className="h-11 rounded-xl border-muted/20" value={createForm.auditor_firm} onChange={(e) => setCreateForm(prev => ({ ...prev, auditor_firm: e.target.value }))} />
                   </div>
                   <div className="space-y-1.5">
                    <Label className="text-[10px] font-black uppercase tracking-widest opacity-40">Initial State</Label>
                    <Select value={createForm.status_code} onValueChange={(val) => setCreateForm(prev => ({ ...prev, status_code: val }))}>
                      <SelectTrigger className="h-11 rounded-xl border-muted/20"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="setup">Setup</SelectItem>
                        <SelectItem value="active">Active</SelectItem>
                      </SelectContent>
                    </Select>
                   </div>
                </div>
                <div className="space-y-1.5">
                    <Label className="text-[10px] font-black uppercase tracking-widest opacity-40">Lead Practitioner</Label>
                    <div className="relative">
                      <select 
                        className="h-11 w-full rounded-xl border border-muted/20 bg-background px-4 text-sm outline-none appearance-none transition focus:border-indigo-500/40"
                        value={createForm.lead_grc_sme || ""} 
                        onChange={(e) => setCreateForm(prev => ({ ...prev, lead_grc_sme: e.target.value }))} 
                      >
                        <option value="">Select Practitioner</option>
                        {Array.from(new Set(team.map(m => m.display_name || m.email))).map(name => (
                          <option key={name} value={name}>{name}</option>
                        ))}
                      </select>
                      <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none opacity-30">
                        <ChevronDown className="h-4 w-4" />
                      </div>
                    </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                   <div className="space-y-1.5">
                    <Label className="text-[10px] font-black uppercase tracking-widest opacity-40">Start Date</Label>
                    <Input type="date" className="h-11 rounded-xl border-muted/20" value={createForm.audit_period_start} onChange={(e) => setCreateForm(prev => ({ ...prev, audit_period_start: e.target.value }))} />
                   </div>
                   <div className="space-y-1.5">
                    <Label className="text-[10px] font-black uppercase tracking-widest opacity-40">End Date</Label>
                    <Input type="date" className="h-11 rounded-xl border-muted/20" value={createForm.audit_period_end} onChange={(e) => setCreateForm(prev => ({ ...prev, audit_period_end: e.target.value }))} />
                   </div>
                </div>
                <div className="grid grid-cols-1 gap-4">
                  <div className="space-y-1.5">
                    <Label className="text-[10px] font-black uppercase tracking-widest opacity-40">Target Dispatch Date</Label>
                    <Input type="date" className="h-11 rounded-xl border-muted/20" value={createForm.target_completion_date} onChange={(e) => setCreateForm(prev => ({ ...prev, target_completion_date: e.target.value }))} />
                  </div>
                  <div className="space-y-1.5">
                      <Label className="text-[10px] font-black uppercase tracking-widest opacity-40">Strategic Scope Definition</Label>
                      <textarea 
                        className="min-h-[100px] w-full rounded-xl border border-muted/20 bg-background px-4 py-3 text-sm outline-none transition focus:border-indigo-500/40"
                        placeholder="Describe the segment boundary..."
                        value={createForm.scope_description} 
                        onChange={(e) => setCreateForm(prev => ({ ...prev, scope_description: e.target.value }))} 
                      />
                  </div>
                </div>
            </div>

            <DialogFooter className="p-6 bg-muted/5 border-t border-muted/10">
              <Button variant="ghost" className="h-11 font-black text-[10px] uppercase tracking-widest" onClick={() => setIsCreateOpen(false)}>Abort</Button>
              <Button className="h-11 bg-indigo-600 font-black text-[10px] uppercase tracking-[0.2em] rounded-xl px-8 shadow-lg shadow-indigo-500/20" onClick={handleCreate} disabled={createLoading}>
                {createLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Dispatch Engagement"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Invite Auditor Dialog */}
        <Dialog open={isInviteOpen} onOpenChange={setIsInviteOpen}>
          <DialogContent className="sm:max-w-[400px] border-none shadow-2xl rounded-2xl p-0 overflow-hidden">
             <DialogHeader className="p-6 bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border-b border-muted/10">
                <DialogTitle className="text-xl font-black uppercase tracking-tight">Dispatch Access</DialogTitle>
             </DialogHeader>
             <div className="p-6 space-y-4">
                <div className="space-y-1.5">
                   <Label className="text-[10px] font-black uppercase tracking-widest opacity-40">Email Identity</Label>
                   <Input placeholder="auditor@firm.com" className="h-11 rounded-xl border-muted/20" value={inviteEmail} onChange={(e) => setInviteEmail(e.target.value)} />
                </div>
                <p className="text-[10px] font-bold text-muted-foreground opacity-50 italic uppercase leading-tight">Authorize external read access to this specific engagement segment.</p>
             </div>
             <DialogFooter className="p-6 bg-muted/5 border-t border-muted/10">
                <Button variant="ghost" className="h-10 text-[10px] font-black uppercase tracking-widest" onClick={() => setIsInviteOpen(false)}>Cancel</Button>
                <Button className="h-10 bg-indigo-600 text-white text-[10px] font-black uppercase tracking-[0.2em] rounded-xl px-6 shadow-md shadow-indigo-500/10" onClick={handleInvite} disabled={isInviting}>{isInviting ? "..." : "Dispatch"}</Button>
             </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Edit Engagement Dialog */}
        <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
          <DialogContent className="sm:max-w-2xl bg-card border-none shadow-2xl p-0 overflow-hidden">
            <DialogHeader className="p-6 bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border-b border-muted/10">
              <DialogTitle className="text-2xl font-black uppercase tracking-tight">Modify Engagement</DialogTitle>
              <DialogDescription className="text-[10px] font-bold uppercase tracking-widest opacity-60">Update Strategic Parameters & Scope</DialogDescription>
            </DialogHeader>

            <div className="p-6 grid grid-cols-2 gap-6 max-h-[70vh] overflow-y-auto scrollbar-none">
              <div className="col-span-2 space-y-1.5">
                <Label className="text-[10px] font-black uppercase tracking-widest opacity-40">Engagement Identity</Label>
                <Input 
                  className="h-11 rounded-xl border-muted/20" 
                  value={editForm.engagement_name || ""} 
                  onChange={(e) => setEditForm(prev => ({ ...prev, engagement_name: e.target.value }))} 
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-[10px] font-black uppercase tracking-widest opacity-40">External Entity / Firm</Label>
                <Input 
                  className="h-11 rounded-xl border-muted/20" 
                  value={editForm.auditor_firm || ""} 
                  onChange={(e) => setEditForm(prev => ({ ...prev, auditor_firm: e.target.value }))} 
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-[10px] font-black uppercase tracking-widest opacity-40">Lead Practitioner</Label>
                <div className="relative">
                  <select 
                    className="h-11 w-full rounded-xl border border-muted/20 bg-background px-4 text-sm outline-none appearance-none transition focus:border-indigo-500/40"
                    value={editForm.lead_grc_sme || ""} 
                    onChange={(e) => setEditForm(prev => ({ ...prev, lead_grc_sme: e.target.value }))} 
                  >
                    <option value="">Select Practitioner</option>
                    {/* Unique GRC members by display name or email */}
                    {Array.from(new Set(team.map(m => m.display_name || m.email))).map(name => (
                      <option key={name} value={name}>{name}</option>
                    ))}
                  </select>
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none opacity-30">
                    <ChevronDown className="h-4 w-4" />
                  </div>
                </div>
                <p className="text-[9px] text-muted-foreground italic mt-1 px-1">Managed via the Team tab</p>
              </div>
              <div className="space-y-1.5">
                <Label className="text-[10px] font-black uppercase tracking-widest opacity-40">Period Start</Label>
                <Input 
                  type="date"
                  className="h-11 rounded-xl border-muted/20" 
                  value={editForm.audit_period_start || ""} 
                  onChange={(e) => setEditForm(prev => ({ ...prev, audit_period_start: e.target.value }))} 
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-[10px] font-black uppercase tracking-widest opacity-40">Period End</Label>
                <Input 
                  type="date"
                  className="h-11 rounded-xl border-muted/20" 
                  value={editForm.audit_period_end || ""} 
                  onChange={(e) => setEditForm(prev => ({ ...prev, audit_period_end: e.target.value }))} 
                />
              </div>
              <div className="col-span-2 space-y-1.5">
                <Label className="text-[10px] font-black uppercase tracking-widest opacity-40">Target Dispatch Date</Label>
                <Input 
                  type="date"
                  className="h-11 rounded-xl border-muted/20" 
                  value={editForm.target_completion_date || ""} 
                  onChange={(e) => setEditForm(prev => ({ ...prev, target_completion_date: e.target.value }))} 
                />
              </div>
              <div className="col-span-2 space-y-1.5">
                <Label className="text-[10px] font-black uppercase tracking-widest opacity-40">Strategic Scope Definition</Label>
                <textarea 
                  className="min-h-[120px] w-full rounded-xl border border-muted/20 bg-background px-4 py-3 text-sm outline-none transition focus:border-indigo-500/40"
                  value={editForm.scope_description || ""} 
                  onChange={(e) => setEditForm(prev => ({ ...prev, scope_description: e.target.value }))} 
                />
              </div>
            </div>

            <DialogFooter className="p-6 bg-muted/5 border-t border-muted/10">
              <Button variant="ghost" className="h-11 font-black text-[10px] uppercase tracking-widest" onClick={() => setIsEditOpen(false)}>Abort</Button>
              <Button 
                className="h-11 bg-indigo-600 font-black text-[10px] uppercase tracking-[0.2em] rounded-xl px-8 shadow-lg shadow-indigo-500/20" 
                onClick={handleUpdateEngagement} 
                disabled={isUpdating}
              >
                {isUpdating ? <Loader2 className="h-4 w-4 animate-spin" /> : "Save Changes"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </TooltipProvider>
  )
}
