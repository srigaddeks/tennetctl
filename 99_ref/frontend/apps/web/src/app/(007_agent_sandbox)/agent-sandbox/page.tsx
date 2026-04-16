"use client"

import { useEffect, useState } from "react"
import { Bot, Cpu, Wrench, Play, ClipboardCheck, ArrowRight } from "lucide-react"
import { useAgentSandbox } from "@/lib/context/AgentSandboxContext"
import { getAgentSandboxStats } from "@/lib/api/agentSandbox"

interface StatCard {
  label: string
  value: number
  icon: React.ElementType
  href: string
  color: string
}

export default function AgentSandboxOverviewPage() {
  const { selectedOrgId, ready } = useAgentSandbox()
  const [stats, setStats] = useState<Record<string, number>>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!ready || !selectedOrgId) return
    setLoading(true)
    getAgentSandboxStats(selectedOrgId)
      .then(setStats)
      .catch(() => setStats({}))
      .finally(() => setLoading(false))
  }, [ready, selectedOrgId])

  const cards: StatCard[] = [
    { label: "Agents", value: stats.agents ?? 0, icon: Cpu, href: "/agent-sandbox/agents", color: "text-blue-500" },
    { label: "Agent Tools", value: stats.tools ?? 0, icon: Wrench, href: "/agent-sandbox/tools", color: "text-green-500" },
    { label: "Agent Runs", value: stats.runs ?? 0, icon: Play, href: "/agent-sandbox/runs", color: "text-purple-500" },
    { label: "Test Scenarios", value: stats.test_scenarios ?? 0, icon: ClipboardCheck, href: "/agent-sandbox/scenarios", color: "text-orange-500" },
  ]

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
          <Bot className="h-5 w-5 text-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Agent Sandbox</h1>
          <p className="text-sm text-muted-foreground">
            Build, test, and deploy autonomous AI agents from the UI
          </p>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map((card) => (
          <a
            key={card.label}
            href={card.href}
            className="group relative flex flex-col gap-2 rounded-xl border bg-card p-5 transition-all hover:shadow-md hover:border-primary/30"
          >
            <div className="flex items-center justify-between">
              <card.icon className={`h-5 w-5 ${card.color}`} />
              <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
            <div>
              <p className="text-2xl font-bold tabular-nums">
                {loading ? "—" : card.value}
              </p>
              <p className="text-xs text-muted-foreground">{card.label}</p>
            </div>
          </a>
        ))}
      </div>

      {/* Quick start */}
      <div className="rounded-xl border bg-card p-6">
        <h2 className="text-lg font-semibold mb-3">Getting Started</h2>
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="flex gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-500/10 text-blue-500 text-sm font-bold">1</div>
            <div>
              <p className="text-sm font-medium">Register Tools</p>
              <p className="text-xs text-muted-foreground">Connect MCP servers, API endpoints, or Python functions your agents can call</p>
            </div>
          </div>
          <div className="flex gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-green-500/10 text-green-500 text-sm font-bold">2</div>
            <div>
              <p className="text-sm font-medium">Build Agents</p>
              <p className="text-xs text-muted-foreground">Write Python graph code defining nodes, transitions, and handler functions</p>
            </div>
          </div>
          <div className="flex gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-purple-500/10 text-purple-500 text-sm font-bold">3</div>
            <div>
              <p className="text-sm font-medium">Test & Deploy</p>
              <p className="text-xs text-muted-foreground">Run test scenarios, observe execution traces, and promote validated agents</p>
            </div>
          </div>
        </div>
      </div>

      {/* Agent Contract Example */}
      <div className="rounded-xl border bg-card p-6">
        <h2 className="text-lg font-semibold mb-3">Agent Code Contract</h2>
        <p className="text-sm text-muted-foreground mb-4">
          Every agent defines handler functions and a <code className="px-1 py-0.5 bg-muted rounded text-xs font-mono">build_graph(ctx)</code> function:
        </p>
        <pre className="rounded-lg bg-muted/50 p-4 text-xs font-mono overflow-x-auto leading-relaxed">{`def build_graph(ctx):
    return {
        "nodes": {
            "analyze": {
                "handler": analyze_data,
                "transitions": {"ready": "report", "needs_more": "gather"}
            },
            "gather": {
                "handler": gather_info,
                "transitions": {"done": "analyze"}
            },
            "report": {
                "handler": write_report,
                "transitions": {"done": "__end__"}
            },
        },
        "entry_point": "analyze",
    }

def analyze_data(ctx):
    data = ctx.tool("fetch_assets", {"type": "github_repo"})
    analysis = ctx.llm(
        system="You are a security analyst.",
        user=f"Analyze: {data}"
    )
    ctx.state["analysis"] = analysis
    return "ready"

def gather_info(ctx):
    answer = ctx.ask_human("Which repos to focus on?")
    ctx.state["focus"] = answer
    return "done"

def write_report(ctx):
    report = ctx.llm(
        system="Write a security report.",
        user=f"Analysis: {ctx.state['analysis']}"
    )
    ctx.emit("report_ready", {"content": report})
    return "done"`}</pre>
      </div>
    </div>
  )
}
