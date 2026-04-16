// ═══════════════════════════════════════════════════════════════════════════════
// ── Attachments ──────────────────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export interface AttachmentRecord {
  id: string
  entity_type: string
  entity_id: string
  uploaded_by: string
  uploader_display_name: string | null
  original_filename: string
  content_type: string
  file_size_bytes: number
  virus_scan_status: "pending" | "clean" | "infected" | "error" | "skipped"
  description: string | null
  auditor_access: boolean
  published_for_audit_by: string | null
  published_for_audit_at: string | null
  /** Storage path — only visible to admins via the API */
  storage_key?: string
  created_at: string
}

export interface AttachmentListResponse {
  items: AttachmentRecord[]
  total: number
  page: number
  per_page: number
}

export interface PresignedDownloadResponse {
  url: string
  expires_at: string
  filename: string
}
