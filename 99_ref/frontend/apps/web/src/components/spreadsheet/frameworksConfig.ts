import type { SpreadsheetColumn } from "./EntitySpreadsheet"

export interface FrameworkSpreadsheetRow extends Record<string, unknown> {
  id?: string
  framework_code: string
  name: string
  description?: string
  framework_type_code?: string
  framework_category_code?: string
  publisher_type?: string
  control_count?: string
  is_marketplace_visible?: string
  version?: string
}

export const frameworksColumns: SpreadsheetColumn<FrameworkSpreadsheetRow>[] = [
  {
    key: "framework_code",
    label: "Code",
    type: "readonly",
    width: 130,
  },
  {
    key: "name",
    label: "Name",
    type: "text",
    required: true,
    width: 260,
  },
  {
    key: "description",
    label: "Description",
    type: "textarea",
    width: 320,
  },
  {
    key: "framework_type_code",
    label: "Type",
    type: "readonly",
    width: 130,
    badgeStyles: {
      regulatory:   "bg-red-500/10 text-red-600 border-red-500/20",
      standard:     "bg-blue-500/10 text-blue-600 border-blue-500/20",
      best_practice:"bg-purple-500/10 text-purple-600 border-purple-500/20",
      internal:     "bg-gray-500/10 text-gray-500 border-gray-500/20",
    },
  },
  {
    key: "framework_category_code",
    label: "Category",
    type: "readonly",
    width: 130,
  },
  {
    key: "publisher_type",
    label: "Publisher",
    type: "readonly",
    width: 120,
    badgeStyles: {
      custom:    "bg-blue-500/10 text-blue-600 border-blue-500/20",
      platform:  "bg-purple-500/10 text-purple-600 border-purple-500/20",
      community: "bg-teal-500/10 text-teal-600 border-teal-500/20",
    },
  },
  {
    key: "control_count",
    label: "Controls",
    type: "readonly",
    width: 90,
  },
  {
    key: "is_marketplace_visible",
    label: "Published",
    type: "readonly",
    width: 90,
    badgeStyles: {
      "true":  "bg-green-500/10 text-green-600 border-green-500/20",
      "false": "bg-gray-500/10 text-gray-500 border-gray-500/20",
    },
  },
  {
    key: "version",
    label: "Version",
    type: "readonly",
    width: 90,
  },
]
