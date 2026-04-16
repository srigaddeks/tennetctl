import { fetchWithAuth } from "./apiClient"
import type {
  AddViewRouteRequest,
  CreatePortalViewRequest,
  PortalViewListResponse,
  PortalViewResponse,
  RoleViewListResponse,
  UpdatePortalViewRequest,
  UserViewsResponse,
  ViewRouteResponse,
} from "../types/views"

/** Get all views available to the current user, scoped to the given org. */
export async function getMyViews(orgId?: string): Promise<UserViewsResponse> {
  const url = orgId
    ? `/api/v1/am/views/my-views?org_id=${encodeURIComponent(orgId)}`
    : "/api/v1/am/views/my-views"
  const res = await fetchWithAuth(url)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to load user views")
  return data as UserViewsResponse
}

/** List all portal views (admin). */
export async function listViews(): Promise<PortalViewListResponse> {
  const res = await fetchWithAuth("/api/v1/am/views")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list views")
  return data as PortalViewListResponse
}

/** List all role → view assignments. */
export async function listRoleViewAssignments(): Promise<RoleViewListResponse> {
  const res = await fetchWithAuth("/api/v1/am/views/role-assignments")
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list role-view assignments")
  return data as RoleViewListResponse
}

/** List views assigned to a specific role. */
export async function listRoleViews(roleId: string): Promise<RoleViewListResponse> {
  const res = await fetchWithAuth(`/api/v1/am/views/roles/${roleId}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.error?.message || "Failed to list role views")
  return data as RoleViewListResponse
}

/** Assign a view to a role. */
export async function assignViewToRole(roleId: string, viewCode: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/am/views/roles/${roleId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ view_code: viewCode }),
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error?.message || "Failed to assign view to role")
  }
}

/** Revoke a view from a role. */
export async function revokeViewFromRole(roleId: string, viewCode: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/am/views/roles/${roleId}/${viewCode}`, {
    method: "DELETE",
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error?.message || "Failed to revoke view from role")
  }
}

// ── View CRUD ─────────────────────────────────────────────────────────────────

export async function createView(payload: CreatePortalViewRequest): Promise<PortalViewResponse> {
  const res = await fetchWithAuth("/api/v1/am/views", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.error?.message || "Failed to create view")
  return data as PortalViewResponse
}

export async function updateView(code: string, payload: UpdatePortalViewRequest): Promise<PortalViewResponse> {
  const res = await fetchWithAuth(`/api/v1/am/views/${code}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.error?.message || "Failed to update view")
  return data as PortalViewResponse
}

export async function deleteView(code: string): Promise<void> {
  const res = await fetchWithAuth(`/api/v1/am/views/${code}`, { method: "DELETE" })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error?.message || "Failed to delete view")
  }
}

export async function addViewRoute(viewCode: string, payload: AddViewRouteRequest): Promise<ViewRouteResponse> {
  const res = await fetchWithAuth(`/api/v1/am/views/${viewCode}/routes`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.error?.message || "Failed to add route")
  return data as ViewRouteResponse
}

export async function removeViewRoute(viewCode: string, routePrefix: string): Promise<void> {
  // Strip leading slash for path param
  const safe = routePrefix.replace(/^\//, "")
  const res = await fetchWithAuth(`/api/v1/am/views/${viewCode}/routes/${safe}`, { method: "DELETE" })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error?.message || "Failed to remove route")
  }
}
