"use client"

import { useCallback, useRef, useState } from "react"
import { streamAgentFormFill } from "@/lib/api/ai"

export type FormFillAgentPhase = "idle" | "thinking" | "done" | "error"

export interface ChatMessage {
  role: "user" | "assistant"
  content: string
}

export interface UseFormFillAgentConfig {
  entityType: string
  orgId?: string | null
  workspaceId?: string | null
  pageContext?: Record<string, unknown>
  /** Called at send time — return current form values to inject as current_form into page context */
  getFormValues?: () => Record<string, unknown>
  onFilled: (fields: Record<string, string>) => void
}

export function useFormFillAgent({
  entityType,
  orgId,
  workspaceId,
  pageContext,
  getFormValues,
  onFilled,
}: UseFormFillAgentConfig) {
  const [phase, setPhase] = useState<FormFillAgentPhase>("idle")
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [streamingText, setStreamingText] = useState("")
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  const sessionIdRef = useRef<string>(crypto.randomUUID())

  // Stable refs to avoid stale closures in sendMessage
  const onFilledRef = useRef(onFilled)
  onFilledRef.current = onFilled
  const messagesRef = useRef(messages)
  messagesRef.current = messages
  const getFormValuesRef = useRef(getFormValues)
  getFormValuesRef.current = getFormValues
  const pageContextRef = useRef(pageContext)
  pageContextRef.current = pageContext

  const sendMessage = useCallback(
    async (userMessage: string) => {
      abortRef.current?.abort()
      const ctrl = new AbortController()
      abortRef.current = ctrl

      const newUserMsg: ChatMessage = { role: "user", content: userMessage }
      // Use ref to always get latest messages (avoids stale closure)
      const currentMessages = messagesRef.current
      const updatedMessages = [...currentMessages, newUserMsg]
      setMessages(updatedMessages)
      setPhase("thinking")
      setStreamingText("")
      setError(null)

      // History = all messages except the last user message (which we send as `message`)
      const history = updatedMessages.slice(0, -1)

      try {
        const currentFormValues = getFormValuesRef.current?.()
        const currentPageContext = pageContextRef.current
        const effectivePageContext = currentFormValues
          ? { ...currentPageContext, current_form: currentFormValues }
          : currentPageContext

        const res = await streamAgentFormFill({
          entity_type: entityType,
          message: userMessage,
          session_id: sessionIdRef.current,
          history,
          org_id: orgId,
          workspace_id: workspaceId,
          page_context: effectivePageContext,
        })

        if (!res.ok) {
          const data = await res.json().catch(() => ({}))
          throw new Error(
            (data as any)?.detail?.[0]?.msg ||
              (data as any)?.error?.message ||
              `HTTP ${res.status}`,
          )
        }

        const reader = res.body?.getReader()
        if (!reader) throw new Error("No response body")

        const decoder = new TextDecoder()
        let buffer = ""
        let assistantText = ""

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })

          const sseMessages = buffer.split("\n\n")
          buffer = sseMessages.pop() ?? ""

          for (const sseMsg of sseMessages) {
            if (!sseMsg.trim()) continue

            const lines = sseMsg.split("\n")
            let eventType = ""
            let dataLine = ""

            for (const line of lines) {
              if (line.startsWith("event:")) eventType = line.slice(6).trim()
              else if (line.startsWith("data:")) dataLine = line.slice(5).trim()
            }

            if (!dataLine) continue

            let parsed: Record<string, unknown>
            try {
              parsed = JSON.parse(dataLine)
            } catch {
              continue
            }

            if (eventType === "content_delta") {
              const delta = (parsed.delta as string) || ""
              assistantText += delta
              setStreamingText(assistantText)
            } else if (eventType === "message_end") {
              // Finalize assistant message
              if (assistantText) {
                const finalText = assistantText
                assistantText = ""
                setMessages((prev) => [
                  ...prev,
                  { role: "assistant", content: finalText },
                ])
                setStreamingText("")
              }
              // After form fill, go back to idle so follow-up messages work
              setPhase("idle")
            } else if (eventType === "form_fill_proposed") {
              const fields = parsed.fields as Record<string, string> | undefined
              if (fields) {
                // Call onFilled on EVERY form_fill_proposed — not just the first
                onFilledRef.current(fields)
                // Append explanation as assistant message if present
                const explanation = (parsed.explanation as string) || ""
                const confirmMsg = explanation
                  ? `I've updated the form. ${explanation}`
                  : "I've updated the form based on your description. Feel free to ask for changes or submit."
                setMessages((prev) => [...prev, { role: "assistant", content: confirmMsg }])
                setStreamingText("")
                // Don't return early — let stream continue to read message_end
              }
            } else if (eventType === "fill_error") {
              const msg = (parsed.message as string) || "AI fill failed"
              setError(msg)
              setPhase("error")
              return
            } else if (eventType === "error") {
              const msg = (parsed.message as string) || "Agent error"
              setError(msg)
              setPhase("error")
              return
            }
          }
        }

        // Stream ended — set idle if not already handled by message_end
        setPhase((p) => (p === "thinking" ? "idle" : p))
      } catch (err) {
        if ((err as Error)?.name === "AbortError") return
        setError(err instanceof Error ? err.message : "AI fill failed")
        setPhase("error")
      }
    },
    // Minimal deps — refs handle the rest to avoid stale closures
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [entityType, orgId, workspaceId],
  )

  const reset = useCallback(() => {
    abortRef.current?.abort()
    setMessages([])
    setStreamingText("")
    setError(null)
    setPhase("idle")
    sessionIdRef.current = crypto.randomUUID()
  }, [])

  return { phase, messages, streamingText, error, sendMessage, reset }
}
