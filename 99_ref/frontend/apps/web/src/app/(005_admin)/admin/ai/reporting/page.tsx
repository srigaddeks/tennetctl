"use client"

import { useEffect, useState, useCallback } from "react"
import { BarChart3, Zap, MessageSquare, Bot, TrendingUp, RefreshCw, Loader2, Activity } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, Button } from "@kcontrol/ui"
import { getAIReportingSummary, listAgentRuns } from "@/lib/api/ai"

interface ReportingSummary {
  total_conversations: number
  total_messages: number
  total_tokens: number
  total_requests: number
  avg_tokens_per_conversation: number
  by_agent_type: Record<string, { conversations: number; tokens: number; requests: number }>
}

interface AgentRun {
  id: string
  agent_type_code: string
  status_code: string
  token_count: number | null
  created_at: string
  completed_at: string | null
}

function StatCard({ icon: Icon, color, label, value }: {
  icon: React.ElementType
  color: string
  label: string
  value: string | number
}) {
  return (
    <Card className="rounded-xl">
      <CardContent className="p-5 flex items-start gap-3">
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${color}`}>
          <Icon className="w-4 h-4" />
        </div>
        <div>
          <p className="text-2xl font-bold tabular-nums leading-none">{value}</p>
          <p className="text-xs text-muted-foreground mt-1">{label}</p>
        </div>
      </CardContent>
    </Card>
  )
}

const STATUS_COLORS: Record<string, string> = {
  completed: "text-emerald-400",
  running: "text-blue-400",
  failed: "text-red-400",
  cancelled: "text-muted-foreground",
}

export default function AIReportingPage() {
  const [summary, setSummary] = useState<ReportingSummary | null>(null)
  const [runs, setRuns] = useState<AgentRun[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingRuns, setLoadingRuns] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setLoadingRuns(true)
    try {
      const [summaryRes, runsRes] = await Promise.all([
        getAIReportingSummary().catch(() => null),
        listAgentRuns({ limit: 50 }).catch(() => ({ items: [] })),
      ])
      setSummary(summaryRes)
      setRuns(runsRes.items ?? [])
    } catch { /* ignore */ }
    finally { setLoading(false); setLoadingRuns(false) }
  }, [])

  useEffect(() => { load() }, [load])

  function formatDuration(run: AgentRun): string {
    if (!run.completed_at) return "—"
    const ms = new Date(run.completed_at).getTime() - new Date(run.created_at).getTime()
    if (ms < 1000) return `${ms}ms`
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
    return `${(ms / 60000).toFixed(1)}m`
  }

  return (
    <div className="max-w-5xl space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-emerald-500/15 flex items-center justify-center">
            <BarChart3 className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold">AI Usage & Reporting</h1>
            <p className="text-sm text-muted-foreground">Token consumption, agent runs, and conversation analytics.</p>
          </div>
        </div>
        <Button variant="ghost" size="sm" onClick={load} className="gap-1.5">
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh
        </Button>
      </div>

      {loading ? (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => <div key={i} className="h-24 rounded-xl bg-muted animate-pulse" />)}
        </div>
      ) : summary ? (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <StatCard icon={MessageSquare} color="bg-blue-500/10 text-blue-400" label="Conversations" value={summary.total_conversations.toLocaleString()} />
            <StatCard icon={Activity} color="bg-purple-500/10 text-purple-400" label="Messages" value={summary.total_messages?.toLocaleString() ?? "—"} />
            <StatCard icon={Zap} color="bg-amber-500/10 text-amber-400" label="Tokens Used" value={summary.total_tokens?.toLocaleString() ?? "—"} />
            <StatCard icon={TrendingUp} color="bg-emerald-500/10 text-emerald-400" label="Avg Tokens / Conv" value={Math.round(summary.avg_tokens_per_conversation ?? 0).toLocaleString()} />
          </div>

          {summary.by_agent_type && Object.keys(summary.by_agent_type).length > 0 && (
            <Card className="rounded-xl">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold flex items-center gap-2">
                  <Bot className="w-4 h-4 text-muted-foreground" />
                  By Agent Type
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border">
                      {["Agent Type", "Conversations", "Messages / Requests", "Tokens"].map(h => (
                        <th key={h} className="px-4 py-2.5 text-left text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(summary.by_agent_type).map(([type, stats]) => (
                      <tr key={type} className="border-b border-border/50 hover:bg-muted/20">
                        <td className="px-4 py-3 font-mono text-xs">{type}</td>
                        <td className="px-4 py-3 text-xs tabular-nums">{stats.conversations?.toLocaleString() ?? "—"}</td>
                        <td className="px-4 py-3 text-xs tabular-nums">{stats.requests?.toLocaleString() ?? "—"}</td>
                        <td className="px-4 py-3 text-xs tabular-nums">{stats.tokens?.toLocaleString() ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          )}
        </>
      ) : (
        <div className="rounded-xl border border-border bg-muted/20 px-5 py-8 text-center">
          <p className="text-sm text-muted-foreground">No reporting data available yet.</p>
        </div>
      )}

      {/* Recent Agent Runs */}
      <Card className="rounded-xl">
        <CardHeader className="pb-3 flex flex-row items-center justify-between">
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <Bot className="w-4 h-4 text-muted-foreground" />
            Recent Agent Runs
          </CardTitle>
          {loadingRuns && <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />}
        </CardHeader>
        <CardContent className="p-0">
          {runs.length === 0 ? (
            <div className="px-4 py-8 text-center text-sm text-muted-foreground">No agent runs recorded yet.</div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  {["Agent", "Status", "Tokens", "Duration", "Started"].map(h => (
                    <th key={h} className="px-4 py-2.5 text-left text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {runs.map(run => (
                  <tr key={run.id} className="border-b border-border/50 hover:bg-muted/20">
                    <td className="px-4 py-3 font-mono text-xs">{run.agent_type_code}</td>
                    <td className="px-4 py-3 text-xs">
                      <span className={`font-semibold ${STATUS_COLORS[run.status_code] ?? "text-muted-foreground"}`}>
                        {run.status_code}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs tabular-nums">{run.token_count?.toLocaleString() ?? "—"}</td>
                    <td className="px-4 py-3 text-xs tabular-nums">{formatDuration(run)}</td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">{new Date(run.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
