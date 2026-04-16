"use client"

import { useEffect, useState, useCallback, useRef } from "react"
import type { SidebarBadgeCounts } from "@kcontrol/ui"
import { listFrameworks, getRiskSummary, getTaskSummary, listPromotedTests } from "@/lib/api/grc"
import { listAdminTickets, listMyTickets } from "@/lib/api/feedback"
import { getUnreadNotificationCount } from "@/lib/api/notifications"
import { useAccess } from "@/components/providers/AccessProvider"

/**
 * Fetches real badge counts for sidebar navigation items.
 * Uses summary endpoints where available, falls back to list totals.
 * Re-fetches when orgId changes.
 */
export function useSidebarCounts(orgId?: string, enabled = true, workspaceId?: string): SidebarBadgeCounts {
  const { hasPlatformAction } = useAccess()
  const [counts, setCounts] = useState<SidebarBadgeCounts>({
    complianceScore: 0,
    compliancePassingCount: 0,
    complianceTotalCount: 0,
  })
  const unreadIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Poll unread notification count every 30 seconds independently
  useEffect(() => {
    if (!enabled) return
    const pollUnread = async () => {
      const count = await getUnreadNotificationCount()
      setCounts((prev) => ({ ...prev, unreadNotifications: count }))
    }
    pollUnread()
    unreadIntervalRef.current = setInterval(pollUnread, 300_000)
    return () => {
      if (unreadIntervalRef.current) clearInterval(unreadIntervalRef.current)
    }
  }, [enabled])

  const fetchCounts = useCallback(async () => {
    if (!enabled) return
    const results: SidebarBadgeCounts = {}

    // Fire all requests in parallel — each is independent and non-blocking
    const [frameworksRes, testsRes, riskRes, taskRes, feedbackRes] = await Promise.allSettled([
      listFrameworks(orgId ? { scope_org_id: orgId, ...(workspaceId ? { scope_workspace_id: workspaceId } : {}) } : undefined),
      orgId ? listPromotedTests({ orgId, ...(workspaceId ? { workspaceId } : {}), limit: 1, offset: 0 }) : Promise.resolve({ total: 0, items: [] }),
      getRiskSummary(orgId, workspaceId),
      getTaskSummary(orgId, workspaceId),
      (hasPlatformAction("feedback.assign")
        ? listAdminTickets({ limit: 1, offset: 0 })
        : listMyTickets({ limit: 1, offset: 0 })
      ).catch(() => ({ total: 0 })),
    ])

    // Frameworks + controls
    if (frameworksRes.status === "fulfilled") {
      const fw = frameworksRes.value
      results.frameworks = fw.total ?? fw.items?.length ?? 0

      // Sum control counts across frameworks
      let totalControls = 0
      for (const f of fw.items ?? []) {
        totalControls += f.control_count ?? 0
      }
      results.controls = totalControls
      results.complianceTotalCount = totalControls
      // Use risk/task data to derive a basic compliance posture score
      // Score = % of controls that exist (have tests coverage mapped)
      // This is a placeholder — real compliance scoring comes from test execution results
    }

    // Tests
    if (testsRes.status === "fulfilled") {
      const testTotal = testsRes.value.total ?? 0
      results.controlTests = testTotal
      // Compliance score: % of controls covered by at least one test
      if (results.controls && results.controls > 0) {
        const covered = Math.min(testTotal, results.controls)
        results.compliancePassingCount = covered
        results.complianceScore = Math.round((covered / results.controls) * 100)
      }
    }

    // Risks (use summary endpoint)
    if (riskRes.status === "fulfilled") {
      const risk = riskRes.value
      results.risks = risk.total_risks ?? 0
      results.openRisks = risk.open_count ?? 0
      results.criticalRisks = risk.critical_count ?? 0
    }

    // Tasks (use summary endpoint)
    if (taskRes.status === "fulfilled") {
      const task = taskRes.value
      results.openTasks = task.open_count + task.in_progress_count
      results.overdueTasks = task.overdue_count ?? 0
      results.tasks = results.openTasks
    }

    // Feedback tickets (admin only — fails silently for non-admins)
    if (feedbackRes.status === "fulfilled") {
      const fb = feedbackRes.value as { total?: number }
      results.feedbackTickets = fb.total ?? 0
    }

    setCounts(results)
  }, [orgId, workspaceId, enabled, hasPlatformAction])

  useEffect(() => {
    fetchCounts()
  }, [fetchCounts])

  return counts
}
