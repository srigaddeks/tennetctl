"use client"

import { useState } from "react"
import {
  Button,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  Label,
  Separator,
  Badge,
} from "@kcontrol/ui"
import {
  FileText,
  RefreshCw,
  Send,
} from "lucide-react"
import { engagementsApi, type EngagementControl } from "@/lib/api/engagements"
import { toast } from "sonner"

interface RequestEvidenceDialogProps {
  engagementId: string
  control: EngagementControl
  onClose: () => void
  onRequested: () => void
}

export function RequestEvidenceDialog({
  engagementId,
  control,
  onClose,
  onRequested,
}: RequestEvidenceDialogProps) {
  const [description, setDescription] = useState("")
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit() {
    if (!description.trim()) return
    setSubmitting(true)
    try {
      await engagementsApi.requestDocs(engagementId, control.id, {
        description: description.trim(),
      })
      toast.success(`Evidence request sent for ${control.control_code}`)
      onRequested()
      onClose()
    } catch (e) {
      toast.error((e as Error).message || "Failed to request evidence")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open onOpenChange={(o) => { if (!o) onClose() }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-blue-500/10 p-2.5">
              <FileText className="h-4 w-4 text-blue-500" />
            </div>
            <div>
              <DialogTitle>Request Evidence</DialogTitle>
              <p className="text-xs text-muted-foreground mt-0.5">
                <span className="font-mono">{control.control_code}</span> — {control.name}
              </p>
            </div>
          </div>
        </DialogHeader>

        <Separator className="my-2" />

        <div className="rounded-lg border border-border bg-muted/20 p-3">
          <div className="flex items-center gap-2 text-xs">
            <Badge variant="outline" className="text-[10px]">{control.category_name}</Badge>
            <Badge variant="outline" className="text-[10px]">{control.criticality_name}</Badge>
          </div>
        </div>

        <div className="space-y-1.5">
          <Label className="text-xs font-semibold">What evidence do you need?</Label>
          <textarea
            className="w-full h-28 rounded-lg border border-border bg-background px-3 py-2 text-sm resize-none focus:outline-none focus:ring-1 focus:ring-ring"
            placeholder="Describe the specific evidence, documents, or screenshots needed to verify this control. Be specific about format, time period, and level of detail required."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            autoFocus
          />
          <p className="text-[10px] text-muted-foreground">
            This request will be sent to the GRC team for fulfillment.
          </p>
        </div>

        <DialogFooter className="mt-3 gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={submitting}>
            Cancel
          </Button>
          <Button size="sm" onClick={handleSubmit} disabled={!description.trim() || submitting}>
            {submitting ? (
              <span className="flex items-center gap-1.5">
                <RefreshCw className="h-3 w-3 animate-spin" />
                Sending...
              </span>
            ) : (
              <span className="flex items-center gap-1.5">
                <Send className="h-3 w-3" />
                Send Request
              </span>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
