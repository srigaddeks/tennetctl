"use client"

import { useEffect, useState, useCallback, useMemo } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Button,
  Input,
  Checkbox,
  Separator,
  Badge,
} from "@kcontrol/ui"
import {
  Search,
  FileText,
  ShieldCheck,
  CheckSquare,
  Square,
  Loader2,
  ChevronDown,
  ChevronRight,
  AlertCircle,
} from "lucide-react"
import { submitFrameworkSelective, listRequirements, listControls } from "@/lib/api/grc"
import type { RequirementResponse, ControlResponse } from "@/lib/types/grc"

interface SubmitForReviewModalProps {
  open: boolean
  framework: { id: string; name: string; framework_code: string } | null
  onClose: () => void
  onSuccess: () => void
}

interface RequirementWithControls extends RequirementResponse {
  controls: ControlResponse[]
}

export function SubmitForReviewModal({
  open,
  framework,
  onClose,
  onSuccess,
}: SubmitForReviewModalProps) {
  const [requirements, setRequirements] = useState<RequirementResponse[]>([])
  const [controls, setControls] = useState<ControlResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notes, setNotes] = useState("")

  const [selectedRequirements, setSelectedRequirements] = useState<Set<string>>(new Set())
  const [selectedControls, setSelectedControls] = useState<Set<string>>(new Set())

  const [search, setSearch] = useState("")
  const [expandedRequirements, setExpandedRequirements] = useState<Set<string>>(new Set())

  const loadData = useCallback(async () => {
    if (!framework) return
    setLoading(true)
    setError(null)
    setRequirements([])
    setControls([])
    try {
      const [reqRes, ctrlRes] = await Promise.all([
        listRequirements(framework.id),
        listControls(framework.id),
      ])
      setRequirements(reqRes.items ?? [])
      setControls(ctrlRes.items ?? [])
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load data")
    } finally {
      setLoading(false)
    }
  }, [framework])

  useEffect(() => {
    if (open && framework) {
      loadData()
      setNotes("")
    }
  }, [open, framework, loadData])

  // Initialize selections when data loads (after loading completes)
  useEffect(() => {
    if (!loading && (requirements.length > 0 || controls.length > 0)) {
      setSelectedRequirements(new Set(requirements.map((r) => r.id)))
      setSelectedControls(new Set(controls.map((c) => c.id)))
    }
  }, [loading, requirements, controls])

  const requirementsWithControls = useMemo((): RequirementWithControls[] => {
    return requirements.map((req) => ({
      ...req,
      controls: controls.filter((ctrl) => ctrl.requirement_id === req.id),
    }))
  }, [requirements, controls])

  const unassignedControls = useMemo(() => {
    return controls.filter((ctrl) => !ctrl.requirement_id || !requirements.find((r) => r.id === ctrl.requirement_id))
  }, [controls, requirements])

  const filteredData = useMemo(() => {
    const searchLower = search.toLowerCase()
    
    const filteredReqs = requirementsWithControls.filter(
      (req) =>
        (req.requirement_code || "").toLowerCase().includes(searchLower) ||
        (req.name ?? "").toLowerCase().includes(searchLower) ||
        req.controls.some(
          (c) =>
            (c.control_code || "").toLowerCase().includes(searchLower) ||
            (c.name ?? "").toLowerCase().includes(searchLower)
        )
    )

    const filteredUnassigned = unassignedControls.filter(
      (c) =>
        (c.control_code || "").toLowerCase().includes(searchLower) ||
        (c.name ?? "").toLowerCase().includes(searchLower)
    )

    return { filteredReqs, filteredUnassigned }
  }, [requirementsWithControls, unassignedControls, search])

  const toggleRequirement = (id: string) => {
    const newSet = new Set(selectedRequirements)
    const requirement = requirements.find((r) => r.id === id)
    const requirementControls = controls.filter((c) => c.requirement_id === id)
    
    if (newSet.has(id)) {
      // Deselecting requirement - also deselect all its controls
      newSet.delete(id)
      setSelectedRequirements(newSet)
      const newControlsSet = new Set(selectedControls)
      requirementControls.forEach((c) => newControlsSet.delete(c.id))
      setSelectedControls(newControlsSet)
    } else {
      // Selecting requirement - also select all its controls
      newSet.add(id)
      setSelectedRequirements(newSet)
      const newControlsSet = new Set(selectedControls)
      requirementControls.forEach((c) => newControlsSet.add(c.id))
      setSelectedControls(newControlsSet)
    }
  }

  const toggleControl = (id: string) => {
    const newSet = new Set(selectedControls)
    const control = controls.find((c) => c.id === id)
    
    if (newSet.has(id)) {
      // Deselecting control
      newSet.delete(id)
      setSelectedControls(newSet)
      // If control has a requirement, check if any controls in that requirement are still selected
      // If none are selected, deselect the requirement too
      if (control?.requirement_id) {
        const remainingControlsInReq = controls.filter(
          (c) => c.requirement_id === control.requirement_id && c.id !== id && newSet.has(c.id)
        )
        if (remainingControlsInReq.length === 0) {
          const newReqSet = new Set(selectedRequirements)
          newReqSet.delete(control.requirement_id)
          setSelectedRequirements(newReqSet)
        }
      }
    } else {
      // Selecting control - also select its parent requirement if exists
      newSet.add(id)
      setSelectedControls(newSet)
      if (control?.requirement_id) {
        const newReqSet = new Set(selectedRequirements)
        newReqSet.add(control.requirement_id)
        setSelectedRequirements(newReqSet)
      }
    }
  }

  const toggleRequirementExpanded = (id: string) => {
    const newSet = new Set(expandedRequirements)
    if (newSet.has(id)) newSet.delete(id)
    else newSet.add(id)
    setExpandedRequirements(newSet)
  }

  const selectAll = () => {
    setSelectedRequirements(new Set(requirements.map((r) => r.id)))
    setSelectedControls(new Set(controls.map((c) => c.id)))
  }

  const deselectAll = () => {
    setSelectedRequirements(new Set())
    setSelectedControls(new Set())
  }

  async function handleSubmit() {
    if (!framework) return
    if (selectedRequirements.size === 0 && selectedControls.size === 0) {
      setError("Please select at least one requirement or control to submit for review")
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      await submitFrameworkSelective(framework.id, {
        requirement_ids: Array.from(selectedRequirements),
        control_ids: Array.from(selectedControls),
        notes: notes || undefined,
      })
      onSuccess()
      onClose()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to submit for review")
    } finally {
      setSubmitting(false)
    }
  }

  if (!framework) return null

  const reqSelectedCount = selectedRequirements.size
  const ctrlSelectedCount = selectedControls.size
  const totalSelected = reqSelectedCount + ctrlSelectedCount
  const totalItems = requirements.length + controls.length

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose() }}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-amber-500/10 p-2.5">
              <CheckSquare className="h-5 w-5 text-amber-500" />
            </div>
            <div>
              <DialogTitle>Submit for Review</DialogTitle>
              <DialogDescription>
                Select requirements and controls to submit for review for {framework.name}
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-12 gap-2">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            <span className="text-sm text-muted-foreground">Loading requirements and controls...</span>
          </div>
        ) : (
          <>
            <div className="flex-1 overflow-y-auto space-y-4">
              {error && (
                <div className="flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-500">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  {error}
                </div>
              )}

              <div className="flex items-center justify-between gap-4">
                <div className="text-sm text-muted-foreground">
                  {totalSelected} of {totalItems} items selected
                </div>
                <div className="relative">
                  <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
                  <Input
                    placeholder="Search..."
                    className="h-8 pl-8 text-xs w-56"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                  />
                </div>
              </div>

              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={selectAll}>
                  Select All
                </Button>
                <Button variant="outline" size="sm" onClick={deselectAll}>
                  Deselect All
                </Button>
              </div>

              <Separator />

              <div className="space-y-2">
                {filteredData.filteredReqs.length === 0 && filteredData.filteredUnassigned.length === 0 ? (
                  <div className="py-8 text-center text-sm text-muted-foreground">
                    No requirements or controls found
                  </div>
                ) : (
                  <>
                    {filteredData.filteredReqs.map((req) => {
                      const isExpanded = expandedRequirements.has(req.id)
                      const reqSelected = selectedRequirements.has(req.id)
                      const someControlsSelected = req.controls.some((c) => selectedControls.has(c.id))
                      const allControlsSelected = req.controls.length > 0 && req.controls.every((c) => selectedControls.has(c.id))

                      return (
                        <div key={req.id} className="border rounded-lg overflow-hidden">
                          <div className="flex items-center gap-2 px-3 py-2.5 bg-muted/30 hover:bg-muted/50">
                            <button
                              type="button"
                              onClick={() => toggleRequirementExpanded(req.id)}
                              className="text-muted-foreground hover:text-foreground"
                            >
                              {isExpanded ? (
                                <ChevronDown className="h-4 w-4" />
                              ) : (
                                <ChevronRight className="h-4 w-4" />
                              )}
                            </button>
                            <Checkbox
                              checked={reqSelected}
                              onCheckedChange={() => toggleRequirement(req.id)}
                            />
                            <FileText className="h-4 w-4 text-blue-500 shrink-0" />
                            <span className="font-mono text-xs font-medium">{req.requirement_code}</span>
                            <span className="text-sm truncate flex-1">{req.name}</span>
                            <Badge variant="outline" className="text-[10px] shrink-0">
                              {req.controls.length} controls
                            </Badge>
                          </div>

                          {isExpanded && req.controls.length > 0 && (
                            <div className="bg-background divide-y">
                              {req.controls.map((ctrl) => (
                                <label
                                  key={ctrl.id}
                                  className="flex items-center gap-3 px-4 py-2 hover:bg-muted/50 cursor-pointer"
                                >
                                  <Checkbox
                                    checked={selectedControls.has(ctrl.id)}
                                    onCheckedChange={() => toggleControl(ctrl.id)}
                                  />
                                  <ShieldCheck className="h-4 w-4 text-muted-foreground shrink-0" />
                                  <span className="font-mono text-xs">{ctrl.control_code}</span>
                                  <span className="text-sm truncate flex-1">{ctrl.name}</span>
                                  {ctrl.criticality_code && (
                                    <Badge
                                      variant="outline"
                                      className={`text-[10px] shrink-0 ${
                                        ctrl.criticality_code === "critical"
                                          ? "border-red-500 text-red-500"
                                          : ctrl.criticality_code === "high"
                                          ? "border-orange-500 text-orange-500"
                                          : ""
                                      }`}
                                    >
                                      {ctrl.criticality_code}
                                    </Badge>
                                  )}
                                </label>
                              ))}
                            </div>
                          )}
                        </div>
                      )
                    })}

                    {filteredData.filteredUnassigned.length > 0 && (
                      <div className="space-y-2">
                        <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground px-1">
                          <ShieldCheck className="h-4 w-4" />
                          Unassigned Controls ({filteredData.filteredUnassigned.length})
                        </div>
                        <div className="border rounded-lg overflow-hidden">
                          {filteredData.filteredUnassigned.map((ctrl) => (
                            <label
                              key={ctrl.id}
                              className="flex items-center gap-3 px-3 py-2 hover:bg-muted/50 cursor-pointer"
                            >
                              <Checkbox
                                checked={selectedControls.has(ctrl.id)}
                                onCheckedChange={() => toggleControl(ctrl.id)}
                              />
                              <ShieldCheck className="h-4 w-4 text-muted-foreground shrink-0" />
                              <span className="font-mono text-xs">{ctrl.control_code}</span>
                              <span className="text-sm truncate flex-1">{ctrl.name}</span>
                              {ctrl.criticality_code && (
                                <Badge
                                  variant="outline"
                                  className={`text-[10px] shrink-0 ${
                                    ctrl.criticality_code === "critical"
                                      ? "border-red-500 text-red-500"
                                      : ctrl.criticality_code === "high"
                                      ? "border-orange-500 text-orange-500"
                                      : ""
                                  }`}
                                >
                                  {ctrl.criticality_code}
                                </Badge>
                              )}
                            </label>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>

              <Separator />

              <div className="space-y-2">
                <label className="text-xs text-muted-foreground">Notes (optional)</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={2}
                  className="w-full rounded-md border border-input bg-background text-sm px-3 py-2 resize-none focus:outline-none focus:ring-1 focus:ring-ring"
                  placeholder="Add any notes for the reviewer..."
                />
              </div>
            </div>
          </>
        )}

        <DialogFooter className="mt-4 gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={submitting}>
            Cancel
          </Button>
          <Button
            size="sm"
            onClick={handleSubmit}
            disabled={submitting || (reqSelectedCount === 0 && ctrlSelectedCount === 0)}
          >
            {submitting ? (
              <>
                <Loader2 className="h-3 w-3 animate-spin mr-1.5" />
                Submitting...
              </>
            ) : (
              `Submit ${totalSelected} Items for Review`
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}