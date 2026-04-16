"use client"

import * as React from "react"
import { 
  CheckCircle2,
  Search,
  Filter,
  Clock,
  Loader2,
  RefreshCw,
  MessageSquare,
  User,
  ShieldAlert,
  ArrowUpRight,
  Activity,
  ClipboardList
} from "lucide-react"

import { 
  Button, 
  Card, 
  CardContent, 
  Badge,
  Input
} from "@kcontrol/ui"

import { listTasks, updateTask } from "@/lib/api/grc"
import { toast } from "sonner"

interface Task {
  id: string
  org_id: string
  workspace_id: string
  task_type_code: string
  task_type_name: string
  priority_code: string
  priority_name: string
  status_code: string
  status_name: string
  title: string
  description: string | null
  entity_type: string
  entity_id: string
  assignee_user_id: string | null
  assignee_name: string | null
  due_date: string | null
  start_date: string | null
  is_overdue: boolean
  created_at: string
  updated_at: string
}

interface TasksViewProps {
  orgId?: string
  workspaceId?: string
  engagementId?: string
}

export function TasksView({ 
  orgId,
  workspaceId,
  engagementId
}: TasksViewProps) {
  const [tasks, setTasks] = React.useState<Task[]>([])
  const [isLoading, setIsLoading] = React.useState(true)
  const [searchQuery, setSearchQuery] = React.useState("")
  const [activeFilter, setActiveFilter] = React.useState("all")

  // Fetch tasks
  const fetchTasks = React.useCallback(async () => {
    if (!orgId && !workspaceId && !engagementId) {
      setIsLoading(false)
      setTasks([])
      return
    }
    setIsLoading(true)
    try {
      const data = await listTasks({
        orgId,
        workspaceId,
        engagementId,
        limit: 100
      })
      setTasks((data.items as any[]) || [])
    } catch (error: any) {
      console.error("Failed to fetch tasks:", error)
      toast.error(error.message || "Failed to load tasks")
    } finally {
      setIsLoading(false)
    }
  }, [orgId, workspaceId, engagementId])

  React.useEffect(() => {
    fetchTasks()
  }, [fetchTasks])

  // Real-time polling
  React.useEffect(() => {
    const interval = setInterval(() => {
      fetchTasks()
    }, 45000)
    return () => clearInterval(interval)
  }, [fetchTasks])

  // Filter tasks
  const filteredTasks = React.useMemo(() => {
    let filtered = tasks

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(task => 
        task.title.toLowerCase().includes(query) ||
        (task.description?.toLowerCase() || "").includes(query) ||
        (task.entity_id || "").toLowerCase().includes(query) ||
        (task.task_type_name || "").toLowerCase().includes(query)
      )
    }

    // Apply status filter
    if (activeFilter !== "all" && activeFilter !== "overdue") {
      filtered = filtered.filter(task => task.status_code === activeFilter)
    } else if (activeFilter === "overdue") {
      filtered = filtered.filter(task => task.is_overdue)
    }

    return filtered
  }, [tasks, searchQuery, activeFilter])

  // Get status badge
  const getStatusBadge = (task: Task) => {
    if (task.is_overdue) {
      return (
        <Badge variant="outline" className="bg-red-500/10 text-red-400 border-red-500/20 px-2 h-5 text-[9px] font-black uppercase tracking-widest">
            <ShieldAlert className="h-2.5 w-2.5 mr-1" />
            Overdue
        </Badge>
      )
    }
    const colors: Record<string, string> = {
      open: "border-border/60 bg-muted/40 text-muted-foreground",
      in_progress: "bg-teal-500/10 text-teal-400 border-teal-500/20",
      resolved: "bg-green-500/10 text-green-400 border-green-500/20",
      completed: "bg-green-500/10 text-green-400 border-green-500/20",
      closed: "border-border/60 bg-muted/40 text-muted-foreground"
    }
    return <Badge variant="outline" className={`${colors[task.status_code] || "border-border/60 bg-muted/40 text-muted-foreground"} px-2 h-5 text-[9px] font-black uppercase tracking-widest`}>{task.status_name}</Badge>
  }

  // Get priority badge
  const getPriorityBadge = (priorityCode: string) => {
    const colors: { [key: string]: string } = {
      critical: 'bg-red-500/20 text-red-500 border-red-500/30',
      high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
      medium: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
      low: 'bg-green-500/20 text-green-400 border-green-500/30'
    }
    return (
      <Badge variant="outline" className={`${colors[priorityCode] || 'border-border/60 bg-muted/40 text-muted-foreground'} text-[9px] h-5 font-black uppercase tracking-tighter`}>
        {priorityCode}
      </Badge>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-foreground uppercase">Workload & Task Ledger</h2>
          <p className="mt-1 text-sm font-medium uppercase tracking-[0.2em] text-primary/80">
             Syncing {tasks.length} active tasks across this workspace
          </p>
        </div>
        <Button 
            variant="ghost" 
            size="sm" 
            onClick={fetchTasks}
            disabled={isLoading}
            className="h-10 rounded-xl border border-border/60 bg-background/70 px-4 font-bold uppercase tracking-widest text-muted-foreground hover:bg-muted hover:text-foreground"
        >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
        </Button>
      </div>

      {/* Control Panel */}
      <div className="flex flex-col items-center gap-4 rounded-2xl border border-border/60 bg-card/80 p-1.5 md:flex-row">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground/60" />
          <Input
            placeholder="Search tasks, types, or entities..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-11 border-none bg-transparent pl-12 text-foreground placeholder:text-muted-foreground/60 focus-visible:ring-0"
          />
        </div>
        <div className="flex shrink-0 gap-1 overflow-x-auto rounded-xl border border-border/60 bg-background/80 p-1">
            {["all", "open", "in_progress", "completed", "overdue"].map(filter => (
                <Button
                key={filter}
                variant={activeFilter === filter ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setActiveFilter(filter)}
                className={`capitalize h-9 px-4 rounded-lg text-[10px] font-black tracking-widest transition-all ${
                    activeFilter === filter 
                    ? "border border-primary/30 bg-primary/15 text-primary" 
                    : "text-muted-foreground hover:text-foreground"
                }`}
                >
                {filter}
                </Button>
            ))}
        </div>
      </div>

      {/* Main Table */}
      <Card className="overflow-hidden rounded-2xl border-border/60 bg-card/85 shadow-sm backdrop-blur-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
                <thead>
                    <tr className="border-b border-border/60 bg-muted/40">
                        <th className="px-6 py-4 text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">Context</th>
                        <th className="px-6 py-4 text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">Task Narrative</th>
                        <th className="px-6 py-4 text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">Ownership</th>
                        <th className="px-6 py-4 text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">Timeline</th>
                        <th className="px-6 py-4 text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">State</th>
                        <th className="px-6 py-4 text-right text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground">Actions</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                    {isLoading ? (
                        <tr>
                            <td colSpan={6} className="py-24 text-center">
                                <Loader2 className="mx-auto h-10 w-10 animate-spin text-primary/60" />
                                <p className="mt-4 text-[10px] font-black uppercase tracking-[0.3em] text-muted-foreground">Syncing Task Hub...</p>
                            </td>
                        </tr>
                    ) : filteredTasks.length === 0 ? (
                        <tr>
                            <td colSpan={6} className="py-24 text-center">
                                <Activity className="mx-auto mb-4 h-12 w-12 text-muted-foreground/30" />
                                <p className="text-sm font-black uppercase tracking-widest text-muted-foreground">No matching tasks found</p>
                            </td>
                        </tr>
                    ) : filteredTasks.map(task => (
                        <tr key={task.id} className={`group transition-colors hover:bg-muted/30 ${task.is_overdue ? 'bg-red-500/[0.04]' : ''}`}>
                            <td className="px-6 py-6 transition-all">
                                <div className="space-y-2">
                                    <Badge variant="outline" className="border-primary/20 bg-primary/10 text-[9px] font-black uppercase text-primary">{task.task_type_name}</Badge>
                                    <div className="flex items-center gap-2">
                                        <div className="h-1.5 w-1.5 rounded-full bg-primary/60" />
                                        <p className="text-[10px] font-mono font-bold uppercase text-muted-foreground">{task.entity_id || 'Global'}</p>
                                    </div>
                                </div>
                            </td>
                            <td className="px-6 py-6 max-w-sm">
                                <p className="text-sm font-black leading-tight text-foreground transition-colors">{task.title}</p>
                                <p className="mt-1.5 line-clamp-2 text-xs leading-relaxed text-muted-foreground">{task.description || "No supplemental details provided."}</p>
                            </td>
                            <td className="px-6 py-6">
                                <div className="flex items-center gap-3">
                                    <div className="flex h-8 w-8 items-center justify-center rounded-full border border-border/60 bg-muted/50 text-[10px] font-black text-muted-foreground">
                                        {task.assignee_name?.[0] || '?'}
                                    </div>
                                    <p className="text-xs font-bold text-muted-foreground">{task.assignee_name || "Unassigned"}</p>
                                </div>
                            </td>
                            <td className="px-6 py-6">
                                {task.due_date ? (
                                    <div className="space-y-0.5">
                                        <p className="text-[9px] font-black uppercase tracking-widest text-muted-foreground">Schedule</p>
                                        <p className={`text-xs font-bold ${task.is_overdue ? 'text-red-500 dark:text-red-400' : 'text-foreground/80'}`}>
                                            {new Date(task.due_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                                        </p>
                                    </div>
                                ) : (
                                    <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/70">Open Schedule</p>
                                )}
                            </td>
                            <td className="px-6 py-6">
                                {getStatusBadge(task)}
                            </td>
                            <td className="px-6 py-6 text-right">
                                <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-all">
                                    <Button 
                                        variant="ghost" 
                                        size="sm" 
                                        className="h-9 w-9 rounded-xl text-muted-foreground hover:bg-muted hover:text-foreground transition-all"
                                    >
                                        <MessageSquare className="h-4 w-4" />
                                    </Button>
                                    <Button 
                                        variant="ghost" 
                                        size="sm" 
                                        className="h-9 w-9 rounded-xl text-muted-foreground hover:bg-muted hover:text-primary transition-all"
                                    >
                                        <ArrowUpRight className="h-4 w-4" />
                                    </Button>
                                </div>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
          </div>
      </Card>
    </div>
  )
}
