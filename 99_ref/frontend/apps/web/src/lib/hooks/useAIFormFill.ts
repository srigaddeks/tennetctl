"use client"

import { useCallback, useRef, useState } from "react"
import { streamFormFill } from "@/lib/api/ai"
import type { FormFillRequest } from "@/lib/api/ai"

export type AIFormFillPhase = "idle" | "loading" | "done" | "error"

export interface UseAIFormFillConfig {
  onFilled: (fields: Record<string, string>) => void
}

export function useAIFormFill({ onFilled }: UseAIFormFillConfig) {
  const [phase, setPhase] = useState<AIFormFillPhase>("idle")
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const fill = useCallback(
    async (request: FormFillRequest) => {
      abortRef.current?.abort()
      const ctrl = new AbortController()
      abortRef.current = ctrl

      setPhase("loading")
      setError(null)

      try {
        const res = await streamFormFill(request)
        if (!res.ok) {
          const data = await res.json().catch(() => ({}))
          throw new Error(
            data?.detail?.[0]?.msg || data?.error?.message || `HTTP ${res.status}`,
          )
        }

        const reader = res.body?.getReader()
        if (!reader) throw new Error("No response body")

        const decoder = new TextDecoder()
        let buffer = ""

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })

          // SSE messages are separated by double newlines
          const messages = buffer.split("\n\n")
          buffer = messages.pop() ?? ""

          for (const message of messages) {
            if (!message.trim()) continue

            const lines = message.split("\n")
            let eventType = ""
            let dataLine = ""

            for (const line of lines) {
              if (line.startsWith("event:")) {
                eventType = line.slice(6).trim()
              } else if (line.startsWith("data:")) {
                dataLine = line.slice(5).trim()
              }
            }

            if (!dataLine) continue

            let parsed: Record<string, unknown>
            try {
              parsed = JSON.parse(dataLine)
            } catch {
              continue
            }

            if (eventType === "fill_complete") {
              const fields = parsed.fields as Record<string, string> | undefined
              if (fields) {
                onFilled(fields)
                setPhase("done")
                return
              }
            } else if (eventType === "fill_error") {
              const msg = (parsed.message as string) || "AI fill failed"
              setError(msg)
              setPhase("error")
              return
            }
          }
        }

        // Stream ended without fill_complete
        setError("AI did not return a complete response. Please try again.")
        setPhase("error")
      } catch (err) {
        if ((err as Error)?.name === "AbortError") return
        setError(err instanceof Error ? err.message : "AI fill failed")
        setPhase("error")
      }
    },
    [onFilled],
  )

  const reset = useCallback(() => {
    abortRef.current?.abort()
    setPhase("idle")
    setError(null)
  }, [])

  return { phase, error, fill, reset }
}
