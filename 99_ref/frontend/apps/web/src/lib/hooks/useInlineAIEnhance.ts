"use client"

import { useCallback, useRef, useState } from "react"
import { streamEnhanceText } from "@/lib/api/ai"

// ── Types ──────────────────────────────────────────────────────────────────────

export type EnhancePhase = "idle" | "loading" | "showing_diff" | "error"

export interface EnhanceState {
  phase: EnhancePhase
  streamedText: string
  original: string | string[]
  enhanced: string | string[]
  error: string | null
  inputTokens: number
  outputTokens: number
}

export interface UseInlineAIEnhanceConfig {
  entityType: string
  entityId: string | null
  fieldName: string
  currentValue: string | string[]
  /** If true, split the enhanced text on newlines for diff/apply */
  isArrayField?: boolean
  orgId: string | null
  workspaceId: string | null
  entityContext?: Record<string, unknown>
  onApply: (value: string | string[]) => void | Promise<void>
}

const INITIAL_STATE: EnhanceState = {
  phase: "idle",
  streamedText: "",
  original: "",
  enhanced: "",
  error: null,
  inputTokens: 0,
  outputTokens: 0,
}

// ── Hook ───────────────────────────────────────────────────────────────────────

export function useInlineAIEnhance(config: UseInlineAIEnhanceConfig) {
  const [state, setState] = useState<EnhanceState>(INITIAL_STATE)
  const abortRef = useRef<AbortController | null>(null)

  const enhance = useCallback(
    async (instruction: string) => {
      abortRef.current?.abort()
      const ac = new AbortController()
      abortRef.current = ac

      setState({
        phase: "loading",
        streamedText: "",
        original: config.currentValue,
        enhanced: "",
        error: null,
        inputTokens: 0,
        outputTokens: 0,
      })

      try {
        const response = await streamEnhanceText({
          entity_type: config.entityType,
          entity_id: config.entityId,
          field_name: config.fieldName,
          current_value: config.currentValue,
          instruction,
          org_id: config.orgId,
          workspace_id: config.workspaceId,
          entity_context: config.entityContext,
        })

        if (!response.ok || !response.body) {
          const errData = await response.json().catch(() => ({})) as {
            error?: { message?: string }
          }
          throw new Error(
            errData?.error?.message ?? `Request failed (${response.status})`,
          )
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ""
        let accumulated = ""

        while (true) {
          if (ac.signal.aborted) {
            reader.cancel()
            break
          }

          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })

          // SSE messages are separated by double newlines
          const messages = buffer.split("\n\n")
          // Keep the last (potentially incomplete) chunk in the buffer
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

            if (eventType === "content_delta" && typeof parsed.delta === "string") {
              accumulated += parsed.delta
              const snapshot = accumulated
              setState(prev => ({ ...prev, streamedText: snapshot }))
            } else if (eventType === "enhance_complete") {
              const finalText =
                typeof parsed.enhanced_value === "string" && parsed.enhanced_value.length > 0
                  ? parsed.enhanced_value
                  : accumulated

              const usageData = parsed.usage as { input_tokens?: number; output_tokens?: number } | undefined
              const inputTokens = usageData?.input_tokens ?? 0
              const outputTokens = usageData?.output_tokens ?? 0

              const finalValue: string | string[] = config.isArrayField
                ? finalText
                    .split("\n")
                    .map((l: string) => l.replace(/^[-•*]\s*/, "").trim())
                    .filter(Boolean)
                : finalText

              setState({
                phase: "showing_diff",
                streamedText: accumulated,
                original: config.currentValue,
                enhanced: finalValue,
                error: null,
                inputTokens,
                outputTokens,
              })
            } else if (eventType === "enhance_error") {
              const msg =
                typeof parsed.message === "string" ? parsed.message : "Enhancement failed"
              throw new Error(msg)
            }
          }
        }

        // Fallback: if stream ended without an enhance_complete event, transition
        // from loading to showing_diff using whatever was accumulated
        setState(prev => {
          if (prev.phase === "loading" && prev.streamedText.length > 0) {
            const finalValue: string | string[] = config.isArrayField
              ? prev.streamedText
                  .split("\n")
                  .map((l: string) => l.replace(/^[-•*]\s*/, "").trim())
                  .filter(Boolean)
              : prev.streamedText
            return {
              ...prev,
              phase: "showing_diff",
              enhanced: finalValue,
            }
          }
          return prev
        })
      } catch (err: unknown) {
        if ((err as { name?: string }).name === "AbortError") return
        setState(prev => ({
          ...prev,
          phase: "error",
          error: (err instanceof Error ? err.message : null) ?? "An unexpected error occurred",
        }))
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [
      config.entityType,
      config.entityId,
      config.fieldName,
      config.currentValue,
      config.isArrayField,
      config.orgId,
      config.workspaceId,
      config.entityContext,
    ],
  )

  const apply = useCallback(async () => {
    if (state.phase !== "showing_diff") return
    await config.onApply(state.enhanced)
    setState(INITIAL_STATE)
  }, [state.phase, state.enhanced, config])

  const cancel = useCallback(() => {
    abortRef.current?.abort()
    setState(prev => ({
      ...prev,
      phase: "idle",
      streamedText: "",
      error: null,
    }))
  }, [])

  const reset = useCallback(() => {
    abortRef.current?.abort()
    setState(INITIAL_STATE)
  }, [])

  return { state, enhance, apply, cancel, reset }
}
