"use client"

import * as React from "react"
import { 
  LayoutDashboard,
  Loader2,
  TrendingUp,
  Building2,
  Inbox,
  CheckCircle2,
  Activity,
  AlertCircle,
  ShieldCheck,
  FileCheck,
  ChevronRight,
  Clock,
  Layers,
  ClipboardList,
  Upload,
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
  TabsList,
  TabsTrigger,
  TabsContent,
} from "@kcontrol/ui"

import { useView } from "@/lib/context/ViewContext"
import { useOrgWorkspace } from "@/lib/context/OrgWorkspaceContext"
import { Engagement, engagementsApi } from "@/lib/api/engagements"
import { dashboardApi, type AuditorDashboardResponse } from "@/lib/api/dashboard"
import { submitReport, generateAndSubmitFrameworkReadinessReport, uploadAndSubmitManualReport } from "@/lib/api/ai"
import { useAccess } from "@/components/providers/AccessProvider"

import { AuditWorkspaceTabs } from "@/components/auditor/AuditWorkspaceTabs"
import { EngagementsTab } from "@/components/auditor/EngagementsTab"
import { EvidenceRequestsTab } from "@/components/auditor/EvidenceRequestsTab"
import { MessagesTab } from "@/components/auditor/MessagesTab"
import { EvidenceLibraryTab } from "@/components/auditor/EvidenceLibraryTab"
import { EvidenceTasksTab } from "@/components/auditor/EvidenceTasksTab"
import { ReportsView } from "@/components/auditor/ReportsView"
import { FrameworksView } from "@/components/auditor/FrameworksView"
import { FindingsView } from "@/components/auditor/FindingsView"

// ── Shared Helpers ──────────────────────────────────────────────────────────

function SimpleProgress({ value, className }: { value: number, className?: string }) {
  return (
    <div className={`w-full bg-muted rounded-full h-1.5 overflow-hidden ${className}`}>
      <div className="bg-primary h-full transition-all duration-1000" style={{ width: `${value}%` }} />
    </div>
  )
}

function IntelCard({ label, value, sub, icon: Icon, color, bg }: any) {
    return (
        <Card className="border-none shadow-sm bg-background/50 backdrop-blur-sm group hover:ring-1 hover:ring-primary/20 transition-all">
            <CardContent className="p-5 flex items-center gap-4">
                <div className={`p-3 rounded-2xl ${bg} ${color} group-hover:scale-110 transition-transform`}>
                    <Icon className="h-6 w-6" />
                </div>
                <div>
                    <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest leading-none mb-1">{label}</p>
                    <p className="text-2xl font-black tracking-tighter">{value}</p>
                    <p className="text-[10px] font-medium text-muted-foreground opacity-60 italic">{sub}</p>
                </div>
            </CardContent>
        </Card>
    )
}

// ── Main Page Component ─────────────────────────────────────────────────────

export default function AuditorPortalPage() {
  const { activeViewDef } = useView()
  const { selectedOrgId } = useOrgWorkspace()
  const { hasFeature, isLoading: isAccessLoading } = useAccess()
  
  // Navigation State
  const [mainTab, setMainTab] = React.useState("command-center")
  const [activeTab, setActiveTab] = React.useState("engagements")
  
  // Data State
  const [engagements, setEngagements] = React.useState<Engagement[]>([])
  const [dbData, setDbData] = React.useState<AuditorDashboardResponse | null>(null)
  const [selectedEngagement, setSelectedEngagement] = React.useState<Engagement | null>(null)
  const [isLoading, setIsLoading] = React.useState(true)
  
  // Entity State (for messaging context)
  const [selectedMessageEntity, setSelectedMessageEntity] = React.useState<{ type: string; id: string; title?: string } | undefined>()

  // Submit Report State
  const [showSubmitDialog, setShowSubmitDialog] = React.useState(false)
  const [isSubmittingReport, setIsSubmittingReport] = React.useState(false)
  const [submissionNotes, setSubmissionNotes] = React.useState("")
  const [submitMode, setSubmitMode] = React.useState<"generate" | "upload">("generate")
  const [selectedFile, setSelectedFile] = React.useState<File | null>(null)
  const fileInputRef = React.useRef<HTMLInputElement>(null)

  const canViewPortfolio = hasFeature("audit_workspace_auditor_portfolio") || hasFeature("audit_workspace_engagement_membership")
  const canViewEvidenceRequests = hasFeature("audit_workspace_evidence_requests")
  const canViewFindings = hasFeature("audit_workspace_auditor_findings")
  const canViewTasks = hasFeature("audit_workspace_auditor_tasks")
  const visibleEngagementTabs = React.useMemo(() => {
    const tabs = ["overview", "engagements"]
    if (canViewFindings) tabs.push("findings")
    if (canViewEvidenceRequests) tabs.push("evidence-requests")
    tabs.push("messages", "reports", "evidence-library")
    if (canViewTasks) tabs.push("evidence-tasks")
    return tabs
  }, [canViewEvidenceRequests, canViewFindings, canViewTasks])

  // ── Data Loading ──────────────────────────────────────────────────────────

  const fetchData = React.useCallback(async () => {
    if (!canViewPortfolio) {
      setDbData(null)
      setEngagements([])
      setIsLoading(false)
      return
    }
    setIsLoading(true)
    try {
      const [db, engs] = await Promise.all([
        dashboardApi.getAuditor(undefined),
        engagementsApi.listMyEngagements(undefined)
      ])
      setDbData(db)
      setEngagements(engs)
    } catch (err) {
      console.error("Failed to load auditor data:", err)
    } finally {
      setIsLoading(false)
    }
  }, [canViewPortfolio])

  React.useEffect(() => { fetchData() }, [fetchData])

  React.useEffect(() => {
    if (!visibleEngagementTabs.includes(activeTab)) {
      setActiveTab("engagements")
    }
  }, [activeTab, visibleEngagementTabs])

  // ── Derived State ─────────────────────────────────────────────────────────

  const tabCounts = React.useMemo(() => ({
    engagements: engagements.length,
    findings: 0,
    evidenceRequests: canViewEvidenceRequests ? (dbData?.total_pending_requests || 0) : 0,
    messages: 0,
    reports: 0,
    evidenceLibrary: 0,
    evidenceTasks: canViewTasks ? (dbData?.review_queue?.length || 0) : 0,
    myAccess: 1,
  }), [canViewEvidenceRequests, canViewTasks, engagements.length, dbData])

  const avgCoverage = dbData?.engagements?.length 
    ? Math.round(dbData.engagements.reduce((acc: number, e: any) => acc + (e.verified_controls_count / (e.total_controls_count || 1)), 0) / dbData.engagements.length * 100)
    : 0

  // ── Handlers ──────────────────────────────────────────────────────────────

  const handleMessageLink = (entity: { type: string; id: string; title?: string }) => {
    setSelectedMessageEntity(entity)
    setActiveTab("messages")
  }

  const handleSelectEngagement = (eng: Engagement | null) => {
    setSelectedEngagement(eng)
    if (eng) {
        setActiveTab("overview")
    }
  }

  const earliestMilestone = React.useMemo(() => {
    if (!dbData?.engagements) return null
    return [...dbData.engagements]
      .filter(e => e.target_date)
      .sort((a,b) => new Date(a.target_date!).getTime() - new Date(b.target_date!).getTime())[0]
  }, [dbData])

  const daysToMilestone = React.useMemo(() => {
    if (!earliestMilestone?.target_date) return null
    const diff = Math.ceil((new Date(earliestMilestone.target_date).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24))
    return diff > 0 ? diff : 0
  }, [earliestMilestone])

  const handleSubmitReport = () => {
    if (!selectedEngagement) return
    setShowSubmitDialog(true)
  }

  // ── Render Views ──────────────────────────────────────────────────────────

  const renderContent = () => {
    if (isLoading && !engagements.length) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
                <Loader2 className="h-10 w-10 animate-spin text-primary" />
                <p className="text-xs font-black uppercase tracking-[0.2em] opacity-40">Compiling Audit Intelligence...</p>
            </div>
        )
    }

    if (!isAccessLoading && !canViewPortfolio) {
        return (
            <div className="flex min-h-[50vh] items-center justify-center">
                <Card className="max-w-xl border-border/60 bg-card/80">
                    <CardContent className="space-y-3 p-8 text-center">
                        <AlertCircle className="mx-auto h-10 w-10 text-muted-foreground/50" />
                        <h2 className="text-xl font-black tracking-tight">Auditor Workspace Unavailable</h2>
                        <p className="text-sm text-muted-foreground">
                            The auditor workspace is not enabled for your current session or scope.
                        </p>
                    </CardContent>
                </Card>
            </div>
        )
    }

    // View: Audit Workspace (Portfolio Dashboard)
    if (!selectedEngagement) {
        return (
            <div className="flex flex-col gap-6 animate-in fade-in duration-700">
                {/* Header: Compact & Professional */}
                <div className="flex items-center justify-between border-b border-muted/10 pb-6">
                    <div className="space-y-0.5">
                        <h1 className="text-2xl font-black tracking-tighter flex items-center gap-3">
                            <LayoutDashboard className="h-7 w-7 text-primary" />
                            AUDITOR COMMAND CENTER
                        </h1>
                        <p className="text-muted-foreground text-[10px] font-black uppercase tracking-[0.25em] opacity-60">
                            Cross-Organization Strategic Portfolio Oversight
                        </p>
                    </div>
                    <Button variant="ghost" size="sm" className="h-9 px-4 rounded-xl font-black text-[10px] uppercase tracking-widest gap-2 hover:bg-muted/50" onClick={fetchData}>
                        <TrendingUp className="h-3.5 w-3.5" />
                        Refresh Intelligence
                    </Button>
                </div>

                {/* Tabs */}
                <Tabs value={mainTab} onValueChange={setMainTab} className="space-y-6">
                    <TabsList className="bg-muted/20 p-1 h-10 items-center rounded-xl backdrop-blur-sm border border-muted/10 w-fit">
                        <TabsTrigger value="command-center" className="gap-2 px-6 h-8 rounded-lg text-[10px] font-black uppercase tracking-widest data-[state=active]:bg-background data-[state=active]:shadow-sm">
                            <LayoutDashboard className="h-3 w-3" />
                            Command Center
                        </TabsTrigger>
                        <TabsTrigger value="frameworks" className="gap-2 px-6 h-8 rounded-lg text-[10px] font-black uppercase tracking-widest data-[state=active]:bg-background data-[state=active]:shadow-sm">
                            <ClipboardList className="h-3 w-3" />
                            Assigned Frameworks
                        </TabsTrigger>
                    </TabsList>

                    <TabsContent value="command-center" className="animate-in fade-in slide-in-from-bottom-2 duration-500 space-y-5 focus-visible:outline-none">
                        {/* Intelligence Board: High Density KPI Grid */}
                        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
                            <Card className="lg:col-span-9 bg-card/40 backdrop-blur-sm border-muted/20 overflow-hidden">
                                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 h-full divide-y sm:divide-y-0 sm:divide-x divide-muted/10">
                                    <div className="p-6 flex flex-col justify-center">
                                        <div className="flex items-center gap-2 text-muted-foreground mb-4 opacity-70">
                                            <Building2 className="h-3.5 w-3.5" />
                                            <span className="text-[10px] font-black uppercase tracking-widest">Active Portfolios</span>
                                        </div>
                                        <div className="text-4xl font-black tracking-tighter tabular-nums">{dbData?.active_engagements_count ?? 0}</div>
                                        <p className="text-[10px] text-muted-foreground mt-2 font-bold uppercase tracking-tighter">
                                            Currently under audit
                                        </p>
                                    </div>
                                    <div className="p-6 flex flex-col justify-center">
                                        <div className="flex items-center gap-2 text-orange-500 mb-4 opacity-80">
                                            <Inbox className="h-3.5 w-3.5" />
                                            <span className="text-[10px] font-black uppercase tracking-widest">Review Queue</span>
                                        </div>
                                        <div className="text-4xl font-black tracking-tighter tabular-nums">{dbData?.total_pending_requests ?? 0}</div>
                                        <p className="text-[10px] text-orange-500/80 mt-2 font-bold uppercase tracking-tighter">
                                            Evidence awaiting sign-off
                                        </p>
                                    </div>
                                    <div className="p-6 flex flex-col justify-center">
                                        <div className="flex items-center gap-2 text-green-500 mb-4 opacity-80">
                                            <CheckCircle2 className="h-3.5 w-3.5" />
                                            <span className="text-[10px] font-black uppercase tracking-widest">Total Verified</span>
                                        </div>
                                        <div className="text-4xl font-black tracking-tighter tabular-nums">{dbData?.total_verified_controls ?? 0}</div>
                                        <p className="text-[10px] text-green-500/80 mt-2 font-bold uppercase tracking-tighter">
                                            Controls cleared this cycle
                                        </p>
                                    </div>
                                    <div className="p-6 flex flex-col justify-center bg-primary/[0.02]">
                                        <div className="flex items-center gap-2 text-primary mb-4 font-black">
                                            <Activity className="h-3.5 w-3.5" />
                                            <span className="text-[10px] uppercase tracking-widest">Mean Coverage</span>
                                        </div>
                                        <div className="text-4xl font-black tracking-tighter tabular-nums">{avgCoverage}%</div>
                                        <div className="flex items-center gap-2 mt-2">
                                            <div className="h-1.5 flex-1 bg-muted/20 rounded-full overflow-hidden">
                                                <div className="h-full bg-primary rounded-full shadow-[0_0_8px_rgba(var(--primary),0.3)]" style={{ width: `${avgCoverage}%` }} />
                                            </div>
                                            <span className="text-[10px] font-black text-muted-foreground italic tabular-nums">Portfolio Avg</span>
                                        </div>
                                    </div>
                                </div>
                            </Card>

                            <Card className="lg:col-span-3 bg-primary text-primary-foreground border-none shadow-xl shadow-primary/10 p-4 relative overflow-hidden group">
                                <div className="absolute top-0 right-0 p-4 opacity-10 -rotate-12 group-hover:rotate-0 transition-transform">
                                    <Clock className="h-16 w-16" />
                                </div>
                                <div className="flex flex-col h-full justify-between relative z-10">
                                    <div className="flex items-center gap-4">
                                        <div className="h-11 w-11 rounded-2xl bg-white/10 backdrop-blur-md flex items-center justify-center font-black text-lg shadow-inner border border-white/10 tabular-nums">
                                            {daysToMilestone !== null ? daysToMilestone : "—"}
                                        </div>
                                        <div>
                                            <h4 className="text-[10px] font-black uppercase tracking-[0.25em] opacity-80 mb-0.5">Next Milestone</h4>
                                            <p className="text-sm font-black truncate max-w-[150px]">
                                                {earliestMilestone?.name || "No Scheduled Dates"}
                                            </p>
                                        </div>
                                    </div>
                                    <Button 
                                        className="w-full bg-white text-primary hover:bg-white/90 font-black text-[9px] uppercase tracking-[0.2em] h-8 rounded-lg mt-4"
                                        onClick={() => {
                                            if (earliestMilestone) {
                                                handleSelectEngagement(engagements.find(e => e.id === earliestMilestone.id) || null)
                                            }
                                        }}
                                    >
                                        View Roadmap
                                    </Button>
                                </div>
                            </Card>
                        </div>

                        <div>
                            <EngagementsTab 
                                engagements={engagements}
                                selectedEngagement={null}
                                onSelectEngagement={handleSelectEngagement}
                                onRefresh={fetchData}
                                isLoading={isLoading}
                                onMessageLink={handleMessageLink}
                            />
                        </div>
                    </TabsContent>

                    <TabsContent value="frameworks" className="animate-in fade-in slide-in-from-bottom-2 duration-500 space-y-5 focus-visible:outline-none">
                        <FrameworksView colorScheme="teal" baseRoute="/frameworks" hideImportTemplate={true} />
                    </TabsContent>
                </Tabs>
            </div>
        )
    }

    // View: Audit Workspace (Individual Engagement Tabs)
    return (
        <div className="flex flex-col gap-6 animate-in slide-in-from-right-4 duration-500">
            {/* Context Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-muted/20 p-6 rounded-3xl">
                <div className="flex items-center gap-4">
                    <Button variant="ghost" size="icon" onClick={() => handleSelectEngagement(null)} className="h-10 w-10 rounded-full bg-background/50">
                        <ChevronRight className="h-5 w-5 rotate-180" />
                    </Button>
                    <div>
                        <h2 className="text-2xl font-black tracking-tight">{selectedEngagement.engagement_name}</h2>
                        <div className="flex flex-wrap items-center gap-2 mt-1">
                            <Badge variant="outline" className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground border-muted-foreground/30">
                                ORG: {selectedEngagement.org_name !== "N/A" ? selectedEngagement.org_name : "No Org"}
                            </Badge>
                            {selectedEngagement.workspace_name ? (
                              <Badge variant="outline" className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground border-muted-foreground/30">
                                WORKSPACE: {selectedEngagement.workspace_name}
                              </Badge>
                            ) : null}
                            <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest opacity-60 ml-1">Engagement Detail</span>
                        </div>
                    </div>
                </div>
                <div className="flex items-center gap-6">
                    <div className="text-right">
                        <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Readiness</p>
                        <div className="flex items-center gap-2">
                            <span className="text-lg font-black italic">{Math.round((selectedEngagement.verified_controls_count / (selectedEngagement.total_controls_count || 1)) * 100)}%</span>
                            <SimpleProgress value={(selectedEngagement.verified_controls_count / (selectedEngagement.total_controls_count || 1)) * 100} className="w-24" />
                        </div>
                    </div>
                    <Button className="rounded-full h-11 px-8 font-bold gap-2" onClick={handleSubmitReport}>
                        <FileCheck className="h-4 w-4" />
                        Submit Report
                    </Button>
                </div>
            </div>

                <AuditWorkspaceTabs 
                activeTab={activeTab}
                onTabChange={setActiveTab}
                tabCounts={tabCounts}
                visibleTabs={visibleEngagementTabs}
                isLoading={isLoading}
                isEngagementContext={!!selectedEngagement}
            />

            <div className="mt-2">
                {activeTab === "overview" && (
                    <div className="grid gap-4 lg:grid-cols-12">
                        <div className="lg:col-span-8 space-y-4">
                            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                                <IntelCard
                                    label="Control Coverage"
                                    value={`${Math.round((selectedEngagement.verified_controls_count / (selectedEngagement.total_controls_count || 1)) * 100)}%`}
                                    sub={`${selectedEngagement.verified_controls_count}/${selectedEngagement.total_controls_count} controls verified`}
                                    icon={ShieldCheck}
                                    color="text-emerald-600"
                                    bg="bg-emerald-500/10"
                                />
                                <IntelCard
                                    label="Evidence Requests"
                                    value={tabCounts.evidenceRequests}
                                    sub="Open items awaiting response"
                                    icon={Inbox}
                                    color="text-amber-600"
                                    bg="bg-amber-500/10"
                                />
                                <IntelCard
                                    label="Task Queue"
                                    value={tabCounts.evidenceTasks}
                                    sub="Engagement tasks in motion"
                                    icon={ClipboardList}
                                    color="text-sky-600"
                                    bg="bg-sky-500/10"
                                />
                                <IntelCard
                                    label="Workspace"
                                    value={selectedEngagement.workspace_name || "Primary"}
                                    sub={selectedEngagement.org_name}
                                    icon={Building2}
                                    color="text-indigo-600"
                                    bg="bg-indigo-500/10"
                                />
                            </div>

                            <Card className="border-border/60 bg-card/85">
                                <CardHeader>
                                    <CardTitle className="text-base font-black tracking-tight">Engagement Snapshot</CardTitle>
                                </CardHeader>
                                <CardContent className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                                    <div className="rounded-2xl border border-border/60 bg-muted/20 p-4">
                                        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">Organization</p>
                                        <p className="mt-2 text-lg font-black tracking-tight">{selectedEngagement.org_name}</p>
                                    </div>
                                    <div className="rounded-2xl border border-border/60 bg-muted/20 p-4">
                                        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">Engagement</p>
                                        <p className="mt-2 text-lg font-black tracking-tight">{selectedEngagement.engagement_name}</p>
                                    </div>
                                    <div className="rounded-2xl border border-border/60 bg-muted/20 p-4">
                                        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">Code</p>
                                        <p className="mt-2 text-lg font-black tracking-tight">{selectedEngagement.engagement_code}</p>
                                    </div>
                                    <div className="rounded-2xl border border-border/60 bg-muted/20 p-4">
                                        <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">Status</p>
                                        <p className="mt-2 text-lg font-black tracking-tight">{selectedEngagement.status_name}</p>
                                    </div>
                                </CardContent>
                            </Card>
                        </div>

                        <div className="lg:col-span-4">
                            <Card className="border-border/60 bg-card/85">
                                <CardHeader>
                                    <CardTitle className="text-base font-black tracking-tight">Quick Navigation</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-3">
                                    <Button variant="outline" className="w-full justify-between rounded-2xl h-12" onClick={() => setActiveTab("engagements")}>
                                        Controls
                                        <ChevronRight className="h-4 w-4" />
                                    </Button>
                                    {canViewFindings && (
                                        <Button variant="outline" className="w-full justify-between rounded-2xl h-12" onClick={() => setActiveTab("findings")}>
                                            Findings
                                            <ChevronRight className="h-4 w-4" />
                                        </Button>
                                    )}
                                    {canViewTasks && (
                                        <Button variant="outline" className="w-full justify-between rounded-2xl h-12" onClick={() => setActiveTab("evidence-tasks")}>
                                            Tasks
                                            <ChevronRight className="h-4 w-4" />
                                        </Button>
                                    )}
                                    {canViewEvidenceRequests && (
                                        <Button variant="outline" className="w-full justify-between rounded-2xl h-12" onClick={() => setActiveTab("evidence-requests")}>
                                            Evidence Requests
                                            <ChevronRight className="h-4 w-4" />
                                        </Button>
                                    )}
                                </CardContent>
                            </Card>
                        </div>
                    </div>
                )}
                {activeTab === "engagements" && (
                    <EngagementsTab 
                        engagements={engagements}
                        selectedEngagement={selectedEngagement}
                        onSelectEngagement={handleSelectEngagement}
                        onRefresh={fetchData}
                        isLoading={isLoading}
                        onMessageLink={handleMessageLink}
                    />
                )}
                {activeTab === "evidence-requests" && canViewEvidenceRequests && (
                    <EvidenceRequestsTab 
                        engagementId={selectedEngagement.id}
                        onRequestCreated={fetchData}
                        onMessageLink={handleMessageLink}
                    />
                )}
                {activeTab === "findings" && canViewFindings && (
                    <FindingsView
                        engagementId={selectedEngagement.id}
                    />
                )}
                {activeTab === "messages" && (
                    <MessagesTab 
                        engagementId={selectedEngagement.id}
                        selectedEntity={selectedMessageEntity}
                        onEntitySelect={setSelectedMessageEntity}
                    />
                )}
                {activeTab === "reports" && (
                    <ReportsView
                        engagementId={selectedEngagement.id}
                    />
                )}
                {activeTab === "evidence-library" && (
                    <EvidenceLibraryTab 
                        engagementId={selectedEngagement.id}
                    />
                )}
                {activeTab === "evidence-tasks" && canViewTasks && (
                    <EvidenceTasksTab 
                        engagementId={selectedEngagement.id}
                        onMessageLink={handleMessageLink}
                    />
                )}
            </div>
        </div>
    )
  }

  // ── Layout ────────────────────────────────────────────────────────────────

  return (
    <div className="flex-1 space-y-6 pb-12">
        {renderContent()}

        {/* Submit Report Dialog */}
        {showSubmitDialog && selectedEngagement && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <Card className="mx-4 w-full max-w-md">
              <CardHeader className="border-b border-border/60">
                <CardTitle>Submit Report to Engagement</CardTitle>
              </CardHeader>
              <div className="p-6 space-y-4">
                <div className="flex p-1 bg-muted rounded-xl mb-4 text-[10px] font-black uppercase tracking-widest">
                  <button
                    className={`flex-1 py-2 rounded-lg transition-all ${submitMode === "generate" ? "bg-background shadow-sm text-primary" : "text-muted-foreground hover:text-foreground"}`}
                    onClick={() => setSubmitMode("generate")}
                  >
                    AI Generate
                  </button>
                  <button
                    className={`flex-1 py-2 rounded-lg transition-all ${submitMode === "upload" ? "bg-background shadow-sm text-primary" : "text-muted-foreground hover:text-foreground"}`}
                    onClick={() => setSubmitMode("upload")}
                  >
                    Manual Upload
                  </button>
                </div>

                <div>
                  <p className="text-sm font-semibold mb-2 text-muted-foreground">Engagement</p>
                  <p className="text-base font-bold">{selectedEngagement.engagement_name}</p>
                  <p className="text-xs text-muted-foreground">{selectedEngagement.engagement_code}</p>
                </div>

                {submitMode === "generate" ? (
                  <div>
                    <p className="text-sm font-semibold mb-2 text-muted-foreground">Framework</p>
                    <p className="text-base font-bold">{selectedEngagement.framework_id || "No framework"}</p>
                  </div>
                ) : (
                  <div>
                    <label className="text-sm font-semibold block mb-2">Report File</label>
                    <div 
                      onClick={() => fileInputRef.current?.click()}
                      className={`cursor-pointer border-2 border-dashed rounded-xl p-8 text-center transition-colors ${selectedFile ? "border-primary/50 bg-primary/5" : "border-border hover:border-primary/30 hover:bg-muted/50"}`}
                    >
                      <input 
                        type="file" 
                        ref={fileInputRef} 
                        className="hidden" 
                        onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                        accept=".pdf,.docx,.doc,.md,.txt"
                      />
                      {selectedFile ? (
                        <div className="space-y-1">
                          <FileCheck className="h-8 w-8 mx-auto text-primary" />
                          <p className="text-sm font-bold text-foreground truncate">{selectedFile.name}</p>
                          <p className="text-xs text-muted-foreground">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                        </div>
                      ) : (
                        <div className="space-y-1">
                          <Upload className="h-8 w-8 mx-auto text-muted-foreground" />
                          <p className="text-sm font-bold text-foreground">Click to select report file</p>
                          <p className="text-xs text-muted-foreground">PDF, DOCX or Markdown</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                <div>
                  <label className="text-sm font-semibold block mb-2">Submission Notes (optional)</label>
                  <textarea
                    value={submissionNotes}
                    onChange={(e) => setSubmissionNotes(e.target.value)}
                    placeholder="Add notes about this submission..."
                    className="w-full h-24 px-3 py-2 text-sm border border-input rounded-lg bg-background focus:outline-none focus:ring-1 focus:ring-ring"
                  />
                </div>
                <div className="flex gap-2 pt-2">
                  <Button
                    variant="outline"
                    onClick={() => {
                      setShowSubmitDialog(false)
                      setSubmissionNotes("")
                      setSelectedFile(null)
                    }}
                    disabled={isSubmittingReport}
                  >
                    Cancel
                  </Button>
                  <Button
                    className="flex-1"
                    disabled={isSubmittingReport || (submitMode === "upload" && !selectedFile)}
                    onClick={async () => {
                      if (!selectedEngagement) return
                      
                      if (submitMode === "upload" && !selectedFile) {
                        toast.error("Please select a file to upload")
                        return
                      }

                      setIsSubmittingReport(true)
                      try {
                        if (submitMode === "generate") {
                          // Generate framework readiness report and submit to engagement
                          await generateAndSubmitFrameworkReadinessReport(
                            selectedEngagement.id,
                            selectedEngagement.org_id,
                            selectedEngagement.workspace_id || undefined,
                            selectedEngagement.framework_id,
                            submissionNotes || "Framework readiness assessment submitted for review"
                          )
                          toast.success("Report successfully generated and submitted", {
                            description: `Framework readiness report linked to ${selectedEngagement.engagement_name}. Engagement status updated.`,
                          })
                        } else if (selectedFile) {
                          // Upload manual report and submit
                          await uploadAndSubmitManualReport(
                            selectedFile,
                            selectedEngagement.id,
                            selectedFile.name.split(".")[0], // Use filename as title
                            selectedEngagement.org_id,
                            selectedEngagement.workspace_id || undefined,
                            submissionNotes || "Manual audit report submitted for review"
                          )
                          toast.success("Report successfully uploaded and submitted", {
                            description: `Manual report linked to ${selectedEngagement.engagement_name}. Engagement status updated.`,
                          })
                        }
                        
                        // Close dialog and reset state
                        setShowSubmitDialog(false)
                        setSubmissionNotes("")
                        setSelectedFile(null)
                        
                        // Refresh data to show updated status
                        await fetchData()
                      } catch (err: any) {
                        console.error("Failed to submit report:", err)
                        toast.error("Failed to submit report", {
                          description: err.message || "An error occurred while submitting the report",
                        })
                      } finally {
                        setIsSubmittingReport(false)
                      }
                    }}
                  >
                    {isSubmittingReport ? (
                      <><Loader2 className="h-4 w-4 animate-spin mr-2" /> {submitMode === "generate" ? "Generating & Submitting..." : "Uploading & Submitting..."}</>
                    ) : (
                      submitMode === "generate" ? "Generate & Submit Report" : "Upload & Submit Report"
                    )}
                  </Button>
                </div>
              </div>
            </Card>
          </div>
        )}
    </div>
  )
}
