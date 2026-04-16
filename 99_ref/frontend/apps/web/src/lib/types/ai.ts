export interface ConversationResponse {
  id: string
  tenant_key: string
  user_id: string
  org_id?: string | null
  workspace_id?: string | null
  agent_type_code: string
  title?: string | null
  page_context?: Record<string, unknown> | null
  is_archived: boolean
  created_at: string
  updated_at: string
}

export interface ConversationListResponse {
  items: ConversationResponse[]
  total: number
}

export interface CreateConversationRequest {
  agent_type_code?: string
  title?: string | null
  page_context?: Record<string, unknown> | null
  org_id?: string | null
  workspace_id?: string | null
}

export interface MessageResponse {
  id: string
  conversation_id: string
  role_code: "user" | "assistant" | "system"
  content: string
  token_count?: number | null
  model_id?: string | null
  created_at: string
}

export interface SendMessageRequest {
  content: string
  page_context?: Record<string, unknown> | null
}

// SSE event shapes
export interface SSEMessageStart { message_id: string }
export interface SSEContentDelta { delta: string }
export interface SSEToolCallStart {
  tool_name: string
  tool_category: "insight" | "navigation"
  input_summary: string
}
export interface SSEToolCallResult {
  tool_name: string
  is_successful: boolean
  output_summary: string
}
export interface SSESessionNamed {
  conversation_id: string
  title: string
}
export interface SSEMessageEnd {
  usage: { input_tokens: number; output_tokens: number; tool_calls: number }
}
export interface SSEError { message: string }
