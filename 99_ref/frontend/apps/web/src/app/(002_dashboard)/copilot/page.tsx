"use client"

import { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import { Sparkles, Plus, Archive, Loader2, Bot, Clock } from "lucide-react"
import { Card, CardContent, Button } from "@kcontrol/ui"
import { listConversations, createConversation, archiveConversation, type ConversationResponse } from "@/lib/api/ai"
import { useCopilotPageContext } from "@/lib/hooks/useCopilotPageContext"

function formatRelative(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  if (diff < 60_000) return "just now"
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`
  if (diff < 7 * 86_400_000) return `${Math.floor(diff / 86_400_000)}d ago`
  return new Date(iso).toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" })
}

export default function CopilotPage() {
  const router = useRouter()
  const pageContext = useCopilotPageContext()
  const [conversations, setConversations] = useState<ConversationResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [archivingId, setArchivingId] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await listConversations(false, 50, 0)
      setConversations(res.items)
    } catch { /* ignore */ }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  async function handleNew() {
    setCreating(true)
    try {
      const conv = await createConversation({
        agent_type_code: "copilot",
        org_id: pageContext.org_id ?? undefined,
        workspace_id: pageContext.workspace_id ?? undefined,
        page_context: pageContext as unknown as Record<string, unknown>,
      })
      router.push(`/copilot/${conv.id}`)
    } catch { /* ignore */ }
    finally { setCreating(false) }
  }

  async function handleArchive(id: string, e: React.MouseEvent) {
    e.stopPropagation()
    setArchivingId(id)
    try {
      await archiveConversation(id)
      setConversations(prev => prev.filter(c => c.id !== id))
    } catch { /* ignore */ }
    finally { setArchivingId(null) }
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-purple-500/15 flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight">AI Copilot</h1>
            <p className="text-sm text-muted-foreground">Context-aware assistant for GRC workflows</p>
          </div>
        </div>
        <Button onClick={handleNew} disabled={creating} className="gap-2">
          {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
          New conversation
        </Button>
      </div>

      <Card className="rounded-xl border-purple-500/15 bg-purple-500/5">
        <CardContent className="p-5">
          <p className="text-xs font-bold text-purple-400 uppercase tracking-wider mb-3">Quick prompts</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {[
              "Summarize my open high-priority risks",
              "Which controls are overdue for evidence?",
              "Show frameworks with the most compliance gaps",
              "List tasks assigned to me that are overdue",
              "Suggest remediation steps for my critical risks",
              "What are the most common control failures?",
            ].map(prompt => (
              <button
                key={prompt}
                onClick={async () => {
                  setCreating(true)
                  try {
                    const conv = await createConversation({
                      agent_type_code: "copilot",
                      title: prompt.slice(0, 80),
                      org_id: pageContext.org_id ?? undefined,
                      workspace_id: pageContext.workspace_id ?? undefined,
                      page_context: pageContext as unknown as Record<string, unknown>,
                    })
                    router.push(`/copilot/${conv.id}?prompt=${encodeURIComponent(prompt)}`)
                  } catch { /* ignore */ }
                  finally { setCreating(false) }
                }}
                className="text-left text-xs px-3 py-2.5 rounded-xl border border-purple-500/15 bg-background/60 hover:bg-purple-500/10 text-foreground transition-colors"
              >
                {prompt}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      <div>
        <h2 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">
          Recent conversations
        </h2>
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-16 rounded-xl bg-muted animate-pulse" />
            ))}
          </div>
        ) : conversations.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 gap-4 text-center">
            <div className="w-14 h-14 rounded-2xl bg-muted flex items-center justify-center">
              <Bot className="w-7 h-7 text-muted-foreground/40" />
            </div>
            <p className="text-sm text-muted-foreground">No conversations yet. Start one above.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {conversations.map(conv => (
              <Card
                key={conv.id}
                className="rounded-xl cursor-pointer hover:border-purple-500/20 transition-colors group"
                onClick={() => router.push(`/copilot/${conv.id}`)}
              >
                <CardContent className="p-4 flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-purple-500/10 flex items-center justify-center shrink-0">
                    <Bot className="w-4.5 h-4.5 text-purple-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">
                      {conv.title ?? "Untitled conversation"}
                    </p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <Clock className="w-3 h-3 text-muted-foreground/50" />
                      <span className="text-[11px] text-muted-foreground/60">
                        {formatRelative(conv.updated_at)}
                      </span>
                      {conv.agent_type_code !== "copilot" && (
                        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold border border-border bg-muted text-muted-foreground">
                          {conv.agent_type_code}
                        </span>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={(e) => handleArchive(conv.id, e)}
                    disabled={archivingId === conv.id}
                    className="opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground"
                    title="Archive conversation"
                  >
                    {archivingId === conv.id
                      ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      : <Archive className="w-3.5 h-3.5" />}
                  </button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
