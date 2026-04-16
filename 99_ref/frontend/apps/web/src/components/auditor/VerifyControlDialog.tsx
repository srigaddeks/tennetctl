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
  CheckCircle2,
  AlertTriangle,
  XCircle,
  RefreshCw,
  Shield,
  FileText,
} from "lucide-react"
import { engagementsApi, type EngagementControl } from "@/lib/api/engagements"
import { toast } from "sonner"

interface VerifyControlDialogProps {
  engagementId: string
  control: EngagementControl
  onClose: () => void
  onVerified: () => void
}

const OUTCOMES = [
  {
    value: "verified",
    label: "Verified",
    description: "Control is operating effectively",
    icon: CheckCircle2,
    color: "bg-green-500/10 border-green-500/30 text-green-700 hover:bg-green-500/20",
    activeColor: "bg-green-500 border-green-500 text-white",
  },
  {
    value: "qualified",
    label: "Qualified",
    description: "Control exists but has gaps",
    icon: AlertTriangle,
    color: "bg-amber-500/10 border-amber-500/30 text-amber-700 hover:bg-amber-500/20",
    activeColor: "bg-amber-500 border-amber-500 text-white",
  },
  {
    value: "failed",
    label: "Failed",
    description: "Control is not operating effectively",
    icon: XCircle,
    color: "bg-red-500/10 border-red-500/30 text-red-700 hover:bg-red-500/20",
    activeColor: "bg-red-500 border-red-500 text-white",
  },
] as const

export function VerifyControlDialog({
  engagementId,
  control,
  onClose,
  onVerified,
}: VerifyControlDialogProps) {
  const [outcome, setOutcome] = useState<string>("")
  const [observations, setObservations] = useState("")
  const [findingDetails, setFindingDetails] = useState("")
  const [submitting, setSubmitting] = useState(false)

  const needsFindings = outcome === "qualified" || outcome === "failed"

  async function handleSubmit() {
    if (!outcome) return
    setSubmitting(true)
    try {
      await engagementsApi.verifyControl(engagementId, control.id, {
        outcome,
        observations: observations.trim() || undefined,
        finding_details: needsFindings ? findingDetails.trim() || undefined : undefined,
      })
      toast.success(`Control ${control.control_code} verified as ${outcome}`)
      onVerified()
      onClose()
    } catch (e) {
      toast.error((e as Error).message || "Failed to verify control")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open onOpenChange={(o) => { if (!o) onClose() }}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-primary/10 p-2.5">
              <Shield className="h-4 w-4 text-primary" />
            </div>
            <div>
              <DialogTitle>Verify Control</DialogTitle>
              <p className="text-xs text-muted-foreground mt-0.5">
                <span className="font-mono">{control.control_code}</span> — {control.name}
              </p>
            </div>
          </div>
        </DialogHeader>

        <Separator className="my-2" />

        {/* Control info */}
        <div className="rounded-lg border border-border bg-muted/20 p-3 space-y-1.5">
          <div className="flex items-center gap-2 text-xs">
            <Badge variant="outline" className="text-[10px]">{control.category_name}</Badge>
            <Badge variant="outline" className="text-[10px]">{control.criticality_name}</Badge>
            <span className="text-muted-foreground">{control.evidence_count} evidence items</span>
          </div>
          {control.description && (
            <p className="text-xs text-muted-foreground line-clamp-2">{control.description}</p>
          )}
        </div>

        {/* Outcome selection */}
        <div className="space-y-2">
          <Label className="text-xs font-semibold">Verification Outcome</Label>
          <div className="grid grid-cols-3 gap-2">
            {OUTCOMES.map((o) => {
              const Icon = o.icon
              const isActive = outcome === o.value
              return (
                <button
                  key={o.value}
                  type="button"
                  onClick={() => setOutcome(o.value)}
                  className={`flex flex-col items-center gap-1.5 rounded-xl border-2 p-3 transition-all ${
                    isActive ? o.activeColor : o.color
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  <span className="text-xs font-bold">{o.label}</span>
                  <span className={`text-[10px] ${isActive ? "text-white/80" : "text-muted-foreground"}`}>
                    {o.description}
                  </span>
                </button>
              )
            })}
          </div>
        </div>

        {/* Observations */}
        <div className="space-y-1.5">
          <Label className="text-xs font-semibold">Observations</Label>
          <textarea
            className="w-full h-20 rounded-lg border border-border bg-background px-3 py-2 text-sm resize-none focus:outline-none focus:ring-1 focus:ring-ring"
            placeholder="Notes on the control's effectiveness, evidence reviewed, etc."
            value={observations}
            onChange={(e) => setObservations(e.target.value)}
          />
        </div>

        {/* Finding details (shown for qualified/failed) */}
        {needsFindings && (
          <div className="space-y-1.5">
            <Label className="text-xs font-semibold text-red-600">
              <FileText className="h-3 w-3 inline mr-1" />
              Finding Details
            </Label>
            <textarea
              className="w-full h-24 rounded-lg border border-red-500/30 bg-red-500/5 px-3 py-2 text-sm resize-none focus:outline-none focus:ring-1 focus:ring-red-500"
              placeholder="Describe the finding: what is the gap, root cause, and recommended remediation..."
              value={findingDetails}
              onChange={(e) => setFindingDetails(e.target.value)}
            />
          </div>
        )}

        <DialogFooter className="mt-3 gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={submitting}>
            Cancel
          </Button>
          <Button size="sm" onClick={handleSubmit} disabled={!outcome || submitting}>
            {submitting ? (
              <span className="flex items-center gap-1.5">
                <RefreshCw className="h-3 w-3 animate-spin" />
                Submitting...
              </span>
            ) : (
              "Submit Verification"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
