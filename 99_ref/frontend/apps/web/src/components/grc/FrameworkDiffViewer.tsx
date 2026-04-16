"use client"

import { useState, useMemo } from "react"
import { ChevronDownIcon, ChevronRightIcon, PlusCircleIcon, MinusCircleIcon, EditIcon, ChevronsDownUp, ChevronsUpDown } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@kcontrol/ui"
import type { FrameworkDiff, RequirementDiff, ControlDiff } from "@/lib/types/grc"

interface FrameworkDiffViewerProps {
  diff: FrameworkDiff
  showUnchanged?: boolean
}

export function FrameworkDiffViewer({ diff, showUnchanged = false }: FrameworkDiffViewerProps) {
  const [expandedReqs, setExpandedReqs] = useState<Set<string>>(
    () => new Set(diff.requirements.filter(r => r.status !== "unchanged").map(r => r.requirement_code))
  )
  const [localShowUnchanged, setLocalShowUnchanged] = useState(showUnchanged)

  const toggleReq = (code: string) => {
    setExpandedReqs(prev => {
      const next = new Set(prev)
      if (next.has(code)) next.delete(code)
      else next.add(code)
      return next
    })
  }

  const hasChanges = diff.controls_added + diff.controls_removed + diff.controls_modified > 0

  const visibleReqs = useMemo(
    () => localShowUnchanged ? diff.requirements : diff.requirements.filter(r => r.status !== "unchanged"),
    [diff.requirements, localShowUnchanged]
  )

  const unchangedCount = useMemo(
    () => diff.requirements.filter(r => r.status === "unchanged").length,
    [diff.requirements]
  )

  const allExpanded = visibleReqs.length > 0 && visibleReqs.every(r => expandedReqs.has(r.requirement_code))

  const expandAll = () => setExpandedReqs(new Set(visibleReqs.map(r => r.requirement_code)))
  const collapseAll = () => setExpandedReqs(new Set())

  return (
    <div className="font-mono text-sm">
      {/* Summary bar */}
      <div className="flex items-center gap-3 p-3 border rounded-md bg-muted/30 mb-4 flex-wrap">
        <span className="text-muted-foreground text-xs">
          <span className="font-semibold text-foreground">{diff.base_label}</span>
          {" → "}
          <span className="font-semibold text-foreground">{diff.compare_label}</span>
        </span>
        <div className="flex gap-2 flex-wrap">
          {diff.controls_added > 0 && (
            <Badge className="bg-green-500/10 text-green-600 border-green-500/30 dark:text-green-400">
              +{diff.controls_added} added
            </Badge>
          )}
          {diff.controls_removed > 0 && (
            <Badge className="bg-red-500/10 text-red-600 border-red-500/30 dark:text-red-400">
              -{diff.controls_removed} removed
            </Badge>
          )}
          {diff.controls_modified > 0 && (
            <Badge className="bg-amber-500/10 text-amber-600 border-amber-500/30 dark:text-amber-400">
              ~{diff.controls_modified} modified
            </Badge>
          )}
          {!hasChanges && (
            <Badge variant="secondary">No changes</Badge>
          )}
        </div>
        <div className="flex items-center gap-2 ml-auto">
          {visibleReqs.length > 1 && (
            <Button
              variant="ghost"
              size="sm"
              className="h-7 text-xs px-2 gap-1"
              onClick={allExpanded ? collapseAll : expandAll}
              title={allExpanded ? "Collapse all" : "Expand all"}
            >
              {allExpanded
                ? <ChevronsDownUp className="h-3.5 w-3.5" />
                : <ChevronsUpDown className="h-3.5 w-3.5" />}
              {allExpanded ? "Collapse all" : "Expand all"}
            </Button>
          )}
          <Button
            variant="outline"
            size="sm"
            className="h-7 text-xs"
            onClick={() => setLocalShowUnchanged(v => !v)}
          >
            {localShowUnchanged
              ? `Hide unchanged`
              : unchangedCount > 0
                ? `Show ${unchangedCount} unchanged`
                : "Show unchanged"}
          </Button>
        </div>
      </div>

      {/* Requirements */}
      {visibleReqs.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-10 text-center gap-2">
          <p className="text-sm text-muted-foreground">No changed requirements to display.</p>
          {unchangedCount > 0 && (
            <Button variant="ghost" size="sm" className="text-xs" onClick={() => setLocalShowUnchanged(true)}>
              Show {unchangedCount} unchanged
            </Button>
          )}
        </div>
      ) : (
        visibleReqs.map(req => {
          const visibleControls = localShowUnchanged
            ? req.controls
            : req.controls.filter(c => c.status !== "unchanged")

          const isExpanded = expandedReqs.has(req.requirement_code)

          return (
            <div key={req.requirement_code} className="border rounded-md mb-2 overflow-hidden">
              {/* Requirement header */}
              <button
                className="w-full flex items-center gap-2 px-3 py-2 bg-muted/50 hover:bg-muted text-left"
                onClick={() => toggleReq(req.requirement_code)}
              >
                {isExpanded ? (
                  <ChevronDownIcon className="w-4 h-4 shrink-0 text-muted-foreground" />
                ) : (
                  <ChevronRightIcon className="w-4 h-4 shrink-0 text-muted-foreground" />
                )}
                <span className="font-semibold text-foreground">
                  {req.requirement_code === "__no_req__" ? "Unassigned Controls" : req.requirement_code}
                </span>
                {(req.name || req.description) && req.requirement_code !== "__no_req__" && (
                  <span className="text-muted-foreground ml-1 font-normal truncate">
                    {req.name}{req.description && ` - ${req.description.slice(0, 50)}${req.description.length > 50 ? "..." : ""}`}
                  </span>
                )}
                <div className="ml-auto flex items-center gap-2 shrink-0">
                  {req.status !== "unchanged" && (
                    <span className="text-xs text-muted-foreground">
                      {req.controls.filter(c => c.status !== "unchanged").length} change{req.controls.filter(c => c.status !== "unchanged").length !== 1 ? "s" : ""}
                    </span>
                  )}
                  <DiffStatusBadge status={req.status} />
                </div>
              </button>

              {/* Controls list */}
              {isExpanded && (
                <div className="divide-y">
                  {visibleControls.length === 0 ? (
                    <p className="px-6 py-2 text-xs text-muted-foreground italic">No changed controls</p>
                  ) : (
                    visibleControls.map(ctrl => (
                      <ControlDiffRow key={ctrl.control_code} ctrl={ctrl} />
                    ))
                  )}
                </div>
              )}
            </div>
          )
        })
      )}
    </div>
  )
}

function ControlDiffRow({ ctrl }: { ctrl: ControlDiff }) {
  const [expanded, setExpanded] = useState(ctrl.status === "modified")
  const bgClass =
    ctrl.status === "added" ? "bg-green-500/10"
    : ctrl.status === "removed" ? "bg-red-500/10"
    : ctrl.status === "modified" ? "bg-amber-500/10"
    : ""

  const fieldCount = Object.keys(ctrl.field_changes).length

  return (
    <div className={bgClass}>
      <div
        className="flex items-center gap-2 px-6 py-2 cursor-pointer hover:bg-black/5 dark:hover:bg-white/5"
        onClick={() => setExpanded(v => !v)}
      >
        <StatusIcon status={ctrl.status} />
        <span className="font-medium">{ctrl.control_code}</span>
        {ctrl.control_name && (
          <span className="text-muted-foreground font-normal truncate">{ctrl.control_name}</span>
        )}
        <DiffStatusBadge status={ctrl.status} />
        {ctrl.status === "modified" && fieldCount > 0 && (
          <span className="text-xs text-muted-foreground ml-auto">
            {fieldCount} field{fieldCount !== 1 ? "s" : ""} changed
          </span>
        )}
      </div>

      {expanded && (
        <div className="px-8 pb-3 space-y-2">
          {/* Control Name & Description */}
          {(ctrl.control_name || ctrl.control_description) && (
            <div className="text-xs space-y-1 border-b border-border pb-2 mb-2">
              {ctrl.control_name && (
                <div>
                  <span className="font-semibold text-muted-foreground uppercase tracking-wide block mb-0.5">Name</span>
                  <p className="text-foreground break-words">{ctrl.control_name}</p>
                </div>
              )}
              {ctrl.control_description && (
                <div>
                  <span className="font-semibold text-muted-foreground uppercase tracking-wide block mb-0.5">Description</span>
                  <p className="text-foreground break-words">{ctrl.control_description}</p>
                </div>
              )}
            </div>
          )}

          {/* Field Changes */}
          {ctrl.status === "modified" && fieldCount > 0 && (
            <div className="space-y-2">
              <span className="font-semibold text-muted-foreground uppercase tracking-wide block text-xs">Changes</span>
              {Object.entries(ctrl.field_changes).map(([field, [base, compare]]) => (
                <div key={field} className="text-xs">
                  <span className="font-semibold text-muted-foreground uppercase tracking-wide block mb-1">{field}</span>
                  <div className="space-y-0.5">
                    {base != null && (
                      <div className="flex items-start gap-1.5">
                        <span className="text-red-500 font-mono shrink-0 mt-0.5">-</span>
                        <span className="text-red-700 dark:text-red-400 line-through break-words">{base}</span>
                      </div>
                    )}
                    {compare != null && (
                      <div className="flex items-start gap-1.5">
                        <span className="text-green-600 font-mono shrink-0 mt-0.5">+</span>
                        <span className="text-green-700 dark:text-green-400 break-words">{compare}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function StatusIcon({ status }: { status: ControlDiff["status"] }) {
  if (status === "added") return <PlusCircleIcon className="w-4 h-4 text-green-600 shrink-0" />
  if (status === "removed") return <MinusCircleIcon className="w-4 h-4 text-red-600 shrink-0" />
  if (status === "modified") return <EditIcon className="w-4 h-4 text-amber-600 shrink-0" />
  return <span className="w-4 h-4 shrink-0" />
}

function DiffStatusBadge({ status, className = "" }: { status: string; className?: string }) {
  const styles: Record<string, string> = {
    added: "bg-green-500/10 text-green-600 border-green-500/30 dark:text-green-400 dark:border-green-500/20",
    removed: "bg-red-500/10 text-red-600 border-red-500/30 dark:text-red-400 dark:border-red-500/20",
    modified: "bg-amber-500/10 text-amber-600 border-amber-500/30 dark:text-amber-400 dark:border-amber-500/20",
    unchanged: "bg-muted text-muted-foreground",
  }
  if (status === "unchanged") return null
  return (
    <Badge className={`${styles[status] ?? ""} ${className}`}>
      {status}
    </Badge>
  )
}
