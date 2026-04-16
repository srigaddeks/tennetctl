"use client"

import { useEffect, useState, useCallback } from "react"
import {
  Button,
  Input,
} from "@kcontrol/ui"
import {
  ClipboardCheck,
  Search,
  RefreshCw,
  Lock,
  Unlock,
  AlertTriangle,
  CheckCircle2,
  Clock,
} from "lucide-react"
import {
  listAssessments,
  listAssessmentTypes,
  listAssessmentStatuses,
  getAssessmentSummary,
} from "@/lib/api/assessments"
import type { AssessmentResponse, AssessmentDimension, AssessmentSummaryResponse } from "@/lib/types/assessments"

const STATUS_META: Record<string, { label: string; color: string }> = {
  planned:     { label: "Planned",     color: "text-muted-foreground bg-muted border-border" },
  in_progress: { label: "In Progress", color: "text-blue-600 bg-blue-500/10 border-blue-500/20" },
  review:      { label: "Review",      color: "text-yellow-600 bg-yellow-500/10 border-yellow-500/20" },
  completed:   { label: "Completed",   color: "text-emerald-600 bg-emerald-500/10 border-emerald-500/20" },
  cancelled:   { label: "Cancelled",   color: "text-slate-500 bg-slate-500/10 border-slate-500/20" },
}

function StatusBadge({ code }: { code: string }) {
  const m = STATUS_META[code] || { label: code, color: "text-muted-foreground bg-muted border-border" }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${m.color}`}>
      {m.label}
    </span>
  )
}

export default function AdminAssessmentsPage() {
  const [allAssessments, setAllAssessments] = useState<AssessmentResponse[]>([])
  const [types, setTypes] = useState<AssessmentDimension[]>([])
  const [statuses, setStatuses] = useState<AssessmentDimension[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const [filterStatus, setFilterStatus] = useState("")
  const [filterType, setFilterType] = useState("")
  const [orgFilter, setOrgFilter] = useState("")

  // For admin view, we try to load across a platform org
  // In real usage the admin would pick an org — here we just show a notice
  const [summaries, setSummaries] = useState<Record<string, AssessmentSummaryResponse>>({})

  useEffect(() => {
    async function loadDims() {
      try {
        const [t, s] = await Promise.all([listAssessmentTypes(), listAssessmentStatuses()])
        setTypes(t)
        setStatuses(s)
      } catch {}
    }
    loadDims()
  }, [])

  const loadData = useCallback(async () => {
    if (!orgFilter) return
    setLoading(true)
    setError(null)
    try {
      const res = await listAssessments(orgFilter, {
        type_code: filterType || undefined,
        status: filterStatus || undefined,
        limit: 100,
      })
      setAllAssessments(res.items)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load assessments")
    } finally {
      setLoading(false)
    }
  }, [orgFilter, filterType, filterStatus])

  useEffect(() => {
    loadData()
  }, [loadData])

  const filtered = allAssessments.filter(a =>
    !search ||
    (a.name ?? "").toLowerCase().includes(search.toLowerCase()) ||
    (a.assessment_type_name ?? "").toLowerCase().includes(search.toLowerCase())
  )

  // Counts
  const totalFindings = allAssessments.reduce((s, a) => s + a.finding_count, 0)
  const openFindings = 0
  const completedCount = allAssessments.filter(a => a.assessment_status_code === "completed").length
  const inProgressCount = allAssessments.filter(a => a.assessment_status_code === "in_progress").length

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <ClipboardCheck className="h-6 w-6 text-primary" />
          <div>
            <h1 className="text-xl font-semibold">Assessments</h1>
            <p className="text-sm text-muted-foreground">Platform-wide assessment and gap analysis management</p>
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={loadData} disabled={loading || !orgFilter}>
          <RefreshCw className={`h-4 w-4 mr-1 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {/* Org filter */}
      <div className="flex items-center gap-2">
        <Input
          className="max-w-xs h-8 text-sm"
          placeholder="Enter Org ID to view assessments..."
          value={orgFilter}
          onChange={e => setOrgFilter(e.target.value)}
        />
        <span className="text-xs text-muted-foreground">Org ID required to query assessments</span>
      </div>

      {/* KPI row */}
      {allAssessments.length > 0 && (
        <div className="grid grid-cols-4 gap-4">
          {[
            { label: "Total Assessments", value: allAssessments.length, icon: ClipboardCheck, color: "text-primary" },
            { label: "In Progress",       value: inProgressCount,       icon: Clock,          color: "text-blue-600" },
            { label: "Completed",         value: completedCount,        icon: CheckCircle2,   color: "text-emerald-600" },
            { label: "Open Findings",     value: openFindings,          icon: AlertTriangle,  color: "text-red-600" },
          ].map(({ label, value, icon: Icon, color }) => (
            <div key={label} className="rounded-lg border border-border bg-card p-4">
              <div className="flex items-center gap-2 mb-1">
                <Icon className={`h-4 w-4 ${color}`} />
                <span className="text-xs text-muted-foreground">{label}</span>
              </div>
              <div className={`text-2xl font-bold ${color}`}>{value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-2">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input className="pl-8 h-8 text-sm" placeholder="Search..." value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <select className="h-8 rounded-md border border-input bg-background px-2 text-sm" value={filterType} onChange={e => setFilterType(e.target.value)}>
          <option value="">All Types</option>
          {types.map(t => <option key={t.code} value={t.code}>{t.name}</option>)}
        </select>
        <select className="h-8 rounded-md border border-input bg-background px-2 text-sm" value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
          <option value="">All Statuses</option>
          {statuses.map(s => <option key={s.code} value={s.code}>{s.name}</option>)}
        </select>
      </div>

      {error && <div className="p-3 rounded-md bg-destructive/10 text-destructive text-sm">{error}</div>}

      {!orgFilter ? (
        <div className="flex flex-col items-center justify-center h-48 text-muted-foreground">
          <ClipboardCheck className="h-12 w-12 mb-3 opacity-20" />
          <p>Enter an Org ID above to view assessments</p>
        </div>
      ) : loading ? (
        <div className="space-y-2">
          {[...Array(3)].map((_, i) => <div key={i} className="h-14 rounded-lg bg-muted animate-pulse" />)}
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-48 text-muted-foreground">
          <ClipboardCheck className="h-12 w-12 mb-3 opacity-20" />
          <p>No assessments found</p>
        </div>
      ) : (
        <div className="rounded-lg border border-border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Title</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Type</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Status</th>
                <th className="px-4 py-2 text-right font-medium text-muted-foreground">Findings</th>
                <th className="px-4 py-2 text-right font-medium text-muted-foreground">Open</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Locked</th>
                <th className="px-4 py-2 text-left font-medium text-muted-foreground">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filtered.map(a => (
                <tr key={a.id} className="hover:bg-muted/30">
                  <td className="px-4 py-2 font-medium">{a.name ?? a.assessment_code}</td>
                  <td className="px-4 py-2 text-muted-foreground">{a.assessment_type_name}</td>
                  <td className="px-4 py-2"><StatusBadge code={a.assessment_status_code} /></td>
                  <td className="px-4 py-2 text-right">{a.finding_count}</td>
                  <td className="px-4 py-2 text-right">
                    <span className="text-muted-foreground">—</span>
                  </td>
                  <td className="px-4 py-2">
                    {a.is_locked
                      ? <Lock className="h-3.5 w-3.5 text-muted-foreground" />
                      : <Unlock className="h-3.5 w-3.5 text-muted-foreground" />
                    }
                  </td>
                  <td className="px-4 py-2 text-muted-foreground text-xs">
                    {new Date(a.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
