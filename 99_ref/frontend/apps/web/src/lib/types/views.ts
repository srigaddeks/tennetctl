export interface ViewRouteResponse {
  view_code: string
  route_prefix: string
  is_read_only: boolean
  sort_order: number
  sidebar_label: string | null
  sidebar_icon: string | null
  sidebar_section: string | null
}

export interface PortalViewResponse {
  code: string
  name: string
  description: string | null
  color: string | null
  icon: string | null
  sort_order: number
  is_active: boolean
  default_route: string | null
  routes: ViewRouteResponse[]
}

export interface PortalViewListResponse {
  views: PortalViewResponse[]
}

export interface RoleViewAssignment {
  role_id: string
  view_code: string
}

export interface RoleViewListResponse {
  assignments: RoleViewAssignment[]
}

export interface UserViewsResponse {
  views: PortalViewResponse[]
}

// ── CRUD request types ────────────────────────────────────────────────────────

export interface CreatePortalViewRequest {
  code: string
  name: string
  description?: string | null
  color?: string | null
  icon?: string | null
  sort_order?: number
  default_route?: string | null
}

export interface UpdatePortalViewRequest {
  name?: string | null
  description?: string | null
  color?: string | null
  icon?: string | null
  sort_order?: number | null
  is_active?: boolean | null
  default_route?: string | null
}

export interface AddViewRouteRequest {
  route_prefix: string
  is_read_only?: boolean
  sort_order?: number
  sidebar_label?: string | null
  sidebar_icon?: string | null
  sidebar_section?: string | null
}
