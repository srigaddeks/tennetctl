"use client"

import { useEffect, useState, useCallback, useRef } from "react"
import {
  Button,
  Input,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@kcontrol/ui"
import { Search, Layers, CheckCircle2, Plus, Loader2, X, AlertTriangle, Sparkles } from "lucide-react"
import { listAllControls, listTestMappings, createTestMapping, deleteTestMapping } from "@/lib/api/grc"
import {
  suggestControlsForTest,
  applyTestLinkerSuggestions,
  type ControlSuggestion,
} from "@/lib/api/testLinker"
import type { ControlResponse, TestControlMappingResponse } from "@/lib/types/grc"

interface LinkControlsDialogProps {
  open: boolean
  testId: string
  testName: string
  orgId?: string
  workspaceId?: string
  onClose: () => void
}

const LINK_TYPE_LABELS: Record<string, string> = {
  covers: "Covers",
  partially_covers: "Partial",
  related: "Related",
}

const LINK_TYPE_STYLES: Record<string, string> = {
  covers: "bg-green-500/10 text-green-600 border-green-500/30",
  partially_covers: "bg-amber-500/10 text-amber-600 border-amber-500/30",
  related: "bg-sky-500/10 text-sky-600 border-sky-500/30",
}

export function LinkControlsDialog({ open, testId, testName, orgId, workspaceId, onClose }: LinkControlsDialogProps) {
  const [search, setSearch] = useState("")
  const [controls, setControls] = useState<ControlResponse[]>([])
  const [mappings, setMappings] = useState<TestControlMappingResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const searchRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // AI suggestions state
  const [aiMode, setAiMode] = useState(false)
  const [aiLoading, setAiLoading] = useState(false)
  const [aiSuggestions, setAiSuggestions] = useState<ControlSuggestion[]>([])
  const [aiError, setAiError] = useState<string | null>(null)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [applying, setApplying] = useState(false)
  const [applyMsg, setApplyMsg] = useState<string | null>(null)

  const linkedControlIds = new Set(mappings.map((m) => m.control_id))

  useEffect(() => {
    if (!open) return
    listTestMappings(testId)
      .then((r) => setMappings(r.items ?? []))
      .catch(() => {})
  }, [open, testId])

  const runSearch = useCallback(async (q: string) => {
    setLoading(true)
    setError(null)
    try {
      const res = await listAllControls({
        search: q || undefined,
        scope_org_id: orgId,
        ...(workspaceId ? { scope_workspace_id: workspaceId } : {}),
        limit: 30,
      })
      setControls(res.items)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load controls")
    } finally {
      setLoading(false)
    }
  }, [orgId, workspaceId])

  useEffect(() => {
    if (!open || aiMode) return
    if (searchRef.current) clearTimeout(searchRef.current)
    searchRef.current = setTimeout(() => runSearch(search), 300)
    return () => { if (searchRef.current) clearTimeout(searchRef.current) }
  }, [search, open, runSearch, aiMode])

  async function handleLink(control: ControlResponse) {
    setSaving(control.id)
    setError(null)
    try {
      const m = await createTestMapping(testId, { control_id: control.id })
      setMappings((prev) => [...prev, m])
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to link control")
    } finally {
      setSaving(null)
    }
  }

  async function handleUnlink(control: ControlResponse) {
    const mapping = mappings.find((m) => m.control_id === control.id)
    if (!mapping) return
    setSaving(control.id)
    setError(null)
    try {
      await deleteTestMapping(testId, mapping.id)
      setMappings((prev) => prev.filter((m) => m.id !== mapping.id))
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to unlink control")
    } finally {
      setSaving(null)
    }
  }

  async function handleAiSuggest() {
    setAiMode(true)
    setAiLoading(true)
    setAiError(null)
    setAiSuggestions([])
    setSelected(new Set())
    setApplyMsg(null)
    try {
      const suggestions = await suggestControlsForTest({
        test_id: testId,
        org_id: orgId,
        workspace_id: workspaceId,
      })
      // Pre-select all suggestions
      setAiSuggestions(suggestions)
      setSelected(new Set(suggestions.map((s) => s.control_id)))
    } catch (e) {
      setAiError(e instanceof Error ? e.message : "AI suggestion failed")
    } finally {
      setAiLoading(false)
    }
  }

  function toggleSuggestion(controlId: string) {
    setSelected((prev) => {
      const next = new Set(prev)
      next.has(controlId) ? next.delete(controlId) : next.add(controlId)
      return next
    })
  }

  async function handleApply() {
    const approved = aiSuggestions.filter((s) => selected.has(s.control_id))
    if (!approved.length) return
    setApplying(true)
    setAiError(null)
    try {
      const result = await applyTestLinkerSuggestions({ test_id: testId, suggestions: approved })
      setApplyMsg(
        `Submitted ${result.created} mapping${result.created !== 1 ? "s" : ""} for approval${result.skipped ? ` (${result.skipped} already existed)` : ""}`,
      )
      // Refresh mappings
      const r = await listTestMappings(testId)
      setMappings(r.items ?? [])
      // Clear suggestions
      setAiSuggestions([])
      setSelected(new Set())
    } catch (e) {
      setAiError(e instanceof Error ? e.message : "Failed to apply suggestions")
    } finally {
      setApplying(false)
    }
  }

  function handleClose() {
    setSearch("")
    setError(null)
    setAiMode(false)
    setAiSuggestions([])
    setAiError(null)
    setApplyMsg(null)
    onClose()
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && handleClose()}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <div className="flex items-center justify-between gap-2">
            <DialogTitle className="flex items-center gap-2">
              <Layers className="h-4 w-4 text-primary" />
              Link to Controls
            </DialogTitle>
            {!aiMode && (
              <Button
                size="sm"
                variant="outline"
                className="gap-1.5 text-violet-600 border-violet-500/30 hover:bg-violet-500/10 h-7 text-xs"
                onClick={handleAiSuggest}
              >
                <Sparkles className="h-3.5 w-3.5" />
                AI Suggest
              </Button>
            )}
          </div>
          <DialogDescription>
            Link <span className="font-medium text-foreground">{testName}</span> to one or more GRC controls.
            {aiMode ? " Review AI suggestions below. Submitted AI mappings stay pending until approved." : " Search and toggle controls below."}
          </DialogDescription>
        </DialogHeader>

        {/* Linked controls summary */}
        {mappings.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pb-1">
            {mappings.map((m) => (
              <span
                key={m.id}
                className="inline-flex items-center gap-1 rounded-full border border-primary/20 bg-primary/5 px-2 py-0.5 text-[11px] font-medium text-primary"
              >
                <CheckCircle2 className="h-2.5 w-2.5" />
                {m.control_code ?? m.control_id.slice(0, 8)}
                {m.framework_code && (
                  <span className="opacity-60">· {m.framework_code}</span>
                )}
              </span>
            ))}
          </div>
        )}

        {applyMsg && (
          <div className="flex items-center gap-2 text-xs text-green-600 bg-green-500/10 rounded-md px-3 py-2 border border-green-500/20">
            <CheckCircle2 className="h-3.5 w-3.5 shrink-0" />
            {applyMsg}
          </div>
        )}

        {/* ── AI Mode ─────────────────────────────────────────────────────────── */}
        {aiMode ? (
          <div className="space-y-3">
            {aiLoading && (
              <div className="flex items-center justify-center gap-2 py-10 text-sm text-muted-foreground">
                <Loader2 className="h-5 w-5 animate-spin text-violet-500" />
                Analysing test and matching controls…
              </div>
            )}
            {aiError && (
              <div className="flex items-center gap-2 text-xs text-destructive bg-destructive/5 rounded-md px-3 py-2">
                <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                {aiError}
              </div>
            )}
            {!aiLoading && aiSuggestions.length === 0 && !aiError && (
              <div className="py-8 text-center text-sm text-muted-foreground">
                No suggestions found. All controls may already be linked, or the AI found no relevant matches.
              </div>
            )}
            {!aiLoading && aiSuggestions.length > 0 && (
              <>
                <div className="flex items-center justify-between text-xs text-muted-foreground px-1">
                  <span>{aiSuggestions.length} suggestion{aiSuggestions.length !== 1 ? "s" : ""} · {selected.size} selected</span>
                  <div className="flex gap-2">
                    <button className="hover:text-foreground underline" onClick={() => setSelected(new Set(aiSuggestions.map(s => s.control_id)))}>Select all</button>
                    <button className="hover:text-foreground underline" onClick={() => setSelected(new Set())}>None</button>
                  </div>
                </div>
                <div className="border border-border rounded-lg overflow-hidden max-h-80 overflow-y-auto divide-y divide-border">
                  {aiSuggestions.map((s) => {
                    const isSelected = selected.has(s.control_id)
                    const alreadyLinked = linkedControlIds.has(s.control_id)
                    return (
                      <div
                        key={s.control_id}
                        className={`flex items-start gap-3 px-3 py-3 transition-colors cursor-pointer ${
                          alreadyLinked ? "opacity-50" : isSelected ? "bg-violet-500/5" : "hover:bg-muted/40"
                        }`}
                        onClick={() => !alreadyLinked && toggleSuggestion(s.control_id)}
                      >
                        {/* Checkbox */}
                        <div className={`mt-0.5 h-4 w-4 rounded border-2 shrink-0 flex items-center justify-center transition-colors ${
                          alreadyLinked ? "border-green-500 bg-green-500/20" :
                          isSelected ? "border-violet-500 bg-violet-500" : "border-border"
                        }`}>
                          {alreadyLinked
                            ? <CheckCircle2 className="h-2.5 w-2.5 text-green-500" />
                            : isSelected && <CheckCircle2 className="h-2.5 w-2.5 text-white" />
                          }
                        </div>

                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-[11px] font-mono text-primary">{s.control_code}</span>
                            <span className={`text-[10px] px-1.5 py-0 rounded border font-semibold ${LINK_TYPE_STYLES[s.link_type] ?? ""}`}>
                              {LINK_TYPE_LABELS[s.link_type] ?? s.link_type}
                            </span>
                            <span className="text-[10px] text-muted-foreground ml-auto">
                              {Math.round(s.confidence * 100)}% confidence
                            </span>
                            {alreadyLinked && (
                              <span className="text-[10px] text-green-600 font-medium">already linked</span>
                            )}
                          </div>
                          <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{s.rationale}</p>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </>
            )}
          </div>
        ) : (
          /* ── Manual Mode ──────────────────────────────────────────────────── */
          <>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
              <Input
                className="pl-8 h-9 text-sm"
                placeholder="Search controls by name, code, or framework..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                autoFocus
              />
            </div>

            {error && (
              <div className="flex items-center gap-2 text-xs text-destructive bg-destructive/5 rounded-md px-3 py-2">
                <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                {error}
              </div>
            )}

            <div className="border border-border rounded-lg overflow-hidden max-h-72 overflow-y-auto">
              {loading ? (
                <div className="flex items-center justify-center py-8 gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Searching…
                </div>
              ) : controls.length === 0 ? (
                <div className="py-8 text-center text-sm text-muted-foreground">
                  {search ? "No controls match your search." : "Start typing to search controls."}
                </div>
              ) : (
                <div className="divide-y divide-border">
                  {controls.map((c) => {
                    const linked = linkedControlIds.has(c.id)
                    const isSaving = saving === c.id
                    return (
                      <div
                        key={c.id}
                        className={`flex items-center gap-3 px-3 py-2.5 transition-colors ${
                          linked ? "bg-primary/5" : "hover:bg-muted/40"
                        }`}
                      >
                        <div className={`h-1.5 w-1.5 rounded-full shrink-0 ${linked ? "bg-primary" : "bg-border"}`} />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <span className="text-[11px] font-mono text-primary shrink-0">{c.control_code}</span>
                            <span className="text-xs font-medium truncate">{c.name}</span>
                          </div>
                          <p className="text-[10px] text-muted-foreground mt-0.5">
                            {c.framework_code}
                            {c.requirement_code && ` · ${c.requirement_code}`}
                          </p>
                        </div>
                        <button
                          disabled={isSaving}
                          onClick={() => linked ? handleUnlink(c) : handleLink(c)}
                          className={`shrink-0 flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium transition-colors ${
                            linked
                              ? "text-destructive hover:bg-destructive/10"
                              : "text-primary hover:bg-primary/10"
                          } disabled:opacity-50`}
                        >
                          {isSaving ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          ) : linked ? (
                            <><X className="h-3 w-3" /> Unlink</>
                          ) : (
                            <><Plus className="h-3 w-3" /> Link</>
                          )}
                        </button>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </>
        )}

        <DialogFooter>
          <div className="flex items-center gap-2 w-full">
            <span className="text-xs text-muted-foreground flex-1">
              {mappings.length} control{mappings.length !== 1 ? "s" : ""} linked
            </span>
            {aiMode && (
              <>
                <Button variant="ghost" size="sm" onClick={() => { setAiMode(false); setAiSuggestions([]) }}>
                  Back to manual
                </Button>
                {aiSuggestions.length > 0 && (
                <Button
                  size="sm"
                  className="gap-1.5 bg-violet-600 hover:bg-violet-700 text-white"
                  disabled={selected.size === 0 || applying}
                  onClick={handleApply}
                >
                  {applying ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Sparkles className="h-3.5 w-3.5" />}
                  Submit {selected.size} Control{selected.size !== 1 ? "s" : ""}
                </Button>
                )}
              </>
            )}
            <Button onClick={handleClose}>Done</Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
