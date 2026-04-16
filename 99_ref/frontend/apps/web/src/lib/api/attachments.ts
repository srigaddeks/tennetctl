import { fetchWithAuth, getAccessToken, API_BASE_URL } from "./apiClient"
import type {
  AttachmentRecord,
  AttachmentListResponse,
  PresignedDownloadResponse,
} from "../types/attachments"

// ═══════════════════════════════════════════════════════════════════════════════
// ── Attachments (/api/v1/at/attachments) ─────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export async function listAttachments(
  entityType: string,
  entityId: string,
  page = 1,
  perPage = 25,
): Promise<AttachmentListResponse> {
  const params = new URLSearchParams({
    entity_type: entityType,
    entity_id: entityId,
    page: String(page),
    per_page: String(perPage),
  })
  const res = await fetchWithAuth(`/api/v1/at/attachments?${params}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to list attachments")
  return data as AttachmentListResponse
}

export async function listEngagementAttachments(
  engagementId: string,
  page = 1,
  perPage = 100,
): Promise<AttachmentListResponse> {
  const params = new URLSearchParams({
    engagement_id: engagementId,
    page: String(page),
    per_page: String(perPage),
  })
  const res = await fetchWithAuth(`/api/v1/at/attachments?${params}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to list engagement attachments")
  return data as AttachmentListResponse
}

export async function uploadAttachment(
  entityType: string,
  entityId: string,
  file: File,
  description?: string,
  onProgress?: (pct: number) => void,
): Promise<AttachmentRecord> {
  // FormData upload: fetchWithAuth forces Content-Type: application/json which
  // would clobber the multipart boundary. We ensure the token is valid by
  // running a no-op fetchWithAuth call first, then build the request manually.
  await fetchWithAuth("/api/v1/at/attachments", { method: "HEAD" }).catch(() => {})
  const token = getAccessToken()

  const formData = new FormData()
  formData.append("file", file)
  formData.append("entity_type", entityType)
  formData.append("entity_id", entityId)
  if (description) formData.append("description", description)

  return new Promise<AttachmentRecord>((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open("POST", `${API_BASE_URL}/api/v1/at/attachments/upload`)
    if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`)
    if (onProgress) {
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100))
      }
    }
    xhr.onload = () => {
      try {
        const data = JSON.parse(xhr.responseText)
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(data as AttachmentRecord)
        } else {
          reject(new Error(data.error?.message || data.detail || "Failed to upload attachment"))
        }
      } catch {
        reject(new Error("Failed to parse upload response"))
      }
    }
    xhr.onerror = () => reject(new Error("Network error during upload"))
    xhr.timeout = 300000 // 5 minute timeout
    xhr.ontimeout = () => reject(new Error("Upload timed out"))
    xhr.send(formData)
  })
}

export async function getDownloadUrl(attachmentId: string): Promise<PresignedDownloadResponse> {
  const res = await fetchWithAuth(`/api/v1/at/attachments/${attachmentId}/download`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to get download URL")
  return data as PresignedDownloadResponse
}

export async function deleteAttachment(attachmentId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/at/attachments/${attachmentId}`, {
    method: "DELETE",
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error?.message || data.detail || "Failed to delete attachment")
  }
}

export async function getAttachmentCount(entityType: string, entityId: string): Promise<number> {
  const res = await listAttachments(entityType, entityId, 1, 1)
  return res.total
}

export async function updateAttachmentDescription(
  attachmentId: string,
  description: string,
): Promise<AttachmentRecord> {
  const res = await fetchWithAuth(`/api/v1/at/attachments/${attachmentId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ description }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to update attachment")
  return data as AttachmentRecord
}

export async function updateAttachmentAuditorAccess(
  attachmentId: string,
  auditorAccess: boolean,
): Promise<AttachmentRecord> {
  const res = await fetchWithAuth(`/api/v1/at/attachments/${attachmentId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ auditor_access: auditorAccess }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to update auditor access")
  return data as AttachmentRecord
}

export async function getAttachment(attachmentId: string): Promise<AttachmentRecord> {
  const res = await fetchWithAuth(`/api/v1/at/attachments/${attachmentId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to get attachment")
  return data as AttachmentRecord
}

export async function bulkUploadAttachments(
  entityType: string,
  entityId: string,
  files: File[],
  descriptions?: Record<string, string>,
  onProgress?: (fileName: string, percent: number) => void,
): Promise<{ results: Array<{ status: string; attachment?: AttachmentRecord; error?: string }> }> {
  // Upload files sequentially using single upload endpoint
  const results = []
  for (const file of files) {
    try {
      const result = await uploadAttachment(entityType, entityId, file, descriptions?.[file.name])
      results.push({ status: "success", attachment: result })
      onProgress?.(file.name, 100)
    } catch (e) {
      results.push({ status: "error", error: String(e) })
    }
  }
  return { results }
}

export async function getDownloadHistory(attachmentId: string): Promise<any[]> {
  const res = await fetchWithAuth(`/api/v1/at/attachments/${attachmentId}/download-history`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to get download history")
  return data
}

export async function checkStorageHealth(): Promise<{ provider: string; status: string; latency_ms: number }> {
  const res = await fetchWithAuth(`/api/v1/at/health`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to check storage health")
  return data
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── Storage Usage (/api/v1/at/attachments/storage-usage) ────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export interface StorageUsageResponse {
  tenant_key: string
  total_bytes: number
  total_files: number
  quota_bytes: number
  usage_percent: number
}

export async function getStorageUsage(): Promise<StorageUsageResponse> {
  const res = await fetchWithAuth("/api/v1/at/attachments/storage-usage")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to get storage usage")
  return data as StorageUsageResponse
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── GDPR Admin (/api/v1/at/attachments/admin) ───────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export interface GdprAttachmentDeleteResult {
  attachments_deleted: number
  user_id: string
}

export async function gdprDeleteUserAttachments(userId: string): Promise<GdprAttachmentDeleteResult> {
  const res = await fetchWithAuth(`/api/v1/at/attachments/admin/users/${userId}/data`, {
    method: "DELETE",
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to delete user attachment data")
  return data as GdprAttachmentDeleteResult
}
