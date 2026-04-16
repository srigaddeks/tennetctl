"use client"

import { useState, useCallback, useEffect } from "react"
import { Button, Input, Label } from "@kcontrol/ui"
import {
  X, RefreshCw, Calendar, FileText, Wrench,
  Plus, Trash2,
} from "lucide-react"
import { createTask, addAssignment, updateTask } from "@/lib/api/grc"
import type { CreateTaskRequest } from "@/lib/types/grc"
import { FormFillChat } from "@/components/ai/FormFillChat"

// ─────────────────────────────────────────────────────────────────────────────
// Props
// ─────────────────────────────────────────────────────────────────────────────

export interface TaskCreateSlideOverProps {
  open: boolean
  onClose: () => void
  onCreated: () => void
  /** Pre-set task type — if provided, the type selector is hidden */
  taskTypeCode?: string
  taskTypeName?: string
  /** The GRC entity this task is linked to */
  entityType: "risk" | "control" | "framework" | "test"
  entityId: string
  entityTitle?: string
  orgId: string
  workspaceId: string
}

// ─────────────────────────────────────────────────────────────────────────────
// Component
// ─────────────────────────────────────────────────────────────────────────────

export function TaskCreateSlideOver({
  open,
  onClose,
  onCreated,
  taskTypeCode,
  taskTypeName,
  entityType,
  entityId,
  entityTitle,
  orgId,
  workspaceId,
}: TaskCreateSlideOverProps) {
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [priority, setPriority] = useState("medium")
  const [typeCode, setTypeCode] = useState(taskTypeCode ?? "evidence_collection")
  const [assigneeEmails, setAssigneeEmails] = useState("")
  const [dueDate, setDueDate] = useState("")
  const [criteria, setCriteria] = useState<string[]>([""])
  const [remediationPlan, setRemediationPlan] = useState("")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Reset on open
  useEffect(() => {
    if (open) {
      setTitle("")
      setDescription("")
      setPriority("medium")
      setTypeCode(taskTypeCode ?? "evidence_collection")
      setAssigneeEmails("")
      setDueDate("")
      setCriteria([""])
      setRemediationPlan("")
      setError(null)
    }
  }, [open, taskTypeCode])

  const handleSubmit = useCallback(async () => {
    if (!title.trim()) { setError("Title is required."); return }
    setSaving(true); setError(null)
    try {
      const criteriaText = criteria.filter(l => l.trim()).join("\n") || undefined
      const payload: CreateTaskRequest = {
        title: title.trim(),
        task_type_code: typeCode,
        priority_code: priority,
        org_id: orgId,
        workspace_id: workspaceId,
        entity_type: entityType,
        entity_id: entityId,
        description: description.trim() || undefined,
        due_date: dueDate || undefined,
        acceptance_criteria: criteriaText,
        remediation_plan: typeCode === "control_remediation" ? remediationPlan.trim() || undefined : undefined,
      }
      let created = await createTask(payload)

      const emails = assigneeEmails.split(",").map(e => e.trim().toLowerCase()).filter(e => e)
      if (emails.length > 0) {
        const assignments = await Promise.all(
          emails.map(email => addAssignment(created.id, { email, role: "co_assignee" }))
        )
        const primaryAssigneeId = assignments[0]?.user_id
        if (primaryAssigneeId) {
          created = await updateTask(created.id, { assignee_user_id: primaryAssigneeId })
        }
      }

      onCreated()
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create task")
    } finally {
      setSaving(false)
    }
  }, [title, typeCode, priority, orgId, workspaceId, entityType, entityId, description, assigneeEmails, dueDate, criteria, remediationPlan, onCreated, onClose])

  if (!open) return null

  const typeLabel = taskTypeName ?? (
    typeCode === "evidence_collection" ? "Evidence Collection" :
    typeCode === "control_remediation" ? "Remediation" :
    typeCode === "risk_mitigation" ? "Risk Mitigation" : typeCode
  )

  const TypeIcon = typeCode === "evidence_collection" ? FileText : Wrench

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Slide-over panel */}
      <div className="fixed top-0 right-0 bottom-0 z-50 w-full sm:w-[520px] bg-background border-l border-border shadow-2xl flex flex-col overflow-hidden">

        {/* Header */}
        <div className="px-5 pt-5 pb-4 border-b border-border shrink-0 space-y-3">
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="flex items-center gap-2 mb-0.5">
                <TypeIcon className="w-4 h-4 text-primary" />
                <h2 className="text-base font-bold text-foreground">
                  New {typeLabel} Task
                </h2>
              </div>
              {entityTitle && (
                <p className="text-xs text-muted-foreground">
                  Linked to <span className="font-medium text-foreground capitalize">{entityType}</span>: {entityTitle}
                </p>
              )}
            </div>
            <button onClick={onClose} className="p-1.5 rounded hover:bg-muted transition-colors mt-0.5">
              <X className="h-4 w-4 text-muted-foreground" />
            </button>
          </div>
          <FormFillChat
            entityType="task"
            orgId={orgId}
            workspaceId={workspaceId}
            pageContext={{ entity_type: entityType, entity_id: entityId, entity_title: entityTitle }}
            getFormValues={() => ({ title, description, task_type_code: typeCode, priority_code: priority })}
            onFilled={(fields) => {
              if (fields.title) setTitle(fields.title)
              if (fields.description) setDescription(fields.description)
              if (fields.task_type_code) setTypeCode(fields.task_type_code)
              if (fields.priority_code && ["critical", "high", "medium", "low"].includes(fields.priority_code)) setPriority(fields.priority_code)
              if (fields.acceptance_criteria) {
                const lines = fields.acceptance_criteria.split("\n").filter(l => l.trim())
                setCriteria(lines.length > 0 ? lines : [""])
              }
              if (fields.remediation_plan) setRemediationPlan(fields.remediation_plan)
            }}
            placeholder={entityTitle ? `e.g. collect evidence for ${entityTitle}` : "e.g. review firewall rules for SOC 2"}
          />
        </div>

        {/* Scrollable body */}
        <div className="flex-1 overflow-y-auto px-5 py-5 space-y-5">

          {/* Task Type (only shown if not pre-set) */}
          {!taskTypeCode && (
            <div className="space-y-1.5">
              <Label>Task Type <span className="text-red-500">*</span></Label>
              <select
                className="w-full rounded-lg border border-border bg-background text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-ring"
                value={typeCode}
                onChange={e => setTypeCode(e.target.value)}
              >
                <option value="evidence_collection">Evidence Collection</option>
                <option value="control_remediation">Remediation</option>
                <option value="risk_mitigation">Risk Mitigation</option>
                <option value="general">General</option>
              </select>
            </div>
          )}

          {/* Title */}
          <div className="space-y-1.5">
            <Label>Title <span className="text-red-500">*</span></Label>
            <Input
              placeholder="Task title…"
              value={title}
              onChange={e => setTitle(e.target.value)}
              autoFocus
            />
          </div>

          {/* Description */}
          <div className="space-y-1.5">
            <Label>Description</Label>
            <textarea
              className="w-full rounded-lg border border-border bg-background text-sm px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-ring min-h-[80px]"
              placeholder="Describe what needs to be done…"
              value={description}
              onChange={e => setDescription(e.target.value)}
            />
          </div>

          {/* Priority */}
          <div className="space-y-1.5">
            <Label>Priority</Label>
            <select
              className="w-full rounded-lg border border-border bg-background text-sm px-3 py-2 focus:outline-none focus:ring-2 focus:ring-ring"
              value={priority}
              onChange={e => setPriority(e.target.value)}
            >
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          {/* Due Date */}
          <div className="space-y-1.5">
            <Label className="flex items-center gap-1.5"><Calendar className="w-3.5 h-3.5" />Due Date</Label>
            <Input type="date" value={dueDate} onChange={e => setDueDate(e.target.value)} />
          </div>

          {/* Assignee emails */}
          <div className="space-y-1.5">
            <Label>Assignee</Label>
            <Input
              placeholder="Email address (e.g. alice@company.com)"
              value={assigneeEmails}
              onChange={e => setAssigneeEmails(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">Enter the email of the assignee</p>
          </div>

          {/* Acceptance Criteria */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Acceptance Criteria</Label>
              <button
                type="button"
                onClick={() => setCriteria(prev => [...prev, ""])}
                className="flex items-center gap-1 text-xs text-primary hover:text-primary/80 transition-colors"
              >
                <Plus className="w-3 h-3" /> Add item
              </button>
            </div>
            <div className="space-y-2">
              {criteria.map((item, i) => (
                <div key={i} className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded border border-border shrink-0 mt-0.5" />
                  <Input
                    placeholder={`Criteria ${i + 1}…`}
                    value={item}
                    onChange={e => {
                      const next = [...criteria]
                      next[i] = e.target.value
                      setCriteria(next)
                    }}
                    className="flex-1"
                  />
                  {criteria.length > 1 && (
                    <button
                      type="button"
                      onClick={() => setCriteria(prev => prev.filter((_, j) => j !== i))}
                      className="p-1 text-muted-foreground hover:text-destructive transition-colors shrink-0"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Remediation Plan — only for control_remediation type */}
          {typeCode === "control_remediation" && (
            <div className="space-y-1.5">
              <Label>Remediation Plan</Label>
              <textarea
                className="w-full rounded-lg border border-border bg-background text-sm px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-ring min-h-[80px]"
                placeholder="Describe the remediation steps…"
                value={remediationPlan}
                onChange={e => setRemediationPlan(e.target.value)}
              />
            </div>
          )}

          {error && (
            <p className="text-sm text-red-600 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
              {error}
            </p>
          )}
        </div>

        {/* Footer */}
        <div className="shrink-0 px-5 py-4 border-t border-border flex items-center justify-end gap-3">
          <Button variant="outline" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={saving}>
            {saving ? <RefreshCw className="w-3.5 h-3.5 animate-spin mr-1.5" /> : null}
            Create Task
          </Button>
        </div>
      </div>
    </>
  )
}
