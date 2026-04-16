"use client"

import React from "react"
import {
  Button,
  Badge,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@kcontrol/ui"
import { AlertTriangle, XCircle, CheckCircle2, Info } from "lucide-react"

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

export interface ImportResult {
  created: number
  updated: number
  skipped?: number
  warnings: string[]
  errors: Array<{
    row?: number
    key?: string
    field?: string
    message: string
  }>
  dry_run: boolean
}

export interface ImportResultDialogProps {
  open: boolean
  onClose: () => void
  result: ImportResult | null
  title?: string
  onCommit?: () => void | Promise<void>
}

// ─────────────────────────────────────────────────────────────────────────────
// Component
// ─────────────────────────────────────────────────────────────────────────────

export function ImportResultDialog({
  open,
  onClose,
  result,
  title = "Import Results",
  onCommit,
}: ImportResultDialogProps) {
  const [committing, setCommitting] = React.useState(false)

  const handleCommit = async () => {
    if (!onCommit) return
    setCommitting(true)
    try {
      await onCommit()
    } finally {
      setCommitting(false)
    }
  }

  if (!result) return null

  const hasErrors = result.errors.length > 0
  const hasWarnings = result.warnings.length > 0
  const hasActivity = result.created > 0 || result.updated > 0

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-lg max-h-[80vh] flex flex-col">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <DialogTitle>{title}</DialogTitle>
            {result.dry_run && (
              <Badge variant="secondary" className="text-xs">
                Dry Run Preview
              </Badge>
            )}
          </div>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto flex flex-col gap-4 py-2">
          {/* ── Summary stats ── */}
          <div className="grid grid-cols-3 gap-3">
            <StatCard
              icon={<CheckCircle2 className="h-4 w-4 text-green-600" />}
              label="Created"
              value={result.created}
              colorClass="text-green-700 dark:text-green-400"
            />
            <StatCard
              icon={<Info className="h-4 w-4 text-blue-600" />}
              label="Updated"
              value={result.updated}
              colorClass="text-blue-700 dark:text-blue-400"
            />
            <StatCard
              icon={<AlertTriangle className="h-4 w-4 text-muted-foreground" />}
              label="Skipped"
              value={result.skipped ?? 0}
              colorClass="text-muted-foreground"
            />
          </div>

          {/* ── No activity message ── */}
          {!hasActivity && !hasErrors && !hasWarnings && (
            <p className="text-sm text-muted-foreground text-center py-2">
              Nothing to import.
            </p>
          )}

          {/* ── Warnings ── */}
          {hasWarnings && (
            <div className="flex flex-col gap-1.5">
              <p className="text-xs font-semibold text-amber-700 dark:text-amber-400 uppercase tracking-wide flex items-center gap-1">
                <AlertTriangle className="h-3.5 w-3.5" />
                Warnings ({result.warnings.length})
              </p>
              <ul className="flex flex-col gap-1">
                {result.warnings.map((w, i) => (
                  <li
                    key={i}
                    className="text-sm text-amber-800 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded px-3 py-1.5"
                  >
                    {w}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* ── Errors ── */}
          {hasErrors && (
            <div className="flex flex-col gap-1.5">
              <p className="text-xs font-semibold text-destructive uppercase tracking-wide flex items-center gap-1">
                <XCircle className="h-3.5 w-3.5" />
                Errors ({result.errors.length})
              </p>
              <ul className="flex flex-col gap-1">
                {result.errors.map((err, i) => (
                  <li
                    key={i}
                    className="text-sm text-red-800 dark:text-red-300 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded px-3 py-1.5"
                  >
                    <span className="flex flex-wrap gap-1 items-start">
                      {err.row != null && (
                        <Badge variant="outline" className="text-xs shrink-0">
                          Row {err.row}
                        </Badge>
                      )}
                      {err.field && (
                        <Badge variant="outline" className="text-xs shrink-0">
                          {err.field}
                        </Badge>
                      )}
                      {err.key && (
                        <Badge variant="outline" className="text-xs shrink-0 font-mono">
                          {err.key}
                        </Badge>
                      )}
                      <span className="flex-1">{err.message}</span>
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={committing}>
            {result.dry_run ? "Cancel" : "Close"}
          </Button>
          {result.dry_run && onCommit && !hasErrors && (
            <Button
              onClick={() => void handleCommit()}
              disabled={committing}
            >
              {committing ? "Committing..." : "Commit Import"}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Stat card sub-component
// ─────────────────────────────────────────────────────────────────────────────

interface StatCardProps {
  icon: React.ReactNode
  label: string
  value: number
  colorClass: string
}

function StatCard({ icon, label, value, colorClass }: StatCardProps) {
  return (
    <div className="flex flex-col items-center gap-1 rounded-lg border border-border bg-muted/30 px-3 py-3">
      <div className="flex items-center gap-1.5">
        {icon}
        <span className={`text-xl font-bold tabular-nums ${colorClass}`}>
          {value}
        </span>
      </div>
      <span className="text-xs text-muted-foreground">{label}</span>
    </div>
  )
}
