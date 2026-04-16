"use client"

import * as React from "react"
import { 
  AlertCircle, 
  CheckSquare, 
  Loader2, 
  ShieldCheck 
} from "lucide-react"
import { toast } from "sonner"
import { 
  Button, 
  Badge,
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogDescription, 
  DialogFooter, 
  Label, 
  Input, 
  ScrollArea,
  cn
} from "@kcontrol/ui"

import { engagementsApi, type AuditorRequest } from "@/lib/api/engagements"
import { listAttachments } from "@/lib/api/attachments"
import type { AttachmentRecord } from "@/lib/types/attachments"

export function EngagementRequests({ engagementId }: { engagementId: string }) {
  const [requests, setRequests] = React.useState<Array<AuditorRequest>>([])
  const [loading, setLoading] = React.useState(true)
  const [fulfilling, setFulfilling] = React.useState<string | null>(null)
  
  // Fulfillment Dialog State
  const [fulfillmentRequest, setFulfillmentRequest] = React.useState<AuditorRequest | null>(null)
  const [attachments, setAttachments] = React.useState<AttachmentRecord[]>([])
  const [selectedAttachmentIds, setSelectedAttachmentIds] = React.useState<string[]>([])
  const [fulfillmentNotes, setFulfillmentNotes] = React.useState("")
  const [loadingAttachments, setLoadingAttachments] = React.useState(false)

  const fetchRequests = React.useCallback(() => {
    setLoading(true)
    engagementsApi.listRequests(engagementId, "open")
      .then(r => setRequests(r as AuditorRequest[]))
      .catch(() => setRequests([]))
      .finally(() => setLoading(false))
  }, [engagementId])

  React.useEffect(() => {
    fetchRequests()
  }, [fetchRequests])

  React.useEffect(() => {
    if (fulfillmentRequest) {
      setLoadingAttachments(true)
      const entityType = fulfillmentRequest.task_id ? "task" : (fulfillmentRequest.control_id ? "control" : "engagement")
      const entityId = fulfillmentRequest.task_id || fulfillmentRequest.control_id || engagementId
      
      listAttachments(entityType, String(entityId))
        .then(res => setAttachments(res.items))
        .catch(() => setAttachments([]))
        .finally(() => setLoadingAttachments(false))
    }
  }, [fulfillmentRequest, engagementId])

  async function handleDismiss(requestId: string) {
    setFulfilling(requestId)
    try {
      await engagementsApi.fulfillRequest(engagementId, requestId, "dismiss", "Dismissed by GRC Lead")
      setRequests(prev => prev.filter(r => r.id !== requestId))
      toast.success("Request dismissed")
    } catch (e) {
      toast.error((e as Error).message || "Failed to dismiss request")
    } finally {
      setFulfilling(null)
    }
  }

  async function handleFulfill() {
    if (!fulfillmentRequest) return
    if (selectedAttachmentIds.length === 0) {
      toast.error("Please select at least one attachment to fulfill the request")
      return
    }

    setFulfilling(fulfillmentRequest.id)
    try {
      await engagementsApi.fulfillRequest(
        engagementId, 
        fulfillmentRequest.id, 
        "fulfill", 
        fulfillmentNotes || "Evidence provided",
        selectedAttachmentIds
      )
      setRequests(prev => prev.filter(r => r.id !== fulfillmentRequest.id))
      toast.success("Access granted successfully")
      setFulfillmentRequest(null)
      setSelectedAttachmentIds([])
      setFulfillmentNotes("")
    } catch (e) {
      toast.error((e as Error).message || "Failed to fulfill request")
    } finally {
      setFulfilling(null)
    }
  }

  const toggleAttachment = (id: string) => {
    setSelectedAttachmentIds(prev => 
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    )
  }

  if (loading) return (
    <div className="flex flex-col items-center justify-center min-h-[40vh] space-y-4">
      <Loader2 className="h-10 w-10 animate-spin text-indigo-500" />
      <p className="text-[10px] font-black uppercase tracking-widest opacity-40">Polling Request Stream...</p>
    </div>
  )

  if (requests.length === 0) return (
    <div className="flex flex-col items-center justify-center min-h-[40vh] space-y-4 opacity-50 grayscale">
      <InboxIcon className="h-12 w-12 text-muted-foreground" />
      <p className="text-[10px] font-black uppercase tracking-widest opacity-40">All Requests Filled</p>
    </div>
  )

  return (
    <div className="space-y-4 max-w-4xl mx-auto py-6">
      <div className="flex items-center justify-between mb-2">
        <p className="text-[10px] font-black uppercase tracking-[0.25em] text-indigo-500 flex items-center gap-2">
          <AlertCircle className="h-3.5 w-3.5" />
          Pending Evidence Requests ({requests.length})
        </p>
      </div>
      
      <Dialog open={!!fulfillmentRequest} onOpenChange={(open) => !open && setFulfillmentRequest(null)}>
        <DialogContent className="sm:max-w-md bg-card border-none shadow-2xl rounded-2xl p-0 overflow-hidden">
          <DialogHeader className="p-6 bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border-b border-muted/10">
            <DialogTitle className="text-xl font-black uppercase tracking-tight">Fulfill Request</DialogTitle>
            <DialogDescription className="text-[10px] font-bold uppercase tracking-widest opacity-60">
              Grant Access To Controlled Intelligence
            </DialogDescription>
          </DialogHeader>
          
          <div className="p-6 space-y-5">
            <div className="space-y-2">
              <Label className="text-[10px] font-black uppercase tracking-widest opacity-40">Auditor Requirement</Label>
              <div className="p-4 bg-muted/20 border border-muted/20 rounded-xl text-[11px] leading-relaxed font-medium italic">
                "{fulfillmentRequest?.request_description}"
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label className="text-[10px] font-black uppercase tracking-widest opacity-40">Evidence Library Access</Label>
                <Badge variant="outline" className="text-[8px] h-4 font-black tracking-widest border-muted/30">{attachments.length} ASSETS</Badge>
              </div>
              <ScrollArea className="h-48 rounded-xl border border-muted/20 bg-background/50 p-2">
                {loadingAttachments ? (
                  <div className="flex items-center justify-center h-full text-[10px] font-black uppercase tracking-widest text-muted-foreground/30 italic">
                    <Loader2 className="w-5 h-5 animate-spin mr-2" />
                    Syncing repository...
                  </div>
                ) : attachments.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full text-center px-4 space-y-2">
                    <AlertCircle className="h-6 w-6 text-amber-500/30" />
                    <p className="text-[10px] font-black uppercase tracking-widest text-amber-500/60">No context found</p>
                    <p className="text-[10px] text-muted-foreground leading-tight italic">Please upload evidence to this control or task before fulfilling the request.</p>
                  </div>
                ) : (
                  <div className="space-y-1">
                    {attachments.map(att => (
                      <div 
                        key={att.id}
                        onClick={() => toggleAttachment(att.id)}
                        className={cn(
                          "flex items-center gap-3 p-3 rounded-xl hover:bg-indigo-500/5 cursor-pointer transition-all border border-transparent",
                          selectedAttachmentIds.includes(att.id) ? "bg-indigo-500/10 border-indigo-500/20" : ""
                        )}
                      >
                        <div className={cn(
                          "w-4 h-4 rounded border flex items-center justify-center transition-all",
                          selectedAttachmentIds.includes(att.id) ? "bg-indigo-500 border-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.5)]" : "border-muted-foreground/20"
                        )}>
                          {selectedAttachmentIds.includes(att.id) && <CheckSquare className="w-3 h-3 text-white" />}
                        </div>
                        <span className="text-[10px] font-black uppercase tracking-tighter truncate opacity-70 group-hover:opacity-100 transition-opacity">{att.original_filename}</span>
                      </div>
                    ))}
                  </div>
                )}
              </ScrollArea>
            </div>

            <div className="space-y-2">
              <Label className="text-[10px] font-black uppercase tracking-widest opacity-40">Transmission Memo (Optional)</Label>
              <Input 
                placeholder="Add clarity for the auditor..."
                className="h-10 border-muted/20 bg-background/50 rounded-lg text-xs"
                value={fulfillmentNotes}
                onChange={(e) => setFulfillmentNotes(e.target.value)}
              />
            </div>
          </div>

          <DialogFooter className="p-6 bg-muted/5 border-t border-muted/10 gap-3">
            <Button variant="ghost" className="h-10 px-6 font-black text-[10px] uppercase tracking-widest" onClick={() => setFulfillmentRequest(null)}>Abort</Button>
            <Button 
              className="h-10 px-8 bg-indigo-600 hover:bg-indigo-700 text-white font-black text-[10px] uppercase tracking-[0.2em] rounded-xl shadow-lg shadow-indigo-500/20"
              onClick={handleFulfill}
              disabled={selectedAttachmentIds.length === 0 || fulfilling === fulfillmentRequest?.id}
            >
              {fulfilling === fulfillmentRequest?.id ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <ShieldCheck className="h-4 w-4 mr-2" />}
              Dispatch Intel
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <div className="grid gap-3">
        {requests.map(req => (
          <div key={req.id} className="rounded-2xl border border-indigo-500/20 bg-card/40 backdrop-blur-sm p-5 space-y-4 hover:shadow-md transition-all group">
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-xl bg-indigo-500/10 flex items-center justify-center">
                  <InboxIcon className="h-5 w-5 text-indigo-500" />
                </div>
                <div>
                  <span className="text-[10px] text-indigo-500 font-black uppercase tracking-[0.2em]">{String(req.auditor_email ?? "")}</span>
                  <div className="flex items-center gap-2 mt-0.5">
                    <Badge variant="outline" className="h-4 text-[8px] font-black tracking-widest border-muted/30">
                      {req.task_id ? "TASK_REQ" : (req.control_id ? "CONTROL_REQ" : "GENERAL_REQ")}
                    </Badge>
                    <span className="text-[10px] font-bold text-muted-foreground opacity-30 tabular-nums">{req.created_at ? new Date(String(req.created_at)).toLocaleDateString() : ""}</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 text-[9px] font-black uppercase tracking-widest px-3 border border-transparent hover:border-destructive/20 hover:text-destructive"
                  onClick={() => handleDismiss(req.id)}
                  disabled={fulfilling === req.id}
                >
                  Dismiss
                </Button>
                <Button
                  size="sm"
                  className="h-8 text-[9px] font-black uppercase tracking-[0.2em] px-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg shadow-sm"
                  onClick={() => {
                    setFulfillmentRequest(req)
                    setSelectedAttachmentIds([])
                    setFulfillmentNotes("")
                  }}
                  disabled={fulfilling === req.id}
                >
                  {fulfilling === req.id ? "Processing..." : "Approve & Grant"}
                </Button>
              </div>
            </div>
            <div className="relative">
              <div className="absolute left-0 top-0 bottom-0 w-[2px] bg-indigo-500/20 rounded-full" />
              <p className="text-xs text-foreground font-medium leading-relaxed pl-5 py-0.5">{String(req.request_description ?? "No description provided")}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function InboxIcon({ className }: { className?: string }) {
  return (
    <svg 
      xmlns="http://www.w3.org/2000/svg" 
      width="24" 
      height="24" 
      viewBox="0 0 24 24" 
      fill="none" 
      stroke="currentColor" 
      strokeWidth="2" 
      strokeLinecap="round" 
      strokeLinejoin="round" 
      className={className}
    >
      <polyline points="22 12 16 12 14 15 10 15 8 12 2 12" />
      <path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" />
    </svg>
  )
}
