# Attachments API

Base path: `/api/v1/at`
Auth: Bearer JWT required on all endpoints
Permission: `attachments.view` to download, `attachments.create` to upload

---

## Overview

The attachments system supports:
- **Multi-provider storage** — AWS S3, Google Cloud Storage, Azure Blob, MinIO
- **Presigned URLs** — clients download directly from storage (files never proxied through API)
- **Virus scanning** — async scan via ClamAV/cloud provider; download blocked until `clean`
- **Storage quota** — per-org limits enforced via materialized view
- **Checksums** — SHA-256 computed server-side for integrity verification
- **Chunked reading** — files >10MB read in 1MB chunks to prevent OOM
- **GDPR** — soft-delete all user attachments via admin endpoint
- **Versions** — immutable upload history in `04_trx_attachment_versions`

---

## List Attachments

### GET /api/v1/at/attachments

List all non-deleted attachments for an entity.

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| entity_type | string | yes | e.g. `task`, `risk`, `control`, `framework` |
| entity_id | UUID | yes | UUID of the entity |
| page | int | no | Page number (default: 1) |
| per_page | int | no | 1–200 (default: 50) |

**Response** `200 OK`
```json
{
  "items": [
    {
      "id": "...",
      "entity_type": "risk",
      "entity_id": "...",
      "original_filename": "risk_assessment_q1.pdf",
      "content_type": "application/pdf",
      "file_size_bytes": 204800,
      "checksum_sha256": "abc123...",
      "description": "Q1 2026 Risk Assessment Report",
      "uploaded_by": "...",
      "upload_status": "committed",
      "virus_scan_status": "clean",
      "virus_scan_at": "2026-03-20T10:05:00Z",
      "is_deleted": false,
      "created_at": "2026-03-20T10:00:00Z",
      "updated_at": "2026-03-20T10:00:00Z"
    }
  ],
  "total": 3,
  "page": 1,
  "per_page": 50
}
```

**`upload_status` values:** `staging`, `uploading`, `committed`, `failed`

**`virus_scan_status` values:** `pending`, `scanning`, `clean`, `infected`, `error`

> Files with `virus_scan_status: infected` are blocked from download.

---

## Upload Attachment

### POST /api/v1/at/attachments/upload

Upload a single file. Requires `attachments.create` permission.

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | File | yes | The file to upload |
| entity_type | string | yes | Target entity type |
| entity_id | UUID | yes | Target entity UUID |
| description | string | no | Human-readable description |

**Response** `201 Created`
```json
{
  "id": "...",
  "original_filename": "evidence_q1.pdf",
  "content_type": "application/pdf",
  "file_size_bytes": 204800,
  "checksum_sha256": "abc123...",
  "upload_status": "committed",
  "virus_scan_status": "pending",
  "created_at": "2026-03-20T10:00:00Z"
}
```

**Limits:**
- Max file size: controlled by `STORAGE_MAX_FILE_SIZE_MB` env var (default: 100MB)
- Allowed types: configurable via `STORAGE_ALLOWED_MIME_TYPES`
- Org quota: enforced via `mv_org_storage_usage` materialized view

---

## Bulk Upload

### POST /api/v1/at/attachments/bulk-upload

Upload up to 10 files in one request.

**Request:** `multipart/form-data` with multiple `files` fields

**Response** `201 Created`
```json
{
  "uploaded": [
    { "id": "...", "original_filename": "file1.pdf", "upload_status": "committed" }
  ],
  "failed": [
    { "filename": "virus.exe", "error": "Content type not allowed: application/x-msdownload" }
  ],
  "total_uploaded": 2,
  "total_failed": 1
}
```

---

## Get Attachment

### GET /api/v1/at/attachments/{attachment_id}

Get metadata for a single attachment.

---

## Update Attachment

### PATCH /api/v1/at/attachments/{attachment_id}

Update the description. Author only.

**Request body**
```json
{ "description": "Updated description for this file" }
```

---

## Delete Attachment

### DELETE /api/v1/at/attachments/{attachment_id}

Soft-delete an attachment. The file remains in storage but is hidden from listings.
Author only (admin can delete any). Returns `204 No Content`.

---

## Get Download URL

### GET /api/v1/at/attachments/{attachment_id}/download

Generate a presigned download URL valid for 15 minutes. Requires `attachments.view` permission.

> **Blocked** if `virus_scan_status` is `infected`.

**Response** `200 OK`
```json
{
  "url": "https://s3.amazonaws.com/bucket/key?X-Amz-Signature=...",
  "expires_at": "2026-03-20T10:15:00Z",
  "original_filename": "risk_assessment_q1.pdf"
}
```

---

## Batch Attachment Counts

### GET /api/v1/at/attachments/counts

Get attachment counts for multiple entities — used for badge indicators.

**Query params**

| Param | Type | Description |
|-------|------|-------------|
| entity_type | string | e.g. `task`, `risk` |
| entity_ids | string | Comma-separated UUIDs (max 100) |

**Response** `200 OK`
```json
{
  "counts": {
    "<entity_id_1>": 3,
    "<entity_id_2>": 0
  }
}
```

---

## Storage Usage

### GET /api/v1/at/attachments/storage-usage

Get storage usage statistics for the current tenant.

**Response** `200 OK`
```json
{
  "tenant_key": "acme",
  "total_bytes": 10485760,
  "total_files": 42,
  "quota_bytes": 104857600,
  "quota_used_pct": 10.0
}
```

---

## Download History

### GET /api/v1/at/attachments/{attachment_id}/history

Get presigned URL generation history for an attachment (audit trail).

**Response** `200 OK`
```json
{
  "items": [
    {
      "id": "...",
      "requested_by": "...",
      "requested_at": "2026-03-20T10:00:00Z",
      "client_ip": "192.168.1.1"
    }
  ],
  "total": 5
}
```

---

## Storage Health (Admin)

### GET /api/v1/at/attachments/health

Check connectivity to the configured storage backend. Requires `admin.view` permission.

**Response** `200 OK`
```json
{
  "provider": "s3",
  "status": "healthy",
  "bucket": "kcontrol-attachments-prod",
  "latency_ms": 12,
  "checked_at": "2026-03-20T10:00:00Z"
}
```

---

## GDPR Delete (Admin)

### POST /api/v1/at/attachments/gdpr-delete

Soft-delete all attachments uploaded by a specific user. Requires platform admin.

**Request body**
```json
{ "user_id": "..." }
```

**Response** `200 OK` — `{ "deleted_count": 23 }`

---

## Permissions

| Permission | Required for |
|-----------|-------------|
| `attachments.view` | GET /attachments, GET /attachments/{id}/download |
| `attachments.create` | POST /attachments/upload, POST /attachments/bulk-upload |
| `attachments.delete` | DELETE /attachments/{id} |
| `admin.view` | GET /attachments/health |

---

## Storage Providers

Configured via `STORAGE_PROVIDER` env var:

| Value | Provider | Required env vars |
|-------|---------|-------------------|
| `s3` | AWS S3 | `S3_BUCKET`, `S3_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` |
| `gcs` | Google Cloud Storage | `GCS_BUCKET`, `GOOGLE_APPLICATION_CREDENTIALS` |
| `azure` | Azure Blob Storage | `AZURE_STORAGE_ACCOUNT`, `AZURE_STORAGE_KEY`, `AZURE_CONTAINER` |
| `minio` | MinIO (S3-compatible) | `MINIO_ENDPOINT`, `MINIO_BUCKET`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY` |

---

## Notes

- Files are **never returned** by the API. Clients receive presigned URLs and download directly from storage.
- **Virus scan polling:** After upload, poll `GET /attachments/{id}` every 10s until `virus_scan_status` is `clean` or `infected`.
- **Chunked reading:** Files >10MB are read in 1MB chunks server-side with incremental SHA-256 to prevent OOM.
- **Inline attachment links:** Attach a file to a comment by including its `id` in `CreateCommentRequest.attachment_ids`.
