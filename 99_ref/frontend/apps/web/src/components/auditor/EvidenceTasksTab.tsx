"use client"

import * as React from "react"
import { 
  CheckSquare,
  Search,
  Filter,
  Download,
  Plus,
  Clock,
  MessageSquare,
  AlertCircle,
  CheckCircle2,
  Loader2,
  RefreshCw,
  ShieldCheck,
} from "lucide-react"
import { SearchableControlSelector } from "./SearchableControlSelector"

import { 
  Button, 
  Card, 
  CardContent, 
  Badge,
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  Input,
  Label,
} from "@kcontrol/ui"

import { 
  engagementsApi,
  type EngagementParticipant,
  type EngagementControl,
} from "@/lib/api/engagements"
import type { TaskResponse } from "@/lib/types/grc"
import { toast } from "sonner"
import { Textarea } from "@/components/ui/textarea"

type Task = TaskResponse & {
  assignee_name?: string | null
  is_overdue?: boolean
}

interface EvidenceTasksTabProps {
  engagementId: string
  onTaskCreated?: () => void
  onMessageLink?: (entity: { type: string; id: string; title?: string }) => void
}

export function EvidenceTasksTab({ 
  engagementId,
  onTaskCreated,
  onMessageLink
}: EvidenceTasksTabProps) {
  const [tasks, setTasks] = React.useState<Task[]>([])
  const [isLoading, setIsLoading] = React.useState(true)
  const [searchQuery, setSearchQuery] = React.useState("")
  const [activeFilter, setActiveFilter] = React.useState("all")
  const [remindingId, setRemindingId] = React.useState<string | null>(null)
  const [requestingAccessId, setRequestingAccessId] = React.useState<string | null>(null)
  const [exporting, setExporting] = React.useState(false)
  const [createOpen, setCreateOpen] = React.useState(false)
  const [isCreating, setIsCreating] = React.useState(false)
  const [participants, setParticipants] = React.useState<EngagementParticipant[]>([])
  const [controls, setControls] = React.useState<EngagementControl[]>([])
  const [createForm, setCreateForm] = React.useState({
    title: "",
    description: "",
    controlId: "",
    taskTypeCode: "evidence_request",
    priorityCode: "medium",
    dueDate: "",
    assigneeUserId: "",
  })

  // Fetch tasks
  const fetchTasks = React.useCallback(async () => {
    if (!engagementId) return
    
    setIsLoading(true)
    try {
      const data = await engagementsApi.listEngagementTasks(engagementId)
      setTasks(
        (data.items as Task[]).map((task) => ({
          ...task,
          is_overdue:
            !!task.due_date &&
            !task.is_terminal &&
            new Date(task.due_date).getTime() < Date.now(),
        })),
      )
    } catch (error) {
      console.error("Failed to fetch tasks:", error)
      toast.error((error as Error).message || "Failed to load engagement tasks")
    } finally {
      setIsLoading(false)
    }
  }, [engagementId])

  React.useEffect(() => {
    fetchTasks()
  }, [fetchTasks])

  React.useEffect(() => {
    if (!engagementId) {
      setParticipants([])
      setControls([])
      return
    }
    engagementsApi
      .listEngagementParticipants(engagementId)
      .then(setParticipants)
      .catch((error) => {
        console.error("Failed to fetch engagement participants:", error)
        toast.error((error as Error).message || "Failed to load engagement participants")
      })

    engagementsApi
      .listEngagementControls(engagementId)
      .then(setControls)
      .catch((error) => {
        console.error("Failed to fetch engagement controls:", error)
      })
  }, [engagementId])

  // Real-time polling every 30 seconds
  React.useEffect(() => {
    const interval = setInterval(() => {
      fetchTasks()
    }, 30000)
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
        task.description?.toLowerCase().includes(query) ||
        (task.entity_id || "").toLowerCase().includes(query)
      )
    }

    // Apply status filter
    if (activeFilter !== "all") {
      filtered = filtered.filter(task => {
        if (activeFilter === "overdue") {
          return task.is_overdue
        }
        if (activeFilter === "open") {
          return task.status_code === 'open'
        }
        if (activeFilter === "finding") {
          return task.task_type_code === 'finding'
        }
        if (activeFilter === "evidence") {
          return task.task_type_code === 'evidence_request'
        }
        return true
      })
    }

    return filtered
  }, [tasks, searchQuery, activeFilter])

  // Handle remind
  const handleRemind = async (taskId: string) => {
    setRemindingId(taskId)
    try {
      // API call to remind
      await new Promise(resolve => setTimeout(resolve, 1000))
      toast.success("Task reminder sent")
      fetchTasks()
    } catch (error) {
      console.error("Failed to send reminder:", error)
      toast.error("Failed to send reminder")
    } finally {
      setRemindingId(null)
    }
  }

  // Handle message
  const handleMessage = (task: Task) => {
    if (onMessageLink) {
      onMessageLink({
        type: 'task',
        id: task.id,
        title: task.title
      })
    }
  }

  // Handle request access
  const handleRequestAccess = async (task: Task) => {
    setRequestingAccessId(task.id)
    try {
      await engagementsApi.requestTaskAccess(engagementId, task.id, {
        description: `Requesting access to evidence for task: ${task.title}`
      })
      toast.success("Evidence access request submitted")
      fetchTasks()
    } catch (error) {
      console.error("Failed to request access:", error)
      toast.error((error as Error).message || "Failed to request access")
    } finally {
      setRequestingAccessId(null)
    }
  }

  // Handle export CSV
  const handleExportCsv = async () => {
    setExporting(true)
    try {
      const csvRows = [
        ["Title", "Type", "Priority", "Status", "Entity", "Due Date", "Description"],
        ...filteredTasks.map((task) => [
          task.title,
          task.task_type_name || task.task_type_code,
          task.priority_name || task.priority_code,
          task.status_name || task.status_code,
          task.entity_id || "",
          task.due_date || "",
          task.description || "",
        ]),
      ]
      const csvContent = csvRows
        .map((row) =>
          row
            .map((value) => `"${String(value).replace(/"/g, '""')}"`)
            .join(","),
        )
        .join("\n")
      const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'evidence-tasks.csv'
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      toast.success("Tasks exported successfully")
    } catch (error) {
      console.error("Failed to export:", error)
      toast.error("Failed to export tasks")
    } finally {
      setExporting(false)
    }
  }

  // Handle new task
  const handleNewTask = () => {
    setCreateOpen(true)
  }

  const handleCreateTask = async () => {
    if (!createForm.title.trim()) {
      toast.error("Task title is required")
      return
    }
    setIsCreating(true)
    try {
      await engagementsApi.createEngagementTask(engagementId, {
        title: createForm.title.trim(),
        description: createForm.description.trim() || undefined,
        task_type_code: createForm.taskTypeCode,
        priority_code: createForm.priorityCode,
        due_date: createForm.dueDate || undefined,
        assignee_user_id: createForm.assigneeUserId || undefined,
        entity_type: createForm.controlId ? "control" : "engagement",
        entity_id: createForm.controlId || undefined,
      })
      toast.success("Engagement task created")
      setCreateOpen(false)
      setCreateForm({
        title: "",
        description: "",
        controlId: "",
        taskTypeCode: "evidence_request",
        priorityCode: "medium",
        dueDate: "",
        assigneeUserId: "",
      })
      await fetchTasks()
      onTaskCreated?.()
    } catch (error) {
      console.error("Failed to create task:", error)
      toast.error((error as Error).message || "Failed to create task")
    } finally {
      setIsCreating(false)
    }
  }

  // Get status badge
  const getStatusBadge = (task: Task) => {
    if (task.is_overdue) {
      return <Badge variant="destructive"><AlertCircle className="h-3 w-3 mr-1" />Overdue</Badge>
    }
    if (task.status_code === 'open') {
      return <Badge variant="secondary"><Clock className="h-3 w-3 mr-1" />Open</Badge>
    }
    if (task.status_code === 'in_progress') {
      return <Badge variant="default"><Loader2 className="h-3 w-3 mr-1 animate-spin" />In Progress</Badge>
    }
    if (task.status_code === 'resolved') {
      return <Badge variant="default" className="bg-green-500/20 text-green-400"><CheckCircle2 className="h-3 w-3 mr-1" />Resolved</Badge>
    }
    return <Badge variant="outline">{task.status_name}</Badge>
  }

  // Get priority badge
  const getPriorityBadge = (priorityCode: string) => {
    const colors: { [key: string]: string } = {
      critical: 'bg-red-500/20 text-red-400',
      high: 'bg-orange-500/20 text-orange-400',
      medium: 'bg-amber-500/20 text-amber-400',
      low: 'bg-green-500/20 text-green-400'
    }
    return (
      <Badge variant="secondary" className={colors[priorityCode] || ''}>
        {priorityCode}
      </Badge>
    )
  }

  return (
    <div className="space-y-6">
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Create Engagement Task</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="auditor-task-title">Task title</Label>
              <Input
                id="auditor-task-title"
                value={createForm.title}
                onChange={(e) => setCreateForm((prev) => ({ ...prev, title: e.target.value }))}
                placeholder="Document request follow-up"
              />
            </div>
            
            <SearchableControlSelector
              label="Associated Control"
              controls={controls}
              value={createForm.controlId}
              onChange={(val) => setCreateForm((prev) => ({ ...prev, controlId: val }))}
            />

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="auditor-task-type">Task type</Label>
                <select
                  id="auditor-task-type"
                  value={createForm.taskTypeCode}
                  onChange={(e) => setCreateForm((prev) => ({ ...prev, taskTypeCode: e.target.value }))}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="evidence_request">Evidence Request</option>
                  <option value="remediation">Remediation</option>
                  <option value="review">Review</option>
                  <option value="documentation">Documentation</option>
                </select>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="auditor-task-priority">Priority</Label>
                <select
                  id="auditor-task-priority"
                  value={createForm.priorityCode}
                  onChange={(e) => setCreateForm((prev) => ({ ...prev, priorityCode: e.target.value }))}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="auditor-task-due-date">Due date</Label>
              <Input
                id="auditor-task-due-date"
                type="date"
                value={createForm.dueDate}
                onChange={(e) => setCreateForm((prev) => ({ ...prev, dueDate: e.target.value }))}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="auditor-task-assignee">Assignee</Label>
              <select
                id="auditor-task-assignee"
                value={createForm.assigneeUserId}
                onChange={(e) => setCreateForm((prev) => ({ ...prev, assigneeUserId: e.target.value }))}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">Unassigned</option>
                {participants.map((participant) => (
                  <option key={participant.user_id} value={participant.user_id}>
                    {participant.display_name || participant.email || participant.user_id}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="auditor-task-description">Description</Label>
              <Textarea
                id="auditor-task-description"
                value={createForm.description}
                onChange={(e) => setCreateForm((prev) => ({ ...prev, description: e.target.value }))}
                placeholder="Explain what needs to be collected, reviewed, or completed."
                className="min-h-[120px]"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)} disabled={isCreating}>
              Cancel
            </Button>
            <Button onClick={handleCreateTask} disabled={isCreating}>
              {isCreating ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Plus className="h-4 w-4 mr-2" />}
              {isCreating ? "Creating..." : "Create Task"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold">Evidence Tasks</h2>
          <p className="text-sm text-muted-foreground">
            {filteredTasks.length} of {tasks.length} tasks
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button 
            variant="outline" 
            size="sm"
            onClick={handleExportCsv}
            disabled={exporting}
          >
            {exporting ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Download className="h-4 w-4 mr-2" />
            )}
            Export CSV
          </Button>
          <Button size="sm" onClick={handleNewTask}>
            <Plus className="h-4 w-4 mr-2" />
            New Evidence Task
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search tasks..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <div className="flex gap-1">
            {["all", "overdue", "open", "finding", "evidence"].map(filter => (
              <Button
                key={filter}
                variant={activeFilter === filter ? "default" : "ghost"}
                size="sm"
                onClick={() => setActiveFilter(filter)}
                className="capitalize"
              >
                {filter}
              </Button>
            ))}
          </div>
        </div>
        <Button 
          variant="ghost" 
          size="sm" 
          onClick={fetchTasks}
          disabled={isLoading}
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
        </Button>
      </div>

      {/* Tasks Table */}
      <Card className="border-none shadow-lg overflow-hidden">
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : filteredTasks.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              <CheckSquare className="h-12 w-12 mb-4 opacity-20" />
              <p className="text-sm font-medium">No tasks found</p>
              <p className="text-xs">Try adjusting your search or filters</p>
            </div>
          ) : (
            <div className="divide-y divide-muted/50">
              {filteredTasks.map(task => (
                <div 
                  key={task.id}
                  className={`
                    grid grid-cols-7 gap-4 px-6 py-4 hover:bg-muted/30 transition-all
                    ${task.is_overdue ? 'border-l-2 border-red-500 bg-red-500/5' : ''}
                  `}
                >
                  <div className="col-span-2">
                    <p className="text-sm font-medium">{task.title}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {task.description || "No description"}
                    </p>
                  </div>
                  <div className="flex items-center">
                    <Badge variant="outline" className="text-xs">
                      {task.task_type_name}
                    </Badge>
                  </div>
                  <div className="flex items-center">
                    <Badge variant="outline" className="text-xs font-mono">
                      {task.entity_id}
                    </Badge>
                  </div>
                  <div className="flex items-center text-sm text-muted-foreground">
                    {task.assignee_name || "Unassigned"}
                  </div>
                  <div className="flex items-center text-sm">
                    {task.due_date ? (
                      <span className={task.is_overdue ? "text-red-500 font-medium" : ""}>
                        {new Date(task.due_date).toLocaleDateString()}
                      </span>
                    ) : (
                      <span className="text-muted-foreground">No due date</span>
                    )}
                  </div>
                  <div className="flex items-center justify-end gap-2">
                    {getStatusBadge(task)}
                    {getPriorityBadge(task.priority_code)}
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => handleRemind(task.id)}
                      disabled={remindingId === task.id}
                    >
                      {remindingId === task.id ? (
                        <Loader2 className="h-3 w-3 animate-spin" />
                      ) : (
                        <Clock className="h-3 w-3" />
                      )}
                    </Button>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => handleMessage(task)}
                    >
                      <MessageSquare className="h-3 w-3" />
                    </Button>
                    {task.status_code === 'resolved' && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-amber-500 hover:text-amber-600 hover:bg-amber-500/10"
                        onClick={() => handleRequestAccess(task)}
                        disabled={requestingAccessId === task.id}
                        title="Request Access to Evidence"
                      >
                        {requestingAccessId === task.id ? (
                          <Loader2 className="h-3 w-3 animate-spin" />
                        ) : (
                          <ShieldCheck className="h-3 w-3" />
                        )}
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
