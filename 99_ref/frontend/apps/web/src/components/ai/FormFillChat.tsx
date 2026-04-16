"use client"

import { useEffect, useRef, useState } from "react"
import { Bot, ChevronDown, ChevronUp, Loader2, Send, Sparkles, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { useFormFillAgent } from "@/lib/hooks/useFormFillAgent"

interface FormFillChatProps {
  entityType: string
  orgId?: string | null
  workspaceId?: string | null
  /** Static page context — entity IDs, framework info, etc. */
  pageContext?: Record<string, unknown>
  /** Called just before each send — return the current form field values so the agent sees the live state */
  getFormValues?: () => Record<string, unknown>
  onFilled: (fields: Record<string, string>) => void
  placeholder?: string
  className?: string
}

export function FormFillChat({
  entityType,
  orgId,
  workspaceId,
  pageContext,
  getFormValues,
  onFilled,
  placeholder,
  className,
}: FormFillChatProps) {
  const [open, setOpen] = useState(false)
  const [input, setInput] = useState("")
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const getFormValuesRef = useRef(getFormValues)
  getFormValuesRef.current = getFormValues

  const defaultPlaceholder =
    placeholder ||
    {
      framework: "e.g. HIPAA Security Rule for a healthcare company",
      control: "e.g. MFA enforcement for all admin accounts",
      risk: "e.g. risk of unauthorized data access via stolen credentials",
      task: "e.g. review MFA configuration on AWS console",
    }[entityType] ||
    "Describe what you want to create..."

  const { phase, messages, streamingText, error, sendMessage, reset } = useFormFillAgent({
    entityType,
    orgId,
    workspaceId,
    pageContext,
    getFormValues: getFormValues ? () => getFormValuesRef.current!() : undefined,
    onFilled,
  })

  const isThinking = phase === "thinking"
  const hasMessages = messages.length > 0

  useEffect(() => {
    if (open && textareaRef.current && messages.length === 0) {
      textareaRef.current.focus()
    }
  }, [open, messages.length])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, streamingText])

  const handleSend = () => {
    const text = input.trim()
    if (!text || isThinking) return
    setInput("")
    sendMessage(text)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleToggle = () => {
    if (open) {
      setOpen(false)
    } else {
      reset()
      setOpen(true)
    }
  }

  return (
    <div className={cn("w-full", className)}>
      {/* Trigger button — plain element, no shadcn to avoid hover:bg-accent override */}
      <button
        type="button"
        onClick={handleToggle}
        style={open
          ? { background: "var(--card)", borderColor: "rgb(109 40 217 / 0.6)" }
          : { background: "var(--card)", borderColor: "rgb(109 40 217 / 0.4)" }
        }
        className="inline-flex h-7 items-center gap-1.5 rounded-md border px-2.5 text-xs font-medium transition-colors text-violet-400 hover:text-violet-300"
      >
        <Sparkles className="h-3.5 w-3.5" />
        AI Fill
        {open ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
      </button>

      {/* Chat panel */}
      {open && (
        <div className="mt-2 rounded-xl overflow-hidden border border-border bg-card">
          {/* Header */}
          <div className="flex items-center justify-between px-3 py-2 border-b border-border">
            <div className="flex items-center gap-1.5">
              <Bot className="h-3.5 w-3.5 text-violet-500" />
              <span className="text-xs font-medium text-foreground">AI Form Assistant</span>
            </div>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>

          {/* Messages */}
          {hasMessages && (
            <div className="max-h-52 overflow-y-auto px-3 py-2 space-y-2">
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={cn(
                    "text-xs leading-relaxed",
                    msg.role === "user"
                      ? "text-right text-muted-foreground"
                      : "text-left text-foreground",
                  )}
                >
                  {msg.role === "assistant" && (
                    <span className="mr-1 font-medium text-violet-500">AI:</span>
                  )}
                  {msg.content}
                </div>
              ))}
              {streamingText && (
                <div className="text-xs leading-relaxed text-foreground">
                  <span className="mr-1 font-medium text-violet-500">AI:</span>
                  {streamingText}
                  <span className="ml-0.5 inline-block h-3 w-0.5 animate-pulse bg-violet-500" />
                </div>
              )}
              {isThinking && !streamingText && (
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Loader2 className="h-3 w-3 animate-spin" />
                  <span>Thinking…</span>
                </div>
              )}
              {error && <div className="text-xs text-destructive">{error}</div>}
              <div ref={messagesEndRef} />
            </div>
          )}

          {/* Input row */}
          <div className="flex items-end gap-2 p-2">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={hasMessages ? "Ask a follow-up…" : defaultPlaceholder}
              rows={2}
              disabled={isThinking}
              style={{ backgroundColor: "var(--input)", color: "var(--foreground)" }}
              className="w-full resize-none rounded-md border border-border px-3 py-2 text-xs outline-none transition-colors placeholder:text-muted-foreground focus:border-violet-500 disabled:opacity-50 disabled:cursor-not-allowed"
            />
            <button
              type="button"
              onClick={handleSend}
              disabled={!input.trim() || isThinking}
              className="h-8 w-8 shrink-0 rounded-lg bg-violet-600 hover:bg-violet-700 disabled:opacity-40 disabled:cursor-not-allowed text-white flex items-center justify-center transition-colors"
            >
              {isThinking ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Send className="h-3.5 w-3.5" />
              )}
            </button>
          </div>

          {/* Hint */}
          {!hasMessages && (
            <p className="px-3 pb-2 text-[10px] text-muted-foreground/60">
              Describe what you want — AI will fill the form for you. Press Enter to send.
            </p>
          )}
        </div>
      )}
    </div>
  )
}
