"use client"

import * as React from "react"
import { 
  Wrench, 
  Upload, 
  MessageSquare, 
  FileCheck, 
  Clock, 
  AlertCircle,
  CheckCircle2,
  ChevronRight,
  Plus,
  Loader2,
  ShieldCheck
} from "lucide-react"

import { 
  Button, 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle,
  Badge,
  Input,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent
} from "@kcontrol/ui"

import { useView } from "@/lib/context/ViewContext"
import { useOrgWorkspace } from "@/lib/context/OrgWorkspaceContext"
import { dashboardApi, type EngineerDashboardResponse } from "@/lib/api/dashboard"
import { listTasks } from "@/lib/api/grc"
import { fetchMe } from "@/lib/api/auth"
import { useRouter } from "next/navigation"

function MetricCard({ title, value, sub, icon: Icon, color }: any) {
    return (
        <Card className={`border-none shadow-sm ${color}`}>
            <CardHeader className="flex flex-row items-center justify-between py-3">
                <CardTitle className="text-[10px] font-bold uppercase tracking-[0.15em] text-muted-foreground">{title}</CardTitle>
                <Icon className="h-4 w-4 opacity-50" />
            </CardHeader>
            <CardContent className="pb-4">
                <div className="text-3xl font-black tracking-tight">{value}</div>
                <p className="text-[10px] text-muted-foreground mt-1 font-medium italic">{sub}</p>
            </CardContent>
        </Card>
    )
}

export default function EngineeringPortalPage() {
  const { activeViewDef } = useView()
  const { selectedOrgId } = useOrgWorkspace()
  const accentColor = activeViewDef?.color ?? "#6366f1"
  const router = useRouter()

  const [data, setData] = React.useState<EngineerDashboardResponse | null>(null)
  const [tasks, setTasks] = React.useState<any[]>([])
  const [profileEmail, setProfileEmail] = React.useState<string | null>(null)
  const [loading, setLoading] = React.useState(true)

  const loadData = React.useCallback(async () => {
      if (!selectedOrgId) return
      setLoading(true)
      try {
          // 1. Get profile so we can display/use the user's authentic email link
          const profile = await fetchMe()
          setProfileEmail(profile.email)

          // 2. Safely parallelize the dashboard metric and list tasks fetching
          const [resp, tasksResp] = await Promise.all([
             dashboardApi.getEngineer(selectedOrgId),
             listTasks({
                 orgId: selectedOrgId,
                 // Using the secure ID mapped from the profile endpoint to correctly resolve assignments
                 assignee_user_id: profile.user_id,
                 limit: 50
             })
          ])

          setData(resp)
          
          // Filter out resolved tasks for the pending queue
          const pendingTasks = (tasksResp.items as any[]).filter(t => t.status_code !== "resolved" && t.status_code !== "cancelled")
          setTasks(pendingTasks)
      } catch (e) {
          console.error("Failed to load engineer dashboard", e)
      } finally {
          setLoading(false)
      }
  }, [selectedOrgId])

  React.useEffect(() => { loadData() }, [loadData])

  const nearestTask = React.useMemo(() => {
     return [...tasks]
         .filter((t) => t.due_date)
         .sort((a, b) => new Date(a.due_date).getTime() - new Date(b.due_date).getTime())[0]
  }, [tasks])

  if (loading) {
      return (
          <div className="flex flex-col items-center justify-center min-h-[50vh] text-muted-foreground space-y-4">
              <Loader2 className="h-8 w-8 animate-spin" />
              <p className="text-xs font-bold uppercase tracking-widest opacity-50">Synthesizing Your Queue...</p>
          </div>
      )
  }

  return (
    <div className="flex-1 space-y-8 pb-20">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-black tracking-tighter flex items-center gap-2">
            <Wrench className="h-6 w-6 text-orange-500" />
            ENGINEER PORTAL
          </h1>
          <p className="text-sm text-muted-foreground font-medium">
             Operational queue for controls and evidence tasks you own.
          </p>
        </div>
        <div className="flex items-center gap-3">
             <Button variant="ghost" size="sm" className="h-9 px-4 rounded-full bg-muted/30 font-bold text-[10px] uppercase tracking-widest" onClick={loadData}>
                 Refresh Queue
             </Button>
             <Button 
                onClick={() => document.getElementById("engineered-task-queue")?.scrollIntoView({ behavior: "smooth" })}
                className="h-9 px-6 rounded-full font-bold text-[10px] uppercase tracking-widest gap-2 shadow-lg shadow-primary/20"
             >
                <Plus className="h-4 w-4" />
                Submit Evidence
             </Button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid gap-4 md:grid-cols-3">
         <MetricCard 
            title="Controls I Own" 
            value={data?.owned_controls_count ?? 0}
            sub="Assigned as primary owner"
            icon={ShieldCheck}
            color="bg-indigo-500/5"
         />
         <MetricCard 
            title="Awaiting Action" 
            value={data?.pending_tasks_count ?? 0}
            sub="Evidence or responses due"
            icon={Clock}
            color="bg-orange-500/5"
         />
         <MetricCard 
            title="In Review" 
            value={data?.tasks_by_status?.['internal_review'] ?? 0}
            sub="Awaiting GRC Lead / Auditor"
            icon={FileCheck}
            color="bg-green-500/5"
         />
      </div>

      {nearestTask && (
         <Card 
            className="bg-orange-500 text-white border-0 shadow-lg cursor-pointer hover:bg-orange-600 transition-colors mt-6" 
            onClick={() => router.push(`/tasks/${nearestTask.id}`)}
         >
            <CardContent className="p-5 flex items-center justify-between">
               <div className="flex items-center gap-4">
                  <div className="bg-black/10 p-3 rounded-xl ring-1 ring-white/20">
                     <Clock className="h-6 w-6 text-white" />
                  </div>
                  <div>
                     <h3 className="text-[10px] font-black uppercase tracking-widest text-white/70 mb-0.5">Nearest Deadline</h3>
                     <p className="text-lg font-black tracking-tight">{nearestTask.title}</p>
                  </div>
               </div>
               <div className="text-right flex items-center gap-4">
                  <div>
                     <div className="text-[10px] font-bold uppercase tracking-widest text-white/70 mb-0.5">Due By</div>
                     <div className="text-xl font-black">{new Date(nearestTask.due_date).toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" })}</div>
                  </div>
                  <ChevronRight className="h-4 w-4 text-white/50" />
               </div>
            </CardContent>
         </Card>
      )}

      <Tabs defaultValue="tasks" className="space-y-6">
         <TabsList className="bg-muted p-1 h-11 items-center rounded-xl">
             <TabsTrigger value="tasks" className="gap-2 px-6 rounded-lg font-bold text-[11px] uppercase tracking-wider">
                 Your Work Item Queue
                 {data?.pending_tasks_count ? (
                    <Badge className="ml-2 h-5 px-1.5 bg-orange-500 text-white border-none">{data.pending_tasks_count}</Badge>
                 ) : null}
             </TabsTrigger>
             <TabsTrigger value="history" className="gap-2 px-6 rounded-lg font-bold text-[11px] uppercase tracking-wider">
                 Verification History
             </TabsTrigger>
         </TabsList>

         <TabsContent value="tasks" className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-500">
             {data?.pending_tasks_count === 0 ? (
                 <Card className="border-dashed border-2 py-20 bg-muted/5">
                    <CardContent className="flex flex-col items-center text-center space-y-4">
                        <div className="h-12 w-12 rounded-full bg-green-500/10 flex items-center justify-center">
                            <CheckCircle2 className="h-6 w-6 text-green-500" />
                        </div>
                        <h3 className="font-bold text-lg leading-none italic uppercase tracking-tighter opacity-70">Queue Clear</h3>
                        <p className="text-xs text-muted-foreground max-w-xs">
                            No evidence tasks or auditor requests are currently pending for your assigned controls.
                        </p>
                    </CardContent>
                 </Card>
             ) : (
                <div id="engineered-task-queue" className="space-y-3">
                   <div className="flex items-center justify-between mb-2">
                       <p className="text-xs font-bold text-muted-foreground uppercase tracking-widest pl-1">
                           High Impact Actions
                       </p>
                       {profileEmail && (
                           <Badge variant="outline" className="text-[9px] uppercase tracking-widest opacity-50 bg-white/5">
                               Viewing Queue For: {profileEmail}
                           </Badge>
                       )}
                   </div>
                   {tasks.map((task) => (
                       <Card key={task.id} className="border-l-4 border-l-orange-500 hover:shadow-md transition-shadow cursor-pointer dark:bg-black/40">
                          <CardContent className="p-5 flex items-center justify-between">
                             <div className="space-y-1">
                                <div className="flex items-center gap-2">
                                   {task.priority_code === "critical" || task.priority_code === "high" ? (
                                      <Badge variant="warning" className="uppercase text-[9px] h-4">Priority Required</Badge>
                                   ) : (
                                       <Badge variant="outline" className="uppercase text-[9px] h-4 border-white/10 dark:text-teal-400 bg-white/5">{task.priority_name}</Badge>
                                   )}
                                   <span className="text-[10px] text-muted-foreground font-bold italic">{task.task_type_name}</span>
                                </div>
                                <h3 className="text-base font-bold">{task.title}</h3>
                                <p className="text-xs text-muted-foreground">
                                    {task.due_date ? `Due for audit review on ${new Date(task.due_date).toLocaleDateString()}` : "No specific due date assigned"}
                                </p>
                             </div>
                             <Button 
                                onClick={() => router.push(`/tasks/${task.id}`)}
                                size="sm" 
                                className="h-8 px-4 rounded-full font-bold text-[10px] uppercase tracking-widest gap-2"
                             >
                                <Upload className="h-3 w-3" />
                                Submit
                             </Button>
                          </CardContent>
                       </Card>
                   ))}
                   {tasks.length === 0 && (
                       <p className="text-sm text-muted-foreground italic pl-1">No tasks returned from query.</p>
                   )}
                </div>
             )}
         </TabsContent>

         <TabsContent value="history" className="animate-in fade-in slide-in-from-bottom-2 duration-500">
             <Card>
                <CardContent className="flex flex-col items-center justify-center py-20 text-center opacity-50">
                    <Clock className="h-12 w-12 mb-4 text-muted-foreground" />
                    <p className="text-sm font-bold uppercase tracking-widest">No recent audit verifications found</p>
                </CardContent>
             </Card>
         </TabsContent>
      </Tabs>
    </div>
  )
}
