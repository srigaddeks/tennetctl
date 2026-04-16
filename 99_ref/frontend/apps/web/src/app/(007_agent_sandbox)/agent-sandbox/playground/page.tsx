"use client"

import { useEffect, useState, useRef, useCallback } from "react"
import { useSearchParams } from "next/navigation"
import {
  Play, Square, Loader2, Send, Trash2, Clock, Zap,
  DollarSign, Bot, ChevronDown, Settings2,
  Brain, FileCheck, ClipboardCheck, Sparkles, Database,
  FileText, Code, ShieldAlert, Library, SearchCheck, TestTubes,
} from "lucide-react"
import { useAgentSandbox } from "@/lib/context/AgentSandboxContext"
import { listRegisteredAgents, playgroundRunUrl, type AgentCatalogEntry } from "@/lib/api/agentSandbox"
import { getAccessToken } from "@/lib/api/apiClient"

const ICON_MAP: Record<string, React.ElementType> = {
  brain: Brain, zap: Zap, "file-check": FileCheck, "clipboard-check": ClipboardCheck,
  sparkles: Sparkles, database: Database, "file-text": FileText, code: Code,
  "shield-alert": ShieldAlert, library: Library, "search-check": SearchCheck,
  "test-tubes": TestTubes, bot: Bot, play: Play,
}

interface SSEEvent {
  event: string
  data: Record<string, unknown>
  timestamp: number
}

export default function PlaygroundPage() {
  const searchParams = useSearchParams()
  const { selectedOrgId, ready } = useAgentSandbox()

  const [agents, setAgents] = useState<AgentCatalogEntry[]>([])
  const [selectedAgent, setSelectedAgent] = useState<AgentCatalogEntry | null>(null)
  const [inputValues, setInputValues] = useState<Record<string, string>>({})
  const [events, setEvents] = useState<SSEEvent[]>([])
  const [running, setRunning] = useState(false)
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const eventSourceRef = useRef<EventSource | null>(null)
  const streamEndRef = useRef<HTMLDivElement | null>(null)

  // Load agents
  useEffect(() => {
    listRegisteredAgents()
      .then((res) => {
        setAgents(res.items)
        const agentParam = searchParams.get("agent")
        if (agentParam) {
          const found = res.items.find((a) => a.code === agentParam)
          if (found) setSelectedAgent(found)
        }
      })
      .catch(console.error)
  }, [searchParams])

  // Auto-scroll
  useEffect(() => {
    streamEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [events])

  const handleRun = useCallback(async () => {
    if (!selectedAgent || !selectedOrgId || running) return

    setRunning(true)
    setEvents([])

    const token = getAccessToken()
    const url = playgroundRunUrl(selectedAgent.code, selectedOrgId)

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({ inputs: inputValues }),
      })

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: "Request failed" }))
        setEvents([{ event: "error", data: { message: err.detail || response.statusText }, timestamp: Date.now() }])
        setRunning(false)
        return
      }

      const reader = response.body?.getReader()
      if (!reader) {
        setRunning(false)
        return
      }

      const decoder = new TextDecoder()
      let buffer = ""

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n")
        buffer = lines.pop() || ""

        let currentEvent = ""
        for (const line of lines) {
          if (line.startsWith("event: ")) {
            currentEvent = line.slice(7).trim()
          } else if (line.startsWith("data: ") && currentEvent) {
            try {
              const data = JSON.parse(line.slice(6))
              setEvents((prev) => [...prev, { event: currentEvent, data, timestamp: Date.now() }])
            } catch {
              setEvents((prev) => [...prev, { event: currentEvent, data: { raw: line.slice(6) }, timestamp: Date.now() }])
            }
            currentEvent = ""
          }
        }
      }
    } catch (e) {
      setEvents((prev) => [...prev, { event: "error", data: { message: (e as Error).message }, timestamp: Date.now() }])
    } finally {
      setRunning(false)
    }
  }, [selectedAgent, selectedOrgId, running, inputValues])

  const handleStop = () => {
    eventSourceRef.current?.close()
    setRunning(false)
  }

  const AgentIcon = selectedAgent ? (ICON_MAP[selectedAgent.icon] ?? Bot) : Bot

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="flex items-center justify-between gap-4 pb-4 border-b shrink-0">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
            <Play className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight">Agent Playground</h1>
            <p className="text-xs text-muted-foreground">Test any agent interactively with live execution streaming</p>
          </div>
        </div>
      </div>

      {/* Main layout: 2 columns */}
      <div className="flex-1 flex gap-4 pt-4 overflow-hidden">
        {/* LEFT: Agent selector + Input panel */}
        <div className="w-[380px] shrink-0 flex flex-col gap-4 overflow-y-auto">
          {/* Agent selector */}
          <div className="relative">
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="w-full flex items-center justify-between gap-2 rounded-lg border bg-card px-4 py-3 text-left hover:border-primary/50 transition-colors"
            >
              <div className="flex items-center gap-3 min-w-0">
                <AgentIcon className="h-5 w-5 shrink-0 text-primary" />
                <div className="min-w-0">
                  <p className="text-sm font-medium truncate">{selectedAgent?.name ?? "Select an agent..."}</p>
                  {selectedAgent && (
                    <p className="text-[10px] text-muted-foreground truncate">{selectedAgent.category} &middot; {selectedAgent.execution_mode}</p>
                  )}
                </div>
              </div>
              <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform ${dropdownOpen ? "rotate-180" : ""}`} />
            </button>

            {dropdownOpen && (
              <div className="absolute z-50 mt-1 w-full rounded-lg border bg-popover shadow-lg max-h-[300px] overflow-y-auto">
                {agents.map((agent) => {
                  const Icon = ICON_MAP[agent.icon] ?? Bot
                  return (
                    <button
                      key={agent.code}
                      onClick={() => { setSelectedAgent(agent); setDropdownOpen(false); setInputValues({}); setEvents([]) }}
                      className={`w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-muted/50 transition-colors ${
                        selectedAgent?.code === agent.code ? "bg-primary/5" : ""
                      }`}
                    >
                      <Icon className="h-4 w-4 shrink-0 text-muted-foreground" />
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate">{agent.name}</p>
                        <p className="text-[10px] text-muted-foreground">{agent.category}</p>
                      </div>
                    </button>
                  )
                })}
              </div>
            )}
          </div>

          {/* Agent details */}
          {selectedAgent && (
            <>
              <div className="rounded-lg border bg-card p-4">
                <p className="text-xs text-muted-foreground leading-relaxed">{selectedAgent.description}</p>
                {selectedAgent.tools_used.length > 0 && (
                  <div className="mt-3 pt-3 border-t">
                    <p className="text-[10px] font-medium text-muted-foreground mb-1.5">TOOLS</p>
                    <div className="flex flex-wrap gap-1">
                      {selectedAgent.tools_used.slice(0, 8).map((t) => (
                        <span key={t} className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground">{t}</span>
                      ))}
                      {selectedAgent.tools_used.length > 8 && (
                        <span className="text-[10px] text-muted-foreground">+{selectedAgent.tools_used.length - 8} more</span>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Input fields */}
              <div className="rounded-lg border bg-card p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-semibold">Inputs</p>
                  <button onClick={() => setShowSettings(!showSettings)} className="p-1 rounded hover:bg-muted">
                    <Settings2 className="h-3.5 w-3.5 text-muted-foreground" />
                  </button>
                </div>

                {selectedAgent.inputs.map((input) => (
                  <div key={input.name}>
                    <label className="text-[11px] font-medium text-muted-foreground flex items-center gap-1">
                      {input.name}
                      {input.required && <span className="text-red-500">*</span>}
                    </label>
                    {input.type === "select" && input.options ? (
                      <select
                        value={inputValues[input.name] ?? input.default ?? ""}
                        onChange={(e) => setInputValues((p) => ({ ...p, [input.name]: e.target.value }))}
                        className="mt-1 w-full rounded-md border px-3 py-1.5 text-sm bg-transparent"
                      >
                        <option value="">Select...</option>
                        {input.options.map((o) => <option key={o} value={o}>{o}</option>)}
                      </select>
                    ) : input.type === "json" ? (
                      <textarea
                        value={inputValues[input.name] ?? ""}
                        onChange={(e) => setInputValues((p) => ({ ...p, [input.name]: e.target.value }))}
                        placeholder={input.description}
                        rows={4}
                        className="mt-1 w-full rounded-md border px-3 py-1.5 text-xs font-mono bg-transparent resize-none"
                      />
                    ) : (
                      <textarea
                        value={inputValues[input.name] ?? ""}
                        onChange={(e) => setInputValues((p) => ({ ...p, [input.name]: e.target.value }))}
                        placeholder={input.description}
                        rows={input.name === "message" || input.name === "prompt" || input.name === "documents" ? 4 : 2}
                        className="mt-1 w-full rounded-md border px-3 py-1.5 text-sm bg-transparent resize-none"
                      />
                    )}
                  </div>
                ))}

                {showSettings && (
                  <div className="pt-3 border-t space-y-2">
                    <p className="text-[10px] font-medium text-muted-foreground">SETTINGS</p>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <label className="text-[10px] text-muted-foreground">Temperature</label>
                        <p className="font-mono">{selectedAgent.default_temperature}</p>
                      </div>
                      <div>
                        <label className="text-[10px] text-muted-foreground">Max Iterations</label>
                        <p className="font-mono">{selectedAgent.max_iterations}</p>
                      </div>
                      <div>
                        <label className="text-[10px] text-muted-foreground">Mode</label>
                        <p>{selectedAgent.execution_mode}</p>
                      </div>
                      <div>
                        <label className="text-[10px] text-muted-foreground">Conversation</label>
                        <p>{selectedAgent.supports_conversation ? "Yes" : "No"}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Run button */}
              <button
                onClick={running ? handleStop : handleRun}
                disabled={!selectedOrgId}
                className={`w-full flex items-center justify-center gap-2 rounded-lg px-4 py-3 text-sm font-medium transition-colors ${
                  running
                    ? "bg-destructive text-destructive-foreground hover:bg-destructive/90"
                    : "bg-primary text-primary-foreground hover:bg-primary/90"
                } disabled:opacity-50`}
              >
                {running ? (
                  <>
                    <Square className="h-4 w-4" />
                    Stop Execution
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4" />
                    Run Agent
                  </>
                )}
              </button>
            </>
          )}
        </div>

        {/* RIGHT: Execution stream + trace */}
        <div className="flex-1 flex flex-col rounded-lg border bg-card overflow-hidden">
          {/* Stream header */}
          <div className="flex items-center justify-between px-4 py-2.5 border-b bg-muted/30">
            <div className="flex items-center gap-2">
              <div className={`h-2 w-2 rounded-full ${running ? "bg-green-500 animate-pulse" : events.length > 0 ? "bg-blue-500" : "bg-gray-300"}`} />
              <span className="text-xs font-medium">
                {running ? "Executing..." : events.length > 0 ? `${events.length} events` : "Ready"}
              </span>
              {running && <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />}
            </div>
            <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
              {events.length > 0 && (
                <>
                  <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{((events[events.length - 1]?.timestamp - events[0]?.timestamp) / 1000).toFixed(1)}s</span>
                  <span className="flex items-center gap-1"><Zap className="h-3 w-3" />{events.length} events</span>
                </>
              )}
              {events.length > 0 && (
                <button onClick={() => setEvents([])} className="p-1 rounded hover:bg-muted">
                  <Trash2 className="h-3 w-3" />
                </button>
              )}
            </div>
          </div>

          {/* Event stream */}
          <div className="flex-1 overflow-y-auto p-4 space-y-1.5">
            {events.length === 0 && !running ? (
              <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                <Bot className="h-12 w-12 mb-3 opacity-20" />
                <p className="text-sm font-medium">No execution yet</p>
                <p className="text-xs mt-1">Select an agent, fill in inputs, and click Run</p>
              </div>
            ) : (
              events.map((evt, i) => (
                <EventRow key={i} event={evt} index={i} />
              ))
            )}
            <div ref={streamEndRef} />
          </div>
        </div>
      </div>
    </div>
  )
}

function EventRow({ event: evt, index }: { event: SSEEvent; index: number }) {
  const [expanded, setExpanded] = useState(false)

  const getEventStyle = (eventName: string) => {
    if (eventName === "error") return { color: "text-red-600", bg: "bg-red-500/10", icon: "!" }
    if (eventName === "run_started") return { color: "text-blue-600", bg: "bg-blue-500/10", icon: ">" }
    if (eventName === "run_completed") return { color: "text-green-600", bg: "bg-green-500/10", icon: "+" }
    if (eventName.startsWith("agent.")) return { color: "text-purple-600", bg: "bg-purple-500/10", icon: "*" }
    if (eventName === "agent_streaming") return { color: "text-amber-600", bg: "bg-amber-500/10", icon: "~" }
    if (eventName === "agent_processing") return { color: "text-amber-600", bg: "bg-amber-500/10", icon: "~" }
    if (eventName === "agent_result") return { color: "text-green-600", bg: "bg-green-500/10", icon: "=" }
    return { color: "text-muted-foreground", bg: "bg-muted/50", icon: "-" }
  }

  const style = getEventStyle(evt.event)
  const hasData = Object.keys(evt.data).length > 0
  const summary = getSummary(evt)

  return (
    <div
      className={`rounded-md ${style.bg} px-3 py-1.5 cursor-pointer hover:opacity-80 transition-opacity`}
      onClick={() => hasData && setExpanded(!expanded)}
    >
      <div className="flex items-center gap-2">
        <span className={`font-mono text-[10px] w-4 text-center ${style.color}`}>{style.icon}</span>
        <span className={`text-xs font-medium ${style.color}`}>{evt.event}</span>
        <span className="flex-1 text-xs text-muted-foreground truncate">{summary}</span>
        <span className="text-[10px] text-muted-foreground tabular-nums">#{index}</span>
      </div>
      {expanded && hasData && (
        <pre className="mt-2 text-[10px] font-mono leading-relaxed overflow-x-auto text-foreground/80 max-h-[200px] overflow-y-auto">
          {JSON.stringify(evt.data, null, 2)}
        </pre>
      )}
    </div>
  )
}

function getSummary(evt: SSEEvent): string {
  const d = evt.data
  if (d.message) return String(d.message).slice(0, 100)
  if (d.text) return String(d.text).slice(0, 100)
  if (d.content) return String(d.content).slice(0, 100)
  if (d.agent_name) return String(d.agent_name)
  if (d.status) return String(d.status)
  if (d.duration_ms) return `${d.duration_ms}ms`
  if (d.enhanced_text) return String(d.enhanced_text).slice(0, 100)
  if (d.full_response) return String(d.full_response).slice(0, 100)
  if (d.result && typeof d.result === "object") return JSON.stringify(d.result).slice(0, 80)
  return ""
}
