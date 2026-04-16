"use client"

import * as React from "react"
import {
  Building2,
  Calendar,
  CheckCircle2,
  Clock,
  AlertCircle,
  MessageSquare,
  Loader2,
  RefreshCw,
  Shield,
  FileText,
  Search,
  XCircle,
  AlertTriangle,
} from "lucide-react"

import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Badge,
  Input,
} from "@kcontrol/ui"

import { Engagement, EngagementControl, engagementsApi } from "@/lib/api/engagements"
import { toast } from "sonner"
import { VerifyControlDialog } from "./VerifyControlDialog"
import { RequestEvidenceDialog } from "./RequestEvidenceDialog"

interface EngagementsTabProps {
  engagements: Engagement[]
  selectedEngagement: Engagement | null
  onSelectEngagement: (engagement: Engagement | null) => void
  onRefresh: () => void
  isLoading?: boolean
  onMessageLink?: (entity: { type: string; id: string; title?: string }) => void
}

export function EngagementsTab({ 
  engagements, 
  selectedEngagement, 
  onSelectEngagement,
  onRefresh,
  onMessageLink,
  isLoading = false 
}: EngagementsTabProps) {
  const [controls, setControls] = React.useState<EngagementControl[]>([])
  const [loadingControls, setLoadingControls] = React.useState(false)

  // Load controls when engagement is selected
  React.useEffect(() => {
    if (selectedEngagement) {
      setLoadingControls(true)
      engagementsApi.listEngagementControls(selectedEngagement.id)
        .then(setControls)
        .catch(console.error)
        .finally(() => setLoadingControls(false))
    }
  }, [selectedEngagement])

  // Calculate CC category progress
  const categoryProgress = React.useMemo(() => {
    if (!controls.length) return []
    
    const categories: { [key: string]: { total: number; verified: number } } = {}
    controls.forEach(control => {
      const category = control.control_code.split('.')[0] // CC6.1 -> CC6
      if (!categories[category]) {
        categories[category] = { total: 0, verified: 0 }
      }
      categories[category].total++
      if (control.verification_status === 'verified') {
        categories[category].verified++
      }
    })
    
    return Object.entries(categories).map(([code, data]) => ({
      code,
      percentage: Math.round((data.verified / data.total) * 100)
    }))
  }, [controls])

  const handleRemind = async (requestId: string) => {
    try {
      // API call to remind
      toast.success("Reminder sent")
      onRefresh()
    } catch (error) {
      console.error("Failed to send reminder:", error)
      toast.error("Failed to send reminder")
    }
  }

  const handleMessage = (control: EngagementControl) => {
    if (onMessageLink) {
      onMessageLink({
        type: 'control',
        id: control.id,
        title: control.name || `Control ${control.control_code}`
      })
    }
  }

  return (
    <div className="space-y-6">
      {/* Engagements Table */}
      {!selectedEngagement && (
      <Card className="border-none shadow-xl overflow-hidden">
        <CardHeader className="px-6 py-4 flex flex-row items-center justify-between border-b bg-muted/20">
          <CardTitle className="text-sm font-bold uppercase tracking-widest opacity-70">Client Portfolio</CardTitle>
          <div className="flex items-center gap-2">
            <div className="h-7 px-3 rounded-full bg-primary/10 text-primary text-[10px] font-black flex items-center">
              {engagements.length} Total
            </div>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={onRefresh}
              disabled={isLoading}
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="divide-y divide-muted/50">
            {/* Column Headers */}
            <div className="hidden lg:grid grid-cols-8 gap-4 px-6 py-3 bg-muted/40 sticky top-0 z-10 border-b border-muted/10">
              <div className="col-span-2 text-[9px] font-black uppercase tracking-[0.2em] text-muted-foreground/70">Engagement</div>
              <div className="text-[9px] font-black uppercase tracking-[0.2em] text-muted-foreground/70">Code</div>
              <div className="text-[9px] font-black uppercase tracking-[0.2em] text-muted-foreground/70">Auditor Firm</div>
              <div className="text-[9px] font-black uppercase tracking-[0.2em] text-muted-foreground/70">Audit Period</div>
              <div className="text-[9px] font-black uppercase tracking-[0.2em] text-muted-foreground/70">Status</div>
              <div className="text-[9px] font-black uppercase tracking-[0.2em] text-muted-foreground/70">Controls</div>
              <div />
            </div>

            {/* List Items */}
            {engagements.map(eng => (
              <div 
                key={eng.id} 
                onClick={() => onSelectEngagement(eng)}
                className={`
                  w-full grid grid-cols-8 gap-4 px-6 py-4 hover:bg-muted/30 transition-all text-left group cursor-pointer items-center
                `}
              >
                <div className="col-span-2 flex items-center gap-3">
                  <div className="h-10 w-10 rounded-xl bg-muted group-hover:bg-primary/10 flex items-center justify-center transition-all">
                    <Building2 className="h-5 w-5 text-muted-foreground group-hover:text-primary" />
                  </div>
                  <div>
                    <p className="font-bold text-sm group-hover:text-primary transition-colors">{eng.engagement_name}</p>
                    <p className="text-[10px] text-muted-foreground">
                      {eng.org_name !== "N/A" ? eng.org_name : "No Org"}
                      {eng.workspace_name ? ` • ${eng.workspace_name}` : ""}
                    </p>
                  </div>
                </div>
                <div className="flex items-center">
                  <Badge variant="outline" className="text-[10px] font-bold">
                    {eng.engagement_code}
                  </Badge>
                </div>
                <div className="flex items-center text-sm text-muted-foreground">
                  {eng.auditor_firm}
                </div>
                <div className="flex items-center text-sm text-muted-foreground">
                  {eng.audit_period_start && eng.audit_period_end ? (
                    <>
                      <Calendar className="h-3 w-3 mr-1" />
                      {new Date(eng.audit_period_start).toLocaleDateString()} - {new Date(eng.audit_period_end).toLocaleDateString()}
                    </>
                  ) : (
                    "N/A"
                  )}
                </div>
                <div className="flex items-center">
                  <Badge 
                    variant={eng.status_name === 'Active' ? 'default' : 'secondary'}
                    className="text-[10px] font-bold"
                  >
                    {eng.status_name}
                  </Badge>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold">
                    {eng.verified_controls_count}/{eng.total_controls_count}
                  </span>
                  <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary transition-all duration-1000"
                      style={{ width: `${(eng.verified_controls_count / (eng.total_controls_count || 1)) * 100}%` }}
                    />
                  </div>
                </div>
                <div className="flex items-center justify-end">
                  <Button variant="ghost" size="sm" className="opacity-0 group-hover:opacity-100 transition-opacity" tabIndex={-1}>
                    Open →
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      )}

      {/* Controls & Progress (when engagement is selected) */}
      {selectedEngagement && (
        <EngagementControlsPanel
          engagementId={selectedEngagement.id}
          controls={controls}
          loading={loadingControls}
          categoryProgress={categoryProgress}
          onMessage={handleMessage}
          onRefresh={() => {
            setLoadingControls(true)
            engagementsApi.listEngagementControls(selectedEngagement.id)
              .then(setControls)
              .catch(console.error)
              .finally(() => setLoadingControls(false))
          }}
        />
      )}
    </div>
  )
}

// ── Controls Panel ────────────────────────────────────────────────────────────

function ControlStatusIcon({ status }: { status: string | null }) {
  if (status === "verified") return <CheckCircle2 className="h-4 w-4 text-green-500" />
  if (status === "qualified") return <AlertTriangle className="h-4 w-4 text-amber-500" />
  if (status === "failed") return <XCircle className="h-4 w-4 text-red-500" />
  return <Clock className="h-4 w-4 text-muted-foreground" />
}

function ControlStatusBadge({ status }: { status: string | null }) {
  if (status === "verified") return <Badge className="text-[10px] bg-green-500/10 text-green-700 border-green-500/20">Verified</Badge>
  if (status === "qualified") return <Badge className="text-[10px] bg-amber-500/10 text-amber-700 border-amber-500/20">Qualified</Badge>
  if (status === "failed") return <Badge className="text-[10px] bg-red-500/10 text-red-700 border-red-500/20">Failed</Badge>
  return <Badge className="text-[10px] bg-muted text-muted-foreground border-border">Pending</Badge>
}

function EngagementControlsPanel({
  engagementId,
  controls,
  loading,
  categoryProgress,
  onMessage,
  onRefresh,
}: {
  engagementId: string
  controls: EngagementControl[]
  loading: boolean
  categoryProgress: { code: string; percentage: number }[]
  onMessage: (control: EngagementControl) => void
  onRefresh: () => void
}) {
  const [search, setSearch] = React.useState("")
  const [verifyTarget, setVerifyTarget] = React.useState<EngagementControl | null>(null)
  const [requestTarget, setRequestTarget] = React.useState<EngagementControl | null>(null)
  const [filterStatus, setFilterStatus] = React.useState<string>("all")

  const filtered = React.useMemo(() => {
    return controls.filter(c => {
      if (filterStatus !== "all") {
        if (filterStatus === "pending" && c.verification_status) return false
        if (filterStatus !== "pending" && c.verification_status !== filterStatus) return false
      }
      if (search.trim()) {
        const q = search.toLowerCase()
        return c.name?.toLowerCase().includes(q) || c.control_code.toLowerCase().includes(q)
      }
      return true
    })
  }, [controls, search, filterStatus])

  const stats = React.useMemo(() => ({
    total: controls.length,
    verified: controls.filter(c => c.verification_status === "verified").length,
    qualified: controls.filter(c => c.verification_status === "qualified").length,
    failed: controls.filter(c => c.verification_status === "failed").length,
    pending: controls.filter(c => !c.verification_status).length,
  }), [controls])

  return (
    <>
      {verifyTarget && (
        <VerifyControlDialog
          engagementId={engagementId}
          control={verifyTarget}
          onClose={() => setVerifyTarget(null)}
          onVerified={onRefresh}
        />
      )}
      {requestTarget && (
        <RequestEvidenceDialog
          engagementId={engagementId}
          control={requestTarget}
          onClose={() => setRequestTarget(null)}
          onRequested={onRefresh}
        />
      )}

      <div className="space-y-4">
        {/* Stats row */}
        <div className="grid grid-cols-5 gap-2">
          {[
            { label: "Total", value: stats.total, color: "text-foreground", bg: "border-l-primary" },
            { label: "Verified", value: stats.verified, color: "text-green-600", bg: "border-l-green-500" },
            { label: "Qualified", value: stats.qualified, color: "text-amber-600", bg: "border-l-amber-500" },
            { label: "Failed", value: stats.failed, color: "text-red-600", bg: "border-l-red-500" },
            { label: "Pending", value: stats.pending, color: "text-muted-foreground", bg: "border-l-border" },
          ].map(s => (
            <div key={s.label} className={`rounded-lg border border-l-[3px] ${s.bg} bg-card px-3 py-2`}>
              <span className={`text-lg font-bold ${s.color}`}>{s.value}</span>
              <span className="text-[10px] text-muted-foreground block">{s.label}</span>
            </div>
          ))}
        </div>

        {/* Category progress bar */}
        {categoryProgress.length > 0 && (
          <div className="flex items-center gap-3 rounded-lg border border-border bg-card px-4 py-3">
            <span className="text-xs font-semibold text-muted-foreground shrink-0">Category Progress</span>
            <div className="flex-1 flex items-center gap-2 overflow-x-auto">
              {categoryProgress.map(cat => (
                <div key={cat.code} className="flex items-center gap-1.5 shrink-0">
                  <span className="text-[10px] font-bold">{cat.code}</span>
                  <div className="w-12 h-1.5 bg-muted rounded-full overflow-hidden">
                    <div className="h-full bg-primary" style={{ width: `${cat.percentage}%` }} />
                  </div>
                  <span className="text-[10px] text-muted-foreground">{cat.percentage}%</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Filter bar */}
        <div className="flex items-center gap-2">
          <div className="relative flex-1 max-w-xs">
            <Search className="absolute left-2.5 top-2 w-3.5 h-3.5 text-muted-foreground" />
            <Input className="pl-8 h-8 text-sm" placeholder="Search controls..." value={search} onChange={e => setSearch(e.target.value)} />
          </div>
          <div className="flex items-center gap-1 bg-muted/40 rounded-lg p-0.5">
            {["all", "pending", "verified", "qualified", "failed"].map(s => (
              <button
                key={s}
                onClick={() => setFilterStatus(s)}
                className={`px-2.5 py-1 rounded text-[10px] font-medium transition-colors ${
                  filterStatus === s ? "bg-background shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {s === "all" ? "All" : s.charAt(0).toUpperCase() + s.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Controls list */}
        <Card className="border-none shadow-lg">
          <CardHeader className="px-4 py-3 border-b bg-muted/20">
            <CardTitle className="text-xs font-bold uppercase tracking-widest">
              Controls ({filtered.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : filtered.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-12">
                {search || filterStatus !== "all" ? "No controls match your filters." : "No controls in this engagement."}
              </p>
            ) : (
              <div className="divide-y divide-border/50">
                {filtered.map(control => (
                  <div
                    key={control.id}
                    className="flex items-center gap-3 px-4 py-3 hover:bg-muted/30 transition-colors group"
                  >
                    <ControlStatusIcon status={control.verification_status} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-primary">{control.control_code}</span>
                        <span className="text-sm truncate">{control.name}</span>
                      </div>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-[10px] text-muted-foreground">{control.category_name}</span>
                        <ControlStatusBadge status={control.verification_status} />
                        {control.evidence_count > 0 && (
                          <span className="text-[10px] text-muted-foreground flex items-center gap-0.5">
                            <FileText className="h-3 w-3" /> {control.evidence_count} evidence
                          </span>
                        )}
                        {control.open_requests_count > 0 && (
                          <Badge variant="outline" className="text-[10px] text-amber-600 border-amber-500/20 bg-amber-500/10">
                            {control.open_requests_count} open request{control.open_requests_count !== 1 ? "s" : ""}
                          </Badge>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-7 text-xs gap-1"
                        onClick={() => setVerifyTarget(control)}
                      >
                        <Shield className="h-3 w-3" />
                        Verify
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-7 text-xs gap-1"
                        onClick={() => setRequestTarget(control)}
                      >
                        <FileText className="h-3 w-3" />
                        Request
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 text-xs gap-1"
                        onClick={() => onMessage(control)}
                      >
                        <MessageSquare className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  )
}
