"use client"

import * as React from "react"
import { 
  FileText,
  Search,
  Filter,
  Download,
  Plus,
  Clock,
  MessageSquare,
  CheckCircle2,
  ShieldOff,
  Loader2,
  RefreshCw,
  HelpCircle,
  Send,
  ClipboardList,
  CheckSquare,
} from "lucide-react"
import { SearchableControlSelector } from "./SearchableControlSelector"

import { 
  Button, 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle,
  Badge,
  Input,
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  Label,
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@kcontrol/ui"
import { toast } from "sonner"

import { AuditorRequest, engagementsApi, type EngagementControl } from "@/lib/api/engagements"

interface EvidenceRequestsTabProps {
  engagementId: string
  onRequestCreated?: () => void
  onMessageLink?: (entity: { type: string; id: string; title?: string }) => void
}

export function EvidenceRequestsTab({ 
  engagementId,
  onRequestCreated,
  onMessageLink
}: EvidenceRequestsTabProps) {
  const [requests, setRequests] = React.useState<AuditorRequest[]>([])
  const [isLoading, setIsLoading] = React.useState(true)
  const [searchQuery, setSearchQuery] = React.useState("")
  const [activeFilter, setActiveFilter] = React.useState("all")
  const [remindingId, setRemindingId] = React.useState<string | null>(null)
  const [exporting, setExporting] = React.useState(false)
  const [revokingId, setRevokingId] = React.useState<string | null>(null)
  const [controls, setControls] = React.useState<EngagementControl[]>([])
  const [isRequestDialogOpen, setIsRequestDialogOpen] = React.useState(false)
  const [requestType, setRequestType] = React.useState<"control" | "task">("control")
  const [tasks, setTasks] = React.useState<any[]>([])
  const [selectedControlId, setSelectedControlId] = React.useState("")
  const [selectedTaskId, setSelectedTaskId] = React.useState("")
  const [requestDescription, setRequestDescription] = React.useState("")
  const [isSubmittingRequest, setIsSubmittingRequest] = React.useState(false)

  // Fetch requests
  const fetchRequests = React.useCallback(async () => {
    if (!engagementId) return
    
    setIsLoading(true)
    try {
      const data = await engagementsApi.listRequests(engagementId)
      setRequests(data)
    } catch (error) {
      console.error("Failed to fetch evidence requests:", error)
    } finally {
      setIsLoading(false)
    }
  }, [engagementId])

  React.useEffect(() => {
    fetchRequests()
  }, [fetchRequests])

  React.useEffect(() => {
    if (!engagementId) return

    engagementsApi.listEngagementControls(engagementId)
      .then(setControls)
      .catch((error) => {
        console.error("Failed to fetch controls for evidence requests:", error)
      })

    engagementsApi.listEngagementTasks(engagementId)
      .then(res => setTasks(res.items))
      .catch((error) => {
        console.error("Failed to fetch tasks for evidence requests:", error)
      })
  }, [engagementId])

  // Real-time polling every 30 seconds
  React.useEffect(() => {
    const interval = setInterval(() => {
      fetchRequests()
    }, 30000)
    return () => clearInterval(interval)
  }, [fetchRequests])

  // Filter requests
  const filteredRequests = React.useMemo(() => {
    let filtered = requests

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(req => 
        req.request_description?.toLowerCase().includes(query) ||
        req.control_id?.toLowerCase().includes(query) ||
        req.task_id?.toLowerCase().includes(query)
      )
    }

    // Apply status filter
    if (activeFilter !== "all") {
      filtered = filtered.filter(req => {
        if (activeFilter === "pending") {
          return req.request_status === "open"
        }
        if (activeFilter === "fulfilled") {
          return req.request_status === "fulfilled"
        }
        return true
      })
    }

    return filtered
  }, [requests, searchQuery, activeFilter])

  // Handle remind
  const handleRemind = async (requestId: string) => {
    setRemindingId(requestId)
    try {
      // API call to remind
      await new Promise(resolve => setTimeout(resolve, 1000)) // Simulated API call
      toast.success("Reminder sent to client")
      fetchRequests()
    } catch (error) {
      console.error("Failed to send reminder:", error)
      toast.error("Failed to send reminder")
    } finally {
      setRemindingId(null)
    }
  }

  // Handle message
  const handleMessage = (request: AuditorRequest) => {
    if (onMessageLink) {
      onMessageLink({
        type: 'evidence_request',
        id: request.id,
        title: request.request_description || `Request ${request.id}`
      })
    }
  }

  // Handle export ZIP
  const handleExportZip = async () => {
    setExporting(true)
    try {
      // Simulated export
      await new Promise(resolve => setTimeout(resolve, 2000))
      toast.success("Evidence exported successfully")
    } catch (error) {
      console.error("Failed to export:", error)
      toast.error("Failed to export evidence")
    } finally {
      setExporting(false)
    }
  }

  // Handle new request
  const handleNewRequest = () => {
    setSelectedControlId("")
    setSelectedTaskId("")
    setRequestDescription("")
    setIsRequestDialogOpen(true)
  }

  const handleSubmitRequest = async () => {
    const isControl = requestType === "control"
    const targetId = isControl ? selectedControlId : selectedTaskId

    if (!targetId || !requestDescription.trim()) {
      toast.error(`${isControl ? "Control" : "Task"} and request description are required`)
      return
    }

    setIsSubmittingRequest(true)
    try {
      if (isControl) {
        await engagementsApi.requestDocs(engagementId, selectedControlId, {
          description: requestDescription.trim(),
        })
      } else {
        await engagementsApi.requestTaskAccess(engagementId, selectedTaskId, {
          description: requestDescription.trim(),
        })
      }
      toast.success("Evidence request created")
      setIsRequestDialogOpen(false)
      setRequestDescription("")
      setSelectedControlId("")
      setSelectedTaskId("")
      await fetchRequests()
      onRequestCreated?.()
    } catch (error) {
      console.error("Failed to create evidence request:", error)
      toast.error((error as Error).message || "Failed to create evidence request")
    } finally {
      setIsSubmittingRequest(false)
    }
  }

  const handleRevokeAccess = async (requestId: string) => {
    setRevokingId(requestId)
    try {
      await engagementsApi.revokeRequestAccess(engagementId, requestId)
      toast.success("Evidence access revoked")
      await fetchRequests()
    } catch (error) {
      console.error("Failed to revoke evidence access:", error)
      toast.error((error as Error).message || "Failed to revoke evidence access")
    } finally {
      setRevokingId(null)
    }
  }

  // Get status badge
  const getStatusBadge = (request: AuditorRequest) => {
    if (request.request_status === "fulfilled") {
      return <Badge variant="default" className="bg-green-500/20 text-green-400"><CheckCircle2 className="h-3 w-3 mr-1" />Fulfilled</Badge>
    }
    if (request.request_status === "open") {
      return <Badge variant="secondary"><Clock className="h-3 w-3 mr-1" />Pending</Badge>
    }
    return <Badge variant="outline">{request.request_status}</Badge>
  }

  const selectedControl = React.useMemo(
    () => controls.find((control) => control.id === selectedControlId) ?? null,
    [controls, selectedControlId],
  )

  return (
    <TooltipProvider delayDuration={0}>
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold">Evidence Requests</h2>
            <Tooltip>
              <TooltipTrigger asChild>
                <button className="inline-flex items-center justify-center rounded-full text-muted-foreground/50 transition-colors hover:text-primary">
                  <HelpCircle className="h-4 w-4" />
                </button>
              </TooltipTrigger>
              <TooltipContent side="top" className="max-w-[240px] text-[11px] leading-relaxed">
                Create, track, remind, and revoke engagement evidence requests sent to the client or GRC team.
              </TooltipContent>
            </Tooltip>
          </div>
          <p className="text-sm text-muted-foreground">
            {filteredRequests.length} of {requests.length} requests
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button 
                variant="outline" 
                size="sm"
                onClick={handleExportZip}
                disabled={exporting}
              >
                {exporting ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Download className="h-4 w-4 mr-2" />
                )}
                Export ZIP
              </Button>
            </TooltipTrigger>
            <TooltipContent side="top">Export the evidence request register for this engagement.</TooltipContent>
          </Tooltip>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button size="sm" onClick={handleNewRequest}>
                <Plus className="h-4 w-4 mr-2" />
                New Request
              </Button>
            </TooltipTrigger>
            <TooltipContent side="top">Create a new evidence request for a specific control or task.</TooltipContent>
          </Tooltip>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search evidence requests..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <div className="flex items-center gap-2">
          <Tooltip>
            <TooltipTrigger asChild>
              <span className="inline-flex">
                <Filter className="h-4 w-4 text-muted-foreground" />
              </span>
            </TooltipTrigger>
            <TooltipContent side="top">Filter requests by status.</TooltipContent>
          </Tooltip>
          <div className="flex gap-1">
            {["all", "pending", "fulfilled"].map(filter => (
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
        <Tooltip>
          <TooltipTrigger asChild>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={fetchRequests}
              disabled={isLoading}
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="top">Refresh the latest evidence request status.</TooltipContent>
        </Tooltip>
      </div>

      {/* Requests Table */}
      <Card className="border-none shadow-lg overflow-hidden">
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : filteredRequests.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              <FileText className="h-12 w-12 mb-4 opacity-20" />
              <p className="text-sm font-medium">No evidence requests found</p>
              <p className="text-xs">Try adjusting your search or filters</p>
            </div>
          ) : (
            <div className="divide-y divide-muted/50">
              {filteredRequests.map(request => (
                <div
                  key={request.id}
                  className="grid grid-cols-6 gap-4 px-6 py-4 hover:bg-muted/30 transition-all"
                >
                  <div className="col-span-2">
                    <p className="text-sm font-medium">{request.request_description || "Evidence Request"}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Requested {new Date(request.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex flex-col justify-center">
                    <Badge variant="outline" className="text-[10px] font-mono w-fit">
                      {request.control_id ? `CTRL: ${request.control_id}` : (request.task_id ? `TASK: ${request.task_id}` : "N/A")}
                    </Badge>
                    {request.task_id && (
                      <span className="text-[10px] text-muted-foreground mt-1 flex items-center gap-1">
                        <CheckSquare className="h-2.5 w-2.5" />
                        Task Request
                      </span>
                    )}
                  </div>
                  <div className="flex items-center text-sm text-muted-foreground">
                    {request.auditor_email || "Unassigned"}
                  </div>
                  <div className="flex items-center text-sm text-muted-foreground">
                    {new Date(request.created_at).toLocaleDateString()}
                  </div>
                  <div className="flex items-center justify-end gap-2">
                    {getStatusBadge(request)}
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => handleRemind(request.id)}
                          disabled={remindingId === request.id}
                        >
                          {remindingId === request.id ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          ) : (
                            <Clock className="h-3 w-3" />
                          )}
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent side="top">Send a reminder for this open evidence request.</TooltipContent>
                    </Tooltip>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => handleMessage(request)}
                        >
                          <MessageSquare className="h-3 w-3" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent side="top">Open messages linked to this evidence request.</TooltipContent>
                    </Tooltip>
                    {request.request_status === "fulfilled" ? (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRevokeAccess(request.id)}
                            disabled={revokingId === request.id}
                          >
                            {revokingId === request.id ? (
                              <Loader2 className="h-3 w-3 animate-spin" />
                            ) : (
                              <ShieldOff className="h-3 w-3" />
                            )}
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent side="top">Revoke previously approved evidence access.</TooltipContent>
                      </Tooltip>
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={isRequestDialogOpen} onOpenChange={setIsRequestDialogOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Plus className="h-4 w-4 text-primary" />
              New Evidence Request
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label className="text-xs font-semibold">Request Context</Label>
              <div className="flex p-1 bg-muted rounded-xl mb-2 text-[10px] font-black uppercase tracking-widest border border-muted/20">
                <button
                  className={`flex-1 py-2 rounded-lg transition-all ${requestType === "control" ? "bg-background shadow-sm text-primary" : "text-muted-foreground hover:text-foreground"}`}
                  onClick={() => setRequestType("control")}
                >
                  Control-Based
                </button>
                <button
                  className={`flex-1 py-2 rounded-lg transition-all ${requestType === "task" ? "bg-background shadow-sm text-primary" : "text-muted-foreground hover:text-foreground"}`}
                  onClick={() => setRequestType("task")}
                >
                  Task-Based
                </button>
              </div>
            </div>

            {requestType === "control" ? (
              <>
                <SearchableControlSelector
                  label="Control"
                  controls={controls}
                  value={selectedControlId}
                  onChange={setSelectedControlId}
                />

                {selectedControl ? (
                  <div className="rounded-2xl border border-border/60 bg-muted/20 p-4">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant="outline" className="text-[10px] font-bold">{selectedControl.category_name}</Badge>
                      <Badge variant="outline" className="text-[10px] font-bold">{selectedControl.criticality_name}</Badge>
                    </div>
                    <p className="mt-2 text-sm font-semibold">{selectedControl.name}</p>
                    {selectedControl.description ? (
                      <p className="mt-1 text-xs text-muted-foreground">{selectedControl.description}</p>
                    ) : null}
                  </div>
                ) : null}
              </>
            ) : (
              <div className="space-y-2">
                <Label className="text-xs font-semibold">Evidence Task</Label>
                <select
                  value={selectedTaskId}
                  onChange={(e) => setSelectedTaskId(e.target.value)}
                  className="w-full flex h-10 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <option value="">Select an evidence task...</option>
                  {tasks.map((task) => (
                    <option key={task.id} value={task.id}>
                      {task.title} ({task.status_name})
                    </option>
                  ))}
                </select>
                {tasks.length === 0 && (
                  <p className="text-[10px] text-amber-500 italic mt-1 px-1">
                    No tasks found. Tasks must be created before requesting evidence for them.
                  </p>
                )}
              </div>
            )}

            <div className="space-y-2">
              <Label className="text-xs font-semibold">Request Details</Label>
              <textarea
                value={requestDescription}
                onChange={(event) => setRequestDescription(event.target.value)}
                placeholder="Describe exactly what evidence is needed, the period it should cover, and any preferred format."
                className="h-32 w-full rounded-2xl border border-border/60 bg-background px-4 py-3 text-sm outline-none transition focus:border-primary/40"
              />
            </div>
          </div>

          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setIsRequestDialogOpen(false)} disabled={isSubmittingRequest}>
              Cancel
            </Button>
            <Button onClick={handleSubmitRequest} disabled={!(requestType === "control" ? selectedControlId : selectedTaskId) || !requestDescription.trim() || isSubmittingRequest}>
              {isSubmittingRequest ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Sending
                </>
              ) : (
                <>
                  <Send className="mr-2 h-4 w-4" />
                  Send Request
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
    </TooltipProvider>
  )
}
