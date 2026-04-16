import type { SpreadsheetColumn } from "./EntitySpreadsheet"

export interface ControlSpreadsheetRow extends Record<string, unknown> {
  id?: string
  control_code: string
  name: string
  description?: string
  control_type?: string
  criticality?: string
  automation_type?: string
  owner_name?: string
  owner_user_id?: string
  requirement_code?: string
  requirement_id?: string
  tags?: string
  framework_code?: string
  tasks_count?: string
  risks_count?: string
}

export const controlsColumns: SpreadsheetColumn<ControlSpreadsheetRow>[] = [
  {
    key: "control_code",
    label: "Control ID",
    type: "readonly",
    width: 120,
  },
  {
    key: "name",
    label: "Name",
    type: "text",
    required: true,
    width: 240,
  },
  {
    key: "description",
    label: "Description",
    type: "textarea",
    width: 300,
  },
  {
    key: "control_type",
    label: "Type",
    type: "select",
    width: 130,
    options: [
      { value: "preventive",   label: "Preventive" },
      { value: "detective",    label: "Detective" },
      { value: "corrective",   label: "Corrective" },
      { value: "compensating", label: "Compensating" },
    ],
    badgeStyles: {
      preventive:   "bg-blue-500/10 text-blue-600 border-blue-500/20",
      detective:    "bg-purple-500/10 text-purple-600 border-purple-500/20",
      corrective:   "bg-amber-500/10 text-amber-600 border-amber-500/20",
      compensating: "bg-teal-500/10 text-teal-600 border-teal-500/20",
    },
  },
  {
    key: "criticality",
    label: "Criticality",
    type: "select",
    width: 110,
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
    key: "automation_type",
    label: "Automation",
    type: "select",
    width: 120,
    options: [
      { value: "full",    label: "Full" },
      { value: "partial", label: "Partial" },
      { value: "manual",  label: "Manual" },
    ],
    badgeStyles: {
      full:    "bg-green-500/10 text-green-600 border-green-500/20",
      partial: "bg-blue-500/10 text-blue-600 border-blue-500/20",
      manual:  "bg-gray-500/10 text-gray-500 border-gray-500/20",
    },
  },
  {
    key: "owner_name",
    label: "Owner",
    type: "readonly",
    width: 160,
  },
  {
    key: "owner_user_id",
    label: "Owner ID",
    type: "readonly",
    hidden: true,
    width: 120,
  },
  {
    key: "requirement_code",
    label: "Requirement",
    type: "text",
    width: 140,
  },
  {
    key: "requirement_id",
    label: "Requirement ID",
    type: "readonly",
    hidden: true,
    width: 120,
  },
  {
    key: "tasks_count",
    label: "Tasks",
    type: "link",
    width: 80,
    getLinkHref: (row) => {
      if (!row.id) return null
      return `/tasks?entity_type=control&entity_id=${row.id}`
    },
  },
  {
    key: "risks_count",
    label: "Risks",
    type: "link",
    width: 80,
    getLinkHref: (row) => {
      if (!row.id) return null
      return `/risks?control_id=${row.id}`
    },
  },
  {
    key: "tags",
    label: "Tags",
    type: "text",
    width: 180,
  },
  {
    key: "framework_code",
    label: "Framework",
    type: "readonly",
    width: 110,
  },
]
