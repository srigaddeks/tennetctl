"use client"

import * as React from "react"
import { 
  BarChart3, 
  Target, 
  TrendingUp, 
  ShieldCheck, 
  AlertTriangle,
  History,
  CheckCircle2,
  Calendar,
  Lock,
  ChevronRight,
  TrendingDown
} from "lucide-react"

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
  TabsContent
} from "@kcontrol/ui"

import { useView } from "@/lib/context/ViewContext"
import { useOrgWorkspace } from "@/lib/context/OrgWorkspaceContext"
import { dashboardApi, type ExecutiveDashboardResponse } from "@/lib/api/dashboard"
import { Loader2 } from "lucide-react"

import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@kcontrol/ui"

import { HelpCircle } from "lucide-react"

function StatCard({ title, value, sub, icon: Icon, color, trend, description }: any) {
  return (
    <Card className={`${color} border-none shadow-sm relative group transition-all duration-300 hover:shadow-md`}>
      <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
        <Icon className="h-20 w-20" />
      </div>
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <CardTitle className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/80">{title}</CardTitle>
          <Tooltip>
            <TooltipTrigger asChild>
              <button className="inline-flex items-center justify-center rounded-full text-muted-foreground/40 hover:text-primary transition-colors focus-visible:outline-none">
                <HelpCircle className="h-3.5 w-3.5" />
              </button>
            </TooltipTrigger>
            <TooltipContent 
              side="top"
              align="start" 
              className="max-w-[240px] text-[12px] leading-relaxed p-4 bg-gray-900 text-white dark:bg-zinc-800 dark:text-zinc-100 border-none shadow-2xl z-[100]"
            >
              <div className="space-y-1.5">
                <p className="font-bold uppercase tracking-wider text-[10px] opacity-70">{title}</p>
                <p className="font-medium">{description}</p>
              </div>
            </TooltipContent>
          </Tooltip>
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-4xl font-black mb-1">{value}</div>
        <p className="text-xs text-muted-foreground font-medium flex items-center gap-1.5 min-h-[1.5rem]">
          {trend && (
             <span className="flex items-center gap-1">
                {trend.up ? <TrendingUp className="h-3 w-3 text-green-500" /> : <TrendingDown className="h-3 w-3 text-red-500" />}
                {trend.text}
             </span>
          )}
          {sub}
        </p>
      </CardContent>
    </Card>
  )
}

export default function ExecutiveAuditView() {
  const { activeViewDef } = useView()
  const { selectedOrgId } = useOrgWorkspace()
  const [loading, setLoading] = React.useState(true)
  const [data, setData] = React.useState<ExecutiveDashboardResponse | null>(null)

  const loadData = React.useCallback(async () => {
    setLoading(true)
    try {
       const resp = await dashboardApi.getExecutive(selectedOrgId)
       setData(resp)
    } catch (e) {
       console.error("Failed to load executive dashboard", e)
    } finally {
       setLoading(false)
    }
  }, [selectedOrgId])

  React.useEffect(() => { loadData() }, [loadData])

  if (loading) {
     return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
           <Loader2 className="h-10 w-10 animate-spin text-primary/50" />
           <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground opacity-50">Aggregating Global Posture...</p>
        </div>
     )
  }
  
  return (
   <TooltipProvider delayDuration={0}>
    <div className="flex-1 space-y-8 animate-in fade-in duration-500">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">Compliance & Audit Posture</h1>
          <p className="text-muted-foreground mt-2 text-lg">
             Strategic overview of ongoing audits, compliance health, and organizational risk.
          </p>
        </div>
        <div className="flex gap-3">
           <Button variant="outline" className="h-11 px-6 font-bold text-xs uppercase tracking-widest gap-2" onClick={loadData}>
              <History className="h-4 w-4 text-muted-foreground" />
              Refresh Data
           </Button>
           <Button className="h-11 px-6 font-bold text-xs uppercase tracking-widest gap-2 shadow-lg shadow-primary/20">
              <BarChart3 className="h-4 w-4" />
              Executive Report
           </Button>
        </div>
      </div>

      {/* Strategic Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
         <StatCard 
            title="Controls Verified" 
            value={`${Math.round(data?.controls_verified_percentage ?? 0)}%`}
            sub="Across all active audits"
            description="The total percentage of security controls that have been tested and verified as compliant across all active frameworks."
            icon={ShieldCheck}
            color="bg-primary/5 dark:bg-primary/10"
         />

         <StatCard 
            title="Org. Findings" 
            value={data?.pending_findings_count ?? 0}
            sub="Open compliance gaps"
            description="The current count of open issues, misconfigurations, or gaps discovered during audits that require resolution."
            icon={AlertTriangle}
            color="bg-amber-500/5 dark:bg-amber-500/10"
         />

         <StatCard 
            title="Audit Status" 
            value={data?.audit_status ?? "On Track"}
            sub={data?.milestones?.length ? `Next milestone: ${data.milestones[0].title}` : "All active work on schedule"}
            description="Aggregated operational health of ongoing engagements, indicating if teams are meeting target audit timelines."
            icon={Target}
            color="bg-purple-500/5 dark:bg-purple-500/10"
         />

         <StatCard 
            title="Trust Score" 
            value={`${Math.round(data?.trust_score ?? 0)}%`}
            sub="Consolidated compliance health"
            description="A real-time metric of your security and compliance posture, weighted by control criticality and verification results."
            icon={Lock}
            color="bg-blue-500/5 dark:bg-blue-500/10"
         />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
         <Card className="lg:col-span-2">
            <CardHeader className="flex flex-row items-center justify-between border-b px-6 py-4">
               <div>
                  <CardTitle className="text-lg font-bold">Audit Portfolio Status</CardTitle>
                  <p className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider mt-0.5">Summary of all active engagements</p>
               </div>
               <Button variant="ghost" size="sm" className="h-8 font-bold text-[10px] uppercase tracking-wide gap-2 text-primary">
                  Detailed Dashboard
                  <ChevronRight className="h-3.5 w-3.5" />
               </Button>
            </CardHeader>
            <CardContent className="p-0">
               <div className="divide-y">
                  {data?.portfolio?.length ? data.portfolio.map((aud) => (
                    <div key={aud.id} className="flex items-center justify-between p-6 hover:bg-muted/30 transition-colors">
                       <div className="space-y-1 flex-1">
                          <h4 className="font-bold text-base">{aud.name}</h4>
                          <div className="flex items-center gap-4">
                             <div className="flex-1 max-w-[200px] h-1.5 bg-muted rounded-full overflow-hidden">
                                <div className="h-full bg-primary" style={{ width: `${aud.progress}%` }} />
                             </div>
                             <span className="text-xs font-bold text-muted-foreground">{Math.round(aud.progress)}% COMPLETE</span>
                          </div>
                       </div>
                       <div className="flex items-center gap-8 pl-8">
                          <div className="flex flex-col items-center">
                             <span className="text-[9px] font-bold text-muted-foreground uppercase tracking-widest mb-1">RISK LEVEL</span>
                             <Badge 
                               variant="outline" 
                               className={`h-5 text-[10px] uppercase tracking-wide font-bold ${
                                 aud.risk_level.toLowerCase() === 'none' ? 'text-green-500 border-green-500/20' : 
                                 aud.risk_level.toLowerCase() === 'low' ? 'text-blue-500 border-blue-500/20' : 
                                 'text-amber-500 border-amber-500/20'
                               }`}
                             >
                                {aud.risk_level}
                             </Badge>
                          </div>
                          <div className="flex flex-col items-end min-w-[80px]">
                             <span className="text-[9px] font-bold text-muted-foreground uppercase tracking-widest mb-1">STATUS</span>
                             <span className="text-sm font-bold">{aud.status}</span>
                          </div>
                       </div>
                    </div>
                  )) : (
                    <div className="flex flex-col items-center justify-center p-20 text-center space-y-2 opacity-50">
                        <BarChart3 className="h-10 w-10 text-muted-foreground" />
                        <p className="text-sm font-bold tracking-tight">No active engagements found</p>
                    </div>
                  )}
               </div>
            </CardContent>
         </Card>

         <Card className="flex flex-col h-full overflow-hidden bg-muted/20 border-none shadow-none">
            <CardHeader className="py-4">
               <CardTitle className="text-xs font-bold uppercase tracking-widest text-muted-foreground">Audit Milestones</CardTitle>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col pt-0">
               <div className="relative flex-1">
                  {/* Timeline Line */}
                  <div className="absolute left-[7px] top-2 bottom-2 w-0.5 bg-primary/20" />
                  
                  <div className="space-y-8 relative">
                     {data?.milestones?.length ? data.milestones.map((m) => (
                       <div key={m.id} className="flex gap-4 group">
                          <div className={`mt-1.5 h-4 w-4 rounded-full border-2 bg-background z-10 shrink-0 transition-all ${
                            m.status === 'completed' ? 'border-primary bg-primary' : 
                            m.status === 'active' ? 'border-primary animate-pulse' : 
                            'border-muted-foreground/30'
                          }`}>
                            {m.status === 'completed' && <CheckCircle2 className="h-3 w-3 text-primary-foreground" />}
                          </div>
                          <div className="space-y-1 overflow-hidden">
                             <p className={`text-sm font-bold leading-none truncate ${m.status === 'setup' ? 'text-muted-foreground' : ''}`}>{m.title}</p>
                             <p className="text-[11px] font-medium text-muted-foreground">
                                {m.date ? new Date(m.date).toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" }) : "TBD"}
                             </p>
                             {m.status === 'active' && (
                               <Badge className="h-5 text-[9px] font-bold uppercase tracking-wider bg-primary/20 text-primary border-none mt-1">Current Focus</Badge>
                             )}
                          </div>
                       </div>
                     )) : (
                        <p className="text-xs text-muted-foreground italic pl-8">No upcoming milestones</p>
                     )}
                  </div>
               </div>
            </CardContent>
         </Card>
      </div>
    </div>
   </TooltipProvider>
  )
}
