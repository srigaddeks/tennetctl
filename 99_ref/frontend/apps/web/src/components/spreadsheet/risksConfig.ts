import type { SpreadsheetColumn } from "./EntitySpreadsheet"

export interface RiskSpreadsheetRow extends Record<string, unknown> {
  id?: string
  risk_code: string
  title: string
  description?: string
  risk_level_code?: string
  treatment_type?: string
  owner_email?: string
  owner_user_id?: string
  status?: string
  business_impact?: string
}

export const risksColumns: SpreadsheetColumn<RiskSpreadsheetRow>[] = [
  {
    key: "risk_code",
    label: "Risk ID",
    type: "readonly",
    width: 130,
  },
  {
    key: "title",
    label: "Title",
    type: "text",
    required: true,
    width: 220,
  },
  {
    key: "description",
    label: "Description",
    type: "textarea",
    width: 280,
  },
  {
    key: "risk_level_code",
    label: "Risk Level",
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
    key: "treatment_type",
    label: "Treatment",
    type: "select",
    width: 130,
    options: [
      { value: "mitigate",  label: "Mitigate" },
      { value: "accept",    label: "Accept" },
      { value: "transfer",  label: "Transfer" },
      { value: "avoid",     label: "Avoid" },
    ],
    badgeStyles: {
      mitigate: "bg-blue-500/10 text-blue-600 border-blue-500/20",
      accept:   "bg-yellow-500/10 text-yellow-600 border-yellow-500/20",
      transfer: "bg-purple-500/10 text-purple-600 border-purple-500/20",
      avoid:    "bg-red-500/10 text-red-600 border-red-500/20",
    },
  },
  {
    key: "status",
    label: "Status",
    type: "select",
    width: 130,
    options: [
      { value: "identified", label: "Identified" },
      { value: "assessed",   label: "Assessed" },
      { value: "treating",   label: "Treating" },
      { value: "accepted",   label: "Accepted" },
      { value: "closed",     label: "Closed" },
    ],
    badgeStyles: {
      identified: "bg-slate-500/10 text-slate-500 border-slate-500/20",
      assessed:   "bg-blue-500/10 text-blue-600 border-blue-500/20",
      treating:   "bg-yellow-500/10 text-yellow-600 border-yellow-500/20",
      accepted:   "bg-emerald-500/10 text-emerald-600 border-emerald-500/20",
      closed:     "bg-green-500/10 text-green-600 border-green-500/20",
    },
  },
  {
    key: "owner_email",
    label: "Owner",
    type: "readonly",
    width: 180,
  },
  {
    key: "owner_user_id",
    label: "Owner ID",
    type: "readonly",
    hidden: true,
    width: 120,
  },
  {
    key: "business_impact",
    label: "Business Impact",
    type: "textarea",
    width: 220,
  },
]
