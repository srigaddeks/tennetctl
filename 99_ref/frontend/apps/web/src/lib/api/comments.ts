import { fetchWithAuth } from "./apiClient"
import type {
  CommentRecord,
  CommentListResponse,
  CommentEditRecord,
  CreateCommentRequest,
  UpdateCommentRequest,
  ReactionSummary,
} from "../types/comments"

type RawCommentRecord = Partial<CommentRecord> & Record<string, unknown>

function normalizeComment(comment: RawCommentRecord): CommentRecord {
  return {
    ...(comment as CommentRecord),
    mention_user_ids: Array.isArray(comment.mention_user_ids) ? comment.mention_user_ids : [],
    attachment_ids: Array.isArray(comment.attachment_ids) ? comment.attachment_ids : [],
    reactions: Array.isArray(comment.reactions) ? comment.reactions : [],
    replies: Array.isArray(comment.replies)
      ? comment.replies.map((reply) => normalizeComment(reply as RawCommentRecord))
      : [],
  }
}

function normalizeCommentListResponse(data: CommentListResponse): CommentListResponse {
  return {
    ...data,
    items: Array.isArray(data.items) ? data.items.map((item) => normalizeComment(item as RawCommentRecord)) : [],
    total: typeof data.total === "number" ? data.total : 0,
    next_cursor: data.next_cursor ?? null,
    unread_count: typeof data.unread_count === "number" ? data.unread_count : 0,
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── Comments (/api/v1/cm/comments) ───────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export async function listComments(
  entityType: string,
  entityId: string,
  page = 1,
  perPage = 25,
  sort?: "newest" | "oldest",
  visibility?: "internal" | "external",
): Promise<CommentListResponse> {
  const params = new URLSearchParams({
    entity_type: entityType,
    entity_id: entityId,
    page: String(page),
    per_page: String(perPage),
  })
  if (sort) params.set("sort", sort === "newest" ? "desc" : "asc")
  if (visibility) params.set("visibility", visibility)
  const res = await fetchWithAuth(`/api/v1/cm/comments?${params}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to list comments")
  return normalizeCommentListResponse(data as CommentListResponse)
}

export async function getComment(commentId: string): Promise<CommentRecord> {
  const res = await fetchWithAuth(`/api/v1/cm/comments/${commentId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to get comment")
  return normalizeComment(data as RawCommentRecord)
}

export async function createComment(payload: CreateCommentRequest): Promise<CommentRecord> {
  const res = await fetchWithAuth("/api/v1/cm/comments", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to create comment")
  return normalizeComment(data as RawCommentRecord)
}

export async function updateComment(commentId: string, payload: UpdateCommentRequest): Promise<CommentRecord> {
  const res = await fetchWithAuth(`/api/v1/cm/comments/${commentId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to update comment")
  return normalizeComment(data as RawCommentRecord)
}

export async function deleteComment(commentId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/cm/comments/${commentId}`, {
    method: "DELETE",
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error?.message || data.detail || "Failed to delete comment")
  }
}

export async function pinComment(commentId: string): Promise<CommentRecord> {
  const res = await fetchWithAuth(`/api/v1/cm/comments/${commentId}/pin`, {
    method: "POST",
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to pin comment")
  return normalizeComment(data as RawCommentRecord)
}

export async function unpinComment(commentId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/cm/comments/${commentId}/pin`, {
    method: "DELETE",
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error?.message || data.detail || "Failed to unpin comment")
  }
}

export async function resolveComment(commentId: string): Promise<CommentRecord> {
  const res = await fetchWithAuth(`/api/v1/cm/comments/${commentId}/resolve`, {
    method: "POST",
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to resolve comment")
  return normalizeComment(data as RawCommentRecord)
}

export async function unresolveComment(commentId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/cm/comments/${commentId}/resolve`, {
    method: "DELETE",
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error?.message || data.detail || "Failed to unresolve comment")
  }
}

export async function getCommentHistory(commentId: string): Promise<CommentEditRecord[]> {
  const res = await fetchWithAuth(`/api/v1/cm/comments/${commentId}/history`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to get comment history")
  return data as CommentEditRecord[]
}

export async function addReaction(commentId: string, reactionCode: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/cm/comments/${commentId}/reactions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reaction_code: reactionCode }),
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error?.message || data.detail || "Failed to add reaction")
  }
}

export async function removeReaction(commentId: string, reactionCode: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/cm/comments/${commentId}/reactions/${reactionCode}`, {
    method: "DELETE",
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error?.message || data.detail || "Failed to remove reaction")
  }
}

export async function getCommentCount(entityType: string, entityId: string): Promise<number> {
  const res = await listComments(entityType, entityId, 1, 1)
  return res.total
}

export async function getReactions(commentId: string): Promise<ReactionSummary[]> {
  const res = await fetchWithAuth(`/api/v1/cm/comments/${commentId}/reactions`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to get reactions")
  return data as ReactionSummary[]
}

export async function listMentions(
  page: number = 1,
  perPage: number = 20,
): Promise<CommentListResponse> {
  const params = new URLSearchParams({ page: String(page), per_page: String(perPage) })
  const res = await fetchWithAuth(`/api/v1/cm/comments/mentions?${params}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to list mentions")
  return normalizeCommentListResponse(data as CommentListResponse)
}

export async function markCommentsRead(
  entityType: string,
  entityId: string,
): Promise<{ marked_at: string }> {
  const res = await fetchWithAuth(`/api/v1/cm/comments/mark-read`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ entity_type: entityType, entity_id: entityId }),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to mark comments as read")
  return data as { marked_at: string }
}

export async function adminDeleteComment(commentId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/cm/comments/${commentId}/admin`, {
    method: "DELETE",
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error?.message || data.detail || "Failed to delete comment")
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── GDPR Admin (/api/v1/cm/comments/admin) ──────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export interface GdprUserCommentsPreview {
  user_id: string
  total: number
  items: Array<{
    id: string
    entity_type: string
    entity_id: string
    content: string
    created_at: string
  }>
}

export interface GdprCommentDeleteResult {
  comments_anonymized: number
  reactions_deleted: number
  user_id: string
}

export async function gdprPreviewUserComments(userId: string): Promise<GdprUserCommentsPreview> {
  const res = await fetchWithAuth(`/api/v1/cm/comments/admin/users/${userId}/comments`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to preview user comments")
  return data as GdprUserCommentsPreview
}

export async function gdprDeleteUserComments(userId: string): Promise<GdprCommentDeleteResult> {
  const res = await fetchWithAuth(`/api/v1/cm/comments/admin/users/${userId}/data`, {
    method: "DELETE",
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || data.detail || "Failed to delete user comment data")
  return data as GdprCommentDeleteResult
}
