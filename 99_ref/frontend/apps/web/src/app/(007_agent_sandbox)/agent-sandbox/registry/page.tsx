"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import {
  Brain, Zap, FileCheck, ClipboardCheck, Sparkles, Database,
  FileText, Code, ShieldAlert, Library, SearchCheck, Play,
  Bot, Layers, ArrowRight, Search, TestTubes,
} from "lucide-react"
import { listRegisteredAgents, type AgentCatalogEntry, type RegistryResponse } from "@/lib/api/agentSandbox"

const ICON_MAP: Record<string, React.ElementType> = {
  brain: Brain, zap: Zap, "file-check": FileCheck, "clipboard-check": ClipboardCheck,
  sparkles: Sparkles, database: Database, "file-text": FileText, code: Code,
  "shield-alert": ShieldAlert, library: Library, "search-check": SearchCheck,
  "test-tubes": TestTubes, bot: Bot, play: Play,
}

const CATEGORY_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  copilot: { bg: "bg-blue-500/10", text: "text-blue-600 dark:text-blue-400", label: "Copilot" },
  builder: { bg: "bg-green-500/10", text: "text-green-600 dark:text-green-400", label: "Builder" },
  generator: { bg: "bg-purple-500/10", text: "text-purple-600 dark:text-purple-400", label: "Generator" },
  analyzer: { bg: "bg-amber-500/10", text: "text-amber-600 dark:text-amber-400", label: "Analyzer" },
  evaluator: { bg: "bg-red-500/10", text: "text-red-600 dark:text-red-400", label: "Evaluator" },
  composer: { bg: "bg-teal-500/10", text: "text-teal-600 dark:text-teal-400", label: "Composer" },
}

const MODE_BADGES: Record<string, { label: string; className: string }> = {
  streaming: { label: "Streaming", className: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300" },
  batch: { label: "Background", className: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300" },
  request_response: { label: "Instant", className: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300" },
}

export default function RegistryPage() {
  const router = useRouter()
  const [registry, setRegistry] = useState<RegistryResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    listRegisteredAgents(selectedCategory ? { category: selectedCategory } : undefined)
      .then(setRegistry)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [selectedCategory])

  const filtered = (registry?.items ?? []).filter(
    (a) =>
      a.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.tags.some((t) => t.includes(searchQuery.toLowerCase()))
  )

  const categories = registry?.categories ?? []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
          <Layers className="h-5 w-5 text-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Agent Registry</h1>
          <p className="text-sm text-muted-foreground">
            {registry?.total ?? 0} AI agents auto-discovered from the platform
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 rounded-md border px-3 py-2 flex-1 max-w-md">
          <Search className="h-4 w-4 text-muted-foreground" />
          <input
            placeholder="Search agents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
          />
        </div>
        <div className="flex gap-1.5">
          <button
            onClick={() => setSelectedCategory(null)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              !selectedCategory ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:text-foreground"
            }`}
          >
            All
          </button>
          {categories.map((cat) => {
            const style = CATEGORY_STYLES[cat] ?? { bg: "bg-muted", text: "text-muted-foreground", label: cat }
            return (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat === selectedCategory ? null : cat)}
                className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                  selectedCategory === cat
                    ? "bg-primary text-primary-foreground"
                    : `${style.bg} ${style.text} hover:opacity-80`
                }`}
              >
                {style.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* Agent Cards */}
      {loading ? (
        <div className="p-12 text-center text-muted-foreground">Loading agents...</div>
      ) : filtered.length === 0 ? (
        <div className="p-12 text-center text-muted-foreground">No agents match your search.</div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((agent) => {
            const IconComponent = ICON_MAP[agent.icon] ?? Bot
            const catStyle = CATEGORY_STYLES[agent.category] ?? { bg: "bg-muted", text: "text-muted-foreground", label: agent.category }
            const modeBadge = MODE_BADGES[agent.execution_mode] ?? { label: agent.execution_mode, className: "bg-muted text-muted-foreground" }

            return (
              <div
                key={agent.code}
                className="group relative flex flex-col rounded-xl border bg-card transition-all hover:shadow-lg hover:border-primary/30 cursor-pointer overflow-hidden"
                onClick={() => router.push(`/agent-sandbox/playground?agent=${agent.code}`)}
              >
                {/* Card header */}
                <div className="p-5 pb-3">
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${catStyle.bg}`}>
                      <IconComponent className={`h-5 w-5 ${catStyle.text}`} />
                    </div>
                    <div className="flex gap-1.5">
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${catStyle.bg} ${catStyle.text}`}>
                        {catStyle.label}
                      </span>
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${modeBadge.className}`}>
                        {modeBadge.label}
                      </span>
                    </div>
                  </div>
                  <h3 className="font-semibold text-sm mb-1">{agent.name}</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2">
                    {agent.description}
                  </p>
                </div>

                {/* Card footer */}
                <div className="mt-auto border-t px-5 py-3 bg-muted/20">
                  <div className="flex items-center justify-between">
                    <div className="flex flex-wrap gap-1">
                      {agent.tags.slice(0, 3).map((tag) => (
                        <span key={tag} className="rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">
                          {tag}
                        </span>
                      ))}
                    </div>
                    <div className="flex items-center gap-1 text-xs text-primary opacity-0 group-hover:opacity-100 transition-opacity">
                      <span>Try it</span>
                      <ArrowRight className="h-3 w-3" />
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
