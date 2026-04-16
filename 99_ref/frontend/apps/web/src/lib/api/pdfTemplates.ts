import { fetchWithAuth, getAccessToken, API_BASE_URL } from "./apiClient"

// ── Types ─────────────────────────────────────────────────────────────────────

export interface PdfTemplateResponse {
  id: string
  tenant_key: string
  name: string
  description: string | null
  cover_style: "dark_navy" | "light_minimal" | "gradient_accent"
  primary_color: string
  secondary_color: string
  header_text: string | null
  footer_text: string | null
  prepared_by: string | null
  doc_ref_prefix: string | null
  classification_label: string | null
  applicable_report_types: string[]
  is_default: boolean
  shell_file_key: string | null
  shell_file_name: string | null
  created_by: string
  created_at: string
  updated_at: string
}

export interface PdfTemplateListResponse {
  items: PdfTemplateResponse[]
  total: number
}

export interface CreatePdfTemplateRequest {
  name: string
  description?: string
  cover_style: "dark_navy" | "light_minimal" | "gradient_accent"
  primary_color: string
  secondary_color: string
  header_text?: string
  footer_text?: string
  prepared_by?: string
  doc_ref_prefix?: string
  classification_label?: string
  applicable_report_types?: string[]
  is_default?: boolean
}

export interface UpdatePdfTemplateRequest {
  name?: string
  description?: string
  cover_style?: "dark_navy" | "light_minimal" | "gradient_accent"
  primary_color?: string
  secondary_color?: string
  header_text?: string
  footer_text?: string
  prepared_by?: string
  doc_ref_prefix?: string
  classification_label?: string
  applicable_report_types?: string[]
  is_default?: boolean
}

// ── API functions ─────────────────────────────────────────────────────────────

export async function listPdfTemplates(params?: {
  report_type?: string
  is_default?: boolean
  limit?: number
  offset?: number
}): Promise<PdfTemplateListResponse> {
  const qs = new URLSearchParams()
  if (params?.report_type) qs.set("report_type", params.report_type)
  if (params?.is_default !== undefined) qs.set("is_default", String(params.is_default))
  if (params?.limit !== undefined) qs.set("limit", String(params.limit))
  if (params?.offset !== undefined) qs.set("offset", String(params.offset))
  const query = qs.toString()
  const res = await fetchWithAuth(`/api/v1/ai/pdf-templates${query ? `?${query}` : ""}`)
  if (!res.ok) throw new Error(`Failed to list PDF templates: ${res.status}`)
  return res.json()
}

export async function getPdfTemplate(templateId: string): Promise<PdfTemplateResponse> {
  const res = await fetchWithAuth(`/api/v1/ai/pdf-templates/${templateId}`)
  if (!res.ok) throw new Error(`Failed to get PDF template: ${res.status}`)
  return res.json()
}

export async function getDefaultTemplateForType(reportType: string): Promise<PdfTemplateResponse | null> {
  const result = await listPdfTemplates({ report_type: reportType, is_default: true, limit: 1 })
  return result.items[0] ?? null
}

export async function createPdfTemplate(
  data: CreatePdfTemplateRequest,
): Promise<PdfTemplateResponse> {
  const res = await fetchWithAuth("/api/v1/ai/pdf-templates", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error(`Failed to create PDF template: ${res.status}`)
  return res.json()
}

export async function updatePdfTemplate(
  templateId: string,
  data: UpdatePdfTemplateRequest,
): Promise<PdfTemplateResponse> {
  const res = await fetchWithAuth(`/api/v1/ai/pdf-templates/${templateId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error(`Failed to update PDF template: ${res.status}`)
  return res.json()
}

export async function deletePdfTemplate(templateId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/ai/pdf-templates/${templateId}`, {
    method: "DELETE",
  })
  if (!res.ok && res.status !== 204) throw new Error(`Failed to delete PDF template: ${res.status}`)
}

export async function setPdfTemplateDefault(templateId: string): Promise<PdfTemplateResponse> {
  const res = await fetchWithAuth(`/api/v1/ai/pdf-templates/${templateId}/set-default`, {
    method: "POST",
  })
  if (!res.ok) throw new Error(`Failed to set default PDF template: ${res.status}`)
  return res.json()
}

export async function uploadPdfShell(
  templateId: string,
  file: File,
  onProgress?: (pct: number) => void,
): Promise<PdfTemplateResponse> {
  await fetchWithAuth(`/api/v1/ai/pdf-templates/${templateId}`, { method: "GET" }).catch(() => {})
  const token = getAccessToken()

  const formData = new FormData()
  formData.append("file", file)

  return new Promise<PdfTemplateResponse>((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open("POST", `${API_BASE_URL}/api/v1/ai/pdf-templates/${templateId}/upload-shell`)
    if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`)
    if (onProgress) {
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100))
      }
    }
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText))
        } catch {
          reject(new Error("Invalid response from server"))
        }
      } else {
        reject(new Error(`Upload failed: ${xhr.status}`))
      }
    }
    xhr.onerror = () => reject(new Error("Network error during upload"))
    xhr.timeout = 120_000
    xhr.send(formData)
  })
}
