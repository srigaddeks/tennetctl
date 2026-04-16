// ═══════════════════════════════════════════════════════════════════════════════
// ── Comments ─────────────────────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export interface ReactionSummary {
  reaction_code: string
  count: number
  user_ids: string[]
  reacted_by_me: boolean
}

export interface CommentEditRecord {
  id: string
  comment_id: string
  previous_content: string
  edited_by: string
  edited_at: string
}

export interface CommentRecord {
  id: string
  tenant_key: string
  entity_type: string
  entity_id: string
  parent_comment_id: string | null
  author_user_id: string
  author_display_name: string | null
  author_email: string | null
  content: string
  content_format: 'plain_text' | 'markdown'
  rendered_html: string | null
  visibility: 'internal' | 'external'
  is_edited: boolean
  is_deleted: boolean
  is_locked: boolean
  locked_by: string | null
  locked_at: string | null
  pinned: boolean
  resolved: boolean
  mention_user_ids: string[]
  reply_count: number
  attachment_ids: string[]
  replies: CommentRecord[]
  reactions: ReactionSummary[]
  author_grc_role_code: string | null
  author_is_external: boolean
  created_at: string
  updated_at: string
}

export interface CommentListResponse {
  items: CommentRecord[]
  total: number
  next_cursor: string | null
  unread_count: number
}

export interface CreateCommentRequest {
  entity_type: string
  entity_id: string
  content: string
  parent_comment_id?: string
  mention_user_ids?: string[]
  content_format?: 'plain_text' | 'markdown'
  visibility?: 'internal' | 'external'
  attachment_ids?: string[]
}

export interface UpdateCommentRequest {
  content: string
}

export interface AddReactionRequest {
  reaction_code: string
}
