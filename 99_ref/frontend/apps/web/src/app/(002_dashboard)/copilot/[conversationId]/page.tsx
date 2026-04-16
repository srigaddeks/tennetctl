"use client"

import { useEffect, useState, useRef, useCallback } from "react"
import { useParams, useRouter, useSearchParams } from "next/navigation"
import {
  ChevronLeft, Bot, User, Loader2, Send, Sparkles,
  Check, XCircle, Archive, Wrench, CheckCircle2, AlertCircle, Database, Search,
} from "lucide-react"
import { Button, Card, CardContent } from "@kcontrol/ui"
import {
  getConversation, listMessages, streamMessage, archiveConversation,
  approveAction, rejectApproval,
  type ConversationResponse, type MessageResponse, type ApprovalResponse,
} from "@/lib/api/ai"
import { useCopilotPageContext } from "@/lib/hooks/useCopilotPageContext"
import { ApprovalModal } from "@/components/copilot/ApprovalModal"

function formatRelative(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  if (diff < 60_000) return "just now"
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`
  return new Date(iso).toLocaleDateString([], { month: "short", day: "numeric" })
}

function ApprovalCard({
  approval,
  onApprove,
  onReject,
}: {
  approval: ApprovalResponse
  onApprove: (id: string) => Promise<void>
  onReject: (id: string, reason: string) => Promise<void>
}) {
  const [acting, setActing] = useState(false)
  const [showReject, setShowReject] = useState(false)
  const [rejectReason, setRejectReason] = useState("")
  const [done, setDone] = useState<"approved" | "rejected" | null>(
    approval.status_code === "approved" ? "approved"
      : approval.status_code === "rejected" ? "rejected" : null
  )

  const opColors: Record<string, string> = {
    create: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    update: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    delete: "bg-red-500/10 text-red-400 border-red-500/20",
  }

  return (
    <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4 space-y-3 max-w-lg">
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider">
          Approval Required
        </span>
        {approval.operation && (
          <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold border ${opColors[approval.operation] ?? "bg-muted text-muted-foreground border-border"}`}>
            {approval.operation}
          </span>
        )}
        {approval.entity_type && (
          <span className="text-xs text-muted-foreground capitalize">
            {approval.entity_type.replace(/_/g, " ")}
          </span>
        )}
      </div>

      <p className="text-xs font-mono text-muted-foreground">{approval.tool_name}</p>

      {approval.diff_json && (
        <div className="rounded-lg bg-background border border-border p-3 text-xs font-mono max-h-40 overflow-auto space-y-1">
          {Object.entries(
            (approval.diff_json as { after?: Record<string, unknown> }).after ?? {}
          ).map(([k, v]) => (
            <div key={k} className="flex gap-2">
              <span className="text-muted-foreground shrink-0">{k}:</span>
              <span className="text-emerald-400">{String(v)}</span>
            </div>
          ))}
        </div>
      )}

      {done ? (
        <div className={`flex items-center gap-1.5 text-sm font-semibold ${done === "approved" ? "text-emerald-400" : "text-red-400"}`}>
          {done === "approved" ? <Check className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
          {done === "approved" ? "Approved" : "Rejected"}
        </div>
      ) : showReject ? (
        <div className="space-y-2">
          <input
            value={rejectReason}
            onChange={e => setRejectReason(e.target.value)}
            placeholder="Reason for rejection…"
            className="w-full h-8 rounded-lg border border-input bg-background text-sm px-3 focus:outline-none focus:ring-2 focus:ring-ring"
          />
          <div className="flex gap-2">
            <Button size="sm" variant="destructive" disabled={acting || !rejectReason.trim()}
              onClick={async () => {
                setActing(true)
                try { await onReject(approval.id, rejectReason); setDone("rejected") } catch { /* ignore */ }
                finally { setActing(false) }
              }}>
              {acting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <XCircle className="w-3.5 h-3.5" />}
              Reject
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setShowReject(false)}>Cancel</Button>
          </div>
        </div>
      ) : (
        <div className="flex gap-2">
          <Button size="sm" className="gap-1.5 bg-emerald-500 hover:bg-emerald-600" disabled={acting}
            onClick={async () => {
              setActing(true)
              try { await onApprove(approval.id); setDone("approved") } catch { /* ignore */ }
              finally { setActing(false) }
            }}>
            {acting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
            Approve
          </Button>
          <Button size="sm" variant="outline" className="gap-1.5 text-red-400 border-red-500/30 hover:bg-red-500/10"
            disabled={acting} onClick={() => setShowReject(true)}>
            <XCircle className="w-3.5 h-3.5" /> Reject
          </Button>
        </div>
      )}
    </div>
  )
}

function MessageBubble({
  msg,
  approvals,
  onApprove,
  onReject,
}: {
  msg: MessageResponse
  approvals: ApprovalResponse[]
  onApprove: (id: string) => Promise<void>
  onReject: (id: string, reason: string) => Promise<void>
}) {
  const isUser = msg.role_code === "user"

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-0.5
        ${isUser ? "bg-primary" : "bg-purple-500/20"}`}>
        {isUser
          ? <User className="w-4 h-4 text-primary-foreground" />
          : <Bot className="w-4 h-4 text-purple-400" />}
      </div>
      <div className={`flex-1 min-w-0 space-y-2 flex flex-col ${isUser ? "items-end" : "items-start"}`}>
        <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed
          ${isUser
            ? "bg-primary text-primary-foreground rounded-tr-sm"
            : "bg-muted/60 text-foreground rounded-tl-sm border border-border/50"
          }`}>
          <p className="whitespace-pre-wrap break-words">{msg.content}</p>
        </div>
        {!isUser && approvals.map(ap => (
          <ApprovalCard key={ap.id} approval={ap} onApprove={onApprove} onReject={onReject} />
        ))}
        <p className="text-[11px] text-muted-foreground/50 px-1">{formatRelative(msg.created_at)}</p>
      </div>
    </div>
  )
}

export default function ConversationPage() {
  const { conversationId } = useParams<{ conversationId: string }>()
  const router = useRouter()
  const searchParams = useSearchParams()
  const initialPrompt = searchParams.get("prompt")
  const pageContext = useCopilotPageContext()

  interface ToolCallEvent {
    tool_name: string
    tool_category: "insight" | "navigation"
    input_summary: string
    is_successful?: boolean
    output_summary?: string
    status: "running" | "done" | "error"
  }

  const [conv, setConv] = useState<ConversationResponse | null>(null)
  const [messages, setMessages] = useState<MessageResponse[]>([])
  const [approvalQueue, setApprovalQueue] = useState<ApprovalResponse[]>([])
  const [streamContent, setStreamContent] = useState("")
  const [streamToolCalls, setStreamToolCalls] = useState<ToolCallEvent[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [input, setInput] = useState(initialPrompt ?? "")
  const [loading, setLoading] = useState(true)
  const [archiving, setArchiving] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const didAutoSend = useRef(false)

  const loadMessages = useCallback(async () => {
    if (!conversationId) return
    try {
      const msgs = await listMessages(conversationId, 100)
      setMessages(msgs.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()))
    } catch { /* ignore */ }
  }, [conversationId])

  useEffect(() => {
    if (!conversationId) return
    setLoading(true)
    Promise.all([
      getConversation(conversationId).then(setConv),
      loadMessages(),
    ]).finally(() => setLoading(false))
  }, [conversationId, loadMessages])

  useEffect(() => {
    if (initialPrompt && !didAutoSend.current && !loading && conv) {
      didAutoSend.current = true
      setInput("")
      doSend(initialPrompt)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading, conv])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, streamContent])

  async function doSend(text: string) {
    if (!conversationId || !text.trim()) return

    setIsStreaming(true)
    setStreamContent("")
    setStreamToolCalls([])

    const optimistic: MessageResponse = {
      id: `opt_${Date.now()}`,
      conversation_id: conversationId,
      role_code: "user",
      content: text,
      token_count: null,
      model_id: null,
      created_at: new Date().toISOString(),
    }
    setMessages(prev => [...prev, optimistic])

    try {
      const res = await streamMessage(conversationId, {
        content: text,
        page_context: pageContext as unknown as Record<string, unknown>,
      })
      if (!res.body) { setIsStreaming(false); return }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ""

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        const parts = buffer.split("\n\n")
        buffer = parts.pop() ?? ""

        for (const part of parts) {
          const lines = part.split("\n")
          const eventLine = lines.find(l => l.startsWith("event:"))
          const dataLine = lines.find(l => l.startsWith("data:"))
          if (!eventLine || !dataLine) continue

          const eventType = eventLine.replace("event:", "").trim()
          let data: Record<string, unknown> = {}
          try { data = JSON.parse(dataLine.replace("data:", "").trim()) } catch { continue }

          if (eventType === "content_delta") {
            setStreamContent(prev => prev + ((data.delta as string) ?? (data.text as string) ?? ""))
          } else if (eventType === "tool_call_start") {
            setStreamToolCalls(prev => [...prev, {
              tool_name: data.tool_name as string,
              tool_category: (data.tool_category as "insight" | "navigation") ?? "navigation",
              input_summary: data.input_summary as string ?? "",
              status: "running" as const,
            }])
          } else if (eventType === "tool_call_result") {
            setStreamToolCalls(prev => prev.map(tc =>
              tc.tool_name === (data.tool_name as string)
                ? { ...tc, status: (data.is_successful ? "done" : "error") as "done" | "error", output_summary: data.output_summary as string }
                : tc
            ))
          } else if (eventType === "session_named") {
            setConv(prev => prev ? { ...prev, title: data.title as string } : prev)
          } else if (eventType === "approval_created") {
            setApprovalQueue(prev => [...prev, data as unknown as ApprovalResponse])
          } else if (eventType === "message_end") {
            await loadMessages()
            setStreamContent("")
            setStreamToolCalls([])
            setIsStreaming(false)
          }
        }
      }
    } catch { /* ignore */ }
    finally {
      setIsStreaming(false)
    }
  }

  async function handleSend(e: React.FormEvent) {
    e.preventDefault()
    const text = input.trim()
    if (!text || isStreaming) return
    setInput("")
    await doSend(text)
  }

  async function handleArchive() {
    if (!conversationId) return
    setArchiving(true)
    try {
      await archiveConversation(conversationId)
      router.push("/copilot")
    } catch { /* ignore */ }
    finally { setArchiving(false) }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  async function handleModalApprove(approvalId: string) {
    await approveAction(approvalId)
    setApprovalQueue(prev => prev.filter(a => a.id !== approvalId))
  }

  async function handleModalReject(approvalId: string, reason: string) {
    await rejectApproval(approvalId, reason)
    setApprovalQueue(prev => prev.filter(a => a.id !== approvalId))
  }

  return (
    <>
    {approvalQueue.length > 0 && (
      <ApprovalModal
        approval={approvalQueue[0]}
        queueLength={approvalQueue.length}
        onApprove={handleModalApprove}
        onReject={handleModalReject}
      />
    )}
    <div className="flex flex-col h-[calc(100vh-4rem)] max-w-4xl mx-auto">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push("/copilot")}
            className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
            Conversations
          </button>
          <div className="h-4 w-px bg-border" />
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-purple-500/15 flex items-center justify-center">
              <Sparkles className="w-3.5 h-3.5 text-purple-400" />
            </div>
            <p className="text-sm font-semibold truncate max-w-[300px]">
              {conv?.title ?? "AI Copilot"}
            </p>
          </div>
        </div>
        <Button size="sm" variant="ghost" className="gap-1.5 text-muted-foreground" onClick={handleArchive} disabled={archiving}>
          {archiving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Archive className="w-3.5 h-3.5" />}
          Archive
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-5 min-h-0">
        {messages.length === 0 && !isStreaming && (
          <div className="flex flex-col items-center justify-center h-full gap-4 text-center">
            <div className="w-14 h-14 rounded-2xl bg-purple-500/10 flex items-center justify-center">
              <Bot className="w-7 h-7 text-purple-400" />
            </div>
            <div>
              <p className="font-semibold text-foreground">What can I help you with?</p>
              <p className="text-sm text-muted-foreground mt-1">I have context about your current page and GRC data.</p>
            </div>
          </div>
        )}

        {messages.map(msg => (
          <MessageBubble
            key={msg.id}
            msg={msg}
            approvals={[]}
            onApprove={async () => {}}
            onReject={async () => {}}
          />
        ))}

        {isStreaming && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-purple-500/20 flex items-center justify-center shrink-0 mt-0.5">
              <Bot className="w-4 h-4 text-purple-400" />
            </div>
            <div className="flex-1 min-w-0 space-y-2">
              {streamToolCalls.map((call, i) => (
                <div key={`${call.tool_name}-${i}`} className="flex items-center gap-2 px-3 py-2 rounded-xl border border-blue-500/20 bg-blue-500/5 text-xs max-w-[80%]">
                  <span className={`inline-flex items-center gap-1.5 font-mono font-semibold ${
                    call.tool_category === "insight" ? "text-blue-400" : "text-indigo-400"
                  }`}>
                    {call.tool_category === "insight"
                      ? <Database className="w-3 h-3" />
                      : <Search className="w-3 h-3" />
                    }
                    {call.tool_name.replace(/^grc_/, "").replace(/_/g, " ")}
                  </span>
                  <span className="text-muted-foreground/60 truncate max-w-[200px]">{call.input_summary}</span>
                  {call.status === "running" && <Loader2 className="w-3 h-3 animate-spin text-blue-400 shrink-0 ml-auto" />}
                  {call.status === "done" && (
                    <span className="inline-flex items-center gap-1 text-emerald-400 ml-auto shrink-0">
                      <CheckCircle2 className="w-3 h-3" />
                      <span className="truncate max-w-[120px]">{call.output_summary}</span>
                    </span>
                  )}
                  {call.status === "error" && <AlertCircle className="w-3 h-3 text-red-400 ml-auto shrink-0" />}
                </div>
              ))}
              <div className="max-w-[80%] rounded-2xl rounded-tl-sm px-4 py-3 text-sm bg-muted/60 border border-border/50">
                {streamContent ? (
                  <p className="whitespace-pre-wrap">{streamContent}</p>
                ) : (
                  <div className="flex gap-1.5 items-center py-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-bounce [animation-delay:0ms]" />
                    <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-bounce [animation-delay:150ms]" />
                    <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-bounce [animation-delay:300ms]" />
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="shrink-0 border-t border-border px-4 py-3">
        <form onSubmit={handleSend} className="flex gap-2 items-end">
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault()
                handleSend(e as unknown as React.FormEvent)
              }
            }}
            placeholder="Ask anything… (Enter to send, Shift+Enter for newline)"
            rows={1}
            disabled={isStreaming}
            className="flex-1 rounded-xl border border-input bg-muted/40 text-sm px-4 py-2.5 resize-none focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50 max-h-40 overflow-y-auto"
            style={{ minHeight: "2.75rem" }}
          />
          <button
            type="submit"
            disabled={!input.trim() || isStreaming}
            className="p-3 rounded-xl bg-primary text-primary-foreground disabled:opacity-40 hover:opacity-90 transition-opacity shrink-0"
          >
            {isStreaming
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : <Send className="w-4 h-4" />}
          </button>
        </form>
        <p className="text-[10px] text-muted-foreground/40 mt-1.5 px-1">
          Current page context is sent with every message.
        </p>
      </div>
    </div>
    </>
  )
}
