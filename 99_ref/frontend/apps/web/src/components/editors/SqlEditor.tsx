"use client"

import React, { useEffect, useRef, useCallback } from "react"
import { EditorView, keymap, placeholder as cmPlaceholder } from "@codemirror/view"
import { EditorState } from "@codemirror/state"
import { sql, PostgreSQL } from "@codemirror/lang-sql"
import { autocompletion, CompletionContext, type Completion } from "@codemirror/autocomplete"
import { oneDark } from "@codemirror/theme-one-dark"
import type { TableMetadata } from "@/lib/types/admin"

// ── Forbidden SQL keywords (visual warning) ─────────────────────────────────

const FORBIDDEN_KEYWORDS = new Set([
  "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
  "CREATE", "GRANT", "REVOKE", "COPY", "EXECUTE", "CALL",
])

// ── Bind param keys available for completion ────────────────────────────────

const BIND_PARAM_COMPLETIONS: Completion[] = [
  { label: "$user_id", type: "variable", detail: "Recipient user ID" },
  { label: "$actor_id", type: "variable", detail: "Actor who triggered event" },
  { label: "$tenant_key", type: "variable", detail: "Tenant key" },
  { label: "$org_id", type: "variable", detail: "Organization ID" },
  { label: "$workspace_id", type: "variable", detail: "Workspace ID" },
  { label: "$framework_id", type: "variable", detail: "Framework ID" },
  { label: "$control_id", type: "variable", detail: "Control ID" },
  { label: "$task_id", type: "variable", detail: "Task ID" },
  { label: "$risk_id", type: "variable", detail: "Risk ID" },
]

// ── Build completions from schema metadata ──────────────────────────────────

function buildSchemaCompletions(tables: TableMetadata[]): Completion[] {
  const completions: Completion[] = []

  for (const t of tables) {
    const qualifiedName = `"${t.schema_name}"."${t.table_name}"`
    completions.push({
      label: qualifiedName,
      type: "class",
      detail: `${t.columns.length} columns`,
      boost: 1,
    })
    // Short table name too
    completions.push({
      label: t.table_name,
      type: "class",
      detail: t.schema_name,
      boost: 0,
    })

    for (const col of t.columns) {
      completions.push({
        label: col.name,
        type: "property",
        detail: `${t.table_name} (${col.data_type})`,
      })
    }
  }

  return completions
}

function customCompletions(schemaCompletions: Completion[]) {
  return function completionSource(context: CompletionContext) {
    // Match word characters, $, ., and double quotes
    const word = context.matchBefore(/[\w$."]+/)
    if (!word || (word.from === word.to && !context.explicit)) return null

    const allCompletions = [...BIND_PARAM_COMPLETIONS, ...schemaCompletions]

    return {
      from: word.from,
      options: allCompletions,
      validFor: /^[\w$."]*$/,
    }
  }
}

// ── Light theme to match kcontrol style ─────────────────────────────────────

const lightTheme = EditorView.theme({
  "&": {
    backgroundColor: "hsl(var(--background))",
    color: "hsl(var(--foreground))",
    borderRadius: "var(--radius)",
    border: "1px solid hsl(var(--border))",
    fontSize: "13px",
    fontFamily: "var(--font-mono, ui-monospace, monospace)",
  },
  ".cm-content": {
    caretColor: "hsl(var(--foreground))",
    padding: "8px 0",
  },
  ".cm-cursor": {
    borderLeftColor: "hsl(var(--foreground))",
  },
  "&.cm-focused": {
    outline: "2px solid hsl(var(--ring))",
    outlineOffset: "-1px",
  },
  ".cm-gutters": {
    backgroundColor: "hsl(var(--muted))",
    color: "hsl(var(--muted-foreground))",
    border: "none",
  },
  ".cm-activeLine": {
    backgroundColor: "hsl(var(--muted) / 0.3)",
  },
  ".cm-selectionMatch": {
    backgroundColor: "hsl(var(--accent) / 0.3)",
  },
  ".cm-tooltip": {
    backgroundColor: "hsl(var(--popover))",
    color: "hsl(var(--popover-foreground))",
    border: "1px solid hsl(var(--border))",
    borderRadius: "var(--radius)",
  },
  ".cm-tooltip-autocomplete": {
    "& > ul > li": {
      padding: "2px 8px",
    },
    "& > ul > li[aria-selected]": {
      backgroundColor: "hsl(var(--accent))",
      color: "hsl(var(--accent-foreground))",
    },
  },
  ".cm-placeholder": {
    color: "hsl(var(--muted-foreground))",
  },
})

// ── SqlEditor component ─────────────────────────────────────────────────────

interface SqlEditorProps {
  value: string
  onChange: (value: string) => void
  schemaMetadata?: TableMetadata[]
  readOnly?: boolean
  minHeight?: string
  placeholderText?: string
}

export default function SqlEditor({
  value,
  onChange,
  schemaMetadata = [],
  readOnly = false,
  minHeight = "180px",
  placeholderText = "SELECT ... FROM ... WHERE user_id = $1",
}: SqlEditorProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const viewRef = useRef<EditorView | null>(null)
  const onChangeRef = useRef(onChange)
  onChangeRef.current = onChange

  const schemaCompletions = React.useMemo(
    () => buildSchemaCompletions(schemaMetadata),
    [schemaMetadata]
  )

  const createExtensions = useCallback(() => {
    return [
      sql({ dialect: PostgreSQL }),
      autocompletion({
        override: [customCompletions(schemaCompletions)],
        activateOnTyping: true,
      }),
      lightTheme,
      EditorView.updateListener.of((update) => {
        if (update.docChanged) {
          onChangeRef.current(update.state.doc.toString())
        }
      }),
      EditorView.lineWrapping,
      EditorState.readOnly.of(readOnly),
      cmPlaceholder(placeholderText),
      EditorView.theme({
        ".cm-scroller": { minHeight },
      }),
    ]
  }, [schemaCompletions, readOnly, minHeight, placeholderText])

  useEffect(() => {
    if (!containerRef.current) return

    const state = EditorState.create({
      doc: value,
      extensions: createExtensions(),
    })

    const view = new EditorView({
      state,
      parent: containerRef.current,
    })

    viewRef.current = view

    return () => {
      view.destroy()
      viewRef.current = null
    }
    // Only re-create on extension changes, not value changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [createExtensions])

  // Sync external value changes into the editor
  useEffect(() => {
    const view = viewRef.current
    if (!view) return
    const currentDoc = view.state.doc.toString()
    if (currentDoc !== value) {
      view.dispatch({
        changes: { from: 0, to: currentDoc.length, insert: value },
      })
    }
  }, [value])

  // Insert text at cursor (exposed for bind param toolbar)
  const insertAtCursor = useCallback((text: string) => {
    const view = viewRef.current
    if (!view || readOnly) return
    const pos = view.state.selection.main.head
    view.dispatch({
      changes: { from: pos, insert: text },
      selection: { anchor: pos + text.length },
    })
    view.focus()
  }, [readOnly])

  // Expose insertAtCursor via data attribute for parent access
  useEffect(() => {
    if (containerRef.current) {
      ;(containerRef.current as any).__insertAtCursor = insertAtCursor
    }
  }, [insertAtCursor])

  // Validate and show warning for forbidden keywords
  const forbiddenFound = React.useMemo(() => {
    const tokens = value.toUpperCase().match(/[A-Z_]+/g) ?? []
    return tokens.filter((t) => FORBIDDEN_KEYWORDS.has(t))
  }, [value])

  return (
    <div className="space-y-1">
      <div
        ref={containerRef}
        className={`overflow-hidden rounded-md ${readOnly ? "opacity-70 cursor-not-allowed" : ""}`}
      />
      {forbiddenFound.length > 0 && !readOnly && (
        <p className="text-[10px] text-red-500">
          Warning: forbidden keyword{forbiddenFound.length > 1 ? "s" : ""} detected: {forbiddenFound.join(", ")}
        </p>
      )}
    </div>
  )
}

// ── BindParamToolbar ────────────────────────────────────────────────────────

const BIND_PARAM_KEYS = [
  { key: "$user_id", label: "$user_id", source: "context" },
  { key: "$actor_id", label: "$actor_id", source: "context" },
  { key: "$tenant_key", label: "$tenant_key", source: "context" },
  { key: "$org_id", label: "$org_id", source: "context" },
  { key: "$workspace_id", label: "$workspace_id", source: "context" },
  { key: "$framework_id", label: "$framework_id", source: "audit_property" },
  { key: "$control_id", label: "$control_id", source: "audit_property" },
  { key: "$task_id", label: "$task_id", source: "audit_property" },
  { key: "$risk_id", label: "$risk_id", source: "audit_property" },
] as const

interface BindParamToolbarProps {
  editorContainerRef: React.RefObject<HTMLDivElement | null>
  disabled?: boolean
}

export function BindParamToolbar({ editorContainerRef, disabled = false }: BindParamToolbarProps) {
  function handleInsert(key: string) {
    if (disabled) return
    const container = editorContainerRef.current
    if (container && (container as any).__insertAtCursor) {
      ;(container as any).__insertAtCursor(key)
    }
  }

  return (
    <div className="flex flex-wrap gap-1">
      <span className="text-[10px] text-muted-foreground mr-1 self-center">Insert:</span>
      {BIND_PARAM_KEYS.map((bp) => (
        <button
          key={bp.key}
          type="button"
          disabled={disabled}
          onClick={() => handleInsert(bp.key)}
          className={`inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[10px] font-mono transition-colors
            ${disabled
              ? "border-border bg-muted/30 text-muted-foreground/50 cursor-not-allowed"
              : "border-border bg-muted text-muted-foreground hover:bg-accent hover:text-accent-foreground cursor-pointer"
            }`}
          title={`Insert ${bp.key} at cursor`}
        >
          {bp.label}
          <span className={`inline-block h-1.5 w-1.5 rounded-full ${bp.source === "context" ? "bg-blue-500" : "bg-amber-500"}`} />
        </button>
      ))}
      <span className="text-[9px] text-muted-foreground self-center ml-1">
        <span className="inline-block h-1.5 w-1.5 rounded-full bg-blue-500 mr-0.5" />context
        <span className="inline-block h-1.5 w-1.5 rounded-full bg-amber-500 mx-0.5 ml-2" />audit
      </span>
    </div>
  )
}
