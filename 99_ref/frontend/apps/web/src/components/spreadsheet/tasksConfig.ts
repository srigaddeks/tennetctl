import type { SpreadsheetColumn } from "./EntitySpreadsheet"

export interface TaskSpreadsheetRow extends Record<string, unknown> {
  id?: string
  title: string
  description?: string
  status?: string
  priority?: string
  due_date?: string
  assignee_name?: string
  assignee_user_id?: string
  entity_type?: string
  entity_id?: string
}

export const tasksColumns: SpreadsheetColumn<TaskSpreadsheetRow>[] = [
  {
    key: "title",
    label: "Title",
    type: "text",
    required: true,
    width: 260,
  },
  {
    key: "description",
    label: "Description",
    type: "textarea",
    width: 280,
  },
  {
    key: "status",
    label: "Status",
    type: "select",
    width: 130,
    options: [
      { value: "open",                 label: "Open" },
      { value: "in_progress",          label: "In Progress" },
      { value: "pending_verification", label: "Pending Review" },
      { value: "resolved",             label: "Resolved" },
      { value: "cancelled",            label: "Cancelled" },
      { value: "blocked",              label: "Blocked" },
    ],
    badgeStyles: {
      open:                 "bg-slate-500/10 text-slate-500 border-slate-500/20",
      in_progress:          "bg-blue-500/10 text-blue-600 border-blue-500/20",
      pending_verification: "bg-purple-500/10 text-purple-600 border-purple-500/20",
      resolved:             "bg-emerald-500/10 text-emerald-600 border-emerald-500/20",
      cancelled:            "bg-gray-500/10 text-gray-400 border-gray-500/20",
      blocked:              "bg-red-600/10 text-red-600 border-red-600/20",
    },
  },
  {
    key: "priority",
    label: "Priority",
    type: "select",
    width: 120,
    options: [
      { value: "critical", label: "Critical" },
      { value: "high",     label: "High" },
      { value: "medium",   label: "Medium" },
      { value: "low",      label: "Low" },
    ],
    badgeStyles: {
      critical: "bg-red-500/10 text-red-600 border-red-500/20",
      high:     "bg-orange-500/10 text-orange-600 border-orange-500/20",
      medium:   "bg-yellow-500/10 text-yellow-600 border-yellow-500/20",
      low:      "bg-green-500/10 text-green-600 border-green-500/20",
    },
  },
  {
    key: "due_date",
    label: "Due Date",
    type: "date",
    width: 130,
  },
  {
    key: "assignee_name",
    label: "Assignee",
    type: "readonly",
    width: 180,
  },
  {
    key: "assignee_user_id",
    label: "Assignee ID",
    type: "readonly",
    hidden: true,
    width: 120,
  },
  {
    key: "entity_type",
    label: "Linked To",
    type: "readonly",
    width: 130,
  },
  {
    key: "entity_id",
    label: "Linked To ID",
    type: "readonly",
    hidden: true,
    width: 120,
  },
]
