import { fetchWithAuth } from "./apiClient"

export interface TestStats {
  pass_rate: number
  total_tests: number
  failing_tests: number
}

export interface TaskForecast {
  overdue: number
  due_this_week: number
  total_pending: number
}

export interface FrameworkStatus {
  id: string
  name: string
  completion_percentage: number
}

export interface GrcDashboardResponse {
  trust_score: number
  test_stats: TestStats
  task_forecast: TaskForecast
  framework_status: FrameworkStatus[]
  recent_activity: any[]
}

export interface EngineerDashboardResponse {
  owned_controls_count: number
  pending_tasks_count: number
  tasks_by_status: Record<string, number>
  upcoming_deadlines: any[]
}

export interface AuditorDashboardResponse {
  active_engagements_count: number
  pending_reviews_count: number
  total_pending_requests: number
  total_verified_controls: number
  engagements: any[]
  review_queue: any[]
}

export interface Milestone {
  id: string
  title: string
  date: string
  status: string
}

export interface PortfolioEngagement {
  id: string
  name: string
  progress: number
  risk_level: string
  status: string
}

export interface ExecutiveDashboardResponse {
  trust_score: number
  controls_verified_percentage: number
  pending_findings_count: number
  audit_status: string
  portfolio: PortfolioEngagement[]
  milestones: Milestone[]
}

export const dashboardApi = {
  getGrc: async (orgId?: string, engagementId?: string): Promise<GrcDashboardResponse> => {
    const params = new URLSearchParams()
    if (orgId) params.append("org_id", orgId)
    if (engagementId) params.append("engagement_id", engagementId)
    
    const url = `/api/v1/grc/dashboard${params.toString() ? '?' + params.toString() : ''}`
    const res = await fetchWithAuth(url)
    if (!res.ok) throw new Error(`GRC Dashboard fetch failed: ${res.statusText}`)
    return res.json()
  },

  getEngineer: async (orgId?: string): Promise<EngineerDashboardResponse> => {
    const url = orgId ? `/api/v1/grc/engineer/dashboard?org_id=${orgId}` : "/api/v1/grc/engineer/dashboard"
    const res = await fetchWithAuth(url)
    if (!res.ok) throw new Error(`Engineer Dashboard fetch failed: ${res.statusText}`)
    return res.json()
  },

  getAuditor: async (orgId?: string): Promise<AuditorDashboardResponse> => {
    const url = orgId ? `/api/v1/engagements/dashboard?org_id=${orgId}` : "/api/v1/engagements/dashboard"
    const res = await fetchWithAuth(url)
    if (!res.ok) throw new Error(`Auditor Dashboard fetch failed: ${res.statusText}`)
    return res.json()
  },

  getExecutive: async (orgId?: string): Promise<ExecutiveDashboardResponse> => {
    const url = orgId ? `/api/v1/grc/executive/dashboard?org_id=${orgId}` : "/api/v1/grc/executive/dashboard"
    const res = await fetchWithAuth(url)
    if (!res.ok) throw new Error(`Executive Dashboard fetch failed: ${res.statusText}`)
    return res.json()
  },
}
