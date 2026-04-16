import { fetchWithAuth } from "./apiClient"

// ═══════════════════════════════════════════════════════════════════════════════
// ── Types ────────────────────────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export interface DocCategoryResponse {
  code: string
  name: string
  description: string | null
  sort_order: number
  is_active: boolean
}

export interface DocumentResponse {
  id: string
  tenant_key: string
  scope: "global" | "org"
  org_id: string | null
  category_code: string
  category_name: string | null
  title: string
  description: string | null
  tags: string[]
  version_label: string | null
  original_filename: string
  content_type: string
  file_size_bytes: number
  virus_scan_status: string
  is_visible: boolean
  uploaded_by: string
  uploader_display_name: string | null
  created_at: string
  updated_at: string
}

export interface DocumentListResponse {
  items: DocumentResponse[]
  total: number
}

export interface PresignedDownloadResponse {
  document_id: string
  filename: string
  download_url: string
  expires_at: string
  content_type: string
  file_size_bytes: number
}

export interface UploadDocumentResponse {
  document: DocumentResponse
  message: string
}

export interface UpdateDocumentRequest {
  title?: string | null
  description?: string | null
  tags?: string[] | null
  version_label?: string | null
  category_code?: string | null
  is_visible?: boolean | null
}

export interface DocEventResponse {
  id: string
  event_type: string
  actor_user_id: string
  actor_display_name: string | null
  created_at: string
  metadata: Record<string, any>
}

export interface DocHistoryResponse {
  items: DocEventResponse[]
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── API calls ────────────────────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export async function listDocCategories(): Promise<DocCategoryResponse[]> {
  const res = await fetchWithAuth("/api/v1/docs/categories", { method: "GET" })
  if (!res.ok) throw new Error(`Failed to load categories: ${res.status}`)
  return res.json()
}

export async function listGlobalDocs(params?: {
  category_code?: string
  search?: string
  tags?: string
  page?: number
  per_page?: number
  include_all?: boolean
}): Promise<DocumentListResponse> {
  const q = new URLSearchParams()
  if (params?.category_code) q.set("category_code", params.category_code)
  if (params?.search) q.set("search", params.search)
  if (params?.tags) q.set("tags", params.tags)
  if (params?.page) q.set("page", String(params.page))
  if (params?.per_page) q.set("per_page", String(params.per_page))
  if (params?.include_all) q.set("include_all", "true")
  const qs = q.toString() ? `?${q}` : ""
  const res = await fetchWithAuth(`/api/v1/docs/global${qs}`, { method: "GET" })
  if (!res.ok) throw new Error(`Failed to load global docs: ${res.status}`)
  return res.json()
}

export async function listOrgDocs(
  orgId: string,
  params?: {
    category_code?: string
    search?: string
    page?: number
    per_page?: number
    include_all?: boolean
  }
): Promise<DocumentListResponse> {
  const q = new URLSearchParams({ org_id: orgId })
  if (params?.category_code) q.set("category_code", params.category_code)
  if (params?.search) q.set("search", params.search)
  if (params?.page) q.set("page", String(params.page))
  if (params?.per_page) q.set("per_page", String(params.per_page))
  if (params?.include_all) q.set("include_all", "true")
  const res = await fetchWithAuth(`/api/v1/docs/org?${q}`, { method: "GET" })
  if (!res.ok) throw new Error(`Failed to load org docs: ${res.status}`)
  return res.json()
}

export async function getDocDownloadUrl(docId: string): Promise<PresignedDownloadResponse> {
  const res = await fetchWithAuth(`/api/v1/docs/${docId}/download`, { method: "GET" })
  if (!res.ok) throw new Error(`Failed to get download URL: ${res.status}`)
  return res.json()
}

export async function uploadGlobalDoc(formData: FormData): Promise<UploadDocumentResponse> {
  const res = await fetchWithAuth("/api/v1/docs/global/upload", {
    method: "POST",
    body: formData,
  })
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    try {
      const parsed = JSON.parse(text)
      if (parsed?.error?.message) throw new Error(`Upload failed: ${parsed.error.message}`)
    } catch (e: any) {
      if (e.message.startsWith("Upload failed:")) throw e
    }
    throw new Error(`Upload failed: ${res.status} — ${text}`)
  }
  return res.json()
}

export async function uploadOrgDoc(formData: FormData): Promise<UploadDocumentResponse> {
  const res = await fetchWithAuth("/api/v1/docs/org/upload", {
    method: "POST",
    body: formData,
  })
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    try {
      const parsed = JSON.parse(text)
      if (parsed?.error?.message) throw new Error(`Upload failed: ${parsed.error.message}`)
    } catch (e: any) {
      if (e.message.startsWith("Upload failed:")) throw e
    }
    throw new Error(`Upload failed: ${res.status} — ${text}`)
  }
  return res.json()
}

export async function updateDocument(
  docId: string,
  body: UpdateDocumentRequest
): Promise<DocumentResponse> {
  const res = await fetchWithAuth(`/api/v1/docs/${docId}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`Update failed: ${res.status}`)
  return res.json()
}

export async function deleteDocument(docId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/docs/${docId}`, { method: "DELETE" })
  if (!res.ok) throw new Error(`Delete failed: ${res.status}`)
}

export async function replaceDocumentFile(docId: string, formData: FormData): Promise<DocumentResponse> {
  const res = await fetchWithAuth(`/api/v1/docs/${docId}/replace`, {
    method: "POST",
    body: formData,
  })
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    try {
      const parsed = JSON.parse(text)
      if (parsed?.error?.message) throw new Error(`Replacement failed: ${parsed.error.message}`)
    } catch (e: any) {
      if (e.message.startsWith("Replacement failed:")) throw e
    }
    throw new Error(`Replacement failed: ${res.status} — ${text}`)
  }
  return res.json()
}

export async function getDocumentHistory(docId: string): Promise<DocHistoryResponse> {
  const res = await fetchWithAuth(`/api/v1/docs/${docId}/history`, { method: "GET" })
  if (!res.ok) throw new Error(`Failed to load history: ${res.status}`)
  return res.json()
}

export async function revertDocument(docId: string, eventId: string): Promise<DocumentResponse> {
  const res = await fetchWithAuth(`/api/v1/docs/${docId}/revert/${eventId}`, { method: "POST" })
  if (!res.ok) throw new Error(`Revert failed: ${res.status}`)
  return res.json()
}
