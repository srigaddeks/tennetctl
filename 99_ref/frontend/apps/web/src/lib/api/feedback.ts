import { fetchWithAuth } from "./apiClient"

// ═══════════════════════════════════════════════════════════════════════════════
// ── Types ────────────────────────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export interface TicketTypeDimResponse {
  code: string
  name: string
  description: string | null
  icon_name: string | null
  sort_order: number
  is_active: boolean
}

export interface TicketStatusDimResponse {
  code: string
  name: string
  description: string | null
  is_terminal: boolean
  sort_order: number
}

export interface TicketPriorityDimResponse {
  code: string
  name: string
  description: string | null
  numeric_level: number
  sort_order: number
}

export interface TicketDimensionsResponse {
  ticket_types: TicketTypeDimResponse[]
  ticket_statuses: TicketStatusDimResponse[]
  ticket_priorities: TicketPriorityDimResponse[]
}

export interface AssignmentResponse {
  assigned_to: string
  assigned_by: string
  assigned_at: string
}

export interface TicketResponse {
  id: string
  tenant_key: string
  submitted_by: string
  ticket_type_code: string
  status_code: string
  priority_code: string
  org_id: string | null
  workspace_id: string | null
  title: string | null
  description: string | null
  context_url: string | null
  browser_info: string | null
  steps_to_reproduce: string | null
  expected_behavior: string | null
  actual_behavior: string | null
  version_info: string | null
  admin_note: string | null
  submitter_email: string | null
  submitter_display_name: string | null
  active_assignments: AssignmentResponse[]
  created_at: string
  updated_at: string
  resolved_at: string | null
}

export interface TicketListResponse {
  items: TicketResponse[]
  total: number
}

export interface TicketEventResponse {
  id: string
  ticket_id: string
  event_type: string
  actor_id: string
  occurred_at: string
  old_value: string | null
  new_value: string | null
  note: string | null
}

export interface TicketEventsResponse {
  items: TicketEventResponse[]
  total: number
}

export interface CreateTicketRequest {
  ticket_type_code: string
  priority_code?: string
  title: string
  description: string
  context_url?: string | null
  browser_info?: string | null
  steps_to_reproduce?: string | null
  expected_behavior?: string | null
  actual_behavior?: string | null
  version_info?: string | null
  org_id?: string | null
  workspace_id?: string | null
}

export interface UpdateTicketRequest {
  title?: string | null
  description?: string | null
  context_url?: string | null
  browser_info?: string | null
  priority_code?: string | null
}

export interface UpdateTicketStatusRequest {
  status_code: string
  note?: string | null
}

export interface AssignTicketRequest {
  assigned_to: string
  note?: string | null
}

export interface AdminUpdateRequest {
  status_code?: string | null
  priority_code?: string | null
  admin_note?: string | null
}

// ═══════════════════════════════════════════════════════════════════════════════
// ── API calls ────────────────────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════════

export async function getFeedbackDimensions(): Promise<TicketDimensionsResponse> {
  const res = await fetchWithAuth("/api/v1/fb/dimensions", { method: "GET" })
  if (!res.ok) throw new Error(`Failed to load feedback dimensions: ${res.status}`)
  return res.json()
}

export async function listMyTickets(params?: {
  status_code?: string
  ticket_type_code?: string
  limit?: number
  offset?: number
}): Promise<TicketListResponse> {
  const q = new URLSearchParams()
  if (params?.status_code) q.set("status_code", params.status_code)
  if (params?.ticket_type_code) q.set("ticket_type_code", params.ticket_type_code)
  if (params?.limit !== undefined) q.set("limit", String(params.limit))
  if (params?.offset !== undefined) q.set("offset", String(params.offset))
  const qs = q.toString() ? `?${q}` : ""
  const res = await fetchWithAuth(`/api/v1/fb/tickets${qs}`, { method: "GET" })
  if (!res.ok) throw new Error(`Failed to list tickets: ${res.status}`)
  return res.json()
}

export async function getTicket(ticketId: string): Promise<TicketResponse> {
  const res = await fetchWithAuth(`/api/v1/fb/tickets/${ticketId}`, { method: "GET" })
  if (!res.ok) throw new Error(`Failed to get ticket: ${res.status}`)
  return res.json()
}

export async function createTicket(body: CreateTicketRequest): Promise<TicketResponse> {
  const res = await fetchWithAuth("/api/v1/fb/tickets", {
    method: "POST",
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`Failed to create ticket: ${res.status}`)
  return res.json()
}

export async function updateTicket(ticketId: string, body: UpdateTicketRequest): Promise<TicketResponse> {
  const res = await fetchWithAuth(`/api/v1/fb/tickets/${ticketId}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`Failed to update ticket: ${res.status}`)
  return res.json()
}

export async function deleteTicket(ticketId: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/fb/tickets/${ticketId}`, { method: "DELETE" })
  if (!res.ok) throw new Error(`Failed to delete ticket: ${res.status}`)
}

export async function getTicketEvents(ticketId: string): Promise<TicketEventsResponse> {
  const res = await fetchWithAuth(`/api/v1/fb/tickets/${ticketId}/events`, { method: "GET" })
  if (!res.ok) throw new Error(`Failed to get ticket events: ${res.status}`)
  return res.json()
}

// ── Admin endpoints ──────────────────────────────────────────────────────────

export async function listAdminTickets(params?: {
  status_code?: string
  ticket_type_code?: string
  priority_code?: string
  submitted_by?: string
  limit?: number
  offset?: number
}): Promise<TicketListResponse> {
  const q = new URLSearchParams()
  if (params?.status_code) q.set("status_code", params.status_code)
  if (params?.ticket_type_code) q.set("ticket_type_code", params.ticket_type_code)
  if (params?.priority_code) q.set("priority_code", params.priority_code)
  if (params?.submitted_by) q.set("submitted_by", params.submitted_by)
  if (params?.limit !== undefined) q.set("limit", String(params.limit))
  if (params?.offset !== undefined) q.set("offset", String(params.offset))
  const qs = q.toString() ? `?${q}` : ""
  const res = await fetchWithAuth(`/api/v1/fb/admin/tickets${qs}`, { method: "GET" })
  if (!res.ok) throw new Error(`Failed to list admin tickets: ${res.status}`)
  return res.json()
}

export async function adminUpdateTicketStatus(
  ticketId: string,
  body: UpdateTicketStatusRequest
): Promise<TicketResponse> {
  const res = await fetchWithAuth(`/api/v1/fb/admin/tickets/${ticketId}/status`, {
    method: "PATCH",
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`Failed to update ticket status: ${res.status}`)
  return res.json()
}

export async function adminUpdateTicket(
  ticketId: string,
  body: AdminUpdateRequest
): Promise<TicketResponse> {
  const res = await fetchWithAuth(`/api/v1/fb/admin/tickets/${ticketId}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`Failed to admin update ticket: ${res.status}`)
  return res.json()
}

export async function adminAssignTicket(
  ticketId: string,
  body: AssignTicketRequest
): Promise<TicketResponse> {
  const res = await fetchWithAuth(`/api/v1/fb/admin/tickets/${ticketId}/assign`, {
    method: "POST",
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`Failed to assign ticket: ${res.status}`)
  return res.json()
}

export async function adminUnassignTicket(
  ticketId: string,
  userId: string
): Promise<TicketResponse> {
  const res = await fetchWithAuth(`/api/v1/fb/admin/tickets/${ticketId}/assign/${userId}`, {
    method: "DELETE",
  })
  if (!res.ok) throw new Error(`Failed to unassign ticket: ${res.status}`)
  return res.json()
}
