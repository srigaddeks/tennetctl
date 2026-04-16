"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Sparkles, Brain, FileCode2, MessageSquare, BarChart3, ArrowRight, Loader2, Zap, Users2, ListTodo, FileType, FlaskConical } from "lucide-react"
import { listAgentConfigs, listPromptTemplates, listAllApprovals, getAIReportingSummary, adminGetQueueDepth } from "@/lib/api/ai"

interface AIStats {
  agentConfigCount: number
  activeAgentCount: number
  promptCount: number
  pendingApprovals: number
  totalConversations: number
  totalTokensUsed: number
  totalRequests: number
  queuedJobs: number
  runningJobs: number
}

export default function AIAdminOverviewPage() {
  const [stats, setStats] = useState<AIStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const [agentsRes, promptsRes, approvalsRes, reportRes, depthRes] = await Promise.all([
          listAgentConfigs().catch(() => ({ items: [] })),
          listPromptTemplates().catch(() => ({ items: [] })),
          listAllApprovals({ status_code: "pending" }).catch(() => ({ items: [], total: 0 })),
          getAIReportingSummary().catch(() => null),
          adminGetQueueDepth().catch(() => []),
        ])
        const queuedJobs  = depthRes.filter((d: { status_code: string }) => d.status_code === "queued").reduce((s: number, d: { job_count: number }) => s + d.job_count, 0)
        const runningJobs = depthRes.filter((d: { status_code: string }) => d.status_code === "running").reduce((s: number, d: { job_count: number }) => s + d.job_count, 0)
        setStats({
          agentConfigCount: agentsRes.items.length,
          activeAgentCount: agentsRes.items.filter((a: { is_active: boolean }) => a.is_active).length,
          promptCount: promptsRes.items.length,
          pendingApprovals: approvalsRes.total ?? approvalsRes.items.length,
          totalConversations: reportRes?.total_conversations ?? 0,
          totalTokensUsed: reportRes?.total_tokens ?? 0,
          totalRequests: reportRes?.total_requests ?? 0,
          queuedJobs,
          runningJobs,
        })
      } catch { /* non-blocking */ }
      finally { setLoading(false) }
    }
    load()
  }, [])

  const cards = [
    {
      icon: Brain,
      color: "text-purple-400",
      bg: "bg-purple-500/10",
      border: "border-l-purple-500",
      title: "Agent Configs",
      description: "Configure LLM providers, models, temperature, and token limits per agent type.",
      href: "/admin/ai/agent-configs",
      stat: stats ? `${stats.activeAgentCount}/${stats.agentConfigCount} active` : null,
      highlight: false,
    },
    {
      icon: FileCode2,
      color: "text-blue-400",
      bg: "bg-blue-500/10",
      border: "border-l-blue-500",
      title: "Prompt Templates",
      description: "Manage system prompts for each agent. Variable substitution with {{var}} syntax.",
      href: "/admin/ai/prompts",
      stat: stats ? `${stats.promptCount} templates` : null,
      highlight: false,
    },
    {
      icon: MessageSquare,
      color: "text-amber-400",
      bg: "bg-amber-500/10",
      border: "border-l-amber-500",
      title: "Approval Requests",
      description: "Review pending write operations requested by AI agents on behalf of users.",
      href: "/admin/ai/approvals",
      stat: stats ? `${stats.pendingApprovals} pending` : null,
      highlight: (stats?.pendingApprovals ?? 0) > 0,
    },
    {
      icon: BarChart3,
      color: "text-emerald-400",
      bg: "bg-emerald-500/10",
      border: "border-l-emerald-500",
      title: "Usage & Reporting",
      description: "Token consumption, cost estimates, per-agent metrics, and conversation analytics.",
      href: "/admin/ai/reporting",
      stat: stats ? `${stats.totalConversations} conversations` : null,
      highlight: false,
    },
    {
      icon: ListTodo,
      color: "text-blue-400",
      bg: "bg-blue-500/10",
      border: "border-l-blue-500",
      title: "Job Queue",
      description: "Monitor background AI jobs, pipeline chain status, cancellations, and live queue depth.",
      href: "/admin/ai/jobs",
      stat: stats ? `${stats.runningJobs} running · ${stats.queuedJobs} queued` : null,
      highlight: (stats?.runningJobs ?? 0) > 0 || (stats?.queuedJobs ?? 0) > 0,
    },
    {
      icon: FileType,
      color: "text-indigo-400",
      bg: "bg-indigo-500/10",
      border: "border-l-indigo-500",
      title: "PDF Templates",
      description: "Define branded PDF templates for report exports — custom colours, cover styles, and PDF shell uploads.",
      href: "/admin/ai/pdf-templates",
      stat: null,
      highlight: false,
    },
    {
      icon: FlaskConical,
      color: "text-violet-400",
      bg: "bg-violet-500/10",
      border: "border-l-violet-500",
      title: "Test Linker",
      description: "Run bulk AI control test-to-control linking and review pending approval decisions before mappings go live.",
      href: "/admin/ai/test-linker",
      stat: null,
      highlight: false,
    },
  ]

  return (
    <div className="max-w-5xl space-y-8">
      <div className="flex items-start gap-4">
        <div className="rounded-xl bg-purple-500/15 p-3 shrink-0">
          <Sparkles className="h-6 w-6 text-purple-400" />
        </div>
        <div>
          <h2 className="text-2xl font-semibold text-foreground">AI Platform</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Manage AI agents, prompt templates, approval workflows, and usage reporting.
          </p>
        </div>
      </div>

      {/* Stats bar */}
      {loading ? (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="w-4 h-4 animate-spin" />
          Loading stats…
        </div>
      ) : stats && (
        <div className="flex gap-3 flex-wrap">
          {[
            { label: "Active Agents", value: stats.activeAgentCount, icon: Brain, border: "border-l-purple-500" },
            { label: "Prompt Templates", value: stats.promptCount, icon: FileCode2, border: "border-l-blue-500" },
            { label: "Pending Approvals", value: stats.pendingApprovals, icon: MessageSquare, border: stats.pendingApprovals > 0 ? "border-l-amber-500" : "border-l-muted" },
            { label: "Conversations", value: stats.totalConversations, icon: Users2, border: "border-l-emerald-500" },
            { label: "Total Tokens", value: stats.totalTokensUsed.toLocaleString(), icon: Zap, border: "border-l-cyan-500" },
            { label: "Jobs Running", value: stats.runningJobs, icon: ListTodo, border: stats.runningJobs > 0 ? "border-l-blue-500" : "border-l-muted" },
          ].map((s) => (
            <div key={s.label} className={`rounded-xl border border-l-[3px] ${s.border} bg-card px-4 py-2.5 flex items-center gap-3`}>
              <div className="rounded-lg p-1.5 bg-muted">
                <s.icon className="h-3.5 w-3.5 text-muted-foreground" />
              </div>
              <div className="flex flex-col">
                <span className="text-xl font-bold tabular-nums text-foreground leading-none">{s.value}</span>
                <span className="text-[10px] text-muted-foreground">{s.label}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Info banner */}
      <div className="rounded-xl border border-purple-500/20 bg-purple-500/5 px-5 py-4">
        <p className="text-sm font-semibold text-foreground mb-1.5">How K-Control AI works</p>
        <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <span className="rounded-md border border-border bg-card px-2 py-1 font-medium text-foreground">User message</span>
          <ArrowRight className="h-3 w-3" />
          <span className="rounded-md border border-border bg-card px-2 py-1 font-medium text-foreground">Guardrails</span>
          <ArrowRight className="h-3 w-3" />
          <span className="rounded-md border border-border bg-card px-2 py-1 font-medium text-foreground">Agent (LangGraph)</span>
          <ArrowRight className="h-3 w-3" />
          <span className="rounded-md border border-purple-500/30 bg-purple-500/10 px-2 py-1 font-medium text-purple-400">MCP Tools</span>
          <ArrowRight className="h-3 w-3" />
          <span className="rounded-md border border-amber-500/30 bg-amber-500/10 px-2 py-1 font-medium text-amber-400">Approval (write ops)</span>
          <ArrowRight className="h-3 w-3" />
          <span className="rounded-md border border-emerald-500/30 bg-emerald-500/10 px-2 py-1 font-medium text-emerald-400">SSE stream to user</span>
        </div>
      </div>

      {/* Section cards */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {cards.map((card) => (
          <Link key={card.href} href={card.href}>
            <div className={`rounded-xl border border-l-[3px] ${card.border} ${card.highlight ? "bg-amber-500/5" : "bg-card"} px-4 py-4 flex items-start gap-4 hover:bg-muted/20 transition-colors`}>
              <div className={`shrink-0 rounded-lg p-2 ${card.bg}`}>
                <card.icon className={`h-5 w-5 ${card.color}`} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <p className="text-sm font-semibold">{card.title}</p>
                  {card.stat && (
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${card.highlight ? "bg-amber-500/15 text-amber-400" : "bg-muted text-muted-foreground"}`}>
                      {card.stat}
                    </span>
                  )}
                </div>
                <p className="text-xs text-muted-foreground">{card.description}</p>
              </div>
              <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0 mt-1" />
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
